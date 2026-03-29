---
name: momentum-flow
description: >
  Institutional momentum strategy — follow the money into sector leaders and sympathy
  plays using relative strength, ETF flow analysis, and constructive base setups.
  Minervini/O'Neil-inspired trend following with progressive exposure. Use when:
  scanning for momentum leaders, identifying sector rotation, evaluating breakout
  setups, building a watchlist, sizing positions with progressive exposure, finding
  sympathy plays, analyzing ETF/sector flow, or asking "where is the money going?"
  Also trigger on: "institutional flow", "relative strength", "sector leaders",
  "momentum scan", "breakout setup", "inside day", "high volume close",
  "sympathy play", or "Minervini".
---

# Momentum Flow: Follow the Institutional Money

## The Edge (why this works)

Institutions (mutual funds, pension funds, hedge funds) manage trillions.
When they decide to buy a stock, they can't do it in one trade — they accumulate
over days and weeks. This creates a footprint: rising price on rising volume with
tight consolidations between pushes. Think of it like watching elephants walk
through snow — they leave tracks you can follow.

The edge is positioning yourself alongside that flow, not against it. You're not
predicting — you're detecting buying that's already happening and joining it.

**Why the edge persists:** Institutions buy in slow, multi-week programs.
Retail traders see the first move and think they missed it. But institutions
aren't done — they're still accumulating. The consolidation after the first
move IS the setup.

**When the edge disappears:** In bear markets and distribution phases, institutions
are selling into strength. The same patterns that signal accumulation can mask
distribution. The 50/200 MA filter exists to avoid this trap.

## Step 1: Universe Scan — Where Is the Money Going?

Run this every evening after market close. The goal: find the 10-20 strongest
names in the market right now.

### Relative Strength Ranking

```
RS Score = (Price / Price_90d_ago - 1) × 100

Example: Stock at $52, was $40 ninety days ago
RS = (52/40 - 1) × 100 = +30%

Rank all stocks by RS Score. Focus on the top 10%.
```

**Why 90 days?** Shorter (20-30 days) catches noise. Longer (180+ days) is too
slow — by the time a stock shows 6-month strength, the move is mature.
90 days balances early detection with confirmation.

### Hard Filters (all must pass)

```
REQUIRED:
  Price > 50-day MA                    # Institutions are buying, not selling
  Price > 200-day MA                   # Long-term trend is up
  50-day MA > 200-day MA               # Golden cross — trend structure confirmed
  Average daily turnover > 10 MSEK     # Institutions CAN buy here (≈$1M USD)
  RS Score top 20% of universe         # Relative strength — outperforming
  No earnings within 5 trading days    # Avoid vol events

PREFERRED:
  10-day MA > 20-day MA > 50-day MA    # All timeframes aligned (stacked MAs)
  ADX > 20                             # Trend has directional strength
  Volume trending up over 20 days      # Accumulation footprint
```

### ETF Sector Flow Analysis

ETFs reveal where institutions are allocating BEFORE individual stocks confirm:

```
SECTOR ETF WATCHLIST:

  Swedish (primary — Nasdaq Stockholm):
    OMXS30              — Broad market gate (replaces SPY)
    SX10 (Energy)       SX15 (Materials)       SX20 (Industrials)
    SX30 (Cons. Disc.)  SX35 (Cons. Staples)   SX40 (Healthcare)
    SX45 (Financials)   SX50 (IT/Technology)    SX55 (Telecom)
    SX60 (Utilities)    SX65 (Real Estate)

    NOTE: Swedish sector indices have fewer liquid ETFs than the US.
    Use OMXS sector indices (SX10-SX65) as flow proxies.
    For sub-sector analysis, group individual stocks manually
    (e.g., ERIC-B.ST + TELIA.ST = Swedish telecom group).

  US (for reference / dual-market scanning):
    XLK — Technology       XLF — Financials
    XLE — Energy           XLV — Healthcare
    XLI — Industrials      XLY — Consumer Discretionary
    SMH — Semiconductors   IBB — Biotech

FLOW SIGNAL:
  ETF/Index price > 50-day MA AND > 200-day MA → Sector is IN PLAY
  ETF/Index price < 50-day MA OR < 200-day MA  → Sector is OUT — skip all components

  Money flowing IN:  Index making new 20-day highs on expanding volume
  Money flowing OUT: Index breaking below 20-day MA on heavy volume
```

