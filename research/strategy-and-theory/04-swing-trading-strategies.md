# Swing Trading Strategies

## Reference Document for Implementation

This document catalogs the major swing trading strategies, organized by category. Each strategy includes specific entry rules, exit rules, stop-loss placement, position sizing guidance, ideal market conditions, realistic win rate expectations, and example setups. This serves as the strategic layer that sits on top of the technical indicators (document 02) and chart patterns (document 03).

---

## Table of Contents

1. [Trend-Following Strategies](#1-trend-following-strategies)
   - [1.1 Moving Average Crossover (Golden Cross / Death Cross)](#11-moving-average-crossover--golden-crossdeath-cross)
   - [1.2 EMA Crossover (9/21 EMA)](#12-ema-crossover-921-ema)
   - [1.3 Pullback / Retracement Trading](#13-pullback--retracement-trading)
   - [1.4 Breakout Trading](#14-breakout-trading)
2. [Mean Reversion Strategies](#2-mean-reversion-strategies)
   - [2.1 Bollinger Band Bounce](#21-bollinger-band-bounce)
   - [2.2 RSI Oversold/Overbought Reversals](#22-rsi-oversoldoverbought-reversals)
   - [2.3 Support/Resistance Bounce Trading](#23-supportresistance-bounce-trading)
3. [Momentum Strategies](#3-momentum-strategies)
   - [3.1 MACD Divergence Trading](#31-macd-divergence-trading)
   - [3.2 Relative Strength Screening](#32-relative-strength-screening)
   - [3.3 Sector Rotation](#33-sector-rotation)
4. [Combined / Advanced Strategies](#4-combined--advanced-strategies)
   - [4.1 Multi-Timeframe Analysis](#41-multi-timeframe-analysis)
   - [4.2 Supply and Demand Zones](#42-supply-and-demand-zones)
   - [4.3 Volume Spread Analysis](#43-volume-spread-analysis)
   - [4.4 Gap Trading Strategies](#44-gap-trading-strategies)
   - [4.5 Swing Failure Patterns](#45-swing-failure-patterns)
5. [Strategy Selection Framework](#5-strategy-selection-framework)
6. [Implementation Priorities](#6-implementation-priorities)

---

## 1. Trend-Following Strategies

Trend-following strategies assume that prices tend to move in sustained directional moves and that it is more profitable to trade with the prevailing trend than against it. These strategies typically have a win rate of 40-55% but compensate with favorable risk/reward ratios (often 1:2 or better).

### 1.1 Moving Average Crossover — Golden Cross/Death Cross

#### Concept

The Golden Cross occurs when a shorter-period moving average crosses above a longer-period moving average, signaling a potential bullish trend change. The Death Cross is the inverse. The classic pairing is the 50-day SMA crossing the 200-day SMA.

#### Entry Rules

**Long Entry (Golden Cross):**
- The 50-day SMA crosses above the 200-day SMA
- Price is above both moving averages at the time of the cross
- Volume on the crossover day should be above the 20-day average volume (confirmation)
- Preferably, the 200-day SMA has flattened or started turning up (not steeply declining)

**Short Entry (Death Cross):**
- The 50-day SMA crosses below the 200-day SMA
- Price is below both moving averages
- Elevated volume on the crossover day

**Filter (optional but recommended):**
- ADX > 20 to confirm the trend has directional strength
- Avoid entries when both MAs are flat and intertwined (choppy market)

#### Exit Rules

- **Primary exit:** When the opposite crossover occurs (Death Cross exits a long, Golden Cross exits a short)
- **Faster exit:** When price closes below the 50-day SMA for 3 consecutive days (long position)
- **Profit target:** Trail a stop at 2x ATR(14) below the highest close since entry
- **Time-based exit:** If the trade has not moved in the expected direction within 10-15 trading days, reassess

#### Stop-Loss Placement

- **Initial stop:** Below the most recent swing low at the time of entry, or 2x ATR(14) below entry price, whichever is tighter
- **Trailing stop:** Once in profit by 1x ATR, trail the stop at 2x ATR below the highest close
- **Hard stop:** 5-8% below entry price as an absolute maximum loss

#### Position Sizing

- Risk 1-2% of total account equity per trade
- Calculate position size: `(Account Equity × Risk%) / (Entry Price - Stop Price)`
- Because this is a longer-duration strategy, account for overnight gap risk by potentially sizing down to 1%

#### Best Market Conditions

- Works best in markets transitioning from ranging to trending
- Strong performance after prolonged consolidation periods
- Performs poorly in choppy, range-bound markets (frequent whipsaws)
- Best applied to large-cap stocks, major indices, and liquid ETFs

#### Win Rate and Expectancy

- **Win rate:** 35-45% (many false signals in sideways markets)
- **Average win:** 15-40% (captures large trend moves)
- **Average loss:** 3-8%
- **Risk/Reward ratio:** Typically 1:3 to 1:5 on winning trades
- **Edge:** The strategy is profitable because winning trades are significantly larger than losing trades

#### Example Setup

> **Stock XYZ** has been in a downtrend for 6 months with the 50-day SMA well below the 200-day SMA. Over the past 2 months, price has built a base and the 50-day SMA has curled upward. On Day T, the 50-day SMA crosses above the 200-day SMA. Price is at $52, sitting above both MAs. Volume is 1.5x the 20-day average. The most recent swing low is $48.
>
> - **Entry:** $52 on the crossover day close
> - **Stop:** $48 (the swing low), risking $4/share
> - **Position size:** With a $50,000 account risking 1.5%, risk = $750, so position = 187 shares ($9,724)
> - **Target:** Trail stop at 2x ATR; if ATR = $1.80, trail at $3.60 below highest close

#### Implementation Notes

- **Signal generation:** Compare the 50-period SMA and 200-period SMA values daily; trigger when the relationship flips
- **Lag warning:** This signal is inherently lagging by weeks or months. By the time the Golden Cross forms, a significant portion of the move has already occurred. It is best used as a trend confirmation tool rather than a precise entry timing tool
- **Combine with:** Pullback entries (section 1.3) after the cross occurs for better entry prices

---

### 1.2 EMA Crossover (9/21 EMA)

#### Concept

A faster-responding crossover system using exponential moving averages. The 9-EMA crossing the 21-EMA captures shorter swings and produces signals much sooner than the 50/200 SMA system. This is the bread-and-butter swing trading crossover.

#### Entry Rules

**Long Entry:**
- The 9-EMA crosses above the 21-EMA
- Price closes above both EMAs on the crossover candle
- The crossover occurs above the 50-EMA (trading with the higher-timeframe trend)
- Volume is above average on the crossover day
- ADX > 20 preferred

**Short Entry:**
- The 9-EMA crosses below the 21-EMA
- Price closes below both EMAs
- The crossover occurs below the 50-EMA

**Additional Filters:**
- Avoid entries if the 9 and 21 EMAs have been crossing back and forth more than twice in the last 20 days (choppy conditions)
- Better entries occur when the crossover follows a clear pullback rather than emerging from a tight range

#### Exit Rules

- **Signal exit:** Opposite crossover (9-EMA crosses back below the 21-EMA)
- **Profit target:** 2-3x the initial risk (stop distance)
- **Trailing stop:** When the trade is up 1.5x risk, move stop to breakeven. Then trail at the 21-EMA level
- **Partial exit:** Take 50% off at 2x risk, let the remainder ride with a trail at the 21-EMA

#### Stop-Loss Placement

- **Initial stop:** Below the most recent swing low, or below the 21-EMA minus 1x ATR(14)
- **Typical distance:** 1.5-3% below entry for most swing-tradable stocks
- **Tight stop variant:** Just below the low of the crossover candle (higher chance of being stopped out but better R:R if it works)

#### Position Sizing

- Risk 1-2% of account per trade
- This system generates more signals than the 50/200 system, so err toward 1% risk to handle more frequent losing trades
- Maximum 3-4 concurrent positions using this strategy to avoid overexposure

#### Best Market Conditions

- Trending markets with clear directional moves
- Stocks with ATR/price ratios between 2-5% (enough movement to profit but not so volatile that stops are constantly hit)
- Works on both daily and 4-hour charts; daily preferred for swing trading
- Avoid during earnings season for individual stocks (gap risk)

#### Win Rate and Expectancy

- **Win rate:** 45-55%
- **Average win:** 5-12%
- **Average loss:** 2-5%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Trades per month:** 3-6 per watched stock

#### Example Setup

> **Stock ABC** is in an uptrend (price above 50-EMA). Over the past 8 days, it pulled back and the 9-EMA dipped below the 21-EMA. On Day T, the 9-EMA crosses back above the 21-EMA at $105. The recent swing low is $101. ATR(14) = $2.50.
>
> - **Entry:** $105 at the close of the crossover day
> - **Stop:** $101 (swing low), risking $4/share
> - **Target 1:** $113 (2x risk)
> - **Target 2:** Trail remainder at 21-EMA
> - **Position size:** $50,000 account × 1.5% risk = $750 / $4 = 187 shares

#### Implementation Notes

- **Signal detection:** Check daily whether the 9-EMA value crosses the 21-EMA value
- **Sensitivity:** The 9/21 EMA system is faster than the 50/200 SMA but produces more false signals. Combining with a trend filter (e.g., price above 50-EMA for longs) greatly improves quality
- **Variants:** Some traders use 8/21, 10/20, or 13/34 EMA pairs. The exact numbers matter less than the concept of a fast EMA crossing a slow EMA
- **For the application:** This should be a core signal generator with configurable EMA periods

---

### 1.3 Pullback / Retracement Trading

#### Concept

Instead of entering at the moment of a crossover or breakout, pullback trading waits for a temporary dip within an established uptrend (or a temporary rally in a downtrend). This provides a better entry price, tighter stop-loss, and superior risk/reward. This is widely considered one of the highest-probability swing trading approaches.

#### Entry Rules

**Long Entry (Buying the Dip in an Uptrend):**

1. **Confirm the uptrend:**
   - Price is above the 50-day SMA/EMA
   - The 50-day SMA/EMA is sloping upward
   - ADX > 25 (strong trend)

2. **Identify the pullback:**
   - Price retraces toward a key support level: 20-EMA, 50-EMA, prior breakout level, or a Fibonacci retracement level (38.2%, 50%, 61.8%)
   - RSI pulls back to 40-50 range (from previously being above 60)
   - The pullback occurs on declining volume (sellers are not aggressive)

3. **Trigger the entry:**
   - A bullish reversal candle forms at the support level (hammer, engulfing, morning star)
   - Price closes back above the 9-EMA or 10-EMA after the pullback
   - Stochastic oscillator crosses up from below 30
   - Volume increases on the reversal candle

**Short Entry (Selling the Rally in a Downtrend):**
- Mirror the above rules: price below 50-EMA, rally to resistance (20-EMA, Fibonacci), bearish reversal candle on declining volume

#### Exit Rules

- **Target 1:** The prior swing high (the high before the pullback began)
- **Target 2:** 1.618x Fibonacci extension of the pullback
- **Trailing stop:** Once the prior swing high is reached, trail at the 10-EMA or 20-EMA
- **Time stop:** If the trade does not move in the expected direction within 5 trading days, close at the market

#### Stop-Loss Placement

- **Below the pullback low** (the lowest point of the retracement), minus a small buffer (0.5% or 0.5x ATR)
- **Alternative:** Below the next Fibonacci level down. If entry is at the 50% retracement, stop goes below the 61.8% or 78.6% level
- **Maximum stop distance:** 3% from entry. If the pullback low is more than 3% away, either skip the trade or use a tighter stop (accepting a higher probability of being stopped out)

#### Position Sizing

- Risk 1-2% of account
- Pullback trades often have tighter stops than breakout trades, allowing for larger position sizes while keeping dollar risk constant
- Maximum 5 concurrent pullback trades to maintain diversification

#### Best Market Conditions

- Established trending markets (up or down)
- Works exceptionally well in steady uptrends with periodic 3-5% pullbacks
- Avoid during market-wide selloffs (pullbacks may become trend reversals)
- Best when the broader market (SPY, QQQ) is also in an uptrend for long pullback trades
- Sector leaders pulling back to support in sector uptrends are ideal candidates

#### Win Rate and Expectancy

- **Win rate:** 55-65% (one of the higher win-rate strategies)
- **Average win:** 5-10%
- **Average loss:** 2-4%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Key advantage:** Higher win rate than breakout trading with comparable reward ratios

#### Example Setup

> **Stock DEF** has rallied from $60 to $80 over 6 weeks. It pulls back over 5 days to $73, which coincides with the 50% Fibonacci retracement ($70 to $80 move) and the 21-EMA. Volume has declined during the pullback. On Day T, a hammer candle forms at $73 on increased volume. RSI is at 45.
>
> - **Entry:** $73.50 (above hammer high)
> - **Stop:** $71.50 (below pullback low of $72), risking $2/share
> - **Target 1:** $80 (prior swing high) = 3.25x risk
> - **Target 2:** $84 (1.618 extension)
> - **Position size:** $50,000 × 1.5% = $750 / $2 = 375 shares

#### Implementation Notes

- **Pullback detection:** Identify when price is in an uptrend but has retraced by more than 1x ATR from the recent swing high. Monitor for bullish reversal candle patterns at support levels
- **Fibonacci automation:** Automatically draw Fibonacci retracements from the most recent swing low to swing high. Alert when price reaches 38.2%, 50%, or 61.8% levels
- **Confluence scoring:** Score pullback setups by how many support factors align (EMA support + Fibonacci level + prior resistance turned support + volume decline). Higher confluence = higher probability
- **This should be a primary strategy in the application** — it combines high win rate with favorable risk/reward

---

### 1.4 Breakout Trading

#### Concept

Breakout trading enters positions when price moves beyond a defined boundary — whether that is a consolidation range, a resistance/support level, a chart pattern boundary, or a previous high/low. The assumption is that breaking through a key level triggers new buying/selling and leads to a sustained move.

#### Entry Rules

**Consolidation Breakout (Range Breakout):**
- Price has traded in a defined range for at least 10-15 trading days (the longer, the more powerful the breakout)
- The range narrows over time (contracting volatility, visible as declining Bollinger Band width or declining ATR)
- **Entry trigger:** Price closes above the range high on volume at least 1.5x the 20-day average
- A retest of the breakout level (old resistance becomes new support) offers a second entry opportunity with lower risk

**Support/Resistance Breakout:**
- Identify a clear horizontal resistance level tested at least 2-3 times
- **Entry trigger:** Price closes above resistance with strong volume
- The more times a level has been tested, the more significant the breakout

**Chart Pattern Breakout:**
- Identify a chart pattern (ascending triangle, cup and handle, flag, etc.)
- **Entry trigger:** Price breaks the pattern boundary on volume
- See document 03 (Chart Patterns) for pattern-specific entries

#### Exit Rules

- **Measured move target:** The height of the consolidation range or pattern projected from the breakout point
  - Range breakout: Target = Breakout level + Range height
  - Triangle breakout: Target = Breakout level + Triangle height at widest point
  - Flag breakout: Target = Breakout level + Flagpole height
- **Trailing stop:** After reaching 1x risk in profit, trail at the 10-EMA or the breakout level (whichever is higher)
- **Failed breakout exit:** If price closes back inside the range within 2 days of the breakout, exit immediately (failed breakout / bull trap)

#### Stop-Loss Placement

- **Below the breakout level:** Place the stop just below the top of the range (the breakout level), minus 0.5% or 0.5x ATR as a buffer
- **Tighter alternative:** Below the low of the breakout candle
- **Wider alternative:** Below the midpoint of the consolidation range
- **Typical distance:** 2-4% from entry

#### Position Sizing

- Risk 1-1.5% of account per trade
- Breakout trades have a lower win rate than pullback trades, so conservative sizing is important
- Consider scaling in: enter half at the breakout, add the other half on a successful retest of the breakout level

#### Best Market Conditions

- Works in any market environment but best when the broader market is trending or transitioning from range-bound to trending
- Volatility contraction breakouts (VCPs) work especially well after a period of declining volatility
- Avoid breakout trading in extremely high-volatility environments (breakouts are more likely to fail)
- Works well on stocks with strong fundamental catalysts (earnings beats, new products) that align with the technical breakout

#### Win Rate and Expectancy

- **Win rate:** 35-50% (many breakouts fail or produce minimal follow-through)
- **Average win:** 8-20% (successful breakouts can run far)
- **Average loss:** 2-5%
- **Risk/Reward ratio:** 1:3 to 1:5 on winning trades
- **Key advantage:** Winning trades can be very large, compensating for the lower win rate

#### Example Setup

> **Stock GHI** has traded between $44 and $48 for 25 trading days. The range has tightened in the last week to $46-$48. Bollinger Band width is at a 30-day low. On Day T, price closes at $49.20 with volume 2.1x the 20-day average.
>
> - **Entry:** $49.20 at the close
> - **Stop:** $47.50 (just below the old resistance at $48), risking $1.70/share
> - **Target:** $53.20 (breakout point $48 + range height $4 = $52, or higher based on trailing)
> - **Position size:** $50,000 × 1% = $500 / $1.70 = 294 shares
> - **Failed breakout plan:** If price closes back below $48 within 2 days, exit immediately

#### Implementation Notes

- **Range detection:** Identify stocks where the high-low range over the last N days is within a threshold percentage (e.g., less than 10%). The Bollinger Band width indicator or ATR percentile rank are useful proxies
- **Volume confirmation:** This is critical for breakout trading. A breakout without volume is unreliable. Compare breakout day volume to the 20-day average
- **False breakout handling:** Implement a rule that closes the trade immediately if price returns inside the range within 1-2 candles. This is essential for capital preservation
- **Watchlist generation:** The application should scan for stocks in tight consolidation ranges (potential breakout candidates) and alert when volume surges occur

---

## 2. Mean Reversion Strategies

Mean reversion strategies assume that prices oscillate around a mean or equilibrium and will return to that mean after extended moves away from it. These strategies profit from temporary overextension. They work best in range-bound or mildly trending markets and tend to fail in strong trends.

### 2.1 Bollinger Band Bounce

#### Concept

Bollinger Bands (typically 20-period SMA with 2 standard deviation bands) expand and contract with volatility. When price touches or exceeds the outer bands, it is statistically overextended and likely to revert toward the mean (the middle band). This strategy buys at the lower band and sells at the upper band.

#### Entry Rules

**Long Entry (Lower Band Bounce):**
- Price touches or closes below the lower Bollinger Band (20, 2)
- RSI(14) is below 30 (confirming oversold conditions)
- A bullish reversal candle forms at the lower band (hammer, bullish engulfing, doji followed by green candle)
- Volume spikes on the touch of the lower band (capitulation selling) then declines, or volume increases on the reversal candle
- The middle band (20-SMA) is relatively flat or slightly upward-sloping (do not buy the lower band in a steep downtrend)

**Short Entry (Upper Band Bounce):**
- Price touches or closes above the upper Bollinger Band
- RSI(14) above 70
- Bearish reversal candle at the upper band
- Middle band is flat or slightly downward-sloping

**Critical Filter:**
- **Do not trade this strategy when bands are expanding rapidly** (i.e., a trend is developing). Bollinger Band bounces work in ranging/mildly trending conditions only
- Check Bollinger Band width: if width is above its 80th percentile over the last 100 days, avoid this strategy
- Check ADX: if ADX > 30, avoid mean reversion plays

#### Exit Rules

- **Primary target:** The middle band (20-SMA) — this is the "mean" in mean reversion
- **Extended target:** The opposite band (lower band entry targets upper band)
- **Partial exits:** Take 60% off at the middle band, trail the remaining 40% toward the upper band
- **Time stop:** If price has not moved back toward the middle band within 5 trading days, exit

#### Stop-Loss Placement

- **Below the lowest point of the band touch**, minus 1% or 1x ATR(14)
- **Alternative:** Use a fixed percentage stop of 3% below entry
- If the lower band itself is moving lower, use the band touch low as the reference, not the current band value
- Typical stop distance: 2-4%

#### Position Sizing

- Risk 1-1.5% per trade
- Because this is a counter-trend strategy, size conservatively
- Never allocate more than 3-4% of the portfolio to a single mean reversion trade

#### Best Market Conditions

- Range-bound markets where price oscillates within well-defined Bollinger Bands
- Low-ADX environments (ADX < 25)
- Stocks with a history of mean-reverting behavior (check if the stock has repeatedly bounced off the bands in the past 3-6 months)
- Works well on large-cap, highly liquid stocks and major ETFs

#### Win Rate and Expectancy

- **Win rate:** 60-70% (high, because mean reversion happens frequently in ranging markets)
- **Average win:** 3-6% (targets are modest: just back to the mean)
- **Average loss:** 2-4%
- **Risk/Reward ratio:** 1:1 to 1:2
- **Key advantage:** High win rate provides psychological comfort and steady returns
- **Key risk:** Occasional large losses when mean reversion fails and a trend develops

#### Example Setup

> **Stock JKL** has been ranging between $90 and $100 for 6 weeks. Bollinger Bands (20, 2) show the middle band at $95, lower band at $89, upper band at $101. On Day T, price drops to $89.50, touching the lower band. RSI is 27. A hammer candle forms with a long lower wick. ADX is 18 (no trend).
>
> - **Entry:** $90 (next day open above hammer high)
> - **Stop:** $87.50 (below the hammer low of $88.50, minus buffer), risking $2.50/share
> - **Target 1:** $95 (middle band) = 2x risk
> - **Target 2:** $100 (upper band area)
> - **Position size:** $50,000 × 1% = $500 / $2.50 = 200 shares

#### Implementation Notes

- **Band touch detection:** Alert when price is within 0.5% of or beyond the lower/upper Bollinger Band
- **Band squeeze detection:** Monitor Bollinger Band width. When it reaches a 6-month low, a large move is coming — but it could go either direction. Do not use mean reversion during a squeeze; wait for the expansion and then determine direction
- **Combine with RSI:** Bollinger Band + RSI confirmation dramatically improves this strategy's reliability
- **Keltner Channel filter:** If Bollinger Bands are inside the Keltner Channel (a "squeeze"), skip mean reversion trades

---

### 2.2 RSI Oversold/Overbought Reversals

#### Concept

RSI (Relative Strength Index) measures the speed and magnitude of price movements on a 0-100 scale. Readings below 30 indicate oversold conditions (selling may be exhausted), and readings above 70 indicate overbought conditions (buying may be exhausted). This strategy enters when RSI reaches extreme levels and then reverses.

#### Entry Rules

**Long Entry (Oversold Reversal):**
- RSI(14) drops below 30 (or below 20 for a stronger signal)
- **Do not enter immediately.** Wait for RSI to cross back above 30 from below (the "RSI reversal")
- Confirm with a bullish candle on the day RSI crosses above 30
- Price should be near a known support level (horizontal support, moving average, Fibonacci level)
- The broader market (SPY) should not be in free fall

**Short Entry (Overbought Reversal):**
- RSI(14) rises above 70 (or above 80 for stronger signal)
- Wait for RSI to cross back below 70 from above
- Bearish candle confirms
- Price near resistance

**Enhanced Entry (RSI Divergence):**
- Price makes a lower low, but RSI makes a higher low (bullish divergence) — stronger signal
- Price makes a higher high, but RSI makes a lower high (bearish divergence)
- See section 3.1 (MACD divergence) for more on divergence trading

#### Exit Rules

- **Target:** When RSI reaches the opposite extreme zone (enters long at RSI 30 area, targets RSI 60-70 area)
- **Measured target:** 2-3x the initial risk
- **Time-based exit:** Mean reversion should happen within 3-7 days. If RSI lingers in the 30-40 range for more than 7 days, the oversold reading may reflect a persistent downtrend, not a temporary dip
- **Trail:** Once RSI reaches 50, trail the stop at 1x ATR below the most recent candle low

#### Stop-Loss Placement

- **Below the low of the oversold period** (the lowest price while RSI was below 30), minus 1% buffer
- **Alternative:** Fixed 3% stop below entry
- If RSI drops below 20 after entry (deeper oversold), reassess but do not widen the stop. If the stop is not hit, the position is still valid; if it is hit, accept the loss

#### Position Sizing

- Risk 1-1.5% of account
- RSI reversal trades are counter-trend and can fail quickly, so conservative sizing is key
- Maximum 2-3 concurrent RSI reversal trades

#### Best Market Conditions

- Range-bound markets or mild uptrends with periodic pullbacks
- Stocks with a track record of RSI reversals at 30/70 (check the chart for the past year)
- Avoid in strongly trending markets: in a powerful downtrend, RSI can stay below 30 for weeks
- Works best on stable, large-cap stocks and major indices

#### Win Rate and Expectancy

- **Win rate:** 55-65%
- **Average win:** 3-7%
- **Average loss:** 2-4%
- **Risk/Reward ratio:** 1:1.5 to 1:2
- **Note:** Win rate drops significantly in trending markets. The filter for trend strength (ADX < 25) is critical

#### Example Setup

> **Stock MNO** is trading around $150 in a gentle uptrend (above 200-day SMA, which is rising). Over 5 days, it drops from $155 to $142 on moderate volume. RSI drops to 24 at $142. The next day, a bullish engulfing candle forms at $143 and RSI crosses back above 30 (RSI = 33). The $142 level coincides with the 50-day SMA.
>
> - **Entry:** $143.50 on the close of the RSI crossover day
> - **Stop:** $139.50 (below the $142 low, minus buffer), risking $4/share
> - **Target:** $152 (prior swing high where RSI was ~65), = 2.1x risk
> - **Position size:** $50,000 × 1.5% = $750 / $4 = 187 shares

#### Implementation Notes

- **RSI crossover detection:** Track when RSI crosses above 30 from below (long signal) or below 70 from above (short signal)
- **RSI divergence detection:** Compare price lows/highs with RSI lows/highs over the last 10-30 bars. This requires a swing-point detection algorithm
- **Configurable thresholds:** Some traders use 25/75 or 20/80 instead of 30/70. More extreme thresholds produce fewer but higher-quality signals
- **Multi-timeframe RSI:** Weekly RSI oversold + daily RSI oversold = very strong signal

---

### 2.3 Support/Resistance Bounce Trading

#### Concept

Price tends to react at levels where it has previously reversed, because these levels represent zones of supply (resistance) and demand (support) where many orders are clustered. This strategy buys at support and sells at resistance in a range-bound market.

#### Entry Rules

**Long Entry (Support Bounce):**
- Identify a clear horizontal support level tested at least 2-3 times previously
- Price approaches the support level from above
- A bullish reversal candle (hammer, engulfing, pin bar) forms within 1% of the support level
- Volume pattern: high volume on the support touch (absorption of selling), or a volume dry-up on the approach followed by a volume spike on the reversal
- RSI is in the 30-40 range (oversold or approaching oversold)

**Short Entry (Resistance Bounce):**
- Clear horizontal resistance tested 2+ times
- Price approaches from below
- Bearish reversal candle within 1% of resistance
- RSI in the 60-70 range

**Confirmation Filters:**
- The range between support and resistance should be at least 5% (otherwise, there is not enough room to profit after stops and commissions)
- The support/resistance levels should be clearly visible on a daily chart without ambiguity
- Higher-timeframe trend should be neutral or aligned (do not buy support in a weekly downtrend)

#### Exit Rules

- **Primary target:** The opposite boundary (buy at support, target resistance)
- **Partial exit:** Take 50% at the midpoint of the range
- **Trail remainder:** Trail at 1x ATR below the most recent swing low after the midpoint
- **Failed support exit:** If price closes below support (for a long) by more than 1%, exit immediately. The support level has broken and the thesis is invalidated

#### Stop-Loss Placement

- **Below support by 1-2%** (accounts for false breaks and wicks below support)
- **Alternative:** Below the reversal candle low
- **Tighter option:** 0.5% below support (accepts more stop-outs for a better R:R)
- Typical stop distance: 1.5-3%

#### Position Sizing

- Risk 1-2% of account
- Because support/resistance bounces can have tight stops, position sizes can be relatively large in dollar terms
- Maximum 4-5 concurrent S/R bounce trades

#### Best Market Conditions

- Clear range-bound markets with well-defined support and resistance
- Works on all timeframes but daily chart is standard for swing trading
- Performs best in low-volatility, high-liquidity environments
- Avoid during news-driven moves that can blow through support/resistance levels

#### Win Rate and Expectancy

- **Win rate:** 55-65% (support and resistance do hold more often than they break, especially on early tests)
- **Average win:** 4-8% (depends on the width of the range)
- **Average loss:** 2-3%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Note:** The more times a level has been tested, the weaker it becomes (each test absorbs some of the resting orders). The 3rd or 4th test of support is more likely to break than the 2nd

#### Example Setup

> **Stock PQR** has bounced off $60 support three times over 2 months and been rejected at $68 resistance twice. On Day T, price drops to $60.30 and forms a bullish engulfing candle. RSI is at 35. Volume on the engulfing candle is above average.
>
> - **Entry:** $61.00 (above the engulfing candle high)
> - **Stop:** $58.80 (2% below support), risking $2.20/share
> - **Target 1:** $64.00 (midpoint) — partial exit
> - **Target 2:** $67.50 (just below resistance)
> - **Position size:** $50,000 × 1.5% = $750 / $2.20 = 340 shares

#### Implementation Notes

- **Support/resistance detection:** This is one of the harder things to automate. Approaches include:
  - Pivot point calculations (standard, Fibonacci, Camarilla)
  - Finding price levels with the most "touches" (clustering algorithm on swing highs/lows)
  - Volume profile: price levels with the highest volume concentration act as S/R
  - Horizontal levels where price has reversed at least 2 times within a defined tolerance zone (e.g., within 1%)
- **Level strength scoring:** Score S/R levels by: number of touches, timeframe (weekly level > daily level), how recently the level was tested, and how strongly price reacted
- **Breakout vs. bounce:** The application should track whether a level is more likely to hold (bounce trade) or break (breakout trade). After 3-4 tests, shift bias toward a breakout

---

## 3. Momentum Strategies

Momentum strategies capitalize on the observation that stocks that have been performing well tend to continue performing well in the short to medium term, and vice versa. These strategies focus on the rate of change and relative performance rather than absolute price levels.

### 3.1 MACD Divergence Trading

#### Concept

MACD divergence occurs when the direction of the MACD indicator disagrees with the direction of price. This disagreement signals weakening momentum and a potential reversal. Bullish divergence (price falling, MACD rising) suggests upside ahead; bearish divergence (price rising, MACD falling) suggests downside ahead.

#### Entry Rules

**Bullish Divergence (Long Entry):**
1. Price makes a lower low (point B is lower than point A)
2. MACD histogram or MACD line makes a higher low at the same points (the dip at B is shallower than at A)
3. Both points A and B should ideally be below the zero line on the MACD
4. **Entry trigger:** Price closes above the high of the most recent 3-5 candles (a minor resistance break confirming the reversal)
5. Alternatively, enter when the MACD histogram turns positive after the divergence pattern

**Bearish Divergence (Short Entry):**
1. Price makes a higher high
2. MACD makes a lower high
3. Both highs preferably above the MACD zero line
4. Enter when price closes below the low of the recent 3-5 candles

**Quality Filters:**
- The divergence should develop over 10-50 bars. Divergences over fewer than 5 bars are unreliable
- The price move between points A and B should be at least 3% (meaningful divergence, not noise)
- Volume should decline on the second leg (point B), confirming weakening momentum
- Hidden divergence (trend continuation signal): price makes a higher low but MACD makes a lower low in an uptrend — this signals trend continuation, not reversal

#### Exit Rules

- **Target:** The price level of the swing that started the divergence pattern (i.e., the high between points A and B for bullish divergence)
- **Extended target:** 1.618x Fibonacci extension of the divergence pattern range
- **MACD exit:** When MACD produces an opposite signal (bearish crossover after a bullish divergence entry)
- **Time stop:** If no meaningful move within 7-10 days, the divergence signal may have been absorbed

#### Stop-Loss Placement

- **Below point B** (the most recent swing low in a bullish divergence setup), minus 1% buffer
- The stop should never exceed 4% from entry
- If price makes a new low after entry (creating a triple divergence), the original stop is still valid — do not widen it

#### Position Sizing

- Risk 1-1.5% of account
- Divergence trades are reversal trades and inherently counter-trend, so size conservatively
- Maximum 2-3 concurrent divergence trades

#### Best Market Conditions

- Works in any market condition but is most reliable at the end of extended trends
- Best at significant support/resistance levels where divergence adds confirmation
- Less reliable in strongly trending markets (MACD can diverge for extended periods without a reversal)
- Works well combined with other strategies (divergence at support + Bollinger Band touch = high confidence)

#### Win Rate and Expectancy

- **Win rate:** 45-55%
- **Average win:** 5-10%
- **Average loss:** 3-5%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Note:** Divergence alone is not sufficient. It must be combined with a trigger (price confirmation) to be tradeable. Divergence without a trigger is just a warning, not a signal

#### Example Setup

> **Stock STU** drops from $50 to $42 (point A) over 3 weeks, with MACD histogram reaching -2.5. Price rallies to $46, then drops again to $40 (point B, a lower low). But the MACD histogram at point B only reaches -1.8 (a higher low = bullish divergence). Volume on the second drop is 30% lower than the first.
>
> On Day T, price closes at $42, above the 5-day high of $41.50, confirming the reversal.
>
> - **Entry:** $42
> - **Stop:** $39 (below point B low of $40, minus buffer), risking $3/share
> - **Target 1:** $46 (the high between A and B) = 1.33x risk
> - **Target 2:** $49 (1.618 extension) = 2.3x risk
> - **Position size:** $50,000 × 1.5% = $750 / $3 = 250 shares

#### Implementation Notes

- **Divergence detection algorithm:**
  1. Identify swing lows and swing highs in price (using a zigzag algorithm or similar)
  2. At each swing low in price, record the MACD histogram or line value
  3. Compare consecutive swing lows: if price low is lower but MACD low is higher, flag bullish divergence
  4. Require a minimum of 10 bars between the two swing points
- **Alert priority:** Divergence at key support/resistance should generate higher-priority alerts
- **Histogram vs. line divergence:** Histogram divergence is faster but less reliable. MACD line divergence is slower but more significant. Implement both and let the user configure

---

### 3.2 Relative Strength Screening

#### Concept

Relative strength (not RSI) measures a stock's performance relative to a benchmark (typically the S&P 500 or its sector). Stocks that outperform their benchmark tend to continue outperforming. This strategy identifies leaders and enters on pullbacks or breakouts.

#### Entry Rules

**Stock Selection:**
- Calculate the relative strength of each stock versus the S&P 500 over 1 month, 3 months, and 6 months
  - `RS = (Stock % change) / (SPY % change)` over the period
  - A stock with RS > 1 is outperforming
- Select stocks in the top 10-20% by relative strength across all three periods (consistent outperformers)
- The stock's relative strength line should be making new highs or trending upward

**Entry Trigger (once a strong RS stock is identified):**
- Use any of the trend-following entry methods (pullback to 21-EMA, breakout from consolidation, EMA crossover)
- Prefer pullback entries on RS leaders, as breakouts tend to be from higher prices
- Enter when the stock pulls back while the broader market is flat or slightly down (the stock is "resting," not "breaking down")

**Avoid:**
- Stocks in the bottom 20% by relative strength (laggards)
- Stocks whose RS line is declining even if the absolute price is rising

#### Exit Rules

- **Relative strength degradation:** If the stock's RS drops below 1.0 (underperforming the benchmark) for 5 consecutive days, exit
- **Standard trailing stop:** 2x ATR below the highest close
- **Profit target:** None — let winners run. This is a momentum strategy; cutting winners early destroys the edge
- **Technical exit:** If the stock breaks below its 50-day SMA, exit

#### Stop-Loss Placement

- **Below the most recent swing low** or 2x ATR below entry
- **Maximum stop:** 5% below entry (RS leaders should not need wide stops)
- Tighten the stop if the stock's RS starts declining before the stop is hit

#### Position Sizing

- Risk 1-2% per trade
- RS leaders have a statistical edge, so slightly larger position sizes (up to 2%) are justified
- Hold 5-10 RS leader positions simultaneously for diversification

#### Best Market Conditions

- Trending markets (up or down) — relative strength screening works by finding the leaders of the trend
- In bull markets, buy the strongest stocks. In bear markets, short the weakest
- During market corrections, RS leaders tend to fall less and recover faster
- Does not work well in a completely flat, directionless market

#### Win Rate and Expectancy

- **Win rate:** 50-60%
- **Average win:** 10-25% (leaders can make large moves)
- **Average loss:** 3-6%
- **Risk/Reward ratio:** 1:3 to 1:5
- **Academic backing:** Momentum/relative strength has been one of the most persistent market anomalies documented in financial research (Jegadeesh and Titman, 1993)

#### Example Setup

> During a market-wide rally, **Stock VWX** has gained 35% over 3 months while the S&P 500 has gained 12% (RS = 2.9). The stock is in a clear uptrend, well above its 50-day and 200-day SMAs. It pulls back 5% over 1 week to its 21-EMA on declining volume.
>
> - **Entry:** $78 at the 21-EMA bounce
> - **Stop:** $74 (below the pullback low), risking $4/share
> - **Target:** Trail at 2x ATR, no fixed target
> - **Position size:** $50,000 × 2% = $1,000 / $4 = 250 shares

#### Implementation Notes

- **RS calculation:** Calculate and rank relative strength for the entire stock universe daily. Store rankings for screening
- **RS line charting:** Plot the RS line (stock price / benchmark price) alongside the stock chart. An upward-sloping RS line means the stock is outperforming
- **Screening criteria:** Allow users to screen for stocks with RS > X over configurable periods
- **Sector-adjusted RS:** Also calculate RS relative to the stock's sector ETF (is this stock outperforming its sector, or is the whole sector strong?)

---

### 3.3 Sector Rotation

#### Concept

Different market sectors lead at different phases of the economic cycle. Sector rotation strategy involves identifying which sectors are gaining momentum, rotating capital into leading sectors, and rotating out of lagging ones. This is a higher-level portfolio strategy that determines where to allocate, after which individual stock selection strategies are applied.

#### Entry Rules

**Sector Identification:**
- Track the 11 GICS sectors via their ETFs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLRE, XLU, XLC)
- Calculate relative strength of each sector vs. SPY over 1-month, 3-month, and 6-month periods
- Rank sectors by composite relative strength

**Rotation Rules:**
- Overweight the top 3 sectors by composite RS
- Underweight or avoid the bottom 3 sectors
- Rebalance sector allocations monthly (or when a sector's RS rank changes by 3+ positions)
- Within leading sectors, select individual stocks using RS screening (section 3.2) or pullback trading (section 1.3)

**Economic Cycle Awareness:**
- **Early expansion:** Technology, Consumer Discretionary, Industrials tend to lead
- **Mid expansion:** Technology continues, Financials strengthen
- **Late expansion:** Energy, Materials, Industrials
- **Recession:** Utilities, Healthcare, Consumer Staples (defensive sectors)
- Use the yield curve, ISM manufacturing, and unemployment claims as cycle indicators

#### Exit Rules

- **Exit a sector when:** Its RS drops from the top 3 to below median (rank 6 or worse) for 2 consecutive weeks
- **Gradual rotation:** Do not rotate all at once. Over a 2-4 week period, reduce positions in weakening sectors and build in strengthening ones
- **Individual stock exits:** Use the standard trailing stop or RS degradation methods from section 3.2

#### Stop-Loss Placement

- At the individual stock level (see section 3.2)
- At the sector level: if a leading sector ETF drops below its 50-day SMA, reduce exposure by 50%. If below the 200-day SMA, exit entirely

#### Position Sizing

- Allocate 25-40% of capital to the top sector, 20-30% to the second, 15-20% to the third
- Remaining capital can be in cash or broad market exposure
- Within each sector, diversify across 3-5 individual stocks

#### Best Market Conditions

- Works in all market conditions because it is adaptive
- Strongest edge during major trend changes and sector leadership rotations
- Less useful in markets where all sectors move in lockstep (highly correlated sell-offs or broad rallies)

#### Win Rate and Expectancy

- **Win rate:** 55-65% (sectors trend more reliably than individual stocks)
- **Average win:** 8-15% per sector rotation (over 1-3 months)
- **Average loss:** 3-6%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Portfolio impact:** Sector rotation has been shown to add 2-5% annualized return versus a static allocation

#### Implementation Notes

- **Sector RS dashboard:** Build a dashboard showing the RS ranking of all 11 sectors with 1m, 3m, 6m columns. Update daily
- **Rotation alerts:** Alert when a sector moves into or out of the top 3 by RS
- **Heat map:** Visualize sector performance as a heat map for quick pattern recognition
- **Pair with fundamentals:** Leading sectors often align with macro trends (e.g., rising oil prices = Energy leading). Incorporating basic macro indicators can provide early signals

---

## 4. Combined / Advanced Strategies

These strategies combine multiple concepts or require more nuanced analysis. They are generally higher in complexity but can offer superior edge when executed correctly.

### 4.1 Multi-Timeframe Analysis

#### Concept

Multi-timeframe analysis (MTA) uses multiple chart timeframes to align trade direction, timing, and confidence. The higher timeframe determines the trend direction, the middle timeframe identifies the setup, and the lower timeframe provides the precise entry. This is not a standalone strategy but a framework that enhances any other strategy.

#### The Three-Timeframe Framework

| Role | Swing Trading Timeframes | Purpose |
|------|--------------------------|---------|
| **Strategic (Trend)** | Weekly chart | Determine the primary trend direction. Only trade in this direction |
| **Tactical (Setup)** | Daily chart | Identify specific trade setups (pullbacks, breakouts, divergences) |
| **Execution (Entry)** | 4-hour or 1-hour chart | Fine-tune entry timing and stop placement |

#### Entry Rules

1. **Weekly chart analysis:**
   - Determine the trend: Is price above the 40-week SMA (approximately 200-day)? Is the SMA rising?
   - If weekly trend is UP: only take long setups on the daily chart
   - If weekly trend is DOWN: only take short setups (or stay in cash)
   - Check weekly RSI: if oversold on weekly, a longer-term reversal may be starting

2. **Daily chart setup:**
   - Identify a trade setup using any strategy from this document (pullback, breakout, divergence, etc.)
   - Confirm that the daily setup aligns with the weekly trend direction

3. **4-hour / 1-hour entry:**
   - Once a daily setup is identified, drop to the 4-hour chart for a more precise entry
   - Wait for a bullish reversal on the 4-hour chart (e.g., 4-hour candle closes above the 4-hour 9-EMA)
   - This provides a tighter stop-loss and better risk/reward compared to entering on the daily chart alone

#### Exit Rules

- **Daily chart targets and trailing stops** (as defined by the specific strategy)
- **Weekly chart override:** If the weekly trend breaks (e.g., weekly close below the 40-week SMA), close all related positions regardless of daily chart status

#### Stop-Loss Placement

- Set stop based on the 4-hour chart structure (below the 4-hour swing low)
- This is typically 30-50% tighter than a stop based on the daily chart, significantly improving R:R
- Never let the daily-chart stop override the 4-hour stop (use the tighter stop)

#### Best Market Conditions

- All conditions. MTA is a universal enhancement, not a condition-specific strategy
- Most impactful in markets where the daily and weekly trends are clearly aligned

#### Win Rate and Expectancy

- MTA improves any base strategy by approximately:
  - +5-10% win rate (by filtering out trades against the higher-timeframe trend)
  - +0.5-1.0 R:R improvement (by tightening entries and stops)
- The overhead is more analysis time per trade and potentially fewer signals (which is often a benefit)

#### Implementation Notes

- **Timeframe data storage:** The application needs to store and process data on multiple timeframes (weekly, daily, 4-hour minimum)
- **Trend alignment indicator:** Create a simple "traffic light" system:
  - Green: Weekly and daily trends aligned (high confidence)
  - Yellow: Weekly trend unclear, daily trend present (medium confidence)
  - Red: Weekly and daily trends conflicting (avoid)
- **Automated alignment:** For every daily signal, automatically check the weekly trend and assign a confidence score

---

### 4.2 Supply and Demand Zones

#### Concept

Supply and demand zones are areas on the chart where a strong imbalance between buyers and sellers caused a sharp move away. Unlike traditional support/resistance (which are lines), supply/demand zones are ranges. These zones are powerful because they represent unfilled institutional orders — when price returns to the zone, those orders may be executed again, causing another move.

#### Identifying Zones

**Demand Zone (Bullish):**
- A sharp, impulsive move up from a basing area
- The base before the impulse move is the demand zone
- Characteristics: consolidation (1-5 candles) followed by a strong bullish candle that closes well above the consolidation
- The zone extends from the low of the consolidation to the open of the impulse candle

**Supply Zone (Bearish):**
- A sharp, impulsive move down from a topping area
- The base before the drop is the supply zone
- Characteristics: consolidation followed by a strong bearish candle closing well below
- The zone extends from the high of the consolidation to the open of the impulse candle

**Zone Quality Scoring:**
- **Strength of departure:** How far did price move away from the zone? Larger moves = stronger zone
- **Time at the zone:** Less time spent at the zone = more unfilled orders remaining = stronger
- **Freshness:** Has price returned to the zone since it was created? Fresh (untested) zones are strongest
- **Trend alignment:** Zones that align with the prevailing trend are more reliable

#### Entry Rules

**Long Entry at Demand Zone:**
- Price returns to a previously identified demand zone
- Set a limit buy order at the top of the demand zone (aggressive) or wait for a bullish reversal candle within the zone (conservative)
- The zone should be "fresh" — price is returning for the first time
- Higher-timeframe trend should be bullish

**Short Entry at Supply Zone:**
- Price returns to a supply zone
- Set a limit sell/short at the bottom of the supply zone or wait for a bearish reversal candle
- Fresh zone, higher-timeframe trend bearish

#### Exit Rules

- **Target:** The next supply zone above (for longs) or demand zone below (for shorts)
- **Alternative target:** 3x the risk
- **Trail:** After 2x risk in profit, trail at 1x ATR below the most recent low

#### Stop-Loss Placement

- **Below the demand zone** (the low of the zone) for longs, by 0.5-1%
- **Above the supply zone** for shorts
- Zones are invalidated if price trades through them — exit immediately if this occurs

#### Position Sizing

- Risk 1-2% per trade
- Fresh, high-quality zones justify closer to 2% risk
- Lower quality or retested zones justify 1% or less

#### Best Market Conditions

- Works in all conditions but strongest in trending markets
- Fresh zones in strongly trending stocks are the highest probability setups
- Avoid zones that have been tested multiple times (each test weakens the zone)

#### Win Rate and Expectancy

- **Win rate:** 55-65% for fresh, high-quality zones; 40-50% for retested zones
- **Average win:** 5-12%
- **Average loss:** 2-4%
- **Risk/Reward ratio:** 1:2 to 1:3

#### Implementation Notes

- **Zone detection algorithm:**
  1. Identify candles with a body size > 2x the average body size of the previous 10 candles (impulse candles)
  2. Look back from the impulse candle to find the 1-5 candles of consolidation preceding it
  3. Define the zone as the range of the consolidation candles
  4. Track whether price has returned to the zone (freshness)
- **Zone visualization:** Draw zones as shaded rectangles on the chart. Color-code by freshness and quality
- **Alert system:** Alert when price approaches a fresh demand/supply zone within 1%

---

### 4.3 Volume Spread Analysis

#### Concept

Volume Spread Analysis (VSA) examines the relationship between price spread (high - low), closing position within the bar, and volume to identify the activity of institutional ("smart money") participants. The core idea is that institutions leave footprints in the volume data that can reveal their accumulation or distribution before price moves.

#### Key VSA Signals

**Buying Signals (Accumulation):**

1. **Selling Climax:**
   - High volume (> 2x average)
   - Wide spread down bar
   - Closes near the high of the bar (long lower wick)
   - Interpretation: Heavy selling absorbed by strong buyers
   - Action: Prepare for potential reversal; do not enter yet

2. **No Supply:**
   - Low volume (< 50% of average)
   - Narrow spread bar
   - Closes near the high
   - Occurs after a pullback in an uptrend
   - Interpretation: Sellers have exhausted; demand exists at current levels
   - Action: Enter long with a stop below the bar's low

3. **Test:**
   - Low to moderate volume
   - Bar dips below a previous support level but closes back above
   - Interpretation: Market "tested" for sellers and found none (or few)
   - Action: Enter long on the close above support; stop below the test bar low

**Selling Signals (Distribution):**

4. **Buying Climax:**
   - High volume, wide spread up bar, closes near the low (long upper wick)
   - Interpretation: Heavy buying absorbed by strong sellers
   - Action: Prepare for potential top; do not enter

5. **No Demand:**
   - Low volume, narrow spread up bar
   - Occurs after a rally in a downtrend
   - Interpretation: No buying interest; expect continued decline
   - Action: Enter short or exit longs

6. **Upthrust:**
   - Bar pushes above resistance on high volume but closes back below
   - Interpretation: Failed breakout; supply overwhelms demand
   - Action: Enter short with stop above the upthrust high

#### Entry Rules

- VSA signals should confirm other strategies rather than being used in isolation
- **Primary use case:** Use VSA to validate entry signals from other strategies
  - A pullback to support + a "no supply" bar = high-confidence long entry
  - A breakout + high volume with close near the high = confirmed breakout
  - A resistance touch + an "upthrust" = high-confidence short

#### Stop-Loss and Exits

- Stop below the VSA signal bar (for longs) or above (for shorts)
- Targets defined by the primary strategy
- Exit if a contradicting VSA signal appears (e.g., long position sees a "no demand" bar)

#### Implementation Notes

- **Volume classification:** Categorize each bar's volume relative to the 20-day average:
  - Ultra-high: > 2x average
  - High: 1.3-2x average
  - Average: 0.7-1.3x average
  - Low: 0.3-0.7x average
  - Ultra-low: < 0.3x average
- **Spread classification:** Categorize the bar's range (high - low) relative to the 14-day ATR:
  - Wide: > 1.3x ATR
  - Average: 0.7-1.3x ATR
  - Narrow: < 0.7x ATR
- **Close position:** Calculate where the close falls within the range:
  - `Close Position = (Close - Low) / (High - Low)`
  - 0.0-0.3 = closes near low; 0.3-0.7 = closes middle; 0.7-1.0 = closes near high
- **Pattern matching:** Combine volume, spread, and close position to classify bars into VSA signal types
- **Confirmation score:** Add VSA signals to the confluence scoring system. A trade setup with VSA confirmation gets a higher score

---

### 4.4 Gap Trading Strategies

#### Concept

Gaps occur when a stock opens significantly higher or lower than the previous close, creating a void on the chart. Gaps happen due to after-hours news, earnings, or overnight sentiment changes. Different types of gaps have different implications and trading approaches.

#### Gap Classification

1. **Common Gap:** Occurs within a trading range, no strong catalyst. Usually fills quickly (price returns to the pre-gap close)
2. **Breakaway Gap:** Occurs at the start of a new trend, breaking out of a consolidation pattern. High volume. Often does not fill for weeks/months
3. **Runaway (Continuation) Gap:** Occurs in the middle of a strong trend. Moderate to high volume. Signals the trend is accelerating
4. **Exhaustion Gap:** Occurs near the end of a trend, often on very high volume. Fills quickly as the trend reverses

#### Entry Rules

**Gap Fill Strategy (Mean Reversion):**
- A common gap occurs (no major news catalyst)
- Gap size is 1-3% (very large gaps are more likely breakaway gaps)
- The stock is in a range-bound or mild trend, not a strong breakaway
- **Entry:** Fade the gap (short a gap up, long a gap down) at the open or after 15-30 minutes of trading
- **Confirmation:** The first 30-minute candle moves in the direction of the fill

**Gap and Go Strategy (Trend Following):**
- A breakaway gap occurs on high volume (> 2x average)
- The gap is associated with a fundamental catalyst (earnings beat, upgrade, new product)
- The stock holds above the gap level for the first 30-60 minutes
- **Entry:** Buy above the first 30-minute high (for a gap up)
- **Alternative entry:** Wait for a pullback to the gap level and buy if it holds as support

**Gap Support/Resistance:**
- Unfilled gaps create support/resistance zones
- The top of a gap-up zone becomes support
- The bottom of a gap-down zone becomes resistance
- Use these zones for pullback entries, similar to supply/demand zones

#### Exit Rules

**Gap Fill:**
- **Target:** The previous close (the "fill" level)
- **Extended target:** The opposite side of the prior day's range
- **Time stop:** If the gap does not begin to fill within 2 hours, exit
- **Trail:** Once 50% of the gap has filled, move stop to breakeven

**Gap and Go:**
- **Trail at 1x ATR** below the highest high after entry
- **Profit target:** 2x the gap size
- **Exit if:** Price fills more than 50% of the gap (thesis broken)

#### Stop-Loss Placement

**Gap Fill:**
- Above the opening price of the gap day (for shorting a gap up), plus 0.5%
- Below the opening price (for buying a gap down), minus 0.5%
- Maximum risk: 2% from entry

**Gap and Go:**
- Below the gap level (the previous day's high for a gap up)
- This can be a wide stop; size accordingly

#### Position Sizing

- Risk 1% per gap trade (gaps are inherently volatile)
- Gap fills are short-duration trades (often same-day to next day), so intraday sizing can be more aggressive if desired
- Gap and Go trades have wider stops; reduce position size to maintain consistent dollar risk

#### Best Market Conditions

**Gap Fill:** Works best in range-bound markets on stocks with no major news catalyst
**Gap and Go:** Works best in trending markets when the gap aligns with the trend direction
- Earnings season creates many gap opportunities (but also higher risk)
- Avoid gap trading in extremely volatile markets (VIX > 30)

#### Win Rate and Expectancy

**Gap Fill:**
- Win rate: 60-70% (most common gaps do fill)
- Average win: 1-3%
- Average loss: 1-2%
- R:R: 1:1 to 1:1.5

**Gap and Go:**
- Win rate: 40-50%
- Average win: 5-15%
- Average loss: 2-5%
- R:R: 1:2 to 1:3

#### Implementation Notes

- **Gap detection:** Compare each day's open to the previous day's close. A gap exists when `|Open - PrevClose| / PrevClose > threshold` (e.g., 0.5%)
- **Gap classification:** Classify gaps based on: size (% gap), volume relative to average, news/catalyst presence, and whether it occurs at a chart pattern boundary
- **Gap tracking:** Maintain a list of unfilled gaps as potential support/resistance levels. Remove gaps from the list when they are filled
- **Gap fill statistics:** Track historical gap fill rates by classification for each stock. Some stocks fill gaps 80%+ of the time; others frequently leave unfilled gaps

---

### 4.5 Swing Failure Patterns

#### Concept

A Swing Failure Pattern (SFP) occurs when price makes a new high or low beyond a prior swing point but fails to hold and reverses. This represents a liquidity grab — institutional players push price beyond an obvious level to trigger stop-losses and pending orders, then reverse the market. SFPs are one of the most reliable short-term reversal signals.

#### Identification

**Bearish SFP (at a Swing High):**
1. Price makes a swing high (point A)
2. Price pulls back
3. Price rallies again and exceeds the point A high (makes a new high)
4. **But the candle closes back below the point A high**
5. The wick above point A is the "failure" — the move above was not sustained
6. Volume on the SFP candle is often high (liquidity grab)

**Bullish SFP (at a Swing Low):**
1. Price makes a swing low (point A)
2. Price bounces
3. Price drops again and exceeds the point A low (makes a new low)
4. **But the candle closes back above the point A low**
5. The wick below point A is the failure

#### Entry Rules

**Short Entry (Bearish SFP):**
- An SFP candle closes below a prior swing high after wicking above it
- The SFP candle has a long upper wick (at least 50% of the candle range)
- Volume is elevated (> 1.2x average)
- **Entry:** At the close of the SFP candle, or on the next candle if it opens below the prior swing high
- **Filter:** Prefer SFPs that occur after an extended rally (3+ legs up) or at a known resistance level

**Long Entry (Bullish SFP):**
- SFP candle closes above a prior swing low after wicking below it
- Long lower wick
- Elevated volume
- Entry at the close or on the next candle
- Prefer SFPs at known support or after an extended decline

#### Exit Rules

- **Target 1:** The midpoint between the SFP and the prior swing in the opposite direction
- **Target 2:** The prior swing in the opposite direction (e.g., for a bearish SFP, target the prior swing low)
- **Trail:** After 1.5x risk in profit, trail at 1x ATR
- **Failed trade:** If price closes above the SFP candle high (for a bearish SFP), the pattern has failed — exit immediately

#### Stop-Loss Placement

- **Above the SFP candle high** (for bearish SFP) by 0.5% or 0.5x ATR
- **Below the SFP candle low** (for bullish SFP) by 0.5%
- Stops are typically tight because the SFP level is a definitive invalidation point
- Typical distance: 1-3%

#### Position Sizing

- Risk 1-2% of account
- Because stops are typically tight and the pattern has a clear invalidation level, position sizes in dollar terms can be relatively large
- SFPs at major levels (weekly swing highs/lows) justify up to 2% risk

#### Best Market Conditions

- Range-bound to mildly trending markets
- SFPs are particularly powerful at the boundaries of large ranges
- In strong trends, SFPs at swing highs during an uptrend may fail (the trend simply continues after a brief pullback). Use with caution in strong trends
- SFPs on higher timeframes (daily, weekly) are more significant than on intraday charts

#### Win Rate and Expectancy

- **Win rate:** 55-65%
- **Average win:** 4-10%
- **Average loss:** 1.5-3%
- **Risk/Reward ratio:** 1:2 to 1:3
- **Key advantage:** Very clear, objective entry and stop levels with no ambiguity

#### Example Setup

> **Stock YZA** has a swing high at $55 from 2 weeks ago. Price has rallied back to this level. On Day T, it opens at $54.80, pushes up to $55.80 (exceeding the $55 swing high), but reverses and closes at $54.30 — back below the $55 level. The candle has a long upper wick of $1.50 and a body of $0.50. Volume is 1.5x average.
>
> - **Entry:** $54.30 (short at the close)
> - **Stop:** $56.10 ($55.80 SFP high + 0.3 buffer), risking $1.80/share
> - **Target 1:** $51.50 (midpoint to prior swing low) = 1.55x risk
> - **Target 2:** $49 (prior swing low) = 2.9x risk
> - **Position size:** $50,000 × 1.5% = $750 / $1.80 = 416 shares

#### Implementation Notes

- **SFP detection algorithm:**
  1. Identify swing highs and lows using a lookback window (e.g., a swing high is the highest high of N bars with lower highs on both sides, where N = 5 is typical)
  2. When the current candle's high exceeds a prior swing high but the close is below that swing high, flag a bearish SFP
  3. When the current candle's low exceeds a prior swing low but the close is above that swing low, flag a bullish SFP
  4. Score SFPs by: wick length relative to body, volume, proximity to other S/R levels, and timeframe
- **Alert priority:** SFPs at weekly swing points or at levels with multiple confluences should be highest priority
- **Combine with:** Supply/demand zones (an SFP at a supply zone is extremely powerful), trend direction (SFPs with the higher-timeframe trend are more reliable)

---

## 5. Strategy Selection Framework

Not every strategy works in every market condition. The application should help users select the right strategy based on current conditions.

### Market Regime Detection

| Regime | Characteristics | Best Strategies |
|--------|----------------|-----------------|
| **Strong Uptrend** | ADX > 30, price above rising 50-day and 200-day SMAs | Pullback trading, RS screening, Gap and Go, EMA crossover |
| **Mild Uptrend** | ADX 20-30, price above 200-day SMA | Pullback trading, breakout trading, BB bounce (carefully) |
| **Range-Bound** | ADX < 20, flat moving averages | BB bounce, RSI reversals, S/R bounce, gap fill, SFP |
| **Mild Downtrend** | ADX 20-30, price below 200-day SMA | Short setups of trend-following strategies, defensive sector rotation |
| **Strong Downtrend** | ADX > 30, price below declining MAs | Short pullback trading, death cross entries, stay mostly cash |
| **Transitioning** | Golden/Death Cross forming, ADX rising from low levels | Breakout trading, MA crossover, new trend entries |

### Strategy Compatibility Matrix

| Strategy | Trending Up | Trending Down | Range-Bound | High Volatility | Low Volatility |
|----------|-------------|---------------|-------------|-----------------|----------------|
| MA Crossover (50/200) | Good | Good (short) | Poor | Fair | Fair |
| EMA Crossover (9/21) | Good | Good (short) | Fair | Fair | Good |
| Pullback Trading | Excellent | Good (short) | Poor | Fair | Good |
| Breakout Trading | Good | Fair | Good (at boundaries) | Poor | Excellent |
| Bollinger Band Bounce | Poor | Poor | Excellent | Fair | Good |
| RSI Reversals | Fair | Fair | Good | Fair | Good |
| S/R Bounce | Fair | Fair | Excellent | Poor | Good |
| MACD Divergence | Good (at turns) | Good (at turns) | Good | Fair | Fair |
| RS Screening | Excellent | Good (short) | Poor | Fair | Fair |
| Sector Rotation | Good | Good | Fair | Fair | Fair |
| Supply/Demand Zones | Good | Good | Good | Fair | Good |
| VSA | Good | Good | Good | Good | Fair |
| Gap Fill | Fair | Fair | Good | Fair | Good |
| Gap and Go | Excellent | Good | Poor | Fair | Fair |
| Swing Failure Pattern | Fair | Fair | Excellent | Good | Fair |

---

## 6. Implementation Priorities

Based on backtesting reliability, frequency of signals, and implementation complexity, here is a recommended priority order for building these strategies into the application:

### Phase 1: Core Strategies (Implement First)
1. **EMA Crossover (9/21)** — Simple to implement, generates frequent signals, core trend-following tool
2. **Pullback Trading** — Highest probability strategy with excellent R:R; requires trend detection + Fibonacci + reversal candle detection
3. **RSI Oversold/Overbought** — Straightforward signal generation, pairs well with other strategies
4. **Support/Resistance Bounce** — Requires S/R detection (challenging but high value)

### Phase 2: Enhancement Strategies
5. **Breakout Trading** — Requires range/consolidation detection and volume confirmation
6. **Bollinger Band Bounce** — Simple indicator-based, good mean reversion complement
7. **MACD Divergence** — Requires swing point detection and divergence comparison algorithm
8. **Multi-Timeframe Analysis** — Framework enhancement that improves all existing strategies

### Phase 3: Advanced Strategies
9. **Relative Strength Screening** — Requires ranking engine across the stock universe
10. **Supply and Demand Zones** — Requires impulse candle detection and zone tracking
11. **Gap Trading** — Requires gap detection, classification, and tracking
12. **Swing Failure Patterns** — Requires swing point detection and real-time candle analysis
13. **Sector Rotation** — Portfolio-level strategy requiring sector ETF tracking and ranking
14. **Volume Spread Analysis** — Confirmation tool requiring bar classification system

### Cross-Cutting Requirements
- **Confluence scoring:** Every trade setup should be scored by how many confirming factors are present. Higher confluence = higher confidence = potentially larger position size
- **Alert system:** All strategies should generate alerts when conditions are met, ranked by confidence score
- **Backtesting engine:** Every strategy should be backtestable with configurable parameters to validate performance on historical data before live trading
- **Risk management integration:** All position sizes should be calculated automatically based on the stop-loss placement rules defined in each strategy (see document 05 for details)
