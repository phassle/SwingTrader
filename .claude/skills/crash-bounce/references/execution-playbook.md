# Execution Playbook — Order Mechanics and Spread Management

## Broker Requirements

Not all brokers handle these trades well. You need:

- **Pre-market data access** — To check if the stock is trading before 09:30
- **Level 2 quotes** — To see bid/ask depth, not just last price
- **Bracket orders** — Entry + SL + TP as one linked package
- **Hotkeys or quick order entry** — Limit orders must go out fast at 10:00

Recommended: Interactive Brokers (IBKR) for commission structure and order routing.
Acceptable: TD Ameritrade/Schwab, Lightspeed, Tradier.
Avoid: Robinhood (no bracket orders, payment for order flow hurts fills on illiquid names).

## Order Types

### Entry: Limit Order at Ask

Do NOT use market orders. The spread on post-crash stocks can be 2-5%. A market order
gives you the worst possible fill. Use a limit order at the current ask — you still get
filled immediately, but you cap your entry price.

```
Example:
  Bid: $0.95  Ask: $1.05  Last: $1.00

  Market order: fills at $1.05 (or worse if ask moves)
  Limit at $1.05: fills at $1.05 (guaranteed cap)
  Limit at $1.02: might not fill (cheaper but risky — you could miss the move)

  Recommendation: Limit at ask. You're paying the spread, but you're paying a KNOWN spread.
```

### Stop Loss: Stop-Limit (not Stop-Market)

Stop-market on illiquid stocks can gap through your price and fill much lower.
Use a stop-limit with a limit price slightly below the stop:

```
Entry: $1.05
Stop trigger: $1.034 (= entry × 0.985 = -1.5%)
Limit: $1.02 (slightly below trigger — gives room to fill)

If price gaps below $1.02: order won't fill. This is a feature, not a bug.
If the stock gaps from $1.05 to $0.80, you don't want to sell at $0.80 —
you want to reassess. But this is rare in intraday trading.
```

### Take Profit: Limit Order

Simple limit sell at entry × 1.03.

```
Entry: $1.05
TP: $1.08 (= entry × 1.03 = +3.0%, rounded to nearest tick)
```

### Time Stop: Market-on-Close or Manual

At 15:30 ET, if position still open, close with a market order. Some brokers support
Market-on-Close (MOC) orders — use these if available as they execute at the closing
auction price, which is less volatile than a mid-day market order.

## Spread Tracking

Track the spread on every trade. Over time, this data reveals:
- Which stocks have tighter spreads (better candidates)
- What time of day spreads are narrowest (optimal entry window)
- Whether your spread assumption in backtests is realistic

```
Track these fields:
  pre_market_spread:   [%]  (from pre-market quotes at 09:00)
  open_spread:         [%]  (at 09:30)
  entry_spread:        [%]  (at time of actual entry)
  exit_spread:         [%]  (at time of actual exit)
```

### Spread Rules of Thumb

| Spread | Action |
|--------|--------|
| < 1% | Excellent — trade with full size |
| 1-2% | Acceptable — trade with standard size |
| 2-3% | Borderline — reduce size by 50% |
| > 3% | Skip — spread eats too much of the edge |

## Pre-Market Data Sources

Before 09:30, check whether the stock is actually trading:

- **Webull** (free): Shows pre-market volume and quotes
- **IBKR Trader Workstation**: Full pre-market Level 2
- **Yahoo Finance**: Basic pre-market price (delayed, but shows if stock is active)
- **OTC Markets** (for OTC names): Pre-market indications

If a stock has ZERO pre-market volume, it may be halted. Verify on:
- NYSE/Nasdaq halt list: https://www.nyse.com/trade-halt-current
- SEC EDGAR for any overnight filings

## Scaling the Strategy

### Adding capital

As account grows, the constraint shifts from position sizing to liquidity:

```
Account: $10k  → Position ~$6k  → Easy to fill on any 500k+ volume stock
Account: $50k  → Position ~$33k → Need stocks with 1M+ volume
Account: $100k → Position ~$66k → Need stocks with 2M+ volume, or split across 2 names
Account: $250k+→ This strategy doesn't scale further without moving the market
```

### Adding a second position

The 2-trades-per-day limit exists for correlation control. If you take 2 trades on the
same day, they must be:
- Different sectors
- Different drop types (E + T is fine; E + E is concentrated)
- Total risk still ≤ 2% of equity

### What NOT to scale

Do NOT scale via leverage. These are already volatile stocks with tight stops. Margin
amplifies both sides — and the losing side matters more because slippage is higher on
stop exits than profit exits.

## Common Execution Mistakes

| Mistake | Why it happens | Fix |
|---------|---------------|-----|
| Market order at open | Urgency / FOMO | Always use limits; missing one trade costs $0 |
| Moving stop loss down | "It'll come back" | Set bracket order and walk away |
| Trading during halt | Didn't check | Always verify stock is trading before placing orders |
| Too large for volume | Didn't calculate | Position < 1% of stock's daily volume |
| Entry at 09:31 | Impatience | Set alert for 10:00; do something else until then |
| No bracket order | Broker doesn't support | Switch brokers; manual stops WILL be forgotten |