**The 50/200 MA rule is a hard gate.** If the sector ETF is below its 50-day
or 200-day MA, institutions are not buying there — they're selling. Don't fight
that flow regardless of how "cheap" individual stocks look. Cheap in a downtrend
means cheaper tomorrow.

→ Deep dive: `references/sector-flow-analysis.md`

## Step 2: Leader vs Sympathy — Group Dynamics

Stocks move in groups. When Nvidia surges, AMD and MRVL follow. When Tesla
runs, the EV chain (RIVN, LCID, LI) moves too. Understanding this hierarchy
is essential.

### Identifying the Leader

The leader is the stock that moves FIRST and MOST:

```
LEADER CRITERIA (must meet ≥3 of 5):
  1. Highest RS Score in its sector group
  2. First to break out of a base / consolidation
  3. Highest volume on breakout day relative to its own average
  4. Makes new 52-week or all-time highs
  5. Strongest earnings/revenue growth in the group
```

### Sympathy Play Framework

Sympathy plays are cheaper stocks in the same sector that follow the leader:

```
SYMPATHY CANDIDATE CRITERIA:
  Same sector or direct supply-chain relationship to leader
  Price > 50-day MA (must have positive trend structure)
  Has NOT yet broken out (still building base)
  Volume picking up — early accumulation signs
  Lower price / market cap than leader (perceived "catch-up" opportunity)

RANKING SYMPATHY CANDIDATES:
  A-tier: Same sub-sector, building tight base, volume rising
  B-tier: Related sector, base forming but less tight
  C-tier: Loose correlation, wide base — high risk of fake breakout
```

**The hierarchy matters for position sizing:**
- Leader: full position size (this is where conviction is highest)
- A-tier sympathy: 75% of leader position
- B-tier sympathy: 50% of leader position
- C-tier sympathy: skip or 25% maximum

### Detecting Group Rotation

```
ROTATION SIGNALS:
  Old leaders breaking 20-day MA on volume → Distribution
  New names making 52-week highs in different sector → Rotation target
  ETF money flow shifting (old sector ETF weakening, new strengthening)

RULE: When the leader breaks its 20-day MA on above-average volume,
the group trade is OVER. Don't look for new sympathy plays — look for
a new group entirely.
```

→ Deep dive: `references/group-dynamics.md`

## Step 3: Setup Recognition — 4 Constructive Patterns

All setups share one principle: the stock has moved up, paused to consolidate
(tight range, declining volume), and is about to move again. The consolidation
IS the setup — it's where institutions rest before resuming buying.

Think of it like a coiled spring: the tighter the coil (consolidation), the
more powerful the release (breakout).

### Setup A: Horizontal Level Break

```
PATTERN:
  Prior resistance level clearly defined (at least 2-3 touches)
  Stock pulls back but holds above the level (resistance → support)
  Volume dries up during consolidation
  Entry: break above the level on volume > 1.5× average

QUALITY CHECKS:
  ✓ Level is obvious — if you have to squint, it's not clear enough
  ✓ Multiple touches (2+) confirm the level matters
  ✓ Volume contracts during the base, expands on breakout
  ✗ Avoid: levels with only 1 touch (too weak)
```

### Setup B: Tight Consolidation at 10/20 MA

```
PATTERN:
  Stock trending up (above all MAs)
  Pulls back to 10-day or 20-day MA
  Daily range contracts (3+ days where range < 0.5× ATR(14))
  Stock "hugs" the MA — closes within 1-2% of it
  Entry: break above the consolidation range high

THIS IS THE HIGHEST-PROBABILITY SETUP.
Why: the MA acts as a magnet. Institutions use pullbacks to the 10/20 MA
as "reload zones" to add to positions. When the stock holds the MA and
tightens, it's a signal they're done accumulating at this level.

QUALITY CHECKS:
  ✓ Volume decreases during pullback (sellers exhausting)
  ✓ At least 3 days of tight closes near the MA
  ✓ Stock doesn't violate the 20-day MA by more than 2%
  ✗ Avoid: deep pullbacks past the 50-day MA (trend weakening)
```

### Setup C: Inside Day

```
PATTERN:
  Day's High < Yesterday's High AND Day's Low > Yesterday's Low
  The entire day's range is "inside" the prior day
  Signals: volatility compression, decision point coming

ENTRY: Break above the inside day's high (bullish resolution)
STOP: Below the inside day's low

QUALITY MULTIPLIERS:
  Inside day at the 10/20 MA → strongest (Setup B + C combined)
  Inside day after a gap-up → strong (consolidating new level)
  Inside day in the middle of nowhere → weakest (could break either way)
```

