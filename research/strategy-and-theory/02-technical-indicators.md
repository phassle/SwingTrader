# Technical Analysis Indicators for Swing Trading

## Reference Document for Implementation

This document covers the major technical analysis indicators used in swing trading, including their mathematical formulas, interpretation, parameter choices, and implementation considerations.

---

## Table of Contents

1. [Moving Averages (SMA, EMA, DEMA, TEMA)](#1-moving-averages)
2. [RSI (Relative Strength Index)](#2-rsi-relative-strength-index)
3. [MACD (Moving Average Convergence Divergence)](#3-macd-moving-average-convergence-divergence)
4. [Bollinger Bands](#4-bollinger-bands)
5. [Stochastic Oscillator](#5-stochastic-oscillator)
6. [Volume Indicators (OBV, VWAP, Volume Profile)](#6-volume-indicators)
7. [ATR (Average True Range)](#7-atr-average-true-range)
8. [Fibonacci Retracements and Extensions](#8-fibonacci-retracements-and-extensions)
9. [Ichimoku Cloud](#9-ichimoku-cloud)
10. [ADX (Average Directional Index)](#10-adx-average-directional-index)

---

## 1. Moving Averages

Moving averages smooth price data to identify trend direction and potential support/resistance levels. They are the foundation of many other indicators.

### 1.1 Simple Moving Average (SMA)

#### Formula

```
SMA(n) = (P_1 + P_2 + ... + P_n) / n
```

Where `P_i` is the closing price at period `i`, and `n` is the lookback period.

#### Implementation Notes

- Requires a buffer of `n` data points before the first value can be calculated.
- Can be computed incrementally: when a new price arrives, subtract the oldest price and add the new one, then divide by `n`.

```
SMA_new = SMA_old + (P_new - P_oldest) / n
```

#### Interpretation

- Price above SMA = bullish bias; price below = bearish bias.
- SMA crossovers (e.g., 50-day crosses above 200-day = "Golden Cross"; below = "Death Cross") signal trend changes.
- Acts as dynamic support/resistance.

#### Common Periods for Swing Trading

| Period | Use Case |
|--------|----------|
| 9-10   | Short-term trend, fast signals |
| 20-21  | Intermediate trend, commonly used with Bollinger Bands |
| 50     | Medium-term trend, institutional reference |
| 200    | Long-term trend, major support/resistance |

#### Strengths

- Simple to calculate and understand.
- Works well in trending markets.
- Equal weighting means no single price dominates.

#### Weaknesses

- Lags significantly, especially with larger periods.
- Equal weighting of all prices may not reflect current conditions.
- Generates false signals in ranging/choppy markets.
- Abrupt price changes ("drop-off effect") can cause sudden moves when an old extreme price leaves the window.

---

### 1.2 Exponential Moving Average (EMA)

#### Formula

```
EMA_today = (Price_today * k) + (EMA_yesterday * (1 - k))
```

Where the smoothing multiplier `k` is:

```
k = 2 / (n + 1)
```

#### Initialization

The first EMA value is typically seeded with the SMA of the first `n` periods.

#### Implementation Notes

- Recursive formula: each new EMA depends only on the previous EMA and the current price.
- All historical prices contribute (weights decay exponentially), so there is no "drop-off" effect.
- Convergence: after approximately `3.45 * n` periods, the initial seed value contributes less than 1% to the current EMA.

#### Interpretation

- Reacts faster to recent price changes than SMA.
- Same crossover and support/resistance logic as SMA.
- EMA(9) and EMA(21) crossovers are popular swing trading signals.

#### Common Periods for Swing Trading

| Period | Use Case |
|--------|----------|
| 9      | Fast signal line, used in MACD |
| 12     | MACD fast line |
| 20-21  | Swing trading "standard" |
| 26     | MACD slow line |
| 50     | Medium-term trend |
| 200    | Long-term trend filter |

#### Strengths

- More responsive to recent price changes than SMA.
- No drop-off effect.
- Better for capturing trend changes early.

#### Weaknesses

- Still lags, though less than SMA.
- More susceptible to whipsaws in choppy markets due to faster response.
- Requires a seed value (first calculation depends on initialization method).

---

### 1.3 Double Exponential Moving Average (DEMA)

#### Formula

```
DEMA(n) = 2 * EMA(n) - EMA(EMA(n))
```

Where `EMA(EMA(n))` means applying an EMA of period `n` to the EMA series itself.

#### Implementation Notes

1. Calculate `EMA1 = EMA(price, n)`
2. Calculate `EMA2 = EMA(EMA1, n)`
3. `DEMA = 2 * EMA1 - EMA2`

The "double smoothing" component `EMA2` captures the lag in `EMA1`. Subtracting it and doubling `EMA1` effectively removes much of the lag.

#### Interpretation

- Tracks price more closely than EMA.
- Used as a drop-in replacement for EMA/SMA when faster response is desired.
- Good for identifying trend changes earlier.

#### Common Periods for Swing Trading

Same as EMA. Typical: 9, 20, 50.

#### Strengths

- Significantly reduced lag compared to EMA and SMA.
- Smoother than simply using a shorter-period EMA.

#### Weaknesses

- Can overshoot price during reversals (overreacts).
- More complex to implement.
- Can generate more false signals in choppy markets.
- Requires `2 * n` periods of data to fully initialize.

---

### 1.4 Triple Exponential Moving Average (TEMA)

#### Formula

```
TEMA(n) = 3 * EMA1 - 3 * EMA2 + EMA3
```

Where:
- `EMA1 = EMA(price, n)`
- `EMA2 = EMA(EMA1, n)`
- `EMA3 = EMA(EMA2, n)`

#### Implementation Notes

1. Calculate three layers of EMA, each applied to the previous.
2. Combine using the formula above.
3. Requires `3 * n` periods of data for full initialization.

#### Interpretation

- Even less lag than DEMA.
- Excellent for identifying trend changes very early.
- Used the same way as other moving averages for crossovers and trend direction.

#### Strengths

- Minimal lag among moving average types.
- Good for fast-moving markets.

#### Weaknesses

- Most prone to overshooting and false signals.
- Most complex to implement of the moving average family.
- Can be too sensitive for higher-timeframe analysis.

---

### 1.5 Moving Average Comparison Summary

| Type | Lag    | Sensitivity | False Signals | Complexity |
|------|--------|-------------|---------------|------------|
| SMA  | High   | Low         | Low           | Minimal    |
| EMA  | Medium | Medium      | Medium        | Low        |
| DEMA | Low    | High        | Medium-High   | Medium     |
| TEMA | Lowest | Highest     | Highest       | High       |

### 1.6 Best Practices for Swing Trading

- Use longer MAs (50, 200) as **trend filters** (only trade in direction of the long-term MA).
- Use shorter MAs (9, 20) for **entry/exit signals**.
- Combine multiple MAs for confluence (e.g., price above 200 SMA AND crossing above 20 EMA = strong bullish entry).
- In ranging markets, reduce reliance on MA crossovers.

---

## 2. RSI (Relative Strength Index)

Developed by J. Welles Wilder Jr. (1978). A momentum oscillator that measures the speed and magnitude of recent price changes.

### Formula

```
RSI = 100 - (100 / (1 + RS))
```

Where:

```
RS = Average Gain over n periods / Average Loss over n periods
```

#### Calculation Steps

1. For each period, calculate the price change: `change = close_today - close_yesterday`
2. Separate into gains (positive changes) and losses (absolute value of negative changes).
3. **First Average Gain** = sum of gains over first `n` periods / `n`
4. **First Average Loss** = sum of losses over first `n` periods / `n`
5. **Subsequent values** use Wilder's smoothing (a form of EMA):

```
Avg Gain = ((Previous Avg Gain) * (n - 1) + Current Gain) / n
Avg Loss = ((Previous Avg Loss) * (n - 1) + Current Loss) / n
```

This is equivalent to an EMA with `k = 1/n` (not `2/(n+1)`).

### Common Parameters

| Parameter | Standard | Alternatives |
|-----------|----------|--------------|
| Period    | 14       | 9 (faster), 21 or 25 (smoother) |
| Overbought | 70     | 80 (strong trend filter) |
| Oversold   | 30     | 20 (strong trend filter) |

### Interpretation

#### Overbought/Oversold

- RSI > 70: Overbought -- potential sell signal or warning.
- RSI < 30: Oversold -- potential buy signal or warning.
- **Important nuance**: In strong uptrends, RSI can remain overbought for extended periods. In strong downtrends, it can stay oversold. Use as a warning, not an automatic reversal signal.

#### Swing Trading Adjustment

- In uptrends, the RSI range tends to be 40-80. Buying at RSI ~40-50 in an uptrend is often better than waiting for 30.
- In downtrends, the RSI range tends to be 20-60. Selling at RSI ~50-60 in a downtrend can be effective.

#### Divergences

**Bullish Divergence**: Price makes a lower low, but RSI makes a higher low. Signals weakening bearish momentum -- potential reversal upward.

**Bearish Divergence**: Price makes a higher high, but RSI makes a lower high. Signals weakening bullish momentum -- potential reversal downward.

**Hidden Bullish Divergence**: Price makes a higher low, RSI makes a lower low. Signals trend continuation in an uptrend.

**Hidden Bearish Divergence**: Price makes a lower high, RSI makes a higher high. Signals trend continuation in a downtrend.

#### Failure Swings

**Bullish Failure Swing**: RSI drops below 30, bounces above 30, pulls back (stays above 30), then breaks above the prior bounce high. Strong buy signal.

**Bearish Failure Swing**: RSI rises above 70, drops below 70, bounces (stays below 70), then breaks below the prior dip low. Strong sell signal.

### Implementation Notes

- Wilder's smoothing uses `k = 1/n`, which differs from standard EMA (`k = 2/(n+1)`). This is critical for matching standard RSI calculations.
- The first `n` periods must use a simple average. All subsequent use the smoothed average.
- RSI is bounded between 0 and 100.
- Watch for division by zero: if average loss = 0, RSI = 100.

### Best Use Cases for Swing Trading

- Identify potential reversal points when combined with support/resistance levels.
- Divergence signals are among the most reliable RSI signals for swing trades.
- Use RSI as a filter: only take long swing trades when RSI is not overbought; only short when not oversold.
- Combine with price action (candlestick patterns) at support/resistance for high-probability entries.

### Strengths

- Bounded (0-100), making it easy to define levels.
- Works well for identifying momentum extremes and divergences.
- Versatile across timeframes.

### Weaknesses

- Can stay overbought/oversold for extended periods in strong trends.
- Standard levels (70/30) produce false signals in trending markets.
- Lagging by nature (based on historical data).
- Single-period spikes can distort the reading.

---

## 3. MACD (Moving Average Convergence Divergence)

Developed by Gerald Appel (1979). Shows the relationship between two EMAs and generates trend-following and momentum signals.

### Formula

```
MACD Line    = EMA(close, fast_period) - EMA(close, slow_period)
Signal Line  = EMA(MACD Line, signal_period)
Histogram    = MACD Line - Signal Line
```

### Common Parameters

| Parameter     | Standard | Alternatives |
|---------------|----------|--------------|
| Fast Period   | 12       | 8 (more sensitive) |
| Slow Period   | 26       | 21 (more sensitive) |
| Signal Period | 9        | 5 (more sensitive) |

### Implementation Notes

- Calculate the fast and slow EMAs first.
- MACD Line is unbounded (can be any positive or negative value).
- The Signal Line is simply an EMA of the MACD Line.
- The Histogram is derived, not independent.
- Requires sufficient data: at minimum `slow_period + signal_period` bars, though more is better for EMA convergence.

### Interpretation

#### Signal Line Crossovers

- **Bullish**: MACD Line crosses above Signal Line (histogram turns positive).
- **Bearish**: MACD Line crosses below Signal Line (histogram turns negative).
- These are the most common MACD trading signals.

#### Centerline Crossovers

- **Bullish**: MACD Line crosses above zero (fast EMA crosses above slow EMA).
- **Bearish**: MACD Line crosses below zero.
- Indicates overall trend direction.

#### Histogram Analysis

- Increasing histogram bars (positive and growing): strengthening bullish momentum.
- Decreasing histogram bars (positive but shrinking): weakening bullish momentum -- potential reversal warning.
- Same logic inverted for negative histogram.
- "Histogram peak/trough" can signal momentum shifts before actual crossovers.

#### Divergences

Same concept as RSI divergences:
- **Bullish Divergence**: Price makes lower low, MACD makes higher low.
- **Bearish Divergence**: Price makes higher high, MACD makes lower high.
- MACD divergences are considered strong signals, especially on daily/weekly charts.

### Best Use Cases for Swing Trading

- Signal line crossovers on the daily chart for entry/exit timing.
- Use centerline position as a trend filter (long above zero, short below zero).
- Histogram momentum shifts as early warning for position management.
- Combine with price action and support/resistance for confirmation.

### Strengths

- Combines trend-following (EMAs) with momentum (histogram).
- Versatile: provides multiple types of signals.
- Histogram gives early momentum warnings.
- Widely followed, making its signals somewhat self-fulfilling.

### Weaknesses

- Lagging indicator (based on EMAs, which lag).
- Produces false signals in ranging/sideways markets.
- Unbounded, so values cannot be compared across different securities.
- Signal line crossovers can whipsaw frequently in choppy conditions.

---

## 4. Bollinger Bands

Developed by John Bollinger (1980s). A volatility envelope placed above and below a moving average.

### Formula

```
Middle Band = SMA(close, n)
Upper Band  = Middle Band + (k * StdDev(close, n))
Lower Band  = Middle Band - (k * StdDev(close, n))
```

Where `StdDev(close, n)` is the **population** standard deviation of the closing prices over `n` periods.

### Standard Deviation Calculation

```
StdDev = sqrt( (1/n) * sum((P_i - SMA)^2) )
```

Note: Bollinger uses **population** standard deviation (divides by `n`), not **sample** standard deviation (divides by `n-1`). This matters for implementation accuracy.

### Common Parameters

| Parameter      | Standard | Alternatives |
|----------------|----------|--------------|
| Period (n)     | 20       | 10 (short-term), 50 (long-term) |
| Std Dev (k)    | 2        | 1.5 (tighter), 2.5 (wider) |

### Interpretation

#### Bollinger Squeeze

- When bands narrow significantly (low volatility), a large move is likely coming.
- **Implementation**: Calculate Bandwidth = `(Upper - Lower) / Middle`. A squeeze is when bandwidth reaches a multi-period low.
- Does not predict direction -- only that volatility is about to expand.
- Combine with other indicators (e.g., MACD, volume) for direction bias.

#### Band Breakouts

- Price closing above the upper band suggests strong bullish momentum.
- Price closing below the lower band suggests strong bearish momentum.
- In trending markets, "walking the band" (price staying near upper or lower band) is normal.

#### Mean Reversion

- In ranging markets, price touching the upper band and then reversing is a sell signal.
- Price touching the lower band and then reversing is a buy signal.
- **Key**: This works in sideways markets, not trending markets.
- Confirm with RSI or other momentum indicators.

#### %B Indicator (Derived)

```
%B = (Price - Lower Band) / (Upper Band - Lower Band)
```

- %B > 1: Price is above upper band.
- %B = 0.5: Price is at middle band.
- %B < 0: Price is below lower band.
- Useful for normalizing price position relative to the bands.

#### Bandwidth Indicator (Derived)

```
Bandwidth = (Upper Band - Lower Band) / Middle Band
```

- Low bandwidth = squeeze = low volatility.
- High bandwidth = expanded bands = high volatility.

### Best Use Cases for Swing Trading

- Squeeze detection for breakout trading setups.
- Mean reversion trades in clearly defined ranges.
- Trend confirmation: price consistently above/below middle band.
- Combine with volume for breakout confirmation.

### Strengths

- Adapts to volatility automatically.
- Provides visual context for "high" and "low" prices.
- Versatile for both trend-following and mean-reversion strategies.
- %B and Bandwidth provide quantifiable metrics.

### Weaknesses

- Not a standalone system -- requires confirmation from other indicators.
- Mean reversion signals fail in trending markets.
- Based on SMA and standard deviation, both of which lag.
- Band width during extreme volatility can make them less useful.

---

## 5. Stochastic Oscillator

Developed by George Lane (1950s). Compares a closing price to its price range over a given period.

### Formula

#### Fast Stochastic

```
%K = 100 * (Close - Lowest Low(n)) / (Highest High(n) - Lowest Low(n))
```

Where `Lowest Low(n)` and `Highest High(n)` are the lowest low and highest high over `n` periods.

#### Slow Stochastic (Standard)

```
%K_slow = SMA(%K_fast, smooth_k)
%D_slow = SMA(%K_slow, d_period)
```

The "slow" stochastic smooths the raw %K with a moving average, then %D is a moving average of the smoothed %K.

### Common Parameters

| Parameter   | Standard | Alternatives |
|-------------|----------|--------------|
| %K Period (n) | 14     | 5 (very fast), 9 (fast), 21 (slow) |
| %K Smoothing  | 3      | 1 (= fast stochastic) |
| %D Period     | 3      | 5 (smoother) |

### Implementation Notes

- Requires high, low, and close prices (not just close).
- Watch for division by zero: if `Highest High == Lowest Low`, set %K to 50 or previous value.
- Bounded between 0 and 100.
- "Full Stochastic" allows customization of all three parameters.

### Interpretation

#### Overbought/Oversold

- %K > 80: Overbought zone.
- %K < 20: Oversold zone.
- Same caveat as RSI: can remain in extreme zones during strong trends.

#### %K/%D Crossovers

- **Bullish**: %K crosses above %D in the oversold zone (below 20). Strong buy signal.
- **Bearish**: %K crosses below %D in the overbought zone (above 80). Strong sell signal.
- Crossovers in the middle range (20-80) are weaker signals.

#### Divergences

- **Bullish Divergence**: Price makes lower low, Stochastic makes higher low.
- **Bearish Divergence**: Price makes higher high, Stochastic makes lower high.

### Best Use Cases for Swing Trading

- Best in ranging/sideways markets for mean reversion entries.
- Use in trending markets only with trend confirmation (e.g., take only buy signals when above 200 SMA).
- %K/%D crossovers in oversold territory during uptrends = strong swing buy signal.
- Combine with support/resistance levels for high-probability entries.

### Strengths

- Bounded and easy to interpret.
- Works well in ranging markets.
- Leading indicator (based on price position within range, not lagged averages).
- Multiple signal types (crossovers, divergences, overbought/oversold).

### Weaknesses

- Produces many false signals in trending markets.
- Very sensitive (especially fast stochastic).
- Can remain in overbought/oversold zones during strong trends.
- Requires high/low/close data, not just close.

---

## 6. Volume Indicators

Volume confirms the strength of price moves. "Volume precedes price" is a core technical analysis principle.

### 6.1 On-Balance Volume (OBV)

Developed by Joseph Granville (1963).

#### Formula

```
If close_today > close_yesterday:  OBV = OBV_prev + volume_today
If close_today < close_yesterday:  OBV = OBV_prev - volume_today
If close_today == close_yesterday: OBV = OBV_prev
```

#### Implementation Notes

- OBV is a running cumulative total. The absolute value is meaningless -- only the direction and trend of OBV matter.
- Initialize OBV to 0 or to the first period's volume.
- Simple to compute -- one comparison and one addition per bar.

#### Interpretation

- **Rising OBV**: Buying pressure (volume on up days exceeds volume on down days).
- **Falling OBV**: Selling pressure.
- **OBV Divergence**: Price making new high but OBV not confirming = bearish warning. Price making new low but OBV not confirming = bullish warning.
- OBV breakouts can precede price breakouts.

#### Best Use Cases for Swing Trading

- Confirm breakouts: price breaks resistance AND OBV is trending up = strong confirmation.
- Divergences signal potential reversals.
- Apply a moving average to OBV for trend/crossover signals.

#### Strengths

- Simple to calculate and understand.
- Effective at confirming trends and breakouts.
- Leading indicator (volume often shifts before price).

#### Weaknesses

- Assigns all volume to either buyers or sellers (binary), which is a simplification.
- Does not account for the magnitude of price change, only direction.
- Can be noisy day-to-day.

---

### 6.2 Volume Weighted Average Price (VWAP)

#### Formula

```
VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
```

Where `Price` is typically the **typical price**:

```
Typical Price = (High + Low + Close) / 3
```

#### Implementation Notes

- VWAP is typically reset at the start of each trading session (intraday indicator).
- For swing trading, **anchored VWAP** is more useful: VWAP calculated from a specific anchor point (e.g., earnings date, swing low, breakout point).
- Running calculation: maintain cumulative sums of `(TP * Volume)` and `Volume`.

#### Interpretation

- Price above VWAP: Bullish bias (buyers in control).
- Price below VWAP: Bearish bias (sellers in control).
- VWAP acts as dynamic support/resistance.
- Institutional traders often reference VWAP for execution benchmarking.

#### Anchored VWAP for Swing Trading

- Anchor from significant highs/lows, earnings dates, or breakout points.
- Multiple anchored VWAPs can create a web of support/resistance.

#### Strengths

- Incorporates both price and volume.
- Widely used by institutions, making it a significant level.
- Anchored VWAP is highly flexible.

#### Weaknesses

- Standard VWAP resets daily -- limited for multi-day swing trades.
- Flattens as the session progresses (cumulative nature).
- Requires tick or intrabar volume data for accuracy.

---

### 6.3 Volume Profile

Volume Profile displays volume traded at each price level rather than over time.

#### Concept

- Creates a horizontal histogram showing how much volume occurred at each price level.
- **Point of Control (POC)**: The price level with the highest traded volume. Strongest support/resistance.
- **Value Area**: The price range where ~70% of volume was traded (one standard deviation). Defined by:
  - **Value Area High (VAH)**: Upper boundary.
  - **Value Area Low (VAL)**: Lower boundary.
- **High Volume Nodes (HVN)**: Price levels with significant volume clusters. Act as support/resistance.
- **Low Volume Nodes (LVN)**: Price levels with little volume. Price tends to move quickly through these zones.

#### Implementation Notes

- Requires tick-level or minute-level data with volume.
- Divide the price range into bins (e.g., $0.10 or $0.50 increments).
- Sum volume at each price bin.
- Can be calculated over any time range (session, week, custom).

#### Best Use Cases for Swing Trading

- Identify high-probability support/resistance levels based on traded volume.
- POC and Value Area boundaries are excellent targets and stop-loss reference points.
- LVNs indicate potential "fast move" zones.

#### Strengths

- Shows where actual trading activity occurred.
- More objective support/resistance than arbitrary price levels.
- Combines well with other indicators.

#### Weaknesses

- Computationally intensive with large datasets.
- Requires granular volume data.
- No standardized calculation -- bin size and time range affect results.

---

## 7. ATR (Average True Range)

Developed by J. Welles Wilder Jr. (1978). Measures volatility by decomposing the entire range of a price for a given period.

### Formula

#### True Range (TR)

```
TR = max(
    High - Low,
    abs(High - Previous Close),
    abs(Low - Previous Close)
)
```

The three components capture:
1. Current bar's range.
2. Gap up from previous close to current high.
3. Gap down from previous close to current low.

#### Average True Range

```
ATR_initial = (1/n) * sum(TR_1 to TR_n)     // Simple average for the first value
ATR = ((ATR_prev * (n - 1)) + TR_current) / n  // Wilder's smoothing for subsequent
```

This uses the same Wilder's smoothing as RSI (equivalent to EMA with `k = 1/n`).

### Common Parameters

| Parameter | Standard | Alternatives |
|-----------|----------|--------------|
| Period    | 14       | 7 (short-term), 20 (intermediate), 10 (common for swing) |

### Implementation Notes

- ATR is always positive.
- The first TR calculation does not need a "previous close" -- use `High - Low` for the first bar.
- ATR is expressed in price units (dollars, pips, etc.), making it security-specific.
- To normalize: `ATR% = ATR / Close * 100` (allows cross-security comparison).

### Interpretation

- **High ATR**: High volatility. Wider stops needed. Larger potential moves.
- **Low ATR**: Low volatility. Tighter stops possible. Potential breakout setup (similar to Bollinger Squeeze).
- **Rising ATR**: Increasing volatility (often during trends and breakouts).
- **Falling ATR**: Decreasing volatility (often during consolidation).

### ATR-Based Stop-Loss Placement

The primary swing trading use of ATR:

```
Long Stop-Loss  = Entry Price - (multiplier * ATR)
Short Stop-Loss = Entry Price + (multiplier * ATR)
```

Common multipliers:
| Multiplier | Use Case |
|------------|----------|
| 1.0 ATR    | Tight stop, more likely to be hit |
| 1.5 ATR    | Standard swing trading stop |
| 2.0 ATR    | Wide stop, allows for more noise |
| 2.5-3.0 ATR | Position trading / very volatile stocks |

#### Chandelier Exit (ATR-based trailing stop)

```
Chandelier Exit (Long)  = Highest High(n) - (multiplier * ATR(n))
Chandelier Exit (Short) = Lowest Low(n) + (multiplier * ATR(n))
```

Common: 22-period with 3x ATR multiplier.

### ATR for Position Sizing

```
Position Size = Risk Amount / (ATR * multiplier)
```

This normalizes risk across securities with different volatility levels.

### Best Use Cases for Swing Trading

- Stop-loss placement that adapts to current volatility.
- Position sizing based on volatility.
- Identifying low-volatility periods (potential breakout setups).
- Trailing stops using Chandelier Exit or Keltner Channels.

### Strengths

- Adapts to current market volatility.
- Accounts for gaps (unlike simple High-Low range).
- Universal applicability across all securities and timeframes.
- Essential for risk management.

### Weaknesses

- Does not indicate direction, only magnitude of movement.
- Can lag during sudden volatility changes.
- Multiplier choice is subjective.
- Not useful as a standalone trading signal.

---

## 8. Fibonacci Retracements and Extensions

Based on the Fibonacci sequence and the golden ratio. Not a calculated indicator but rather a framework for identifying potential support/resistance levels.

### Key Ratios

Derived from the Fibonacci sequence (0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, ...):

| Ratio   | Derivation | Use |
|---------|-----------|------|
| 23.6%   | Divide by number three places ahead | Shallow retracement |
| 38.2%   | Divide by number two places ahead | Moderate retracement |
| 50.0%   | Not a Fibonacci ratio, but widely used | Psychological midpoint |
| 61.8%   | Divide by next number (the golden ratio inverse) | Deep retracement, most significant |
| 78.6%   | Square root of 61.8% | Deep retracement |
| 100%    | Full retracement | Complete reversal |

### Fibonacci Retracement Calculation

Given a significant swing:

```
For an upswing (swing low to swing high):
  Level = Swing High - (Swing High - Swing Low) * ratio

For a downswing (swing high to swing low):
  Level = Swing Low + (Swing High - Swing Low) * ratio
```

### Fibonacci Extension Levels

Used to project profit targets beyond the original move:

| Ratio   | Use |
|---------|------|
| 100%    | Equal move extension |
| 127.2%  | Common first target |
| 161.8%  | Golden ratio extension, primary target |
| 200%    | Double move |
| 261.8%  | Extended target |

#### Calculation (using three points: A, B, C where A-B is the initial move and C is the retracement)

```
Extension Level = C + (B - A) * ratio
```

### Implementation Notes

- Requires identification of "significant" swing highs and lows -- this is the subjective part.
- Consider automating swing detection using a zig-zag indicator or fractals.
- Draw from the start of the swing to the end (direction matters).
- Multiple Fibonacci levels from different swings that cluster at the same price = **Fibonacci confluence** = stronger level.

### Best Use Cases for Swing Trading

- Identify potential support levels during pullbacks in an uptrend (buy at 38.2%, 50%, or 61.8% retracement).
- Set profit targets using extension levels.
- Fibonacci confluence zones are high-probability reversal areas.
- Combine with other support/resistance (horizontal levels, moving averages, trendlines).

### Strengths

- Self-fulfilling prophecy (widely watched by traders).
- Provides specific price levels for entries, exits, and stops.
- Works across all timeframes.
- Fibonacci confluence zones are powerful.

### Weaknesses

- Highly subjective (which swing high/low to use?).
- No theoretical basis in market mechanics -- based on a mathematical constant.
- Does not work in isolation; requires confirmation.
- Multiple levels mean at least one will often "work," creating confirmation bias.

---

## 9. Ichimoku Cloud (Ichimoku Kinko Hyo)

Developed by Goichi Hosoda (1960s, published 1969). A comprehensive indicator that defines support/resistance, trend direction, momentum, and trading signals in one view.

### Components and Formulas

#### Tenkan-sen (Conversion Line)

```
Tenkan-sen = (Highest High(9) + Lowest Low(9)) / 2
```

Midpoint of the 9-period high-low range. Similar to a short-term moving average but uses high/low midpoint instead of close.

#### Kijun-sen (Base Line)

```
Kijun-sen = (Highest High(26) + Lowest Low(26)) / 2
```

Midpoint of the 26-period high-low range. Medium-term equilibrium.

#### Senkou Span A (Leading Span A)

```
Senkou Span A = (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
```

#### Senkou Span B (Leading Span B)

```
Senkou Span B = (Highest High(52) + Lowest Low(52)) / 2, plotted 26 periods ahead
```

#### The Cloud (Kumo)

The area between Senkou Span A and Senkou Span B. When Span A > Span B, the cloud is "bullish" (often colored green). When Span B > Span A, the cloud is "bearish" (often colored red).

#### Chikou Span (Lagging Span)

```
Chikou Span = Current Close, plotted 26 periods back
```

### Common Parameters

| Parameter | Standard | Notes |
|-----------|----------|-------|
| Tenkan    | 9        | Some use 7 for crypto/forex |
| Kijun     | 26       | Some use 22 for crypto/forex |
| Senkou B  | 52       | Some use 44 for crypto/forex |
| Displacement | 26   | Same as Kijun period |

The original parameters (9, 26, 52) were designed for Japanese markets trading 6 days/week (roughly 1.5 weeks, 1 month, 2 months). Some traders adjust to 7, 22, 44 for 5-day markets, but the standard values are most widely used.

### Implementation Notes

- The cloud is plotted 26 periods **into the future**, so the current cloud was calculated 26 bars ago.
- Chikou Span is plotted 26 periods **into the past**.
- These time-shifted components make Ichimoku unique but require careful array indexing.
- For real-time analysis, the "future cloud" provides forward-looking support/resistance.

### Interpretation

#### Trend Identification

- Price above cloud: Bullish trend.
- Price below cloud: Bearish trend.
- Price inside cloud: Trend is transitioning/unclear.
- Cloud thickness indicates support/resistance strength.

#### Trading Signals

**TK Cross (Tenkan/Kijun crossover)**:
- Bullish: Tenkan crosses above Kijun.
  - Strong if above cloud.
  - Neutral if inside cloud.
  - Weak if below cloud.
- Bearish: Tenkan crosses below Kijun (same strength rules inverted).

**Kumo Breakout**:
- Price breaks above cloud = bullish.
- Price breaks below cloud = bearish.
- A thin cloud is easier to break; a thick cloud provides stronger support/resistance.

**Chikou Span Confirmation**:
- Chikou Span above price (26 periods ago) = bullish confirmation.
- Chikou Span below price (26 periods ago) = bearish confirmation.

**Kumo Twist**:
- When Senkou Span A crosses Senkou Span B, the cloud changes color.
- A future Kumo twist suggests a potential trend change.

#### The "Five-Line Confirmation"

The strongest signal occurs when all five conditions align:
1. Price above cloud.
2. Tenkan above Kijun.
3. Chikou Span above price (26 bars ago).
4. Senkou Span A above Senkou Span B (bullish cloud).
5. Price, Tenkan, and Kijun are all moving in the same direction.

### Best Use Cases for Swing Trading

- Comprehensive trend assessment in a single indicator.
- Cloud provides natural support/resistance zones.
- TK crosses above/below cloud for entry signals.
- Kumo twists as early warning of trend changes.
- Works particularly well on daily and weekly charts.

### Strengths

- All-in-one indicator: trend, momentum, support/resistance, and signals.
- Forward-looking component (projected cloud).
- Built-in signal strength classification (above/inside/below cloud).
- Works well in trending markets.

### Weaknesses

- Complex and visually busy.
- Produces late signals in choppy markets.
- Standard parameters may not suit all markets equally.
- Requires significant historical data (52+ periods).
- Can overwhelm charts when combined with other indicators.

---

## 10. ADX (Average Directional Index)

Developed by J. Welles Wilder Jr. (1978). Measures trend **strength** regardless of direction.

### Formula

#### Step 1: Directional Movement (DM)

```
+DM = High_today - High_yesterday  (if positive and > -DM, else 0)
-DM = Low_yesterday - Low_today    (if positive and > +DM, else 0)
```

Rules:
- If `+DM > -DM` and `+DM > 0`: use `+DM`, set `-DM = 0`.
- If `-DM > +DM` and `-DM > 0`: use `-DM`, set `+DM = 0`.
- If `+DM == -DM`: both are 0.
- Inside bars (both are negative): both are 0.

#### Step 2: Smoothed DM and TR

Apply Wilder's smoothing (period = n, typically 14):

```
Smoothed +DM = Previous Smoothed +DM - (Previous Smoothed +DM / n) + Current +DM
Smoothed -DM = Previous Smoothed -DM - (Previous Smoothed -DM / n) + Current -DM
Smoothed TR  = Previous Smoothed TR - (Previous Smoothed TR / n) + Current TR
```

(First values are simple sums of the first `n` periods.)

#### Step 3: Directional Indicators

```
+DI = 100 * (Smoothed +DM / Smoothed TR)
-DI = 100 * (Smoothed -DM / Smoothed TR)
```

#### Step 4: DX (Directional Index)

```
DX = 100 * abs(+DI - -DI) / (+DI + -DI)
```

#### Step 5: ADX

```
ADX_initial = average of first n DX values
ADX = ((Previous ADX * (n - 1)) + Current DX) / n  // Wilder's smoothing
```

### Common Parameters

| Parameter | Standard | Alternatives |
|-----------|----------|--------------|
| Period    | 14       | 10 (more responsive), 20 (smoother) |

### Implementation Notes

- ADX is bounded between 0 and 100 (in practice rarely exceeds 60-70).
- Requires `2n` bars of data for the first ADX value (n for smoothed DM/TR, then n for ADX smoothing).
- Uses Wilder's smoothing throughout (same as RSI and ATR).
- Watch for division by zero in the DX calculation when `+DI + -DI = 0`.

### Interpretation

#### ADX Levels

| ADX Value | Interpretation |
|-----------|---------------|
| 0-20      | Weak or no trend (ranging market) |
| 20-25     | Emerging trend |
| 25-50     | Strong trend |
| 50-75     | Very strong trend |
| 75-100    | Extremely strong trend (rare) |

#### Key Signals

**Trend Strength**:
- Rising ADX: Trend is strengthening (regardless of direction).
- Falling ADX: Trend is weakening.
- ADX rising above 25: Trend is strong enough to trade with trend-following strategies.
- ADX falling below 20: Market is ranging -- switch to mean-reversion strategies.

**+DI/-DI Crossovers**:
- `+DI` crosses above `-DI`: Bullish signal.
- `-DI` crosses above `+DI`: Bearish signal.
- These crossovers combined with ADX > 25 are high-quality signals.

**DI Spread**:
- Wide gap between `+DI` and `-DI`: Strong directional move.
- Narrow or overlapping: Choppy, directionless market.

### Best Use Cases for Swing Trading

- **Trend filter**: Only use trend-following strategies when ADX > 25.
- **Strategy selector**: ADX < 20 = use range-bound strategies (Stochastic, Bollinger Bands). ADX > 25 = use trend strategies (MACD, moving average crossovers).
- DI crossovers as directional signals, filtered by ADX level.
- Falling ADX after a strong trend = potential reversal or consolidation.

### Strengths

- Only indicator specifically designed to measure trend strength.
- Direction-agnostic (measures strength, not direction).
- Helps select appropriate strategies (trend-following vs. mean-reversion).
- Combines with nearly any other indicator effectively.

### Weaknesses

- Lagging (double-smoothed, so it reacts slowly).
- DI crossovers can produce false signals in choppy markets.
- Does not indicate trend direction on its own (need DI lines for that).
- Complex calculation with multiple smoothing steps.

---

## Indicator Combination Guidelines for Swing Trading

### Recommended Combinations

| Strategy Type | Primary Signal | Trend Filter | Momentum Confirm | Volume Confirm | Risk Management |
|--------------|----------------|-------------|-------------------|----------------|-----------------|
| Trend Following | EMA crossovers, MACD | 200 SMA, ADX > 25 | RSI not extreme | OBV trend | ATR stop-loss |
| Pullback Entry | Fibonacci 38.2-61.8% | Price above cloud | RSI ~40-50 in uptrend | Volume dry-up on pullback | ATR stop below Fib level |
| Breakout | Bollinger Squeeze | ADX rising from < 20 | MACD histogram growing | Volume spike, OBV breakout | ATR-based stop |
| Mean Reversion | Bollinger Band touch | ADX < 20 (ranging) | Stochastic oversold/overbought | Volume Profile POC | ATR or Bollinger middle band |

### Avoiding Redundancy

Do not stack similar indicators. They use overlapping data and create false confidence:

- **Redundant**: RSI + Stochastic (both momentum oscillators using similar inputs).
- **Redundant**: MACD + EMA crossover (MACD is literally an EMA crossover).
- **Better**: RSI (momentum) + ADX (trend strength) + OBV (volume) -- three different data dimensions.

### Category Classification

| Category | Indicators | Data Used |
|----------|-----------|-----------|
| Trend | SMA, EMA, DEMA, TEMA, Ichimoku | Price (close) |
| Momentum | RSI, MACD, Stochastic | Price (close, high, low) |
| Volatility | Bollinger Bands, ATR | Price (high, low, close) |
| Volume | OBV, VWAP, Volume Profile | Volume + Price |
| Trend Strength | ADX | Price (high, low, close) |
| Price Levels | Fibonacci | Swing highs/lows |

**Best practice**: Select one indicator from each relevant category for a well-rounded analysis.

---

## Implementation Priority for a Swing Trading System

### Phase 1: Core (Must Have)

1. **EMA** (9, 20, 50, 200) -- trend identification and signals
2. **RSI** (14) -- momentum and overbought/oversold
3. **ATR** (14) -- stop-loss placement and position sizing
4. **Volume** (raw) -- basic volume analysis

### Phase 2: Enhanced Signals

5. **MACD** (12, 26, 9) -- momentum confirmation
6. **Bollinger Bands** (20, 2) -- volatility and mean reversion
7. **Stochastic** (14, 3, 3) -- additional momentum in ranging markets
8. **OBV** -- volume trend confirmation

### Phase 3: Advanced

9. **ADX** (14) -- trend strength filter and strategy selection
10. **Fibonacci** -- price level targets
11. **Ichimoku** (9, 26, 52) -- comprehensive trend system
12. **VWAP / Volume Profile** -- institutional price levels

### Phase 4: Optimization

13. **DEMA/TEMA** -- reduced-lag alternatives to EMA
14. **Chandelier Exit** -- ATR-based trailing stops
15. **Anchored VWAP** -- context-specific volume-weighted levels

---

## Data Requirements Summary

| Indicator | Minimum Data Fields | Minimum Bars Needed |
|-----------|-------------------|---------------------|
| SMA(n)    | Close | n |
| EMA(n)    | Close | n (seed) + ~3.5n (convergence) |
| DEMA(n)   | Close | 2n + convergence |
| TEMA(n)   | Close | 3n + convergence |
| RSI(n)    | Close | n + 1 |
| MACD(f,s,sig) | Close | s + sig |
| Bollinger(n,k) | Close | n |
| Stochastic(n,sk,d) | High, Low, Close | n + sk + d |
| OBV       | Close, Volume | 2 |
| VWAP      | High, Low, Close, Volume | 1 (cumulative) |
| ATR(n)    | High, Low, Close | n + 1 |
| Ichimoku  | High, Low, Close | 52 + 26 (for future cloud) |
| ADX(n)    | High, Low, Close | 2n + 1 |
| Fibonacci | High, Low (swing points) | Depends on swing identification |
