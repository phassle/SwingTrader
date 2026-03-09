# 07 - Backtesting and Performance Evaluation

## Table of Contents

1. [Backtesting Fundamentals](#1-backtesting-fundamentals)
2. [Common Pitfalls](#2-common-pitfalls)
3. [Performance Metrics](#3-performance-metrics)
4. [Statistical Validation](#4-statistical-validation)
5. [Optimization Techniques](#5-optimization-techniques)
6. [Benchmark Comparison](#6-benchmark-comparison)

---

## 1. Backtesting Fundamentals

### 1.1 What Is Backtesting?

Backtesting is the process of applying a trading strategy to historical data to evaluate how it would have performed in the past. It is the primary tool for strategy development and validation before committing real capital.

A backtest simulates:

- **Entry signals** — when and why a position is opened
- **Exit signals** — stop-losses, take-profits, trailing stops, time-based exits
- **Position sizing** — how much capital is allocated per trade
- **Portfolio management** — how multiple concurrent positions interact

The goal is not to prove a strategy "works" but to gather evidence about its statistical properties under realistic conditions.

### 1.2 Event-Driven vs Vectorized Backtesting

**Vectorized backtesting** applies trading logic across entire arrays of price data at once. It is fast and simple but struggles with realistic order modeling and portfolio-level constraints.

**Event-driven backtesting** processes data bar-by-bar (or tick-by-tick), simulating the sequential nature of real trading. This approach naturally handles:

- Order fills at realistic prices
- Portfolio-level position limits
- Dynamic position sizing based on current equity
- Slippage and commission modeling

For swing trading strategies, event-driven backtesting is strongly preferred because trade frequency is low enough that speed is rarely a concern, and realistic execution modeling matters significantly.

### 1.3 In-Sample vs Out-of-Sample Testing

The most important concept in backtesting methodology is the separation of data into segments:

| Segment | Purpose | Typical Allocation |
|---|---|---|
| **In-sample (IS)** | Develop and tune the strategy | 50-70% of data |
| **Out-of-sample (OOS)** | Validate the strategy on unseen data | 20-30% of data |
| **Holdout / Final validation** | One-time confirmation before live trading | 10-20% of data |

**Critical rule:** Out-of-sample data must never be used during development. Once you look at OOS results and adjust parameters, that data becomes in-sample and the test is invalidated.

A practical split for swing trading on US equities with 20 years of daily data:

- IS: 2004-2017 (development)
- OOS: 2018-2022 (validation)
- Holdout: 2023-2024 (final confirmation)

### 1.4 Walk-Forward Analysis (WFA)

Walk-forward analysis is the gold standard for backtesting. It addresses the static nature of a single IS/OOS split by repeatedly optimizing on a rolling window and testing on the subsequent period.

**Procedure:**

1. Define an optimization window (e.g., 2 years) and a test window (e.g., 6 months).
2. Optimize the strategy on the first 2-year window.
3. Apply the optimized parameters to the next 6 months (out-of-sample).
4. Record the OOS performance.
5. Slide the window forward by 6 months and repeat.
6. Concatenate all OOS segments to get the full walk-forward result.

```
|--- IS Window 1 ---|--- OOS 1 ---|
         |--- IS Window 2 ---|--- OOS 2 ---|
                  |--- IS Window 3 ---|--- OOS 3 ---|
```

**Walk-Forward Efficiency (WFE):**

```
WFE = (OOS Annual Return) / (IS Annual Return)
```

A WFE above 0.5 (50%) is generally considered acceptable. Below 0.3 suggests the strategy is overfit to in-sample data.

**Anchored vs Rolling:**

- **Rolling WFA**: The IS window stays the same size and slides forward. Better for strategies that need to adapt to changing regimes.
- **Anchored WFA**: The IS window always starts at the beginning and grows over time. Better for strategies that benefit from more data.

### 1.5 Paper Trading

Paper trading (forward testing or simulated trading) applies the strategy in real-time on live market data without risking capital. It serves as the final validation step before live deployment.

**Benefits:**

- Tests strategy in truly unseen market conditions
- Validates execution logic, data feeds, and infrastructure
- Reveals psychological factors (can you follow the signals?)
- Catches bugs that backtesting cannot

**Guidelines for swing trading paper trading:**

- Run for a minimum of 30-50 trades (often 3-6 months for a typical swing strategy)
- Track every metric you would in live trading
- Compare results to backtest expectations — significant divergence indicates a problem
- Use realistic fill assumptions (do not assume you get the exact price)

### 1.6 Monte Carlo Simulation

Monte Carlo simulation quantifies the range of possible outcomes by resampling the strategy's trade results. It answers the question: "Given this set of trade outcomes, what is the distribution of possible equity curves?"

**Method:**

1. Collect all trade results from the backtest (e.g., 200 trades with their individual returns).
2. Randomly resample the trade sequence with replacement (bootstrapping).
3. Generate a new equity curve from the reshuffled trades.
4. Repeat 1,000-10,000 times.
5. Analyze the distribution of terminal wealth, max drawdown, and other metrics.

**Key outputs:**

- **Median terminal wealth** — the expected outcome
- **5th percentile terminal wealth** — the "bad luck" scenario
- **95th percentile max drawdown** — the worst drawdown you should prepare for
- **Probability of ruin** — chance of hitting a predefined loss threshold

Monte Carlo simulation is particularly valuable for swing trading because trade counts are typically moderate (50-300 trades per year), making the sequence of trades highly influential on realized performance.

---

## 2. Common Pitfalls

### 2.1 Overfitting (Curve Fitting)

Overfitting occurs when a strategy is tuned so precisely to historical data that it captures noise rather than genuine patterns. An overfit strategy performs brilliantly in-sample but fails out-of-sample.

**Warning signs:**

- Strategy has many parameters relative to the number of trades
- Small parameter changes cause large performance changes
- Performance degrades sharply on out-of-sample data
- Strategy logic has no economic or behavioral rationale

**Rule of thumb (degrees of freedom):** A strategy should generate at least 10-20 trades per free parameter. A strategy with 5 tunable parameters needs a minimum of 50-100 trades in the backtest to have any statistical validity.

**Mitigation:**

- Keep strategies simple (fewer parameters)
- Use walk-forward analysis
- Demand that the strategy logic has a clear rationale (why should this edge exist?)
- Test across multiple markets and timeframes

### 2.2 Look-Ahead Bias

Look-ahead bias occurs when the backtest uses information that would not have been available at the time of the trade decision.

**Common sources:**

- Using the close price to make a decision that must be executed at the close price (you cannot know the close until it has happened)
- Calculating indicators using the full dataset (e.g., normalizing a Z-score over the entire history rather than a rolling window)
- Adjusting for stock splits or dividends using future adjustment factors
- Using fundamental data before its actual release date (earnings are reported with a lag)

**Prevention:**

- Use point-in-time data where possible
- Process data strictly chronologically
- For indicators, use only data available up to and including the current bar
- For fundamental data, apply the reporting lag (typically 45-90 days after quarter-end)

### 2.3 Survivorship Bias

Survivorship bias occurs when the backtest universe only includes securities that have survived to the present day, excluding delisted, bankrupt, or merged companies.

**Impact on swing trading:**

- Stocks that went to zero are excluded, inflating average returns
- Mean-reversion strategies are particularly affected because stocks that "reverted" in the backtest may have been delisted in reality
- Can inflate annual returns by 1-3% or more

**Mitigation:**

- Use survivorship-bias-free databases (e.g., CRSP, Norgate Data, Sharadar)
- Include delisted stocks with their terminal returns
- Apply delisting returns rather than simply dropping securities from the universe

### 2.4 Data Snooping (Multiple Testing Bias)

Data snooping occurs when many strategy variants are tested on the same dataset, and only the best-performing variant is selected. Even random strategies will occasionally produce good backtests by chance, and testing many variants guarantees finding one.

**Example:** Testing 100 moving average crossover combinations on the same dataset. If each has a 5% chance of appearing significant by luck, you expect roughly 5 false positives.

**Mitigation:**

- Apply Bonferroni correction or similar adjustments for multiple comparisons
- Reserve truly untouched out-of-sample data
- Use walk-forward analysis
- Maintain a research log documenting all tested variants (not just the winners)

**White's Reality Check and Hansen's SPA Test** are formal statistical procedures for adjusting p-values when many strategies have been tested on the same data.

### 2.5 Transaction Costs

Ignoring or underestimating transaction costs is one of the most common reasons backtests overstate performance.

**Components for swing trading:**

| Cost Component | Typical Range (US Equities) |
|---|---|
| Commission | $0 (many brokers) to $0.005/share |
| Bid-ask spread | 0.02-0.10% per side for liquid stocks; 0.20%+ for small caps |
| Market impact | Negligible for retail; relevant above ~$50K per trade in small caps |
| SEC fee | ~$0.000008 per dollar sold |

**For a swing trading backtest, a conservative all-in cost assumption is 0.05-0.10% per side (0.10-0.20% round trip) for liquid large-cap stocks, and 0.15-0.30% per side for small caps.**

### 2.6 Slippage

Slippage is the difference between the expected fill price and the actual fill price. It is caused by price movement between signal generation and order execution, and by the bid-ask spread.

**Modeling slippage in backtests:**

- **Fixed slippage:** Add a fixed cost per share (e.g., $0.02) or percentage (e.g., 0.05%)
- **Volume-based slippage:** Scale slippage by the ratio of order size to average volume
- **Volatility-based slippage:** Higher ATR stocks experience more slippage

For swing trading with next-day market orders on liquid stocks, slippage of 0.05-0.15% per trade is a reasonable assumption.

### 2.7 Liquidity Constraints

Backtests often assume unlimited liquidity — any position size can be entered or exited at the quoted price. In reality:

- Small-cap and micro-cap stocks may trade very thin volumes
- A position exceeding 1-5% of average daily volume will experience significant market impact
- Exits during fast-moving markets (gap downs, panic selling) may face extreme slippage

**Rule of thumb:** Limit position size to no more than 1-2% of the stock's average daily volume for entries, and be aware that exits under stress may require multiple days.

---

## 3. Performance Metrics

### 3.1 Total Return

The simplest metric. The percentage gain or loss over the entire backtest period.

```
Total Return = (Final Equity - Initial Equity) / Initial Equity
```

Total return is easy to understand but misleading in isolation because it ignores the time period, risk taken, and path dependency.

### 3.2 Compound Annual Growth Rate (CAGR)

Annualizes the total return to enable comparison across strategies with different backtest durations.

```
CAGR = (Final Equity / Initial Equity)^(1 / Years) - 1
```

**Example:** A strategy that turns $100,000 into $250,000 over 5 years:

```
CAGR = (250,000 / 100,000)^(1/5) - 1 = 2.5^0.2 - 1 = 0.201 = 20.1%
```

### 3.3 Sharpe Ratio

The most widely used risk-adjusted return metric. Measures excess return per unit of total volatility.

```
Sharpe Ratio = (R_p - R_f) / sigma_p
```

Where:
- `R_p` = annualized portfolio return
- `R_f` = risk-free rate (e.g., T-bill yield)
- `sigma_p` = annualized standard deviation of portfolio returns

**Interpretation:**

| Sharpe Ratio | Assessment |
|---|---|
| < 0.5 | Poor |
| 0.5 - 1.0 | Acceptable |
| 1.0 - 2.0 | Good |
| 2.0 - 3.0 | Very good |
| > 3.0 | Excellent (verify — may indicate overfitting) |

**Annualization from daily returns:**

```
Sharpe_annual = Sharpe_daily * sqrt(252)
```

**Limitations:**

- Penalizes upside volatility equally with downside volatility
- Assumes returns are normally distributed (they are not — fat tails exist)
- Sensitive to the return frequency used in calculation (daily vs weekly vs monthly)

### 3.4 Sortino Ratio

Addresses the Sharpe Ratio's main weakness by only penalizing downside volatility.

```
Sortino Ratio = (R_p - R_f) / sigma_d
```

Where `sigma_d` is the annualized standard deviation of negative returns only (downside deviation).

For swing trading strategies that aim for occasional large gains with controlled losses, the Sortino Ratio is often a more appropriate measure than Sharpe.

### 3.5 Calmar Ratio

Measures return relative to the worst drawdown experienced.

```
Calmar Ratio = CAGR / |Max Drawdown|
```

**Example:** A strategy with 15% CAGR and 20% max drawdown:

```
Calmar = 0.15 / 0.20 = 0.75
```

**Interpretation:**

| Calmar Ratio | Assessment |
|---|---|
| < 0.5 | Poor risk/reward |
| 0.5 - 1.0 | Acceptable |
| 1.0 - 2.0 | Good |
| > 2.0 | Excellent |

The Calmar Ratio is particularly relevant for swing traders because max drawdown directly determines the psychological and financial pain of the strategy.

### 3.6 Maximum Drawdown (MDD)

The largest peak-to-trough decline in equity during the backtest.

```
MDD = max over all t of [ (Peak_t - Trough_t) / Peak_t ]
```

**Key considerations:**

- Always report both the percentage and the duration of the max drawdown
- **Max drawdown duration** — how long it took to recover to the previous peak — is equally important
- In live trading, the actual max drawdown will almost certainly exceed the backtest max drawdown
- A common heuristic: expect live drawdowns to be 1.5-2x the backtest maximum

### 3.7 Win Rate

The percentage of trades that are profitable.

```
Win Rate = Winning Trades / Total Trades
```

Win rate alone is meaningless without knowing the average win size and average loss size. A strategy with a 30% win rate can be highly profitable if winners are much larger than losers.

**Typical ranges for swing trading:**

- Trend-following strategies: 35-50% win rate with high reward-to-risk
- Mean-reversion strategies: 55-70% win rate with lower reward-to-risk

### 3.8 Profit Factor

The ratio of gross profits to gross losses.

```
Profit Factor = Sum of Winning Trades / |Sum of Losing Trades|
```

**Interpretation:**

| Profit Factor | Assessment |
|---|---|
| < 1.0 | Losing strategy |
| 1.0 - 1.5 | Marginal (may not survive costs) |
| 1.5 - 2.0 | Good |
| 2.0 - 3.0 | Very good |
| > 3.0 | Excellent (verify — may be overfit or based on few trades) |

Profit factor is intuitive and robust. A value above 1.5 after realistic transaction costs is a reasonable threshold for a viable swing trading strategy.

### 3.9 Expectancy

The average amount you expect to make (or lose) per dollar risked on each trade.

```
Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
```

Or expressed per dollar risked:

```
Expectancy per $1 risked = (Win Rate * Avg Win / Avg Loss) - Loss Rate
```

**Example:** A strategy with 45% win rate, average win of $600, average loss of $300:

```
Expectancy = (0.45 * $600) - (0.55 * $300) = $270 - $165 = $105 per trade
```

This means on average each trade is expected to generate $105 of profit.

### 3.10 Recovery Factor

Measures the strategy's ability to recover from drawdowns relative to total profit.

```
Recovery Factor = Net Profit / |Max Drawdown|
```

A recovery factor above 3.0 over a multi-year backtest suggests a robust strategy. A value below 1.0 means the strategy has not earned enough to justify the drawdown it experienced.

### 3.11 Summary Table of Desirable Metric Ranges

For a swing trading strategy on US equities, approximate targets:

| Metric | Minimum Viable | Good | Excellent |
|---|---|---|---|
| CAGR | 10% | 15-25% | > 25% |
| Sharpe Ratio | 0.5 | 1.0-1.5 | > 2.0 |
| Sortino Ratio | 0.7 | 1.5-2.5 | > 3.0 |
| Calmar Ratio | 0.3 | 0.7-1.5 | > 2.0 |
| Max Drawdown | < 40% | < 20% | < 10% |
| Win Rate | 30% | 45-55% | > 60% |
| Profit Factor | 1.2 | 1.5-2.0 | > 2.5 |
| Expectancy | > $0 | > $50/trade | > $200/trade |

---

## 4. Statistical Validation

### 4.1 Why Statistical Significance Matters

A backtest showing 15% CAGR means nothing if the result could easily be explained by random chance. Statistical validation determines whether the observed performance is genuinely different from zero (or from a benchmark) with sufficient confidence.

### 4.2 T-Test for Strategy Returns

The one-sample t-test evaluates whether the mean return of the strategy is significantly different from zero.

```
t = (mean_return - 0) / (std_return / sqrt(N))
```

Where:
- `mean_return` = average trade return (or daily return)
- `std_return` = standard deviation of trade returns
- `N` = number of trades (or trading days)

**Degrees of freedom:** `df = N - 1`

At a 95% confidence level (alpha = 0.05), a t-statistic above approximately 1.96 indicates the strategy's returns are statistically distinguishable from zero.

**Example:** A strategy with 150 trades, mean return per trade of 0.8%, and standard deviation of 4.5%:

```
t = 0.008 / (0.045 / sqrt(150)) = 0.008 / 0.00367 = 2.18
```

With `t = 2.18 > 1.96`, the strategy's returns are statistically significant at the 5% level.

**Important caveats:**

- Returns are typically not normally distributed (violates a t-test assumption)
- Serial correlation in returns can inflate the t-statistic
- Statistical significance does not imply economic significance (a statistically significant 0.01% edge may not cover costs)

### 4.3 Bootstrap Analysis

Bootstrapping is a non-parametric method that avoids distributional assumptions. It is particularly suited to trading strategy evaluation because trade returns are often skewed and fat-tailed.

**Procedure:**

1. Collect the N trade returns from the backtest.
2. Draw N returns randomly with replacement to form a bootstrap sample.
3. Calculate the metric of interest (e.g., mean return, Sharpe Ratio) from the bootstrap sample.
4. Repeat 10,000 times.
5. Construct a confidence interval from the distribution of bootstrap estimates.

**Confidence interval interpretation:** If the 95% bootstrap confidence interval for the mean trade return is [0.2%, 1.4%], we are 95% confident the true mean return lies in that range. If the interval does not include zero, the strategy's edge is statistically significant.

**Permutation test (randomization test):**

An alternative bootstrap approach: randomly shuffle the assignment of entries and exits to test whether the strategy's returns could have occurred by chance. If the actual strategy return exceeds 95% of the permuted returns, the strategy is significant at the 5% level.

### 4.4 Minimum Number of Trades

The number of trades required for statistical significance depends on the signal-to-noise ratio of the strategy.

**Approximation using the t-test formula, solving for N:**

```
N_min = (t_critical * std_return / mean_return)^2
```

At 95% confidence (`t_critical ≈ 2.0`):

| Mean Trade Return | Std Dev of Returns | Min Trades Needed |
|---|---|---|
| 0.5% | 3.0% | 144 |
| 1.0% | 5.0% | 100 |
| 1.0% | 3.0% | 36 |
| 2.0% | 5.0% | 25 |
| 0.3% | 4.0% | 711 |

**Practical guideline for swing trading:** Aim for a minimum of 100-200 trades in the backtest. Fewer than 50 trades makes it nearly impossible to distinguish signal from noise for typical swing trading edge magnitudes.

### 4.5 Confidence Intervals for Key Metrics

Beyond mean return, confidence intervals should be constructed for all key metrics:

**Sharpe Ratio confidence interval (approximate):**

```
SE(Sharpe) ≈ sqrt( (1 + 0.5 * Sharpe^2) / N )
95% CI: Sharpe +/- 1.96 * SE(Sharpe)
```

Where N is the number of return observations.

**Example:** A Sharpe Ratio of 1.2 estimated from 252 daily returns:

```
SE = sqrt( (1 + 0.5 * 1.44) / 252 ) = sqrt(1.72 / 252) = sqrt(0.00683) = 0.0826
95% CI: 1.2 +/- 0.162 = [1.04, 1.36]
```

**Max Drawdown confidence interval:** No clean analytical formula exists. Use Monte Carlo simulation (Section 1.6) to estimate the distribution of max drawdowns and extract percentiles.

### 4.6 Multiple Hypothesis Correction

When testing multiple strategies or parameter sets, the probability of finding a false positive increases rapidly.

**Family-wise error rate (FWER):**

```
P(at least one false positive) = 1 - (1 - alpha)^k
```

Where k is the number of tests. With 50 tests at alpha = 0.05:

```
P = 1 - 0.95^50 = 0.923
```

A 92% chance of at least one false positive — almost guaranteed.

**Corrections:**

- **Bonferroni:** Divide alpha by k. Simple but very conservative.
- **Holm-Bonferroni:** A step-down procedure that is less conservative than Bonferroni.
- **False Discovery Rate (FDR / Benjamini-Hochberg):** Controls the expected proportion of false positives among rejected hypotheses. Often more appropriate for strategy screening.

**Deflated Sharpe Ratio (DSR)** — proposed by Bailey and Lopez de Prado — adjusts the Sharpe Ratio for the number of trials, skewness, and kurtosis:

```
DSR = P[ SR > 0 | SR_hat, SE(SR_hat), skew, kurtosis, trials ]
```

This is arguably the single most important metric for evaluating a backtested strategy because it directly accounts for the data snooping that is inherent in strategy development.

---

## 5. Optimization Techniques

### 5.1 Parameter Optimization

Most trading strategies have tunable parameters: moving average periods, RSI thresholds, stop-loss distances, position sizing rules, etc. Optimization is the process of selecting parameter values that maximize some objective function (usually a risk-adjusted return metric).

**Objective function selection matters:**

| Objective | Pros | Cons |
|---|---|---|
| Total Return | Simple | Ignores risk; leads to overfitting |
| Sharpe Ratio | Risk-adjusted | Penalizes upside volatility |
| Sortino Ratio | Penalizes only downside | Still can overfit |
| Calmar Ratio | Focuses on drawdown | Sensitive to a single event |
| Profit Factor | Robust, intuitive | Does not account for return magnitude per unit of time |
| Custom (e.g., Sharpe * sqrt(N_trades)) | Can balance multiple objectives | Harder to interpret |

**Best practice:** Optimize on a composite objective or on Sharpe/Sortino, and then verify that other metrics (drawdown, profit factor, trade count) remain acceptable.

### 5.2 Grid Search

Grid search exhaustively evaluates every combination of parameter values on a predefined grid.

**Example:** A strategy with two parameters:
- Moving average period: [10, 15, 20, 25, 30, 40, 50]
- RSI threshold: [20, 25, 30, 35]

Total combinations: 7 * 4 = 28

**Advantages:**
- Complete coverage of the parameter space
- Easy to visualize (parameter heatmaps)
- Reveals the shape of the performance surface

**Disadvantages:**
- Computational cost scales exponentially with the number of parameters (curse of dimensionality)
- For 5+ parameters, becomes impractical

**Parameter heatmap analysis:** After a grid search, plot a heatmap of the objective function across parameter pairs. A robust strategy shows a broad, smooth "plateau" of good performance — not a single sharp peak. If performance is concentrated in a narrow spike, the strategy is likely overfit.

### 5.3 Random Search

Instead of exhaustively testing a grid, random search samples parameter combinations randomly from defined ranges.

**Advantages over grid search:**
- More efficient in high-dimensional spaces (Bergstra & Bengio, 2012)
- Can cover irregular parameter spaces
- Avoids grid alignment artifacts

**In practice:** For strategy development with 3-5 parameters, random search with 200-500 samples often outperforms an equivalent-cost grid search in finding good parameter regions.

### 5.4 Walk-Forward Optimization (WFO)

Walk-forward optimization combines optimization with walk-forward analysis (Section 1.4). It is the most rigorous approach to parameter selection.

**Detailed procedure:**

1. Define the IS optimization window length (e.g., 3 years).
2. Define the OOS test window length (e.g., 6 months).
3. On the first IS window, run a grid or random search to find optimal parameters.
4. Apply those parameters to the subsequent OOS window and record results.
5. Advance the window by the OOS length.
6. Repeat until all data is consumed.
7. Concatenate all OOS results for the final performance report.

**Key decisions:**

- **IS/OOS ratio:** A ratio of 4:1 to 6:1 (IS:OOS) is common. Too short an IS window leads to unstable optimization; too short an OOS window does not provide enough trades for evaluation.
- **Re-optimization frequency:** For swing trading on daily bars, re-optimizing every 3-6 months is typical.
- **Anchored vs rolling:** If market regimes change slowly, anchored (expanding) windows may be better. If regimes change quickly, rolling windows adapt faster.

### 5.5 Robustness Testing

Even after walk-forward optimization, additional robustness checks help ensure the strategy is not fragile.

**Parameter sensitivity analysis:**

Perturb each parameter by +/- 10-20% from its optimal value. If performance degrades dramatically, the strategy is fragile. A robust strategy should degrade gradually.

**Multi-market testing:**

Apply the strategy to related but different markets. A swing trading strategy developed on US large-cap stocks should ideally show positive (even if weaker) results on:
- US mid-cap and small-cap stocks
- European or Asian equity markets
- Different time periods not included in the original backtest

**Regime-specific testing:**

Evaluate performance separately in:
- Bull markets (rising 200-day MA)
- Bear markets (falling 200-day MA)
- High volatility regimes (VIX > 25)
- Low volatility regimes (VIX < 15)
- Ranging markets (no clear trend)

A strategy that only works in one regime is not necessarily bad — but you must be aware of this dependency and manage exposure accordingly.

**Noise injection:**

Add small random noise to entry/exit prices (e.g., +/- 0.1-0.5%) and re-run the backtest. A robust strategy should show similar performance. If results change dramatically with tiny price perturbations, the strategy is fragile and likely overfit.

---

## 6. Benchmark Comparison

### 6.1 Why Benchmarks Matter

A strategy that returns 12% per year sounds good — until you realize the S&P 500 returned 14% per year over the same period with no effort. Every strategy must be compared to relevant benchmarks to determine whether the active trading adds value.

### 6.2 Buy-and-Hold Benchmark

The simplest benchmark: invest the full capital in a broad index (or the strategy's universe) at the start and hold throughout the backtest period.

**Implementation:**
- Match the benchmark's starting date and capital to the strategy
- Include dividends (use total return index)
- Apply the same transaction costs for the initial purchase

### 6.3 S&P 500 (and Other Index Benchmarks)

Common benchmarks for US equity swing trading:

| Benchmark | Ticker | Use Case |
|---|---|---|
| S&P 500 Total Return | SPX / SPY | Large-cap strategies |
| Russell 2000 | IWM | Small-cap strategies |
| Nasdaq 100 | QQQ | Tech / growth strategies |
| Equal-weight S&P 500 | RSP | Strategies with equal-weight portfolios |
| 60/40 Stock/Bond | — | Risk-parity comparison |

**Important:** Always compare to the benchmark that most closely matches the strategy's investment universe and risk profile.

### 6.4 Risk-Adjusted Comparisons

Raw return comparisons are misleading because they ignore risk. A strategy that returns 20% with 30% max drawdown is not necessarily better than one returning 12% with 8% max drawdown.

**Compare these metrics head-to-head:**

- Sharpe Ratio of strategy vs Sharpe Ratio of benchmark
- Sortino Ratio of strategy vs Sortino Ratio of benchmark
- Max drawdown of strategy vs max drawdown of benchmark
- Calmar Ratio of strategy vs Calmar Ratio of benchmark
- Ulcer Performance Index (UPI): captures both depth and duration of drawdowns

### 6.5 Alpha and Beta

**CAPM Alpha (Jensen's Alpha):**

```
Alpha = R_p - [R_f + Beta * (R_m - R_f)]
```

Where:
- `R_p` = portfolio return
- `R_f` = risk-free rate
- `R_m` = market return
- `Beta` = portfolio's sensitivity to market movements

Alpha represents the excess return not explained by market exposure. Positive alpha means the strategy adds value beyond what could be achieved by simply leveraging or de-leveraging a market index.

**Beta:**

```
Beta = Cov(R_p, R_m) / Var(R_m)
```

| Beta | Interpretation |
|---|---|
| 0 | Uncorrelated with the market (market-neutral) |
| 0.5 | Half the market's volatility exposure |
| 1.0 | Moves with the market |
| 1.5 | 50% more volatile than the market |
| Negative | Inversely correlated (hedging) |

**For swing trading strategies:**

- A beta close to 1.0 with positive alpha means the strategy captures market returns plus an additional edge.
- A beta significantly below 1.0 with positive alpha is particularly valuable because it provides returns with less market exposure.
- A high-beta strategy with no alpha is simply leveraged index exposure and offers no real edge.

### 6.6 Information Ratio

Measures the consistency of alpha generation relative to tracking error.

```
Information Ratio = (R_p - R_b) / Tracking Error
```

Where:
- `R_b` = benchmark return
- `Tracking Error` = standard deviation of (R_p - R_b)

An Information Ratio above 0.5 is good; above 1.0 is excellent.

### 6.7 Practical Benchmark Comparison Framework

When evaluating a swing trading strategy, present results in a comparison table:

```
                        Strategy    S&P 500     60/40
CAGR                    18.2%       11.4%       7.8%
Max Drawdown           -16.3%      -33.9%     -20.1%
Sharpe Ratio            1.35        0.72       0.65
Sortino Ratio           2.10        0.95       0.88
Calmar Ratio            1.12        0.34       0.39
Beta                    0.45         1.0       0.60
Alpha (annual)          9.1%         0%        1.2%
% Time in Market       62%         100%       100%
```

This format immediately shows whether the strategy justifies its complexity and trading costs compared to passive alternatives.

### 6.8 The Ultimate Test

A strategy is worth trading live only if:

1. **Positive OOS performance** — walk-forward results are profitable after costs
2. **Statistical significance** — t-stat > 2.0 or bootstrap CI excludes zero
3. **Superior risk-adjusted returns** — Sharpe and Sortino beat the benchmark
4. **Positive alpha** — returns are not just leveraged beta
5. **Acceptable drawdowns** — max drawdown is within psychological and financial tolerance
6. **Logical rationale** — there is a plausible explanation for why the edge exists and why it should persist
7. **Robustness** — results hold across parameter perturbations, markets, and time periods

Meeting all seven criteria is rare. Meeting five or six is a good starting point for paper trading and gradual capital deployment.

---

## References and Further Reading

- Aronson, D. (2006). *Evidence-Based Technical Analysis*. Wiley.
- Bailey, D. & Lopez de Prado, M. (2014). "The Deflated Sharpe Ratio." *Journal of Portfolio Management*.
- Bergstra, J. & Bengio, Y. (2012). "Random Search for Hyper-Parameter Optimization." *JMLR*.
- Harvey, C., Liu, Y., & Zhu, H. (2016). "...and the Cross-Section of Expected Returns." *Review of Financial Studies*.
- Pardo, R. (2008). *The Evaluation and Optimization of Trading Strategies*. Wiley.
- Tomasini, E. & Jaekle, U. (2009). *Trading Systems: A New Approach to System Development and Portfolio Optimization*. Harriman House.
- White, H. (2000). "A Reality Check for Data Snooping." *Econometrica*.
