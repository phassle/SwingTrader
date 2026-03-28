# Practical Regime Switching Rules

Rules for detecting transitions between regimes in real-time.

## Rule 1: Breakout Follow-Through Collapse

- Track: % of daily breakouts above 20-day high that hold 3+ days.
- If falls <55% for 2+ weeks → Shift from Regime A to B/C. Reduce breakout allocation.

## Rule 2: VIX Spike Into Event

- If VIX spikes >25 on macro event date → Switch to Regime D rules. Cap overnight.
- If VIX falls back below 20 next day → Resume prior regime.

## Rule 3: MA Slope Flattening

- If 20 EMA slope drops <20° over 5 bars → Likely leaving Regime A.
- Check ADX; if also falling → Regime C incoming.

## Rule 4: Breadth Divergence

- If major index rallies but <50% of Nasdaq stocks above 50 MA → Weakening. Reduce size.

## Rule 5: Sector Alignment Check (Weekly)

- Count sectors in uptrend vs downtrend. If split <60/40 → Regime C/D likely.

## General Principle

When in doubt, shift to the more conservative regime. It's cheaper to miss a trade than to take a loss in the wrong regime.
