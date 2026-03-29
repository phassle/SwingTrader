---
name: risk-management
description: >
  Position sizing, stop-loss levels, portfolio heat, and drawdown protocols for SwingTrader.
  Trigger when: calculating position size, setting stops, managing portfolio heat, risk/reward,
  drawdown management, pyramiding, sector concentration, correlation checks, or "how much should I buy?"
---

# Risk Management for SwingTrader

Risk is the only thing you control. Without these rules, profitable systems blow up.

## Rule 1: Position sizing formula

```
Shares = (Account × Risk%) / (ATR × Multiplier)

Example: Account 100k, 1.5% risk, ATR 3.75, multiplier 2.0
Shares = (100000 × 0.015) / (3.75 × 2.0) = 200 shares

Equivalent: Shares = (Account × Risk%) / (Entry − Stop)
  where Stop = Entry − (ATR × Multiplier)
```

Never exceed 2% per trade. If stop > entry × 10%, shrink or reject.

## Rule 2: ATR-based stops

```
Stop = Entry − (ATR(14) × multiplier)
  VIX < 15: 1.5× ATR (tight)
  Normal: 2.0× ATR
  VIX > 25: 2.5× ATR (volatile)
  Pre-earnings: add +0.5× ATR buffer
```

Mechanical stops prevent revenge trading.

## Rule 3: Portfolio heat — 4-tier action bands

```
Heat = Σ(position size × distance to stop) / account size

Heat action bands:
  < 3%:  COMFORTABLE — Room to add positions freely
  3–6%:  NORMAL      — Default operating range, selective new entries only
  6–8%:  CAUTION     — Stop adding positions, tighten existing stops
  > 8%:  STOP        — No new trades; close weakest position immediately

During drawdown or VIX > 25: shift all bands down by 3% (e.g. >5% = STOP)
```

## Rule 4: Max concurrent positions by account

```
≤50k SEK: 2–3 positions
50–100k: 3–5 positions
100–250k: 5–8 positions
>250k: 8–12 positions
```

Exceeding limits = harder to monitor, false diversification.

## Rule 5: Sector concentration — max 2–3 per sector, max 30% per sector

Check before entry: Is sector at limit? If YES, reject unless closing existing.

## Rule 6: Correlation limit — >0.7 = redundant, avoid pairing

```
Check rolling 20-day correlation to all open positions before adding.
High correlation (>0.7) = concentrated risk disguised as diversification.
Target: all correlations < 0.5.
```

## Rule 7: Drawdown protocol (hard stops)

```
5% drawdown: Halve position sizes, tighten stops, no new entries
10% drawdown: Close ALL positions, stop trading this month
20% drawdown: STOP ALL trading, 30-day halt minimum
```

Track equity high-water mark daily; measure drawdown in real-time.

### Position triage priority (when cutting positions)

When heat or drawdown forces you to reduce, close positions in this order — borrowed from financial variance investigation methodology:

1. **Largest absolute loss** — biggest drag on equity, cut first
2. **Worst R-multiple** — position farthest from target relative to risk
3. **Unexpected direction** — trade moving opposite to thesis (broken setup)
4. **Regime mismatch** — position opened in regime A, now in regime C/D
5. **Oldest stale trade** — no progress toward target in >7 days

## Rule 8: Partial exit strategy — 1/3 at 1R, 1/3 at 2R, 1/3 trailing

```
Entry 265.50, Stop 258.00 (Risk = 7.50)
1R target: 273.00 → Sell 1/3, move stop to entry+0.5R
2R target: 280.50 → Sell 1/3, reduce further
Remaining 1/3: Trail stop (1.5× ATR) or trend break
```

Lock in gains systematically; don't let winners become losers.

## Rule 9: Time-based exit — no 1R profit in 10 days = close

```
≤3 days: Must be +1R or close if <0.5R
4–7 days: Must be +0.5R or close if flat/negative
8–10 days: Must be +1R or exit
>10 days: Exit regardless (capital decay)
```

## Risk:Reward ratio — always ≥1:1.5, ideally 1:2

Every trade must justify the risk taken. Reject <1:1.5 setups.

## Pre-trade checklist

```
[ ] Position size calculated via formula?
[ ] Stop is ATR-based (Rule 2)?
[ ] Risk ≤ 1–2% of account (Rule 1)?
[ ] Portfolio heat remains < 6% (Rule 3)?
[ ] Sector concentration OK (Rule 5)?
[ ] No correlation > 0.7 (Rule 6)?
[ ] Account not in drawdown protocol (Rule 7)?
[ ] Risk:Reward ≥ 1:1.5?
```

**If any unchecked: DO NOT TRADE.**

## Reference documents

Deep dives by topic:

- `research/strategy-and-theory/05-risk-management.md` — Kelly Criterion, Monte Carlo models
- `research/strategy-and-theory/14-trade-management.md` — Trailing stops, pyramiding mechanics
- `research/strategy-and-theory/18-correlation-and-portfolio-construction.md` — Correlation matrices, sector rotation
- `research/strategy-and-theory/29-position-scaling-and-pyramiding.md` — Scaling into winners, pyramid structure
- `research/strategy-and-theory/24-execution-and-slippage-playbook.md` — Slippage, commissions, order placement