### Setup D: Delayed Breakout (High-Volume Close)

```
PATTERN:
  Stock gaps up or surges on very high volume (>2× average)
  Often news-driven (earnings beat, upgrade, product launch)
  DON'T chase on the gap day — wait.
  Mark the CLOSE price of the big-volume day
  Entry: when stock breaks above that closing price on a subsequent day

WHY THIS WORKS:
  The gap day attracts emotional buyers. Many get shaken out in the
  next few days of pullback/consolidation. When the stock RECLAIMS
  the high-volume close, it means the selling from latecomers is done
  and fresh demand is entering.

TIMELINE: Entry typically 2-7 days after the high-volume event.
If it takes >10 days, the setup is stale — skip.
```

## Step 4: Entry and Stop Rules

### Entry

```
TRIGGER: Price breaks above setup's trigger level (prior high, MA, level)
ORDER TYPE: Buy-stop order at trigger + $0.02-0.05 buffer
  (Ensures you only enter if the breakout actually happens)

CONFIRMATION: Volume on entry day should be > 1.5× 20-day average
  for Setup A (horizontal level breaks need strong participation).
  For Setups B/C/D: > 1.2× 20-day average is sufficient.
  If volume is below average: breakout is suspect — reduce size by 50%

TIMING (Nasdaq Stockholm):
  First 30 min after open (09:00-09:30 CET) breakouts are noisier.
  Best entries are 09:30-15:00 CET when institutional algos are active.
  Avoid last 30 min (17:00-17:30) — closing auction distorts price.
  US market opens 15:30 CET — Swedish stocks with US exposure may
  see secondary moves after US open. Factor this into alert timing.
```

### Stop Loss

```
PRIMARY: Below prior day's low
  Simple, mechanical, respects structure.

ALTERNATIVE: Below the pivot (recent swing low in the consolidation)
  Use when prior day's low is too tight (< 1 ATR from entry).

MAXIMUM STOP: 7-8% below entry price
  If the required stop is >8% away, the setup is too extended — skip.

RULE: Stop is set BEFORE entry. If you can't define the stop,
  you can't define the risk, and you can't size the position.
```

### Position Sizing

```
Risk per trade: fixed percentage of equity

  CONSERVATIVE: 0.5% risk per trade
  STANDARD:     1.0% risk per trade
  AGGRESSIVE:   1.5% risk per trade (only when on a winning streak)

Position size = (Account × Risk%) / (Entry - Stop)

Example: $50k account, 1% risk, entry $28.50, stop $27.00
  Size = ($50,000 × 0.01) / ($28.50 - $27.00)
  Size = $500 / $1.50 = 333 shares
  Dollar exposure = $9,500 (19% of account — normal for a tight setup)
```

## Step 5: Progressive Exposure (Minervini Model)

Don't go from 100% cash to fully invested in one day. Build exposure gradually
based on results. Think of it like a pilot testing conditions before committing
to full throttle.

```
PHASE 1: PROBING (0-25% invested)
  Start with 2-3 small positions (50% of normal size)
  Purpose: test the current market environment
  If these work → proceed to Phase 2
  If 2 of 3 stop out → STOP. Market isn't ready. Return to cash.

PHASE 2: BUILDING (25-60% invested)
  Add positions at normal size
  Only add when existing positions are profitable
  Each new position requires: setup A/B/C/D + leader or A-sympathy

PHASE 3: PRESSING (60-90% invested)
  Add to winners (pyramid into existing positions)
  Pyramids: add 50% of original size on new breakout from consolidation
  The entry must be higher than the original entry (adding into strength)
  Move stop on original position to breakeven before adding

PHASE 4: PROTECTING (holding / trailing)
  No new positions. Trail stops on all positions.
  When first position hits stop → reduce exposure by selling weakest
  When 50% of positions have hit stops → back to Phase 1

RULES:
  - Never move from Phase 1 to Phase 3 without Phase 2
  - Never add to a losing position (pyramiding is INTO winners only)
  - If first 2 trades are losers → back to cash, wait 1 week
```

## Step 6: Exit Rules

### Profit Exits (Trimming)

