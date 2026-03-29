---
name: parabolic-panic
description: >
  Intraday bounce strategy targeting stocks that went parabolic (+100% in 5 days) then
  panic-crashed ≥30% from open. Uses 5-min data to detect capitulation candles and
  trades the first green candle bounce. Use when: scanning for parabolic-crash candidates,
  evaluating a panic drop for bounce potential, detecting capitulation candles on intraday
  charts, sizing a panic-bounce position, backtesting extreme intraday reversals, or
  asking "should I buy this crash?" Also trigger on: "parabolic crash", "panic selling",
  "capitulation candle", "intraday bounce", "5-minute chart entry", "first green candle",
  or any discussion of trading the bounce after a parabolic run-up collapses.
---

# Parabolic Panic: Intraday Capitulation Bounce

## Market Applicability

**This strategy targets US micro/small-cap stocks ($0.50–$10).** Nasdaq Stockholm
Large Cap stocks almost never go +100% in 5 days — that behavior is specific to US
penny stocks, SPAC squeeze plays, and micro-cap momentum names. This skill is designed
for US market execution as a complement to the main SwingTrader system.

**When to use crash-bounce vs parabolic-panic:**
- **Crash-bounce:** Any stock that drops ≥40% in a single day (no prior run-up required).
  Works on both US and Swedish markets (earnings misses, offerings, sector contagion).
- **Parabolic-panic:** Only stocks with prior +100%/5d parabolic run-up that then crash
  ≥30% intraday. US micro-cap only. The run-up creates a specific holder profile
  (weak hands) that makes the bounce mechanics different.

## The Edge (why this works)

When a stock runs +100% in 5 days, it attracts a specific crowd: retail momentum
chasers, FOMO buyers, options-driven gamma squeezes. These are "weak hands" — they
bought for the move, not the value. When the move reverses, they all panic at once.

Think of it like a crowded escalator reversing direction — everyone piles into the
exit at the same time, creating a jam. The jam IS the capitulation. When the last
panic seller has sold, the stock bounces — not because it's worth more, but because
selling pressure is temporarily exhausted.

The edge: you're buying the exhaustion point of panic selling, not a recovery.

## Step 1: Universe Filter (Evening Scan)

Run daily after close. Identify stocks that went parabolic and are candidates for
next-day panic.

```
REQUIRED (all must pass):
  Close(today) ≥ 2.0 × Close(5 trading days ago)   # +100% in 5 days
  Price(today): $0.50 – $10.00                       # Small/micro-cap sweet spot
  Volume(today) ≥ 500,000 shares                     # Liquid enough to trade
  At least 1 day in the 5-day run had ≥ +50% gain    # Parabolic, not gradual

WHY THE PARABOLIC FILTER:
  A stock that grinds up +100% over 5 days (e.g., +15%/day × 5) has a different
  holder profile than one that spikes +80% in one day then adds +20%. The spike
  attracts more weak hands = more panic potential = better bounce setup.
```

**Why $0.50–$10?** Below $0.50, spreads are too wide relative to price (a $0.01
spread on a $0.30 stock is 3.3%). Above $10, the stocks rarely go parabolic in
5 days — that's more of a large-cap earnings move, which is a different strategy.

## Step 2: Intraday Data Requirements (5-Min OHLCV)

On the day AFTER the stock qualifies, you need 5-minute candle data from 09:30–16:00.

### Derived Metrics

```
%-drop from open:
  drop_pct = (low_of_candle - open_of_day) / open_of_day × 100

Panic low:
  lowest price reached within the first 60 minutes (09:30–10:30)

Capitulation candle (must meet ALL three):
  1. Candle range ≥ 10% of stock price
     (e.g., stock at $3 → candle high-low ≥ $0.30)
  2. Lower wick ≥ 5% of stock price
     (e.g., stock at $3 → wick ≥ $0.15)
  3. Volume ≥ 2× average 5-min volume for that stock

The capitulation candle is the "flush" — high volume, wide range, long lower wick
means sellers dumped and buyers absorbed it. The wick is the key — it shows that
price went low but was rejected. That rejection IS the signal.
```

## Step 3: Entry Rules

