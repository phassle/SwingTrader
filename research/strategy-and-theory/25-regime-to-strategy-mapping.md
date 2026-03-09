# Regime-To-Strategy Mapping For Swing Trading

Prepared by Codex on 2026-03-08. This file explains how swing-trading strategy selection should change with market regime. It is meant to connect `04-swing-trading-strategies.md`, `08-market-structure-and-conditions.md`, and the future portfolio-construction work.

## Why this matters

Many swing traders fail by applying one favorite setup in every environment. But strategy edge is conditional. A breakout setup that works in a healthy trend can fail repeatedly in a choppy or event-driven tape.

The goal of regime mapping is to answer:

- what environment are we in
- which strategy families are favored
- which strategies should be reduced or disabled
- how sizing should change

## 1. The main regime dimensions

There is no single regime variable. A useful working model combines:

- trend direction
- volatility
- breadth and leadership
- event pressure

The existing market-structure research already covers trend and structure. This file turns that into an operating matrix.

## 2. Four practical regimes

### Regime A: Trending and orderly

Characteristics:

- higher highs and higher lows, or lower highs and lower lows
- clean pullbacks
- moderate volatility
- breakouts hold more often

Best strategy fit:

- trend continuation
- breakout and base breakout
- pullback to moving average
- relative-strength leaders

Reduce:

- aggressive mean reversion against the trend

Sizing:

- normal to above-normal size if liquidity and breadth support it

## 3. Regime B: Trending but volatile

Characteristics:

- trend exists but candles are wider
- gaps are larger
- intraday reversals are sharper
- macro and headline sensitivity is higher

Best strategy fit:

- continuation setups with smaller size
- pullbacks into major levels
- catalyst-driven continuation after confirmation

Reduce:

- tight-stop breakout chasing
- oversized positions

Sizing:

- smaller than normal
- wider stop assumptions and lower gross exposure

## 4. Regime C: Sideways and choppy

Characteristics:

- breakouts fail often
- price rotates inside ranges
- sector leadership is inconsistent
- trend signals whipsaw

Best strategy fit:

- range trading
- selective mean reversion
- support and resistance fades

Reduce:

- breakout systems
- late trend continuation entries

Sizing:

- smaller and more selective

## 5. Regime D: Event-driven or panic regime

Characteristics:

- macro calendar dominates
- gaps and correlations rise
- normal technical levels become less reliable
- volatility jumps

Cboe describes the VIX as a leading measure of near-term expected volatility derived from S&P 500 option prices. That makes it a useful regime input, not because of a magic threshold, but because it reflects stress and uncertainty.

Best strategy fit:

- very selective post-event continuation
- reduced-size reaction trades
- defensive ETF swings or hedged exposure

Reduce heavily:

- routine breakout trading
- full-size overnight holds into unknown event flow

Sizing:

- reduced exposure
- explicit cap on overnight risk

## 6. Regime inputs to monitor

Useful inputs include:

- market trend on daily and weekly timeframe
- sector trend and breadth
- realized and implied volatility
- macro event calendar
- percentage of breakouts holding versus failing
- gap frequency

The Federal Reserve publishes FOMC calendars, and BLS publishes CPI release schedules. Those calendars should be treated as regime inputs because they can temporarily shift the market from ordinary trend conditions into event-dominated conditions.

## 7. Strategy-regime matrix

### Breakouts

- best in orderly trend
- acceptable in volatile trend with smaller size
- weak in chop
- dangerous into event-heavy sessions without confirmation

### Pullback continuation

- strong in orderly trend
- still workable in volatile trend if levels are clean
- weaker in chop unless the range edge is obvious

### Mean reversion

- weak against strong trend
- stronger in chop or after short-term overextension
- very execution-sensitive in high-volatility regimes

### Catalyst continuation

- strongest when event is real and market context supports it
- fragile if the broad tape is risk-off

## 8. Practical switching rules

Good regime mapping uses simple rules rather than vague intuition.

Examples:

- if breakout follow-through rate falls materially for several weeks, reduce breakout allocation
- if gap size and volatility expand, reduce size and require stronger confirmation
- if market and sector trends are aligned, allow more trend-following setups
- if macro event density is high, reduce overnight exposure

## 9. App design implications

Store regime fields explicitly:

- `market_regime`
- `volatility_regime`
- `breadth_state`
- `event_pressure`
- `preferred_strategies`
- `suppressed_strategies`
- `size_multiplier`

This allows the app to answer not only "is this a valid setup?" but also "is this the right environment for this setup?"

## 10. Common mistake

The most common mistake is assuming that a strategy stopped working because the strategy is bad, when the real issue is that the regime changed and the trader did not adapt.

## Bottom line

Swing-trading strategies should not be chosen in isolation. They should be selected and sized according to regime. The right setup in the wrong environment is often still a bad trade.

## Sources

- Cboe, "VIX Volatility Products"
  https://www.cboe.com/tradable-products/vix/

- Federal Reserve, "Meeting calendars and information"
  https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

- U.S. Bureau of Labor Statistics, CPI
  https://www.bls.gov/cpi/

- FINRA, "Concentrate on Concentration Risk"
  https://www.finra.org/investors/insights/concentration-risk

- `08-market-structure-and-conditions.md`
- `10-empirical-evidence-and-edge-quality.md`
