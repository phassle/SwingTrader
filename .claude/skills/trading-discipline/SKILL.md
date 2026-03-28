---
name: Trading Discipline
description: Pre-trade checklists, hard limits, journaling templates, daily routines, and mistake flagging for swing trading. Triggers on trade reviews, daily summaries, mistake discussions, journal entries, pre-trade checklists, emotional discipline questions, or "what did I do wrong?"
tags: [trading, discipline, psychology, risk-management, journaling]
---

# Trading Discipline Framework

## PRE-TRADE CHECKLIST (Do NOT enter without all 7)

- [ ] **Signal score ≥ 12/20**: Run setup through the SwingTrader 0-20 signal scoring system (see `signal-scoring` skill). Score must reach B-grade (12+) or higher. No trade below 12 regardless of "gut feeling."
- [ ] **Trend confirmed**: Market regime identified (A/B/C/D per `market-regime` skill). Daily/4H chart context verified.
- [ ] **Setup matches playbook**: Entry setup aligns with documented playbook (gap fill, breakout, pullback, catalyst). Not a subjective "looks good" entry.
- [ ] **Volume confirms**: Volume bar at entry > 20-day average. No thin entry. Breakouts show volume expansion.
- [ ] **Risk calculated**: Exact stop loss level set via ATR × multiplier. Risk in SEK defined. Never trade without knowing max loss.
- [ ] **R:R ≥ 2:1**: Target reward ≥ 2x the risk. Minimum 2:1, target 3:1+. No low-reward trades.
- [ ] **No earnings in 48h**: Check calendar. No pre-earnings entries. Earnings = no swing trades same ticker for 48h after.

---

## HARD LIMITS (Non-negotiable)

| Limit | Action |
|-------|--------|
| **Daily loss > 2%** | STOP TRADING. Close open positions EOD. No new entries rest of day. |
| **2 consecutive losses** | MANDATORY BREAK. 15-30 min. Walk away. Emotional reset required. |
| **Weekly loss > 4%** | HALF SIZE. Reduce position size 50% for following week. |
| **10% account drawdown** | STOP ALL TRADING. Review strategy. Return to normal size only after documented root cause analysis. |

---

## TRADE JOURNAL FIELDS (Mandatory for every exit)

```
trade_id: [TICKER]_[YYYY-MM-DD]_[HH-MM]
symbol: [OMX ticker]
entry_date: YYYY-MM-DD HH:MM
exit_date: YYYY-MM-DD HH:MM
entry_price: [SEK]
exit_price: [SEK]
position_size: [shares]
strategy: [playbook name]
setup_type: [gap-fill, breakout, pullback, catalyst, reversal]
market_regime: [strong-uptrend, uptrend, range, downtrend, strong-downtrend]
exit_reason: [target-hit, stop-loss, breakeven, early-exit-reason]
r_multiple: [profit/risk or loss/risk]
emotional_state: [calm, confident, anxious, fearful, greedy, impulsive]
mistakes: [list any deviations from plan]
lessons: [key takeaway from this trade]
```

---

## DAILY ROUTINE (Non-negotiable)

### PRE-MARKET (30 minutes, 08:00-08:30 CET)
- [ ] Check **economic calendar** — any 08:30 CET+ events? (Typically none, but verify.)
- [ ] Check **market regime** — OMX strength, sector leadership, support/resistance levels.
- [ ] Scan for **gap plays** — which tickers gapped overnight? Up gaps, down gaps, size?
- [ ] Review **sector strength** — which sectors are leading/lagging?
- [ ] Update **watchlist** — remove broken setups, add new candidates from scanner alerts.

### DURING-MARKET (09:00-17:00 CET)
- [ ] **Alerts only**. Do NOT watch charts constantly. Set alerts, check infrequently.
- [ ] If alert triggers: Take 2 min to evaluate. Make entry decision. Execute.
- [ ] NO chart watching. NO second-guessing open trades. NO "what if" thinking.
- [ ] If tempted to enter outside plan: Ask "Does this match the pre-market checklist?" If no → skip.

### POST-MARKET (15 minutes, 17:15-17:30 CET)
- [ ] **Log all trades** — entry, exit, prices, reason. Emotional state. Mistakes.
- [ ] **Check alerts** — any after-hours moves to log or plan for tomorrow?
- [ ] **Tomorrow plan** — which setups forming? Any calendar events? Adjusted stops on open positions?

---

## WEEKLY REVIEW CHECKLIST (Every Friday EOD)

