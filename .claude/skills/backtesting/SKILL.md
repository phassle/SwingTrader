---
title: Backtesting & Validation Framework
description: >-
  Validates swing trading strategies before deployment. Use when evaluating backtests,
  running performance tests, discussing overfitting, walk-forward analysis,
  or asking "does this strategy work?"
tags: [backtesting, performance-metrics, validation, overfitting, walk-forward-analysis]
---

# Backtesting & Validation Framework for SwingTrader

## 1. Minimum Trade Requirements

| Stage | Min Trades | Rationale |
|-------|-----------|-----------|
| **In-sample backtest** | 30 minimum | Basic logic validation |
| **Statistical validity** | 100+ trades | Distinguish signal from noise |
| **Confidence deployment** | 200+ trades | Strong signal-to-noise |

**Rule:** At least 10-20 trades per free parameter. A 5-parameter strategy needs ≥50-100 trades.

## 2. Data Split: IS / OOS / Holdout

| Segment | Allocation | Purpose |
|---------|-----------|---------|
| **In-Sample (IS)** | 50-70% | Develop & tune strategy |
| **Out-of-Sample (OOS)** | 20-30% | Validate on unseen data |
| **Holdout / Final** | 10-20% | One-time confirmation before live |

**Critical:** Once you examine OOS results, that data becomes in-sample. Never adjust parameters after looking at OOS.

## 3. Performance Targets (Post-Costs)

Swedish market swing trading on Nasdaq Stockholm Large Cap (~90 tickers):

| Metric | Minimum | Good |
|--------|---------|------|
| **CAGR** | 10% | 15-25% |
| **Sharpe Ratio** | 0.5 | 1.0-1.5 |
| **Sortino Ratio** | 0.7 | 1.5-2.5 |
| **Max Drawdown** | < 40% | < 20% |
| **Win Rate** | 30% | 45-55% |
| **Profit Factor** | 1.2 | 1.5-2.0 |

Deduct ~0.5-1% CAGR for slippage/commission if backtest doesn't include costs.

## 4. Go-Live Checklist

All criteria must pass before trading live capital:

- [ ] **OOS performance positive** — Walk-forward backtest profits after costs
- [ ] **Statistical significance** — t-stat > 2.0 or bootstrap CI excludes zero; N ≥ 100
- [ ] **Risk-adjusted metrics** — Sharpe/Sortino beat OMXS30 benchmark
- [ ] **Max drawdown acceptable** — Within tolerance (typically < 20%)
- [ ] **Paper trading validated** — 30-50 live trades within backtest expectations
- [ ] **Logical edge rationale** — Clear explanation of why edge persists
- [ ] **Robustness tested** — Holds across ±10-20% parameter perturbations

**Decision rule:** Must pass 6+ of 7 criteria for small live position.

## 5. Evidence Hierarchy

| Tier | Examples | Confidence |
|------|----------|------------|
| **Highest** | RS momentum, trend continuation, post-earnings drift | Strong academic support |
| **Medium** | Vol expansion/compression, mean reversion after extremes | Implementation-sensitive |
| **Lower** | Standalone oscillators, loose chart patterns | Needs strong context |

## Quick Decision Tree

```
≥30 trades? → No: Need more data
WFE > 0.5? → No: Likely overfit (see references/walk-forward-analysis.md)
CAGR >10%, Sharpe >0.5 post-costs? → No: Edge too small
All 7 go-live criteria? → No: Fix issues
Paper trading 30+ trades in range? → No: Investigate divergence
→ YES to all: Clear for small live position
```

## Reference documents

- `references/walk-forward-analysis.md` — WFA procedure and WFE thresholds
- `references/pitfalls.md` — Overfitting, look-ahead bias, survivorship bias checklist
- `references/swedish-costs.md` — Transaction costs and paper trading requirements
- `research/strategy-and-theory/07-backtesting-and-performance.md` — Full methodology
- `research/strategy-and-theory/10-empirical-evidence-and-edge-quality.md` — Evidence base
- `research/strategy-and-theory/26-latest-research-update-and-evidence-review.md` — Recent evidence
- `research/strategy-and-theory/19-algorithmic-swing-trading.md` — Implementation details
