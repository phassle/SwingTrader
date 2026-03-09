# Correlation and Portfolio Construction for Swing Trading

Understanding how assets move relative to one another is essential for building a swing trading portfolio that does not quietly concentrate risk. A trader may believe they are diversified across five positions, only to discover during a sell-off that all five are highly correlated and behave as a single large bet. This document covers correlation theory, asset class relationships, practical portfolio construction rules, risk budgeting, pair trading, and Python implementation -- all through the lens of a swing trader holding positions for days to weeks.

Cross-references to other research files are noted where relevant:
- Position sizing and the 1-2% rule: see `05-risk-management.md`
- Market regimes and volatility sub-regimes: see `08-market-structure-and-conditions.md`
- Backtesting portfolio-level strategies: see `07-backtesting-and-performance.md`
- Technical indicators (ATR, Bollinger Bands, RSI): see `02-technical-indicators.md`
- Strategy design and entry/exit logic: see `04-swing-trading-strategies.md`

---

## Table of Contents

1. [Correlation Fundamentals](#1-correlation-fundamentals)
2. [Asset Correlations](#2-asset-correlations)
3. [Portfolio Construction for Swing Traders](#3-portfolio-construction-for-swing-traders)
4. [Risk Budgeting](#4-risk-budgeting)
5. [Practical Portfolio Rules](#5-practical-portfolio-rules)
6. [Pair Trading for Swing Traders](#6-pair-trading-for-swing-traders)
7. [Implementation](#7-implementation)

---

## 1. Correlation Fundamentals

### 1.1 Pearson Correlation Coefficient

The Pearson correlation coefficient measures the linear relationship between two variables. For two return series X and Y:

```
r(X, Y) = Cov(X, Y) / (StdDev(X) * StdDev(Y))

Where:
  Cov(X, Y) = (1/n) * SUM[(Xi - mean(X)) * (Yi - mean(Y))]
  StdDev(X) = sqrt((1/n) * SUM[(Xi - mean(X))^2])
```

**Interpretation:**

| Value      | Meaning                          | Portfolio Implication                         |
|------------|----------------------------------|-----------------------------------------------|
| +1.0       | Perfect positive correlation     | No diversification benefit; positions are redundant |
| +0.7 to +1.0 | Strong positive correlation    | Limited diversification; treat as overlapping bets |
| +0.3 to +0.7 | Moderate positive correlation  | Some diversification benefit                  |
| -0.3 to +0.3 | Low or no correlation          | Good diversification; positions are independent |
| -0.3 to -0.7 | Moderate negative correlation  | Hedge effect; reduces portfolio volatility    |
| -0.7 to -1.0 | Strong negative correlation    | Strong hedge; useful for explicit hedging     |
| -1.0       | Perfect negative correlation     | Complete hedge; gains on one offset losses on other |

**Important caveats:**
- Pearson captures only **linear** relationships. Two assets can be dependent in nonlinear ways yet show r near zero.
- Correlation is calculated from returns, not prices. Using price levels directly produces spurious correlations because most prices trend upward over time.
- Outliers heavily influence Pearson correlation. A single crash day can shift a 63-day correlation estimate by 0.1 or more.

### 1.2 Spearman Rank Correlation

Spearman rank correlation replaces raw values with their ranks before computing correlation. It captures monotonic (but not necessarily linear) relationships and is more robust to outliers.

```
r_s = 1 - (6 * SUM(di^2)) / (n * (n^2 - 1))

Where:
  di = rank(Xi) - rank(Yi)
```

For swing trading, Spearman correlation is useful when comparing assets with very different volatility profiles (e.g., a low-vol utility stock and a high-vol tech stock). If Pearson and Spearman diverge significantly, the relationship may be driven by a few extreme observations.

### 1.3 Rolling Correlation

Static correlation over a long window masks the fact that relationships between assets change over time. Rolling correlation computes the correlation over a sliding window of n periods.

**Common windows:**

| Window    | Trading Days | Use Case                                         |
|-----------|-------------|--------------------------------------------------|
| 1 month   | 21 days     | Captures short-term regime shifts; noisy          |
| 3 months  | 63 days     | Standard for swing trading; balances signal/noise |
| 6 months  | 126 days    | Smooth but slow to react to regime changes        |
| 1 year    | 252 days    | Strategic allocation; too slow for active trading |

**Practical usage:**
- Track the 21-day rolling correlation between your positions daily. When it spikes above 0.8, you are effectively running one large position.
- Compare the 21-day and 63-day rolling correlations. If the short window is much higher than the long window, a temporary correlation spike is underway -- consider reducing exposure.

### 1.4 Correlation vs Causation

Correlation does not imply causation. Common traps for traders:

1. **Spurious correlation:** Two unrelated assets may show high correlation over a sample period by chance. Example: a tech stock and a biotech stock may both rally during a risk-on month, showing r = 0.85, but the underlying drivers are completely different.
2. **Common factor:** Two stocks may be correlated not because one drives the other but because both respond to a third factor (interest rates, the S&P 500, sector ETF flows).
3. **Lagged effects:** Stock A may lead Stock B by a few days. The contemporaneous correlation may be moderate, but the real relationship is a lead-lag dynamic better captured by cross-correlation analysis.

**Rule of thumb for swing traders:** Use correlation as a risk management tool (controlling concentration), not as a signal generator. If you want to trade relationships, use cointegration and statistical tests (see Section 6).

### 1.5 Correlation Regimes

Correlations are not stable. They shift predictably across market environments:

| Market Regime               | Typical Correlation Behavior                              |
|-----------------------------|-----------------------------------------------------------|
| Calm bull market            | Low-to-moderate intra-stock correlations (0.2-0.5)        |
| Late-cycle bull / euphoria  | Correlations diverge: leaders pull away from laggards      |
| Correction / sell-off       | Correlations spike sharply (0.6-0.9); "everything drops"  |
| Crisis / panic              | Correlations approach 1.0; only cash and safe havens decouple |
| Recovery                    | Correlations decline as sector rotation resumes            |

**Why this matters for swing traders:**
- Diversification benefits are weakest exactly when you need them most (during crises). See `08-market-structure-and-conditions.md` for regime identification tools.
- During high-correlation regimes, reduce total position count and total portfolio heat. A portfolio of 8 positions at r = 0.9 behaves like one position with 8x leverage.
- Monitor the CBOE Implied Correlation Index (ICJ, JCJ) or compute average pairwise correlation of your holdings as an early-warning signal.

### 1.6 Correlation Matrix Visualization

A correlation matrix displays pairwise correlations for all assets in a portfolio. For n assets, the matrix is n x n, symmetric, with 1.0 on the diagonal.

**Example for a 5-position portfolio:**

```
          AAPL    MSFT    XOM     JNJ     GLD
AAPL      1.00    0.78    0.15    0.22   -0.10
MSFT      0.78    1.00    0.18    0.25   -0.08
XOM       0.15    0.18    1.00    0.30    0.20
JNJ       0.22    0.25    0.30    1.00    0.05
GLD      -0.10   -0.08    0.20    0.05    1.00
```

**Reading this matrix:**
- AAPL and MSFT are highly correlated (0.78) -- they are both large-cap tech. Holding both adds limited diversification.
- GLD has low or negative correlation with all equity positions -- it provides genuine portfolio diversification.
- XOM and JNJ have moderate correlation (0.30) -- reasonable to hold simultaneously.

**Heatmap visualization:** Use color coding (red for high positive, blue for negative, white for zero) to quickly identify clusters of correlated positions. Python implementation is covered in Section 7.

---

## 2. Asset Correlations

### 2.1 Stock-to-Stock Correlations Within Sectors

Stocks in the same sector tend to be highly correlated because they share common fundamental drivers:

| Sector              | Typical Intra-Sector Correlation | Key Shared Drivers                        |
|---------------------|----------------------------------|-------------------------------------------|
| Technology          | 0.60 - 0.85                      | Rate sensitivity, growth expectations, AI narrative |
| Financials          | 0.65 - 0.80                      | Interest rates, credit spreads, yield curve |
| Energy              | 0.70 - 0.90                      | Oil/gas prices, OPEC decisions, demand outlook |
| Healthcare          | 0.30 - 0.55                      | Lower; biotech vs pharma vs devices diverge |
| Utilities           | 0.55 - 0.75                      | Bond yields, regulation, dividend expectations |
| Consumer Staples    | 0.50 - 0.70                      | Input costs, consumer spending, defensive flows |
| Consumer Discretionary | 0.55 - 0.75                   | Consumer confidence, retail sales, housing |

**Swing trading implication:** Holding two tech stocks (e.g., AAPL and MSFT) provides far less diversification than holding one tech and one energy stock. When constructing a swing portfolio, limit same-sector exposure to 2-3 positions maximum.

### 2.2 Cross-Sector Correlations

Cross-sector correlations are typically lower than intra-sector, but they increase during broad market moves:

| Pair                              | Normal Period | Sell-off Period |
|-----------------------------------|---------------|-----------------|
| Tech vs Financials                | 0.35 - 0.50   | 0.65 - 0.80     |
| Energy vs Technology              | 0.10 - 0.30   | 0.50 - 0.70     |
| Healthcare vs Consumer Staples    | 0.35 - 0.50   | 0.55 - 0.70     |
| Utilities vs Technology           | 0.05 - 0.25   | 0.40 - 0.60     |

**Sector rotation and correlation:** During sector rotation, one sector may rally while another sells off, temporarily creating negative cross-sector correlations. This is the ideal environment for a diversified swing portfolio because genuine diversification is available. See `08-market-structure-and-conditions.md` for sector rotation patterns.

### 2.3 Stock-to-Index Correlations (Beta)

Beta measures a stock's sensitivity to the broad market index (typically the S&P 500):

```
Beta = Cov(Stock, Market) / Var(Market)
     = Correlation(Stock, Market) * (StdDev(Stock) / StdDev(Market))
```

| Beta Range | Interpretation                           | Swing Trading Note                        |
|------------|------------------------------------------|-------------------------------------------|
| > 1.5      | High beta; amplifies market moves        | Larger gains and losses; tighter stops needed |
| 1.0 - 1.5  | Above-average beta                       | Moves with market but with extra volatility |
| 0.8 - 1.0  | Market-like beta                         | Tracks the index closely                  |
| 0.5 - 0.8  | Low beta; dampened moves                 | More independent; useful for diversification |
| < 0.5      | Very low beta / defensive                | Often uncorrelated; may not participate in rallies |
| Negative   | Inverse relationship to market           | Rare in equities; gold miners sometimes qualify |

**Using beta in portfolio construction:** The beta-weighted delta of your portfolio tells you your effective market exposure. If you hold 5 long positions with an average beta of 1.3, your portfolio behaves like 6.5 units of S&P 500 exposure. See Section 3.6 for calculation.

### 2.4 Equity-Bond Correlation

The equity-bond correlation is one of the most important macro relationships:

| Period                | Correlation | Driver                                           |
|-----------------------|-------------|--------------------------------------------------|
| 1960-1999             | Positive    | Inflation drove both rates and equity valuations  |
| 2000-2021             | Negative    | "Flight to quality"; bonds rallied when stocks fell |
| 2022-2023             | Positive    | Inflation resurgence; rates up = stocks down      |
| 2024-2026             | Variable    | Regime-dependent; watch the 10Y yield narrative   |

**Swing trading implication:**
- When equity-bond correlation is negative, holding bond ETFs (TLT, IEF) provides a portfolio hedge.
- When equity-bond correlation is positive (as in inflationary periods), bonds no longer hedge equity risk. In this regime, consider cash, gold, or managed futures for diversification.
- Monitor the 63-day rolling correlation between SPY and TLT as a macro regime indicator.

### 2.5 Equity-Commodity Correlations

| Commodity           | Correlation with S&P 500 (Normal) | Correlation in Crisis | Notes                               |
|---------------------|------------------------------------|-----------------------|-------------------------------------|
| Gold (GLD)          | -0.10 to +0.15                     | -0.30 to +0.10        | Classic safe haven; best diversifier |
| Crude Oil (USO)     | +0.30 to +0.50                     | +0.40 to +0.70        | Pro-cyclical; correlates with growth |
| Copper (CPER)       | +0.35 to +0.55                     | +0.50 to +0.75        | "Dr. Copper"; economic bellwether    |
| Agricultural (DBA)  | +0.10 to +0.30                     | +0.20 to +0.40        | Supply-driven; moderate diversifier  |
| Natural Gas (UNG)   | -0.05 to +0.20                     | +0.10 to +0.30        | Weather/supply driven; idiosyncratic |

**Practical use:** Gold (GLD) and gold miners (GDX) are the most commonly used commodity-linked diversifiers for swing portfolios. They tend to rally during equity sell-offs, especially when the sell-off is driven by geopolitical risk or currency weakness.

### 2.6 Currency Correlations

Currency movements affect equity returns, especially for international stocks or exporters/importers:

| Pair                      | Typical Correlation | Driver                                         |
|---------------------------|---------------------|-------------------------------------------------|
| USD strength vs S&P 500   | -0.20 to +0.20     | Complex; depends on whether rates or risk drive USD |
| EUR/USD vs European stocks| +0.30 to +0.50     | Weak euro helps exporters; strong euro helps importers |
| USD/JPY vs Nikkei 225     | +0.50 to +0.70     | Weak yen is bullish for Japanese exporters       |
| AUD/USD vs commodities    | +0.60 to +0.80     | AUD is a commodity currency                      |

**Swing trading note:** If you trade U.S. equities exclusively, currency correlation is less directly relevant. However, a sharply rising dollar can pressure multinational earnings and commodity prices, creating headwinds for energy and materials stocks.

### 2.7 Crypto Correlations with Traditional Assets

| Period                | BTC vs S&P 500 | BTC vs Gold | BTC vs Nasdaq |
|-----------------------|-----------------|-------------|---------------|
| Pre-2020              | ~0.00           | ~0.05       | ~0.05         |
| 2020-2021 (stimulus)  | +0.30 to +0.50  | +0.20       | +0.40 to +0.60|
| 2022 (rate hikes)     | +0.50 to +0.70  | -0.10       | +0.60 to +0.80|
| 2023-2026 (maturing)  | +0.30 to +0.50  | +0.10       | +0.40 to +0.60|

**Key observations:**
- Bitcoin has become increasingly correlated with the Nasdaq/tech stocks as institutional adoption has grown. The "digital gold / uncorrelated asset" narrative has weakened.
- During risk-off episodes, crypto tends to sell off with equities, providing no diversification benefit when it matters most.
- For swing traders already holding tech stocks, adding crypto exposure does not provide meaningful diversification. It amplifies the same risk-on/risk-off exposure with added volatility.

---

## 3. Portfolio Construction for Swing Traders

### 3.1 Maximum Number of Concurrent Positions

The optimal number of positions depends on account size, per-trade risk, and the trader's ability to monitor positions:

| Account Size     | Max Concurrent Positions | Position Size Range | Rationale                          |
|------------------|--------------------------|---------------------|------------------------------------|
| $5,000 - $15,000 | 2 - 3                   | $1,500 - $5,000     | Limited capital; commissions matter |
| $15,000 - $50,000| 3 - 5                   | $3,000 - $15,000    | Enough for basic diversification   |
| $50,000 - $150,000| 5 - 8                  | $6,000 - $30,000    | Good diversification possible      |
| $150,000 - $500,000| 6 - 12                | $12,000 - $60,000   | Full portfolio construction        |
| $500,000+        | 8 - 15                  | $30,000 - $100,000  | Institutional-level diversification|

**Guidelines:**
- With fewer than 5 positions, each trade has outsized impact on portfolio P&L. Tight risk management is critical (see `05-risk-management.md`).
- Beyond 12-15 positions, monitoring becomes difficult for a part-time swing trader. Each additional position adds diminishing diversification benefit.
- Quality over quantity: it is better to have 5 high-conviction, uncorrelated positions than 10 mediocre positions that are all in the same sector.

### 3.2 Sector Diversification Rules

| Rule                                        | Guideline                                    |
|---------------------------------------------|----------------------------------------------|
| Maximum positions in any single sector       | 2 - 3                                        |
| Maximum capital in any single sector         | 25 - 35% of portfolio                        |
| Minimum number of sectors represented        | 3 (for portfolios with 5+ positions)         |
| Defensive sector allocation in bear markets  | At least 30 - 50% in utilities, staples, healthcare |

**Example portfolio allocation by sector:**

```
Account: $100,000, 6 positions

Position 1: NVDA (Technology)     - $18,000 (18%)
Position 2: MSFT (Technology)     - $15,000 (15%)  <- 33% total in tech, at the limit
Position 3: XOM  (Energy)         - $17,000 (17%)
Position 4: UNH  (Healthcare)     - $18,000 (18%)
Position 5: JPM  (Financials)     - $16,000 (16%)
Position 6: GLD  (Commodities)    - $16,000 (16%)

Sector breakdown: Tech 33%, Energy 17%, Healthcare 18%, Financials 16%, Commodities 16%
```

### 3.3 Correlation-Based Position Limits

Beyond sector rules, use actual correlation data to limit overlapping risk:

| Average Pairwise Correlation | Maximum Positions | Rationale                                    |
|------------------------------|-------------------|----------------------------------------------|
| > 0.8                        | 3 - 4             | Positions are near-identical; risk concentrates |
| 0.5 - 0.8                    | 5 - 7             | Moderate diversification; acceptable          |
| 0.3 - 0.5                    | 7 - 10            | Good diversification; full position count     |
| < 0.3                        | 10 - 15           | Excellent diversification; maximum positions  |

**Practical rule:** Calculate the average pairwise correlation of all current positions every evening. If it exceeds 0.7, do not add new positions until you either close a correlated position or find a trade that lowers average portfolio correlation.

### 3.4 Net Exposure Management (Long vs Short)

Net exposure = (Long Exposure - Short Exposure) / Total Capital

| Net Exposure | Description                        | When to Use                                |
|-------------|------------------------------------|--------------------------------------------|
| +55 to +75% | Net long (maximum gross exposure)  | Strong bull market; clear uptrend. Always hold 20-25% cash. |
| +40 to +55% | Net long with some hedges          | Normal bull market; moderate conviction     |
| +20 to +50% | Cautiously net long                | Late-cycle; mixed signals; uncertain regime |
| -20 to +20% | Market neutral                     | Sideways market; high uncertainty           |
| -20 to -50% | Net short                          | Bear market confirmed; downtrend in indices |
| -50 to -80% | Aggressively short                 | Strong bear; only experienced traders       |

**For most swing traders:** Stay between +30% and +75% net long in normal conditions, always maintaining at least 20-25% cash regardless of market regime. Maximum gross exposure should never exceed 75-80% of portfolio. True market-neutral or net-short positioning requires significant skill and experience. The long-term upward drift of equities means being net short is a headwind unless the bear trend is unambiguous.

### 3.5 Portfolio Heat (Total Risk Exposure)

Portfolio heat measures the total percentage of capital at risk across all open positions if every stop loss is hit simultaneously.

```
Portfolio Heat = SUM(Risk per Position) / Account Equity

Where:
  Risk per Position = Position Size * (Entry Price - Stop Price) / Entry Price
```

| Portfolio Heat | Assessment       | Action                                      |
|---------------|------------------|---------------------------------------------|
| < 3%          | Conservative     | Room to add positions                        |
| 3 - 6%        | Moderate         | Standard swing trading exposure              |
| 6 - 10%       | Aggressive       | Acceptable only with high-conviction setups  |
| > 10%         | Dangerous        | Reduce positions immediately                 |

**Example:**

```
Account: $100,000

Position 1: 300 shares of AAPL at $185, stop at $179 -> Risk = 300 * $6 = $1,800 (1.8%)
Position 2: 200 shares of XOM at $110, stop at $105  -> Risk = 200 * $5 = $1,000 (1.0%)
Position 3: 150 shares of MSFT at $420, stop at $408 -> Risk = 150 * $12 = $1,800 (1.8%)
Position 4: 400 shares of JPM at $195, stop at $189  -> Risk = 400 * $6 = $2,400 (2.4%)

Portfolio Heat = ($1,800 + $1,000 + $1,800 + $2,400) / $100,000 = 7.0%
```

This 7.0% heat is on the aggressive side. The trader should consider tightening stops on winning positions to reduce heat, or skipping the next setup until one position closes.

### 3.6 Beta-Weighted Portfolio Delta

Beta-weighted delta expresses your total portfolio exposure in terms of equivalent S&P 500 (SPY) units:

```
Beta-Weighted Delta = SUM(Position Value * Beta of each position) / SPY Price

Example:
  AAPL: $55,500 position, beta 1.20 -> $55,500 * 1.20 = $66,600
  XOM:  $22,000 position, beta 0.80 -> $22,000 * 0.80 = $17,600
  MSFT: $63,000 position, beta 1.15 -> $63,000 * 1.15 = $72,450
  JPM:  $78,000 position, beta 1.10 -> $78,000 * 1.10 = $85,800

  Total beta-weighted exposure = $242,450
  SPY price = $510
  Beta-weighted delta = $242,450 / $510 = 475.4 SPY-equivalent shares
```

**Interpretation:** If the S&P 500 drops 1%, this portfolio is expected to lose approximately $2,425 (475.4 shares x $510 x 1%). This metric helps you understand your real market exposure regardless of how many individual positions you hold.

**Hedging with SPY puts:** If your beta-weighted delta is 475 SPY shares and you want to hedge 50% of your market risk, you could buy 2-3 SPY put contracts (each contract covers 100 shares).

---

## 4. Risk Budgeting

### 4.1 Equal Risk Contribution (Risk Parity Lite)

Instead of allocating equal dollar amounts to each position, allocate so that each position contributes equal risk to the portfolio:

```
Weight_i = (1 / Volatility_i) / SUM(1 / Volatility_j for all j)

Where:
  Volatility_i = annualized standard deviation of returns (or ATR-based volatility)
```

**Example:**

| Stock | Annual Volatility | 1/Vol   | Weight  | Allocation ($100k) |
|-------|-------------------|---------|---------|---------------------|
| AAPL  | 28%               | 3.57    | 22.2%   | $22,200             |
| TSLA  | 55%               | 1.82    | 11.3%   | $11,300             |
| JNJ   | 15%               | 6.67    | 41.4%   | $41,400             |
| XOM   | 25%               | 4.00    | 24.9%   | $24,900             |
| **Total** |                | **16.06** | **100%** | **$100,000**       |

Notice how TSLA gets the smallest allocation because it is the most volatile. JNJ gets the largest because it is the least volatile. The goal is that a 1-standard-deviation move in any single stock produces roughly the same dollar P&L impact.

**Swing trading adaptation:** Full risk parity is designed for long-term portfolios. For swing trading, use ATR-based position sizing (see `05-risk-management.md`) which achieves a similar effect: volatile stocks get smaller positions, stable stocks get larger positions.

### 4.2 Volatility-Weighted Allocation

A simpler version of risk parity:

```
Position Size = (Target Risk per Position) / (ATR * ATR Multiplier)

Where:
  Target Risk = 1% of account
  ATR = 14-day Average True Range
  ATR Multiplier = stop distance in ATR units (typically 1.5 - 2.5)
```

This is the standard approach recommended in `05-risk-management.md` and naturally produces a volatility-balanced portfolio.

### 4.3 Maximum Sector Exposure

| Constraint                                | Limit          |
|-------------------------------------------|----------------|
| Maximum single-sector allocation           | 30 - 35%       |
| Maximum in any two correlated sectors      | 50%            |
| Minimum allocation to uncorrelated assets  | 15 - 20%       |

**Correlated sector pairs to watch:**
- Technology + Communication Services (META, GOOG classified as Comm Services but behave like tech)
- Financials + Real Estate (both rate-sensitive)
- Energy + Materials (both commodity-cycle driven)
- Consumer Discretionary + Industrials (both economically sensitive)

When calculating sector exposure, consider the **effective** sector, not just the GICS classification. META is in Communication Services but trades like a tech stock for correlation purposes.

### 4.4 Maximum Correlated Exposure

A more sophisticated constraint than sector limits: no group of positions with pairwise correlation > 0.6 should exceed 40% of the portfolio.

```
For each pair (i, j) where Correlation(i, j) > 0.6:
  Combined weight of i + j <= 40% of portfolio
```

**Practical implementation:** After adding a new position, recompute the correlation matrix and check all high-correlation pairs. If any pair exceeds 40%, reduce the newer position's size.

### 4.5 Drawdown Budgeting

Set a maximum acceptable drawdown for a given period and work backward to determine position sizing:

```
Maximum Drawdown Budget = 15% per quarter (example)

If average correlation = 0.5 and you have 6 positions:
  Effective independent bets = 6 / (1 + (6-1) * 0.5) = 6 / 3.5 = 1.71

  Per-position risk allowance = 15% / (sqrt(1.71) * time_factor)
```

| Drawdown Budget | Risk Per Trade | Max Positions | Scenario                 |
|-----------------|---------------|---------------|--------------------------|
| 5% / quarter    | 0.5 - 0.75%  | 3 - 5         | Conservative; rebuilding |
| 10% / quarter   | 1.0%          | 5 - 8         | Standard swing trading   |
| 15% / quarter   | 1.5%          | 6 - 10        | Aggressive swing trading |
| 20% / quarter   | 2.0%          | 8 - 12        | Very aggressive          |

**Important:** Drawdown budgets should be hard limits. If you hit 75% of your quarterly drawdown budget, scale back to half-size positions for the remainder of the period. If you hit the full budget, stop trading until the next period begins. This discipline prevents drawdowns from compounding during losing streaks.

---

## 5. Practical Portfolio Rules

### 5.1 Sector Concentration Rule

**Rule: Never hold more than 2-3 positions in the same sector.**

Rationale: Sector-specific news (regulation, earnings season, commodity price shocks) affects all stocks in a sector simultaneously. Holding 4 bank stocks and getting surprised by a Fed announcement turns four "independent" positions into one massive loss.

Exceptions:
- Pairs trades within a sector (one long, one short) partially offset this risk.
- A strong sector trend with staggered entries (different entry dates and stop levels) may justify 3 positions if the stops are well-separated.

### 5.2 Daily Correlation Monitoring

**Rule: Monitor the average pairwise correlation of your portfolio daily.**

Steps:
1. Compute the 21-day rolling correlation matrix for all open positions.
2. Extract all unique pairwise correlations (n*(n-1)/2 values).
3. Compute the average.
4. Track this average over time.

| Average Pairwise Correlation | Action                                            |
|------------------------------|---------------------------------------------------|
| < 0.3                        | Portfolio is well-diversified. Proceed normally.   |
| 0.3 - 0.5                    | Acceptable. No action required.                    |
| 0.5 - 0.7                    | Caution. Avoid adding correlated positions.        |
| > 0.7                        | Danger. Reduce position count or add hedges.       |

### 5.3 Correlation Spike Response

**Rule: When average portfolio correlation spikes above 0.7, reduce total positions by 30-50%.**

Correlation spikes usually coincide with market stress (see `08-market-structure-and-conditions.md` for VIX-based regime detection). During these periods:
- Close the weakest setups first (those with the worst risk/reward or furthest from their stop).
- Tighten stops on remaining positions.
- Do not add new long positions until correlation normalizes.
- Consider a portfolio hedge (SPY puts, inverse ETFs) if you want to maintain positions.

### 5.4 Uncorrelated Strategy Diversification

**Rule: Use multiple uncorrelated strategies to smooth the equity curve.**

| Strategy Type        | Correlation to "Buy Pullback" | When It Works Best     |
|----------------------|-------------------------------|------------------------|
| Trend pullback (long)| 1.00 (reference)              | Bull market             |
| Breakout (long)      | 0.60 - 0.70                   | Strong trends           |
| Mean reversion (long)| 0.20 - 0.40                   | Choppy / range-bound    |
| Momentum short       | -0.30 to -0.10                | Bear market / overextended |
| Pairs / stat arb     | -0.10 to +0.20                | All conditions          |

Running 2-3 complementary strategies simultaneously can reduce portfolio-level drawdowns by 20-40% compared to a single strategy, even if each individual strategy has the same expected return.

See `04-swing-trading-strategies.md` for detailed strategy descriptions and `07-backtesting-and-performance.md` for how to measure strategy correlation in backtests.

### 5.5 Long/Short Balance in Uncertain Markets

**Rule: In uncertain or transitional markets, maintain a long/short balance to reduce directional exposure.**

| Market Condition                  | Suggested Long/Short Ratio    |
|----------------------------------|-------------------------------|
| Clear uptrend (above rising 50 SMA)| 80/20 or 100/0              |
| Uptrend with weakening breadth   | 60/40                         |
| Sideways / choppy                | 50/50                         |
| Downtrend with bounces           | 30/70                         |
| Clear downtrend                  | 10/90 or 0/100                |

**How to implement shorts for swing traders:**
- Short overextended stocks showing bearish technical patterns (head and shoulders, failed breakouts). See `03-chart-patterns.md`.
- Use inverse ETFs (SH, SDS, SQQQ) as portfolio hedges rather than individual shorts if you are uncomfortable with unlimited-loss risk.
- Short sells in swing trading typically have shorter holding periods (3-7 days vs 5-15 days for longs) because declines tend to be faster than advances.

---

## 6. Pair Trading for Swing Traders

### 6.1 Cointegration vs Correlation

| Property       | Correlation                          | Cointegration                             |
|----------------|--------------------------------------|-------------------------------------------|
| Measures       | Linear co-movement of returns        | Long-run equilibrium relationship of prices |
| Stationarity   | Does not require price stationarity   | Requires the spread to be stationary       |
| Time horizon   | Short-to-medium term                  | Medium-to-long term                        |
| Trading signal | Limited; measures risk, not opportunity | Directly produces trade signals (spread reversion) |
| Stability      | Can break down at any time            | More stable if based on economic relationship |

**Key insight:** Two stocks can be highly correlated but not cointegrated (they move together but the spread between them drifts). Two stocks can be cointegrated but have moderate correlation (they mean-revert to a stable spread but with imperfect short-term co-movement). For pair trading, you need **cointegration**, not just correlation.

### 6.2 Finding Pairs

**Step 1: Screen for candidates**
- Same sector and similar market cap
- Similar business models (e.g., Coca-Cola and Pepsi, Visa and Mastercard)
- Similar beta (within 0.2 of each other)
- High historical correlation (> 0.7 over 1 year)

**Step 2: Test for cointegration**

Use the Engle-Granger two-step method:
1. Regress Price_A on Price_B: `Price_A = alpha + beta * Price_B + residual`
2. Test the residuals for stationarity using the Augmented Dickey-Fuller (ADF) test.
3. If the ADF p-value < 0.05, the pair is cointegrated.

Alternatively, use the Johansen test for a more robust multi-variate approach.

**Step 3: Calculate the hedge ratio**

```
Hedge Ratio = Beta from the cointegrating regression

Spread = Price_A - Hedge_Ratio * Price_B
```

The hedge ratio determines how many shares of Stock B to trade for each share of Stock A. It is not necessarily 1:1.

### 6.3 Entry and Exit Signals (Z-Score of Spread)

```
Z-Score = (Current Spread - Mean Spread) / StdDev(Spread)

Where:
  Mean and StdDev are calculated over a lookback window (typically 20-60 days)
```

| Z-Score      | Action                                                |
|-------------|-------------------------------------------------------|
| Z > +2.0    | Short the spread (short A, long B)                    |
| Z > +1.5    | Prepare to short; tighten alerts                      |
| Z = 0       | No action; spread is at equilibrium                    |
| Z < -1.5    | Prepare to go long the spread                         |
| Z < -2.0    | Long the spread (long A, short B)                     |

**Exit rules:**
- Take profit when Z-score reverts to 0 (or +/- 0.5 for partial profits).
- Stop loss if Z-score exceeds +/- 3.0 (the relationship may be breaking down).
- Time stop: if the spread has not reverted within 15-20 trading days, exit and reassess.

**Example: KO/PEP pair trade**

```
KO price: $62.00
PEP price: $175.00
Hedge ratio: 0.35 (from cointegrating regression)

Spread = KO - 0.35 * PEP = 62.00 - 61.25 = 0.75
Mean spread (60-day): 1.50
StdDev (60-day): 0.40

Z-Score = (0.75 - 1.50) / 0.40 = -1.875

Action: Z-score is below -1.5, approaching -2.0. Prepare to go long the spread:
  Long 100 shares KO at $62.00 ($6,200)
  Short 35 shares PEP at $175.00 ($6,125)

Target: Z-score reverts to 0 (spread = 1.50, profit on convergence)
Stop: Z-score hits -3.0 (spread = 0.30, cut loss)
```

### 6.4 Risk Management for Pairs

| Risk Factor                | Mitigation                                           |
|---------------------------|------------------------------------------------------|
| Cointegration breakdown    | Re-test cointegration monthly; exit if ADF p-value > 0.10 |
| Earnings divergence        | Close pairs before either stock reports earnings      |
| Sector-wide shock          | Pairs within same sector are partially hedged but not immune to sector-specific events |
| Execution risk (short leg) | Ensure shares are available to borrow; check borrow cost |
| Leverage                   | Keep pair trade notional below 20% of account on each leg |

**Pairs trading capital requirement:** Each pair requires capital for both the long and short legs. A pair using $6,000 per leg requires $12,000 in capital (plus margin for the short leg). For a $100,000 account, this limits you to approximately 3-4 simultaneous pairs.

---

## 7. Implementation

### 7.1 Correlation Calculation with Python

**Computing a correlation matrix:**

```python
import pandas as pd
import numpy as np
import yfinance as yf

# Download price data
tickers = ['AAPL', 'MSFT', 'XOM', 'JNJ', 'GLD']
data = yf.download(tickers, start='2025-01-01', end='2026-03-01')['Adj Close']

# Compute daily returns
returns = data.pct_change().dropna()

# Correlation matrix
corr_matrix = returns.corr()
print(corr_matrix.round(3))
```

**Rolling correlation between two assets:**

```python
# 21-day and 63-day rolling correlation
rolling_21 = returns['AAPL'].rolling(21).corr(returns['MSFT'])
rolling_63 = returns['AAPL'].rolling(63).corr(returns['MSFT'])

# Plot
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 5))
rolling_21.plot(ax=ax, label='21-day', alpha=0.7)
rolling_63.plot(ax=ax, label='63-day', alpha=0.9)
ax.axhline(y=0.7, color='red', linestyle='--', label='Danger threshold')
ax.set_title('AAPL vs MSFT Rolling Correlation')
ax.set_ylabel('Correlation')
ax.legend()
plt.tight_layout()
plt.savefig('rolling_correlation.png', dpi=150)
```

**Correlation heatmap:**

```python
import seaborn as sns

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt='.2f',
    cmap='RdBu_r',
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
    ax=ax
)
ax.set_title('Portfolio Correlation Matrix')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=150)
```

**Average pairwise correlation (portfolio monitoring):**

```python
def average_pairwise_correlation(returns_df, window=21):
    """Compute average pairwise rolling correlation for a portfolio."""
    n = len(returns_df.columns)
    if n < 2:
        return pd.Series(dtype=float)

    pair_corrs = []
    for i in range(n):
        for j in range(i + 1, n):
            col_i = returns_df.columns[i]
            col_j = returns_df.columns[j]
            pair_corr = returns_df[col_i].rolling(window).corr(returns_df[col_j])
            pair_corrs.append(pair_corr)

    avg_corr = pd.concat(pair_corrs, axis=1).mean(axis=1)
    return avg_corr

avg_corr = average_pairwise_correlation(returns, window=21)
print(f"Current average pairwise correlation: {avg_corr.iloc[-1]:.3f}")
```

### 7.2 Real-Time Correlation Monitoring

For a swing trader, "real-time" means end-of-day updates. A practical monitoring workflow:

```python
import warnings
warnings.filterwarnings('ignore')

def daily_portfolio_check(tickers, account_value, positions):
    """
    Run this at market close each day.

    tickers: list of ticker symbols for open positions
    account_value: current account value
    positions: dict of {ticker: {'shares': n, 'entry': price, 'stop': price}}
    """
    # Download last 90 days of data
    data = yf.download(tickers, period='90d')['Adj Close']
    returns = data.pct_change().dropna()

    # 1. Correlation matrix (21-day)
    corr_21 = returns.tail(21).corr()

    # 2. Average pairwise correlation
    upper_tri = corr_21.where(
        np.triu(np.ones(corr_21.shape), k=1).astype(bool)
    )
    avg_corr = upper_tri.stack().mean()

    # 3. Portfolio heat
    total_risk = 0
    for ticker, pos in positions.items():
        risk = pos['shares'] * (pos['entry'] - pos['stop'])
        total_risk += max(risk, 0)
    heat = total_risk / account_value * 100

    # 4. Alerts
    alerts = []
    if avg_corr > 0.7:
        alerts.append(f"WARNING: Avg correlation {avg_corr:.2f} > 0.7. Reduce positions.")
    if heat > 8:
        alerts.append(f"WARNING: Portfolio heat {heat:.1f}% > 8%. Tighten stops.")

    # Check for high-correlation pairs
    for col in upper_tri.columns:
        for idx in upper_tri.index:
            val = upper_tri.loc[idx, col]
            if pd.notna(val) and val > 0.8:
                alerts.append(f"High correlation: {idx} vs {col} = {val:.2f}")

    return {
        'correlation_matrix': corr_21.round(3),
        'avg_pairwise_correlation': round(avg_corr, 3),
        'portfolio_heat_pct': round(heat, 2),
        'alerts': alerts
    }
```

### 7.3 Portfolio Optimization Basics

#### Mean-Variance Optimization (Markowitz)

The classic approach finds portfolio weights that maximize the Sharpe ratio:

```
Maximize: (Portfolio Return - Risk-Free Rate) / Portfolio Volatility

Subject to:
  SUM(weights) = 1
  weights >= 0 (long-only constraint)
  weights <= 0.30 (maximum position size constraint)
```

```python
from scipy.optimize import minimize

def optimize_portfolio(returns_df, risk_free_rate=0.05):
    """
    Mean-variance optimization for maximum Sharpe ratio.
    """
    n = len(returns_df.columns)
    mean_returns = returns_df.mean() * 252  # annualized
    cov_matrix = returns_df.cov() * 252     # annualized

    def neg_sharpe(weights):
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return -(port_return - risk_free_rate) / port_vol

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0.05, 0.35)] * n  # min 5%, max 35% per position
    initial = np.array([1/n] * n)

    result = minimize(
        neg_sharpe,
        initial,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    optimal_weights = result.x
    return dict(zip(returns_df.columns, optimal_weights.round(4)))
```

**Caveats for swing traders:**
- Mean-variance optimization is highly sensitive to input estimates (expected returns and covariance). Small changes in inputs produce wildly different optimal weights.
- For swing trading, use mean-variance as a guide, not a gospel. The output tells you which positions are contributing most to risk-adjusted returns and which are redundant.
- A simpler approach (equal risk contribution or volatility-weighted) is more robust in practice.

#### Risk Parity

Risk parity allocates so each position contributes equally to total portfolio risk:

```python
def risk_parity_weights(cov_matrix):
    """
    Compute risk parity weights using inverse-volatility as starting point,
    then iteratively refine.
    """
    n = cov_matrix.shape[0]
    vols = np.sqrt(np.diag(cov_matrix))
    inv_vol_weights = (1 / vols) / np.sum(1 / vols)

    # For a more precise solution, use iterative optimization
    def risk_contribution_error(weights):
        port_vol = np.sqrt(weights @ cov_matrix @ weights)
        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / port_vol
        target = port_vol / n
        return np.sum((risk_contrib - target) ** 2)

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0.01, 0.50)] * n

    result = minimize(
        risk_contribution_error,
        inv_vol_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    return result.x
```

### 7.4 Cointegration Testing for Pair Trading

```python
from statsmodels.tsa.stattools import adfuller, coint

def find_cointegrated_pairs(data, significance=0.05):
    """
    Test all pairs for cointegration. Returns pairs with p-value < significance.
    """
    n = data.shape[1]
    keys = data.columns
    pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            stock1 = data[keys[i]]
            stock2 = data[keys[j]]
            score, pvalue, _ = coint(stock1, stock2)
            if pvalue < significance:
                pairs.append({
                    'stock1': keys[i],
                    'stock2': keys[j],
                    'p_value': round(pvalue, 4),
                    'correlation': round(
                        stock1.pct_change().corr(stock2.pct_change()), 3
                    )
                })

    return sorted(pairs, key=lambda x: x['p_value'])


def compute_pair_zscore(stock1_prices, stock2_prices, lookback=60):
    """
    Compute the z-score of the spread for a cointegrated pair.
    """
    # Hedge ratio from OLS regression
    from numpy.polynomial.polynomial import polyfit
    hedge_ratio = np.polyfit(stock2_prices, stock1_prices, 1)[0]

    spread = stock1_prices - hedge_ratio * stock2_prices
    zscore = (spread - spread.rolling(lookback).mean()) / spread.rolling(lookback).std()

    return zscore, spread, hedge_ratio
```

### 7.5 Rebalancing Triggers and Frequency

Swing trading portfolios are not rebalanced on a fixed schedule like long-term portfolios. Instead, use event-driven triggers:

| Trigger                                        | Action                                          |
|------------------------------------------------|-------------------------------------------------|
| New trade entry                                | Recompute correlation matrix and portfolio heat  |
| Trade exit (stop or target hit)                | Reassess remaining portfolio balance             |
| Average pairwise correlation > 0.7             | Reduce most correlated positions                 |
| Portfolio heat > 8%                            | Tighten stops or close weakest position          |
| VIX spikes above 25                            | Reduce total position count by 30-50%            |
| Sector weight exceeds 35%                      | Do not add more positions in that sector         |
| Single position exceeds 25% of portfolio value | Trim to 20% or less                              |
| Drawdown exceeds 50% of quarterly budget       | Move to half-size positions                      |
| Drawdown hits quarterly budget                 | Stop trading until next period                   |

**Minimum monitoring cadence:**

| Task                              | Frequency         |
|-----------------------------------|--------------------|
| Check stops and P&L               | Daily (market close)|
| Update correlation matrix         | Daily or every 2-3 days |
| Recompute portfolio heat          | Each time a position is opened or closed |
| Full portfolio review             | Weekly (weekend)   |
| Strategy performance attribution  | Monthly            |
| Cointegration re-test (for pairs) | Monthly            |

---

## Summary Checklist

Before adding any new position, run through this checklist:

1. **Position risk:** Does this trade risk <= 1-2% of account? (see `05-risk-management.md`)
2. **Portfolio heat:** Will total heat remain below 6-8% after adding this position?
3. **Sector exposure:** Will any sector exceed 30-35% allocation?
4. **Correlation check:** Is this new position's correlation with existing holdings below 0.7?
5. **Net exposure:** Is my long/short balance appropriate for the current market regime?
6. **Beta exposure:** Does my beta-weighted delta reflect my intended market exposure?
7. **Drawdown budget:** Am I within my quarterly drawdown budget?

If any check fails, either skip the trade, reduce its size, or close an existing correlated position first.

---

## Sources and Further Reading

- Markowitz, H. (1952). "Portfolio Selection." *Journal of Finance*, 7(1), 77-91.
- Engle, R.F. and Granger, C.W.J. (1987). "Co-integration and Error Correction." *Econometrica*, 55(2), 251-276.
- Qian, E. (2005). "Risk Parity Portfolios." *PanAgora Asset Management*.
- Gatev, E., Goetzmann, W.N., and Rouwenhorst, K.G. (2006). "Pairs Trading: Performance of a Relative-Value Arbitrage Rule." *Review of Financial Studies*, 19(3), 797-827.
- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
- Vidyamurthy, G. (2004). *Pairs Trading: Quantitative Methods and Analysis*. Wiley.
