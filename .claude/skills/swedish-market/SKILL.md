---
title: Swedish Market Knowledge
description: SwingTrader Swedish market specifics. Triggers on ISK accounts, .ST tickers, Avanza, Nasdaq Stockholm, tax implications, trading hours, or market structure questions.
tags: [swedish-stocks, nasdaq-stockholm, isk-account, tax, trading-hours, liquidity, avanza]
---

# Swedish Market Knowledge for SwingTrader

## ISK Account Rules

| Feature | ISK Account |
|---------|-------------|
| Capital gains tax | 0% — no tax on profits |
| Annual tax | ~0.9% schablonbeskattning (deemed income) on account value |
| Wash sale rule | No such rule in Sweden |
| Loss deduction | Cannot deduct losses |
| Settlement | T+2 standard |
| Account type | Tax-advantaged investment savings |

**Key implication:** Loss harvesting doesn't work. Accept losses as part of trading costs. The ISK's no-tax advantage makes it the default account for Swedish traders despite annual wealth tax.

## Trading Hours & Market Structure

| Time (CET) | Event |
|-----------|-------|
| 08:45–09:00 | Opening auction (order accumulation) |
| 09:00–17:25 | Continuous trading |
| 17:25–17:30 | Closing auction |
| 17:30+ | After-hours (minimal liquidity) |

**No extended hours trading.** Overnight gaps are real. Plan exits and stops with T+2 settlement in mind.

## Ticker Format & Universe

**Nasdaq Stockholm tickers end in `.ST`**
- A-shares: founder/family controlled, low liquidity
- B-shares: publicly tradable, higher liquidity — always trade B shares
- Example: `VOLV B.ST` (Volvo B), not `VOLV A.ST`

**Large Cap universe (~60–80 names):**
- Market cap >SEK 20B
- ADTV >SEK 10M
- Includes OMXS30 constituents

**Expanded to Mid Cap** when scanner diversifies. Mid Cap threshold ~SEK 1–5B.

## Liquidity Reality vs US Markets

| Metric | US (S&P 500) | Swedish (Large Cap) |
|--------|-------------|-------------------|
| Bid-ask spread | 0.01–0.02% | 0.05–0.15% |
| ADTV threshold | >$1M | >SEK 10M (~$1M) |
| Slippage on 1% position | Minimal | 0.1–0.3% |

**Implication:** Position sizing must account for wider spreads. A 1% position in a large-cap stock may incur 15+ bps slippage on entry/exit.

## Key Differences from US Market

| Feature | US | Sweden |
|---------|----|----|
| PDT rule | Yes (min $25k, 3 trades/5 days) | No — trade as much as you want |
| Settlement | T+1 (standard) | T+2 |
| Options markets | Extensive | Limited, expensive |
| Extended hours | 4am–8pm | None |
| Dividend tax | Long/short term rates | Part of ISK (0%) |

## Avanza-Specific Rules

**Courtage (commission):**
- 0.049–0.25% depending on account tier
- Minimum ~SEK 10 per trade

**Stop-loss orders:**
- Only executable during market hours (09:00–17:30)
- Triggers automatically if price touches trigger level
- No trailing stops — fixed price only
- Orders expire at end of day unless renewed

**Impact:** Cannot protect overnight positions. Plan accordingly.

## Data Sources & Benchmarks

| Source | Coverage | Notes |
|--------|----------|-------|
| Börsdata | All Swedish stocks | Official, real-time |
| Yahoo Finance | .ST tickers | Quotes, fundamentals, historical |
| Avanza | Holdings, balances | Real account data |
| Nasdaq Nordic | Official exchange | Technical specs, halts |

**Key indices:**
- `OMXS30.ST` — 30 largest, blue-chip proxy
- `OMXSPI.ST` — Broad market (all listed stocks)
- SX sector indices — sector rotation signals

## Research & Deeper Dives

Extend or reference these documents before creating new ones:
- **27-swedish-market-adaptation.md** — Full market structure, tax optimization
- **09-regulation-tax-and-trade-operations.md** — Regulatory constraints, T+2, ISK mechanics
- **22-watchlist-and-universe-selection.md** — Screening criteria, filtering logic
- **16-stock-screening-playbook.md** — Technical screening adapted to Swedish liquidity

## Quick Decision Tree

**Q: Should I trade A or B shares?**
A: Always B shares. Higher liquidity, lower slippage.

**Q: Can I use stop-losses overnight?**
A: No. Avanza stops only work 09:00–17:30. Use alerts instead.

**Q: How much capital gains tax will I pay?**
A: Zero if trading in ISK. Pay ~0.9% annual wealth tax on account balance instead.

**Q: What's the universe size?**
A: ~60–80 Large Cap (>SEK 20B), expandable to ~200 with Mid Cap.

**Q: How do Swedish spreads compare to the US?**
A: 5–10x wider. Account for 0.1–0.3% slippage on 1% positions.
