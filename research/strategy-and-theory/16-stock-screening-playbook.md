# Stock Screening Playbook for Swing Trading

## Reference Document for Implementation

This document provides a complete, actionable framework for screening and filtering stocks for swing trading setups. It covers screening philosophy, six concrete scanner configurations with exact parameters, watchlist management, a multi-step filtering pipeline, and Python implementation examples.

**Cross-references:**
- Technical indicator formulas and interpretation: `02-technical-indicators.md`
- Strategy entry/exit rules that scanners feed into: `04-swing-trading-strategies.md`
- Risk management and position sizing applied after screening: `05-risk-management.md`
- API and data source details for implementation: `06-apis-and-technology.md`
- Backtesting scanner-driven strategies: `07-backtesting-and-performance.md`
- Market regime identification (determines which scanners to run): `08-market-structure-and-conditions.md`
- Empirical evidence on momentum vs. reversal edge: `10-empirical-evidence-and-edge-quality.md`
- Chart pattern recognition for confirmation: `03-chart-patterns.md`

---

## Table of Contents

1. [Screening Philosophy](#1-screening-philosophy)
2. [Pullback Scanner (Trend Continuation)](#2-pullback-scanner-trend-continuation)
3. [Breakout Scanner](#3-breakout-scanner)
4. [Mean Reversion Scanner](#4-mean-reversion-scanner)
5. [Momentum Scanner](#5-momentum-scanner)
6. [Gap Scanner](#6-gap-scanner)
7. [Sector Rotation Scanner](#7-sector-rotation-scanner)
8. [Watchlist Management](#8-watchlist-management)
9. [Filtering Pipeline](#9-filtering-pipeline)
10. [Implementation Notes](#10-implementation-notes)

---

## 1. Screening Philosophy

### 1.1 Top-Down vs. Bottom-Up Approach

Stock screening can follow two paths. In practice, the best results come from combining both.

**Top-Down (Macro to Micro):**

1. Assess the broad market regime (bull, bear, sideways) using SPY/QQQ. See `08-market-structure-and-conditions.md` Section 1 for regime classification.
2. Identify the strongest or weakest sectors using sector ETFs (XLK, XLF, XLE, etc.).
3. Screen individual stocks within the favored sectors.
4. Apply setup-specific filters.

**Bottom-Up (Stock First):**

1. Run a broad technical scanner across the full universe.
2. Filter results by sector and market conditions.
3. Validate that the stock's sector and the broad market support the trade direction.

**Recommended Hybrid Flow:**

```
Market Regime Assessment (daily)
    |
    v
Sector Relative Strength Ranking (daily)
    |
    v
Run Setup Scanners on favored sectors (daily)
    |
    v
Run Setup Scanners on full universe (weekly, to catch outliers)
    |
    v
Filter Pipeline (quality checks)
    |
    v
Watchlist Placement
```

The top-down filter is not optional. As documented in `08-market-structure-and-conditions.md`, 60-80% of individual stocks follow the general market direction. Running long-side scanners in a bear regime or short-side scanners in a bull regime wastes time and capital.

### 1.2 Universe Selection

#### Exchanges

| Exchange | Include | Notes |
|----------|---------|-------|
| NYSE | Yes | Large-cap, liquid, established companies |
| NASDAQ | Yes | Tech-heavy, growth stocks, higher volatility |
| NYSE Arca | Yes | ETFs and some equities |
| OTC / Pink Sheets | No | Low liquidity, poor data, manipulation risk |
| Foreign ADRs | Selective | Include only liquid ADRs (> 500K daily volume) |

**Sweden:** For Swedish stocks, replace the exchanges above with Nasdaq Stockholm Large Cap (primary) and Mid Cap (selective). Use `.ST` suffix tickers in yfinance (e.g., `VOLV-B.ST`, `SEB-A.ST`). Avoid First North and Small Cap for the default scanner universe. See `27-swedish-market-adaptation.md` Section 5 for full thresholds.

#### Market Capitalization Ranges

| Category | Market Cap | Scanner Suitability |
|----------|-----------|-------------------|
| Mega Cap | > $200B | Low volatility, good for sector rotation |
| Large Cap | $10B - $200B | Primary swing trading universe |
| Mid Cap | $2B - $10B | Excellent for swing trading; institutional + retail flow |
| Small Cap | $500M - $2B | **Advanced/optional expansion tier only.** More volatile; wider spreads; requires explicit opt-in |
| Micro Cap | < $500M | Exclude from automated scanning |

**Recommended primary universe (conservative default):** Stocks with market cap > $2B listed on NYSE or NASDAQ. This typically yields 1,200-1,800 names, which is manageable for daily scanning. An advanced expansion tier may include stocks down to $500M market cap, but this must be explicitly enabled and is not the default.

**Sweden:** The equivalent conservative default is market cap > SEK 20B (Nasdaq Stockholm Large Cap), which yields ~60-80 names. The expanded tier adds Mid Cap names with ADTV > SEK 5M/day (~90-130 total). The Swedish universe is much smaller and can be scanned entirely in a single batch.

### 1.3 Pre-Filtering for Tradability

Before applying any technical filter, every stock must pass basic tradability requirements. These eliminate illiquid, low-priced, or hard-to-execute names.

| Filter | Minimum Threshold | Rationale |
|--------|-------------------|-----------|
| Price | > $10.00 | Avoids penny stocks; ensures meaningful tick sizes |
| Average Daily Volume (20-day) | > 500,000 shares | Ensures entry/exit without excessive slippage |
| Average Daily Dollar Volume | > $5M | Better than share volume alone for higher-priced stocks |
| Bid-Ask Spread | < 0.10% of price | Limits execution cost; critical for mean reversion |
| Days Since IPO | > 60 days | Allows sufficient price history for indicator calculation |
| Not Halted | Active trading status | Avoid stocks under SEC or exchange halts |
| No Pending Earnings | Configurable | Many swing traders avoid holding through earnings (see `05-risk-management.md` Section 4) |

**Python pre-filter example:**

```python
def passes_tradability_filter(ticker_data: dict) -> bool:
    """
    ticker_data keys: price, avg_volume_20d, avg_dollar_volume,
                      market_cap, days_since_ipo
    """
    return (
        ticker_data["price"] > 10.0
        and ticker_data["avg_volume_20d"] > 500_000
        and ticker_data["avg_dollar_volume"] > 5_000_000
        and ticker_data["market_cap"] > 2_000_000_000
        and ticker_data["days_since_ipo"] > 60
    )
```

---

## 2. Pullback Scanner (Trend Continuation)

### 2.1 Concept

This scanner finds stocks in established uptrends that have pulled back to a favorable entry zone. It is the highest-probability swing trading setup according to empirical evidence (see `10-empirical-evidence-and-edge-quality.md` Section 1 on momentum). The idea is to buy temporary weakness within a strong trend.

### 2.2 Exact Parameters

| Parameter | Condition | Value |
|-----------|-----------|-------|
| Price vs. 50 SMA | Above | `close > SMA(50)` |
| Price vs. 200 SMA | Above | `close > SMA(200)` |
| 50 SMA vs. 200 SMA | Above | `SMA(50) > SMA(200)` (Golden Cross intact) |
| RSI(14) | Between | `30 <= RSI(14) <= 50` |
| Price vs. 20 EMA | Within 5% | `abs(close - EMA(20)) / EMA(20) <= 0.05` |
| Price vs. 20 EMA | At or below | `close <= EMA(20) * 1.01` (allowing 1% buffer above) |
| Volume trend | Declining | `SMA(volume, 5) < SMA(volume, 20)` |
| ADX(14) | Above threshold | `ADX(14) > 25` |

### 2.3 Logic Flow

```
Step 1: close > SMA(200) AND close > SMA(50)     -- Uptrend confirmed
Step 2: SMA(50) > SMA(200)                        -- Trend structure intact
Step 3: RSI(14) >= 30 AND RSI(14) <= 50           -- Pulling back, not broken
Step 4: close <= EMA(20) * 1.05                   -- Near the 20 EMA (within 5%)
Step 5: close >= EMA(20) * 0.95                   -- Not too far below 20 EMA
Step 6: avg_volume(5) < avg_volume(20)            -- Volume declining on pullback
Step 7: ADX(14) > 25                              -- Trend has directional strength
```

### 2.4 Scoring (Optional Ranking)

When the scanner returns multiple results, rank by quality:

| Factor | Weight | Scoring |
|--------|--------|---------|
| RSI distance from 40 | 25% | Closer to 40 = higher score (sweet spot) |
| ADX strength | 20% | Higher ADX = stronger trend |
| Distance from 20 EMA | 20% | Closer = better entry |
| Volume decline ratio | 15% | Greater decline = healthier pullback |
| Relative strength vs. SPY (20-day) | 20% | Higher RS = sector/stock leadership |

### 2.5 Python Implementation

```python
import pandas as pd
import pandas_ta as ta


def pullback_scanner(df: pd.DataFrame) -> bool:
    """
    df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
    Returns True if the latest bar passes the pullback scan.
    """
    if len(df) < 200:
        return False

    close = df["close"].iloc[-1]
    sma_50 = ta.sma(df["close"], length=50).iloc[-1]
    sma_200 = ta.sma(df["close"], length=200).iloc[-1]
    ema_20 = ta.ema(df["close"], length=20).iloc[-1]
    rsi_14 = ta.rsi(df["close"], length=14).iloc[-1]
    adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
    adx_val = adx_df["ADX_14"].iloc[-1]
    vol_sma_5 = ta.sma(df["volume"], length=5).iloc[-1]
    vol_sma_20 = ta.sma(df["volume"], length=20).iloc[-1]

    return (
        close > sma_50
        and close > sma_200
        and sma_50 > sma_200
        and 30 <= rsi_14 <= 50
        and abs(close - ema_20) / ema_20 <= 0.05
        and vol_sma_5 < vol_sma_20
        and adx_val > 25
    )
```

### 2.6 Expected Hit Rate

In a normal bull market, this scanner typically returns 10-30 names per day from a 2,500-stock universe. During broad market pullbacks, the count rises. During strong rallies with no pullback, the count drops to near zero (which is correct behavior -- there are no pullback entries to take).

### 2.7 Strategy Connection

Stocks passing this scan feed directly into the Pullback/Retracement Trading strategy documented in `04-swing-trading-strategies.md` Section 1.3. Entry rules, stop placement, and targets are defined there.

---

## 3. Breakout Scanner

### 3.1 Concept

This scanner identifies stocks approaching or breaking through significant resistance levels on expanding volume with a compression setup (Bollinger Band squeeze). The combination of proximity to highs, volume expansion, and volatility compression creates high-probability breakout candidates.

### 3.2 Exact Parameters

| Parameter | Condition | Value |
|-----------|-----------|-------|
| Price vs. 52-week high | Within 2% | `close >= high_52w * 0.98` |
| Volume today | Above average | `volume > avg_volume(20) * 1.5` |
| ADX(14) | Above and rising | `ADX(14) > 20` AND `ADX(14) > ADX(14)[5 bars ago]` |
| Bollinger Band Width | At 6-month low | `bbw(20,2) <= min(bbw(20,2) over 126 bars)` |
| Price vs. upper BB | Approaching or touching | `close >= upper_bb * 0.98` |

### 3.3 Logic Flow

```
Step 1: close >= 52_week_high * 0.98              -- Near breakout level
Step 2: volume > SMA(volume, 20) * 1.5            -- Volume surge
Step 3: ADX(14) > 20                              -- Directional move developing
Step 4: ADX(14) > ADX(14, 5 bars ago)             -- ADX trending higher
Step 5: BB_width <= min(BB_width, 126 bars)        -- Volatility squeeze
```

**Important:** Not all five conditions need to fire simultaneously. The scanner can be tiered:

- **Tier 1 (Watch):** Steps 1 + 5 (near high + squeeze). Add to watchlist.
- **Tier 2 (Alert):** Steps 1 + 3 + 5 (near high + squeeze + ADX confirming).
- **Tier 3 (Trade):** All five conditions met. Execute per breakout strategy.

### 3.4 Bollinger Band Width Calculation

Bollinger Band Width (BBW) measures the distance between the upper and lower bands relative to the middle band:

```
BBW = (Upper Band - Lower Band) / Middle Band
```

A 6-month low in BBW signals that volatility has compressed significantly, which often precedes a sharp directional move. See `02-technical-indicators.md` Section 4 for full Bollinger Band formulas.

### 3.5 Python Implementation

```python
def breakout_scanner(df: pd.DataFrame) -> dict:
    """
    Returns a dict with 'passes' (bool) and 'tier' (int).
    """
    if len(df) < 252:
        return {"passes": False, "tier": 0}

    close = df["close"].iloc[-1]
    volume = df["volume"].iloc[-1]
    high_52w = df["high"].rolling(252).max().iloc[-1]
    vol_avg_20 = ta.sma(df["volume"], length=20).iloc[-1]

    # ADX
    adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
    adx_now = adx_df["ADX_14"].iloc[-1]
    adx_5ago = adx_df["ADX_14"].iloc[-6] if len(adx_df) > 6 else 0

    # Bollinger Bands
    bb = ta.bbands(df["close"], length=20, std=2)
    bb_upper = bb["BBU_20_2.0"].iloc[-1]
    bb_lower = bb["BBL_20_2.0"].iloc[-1]
    bb_mid = bb["BBM_20_2.0"].iloc[-1]
    bbw_current = (bb_upper - bb_lower) / bb_mid

    # BB width over last 126 bars
    bb_upper_series = bb["BBU_20_2.0"].iloc[-126:]
    bb_lower_series = bb["BBL_20_2.0"].iloc[-126:]
    bb_mid_series = bb["BBM_20_2.0"].iloc[-126:]
    bbw_series = (bb_upper_series - bb_lower_series) / bb_mid_series
    bbw_at_6m_low = bbw_current <= bbw_series.min() * 1.05  # 5% tolerance

    near_high = close >= high_52w * 0.98
    volume_surge = volume > vol_avg_20 * 1.5
    adx_above = adx_now > 20
    adx_rising = adx_now > adx_5ago

    tier = 0
    if near_high and bbw_at_6m_low:
        tier = 1
    if near_high and bbw_at_6m_low and adx_above:
        tier = 2
    if near_high and volume_surge and adx_above and adx_rising and bbw_at_6m_low:
        tier = 3

    return {"passes": tier > 0, "tier": tier}
```

### 3.6 False Breakout Protection

Breakout scanners have high false-positive rates (30-50% of breakouts fail). Mitigation strategies:

1. **Volume confirmation:** Require volume > 1.5x average. Breakouts on low volume fail more often.
2. **Wait for close above resistance:** Do not buy on an intraday touch. Wait for a daily close above the level.
3. **Retest entry:** Wait for a pullback to the breakout level that holds as support. This reduces entries but improves win rate.
4. **Sector confirmation:** The stock's sector ETF should be in an uptrend or at least not in a downtrend.

See `04-swing-trading-strategies.md` Section 1.4 for complete breakout entry and exit rules.

---

## 4. Mean Reversion Scanner

### 4.1 Concept

This scanner identifies stocks that have been pushed to statistical extremes and are likely to revert toward their mean. Mean reversion has empirical support at short horizons (see `10-empirical-evidence-and-edge-quality.md` Section 2), but the edge is more fragile and more sensitive to execution costs than momentum.

### 4.2 Exact Parameters

| Parameter | Condition | Value |
|-----------|-----------|-------|
| Price vs. Lower Bollinger Band | Below | `close < BB_lower(20, 2.0)` |
| RSI(14) | Oversold | `RSI(14) < 30` |
| Price vs. Support | At or near | `close within 2% of identified support level` |
| ADX(14) | Below threshold | `ADX(14) < 20` (ranging, not trending) |
| Volume | Spike | `volume > avg_volume(20) * 2.0` (potential capitulation) |

### 4.3 Logic Flow

```
Step 1: close < BB_lower(20, 2)                    -- Below lower Bollinger Band
Step 2: RSI(14) < 30                               -- Oversold
Step 3: ADX(14) < 20                               -- Ranging market (not trending down)
Step 4: volume > SMA(volume, 20) * 2.0             -- Volume spike (capitulation)
Step 5: close within 2% of prior support level     -- Near support
```

### 4.4 Support Level Identification

The "near support" condition requires a reference support level. Automated approaches:

| Method | Implementation | Reliability |
|--------|---------------|-------------|
| Prior swing low | Lowest close in last 20-60 bars | Good |
| Round number | Price within 2% of $10, $20, $50, $100 increments | Moderate |
| High-volume node | Price level with highest volume in last 60 bars (volume profile) | Best |
| 200 SMA | `close within 3% of SMA(200)` | Good for long-term support |

```python
def find_swing_lows(df: pd.DataFrame, lookback: int = 60, window: int = 5) -> list:
    """
    Find swing lows: bars where the low is lower than the surrounding
    'window' bars on each side.
    """
    lows = []
    data = df["low"].iloc[-lookback:]
    for i in range(window, len(data) - window):
        if all(data.iloc[i] <= data.iloc[i - j] for j in range(1, window + 1)):
            if all(data.iloc[i] <= data.iloc[i + j] for j in range(1, window + 1)):
                lows.append(data.iloc[i])
    return lows
```

### 4.5 Python Implementation

```python
def mean_reversion_scanner(df: pd.DataFrame) -> bool:
    """
    Returns True if the latest bar passes the mean reversion scan.
    """
    if len(df) < 200:
        return False

    close = df["close"].iloc[-1]
    volume = df["volume"].iloc[-1]

    # Bollinger Bands
    bb = ta.bbands(df["close"], length=20, std=2)
    bb_lower = bb["BBL_20_2.0"].iloc[-1]

    # RSI
    rsi_14 = ta.rsi(df["close"], length=14).iloc[-1]

    # ADX
    adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
    adx_val = adx_df["ADX_14"].iloc[-1]

    # Volume spike
    vol_avg_20 = ta.sma(df["volume"], length=20).iloc[-1]

    # Support: use nearest swing low
    swing_lows = find_swing_lows(df, lookback=60, window=5)
    near_support = False
    if swing_lows:
        nearest_support = min(swing_lows, key=lambda x: abs(x - close))
        near_support = abs(close - nearest_support) / nearest_support <= 0.02

    return (
        close < bb_lower
        and rsi_14 < 30
        and adx_val < 20
        and volume > vol_avg_20 * 2.0
        and near_support
    )
```

### 4.6 Critical Warnings

Mean reversion scanning is the most dangerous of all scanner types because:

1. **Stocks can stay oversold.** A low RSI in a strong downtrend is a feature, not a bug. The ADX < 20 filter is essential to exclude trending declines.
2. **Execution cost matters more.** See `10-empirical-evidence-and-edge-quality.md` Section 2: "Reversal edges are usually more sensitive to spreads, slippage, borrow costs."
3. **Earnings risk.** A stock dropping to mean reversion levels before earnings may be pricing in bad news. Always check the earnings calendar.
4. **Sector context.** If the entire sector is declining, the stock is likely following sector rotation, not mean-reverting. Add a sector filter.

---

## 5. Momentum Scanner

### 5.1 Concept

This scanner finds stocks showing strong relative and absolute momentum with aligned moving averages, confirmed by MACD and volume. Momentum is the most empirically supported edge in swing trading (see `10-empirical-evidence-and-edge-quality.md` Section 1).

### 5.2 Exact Parameters

| Parameter | Condition | Value |
|-----------|-----------|-------|
| Relative Strength vs. SPY (20-day) | Positive | `RS_ratio > 0` (outperforming S&P 500) |
| MA alignment | Bullish stack | `close > EMA(20) > SMA(50)` |
| MACD | Bullish | `MACD_line > signal_line` AND `MACD_line > 0` |
| Volume | Above average | `volume > SMA(volume, 20)` |

### 5.3 Relative Strength Calculation

Relative strength (not RSI) measures a stock's performance against a benchmark:

```python
def relative_strength_vs_spy(stock_df: pd.DataFrame, spy_df: pd.DataFrame,
                              period: int = 20) -> float:
    """
    Returns the relative strength ratio over the given period.
    Positive = outperforming SPY. Negative = underperforming.
    """
    stock_return = (
        stock_df["close"].iloc[-1] / stock_df["close"].iloc[-period] - 1
    )
    spy_return = (
        spy_df["close"].iloc[-1] / spy_df["close"].iloc[-period] - 1
    )
    return stock_return - spy_return
```

### 5.4 Logic Flow

```
Step 1: RS vs SPY (20-day) > 0                    -- Outperforming the market
Step 2: close > EMA(20) > SMA(50)                 -- MAs aligned bullishly
Step 3: MACD(12,26,9) > MACD_signal(9)            -- MACD bullish crossover
Step 4: MACD(12,26,9) > 0                         -- Above zero line
Step 5: volume > SMA(volume, 20)                   -- Volume confirmation
```

### 5.5 Python Implementation

```python
def momentum_scanner(df: pd.DataFrame, spy_df: pd.DataFrame) -> bool:
    """
    Returns True if the latest bar passes the momentum scan.
    Requires both the stock DataFrame and the SPY DataFrame.
    """
    if len(df) < 200 or len(spy_df) < 200:
        return False

    close = df["close"].iloc[-1]
    volume = df["volume"].iloc[-1]

    # Relative strength
    rs = relative_strength_vs_spy(df, spy_df, period=20)

    # Moving averages
    ema_20 = ta.ema(df["close"], length=20).iloc[-1]
    sma_50 = ta.sma(df["close"], length=50).iloc[-1]

    # MACD
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    macd_line = macd_df["MACD_12_26_9"].iloc[-1]
    signal_line = macd_df["MACDs_12_26_9"].iloc[-1]

    # Volume
    vol_avg_20 = ta.sma(df["volume"], length=20).iloc[-1]

    return (
        rs > 0
        and close > ema_20 > sma_50
        and macd_line > signal_line
        and macd_line > 0
        and volume > vol_avg_20
    )
```

### 5.6 Momentum Scoring

When the scanner returns many results (common in strong bull markets), rank by momentum quality:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Relative Strength vs. SPY (20d) | 30% | Higher outperformance = higher score |
| Relative Strength vs. SPY (60d) | 20% | Longer-term momentum confirmation |
| MACD histogram value | 15% | Larger positive histogram = stronger momentum |
| Volume ratio (today / 20d avg) | 15% | Higher ratio = more conviction |
| Distance above 50 SMA (%) | 20% | Moderate (5-15%) is ideal; too far (>25%) = extended |

```python
def momentum_score(df: pd.DataFrame, spy_df: pd.DataFrame) -> float:
    """
    Returns a 0-100 score for momentum quality.
    """
    rs_20 = relative_strength_vs_spy(df, spy_df, period=20)
    rs_60 = relative_strength_vs_spy(df, spy_df, period=60)

    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    macd_hist = macd_df["MACDh_12_26_9"].iloc[-1]

    vol_ratio = df["volume"].iloc[-1] / ta.sma(df["volume"], length=20).iloc[-1]

    close = df["close"].iloc[-1]
    sma_50 = ta.sma(df["close"], length=50).iloc[-1]
    dist_above_50 = (close - sma_50) / sma_50

    # Normalize each factor to 0-1 range (capped)
    rs_20_score = min(max(rs_20 * 10, 0), 1)     # 10% outperformance = max
    rs_60_score = min(max(rs_60 * 5, 0), 1)      # 20% outperformance = max
    macd_score = min(max(macd_hist / 2, 0), 1)    # Normalized by price context
    vol_score = min(max((vol_ratio - 1) / 2, 0), 1)  # 3x avg = max
    # Distance: 5-15% ideal, penalize >25%
    if 0.05 <= dist_above_50 <= 0.15:
        dist_score = 1.0
    elif dist_above_50 < 0.05:
        dist_score = dist_above_50 / 0.05
    else:
        dist_score = max(1.0 - (dist_above_50 - 0.15) / 0.10, 0)

    score = (
        rs_20_score * 0.30
        + rs_60_score * 0.20
        + macd_score * 0.15
        + vol_score * 0.15
        + dist_score * 0.20
    ) * 100

    return round(score, 1)
```

---

## 6. Gap Scanner

### 6.1 Concept

This scanner identifies stocks that have gapped up or down significantly on above-average volume. Gaps represent a sudden shift in supply/demand and often lead to continuation moves, especially when supported by a catalyst (see `10-empirical-evidence-and-edge-quality.md` Section 3 on post-earnings drift and catalyst-driven moves).

### 6.2 Exact Parameters

| Parameter | Condition | Value |
|-----------|-----------|-------|
| Gap size | Up > 2% | `open_today / close_yesterday - 1 > 0.02` |
| Volume | Above average | `volume > SMA(volume, 20) * 1.5` |
| Pre-market volume | Significant | `premarket_volume > 100,000 shares` (requires pre-market data) |
| Gap type | Classify | Breakaway, Continuation, or Exhaustion |

### 6.3 Gap Classification

| Gap Type | Characteristics | Trade Approach |
|----------|----------------|---------------|
| **Breakaway Gap** | Gaps out of a consolidation range; high volume; often at 52-week high | Trade for continuation; do NOT fade |
| **Continuation (Runaway) Gap** | Occurs mid-trend; volume moderate-to-high; trend already established | Trade for continuation with trailing stop |
| **Exhaustion Gap** | Occurs after extended move; volume spike but price reversal follows | Fade the gap or avoid entirely |
| **Common Gap** | Small gap within trading range; low volume | Usually fills; low-probability setup |

### 6.4 Gap Fill vs. Gap Continuation Criteria

**Trade for gap continuation when:**
- Gap is > 3% on volume > 2x average
- Stock was in an uptrend before the gap (close > 50 SMA)
- A catalyst exists (earnings, FDA approval, analyst upgrade)
- Price holds above gap-open level in first 30 minutes of trading
- Sector is also strong

**Trade for gap fill (fade) when:**
- Gap is 2-4% on only moderate volume (1-1.5x average)
- No clear catalyst
- Stock was not in a trend (ADX < 20)
- Gap into resistance rather than out of consolidation
- First 15 minutes shows rejection candle (long upper wick)

### 6.5 Python Implementation

```python
def gap_scanner(df: pd.DataFrame, min_gap_pct: float = 0.02) -> dict:
    """
    Analyzes the most recent bar for gap conditions.
    Returns dict with gap info or None if no gap.
    """
    if len(df) < 50:
        return None

    open_today = df["open"].iloc[-1]
    close_yesterday = df["close"].iloc[-2]
    volume_today = df["volume"].iloc[-1]
    vol_avg_20 = ta.sma(df["volume"], length=20).iloc[-2]  # use yesterday's avg

    gap_pct = (open_today / close_yesterday) - 1

    if abs(gap_pct) < min_gap_pct:
        return None

    # Classify gap context
    sma_50 = ta.sma(df["close"], length=50).iloc[-2]
    adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
    adx_val = adx_df["ADX_14"].iloc[-2]

    # Was price in a consolidation? Check if BB width is at 20-bar low
    bb = ta.bbands(df["close"], length=20, std=2)
    bb_upper = bb["BBU_20_2.0"]
    bb_lower = bb["BBL_20_2.0"]
    bb_mid = bb["BBM_20_2.0"]
    bbw = (bb_upper - bb_lower) / bb_mid
    in_squeeze = bbw.iloc[-2] <= bbw.iloc[-22:-2].min() * 1.10

    direction = "up" if gap_pct > 0 else "down"
    vol_ratio = volume_today / vol_avg_20 if vol_avg_20 > 0 else 0

    # Simple gap type classification
    if in_squeeze and vol_ratio > 2.0:
        gap_type = "breakaway"
    elif adx_val > 25 and close_yesterday > sma_50:
        gap_type = "continuation"
    elif adx_val > 30 and vol_ratio > 2.5:
        gap_type = "exhaustion"  # extended trend + huge volume
    else:
        gap_type = "common"

    return {
        "direction": direction,
        "gap_pct": round(gap_pct * 100, 2),
        "volume_ratio": round(vol_ratio, 2),
        "gap_type": gap_type,
        "in_uptrend": close_yesterday > sma_50,
        "tradeable": gap_type in ("breakaway", "continuation") and vol_ratio > 1.5,
    }
```

### 6.6 Pre-Market Scanning

Gap scanning is most useful in the 30-60 minutes before market open:

| Timeframe | Data Source | Action |
|-----------|------------|--------|
| 7:00 - 8:00 AM ET | Pre-market movers API | Initial gap list, filter by size and volume |
| 8:00 - 9:00 AM ET | Pre-market data + news | Classify gaps, check catalysts, set alerts |
| 9:00 - 9:30 AM ET | Pre-market OHLCV | Finalize watchlist, set entry orders |
| 9:30 - 10:00 AM ET | First 30 min of trading | Confirm gap hold/fill, execute strategy |

See `06-apis-and-technology.md` Section 1 for API options that provide pre-market data. Not all free APIs (e.g., yfinance) support real-time pre-market quotes.

---

## 7. Sector Rotation Scanner

### 7.1 Concept

This scanner ranks sectors by relative strength and momentum to identify where institutional money is flowing. Sector rotation is a top-down strategy that narrows the stock universe to the strongest (or weakest, for shorts) sectors. See `04-swing-trading-strategies.md` Section 3.3 for the full sector rotation strategy.

### 7.2 Sector ETF Universe

| Sector | ETF | Description |
|--------|-----|-------------|
| Technology | XLK | Mega-cap tech |
| Healthcare | XLV | Pharma, biotech, health services |
| Financials | XLF | Banks, insurance, capital markets |
| Consumer Discretionary | XLY | Retail, autos, entertainment |
| Consumer Staples | XLP | Food, beverage, household |
| Energy | XLE | Oil, gas, energy equipment |
| Industrials | XLI | Aerospace, defense, machinery |
| Materials | XLB | Chemicals, metals, packaging |
| Utilities | XLU | Electric, gas, water utilities |
| Real Estate | XLRE | REITs |
| Communication Services | XLC | Telecom, media, internet |
| Semiconductors | SMH | Semi-specific (not GICS sector but trades like one) |

### 7.3 Relative Strength Ranking

Rank each sector ETF by performance over multiple timeframes:

```python
import yfinance as yf


def sector_rotation_ranking(period_weights: dict = None) -> pd.DataFrame:
    """
    Ranks sector ETFs by weighted relative strength.
    Default weights emphasize recent performance.
    """
    if period_weights is None:
        period_weights = {5: 0.35, 20: 0.35, 60: 0.30}

    sectors = {
        "XLK": "Technology", "XLV": "Healthcare", "XLF": "Financials",
        "XLY": "Cons. Disc.", "XLP": "Cons. Staples", "XLE": "Energy",
        "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities",
        "XLRE": "Real Estate", "XLC": "Communication", "SMH": "Semis",
    }

    tickers = list(sectors.keys()) + ["SPY"]
    data = yf.download(tickers, period="6mo", interval="1d", progress=False)["Close"]

    spy = data["SPY"]
    results = []

    for ticker, name in sectors.items():
        sector_data = data[ticker]
        weighted_rs = 0

        for period, weight in period_weights.items():
            sector_ret = sector_data.iloc[-1] / sector_data.iloc[-period] - 1
            spy_ret = spy.iloc[-1] / spy.iloc[-period] - 1
            rs = sector_ret - spy_ret
            weighted_rs += rs * weight

        results.append({
            "ticker": ticker,
            "sector": name,
            "weighted_rs": round(weighted_rs * 100, 2),
            "5d_return": round(
                (sector_data.iloc[-1] / sector_data.iloc[-5] - 1) * 100, 2
            ),
            "20d_return": round(
                (sector_data.iloc[-1] / sector_data.iloc[-20] - 1) * 100, 2
            ),
            "60d_return": round(
                (sector_data.iloc[-1] / sector_data.iloc[-60] - 1) * 100, 2
            ),
        })

    ranking = pd.DataFrame(results).sort_values("weighted_rs", ascending=False)
    ranking["rank"] = range(1, len(ranking) + 1)
    return ranking.reset_index(drop=True)
```

### 7.4 Money Flow Indicators

Beyond price-based relative strength, volume and money flow indicators add conviction:

| Indicator | What It Measures | Scanner Rule |
|-----------|-----------------|-------------|
| OBV slope (20-day) | Cumulative volume pressure | Rising OBV = money flowing in |
| Chaikin Money Flow (21) | Buying/selling pressure | CMF > 0.05 = strong inflow |
| Volume ratio | Current vs. average volume | Sector vol > 1.2x average |
| RS Momentum | Change in RS rank over 5 days | Improving rank = emerging leader |

### 7.5 Cross-Sector Momentum Signals

| Signal | Interpretation | Action |
|--------|---------------|--------|
| Top 3 sectors all improving | Broad market strength | Increase long exposure |
| Bottom 3 sectors all weakening | Broad weakness building | Tighten stops, reduce positions |
| Defensive sectors (XLU, XLP) rising to top | Risk-off rotation | Reduce aggressive longs, consider hedges |
| Cyclicals (XLI, XLB, XLY) at top | Risk-on rotation | Favor growth and momentum longs |
| Energy diverging strongly | Commodity cycle shift | Check oil, inflation expectations |
| Semis (SMH) leading | Tech bull market likely | Overweight tech individual names |

### 7.6 Implementation Strategy

1. Run the sector ranking daily at market close.
2. Focus individual stock scanners (Sections 2-6) on the top 3-4 sectors.
3. Avoid initiating new longs in the bottom 3 sectors.
4. When sector leadership changes (a new sector enters top 3), start building a watchlist in that sector.
5. Rotate holdings gradually -- do not dump all positions at once.

---

## 8. Watchlist Management

### 8.1 Watchlist Structure

Maintain two distinct watchlists with clear roles:

| Watchlist | Size | Purpose | Update Frequency |
|-----------|------|---------|-----------------|
| **Primary** | 5-10 stocks | Ready to trade within 1-2 days | Daily |
| **Secondary** | 20-30 stocks | Developing setups, not yet actionable | Every 2-3 days |

### 8.2 Primary Watchlist Requirements

A stock earns a spot on the primary watchlist only when:

1. It passed at least one scanner (Sections 2-6) within the last 2 trading days.
2. It has a defined entry price, stop-loss level, and target price.
3. Position size is pre-calculated using the method from `05-risk-management.md` Section 1.
4. No earnings announcement within the planned holding period (unless the trade is catalyst-based).
5. The stock's sector is not in the bottom 3 of the sector rotation ranking.

**Primary watchlist entry format:**

| Field | Example |
|-------|---------|
| Ticker | AAPL |
| Setup Type | Pullback |
| Scanner Date | 2026-03-06 |
| Entry Price | $185.50 (limit order) |
| Stop Loss | $179.00 (-3.5%) |
| Target 1 | $195.00 (+5.1%) |
| Target 2 | $202.00 (+8.9%) |
| R:R Ratio | 1:1.5 / 1:2.5 |
| Position Size | 150 shares ($27,825) |
| Risk Amount | $975 (0.97% of $100K account) |
| Sector RS Rank | 2 / 12 |
| Notes | Above 50 SMA, RSI at 42, volume declining |

### 8.3 Secondary Watchlist Requirements

A stock earns a spot on the secondary watchlist when:

1. It shows one or more (but not all) conditions for a scanner setup.
2. The setup is developing but not yet at an actionable entry point.
3. The stock has favorable sector and market context.

**Secondary watchlist entry format (simplified):**

| Field | Example |
|-------|---------|
| Ticker | MSFT |
| Potential Setup | Breakout (Tier 1) |
| What's Missing | Volume confirmation, ADX still below 20 |
| Key Level | $420 (52-week high) |
| Alert Trigger | Price > $418 AND volume > 1.5x avg |
| Added | 2026-03-04 |

### 8.4 Organization by Setup Type

Group watchlist entries by scanner type for efficient daily review:

```
WATCHLIST - 2026-03-08
========================

PULLBACKS (3):
  AAPL  - RSI 42, 2% from 20 EMA, ADX 28     [PRIMARY]
  AMZN  - RSI 38, touching 20 EMA, ADX 32     [PRIMARY]
  HD    - RSI 45, 3% from 20 EMA, ADX 24      [SECONDARY - ADX borderline]

BREAKOUTS (2):
  NVDA  - 1% from 52w high, BB squeeze active  [SECONDARY - needs volume]
  CRM   - At resistance, ADX 22 and rising      [SECONDARY - needs breakout]

MOMENTUM (2):
  META  - RS +4.2%, MAs aligned, MACD bullish  [PRIMARY]
  NFLX  - RS +3.1%, MAs aligned                [PRIMARY]

MEAN REVERSION (1):
  PFE   - Below BB, RSI 27, at support         [SECONDARY - ADX 22, too high]

GAPS (1):
  TSLA  - Gap up 4.2% on 2.5x vol, breakaway  [PRIMARY - entered at open]
```

### 8.5 Daily Watchlist Maintenance Routine

| Time (ET) | Task | Duration |
|-----------|------|----------|
| 7:00 - 7:30 AM | Pre-market gap scan. Check overnight news for watchlist stocks. | 30 min |
| 7:30 - 8:00 AM | Review primary watchlist. Update entry/stop levels. Set alerts. | 30 min |
| 8:00 - 9:00 AM | Run pre-market scanners. Review sector rotation ranking. | 60 min |
| 9:30 - 10:00 AM | Execute entries on primary watchlist if triggered. Monitor gaps. | 30 min |
| 12:00 - 12:30 PM | Mid-day review. Check open positions. Adjust stops. | 30 min |
| 4:00 - 5:00 PM | Post-market scan. Run all scanners on daily close data. | 60 min |
| 5:00 - 5:30 PM | Update watchlists. Promote/demote between primary and secondary. | 30 min |
| Weekend | Full universe scan. Deep review of sector rotation. Clean up watchlists. | 2-3 hours |

### 8.6 Watchlist Scoring and Ranking System

Assign a composite score (0-100) to each watchlist entry to prioritize attention:

| Factor | Weight | Scoring Criteria |
|--------|--------|-----------------|
| Setup completeness | 25% | All scanner conditions met = 100; 4 of 5 = 80; 3 of 5 = 60 |
| Risk/reward ratio | 20% | R:R >= 3:1 = 100; 2:1 = 75; 1.5:1 = 50; < 1:1 = 0 |
| Sector RS rank | 15% | Top 3 = 100; Top 6 = 60; Bottom 6 = 20; Bottom 3 = 0 |
| Market regime alignment | 15% | Setup matches regime (e.g., long in bull) = 100; neutral = 50; counter-trend = 0 |
| Volume confirmation | 10% | Volume > 2x avg = 100; > 1.5x = 75; > 1x = 50; below avg = 25 |
| Catalyst proximity | 15% | Post-earnings drift = 100; no catalyst = 50; pre-earnings = 20 |

**Score interpretation:**

| Score | Action |
|-------|--------|
| 80-100 | Highest conviction. Full position size. Primary watchlist. |
| 60-79 | Good setup. Standard position size. Primary watchlist. |
| 40-59 | Developing. Half position or wait. Secondary watchlist. |
| < 40 | Remove from watchlist. Not actionable. |

---

## 9. Filtering Pipeline

The filtering pipeline is a systematic, multi-step process that transforms a raw universe of thousands of stocks into a ranked list of 5-10 actionable trade candidates. Each step is a gate -- a stock must pass all preceding steps to reach the next.

### 9.1 Pipeline Overview

```
STEP 1: Universe Filter (2,500+ stocks --> ~1,500)
    |
STEP 2: Trend Filter (~1,500 --> ~500-800)
    |
STEP 3: Setup Filter (~500-800 --> 20-50)
    |
STEP 4: Quality Filter (20-50 --> 10-20)
    |
STEP 5: Final Ranking (10-20 --> 5-10 actionable)
```

### 9.2 Step 1: Universe Filter

**Purpose:** Eliminate untradeable stocks. This runs first because it is the cheapest computation and removes the most candidates.

| Criterion | Threshold | Implementation |
|-----------|-----------|---------------|
| Price | > $10.00 | `close > 10` |
| Avg Daily Volume (20d) | > 500,000 shares | `SMA(volume, 20) > 500000` |
| Market Cap | > $2B | `market_cap > 2_000_000_000` |
| Exchange | NYSE, NASDAQ | Exclude OTC, Pink Sheets |
| Stock Type | Common stock only | Exclude ETFs, ETNs, warrants, preferreds (for stock scanners) |
| Days Since IPO | > 60 | Sufficient history for indicators |

**Approximate reduction:** 5,000+ listed securities --> ~1,200-1,800 tradeable stocks.

### 9.3 Step 2: Trend Filter

**Purpose:** Separate stocks by trend direction to route them to the appropriate scanner. See `08-market-structure-and-conditions.md` for the market regime framework that determines which trend direction to favor.

| Trend State | Criteria | Route To |
|-------------|----------|----------|
| **Strong Uptrend** | `close > SMA(50) > SMA(200)` AND `ADX > 25` | Pullback, Breakout, Momentum scanners |
| **Moderate Uptrend** | `close > SMA(200)` AND `SMA(50) > SMA(200)` | Pullback, Momentum scanners |
| **Neutral/Range** | `SMA(50) within 3% of SMA(200)` AND `ADX < 20` | Mean Reversion scanner |
| **Moderate Downtrend** | `close < SMA(200)` | Mean Reversion (with caution), Short setups |
| **Strong Downtrend** | `close < SMA(50) < SMA(200)` AND `ADX > 25` | Avoid longs; short-side scanners only |

### 9.4 Step 3: Setup Filter

**Purpose:** Apply the specific scanner criteria from Sections 2-6. This is where the exact technical conditions are checked.

Each scanner runs independently on the stocks that passed the appropriate trend filter:

```python
def apply_setup_filters(universe: pd.DataFrame, spy_df: pd.DataFrame) -> dict:
    """
    Runs all scanners on the filtered universe.
    Returns a dict of scanner_name -> list of tickers.
    """
    results = {
        "pullback": [],
        "breakout": [],
        "mean_reversion": [],
        "momentum": [],
        "gap": [],
    }

    for ticker in universe.index:
        df = get_daily_data(ticker)  # fetch OHLCV data

        if pullback_scanner(df):
            results["pullback"].append(ticker)

        breakout_result = breakout_scanner(df)
        if breakout_result["passes"]:
            results["breakout"].append((ticker, breakout_result["tier"]))

        if mean_reversion_scanner(df):
            results["mean_reversion"].append(ticker)

        if momentum_scanner(df, spy_df):
            results["momentum"].append(ticker)

        gap_result = gap_scanner(df)
        if gap_result and gap_result["tradeable"]:
            results["gap"].append((ticker, gap_result))

    return results
```

### 9.5 Step 4: Quality Filter

**Purpose:** Eliminate stocks that pass technical criteria but have fundamental or event-driven risks.

| Check | Rule | Rationale |
|-------|------|-----------|
| Earnings date | No earnings within next 5 trading days (configurable) | Avoid binary event risk |
| Recent news | No pending FDA decisions, lawsuits, M&A rumors | Reduce unquantifiable risk |
| Sector health | Sector ETF RS rank not in bottom 3 | Avoid sector headwinds |
| Short interest | Short interest < 20% of float (unless squeeze setup) | High SI = volatile and unpredictable |
| Average spread | Bid-ask spread < 0.10% of price | Execution cost control |
| Correlation check | Not highly correlated (> 0.85) with another stock already on watchlist | Portfolio diversification |

```python
def quality_filter(ticker: str, earnings_dates: dict,
                   sector_ranking: pd.DataFrame) -> dict:
    """
    Returns dict with 'passes' (bool) and 'reason' (str if failed).
    """
    info = get_ticker_info(ticker)

    # Earnings check
    next_earnings = earnings_dates.get(ticker)
    if next_earnings and (next_earnings - pd.Timestamp.today()).days <= 5:
        return {"passes": False, "reason": "earnings_within_5_days"}

    # Sector check
    sector = info.get("sector")
    sector_etf = SECTOR_TO_ETF.get(sector)
    if sector_etf:
        rank = sector_ranking.loc[
            sector_ranking["ticker"] == sector_etf, "rank"
        ]
        if not rank.empty and rank.iloc[0] > 9:  # bottom 3 of 12
            return {"passes": False, "reason": "weak_sector"}

    # Short interest check
    short_pct = info.get("shortPercentOfFloat", 0)
    if short_pct > 0.20:
        return {"passes": False, "reason": "high_short_interest"}

    return {"passes": True, "reason": None}
```

### 9.6 Step 5: Final Ranking and Selection

**Purpose:** Score and rank the remaining candidates to build the primary watchlist.

Apply the watchlist scoring system from Section 8.6, then:

1. Sort by composite score (descending).
2. Take the top 5-10 names for the primary watchlist.
3. Place the next 10-20 on the secondary watchlist.
4. Discard the rest (they can be re-scanned tomorrow).

**Diversification constraint:** No more than 2 stocks from the same sector on the primary watchlist. If a sector dominates the top scores, demote excess names to the secondary list.

```python
def final_ranking(candidates: list, max_primary: int = 10,
                  max_per_sector: int = 2) -> dict:
    """
    candidates: list of dicts with 'ticker', 'score', 'sector', 'setup_type'
    Returns dict with 'primary' and 'secondary' lists.
    """
    sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    primary = []
    secondary = []
    sector_counts = {}

    for c in sorted_candidates:
        sector = c["sector"]
        sector_counts.setdefault(sector, 0)

        if (
            len(primary) < max_primary
            and sector_counts[sector] < max_per_sector
            and c["score"] >= 60
        ):
            primary.append(c)
            sector_counts[sector] += 1
        else:
            secondary.append(c)

    return {"primary": primary, "secondary": secondary[:30]}
```

---

## 10. Implementation Notes

### 10.1 Full Pipeline Script

Below is a complete end-to-end scanning pipeline. For data API details, see `06-apis-and-technology.md`.

```python
"""
swing_scanner.py - Complete stock screening pipeline for swing trading.

Dependencies:
    pip install yfinance pandas pandas-ta

Usage:
    python swing_scanner.py
"""

import warnings
from datetime import datetime

import pandas as pd
import pandas_ta as ta
import yfinance as yf

warnings.filterwarnings("ignore")

# ---------- CONFIGURATION ----------

UNIVERSE_FILTERS = {
    "min_price": 10.0,
    "min_avg_volume": 500_000,
    "min_market_cap": 2_000_000_000,
}

SECTOR_ETFS = [
    "XLK", "XLV", "XLF", "XLY", "XLP", "XLE",
    "XLI", "XLB", "XLU", "XLRE", "XLC", "SMH",
]


# ---------- DATA FETCHING ----------

def get_sp500_tickers() -> list:
    """Fetch S&P 500 constituents from Wikipedia."""
    table = pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    )[0]
    return table["Symbol"].str.replace(".", "-", regex=False).tolist()


def fetch_data(tickers: list, period: str = "1y") -> dict:
    """
    Download daily OHLCV for a list of tickers.
    Returns dict of ticker -> DataFrame.
    """
    data = {}
    # Batch download for efficiency
    raw = yf.download(tickers, period=period, interval="1d",
                      group_by="ticker", progress=False, threads=True)
    for ticker in tickers:
        try:
            df = raw[ticker].dropna()
            if len(df) > 0:
                df.columns = [c.lower() for c in df.columns]
                data[ticker] = df
        except (KeyError, TypeError):
            continue
    return data


# ---------- UNIVERSE FILTER ----------

def universe_filter(data: dict) -> list:
    """Step 1: Filter by price, volume, and basic tradability."""
    passed = []
    for ticker, df in data.items():
        if len(df) < 50:
            continue
        close = df["close"].iloc[-1]
        avg_vol = df["volume"].iloc[-20:].mean()

        if (
            close > UNIVERSE_FILTERS["min_price"]
            and avg_vol > UNIVERSE_FILTERS["min_avg_volume"]
        ):
            passed.append(ticker)
    return passed


# ---------- SCANNER FUNCTIONS ----------
# (Use the scanner functions defined in Sections 2-6 above)


# ---------- MAIN PIPELINE ----------

def run_daily_scan():
    """Execute the complete daily screening pipeline."""
    print(f"=== Swing Trading Scanner - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    # Step 0: Get universe
    print("Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers()

    # Step 1: Download data
    print(f"Downloading data for {len(tickers)} tickers...")
    data = fetch_data(tickers)
    spy_df = fetch_data(["SPY"])["SPY"]
    print(f"Data retrieved for {len(data)} tickers.\n")

    # Step 2: Universe filter
    tradeable = universe_filter(data)
    print(f"Step 1 - Universe filter: {len(tradeable)} stocks pass.\n")

    # Step 3: Run scanners
    results = {
        "pullback": [],
        "breakout": [],
        "momentum": [],
        "mean_reversion": [],
        "gap": [],
    }

    for ticker in tradeable:
        df = data[ticker]

        if pullback_scanner(df):
            results["pullback"].append(ticker)

        br = breakout_scanner(df)
        if br["passes"]:
            results["breakout"].append(f"{ticker} (Tier {br['tier']})")

        if momentum_scanner(df, spy_df):
            score = momentum_score(df, spy_df)
            results["momentum"].append(f"{ticker} (Score: {score})")

        if mean_reversion_scanner(df):
            results["mean_reversion"].append(ticker)

        gr = gap_scanner(df)
        if gr and gr["tradeable"]:
            results["gap"].append(
                f"{ticker} ({gr['direction']} {gr['gap_pct']}%, {gr['gap_type']})"
            )

    # Step 4: Print results
    print("=" * 60)
    for scanner_name, hits in results.items():
        print(f"\n{scanner_name.upper()} SCANNER ({len(hits)} hits):")
        if hits:
            for h in hits:
                print(f"  - {h}")
        else:
            print("  (no results)")

    print("\n" + "=" * 60)
    print("Scan complete.")


if __name__ == "__main__":
    run_daily_scan()
```

### 10.2 API Endpoints for Real-Time Scanning

For production scanning beyond yfinance, see `06-apis-and-technology.md` for full API comparison. Summary of scanner-relevant capabilities:

| Provider | Real-Time | Pre-Market | Screening API | Cost |
|----------|-----------|------------|---------------|------|
| yfinance | No (15 min delay) | Limited | No (build your own) | Free |
| Alpha Vantage | Delayed | No | Technical indicators endpoint | Free tier / $49+/mo |
| Polygon.io | Yes | Yes | Snapshot endpoint (all tickers) | $29+/mo |
| Alpaca | Yes | Yes | No native screener | Free (with brokerage account) |
| TradingView | Yes | Yes | Built-in screener (Pine Script) | Free tier / $14.95+/mo |
| FinViz | Yes | Limited | Pre-built screener with export | Free tier / $39.50/mo |

**For a self-hosted scanner, the recommended stack is:**

1. **Data:** Polygon.io (real-time snapshots for all tickers in one API call).
2. **Compute:** pandas + pandas-ta for indicator calculation.
3. **Storage:** SQLite or PostgreSQL for historical data cache and scan results.
4. **Alerts:** Email, Slack webhook, or push notification for triggered setups.

### 10.3 Performance Considerations for Large Universes

| Universe Size | Approach | Estimated Time |
|---------------|----------|---------------|
| 500 (S&P 500) | Single batch download, in-memory scan | 2-5 minutes |
| 2,500 (full NYSE+NASDAQ) | Batched downloads (100 tickers per batch), parallel processing | 15-30 minutes |
| 8,000+ (all US equities) | Pre-cached database, incremental daily updates | 5-10 minutes (after initial load) |

**Optimization tips:**

1. **Cache historical data locally.** Download once, then append daily bars. Do not re-download full history every day.
2. **Pre-compute indicators.** Store SMA, EMA, RSI, ADX values in the database. Only recalculate the latest bar.
3. **Use vectorized operations.** pandas-ta calculates indicators for entire DataFrames at once -- do not loop row by row.
4. **Filter early.** Apply the universe filter before downloading full history. Use a lightweight endpoint (e.g., Polygon snapshot) to get current price and volume, then download history only for stocks that pass.
5. **Parallelize downloads.** Use `yf.download()` with `threads=True` or `concurrent.futures.ThreadPoolExecutor` for custom APIs.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def parallel_scan(tickers: list, scanner_func, max_workers: int = 10) -> list:
    """Run a scanner function on multiple tickers in parallel."""
    results = []

    def scan_one(ticker):
        df = get_cached_data(ticker)
        if df is not None and scanner_func(df):
            return ticker
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_one, t): t for t in tickers}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results
```

### 10.4 Scheduling Scans

| Scan Type | Schedule | Data Needed |
|-----------|----------|-------------|
| Pre-market gap scan | 7:30 AM ET daily | Pre-market OHLCV (requires real-time API) |
| Intraday momentum check | 10:00 AM ET, 1:00 PM ET | Intraday data |
| Post-market full scan | 4:30 PM ET daily (after data settles) | Daily OHLCV (free APIs work) |
| Sector rotation ranking | 5:00 PM ET daily | Daily closes for sector ETFs |
| Weekend deep scan | Saturday morning | Weekly OHLCV for full universe |
| Watchlist cleanup | Sunday evening | Review notes, remove stale entries |

**Cron job example (post-market scan):**

```bash
# Run daily at 4:30 PM ET (21:30 UTC) -- US market
30 21 * * 1-5 cd /path/to/project && python swing_scanner.py >> logs/scan_$(date +\%Y\%m\%d).log 2>&1

# Sweden: Run daily at 17:45 CET (16:45 UTC) -- after Stockholm close
45 16 * * 1-5 cd /path/to/project && python swing_scanner_se.py >> logs/scan_se_$(date +\%Y\%m\%d).log 2>&1
```

### 10.5 Scanner Validation via Backtesting

Before relying on any scanner in live trading, validate its output through backtesting (see `07-backtesting-and-performance.md` for methodology):

1. **Record scanner output daily for at least 60 trading days** before acting on it.
2. **Forward-test on paper:** Simulate entries on scanner hits using the corresponding strategy rules.
3. **Measure hit rate:** What percentage of scanner hits become profitable trades?
4. **Measure signal-to-noise:** How many scanner hits are false positives vs. actionable setups?

**Target metrics by scanner type:**

| Scanner | Expected Signal Rate | Expected Win Rate (with proper strategy) | Notes |
|---------|---------------------|------------------------------------------|-------|
| Pullback | 10-30 hits/day | 55-65% | Highest probability scanner |
| Breakout | 5-15 hits/day | 40-50% | High false positive rate; compensated by R:R |
| Mean Reversion | 3-10 hits/day | 50-60% | Smaller average win; sensitive to execution |
| Momentum | 15-40 hits/day | 45-55% | Needs ranking to prioritize; many hits in bull market |
| Gap | 5-20 hits/day | Varies by gap type | Breakaway gaps: 60%+; common gaps: 40% |
| Sector Rotation | N/A (ranking) | Improves all scanners by 5-10% | Overlay, not standalone |

---

## Appendix A: Quick Reference - Scanner Parameter Summary

| Scanner | Key Indicators | Critical Thresholds | Best Market Regime |
|---------|---------------|--------------------|--------------------|
| Pullback | SMA(50/200), EMA(20), RSI(14), ADX(14) | RSI 30-50, ADX > 25 | Bull market |
| Breakout | 52w High, Volume, ADX(14), BBW | Vol > 1.5x avg, BBW at 6m low | Bull or transitional |
| Mean Reversion | BB(20,2), RSI(14), ADX(14), Volume | RSI < 30, ADX < 20, Vol > 2x | Sideways/range |
| Momentum | RS vs SPY, EMA(20), SMA(50), MACD | RS > 0, MACD > 0 | Bull market |
| Gap | Open vs Prior Close, Volume | Gap > 2%, Vol > 1.5x avg | Any (catalyst-driven) |
| Sector Rotation | Sector ETF returns (5d/20d/60d) | RS ranking, CMF > 0.05 | Any |

## Appendix B: Sector-to-ETF Mapping (for code)

```python
SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Financials": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}

# Swedish market: Nasdaq Stockholm SX sector indices replace US sector ETFs.
# These are index tickers, not ETFs -- use for relative strength ranking.
# Swedish sector ETFs exist but have limited liquidity.
SWEDISH_SECTOR_INDICES = {
    "Energy": "SX10",        # SX10 Energy
    "Industrials": "SX20",   # SX20 Industrials (dominant sector in Sweden)
    "Consumer Discretionary": "SX25",
    "Consumer Staples": "SX30",
    "Healthcare": "SX35",
    "Financials": "SX40",    # SEB, Handelsbanken, Swedbank, Investor
    "Technology": "SX45",    # Ericsson, Hexagon, etc.
    "Telecom": "SX50",
    "Utilities": "SX55",
    "Real Estate": "SX60",   # Castellum, Sagax, etc.
}
```

## Appendix C: Recommended Daily Workflow Checklist

```
PRE-MARKET (7:00 - 9:30 AM ET):
[ ] Check overnight futures / global markets for regime context
[ ] Run gap scanner on pre-market movers
[ ] Review primary watchlist - any stocks triggered overnight?
[ ] Check news for watchlist stocks (earnings surprises, analyst actions)
[ ] Update entry orders for primary watchlist names
[ ] Review sector ETFs for pre-market strength/weakness

MARKET OPEN (9:30 - 10:30 AM ET):
[ ] Monitor gap scanner results through first 30 minutes
[ ] Execute entries on primary watchlist if triggered
[ ] Do NOT initiate new positions in first 15 minutes (noise period)

MID-DAY (12:00 - 1:00 PM ET):
[ ] Check open positions - adjust stops if needed
[ ] Quick scan for intraday setups developing (optional)

POST-MARKET (4:00 - 5:30 PM ET):
[ ] Run full scanner pipeline on daily closing data
[ ] Update sector rotation ranking
[ ] Score and rank all scanner hits
[ ] Update primary watchlist (promote/demote)
[ ] Update secondary watchlist
[ ] Set alerts for next-day entries
[ ] Log today's trades in journal (link to 05-risk-management.md Section 6)

WEEKEND:
[ ] Run full universe deep scan
[ ] Review weekly sector rotation trends
[ ] Clean up watchlists - remove stale entries (> 5 days without progress)
[ ] Review week's trades - identify patterns in winners/losers
[ ] Assess market regime for coming week (link to 08-market-structure-and-conditions.md)
```
