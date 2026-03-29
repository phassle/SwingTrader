# Sector Flow Analysis — ETF-Based Institutional Detection

## Core Principle

Institutions allocate capital top-down: first they decide WHICH sectors to overweight,
then they pick stocks within those sectors. By watching sector ETFs, you see the
allocation decision BEFORE individual stocks confirm it.

Think of it like watching water flow downhill — the ETF is the river, individual stocks
are the streams. The river moves first.

## The 50/200 MA Gate

This is the single most important filter in the strategy:

```
SECTOR IS IN PLAY:
  ETF price > 50-day MA AND > 200-day MA

SECTOR IS OUT:
  ETF price < 50-day MA OR < 200-day MA
  → Skip ALL stocks in this sector, regardless of individual strength

NO EXCEPTIONS. A strong stock in a weak sector is swimming upstream.
It may work short-term, but the odds are against you.
```

## ETF-to-Stock Mapping

### US Sector ETFs and Key Holdings

```
TECHNOLOGY (XLK):
  Leaders: AAPL, MSFT, NVDA, AVGO
  Sub-sector: SMH (semiconductors) → NVDA, AMD, MRVL, KLAC, LRCX

FINANCIALS (XLF):
  Leaders: JPM, BAC, GS, MS
  Sub-sector: KRE (regional banks), KBE (banks)

ENERGY (XLE):
  Leaders: XOM, CVX, SLB, EOG
  Sub-sector: OIH (oil services), AMLP (MLPs)

HEALTHCARE (XLV):
  Leaders: UNH, JNJ, LLY, ABBV
  Sub-sector: IBB (biotech), XBI (small-cap biotech)

INDUSTRIALS (XLI):
  Leaders: CAT, DE, GE, HON
  Sub-sector: ITA (defense), JETS (airlines)

CONSUMER DISCRETIONARY (XLY):
  Leaders: AMZN, TSLA, HD, NKE
  Sub-sector: XRT (retail), BETZ (gambling)

SEMICONDUCTORS (SMH):
  Leaders: NVDA, AMD, AVGO, MRVL, KLAC
  This is often THE leading group in bull markets
```

## Flow Detection Signals

### Accumulation (money flowing IN)

```
STRONG SIGNAL:
  ETF making new 20-day highs
  AND volume expanding (20-day vol MA rising)
  AND at least 3 of 5 top holdings also at 20-day highs

MODERATE SIGNAL:
  ETF above rising 50-day MA
  AND volume steady or slightly expanding
  AND at least 2 of 5 top holdings outperforming

WATCH:
  ETF reclaiming 50-day MA from below
  AND volume spike (>1.5× average) on the reclaim day
  → Early rotation signal. Add to watchlist, wait for confirmation.
```

### Distribution (money flowing OUT)

```
WARNING:
  ETF breaks below 10-day MA on above-average volume
  AND 2+ top holdings also break 10-day MA

CONFIRMED DISTRIBUTION:
  ETF breaks below 50-day MA on heavy volume
  AND sector breadth deteriorating (>40% of components below 50-day MA)
  → Close all positions in this sector. Do not re-enter until reclaim.
```

## Rotation Detection

Rotation = money leaving one sector and entering another. This is your signal
to shift your watchlist.

```
ROTATION SIGNAL:
  Old leader ETF: breaking below 20-day MA, declining volume on bounces
  New leader ETF: breaking above 50-day MA, expanding volume, new 20-day highs

CONFIRMATION: Takes 3-5 days of divergence.
  Day 1: Old sector weak, new sector strong → could be noise
  Day 3: Same pattern continues → rotation likely
  Day 5: Old sector making new lows, new sector making new highs → confirmed

ACTION: Start probing new sector with 50% size positions.
```

## Weekly Sector Scorecard

Run this every Sunday:

```
For each sector ETF:
  Price vs 50-day MA:  Above / Below
  Price vs 200-day MA: Above / Below
  20-day volume trend: Rising / Flat / Falling
  New 20-day high:     Yes / No
  Breadth (% above 50 MA): >60% / 40-60% / <40%

SCORE:
  5/5 checks = A (strongest allocation target)
  4/5 = B (solid, trade leaders)
  3/5 = C (mixed, be selective)
  ≤2/5 = F (avoid entirely)
```
