# Data Pipeline & Data Quality for SwingTrader

> Research date: 2026-03-08
> Goal: Design a reliable pipeline for fetching, cleaning, storing, and maintaining daily market data for ~150 Swedish stocks using yfinance + SQLite.

---

## Table of Contents

1. [Data Pipeline Overview](#1-data-pipeline-overview)
2. [Fetching Data with yfinance](#2-fetching-data-with-yfinance)
3. [Data Quality Problems](#3-data-quality-problems)
4. [Data Cleaning Pipeline](#4-data-cleaning-pipeline)
5. [SQLite Schema and Storage](#5-sqlite-schema-and-storage)
6. [Incremental Updates vs Full Refresh](#6-incremental-updates-vs-full-refresh)
7. [Swedish Market Calendar](#7-swedish-market-calendar)
8. [Dividend and Split Handling](#8-dividend-and-split-handling)
9. [Data Freshness and Timing](#9-data-freshness-and-timing)
10. [Monitoring and Alerts](#10-monitoring-and-alerts)
11. [Complete Data Pipeline Code](#11-complete-data-pipeline-code)

---

## 1. Data Pipeline Overview

### The Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│   FETCH     │───▶│   VALIDATE   │───▶│    CLEAN     │───▶│    STORE     │───▶│    SERVE     │
│  (yfinance) │    │  (structure) │    │  (quality)   │    │  (SQLite)   │    │ (signal eng) │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
       │                  │                  │                  │                    │
   Download          Check for:         Remove bad         Insert/update       Query by ticker
   OHLCV data        - Empty frames     rows, fix          with upsert         and date range
   from Yahoo        - Missing cols     NaNs, flag         logic               for indicators
                     - Date sanity      suspicious                              and strategy
                                        moves
```

### What Data We Need

| Data Field | Purpose | Source |
|---|---|---|
| **Open** | Candlestick patterns, gap analysis | yfinance |
| **High** | Support/resistance, range analysis | yfinance |
| **Low** | Support/resistance, range analysis | yfinance |
| **Close** | Most indicators use close price | yfinance |
| **Adj Close** | Accurate returns after splits/dividends | yfinance |
| **Volume** | Volume confirmation of breakouts | yfinance |
| **Dividends** | Explain ex-dividend price drops | yfinance |
| **Splits** | Detect and verify price adjustments | yfinance |

For swing trading on Swedish stocks, **daily OHLCV + adjusted close** is the core dataset. Dividends and splits are secondary but important for understanding price jumps and ensuring indicator accuracy.

---

## 2. Fetching Data with yfinance

### How yfinance Works for Swedish Stocks

Swedish stocks on Nasdaq Stockholm use the `.ST` suffix in Yahoo Finance:

```python
import yfinance as yf

# Single stock
volvo = yf.download("VOLV-B.ST", start="2024-01-01")

# Multiple stocks at once — much faster
tickers = ["VOLV-B.ST", "SEB-A.ST", "ERIC-B.ST", "ASSA-B.ST"]
data = yf.download(tickers, start="2024-01-01", group_by="ticker")
```

**Key behaviors:**
- `.ST` suffix maps to Nasdaq Stockholm (OMX)
- Tickers with share classes use a hyphen: `VOLV-B.ST`, `SEB-A.ST`
- Some tickers have changed over the years — always verify against a current list
- yfinance returns a pandas DataFrame with a DatetimeIndex

### Batch Downloading vs Individual Tickers

**Batch is preferred** for daily scans:

```python
# GOOD: One network call, Yahoo handles batching internally
# Downloads all tickers in parallel behind the scenes
data = yf.download(
    tickers=["VOLV-B.ST", "SEB-A.ST", "ERIC-B.ST"],
    start="2024-01-01",
    end="2026-03-08",
    group_by="ticker",
    threads=True  # default, uses concurrent downloads
)

# SLOWER: One network call per ticker
for ticker in tickers:
    data = yf.download(ticker, start="2024-01-01")
```

However, **batch downloads hide individual failures**. If one ticker fails in a batch, yfinance may silently skip it or return NaN columns. For production use, a hybrid approach works best:

1. Try batch download first (fast path)
2. Check which tickers actually returned data
3. Retry missing tickers individually (fallback)

### Rate Limiting and Error Handling

yfinance does not have a formal rate limit, but Yahoo Finance will throttle or block aggressive usage:

- **Safe threshold:** ~2,000 requests per hour from a single IP
- **For 150 stocks daily:** Well within limits, even with retries
- **If blocked:** You get HTTP 429 errors or empty responses. Wait and retry.

### Robust Data Fetcher with Retry Logic

```python
import yfinance as yf
import pandas as pd
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_ticker_data(
    ticker: str,
    start: str,
    end: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a single ticker with retry logic.

    Returns a DataFrame with columns: Open, High, Low, Close, Adj Close, Volume
    Returns None if all retries fail.
    """
    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                auto_adjust=False,  # keep both Close and Adj Close
            )

            if df.empty:
                logger.warning(
                    f"{ticker}: empty response (attempt {attempt}/{max_retries})"
                )
                time.sleep(retry_delay * attempt)
                continue

            # yfinance sometimes returns MultiIndex columns for single tickers
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Basic sanity: must have at least these columns
            required = {"Open", "High", "Low", "Close", "Volume"}
            if not required.issubset(set(df.columns)):
                logger.warning(
                    f"{ticker}: missing columns {required - set(df.columns)}"
                )
                time.sleep(retry_delay * attempt)
                continue

            logger.info(f"{ticker}: fetched {len(df)} rows")
            return df

        except Exception as e:
            logger.error(
                f"{ticker}: error on attempt {attempt}/{max_retries}: {e}"
            )
            time.sleep(retry_delay * attempt)

    logger.error(f"{ticker}: all {max_retries} retries failed")
    return None


def fetch_batch(
    tickers: list[str],
    start: str,
    end: Optional[str] = None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch data for multiple tickers. Uses batch download with individual
    fallback for any that fail.
    """
    results = {}

    # Step 1: try batch download
    try:
        batch_data = yf.download(
            tickers,
            start=start,
            end=end,
            group_by="ticker",
            progress=False,
            auto_adjust=False,
            threads=True,
        )
    except Exception as e:
        logger.error(f"Batch download failed: {e}")
        batch_data = pd.DataFrame()

    # Step 2: extract individual ticker DataFrames from batch result
    for ticker in tickers:
        try:
            if not batch_data.empty and ticker in batch_data.columns.get_level_values(0):
                df = batch_data[ticker].dropna(how="all")
                if not df.empty and len(df) > 0:
                    results[ticker] = df
                    continue
        except (KeyError, TypeError):
            pass

        # Step 3: fallback to individual download
        logger.info(f"{ticker}: not in batch result, trying individual fetch")
        df = fetch_ticker_data(ticker, start=start, end=end)
        if df is not None:
            results[ticker] = df

    succeeded = len(results)
    failed = len(tickers) - succeeded
    logger.info(
        f"Batch fetch complete: {succeeded} succeeded, {failed} failed "
        f"out of {len(tickers)} tickers"
    )
    return results
```

### Known yfinance Issues

| Issue | Symptom | Mitigation |
|---|---|---|
| **Silent failures** | Returns empty DataFrame, no error raised | Always check `df.empty` after download |
| **Stale data** | Last row is from yesterday even though market closed today | Verify the max date in returned data matches expected trading day |
| **Bad OHLC values** | High < Low, or negative prices | OHLC consistency check in cleaning step |
| **Missing days** | Gaps in the date index that are not holidays | Compare against market calendar |
| **API changes** | Yahoo changes endpoints, library breaks temporarily | Pin yfinance version, monitor releases |
| **Adj Close divergence** | Adj Close suddenly recalculated by Yahoo retroactively | Periodic full refresh catches this |

---

## 3. Data Quality Problems

### Missing Trading Days (Holidays)

Swedish stocks do not trade on weekends or public holidays. Gaps in the data for these days are **expected and correct**. The problem is when a trading day is missing — this indicates a fetch failure or data issue.

To detect missing trading days, compare the data against a Swedish market calendar (see [Section 7](#7-swedish-market-calendar)).

### Zero Volume Days

Some thinly traded Swedish stocks may have genuine zero-volume days (no trades occurred). However, zero volume combined with unchanged OHLC often indicates bad data.

**Rule of thumb:**
- If a stock consistently has volume > 0 and then shows volume = 0 for one day → likely bad data, exclude that row
- If a small-cap stock regularly shows zero volume → the stock is too illiquid for swing trading and should be excluded from the universe

### Stock Splits and Adjusted Prices

yfinance handles splits in the **Adj Close** column, but the raw Close column shows pre-split prices. This is important:

```
Example: Stock splits 2:1 on 2025-06-01
- 2025-05-31: Close = 200 SEK, Adj Close = 100 SEK
- 2025-06-02: Close = 100 SEK, Adj Close = 100 SEK
```

If you calculate a 50-day moving average using raw Close, you get a massive artificial drop at the split date. **Always use Adj Close for indicator calculations.**

### Corporate Actions

Swedish stocks are subject to:
- **Name changes:** Ticker changes (e.g., when a company rebrands). yfinance treats the new ticker as a new entity — historical data may not carry over.
- **Mergers:** Acquired company delists. yfinance stops returning data.
- **Delistings:** Stock removed from exchange. Historical data may still be available but stops updating.
- **Spin-offs:** New ticker appears, parent company price drops. Both need to be tracked.

**Practical approach:** Maintain a list of active tickers and review it quarterly. Remove delisted stocks. Add new listings if they meet your criteria.

### yfinance Returning NaN or Wrong Data

NaN values appear for various reasons:
- The stock was not yet listed on that date
- A data gap at Yahoo's source
- A temporary API issue during download

**Detection:**
```python
# Check for NaN in critical columns
nan_rows = df[df[["Open", "High", "Low", "Close", "Volume"]].isna().any(axis=1)]
if not nan_rows.empty:
    logger.warning(f"Found {len(nan_rows)} rows with NaN values")
```

### Price Spikes and Errors

Occasionally, yfinance returns obviously wrong prices — a stock that trades at 100 SEK suddenly shows 1,000 SEK or 0.10 SEK for one day, then returns to normal. These are data errors, not real moves.

**Detection heuristic:** Flag any single-day price change > 20% and then a reversal the next day. Real 20%+ moves exist (earnings surprises, takeover bids) but a spike followed by immediate reversal is almost always bad data.

### Swedish Stock Specifics

- **Ex-dividend drops:** Swedish companies often pay large annual dividends (3-6% of stock price). On the ex-dividend date, the stock drops by approximately the dividend amount. This is a **real price move**, not bad data. The Adj Close column accounts for this, but raw Close shows the drop.
- **Dual share classes:** Many Swedish companies have A and B shares (e.g., `VOLV-A.ST` and `VOLV-B.ST`). The B shares are typically more liquid and should be preferred for trading.
- **SEK currency:** All prices are in Swedish kronor. No currency conversion needed if you trade on the Stockholm exchange.

---

## 4. Data Cleaning Pipeline

```python
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def clean_ohlcv(
    df: pd.DataFrame,
    ticker: str,
    max_daily_change_pct: float = 25.0,
) -> pd.DataFrame:
    """
    Clean and validate OHLCV data for a single ticker.

    Steps:
    1. Remove rows where volume is zero (likely bad data for liquid stocks)
    2. Handle NaN values
    3. Verify OHLC consistency
    4. Flag suspicious price moves
    5. Sort by date and remove duplicates

    Returns cleaned DataFrame with an added 'flag' column for suspicious rows.
    """
    if df.empty:
        return df

    original_len = len(df)
    df = df.copy()

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Remove duplicate dates (keep last — most recently fetched)
    df = df[~df.index.duplicated(keep="last")]

    # Sort by date ascending
    df = df.sort_index()

    # Initialize flag column
    df["flag"] = ""

    # ── Step 1: Handle NaN values ──────────────────────────────────────
    nan_mask = df[["Open", "High", "Low", "Close"]].isna().any(axis=1)
    if nan_mask.any():
        nan_count = nan_mask.sum()
        logger.warning(f"{ticker}: dropping {nan_count} rows with NaN OHLC")
        df = df[~nan_mask]

    if df.empty:
        return df

    # ── Step 2: Remove zero-volume rows ────────────────────────────────
    # Exception: keep the row if it is the most recent (today might still
    # be updating and show volume=0 temporarily)
    zero_vol_mask = df["Volume"] == 0
    if zero_vol_mask.any():
        # Keep the last row even if volume is zero
        zero_vol_mask.iloc[-1] = False
        zero_count = zero_vol_mask.sum()
        if zero_count > 0:
            logger.info(f"{ticker}: removing {zero_count} zero-volume rows")
            df = df[~zero_vol_mask]

    if df.empty:
        return df

    # ── Step 3: Verify OHLC consistency ────────────────────────────────
    # High must be >= Open, Close, Low
    # Low must be <= Open, Close, High
    bad_high = df["High"] < df[["Open", "Close", "Low"]].max(axis=1)
    bad_low = df["Low"] > df[["Open", "Close", "High"]].min(axis=1)
    inconsistent = bad_high | bad_low

    if inconsistent.any():
        count = inconsistent.sum()
        logger.warning(f"{ticker}: {count} rows with inconsistent OHLC")
        # Fix by adjusting High/Low to encompass Open and Close
        df.loc[bad_high, "High"] = df.loc[bad_high, ["Open", "Close", "High"]].max(axis=1)
        df.loc[bad_low, "Low"] = df.loc[bad_low, ["Open", "Close", "Low"]].min(axis=1)
        df.loc[inconsistent, "flag"] = "ohlc_fixed"

    # ── Step 4: Detect suspicious price moves ──────────────────────────
    close = df["Close"]
    pct_change = close.pct_change().abs() * 100

    # Flag moves larger than threshold
    suspicious = pct_change > max_daily_change_pct
    if suspicious.any():
        # Check for spike-and-reversal pattern (bad data signature)
        for idx in df.index[suspicious]:
            pos = df.index.get_loc(idx)
            if pos > 0 and pos < len(df) - 1:
                prev_close = df["Close"].iloc[pos - 1]
                curr_close = df["Close"].iloc[pos]
                next_close = df["Close"].iloc[pos + 1]

                # If price spikes and then returns close to the previous level,
                # this is almost certainly bad data
                move_out = abs(curr_close - prev_close) / prev_close
                move_back = abs(next_close - prev_close) / prev_close

                if move_out > 0.20 and move_back < 0.05:
                    logger.warning(
                        f"{ticker}: likely bad data spike on {idx.date()}: "
                        f"{prev_close:.2f} → {curr_close:.2f} → {next_close:.2f}"
                    )
                    df.loc[idx, "flag"] = "spike_removed"
                    # Replace with interpolated values
                    df.loc[idx, "Close"] = (prev_close + next_close) / 2
                    df.loc[idx, "Open"] = df.loc[idx, "Close"]
                    df.loc[idx, "High"] = max(prev_close, next_close)
                    df.loc[idx, "Low"] = min(prev_close, next_close)
                else:
                    # Large move but not a spike-reversal — could be real
                    # (earnings, takeover, ex-dividend, etc.)
                    df.loc[idx, "flag"] = "large_move"
                    logger.info(
                        f"{ticker}: large move on {idx.date()}: "
                        f"{pct_change.loc[idx]:.1f}% (kept, may be real)"
                    )

    # ── Step 5: Negative price check ───────────────────────────────────
    neg_price = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
    if neg_price.any():
        logger.warning(f"{ticker}: removing {neg_price.sum()} rows with negative/zero prices")
        df = df[~neg_price]

    cleaned_len = len(df)
    removed = original_len - cleaned_len
    if removed > 0:
        logger.info(f"{ticker}: cleaned {original_len} → {cleaned_len} rows ({removed} removed)")

    return df
```

### Adjusted vs Unadjusted Prices

**Best practice: store both.**

- Use **Adj Close** for calculating indicators and backtesting returns. This gives you a continuous price series that accounts for splits and dividends.
- Use raw **Close** for displaying current prices and setting stop-loss levels at actual trading prices.
- The difference between Close and Adj Close grows over time as more dividends accumulate.

```python
# Example: Adj Close divergence for a high-dividend stock over 3 years
# VOLV-B.ST might show:
#   Close (today):     280 SEK
#   Adj Close (today): 280 SEK  (same for the most recent day)
#   Close (3yr ago):   180 SEK
#   Adj Close (3yr ago): 155 SEK  (lower because future dividends are "removed")
```

---

## 5. SQLite Schema and Storage

### Database Schema

```sql
-- Core price data table
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker      TEXT    NOT NULL,
    date        TEXT    NOT NULL,  -- ISO format: YYYY-MM-DD
    open        REAL    NOT NULL,
    high        REAL    NOT NULL,
    low         REAL    NOT NULL,
    close       REAL    NOT NULL,
    adj_close   REAL    NOT NULL,
    volume      INTEGER NOT NULL,
    flag        TEXT    DEFAULT '',  -- data quality flags from cleaning
    updated_at  TEXT    NOT NULL,    -- when this row was last fetched/updated

    PRIMARY KEY (ticker, date)
);

-- Index for querying a single ticker's history (most common query)
CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
    ON daily_prices (ticker, date);

-- Index for finding all tickers on a specific date
CREATE INDEX IF NOT EXISTS idx_prices_date
    ON daily_prices (date);

-- Metadata about each ticker
CREATE TABLE IF NOT EXISTS tickers (
    ticker      TEXT    PRIMARY KEY,
    name        TEXT,
    sector      TEXT,
    is_active   INTEGER DEFAULT 1,   -- 1 = actively tracked, 0 = delisted/removed
    added_at    TEXT    NOT NULL,
    last_fetch  TEXT,                 -- last successful fetch date
    notes       TEXT    DEFAULT ''
);

-- Track pipeline runs for monitoring
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date        TEXT    NOT NULL,
    started_at      TEXT    NOT NULL,
    finished_at     TEXT,
    tickers_total   INTEGER,
    tickers_success INTEGER,
    tickers_failed  INTEGER,
    rows_inserted   INTEGER,
    rows_updated    INTEGER,
    status          TEXT    DEFAULT 'running',  -- running, success, failed
    error_message   TEXT
);

-- Store dividend and split events
CREATE TABLE IF NOT EXISTS corporate_actions (
    ticker      TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    action_type TEXT    NOT NULL,  -- 'dividend' or 'split'
    value       REAL    NOT NULL,  -- dividend amount in SEK or split ratio
    PRIMARY KEY (ticker, date, action_type)
);
```

### Why This Schema Works

- **Composite primary key** `(ticker, date)` prevents duplicate entries and enables natural upsert logic
- **`updated_at`** tracks data freshness — useful for debugging stale data issues
- **`flag`** column preserves cleaning annotations so you can audit data quality
- **`pipeline_runs`** table provides a simple audit trail without external monitoring tools
- **`is_active`** flag on tickers lets you soft-delete stocks without losing historical data

### Storage Size Estimate

```
150 tickers × 250 trading days/year × 3 years = 112,500 rows

Each row is approximately:
  ticker (avg 10 chars) + date (10) + 6 floats (48 bytes) + volume (8)
  + flag (avg 5) + updated_at (19) = ~100 bytes per row

112,500 rows × 100 bytes ≈ 11 MB raw data

With indexes and SQLite overhead: ~15-20 MB total

This is trivially small. Even 10 years of data for 500 stocks
would be under 200 MB. Storage is not a constraint.
```

### Data Storage Class

```python
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PriceDatabase:
    """SQLite storage for daily OHLCV price data."""

    def __init__(self, db_path: str = "swingtrader.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # better concurrent read perf
        conn.execute("PRAGMA synchronous=NORMAL")  # faster writes, still safe
        return conn

    def _init_db(self):
        """Create tables and indexes if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                ticker      TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                open        REAL    NOT NULL,
                high        REAL    NOT NULL,
                low         REAL    NOT NULL,
                close       REAL    NOT NULL,
                adj_close   REAL    NOT NULL,
                volume      INTEGER NOT NULL,
                flag        TEXT    DEFAULT '',
                updated_at  TEXT    NOT NULL,
                PRIMARY KEY (ticker, date)
            );

            CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
                ON daily_prices (ticker, date);

            CREATE INDEX IF NOT EXISTS idx_prices_date
                ON daily_prices (date);

            CREATE TABLE IF NOT EXISTS tickers (
                ticker      TEXT PRIMARY KEY,
                name        TEXT,
                sector      TEXT,
                is_active   INTEGER DEFAULT 1,
                added_at    TEXT NOT NULL,
                last_fetch  TEXT,
                notes       TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date        TEXT NOT NULL,
                started_at      TEXT NOT NULL,
                finished_at     TEXT,
                tickers_total   INTEGER,
                tickers_success INTEGER,
                tickers_failed  INTEGER,
                rows_inserted   INTEGER,
                rows_updated    INTEGER,
                status          TEXT DEFAULT 'running',
                error_message   TEXT
            );
        """)
        conn.commit()
        conn.close()

    def upsert_prices(self, ticker: str, df: pd.DataFrame) -> tuple[int, int]:
        """
        Insert or update price data for a ticker.
        Returns (inserted_count, updated_count).
        """
        if df.empty:
            return 0, 0

        conn = self._get_conn()
        now = datetime.utcnow().isoformat()
        inserted = 0
        updated = 0

        for date_idx, row in df.iterrows():
            date_str = date_idx.strftime("%Y-%m-%d")
            flag = row.get("flag", "")

            # Try insert first, update on conflict
            cursor = conn.execute(
                """
                INSERT INTO daily_prices
                    (ticker, date, open, high, low, close, adj_close, volume, flag, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    adj_close = excluded.adj_close,
                    volume = excluded.volume,
                    flag = excluded.flag,
                    updated_at = excluded.updated_at
                """,
                (
                    ticker,
                    date_str,
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    float(row.get("Adj Close", row["Close"])),
                    int(row["Volume"]),
                    str(flag),
                    now,
                ),
            )
            if cursor.rowcount == 1:
                inserted += 1
            else:
                updated += 1

        conn.commit()

        # Update last_fetch for this ticker
        conn.execute(
            "UPDATE tickers SET last_fetch = ? WHERE ticker = ?",
            (now, ticker),
        )
        conn.commit()
        conn.close()

        logger.info(f"{ticker}: upserted {inserted} new, {updated} updated rows")
        return inserted, updated

    def get_prices(
        self,
        ticker: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Query price data for a ticker, optionally filtered by date range.
        Returns a DataFrame indexed by date.
        """
        conn = self._get_conn()
        query = "SELECT * FROM daily_prices WHERE ticker = ?"
        params: list = [ticker]

        if start:
            query += " AND date >= ?"
            params.append(start)
        if end:
            query += " AND date <= ?"
            params.append(end)

        query += " ORDER BY date ASC"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

        return df

    def get_latest_date(self, ticker: str) -> str | None:
        """Get the most recent date we have data for this ticker."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT MAX(date) FROM daily_prices WHERE ticker = ?",
            (ticker,),
        )
        result = cursor.fetchone()[0]
        conn.close()
        return result

    def get_active_tickers(self) -> list[str]:
        """Return all active tickers."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT ticker FROM tickers WHERE is_active = 1 ORDER BY ticker"
        )
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tickers

    def add_ticker(self, ticker: str, name: str = "", sector: str = ""):
        """Add a ticker to the tracked universe."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR IGNORE INTO tickers (ticker, name, sector, added_at)
            VALUES (?, ?, ?, ?)
            """,
            (ticker, name, sector, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
```

---

## 6. Incremental Updates vs Full Refresh

### Strategy

| Frequency | Action | Purpose |
|---|---|---|
| **Daily** (after market close) | Fetch last 5 trading days, upsert | Catch today's data + fill any recent gaps |
| **Weekly** (weekend) | Verify data integrity for past 30 days | Detect and fix any missed data |
| **Monthly** (first weekend) | Full refresh of last 3 months | Catch retroactive adjustments by Yahoo |
| **Quarterly** | Full refresh of all data | Reset adjusted prices after dividend recalculations |

### Why Fetch 5 Days Instead of 1

Fetching only today's data is fragile:
- If the pipeline fails one day, the next run would miss a day
- yfinance sometimes updates yesterday's data retroactively
- Weekend/holiday gaps mean "today" is ambiguous
- Fetching 5 days costs almost nothing extra and provides natural self-healing

### Incremental Update Code

```python
from datetime import datetime, timedelta


def get_fetch_start_date(
    db: PriceDatabase,
    ticker: str,
    lookback_days: int = 7,
    min_history_years: int = 3,
) -> str:
    """
    Determine the start date for fetching data.

    - If we have recent data: fetch from (latest_date - lookback_days)
    - If we have no data or very old data: fetch full history
    """
    latest = db.get_latest_date(ticker)

    if latest is None:
        # No data at all — fetch full history
        start = datetime.now() - timedelta(days=min_history_years * 365)
        return start.strftime("%Y-%m-%d")

    latest_dt = datetime.strptime(latest, "%Y-%m-%d")
    days_stale = (datetime.now() - latest_dt).days

    if days_stale > 90:
        # Data is very stale — do a longer backfill
        start = latest_dt - timedelta(days=30)
    else:
        # Normal incremental update
        start = latest_dt - timedelta(days=lookback_days)

    return start.strftime("%Y-%m-%d")


def run_daily_update(db: PriceDatabase, tickers: list[str]):
    """
    Daily incremental update for all tickers.
    """
    results = {"success": [], "failed": []}

    for ticker in tickers:
        start_date = get_fetch_start_date(db, ticker)
        logger.info(f"{ticker}: fetching from {start_date}")

        df = fetch_ticker_data(ticker, start=start_date)
        if df is None:
            results["failed"].append(ticker)
            continue

        df = clean_ohlcv(df, ticker)
        if df.empty:
            results["failed"].append(ticker)
            continue

        inserted, updated = db.upsert_prices(ticker, df)
        results["success"].append(ticker)

    logger.info(
        f"Daily update complete: {len(results['success'])} success, "
        f"{len(results['failed'])} failed"
    )
    if results["failed"]:
        logger.warning(f"Failed tickers: {results['failed']}")

    return results


def run_monthly_refresh(db: PriceDatabase, tickers: list[str]):
    """
    Monthly full refresh of the last 3 months to catch corrections.
    """
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    for ticker in tickers:
        logger.info(f"{ticker}: monthly refresh from {start}")
        df = fetch_ticker_data(ticker, start=start)
        if df is not None:
            df = clean_ohlcv(df, ticker)
            db.upsert_prices(ticker, df)
```

---

## 7. Swedish Market Calendar

### Nasdaq Stockholm Trading Holidays (2026)

| Date | Holiday |
|---|---|
| January 1 | New Year's Day |
| January 6 | Epiphany |
| April 3 | Good Friday |
| April 6 | Easter Monday |
| May 1 | Labour Day |
| May 14 | Ascension Day |
| June 5 | National Day (observed) |
| June 19 | Midsummer Eve |
| December 24 | Christmas Eve |
| December 25 | Christmas Day |
| December 31 | New Year's Eve |

**Half-days** (market closes at 13:00 CET):
- January 5 (day before Epiphany)
- April 2 (day before Good Friday — Maundy Thursday)
- April 30 (Walpurgis Night / day before May Day)
- May 13 (day before Ascension Day)
- November 30 (if a weekday)
- December 23 (if a weekday)

### Using exchange_calendars

The `exchange_calendars` Python package provides pre-built calendars for most exchanges, including Nasdaq Stockholm:

```python
import exchange_calendars as xcals
from datetime import datetime, date

# Get the Stockholm exchange calendar
# XSTO = Nasdaq Stockholm
cal = xcals.get_calendar("XSTO")


def is_trading_day(check_date: date | None = None) -> bool:
    """Check if a given date is a trading day on Nasdaq Stockholm."""
    if check_date is None:
        check_date = date.today()

    # exchange_calendars uses pandas Timestamp
    import pandas as pd
    ts = pd.Timestamp(check_date)

    return cal.is_session(ts)


def get_last_trading_day(before_date: date | None = None) -> date:
    """Get the most recent trading day on or before the given date."""
    if before_date is None:
        before_date = date.today()

    import pandas as pd
    ts = pd.Timestamp(before_date)

    if cal.is_session(ts):
        return before_date

    prev = cal.previous_session(ts)
    return prev.date()


def get_trading_days(start: str, end: str) -> list[date]:
    """Get all trading days between two dates (inclusive)."""
    import pandas as pd
    sessions = cal.sessions_in_range(
        pd.Timestamp(start),
        pd.Timestamp(end),
    )
    return [s.date() for s in sessions]


# Example usage
if __name__ == "__main__":
    today = date(2026, 3, 8)  # Sunday
    print(f"Is {today} a trading day? {is_trading_day(today)}")
    # False (Sunday)

    last = get_last_trading_day(today)
    print(f"Last trading day before {today}: {last}")
    # 2026-03-06 (Friday)

    days = get_trading_days("2026-03-01", "2026-03-08")
    print(f"Trading days in range: {days}")
    # [2026-03-02, 2026-03-03, 2026-03-04, 2026-03-05, 2026-03-06]
```

**Installation:**
```bash
pip install exchange_calendars
```

---

## 8. Dividend and Split Handling

### Swedish Dividend Patterns

Swedish companies typically pay dividends once a year (some twice), with the majority paying in April-May after the AGM (annual general meeting) season. Dividend yields of 3-6% are common for large caps, meaning a stock priced at 200 SEK might drop 8-10 SEK on the ex-dividend date.

**This is critical for swing trading:** An 8 SEK drop on a 200 SEK stock is a 4% decline that has nothing to do with the company's prospects or technical indicators. If your strategy triggers a sell signal based on this drop, it is reacting to a non-event.

### How yfinance Handles Adjustments

- **Adj Close** is calculated by Yahoo Finance to account for both splits and dividends
- The adjustment is applied retroactively to all historical data
- The most recent day always has `Close == Adj Close`
- Yahoo may recalculate adjusted prices when new dividends are announced, changing historical values

### Best Practice: Store Both Raw and Adjusted

```python
# Store both in the database (our schema already does this)
# Use Adj Close for:
#   - Calculating moving averages, RSI, MACD, etc.
#   - Backtesting returns
#   - Any percentage-based calculation

# Use raw Close for:
#   - Displaying current price to the user
#   - Setting actual stop-loss orders (you trade at real prices)
#   - Comparing to brokerage account values
```

### Detecting Splits in the Data

```python
def detect_splits(df: pd.DataFrame, ticker: str) -> list[dict]:
    """
    Detect likely stock splits by looking for large price changes
    where Adj Close remains continuous but raw Close jumps.

    Returns a list of detected split events.
    """
    splits = []

    if "Close" not in df.columns or "Adj Close" not in df.columns:
        return splits

    close_change = df["Close"].pct_change()
    adj_change = df["Adj Close"].pct_change()

    for i in range(1, len(df)):
        raw_pct = abs(close_change.iloc[i])
        adj_pct = abs(adj_change.iloc[i])

        # A split shows as a large change in raw Close
        # but small change in Adj Close
        if raw_pct > 0.30 and adj_pct < 0.05:
            ratio = df["Close"].iloc[i - 1] / df["Close"].iloc[i]
            # Round to nearest common split ratio
            common_ratios = [2, 3, 4, 5, 10, 0.5, 0.33, 0.25, 0.2, 0.1]
            nearest = min(common_ratios, key=lambda r: abs(r - ratio))

            splits.append({
                "date": df.index[i].strftime("%Y-%m-%d"),
                "ticker": ticker,
                "estimated_ratio": nearest,
                "raw_ratio": round(ratio, 4),
            })
            logger.info(
                f"{ticker}: likely {nearest}:1 split on {df.index[i].date()} "
                f"(raw ratio: {ratio:.4f})"
            )

    return splits
```

### Handling Ex-Dividend Days in Signals

```python
def is_ex_dividend_drop(
    df: pd.DataFrame,
    date_idx: int,
    ticker_info: dict | None = None,
) -> bool:
    """
    Check if a price drop on a given day is likely due to ex-dividend.

    Heuristic: Adj Close barely changed but raw Close dropped significantly.
    """
    if date_idx < 1:
        return False

    raw_change = (df["Close"].iloc[date_idx] - df["Close"].iloc[date_idx - 1]) / df["Close"].iloc[date_idx - 1]
    adj_change = (df["Adj Close"].iloc[date_idx] - df["Adj Close"].iloc[date_idx - 1]) / df["Adj Close"].iloc[date_idx - 1]

    # If raw price dropped 2%+ but adjusted price barely moved,
    # it is almost certainly an ex-dividend drop
    if raw_change < -0.02 and abs(adj_change) < 0.01:
        return True

    return False
```

---

## 9. Data Freshness and Timing

### yfinance Data Delay

yfinance pulls data from Yahoo Finance, which in turn sources from exchange feeds. For Nordic stocks, the typical delay pattern is:

| Time (CET) | Data Availability |
|---|---|
| During trading hours (09:00-17:25) | 15-20 minute delay |
| 17:30 (market close) | Final bar not yet available |
| 17:45-18:00 | End-of-day bar usually appears |
| 18:30+ | End-of-day bar reliably available |
| Next morning | Data is stable and final |

**Recommendation:** Run the daily pipeline at **18:15 CET** or later. Running at exactly 17:30 often returns stale/incomplete data for the final bar.

### Verifying Data Freshness

```python
from datetime import date, datetime


def verify_data_freshness(
    df: pd.DataFrame,
    ticker: str,
    expected_date: date | None = None,
) -> dict:
    """
    Check if the fetched data includes the expected trading day.

    Returns a dict with freshness status and details.
    """
    if expected_date is None:
        expected_date = get_last_trading_day()

    if df.empty:
        return {
            "fresh": False,
            "reason": "empty dataframe",
            "latest_date": None,
            "expected_date": expected_date,
        }

    latest_in_data = df.index.max().date()

    if latest_in_data >= expected_date:
        return {
            "fresh": True,
            "reason": "data includes expected date",
            "latest_date": latest_in_data,
            "expected_date": expected_date,
        }
    else:
        days_behind = (expected_date - latest_in_data).days
        return {
            "fresh": False,
            "reason": f"data is {days_behind} day(s) behind",
            "latest_date": latest_in_data,
            "expected_date": expected_date,
        }
```

### Cron Schedule

```bash
# Run daily at 18:15 CET (17:15 UTC during winter, 16:15 UTC during summer)
# Using CET timezone via TZ environment variable
15 18 * * 1-5 cd /path/to/swingtrader && TZ="Europe/Stockholm" python -m swingtrader.pipeline daily

# Weekly integrity check — Sunday at 10:00
0 10 * * 0 cd /path/to/swingtrader && TZ="Europe/Stockholm" python -m swingtrader.pipeline weekly

# Monthly full refresh — first Sunday of the month at 08:00
0 8 1-7 * 0 cd /path/to/swingtrader && TZ="Europe/Stockholm" python -m swingtrader.pipeline monthly
```

---

## 10. Monitoring and Alerts

### What Can Go Wrong

| Failure Mode | Detection | Severity |
|---|---|---|
| yfinance API is down | All tickers fail to fetch | High — no data for today |
| Single ticker fails | One ticker missing, others OK | Low — retry tomorrow |
| Data is stale | Latest date is not today | Medium — check timing |
| Bad data quality | Unusual number of flagged rows | Medium — investigate |
| Database corruption | SQLite errors on read/write | High — restore from backup |
| Pipeline hangs | Process runs > 30 minutes | High — kill and investigate |

### Simple Monitoring Function

```python
from datetime import datetime, date, timedelta


def run_health_check(db: PriceDatabase) -> dict:
    """
    Run basic health checks on the data pipeline.

    Returns a dict with check results and overall status.
    """
    checks = {}
    overall_ok = True

    tickers = db.get_active_tickers()
    expected_date = get_last_trading_day()
    expected_str = expected_date.strftime("%Y-%m-%d")

    # Check 1: Do we have any data at all?
    conn = db._get_conn()
    cursor = conn.execute("SELECT COUNT(*) FROM daily_prices")
    total_rows = cursor.fetchone()[0]
    checks["total_rows"] = total_rows
    if total_rows == 0:
        checks["has_data"] = False
        overall_ok = False
    else:
        checks["has_data"] = True

    # Check 2: How many tickers have data for the expected date?
    cursor = conn.execute(
        "SELECT COUNT(DISTINCT ticker) FROM daily_prices WHERE date = ?",
        (expected_str,),
    )
    tickers_with_today = cursor.fetchone()[0]
    checks["tickers_with_latest"] = tickers_with_today
    checks["tickers_total"] = len(tickers)
    checks["expected_date"] = expected_str

    coverage_pct = (tickers_with_today / len(tickers) * 100) if tickers else 0
    checks["coverage_pct"] = round(coverage_pct, 1)

    if coverage_pct < 90:
        overall_ok = False
        logger.warning(
            f"Low coverage: only {tickers_with_today}/{len(tickers)} "
            f"tickers have data for {expected_str}"
        )

    # Check 3: Which tickers are missing today's data?
    cursor = conn.execute(
        """
        SELECT t.ticker
        FROM tickers t
        LEFT JOIN daily_prices dp ON t.ticker = dp.ticker AND dp.date = ?
        WHERE t.is_active = 1 AND dp.ticker IS NULL
        """,
        (expected_str,),
    )
    missing = [row[0] for row in cursor.fetchall()]
    checks["missing_tickers"] = missing

    # Check 4: Any tickers with suspiciously old data?
    stale_threshold = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    cursor = conn.execute(
        """
        SELECT ticker, MAX(date) as latest
        FROM daily_prices
        GROUP BY ticker
        HAVING latest < ?
        """,
        (stale_threshold,),
    )
    stale = [(row[0], row[1]) for row in cursor.fetchall()]
    checks["stale_tickers"] = stale
    if stale:
        logger.warning(f"Stale tickers (no data in 5+ days): {stale}")

    # Check 5: Any data quality flags from today?
    cursor = conn.execute(
        "SELECT COUNT(*) FROM daily_prices WHERE date = ? AND flag != ''",
        (expected_str,),
    )
    flagged_today = cursor.fetchone()[0]
    checks["flagged_rows_today"] = flagged_today

    conn.close()

    checks["overall_ok"] = overall_ok
    status = "HEALTHY" if overall_ok else "DEGRADED"
    logger.info(f"Health check: {status} — {checks['coverage_pct']}% coverage for {expected_str}")

    return checks
```

### Logging Best Practices

```python
import logging
from pathlib import Path

def setup_logging(log_dir: str = "logs"):
    """Configure logging for the data pipeline."""
    Path(log_dir).mkdir(exist_ok=True)

    # File handler — detailed logs, rotated daily
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=f"{log_dir}/pipeline.log",
        when="midnight",
        backupCount=30,  # keep 30 days of logs
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    ))

    # Console handler — summary level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

---

## 11. Complete Data Pipeline Code

The following is a complete, runnable pipeline module that ties everything together. It is designed to be called from a cron job or manually from the command line.

```python
#!/usr/bin/env python3
"""
SwingTrader Data Pipeline
=========================
Fetches, cleans, and stores daily OHLCV data for Swedish stocks.

Usage:
    python data_pipeline.py daily     # incremental update (run after market close)
    python data_pipeline.py weekly    # integrity check for past 30 days
    python data_pipeline.py monthly   # full refresh of last 3 months
    python data_pipeline.py init      # initial setup and full history load
    python data_pipeline.py health    # run health checks only
"""

import sys
import time
import sqlite3
import logging
import logging.handlers
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
import yfinance as yf

try:
    import exchange_calendars as xcals
    MARKET_CAL = xcals.get_calendar("XSTO")
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

logger = logging.getLogger("pipeline")

# ── Configuration ──────────────────────────────────────────────────────

DB_PATH = "swingtrader.db"
LOG_DIR = "logs"
HISTORY_YEARS = 3
DAILY_LOOKBACK_DAYS = 7
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Default universe of Swedish large/mid-cap stocks
DEFAULT_TICKERS = [
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-A.ST", "ATCO-B.ST",
    "AZN.ST", "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST",
    "EVO.ST", "GETI-B.ST", "HEXA-B.ST", "HM-B.ST", "HUSQ-B.ST",
    "INVE-B.ST", "KINV-B.ST", "LUND-B.ST", "NIBE-B.ST", "SAND.ST",
    "SBB-B.ST", "SCA-B.ST", "SEB-A.ST", "SHB-A.ST", "SINCH.ST",
    "SKA-B.ST", "SKF-B.ST", "SSAB-A.ST", "SWED-A.ST", "TEL2-B.ST",
    "TELIA.ST", "VOLV-B.ST",
]


# ── Market Calendar ────────────────────────────────────────────────────

def is_trading_day(check_date: Optional[date] = None) -> bool:
    if check_date is None:
        check_date = date.today()
    if HAS_CALENDAR:
        ts = pd.Timestamp(check_date)
        return MARKET_CAL.is_session(ts)
    # Fallback: assume weekdays are trading days
    return check_date.weekday() < 5


def get_last_trading_day(before: Optional[date] = None) -> date:
    if before is None:
        before = date.today()
    if HAS_CALENDAR:
        ts = pd.Timestamp(before)
        if MARKET_CAL.is_session(ts):
            return before
        return MARKET_CAL.previous_session(ts).date()
    # Fallback
    d = before
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


# ── Data Fetching ──────────────────────────────────────────────────────

def fetch_ticker(
    ticker: str, start: str, end: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(
                ticker, start=start, end=end,
                progress=False, auto_adjust=False,
            )
            if df.empty:
                logger.warning(f"{ticker}: empty (attempt {attempt})")
                time.sleep(RETRY_DELAY * attempt)
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            required = {"Open", "High", "Low", "Close", "Volume"}
            if not required.issubset(set(df.columns)):
                logger.warning(f"{ticker}: missing columns")
                time.sleep(RETRY_DELAY * attempt)
                continue
            return df
        except Exception as e:
            logger.error(f"{ticker}: error attempt {attempt}: {e}")
            time.sleep(RETRY_DELAY * attempt)
    logger.error(f"{ticker}: all retries exhausted")
    return None


# ── Data Cleaning ──────────────────────────────────────────────────────

def clean_ohlcv(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df["flag"] = ""

    # Drop rows with NaN in OHLC
    nan_mask = df[["Open", "High", "Low", "Close"]].isna().any(axis=1)
    if nan_mask.any():
        logger.info(f"{ticker}: dropping {nan_mask.sum()} NaN rows")
        df = df[~nan_mask]
    if df.empty:
        return df

    # Remove zero-volume rows (except the latest)
    zero_vol = df["Volume"] == 0
    if zero_vol.any():
        zero_vol.iloc[-1] = False
        if zero_vol.sum() > 0:
            logger.info(f"{ticker}: removing {zero_vol.sum()} zero-volume rows")
            df = df[~zero_vol]
    if df.empty:
        return df

    # Fix OHLC consistency
    bad_h = df["High"] < df[["Open", "Close"]].max(axis=1)
    bad_l = df["Low"] > df[["Open", "Close"]].min(axis=1)
    if bad_h.any():
        df.loc[bad_h, "High"] = df.loc[bad_h, ["Open", "Close", "High"]].max(axis=1)
    if bad_l.any():
        df.loc[bad_l, "Low"] = df.loc[bad_l, ["Open", "Close", "Low"]].min(axis=1)
    if (bad_h | bad_l).any():
        df.loc[bad_h | bad_l, "flag"] = "ohlc_fixed"

    # Flag spike-and-reversal patterns (likely bad data)
    pct = df["Close"].pct_change().abs()
    for i in range(1, len(df) - 1):
        if pct.iloc[i] > 0.25:
            prev, curr, nxt = df["Close"].iloc[i-1], df["Close"].iloc[i], df["Close"].iloc[i+1]
            move_out = abs(curr - prev) / prev
            move_back = abs(nxt - prev) / prev
            if move_out > 0.20 and move_back < 0.05:
                idx = df.index[i]
                logger.warning(f"{ticker}: spike on {idx.date()}, interpolating")
                df.loc[idx, "Close"] = (prev + nxt) / 2
                df.loc[idx, "Open"] = df.loc[idx, "Close"]
                df.loc[idx, "High"] = max(prev, nxt)
                df.loc[idx, "Low"] = min(prev, nxt)
                df.loc[idx, "flag"] = "spike_fixed"

    # Remove negative prices
    neg = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
    if neg.any():
        df = df[~neg]

    return df


# ── Database ───────────────────────────────────────────────────────────

class PriceDB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    def _init(self):
        c = self._conn()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                ticker TEXT NOT NULL, date TEXT NOT NULL,
                open REAL NOT NULL, high REAL NOT NULL,
                low REAL NOT NULL, close REAL NOT NULL,
                adj_close REAL NOT NULL, volume INTEGER NOT NULL,
                flag TEXT DEFAULT '', updated_at TEXT NOT NULL,
                PRIMARY KEY (ticker, date));
            CREATE INDEX IF NOT EXISTS idx_td ON daily_prices(ticker, date);
            CREATE INDEX IF NOT EXISTS idx_d ON daily_prices(date);
            CREATE TABLE IF NOT EXISTS tickers (
                ticker TEXT PRIMARY KEY, name TEXT, sector TEXT,
                is_active INTEGER DEFAULT 1, added_at TEXT NOT NULL,
                last_fetch TEXT, notes TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT, started_at TEXT, finished_at TEXT,
                tickers_total INTEGER, tickers_success INTEGER,
                tickers_failed INTEGER, status TEXT DEFAULT 'running',
                error_message TEXT);
        """)
        c.commit()
        c.close()

    def upsert(self, ticker: str, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        c = self._conn()
        now = datetime.utcnow().isoformat()
        count = 0
        for dt, row in df.iterrows():
            c.execute("""
                INSERT INTO daily_prices
                    (ticker,date,open,high,low,close,adj_close,volume,flag,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(ticker,date) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, adj_close=excluded.adj_close,
                    volume=excluded.volume, flag=excluded.flag,
                    updated_at=excluded.updated_at
            """, (ticker, dt.strftime("%Y-%m-%d"),
                  float(row["Open"]), float(row["High"]),
                  float(row["Low"]), float(row["Close"]),
                  float(row.get("Adj Close", row["Close"])),
                  int(row["Volume"]), str(row.get("flag", "")), now))
            count += 1
        c.execute("UPDATE tickers SET last_fetch=? WHERE ticker=?", (now, ticker))
        c.commit()
        c.close()
        return count

    def get_prices(self, ticker: str, start: str = None, end: str = None) -> pd.DataFrame:
        c = self._conn()
        q = "SELECT * FROM daily_prices WHERE ticker=?"
        p = [ticker]
        if start:
            q += " AND date>=?"
            p.append(start)
        if end:
            q += " AND date<=?"
            p.append(end)
        q += " ORDER BY date"
        df = pd.read_sql_query(q, c, params=p)
        c.close()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        return df

    def latest_date(self, ticker: str) -> Optional[str]:
        c = self._conn()
        r = c.execute(
            "SELECT MAX(date) FROM daily_prices WHERE ticker=?", (ticker,)
        ).fetchone()[0]
        c.close()
        return r

    def active_tickers(self) -> list[str]:
        c = self._conn()
        rows = c.execute(
            "SELECT ticker FROM tickers WHERE is_active=1 ORDER BY ticker"
        ).fetchall()
        c.close()
        return [r[0] for r in rows]

    def add_ticker(self, ticker: str, name: str = ""):
        c = self._conn()
        c.execute(
            "INSERT OR IGNORE INTO tickers(ticker,name,added_at) VALUES(?,?,?)",
            (ticker, name, datetime.utcnow().isoformat()),
        )
        c.commit()
        c.close()

    def log_run(self, **kwargs):
        c = self._conn()
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        c.execute(
            f"INSERT INTO pipeline_runs({cols}) VALUES({placeholders})",
            list(kwargs.values()),
        )
        c.commit()
        c.close()

    def health_check(self) -> dict:
        expected = get_last_trading_day()
        expected_str = expected.strftime("%Y-%m-%d")
        c = self._conn()
        total = c.execute("SELECT COUNT(*) FROM daily_prices").fetchone()[0]
        tickers = self.active_tickers()
        with_data = c.execute(
            "SELECT COUNT(DISTINCT ticker) FROM daily_prices WHERE date=?",
            (expected_str,),
        ).fetchone()[0]
        missing = c.execute("""
            SELECT t.ticker FROM tickers t
            LEFT JOIN daily_prices dp ON t.ticker=dp.ticker AND dp.date=?
            WHERE t.is_active=1 AND dp.ticker IS NULL
        """, (expected_str,)).fetchall()
        c.close()
        coverage = (with_data / len(tickers) * 100) if tickers else 0
        return {
            "expected_date": expected_str,
            "total_rows": total,
            "tickers_total": len(tickers),
            "tickers_with_data": with_data,
            "coverage_pct": round(coverage, 1),
            "missing": [r[0] for r in missing],
            "ok": coverage >= 90,
        }


# ── Pipeline Orchestration ─────────────────────────────────────────────

def setup_logging():
    Path(LOG_DIR).mkdir(exist_ok=True)
    fh = logging.handlers.TimedRotatingFileHandler(
        f"{LOG_DIR}/pipeline.log", when="midnight", backupCount=30)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(fh)
    root.addHandler(ch)


def run_pipeline(mode: str = "daily"):
    setup_logging()
    db = PriceDB()

    if mode == "init":
        logger.info("Initializing database with default tickers")
        for t in DEFAULT_TICKERS:
            db.add_ticker(t)
        mode = "monthly"  # do a full load after init

    tickers = db.active_tickers()
    if not tickers:
        logger.error("No active tickers. Run with 'init' first.")
        return

    if mode == "health":
        result = db.health_check()
        logger.info(f"Health: {result}")
        return result

    today_str = datetime.utcnow().isoformat()
    run_date = date.today().strftime("%Y-%m-%d")
    db.log_run(
        run_date=run_date, started_at=today_str,
        tickers_total=len(tickers), status="running",
    )

    success, failed = 0, 0

    for ticker in tickers:
        # Determine start date based on mode
        if mode == "daily":
            latest = db.latest_date(ticker)
            if latest:
                start_dt = datetime.strptime(latest, "%Y-%m-%d") - timedelta(days=DAILY_LOOKBACK_DAYS)
            else:
                start_dt = datetime.now() - timedelta(days=HISTORY_YEARS * 365)
            start = start_dt.strftime("%Y-%m-%d")
        elif mode == "weekly":
            start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        elif mode == "monthly":
            start = (datetime.now() - timedelta(days=HISTORY_YEARS * 365)).strftime("%Y-%m-%d")
        else:
            logger.error(f"Unknown mode: {mode}")
            return

        logger.info(f"{ticker}: fetching from {start} (mode={mode})")
        df = fetch_ticker(ticker, start=start)

        if df is None:
            failed += 1
            continue

        df = clean_ohlcv(df, ticker)
        if df.empty:
            failed += 1
            continue

        count = db.upsert(ticker, df)
        logger.info(f"{ticker}: upserted {count} rows")
        success += 1

    # Log completion
    finished = datetime.utcnow().isoformat()
    status = "success" if failed == 0 else ("partial" if success > 0 else "failed")
    db.log_run(
        run_date=run_date, started_at=today_str, finished_at=finished,
        tickers_total=len(tickers), tickers_success=success,
        tickers_failed=failed, status=status,
    )

    logger.info(
        f"Pipeline {mode} complete: {success}/{len(tickers)} success, "
        f"{failed} failed — status: {status}"
    )

    # Run health check after pipeline
    if mode in ("daily", "weekly"):
        health = db.health_check()
        if not health["ok"]:
            logger.warning(f"Health check DEGRADED: {health}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if mode not in ("daily", "weekly", "monthly", "init", "health"):
        print(f"Usage: {sys.argv[0]} [daily|weekly|monthly|init|health]")
        sys.exit(1)
    run_pipeline(mode)
```

### How to Use This Module

```bash
# First time: initialize the database and load full history
python data_pipeline.py init

# Daily cron job (run at 18:15 CET on weekdays)
python data_pipeline.py daily

# Weekly integrity check (run on Sunday mornings)
python data_pipeline.py weekly

# Monthly full refresh (run first Sunday of the month)
python data_pipeline.py monthly

# Check pipeline health anytime
python data_pipeline.py health
```

### What This Module Does NOT Do

- **Calculate indicators** — that is the signal engine's job, documented separately
- **Send notifications** — the alerting layer sits on top of the signal engine
- **Handle real-time data** — this is a daily batch pipeline only
- **Manage the ticker universe** — adding/removing stocks is a manual or semi-manual process

These responsibilities are intentionally separated to keep each component simple and testable.

---

## Key Takeaways

1. **yfinance is good enough** for a personal swing trading scanner, but you must handle its quirks (silent failures, stale data, occasional bad values).

2. **Always validate and clean** data before storing it. Never trust raw API output.

3. **Incremental updates with periodic full refreshes** give you the best balance of speed and data integrity.

4. **Store both raw and adjusted prices.** Use adjusted for calculations, raw for display and order placement.

5. **Swedish stocks have specific patterns** (large ex-dividend drops, dual share classes, Nordic holiday calendar) that your pipeline must account for.

6. **Monitoring is not optional.** A data pipeline that fails silently will produce wrong trading signals. Even simple health checks (did we get data today?) prevent the worst failure modes.

7. **SQLite is more than adequate** for this use case. 150 stocks times 3 years fits in ~15 MB. No need for PostgreSQL, Redis, or any other infrastructure.
