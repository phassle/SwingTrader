---
name: crash-bounce
description: >
  Intraday mean reversion strategy for extreme gap-downs (≥40% single-day drops).
  Scans for crash candidates, classifies the drop type, and trades the next-day bounce
  with strict intraday risk management. Use when: scanning for crash-bounce candidates,
  evaluating whether a gap-down is tradeable, sizing a crash-bounce position, classifying
  why a stock crashed, reviewing crash-bounce results, or backtesting extreme-drop strategies.
  Also trigger on: "dead cat bounce", "extreme gap down", "oversold bounce", "crash recovery",
  "50% drop trade", or any discussion of trading stocks after massive single-day declines.
---

# Crash-Bounce: Intraday Mean Reversion on Extreme Gap-Downs

## The Edge (why this works)

When a stock drops ≥40% in a single day, the selling is often mechanical — margin calls,
stop-loss cascades, panic liquidation. Think of it like an overcrowded exit: everyone
rushes through the door at once, pushing the price below where it would settle if people
had time to think. The next morning, that forced selling pressure is exhausted, and the
stock often bounces before finding its new equilibrium.

The edge is NOT that the stock will recover. It won't. The edge is that extreme selling
overshoots fair value temporarily, creating a 1-day bounce window.

**Why the edge persists:** Most institutional traders can't or won't touch stocks in
freefall (risk mandates, compliance). Retail panic-sells. That leaves a gap for
disciplined short-term traders willing to buy the day after the crash.

**Why the edge is fragile:** Slippage on these names is severe. The gap between
"works in backtest" and "works live" is wider here than in almost any other strategy.
Every rule below exists to protect that fragile edge from being eaten by execution costs.

## Step 1: Scanning Rules

Run daily after market close. Identify candidates for next-day trading.

```
REQUIRED (all must pass):
  Close(today) ≤ 0.60 × Open(today)          # ≥40% intraday drop
  Volume(today) ≥ 500,000 shares              # Enough liquidity to trade
  Close(today) ≥ $0.50                        # Eliminates sub-penny noise
  Stock was listed ≥ 30 days ago              # Not a broken IPO/SPAC
  No trading halt pending                     # Must open tomorrow
  Market cap(prior day) ≥ $50M               # Not a shell company

PREFERRED (improve quality):
  Average daily volume(20d prior) ≥ 100,000   # Was liquid before crash
  At least 2 market makers quoting next day   # Someone is making a market
```

**Why ≥40% instead of ≥50%:** The original 50% threshold produces ~13 trades/year.
That's too few for statistical validation (you need 100+ to distinguish signal from noise).
Lowering to 40% roughly doubles the candidate pool without materially diluting the edge,
because the mean-reversion effect is present across the extreme-drop spectrum.

**Why volume ≥500k:** The original 5,000 shares in 5 minutes is far too low. If you're
deploying $5,000-10,000 per trade and the stock is at $1, you need to buy 5,000-10,000
shares. With only 5,000 shares total volume, your order IS the market — you'll move the
price against yourself. 500k daily volume gives you enough depth to enter and exit without
being the dominant flow.

## Step 2: Drop Classification

Not all crashes are equal. The bounce profile depends entirely on WHY the stock dropped.
Classify every candidate before trading.

| Type | Cause | Bounce Quality | Trade? |
|------|-------|---------------|--------|
| **E — Earnings miss** | Revenue/EPS miss, guidance cut | ★★★ Good | YES — company still operates, overreaction common |
| **O — Offering/dilution** | Secondary offering, PIPE, convert | ★★ Moderate | YES with caution — new shares depress price but company is real |
| **S — Sector contagion** | Peer crashed, sympathy selling | ★★★ Good | YES — if own fundamentals unchanged |
| **T — Technical/mechanical** | Margin calls, ETF rebalance, forced liquidation | ★★★★ Best | YES — purest mean reversion, no fundamental change |
| **F — Fraud/regulatory** | SEC investigation, audit failure, delisting risk | ★ Poor | NO — no bottom, avoid entirely |
| **B — Bankruptcy/insolvency** | Debt default, Chapter 11 filing | ✗ None | NO — stock may go to zero |

**How to classify:** Check the news. Takes 2 minutes. If you can't determine the cause,
skip the trade — the cost of sitting out one opportunity is zero; the cost of trading a
fraud is unlimited.

→ Deep dive: `references/drop-taxonomy.md`

## Step 3: Entry Rules

Entry happens the morning after the crash. The goal is to wait for the chaos to settle
before buying — not to rush in at the open.

