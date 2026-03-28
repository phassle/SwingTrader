# Backtesting Pitfall Checklist

Common traps that invalidate backtest results.

## Overfitting
- Parameter count vs trade count reasonable? Rule: 10-20 trades per free parameter.
- WFE > 0.5? If not, strategy is likely curve-fitted.

## Look-Ahead Bias
- Using only data available at signal time? No peeking at future closes?
- Common mistake: using daily close to generate signal that trades at daily close.

## Survivorship Bias
- Including delisted/bankrupt stocks, or just survivors?
- Survivor-only backtests overstate returns by 1-3% annually.

## Data Snooping
- Tested 50+ parameter combos? If yes, apply Bonferroni correction or WFA.
- Multiple comparisons inflate false positives exponentially.

## Transaction Costs
- Included courtage, spread, slippage realistically?
- Swedish large-cap round-trip: 0.20-0.90% (see swedish-costs.md).

## Liquidity
- Position size ≤ 1-2% of avg daily volume?
- Illiquid positions create phantom returns that can't be realized.

## Slippage Modeling
- Included 0.05-0.15% per trade for execution friction?
- Momentum strategies are particularly sensitive to slippage assumptions.
