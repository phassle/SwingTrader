# Progressive Exposure — Detailed Minervini-Style Position Building

## Core Philosophy

Progressive exposure is the idea that you earn the right to be more invested by
being right first. Think of it like a poker tournament — you don't go all-in on
the first hand. You play small pots to feel out the table, then increase your bets
when you're reading the game well.

In trading terms: start with small "probe" positions. If they work, the market is
confirming your read — add more. If they fail, the market is telling you something —
reduce and wait.

## The Four Phases

### Phase 1: PROBING (0-25% invested)

```
PURPOSE: Test the current market environment with real money, small size.

RULES:
  - Open 2-3 positions at 50% of normal size
  - Use only Setup A (horizontal level) or Setup B (MA consolidation)
    These are the highest-probability setups — save C and D for later phases
  - Each position must be in a different sector (diversify the test)
  - Maximum total exposure: 25% of equity

DECISION TREE:
  2 of 3 positions hit TP or trail profitably → Move to Phase 2
  1 of 3 profitable, 2 flat → Stay in Phase 1, try 2 more probes
  2 of 3 stop out → STOP. Go to cash. Wait 5 trading days minimum.
  3 of 3 stop out → STOP. Go to cash. Wait 10 trading days.
    Market environment is hostile. Re-evaluate sector ETF positions.

WHY 50% SIZE:
  If your normal risk is 1% per trade, probes risk 0.5%.
  3 probes × 0.5% = 1.5% max drawdown if all fail.
  That's a cheap "tuition" to learn the market isn't ready.
```

### Phase 2: BUILDING (25-60% invested)

```
PURPOSE: Confirmed the market is working. Add positions at full size.

RULES:
  - Add positions at 100% of normal size
  - Each new position requires: passing setup (A/B/C/D) + sector flow confirmed
  - Only add when existing Phase 1 positions are profitable
    (If Phase 1 positions have turned negative since Phase 2 started → pause)
  - Maximum 5 positions total (including Phase 1 probes)

POSITION QUALITY FILTER:
  Leader stocks: full size (1% risk)
  A-tier sympathy: 75% size (0.75% risk)
  B-tier sympathy: 50% size (0.5% risk)
  C-tier sympathy: skip entirely in Phase 2

STOP MANAGEMENT:
  Phase 1 positions: if profitable, move stops to breakeven
  Phase 2 positions: initial stops per setup rules (prior day low / pivot)

TRANSITION TO PHASE 3:
  At least 4 of 5 positions are profitable → eligible for Phase 3
  Portfolio is up ≥2% since Phase 1 started → eligible for Phase 3
  Both conditions must be true.
```

### Phase 3: PRESSING (60-90% invested)

```
PURPOSE: Market is strongly confirming. Press the advantage.

RULES:
  - Add to existing winners (pyramid) AND/OR open new positions
  - Pyramids: add 50% of original size at a new breakout within the trend
    Example: bought 333 shares at $28.50, stock consolidates at $31,
    breaks out → add 166 shares at $31.10
  - The pyramid entry MUST be higher than the original entry
    (You are adding into strength, never into weakness)
  - Before pyramiding: move original position stop to breakeven
  - Maximum 7 positions total
  - Maximum 90% of equity invested

CRITICAL RULE — NEVER DO THIS:
  ✗ Add to a losing position
  ✗ Average down
  ✗ Pyramid below original entry
  ✗ Add to a position that's "about to bounce"

  The whole point of progressive exposure is that you only increase
  when you're RIGHT. Adding to losers is the opposite of this system.

STOP MANAGEMENT:
  Original positions: trail with 20-day MA (2 consecutive closes below = exit)
  Pyramids: initial stop at prior day's low
  If any position hits stop → evaluate Phase 4 transition
```

### Phase 4: PROTECTING (holding / trailing)

