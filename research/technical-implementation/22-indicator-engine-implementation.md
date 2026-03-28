# 22 - Indicator Engine Implementation

> Research date: 2026-03-10
> Goal: Define the architecture for calculating technical indicators (RSI, MACD, Bollinger Bands, moving averages, ATR, volume) using pandas-ta, handling edge cases (insufficient history, NaN values), and persisting snapshots to Cosmos DB indicators container.
> Prerequisites: [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md), [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md), [21-market-data-ingestion-implementation.md](21-market-data-ingestion-implementation.md)

## Table of Contents

1. [Overview](#overview)
2. [Indicator Selection](#indicator-selection)
3. [pandas-ta Integration](#pandas-ta-integration)
4. [Calculation Strategy](#calculation-strategy)
5. [Edge Case Handling](#edge-case-handling)
6. [Indicator Snapshot Schema](#indicator-snapshot-schema)
7. [Cosmos Persistence](#cosmos-persistence)
8. [Performance Optimization](#performance-optimization)
9. [Testing Strategy](#testing-strategy)
10. [Future Extensibility](#future-extensibility)

---

## Overview

The indicator engine calculates **technical indicators** from OHLCV price data and persists snapshots for use by the signal engine. Key responsibilities:

1. **Load price history** from Cosmos daily_prices container
2. **Calculate indicators** using pandas-ta library
3. **Handle edge cases** — insufficient history, NaN values, invalid data
4. **Persist snapshots** to Cosmos indicators container (one doc per ticker per day)
5. **Log calculation metadata** — success/failure, tickers skipped, duration

**Design principles:**
- **Calculate once, use many times:** Indicators persisted for all strategies to use
- **Fail gracefully:** Skip tickers with insufficient history (don't fail entire scan)
- **Explicit schema:** Store indicators as dict (not raw pandas columns)
- **Observable:** Log which tickers skipped and why

---

## Indicator Selection

### Phase 1 Indicator Set

Based on [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md) and signal engine requirements:

| Indicator | Parameters | Purpose | Minimum History |
|-----------|------------|---------|-----------------|
| RSI (Relative Strength Index) | Period=14 | Overbought/oversold detection | 14 days |
| MACD (Moving Average Convergence Divergence) | Fast=12, Slow=26, Signal=9 | Momentum and trend | 26 days |
| Bollinger Bands | Period=20, StdDev=2 | Volatility and mean reversion | 20 days |
| SMA (Simple Moving Average) | Period=50, 200 | Trend identification | 50 / 200 days |
| EMA (Exponential Moving Average) | Period=20 | Short-term trend | 20 days |
| ATR (Average True Range) | Period=14 | Volatility for position sizing | 14 days |
| Volume SMA | Period=20 | Volume comparison | 20 days |

**Rationale:**
- **RSI:** Mean reversion strategy (buy when RSI < 30)
- **MACD:** Crossover strategy (buy on MACD crossover above signal)
- **Bollinger Bands:** Breakout and mean reversion (buy at lower band, sell at upper)
- **SMA 50/200:** Trend filter (only long if price > SMA 200)
- **ATR:** Position sizing (risk 1% per ATR)
- **Volume:** Confirm breakouts (volume > 20-day average)

### Minimum History Requirement

**Decision:** Require **200 days** of history minimum (for SMA 200).

**Handling:**
- If ticker has < 200 days: Skip indicator calculation, log warning
- Scanner continues with other tickers (don't fail entire scan)

---

## pandas-ta Integration

### pandas-ta Basics

**pandas-ta** is a Pandas extension that adds indicator methods to DataFrames.

```python
import pandas as pd
import pandas_ta as ta

# Example: Calculate RSI on a price DataFrame
df['RSI_14'] = ta.rsi(df['Close'], length=14)

# Example: Calculate MACD
macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
df = pd.concat([df, macd], axis=1)  # Adds MACD, MACDh, MACDs columns
```

**pandas-ta features:**
- 130+ indicators built-in
- Clean API (functions or DataFrame methods)
- Handles NaN automatically (returns NaN for insufficient history)

### Installation

```bash
pip install pandas-ta
```

**requirements.txt:**
```
pandas-ta==0.3.14b
pandas>=2.0.0
numpy>=1.24.0
```

---

## Calculation Strategy

### Indicator Calculation Flow

```
For each ticker:
    1. Load price history from Cosmos (last 250 days)
    2. Check if sufficient history (>= 200 days)
    3. Calculate all indicators using pandas-ta
    4. Extract latest indicator values (most recent date)
    5. Persist indicator snapshot to Cosmos
```

**Why calculate on full history:**
- Indicators need lookback (RSI needs 14 days, SMA 200 needs 200 days)
- Calculate on full history, extract latest values for persistence

**Why persist only latest:**
- Signal engine only needs today's indicators
- Historical indicators not needed (can recalculate if needed)
- Reduces storage (1 doc per ticker per day, not 200)

### IndicatorEngine Implementation

```python
import pandas as pd
import pandas_ta as ta
import logging
from datetime import date, timedelta
from scanner.repository import CosmosRepository

logger = logging.getLogger(__name__)

class IndicatorEngine:
    """Calculates technical indicators from price data."""
    
    def __init__(self, repository: CosmosRepository):
        self.repository = repository
    
    def calculate_indicators_for_ticker(self, ticker: str, calc_date: date) -> bool:
        """Calculate indicators for a single ticker.
        
        Returns True if successful, False if skipped.
        """
        
        # Load price history (last 250 days)
        start_date = calc_date - timedelta(days=250)
        prices = self.repository.daily_prices.get_price_history(
            ticker=ticker,
            start_date=start_date,
            end_date=calc_date,
        )
        
        if not prices:
            logger.warning(f"No price data for {ticker}, skipping indicators")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(prices)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Check sufficient history
        if len(df) < 200:
            logger.warning(f"{ticker} has only {len(df)} days of history (need 200), skipping")
            return False
        
        # Calculate indicators
        indicators = self._calculate_all_indicators(df)
        
        # Extract latest values (most recent date)
        latest_indicators = self._extract_latest(indicators)
        
        # Persist to Cosmos
        self.repository.indicators.upsert_indicators(
            ticker=ticker,
            date=calc_date,
            indicators=latest_indicators,
        )
        
        logger.debug(f"Calculated indicators for {ticker}: {list(latest_indicators.keys())}")
        return True
    
    def _calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators on price DataFrame."""
        
        # RSI
        df['RSI_14'] = ta.rsi(df['close'], length=14)
        
        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        # Bollinger Bands
        bbands = ta.bbands(df['close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        
        # SMAs
        df['SMA_50'] = ta.sma(df['close'], length=50)
        df['SMA_200'] = ta.sma(df['close'], length=200)
        
        # EMA
        df['EMA_20'] = ta.ema(df['close'], length=20)
        
        # ATR
        df['ATR_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Volume SMA
        df['Volume_SMA_20'] = ta.sma(df['volume'], length=20)
        
        return df
    
    def _extract_latest(self, df: pd.DataFrame) -> dict:
        """Extract latest indicator values as dictionary."""
        
        latest_row = df.iloc[-1]  # Most recent date
        
        indicators = {
            'rsi_14': self._safe_float(latest_row.get('RSI_14')),
            'macd': self._safe_float(latest_row.get('MACD_12_26_9')),
            'macd_signal': self._safe_float(latest_row.get('MACDs_12_26_9')),
            'macd_histogram': self._safe_float(latest_row.get('MACDh_12_26_9')),
            'bb_upper': self._safe_float(latest_row.get('BBU_20_2.0')),
            'bb_middle': self._safe_float(latest_row.get('BBM_20_2.0')),
            'bb_lower': self._safe_float(latest_row.get('BBL_20_2.0')),
            'bb_bandwidth': self._safe_float(latest_row.get('BBB_20_2.0')),
            'sma_50': self._safe_float(latest_row.get('SMA_50')),
            'sma_200': self._safe_float(latest_row.get('SMA_200')),
            'ema_20': self._safe_float(latest_row.get('EMA_20')),
            'atr_14': self._safe_float(latest_row.get('ATR_14')),
            'volume_sma_20': self._safe_float(latest_row.get('Volume_SMA_20')),
            'close': self._safe_float(latest_row.get('close')),
            'volume': self._safe_float(latest_row.get('volume')),
        }
        
        return indicators
    
    def _safe_float(self, value) -> float | None:
        """Convert value to float, return None if NaN or invalid."""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
```

---

## Edge Case Handling

### Case 1: Insufficient History

**Problem:** Newly listed stocks have < 200 days of data.

**Solution:** Skip indicator calculation, log warning.

```python
if len(df) < 200:
    logger.warning(f"{ticker} has only {len(df)} days of history (need 200), skipping")
    return False
```

**Phase 2 improvement:** Calculate indicators with available history (fallback to shorter SMAs).

---

### Case 2: NaN in Indicator Values

**Problem:** pandas-ta returns NaN for early rows (e.g., RSI undefined for first 14 days).

**Solution:** Extract latest value (which should be valid if sufficient history).

```python
latest_row = df.iloc[-1]  # Most recent date
rsi = latest_row.get('RSI_14')

if pd.isna(rsi):
    logger.warning(f"{ticker} has NaN RSI (unexpected)")
```

**Handling in persistence:**
Store None for NaN indicators (don't fail, signal engine checks for None).

---

### Case 3: Data Quality Issues

**Problem:** Corrupted price data (e.g., sudden spike) causes invalid indicators.

**Solution:** Validate indicator reasonableness (basic sanity checks).

```python
def validate_indicators(indicators: dict) -> bool:
    """Basic sanity checks on calculated indicators."""
    
    # RSI should be in [0, 100]
    rsi = indicators.get('rsi_14')
    if rsi is not None and (rsi < 0 or rsi > 100):
        logger.warning(f"Invalid RSI: {rsi} (expected [0, 100])")
        return False
    
    # ATR should be positive
    atr = indicators.get('atr_14')
    if atr is not None and atr <= 0:
        logger.warning(f"Invalid ATR: {atr} (expected > 0)")
        return False
    
    return True
```

**Phase 1 decision:** Skip validation (trust pandas-ta output, rely on data cleaning).

---

## Indicator Snapshot Schema

### Snapshot Document Structure

From [13-data-model-design.md](13-data-model-design.md):

```json
{
  "id": "ERIC.ST_2026-03-10",
  "ticker": "ERIC.ST",
  "date": "2026-03-10",
  "indicators": {
    "rsi_14": 45.2,
    "macd": -0.15,
    "macd_signal": -0.12,
    "macd_histogram": -0.03,
    "bb_upper": 105.5,
    "bb_middle": 100.0,
    "bb_lower": 94.5,
    "bb_bandwidth": 0.11,
    "sma_50": 98.3,
    "sma_200": 95.1,
    "ema_20": 101.2,
    "atr_14": 2.5,
    "volume_sma_20": 1200000,
    "close": 100.5,
    "volume": 1500000
  },
  "calculated_at": "2026-03-10T14:35:00Z"
}
```

**Design rationale:**

1. **Flat indicator dict:** Easy to access (no nested objects)
2. **Include close and volume:** For context (avoid extra query)
3. **Explicit names:** `rsi_14` not `RSI` (clear which parameters used)
4. **Nullable fields:** None for NaN indicators (signal engine checks)

---

## Cosmos Persistence

### Persistence Pattern

```python
# In IndicatorEngine
self.repository.indicators.upsert_indicators(
    ticker=ticker,
    date=calc_date,
    indicators=latest_indicators,
)
```

**From [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md):**

```python
class IndicatorsRepository(BaseRepository):
    def upsert_indicators(self, ticker: str, date: date, indicators: dict):
        doc_id = generate_indicator_id(ticker, date)  # "ERIC.ST_2026-03-10"
        document = {
            "id": doc_id,
            "ticker": ticker,
            "date": date.isoformat(),
            "indicators": indicators,
            "calculated_at": datetime.utcnow().isoformat(),
        }
        return self.upsert(document)
```

**Idempotency:**
- Same ticker + date → same doc ID
- Re-run indicator calculation → replaces existing snapshot
- No duplicates

---

## Performance Optimization

### Calculation Performance

**Single ticker calculation:**
- Load 250 days of prices: ~1 RU (single-partition query)
- Calculate indicators: ~50ms CPU (pandas-ta vectorized operations)
- Persist snapshot: ~5 RU

**Full scan (150 tickers):**
- Total time: 150 tickers × 50ms = 7.5 seconds (CPU-bound)
- Total RU: 150 × (1 load + 5 upsert) = 900 RU

**Bottleneck:** CPU (pandas-ta calculations), not Cosmos.

### Optimization Strategies

**Phase 1:** Sequential calculation (simple, sufficient).

**Phase 2 considerations:**

1. **Parallel calculation:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(engine.calculate_indicators_for_ticker, ticker, calc_date) 
               for ticker in tickers]
    results = [f.result() for f in futures]
```

**Trade-off:** 4× faster, but higher Cosmos RU consumption (parallel upserts).

2. **Caching price data:**
- Load all tickers' prices in one query (cross-partition)
- Cache in memory, avoid repeated Cosmos queries
- More complex code, marginal benefit (load is already fast)

**Recommendation:** Stick with sequential for Phase 1 (7.5s is acceptable).

---

## Testing Strategy

### Unit Tests

```python
# tests/test_indicator_engine.py
import pytest
import pandas as pd
from scanner.indicators import IndicatorEngine

def test_calculate_indicators_rsi():
    """Test RSI calculation."""
    # Create sample price data
    prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]
    df = pd.DataFrame({'close': prices})
    
    # Calculate RSI
    rsi = ta.rsi(df['close'], length=14)
    
    # Verify RSI in valid range
    assert rsi.iloc[-1] >= 0
    assert rsi.iloc[-1] <= 100

def test_extract_latest():
    """Test extracting latest indicator values."""
    df = pd.DataFrame({
        'RSI_14': [45.2, 46.1, 47.3],
        'close': [100, 101, 102],
    })
    
    engine = IndicatorEngine(mock_repository)
    latest = engine._extract_latest(df)
    
    assert latest['rsi_14'] == 47.3
    assert latest['close'] == 102

def test_safe_float_handles_nan():
    """Test NaN converted to None."""
    engine = IndicatorEngine(mock_repository)
    
    assert engine._safe_float(42.5) == 42.5
    assert engine._safe_float(pd.NA) is None
    assert engine._safe_float(float('nan')) is None
```

### Integration Test

```python
def test_calculate_indicators_integration(repository):
    """Integration test: calculate indicators on real data."""
    from datetime import date, timedelta
    
    # Setup: Insert 250 days of mock price data
    ticker = "TEST.ST"
    for i in range(250):
        calc_date = date.today() - timedelta(days=250-i)
        repository.daily_prices.upsert_price(
            ticker=ticker,
            date=calc_date,
            open=100 + i*0.1,
            high=105 + i*0.1,
            low=95 + i*0.1,
            close=100 + i*0.1,
            volume=1000000,
        )
    
    # Execute
    engine = IndicatorEngine(repository)
    success = engine.calculate_indicators_for_ticker(ticker, date.today())
    
    # Verify
    assert success
    
    # Check persisted indicators
    indicators_doc = repository.indicators.get_indicators(ticker, date.today())
    assert indicators_doc is not None
    assert 'rsi_14' in indicators_doc['indicators']
    assert indicators_doc['indicators']['rsi_14'] is not None
```

---

## Future Extensibility

### Adding New Indicators

**Process:**
1. Add pandas-ta calculation in `_calculate_all_indicators()`
2. Add extraction in `_extract_latest()` with clear name
3. Update indicator snapshot schema documentation
4. No changes to repository (dict schema is flexible)

**Example: Add VWAP (Volume Weighted Average Price):**

```python
def _calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
    # Existing indicators...
    
    # Add VWAP
    df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
    
    return df

def _extract_latest(self, df: pd.DataFrame) -> dict:
    latest_row = df.iloc[-1]
    
    indicators = {
        # Existing indicators...
        'vwap': self._safe_float(latest_row.get('VWAP')),
    }
    
    return indicators
```

**No breaking changes:** Existing signals continue working (ignore new indicator).

---

## Summary

### Key Decisions

1. **pandas-ta for indicator calculations** — 130+ indicators, clean API
2. **Require 200 days minimum history** — skip tickers with insufficient data
3. **Calculate on full history, persist latest** — reduces storage, sufficient for Phase 1
4. **Store indicators as dict** — flexible schema, easy to extend
5. **Handle NaN gracefully** — store None, signal engine checks
6. **Sequential calculation** — simple, sufficient performance (7.5s for 150 tickers)

### What This Enables

- **Consistent indicators across strategies:** Calculate once, use many times
- **Observable:** Log tickers skipped, indicators calculated
- **Idempotent:** Re-run indicator calculation, no duplicates
- **Extensible:** Add new indicators without schema changes

### Next Steps

1. **Build signal engine** → [23-signal-engine-implementation.md](23-signal-engine-implementation.md)
2. **Implement Telegram notifications** → [24-telegram-notification-implementation.md](24-telegram-notification-implementation.md)
3. **Test end-to-end locally** → [25-local-development-workflow.md](25-local-development-workflow.md)

---

## References

- [pandas-ta documentation](https://github.com/twopirllc/pandas-ta)
- [pandas-ta indicators list](https://github.com/twopirllc/pandas-ta/blob/main/pandas_ta/INDICATORS.md)
- [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md) — pandas-ta research
- [13-data-model-design.md](13-data-model-design.md) — indicators container schema
- [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md) — Cosmos persistence
- [21-market-data-ingestion-implementation.md](21-market-data-ingestion-implementation.md) — Price data source