- [ ] Total P&L for week. How far from target?
- [ ] Win rate % this week. Average R:R on winners vs losers.
- [ ] How many trades deviated from playbook? (Should be <5%.)
- [ ] Emotional violations: Revenge trades? FOMO entries? Oversize positions? (Record count.)
- [ ] What was the best trade this week? Why? What was the worst? Why?
- [ ] Did I follow hard limits? Any breaches?
- [ ] Did I follow daily routine? Any skips?
- [ ] One thing to improve next week.

---

## COMMON MISTAKES TO FLAG

### Revenge Trading
**Red flag**: Two losses in a row, then immediately entering next available setup without full checklist.
**Check**: Did you take the trade to "make back" the loss? If yes, close it. Sit out 30 min.

### Moving Stops
**Red flag**: Stop loss moves up (in a profit trade) or down (in a loss trade) after entry.
**Check**: Is this adjustment based on new chart structure? Or emotion? If emotion → reject it. Use original stop.

### FOMO Entries
**Red flag**: Entering a trade already 5%+ in the move, "before it goes higher."
**Check**: Did this setup miss the pre-trade checklist? If yes → skip. Your edge is only on proper setups.

### Overtrading
**Red flag**: Taking 5+ trades in one day. Or positions that total > 2% account risk in one day.
**Check**: Are these all playbook setups? Or are you forcing trades because "the market is moving"?

### No Journal
**Red flag**: Trading but not logging. "I'll remember." You won't.
**Check**: Do you have a journal entry for every trade? If not, you can't improve.

### Oversized Positions
**Red flag**: Position size > 2% account risk. Or three open trades, all at max size.
**Check**: Calculate actual risk. Should be 0.5-1.5% per trade. Adjust position size down if needed.

---

## RECOVERY PROTOCOL (After major breach or drawdown)

After ignoring a stop, revenge trading, or hitting a drawdown limit:

```
Phase 1: HALT (1-3 days)
  - Zero trading. Journal what happened. Identify the breach type.
  - Breach types: moved-stop, revenge-trade, skipped-checklist,
    FOMO-entry, oversized-position, ignored-regime

Phase 2: PAPER TRADE (trades 1-20)
  - Trade at 0% real capital. Full checklist + journal required.
  - Must complete 20 consecutive trades following all rules.

Phase 3: REDUCED SIZE (trades 21-50)
  - 50% of normal position size. Real capital.
  - If any rule breach: restart Phase 3 counter.

Phase 4: NORMAL SIZE (trades 51-100)
  - Full position size. Track breach rate.
  - At trade 100: if breach rate < 5%, recovery complete.
```

## THE 100-TRADE HORIZON

**Your edge is invisible in 5-10 trades.**

- Variance will show you noise, not signal.
- A 2:1 R:R system can have 10-trade losing streaks with 60% win rate.
- A 3:1 R:R system needs only 35% win rate but takes 50+ trades to prove.

**Action**: Don't evaluate strategy on single-digit trade counts. Log trades. At trade 20, evaluate. At trade 50, refine. At trade 100, you'll see your true edge.

---

## WHEN TO USE THIS SKILL

Ask me to review or discuss:
- Pre-trade checklist validation before entering
- Daily summary or post-market review
- Mistake identification ("What did I do wrong?")
- Journal entry construction
- Hard limit breaches or near-breaches
- Weekly performance review
- Emotional discipline violations
- Revenge trading temptation
- Watchlist or setup evaluation

---

## RESEARCH DOCUMENTS

Detailed theory and deeper context:
- **[28-trading-psychology-and-behavioral-discipline.md](file:///sessions/festive-confident-lamport/mnt/SwingTrader/research/strategy-and-theory/28-trading-psychology-and-behavioral-discipline.md)** — Psychology, emotional patterns, overtrading.
- **[20-common-mistakes-and-case-studies.md](file:///sessions/festive-confident-lamport/mnt/SwingTrader/research/strategy-and-theory/20-common-mistakes-and-case-studies.md)** — Real examples of discipline failures and recoveries.
- **[13-trading-plan-and-daily-routine.md](file:///sessions/festive-confident-lamport/mnt/SwingTrader/research/strategy-and-theory/13-trading-plan-and-daily-routine.md)** — Structured daily workflow and market structure.
- **[17-trading-journal-framework.md](file:///sessions/festive-confident-lamport/mnt/SwingTrader/research/strategy-and-theory/17-trading-journal-framework.md)** — Journal design, analysis patterns, improvement loops.
