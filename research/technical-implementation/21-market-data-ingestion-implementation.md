# 21 - Market Data Ingestion Implementation

> Research date: 2026-03-10
> Goal: Define the architecture for fetching daily OHLCV price data from yfinance, validating data quality, handling failures, and persisting to Cosmos DB daily_prices container with comprehensive logging.
> Prerequisites: [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md), [05-data-pipeline-and-quality.md](05-data-pipeline-and-quality.md), [16-omx-ticker-list-management.md](16-omx-ticker-list-management.md), [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md)

## Table of Contents

1. [Overview](#overview)
2. [Fetcher Architecture](#fetcher-architecture)
3. [yfinance Integration](#yfinance-integration)
4. [Batch Fetching Strategy](#batch-fetching-strategy)
5. [Data Validation](#data-validation)
6. [Data Cleaning](#data-cleaning)
7. [Cosmos Persistence](#cosmos-persistence)
8. [Error Handling and Logging](#error-handling-and-logging)
9. [Swedish Market Calendar](#swedish-market-calendar)
10. [Testing Strategy](#testing-strategy)

---

## Overview

Market data ingestion is the **foundation of the scanner** — everything depends on fresh, clean OHLCV data. The fetcher component:

1. **Fetches data** from yfinance for OMX Stockholm tickers
2. **Validates data** — checks for gaps, missing columns, stale data
3. **Cleans data** — handles NaN values, deduplicates, filters invalid records
4. **Persists to Cosmos** — upserts to daily_prices container
5. **Logs metadata** — records fetch results in scan_runs for observability

**Design principles:**
- **Fail gracefully:** One ticker failure doesn't stop entire scan
- **Log everything:** Success/failure counts, failed tickers, duration
- **Idempotent:** Re-run same day, no duplicates (leveraging deterministic IDs from repository)
- **Observable:** Detailed logs for debugging, summary stats for monitoring

---

## Fetcher Architecture

### Component Responsibilities

```
MarketDataFetcher
    ├── fetch_universe(tickers, start_date, end_date) → FetchResult
    │   ├── For each ticker:
    │   │   ├── fetch_ticker_data(ticker)
    │   │   ├── validate_data(df)
    │   │   ├── clean_data(df)
    │   │   └── persist_to_cosmos(df)
    │   └── Aggregate results → FetchResult
    ├── validate_data(df) → ValidationResult
    ├── clean_data(df) → DataFrame
    └── persist_prices(ticker, df) → int (rows persisted)
```

### FetchResult Dataclass

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class FetchResult:
    """Result of fetching data for multiple tickers."""
    tickers_requested: int
    tickers_success: int
    tickers_failed: int
    failed_tickers: List[str] = field(default_factory=list)
    total_rows_persisted: int = 0
    duration_seconds: float = 0.0
```

---

## yfinance Integration

### yfinance Basics

**yfinance** is a Python library that scrapes Yahoo Finance data (unofficial API).

```python
import yfinance as yf

# Fetch single ticker
ticker = yf.Ticker("ERIC.ST")
df = ticker.history(start="2025-01-01", end="2026-03-10")

# Result: DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
```

**Swedish ticker format:**
- OMX Stockholm tickers: `{TICKER}.ST` (e.g., `ERIC.ST`, `VOLV-B.ST`, `ABB.ST`)
- Note: Some tickers have suffixes (e.g., `-B` for B shares)

### yfinance Limitations

1. **Rate limits:** No official limit, but aggressive fetching may get blocked
2. **Data gaps:** Occasional missing days (exchange holidays, low-volume stocks)
3. **Ticker changes:** Company name changes may break historical data
4. **No official support:** Yahoo can change format/availability anytime

**Mitigation strategies:**
- **Rate limiting:** Add small delay between fetches (0.1-0.5s)
- **Retry logic:** Retry transient failures (network errors, timeouts)
- **Validation:** Check for gaps, missing data, stale data
- **Logging:** Record all failures for manual review

---

## Batch Fetching Strategy

### Sequential vs Parallel Fetching

**Phase 1 decision:** Sequential fetching with small delay (simple, sufficient)

**Sequential pattern:**
```python
import time

for ticker in tickers:
    df = yf.Ticker(ticker).history(start=start_date, end=end_date)
    # Process df...
    time.sleep(0.2)  # 200ms delay between requests
```

**Why sequential:**
- OMX universe ~150 tickers × 0.2s delay = 30 seconds total
- No risk of rate limiting
- Simple error handling (one ticker fails, others continue)

**Phase 2 consideration:** Parallel fetching with ThreadPoolExecutor
```python
from concurrent.futures import ThreadPoolExecutor

def fetch_ticker(ticker):
    return ticker, yf.Ticker(ticker).history(...)

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(fetch_ticker, tickers)
```

**Trade-off:** 5× faster but higher rate limit risk.

---

### Fetch Date Range Strategy

**For daily scans:**
- Fetch last 5 days (to fill any gaps from weekends/holidays)
- Upsert to Cosmos (idempotent, no duplicates)

**For initial backfill:**
- Fetch last 250 days (1 year of trading history)
- Required for indicators that need lookback (e.g., 50-day SMA)

```python
from datetime import date, timedelta

def calculate_fetch_range(scan_date: date, backfill_days: int = 5) -> tuple[date, date]:
    """Calculate start and end dates for fetching."""
    end_date = scan_date
    start_date = scan_date - timedelta(days=backfill_days)
    return start_date, end_date
```

---

## Data Validation

### Validation Rules

From [05-data-pipeline-and-quality.md](05-data-pipeline-and-quality.md), validate:

1. **Required columns present:** Open, High, Low, Close, Volume
2. **No NaN in critical columns:** Close, Volume (Open/High/Low can have rare gaps)
3. **Price sanity checks:**
   - High >= Low
   - Close between Low and High
   - Open between Low and High (if present)
4. **Volume sanity check:** Volume >= 0
5. **Date range:** Data within requested date range
6. **Freshness:** Latest data is recent (not stale by >3 days)

### Validation Implementation

```python
import pandas as pd
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    issues: list[str]
    rows_before: int
    rows_after_clean: int = 0

def validate_price_data(df: pd.DataFrame, ticker: str) -> ValidationResult:
    """Validate fetched price data.
    
    Returns ValidationResult with is_valid=True if data passes checks.
    Logs warnings for non-critical issues.
    """
    
    issues = []
    rows_before = len(df)
    
    # Check 1: DataFrame not empty
    if df.empty:
        issues.append("No data returned")
        return ValidationResult(is_valid=False, issues=issues, rows_before=0)
    
    # Check 2: Required columns present
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        issues.append(f"Missing columns: {missing_columns}")
        return ValidationResult(is_valid=False, issues=issues, rows_before=rows_before)
    
    # Check 3: Critical columns have no NaN (Close, Volume)
    if df['Close'].isna().any():
        nan_count = df['Close'].isna().sum()
        issues.append(f"Close has {nan_count} NaN values")
        # Don't fail — clean_data() will drop these rows
    
    if df['Volume'].isna().any():
        nan_count = df['Volume'].isna().sum()
        issues.append(f"Volume has {nan_count} NaN values")
    
    # Check 4: Price sanity (High >= Low)
    invalid_high_low = df[df['High'] < df['Low']]
    if not invalid_high_low.empty:
        issues.append(f"{len(invalid_high_low)} rows have High < Low")
    
    # Check 5: Close within [Low, High]
    invalid_close = df[(df['Close'] < df['Low']) | (df['Close'] > df['High'])]
    if not invalid_close.empty:
        issues.append(f"{len(invalid_close)} rows have Close outside [Low, High]")
    
    # Check 6: Volume >= 0
    negative_volume = df[df['Volume'] < 0]
    if not negative_volume.empty:
        issues.append(f"{len(negative_volume)} rows have negative volume")
    
    # Log issues as warnings (non-critical if we have some valid rows)
    if issues:
        logger.warning(f"Validation issues for {ticker}: {issues}")
    
    # Consider valid if we have at least some data (cleaning will remove bad rows)
    is_valid = rows_before > 0 and 'Close' in df.columns
    
    return ValidationResult(is_valid=is_valid, issues=issues, rows_before=rows_before)
```

**Key design choices:**

1. **Non-blocking validation:** Issues logged as warnings, not errors
2. **Critical vs non-critical:** Missing Close/Volume is critical, other issues can be cleaned
3. **Detailed logging:** Each issue tracked for debugging

---

## Data Cleaning

### Cleaning Rules

1. **Drop rows with NaN in Close or Volume**
2. **Drop rows with invalid price relationships** (High < Low, Close outside range)
3. **Drop rows with negative volume**
4. **Forward-fill missing Open/High/Low** (from previous day, if available)
5. **Deduplicate** by date index (keep first occurrence)

### Cleaning Implementation

```python
def clean_price_data(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Clean fetched price data by removing invalid rows.
    
    Returns cleaned DataFrame (may be empty if all rows invalid).
    """
    
    if df.empty:
        return df
    
    rows_before = len(df)
    
    # 1. Drop rows with NaN in critical columns
    df = df.dropna(subset=['Close', 'Volume'])
    
    # 2. Drop rows with invalid price relationships
    df = df[df['High'] >= df['Low']]
    df = df[(df['Close'] >= df['Low']) & (df['Close'] <= df['High'])]
    
    # 3. Drop rows with negative volume
    df = df[df['Volume'] >= 0]
    
    # 4. Forward-fill missing Open/High/Low (if any)
    df['Open'] = df['Open'].fillna(method='ffill')
    df['High'] = df['High'].fillna(method='ffill')
    df['Low'] = df['Low'].fillna(method='ffill')
    
    # 5. Deduplicate by date index
    df = df[~df.index.duplicated(keep='first')]
    
    rows_after = len(df)
    rows_removed = rows_before - rows_after
    
    if rows_removed > 0:
        logger.info(f"Cleaned {ticker}: removed {rows_removed} invalid rows (kept {rows_after})")
    
    return df
```

**Why forward-fill:**
- If High/Low missing but Close available, estimate from previous day
- Better than dropping entire row (preserves Close price for indicators)

**Deduplication:**
- yfinance occasionally returns duplicate dates (e.g., timezone issues)
- Keep first occurrence (arbitrary, but consistent)

---

## Cosmos Persistence

### Persistence Strategy

**Pattern:** Upsert each row as separate document (idempotent).

```python
from datetime import datetime
from scanner.repository import CosmosRepository

def persist_prices(repository: CosmosRepository, ticker: str, df: pd.DataFrame) -> int:
    """Persist cleaned price DataFrame to Cosmos DB.
    
    Returns number of rows persisted.
    """
    
    rows_persisted = 0
    
    for date_index, row in df.iterrows():
        try:
            repository.daily_prices.upsert_price(
                ticker=ticker,
                date=date_index.date(),  # Convert pandas Timestamp to date
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row.get('Adj Close', row['Close'])),
            )
            rows_persisted += 1
        except Exception as e:
            logger.error(f"Failed to persist {ticker} {date_index.date()}", exc_info=True)
            # Continue with next row (don't fail entire ticker)
    
    return rows_persisted
```

**Why row-by-row:**
- Deterministic IDs (ticker_date) enable idempotent upserts
- Partial success (if one date fails, others persist)
- Simplicity (no batch API needed)

**Performance consideration:**
- 150 tickers × 5 days = 750 upserts per daily scan
- ~5 RU per upsert = 3,750 RU total
- Well under 400 RU/s limit (spread over ~30s fetch duration)

---

## Error Handling and Logging

### Fetcher Implementation

```python
import yfinance as yf
import time
from datetime import date, datetime
from scanner.repository import CosmosRepository

class MarketDataFetcher:
    """Fetches and persists market data for OMX tickers."""
    
    def __init__(self, repository: CosmosRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def fetch_universe(self, tickers: list[str], start_date: date, end_date: date) -> FetchResult:
        """Fetch data for list of tickers and persist to Cosmos.
        
        Returns FetchResult with summary statistics.
        """
        
        self.logger.info(f"Fetching data for {len(tickers)} tickers", extra={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        })
        
        start_time = time.time()
        result = FetchResult(tickers_requested=len(tickers))
        
        for i, ticker in enumerate(tickers):
            self.logger.debug(f"Fetching {ticker} ({i+1}/{len(tickers)})")
            
            try:
                # Fetch data from yfinance
                yf_ticker = yf.Ticker(ticker)
                df = yf_ticker.history(start=start_date, end=end_date)
                
                # Validate
                validation = validate_price_data(df, ticker)
                if not validation.is_valid:
                    self.logger.warning(f"Validation failed for {ticker}: {validation.issues}")
                    result.tickers_failed += 1
                    result.failed_tickers.append(ticker)
                    continue
                
                # Clean
                df = clean_price_data(df, ticker)
                if df.empty:
                    self.logger.warning(f"No valid data for {ticker} after cleaning")
                    result.tickers_failed += 1
                    result.failed_tickers.append(ticker)
                    continue
                
                # Persist
                rows = persist_prices(self.repository, ticker, df)
                result.total_rows_persisted += rows
                result.tickers_success += 1
                
                self.logger.debug(f"Persisted {rows} rows for {ticker}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {ticker}", exc_info=True)
                result.tickers_failed += 1
                result.failed_tickers.append(ticker)
            
            # Rate limiting delay
            time.sleep(0.2)
        
        result.duration_seconds = time.time() - start_time
        
        self.logger.info("Market data fetch complete", extra={
            "tickers_success": result.tickers_success,
            "tickers_failed": result.tickers_failed,
            "rows_persisted": result.total_rows_persisted,
            "duration_seconds": result.duration_seconds,
            "failed_tickers": result.failed_tickers,
        })
        
        return result
```

### Logging Strategy

**Log levels:**
- **DEBUG:** Per-ticker progress, row counts
- **INFO:** Overall summary (start, completion, statistics)
- **WARNING:** Validation failures, empty data after cleaning
- **ERROR:** Exception during fetch/persist

**Structured logging (JSON):**
```json
{
  "asctime": "2026-03-10T14:32:45",
  "name": "scanner.fetcher",
  "levelname": "INFO",
  "message": "Market data fetch complete",
  "tickers_success": 145,
  "tickers_failed": 5,
  "rows_persisted": 725,
  "duration_seconds": 32.5,
  "failed_tickers": ["ERIC.ST", "ABB.ST", "SAND.ST", "KINV-B.ST", "LIFCO-B.ST"]
}
```

**Why structured:**
- Easy to aggregate: "How many tickers failed yesterday?"
- Alert on thresholds: "If tickers_failed > 10, send alert"
- Trend analysis: "Is fetch duration increasing?"

---

## Swedish Market Calendar

### Market Holidays

**Problem:** yfinance may return no data for Swedish holidays (Midsummer, etc.)

**Solution:** Track expected trading days, don't fail scan if no new data.

### Trading Days Check

```python
import pandas_market_calendars as mcal

def is_trading_day(date: date) -> bool:
    """Check if date is a trading day on OMX Stockholm."""
    
    # Use pandas_market_calendars (supports Stockholm exchange)
    omx_calendar = mcal.get_calendar('XSTO')  # OMX Stockholm
    
    # Get trading days in range
    trading_days = omx_calendar.valid_days(
        start_date=date.isoformat(),
        end_date=date.isoformat(),
    )
    
    return len(trading_days) > 0
```

**Usage:**
```python
from datetime import date

scan_date = date.today()

if not is_trading_day(scan_date):
    logger.info(f"{scan_date} is not a trading day, skipping scan")
    sys.exit(0)  # Exit successfully (not an error)
```

**Phase 1 decision:** Skip calendar check (run scan every day, fail gracefully if no new data)

**Phase 2 improvement:** Add calendar check to avoid unnecessary scans.

---

## Testing Strategy

### Unit Tests

```python
# tests/test_fetcher.py
import pytest
import pandas as pd
from scanner.fetcher import validate_price_data, clean_price_data

def test_validate_price_data_valid():
    """Test validation passes for valid data."""
    df = pd.DataFrame({
        'Open': [100, 102],
        'High': [105, 107],
        'Low': [99, 101],
        'Close': [103, 106],
        'Volume': [1000000, 1200000],
    })
    
    result = validate_price_data(df, "TEST.ST")
    assert result.is_valid
    assert len(result.issues) == 0

def test_clean_price_data_removes_invalid():
    """Test cleaning removes invalid rows."""
    df = pd.DataFrame({
        'Open': [100, 102, 105],
        'High': [105, 107, 103],  # Row 2: High < Low (invalid)
        'Low': [99, 101, 104],
        'Close': [103, 106, 102],
        'Volume': [1000000, 1200000, -100],  # Row 2: Negative volume
    })
    
    cleaned = clean_price_data(df, "TEST.ST")
    
    assert len(cleaned) == 1  # Only row 0 valid
    assert cleaned.iloc[0]['Close'] == 103
```

### Integration Test (Against yfinance)

```python
def test_fetch_ticker_live():
    """Integration test: fetch real data from yfinance."""
    from datetime import date, timedelta
    import yfinance as yf
    
    ticker = "ERIC.ST"
    end_date = date.today()
    start_date = end_date - timedelta(days=10)
    
    df = yf.Ticker(ticker).history(start=start_date, end=end_date)
    
    # Basic assertions
    assert not df.empty
    assert 'Close' in df.columns
    assert len(df) > 0
```

**Note:** Integration test depends on Yahoo Finance availability (may fail if service down).

---

## Summary

### Key Decisions

1. **Sequential fetching with delay** — simple, avoids rate limits
2. **Fetch last 5 days for daily scans** — fills gaps from weekends
3. **Validate then clean** — log issues, drop invalid rows
4. **Idempotent persistence** — upsert with deterministic IDs
5. **Graceful failures** — one ticker fails, others continue
6. **Structured logging** — track success/failure rates, durations
7. **No calendar check (Phase 1)** — run daily, gracefully handle no-data days

### What This Enables

- **Reliable data pipeline:** Handles missing data, validation errors, network failures
- **Observable:** Clear logs show what succeeded/failed
- **Idempotent:** Re-run scan, no duplicates
- **Testable:** Unit tests for validation/cleaning, integration tests for yfinance

### Next Steps

1. **Build indicator engine** → [22-indicator-engine-implementation.md](22-indicator-engine-implementation.md)
2. **Implement signal generation** → [23-signal-engine-implementation.md](23-signal-engine-implementation.md)
3. **Test end-to-end locally** → [25-local-development-workflow.md](25-local-development-workflow.md)

---

## References

- [yfinance documentation](https://github.com/ranaroussi/yfinance)
- [pandas-market-calendars](https://github.com/rsheftel/pandas_market_calendars) — Trading calendar library
- [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md) — yfinance research
- [05-data-pipeline-and-quality.md](05-data-pipeline-and-quality.md) — Pipeline design
- [16-omx-ticker-list-management.md](16-omx-ticker-list-management.md) — Ticker universe
- [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md) — Cosmos persistence