```
ENTRY WINDOW: 10:00 - 10:30 ET (not 09:30-09:35)

Pre-entry checks (all must pass):
  [ ] Bid-ask spread has narrowed to < 2% of price
  [ ] Stock is NOT making new lows (price ≥ day's low + 1%)
  [ ] Volume in first 30 min ≥ 50,000 shares
  [ ] Drop classification is E, O, S, or T (not F or B)

Entry: Limit order at the ask (don't try to get a better fill —
       speed matters more than a few cents)
```

**Why 10:00 instead of 09:35:** The first 30 minutes after open are the most volatile
period. Spreads on a post-crash stock at 09:35 can be 3-5% of the price — your entire
profit target. By 10:00, market makers have recalibrated, spreads tighten, and you can
see whether there's actual buying interest or just a dead bounce. You sacrifice some
upside for dramatically better fills.

**Why the spread check matters:** A stock at $1.00 with a $0.95 bid / $1.05 ask has
a 10% spread. If you buy at $1.05 and your TP is +3% ($1.08), you're targeting 3 cents
of profit on a stock where the spread alone is 10 cents. The math doesn't work.
Wait for the spread to narrow, or skip.

## Step 4: Exit Rules

All positions close the same day. No overnight risk. No exceptions.

```
STOP LOSS:    -1.5% from entry price
TAKE PROFIT:  +3.0% from entry price
TIME STOP:    Close at 15:30 ET (30 min before close, avoids closing-auction volatility)

If neither SL nor TP hits by 15:30 → market order to close.

R:R ratio: 1:2 (risk 1.5 to make 3.0)
Required winrate to break even (after ~0.5% round-trip slippage): ~42%
```

**Why -1.5% SL instead of -0.5%:** The original -0.5% stop is inside normal bid-ask
bounce on these stocks. A stock at $1.00 with a $0.98/$1.02 spread will trigger a -0.5%
stop just from normal oscillation — that's not a losing trade, that's a spread artifact.
At -1.5%, you're stopped out by genuine adverse price movement, not noise.

**Slippage reality check (do this math before going live):**

```
Entry slippage:    ~0.3-0.5% (buying into post-crash spread)
Exit at TP:        ~0.1-0.2% (selling into buying interest)
Exit at SL:        ~0.3-0.5% (selling into renewed weakness)

Winner net: +3.0% - 0.4% entry - 0.15% exit = +2.45%
Loser net:  -1.5% - 0.4% entry - 0.4% exit  = -2.30%

Break-even winrate with slippage: 2.30 / (2.45 + 2.30) = 48.4%
```

If your backtest shows 55%+ winrate with proper slippage modeling, you have an edge.
If it shows 44-48%, the edge is too thin — either tighten execution or widen the parameters.

→ Deep dive: `references/execution-playbook.md`

## Step 5: Position Sizing

```
FIXED RULE: Risk 1% of equity per trade. Period.

Position size = (Equity × 0.01) / (Entry × 0.015)

Example: $25,000 account, entry at $1.20
  Size = ($25,000 × 0.01) / ($1.20 × 0.015)
  Size = $250 / $0.018
  Size = 13,888 shares → round to 13,800
  Dollar exposure = $16,560 (66% of account — this is normal for tight stops)

HARD LIMITS:
  Max 2 crash-bounce trades per day
  Max 5% total equity in crash-bounce at any time
  Position must be < 1% of stock's daily volume (you shouldn't be the market)
```

**Why no Kelly sizing:** Kelly requires precise winrate and payoff estimates. With 65
trades over 5 years, your winrate confidence interval is roughly ±12 percentage points.
Kelly at ⅛ with a true winrate at the low end of that interval will blow through the
account. Fixed 1% risk is boring, but boring is what survives to trade 200.

**When to graduate to Kelly:** After 200+ trades with live fills (not backtest),
compute actual slippage-adjusted winrate and payoff ratio. If the confidence interval
for the Kelly fraction is above 1%, you can consider ⅛ Kelly. Not before.

## Step 6: Daily Workflow

Think of this like a month-end close process — tasks have dependencies, and skipping
steps creates compounding errors.

```
EVENING SCAN (18:00, after market close):
  1. Run scanner → list candidates
  2. Classify each drop (E/O/S/T/F/B)
  3. Eliminate F and B types
  4. Check next-day calendar (Fed, major earnings → skip)
  5. Set alerts for remaining candidates

PRE-MARKET (09:00-09:30):
  6. Check pre-market quotes → is the stock trading?
  7. Check spread width → below 3%? (it will narrow further by 10:00)
  8. Confirm no overnight halt or news change

ENTRY WINDOW (10:00-10:30):
  9. Recheck spread (< 2%?)
  10. Confirm not making new lows
  11. Calculate exact position size
  12. Place limit order at ask

MONITORING (10:30-15:30):
  13. Set SL and TP as bracket order (automated, no manual intervention)
  14. DO NOT watch the chart. Bracket orders handle exits.

CLOSE (15:30):
  15. If position still open → close at market
  16. Log trade in journal

POST-CLOSE (15:45):
  17. Record fill prices, actual slippage, P&L
  18. Classify: was execution as expected?
```