```
PANIC DROP GATE: Price must drop ≥ 30% from today's open within first 60 min
  If drop < 30%: not a panic — skip. Could be an orderly selloff.
  If drop ≥ 30%: proceed to entry scan.

ENTRY SIGNAL:
  First GREEN 5-min candle after the panic low
  (Green = Close > Open on that 5-min candle)

  This means: after continuous red candles driving the stock down,
  the first candle where buyers step in and close above its open.

ENTRY PRICE: Close of that first green candle
  (Or a limit order at the open of the next candle if you need a second to react)

ENTRY PRICE: Close of the first green 5-min candle.
  If you need reaction time: use a limit order at the ASK price on the
  very next 5-min candle after the green candle closes. Priority is
  speed over price — these bounces move fast.

ENTRY WINDOW: 09:45 – 10:30 ET
  Before 09:45: too early, opening chaos hasn't settled
  After 10:30: the first bounce window is closing, risk/reward deteriorates

  EDGE CASE — LATE DROP: If the stock doesn't drop 30% until after 10:30,
  skip the trade. The entry window is hard. The bounce mechanics weaken
  after 10:30 because: (1) initial margin calls are done, (2) short sellers
  have finished their morning covering, and (3) lunch-hour volume dries up.

  EDGE CASE — HALT: If the stock gets halted during the entry window,
  the entry window extends by the halt duration (max extension: 30 min).
  If halt lasts >30 min or extends past 11:00 ET, skip the trade entirely.

ENTRY CHECKLIST:
  [ ] Stock dropped ≥ 30% from today's open
  [ ] Panic low occurred within first 60 min
  [ ] Capitulation candle identified (range ≥ 10%, wick ≥ 5%, volume ≥ 2×)
  [ ] First green 5-min candle has appeared
  [ ] Bid-ask spread < 3% (these stocks will be wide — but not TOO wide)
  [ ] Entry window is 09:45–10:30
```

## Step 4: Exit Rules

```
TP1: +15% from entry → Sell 50% of position
TP2: +30% from entry → Sell remaining 50%

STOP LOSS: Below the panic low OR -10% from entry (whichever comes FIRST)

TIME STOP: Flat by 15:30 ET (no overnight positions, ever)

MAX 1 TRADE PER TICKER PER DAY
  After the first bounce, the edge disappears. The stock may chop around or
  do a second flush, but that's a different (worse) setup. One shot per name.
```

**Why the two-tier TP?** These stocks can bounce 20-50% from the panic low, but
the bounce is often a V-shape that reverses quickly. Selling 50% at +15% locks
in a guaranteed profit; the remaining 50% has room to run to +30%.

**Slippage reality check:**
```
Entry slippage:    ~1-2% (buying into a wide spread on a volatile stock)
Exit at TP:        ~0.5% (selling into bounce demand)
Exit at SL:        ~1-2% (selling into renewed panic)

Winner (TP1 only): +15% - 1.5% entry - 0.5% exit = +13% on 50% of position
Loser:             -10% - 1.5% entry - 1.5% exit = -13% on full position

For the system to work: need TP1 hit rate > 50% to be net positive.
Hitting TP2 on the remaining 50% is gravy.
```

## Step 5: Position Sizing

```
RULE: Risk no more than 1% of equity per trade.

Position size = (Equity × 0.01) / (Entry × Stop%)

Example: $25k account, entry at $2.50, stop at 10% below = $2.25
  Risk per share = $0.25
  Size = ($25,000 × 0.01) / $0.25 = 1,000 shares
  Dollar exposure = $2,500 (10% of account)

HARD LIMITS:
  Max 1 parabolic-panic trade per day (not per ticker — total)
  Position < 2% of stock's first-hour volume
  No more than 5% of equity in this strategy at any time
```

## Step 6: Catalyst Identification (AI Opportunity)

Every parabolic run has a catalyst. Understanding the catalyst tells you whether
the panic is likely to produce a bounce or a permanent collapse:

```
CATALYST TYPES AND BOUNCE QUALITY:

  Social media / Reddit / X pump → ★★★ Good bounce
    Why: retail-driven, herd behavior, sells off as fast as it ran up,
    but same crowd often "buys the dip" creating a bounce

  Earnings beat (small cap) → ★★ Moderate bounce
    Why: real fundamental event, but the +100% was an overreaction.
    Stock finds new level — partial reversion, not full

  Short squeeze → ★★★★ Best bounce
    Why: shorts covering drove the run-up. When it reverses, some shorts
    re-short too early and get squeezed again on the bounce

  FDA approval / regulatory → ★★ Moderate bounce
    Why: real event, real price discovery. Panic = confused retail,
    bounce = institutions buying the new fair value

  Dilution announcement during run → ★ Poor bounce
    Why: company issuing shares into the strength. New supply = permanent
    price pressure. Bounce is small and fake.

  Pump and dump / fraud → ✗ No trade
    Why: no floor. The entire run was artificial.
```