```
PURPOSE: Protect profits. No new positions. Trail everything.

TRIGGERS TO ENTER PHASE 4:
  - First position in the portfolio hits its trailing stop
  - OR portfolio drawdown from peak reaches 3%
  - OR market environment signal fires (SPY breaks 20-day MA on volume)

RULES:
  - NO new positions of any kind
  - Trail all stops to the tighter of:
    a) 10-day MA (aggressive trail)
    b) Prior swing low (structural trail)
  - When a position stops out, sell and do NOT replace it
  - When 50% of positions have stopped out → back to Phase 1

PHASE 4 EXIT:
  All positions stopped out → Cash. Wait for Phase 1 re-entry.
  Market stabilizes (SPY reclaims 50-day MA) → Back to Phase 2
    (Skip Phase 1 probes only if you still hold profitable positions)
```

## Phase Transition Summary

```
CASH → Phase 1:  SPY > 50-day MA, >50% sector ETFs above 50-day MA
Phase 1 → Phase 2: 2 of 3 probes profitable
Phase 2 → Phase 3: 4 of 5 positions profitable AND portfolio +2%
Phase 3 → Phase 4: First trailing stop hit OR 3% drawdown from peak
Phase 4 → Phase 1: 50% of positions stopped out
Phase 4 → Phase 2: Market stabilizes while still holding winners

ANY PHASE → CASH:
  First 2-3 probes all stop out (market hostile)
  SPY breaks 200-day MA (bear market)
  VIX > 30 (panic environment)
```

## Position Sizing Within Each Phase

```
FORMULA: Position size = (Account × Risk%) / (Entry - Stop)

RISK% BY PHASE:
  Phase 1: 0.5% risk per trade (half size)
  Phase 2: 1.0% risk per trade (full size)
  Phase 3: 1.0% risk per trade (full size) + 0.5% for pyramids
  Phase 4: no new positions, but trail existing

MAXIMUM PORTFOLIO HEAT:
  Phase 1: 1.5% total risk (3 × 0.5%)
  Phase 2: 5.0% total risk (5 × 1.0%)
  Phase 3: 8.5% total risk (5 × 1.0% + 5 × 0.5% pyramids + 1 new)
  Phase 4: declining as stops tighten
```

## Tracking Exposure Phase

Add this to your daily journal:

```
date:             [YYYY-MM-DD]
phase:            [1-probe / 2-build / 3-press / 4-protect / cash]
positions_open:   [count]
positions_profit: [count profitable]
portfolio_pct:    [% of equity invested]
portfolio_heat:   [total open risk %]
phase_trigger:    [what moved you to this phase]
next_transition:  [what would move you to next phase]
```

## Common Mistakes

```
MISTAKE 1: Skipping Phase 1
  "The market looks great, I'll just go all in"
  → The probe phase exists because your PERCEPTION of the market
    is not the same as the market's REALITY. Test first.

MISTAKE 2: Staying in Phase 1 too long
  "I want to be really sure before I commit"
  → If 2 of 3 probes work, MOVE to Phase 2. The signal is there.
    Excessive caution after confirmation costs you the best part of the move.

MISTAKE 3: Not reducing in Phase 4
  "This stock is still above its 50-day MA, I'll hold"
  → Phase 4 means the PORTFOLIO is deteriorating. Individual stocks
    may look fine but the environment is shifting. Trail tight.

MISTAKE 4: Going back to Phase 3 from Phase 4
  "Things stabilized, I'll press again"
  → You can go from Phase 4 to Phase 2, never back to Phase 3.
    Phase 3 is earned by building from Phase 1 → 2 → 3 sequentially.
    Skipping back to pressing mode without re-proving the environment
    is how drawdowns compound.
```

## Analogy: The Thermostat Model

Think of your exposure like a thermostat:

- Phase 1 is checking the temperature (small probes)
- Phase 2 is turning on the heat (confirmed it's cold, adding warmth)
- Phase 3 is cranking it up (it's working, room is warming nicely)
- Phase 4 is the thermostat turning off (room is warm enough, protect the gains)

The thermostat doesn't go from "off" to "max" — it ramps up gradually and
backs off when the target is reached. Your portfolio exposure should work
the same way.
