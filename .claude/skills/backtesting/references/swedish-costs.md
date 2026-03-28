# Swedish Market Transaction Cost Model

Realistic cost assumptions for Nasdaq Stockholm Large Cap.

| Component | Range | Notes |
|-----------|-------|-------|
| **Courtage (commission)** | 0.05-0.25% | Depends on broker; many offer zero commissions |
| **Bid-Ask Spread (round-trip)** | 0.10-0.50% | Large caps ~0.10-0.20%; mid-caps wider |
| **Slippage** | 0.05-0.15% | Market impact + execution delay |
| **Total per round-trip trade** | **0.20-0.90%** | Conservative: assume 0.50-0.75% |

## Application

- Reduce backtest return by 0.50-0.75% annualized (for typical turnover).
- Higher turnover strategies (>50 trades/year) should use the upper bound.
- Zero-commission brokers still have spread and slippage costs.

## Paper Trading Validation

| Requirement | Target | Purpose |
|-------------|--------|---------|
| **Minimum trades** | 30-50 | Capture regime changes |
| **Minimum duration** | 3-6 months | Real market conditions |
| **Track all metrics** | All backtest metrics | Identify divergence early |
| **Compare to backtest** | Within 20-30% range | Significant gap = warning sign |

**Go-live gate:** Paper trading results must be within backtest expectations ± 1 standard deviation.