### Using AI to Detect Catalyst Type

```
APPROACH: Feed AI (Claude, GPT) the stock ticker + date range:
  "What caused [TICKER] to go from $X to $Y between [date] and [date]?
   Classify as: social-media, earnings, short-squeeze, regulatory,
   dilution, or fraud."

SOURCES TO FEED:
  - SEC EDGAR filings (8-K, S-3 for offerings)
  - StockTwits / Reddit WallStreetBets trending mentions
  - Finviz news feed for the ticker
  - Short interest data (Ortex, S3 Partners)

AUTOMATED VERSION:
  1. Scrape news headlines for the ticker from last 5 days
  2. Count mention sources (Reddit vs SEC vs PR Newswire)
  3. Check for S-3/S-1 filings (offering = dilution catalyst)
  4. Check short interest % (>20% SI = squeeze candidate)
  5. Classify and flag in the scanner output
```

### Extracting Key Data from Earnings

```
For earnings-driven runs, pull:
  Revenue: actual vs estimate
  EPS: actual vs estimate
  Guidance: raised / maintained / lowered / none
  Surprise %: how much the beat/miss was

IF revenue beat > 30% AND guidance raised → Strong bounce candidate
IF revenue beat < 10% OR guidance lowered → Weak bounce, likely to fade
```

## Step 7: Daily Workflow

```
EVENING (after close):
  1. Run universe filter → list parabolic stocks ($0.50-$10, +100%/5d, 500k vol)
  2. Classify catalyst for each (AI-assisted)
  3. Eliminate fraud / dilution catalysts
  4. Set pre-market alerts for remaining names

MORNING (09:00-09:30):
  5. Check pre-market quotes — is the stock already gapping down hard?
  6. If gapping down > 15%: likely candidate for intraday panic
  7. Prepare order templates (no position yet — wait for entry signal)

ENTRY WINDOW (09:30-10:30):
  8. Watch 5-min chart for panic drop ≥ 30% from open
  9. Identify capitulation candle (range ≥ 10%, wick ≥ 5%, vol ≥ 2×)
  10. Wait for first green 5-min candle → entry
  11. Immediately set bracket: SL below panic low, TP1 at +15%, TP2 at +30%

MONITORING (10:30-15:30):
  12. If TP1 hits: sell 50%, move SL on remainder to breakeven
  13. DO NOT add to position or re-enter after exit
  14. If nothing triggers by 10:30 → skip. Setup is stale.

CLOSE (15:30):
  15. Close any remaining position at market
  16. Log trade in journal with all 5-min metrics
```

## Step 8: Trade Journal

```
date:             [YYYY-MM-DD]
ticker:           [SYMBOL]
run_up_pct:       [total % gain over prior 5 days]
max_single_day:   [largest single-day gain in the run-up]
catalyst_type:    [social-media / earnings / short-squeeze / regulatory / dilution]
open_price:       [today's open]
panic_low:        [lowest price in first 60 min]
panic_drop_pct:   [% from open to panic low]
capitulation:     [yes/no — did it meet all 3 criteria?]
entry_time:       [HH:MM]
entry_price:      [actual fill]
entry_spread:     [bid-ask % at entry]
tp1_hit:          [yes/no, at what time]
tp2_hit:          [yes/no, at what time]
exit_price:       [final fill]
exit_reason:      [TP1 / TP2 / SL / TIME-STOP]
actual_pnl:       [$]
slippage_total:   [$]
notes:            [what I'd do differently]
```

## Validation Requirements

```
BEFORE LIVE TRADING:
  1. Backtest 2020-2025 with 5-min data (Polygon, Alpaca)
  2. Minimum 50 qualifying trades in backtest
  3. Must include slippage model: 1.5% entry, 1% exit (minimum)
  4. Paper trade 20 trades with real-time 5-min data
  5. If paper TP1 hit rate < 45%: revisit parameters before going live

PARAMETER SENSITIVITY:
  Test panic drop threshold: 25%, 30%, 35%
  Test TP1: 10%, 15%, 20%
  Test SL: -8%, -10%, -12%
  If results collapse with ±5% changes: overfit
```

## Reference Documents

- **`references/capitulation-detection.md`** — Technical details on identifying
  capitulation candles, volume analysis, and false signals
- **`references/data-sources.md`** — Where to get 5-min OHLCV for OTC/small-caps
  (Polygon, Alpaca, FirstRate Data), cost comparison, API examples
