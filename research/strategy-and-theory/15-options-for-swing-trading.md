# Options for Swing Trading

## Reference Document for Implementation

This document covers the use of options as instruments for swing trading, including foundational concepts, strategy selection, risk management specific to options, and practical screening criteria. It builds on the strategies in [04-swing-trading-strategies.md](04-swing-trading-strategies.md), the risk framework in [05-risk-management.md](05-risk-management.md), the technical indicators in [02-technical-indicators.md](02-technical-indicators.md), and the regulatory context in [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md).

---

## Table of Contents

1. [Options Basics for Swing Traders](#1-options-basics-for-swing-traders)
   - [1.1 Call and Put Options](#11-call-and-put-options)
   - [1.2 Strike Price, Expiration, and Premium](#12-strike-price-expiration-and-premium)
   - [1.3 Intrinsic vs Extrinsic Value](#13-intrinsic-vs-extrinsic-value)
   - [1.4 The Greeks](#14-the-greeks)
2. [Why Use Options for Swing Trading](#2-why-use-options-for-swing-trading)
3. [Options Strategies for Swing Trading](#3-options-strategies-for-swing-trading)
   - [3.1 Long Calls and Puts (Directional)](#31-long-calls-and-puts-directional)
   - [3.2 Vertical Spreads (Defined Risk)](#32-vertical-spreads-defined-risk)
   - [3.3 Protective Puts (Hedging)](#33-protective-puts-hedging)
   - [3.4 Swing Trading with LEAPS](#34-swing-trading-with-leaps)
4. [Options-Specific Risk Management](#4-options-specific-risk-management)
5. [Screening for Options Swing Trades](#5-screening-for-options-swing-trades)
6. [Practical Guidelines](#6-practical-guidelines)

---

## 1. Options Basics for Swing Traders

### 1.1 Call and Put Options

An option is a contract that gives the buyer the right, but not the obligation, to buy or sell an underlying asset at a specified price on or before a specified date.

**Call Option:**
- Gives the buyer the right to **buy** 100 shares of the underlying stock at the strike price before expiration.
- The call buyer profits when the underlying price rises above the strike price plus the premium paid.
- The call seller (writer) is obligated to sell 100 shares at the strike price if the option is exercised.

**Put Option:**
- Gives the buyer the right to **sell** 100 shares of the underlying stock at the strike price before expiration.
- The put buyer profits when the underlying price falls below the strike price minus the premium paid.
- The put seller (writer) is obligated to buy 100 shares at the strike price if the option is exercised.

**Quick Reference:**

| Action | Bullish | Bearish |
|--------|---------|---------|
| Buy to open | Buy call | Buy put |
| Sell to open | Sell put | Sell call |

**American vs European style:**
- Most U.S. equity and ETF options are American style and can be exercised at any time before expiration.
- Index options (SPX, NDX, RUT) are typically European style and can only be exercised at expiration.
- For swing trading purposes, early exercise risk is relevant primarily for short in-the-money options near ex-dividend dates.

### 1.2 Strike Price, Expiration, and Premium

**Strike Price (Exercise Price):**
The price at which the option buyer can buy (call) or sell (put) the underlying stock.

| Moneyness | Call | Put |
|-----------|------|-----|
| In-the-Money (ITM) | Stock price > Strike | Stock price < Strike |
| At-the-Money (ATM) | Stock price = Strike | Stock price = Strike |
| Out-of-the-Money (OTM) | Stock price < Strike | Stock price > Strike |

**Expiration Date:**
The last day on which the option can be exercised. For U.S. equity options, standard monthly options expire on the third Friday of the expiration month. Weekly options expire every Friday.

For swing trading, expiration selection is critical. A minimum of 2-4 weeks until expiration is recommended to avoid accelerating theta decay (see Section 1.4).

**Premium:**
The price paid to buy an option contract. Premium is quoted per share, so multiply by 100 to get the total cost.

```
Total Premium Cost = Quoted Premium x 100 shares per contract x Number of Contracts
```

**Example:**
- A call option is quoted at $3.50
- Buying 2 contracts costs: $3.50 x 100 x 2 = $700

### 1.3 Intrinsic vs Extrinsic Value

Every option premium can be decomposed into two components:

```
Premium = Intrinsic Value + Extrinsic Value (Time Value)
```

**Intrinsic Value:**
The amount by which an option is in-the-money. It represents the immediate exercise value.

```
Call Intrinsic Value = max(0, Stock Price - Strike Price)
Put Intrinsic Value  = max(0, Strike Price - Stock Price)
```

Out-of-the-money and at-the-money options have zero intrinsic value.

**Extrinsic Value (Time Value):**
Everything in the premium beyond intrinsic value. It reflects:
- Time remaining until expiration (more time = more extrinsic value)
- Implied volatility of the underlying
- Interest rates (minor effect)
- Dividends (minor effect)

```
Extrinsic Value = Premium - Intrinsic Value
```

**Example Decomposition:**

| | Stock at $105 | Stock at $95 |
|---|---|---|
| Call with $100 strike, premium $8.00 | Intrinsic: $5.00, Extrinsic: $3.00 | Intrinsic: $0.00, Extrinsic: $8.00 |
| Put with $100 strike, premium $6.50 | Intrinsic: $0.00, Extrinsic: $6.50 | Intrinsic: $5.00, Extrinsic: $1.50 |

**Why this matters for swing traders:**
- When you buy options, you are paying for extrinsic value that decays over time.
- Deep ITM options have high intrinsic value and low extrinsic value, making them behave more like stock.
- OTM options are 100% extrinsic value and will expire worthless if the stock does not move enough.

### 1.4 The Greeks

The Greeks measure how an option's price changes in response to different variables. Understanding the Greeks is essential for selecting the right options and managing swing trade risk.

#### Delta

**Definition:** The rate of change of option price with respect to a $1 move in the underlying stock.

```
Delta = dOption Price / dStock Price
```

| Option Type | Delta Range | Interpretation |
|------------|-------------|----------------|
| Long call | 0 to +1.00 | Gains value as stock rises |
| Long put | -1.00 to 0 | Gains value as stock falls |
| ATM call | ~+0.50 | Moves ~$0.50 for every $1 stock move |
| Deep ITM call | ~+0.90 to +1.00 | Moves nearly $1-for-$1 with stock |
| Far OTM call | ~+0.05 to +0.20 | Barely moves with stock |

**How delta affects swing trades:**
- Delta tells you how much directional exposure you have. A delta of 0.70 on a 2-contract position gives you 0.70 x 200 = 140 delta, equivalent to owning 140 shares.
- For directional swing trades, target delta between 0.60 and 0.70 (slightly ITM). This provides strong directional sensitivity while keeping the premium reasonable.
- Delta also approximates the probability that an option will expire ITM. A 0.70 delta call has roughly a 70% chance of finishing ITM.

#### Gamma

**Definition:** The rate of change of delta with respect to a $1 move in the underlying stock.

```
Gamma = dDelta / dStock Price
```

- Gamma is highest for ATM options and near-expiration options.
- High gamma means delta changes rapidly, which amplifies profits on winning trades but also amplifies losses.
- For swing traders, high gamma near expiration creates unpredictable position behavior. This is another reason to avoid holding options too close to expiration.

**Gamma by moneyness (typical 30-day option):**

| Moneyness | Gamma | Implication |
|-----------|-------|-------------|
| Deep ITM | Low (~0.01-0.02) | Delta is stable near 1.0 |
| ATM | High (~0.05-0.08) | Delta swings significantly with price |
| Far OTM | Low (~0.01-0.02) | Delta remains low |

#### Theta

**Definition:** The rate of change of option price with respect to the passage of one day (time decay).

```
Theta = dOption Price / dTime (per day)
```

- Theta is always negative for long option positions (you lose money each day, all else equal).
- Theta accelerates as expiration approaches. The last 30 days see the steepest decay, and the last 7 days are the worst.
- ATM options have the highest theta because they have the most extrinsic value.

**Theta decay curve (approximate, for an ATM option):**

| Days to Expiration | Daily Theta Decay (as % of initial premium) |
|-------------------|----------------------------------------------|
| 90 | ~0.3% per day |
| 60 | ~0.5% per day |
| 45 | ~0.7% per day |
| 30 | ~1.0% per day |
| 14 | ~1.8% per day |
| 7 | ~3.5% per day |
| 3 | ~6.0% per day |
| 1 | ~15.0% per day |

**How theta affects swing trades:**
- A swing trade held for 5-10 days in a 30-day option loses roughly 5-10% of premium to theta alone, even if the stock does not move.
- Rule of thumb: buy options with at least 2x your expected holding period until expiration. If you plan to hold for 2 weeks, buy options with at least 30 days to expiration.
- Theta is your enemy when buying options and your ally when selling them (spreads, covered calls).

#### Vega

**Definition:** The rate of change of option price with respect to a 1% change in implied volatility (IV).

```
Vega = dOption Price / dImplied Volatility (per 1%)
```

- Vega is highest for ATM options and longer-dated options.
- When implied volatility rises, all options gain value (long vega benefits).
- When implied volatility drops, all options lose value (long vega hurts).

**How vega affects swing trades:**
- Buying options before an expected volatility expansion (breakout setup, pre-earnings run) benefits from rising IV.
- Buying options when IV is already elevated (after a big move, right before earnings) exposes you to IV crush. Even if the stock moves in your direction, collapsing IV can reduce or eliminate your profit.
- Check IV rank (IVR) and IV percentile before entering. See [Section 5](#5-screening-for-options-swing-trades) for thresholds.

#### Rho

**Definition:** The rate of change of option price with respect to a 1% change in the risk-free interest rate.

```
Rho = dOption Price / dInterest Rate (per 1%)
```

- Rho is typically the least impactful Greek for swing traders.
- Higher interest rates slightly increase call values and decrease put values.
- Rho matters more for LEAPS (long-dated options) because there is more time for interest rate changes to compound.
- For short-duration swing trades (2-6 weeks), rho is generally negligible.

#### Greeks Summary Table

| Greek | Measures | Favorable For Buyer | Unfavorable For Buyer |
|-------|----------|--------------------|-----------------------|
| Delta | Price sensitivity | Stock moves in your direction | Stock moves against you |
| Gamma | Delta acceleration | Large favorable moves | Position instability near expiration |
| Theta | Time decay | N/A (always negative) | Holding too long, especially near expiration |
| Vega | Volatility sensitivity | IV expansion | IV crush |
| Rho | Interest rate sensitivity | Rising rates (calls) | Falling rates (calls) |

---

## 2. Why Use Options for Swing Trading

Options offer several structural advantages over trading the underlying stock. They also introduce new risks. This section covers when options are the right tool and when stock is simpler and better.

### 2.1 Defined Risk

When you buy an option (long call or long put), the maximum loss is the premium paid. You cannot lose more, regardless of how far the stock moves against you.

**Comparison:**

| Scenario | Stock Position (100 shares at $50) | Long Call ($3.00 premium, $50 strike) |
|----------|-----------------------------------|---------------------------------------|
| Stock drops to $40 | Loss: $1,000 | Loss: $300 (premium) |
| Stock drops to $30 | Loss: $2,000 | Loss: $300 (premium) |
| Stock gaps to $20 overnight | Loss: $3,000 | Loss: $300 (premium) |

This is especially valuable in swing trading where positions are held overnight and are exposed to gap risk. See the gap risk discussion in [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md) and the stop-loss limitations in [05-risk-management.md](05-risk-management.md).

### 2.2 Leverage Without Margin

A single option contract controls 100 shares. A $3.00 call option on a $50 stock costs $300 to control $5,000 worth of stock, a leverage ratio of roughly 17:1.

This leverage does not require a margin account and does not incur margin interest. The entire cost is paid upfront as premium. This avoids the margin call risk discussed in [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md).

### 2.3 Ability to Profit from Direction and Volatility

Stock positions only profit from directional moves. Options can profit from:
- **Direction** (delta): Stock moves in the expected direction
- **Volatility expansion** (vega): Implied volatility rises, increasing option value
- **Acceleration** (gamma): Large moves amplify delta, creating outsized gains

This means a swing trader can profit from a breakout even before the breakout completes, as the anticipation of a move can increase IV.

### 2.4 Lower Capital Requirements

Options allow swing traders to take directional positions with a fraction of the capital required for stock.

| Approach | Capital for Bullish Exposure to 100 shares of $100 stock |
|----------|----------------------------------------------------------|
| Buy 100 shares (cash) | $10,000 |
| Buy 100 shares (50% margin) | $5,000 |
| Buy 1 ATM call (30 days, ~$4.00 premium) | $400 |
| Buy 1 ITM call (delta 0.70, ~$6.50 premium) | $650 |
| Bull call spread ($95/$105, ~$3.50 debit) | $350 |

This matters for accounts below the $25,000 PDT threshold discussed in [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md), and for the smaller capital ranges mentioned in [01-swing-trading-fundamentals.md](01-swing-trading-fundamentals.md).

### 2.5 Hedging Existing Stock Positions

Options can protect stock-based swing trades against overnight and event risk without closing the position. See Section 3.3 for protective put and collar strategies.

### 2.6 When Stock Is Better Than Options

Options are not always the right tool. Prefer stock when:
- The underlying has illiquid options (wide bid-ask spreads, low open interest)
- The expected holding period is very short (1-2 days) and theta will eat into profits
- The expected move is small (under 2-3%), making the premium cost disproportionate
- You are trading low-volatility stocks where option premiums are minimal and the delta advantage is small
- You want to use limit orders for precise entries and exits without dealing with option pricing complexity

---

## 3. Options Strategies for Swing Trading

### 3.1 Long Calls and Puts (Directional)

The simplest options strategy: buy a call when bullish, buy a put when bearish. The entry signal comes from the same technical setups described in [04-swing-trading-strategies.md](04-swing-trading-strategies.md).

#### When to Buy Calls

- Bullish swing setups: pullback to support in an uptrend, breakout above resistance, bullish chart patterns (see [03-chart-patterns.md](03-chart-patterns.md)), bullish candlestick confirmation (see [11-candlestick-interpretation.md](11-candlestick-interpretation.md))
- Market regime is bullish or neutral (see [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md))
- IV is not elevated (IVR below 50 is ideal; see Section 5)

#### When to Buy Puts

- Bearish swing setups: rally into resistance in a downtrend, breakdown below support, bearish chart patterns
- Market regime is bearish or deteriorating
- IV considerations are less restrictive for puts because IV tends to rise as stocks fall, which benefits long put holders

#### Strike Selection

| Strike | Delta | Pros | Cons | Best For |
|--------|-------|------|------|----------|
| Deep ITM | 0.80-0.95 | High delta, low extrinsic value, behaves like stock | Expensive, low leverage | Stock replacement, conservative traders |
| Slightly ITM | 0.60-0.70 | Good delta, reasonable cost, balanced risk | Still costs more than ATM/OTM | **Recommended for most swing trades** |
| ATM | ~0.50 | Highest liquidity, maximum gamma | 50% chance of expiring worthless | When conviction is moderate |
| Slightly OTM | 0.30-0.40 | Cheaper, higher leverage | Needs larger move to profit | High-conviction breakout trades |
| Far OTM | 0.05-0.20 | Very cheap, lottery-ticket upside | Very low probability of profit | Not recommended for swing trading |

**Recommended default:** Slightly ITM, delta 0.60-0.70. This provides a good balance of directional sensitivity, cost, and probability of profit.

#### Expiration Selection

| Expected Holding Period | Minimum Expiration | Recommended Expiration |
|------------------------|--------------------|-----------------------|
| 2-5 days | 14 days | 21-30 days |
| 5-10 days | 21 days | 30-45 days |
| 10-20 days | 30 days | 45-60 days |

**Rule:** Buy at least 2x your expected holding period in days to expiration. This gives your trade time to work while keeping theta decay manageable.

**Avoid weekly options** for swing trades unless the expected holding period is very short (1-3 days) and you accept the accelerated theta decay.

#### Entry Rules

1. Identify the swing setup using technical analysis from [02-technical-indicators.md](02-technical-indicators.md) and [04-swing-trading-strategies.md](04-swing-trading-strategies.md).
2. Confirm the market regime supports the direction (see [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md)).
3. Check IV rank/percentile. Prefer IVR below 50 for long options.
4. Check option liquidity: open interest > 500, bid-ask spread < 10% of mid-price.
5. Select strike (delta 0.60-0.70) and expiration (2x expected hold time).
6. Calculate position size based on premium at risk, not notional value (see Section 4).
7. Enter with a limit order at or near the mid-price. Avoid market orders on options.

#### Exit Rules

| Condition | Action |
|-----------|--------|
| Profit target reached (underlying hits resistance/support target) | Close the option position |
| Underlying hits stop-loss level | Close the option position |
| Time-based stop: 50% of time to expiration used with no profit | Close to preserve remaining time value |
| Premium drops to 50% of entry (alternative stop) | Close the position |
| IV crush event (earnings, FOMC) | Evaluate and likely close pre-event |

**Trailing stop approach:** Rather than trailing the option price (which is noisy due to Greeks), trail based on the underlying stock's price action. If the stock breaks below a swing low (for calls) or above a swing high (for puts), close the option.

#### Example: Long Call Swing Trade

```
Setup: AAPL pulls back to 20 EMA support at $185 in a confirmed uptrend
       RSI at 42 (oversold-ish), bullish engulfing candle forms

Action:
  Buy 2 AAPL $180 Call (delta 0.68), 35 days to expiration
  Premium: $9.50 per contract
  Total cost: $9.50 x 100 x 2 = $1,900

Risk management:
  Stop-loss on stock: $181 (below 50 EMA)
  If AAPL drops to $181, close the calls immediately
  Maximum loss: $1,900 (premium paid), likely less if closed early
  Time stop: If no profit after 15 days, close to preserve time value

Target:
  Stock target: $195 (prior swing high)
  Expected call value at $195: ~$16.50 (intrinsic $15 + ~$1.50 time)
  Profit: ($16.50 - $9.50) x 200 = $1,400

Risk/Reward: $1,900 risk / $1,400 reward = 1:0.74
  (Risk = full premium paid. This is the default for position sizing
   and portfolio risk calculations.)

  Advanced alternative (early exit at technical invalidation):
  If AAPL hits $181, the option is worth ~$1,300, so actual loss is ~$600.
  Adjusted R/R: ~$600 / $1,400 = 1:2.3
  NOTE: This is an optimistic estimate that assumes timely execution and
  no gap through the stop level. Do NOT use this as the default risk
  figure for portfolio-level risk budgeting.
```

### 3.2 Vertical Spreads (Defined Risk)

A vertical spread involves buying and selling options of the same type (both calls or both puts), same expiration, but different strike prices. The sold option partially offsets the cost of the bought option, reducing capital outlay and defining both maximum profit and maximum loss.

#### Bull Call Spread (Debit)

**Setup:** Buy a lower-strike call and sell a higher-strike call.

**When to use:**
- Bullish outlook, but with a defined price target
- IV is moderate to high (the sold call helps offset vega risk)
- You want to reduce the cost of a long call

**Formulas:**

```
Max Profit = (Strike Sold - Strike Bought) x 100 - Net Debit
Max Loss   = Net Debit (premium paid)
Breakeven  = Strike Bought + Net Debit
```

**Example:**

```
Stock: MSFT at $400
Buy $395 call at $12.00
Sell $410 call at $5.50
Net debit: $6.50 per share = $650 per spread

Max profit: ($410 - $395) x 100 - $650 = $850
Max loss: $650
Breakeven: $395 + $6.50 = $401.50
Risk/reward: $650 / $850 = 1:1.31
```

#### Bear Put Spread (Debit)

**Setup:** Buy a higher-strike put and sell a lower-strike put.

**When to use:**
- Bearish outlook with a defined downside target
- IV is moderate to high

**Formulas:**

```
Max Profit = (Strike Bought - Strike Sold) x 100 - Net Debit
Max Loss   = Net Debit
Breakeven  = Strike Bought - Net Debit
```

**Example:**

```
Stock: TSLA at $250
Buy $255 put at $11.00
Sell $240 put at $5.00
Net debit: $6.00 per share = $600 per spread

Max profit: ($255 - $240) x 100 - $600 = $900
Max loss: $600
Breakeven: $255 - $6.00 = $249.00
Risk/reward: $600 / $900 = 1:1.50
```

#### Bull Put Spread (Credit)

**Setup:** Sell a higher-strike put and buy a lower-strike put.

**When to use:**
- Neutral to bullish outlook
- IV is elevated (you benefit from selling expensive premium)
- You want to profit from time decay and/or a stock staying above a support level
- Pairs well with support bounce setups from [04-swing-trading-strategies.md](04-swing-trading-strategies.md)

**Formulas:**

```
Max Profit = Net Credit received
Max Loss   = (Strike Sold - Strike Bought) x 100 - Net Credit
Breakeven  = Strike Sold - Net Credit
```

**Example:**

```
Stock: AMZN at $185, holding above 50 EMA support at $178
Sell $175 put at $3.20
Buy $165 put at $1.30
Net credit: $1.90 per share = $190 per spread

Max profit: $190 (if AMZN stays above $175 at expiration)
Max loss: ($175 - $165) x 100 - $190 = $810
Breakeven: $175 - $1.90 = $173.10
Probability of profit: ~70% (stock needs to stay above $173.10)
```

#### Bear Call Spread (Credit)

**Setup:** Sell a lower-strike call and buy a higher-strike call.

**When to use:**
- Neutral to bearish outlook
- IV is elevated
- You want to profit from a stock staying below a resistance level

**Formulas:**

```
Max Profit = Net Credit received
Max Loss   = (Strike Bought - Strike Sold) x 100 - Net Credit
Breakeven  = Strike Sold + Net Credit
```

#### Debit vs Credit Spreads: Decision Framework

| Factor | Debit Spread | Credit Spread |
|--------|-------------|---------------|
| Directional conviction | Higher (need stock to move) | Lower (need stock to stay) |
| IV environment | Low to moderate IV (buying cheap) | High IV (selling expensive) |
| Theta | Works against you | Works for you |
| Typical win rate | 40-55% | 55-70% |
| Risk/reward | Often 1:1.5 to 1:3 | Often 1:0.3 to 1:0.8 |
| Management | Close for profit or loss | Can let expire worthless (ideal) |
| Best swing setups | Breakouts, momentum | Support/resistance holds, range trades |

#### Spread Width Selection

| Account Size | Typical Spread Width | Max Risk Per Trade |
|-------------|---------------------|--------------------|
| $5,000 | $2.50-$5 | $100-$250 |
| $10,000 | $5-$10 | $200-$500 |
| $25,000 | $5-$15 | $500-$1,000 |
| $50,000+ | $10-$25 | $1,000-$2,500 |

The 1-2% risk-per-trade rule from [05-risk-management.md](05-risk-management.md) applies to the max loss of the spread, not the notional value of the underlying.

### 3.3 Protective Puts (Hedging)

#### Basic Protective Put

Buy a put option on a stock you already own to insure against a large downside move. This is particularly useful for swing trades held over weekends, earnings announcements, or other event risk windows described in [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md).

**Setup:**
- Own 100 shares of stock at $50
- Buy 1 put at $47 strike for $1.20 ($120 total)

**Result:**
- Maximum loss on the stock position below $47: $3.00/share ($300) + $1.20/share put cost ($120) = $420 total
- Without the put, a gap to $40 would cost $1,000
- Upside remains unlimited, minus the put cost

**When to use protective puts for swing trades:**
- Holding a stock position over a binary event (earnings, FDA decision, FOMC)
- Weekend gap risk on volatile names
- Portfolio insurance when you have a strong conviction long but want to limit tail risk

**Cost-effective hedging tips:**
- Buy OTM puts (delta -0.20 to -0.30) to reduce cost. You accept a larger initial loss but insure against catastrophic gaps.
- Use shorter-dated puts (7-14 days) if you only need protection for a specific event window.
- Factor the put cost into your trade P&L when calculating risk/reward.

#### Collar Strategy (Protective Put + Covered Call)

A collar finances the protective put by selling a covered call above the current price. This caps both downside and upside.

**Setup:**
- Own 100 shares at $50
- Buy 1 put at $46 strike for $1.00
- Sell 1 call at $55 strike for $1.10
- Net credit: $0.10 (the hedge is essentially free)

**Result:**
- Maximum loss: $50 - $46 = $4.00/share ($400) minus $0.10 credit = $390
- Maximum profit: $55 - $50 = $5.00/share ($500) plus $0.10 credit = $510
- If stock stays between $46 and $55, both options expire worthless and you keep the $10 credit

**When to use collars:**
- You have a profitable swing position and want to lock in gains while staying in the trade
- Over a weekend or holiday when you expect low liquidity
- When IV is high enough that the sold call premium is attractive

### 3.4 Swing Trading with LEAPS

LEAPS (Long-term Equity Anticipation Securities) are options with expiration dates more than one year away. They can serve as stock replacement vehicles for swing trading.

#### Why Use LEAPS for Swing Trading

- **Lower capital:** A deep ITM LEAPS call on a $100 stock might cost $25 ($2,500) vs $10,000 for 100 shares
- **Defined risk:** Maximum loss is the premium paid
- **Minimal theta decay:** LEAPS with 12+ months lose very little time value day-to-day
- **Multiple swing trades:** You can hold the LEAPS position and trade around it, adding to or reducing the position on swing signals

#### LEAPS Strike and Delta Selection

| Purpose | Strike | Delta | Cost (approx.) | Behavior |
|---------|--------|-------|-----------------|----------|
| Stock replacement (conservative) | Deep ITM | 0.80-0.90 | 70-85% of stock price | Moves nearly 1:1 with stock |
| Stock replacement (moderate) | ITM | 0.70-0.80 | 50-70% of stock price | Good balance of cost and tracking |
| Leveraged directional | Slightly ITM / ATM | 0.50-0.65 | 25-45% of stock price | Higher leverage, more risk |

**Recommended for swing trading:** Deep ITM LEAPS with delta 0.80+ for stock replacement. This minimizes extrinsic value (reducing theta cost) while providing leverage.

#### LEAPS Example: Stock Replacement

```
Stock: NVDA at $800
Alternative 1: Buy 100 shares = $80,000
Alternative 2: Buy 1 LEAPS call

  Strike: $650 (deep ITM)
  Expiration: 14 months out
  Delta: 0.85
  Premium: $185.00 = $18,500

Capital savings: $80,000 - $18,500 = $61,500
Maximum risk: $18,500 (vs unlimited for stock, though practically
              limited by stop-loss discipline)

If NVDA rises to $900:
  Stock profit: $100 x 100 = $10,000 (12.5% return on $80,000)
  LEAPS profit: ~$85 x 100 = $8,500 (45.9% return on $18,500)
  Note: LEAPS gains slightly less due to delta < 1.0 and some
        extrinsic value decay

If NVDA drops to $700:
  Stock loss: $100 x 100 = $10,000
  LEAPS loss: ~$80 x 100 = $8,000 (delta effect + some IV change)
  Note: LEAPS loss is slightly less, and cannot exceed $18,500
```

#### LEAPS Management for Swing Traders

- **Roll when 6-9 months remain.** At this point, theta begins to accelerate. Roll the LEAPS forward by 6-12 months to a new deep ITM strike.
- **Sell shorter-dated calls against LEAPS** (poor man's covered call) to generate income and reduce cost basis. This is effectively a diagonal spread.
- **Exit LEAPS if the fundamental thesis changes,** not on short-term swing signals. Use LEAPS as the core position and trade around it with shorter-term options or stock.

---

## 4. Options-Specific Risk Management

The risk management principles in [05-risk-management.md](05-risk-management.md) apply to options, but several options-specific factors require additional discipline.

### 4.1 Theta Decay Management

**Core rule:** Never hold a long option position into the zone of accelerated theta decay unless the trade is already profitable and you are managing a trailing stop.

| Days to Expiration | Theta Status | Action |
|-------------------|--------------|--------|
| 45+ days | Slow, manageable | Safe to hold |
| 30-45 days | Moderate | Normal swing holding range |
| 14-30 days | Accelerating | Close if trade is not working |
| 7-14 days | Rapid | Close unless deep ITM |
| < 7 days | Extreme | Close immediately unless exercising |

**Time stop rule:** If 50% of the time between entry and expiration has elapsed and the trade is not profitable, close the position to recover remaining time value.

### 4.2 Implied Volatility Considerations

#### IV Crush

Implied volatility tends to spike before known events (earnings, FOMC, product announcements) and collapse immediately after. This is called IV crush.

**Impact on long options:**

```
Example: Stock at $100, buy $100 call with 30 days to expiration
  IV at 45%: Option price = $5.50
  IV drops to 30% (after earnings): Option price = $3.80
  Loss from IV crush alone: $1.70 per share, even if the stock
  did not move at all
```

**Rules for avoiding IV crush:**
- Do not buy options within 5 trading days of an earnings announcement unless you are specifically trading the earnings event.
- If holding a swing position into an earnings report, either close before the report or switch to a spread to reduce vega exposure.
- Check IV rank (IVR) before entry. If IVR is above 60-70, IV is elevated relative to its historical range and is more likely to contract.

#### IV Expansion Opportunities

- Buying options when IV is low (IVR below 30) means you can benefit from both directional moves and potential IV expansion.
- Breakout setups (see [04-swing-trading-strategies.md](04-swing-trading-strategies.md)) often coincide with IV expansion as the stock moves out of a consolidation range.
- Pair low-IV entries with strong directional signals for the best risk/reward on long options.

### 4.3 Position Sizing for Options

**Canonical risk rule for long options:** For any long option (call or put), the position's risk contribution is the **full premium paid**. This is the default for all position sizing and portfolio risk calculations. Do not substitute "expected loss at technical invalidation" or any other reduced-risk estimate as the default; the option can go to zero and the full premium is at risk. If you choose to use estimated loss at a technical stop level, treat this as an advanced alternative and size your positions conservatively, acknowledging that gaps, slippage, and IV crush can cause actual losses up to the full premium.

Options position sizing uses the **premium at risk** (full premium paid), not the notional value of the underlying.

**Formula:**

```
Number of Contracts = (Account Equity x Risk Percentage) / (Premium per Contract x 100)
```

**Example:**
- Account: $50,000
- Risk per trade: 2% = $1,000
- Option premium: $4.50 per contract = $450 total cost per contract
- Number of contracts: $1,000 / $450 = 2.2, round down to 2 contracts
- Total capital at risk: $900

**Important:** For debit spreads, the max risk is the net debit, not the cost of the long leg. Size based on max risk.

**Portfolio-level limits (using full premium at risk):**
- Total premium at risk (full premium paid) across all open options positions should not exceed 5-10% of account equity.
- No more than 3-5 concurrent options positions to maintain focus and management bandwidth.
- Limit sector concentration: no more than 2 options positions in the same sector.
- When calculating portfolio heat (total risk across all positions), use the full premium paid for each long option, not a reduced estimate based on stop levels.

These portfolio limits complement the portfolio management guidelines in [05-risk-management.md](05-risk-management.md).

### 4.4 Rolling Options

Rolling is closing an existing option position and simultaneously opening a new one, typically with a later expiration date and/or a different strike price.

**When to roll:**

| Situation | Roll Type | Goal |
|-----------|-----------|------|
| Trade is working but approaching expiration | Roll out (same strike, later expiration) | Extend duration, avoid theta acceleration |
| Trade is working, stock has moved significantly | Roll up/down and out (better strike, later expiration) | Lock in partial profits, reset time |
| Trade is not working, thesis still valid | Roll out (same strike, later expiration) | Give the trade more time |
| Trade is not working, thesis weakened | Do not roll. Close for a loss. | Capital preservation |

**Rolling cost:** You will pay a net debit (the new option costs more than the closing proceeds) or receive a net credit (rare, usually only when rolling far out in time). The debit adds to your total cost basis and must be factored into risk/reward.

**Rule:** Only roll if the new position, evaluated on its own merits, would be a trade you would enter fresh. Do not roll losing trades just to avoid realizing a loss.

### 4.5 Assignment Risk

When you sell options (as part of a spread), you carry assignment risk: the buyer of the option you sold can exercise it, requiring you to buy or sell 100 shares at the strike price.

**Key assignment facts:**
- Assignment is most common for ITM options near expiration and for calls on stocks about to go ex-dividend.
- American-style options can be assigned at any time, though early assignment is rare except near ex-dividend dates.
- If assigned on a short call in a spread, you would need to sell shares at the strike price. If you do not own the shares, this creates a short stock position.
- If assigned on a short put in a spread, you would need to buy shares at the strike price.

**Managing assignment risk:**
- Close spreads before expiration rather than letting them expire, especially if either leg is near the money.
- Be aware of ex-dividend dates when holding short call positions.
- Maintain sufficient account equity to handle an assignment if it occurs.

---

## 5. Screening for Options Swing Trades

Not all optionable stocks are suitable for swing trading with options. Illiquid options have wide spreads that eat into profits and make exits difficult. Apply these filters before considering any options trade.

### 5.1 Minimum Open Interest and Volume

| Metric | Minimum Threshold | Preferred |
|--------|-------------------|-----------|
| Open interest (per strike) | 500 contracts | 1,000+ contracts |
| Daily volume (per strike) | 100 contracts | 300+ contracts |
| Total option chain volume | 5,000 contracts/day | 20,000+ contracts/day |

Low open interest and volume lead to wide bid-ask spreads and difficulty exiting positions at fair prices.

### 5.2 Bid-Ask Spread Thresholds

| Option Price | Maximum Bid-Ask Spread | Spread as % of Mid-Price |
|-------------|------------------------|--------------------------|
| Under $2.00 | $0.10 | 5-10% |
| $2.00-$5.00 | $0.20 | 4-8% |
| $5.00-$10.00 | $0.30 | 3-5% |
| $10.00-$20.00 | $0.50 | 2.5-4% |
| Over $20.00 | $0.80 | 2-3% |

**Rule of thumb:** If the bid-ask spread is more than 10% of the option's mid-price, the option is too illiquid for swing trading. The spread cost is a hidden tax on every entry and exit.

### 5.3 Implied Volatility Rank (IVR) and Percentile

**IV Rank (IVR):**

```
IVR = (Current IV - 52-week Low IV) / (52-week High IV - 52-week Low IV) x 100
```

IVR tells you where current IV sits relative to its annual range.

**IV Percentile (IVP):**
The percentage of days in the past year that IV was below the current level. IVP is generally considered a more robust measure because it is not distorted by single-day spikes.

| IVR / IVP | Interpretation | Strategy Implication |
|-----------|----------------|---------------------|
| 0-25 | IV is very low | Good for buying options (cheap premium) |
| 25-50 | IV is below average | Favorable for long options |
| 50-75 | IV is above average | Consider spreads to reduce vega |
| 75-100 | IV is very high | Favor credit spreads or avoid long options |

**Pre-trade checklist:**
- If IVR is below 50: long calls/puts are favorable
- If IVR is 50-75: use debit spreads to reduce vega exposure
- If IVR is above 75: use credit spreads or wait for IV to decline

### 5.4 Liquid Options: Qualifying Underlyings

The most liquid options tend to be on heavily traded large-cap stocks and ETFs. A short list of consistently liquid option underlyings:

**ETFs:** SPY, QQQ, IWM, EEM, GLD, SLV, XLF, XLE, XLK, TLT, HYG, ARKK

**Mega-cap stocks:** AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA, AMD, NFLX, JPM, BAC, BA, DIS, V, MA

**How to screen programmatically:**
When building automated screening (see [06-apis-and-technology.md](06-apis-and-technology.md)), filter for:
- Average daily stock volume > 2 million shares
- Weekly options available (indicates market maker interest)
- Options listed on multiple exchanges (better competition, tighter spreads)

---

## 6. Practical Guidelines

### 6.1 Minimum Account Size for Options Swing Trading

| Strategy | Minimum Account | Recommended Account | Notes |
|----------|----------------|--------------------|----|
| Long calls/puts | $2,000 | $5,000+ | Allows 2-3 concurrent positions at $300-$600 each |
| Vertical spreads | $2,000 | $5,000+ | Spread widths of $2.50-$5 keep risk per trade manageable |
| Credit spreads | $5,000 | $10,000+ | Broker may require higher margin for naked legs |
| LEAPS stock replacement | $5,000 | $15,000+ | LEAPS contracts are expensive; need enough for diversification |
| Collars/protective puts | $10,000 | $25,000+ | Requires owning 100+ shares of underlying stock |

Note: Options trading does not trigger the PDT rule since options are not equities, but buying and selling the same option contract in the same day does count as a day trade for PDT purposes if done in a margin account. See [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md).

### 6.2 Options vs Stock: Decision Framework

| Factor | Favor Stock | Favor Options |
|--------|-------------|---------------|
| Expected holding period | 1-3 days | 5+ days |
| Expected move magnitude | Small (1-3%) | Large (5%+) |
| Gap/event risk | Low | High (defines max loss) |
| IV environment | N/A | Low to moderate IVR |
| Option liquidity | Poor on the underlying | Good (tight spreads, high OI) |
| Capital available | Ample for position sizing | Limited, need leverage |
| Risk tolerance | Can handle open-ended risk with stops | Prefer defined risk |
| Complexity tolerance | Prefer simplicity | Comfortable with Greeks and pricing |

**Decision rule:** Use options when you want defined risk, need leverage, or face event risk. Use stock when the trade is short-duration, the expected move is small, or option liquidity is poor.

### 6.3 Tax Implications of Options Trades

This extends the tax discussion in [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md).

**Short-term capital gains:** Most swing trade options positions are held for less than one year, so profits are taxed as short-term capital gains (ordinary income rates). This applies to:
- Closing a long option for a profit
- Options that expire worthless (the premium paid is a short-term capital loss)
- Closing a short option (spread leg) for less than the credit received

**LEAPS and long-term gains:** If a LEAPS option is held for more than 12 months before being closed or exercised, the gain qualifies for long-term capital gains treatment.

**Wash sale rule:** The wash sale rule applies to options. If you sell an option at a loss and buy a substantially identical option within 30 days (before or after), the loss is disallowed and added to the cost basis of the new position. Note:
- A call on the same stock at a different strike or expiration may or may not be considered substantially identical. IRS guidance is ambiguous; consult a tax professional.
- Selling stock at a loss and buying a call on the same stock within 30 days can trigger the wash sale rule.

**Section 1256 contracts:** Index options (SPX, NDX, RUT, VIX) receive favorable 60/40 tax treatment under Section 1256: 60% of gains are treated as long-term and 40% as short-term, regardless of holding period. Equity options do not qualify for this treatment.

**Record-keeping requirements:**
- Track each option trade: underlying, strike, expiration, entry date, exit date, premium paid/received, number of contracts
- Track whether the option was exercised, assigned, or expired
- Maintain records for wash sale tracking across equity and options positions on the same underlying

### 6.4 Common Mistakes with Options

| Mistake | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| Buying far OTM options ("cheap" options) | Low absolute cost feels affordable | Focus on delta (0.60-0.70), not premium cost |
| Buying too little time (weekly options) | Cheaper premium, more leverage | Buy at least 2x expected holding period to expiration |
| Ignoring IV before entry | Not checking or understanding IVR | Always check IVR; prefer below 50 for long options |
| Holding through earnings with long options | Hope for a big move | IV crush after earnings often destroys long option value |
| Over-sizing positions | Options are cheap so buying too many | Size based on total premium at risk, not per-contract cost |
| Not using limit orders | Market orders on options get terrible fills | Always use limit orders at or near mid-price |
| Selling naked options without experience | High win rate feels safe | Start with defined-risk spreads only |
| Averaging down on losing options | Cost per contract drops, feels like a deal | Never add to a losing options position; theta compounds losses |
| Letting losing trades run to expiration | Hoping for a reversal | Use time stops: close when 50% of time has elapsed without profit |
| Not accounting for bid-ask spread in P&L | Calculating profit from mid-price quotes | Include full round-trip spread cost in expected P&L |

---

## Quick Reference: Options Swing Trading Checklist

Use this before every options swing trade.

```
PRE-TRADE CHECKLIST
--------------------
[ ] Technical setup identified (pullback, breakout, pattern)
    Reference: 02-technical-indicators.md, 03-chart-patterns.md,
               04-swing-trading-strategies.md

[ ] Market regime supports direction
    Reference: 08-market-structure-and-conditions.md

[ ] IV rank (IVR) checked
    - Below 50: long options OK
    - 50-75: use spreads
    - Above 75: credit spreads or pass

[ ] Option liquidity verified
    - Open interest > 500
    - Bid-ask spread < 10% of mid-price
    - Daily volume > 100 contracts

[ ] Strike selected
    - Directional: delta 0.60-0.70 (slightly ITM)
    - Spread: define spread width based on account size

[ ] Expiration selected
    - At least 2x expected holding period
    - No earnings within the holding window (unless intended)

[ ] Position sized
    - Premium at risk < 1-2% of account equity
    - Total options exposure < 5-10% of account equity

[ ] Exit plan defined
    - Stock-price stop-loss level
    - Profit target (stock price and option price)
    - Time stop (50% of time elapsed = evaluate)

[ ] Order type: limit order at mid-price or better
```

---

## Sources and Further Reading

- Hull, J.C. *Options, Futures, and Other Derivatives* (11th ed.). Standard academic reference for options pricing and Greeks.
- Natenberg, S. *Option Volatility and Pricing* (2nd ed.). Practical guide to implied volatility and trading strategies.
- McMillan, L.G. *Options as a Strategic Investment* (6th ed.). Comprehensive reference for options strategies.
- CBOE Education Center: https://www.cboe.com/education/
- OCC (Options Clearing Corporation): https://www.optionseducation.org/
- tastylive research on IV rank, theta decay, and mechanical options strategies: https://www.tastylive.com/
- IRS Publication 550 (Investment Income and Expenses) for tax treatment of options
- Cross-references within this research project:
  - [01-swing-trading-fundamentals.md](01-swing-trading-fundamentals.md) - Capital requirements, holding periods
  - [02-technical-indicators.md](02-technical-indicators.md) - Entry signals (RSI, MACD, Bollinger Bands)
  - [03-chart-patterns.md](03-chart-patterns.md) - Chart patterns as entry triggers
  - [04-swing-trading-strategies.md](04-swing-trading-strategies.md) - Strategy details for entries and exits
  - [05-risk-management.md](05-risk-management.md) - Position sizing, portfolio risk, 1-2% rule
  - [06-apis-and-technology.md](06-apis-and-technology.md) - Automated screening
  - [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md) - Market regimes, gap risk, event risk
  - [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md) - PDT rules, tax treatment, account types
  - [11-candlestick-interpretation.md](11-candlestick-interpretation.md) - Candlestick confirmation for entries