```
ADR (Average Daily Range) = SMA(High - Low, 20 days)
  Example: stock with daily ranges of 2.50, 3.10, 2.80... over 20 days
  ADR = average of those ranges = ~2.80 SEK

ATR (Average True Range) = SMA(max(H-L, |H-Cprev|, |L-Cprev|), 14 days)
  ATR accounts for gaps; ADR does not. Use ATR for stop placement,
  ADR for extension measurement.

TRIM 25% when stock is extended > 5× ADR from 10-day MA
TRIM 50% when stock is extended > 7× ADR from 50-day MA

WHY: Extensions from the MA measure "stretch." When a stock runs too far
too fast, it snaps back to the MA like a rubber band. Take profits before
the snap.
```

### Trailing Stops

```
Match your trailing MA to your entry setup:

  Entered at 10-day MA setup → Trail with 10-day MA
    (Aggressive trail. Fast exit. For short-term trades.)

  Entered at 20-day MA setup → Trail with 20-day MA
    (Standard trail. Holds through normal pullbacks.)

  Entered at 50-day MA setup → Trail with 50-day MA
    (Loose trail. For larger trend moves. More drawdown tolerance.)

EXIT TRIGGER: Close below the trailing MA for 2 consecutive days.
  Single-day violation is noise. Two days means the trend at that timeframe
  is broken.
```

### Earnings Handling

```
IF holding through earnings AND stock gaps UP:
  Keep position if stock holds above 50-day MA after earnings
  Move stop to low of earnings day
  Let the winner run — institutional re-rating in progress

IF holding through earnings AND stock gaps DOWN:
  Sell immediately if close below 50-day MA
  If still above 50-day MA: hold with tight stop at earnings-day low

OPTION: Sell 50% before earnings, let 50% ride. Reduces risk, keeps exposure.
```

## Step 7: Daily Workflow

```
EVENING SCAN (after close):
  1. Run RS ranking → top 20% list
  2. Check sector ETFs → which are above 50/200 MA?
  3. Cross-reference → which top-RS stocks are in strong sectors?
  4. Scan for setups A/B/C/D on the filtered list
  5. Set alerts for tomorrow's potential triggers
  6. Update watchlist (add new setups, remove broken ones)

PRE-MARKET (30 min before open):
  7. Check overnight news for watchlist names
  8. Check pre-market gaps → any watchlist names gapping up?
  9. Confirm orders (buy-stops at trigger levels)

DURING MARKET:
  10. Monitor alerts only — do NOT watch charts all day
  11. When alert triggers: verify volume confirms, execute
  12. Review existing positions: any stops hit? Any exits needed?

POST-MARKET (15 min):
  13. Log trades in journal
  14. Review: did I follow the plan? Any emotional decisions?
  15. Update exposure phase (1/2/3/4)
```

## Step 8: Trade Journal

```
date:             [YYYY-MM-DD]
ticker:           [SYMBOL]
sector:           [Sector ETF / group]
role:             [leader / A-sympathy / B-sympathy]
setup_type:       [A-level / B-MA-consolidation / C-inside-day / D-delayed]
entry_trigger:    [what triggered entry — e.g., "break above $28.50"]
entry_price:      [actual fill]
stop_price:       [initial stop level]
risk_pct:         [% of account risked]
position_pct:     [% of account invested]
exposure_phase:   [1-probe / 2-build / 3-press / 4-protect]
exit_price:       [fill]
exit_reason:      [trailing-stop / trim / earnings / time]
r_multiple:       [profit ÷ initial risk]
group_status:     [leader still strong? sector ETF still above MAs?]
notes:            [what I learned]
```

## When NOT To Trade (Market Environment Filter)

```
STOP SIGNALS (go to cash):
  OMXS30 below 200-day MA → No new longs. Protect existing.
  >60% of SX sector indices below 50-day MA → Broad distribution
  Your first 2-3 probe trades both stop out → Market not confirming
  VIX > 30 (US) or VSTOXX > 30 (EU) → Panic environment, setups fail

  NOTE: Even if OMXS30 is above MAs, check SPY/S&P 500 too.
  Swedish large caps (ERIC-B, VOLV-B, ABB) correlate heavily with
  US markets. A US sell-off at 15:30 CET can erase Swedish gains.

RESTART SIGNALS:
  OMXS30 reclaims 50-day MA on volume
  >50% of SX sector indices back above 50-day MA
  Probe trades start working (2 of 3 profitable)
```

## Reference Documents

- **`references/sector-flow-analysis.md`** — ETF mapping, flow detection, rotation signals
- **`references/group-dynamics.md`** — Leader identification, sympathy plays, AI screening ideas
- **`references/progressive-exposure-rules.md`** — Detailed Minervini-style position building
