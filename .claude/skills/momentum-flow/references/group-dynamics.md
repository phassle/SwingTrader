# Group Dynamics — Leaders, Sympathy Plays, and AI Screening

## How Group Moves Work

Stocks don't move in isolation. When a sector leader surges, the "family" follows.
This isn't random — it's driven by:

1. **Fund rebalancing:** When NVDA surges, funds overweight in semis need to rebalance.
   They buy AMD, MRVL, and KLAC to maintain sector allocation targets.
2. **Analyst upgrades cascading:** One analyst upgrades NVDA → others re-evaluate the sector
   → upgrades hit AMD two weeks later.
3. **Retail copycat behavior:** Traders who "missed" NVDA look for the "next NVDA" in the
   same sector at a lower price.
4. **Algorithmic pair-trading:** Quant funds trade sector pairs. When one stock spikes,
   algorithms buy correlated names to capture the spread.

The leader-sympathy delay is typically 2-7 days. That's your window.

## Leader Identification Checklist

Score each stock in the group. The highest score is the leader:

```
+2: Highest RS Score in the group (90-day)
+2: First to break out of a base
+2: Highest volume on breakout day (relative to own average)
+1: Making new 52-week or all-time highs
+1: Strongest earnings growth in the group
+1: Highest analyst revision momentum (estimates rising)
+1: Most institutional ownership increase (13F quarterly)

LEADER = highest score. Typically 6-8 points.
SYMPATHY = everyone else in the group with ≥3 points.
LAGGARD = <3 points. Skip — there's a reason money isn't flowing there.
```

## Famous Group Moves (Study These)

### EV Group (2020-2021)
- Leader: TSLA
- A-sympathy: NIO, XPEV, LI (Chinese EVs)
- B-sympathy: RIVN, LCID (pre-revenue)
- Laggard: FSR, RIDE (skip — weak fundamentals confirmed later)

### AI/Semiconductor Group (2023-2024)
- Leader: NVDA
- A-sympathy: AMD, AVGO, MRVL
- B-sympathy: SMCI, ARM
- Infrastructure play: MSFT, GOOGL (AI application layer)

### Cannabis Group (2021)
- Leader: TLRY
- A-sympathy: CGC, ACB
- Lesson: When ALL stocks in a group spike at once with no fundamental change,
  it's retail-driven, not institutional. These "group moves" reverse violently.
  Only trade groups where the leader has FUNDAMENTAL support (earnings, revenue).

## Detecting Sympathy Setup Formation

After the leader breaks out, scan the group for consolidation patterns:

```
DAY 1-2 after leader breakout:
  Group stocks gap up in sympathy → DON'T CHASE
  Wait for them to consolidate

DAY 3-5:
  Look for Setup B (tight consolidation at 10/20 MA) in sympathy names
  This is the "reload zone" — institutions who missed the leader
  are entering the sympathy names here

DAY 5-7:
  Sympathy stocks that build tight bases → watchlist candidates
  Sympathy stocks that fade below 10-day MA → remove (weak)

DAY 7+:
  If sympathy hasn't set up by now, the group move may be exhausted
  Monitor but don't force
```

## Using AI to Find Sympathy Plays

### Automated Screening Approach

AI/algorithms can screen much faster than humans. Here's what to build:

```python
# Concept: find stocks correlated to a leader that haven't broken out yet
def find_sympathy_candidates(leader_ticker, universe, lookback=90):
    """
    1. Compute 90-day rolling correlation between leader and all stocks
    2. Filter: correlation > 0.6 (meaningfully related)
    3. Filter: stock is above 50-day MA (trend intact)
    4. Filter: stock has NOT made new 20-day high (hasn't broken out)
    5. Rank by: tightness of consolidation (lower ATR% = tighter base)
    """
    leader_returns = get_returns(leader_ticker, lookback)
    candidates = []
    for stock in universe:
        corr = compute_correlation(leader_returns, get_returns(stock, lookback))
        if corr > 0.6 and above_50ma(stock) and not new_20d_high(stock):
            tightness = atr_percent(stock, period=10)  # lower = tighter base
            candidates.append((stock, corr, tightness))
    return sorted(candidates, key=lambda x: x[2])  # tightest first
```

### NLP-Based Sector Mapping

For finding non-obvious sympathy plays, use NLP on earnings call transcripts:

```
APPROACH:
  1. Take the leader's earnings call transcript
  2. Extract: key suppliers, customers, partners mentioned
  3. Cross-reference with the universe
  4. Stocks mentioned as suppliers/partners are potential sympathy plays
     that traditional sector classification would miss

EXAMPLE:
  NVDA mentions "TSMC, SK Hynix, Dell, Super Micro" in earnings call
  → SMCI, DELL are sympathy candidates even though they're not "semiconductors"
```

### Flow Detection via Options

```
INSTITUTIONAL FLOW SIGNAL:
  Unusual options activity in a group member = potential smart money positioning

SCREEN FOR:
  Call volume > 3× average in a stock in the same group as the leader
  Large block trades (>$500k premium) on OTM calls
  Call/Put ratio > 3:1 when it's normally around 1:1

TOOLS: Unusual Whales, OptionStrat, Barchart unusual activity
```

## When the Group Trade Ends

```
DISTRIBUTION SIGNALS:
  Leader breaks 20-day MA on above-average volume → Warning
  Leader breaks 50-day MA → Group trade is OVER
  ETF for the sector breaks 50-day MA → Sector rotation out
  Sympathy plays start failing breakouts → Institutions are done

ACTION:
  Trail all positions tightly (10-day MA)
  Do NOT add new positions in this group
  Start scanning for the NEXT group showing accumulation
```
