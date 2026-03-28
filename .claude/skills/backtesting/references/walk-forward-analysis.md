# Walk-Forward Analysis (WFA)

The gold standard for avoiding static overfitting.

## Procedure

1. Define optimization window (e.g., 2 years) and test window (e.g., 6 months)
2. Optimize parameters on IS window
3. Apply optimized parameters to subsequent OOS window
4. Record OOS performance
5. Slide windows forward; repeat
6. Concatenate all OOS results for final report

## Walk-Forward Efficiency (WFE)

```
WFE = OOS Annual Return / IS Annual Return
```

| WFE | Assessment |
|-----|-----------|
| **> 0.5** | **Pass** — Strategy generalizes acceptably |
| 0.3 – 0.5 | Marginal — Possible overfitting; investigate |
| **< 0.3** | **Fail** — Strong overfitting signal; redesign strategy |

## Key Principles

- Once you examine OOS results, that data becomes in-sample. Never adjust parameters after looking at OOS performance.
- WFE is the single best overfitting detector available for retail traders.
- If WFE is marginal (0.3-0.5), try reducing the number of free parameters before abandoning the strategy.
