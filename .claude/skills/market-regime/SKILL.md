---
name: market-regime
description: >
  Assess current market regime, match strategy to conditions, and anticipate shifts.
  Use when asking "what's the market doing?", choosing strategy based on regime,
  sector rotation, catalyst planning, or deciding "should I be trading now?"
  Four regimes (A:Trending Orderly, B:Trending Volatile, C:Sideways Choppy,
  D:Event-Panic). Detection via MA slopes, ADX, VIX, breakout follow-through.
  Swedish market focus (OMXS30, Riksbanken, ex-dividend April-May).
---

# Market Regime Assessment for SwingTrader

Identify regime, select strategies, size positions, manage sector exposure.

## Decision Tree: What Regime Are We In?

```
START
├─ MA Setup: 20 EMA > 50 SMA > 200 SMA (upslope)?
│  ├─ YES → Continue checking volatility
│  │  ├─ ADX 25-40 & VIX 15-20? → REGIME A (Orderly Trend)
│  │  └─ ADX 15-25 or VIX 20-30? → REGIME B (Volatile Trend)
│  └─ NO → Continue checking
├─ MA Setup: Flat/Intertwined or price choppy inside range?
│  ├─ Breakouts failing? Sector leadership inconsistent?
│  └─ → REGIME C (Sideways Choppy)
└─ Major macro event pending? (Fed, earnings season, >10% gap?)
   ├─ VIX > 25? Gaps wide? Correlations spiking?
   └─ → REGIME D (Event/Panic)
```

## The Four Regimes

### Regime A: Trending and Orderly
**Signals:** 20>50>200 MA rising, ADX 25-40, VIX 15-20, >60% breakout follow-through.
**Best strategies:** Trend continuation, breakouts, pullback-to-MA, RS leaders.
**Position sizing:** 100% normal.

### Regime B: Trending but Volatile
**Signals:** Trend exists but candles wide, gaps larger, ADX <25 or VIX 20-30.
**Best strategies:** Continuation with smaller size, pullbacks into major levels.
**Position sizing:** 60-75% of normal.

### Regime C: Sideways and Choppy
**Signals:** Range-bound, breakouts fail, MA flat/intertwined, ADX <20, VIX <18.
**Best strategies:** Range trading, selective mean reversion, S/R fades.
**Position sizing:** 50% of normal.

### Regime D: Event-Driven / Panic
**Signals:** Macro calendar dominates, VIX >30, gaps >3%, correlations near 1.0.
**Best strategies:** Very selective post-event continuation, defensive rotations.
**Position sizing:** 30-50% of normal. Consider cash/hedge.

## Strategy-Regime Matrix

```
┌────────────────────┬──────┬──────┬──────┬──────┐
│ Strategy           │  A   │  B   │  C   │  D   │
├────────────────────┼──────┼──────┼──────┼──────┤
│ Breakout           │ ★★★  │ ★★   │ ★    │ ✗    │
│ Pullback→MA        │ ★★★  │ ★★   │ ★    │ ✗    │
│ Mean Reversion     │ ★    │ ★    │ ★★★  │ ★    │
│ Trend Continuation │ ★★★  │ ★★   │ ✗    │ ✗    │
│ RS Leaders         │ ★★★  │ ★★   │ ★    │ ✗    │
│ Catalyst Fade      │ ★    │ ★★   │ ★    │ ★★★  │
└────────────────────┴──────┴──────┴──────┴──────┘
★★★ = Ideal | ★★ = Good | ★ = Weak | ✗ = Avoid
```

## Quick Regime Checklist (Daily)

- [ ] 20 EMA slope > 30° or flat?
- [ ] ADX above/below 20?
- [ ] VIX in/out of 15-20 band?
- [ ] This week's breakout success rate?
- [ ] % tickers above 50 MA?
- [ ] Which sectors in uptrend?
- [ ] Major event pending this week/month?
- [ ] Sizing: 100% (A), 75% (B), 50% (C), 30% (D)?

## Swedish Market: Key Events

**Benchmark:** OMXS30. **Riksbanken:** ~6x/year. **Reporting season:** Apr-May, Oct-Nov. **Ex-div clusters:** Apr-May.

## Reference documents

Deep dives by topic:

- `references/detection-inputs.md` — Full detection input table by regime
- `references/switching-rules.md` — 5 practical rules for regime transitions
- `references/sector-rotation.md` — Sector rotation by economic phase
- `references/catalysts.md` — Catalyst classification and Swedish calendar events
- `research/strategy-and-theory/08-market-structure-and-conditions.md` — MA, ADX, VIX
- `research/strategy-and-theory/25-regime-to-strategy-mapping.md` — Full matrix
- `research/strategy-and-theory/30-sector-rotation-and-economic-cycles.md` — Phase lens
- `research/strategy-and-theory/21-catalyst-and-event-playbook.md` — Event timing
- `research/strategy-and-theory/04-swing-trading-strategies.md` — Strategy details
