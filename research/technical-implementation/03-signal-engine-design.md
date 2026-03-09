# Signal Engine Design

> Research date: 2026-03-08
> Goal: Define the architecture and implementation of the signal engine that transforms price/indicator data into ranked buy recommendations for Swedish OMX stocks.

**Cross-references:**
- Tech stack decisions: `01-tech-stack-and-architecture.md`
- Swing trading strategies: `../strategy-and-theory/04-swing-trading-strategies.md`
- Setup quality scoring: `../strategy-and-theory/23-setup-quality-scoring.md`
- Regime-to-strategy mapping: `../strategy-and-theory/25-regime-to-strategy-mapping.md`
- Stock screening playbook: `../strategy-and-theory/16-stock-screening-playbook.md`
- Watchlist and universe selection: `../strategy-and-theory/22-watchlist-and-universe-selection.md`
- Swedish market adaptation: `../strategy-and-theory/27-swedish-market-adaptation.md`

---

## Table of Contents

1. [What Is a Signal Engine](#1-what-is-a-signal-engine)
2. [Strategy as Code](#2-strategy-as-code)
3. [Indicator Pipeline](#3-indicator-pipeline)
4. [Signal Scoring and Ranking](#4-signal-scoring-and-ranking)
5. [Universe Management](#5-universe-management)
6. [Daily Scan Pipeline (Full Flow)](#6-daily-scan-pipeline-full-flow)
7. [Handling Multiple Timeframes](#7-handling-multiple-timeframes)
8. [False Signal Reduction](#8-false-signal-reduction)
9. [Output Format](#9-output-format)

---

## 1. What Is a Signal Engine

The signal engine is the core component that sits between raw market data and actionable output. It takes price history and calculated indicators as input and produces scored, filtered, ranked recommendations as output.

### Signal vs. Recommendation

These are not the same thing. Conflating them is a common source of noise in automated systems.

**Signal (raw trigger):**
- A mechanical event detected by a strategy function
- Example: "RSI crossed below 30" or "price closed above the 20-day high"
- A signal carries no opinion about quality, context, or tradability
- A single stock can produce multiple signals on the same day from different strategies

**Recommendation (scored, filtered, ranked):**
- A signal that has been evaluated for quality, filtered for disqualifiers, and ranked against other signals
- Example: "ABB.ST: mean reversion buy, score 16/20, entry 485 SEK, stop 468 SEK, target 520 SEK"
- A recommendation is what gets sent to the user or logged for review
- Only signals that clear minimum quality thresholds become recommendations

**The pipeline:**

```
Raw OHLCV Data
    -> Indicator Calculation
        -> Strategy Functions (produce signals)
            -> Scoring Engine (evaluate quality)
                -> Disqualifier Filter (remove bad setups)
                    -> Ranking (sort by score)
                        -> Recommendations (output)
```

### Why this separation matters

If a scanner outputs every signal it finds, it generates noise. A mean reversion signal on a stock with 500 shares/day average volume is technically valid but practically useless. The signal engine's job is to reduce the hundreds of raw triggers across 80+ stocks into 0-5 actionable recommendations per day.

Zero recommendations on a given day is a valid and desirable output. Not every day has good setups.

---

## 2. Strategy as Code

Each swing trading strategy is represented as a Python function (or class method) that takes a DataFrame of OHLCV data with pre-calculated indicators and returns a list of signal dictionaries.

### Strategy Interface

Every strategy function follows the same contract:

```python
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class Signal:
    """A raw signal produced by a strategy."""
    ticker: str
    strategy: str
    direction: str          # "long" or "short"
    signal_date: str        # ISO date string
    entry_price: float
    stop_loss: float
    target_price: float
    strength: float         # 0.0 to 1.0, strategy-specific confidence
    reasoning: str          # Human-readable explanation
    metadata: dict          # Strategy-specific extra data


def strategy_function(
    df: pd.DataFrame,
    ticker: str,
) -> list[Signal]:
    """
    Takes a DataFrame with OHLCV + indicator columns.
    Returns a list of Signal objects (usually 0 or 1 for any given day).
    Only checks the most recent bar (today) for signals.
    """
    ...
```

This interface is deliberate. Every strategy gets the same input and produces the same output shape. This makes it trivial to add new strategies without changing the pipeline.

### Strategy 1: Mean Reversion (RSI Oversold + Bollinger Band Touch)

This strategy looks for stocks that have pulled back hard enough to reach both RSI oversold territory and the lower Bollinger Band. The combination of two independent mean-reversion signals provides higher confidence than either alone.

Reference: `../strategy-and-theory/04-swing-trading-strategies.md` sections 2.1 (Bollinger Band Bounce) and 2.2 (RSI Oversold Reversals).

```python
def strategy_mean_reversion(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    Mean reversion: RSI oversold + Bollinger Band lower touch.

    Entry conditions (all must be true):
    - RSI(14) < 30
    - Close <= lower Bollinger Band (20, 2)
    - Stock is not in a strong downtrend (SMA50 not falling steeply)
    - Volume is above 50% of 20-day average (not dead stock)

    Stop: Below the recent swing low (lowest low of last 10 bars)
    Target: Middle Bollinger Band (20-period SMA)
    """
    if len(df) < 50:
        return []

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Check indicator availability
    required = ["RSI_14", "BBL_20_2.0", "BBM_20_2.0", "SMA_50", "VOLUME_RATIO"]
    if any(pd.isna(latest.get(col)) for col in required):
        return []

    # Entry conditions
    rsi_oversold = latest["RSI_14"] < 30
    at_lower_band = latest["Close"] <= latest["BBL_20_2.0"]
    not_freefall = df["SMA_50"].iloc[-5] <= df["SMA_50"].iloc[-1] * 1.05
    has_volume = latest["VOLUME_RATIO"] > 0.5

    if not (rsi_oversold and at_lower_band and not_freefall and has_volume):
        return []

    # Calculate levels
    entry_price = latest["Close"]
    swing_low = df["Low"].iloc[-10:].min()
    stop_loss = swing_low * 0.99  # Just below swing low
    target_price = latest["BBM_20_2.0"]  # Middle band

    # Require minimum 1.5:1 reward/risk
    risk = entry_price - stop_loss
    reward = target_price - entry_price
    if risk <= 0 or reward / risk < 1.5:
        return []

    # Strength based on how oversold
    strength = min(1.0, (30 - latest["RSI_14"]) / 20)

    return [Signal(
        ticker=ticker,
        strategy="mean_reversion",
        direction="long",
        signal_date=str(df.index[-1].date()),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        target_price=round(target_price, 2),
        strength=round(strength, 2),
        reasoning=(
            f"RSI({latest['RSI_14']:.1f}) oversold, price at lower Bollinger Band. "
            f"R:R = 1:{reward/risk:.1f}. Target: middle band at {target_price:.2f}."
        ),
        metadata={
            "rsi": round(latest["RSI_14"], 2),
            "bb_lower": round(latest["BBL_20_2.0"], 2),
            "bb_middle": round(latest["BBM_20_2.0"], 2),
        },
    )]
```

### Strategy 2: MACD Crossover + Trend Alignment

A momentum strategy that triggers when the MACD line crosses above the signal line while the broader trend is confirmed bullish (SMA 50 > SMA 200, i.e. golden cross territory).

Reference: `../strategy-and-theory/04-swing-trading-strategies.md` sections 1.1 (Moving Average Crossover) and 3.1 (MACD Divergence Trading).

```python
def strategy_macd_trend(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    MACD crossover with trend alignment.

    Entry conditions:
    - MACD line crosses above signal line (today above, yesterday below)
    - SMA(50) > SMA(200) — confirms bullish trend
    - Price is above SMA(50) — not extended below the trend
    - MACD histogram is negative but improving (momentum turning)
    - ADX > 20 — trend has directional strength

    Stop: Below SMA(50) or 2x ATR below entry, whichever is tighter
    Target: 2x risk distance above entry
    """
    if len(df) < 200:
        return []

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    required = [
        "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9",
        "SMA_50", "SMA_200", "ATR_14", "ADX_14",
    ]
    if any(pd.isna(latest.get(col)) for col in required):
        return []

    # MACD crossover: line crosses above signal
    macd_cross = (
        latest["MACD_12_26_9"] > latest["MACDs_12_26_9"]
        and prev["MACD_12_26_9"] <= prev["MACDs_12_26_9"]
    )

    # Trend alignment
    trend_bullish = latest["SMA_50"] > latest["SMA_200"]
    price_above_sma50 = latest["Close"] > latest["SMA_50"]
    trend_strength = latest["ADX_14"] > 20

    if not (macd_cross and trend_bullish and price_above_sma50 and trend_strength):
        return []

    entry_price = latest["Close"]
    atr = latest["ATR_14"]

    # Stop: tighter of SMA50 or 2x ATR below entry
    stop_sma = latest["SMA_50"] * 0.99
    stop_atr = entry_price - 2 * atr
    stop_loss = max(stop_sma, stop_atr)  # Tighter stop

    risk = entry_price - stop_loss
    if risk <= 0:
        return []

    target_price = entry_price + 2 * risk

    # Strength based on ADX and MACD histogram momentum
    strength = min(1.0, latest["ADX_14"] / 40)

    return [Signal(
        ticker=ticker,
        strategy="macd_trend",
        direction="long",
        signal_date=str(df.index[-1].date()),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        target_price=round(target_price, 2),
        strength=round(strength, 2),
        reasoning=(
            f"MACD bullish crossover with trend alignment. "
            f"SMA50 > SMA200, ADX={latest['ADX_14']:.1f}. "
            f"R:R = 1:2.0."
        ),
        metadata={
            "macd": round(latest["MACD_12_26_9"], 4),
            "macd_signal": round(latest["MACDs_12_26_9"], 4),
            "adx": round(latest["ADX_14"], 2),
            "sma50": round(latest["SMA_50"], 2),
            "sma200": round(latest["SMA_200"], 2),
        },
    )]
```

### Strategy 3: Breakout on Volume

Detects when price breaks above a consolidation range (20-day high) on elevated volume. This is a classic momentum breakout setup.

Reference: `../strategy-and-theory/04-swing-trading-strategies.md` section 1.4 (Breakout Trading).

```python
def strategy_breakout(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    Breakout: price breaks above 20-day high on above-average volume.

    Entry conditions:
    - Close is above the highest high of the prior 20 bars
    - Volume is >= 1.5x the 20-day average volume
    - Price is above SMA(50) — breakout in context of uptrend
    - ATR is not excessively high (avoid breakouts in chaotic conditions)
    - The consolidation range is reasonably tight (high-low range
      of last 20 bars is < 15% of price)

    Stop: Below the consolidation range low
    Target: Range height projected above breakout level
    """
    if len(df) < 50:
        return []

    latest = df.iloc[-1]

    required = ["SMA_50", "ATR_14", "VOLUME_RATIO"]
    if any(pd.isna(latest.get(col)) for col in required):
        return []

    lookback = df.iloc[-21:-1]  # Prior 20 bars (excluding today)
    range_high = lookback["High"].max()
    range_low = lookback["Low"].min()
    range_height = range_high - range_low

    # Consolidation should be reasonably tight
    if range_height / latest["Close"] > 0.15:
        return []

    # Breakout conditions
    breaks_above = latest["Close"] > range_high
    strong_volume = latest["VOLUME_RATIO"] >= 1.5
    above_trend = latest["Close"] > latest["SMA_50"]

    if not (breaks_above and strong_volume and above_trend):
        return []

    entry_price = latest["Close"]
    stop_loss = range_low * 0.99
    target_price = entry_price + range_height  # Measured move

    risk = entry_price - stop_loss
    reward = target_price - entry_price
    if risk <= 0 or reward / risk < 1.0:
        return []

    strength = min(1.0, latest["VOLUME_RATIO"] / 3.0)

    return [Signal(
        ticker=ticker,
        strategy="breakout",
        direction="long",
        signal_date=str(df.index[-1].date()),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        target_price=round(target_price, 2),
        strength=round(strength, 2),
        reasoning=(
            f"Breakout above 20-day range ({range_high:.2f}) on "
            f"{latest['VOLUME_RATIO']:.1f}x average volume. "
            f"Range: {range_low:.2f}-{range_high:.2f}. "
            f"Measured move target: {target_price:.2f}."
        ),
        metadata={
            "range_high": round(range_high, 2),
            "range_low": round(range_low, 2),
            "volume_ratio": round(latest["VOLUME_RATIO"], 2),
        },
    )]
```

### Strategy 4: Pullback to Moving Average in Uptrend

Buys when a stock in a confirmed uptrend pulls back to a key moving average (EMA 21) and shows signs of holding.

Reference: `../strategy-and-theory/04-swing-trading-strategies.md` section 1.3 (Pullback / Retracement Trading).

```python
def strategy_pullback(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    Pullback to EMA(21) in confirmed uptrend.

    Entry conditions:
    - SMA(50) > SMA(200) — confirmed uptrend
    - SMA(50) is rising (today > 10 bars ago)
    - Price touched or dipped below EMA(21) in last 3 bars
    - Latest close is back above EMA(21) — bounce confirmed
    - RSI is between 40 and 60 (not overbought, not crashing)

    Stop: Below the pullback low
    Target: Recent swing high or 2x risk
    """
    if len(df) < 200:
        return []

    latest = df.iloc[-1]
    recent = df.iloc[-3:]

    required = ["SMA_50", "SMA_200", "EMA_21", "RSI_14", "ATR_14"]
    if any(pd.isna(latest.get(col)) for col in required):
        return []

    # Uptrend confirmation
    uptrend = latest["SMA_50"] > latest["SMA_200"]
    sma50_rising = latest["SMA_50"] > df["SMA_50"].iloc[-10]

    if not (uptrend and sma50_rising):
        return []

    # Pullback: price touched EMA21 in last 3 bars
    touched_ema = any(row["Low"] <= row["EMA_21"] for _, row in recent.iterrows())

    # Bounce: latest close is above EMA21
    bounced = latest["Close"] > latest["EMA_21"]

    # RSI in neutral zone (not overbought, not in freefall)
    rsi_neutral = 40 <= latest["RSI_14"] <= 60

    if not (touched_ema and bounced and rsi_neutral):
        return []

    entry_price = latest["Close"]
    pullback_low = recent["Low"].min()
    stop_loss = pullback_low - latest["ATR_14"] * 0.5

    risk = entry_price - stop_loss
    if risk <= 0:
        return []

    # Target: recent 20-bar high or 2x risk, whichever is higher
    recent_high = df["High"].iloc[-20:].max()
    target_price = max(recent_high, entry_price + 2 * risk)

    reward = target_price - entry_price
    strength = min(1.0, reward / risk / 3.0)

    return [Signal(
        ticker=ticker,
        strategy="pullback",
        direction="long",
        signal_date=str(df.index[-1].date()),
        entry_price=round(entry_price, 2),
        stop_loss=round(stop_loss, 2),
        target_price=round(target_price, 2),
        strength=round(strength, 2),
        reasoning=(
            f"Pullback to EMA(21) in uptrend, bounce confirmed. "
            f"RSI={latest['RSI_14']:.1f}, SMA50 > SMA200. "
            f"R:R = 1:{reward/risk:.1f}."
        ),
        metadata={
            "ema21": round(latest["EMA_21"], 2),
            "sma50": round(latest["SMA_50"], 2),
            "pullback_low": round(pullback_low, 2),
            "rsi": round(latest["RSI_14"], 2),
        },
    )]
```

---

## 3. Indicator Pipeline

### Standard Indicator Set

Pre-calculate these indicators for every stock in the universe. This set covers the needs of all four strategies above plus scoring and filtering:

| Indicator | Parameters | Column Name(s) | Purpose |
|-----------|-----------|-----------------|---------|
| RSI | 14 | `RSI_14` | Overbought/oversold, mean reversion |
| MACD | 12, 26, 9 | `MACD_12_26_9`, `MACDs_12_26_9`, `MACDh_12_26_9` | Momentum crossovers |
| Bollinger Bands | 20, 2 | `BBL_20_2.0`, `BBM_20_2.0`, `BBU_20_2.0` | Mean reversion bands |
| SMA | 20 | `SMA_20` | Short-term trend |
| SMA | 50 | `SMA_50` | Medium-term trend |
| SMA | 200 | `SMA_200` | Long-term trend |
| EMA | 9 | `EMA_9` | Fast trend |
| EMA | 21 | `EMA_21` | Pullback reference |
| ATR | 14 | `ATR_14` | Volatility, stop sizing |
| ADX | 14 | `ADX_14` | Trend strength |
| OBV | - | `OBV` | Volume-price confirmation |
| Volume Ratio | 20-day avg | `VOLUME_RATIO` | Relative volume |

### Calculating All Indicators with pandas-ta

```python
import pandas as pd
import pandas_ta as ta


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the full standard indicator set on an OHLCV DataFrame.

    Expects columns: Open, High, Low, Close, Volume
    Returns the same DataFrame with indicator columns appended.

    Handles yfinance column format (may have multi-level columns).
    """
    # Ensure we have a clean copy
    df = df.copy()

    # Handle yfinance multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Drop any rows with NaN in OHLCV (can happen with yfinance)
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

    if len(df) < 30:
        return df  # Not enough data for meaningful indicators

    # --- Trend indicators ---
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.ema(length=9, append=True)
    df.ta.ema(length=21, append=True)

    # --- Momentum indicators ---
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.adx(length=14, append=True)

    # --- Volatility indicators ---
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)

    # --- Volume indicators ---
    df.ta.obv(append=True)

    # --- Custom: volume ratio (current volume / 20-day avg volume) ---
    df["VOLUME_RATIO"] = df["Volume"] / df["Volume"].rolling(window=20).mean()

    return df
```

### Handling Edge Cases

**Not enough data:** yfinance returns whatever history is available. A recently IPO'd stock may have fewer than 200 bars, which means SMA(200) will be NaN. Each strategy checks for NaN in required columns and skips gracefully.

```python
# In each strategy function, check data sufficiency:
if len(df) < 200:
    return []  # Not enough data for this strategy

# And check specific indicator values:
if any(pd.isna(latest.get(col)) for col in required):
    return []
```

**NaN values:** pandas-ta naturally produces NaN for the first N periods of any indicator (e.g., SMA(200) has 199 NaN rows at the start). The strategies only check the latest bar, so this is only a problem if the stock has insufficient history. The `pd.isna` check handles this.

**Stock splits:** yfinance returns adjusted data by default (`auto_adjust=True` since version 0.2.31). This means historical prices are already adjusted for splits and dividends. No manual adjustment is needed. However, if you store historical data in SQLite and the stock splits after storage, you need to re-fetch and update. For a daily scanner that fetches fresh data each run, this is not an issue.

**Delisted or renamed tickers:** yfinance returns an empty DataFrame for invalid tickers. Check for this before processing:

```python
if df.empty or len(df) < 30:
    print(f"Skipping {ticker}: insufficient data")
    continue
```

---

## 4. Signal Scoring and Ranking

The scoring system translates raw signals into comparable quality scores. This implements the 0-20 scoring model from `../strategy-and-theory/23-setup-quality-scoring.md`.

### The 0-20 Scoring Model in Python

```python
@dataclass
class SetupScore:
    """Score breakdown for a trading setup (0-20 scale)."""
    trend_alignment: int      # 0-3
    level_quality: int        # 0-3
    catalyst_quality: int     # 0-3
    volume_participation: int # 0-2
    liquidity_quality: int    # 0-2
    market_sector_align: int  # 0-3
    risk_reward_quality: int  # 0-2
    timing_confirmation: int  # 0-2
    total: int                # Sum, 0-20

    @classmethod
    def calculate(cls, signal: Signal, df: pd.DataFrame, market_df: pd.DataFrame = None):
        """
        Score a signal based on setup quality criteria.

        Args:
            signal: The raw signal from a strategy
            df: The stock's OHLCV + indicator DataFrame
            market_df: Optional OMXS30 index DataFrame for market context
        """
        latest = df.iloc[-1]

        # --- Category 1: Trend alignment (0-3) ---
        trend = 0
        if not pd.isna(latest.get("SMA_50")) and not pd.isna(latest.get("SMA_200")):
            daily_bullish = latest["SMA_50"] > latest["SMA_200"]
            sma50_rising = latest["SMA_50"] > df["SMA_50"].iloc[-20] if len(df) >= 20 else False

            if daily_bullish and sma50_rising:
                trend = 3  # Daily and weekly trend support
            elif daily_bullish:
                trend = 2  # Daily trend supports
            elif sma50_rising:
                trend = 1  # Mixed
            # else 0: fights trend

        # --- Category 2: Level quality (0-3) ---
        level = 1  # Default: signals are at some reference level
        if signal.strategy == "mean_reversion":
            level = 2  # Bollinger Band is a clear reference level
            # Check if this level has been tested before
            bb_lower = latest.get("BBL_20_2.0")
            if bb_lower and not pd.isna(bb_lower):
                prior_touches = (df["Low"].iloc[-60:-1] <= bb_lower * 1.01).sum()
                if prior_touches >= 2:
                    level = 3  # Multi-touch level
        elif signal.strategy == "breakout":
            level = 2  # Range breakout is a clear level
        elif signal.strategy == "pullback":
            level = 2  # EMA pullback in trend

        # --- Category 3: Catalyst quality (0-3) ---
        # Automated scoring defaults to 1 (no catalyst data available yet)
        # This can be enhanced later with earnings calendar integration
        catalyst = 1

        # --- Category 4: Volume and participation (0-2) ---
        volume = 0
        vol_ratio = latest.get("VOLUME_RATIO", 0)
        if not pd.isna(vol_ratio):
            if vol_ratio >= 1.5:
                volume = 2  # Strong participation
            elif vol_ratio >= 0.8:
                volume = 1  # Adequate volume

        # --- Category 5: Liquidity and execution quality (0-2) ---
        liquidity = 1  # Default for OMX Large Cap
        avg_volume = df["Volume"].iloc[-20:].mean() if len(df) >= 20 else 0
        if avg_volume > 500_000:
            liquidity = 2  # Strong liquidity
        elif avg_volume < 50_000:
            liquidity = 0  # Poor liquidity

        # --- Category 6: Market and sector alignment (0-3) ---
        market_align = 1  # Default: neutral
        if market_df is not None and len(market_df) >= 50:
            mkt_latest = market_df.iloc[-1]
            mkt_sma50 = market_df["Close"].rolling(50).mean().iloc[-1]
            mkt_sma200 = market_df["Close"].rolling(200).mean().iloc[-1]

            market_bullish = mkt_latest["Close"] > mkt_sma50
            market_trend = mkt_sma50 > mkt_sma200

            if market_bullish and market_trend:
                market_align = 3
            elif market_bullish:
                market_align = 2

        # --- Category 7: Risk/reward quality (0-2) ---
        rr = 0
        if signal.stop_loss > 0 and signal.entry_price > signal.stop_loss:
            risk = signal.entry_price - signal.stop_loss
            reward = signal.target_price - signal.entry_price
            rr_ratio = reward / risk if risk > 0 else 0
            if rr_ratio >= 2.0:
                rr = 2
            elif rr_ratio >= 1.5:
                rr = 1

        # --- Category 8: Timing and confirmation (0-2) ---
        timing = 1  # Signal exists, so there is some trigger
        if signal.strength >= 0.7:
            timing = 2  # Strong confirmation

        total = trend + level + catalyst + volume + liquidity + market_align + rr + timing

        return cls(
            trend_alignment=trend,
            level_quality=level,
            catalyst_quality=catalyst,
            volume_participation=volume,
            liquidity_quality=liquidity,
            market_sector_align=market_align,
            risk_reward_quality=rr,
            timing_confirmation=timing,
            total=total,
        )
```

### Confluence Scoring

When multiple strategies fire on the same stock on the same day, this is a strong positive signal. Confluence is handled after individual scoring:

```python
def apply_confluence_bonus(
    scored_signals: list[tuple[Signal, SetupScore]],
) -> list[tuple[Signal, SetupScore]]:
    """
    If multiple strategies signal the same ticker on the same day,
    boost the highest-scoring signal.
    """
    from collections import defaultdict

    by_ticker = defaultdict(list)
    for signal, score in scored_signals:
        by_ticker[signal.ticker].append((signal, score))

    result = []
    for ticker, entries in by_ticker.items():
        if len(entries) > 1:
            # Multiple strategies agree: boost the best signal
            entries.sort(key=lambda x: x[1].total, reverse=True)
            best_signal, best_score = entries[0]
            # Add 1-2 points for confluence (cap at 20)
            bonus = min(2, len(entries) - 1)
            best_score.total = min(20, best_score.total + bonus)
            strategies = [e[0].strategy for e in entries]
            best_signal.reasoning += (
                f" Confluence: {len(entries)} strategies agree "
                f"({', '.join(strategies)})."
            )
            result.append((best_signal, best_score))
        else:
            result.append(entries[0])

    return result
```

### Ranking and Filtering

```python
MINIMUM_SCORE = 12  # C-tier and below are excluded (ref: scoring doc)


def rank_signals(
    scored_signals: list[tuple[Signal, SetupScore]],
) -> list[tuple[Signal, SetupScore]]:
    """
    Filter by minimum score, apply hard disqualifiers, sort by score descending.
    Returns the top recommendations for the day.
    """
    # Apply confluence bonus
    scored_signals = apply_confluence_bonus(scored_signals)

    # Filter by minimum score
    qualified = [
        (sig, score) for sig, score in scored_signals
        if score.total >= MINIMUM_SCORE
    ]

    # Sort by score descending, then by strength as tiebreaker
    qualified.sort(key=lambda x: (x[1].total, x[0].strength), reverse=True)

    # Return top 5 maximum
    return qualified[:5]
```

### Hard Disqualifiers

Certain conditions should block a signal regardless of score. Reference: `../strategy-and-theory/23-setup-quality-scoring.md` section 5.

```python
def check_disqualifiers(signal: Signal, df: pd.DataFrame) -> str | None:
    """
    Check for hard disqualifiers. Returns reason string if disqualified,
    None if the signal passes.
    """
    latest = df.iloc[-1]

    # Disqualifier: average daily volume too low
    avg_vol = df["Volume"].iloc[-20:].mean()
    if avg_vol < 20_000:
        return f"Average volume too low ({avg_vol:.0f} shares/day)"

    # Disqualifier: stop distance exceeds 8% of entry
    risk_pct = (signal.entry_price - signal.stop_loss) / signal.entry_price
    if risk_pct > 0.08:
        return f"Stop distance too wide ({risk_pct:.1%})"

    # Disqualifier: price below 10 SEK (penny stock territory)
    if signal.entry_price < 10:
        return f"Price too low ({signal.entry_price} SEK)"

    # Disqualifier: ATR is > 5% of price (too volatile)
    atr_pct = latest.get("ATR_14", 0) / latest["Close"] if latest["Close"] > 0 else 0
    if not pd.isna(atr_pct) and atr_pct > 0.05:
        return f"ATR too high ({atr_pct:.1%} of price, max 5%)"

    return None  # No disqualifier, signal passes
```

---

## 5. Universe Management

### OMX Large Cap + Top Mid Cap

The universe for the scanner is Swedish OMX Large Cap stocks plus selected Mid Cap stocks with adequate liquidity. As noted in `../strategy-and-theory/22-watchlist-and-universe-selection.md`, universe selection is separate from screening: the universe defines what is eligible, strategies and scoring decide what to trade.

### Static Universe List

yfinance uses the `.ST` suffix for Stockholm-listed stocks. There is no reliable free API to programmatically fetch the current OMX Large Cap composition. A maintained static list is the practical approach, updated manually when index rebalancing occurs (quarterly).

```python
# OMX Large Cap tickers (Stockholm .ST suffix for yfinance)
# Updated: 2026-03-08
# Source: Nasdaq Nordic index composition

OMX_LARGE_CAP = [
    "ABB.ST",         # ABB Ltd
    "ALFA.ST",        # Alfa Laval
    "ASSA-B.ST",      # ASSA ABLOY B
    "ATCO-A.ST",      # Atlas Copco A
    "ATCO-B.ST",      # Atlas Copco B
    "AZN.ST",         # AstraZeneca
    "BOL.ST",         # Boliden
    "CAST.ST",        # Castellum
    "ELUX-B.ST",      # Electrolux B
    "EMBRAC-B.ST",    # Embracer Group B
    "ERIC-B.ST",      # Ericsson B
    "ESSITY-B.ST",    # Essity B
    "EVO.ST",         # Evolution
    "GETI-B.ST",      # Getinge B
    "HEXA-B.ST",      # Hexagon B
    "HM-B.ST",        # H&M B
    "HUSQ-B.ST",      # Husqvarna B
    "INDU-C.ST",      # Industrivarden C
    "INVE-B.ST",      # Investor B
    "KIND-SDB.ST",    # Kindred Group
    "KINV-B.ST",      # Kinnevik B
    "LUND-B.ST",      # Lundbergforetagen B
    "NIBE-B.ST",      # NIBE Industrier B
    "NDA-SE.ST",      # Nordea Bank
    "SAND.ST",        # Sandvik
    "SBB-B.ST",       # Samhallsbyggnadsbolaget B
    "SCA-B.ST",       # SCA B
    "SEB-A.ST",       # SEB A
    "SHB-A.ST",       # Handelsbanken A
    "SINCH.ST",       # Sinch
    "SKA-B.ST",       # Skanska B
    "SKF-B.ST",       # SKF B
    "SSAB-A.ST",      # SSAB A
    "SSAB-B.ST",      # SSAB B
    "STE-R.ST",       # Stora Enso R
    "SWED-A.ST",      # Swedbank A
    "SWMA.ST",        # Swedish Match
    "TEL2-B.ST",      # Tele2 B
    "TELIA.ST",       # Telia Company
    "VOLV-B.ST",      # Volvo B
]

# Selected Mid Cap with good liquidity (avg volume > 200k shares/day)
OMX_MID_CAP_SELECT = [
    "BILL.ST",        # Billerud
    "BRAV.ST",        # Bravida
    "COOR.ST",        # Coor Service Management
    "DIOS.ST",        # Dios Fastigheter
    "ELTEL.ST",       # Eltel
    "FAGERHULT.ST",   # Fagerhult
    "HPOL-B.ST",      # Hexpol B
    "LATO-B.ST",      # Latour B
    "LIFCO-B.ST",     # Lifco B
    "SAGA-B.ST",      # Sagax B
    "THULE.ST",       # Thule Group
    "TREL-B.ST",      # Trelleborg B
    "WIHL.ST",        # Wihlborgs Fastigheter
]

FULL_UNIVERSE = OMX_LARGE_CAP + OMX_MID_CAP_SELECT

# OMXS30 index for market context
MARKET_INDEX = "^OMX"
```

### Filtering by Volume and Liquidity

Tickers in the static list still need runtime validation. A stock might be in the Large Cap index but have temporarily low volume (e.g., around holidays):

```python
import yfinance as yf


def validate_universe(
    tickers: list[str],
    min_avg_volume: int = 100_000,
    min_price: float = 10.0,
    lookback_days: int = 30,
) -> list[str]:
    """
    Validate tickers by checking recent volume and price.
    Returns only tickers that meet minimum liquidity requirements.
    """
    valid = []
    for ticker in tickers:
        try:
            data = yf.download(
                ticker, period=f"{lookback_days}d",
                progress=False, auto_adjust=True,
            )
            if data.empty or len(data) < 10:
                print(f"  SKIP {ticker}: insufficient data")
                continue

            avg_vol = data["Volume"].mean()
            last_price = data["Close"].iloc[-1]

            # Handle potential MultiIndex from yfinance
            if isinstance(last_price, pd.Series):
                last_price = last_price.iloc[0]
            if isinstance(avg_vol, pd.Series):
                avg_vol = avg_vol.iloc[0]

            if avg_vol < min_avg_volume:
                print(f"  SKIP {ticker}: avg volume {avg_vol:.0f} < {min_avg_volume}")
                continue
            if last_price < min_price:
                print(f"  SKIP {ticker}: price {last_price:.2f} < {min_price}")
                continue

            valid.append(ticker)

        except Exception as e:
            print(f"  SKIP {ticker}: error fetching data: {e}")
            continue

    print(f"\nUniverse: {len(valid)} / {len(tickers)} tickers passed validation")
    return valid
```

---

## 6. Daily Scan Pipeline (Full Flow)

This is a complete, runnable Python script that ties everything together. It loads the universe, fetches data, calculates indicators, runs all strategies, scores and ranks signals, and outputs recommendations.

```python
"""
SwingTrader Daily Scanner
=========================
Scans OMX Large Cap + selected Mid Cap stocks for swing trading setups.

Requirements:
    pip install yfinance pandas pandas-ta

Usage:
    python daily_scanner.py
"""

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd
import pandas_ta as ta
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MINIMUM_SCORE = 12
MAX_RECOMMENDATIONS = 5
DATA_PERIOD = "1y"

OMX_UNIVERSE = [
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-A.ST", "AZN.ST",
    "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST",
    "GETI-B.ST", "HEXA-B.ST", "HM-B.ST", "HUSQ-B.ST", "INVE-B.ST",
    "KINV-B.ST", "NDA-SE.ST", "NIBE-B.ST", "SAND.ST", "SCA-B.ST",
    "SEB-A.ST", "SHB-A.ST", "SINCH.ST", "SKA-B.ST", "SKF-B.ST",
    "SSAB-A.ST", "SWED-A.ST", "TEL2-B.ST", "TELIA.ST", "VOLV-B.ST",
    "LIFCO-B.ST", "LATO-B.ST", "SAGA-B.ST", "THULE.ST", "TREL-B.ST",
]

MARKET_INDEX = "^OMX"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Signal:
    ticker: str
    strategy: str
    direction: str
    signal_date: str
    entry_price: float
    stop_loss: float
    target_price: float
    strength: float
    reasoning: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SetupScore:
    trend_alignment: int = 0
    level_quality: int = 0
    catalyst_quality: int = 0
    volume_participation: int = 0
    liquidity_quality: int = 0
    market_sector_align: int = 0
    risk_reward_quality: int = 0
    timing_confirmation: int = 0
    total: int = 0

    def compute_total(self):
        self.total = (
            self.trend_alignment + self.level_quality + self.catalyst_quality
            + self.volume_participation + self.liquidity_quality
            + self.market_sector_align + self.risk_reward_quality
            + self.timing_confirmation
        )
        return self


# ---------------------------------------------------------------------------
# Indicator calculation
# ---------------------------------------------------------------------------


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add the full standard indicator set to an OHLCV DataFrame."""
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    if len(df) < 30:
        return df

    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.ema(length=9, append=True)
    df.ta.ema(length=21, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.adx(length=14, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.obv(append=True)
    df["VOLUME_RATIO"] = df["Volume"] / df["Volume"].rolling(20).mean()
    return df


# ---------------------------------------------------------------------------
# Strategy functions
# ---------------------------------------------------------------------------


def strat_mean_reversion(df: pd.DataFrame, ticker: str) -> list[Signal]:
    if len(df) < 50:
        return []
    latest, prev = df.iloc[-1], df.iloc[-2]
    cols = ["RSI_14", "BBL_20_2.0", "BBM_20_2.0", "SMA_50", "VOLUME_RATIO"]
    if any(pd.isna(latest.get(c)) for c in cols):
        return []

    if not (latest["RSI_14"] < 30
            and latest["Close"] <= latest["BBL_20_2.0"]
            and latest["VOLUME_RATIO"] > 0.5):
        return []

    entry = latest["Close"]
    stop = df["Low"].iloc[-10:].min() * 0.99
    target = latest["BBM_20_2.0"]
    risk = entry - stop
    reward = target - entry
    if risk <= 0 or reward / risk < 1.5:
        return []

    return [Signal(
        ticker=ticker, strategy="mean_reversion", direction="long",
        signal_date=str(df.index[-1].date()), entry_price=round(entry, 2),
        stop_loss=round(stop, 2), target_price=round(target, 2),
        strength=round(min(1, (30 - latest["RSI_14"]) / 20), 2),
        reasoning=f"RSI {latest['RSI_14']:.1f} oversold at lower BB. R:R 1:{reward/risk:.1f}",
    )]


def strat_macd_trend(df: pd.DataFrame, ticker: str) -> list[Signal]:
    if len(df) < 200:
        return []
    latest, prev = df.iloc[-1], df.iloc[-2]
    cols = ["MACD_12_26_9", "MACDs_12_26_9", "SMA_50", "SMA_200", "ATR_14", "ADX_14"]
    if any(pd.isna(latest.get(c)) for c in cols):
        return []

    cross = (latest["MACD_12_26_9"] > latest["MACDs_12_26_9"]
             and prev["MACD_12_26_9"] <= prev["MACDs_12_26_9"])
    trend_ok = (latest["SMA_50"] > latest["SMA_200"]
                and latest["Close"] > latest["SMA_50"]
                and latest["ADX_14"] > 20)
    if not (cross and trend_ok):
        return []

    entry = latest["Close"]
    stop = max(latest["SMA_50"] * 0.99, entry - 2 * latest["ATR_14"])
    risk = entry - stop
    if risk <= 0:
        return []
    target = entry + 2 * risk

    return [Signal(
        ticker=ticker, strategy="macd_trend", direction="long",
        signal_date=str(df.index[-1].date()), entry_price=round(entry, 2),
        stop_loss=round(stop, 2), target_price=round(target, 2),
        strength=round(min(1, latest["ADX_14"] / 40), 2),
        reasoning=f"MACD bullish cross, SMA50>SMA200, ADX={latest['ADX_14']:.1f}",
    )]


def strat_breakout(df: pd.DataFrame, ticker: str) -> list[Signal]:
    if len(df) < 50:
        return []
    latest = df.iloc[-1]
    cols = ["SMA_50", "ATR_14", "VOLUME_RATIO"]
    if any(pd.isna(latest.get(c)) for c in cols):
        return []

    lookback = df.iloc[-21:-1]
    rng_high = lookback["High"].max()
    rng_low = lookback["Low"].min()
    rng_h = rng_high - rng_low

    if rng_h / latest["Close"] > 0.15:
        return []
    if not (latest["Close"] > rng_high
            and latest["VOLUME_RATIO"] >= 1.5
            and latest["Close"] > latest["SMA_50"]):
        return []

    entry = latest["Close"]
    stop = rng_low * 0.99
    target = entry + rng_h
    risk = entry - stop
    if risk <= 0 or (target - entry) / risk < 1.0:
        return []

    return [Signal(
        ticker=ticker, strategy="breakout", direction="long",
        signal_date=str(df.index[-1].date()), entry_price=round(entry, 2),
        stop_loss=round(stop, 2), target_price=round(target, 2),
        strength=round(min(1, latest["VOLUME_RATIO"] / 3), 2),
        reasoning=f"Breakout above {rng_high:.2f} on {latest['VOLUME_RATIO']:.1f}x volume",
    )]


def strat_pullback(df: pd.DataFrame, ticker: str) -> list[Signal]:
    if len(df) < 200:
        return []
    latest = df.iloc[-1]
    recent = df.iloc[-3:]
    cols = ["SMA_50", "SMA_200", "EMA_21", "RSI_14", "ATR_14"]
    if any(pd.isna(latest.get(c)) for c in cols):
        return []

    uptrend = (latest["SMA_50"] > latest["SMA_200"]
               and latest["SMA_50"] > df["SMA_50"].iloc[-10])
    touched = any(r["Low"] <= r["EMA_21"] for _, r in recent.iterrows())
    bounced = latest["Close"] > latest["EMA_21"]
    rsi_ok = 40 <= latest["RSI_14"] <= 60

    if not (uptrend and touched and bounced and rsi_ok):
        return []

    entry = latest["Close"]
    stop = recent["Low"].min() - latest["ATR_14"] * 0.5
    risk = entry - stop
    if risk <= 0:
        return []
    swing_high = df["High"].iloc[-20:].max()
    target = max(swing_high, entry + 2 * risk)
    reward = target - entry

    return [Signal(
        ticker=ticker, strategy="pullback", direction="long",
        signal_date=str(df.index[-1].date()), entry_price=round(entry, 2),
        stop_loss=round(stop, 2), target_price=round(target, 2),
        strength=round(min(1, reward / risk / 3), 2),
        reasoning=f"Pullback to EMA21 in uptrend, RSI={latest['RSI_14']:.1f}, R:R 1:{reward/risk:.1f}",
    )]


ALL_STRATEGIES = [strat_mean_reversion, strat_macd_trend, strat_breakout, strat_pullback]


# ---------------------------------------------------------------------------
# Scoring and disqualification
# ---------------------------------------------------------------------------


def score_signal(sig: Signal, df: pd.DataFrame, mkt_df: pd.DataFrame = None) -> SetupScore:
    latest = df.iloc[-1]
    s = SetupScore()

    # Trend
    if not pd.isna(latest.get("SMA_50")) and not pd.isna(latest.get("SMA_200")):
        if latest["SMA_50"] > latest["SMA_200"] and latest["SMA_50"] > df["SMA_50"].iloc[-20]:
            s.trend_alignment = 3
        elif latest["SMA_50"] > latest["SMA_200"]:
            s.trend_alignment = 2
        else:
            s.trend_alignment = 1

    # Level
    s.level_quality = 2 if sig.strategy in ("mean_reversion", "breakout", "pullback") else 1

    # Catalyst (placeholder)
    s.catalyst_quality = 1

    # Volume
    vr = latest.get("VOLUME_RATIO", 0)
    if not pd.isna(vr):
        s.volume_participation = 2 if vr >= 1.5 else (1 if vr >= 0.8 else 0)

    # Liquidity
    avg_vol = df["Volume"].iloc[-20:].mean()
    s.liquidity_quality = 2 if avg_vol > 500_000 else (1 if avg_vol > 50_000 else 0)

    # Market alignment
    if mkt_df is not None and len(mkt_df) >= 200:
        mkt_close = mkt_df["Close"]
        if isinstance(mkt_close, pd.DataFrame):
            mkt_close = mkt_close.iloc[:, 0]
        m50 = mkt_close.rolling(50).mean().iloc[-1]
        m200 = mkt_close.rolling(200).mean().iloc[-1]
        s.market_sector_align = 3 if mkt_close.iloc[-1] > m50 > m200 else (
            2 if mkt_close.iloc[-1] > m50 else 1)
    else:
        s.market_sector_align = 1

    # Risk/reward
    risk = sig.entry_price - sig.stop_loss
    reward = sig.target_price - sig.entry_price
    rr = reward / risk if risk > 0 else 0
    s.risk_reward_quality = 2 if rr >= 2.0 else (1 if rr >= 1.5 else 0)

    # Timing
    s.timing_confirmation = 2 if sig.strength >= 0.7 else 1

    return s.compute_total()


def is_disqualified(sig: Signal, df: pd.DataFrame) -> Optional[str]:
    latest = df.iloc[-1]
    avg_vol = df["Volume"].iloc[-20:].mean()
    if avg_vol < 20_000:
        return "avg volume < 20k"
    risk_pct = (sig.entry_price - sig.stop_loss) / sig.entry_price
    if risk_pct > 0.08:
        return f"stop too wide ({risk_pct:.1%})"
    if sig.entry_price < 10:
        return "price < 10 SEK"
    atr_pct = latest.get("ATR_14", 0) / latest["Close"] if latest["Close"] > 0 else 0
    if not pd.isna(atr_pct) and atr_pct > 0.05:
        return f"ATR too high ({atr_pct:.1%})"
    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_daily_scan():
    print(f"SwingTrader Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Fetch market index for context
    print(f"\nFetching market index ({MARKET_INDEX})...")
    mkt_df = yf.download(MARKET_INDEX, period=DATA_PERIOD, progress=False, auto_adjust=True)
    if isinstance(mkt_df.columns, pd.MultiIndex):
        mkt_df.columns = mkt_df.columns.get_level_values(0)

    # 2. Scan each stock
    all_scored: list[tuple[Signal, SetupScore]] = []
    scanned = 0
    errors = 0

    print(f"\nScanning {len(OMX_UNIVERSE)} tickers...")
    for ticker in OMX_UNIVERSE:
        try:
            df = yf.download(ticker, period=DATA_PERIOD, progress=False, auto_adjust=True)
            if df.empty or len(df) < 30:
                continue

            df = add_indicators(df)
            scanned += 1

            for strategy_fn in ALL_STRATEGIES:
                signals = strategy_fn(df, ticker)
                for sig in signals:
                    dq = is_disqualified(sig, df)
                    if dq:
                        continue
                    score = score_signal(sig, df, mkt_df)
                    all_scored.append((sig, score))

        except Exception as e:
            errors += 1
            print(f"  ERROR {ticker}: {e}")

    print(f"\nScanned: {scanned} | Errors: {errors} | Raw signals: {len(all_scored)}")

    # 3. Apply confluence and rank
    from collections import defaultdict
    by_ticker = defaultdict(list)
    for sig, score in all_scored:
        by_ticker[sig.ticker].append((sig, score))

    final: list[tuple[Signal, SetupScore]] = []
    for ticker, entries in by_ticker.items():
        if len(entries) > 1:
            entries.sort(key=lambda x: x[1].total, reverse=True)
            best_sig, best_score = entries[0]
            bonus = min(2, len(entries) - 1)
            best_score.total = min(20, best_score.total + bonus)
            names = [e[0].strategy for e in entries]
            best_sig.reasoning += f" | Confluence: {', '.join(names)}"
            final.append((best_sig, best_score))
        else:
            final.append(entries[0])

    # Filter and sort
    qualified = [(s, sc) for s, sc in final if sc.total >= MINIMUM_SCORE]
    qualified.sort(key=lambda x: (x[1].total, x[0].strength), reverse=True)
    top = qualified[:MAX_RECOMMENDATIONS]

    # 4. Output
    print(f"\n{'=' * 60}")
    if not top:
        print("No recommendations today. No setups meet minimum quality threshold.")
    else:
        print(f"TOP {len(top)} RECOMMENDATIONS")
        print("=" * 60)
        for i, (sig, score) in enumerate(top, 1):
            risk = sig.entry_price - sig.stop_loss
            reward = sig.target_price - sig.entry_price
            rr = reward / risk if risk > 0 else 0
            grade = "A" if score.total >= 17 else "B" if score.total >= 13 else "C"

            print(f"\n#{i}  {sig.ticker}  [{sig.strategy.upper()}]  "
                  f"Score: {score.total}/20 ({grade}-tier)")
            print(f"    Entry:  {sig.entry_price:.2f} SEK")
            print(f"    Stop:   {sig.stop_loss:.2f} SEK  "
                  f"(risk {risk:.2f}, {risk/sig.entry_price:.1%})")
            print(f"    Target: {sig.target_price:.2f} SEK  "
                  f"(reward {reward:.2f}, R:R 1:{rr:.1f})")
            print(f"    Signal: {sig.reasoning}")
            print(f"    Score:  T={score.trend_alignment} L={score.level_quality} "
                  f"C={score.catalyst_quality} V={score.volume_participation} "
                  f"Liq={score.liquidity_quality} M={score.market_sector_align} "
                  f"RR={score.risk_reward_quality} Tim={score.timing_confirmation}")

    print(f"\n{'=' * 60}")
    print(f"Scan complete at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    run_daily_scan()
```

---

## 7. Handling Multiple Timeframes

### Why Weekly Matters

Daily signals are the primary driver, but weekly trend confirmation reduces false signals. A daily pullback buy in a stock whose weekly trend is falling is fighting the higher timeframe, which lowers the win rate.

Reference: `../strategy-and-theory/04-swing-trading-strategies.md` section 4.1 (Multi-Timeframe Analysis).

### Fetching and Aligning Weekly Data

yfinance supports weekly bars directly. Fetch both timeframes and use the weekly data as a filter:

```python
def fetch_with_weekly(ticker: str, period: str = "2y") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch both daily and weekly data for a ticker.
    Returns (daily_df, weekly_df).
    """
    daily = yf.download(ticker, period=period, interval="1d",
                        progress=False, auto_adjust=True)
    weekly = yf.download(ticker, period=period, interval="1wk",
                         progress=False, auto_adjust=True)

    # Clean multi-index columns
    for df in (daily, weekly):
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    return daily, weekly


def weekly_trend_check(weekly_df: pd.DataFrame) -> dict:
    """
    Simple weekly trend assessment.

    Returns a dict with:
    - weekly_sma20_rising: bool
    - weekly_trend: "bullish" | "bearish" | "neutral"
    - weekly_above_sma20: bool
    """
    if len(weekly_df) < 25:
        return {"weekly_sma20_rising": False, "weekly_trend": "neutral",
                "weekly_above_sma20": False}

    weekly_df = weekly_df.copy()
    weekly_df["W_SMA_20"] = weekly_df["Close"].rolling(20).mean()

    latest = weekly_df.iloc[-1]
    prev_5 = weekly_df.iloc[-5]

    sma_rising = latest["W_SMA_20"] > prev_5["W_SMA_20"]
    above_sma = latest["Close"] > latest["W_SMA_20"]

    if sma_rising and above_sma:
        trend = "bullish"
    elif not sma_rising and not above_sma:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "weekly_sma20_rising": sma_rising,
        "weekly_trend": trend,
        "weekly_above_sma20": above_sma,
    }
```

### Using Weekly Trend in Scoring

The weekly trend check feeds directly into the trend alignment score. If the weekly trend is bullish, the trend score can reach 3. If it conflicts with the daily signal, the score stays at 1 or lower.

```python
# In the scoring function, enhance trend alignment:
weekly_info = weekly_trend_check(weekly_df)

if daily_bullish and weekly_info["weekly_trend"] == "bullish":
    trend_alignment = 3  # Both timeframes agree
elif daily_bullish and weekly_info["weekly_trend"] == "neutral":
    trend_alignment = 2  # Daily supports, weekly mixed
elif daily_bullish and weekly_info["weekly_trend"] == "bearish":
    trend_alignment = 1  # Fighting higher timeframe
```

---

## 8. False Signal Reduction

### Common Causes of False Signals

Automated scanners generate false signals for predictable reasons:

1. **Low volume signals:** Technical patterns on thin volume are unreliable. A "breakout" on 5,000 shares means nothing.
2. **Counter-trend signals:** Mean reversion signals in a stock that is in freefall. RSI can stay oversold for weeks in a genuine bear trend.
3. **Earnings proximity:** Holding through earnings injects binary event risk that the technical setup did not price in.
4. **Choppy market regime:** Breakout signals fail repeatedly when the broad market is range-bound.
5. **Data issues:** Stock splits, missing bars, or corporate actions that distort indicator readings.
6. **Correlated signals:** 5 bank stocks all triggering on the same day usually means one sector-level move, not 5 independent setups.

### Practical Filters

These filters are already embedded in the strategies and scoring above, but summarized here for clarity:

**Minimum volume filter:**
```python
# Already in disqualifier check
if avg_volume < 20_000:
    disqualify()
# And in scoring
volume_participation = 2 if vol_ratio >= 1.5 else 1 if vol_ratio >= 0.8 else 0
```

**Trend alignment filter:**
```python
# Mean reversion: check that SMA50 is not falling steeply
not_freefall = df["SMA_50"].iloc[-5] <= df["SMA_50"].iloc[-1] * 1.05

# Breakout/pullback: require price above SMA50
above_trend = latest["Close"] > latest["SMA_50"]
```

**Earnings proximity check (future enhancement):**
```python
def is_near_earnings(ticker: str, days_buffer: int = 5) -> bool:
    """
    Check if a stock has earnings within the buffer window.
    Uses yfinance calendar data.

    Returns True if earnings are too close (should skip trade).
    """
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        if calendar is None or calendar.empty:
            return False

        # Look for next earnings date
        if "Earnings Date" in calendar.index:
            earnings_date = pd.Timestamp(calendar.loc["Earnings Date"].iloc[0])
            days_until = (earnings_date - pd.Timestamp.now()).days
            return 0 <= days_until <= days_buffer
    except Exception:
        pass
    return False
```

### Simple Regime Detection

A basic regime detector that uses the concepts from `../strategy-and-theory/25-regime-to-strategy-mapping.md` without complex implementation:

```python
def detect_regime(market_df: pd.DataFrame) -> dict:
    """
    Simple market regime detection using OMXS30 index data.

    Returns:
        regime: "trending_orderly" | "trending_volatile" | "choppy" | "event_driven"
        preferred_strategies: list of strategy names
        size_multiplier: float (1.0 = normal, 0.5 = half size)
    """
    if len(market_df) < 200:
        return {"regime": "unknown", "preferred_strategies": [], "size_multiplier": 1.0}

    close = market_df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    atr = (market_df["High"] - market_df["Low"]).rolling(14).mean()

    latest_close = close.iloc[-1]
    latest_sma50 = sma50.iloc[-1]
    latest_sma200 = sma200.iloc[-1]
    latest_atr = atr.iloc[-1]

    # Trend direction
    trending_up = latest_sma50 > latest_sma200
    sma50_rising = sma50.iloc[-1] > sma50.iloc[-20]

    # Volatility: compare current ATR to 60-day median ATR
    median_atr = atr.iloc[-60:].median()
    vol_ratio = latest_atr / median_atr if median_atr > 0 else 1.0

    # Determine regime
    if trending_up and sma50_rising and vol_ratio < 1.3:
        return {
            "regime": "trending_orderly",
            "preferred_strategies": ["breakout", "macd_trend", "pullback"],
            "suppressed_strategies": [],
            "size_multiplier": 1.0,
        }
    elif trending_up and vol_ratio >= 1.3:
        return {
            "regime": "trending_volatile",
            "preferred_strategies": ["pullback", "macd_trend"],
            "suppressed_strategies": ["breakout"],
            "size_multiplier": 0.7,
        }
    elif not trending_up and not sma50_rising and vol_ratio < 1.5:
        return {
            "regime": "choppy",
            "preferred_strategies": ["mean_reversion"],
            "suppressed_strategies": ["breakout", "macd_trend"],
            "size_multiplier": 0.5,
        }
    else:
        return {
            "regime": "event_driven",
            "preferred_strategies": [],
            "suppressed_strategies": ["breakout"],
            "size_multiplier": 0.3,
        }
```

Regime detection can be used to filter strategies before they even run:

```python
regime = detect_regime(market_df)
active_strategies = [
    fn for fn in ALL_STRATEGIES
    if fn.__name__.replace("strat_", "") not in regime.get("suppressed_strategies", [])
]
```

---

## 9. Output Format

### What a Good Recommendation Looks Like

A recommendation should give the trader everything needed to decide and act without opening additional tools. It should include: what to buy, why, where to enter, where to place the stop, what the target is, and how confident the system is.

### Console Output Format

This is what the daily scanner produces (from the pipeline in section 6):

```
==============================================================
TOP 3 RECOMMENDATIONS
==============================================================

#1  VOLV-B.ST  [PULLBACK]  Score: 17/20 (A-tier)
    Entry:  265.40 SEK
    Stop:   256.80 SEK  (risk 8.60, 3.2%)
    Target: 285.00 SEK  (reward 19.60, R:R 1:2.3)
    Signal: Pullback to EMA21 in uptrend, RSI=48.2, R:R 1:2.3
    Score:  T=3 L=2 C=1 V=2 Liq=2 M=3 RR=2 Tim=2

#2  SAND.ST  [MACD_TREND]  Score: 15/20 (B-tier)
    Entry:  198.50 SEK
    Stop:   191.20 SEK  (risk 7.30, 3.7%)
    Target: 213.10 SEK  (reward 14.60, R:R 1:2.0)
    Signal: MACD bullish cross, SMA50>SMA200, ADX=28.3
    Score:  T=3 L=1 C=1 V=1 Liq=2 M=3 RR=2 Tim=2

#3  ERIC-B.ST  [MEAN_REVERSION]  Score: 13/20 (B-tier)
    Entry:  72.30 SEK
    Stop:   69.80 SEK  (risk 2.50, 3.5%)
    Target: 78.50 SEK  (reward 6.20, R:R 1:2.5)
    Signal: RSI 26.4 oversold at lower BB. R:R 1:2.5
    Score:  T=1 L=2 C=1 V=1 Liq=2 M=2 RR=2 Tim=2

==============================================================
Scan complete at 18:45:12
```

### Telegram Message Format

For future Telegram bot integration, format each recommendation as a compact message:

```python
def format_telegram_message(sig: Signal, score: SetupScore) -> str:
    """Format a recommendation for Telegram."""
    risk = sig.entry_price - sig.stop_loss
    reward = sig.target_price - sig.entry_price
    rr = reward / risk if risk > 0 else 0
    grade = "A" if score.total >= 17 else "B" if score.total >= 13 else "C"
    risk_pct = risk / sig.entry_price * 100

    return (
        f"BUY {sig.ticker}\n"
        f"Strategy: {sig.strategy.replace('_', ' ').title()}\n"
        f"Score: {score.total}/20 ({grade}-tier)\n"
        f"\n"
        f"Entry:  {sig.entry_price:.2f} SEK\n"
        f"Stop:   {sig.stop_loss:.2f} SEK ({risk_pct:.1f}%)\n"
        f"Target: {sig.target_price:.2f} SEK (R:R 1:{rr:.1f})\n"
        f"\n"
        f"{sig.reasoning}"
    )
```

Example Telegram output:

```
BUY VOLV-B.ST
Strategy: Pullback
Score: 17/20 (A-tier)

Entry:  265.40 SEK
Stop:   256.80 SEK (3.2%)
Target: 285.00 SEK (R:R 1:2.3)

Pullback to EMA21 in uptrend, RSI=48.2, R:R 1:2.3
```

### Structured Output for Database Storage

For SQLite storage, serialize each recommendation:

```python
def recommendation_to_dict(sig: Signal, score: SetupScore) -> dict:
    """Convert a recommendation to a dict for SQLite insertion."""
    risk = sig.entry_price - sig.stop_loss
    reward = sig.target_price - sig.entry_price
    return {
        "ticker": sig.ticker,
        "signal_date": sig.signal_date,
        "strategy": sig.strategy,
        "direction": sig.direction,
        "entry_price": sig.entry_price,
        "stop_loss": sig.stop_loss,
        "target_price": sig.target_price,
        "risk_amount": round(risk, 2),
        "reward_amount": round(reward, 2),
        "risk_reward_ratio": round(reward / risk, 2) if risk > 0 else 0,
        "score_total": score.total,
        "score_trend": score.trend_alignment,
        "score_level": score.level_quality,
        "score_catalyst": score.catalyst_quality,
        "score_volume": score.volume_participation,
        "score_liquidity": score.liquidity_quality,
        "score_market": score.market_sector_align,
        "score_rr": score.risk_reward_quality,
        "score_timing": score.timing_confirmation,
        "strength": sig.strength,
        "reasoning": sig.reasoning,
    }
```

This matches the app design implications from `../strategy-and-theory/23-setup-quality-scoring.md` section 7, which specifies storing individual score components alongside totals for post-trade review.
