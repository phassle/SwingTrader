# Capitulation Detection — Technical Deep Dive

## What Is a Capitulation Candle?

A capitulation candle is the "flush" — the moment when the last wave of panic sellers
dumps simultaneously, creating a brief price vacuum that snaps back almost instantly.
On a chart it looks like a long lower wick: price plunged but closed well above the low.

Think of it like a crowded elevator free-falling for a second before the emergency brake
catches. The spike downward IS the panic; the snap-back IS the exhaustion of sellers.

## The Three-Criteria Test

All three must be met on a single 5-minute candle:

```
1. RANGE ≥ 10% of stock price
   candle_range = high - low
   range_pct = candle_range / stock_price × 100
   Example: stock at $3.00, candle high $3.10, low $2.70 → range $0.40 = 13.3% ✓

2. LOWER WICK ≥ 5% of stock price
   lower_wick = min(open, close) - low
   wick_pct = lower_wick / stock_price × 100
   Example: candle low $2.70, close $2.95 → wick $0.25 = 8.3% ✓

3. VOLUME ≥ 2× average 5-min volume
   avg_5min_vol = total_daily_volume / N_BARS
     US regular session: 78 bars (09:30-16:00 = 390 min / 5)
     Nasdaq Stockholm:  102 bars (09:00-17:30 = 510 min / 5)
   Or better: compute rolling 20-bar average of 5-min volume
   Example: avg 5-min vol = 15,000 shares, candle vol = 45,000 → 3× ✓
```

### Why These Specific Thresholds?

**Range ≥ 10%:** Normal 5-min candles on a $3 stock have ranges of 1-3%. A 10% range
means something extraordinary happened — a wave of market orders hitting thin bids.
Below 10%, it's just normal volatility on a cheap stock.

**Wick ≥ 5%:** The wick is the rejection signal. A 5% wick means price dropped sharply
but was bought back within 5 minutes. This requires actual buying pressure, not just
a pause in selling. A candle with a big range but no wick (big red body) is NOT
capitulation — it's continued selling.

**Volume ≥ 2×:** High volume confirms this was a real event, not a thin-market artifact.
On low-volume stocks, a single large sell order can create a long wick that looks like
capitulation but is really just one seller hitting air. The 2× volume threshold ensures
many participants were involved.

## Implementation in Code

```python
def is_capitulation_candle(candle, avg_volume, stock_price):
    """
    candle: dict with keys: open, high, low, close, volume
    avg_volume: average 5-min volume (float)
    stock_price: reference price, typically today's open (float)
    """
    range_pct = (candle['high'] - candle['low']) / stock_price * 100
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    wick_pct = lower_wick / stock_price * 100
    vol_ratio = candle['volume'] / avg_volume if avg_volume > 0 else 0

    return (
        range_pct >= 10.0
        and wick_pct >= 5.0
        and vol_ratio >= 2.0
    )
```

### Reference Price Choice

Use **today's open** as the reference price, not the candle's own price. Why?
During a panic crash, the stock might be at $1.50 after opening at $4.00. Using
$1.50 as reference makes the 10% threshold too easy to hit ($0.15 range). Using
the open ($4.00) keeps the threshold meaningful ($0.40 range).

## False Capitulation Signals

### Type 1: Thin-Market Wick
```
LOOKS LIKE: Long lower wick on a 5-min candle
REALITY:    Stock has $0.10 spread, one market sell order of 5k shares
            walks through 3 price levels, creating an artificial wick
TELL:       Volume is high on ONE side only. Check time & sales —
            if 80%+ of volume is at the low, it's one seller, not capitulation
FIX:        The 2× volume filter catches most of these, but also check
            that volume is distributed across the candle, not clustered
```

### Type 2: Dead Cat Bounce Setup
```
LOOKS LIKE: Capitulation candle followed by green candle (entry signal)
REALITY:    Stock is in a multi-day downtrend with no catalyst for reversal.
            The "bounce" is just short-covering before the next leg down.
TELL:       No prior parabolic run-up. The stock was already weak.
FIX:        The parabolic-panic strategy requires +100%/5d run-up as a
            prerequisite. This filters out dead cat bounces by design.
```

### Type 3: Halt-Resume Artifact
```
LOOKS LIKE: Massive range candle with huge volume
REALITY:    Stock was halted (LULD or T12), and the first post-halt candle
            contains all the pent-up supply. The "capitulation" is actually
            just the halt unwind.
TELL:       Check for trading halts. If the candle spans a halt period,
            the wick doesn't mean what it normally means.
FIX:        Skip any 5-min bar that overlaps a trading halt.
            US: NYSE halt data (ftp.nyxdata.com) or Polygon reference API.
            Sweden: Nasdaq OMX halt data via IBKR or Millistream.
```

### Type 4: Pre-Market Bleed Already Priced In
```
LOOKS LIKE: Stock opens at $2.00 (down 40% from prior close of $3.30),
            drops to $1.60 (another 20%), capitulation candle appears
REALITY:    The "drop from open" is only 20%, but total drop from
            yesterday's close is 52%. The panic already happened pre-market.
TELL:       Check the gap-down size. If stock gapped down >20% at open,
            the intraday drop threshold should be measured differently.
FIX:        The strategy measures drop from today's open, which is correct.
            The prior close doesn't matter — what matters is whether
            intraday sellers are exhausted.
```

## Volume Analysis Beyond the 2× Threshold

### Volume Profile Within the Candle

For more sophisticated detection, analyze how volume is distributed:

```
STRONG CAPITULATION:
  Volume clustered at the LOW of the candle
  Then shifts to the HIGH of the candle
  Interpretation: sellers dumped at the bottom, buyers absorbed and lifted

WEAK SIGNAL:
  Volume evenly distributed throughout the candle
  Interpretation: two-way battle, no clear exhaustion

FAKE SIGNAL:
  Volume clustered at the HIGH of the candle only
  Interpretation: sellers pushed it down on low volume,
  one buyer scooped it up — not broad-based capitulation
```

### Cumulative Volume Delta

```
CVD = Σ(volume at ask) - Σ(volume at bid)

During capitulation:
  CVD goes deeply negative (sellers dominating)
  Then sharply positive within the same candle or next candle
  The CVD reversal IS the capitulation signature

This requires tick-level data (Level 2 / time & sales).
Available from: Polygon tick data, Alpaca SIP feed, FirstRate Data
```

## Practical Screening Workflow

```
1. Pre-filter: stocks on watchlist (passed evening scan)
2. At market open: stream 5-min candles
3. For each candle after 09:45:
   a. Check if stock has dropped ≥30% from open → panic gate
   b. If yes, check capitulation criteria on each new candle
   c. If capitulation detected, flag and wait for first green candle
4. First green candle after capitulation → entry signal
5. Log: candle time, range%, wick%, vol ratio, entry price
```
