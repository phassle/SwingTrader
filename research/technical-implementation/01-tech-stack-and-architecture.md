# Tech Stack & Architecture Research for SwingTrader

> Research date: 2026-03-08
> Goal: Determine the best tech stack for a swing trading signal system targeting Swedish (and possibly US) stocks.

---

## Table of Contents

1. [Data Sources](#1-data-sources--whats-available-and-freecheap)
2. [Technical Indicator Libraries](#2-technical-indicator-libraries)
3. [Data Storage Options](#3-data-storage-options)
4. [Architecture Options](#4-architecture-options)
5. [How a Buy Recommendation System Works](#5-how-a-buy-recommendation-system-actually-works)
6. [Hello World Example](#6-concrete-hello-world-example)
7. [Path Forward](#7-path-forward)

---

## 1. Data Sources — What's Available and Free/Cheap

### Yahoo Finance via yfinance (Python)

**The recommended starting point.**

- **Library:** `yfinance` (current version ~1.2.0, actively maintained)
- **Cost:** Free. Uses Yahoo Finance's public API.
- **Swedish stocks:** Works with `.ST` suffix. Example: `VOLV-B.ST` (Volvo B), `SEB-A.ST`, `ERIC-B.ST`
- **What you get:** OHLCV daily/weekly/monthly bars, dividends, splits, company info, financials
- **Historical depth:** Typically 20+ years of daily data
- **Rate limits:** No hard API key, but Yahoo may throttle aggressive usage. In practice, scanning 100 stocks daily is fine.
- **Limitations:**
  - Not affiliated with Yahoo — unofficial, could break if Yahoo changes their API (has happened before, library adapts)
  - Intended for personal use only (Yahoo's terms)
  - Data is delayed ~15 minutes for most exchanges
  - Occasional gaps or quirks in Swedish stock data (thinly traded stocks may have missing days)
  - Not suitable for intraday/real-time trading — daily bars are the sweet spot

```python
import yfinance as yf

# Fetch 6 months of Volvo B
volvo = yf.download("VOLV-B.ST", period="6mo")
print(volvo.tail())
```

### Avanza Unofficial API

- **Python:** `avanza` package on PyPI (unofficial wrapper)
- **Node.js:** `avanza` npm package also exists
- **Cost:** Free, but **requires an Avanza account** with BankID authentication
- **What you get:** Real-time Swedish stock data, order book, portfolio management, even order placement
- **Pros:**
  - Real-time data (not delayed)
  - Deep integration with the Swedish market
  - Can place actual trades programmatically
- **Cons:**
  - Unofficial — Avanza does not officially support API access, could break or get your account flagged
  - Requires 2FA/BankID authentication flow (complex to automate)
  - Not well-documented, smaller community
  - Overkill for daily swing trading signals — you don't need real-time data for end-of-day analysis
- **Verdict:** Skip for now. Useful later if you want to automate order execution, but yfinance is simpler for data fetching.

### Alpha Vantage

- **Cost:** Free tier available with API key
- **Free tier limits:** 25 API requests per day (as of 2025 — they tightened this significantly from the old 5/minute model)
- **What you get:** Daily/weekly/monthly OHLCV, some technical indicators pre-calculated, fundamental data
- **Swedish stocks:** Limited support. Works for some `.ST` tickers but coverage is inconsistent
- **Pros:** Clean JSON API, some pre-built indicator endpoints
- **Cons:**
  - 25 calls/day on free tier is brutal — scanning 50 stocks with multiple data points burns through it instantly
  - Premium plans start at ~$50/month
  - Swedish stock coverage is spotty
- **Verdict:** Not great for Swedish stocks. Could be a supplementary source for US stocks.

### Polygon.io

- **Cost:** Free tier for US stocks (delayed data), paid plans from ~$29/month for real-time
- **What you get:** Excellent US stock data — trades, quotes, OHLCV, reference data
- **Swedish stocks:** **No coverage.** US markets only.
- **Pros:** Best-in-class US market data API, WebSocket streaming, well-documented
- **Cons:** No Nordic/European stocks, costs money for real-time
- **Verdict:** Only relevant if you expand to US stocks later. Not useful for Swedish market.

### Nasdaq Nordic Open Data

- **Source:** [nasdaqomxnordic.com](http://www.nasdaqomxnordic.com/)
- **What you get:** End-of-day data for all Nasdaq Nordic listed stocks, index compositions
- **Cost:** Free for delayed/EOD data
- **Pros:** Official source, covers all Swedish listed stocks
- **Cons:** No convenient Python library — you'd need to scrape or use their CSV exports. More work to integrate.
- **Verdict:** Good reference source, but yfinance already pulls this data more conveniently.

### Data Source Comparison for Swedish Stocks

| Source | Swedish Stocks | Cost | Ease of Use | Real-time | Daily Bars |
|--------|---------------|------|-------------|-----------|------------|
| **yfinance** | Yes (.ST) | Free | Excellent | No (15min delay) | Yes |
| Avanza API | Yes | Free (need account) | Medium | Yes | Yes |
| Alpha Vantage | Partial | Free (25/day) | Good | No | Yes |
| Polygon.io | No | $29+/mo | Excellent | Yes (paid) | Yes |
| Nasdaq Nordic | Yes | Free | Poor (manual) | No | Yes |

### Recommendation

**Start with yfinance.** It covers Swedish stocks, it's free, the Python library is mature and actively maintained, and daily OHLCV bars are exactly what swing trading needs. You don't need real-time data — swing trades are held for days to weeks, so end-of-day analysis is perfect.

---

## 2. Technical Indicator Libraries

### Python Ecosystem

#### pandas-ta (Recommended)

- **Version:** 0.4.71b (actively developed)
- **Indicators:** 150+ indicators and 60+ candlestick patterns
- **Key indicators for swing trading:** Bollinger Bands, RSI, MACD, ATR, Stochastic, OBV, ADX, Ichimoku, EMA, SMA, VWAP — all included
- **How it works:** Extends pandas DataFrames directly. You call `df.ta.rsi()` and it adds an RSI column.
- **Dependencies:** numpy, pandas (things you already need)
- **Performance:** Uses numba for JIT compilation where possible
- **Install:** `pip install pandas-ta`

```python
import pandas_ta as ta

# After fetching OHLCV data into a DataFrame:
df.ta.rsi(length=14, append=True)
df.ta.macd(append=True)
df.ta.bbands(length=20, std=2, append=True)
# DataFrame now has RSI_14, MACD_12_26_9, BBL_20_2.0, BBM_20_2.0, BBU_20_2.0 columns
```

- **Why it's the best choice:**
  - Pure Python, no C compilation headaches
  - Pandas-native — fits naturally into a data pipeline
  - Comprehensive coverage of every indicator you'll need
  - Good documentation with examples
  - Active community

#### TA-Lib (via ta-lib Python wrapper)

- **The industry standard** for technical analysis, used by professional quant shops
- **Performance:** C-based core, extremely fast
- **Indicators:** 200+ indicators
- **The catch:** Installation is painful.
  - Requires compiling the underlying C library first
  - On macOS: `brew install ta-lib` then `pip install ta-lib`
  - On Linux: download source, `./configure && make && make install`
  - On Windows: download pre-built binaries
  - Docker helps but adds complexity
- **When to use it:** If you're processing thousands of stocks with millions of data points and pandas-ta is too slow. For scanning 100-200 Swedish stocks daily, pandas-ta is more than fast enough.
- **Verdict:** Overkill for this project. The installation friction alone makes pandas-ta the better starting choice.

#### ta (Technical Analysis Library)

- **Simpler alternative** to pandas-ta
- **Indicators:** ~40 indicators (fewer than pandas-ta)
- **Install:** `pip install ta`
- **Pros:** Simple API, easy to get started
- **Cons:** Fewer indicators, less actively maintained, less flexible
- **Verdict:** pandas-ta does everything `ta` does and more. No reason to choose this.

### Node.js / TypeScript Ecosystem

#### technicalindicators (npm)

- **The most popular** Node.js technical analysis library
- **Indicators:** ~40 indicators (RSI, MACD, Bollinger, SMA, EMA, Stochastic, ADX, ATR, etc.)
- **Install:** `npm install technicalindicators`
- **API style:** Functional — you pass arrays of numbers, get arrays back

```typescript
import { RSI, BollingerBands, MACD } from 'technicalindicators';

const rsiValues = RSI.calculate({ values: closePrices, period: 14 });
```

- **Pros:** TypeScript types included, works in browser and Node
- **Cons:**
  - Significantly fewer indicators than pandas-ta (40 vs 150+)
  - No DataFrame integration — you manage data alignment yourself
  - Less financial community support
  - Last meaningful update was a while ago

#### tulind (npm)

- **C-based** bindings (like TA-Lib for Node)
- **Performance:** Fast
- **Cons:** Native compilation required, fewer users, less maintained

#### talib.js

- **TA-Lib compiled to JavaScript** via Emscripten
- **Cons:** Large bundle size, awkward API, essentially abandoned

### Honest Comparison: Python vs Node/TypeScript for Financial Analysis

| Aspect | Python | Node/TypeScript |
|--------|--------|-----------------|
| **Indicator libraries** | 150+ indicators (pandas-ta) | ~40 indicators (technicalindicators) |
| **Data manipulation** | pandas is world-class for this | No equivalent (lodash doesn't count) |
| **Data fetching** | yfinance is excellent | No equivalent library for stock data |
| **Community** | Massive quant/finance community | Almost no financial analysis community |
| **Tutorials/examples** | Thousands of blog posts, books | Very few |
| **Backtesting** | backtrader, zipline, vectorbt | Nothing mature |
| **ML integration** | scikit-learn, TensorFlow, PyTorch | TensorFlow.js exists but less mature |
| **Type safety** | Weak (unless using mypy) | Strong (TypeScript) |
| **Web/API development** | Flask/FastAPI are fine | Express/Nest.js are excellent |

### Verdict

**Python wins decisively for the core financial analysis work.** This isn't even close. The ecosystem gap is massive:

- pandas + yfinance + pandas-ta gives you a complete pipeline in ~20 lines of code
- In Node/TypeScript, you'd be writing custom data fetching, manual array alignment, and working with a library that has 1/4 the indicators

**TypeScript is better for:** building a web dashboard, REST APIs, real-time UIs. If you want a frontend later, that's where TypeScript shines.

**The pragmatic answer:** Write the core analysis engine in Python. If you want a web UI later, build it in TypeScript/Next.js and have it call the Python backend.

---

## 3. Data Storage Options

### What Needs Storing

Before picking a database, let's define what data this system produces:

1. **OHLCV daily bars** — Open, High, Low, Close, Volume for each stock for each day
2. **Calculated indicators** — RSI, MACD, Bollinger values per stock per day
3. **Signals** — "Stock X triggered buy signal Y on date Z"
4. **Trade recommendations** — Scored, ranked list of current signals
5. **Stock metadata** — Ticker, name, sector, market cap
6. **Watchlist / universe** — Which stocks to scan

### Option: Plain CSV / Parquet Files

- **Simplest possible start.** yfinance already returns pandas DataFrames; save them as CSV or Parquet.
- **Parquet** is better than CSV: compressed, typed, fast to read with pandas.
- **Pros:** Zero setup, human-readable (CSV), works with git
- **Cons:** No querying, no relationships, gets messy with 100+ stocks over time, no concurrent access
- **When to use:** Prototyping. Your first version can just dump results to CSV.

### Option: SQLite (Recommended for Phase 1-2)

- **File-based database.** One `.db` file, no server process, zero configuration.
- **Python support:** Built into the standard library (`import sqlite3`). Also great with `sqlalchemy`.
- **Capacity:** Handles millions of rows easily. 200 stocks x 252 trading days x 10 years = 504,000 rows. SQLite laughs at this.
- **Pros:**
  - Zero setup — just `import sqlite3`
  - Single file, easy to backup (copy the file)
  - Fast enough for this workload (not even close to its limits)
  - SQL queries for analysis ("show me all buy signals in the last 30 days")
  - Works great with pandas: `pd.read_sql()` and `df.to_sql()`
- **Cons:**
  - Single-writer (fine for a single scanning script)
  - No built-in time-series optimizations
  - Not great if multiple services need to write simultaneously
- **Verdict:** Perfect for a single-user swing trading scanner. Start here.

### Option: PostgreSQL

- **When you'd need it:** Multiple services writing data, web API serving queries, multi-user access
- **Pros:** Rock-solid, scales to millions of rows, concurrent access, rich SQL
- **Cons:** Requires running a server (Docker makes this easy, but still more complexity)
- **Verdict:** Overkill for Phase 1-2. Consider when adding a web UI or if you want cloud deployment.

### Option: TimescaleDB (PostgreSQL Extension)

- **What it is:** PostgreSQL with automatic time-series optimizations (hypertables, compression, continuous aggregates)
- **When you'd need it:** If you're storing tick-level data or millions of intraday bars
- **Verdict:** Way overkill. Daily bars for 200 stocks is trivial for any database.

### Recommended Schema (SQLite)

```sql
-- Stock universe
CREATE TABLE stocks (
    ticker TEXT PRIMARY KEY,        -- e.g., 'VOLV-B.ST'
    name TEXT NOT NULL,             -- e.g., 'Volvo B'
    sector TEXT,                    -- e.g., 'Industrials'
    market TEXT DEFAULT 'OMX',      -- e.g., 'OMX', 'NYSE'
    active BOOLEAN DEFAULT 1
);

-- Daily OHLCV price data
CREATE TABLE daily_prices (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,             -- ISO format: '2026-03-07'
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Calculated indicator values (denormalized for query speed)
CREATE TABLE indicators (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    rsi_14 REAL,
    macd REAL,
    macd_signal REAL,
    macd_hist REAL,
    bb_upper REAL,
    bb_middle REAL,
    bb_lower REAL,
    sma_50 REAL,
    sma_200 REAL,
    atr_14 REAL,
    adx_14 REAL,
    volume_sma_20 REAL,
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Generated buy/sell signals
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    signal_type TEXT NOT NULL,      -- 'BUY' or 'SELL'
    strategy TEXT NOT NULL,         -- e.g., 'mean_reversion', 'macd_crossover'
    strength REAL,                  -- 0.0 to 1.0, how strong the signal is
    rsi_value REAL,                 -- snapshot of key indicators at signal time
    price_at_signal REAL,
    notes TEXT,                     -- human-readable explanation
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Index for common queries
CREATE INDEX idx_signals_date ON signals(date);
CREATE INDEX idx_signals_ticker ON signals(ticker);
CREATE INDEX idx_daily_prices_date ON daily_prices(date);
```

This schema is intentionally simple. The `indicators` table is denormalized (one wide row per stock per day) because that's how you'll query it — "give me all indicators for VOLV-B.ST on 2026-03-07" is one row read.

---

## 4. Architecture Options

### Option A: Python Monolith (Recommended Start)

```
┌─────────────────────────────────────────────┐
│              Python Script / App             │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Fetch   │→ │ Calculate│→ │  Generate  │ │
│  │  Data    │  │ Indicators│  │  Signals   │ │
│  │(yfinance)│  │(pandas-ta)│  │ (rules)   │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│                      │                       │
│                 ┌────▼────┐                  │
│                 │ SQLite  │                  │
│                 │   DB    │                  │
│                 └─────────┘                  │
│                      │                       │
│              ┌───────▼────────┐              │
│              │ Output: console│              │
│              │ / file / email │              │
│              └────────────────┘              │
└─────────────────────────────────────────────┘
```

**How it works:**
1. Run the script daily (manually, cron job, or scheduled task)
2. It fetches fresh data for your stock universe
3. Calculates all indicators
4. Applies strategy rules
5. Stores everything in SQLite
6. Prints/emails any new buy signals

**Pros:**
- Simplest possible architecture
- One language, one process, one file for the database
- Easy to debug — just run the script and look at the output
- Can be a single Python file to start, grow into a package later
- All the best financial libraries are Python-native

**Cons:**
- No web UI (console output only to start)
- No real-time anything
- Single machine only

**This is the right starting point.** Get the core logic working before adding complexity.

### Option B: TypeScript / Node.js Monolith

Same architecture as Option A but in TypeScript.

```typescript
// Pseudocode — what this would look like in TypeScript
import { RSI, BollingerBands, MACD } from 'technicalindicators';
// No good yfinance equivalent — need to call Yahoo API directly or use a wrapper
// Manual data alignment — no pandas equivalent
// Fewer indicators available
```

**Pros:**
- Type safety
- If you're more comfortable in TypeScript
- Easier to add a web UI later (same language)

**Cons:**
- **Significantly worse library ecosystem for financial analysis**
- No pandas equivalent — manual data wrangling
- No yfinance equivalent — need to build your own data fetcher
- Fewer indicators (40 vs 150+)
- Almost no community resources for quant work in Node
- You'd be fighting the ecosystem instead of leveraging it

**Verdict:** Only choose this if you absolutely refuse to write Python. The library gap is too large.

### Option C: Microservices

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│ Data Fetch │    │ Indicator  │    │  Signal    │
│  Service   │───▶│ Calculator │───▶│  Engine    │
│ (Python)   │    │ (Python)   │    │ (Python)   │
└────────────┘    └────────────┘    └────────────┘
      │                 │                  │
      └────────────────▼──────────────────┘
                   ┌────────┐
                   │ Postgres│
                   │   DB    │
                   └────────┘
                       │
                ┌──────▼──────┐
                │  Web API    │
                │ (TS/Python) │
                └─────────────┘
                       │
                ┌──────▼──────┐
                │  Frontend   │
                │ (Next.js)   │
                └─────────────┘
```

**When this makes sense:**
- You want independent scaling (not needed for 200 stocks)
- Multiple people working on different services
- You want the data fetcher to run on a schedule independently of the signal engine
- You want a web UI and API

**When this is overkill:**
- When you're one developer scanning 100-200 stocks daily
- When the entire pipeline runs in under 30 seconds
- When you haven't validated that the core strategy even works yet

**Verdict:** Don't start here. You'll spend weeks on infrastructure instead of building the actual trading logic. Microservices are a Phase 3-4 consideration.

### Architecture Recommendation

**Start with Option A (Python monolith).** Here's why:

1. **Validate first, architect later.** You don't know if your strategy works yet. A simple script lets you iterate on strategy logic 10x faster than a microservice architecture.
2. **The entire pipeline for 200 stocks takes seconds.** There's nothing to optimize with distributed systems.
3. **Python's financial ecosystem is unmatched.** yfinance + pandas + pandas-ta gives you everything in 3 imports.
4. **You can always extract services later.** A well-structured Python script with clear functions naturally evolves into separate modules, then separate services if needed.

---

## 5. How a Buy Recommendation System Actually Works

Let's walk through the entire flow, step by step. This is what your Python script will do every time it runs.

### Step 1: Define Your Stock Universe

You need a list of stocks to scan. Start with something manageable:

- **OMX Stockholm Large Cap** (~90 stocks) — the biggest, most liquid Swedish stocks
- Examples: VOLV-B.ST, SEB-A.ST, ERIC-B.ST, ASSA-B.ST, INVE-B.ST, HM-B.ST

Why not scan everything? Small-cap stocks are thinly traded (low volume), which makes technical analysis less reliable. Stick to large cap to start.

### Step 2: Fetch OHLCV Data

For each stock, download the last 6-12 months of daily data. You need history because indicators like the 200-day SMA need 200 days of data to calculate.

**OHLCV explained simply:**
- **Open:** Price at market open
- **High:** Highest price during the day
- **Low:** Lowest price during the day
- **Close:** Price at market close (the most important one)
- **Volume:** How many shares were traded (high volume = more conviction in the price move)

### Step 3: Calculate Technical Indicators

For each stock's price history, calculate a set of indicators. Each indicator tells you something different:

- **RSI (Relative Strength Index):** Measures if a stock is overbought (>70) or oversold (<30). Oversold stocks are potential buy candidates for mean reversion.
- **MACD (Moving Average Convergence Divergence):** Shows momentum direction. When the MACD line crosses above the signal line, momentum is turning bullish.
- **Bollinger Bands:** A channel around the stock's moving average. When price drops below the lower band, the stock has moved unusually far from its average — potential bounce.
- **Moving Averages (SMA 50, 200):** Trend direction. Price above SMA 200 = long-term uptrend. The "golden cross" (SMA 50 crosses above SMA 200) is a classic bullish signal.
- **Volume:** Confirms moves. A price bounce on high volume is more trustworthy than one on low volume.

For more on what each indicator means and how swing traders use them, see `../strategy-and-theory/`.

### Step 4: Apply Strategy Rules

A strategy is just a set of if/then rules applied to the indicator values. Here are examples:

**Mean Reversion Strategy (buying the dip):**
```
IF RSI(14) < 35
AND Close < Lower Bollinger Band
AND Volume > 1.2 * Average Volume (20-day)
THEN → Buy Signal (strength: high)
```

**MACD Momentum Strategy:**
```
IF MACD histogram crosses from negative to positive
AND RSI(14) > 40 AND RSI(14) < 60  (not already overbought)
AND Close > SMA(200)                (stock is in long-term uptrend)
THEN → Buy Signal (strength: medium)
```

**Trend Following Strategy:**
```
IF SMA(50) crosses above SMA(200)   (golden cross)
AND ADX(14) > 25                    (trend is strong)
AND Volume increasing over 5 days
THEN → Buy Signal (strength: medium-high)
```

Each strategy catches a different kind of opportunity. Mean reversion buys oversold dips; MACD catches momentum shifts; trend following rides big moves.

### Step 5: Score and Rank Signals

When multiple stocks trigger signals, you need to rank them:

1. **Number of confirming indicators:** RSI oversold AND below Bollinger AND MACD crossing up is stronger than just RSI oversold alone
2. **How extreme the reading is:** RSI at 20 is a stronger signal than RSI at 34
3. **Volume confirmation:** Signals with above-average volume rank higher
4. **Sector diversification:** Don't buy 5 bank stocks — spread across sectors

### Step 6: Generate Output

The final output looks like:

```
=== SwingTrader Buy Signals — 2026-03-08 ===

1. VOLV-B.ST (Volvo B) — Score: 0.85
   Strategy: Mean Reversion
   RSI(14): 28.3 (oversold)
   Price: 242.50 (below lower BB: 245.10)
   MACD: histogram turning positive
   Volume: 1.4x average
   → STRONG BUY SIGNAL

2. SEB-A.ST (SEB A) — Score: 0.62
   Strategy: MACD Crossover
   RSI(14): 45.2
   MACD: bullish crossover today
   Above SMA(200): Yes
   → MODERATE BUY SIGNAL

No signals: ERIC-B.ST, HM-B.ST, ASSA-B.ST
```

---

## 6. Concrete "Hello World" Example

A complete, runnable Python script. Copy-paste this and run it.

### Setup

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install yfinance pandas pandas-ta
```

### The Script

```python
#!/usr/bin/env python3
"""
SwingTrader Hello World — Mean Reversion Scanner for Swedish Large Caps

Fetches daily data, calculates RSI + Bollinger Bands + MACD,
and prints buy signals where RSI < 35 AND price is below the lower Bollinger Band.
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- Configuration ---
STOCKS = {
    "VOLV-B.ST": "Volvo B",
    "SEB-A.ST": "SEB A",
    "ERIC-B.ST": "Ericsson B",
    "ASSA-B.ST": "ASSA ABLOY B",
    "INVE-B.ST": "Investor B",
}

RSI_PERIOD = 14
RSI_OVERSOLD = 35
BB_LENGTH = 20
BB_STD = 2.0
LOOKBACK = "8mo"  # Need enough history for indicators to warm up


def scan_stock(ticker: str, name: str) -> dict | None:
    """Fetch data and check for buy signals on a single stock."""

    # 1. Fetch OHLCV data
    df = yf.download(ticker, period=LOOKBACK, progress=False)

    if df.empty or len(df) < BB_LENGTH + 50:
        print(f"  {ticker}: Not enough data, skipping")
        return None

    # yfinance may return MultiIndex columns; flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. Calculate indicators
    df.ta.rsi(length=RSI_PERIOD, append=True)
    df.ta.bbands(length=BB_LENGTH, std=BB_STD, append=True)
    df.ta.macd(append=True)

    # Get the latest row (most recent trading day)
    latest = df.iloc[-1]

    # Column names generated by pandas-ta
    rsi_col = f"RSI_{RSI_PERIOD}"
    bbl_col = f"BBL_{BB_LENGTH}_{BB_STD}"
    bbm_col = f"BBM_{BB_LENGTH}_{BB_STD}"
    bbu_col = f"BBU_{BB_LENGTH}_{BB_STD}"
    macd_col = "MACD_12_26_9"
    macd_hist_col = "MACDh_12_26_9"
    macd_signal_col = "MACDs_12_26_9"

    rsi_val = latest.get(rsi_col)
    close = latest.get("Close")
    bb_lower = latest.get(bbl_col)
    bb_upper = latest.get(bbu_col)
    macd_hist = latest.get(macd_hist_col)

    if pd.isna(rsi_val) or pd.isna(bb_lower):
        print(f"  {ticker}: Indicators not ready (NaN), skipping")
        return None

    # 3. Apply mean reversion buy signal
    rsi_oversold = rsi_val < RSI_OVERSOLD
    below_lower_bb = close < bb_lower

    is_buy_signal = rsi_oversold and below_lower_bb

    result = {
        "ticker": ticker,
        "name": name,
        "close": round(float(close), 2),
        "rsi": round(float(rsi_val), 1),
        "bb_lower": round(float(bb_lower), 2),
        "bb_upper": round(float(bb_upper), 2),
        "macd_hist": round(float(macd_hist), 4) if not pd.isna(macd_hist) else None,
        "is_buy_signal": is_buy_signal,
        "date": df.index[-1].strftime("%Y-%m-%d"),
    }

    return result


def main():
    print(f"\n{'='*60}")
    print(f"  SwingTrader Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Strategy: Mean Reversion (RSI < {RSI_OVERSOLD} + Below Lower BB)")
    print(f"{'='*60}\n")

    results = []
    for ticker, name in STOCKS.items():
        result = scan_stock(ticker, name)
        if result:
            results.append(result)

    # Separate signals from non-signals
    buy_signals = [r for r in results if r["is_buy_signal"]]
    no_signals = [r for r in results if not r["is_buy_signal"]]

    # Print buy signals
    if buy_signals:
        print("\n** BUY SIGNALS **\n")
        for s in buy_signals:
            print(f"  {s['ticker']} ({s['name']})")
            print(f"    Close: {s['close']}  |  RSI: {s['rsi']}  |  Lower BB: {s['bb_lower']}")
            print(f"    MACD Histogram: {s['macd_hist']}")
            print(f"    Date: {s['date']}")
            print()
    else:
        print("\n  No buy signals today.\n")

    # Print summary of all stocks
    print("-" * 60)
    print("  Stock Summary:\n")
    for r in results:
        status = "** BUY **" if r["is_buy_signal"] else "hold"
        print(f"    {r['ticker']:15s}  RSI: {r['rsi']:5.1f}  Close: {r['close']:>10.2f}  [{status}]")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
```

### Running It

```bash
python scanner.py
```

Expected output (values will vary based on current market data):

```
============================================================
  SwingTrader Scanner — 2026-03-08 14:30
  Strategy: Mean Reversion (RSI < 35 + Below Lower BB)
============================================================

  No buy signals today.

------------------------------------------------------------
  Stock Summary:

    VOLV-B.ST        RSI:  52.3  Close:     258.40  [hold]
    SEB-A.ST         RSI:  61.7  Close:     142.85  [hold]
    ERIC-B.ST        RSI:  44.1  Close:      72.30  [hold]
    ASSA-B.ST        RSI:  48.9  Close:     287.60  [hold]
    INVE-B.ST        RSI:  55.2  Close:     232.10  [hold]

============================================================
```

Most days you'll see "no buy signals" — that's correct. Mean reversion signals are uncommon because stocks don't hit extreme oversold levels very often. When they do trigger, that's when they're valuable.

---

## 7. Path Forward

### Phase 1: Get the Scanner Working (Week 1-2)

**Goal:** A Python script that scans Swedish large caps daily and prints buy signals.

- Start with the Hello World script above
- Expand the stock universe to all OMX Large Cap stocks (~90 tickers)
- Add the MACD crossover strategy alongside mean reversion
- Run it manually each evening after market close
- Store results in SQLite (use the schema from Section 3)
- Set up a cron job or similar to run it daily at 18:00 CET

**Tech stack:** Python + yfinance + pandas-ta + SQLite

### Phase 2: Multiple Strategies + History (Week 3-6)

**Goal:** A more robust scanner with multiple strategies and historical signal tracking.

- Add more strategies: trend following (golden cross), breakout (52-week high on volume), MACD divergence
- Implement signal scoring and ranking (combine multiple indicators)
- Store all signals in SQLite so you can review past performance
- Add a simple "how did past signals perform?" report
  - "Signal X fired on 2026-02-15 at price 240. Stock is now at 260. +8.3%"
- Start paper-trading: track signals without real money to validate
- Consider adding email/Slack/Telegram notifications for new signals

**Tech stack:** Same as Phase 1, more strategy modules

### Phase 3: Web UI or Notifications (Week 7-12)

**Goal:** Make the signals accessible beyond the terminal.

This is where TypeScript can enter the picture:

- **Option A:** Next.js dashboard that reads from the SQLite/PostgreSQL database
  - Shows current signals, historical performance, stock charts
  - Python backend stays as-is, runs on a schedule
  - TypeScript frontend queries the database via a small API

- **Option B:** Python FastAPI backend + any frontend
  - FastAPI serves the signal data as a REST API
  - Frontend can be React, Next.js, or even a simple HTML page

- **Option C:** Keep it simple — just add Telegram/Slack notifications
  - Python script sends a message when buy signals fire
  - No web UI needed if you just want alerts on your phone

**When to migrate from SQLite to PostgreSQL:** When you add a web API that might have concurrent reads, or when you want cloud deployment (PostgreSQL on Supabase/Railway is easy).

### Phase 4: Backtesting (Month 2-3)

**Goal:** Test strategies against historical data before trusting them with real money.

- Use `vectorbt` or `backtrader` (Python libraries) to backtest strategies
- Answer questions like: "If I had followed this mean reversion strategy on OMX Large Cap for the last 5 years, what would my returns be?"
- Optimize indicator parameters (is RSI < 30 better than RSI < 35?)
- Measure win rate, average gain, max drawdown, Sharpe ratio

**This is critical before trading real money.** A strategy that "looks good" on paper can have terrible historical performance.

### When to Consider Microservices

Microservices become worth the complexity when:

1. **Different components need different scaling** — e.g., the data fetcher runs every minute but the signal engine runs once daily
2. **Multiple developers** are working on different parts
3. **You want independent deployment** — update the signal engine without touching the data fetcher
4. **Different languages make sense for different parts** — Python for analysis, TypeScript for web API

For a solo developer scanning stocks daily, a monolith is the right choice for at least the first 3-6 months. Don't over-engineer before you've validated the core idea.

### When TypeScript Makes Sense

TypeScript enters the picture naturally in Phase 3:

- **Web dashboard** (Next.js / React)
- **REST API** serving signal data (though FastAPI in Python is also great)
- **Real-time UI** with WebSocket updates
- **Mobile-friendly PWA** for checking signals on your phone

The architecture would be:

```
Python (scheduled job) → SQLite/PostgreSQL ← TypeScript API ← React Frontend
```

Python does the heavy lifting (data + analysis). TypeScript serves the results to users. Each language plays to its strengths.

---

## Summary of Recommendations

| Decision | Recommendation | Why |
|----------|---------------|-----|
| **Language** | Python (core) | Unmatched financial library ecosystem |
| **Data source** | yfinance | Free, reliable, supports .ST tickers |
| **Indicators** | pandas-ta | 150+ indicators, pandas-native, easy install |
| **Storage** | SQLite → PostgreSQL later | Zero setup to start, upgrade path clear |
| **Architecture** | Monolith → Services later | Validate strategy first, architect second |
| **Frontend** | Phase 3 (TypeScript/Next.js) | Not needed until core logic is proven |
| **First strategy** | Mean reversion (RSI + BB) | Simple, well-understood, good for swing trading |
