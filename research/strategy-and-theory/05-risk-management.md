# Risk Management and Money Management for Swing Trading

Risk management is the single most important factor separating consistently profitable traders from those who blow up their accounts. A trader with a mediocre strategy but excellent risk management will outperform a trader with a great strategy but poor risk management every time. This document covers the complete framework for managing risk in a swing trading context.

---

## Table of Contents

1. [Position Sizing](#1-position-sizing)
2. [Stop-Loss Strategies](#2-stop-loss-strategies)
3. [Take-Profit Strategies](#3-take-profit-strategies)
4. [Portfolio Management](#4-portfolio-management)
5. [Risk Metrics](#5-risk-metrics)
6. [Psychology and Discipline](#6-psychology-and-discipline)

---

## 1. Position Sizing

Position sizing determines how many shares or contracts to buy for each trade. It is the primary lever for controlling risk and is more important than entry timing.

### 1.1 Fixed Percentage Risk Model (The 1-2% Rule)

The most widely recommended position sizing method for swing traders. The core principle: never risk more than 1-2% of total account equity on any single trade.

**Formula:**

```
Position Size (shares) = (Account Equity x Risk Percentage) / (Entry Price - Stop Loss Price)
```

**Example:**
- Account equity: $100,000
- Risk per trade: 1% = $1,000
- Entry price: $50.00
- Stop loss: $47.00
- Risk per share: $3.00
- Position size: $1,000 / $3.00 = 333 shares
- Total position value: 333 x $50 = $16,650 (16.65% of account)

**Guidelines by experience level:**
| Experience | Risk Per Trade | Rationale |
|---|---|---|
| Beginner (< 1 year) | 0.5 - 1.0% | Capital preservation while learning |
| Intermediate (1-3 years) | 1.0 - 1.5% | Proven edge, growing confidence |
| Advanced (3+ years) | 1.5 - 2.0% | Documented edge, emotional control |
| Professional | Up to 2.5% | Institutional risk frameworks |

**Key advantages:**
- Automatically adjusts position size as account grows or shrinks
- Prevents catastrophic losses from any single trade
- At 1% risk, you can lose 20 consecutive trades and still retain ~82% of capital
- Mathematically, it takes approximately 70 consecutive losses at 1% risk to lose half of your account

**Common mistake:** Confusing position size with risk. A $10,000 position in a $100,000 account is 10% of capital, but if the stop loss is 3% below entry, the actual risk is only $300 (0.3% of capital).

### 1.2 Kelly Criterion

Developed by John Kelly at Bell Labs in 1956 for signal noise optimization, later adapted for gambling and trading. It calculates the theoretically optimal fraction of capital to risk for maximum long-term growth.

**Formula:**

```
Kelly % = W - [(1 - W) / R]

Where:
  W = Win rate (probability of winning)
  R = Win/loss ratio (average win / average loss)
```

**Alternative full formula:**

```
Kelly % = (bp - q) / b

Where:
  b = Decimal odds received on the bet (average win / average loss)
  p = Probability of winning
  q = Probability of losing (1 - p)
```

**Example:**
- Win rate: 55% (W = 0.55)
- Average win: $600, Average loss: $300 (R = 2.0)
- Kelly % = 0.55 - [(1 - 0.55) / 2.0] = 0.55 - 0.225 = 0.325 (32.5%)

**Practical application -- Half Kelly and fractional Kelly:**

Full Kelly is extremely aggressive and produces severe drawdowns. Most practitioners use fractional Kelly:

| Fraction | Kelly Example (32.5%) | Drawdown Profile |
|---|---|---|
| Full Kelly | 32.5% | Extreme volatility, 50%+ drawdowns likely |
| 3/4 Kelly | 24.4% | Still very aggressive |
| Half Kelly | 16.25% | ~75% of full Kelly's return, ~50% of the variance |
| Quarter Kelly | 8.1% | Much smoother equity curve |

**Why half Kelly is preferred:**
- Achieves approximately 75% of the theoretical maximum growth rate
- Reduces variance by approximately 50%
- Provides a buffer against estimation errors in win rate and payoff ratio
- Real trading parameters are never perfectly known -- fractional Kelly accounts for this uncertainty

**Limitations:**
- Requires accurate knowledge of win rate and average win/loss ratio, which change over time
- Assumes independent outcomes (trades are often correlated)
- Does not account for market regime changes
- Can suggest dangerously large position sizes with favorable-looking statistics
- Garbage in, garbage out: unreliable with small sample sizes (need 100+ trades minimum)

### 1.3 Fixed Ratio Method

Developed by Ryan Jones, this method ties position size increases to accumulated profits rather than account balance. It introduces the concept of a "delta" -- the amount of profit required per contract/unit before adding another unit.

**Core concept:**

```
Next position size increase when:
  Profit >= Current contracts x Delta
```

**Example with delta = $5,000:**

| Contracts | Profit Needed for Next Unit | Cumulative Profit Needed |
|---|---|---|
| 1 | $5,000 | $5,000 |
| 2 | $10,000 | $15,000 |
| 3 | $15,000 | $30,000 |
| 4 | $20,000 | $50,000 |
| 5 | $25,000 | $75,000 |

**Characteristics:**
- Slower scaling during drawdowns (protective)
- Geometric growth during winning periods
- The delta parameter controls aggressiveness: smaller delta = faster scaling
- Does not require knowing win rate or payoff ratio in advance
- Works well for futures and options trading
- Less common in equity swing trading but still applicable

**Choosing a delta:**
- Conservative: Delta = Maximum historical drawdown per unit
- Moderate: Delta = 50-75% of maximum historical drawdown per unit
- Aggressive: Delta = 25-50% of maximum historical drawdown per unit

### 1.4 Volatility-Based Position Sizing (ATR-Based)

Uses the Average True Range (ATR) to normalize position sizes across instruments of different volatility. This ensures each position contributes roughly equal risk to the portfolio.

**Average True Range (ATR) calculation:**

True Range is the greatest of:
1. Current High - Current Low
2. |Current High - Previous Close|
3. |Current Low - Previous Close|

ATR = Moving average of True Range over N periods (typically 14 days for swing trading)

**ATR-based position sizing formula:**

```
Position Size = (Account Equity x Risk %) / (ATR x ATR Multiplier)
```

**Example:**
- Account: $100,000
- Risk: 1% = $1,000
- Stock price: $80.00
- 14-day ATR: $2.50
- ATR multiplier: 2.0
- Dollar risk per share: $2.50 x 2.0 = $5.00
- Position size: $1,000 / $5.00 = 200 shares

**Why ATR-based sizing is powerful for swing trading:**
- Automatically reduces position size for volatile stocks (protection)
- Automatically increases position size for stable stocks (efficiency)
- Normalizes risk across your entire portfolio
- Adapts to changing market conditions (ATR expands during volatile periods, contracts during calm periods)
- The turtle traders famously used this method ("N-based" sizing)

**Choosing ATR period and multiplier:**
| Timeframe | ATR Period | Typical Multiplier |
|---|---|---|
| Short-term swing (2-5 days) | 7-10 day ATR | 1.5x - 2.0x |
| Medium-term swing (5-20 days) | 14 day ATR | 2.0x - 2.5x |
| Longer swing (20-60 days) | 20 day ATR | 2.5x - 3.0x |

### 1.5 Portfolio Heat (Total Risk Exposure)

Portfolio heat measures the total percentage of account equity at risk across all open positions simultaneously.

**Formula:**

```
Portfolio Heat = Sum of (Risk per share x Shares) for all open positions / Account Equity
```

**Recommended limits:**

| Risk Tolerance | Maximum Portfolio Heat |
|---|---|
| Conservative | 3-5% |
| Moderate | 5-8% |
| Aggressive | 8-12% |
| Maximum (not recommended) | 15% |

**Example:**
- Account: $100,000
- Position 1: 300 shares, $2.00 risk = $600
- Position 2: 200 shares, $3.00 risk = $600
- Position 3: 500 shares, $1.50 risk = $750
- Position 4: 150 shares, $4.00 risk = $600
- Total risk: $2,550
- Portfolio heat: 2.55% (conservative)

**Portfolio heat management rules:**
1. Do not open new positions when portfolio heat exceeds your maximum threshold
2. As existing positions move to breakeven (trailing stops), heat decreases, allowing new positions
3. During high-volatility markets (VIX > 25), reduce maximum heat by 25-50%
4. Track both initial heat (at entry) and current heat (adjusted for trailing stops)

---

## 2. Stop-Loss Strategies

Stop losses define the maximum acceptable loss on a trade before exiting. They are the most critical risk management tool.

### 2.1 Fixed Percentage Stops

Setting a stop at a fixed percentage below (for longs) or above (for shorts) the entry price.

**Common levels:**
| Market Cap / Volatility | Typical Stop |
|---|---|
| Large-cap, low volatility | 3-5% |
| Mid-cap, moderate volatility | 5-8% |
| Small-cap, high volatility | 8-12% |

**Advantages:**
- Simple to calculate and implement
- Easy to automate
- Consistent risk per trade when combined with position sizing

**Disadvantages:**
- Does not account for individual stock volatility
- A 5% stop might be too tight for a volatile stock and too loose for a stable one
- Ignores chart structure (support/resistance levels)
- Can lead to being stopped out by normal price fluctuations

### 2.2 ATR-Based Stops

Using the Average True Range to set stops that respect a stock's natural volatility. This is widely considered the most effective stop-loss method for swing trading.

**Common ATR multiples for swing trading:**

| Multiple | Use Case | Characteristics |
|---|---|---|
| 1.0x ATR | Very tight, only for momentum/breakout trades | Frequent stops, higher win/loss ratio needed |
| 1.5x ATR | Standard for shorter swings (3-5 days) | Good balance for active swing trading |
| 2.0x ATR | Most common for typical swing trades | Allows normal retracements |
| 2.5x ATR | For longer-term swings or volatile names | Wider stop, requires smaller position |
| 3.0x ATR | Position trading territory | Rarely hit by noise, but large dollar risk |

**Formula:**

```
Long stop = Entry Price - (ATR x Multiplier)
Short stop = Entry Price + (ATR x Multiplier)
```

**Example:**
- Entry: $50.00
- 14-day ATR: $1.80
- 2x ATR stop: $50.00 - ($1.80 x 2) = $46.40

**Why ATR stops are superior:**
- They adapt to the stock's actual behavior
- Tight enough to protect capital, wide enough to avoid noise
- Work across any market, sector, or timeframe
- Can be backtested and optimized for specific strategies

### 2.3 Support/Resistance-Based Stops

Placing stops just below key support levels (for longs) or above resistance levels (for shorts). This is the most technically sound approach.

**Implementation:**
- Identify the nearest meaningful support level below entry
- Place the stop 1-3% below that support level (or 0.5-1.0x ATR below support)
- The "buffer" below support avoids stop-runs and false breakdowns

**Finding support/resistance:**
- Previous swing lows/highs
- Moving averages (20, 50, 200 SMA/EMA)
- Volume profile levels (high volume nodes)
- Fibonacci retracement levels (38.2%, 50%, 61.8%)
- Trendlines
- Round numbers (psychological support)

**Best practice:** Combine ATR-based stops with support/resistance. Use the support level to determine WHERE the stop goes, and ATR to determine if the stop distance is reasonable. If the support level is too far away (making the risk too large), either reduce position size or skip the trade.

### 2.4 Trailing Stops

Trailing stops move with the price as the trade becomes profitable, locking in gains while allowing the trade to run.

#### Fixed Trailing Stop
- Trails a fixed dollar amount or percentage below the highest price reached
- Example: A 5% trailing stop on a stock that rises from $50 to $60 would be at $57 ($60 x 0.95)
- Simple but does not account for volatility

#### ATR Trailing Stop
- Trails at N x ATR below the highest close (for longs)
- Formula: `Trailing Stop = Highest Close - (ATR x Multiplier)`
- Adapts to changing volatility as the trade progresses
- Typically uses 2.0-3.0x ATR for swing trading
- Recalculated daily as new price data comes in

#### Chandelier Exit (Developed by Charles Le Beau)
- A specific type of ATR trailing stop that trails from the highest high (not highest close)
- Formula: `Chandelier Exit = Highest High (N periods) - (ATR x Multiplier)`
- Default settings: 22-period lookback, 3.0x ATR multiplier
- For swing trading: 10-period lookback, 2.0-2.5x ATR multiplier
- Very effective for trending trades

**Trailing stop best practices:**
1. Never move a trailing stop backward (away from the current price)
2. Only begin trailing after the trade has moved in your favor by at least 1x ATR
3. Consider using different trailing methods for different market phases:
   - Tight trail (1.5x ATR) in overbought or extended moves
   - Wider trail (2.5-3.0x ATR) in strong trends with clean pullbacks

### 2.5 Time-Based Stops

Exiting a trade if it has not moved meaningfully in a specified time period. This is an underutilized but valuable approach.

**Common time-based rules:**
- Exit if the trade has not reached 1R (one unit of risk) profit within 5-10 trading days
- Exit if the stock is flat or slightly negative after 3-5 days
- Exit before known catalysts (earnings, FDA decisions) unless the trade thesis depends on the event
- Friday rule: consider reducing positions before weekends to avoid gap risk

**Why time stops matter:**
- Opportunity cost: capital tied up in a dead trade cannot be deployed elsewhere
- Thesis invalidation: if the expected move has not occurred, the setup may have failed
- Reduces exposure: fewer days in the market = fewer days of risk

### 2.6 Mental Stops vs. Hard Stops

| Aspect | Hard Stop (Order in Market) | Mental Stop (Manual Exit) |
|---|---|---|
| Execution | Automatic, guaranteed (market order) or near-guaranteed (stop-limit) | Requires discipline and monitoring |
| Stop-hunting | Visible to market makers and algorithms | Not visible to the market |
| Gaps | Cannot protect against overnight gaps | Cannot protect against gaps either |
| Slippage | Stop-market can have significant slippage | Can choose order type at exit |
| Discipline | Removes emotion from the equation | Subject to "I'll give it a little more room" |
| Best for | Beginners, large positions, overnight holds | Experienced traders, intraday monitoring |

**Recommendation for swing traders:** Use hard stops. The risk of discipline failure with mental stops far outweighs the risk of stop-hunting. If stop-hunting is a concern, use wider ATR-based stops or place stops at less obvious levels (avoid round numbers and obvious support).

**Stop-limit vs. stop-market orders:**
- Stop-market: Guaranteed execution, potential slippage. Use for normal situations.
- Stop-limit: No slippage but no guaranteed fill. Dangerous -- your stop may not execute in a fast-moving market.
- Recommendation: Use stop-market orders for risk management. The purpose of a stop is to get you OUT, not to get you a good price.

---

## 3. Take-Profit Strategies

Knowing when and how to take profits is as important as knowing when to cut losses.

### 3.1 Risk/Reward Ratio Targets

The risk/reward ratio (R:R or R-multiple) compares the potential profit to the potential loss on a trade.

**Common targets for swing trading:**

| R:R Ratio | Required Win Rate to Break Even | Use Case |
|---|---|---|
| 1:1 | 50% | Not recommended -- no edge after commissions |
| 1:1.5 | 40% | Minimum acceptable for swing trading |
| 1:2 | 33% | Standard swing trading target |
| 1:3 | 25% | Ideal, works well with trend-following |
| 1:4+ | 20% | Rare but possible in strong trends |

**Calculating R-multiples:**

```
R = (Target Price - Entry Price) / (Entry Price - Stop Loss Price)

Example:
  Entry: $50.00
  Stop: $47.00 (risk = $3.00, this is 1R)
  Target at 1:2 = $50.00 + ($3.00 x 2) = $56.00
  Target at 1:3 = $50.00 + ($3.00 x 3) = $59.00
```

**The expectancy connection:**

```
Expectancy = (Win Rate x Average Win) - (Loss Rate x Average Loss)
Expectancy = (0.50 x $600) - (0.50 x $300) = $300 - $150 = $150 per trade
```

A positive expectancy means the system makes money over time. Higher R:R ratios allow you to be profitable even with a win rate below 50%.

**Practical guideline:** Only take trades where the chart structure supports at least a 1:2 risk/reward ratio. If the nearest resistance (for longs) is closer than 2R from entry, the trade does not offer enough reward for the risk.

### 3.2 Fibonacci Extension Targets

Using Fibonacci extensions to project potential price targets from a swing.

**Key extension levels:**
| Level | Description |
|---|---|
| 100% (1.000) | Full measured move (common target) |
| 127.2% (1.272) | First extension beyond measured move |
| 161.8% (1.618) | The "golden ratio" extension -- very popular target |
| 200% (2.000) | Double the measured move |
| 261.8% (2.618) | Extended trend target |

**How to draw extensions:**
1. Identify the impulse move (swing low to swing high for uptrend)
2. Identify the retracement low
3. Project extension levels from the retracement low using the size of the impulse

**Practical use:**
- 127.2% extension: Conservative target, take partial profits
- 161.8% extension: Standard target for swing trades
- 200%+ extension: Only achievable in strong trends

### 3.3 Previous Swing High/Low Targets

Using historical price structure to set targets:
- For longs: target the previous swing high or a higher resistance level
- For shorts: target the previous swing low or a lower support level

**Implementation:**
1. Look left on the chart for the most recent significant swing high above the entry
2. Set the target slightly below that level (to account for resistance)
3. Verify the R:R ratio is at least 1:2 before taking the trade

**Why this works:**
- Previous swing highs/lows are areas where supply and demand historically shifted
- Many traders watch these levels, creating self-fulfilling prophecy
- They represent natural "resting points" where price may stall or reverse

### 3.4 Partial Profit Taking (Scaling Out)

Exiting a position in stages rather than all at once. This is one of the most important practical techniques for swing traders.

**Common scaling-out plans:**

**The Thirds Method:**
1. Exit 1/3 of position at 1R profit (covers risk, ensures breakeven worst case)
2. Move stop to breakeven on remaining position
3. Exit 1/3 at 2R profit
4. Trail stop on final 1/3 for maximum trend capture

**The Halves Method:**
1. Exit 1/2 at predetermined target (e.g., 1.5R or 2R)
2. Trail stop on remaining 1/2

**The 70/30 Method:**
1. Exit 70% at first target (e.g., 2R)
2. Trail remaining 30% with a wide ATR trailing stop

**Advantages of scaling out:**
- Locks in profits and reduces risk of giving back gains
- Psychologically easier -- you have "banked" money
- Allows participation in extended moves with remaining shares
- Turns a potentially losing trade into a breakeven trade earlier

**Disadvantages of scaling out:**
- Reduces average profit on winning trades (compared to full exit at maximum)
- More complex order management
- Can lead to over-optimization of exit levels
- In strong trending environments, holding full size performs better

**Best practice:** Scale out at the first target and trail the rest. This gives you both the certainty of locked-in profits and the optionality of a bigger move.

### 3.5 Trailing Take-Profit

Rather than having a fixed price target, let profits run using a trailing mechanism.

**Methods:**
- **ATR trailing profit stop:** Trail 2-3x ATR below the highest close. Tighten to 1.5x ATR if the move becomes parabolic.
- **Moving average trail:** Exit when price closes below the 10 EMA or 20 EMA (depending on trend strength).
- **Parabolic SAR:** Automatically accelerating trailing stop that tightens as the trend extends.
- **Bar-count trail:** After a new high, give the trade N bars to make another new high; if it fails, exit.

**When to use trailing take-profit vs. fixed targets:**
- Use fixed targets when trading range-bound or mean-reverting setups
- Use trailing exits when trading trend-following or breakout setups
- Consider hybrid: take partial profits at fixed target, trail the rest

---

## 4. Portfolio Management

Effective portfolio management ensures that your collection of trades, taken together, represents acceptable aggregate risk.

### 4.1 Diversification Across Sectors and Assets

**Why diversification matters for swing traders:**
- Reduces the impact of sector-specific news (earnings, regulation, sector rotation)
- Smooths the equity curve
- Prevents correlated drawdowns from wiping out the portfolio

**Sector diversification guidelines:**
- Aim for positions across at least 3-4 different sectors
- Limit single-sector exposure to 25-30% of total portfolio value
- Consider diversifying across asset classes: equities, ETFs, commodities, forex

**GICS Sectors for reference:**
1. Technology
2. Healthcare
3. Financials
4. Consumer Discretionary
5. Consumer Staples
6. Energy
7. Materials
8. Industrials
9. Utilities
10. Real Estate
11. Communication Services

### 4.2 Correlation Management

Correlation measures how much two assets move together. Highly correlated positions amplify risk.

**Correlation scale:**
| Correlation | Interpretation |
|---|---|
| +0.7 to +1.0 | Highly correlated (nearly identical risk) |
| +0.3 to +0.7 | Moderately correlated |
| -0.3 to +0.3 | Low correlation (good diversification) |
| -0.7 to -0.3 | Moderately negatively correlated |
| -1.0 to -0.7 | Highly negatively correlated (hedge) |

**Practical rules:**
- Avoid holding more than 2 positions with correlation > 0.7 to each other
- If you are long AAPL and MSFT (high correlation), treat them as a single combined position for risk purposes
- During market stress, correlations spike -- positions that seemed uncorrelated can move together
- Check correlations monthly using free tools (e.g., Portfolio Visualizer, stock correlation calculators)
- Index-heavy stocks (large-cap) tend to correlate with SPY; be aware of implicit market-direction bets

### 4.3 Maximum Positions at One Time

**Guidelines by account size:**

| Account Size | Recommended Max Positions | Rationale |
|---|---|---|
| < $25,000 | 3-5 | Focus, manageable, meaningful position sizes |
| $25,000 - $100,000 | 5-8 | Good diversification without over-dilution |
| $100,000 - $500,000 | 8-12 | Sector diversification possible |
| > $500,000 | 10-15 | Full diversification, still manageable |

**Why too many positions is harmful:**
- Dilutes edge: each position becomes too small to impact P&L meaningfully
- Cognitive overload: cannot effectively monitor 20+ swing trades
- Over-diversification approaches index returns minus your trading costs
- Better to have 5-8 high-conviction trades than 15 mediocre ones

**Why too few positions is risky:**
- One bad trade (gap, news event) can cause outsized portfolio damage
- Concentration risk is the leading cause of account blowups
- Minimum of 3-4 positions recommended for risk distribution

### 4.4 Maximum Sector Exposure

**Recommended limits:**

| Exposure Type | Maximum |
|---|---|
| Single stock | 15-20% of portfolio value |
| Single sector | 25-30% of portfolio value |
| Long/short bias | 70-80% net long (or net short) |
| Correlated positions | Count as combined for sector limit |

**Market regime adjustments:**
- Bull market: Maximum 75-80% invested, bias long. Always maintain at least 20-25% cash.
- Neutral/choppy market: Reduce to 50-60% invested, balanced long/short. Hold 40-50% cash.
- Bear market: Reduce to 30-50% invested, consider net short or hedged. Hold 50-70% cash.
- Cash is a position -- the 20-25% cash floor is a hard rule regardless of regime, not a suggestion.

### 4.5 Drawdown Management and Recovery

**Understanding drawdowns:**

| Drawdown | Recovery Needed | Psychological Impact |
|---|---|---|
| 5% | 5.3% to recover | Manageable, normal part of trading |
| 10% | 11.1% to recover | Uncomfortable but survivable |
| 15% | 17.6% to recover | Requires strategy review |
| 20% | 25.0% to recover | Stop trading, full strategy audit |
| 30% | 42.9% to recover | Severe, may take months/years |
| 50% | 100% to recover | Devastating, often career-ending |

The asymmetric math of drawdowns is critical: losses require proportionally larger gains to recover.

**Drawdown management rules:**

1. **Circuit breakers:**
   - 5% monthly drawdown: Reduce position sizes by 50%
   - 10% monthly drawdown: Stop trading for the rest of the month. Review all trades.
   - 15% quarterly drawdown: Stop trading for 2 weeks minimum. Full strategy review.
   - 20% drawdown from peak: Stop trading entirely. Paper trade until 2 weeks of profitable simulated trading.

2. **Graduated position sizing:**
   - At new equity highs: Full position sizes
   - 5% below peak: 75% of normal position sizes
   - 10% below peak: 50% of normal position sizes
   - This automatically reduces risk when the system is underperforming

3. **Recovery protocol:**
   - After a significant drawdown, do NOT try to make it back quickly
   - Reduce position sizes and gradually increase as confidence and equity recover
   - Focus on high-probability setups only
   - The goal is to stop the bleeding first, then rebuild systematically

---

## 5. Risk Metrics

Quantitative metrics for evaluating trading performance and risk.

### 5.1 Sharpe Ratio

Measures risk-adjusted return. How much return you earn per unit of total risk (volatility).

**Formula:**

```
Sharpe Ratio = (Rp - Rf) / σp

Where:
  Rp = Portfolio return
  Rf = Risk-free rate (e.g., T-bill yield, ~5% in 2024-2025)
  σp = Standard deviation of portfolio returns
```

**Interpretation:**
| Sharpe Ratio | Quality |
|---|---|
| < 0 | Losing money relative to risk-free rate |
| 0 - 0.5 | Poor |
| 0.5 - 1.0 | Acceptable |
| 1.0 - 2.0 | Good |
| 2.0 - 3.0 | Excellent |
| > 3.0 | Outstanding (verify calculation, may be too good to be true) |

**Limitations:**
- Penalizes upside volatility equally to downside volatility
- Assumes normally distributed returns (markets have fat tails)
- Can be gamed by strategies that collect small premiums with tail risk (e.g., selling options)
- Time-period dependent: annualize consistently for comparison

### 5.2 Sortino Ratio

An improvement over the Sharpe Ratio that only penalizes downside volatility. This is more meaningful for traders because upside volatility is desirable.

**Formula:**

```
Sortino Ratio = (Rp - Rf) / σd

Where:
  σd = Standard deviation of negative returns only (downside deviation)
```

**Interpretation:**
| Sortino Ratio | Quality |
|---|---|
| < 1.0 | Poor |
| 1.0 - 2.0 | Acceptable |
| 2.0 - 3.0 | Good |
| > 3.0 | Excellent |

**Why Sortino is better for swing traders:**
- A swing trade that moves up 15% has high volatility, but that is desirable
- The Sharpe Ratio would penalize this; the Sortino Ratio does not
- Better reflects the actual risk profile of directional trading strategies

### 5.3 Maximum Drawdown (MDD)

The largest peak-to-trough decline in portfolio value.

**Formula:**

```
MDD = (Trough Value - Peak Value) / Peak Value x 100
```

**Benchmarks for swing trading systems:**
| Maximum Drawdown | Assessment |
|---|---|
| < 10% | Excellent, conservative system |
| 10-20% | Good, typical of well-managed swing trading |
| 20-30% | Acceptable if returns are high enough |
| 30-40% | Problematic, needs review |
| > 40% | Unacceptable for most traders |

**Related metrics:**
- **Average drawdown:** Typical drawdown depth, more representative than maximum
- **Drawdown duration:** How long drawdowns last (time to recovery)
- **Calmar Ratio:** Annualized return / Maximum drawdown (higher is better; > 1.0 is good)
- **Ulcer Index:** Measures depth and duration of drawdowns combined

### 5.4 Win Rate and Expectancy

**Win Rate:**

```
Win Rate = Number of Winning Trades / Total Number of Trades x 100
```

Win rate alone is meaningless without knowing the average win and average loss sizes.

**Expectancy (the single most important metric):**

```
Expectancy = (Win Rate x Average Win) - (Loss Rate x Average Loss)

Or equivalently:
Expectancy per dollar risked = (Win Rate x Average R-multiple of wins) - (Loss Rate x 1)
```

**Example:**
- Win rate: 45%
- Average win: $800 (2.67R)
- Average loss: $300 (1R)
- Expectancy = (0.45 x $800) - (0.55 x $300) = $360 - $165 = $195 per trade

**Expectancy per dollar risked:**
- (0.45 x 2.67) - (0.55 x 1.0) = 1.20 - 0.55 = $0.65 per $1 risked

This means for every dollar you risk, you expect to make $0.65 over time.

**Benchmarks:**
| Expectancy per $1 Risked | Quality |
|---|---|
| Negative | Losing system -- do not trade |
| $0.00 - $0.20 | Marginal edge, barely profitable after costs |
| $0.20 - $0.50 | Solid edge |
| $0.50 - $1.00 | Excellent edge |
| > $1.00 | Exceptional (verify with out-of-sample testing) |

### 5.5 Profit Factor

**Formula:**

```
Profit Factor = Gross Profits / Gross Losses
```

**Interpretation:**
| Profit Factor | Quality |
|---|---|
| < 1.0 | Losing system |
| 1.0 - 1.5 | Marginal |
| 1.5 - 2.0 | Good |
| 2.0 - 3.0 | Very good |
| > 3.0 | Excellent (may indicate curve-fitting in backtests) |

**Why profit factor is useful:**
- Simple to calculate and understand
- Combines win rate and average win/loss into a single number
- A profit factor of 2.0 means you make $2 for every $1 you lose
- Less subject to manipulation than some other metrics

### 5.6 Risk of Ruin Calculations

Risk of ruin calculates the probability of losing a specified percentage of your account (typically 50% or 100%) given your trading parameters.

**Simplified formula (for equal-sized bets):**

```
Risk of Ruin = ((1 - Edge) / (1 + Edge)) ^ Capital_Units

Where:
  Edge = (Win Rate x Payoff Ratio) - Loss Rate
  Capital_Units = Account size / Amount risked per trade
```

**Factors that increase risk of ruin:**
- Higher risk per trade (largest factor)
- Lower win rate
- Lower payoff ratio
- Higher correlation between trades
- Fewer capital units (smaller account relative to risk per trade)

**Monte Carlo simulation approach:**
Rather than using simplified formulas, the most accurate method is Monte Carlo simulation:
1. Define your trading parameters (win rate, average win, average loss, number of trades)
2. Simulate thousands of random sequences of wins and losses
3. Calculate how many sequences result in a specified drawdown level
4. This accounts for the randomness of trade sequences

**Key insight:** Even with a profitable system, unfavorable sequences of losses happen more often than intuition suggests. A system with a 50% win rate and 2:1 payoff can still experience 10+ consecutive losses. At 2% risk per trade, 10 consecutive losses = 18% drawdown. At 5% risk per trade, 10 consecutive losses = 40% drawdown.

**Target:** Risk of ruin should be less than 1% for a well-managed trading plan.

---

## 6. Psychology and Discipline

Technical skill and strategy are insufficient without the psychological framework to execute consistently.

### 6.1 Common Psychological Pitfalls

**Loss aversion:**
- Losses feel 2-2.5x more painful than equivalent gains feel good (Kahneman & Tversky)
- Leads to: holding losers too long ("it will come back"), cutting winners too early (locking in comfort)
- Remedy: Pre-define exits (stop and target) before entering, automate exits where possible

**Overconfidence bias:**
- After a winning streak, traders increase risk and trade more aggressively
- Often leads to giving back all recent profits and more
- Remedy: Stick to position sizing rules regardless of recent results. Your edge works over hundreds of trades, not the next one.

**Recency bias:**
- Overweighting recent trades in decision-making
- After losses: becoming overly conservative, missing valid setups
- After wins: becoming aggressive, taking marginal setups
- Remedy: Make decisions based on the system rules, not recent P&L

**Anchoring:**
- Fixating on a specific price (e.g., your entry price or a previous high)
- "I'll sell when it gets back to my entry" -- irrational attachment to breakeven
- Remedy: Evaluate every position as if you just discovered it today: would you buy it here with fresh capital?

**Sunk cost fallacy:**
- Refusing to exit a losing trade because of the time, effort, or losses already invested
- "I've already lost $2,000, I can't sell now"
- Remedy: The market does not know or care about your entry price. The only question is: what is the best use of this capital right now?

**Disposition effect:**
- Tendency to sell winners quickly and hold losers
- Statistically the most damaging psychological bias for traders
- Remedy: Enforce systematic stops and targets. Track whether you are exiting winners too early.

### 6.2 Trading Journal Importance

A trading journal is the most valuable tool for improvement. It converts experience into knowledge.

**What to record for every trade:**

1. **Pre-trade:**
   - Date and time of entry
   - Instrument and direction (long/short)
   - Setup type (breakout, pullback, reversal, etc.)
   - Entry price and order type
   - Stop loss price and rationale
   - Target price(s) and rationale
   - Position size and risk amount
   - R:R ratio
   - Market conditions (trend, volatility, sector strength)
   - Thesis: why you are taking this trade (1-2 sentences)
   - Confidence level (1-10)

2. **During trade:**
   - Stop adjustments and reasons
   - Partial exits and prices
   - Emotional state notes
   - Any deviations from the plan and why

3. **Post-trade:**
   - Exit date, price, and reason
   - P&L in dollars and R-multiples
   - What went right
   - What went wrong
   - What would you do differently
   - Screenshot of the chart with entry/exit marked

**Weekly and monthly reviews:**
- Calculate expectancy, win rate, profit factor, average R-multiple
- Identify best and worst performing setups
- Look for patterns in losses (time of day, market conditions, emotional state)
- Track compliance: how often did you follow your rules vs. deviate
- Adjust strategy based on data, not feelings

**"If you can't measure it, you can't improve it."** The traders who keep detailed journals consistently outperform those who do not.

### 6.3 Revenge Trading Prevention

Revenge trading is attempting to immediately recover losses by taking impulsive, oversized, or low-quality trades. It is one of the fastest paths to account destruction.

**Warning signs:**
- Feeling angry, frustrated, or desperate after a loss
- Wanting to "make it back" quickly
- Increasing position size after a loss
- Taking trades outside your strategy
- Trading during normally off-hours for your strategy
- Feeling physically tense or agitated

**Prevention rules:**
1. **Mandatory cool-down:** After 2 consecutive losses, take a 30-minute break (walk away from screens)
2. **Daily loss limit:** If you lose 3% of your account in a single day, stop trading for the day
3. **Loss count limit:** After 3 consecutive losing trades, stop for the day (regardless of dollar amount)
4. **Size lock:** Never increase position size on the trade immediately after a loss
5. **Quality filter:** After a loss, your next trade must score at least 8/10 on your setup quality checklist
6. **Accountability:** Tell a trading buddy or write in your journal before taking the next trade after a loss

**Reframe the mindset:**
- A losing trade is not a failure; it is a cost of doing business
- Even the best strategies have 40-50% loss rates
- Focus on executing the process, not the outcome of any single trade
- "The next trade is independent of the last trade"

### 6.4 FOMO (Fear of Missing Out) Management

FOMO drives traders to chase trades they missed, enter late at poor prices, or over-trade to avoid missing opportunities.

**Common FOMO scenarios:**
- A stock you were watching breaks out without you
- A stock gaps up 10% on news and you chase the opening
- Other traders on social media post big gains and you want to participate
- You see a sector moving and buy without doing proper analysis

**Anti-FOMO rules:**
1. **The bus rule:** "There is always another bus." Missed opportunities are irrelevant -- new setups appear daily.
2. **Entry quality standards:** Only enter trades that meet ALL of your predefined criteria. No exceptions.
3. **No-chase rule:** If a stock has already moved more than 2% from your ideal entry, do not chase. Wait for a pullback or move on.
4. **Social media distance:** Reduce exposure to trading social media (Twitter/X, Discord, Reddit) during trading hours. Others' trades are irrelevant to your strategy.
5. **Daily setup limit:** Set a maximum number of new positions per day (e.g., 2). This forces selectivity.
6. **Pre-market plan:** Each morning, identify your best 3-5 setups with exact entry, stop, and target levels. Only trade from this list.

**Reframe FOMO:**
- Missing a trade costs you $0. Chasing a bad trade costs real money.
- The best trades come to you when you are patient and prepared
- Quality over quantity is the defining principle of successful swing trading
- Your job is not to trade every opportunity -- it is to trade your best opportunities with proper risk management

---

## Summary: The Complete Risk Management Checklist

Before every trade, verify:

- [ ] Position size calculated based on account equity and stop distance
- [ ] Risk per trade is within 1-2% of account equity
- [ ] Portfolio heat (total open risk) is within acceptable limits
- [ ] Stop loss is placed at a technically sound level
- [ ] Risk/reward ratio is at least 1:2
- [ ] No more than 25-30% sector concentration
- [ ] Correlation with existing positions checked
- [ ] Maximum concurrent positions not exceeded
- [ ] No revenge trading or FOMO driving the decision
- [ ] Trade thesis written in journal before entry

**The hierarchy of importance:**
1. **Survival first** -- never risk more than you can afford to lose on any single trade
2. **Consistent risk** -- every trade should risk approximately the same percentage of equity
3. **Positive expectancy** -- your system must have a mathematical edge
4. **Disciplined execution** -- follow the rules every single time
5. **Continuous improvement** -- review, measure, adapt

The trader who masters risk management does not need to predict the market. They need only a slight edge, consistent execution, and the discipline to let probability work in their favor over hundreds of trades.

---

## Notes for Swedish Market Traders

> **Full reference:** See `27-swedish-market-adaptation.md` for complete details.

### Pattern Day Trader rule does not apply

The PDT rule (Section 2 of `09-regulation-tax-and-trade-operations.md`) is a US FINRA rule. It does not exist in Sweden or the EU. Swedish traders can day-trade freely without the $25,000 minimum equity requirement or the 4-day-trade-per-5-days restriction. This removes one constraint from system design, but all other risk management principles in this document still apply fully.

### Position sizing: currency note

All position sizing examples in this document use USD. For Swedish traders operating in SEK:

- The formulas are identical -- just substitute SEK for USD.
- A $100,000 account example corresponds roughly to a SEK 1,000,000 account (at ~10 SEK/USD; use the current exchange rate).
- The 1-2% risk rule, portfolio heat limits, and drawdown thresholds are percentage-based and apply regardless of currency.

**SEK example (Section 1.1 formula):**

```
Account equity: SEK 500,000
Risk per trade: 1% = SEK 5,000
Entry price: SEK 250.00
Stop loss: SEK 238.00
Risk per share: SEK 12.00
Position size: SEK 5,000 / SEK 12.00 = 416 shares
Total position value: 416 x SEK 250 = SEK 104,000 (20.8% of account)
```

### Wider spreads on Swedish stocks

Swedish Mid Cap and Small Cap stocks have significantly wider bid-ask spreads than US Large Caps (0.10-3.00% vs. 0.01-0.02%). This affects:

- **Stop-loss execution:** Market stop orders can experience more slippage. Use limit orders for entries on thinner Swedish names.
- **Round-trip cost:** Include both spread cost and Avanza courtage (0.049-0.25%) in risk calculations. A Swedish Mid Cap trade may have 0.5-1.5% round-trip friction compared to 0.02-0.10% for US Large Caps.
- **Position sizing adjustment:** For Swedish Mid/Small Cap stocks, consider reducing position size slightly to account for higher execution friction.

### Margin rules differ

Swedish/EU margin rules differ from US Regulation T. Avanza's margin lending terms depend on the specific securities and the customer's total portfolio. ISK accounts do not support traditional margin borrowing. If using margin on a regular depot, check Avanza's current belaning (collateral) rules rather than applying US margin ratios.
