# Trade Management for Swing Trading

Trade management is what happens between entry and exit. It is arguably the most skill-intensive phase of a trade, where discipline, adaptability, and rules-based thinking determine whether a good setup becomes a profitable outcome. The best entry in the world is worthless if the trade is managed poorly. This document provides a complete framework for managing open swing trades from the moment of entry to final exit.

> **Cross-references:** This document builds on the position sizing and stop-loss foundations in [05-risk-management.md](05-risk-management.md), the strategy-specific exit rules in [04-swing-trading-strategies.md](04-swing-trading-strategies.md), the technical indicators used for trailing decisions in [02-technical-indicators.md](02-technical-indicators.md), and the market regime awareness covered in [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md). Alerting and notification infrastructure is covered in [06-apis-and-technology.md](06-apis-and-technology.md).

---

## Table of Contents

1. [Managing Open Positions](#1-managing-open-positions)
2. [Scaling In and Out](#2-scaling-in-and-out)
3. [Adjusting Stop-Losses](#3-adjusting-stop-losses)
4. [Handling Gaps](#4-handling-gaps)
5. [News and Events During a Trade](#5-news-and-events-during-a-trade)
6. [Trade Adjustments](#6-trade-adjustments)
7. [Exit Strategies in Detail](#7-exit-strategies-in-detail)
8. [Position Correlation Management](#8-position-correlation-management)

---

## 1. Managing Open Positions

Once a trade is entered, the goal shifts from finding setups to protecting capital and maximizing the move. The single biggest mistake swing traders make during this phase is overtrading -- constantly adjusting, second-guessing, and micromanaging positions that need time to work.

### 1.1 Monitoring Active Trades Without Overtrading

**The core principle:** A swing trade is designed to capture a multi-day move. Checking it every 15 minutes adds anxiety, not alpha.

**What to monitor and how often:**

| Data Point | Frequency | Reason |
|---|---|---|
| Price relative to stop-loss | 2-3 times daily (open, midday, close) | Ensures protective exit is still valid |
| Daily closing price | Once at market close | The only price that matters for swing trading |
| Volume | Once at close | Confirms or warns about the trend |
| Broader market regime | Once daily (morning) | Regime changes affect all positions (see [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md)) |
| Sector performance | Once daily (morning) | Sector rotation can invalidate a thesis |
| News headlines for held tickers | Morning pre-market, after close | Unexpected catalysts require assessment |

**What NOT to do:**
- Do not watch the intraday tick-by-tick price action of a swing trade
- Do not recalculate targets or stops mid-day unless a major event occurs
- Do not check your P&L intraday -- it creates emotional reactions to noise
- Do not place or adjust orders during the first 15 minutes of the trading session (volatility noise)

### 1.2 When to Check Positions: Scheduled vs. Reactive

**Scheduled monitoring (the default):**

A disciplined swing trader follows a routine:

```
DAILY TRADE MANAGEMENT ROUTINE

Pre-market (30 minutes before open):
  [ ] Check overnight futures for gap risk
  [ ] Scan news for held tickers
  [ ] Review economic calendar for the day
  [ ] Note any earnings reports in your sector

Market open (9:30-9:45 AM ET):
  [ ] Observe opening prices relative to stops/targets
  [ ] Do NOT act on the open unless a gap scenario triggers (see Section 4)

Midday (12:00-1:00 PM ET):
  [ ] Quick check: any position within 1% of stop or target?
  [ ] If yes, review whether to tighten or hold

Market close (3:45-4:00 PM ET):
  [ ] Review daily candles for all held positions
  [ ] Adjust trailing stops based on daily close (see Section 3)
  [ ] Log observations in trade journal

Post-market (after 4:00 PM ET):
  [ ] Check for after-hours earnings or news
  [ ] Prepare orders for next day if needed
```

**Reactive monitoring (exceptions only):**

Switch to active monitoring only when:
- A position has gapped significantly at the open
- A major news event hits during market hours (FOMC, unexpected earnings, geopolitical)
- A position is within 0.5% of a key target or stop level
- The broader market drops more than 2% intraday (circuit breaker territory)
- Your sector is leading or lagging by more than 2 standard deviations

### 1.3 Using Alerts Instead of Constant Monitoring

Price alerts are the swing trader's best friend. They allow you to step away from the screen while staying informed about meaningful price action.

**Essential alerts to set for every position:**

| Alert Type | Trigger Level | Purpose |
|---|---|---|
| Stop proximity | Price within 1-2% of stop-loss | Prepare for potential exit |
| Target proximity | Price within 1-2% of first target | Prepare for partial or full exit |
| Breakeven zone | Price returns to entry after being profitable | Assess whether to tighten stop |
| Volume spike | Volume exceeds 2x 20-day average | Unusual activity may require attention |
| Key moving average | Price touches 20 EMA or 50 SMA | Dynamic support/resistance test |
| Gap alert | Pre-market price more than 2% from prior close | Gap scenario requires assessment |

**Alert infrastructure options (see [06-apis-and-technology.md](06-apis-and-technology.md) for implementation):**
- Broker platform alerts (most reliable, direct to phone)
- TradingView alerts (flexible conditions, webhook support)
- Custom scripts using market data APIs (most customizable)
- SMS/email alerts from screening platforms

**The golden rule of alerts:** Set them and walk away. If your alerts are properly configured, there is no reason to stare at a chart. The alert will tell you when you need to pay attention.

---

## 2. Scaling In and Out

Scaling is the art of adjusting position size during a trade. Done correctly, it increases average profit on winners and reduces average loss on losers. Done incorrectly, it amplifies losses and creates emotional chaos.

### 2.1 Pyramiding Into Winning Positions (Adding to Winners)

Pyramiding means adding to a position that is already profitable. The logic is simple: the trade is confirming your thesis, so you increase exposure while the market is proving you right.

**The pyramid structure:**

```
Entry 1 (initial):  50% of planned full position
Entry 2 (add #1):   30% of planned full position  (after first confirmation)
Entry 3 (add #2):   20% of planned full position  (after second confirmation)
```

Each addition is smaller than the previous one. This is critical because it keeps the average cost favorable and limits risk if the trade reverses after an add.

**Example -- pyramiding a breakout trade:**

```
Stock XYZ breaks out above $50 resistance on volume:
  Entry 1: Buy 500 shares at $50.50 (initial position)
  Stop: $48.00 (below breakout level)
  Risk: 500 x $2.50 = $1,250

Price moves to $53.00 and pulls back to $51.50 on light volume:
  Entry 2: Buy 300 shares at $51.50 (pullback to breakout level)
  Move stop to $49.50 for entire position
  New risk: 800 shares x avg stop distance = manageable

Price moves to $56.00, consolidates, then breaks higher:
  Entry 3: Buy 200 shares at $56.50 (breakout from consolidation)
  Move stop to $54.00 (below consolidation)
  Total: 1,000 shares, average cost ~$52.15
```

### 2.2 Rules for Adding to a Position

Never add to a position on impulse. Every add must meet strict criteria:

**Mandatory conditions before adding:**

1. **The original position must be profitable.** Never add to a losing trade. This is the most important rule of pyramiding.
2. **Technical confirmation must exist.** The add should coincide with a pullback to support, a breakout from consolidation, or a moving average bounce -- not random price movement.
3. **Volume must confirm.** The move supporting the add should be on adequate volume (above 20-day average on up days, below average on pullback days).
4. **The stop for the entire position must be defined before adding.** Calculate total risk across all entries before clicking buy.
5. **Each add must be smaller than the previous entry.** The pyramid narrows upward, never widens.
6. **Total position risk must stay within your per-trade limit.** If adding would push total position risk above 2% of account equity, do not add. (See position sizing rules in [05-risk-management.md](05-risk-management.md).)

**Pyramiding decision checklist:**

```
BEFORE ADDING TO A WINNER:

[ ] Current position is profitable (price above average entry for longs)
[ ] Technical setup confirms continuation (pullback to support, consolidation break)
[ ] Volume supports the add (not adding into a vacuum)
[ ] Stop-loss for full position is defined
[ ] Total position risk (all entries) stays within per-trade limit (1-2% of equity)
[ ] Add size is smaller than previous entry
[ ] Market regime still supports the trade direction
[ ] No major catalyst (earnings, FOMC) within 2 trading days

If ANY box is unchecked: DO NOT ADD.
```

### 2.3 Scaling Out of Winners

Scaling out means selling portions of a winning position at different price levels. This approach balances the psychological need to lock in profits with the goal of letting winners run.

**The standard 1/3 scaling plan:**

| Tranche | Trigger | Action |
|---|---|---|
| First 1/3 | Price reaches 1R target (risk/reward 1:1) | Sell 1/3, move stop to breakeven on remainder |
| Second 1/3 | Price reaches 2R target (risk/reward 1:2) | Sell 1/3, tighten trailing stop on remainder |
| Final 1/3 | Trailing stop is hit or 3R+ target reached | Exit final portion |

**Example:**

```
Entry: $50.00, Stop: $47.00, Risk (1R) = $3.00

First 1/3 exit at $53.00 (1R profit):
  - Lock in $3.00/share on 1/3 of position
  - Move stop to $50.00 (breakeven) on remaining 2/3
  - Trade is now "risk-free" on paper

Second 1/3 exit at $56.00 (2R profit):
  - Lock in $6.00/share on another 1/3
  - Tighten trailing stop to $54.00 (1.5x ATR trail) on final 1/3
  - Significant profit already banked

Final 1/3 exits when trailing stop hits:
  - If stock runs to $62.00 and trailing stop triggers at $59.00:
    Final profit = $9.00/share on last 1/3
  - If stock reverses after $56.00 and hits $54.00 trail:
    Final profit = $4.00/share on last 1/3
```

**Alternative scaling plans:**

| Plan | Best For | Approach |
|---|---|---|
| 1/3, 1/3, 1/3 | General purpose | Standard plan above |
| 1/2, 1/2 | Strong trends, simpler management | Half at first target, half trailing |
| 1/4, 1/4, 1/4, 1/4 | Large positions, volatile stocks | More granular profit-taking |
| All out | Mean-reversion trades | Single target, single exit (see [04-swing-trading-strategies.md](04-swing-trading-strategies.md)) |

**When to use all-out exits instead of scaling:**
- Mean-reversion trades where the edge evaporates quickly
- Small position sizes where scaling creates odd lots
- When the risk/reward was tight from the start (1:1.5 or less)
- Trades driven by a single catalyst with a known expiry

### 2.4 When NOT to Scale In

Scaling in (pyramiding) is not always appropriate. Avoid it in these situations:

- **Counter-trend trades.** Adding to a trade against the primary trend compounds risk.
- **Low-volume environments.** Adding into thin volume means poor fills on exit if the trade reverses.
- **Near earnings or major catalysts.** Binary events make the add a gamble, not a thesis extension.
- **When the initial stop has already been tightened significantly.** If the stop is close, an add increases the chance of the entire position being stopped out.
- **When portfolio heat is already elevated.** Adding to one position while other positions are also at risk creates concentration risk (see [05-risk-management.md](05-risk-management.md), Section 1.5 on portfolio heat).
- **Choppy or sideways market regimes.** Pyramiding works in trends, not in ranges (see [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md)).

---

## 3. Adjusting Stop-Losses

Stop-loss management during a trade is where risk management theory meets real-time decision-making. The overarching principle: stops can only move in one direction -- closer to current price (protecting more profit or reducing risk). Never widen a stop.

### 3.1 Moving Stops to Breakeven

Moving a stop to the entry price ("breakeven") eliminates risk on the trade. It is one of the most psychologically satisfying actions a trader can take, but timing matters.

**When to move to breakeven:**

| Trigger | Reasoning |
|---|---|
| Price reaches 1R in profit | The trade has proven its thesis; protect the entry |
| First partial exit taken | After selling 1/3, breakeven on remainder is standard |
| End of Day 2 in profit | If still profitable after two full sessions, protect the position |
| Price confirms support above entry | A higher low forms above your entry level |

**When NOT to move to breakeven too early:**

- The stock is still within normal ATR range of entry. Moving to breakeven when price is only 0.5 ATR above entry virtually guarantees being stopped out by noise.
- Strong trend trades that need room to breathe. In a well-structured uptrend, a pullback to near your entry is normal and healthy.

**The breakeven trap:** Moving to breakeven too aggressively is one of the most common trade management errors. It feels safe but it often results in being stopped out of trades that go on to hit their targets. The solution: use ATR as a guide. Do not move to breakeven until the trade is at least 1.5x ATR in profit.

**Rule of thumb:**

```
Minimum profit before breakeven stop = 1.5 x ATR(14)

Example:
  Entry: $50.00
  ATR(14): $2.00
  Minimum price before moving to breakeven: $50.00 + $3.00 = $53.00
```

### 3.2 Trailing Stop Techniques During a Trade

Trailing stops lock in progressively more profit as the trade moves favorably. The method chosen should match the character of the trade.

> **Foundation:** The trailing stop types below build on the formulas and concepts in [05-risk-management.md](05-risk-management.md), Section 2.4. This section focuses on when and how to apply each method during active trade management.

#### ATR-Based Trailing Stops

The most versatile and widely used trailing stop for swing trades. It adapts automatically to the stock's volatility.

**Implementation:**

```
Trailing Stop (long) = Highest Close since entry - (ATR(14) x Multiplier)

Multiplier selection:
  Aggressive (capture smaller moves): 1.5x ATR
  Standard (balanced):               2.0x ATR
  Conservative (let winners run):    2.5-3.0x ATR
```

**Daily recalculation process:**

```
Each day at market close:
  1. Record the closing price
  2. Update the highest close if today's close is a new high
  3. Calculate new trailing stop = highest close - (ATR x multiplier)
  4. If new stop > current stop: MOVE stop up to new level
  5. If new stop < current stop: KEEP current stop (never move backward)
  6. Recalculate ATR using latest 14 periods (ATR itself changes over time)
```

**Tightening the ATR trail as the trade matures:**

| Trade Stage | ATR Multiplier | Logic |
|---|---|---|
| Early (Day 1-3) | 2.5x | Give the trade room to develop |
| Developing (Day 4-7) | 2.0x | Trade should be trending by now |
| Extended (Day 8+) | 1.5x | Protect profits; the move may be exhausting |
| After 3R+ profit | 1.0x | Very tight; willing to be stopped out of a big winner |

#### Trendline-Based Trailing Stops

Using the prevailing trendline as a trailing stop is effective in well-defined trends with clear swing lows.

**How to apply:**

1. Connect at least two swing lows (for a long trade) to form an ascending trendline
2. Place the trailing stop 1-2% below the trendline (or 0.5x ATR below it)
3. As the trendline rises, the stop rises with it
4. A close below the trendline triggers the exit

**Advantages:**
- Respects the actual trend structure rather than a fixed formula
- Allows the trade to breathe within the trend channel
- Provides natural exit when the trend breaks

**Disadvantages:**
- Requires judgment to draw the trendline correctly
- Can be hard to automate without pattern recognition
- Inner trendlines vs. outer trendlines produce different results

#### Moving Average Trailing Stops

Use a moving average as a dynamic trailing stop:

| Moving Average | Best For | Exit Rule |
|---|---|---|
| 10 EMA | Aggressive momentum trades | Close below 10 EMA |
| 20 EMA | Standard swing trades | Close below 20 EMA for 2 consecutive days |
| 50 SMA | Extended swings / position trades | Close below 50 SMA |

**Hybrid approach (recommended):** Use ATR-based trailing as the primary stop, but also monitor the position relative to the 20 EMA. If both the ATR trail and the 20 EMA are violated, exit with conviction. If only one is violated, assess before acting.

### 3.3 The Cardinal Rule: Never Widen a Stop

**Never move a stop further from the current price (away from entry on a losing trade, or away from profit on a winning trade).**

This rule has no exceptions. The temptation to widen a stop comes from:

- "It's just a little more room, it'll come back" (hope)
- "The support is slightly lower than I thought" (rationalization)
- "The overall market dipped, it's not the stock's fault" (excuse)

If the original stop was placed correctly using ATR, support/resistance, or chart structure (as described in [05-risk-management.md](05-risk-management.md)), then the stop represents the point where the trade thesis is invalidated. Moving it wider does not change the thesis -- it just increases the loss.

**What to do instead of widening:**
- Accept the stop and exit
- If you believe in the setup, re-enter as a new trade with a new risk calculation
- Re-evaluate your initial stop placement methodology to prevent the issue on future trades

---

## 4. Handling Gaps

Gaps are a defining feature of swing trading. Because positions are held overnight (and often over weekends), gap risk is unavoidable. Managing gaps properly separates experienced swing traders from beginners.

### 4.1 Overnight Gap Analysis

**Types of gaps and their implications:**

| Gap Type | Characteristics | Typical Action |
|---|---|---|
| Breakaway gap | Large gap on heavy volume, breaks through support/resistance | Often continues; hold through or add |
| Continuation gap | Gap in the direction of the trend mid-move | Usually fills partially then resumes; hold |
| Exhaustion gap | Large gap after an extended move, often on climactic volume | Potential reversal; tighten stop or exit |
| Common gap | Small gap in a range-bound market | Usually fills quickly; ignore |

**Pre-market gap assessment checklist:**

```
WHEN YOUR STOCK GAPS OVERNIGHT:

1. Determine gap size:
   [ ] < 1%: Likely noise. No action needed.
   [ ] 1-3%: Moderate. Assess direction and volume.
   [ ] 3-5%: Significant. Requires immediate assessment.
   [ ] > 5%: Major event. Shift to reactive monitoring.

2. Identify the cause:
   [ ] Earnings (see Section 4.5)
   [ ] Sector-wide news
   [ ] Company-specific news (upgrade/downgrade, FDA, M&A)
   [ ] Macro event (FOMC, economic data, geopolitical)
   [ ] No identifiable cause (pre-market order flow)

3. Check volume:
   [ ] Pre-market volume high: gap is real, likely to hold
   [ ] Pre-market volume low: gap may fill
```

### 4.2 Gap Up Through Target

Your stock gaps up past your profit target. This is a good problem to have, but requires discipline.

**Decision tree:**

```
Stock gaps up through your target:
  |
  |-- Gap is < 2% above target:
  |     |-- Sell at open (take the gift)
  |     |-- The target was set for a reason; honor it
  |
  |-- Gap is 2-5% above target:
  |     |-- Sell 1/2 at open (lock in profit above target)
  |     |-- Hold 1/2 with tight trailing stop (1.5x ATR)
  |     |-- If volume is 3x+ average: potential breakaway gap, hold more
  |
  |-- Gap is > 5% above target:
  |     |-- Is there a fundamental reason (earnings beat, M&A)?
  |     |     |-- YES: Hold with trailing stop, reassess thesis
  |     |     |-- NO: Sell 2/3 at open, trail 1/3
  |     |
  |     |-- Check if this is an exhaustion gap:
  |           |-- After extended move + climactic volume = likely exhaustion
  |           |-- Sell all at open
```

**Key principle:** When in doubt, take partial profits on a gap up. You can always re-enter. You cannot un-sell a gap that reverses.

### 4.3 Gap Down Through Stop

This is the nightmare scenario. Your stock gaps below your stop-loss level, and your order fills at a worse price than expected (or the stop was a stop-limit and did not fill at all).

**Immediate response protocol:**

```
Stock gaps down through your stop:
  |
  |-- Stop-market order already in place:
  |     |-- It will fill near the open (with slippage)
  |     |-- Accept the loss; this is why we position size correctly
  |     |-- Do NOT cancel the stop and "wait for a bounce"
  |
  |-- Stop-limit order did not fill:
  |     |-- Switch to market order immediately at the open
  |     |-- Holding and hoping after a gap through your stop is the path to large losses
  |
  |-- No stop was in place (mental stop):
  |     |-- Exit via market order at the open
  |     |-- This is a lesson: always use hard stops for overnight holds
  |
  |-- The gap creates a loss > 2x your planned risk:
  |     |-- Still exit. The position size was calculated to absorb this
  |     |-- Review whether gap risk was accounted for in position sizing
  |     |-- Consider reducing overnight exposure in the future
```

**Damage control after a gap-down exit:**
1. Log the trade and the gap in your journal
2. Do NOT revenge trade to "make it back"
3. Reduce position sizes for the next 2-3 trades if the loss was emotionally significant
4. Review whether the gap was foreseeable (earnings, catalyst, sector weakness)

### 4.4 Weekend Gap Risk Management

Weekend gaps introduce an additional 64 hours (Friday close to Monday open) of uncontrolled risk. News events, geopolitical developments, and global market moves can all trigger Monday gaps.

**Friday decision framework:**

```
END-OF-WEEK POSITION ASSESSMENT:

For each open position, evaluate:

1. How profitable is the position?
   [ ] Deeply profitable (> 2R): Hold through weekend with trailing stop
   [ ] Moderately profitable (1-2R): Consider taking partial profits Friday
   [ ] Near breakeven: Consider closing to eliminate weekend risk
   [ ] Underwater: Close. Do not carry losing positions over the weekend

2. Are there weekend risk events?
   [ ] Geopolitical tensions elevated
   [ ] Economic data releases Monday morning
   [ ] Fed speakers over the weekend
   [ ] Company-specific news expected
   If YES to any: reduce exposure by 25-50% on Friday

3. Market regime check:
   [ ] High-volatility environment (VIX > 25): reduce weekend exposure
   [ ] Low-volatility bull market: more comfortable holding
   [ ] Uncertain/choppy: lean toward cash
```

**Position size adjustment for weekend holds:**
- Some traders reduce position size by 25-50% on Friday specifically to account for weekend gap risk
- Another approach: take partial profits on winners Friday afternoon, re-enter Monday if the trade remains valid
- This is a personal risk tolerance decision, but the key is to make it deliberately, not passively

### 4.5 Earnings Gap Strategies

Earnings announcements create the largest and most unpredictable gaps. The consensus among experienced swing traders is clear: **do not hold through earnings unless you have a specific, well-defined edge for doing so.**

**The case for exiting before earnings:**

- Earnings gaps of 5-20% are common; 20%+ gaps occur regularly
- The direction is essentially a coin flip, regardless of analyst expectations
- A single earnings gap can erase weeks of gains from the position
- Position sizing cannot fully protect against a 15% adverse gap
- The risk/reward of holding through earnings is poor relative to the many other opportunities available

**Rules for managing around earnings:**

| Situation | Recommended Action |
|---|---|
| Long position, earnings in 1-2 days | Exit before earnings or reduce to 25% position |
| Earnings of a major sector peer | Assess potential sympathy move; consider reducing exposure |
| Already took 2R+ profit | Acceptable to hold a small "house money" position through earnings |
| Using options for protection | Buying a put to hedge can make holding worthwhile (advanced) |

**If you choose to hold through earnings (advanced only):**
1. Reduce position to 1/4 or less of normal size
2. Accept the full position value as potential risk
3. Define exit rules for both gap-up and gap-down scenarios before the report
4. Consider hedging with a protective put (cost of the put is the "insurance premium")

> **See also:** Gap trading strategies for entering after earnings gaps in [04-swing-trading-strategies.md](04-swing-trading-strategies.md), Section 4.4.

---

## 5. News and Events During a Trade

Markets are driven by information flow. Even the best technical setup can be invalidated by a news event. The key is having a framework for assessing events and deciding when to act versus when to hold steady.

### 5.1 How to Handle Unexpected News

**The 3-step news assessment framework:**

```
Step 1: CLASSIFY the news
  - Is it company-specific, sector-wide, or macro?
  - Is it material (changes fundamentals) or sentiment (changes mood)?
  - Is it confirmed or rumor?

Step 2: QUANTIFY the impact
  - How much has price moved on the news?
  - How does the move compare to 1 ATR? (< 1 ATR = noise, > 2 ATR = significant)
  - Has volume spiked? (> 3x average = market agrees this matters)

Step 3: DECIDE
  - Does this news invalidate the original trade thesis?
    YES -> Exit immediately regardless of stop level
    NO  -> Hold the position, keep existing stop
  - Is the news ambiguous?
    -> Reduce position size by 50% and reassess at close
```

**Types of news and typical responses:**

| News Type | Impact Assessment | Action |
|---|---|---|
| Analyst upgrade/downgrade | Usually 2-5% move, fades within days | Hold if in your direction; exit if against |
| FDA approval/rejection | Binary, 10-50% moves | Should have exited before if foreseeable |
| M&A announcement | Target usually gaps 20-40% to deal price | Take the windfall and exit |
| Lawsuit/investigation | Varies widely, often oversold initially | Exit; uncertainty kills swing trades |
| Product recall/safety issue | Sector-dependent, can be severe | Exit immediately; thesis is broken |
| Guidance revision | 3-10% typical move | Reassess fundamental thesis |

### 5.2 FOMC During a Trade

Federal Reserve meetings and statements are scheduled events that every swing trader should have on their calendar. FOMC decisions can move the entire market 2-5% in either direction.

**FOMC trade management protocol:**

```
BEFORE FOMC (day of or day before):
  [ ] Identify all open positions with beta > 1.0 to the market
  [ ] Consider reducing aggregate exposure by 25-50%
  [ ] Tighten trailing stops on profitable positions
  [ ] Do NOT open new positions within 24 hours before the announcement

DURING FOMC ANNOUNCEMENT (2:00 PM ET):
  [ ] Do NOT trade during the first 30 minutes after the statement
  [ ] Initial reaction is often reversed (the "FOMC whipsaw")
  [ ] Wait for the press conference to end before making decisions

AFTER FOMC (next trading day):
  [ ] Assess the market's digested reaction
  [ ] The next-day response is more reliable than the same-day reaction
  [ ] Re-enter or add to positions if the trend resumes
```

### 5.3 Earnings Announcement While Holding

If you find yourself holding a position into an earnings announcement (either because you chose to or because the date moved/you missed it):

1. **If you discover earnings are tomorrow and you are profitable:** Exit today. The profit is real; the earnings outcome is a gamble.
2. **If you discover earnings are tomorrow and you are at a loss:** Exit today. Adding earnings risk to an already-losing trade is compounding mistakes.
3. **If earnings were just reported after hours and your stock is moving:** Wait for the regular session open. After-hours prices are unreliable due to low liquidity.

### 5.4 Sector News Impact Assessment

A news event affecting a sector peer (but not your specific holding) still requires assessment:

```
SECTOR NEWS IMPACT ASSESSMENT:

1. How correlated is your stock to the affected company?
   - Same sub-sector, direct competitor: HIGH correlation, likely to move in sympathy
   - Same broad sector, different business: MODERATE correlation, may move
   - Different sector entirely: LOW correlation, probably noise

2. Is the news company-specific or industry-wide?
   - Company-specific (accounting fraud, product failure): Low spillover risk
   - Industry-wide (regulation change, commodity price shock): High spillover risk

3. What is the market's initial reaction in your stock?
   - Moving in sympathy: The market sees a connection; respect it
   - Not moving: The market does not see a connection; hold your position
```

### 5.5 When to Override Your Plan vs. Stick to It

This is one of the hardest decisions in trade management. The default should always be to stick to the plan. Overriding the plan should be the rare exception, not the rule.

**When to STICK to the plan (almost always):**
- Price action is noisy but within normal ATR range
- You "feel" like the trade is not working but it has not hit your stop
- A talking head on financial media says something scary
- A single red candle appears in an uptrend
- You are up nicely and "just want to lock it in" before the target

**When to OVERRIDE the plan (rare exceptions):**
- A material, fundamental change invalidates the thesis (e.g., the company you are long announces a major downward guidance revision)
- The broader market enters a crash-like decline (circuit breakers triggered, VIX spikes above 40)
- You discover you made an error in your analysis (wrong support level, incorrect earnings date)
- A correlated position has already triggered your stop, and the same force is likely to hit this position

**Override decision rule:**

```
Would a rational trader, seeing today's information for the first time with no
existing position, still enter this trade?

  YES -> Hold the position. Your plan is still valid.
  NO  -> Exit. The thesis has changed.
```

---

## 6. Trade Adjustments

Trade adjustments are deliberate modifications to a position's size, duration, or structure based on new information. They are different from exits -- they keep you in the trade but alter the risk profile.

### 6.1 Reducing Position Size on Weakness

Sometimes a trade is not clearly wrong (stop has not been hit) but is showing warning signs. Reducing position size is a middle ground between holding and exiting.

**Warning signs that warrant size reduction:**

| Warning Sign | Action |
|---|---|
| Volume declining on up days, rising on down days | Reduce by 25-50% |
| Price stalls at resistance for 3+ days | Reduce by 25% and set a time stop |
| The broader market weakens while your stock holds | Reduce by 25% (rising tide may recede) |
| Sector rotation away from your stock's sector | Reduce by 25-50% |
| Key moving average (50 SMA) is broken but stop is lower | Reduce by 50%, tighten stop |

**How to reduce:**
- Sell the weakest portion of a scaled position (highest cost basis lots)
- Use the close of the current day as the decision point
- Log the reduction and the reason in your trade journal
- Do NOT add the proceeds to another existing position immediately (avoid revenge trading)

### 6.2 Adding to Strength with Confirmation

This is the positive counterpart to reducing on weakness. When a position shows exceptional strength, adding (pyramiding) is appropriate under the conditions outlined in Section 2.

**Signs of strength that support adding:**
- Price breaks out of a consolidation pattern within the trade
- Volume surges on an up day (2x+ average)
- The stock shows relative strength versus the market (market flat or down, stock up)
- A new catalyst supports the thesis (sector news, analyst upgrade)
- A higher low forms above your entry, confirming the trend

### 6.3 Time-Based Exits

A trade that is not working after a reasonable period is consuming capital that could be deployed elsewhere. Time stops are an underappreciated trade management tool.

**Time stop guidelines for swing trades:**

| Trade Type | Time Limit | Rationale |
|---|---|---|
| Breakout trade | 3-5 days | Breakouts should move quickly or they fail |
| Pullback/retracement | 5-7 days | Pullback bounce should develop within a week |
| Mean-reversion | 3-5 days | Reversion trades have a short shelf life |
| Trend continuation | 10-15 days | Trends can develop slowly but should show progress |

**The time stop decision process:**

```
After [X] trading days, ask:
  1. Is the trade profitable?
     YES -> Continue holding; time stop does not apply to winners
     NO  -> Proceed to question 2

  2. Is the trade within 1 ATR of entry (essentially flat)?
     YES -> Exit at close today; the setup has failed to perform
     NO  -> If it is between entry and stop, the stop will handle it

  3. Has anything changed in the thesis?
     YES -> Exit regardless of time
     NO  -> The time stop itself is the reason to exit; honor it
```

### 6.4 Opportunity Cost Assessment

Every dollar tied up in a stagnant position is a dollar that cannot be used for a fresh, high-probability setup. This opportunity cost is invisible but real.

**When to assess opportunity cost:**
- You see a new A+ setup but have no capital (because it is tied up in a B- trade)
- A position has been flat for more than 5 days with no catalyst on the horizon
- The market has rotated to a new sector and your capital is stuck in the old one

**What to do:**
- Rank your open positions from strongest to weakest
- If a new setup is materially better than your weakest position, close the weak position and enter the new one
- Never close a strong, trending position to chase a new setup (the grass-is-greener trap)
- Maintain a watchlist priority system so these decisions are rule-based, not emotional

### 6.5 Hedging with Options or Correlated Instruments

For positions you want to hold through a risk event (earnings, FOMC, weekend) but with reduced risk:

**Protective put (portfolio insurance):**
- Buy a put option at or slightly below your stop-loss level
- Cost is typically 1-3% of position value per month
- Provides a guaranteed exit price regardless of gap size
- Best for large positions or high-conviction trades near events

**Correlated ETF hedge:**
- If long individual tech stocks, short a small QQQ position as a market hedge
- Reduces directional risk while maintaining the stock-specific thesis
- Requires monitoring the hedge ratio (beta-weighting)

**Pair trade hedge:**
- Long your stock, short its closest competitor in equal dollar amounts
- Neutralizes sector risk, isolates the company-specific thesis
- Advanced technique; requires understanding of pair correlation

> **Note:** Options hedging is an advanced technique that adds complexity. For most swing traders, proper position sizing and stops are sufficient. Only consider hedging when position size is large or the event risk is specific and unavoidable. See [09-regulation-tax-and-trade-operations.md](09-regulation-tax-and-trade-operations.md) for tax implications of hedging strategies.

---

## 7. Exit Strategies in Detail

The exit is where profits or losses are realized. Every other aspect of trade management ultimately serves this moment. Having a pre-defined exit plan removes emotion from the most critical decision.

### 7.1 Full Exit vs. Partial Exit Decision Tree

```
SHOULD I EXIT FULLY OR PARTIALLY?

Is the trade thesis still intact?
  |
  NO -> Full exit. Immediately.
  |
  YES -> Has the trade reached a target?
           |
           NO -> Is the stop about to be hit?
           |       |
           |       YES -> Let the stop execute (full exit)
           |       NO  -> Hold. No action needed.
           |
           YES -> Is momentum still strong?
                    |
                    NO  -> Full exit at target
                    YES -> Partial exit (scale out)
                           |
                           |-- Strong volume + no resistance above: exit 1/3
                           |-- Moderate momentum: exit 1/2
                           |-- Extended move + climactic volume: exit 2/3 or all
```

### 7.2 Target Reached but Momentum Continues

This is the "good problem" scenario. The stock has hit your profit target, but everything suggests it is going higher.

**Framework:**

1. **Always take at least partial profits at the target.** Sell 1/3 to 1/2. This is non-negotiable. The target existed for a reason, and taking partial profits converts paper gains to realized gains.

2. **Assess continuation potential:**
   - Is volume increasing on the breakout through target? (Bullish)
   - Is the stock entering a clear resistance zone above? (Bearish)
   - Is the broader market supporting the move? (Check [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md))
   - What does the next resistance level look like? (Chart patterns from [03-chart-patterns.md](03-chart-patterns.md))

3. **Trail the remainder aggressively:**
   - Switch from standard 2.0x ATR trail to 1.5x or even 1.0x ATR
   - The remaining position is "house money" -- you have already locked in profit
   - Accept that you will be stopped out at some point and that is perfectly fine

### 7.3 Stop Hit but Showing Reversal Signs

**The rule: DO NOT override your stop.**

This is one of the most dangerous temptations in trading. The stock hits your stop, you get filled, and then it immediately reverses and starts going up. The emotional urge to re-enter immediately is enormous.

**Why you must honor the stop:**
- Survivorship bias: you remember the times it bounced, not the times it kept falling
- The stop represented your maximum acceptable loss -- exceeding it changes your entire risk math
- Re-entering at the same price with the same stop means the exact same risk/reward as before, minus commissions and slippage
- If the reversal is real, it will still be there in 30-60 minutes -- you can re-enter as a new trade with a fresh analysis

**If the stop was hit and you want to re-enter:**
1. Wait at least 30 minutes (ideally until the next daily close)
2. Conduct a new, fresh analysis as if you had never been in the trade
3. Define a new entry, stop, and target
4. Size the new position according to standard rules (not "make up for the loss" sizing)
5. If the new analysis does not produce a valid setup, the reversal is not worth trading

### 7.4 Break-Even Exits and Their Psychological Impact

A break-even exit -- where you exit at your entry price after the stock ran in your favor and then reversed -- is one of the most frustrating outcomes in trading. You had a profit and now you have nothing.

**The psychology:** A break-even exit often feels worse than a small loss because of regret ("I should have taken profit"). This emotional response can lead to two destructive behaviors:
1. Taking profits too early on the next trade (cutting winners short)
2. Refusing to move stops to breakeven on future trades (leading to larger losses)

**How to handle break-even exits mentally:**
- A break-even exit is a win. You risked capital, the market moved against you, and you lost nothing. This is a success of your risk management system.
- The alternative to a breakeven stop is a losing stop. Over 100 trades, breakeven stops save significant capital.
- Log breakeven exits separately in your journal and review them monthly. If more than 30% of your trades exit at breakeven, your breakeven stop timing may need adjustment (probably moving too early; see Section 3.1).

### 7.5 End-of-Week Exits Before Weekends

As discussed in Section 4.4 (weekend gap risk), Friday afternoon is a decision point for all open positions.

**End-of-week exit checklist:**

```
FRIDAY AFTERNOON REVIEW (3:00-3:45 PM ET):

For each open position:

1. Profitability:
   [ ] > 2R profit: Comfortable holding. Trail stop.
   [ ] 1-2R profit: Hold if trend is strong; take partial if uncertain.
   [ ] 0-1R profit: Consider closing; risk/reward for weekend is poor.
   [ ] Losing: Close. Do not carry a losing position into the weekend.

2. Catalyst check:
   [ ] Any company-specific news expected over the weekend?
   [ ] Major global events this weekend?
   [ ] Monday is a holiday or has major economic releases?
   If YES: Reduce exposure by 25-50%.

3. Market context:
   [ ] VIX below 20: Standard risk. Holding is acceptable.
   [ ] VIX 20-30: Elevated risk. Reduce weekend exposure.
   [ ] VIX above 30: High risk. Strongly consider going to cash.

4. Portfolio heat:
   [ ] Total portfolio heat > 5%: Reduce at least one position.
   [ ] Total portfolio heat < 3%: Comfortable level for weekend.
```

---

## 8. Position Correlation Management

Managing a single trade is relatively straightforward. Managing multiple simultaneous positions introduces a new dimension of risk: correlation. When your positions are correlated, a single market move can trigger losses across your entire portfolio at once.

### 8.1 Managing Multiple Open Trades

**Maximum position guidelines:**

| Account Size | Max Concurrent Positions | Reasoning |
|---|---|---|
| < $25,000 | 3-4 | Limited capital; each position must be meaningful |
| $25,000 - $100,000 | 4-6 | Enough to diversify without over-complicating |
| $100,000 - $500,000 | 6-8 | Can spread across sectors meaningfully |
| > $500,000 | 8-12 | Institutional-level diversification |

**Rules for managing multiple positions:**
1. Each position must stand on its own merit -- never hold a trade just to "fill a slot"
2. Review all positions as a portfolio at least once daily, not just individually
3. Rank positions weekly from strongest to weakest; close the weakest if a new setup appears
4. Ensure no single position accounts for more than 30% of total portfolio value

### 8.2 Sector Concentration Monitoring

Sector concentration is the hidden risk in many swing trading portfolios. If all your trades are in technology stocks, you effectively have one big tech bet, not five independent trades.

**Sector concentration limits:**

| Concentration Level | Guideline |
|---|---|
| Single sector | Maximum 40% of total portfolio exposure |
| Two correlated sectors (e.g., tech + communication) | Maximum 50% combined |
| Single industry within a sector | Maximum 25% of portfolio exposure |

**How to monitor:**
- Tag each position with its GICS sector and industry
- Calculate percentage of portfolio value in each sector daily
- Maintain a simple sector exposure table:

```
Sector Exposure Dashboard:
  Technology:     35% (AAPL, MSFT, NVDA)    [NEAR LIMIT]
  Healthcare:     20% (JNJ, PFE)            [OK]
  Consumer Disc:  15% (AMZN)                [OK]
  Cash:           30%                        [OK]
```

### 8.3 Net Exposure Tracking

Net exposure measures the directional bias of your portfolio. It is the difference between long exposure and short exposure.

**Formula:**

```
Net Exposure = (Total Long Value - Total Short Value) / Account Equity x 100%

Example:
  Long positions total value: $60,000
  Short positions total value: $15,000
  Account equity: $100,000
  Net exposure: ($60,000 - $15,000) / $100,000 = 45% net long
```

**Net exposure guidelines by market regime (see [08-market-structure-and-conditions.md](08-market-structure-and-conditions.md)):**

| Market Regime | Recommended Net Exposure |
|---|---|
| Strong bull (uptrend, low VIX) | 60-80% net long |
| Moderate bull | 40-60% net long |
| Sideways/uncertain | 10-30% net long (or market neutral) |
| Moderate bear | -20% to +10% (lean short) |
| Strong bear (downtrend, high VIX) | -40% to -10% net short |

**Tracking net exposure daily:**
- Add this to your post-close routine
- If net exposure drifts outside the range for the current regime, adjust by trimming positions or adding hedges
- A sudden shift in net exposure without intentional action is a warning sign (your positions are moving against you together)

### 8.4 Reducing Correlated Risk

When multiple positions are correlated and all moving in the same direction (either all profiting or all losing), the portfolio is more vulnerable than it appears.

**The correlation problem:**

```
Scenario: 5 positions, all tech stocks
  Day 1: All 5 profit (feels great)
  Day 2: All 5 profit (portfolio surging)
  Day 3: NASDAQ drops 3%; all 5 gap down, all 5 stop out simultaneously
  Result: 5 x 1% risk = 5% portfolio loss in one day
         (This is within limits but could have been 1% with better diversification)
```

**Correlation management rules:**

1. **When correlated positions all profit together:**
   - Recognize this as a warning sign, not a reason to celebrate
   - Take partial profits on the weakest of the correlated group
   - Move stops to breakeven more aggressively on correlated positions

2. **When correlated positions all lose together:**
   - Close the weakest position immediately
   - Tighten stops on remaining correlated positions
   - Do NOT add to any of them ("they're all oversold" is a trap)

3. **Proactive correlation reduction:**
   - Before entering a new trade, check if it is in the same sector as existing positions
   - If it is, require a stronger setup (A+ only) to justify the concentration
   - Consider replacing a correlated position rather than adding to the sector
   - Use low-correlation assets (e.g., adding a utility or consumer staples trade to offset tech exposure)

**Simple correlation check before a new trade:**

```
NEW TRADE CORRELATION CHECK:

New trade sector: [Technology]

Current portfolio:
  Position 1: AAPL (Technology) -- SAME SECTOR
  Position 2: JNJ (Healthcare) -- Different
  Position 3: XOM (Energy) -- Different

Sector overlap: 1 out of 3 positions (33%)
If I add this trade: 2 out of 4 positions (50%) in Technology

Decision: Only enter if the setup is exceptional AND total tech exposure
stays below 40% of portfolio value. Otherwise, pass.
```

---

## Summary: Trade Management Master Checklist

```
DAILY TRADE MANAGEMENT CHECKLIST

PRE-MARKET:
  [ ] Check overnight futures and pre-market prices
  [ ] Scan news for held tickers
  [ ] Review economic calendar
  [ ] Assess any gap scenarios (Section 4)

MARKET OPEN:
  [ ] Observe opening prices relative to stops and targets
  [ ] Execute any gap-related decisions
  [ ] Do NOT open new trades in the first 15 minutes

MIDDAY:
  [ ] Quick check: any position within 1% of stop or target?
  [ ] Any unusual volume in held positions?

MARKET CLOSE:
  [ ] Review daily candles for all positions
  [ ] Update trailing stops (Section 3)
  [ ] Apply time stops where applicable (Section 6.3)
  [ ] Assess opportunity cost of stagnant positions (Section 6.4)

POST-MARKET:
  [ ] Update portfolio exposure dashboard (Section 8)
  [ ] Check sector concentration and net exposure
  [ ] Review correlation of positions
  [ ] Log observations in trade journal
  [ ] Set/update price alerts for all positions

FRIDAY ADDITIONAL:
  [ ] Run end-of-week exit assessment (Section 7.5)
  [ ] Reduce or close positions with elevated weekend risk
  [ ] Verify portfolio heat is within weekend comfort level
```

---

## Key Principles (Quick Reference)

1. **Stops only move in one direction** -- toward protecting profit, never toward increasing risk.
2. **Scale out of winners, not into losers.** Never add to a losing position.
3. **Time is a cost.** A trade that is not working after its expected timeframe is consuming capital.
4. **Correlation is hidden risk.** Five correlated positions are one big position.
5. **Earnings are binary events.** Exit before them unless you have a specific edge and plan.
6. **The plan is the plan.** Override it only when the fundamental thesis has materially changed.
7. **Alerts replace attention.** Set alerts, walk away, respond when triggered.
8. **Partial profits are real profits.** Taking some off the table is never wrong.
9. **A breakeven exit is a win.** You risked capital and lost nothing.
10. **Revenge trading is the enemy.** After a stop-out, slow down, do not speed up.
