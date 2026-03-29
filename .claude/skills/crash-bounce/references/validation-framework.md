# Validation Framework — From Backtest to Live

## The Core Problem

Every backtest lies a little. The question is how much. For crash-bounce, the lies are
bigger than most strategies because:

1. These stocks have the widest spreads in the market
2. Halted/delisted stocks disappear from databases (survivorship bias)
3. 65 trades is not enough to distinguish edge from luck
4. Execution at 09:35 on a post-crash stock is fantasy without realistic fill modeling

This framework exists to systematically close the gap between backtest and reality.

## Phase 1: Backtest Audit

Before trusting any backtest result, verify these items. Think of it like an auditor
checking financial controls — you need evidence, not assumptions.

### 1.1 Survivorship Bias Check

```
For every scanning day in the backtest period:
  - How many stocks met the ≥40% drop criterion?
  - How many of those had valid next-day OHLCV data?
  - How many were halted or had no data?

Halted/missing stocks = trades you WOULD have taken but couldn't.
These aren't neutral — they're likely losses (the stock was halted
because something even worse happened overnight).

CONSERVATIVE: Count each missing stock as a -100% loss on risk amount.
MODERATE: Count each as a -50% loss.
WRONG: Ignore them.
```

### 1.2 Slippage Model Verification

```
The backtest must include realistic slippage. Verify:

  Entry slippage modeled:     ≥ 0.3%  (buying into wide spread)
  Exit-at-TP slippage:        ≥ 0.1%  (selling into buying interest)
  Exit-at-SL slippage:        ≥ 0.3%  (selling into renewed weakness)
  Exit-at-time-stop slippage: ≥ 0.2%  (closing during normal trading)

If the backtest used ZERO slippage:
  - Subtract 0.5% from every trade's return
  - Recompute winrate, profit factor, and drawdown
  - If still profitable: proceed. If not: edge doesn't exist.
```

### 1.3 Fill Assumption Check

```
The backtest assumes you can buy at price X. Can you actually?

Check:
  - Was the entry price the Open, Close, VWAP, or something else?
  - If Open: you're assuming a fill at the exact opening print. On a
    volatile post-crash stock, the open price may exist for milliseconds.
  - If VWAP: more realistic, but assumes you trade throughout the day.

RECOMMENDATION: Use the ask price at 10:00 (or VWAP of 09:30-10:30)
  as the entry price. This is conservative but honest.
```

### 1.4 Data Quality

```
Verify the data source handles:
  - Stock splits (adjusted prices?)
  - Reverse splits (common in stocks that crash 50%+)
  - Ticker changes (post-restructuring)
  - Delistings (when does the stock leave the dataset?)
  - Halts (are halt days correctly represented?)

Polygon.io is good for US equity data. Yahoo Finance has known issues
with split adjustments and delisted stocks.
```

## Phase 2: Statistical Validation

### 2.1 Sample Size Assessment

```
With N trades, the standard error of winrate is:

  SE = sqrt(WR × (1 - WR) / N)

  N=65, WR=0.446:
  SE = sqrt(0.446 × 0.554 / 65) = 0.0617 = 6.17%

  95% confidence interval: 0.446 ± 1.96 × 0.0617
  = 0.446 ± 0.121
  = [0.325, 0.567]

This means: with 65 trades, the true winrate could be anywhere from
32.5% to 56.7%. That's an enormous range.

At 32.5% winrate with the original parameters (0.5% SL, 2% TP):
  E = 0.325 × 2 - 0.675 × 0.5 = 0.65 - 0.3375 = +0.31% per trade
  Still positive! But add slippage and it's likely zero.

At 32.5% winrate with improved parameters (1.5% SL, 3% TP):
  E = 0.325 × 3 - 0.675 × 1.5 = 0.975 - 1.0125 = -0.04% per trade
  Negative. You need a higher winrate with wider stops.

CONCLUSION: 65 trades gives a directional signal but NOT enough
precision for position sizing decisions. Get to 150+ before adjusting
parameters or using Kelly.
```

### 2.2 Monte Carlo Simulation

Run 10,000 simulations of N trades drawn from the observed distribution:

```python
import numpy as np

# From backtest results
wins = np.array([...])   # actual % return on each winning trade
losses = np.array([...]) # actual % return on each losing trade
winrate = len(wins) / (len(wins) + len(losses))

results = []
for _ in range(10000):
    equity = 10000
    for _ in range(200):  # simulate 200 trades
        if np.random.random() < winrate:
            ret = np.random.choice(wins)
        else:
            ret = np.random.choice(losses)
        equity *= (1 + ret/100)
    results.append(equity)

results = np.array(results)
print(f"Median final equity: ${np.median(results):,.0f}")
print(f"5th percentile (worst case): ${np.percentile(results, 5):,.0f}")
print(f"95th percentile (best case): ${np.percentile(results, 95):,.0f}")
print(f"Probability of loss: {(results < 10000).mean():.1%}")
```

Key outputs:
- If 5th percentile is below starting equity → real risk of loss over 200 trades
- If probability of loss > 20% → edge too thin for real money
- If median is < 1.5× starting equity → not worth the effort/risk

### 2.3 T-Test for Edge Existence

```python
from scipy import stats

all_returns = np.concatenate([wins, losses])  # % returns
t_stat, p_value = stats.ttest_1samp(all_returns, 0)

print(f"t-statistic: {t_stat:.2f}")
print(f"p-value: {p_value:.4f}")

# t > 2.0 and p < 0.05: statistically significant edge
# t between 1.0-2.0: suggestive but not conclusive
# t < 1.0: no evidence of edge
```

## Phase 3: Paper Trading

Paper trade 30-50 trades with real market data before risking capital.

### 3.1 Paper Trading Protocol

```
REQUIREMENTS:
  - Use a broker's paper trading mode (IBKR paper account is ideal)
  - Execute at real market prices during real market hours
  - Follow every rule in the skill exactly
  - Log every trade with the full journal template

DO NOT:
  - "Paper trade" by writing down what you would have done at end of day
  - Use delayed quotes (need real-time for entry timing)
  - Skip the classification step "because I know it's a good one"
```

### 3.2 Paper vs Backtest Reconciliation

After 30 paper trades, reconcile:

```
                        Backtest    Paper      Delta     Flag if
Winrate:                ____%       ____%      ____pp    > 5pp gap
Avg winner (gross):     ____%       ____%      ____%     > 1% gap
Avg loser (gross):      ____%       ____%      ____%     > 1% gap
Avg entry slippage:     ____%       ____%      ____%     > 0.3% gap
Avg exit slippage:      ____%       ____%      ____%     > 0.3% gap
Profit factor:          ____        ____       ____      < 80% of backtest
Avg spread at entry:    ____%       ____%      ____%     > 2× backtest
Trades skipped (illiq): ____        n/a        n/a       > 20% of candidates
```

**Investigation triggers** (any one → pause and diagnose):
- Winrate > 5pp below backtest → spreads wider than modeled, or F-types leaking in
- Profit factor < 80% of backtest → slippage model was too optimistic
- > 20% of candidates skipped → volume filter too loose

### 3.3 Go/No-Go Decision

```
GO (start with real money at 1% risk):
  ✓ Paper winrate within 5pp of backtest
  ✓ Paper profit factor > 1.2
  ✓ Slippage is within 2× of backtest model
  ✓ No systematic execution problems
  ✓ Completed 30+ paper trades

CONDITIONAL GO (start at 0.5% risk):
  ~ Paper winrate 5-10pp below backtest
  ~ Profit factor 1.0-1.2
  ~ Some execution issues identified but addressable

NO-GO (do not trade with real money):
  ✗ Paper winrate > 10pp below backtest
  ✗ Profit factor < 1.0
  ✗ Slippage makes most trades unprofitable
  ✗ > 30% of candidates untradeable due to liquidity
```

## Phase 4: Live Trading Monitoring

### 4.1 Drawdown Limits

```
5% drawdown from peak:  Reduce to 0.5% risk per trade
8% drawdown from peak:  Stop trading. Reassess everything.
                        Re-enter only after 20 paper trades
                        showing expected performance.
```

### 4.2 Monthly Review

```
Monthly checklist:
  [ ] Winrate within expected range (±10pp of backtest)?
  [ ] Slippage consistent with paper trading period?
  [ ] P&L decomposed by drop type — any types consistently losing?
  [ ] Sample size growing — how many trades total now?
  [ ] Any new patterns (regulatory changes, market structure)?
  [ ] Reconcile: backtest → paper → live trajectory
```

### 4.3 When to Stop Trading the Strategy

```
STOP if any of these are true:
  - Live profit factor < 1.0 over 50+ trades
  - Slippage has increased >50% vs paper trading period
  - Market structure change (e.g., new circuit breaker rules)
  - You can't execute the daily workflow consistently
  - Drawdown exceeds 8% and paper trading doesn't recover it
```