## Step 7: Trade Journal (mandatory for every trade)

```
date:             [YYYY-MM-DD]
ticker:           [SYMBOL]
drop_pct:         [prior day's actual drop %]
drop_type:        [E / O / S / T]
drop_cause:       [1-sentence: what happened]
entry_time:       [HH:MM]
entry_price:      [actual fill]
entry_spread:     [bid-ask spread % at time of entry]
exit_time:        [HH:MM]
exit_price:       [actual fill]
exit_reason:      [TP / SL / TIME-STOP]
planned_risk:     [$]
actual_pnl:       [$]
slippage:         [entry slippage $ + exit slippage $]
notes:            [what would I do differently?]
```

### Journal Quality Check

Good: "ACME dropped 52% on earnings miss (rev $40M vs $55M expected). Entered at
$1.22 at 10:08, spread was 1.1%. Hit TP at $1.26 (+3.3% gross, +2.7% net after
slippage). Slippage was lower than expected — stock had strong retail buying interest."

Bad: "Bought ACME, made money." (This teaches you nothing.)

## Step 8: Validation Framework

Before trading real money, validate the backtest properly. Think of it like auditing
financial controls — you test both that the strategy *should* work (design) and that
it *did* work on data it's never seen (operating effectiveness).

### Required validation steps

```
1. SURVIVORSHIP CHECK
   - How many candidates had no next-day data? (halted, delisted)
   - These are losses you didn't count. Add them as -100% trades.

2. SLIPPAGE MODELING
   - Add 0.5% round-trip minimum to every backtest trade
   - Better: use actual bid-ask spreads from historical data

3. DATA SPLIT
   - In-sample (train): 60% of period → develop parameters
   - Out-of-sample (test): 40% of period → validate, DO NOT adjust
   - If OOS returns < 50% of IS returns: likely overfitted

4. PARAMETER SENSITIVITY
   - Vary drop threshold ±10% (test 35% and 45%)
   - Vary SL ±0.5% (test -1.0% and -2.0%)
   - Vary TP ±1.0% (test +2.0% and +4.0%)
   - If results collapse with small changes: overfitted

5. PAPER TRADING (minimum 30 trades)
   - Trade with real market data, fake money
   - Track actual fills vs backtest assumptions
   - If actual slippage > 2× backtest assumption: fix the model

6. SAMPLE SIZE
   - 65 trades: preliminary signal only
   - 100 trades: basic statistical validity (t-stat > 2.0)
   - 200 trades: confident enough for real sizing decisions
```

### Backtest vs Live Reconciliation

After 30+ live trades, reconcile backtest expectations against reality:

```
RECONCILIATION TABLE:
                    Backtest    Live       Variance
Winrate:            ____%       ____%      ____pp
Avg winner:         ____$       ____$      ____%
Avg loser:          ____$       ____$      ____%
Avg slippage:       ____$       ____$      ____%
Profit factor:      ____        ____       ____%
```

If live winrate is >5pp below backtest: investigate. Common causes are wider spreads
than modeled, fills at worse prices than assumed, or drop types that don't bounce as
expected (possibly F-type leaking through the filter).

→ Deep dive: `references/validation-framework.md`

## Step 9: P&L Decomposition (weekly/monthly)

Don't just track total P&L. Break it down by driver to understand where the edge
comes from and where it leaks:

```
MONTHLY P&L WATERFALL:
  Starting equity:                           $______
    [+/-] Type E trades (earnings):          $______ (N trades, __% WR)
    [+/-] Type O trades (offering):          $______ (N trades, __% WR)
    [+/-] Type S trades (sector):            $______ (N trades, __% WR)
    [+/-] Type T trades (technical):         $______ (N trades, __% WR)
    [-]   Total slippage cost:               $______
    [-]   Commissions:                       $______
  Ending equity:                             $______

Which drop type is most profitable?
Which drop type has highest slippage?
Are there drop types you should stop trading?
```

## Reference documents

Read these for deeper guidance on specific topics:

- **`references/drop-taxonomy.md`** — Detailed classification system with real examples,
  news source recommendations, and edge cases (what about biotech FDA rejections? SPAC
  de-SPACs? Chinese ADR delistings?)
- **`references/execution-playbook.md`** — Order types, broker requirements, pre-market
  data sources, spread tracking, and scaling the strategy
- **`references/validation-framework.md`** — Full validation checklist, Monte Carlo
  simulation setup, confidence interval calculations, and when to stop trading
