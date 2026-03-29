# Drop Taxonomy — Detailed Classification Guide

## Why Classification Matters

A 50% drop from an earnings miss and a 50% drop from an SEC fraud investigation look
identical on a price chart. But the earnings-miss stock has a functioning business that
was repriced; the fraud stock may be worthless. Trading them the same way is like
prescribing the same treatment for a broken arm and a heart attack — same symptom
(pain), completely different prognosis.

Spend 2 minutes classifying. It's the highest-value 2 minutes in the entire workflow.

## Type E: Earnings Miss

**What happened:** Company reported revenue, earnings, or guidance below expectations.
The business still operates. The market repriced the stock to reflect lower growth/margins.

**Typical drop profile:** 40-60% drops common in small/mid-cap growth stocks.
Large-caps rarely drop this much on earnings alone.

**Bounce quality: ★★★ Good.** Earnings misses are the classic overreaction setup.
The stock was real yesterday, it's real today, and panicked selling pushes it below
reasonable fair value. Bounce window is 1-3 days.

**What to check:**
- Was it a revenue miss or just an EPS miss? (Revenue misses are more severe.)
- Was guidance cut or just missed? (Guidance cut = longer recovery.)
- Is the company profitable or cash-burning? (Cash-burners with earnings miss risk
  going to zero over months — the bounce is still tradeable but be cautious.)

**News sources:** Yahoo Finance earnings calendar, company PR, earnings call transcript
highlights on Seeking Alpha.

**Example:** Biotech with $200M market cap misses revenue by 20%, stock drops 55%.
Company still has $80M cash and 2 years of runway. Classic E-type — trade it.

## Type O: Offering/Dilution

**What happened:** Company announced a secondary offering, PIPE deal, convertible note,
or other dilutive capital raise. More shares = each share worth less.

**Typical drop profile:** 30-50%. The drop reflects dilution math plus signal that the
company needs cash (negative sentiment multiplier).

**Bounce quality: ★★ Moderate.** The dilution is real and permanent — the stock won't
recover to pre-offering levels. But the initial selling often overshoots because traders
front-run the offering and short aggressively. Once the offering is priced and shorts
cover, there's a bounce.

**What to check:**
- Was the offering already priced? (If yes, selling pressure is exhausted — better bounce.)
- At what discount was it priced? (>20% discount = more severe.)
- Is the offering for growth capital or to avoid bankruptcy? (Growth = better; survival = worse.)

**News sources:** SEC Edgar (S-3 filings), company PR, the offering prospectus.

## Type S: Sector Contagion

**What happened:** A peer or sector leader crashed, and the stock dropped in sympathy.
Its own fundamentals may be unchanged.

**Bounce quality: ★★★ Good.** If the company's own business is unaffected, the
sympathy drop is pure overreaction. This is the easiest classification to confirm —
just check whether there's company-specific negative news.

**What to check:**
- Is there ANY company-specific news? (If yes, reclassify.)
- How correlated is the stock to the crashed peer? (Higher correlation = the sympathy
  selling may be more justified.)
- Did the sector index (XLK, XBI, etc.) also drop >5%? (Sector-wide drops take longer
  to recover — less clean bounce.)

**News sources:** Sector ETF performance, peer company news, no company-specific filing.

## Type T: Technical/Mechanical

**What happened:** The stock was forced down by market mechanics, not fundamental news.
Margin calls, ETF rebalancing, large block liquidation, options market-maker hedging.

**Bounce quality: ★★★★ Best.** This is the purest mean reversion setup. The drop has
nothing to do with the company — it's plumbing. Once the forced selling is done, the
stock reverts toward its fundamental value.

**How to identify:**
- No news, no filing, no earnings — the stock just dropped
- Very high volume concentrated in a short window (looks like a liquidation)
- Other unrelated stocks from the same fund also dropped (cross-reference 13F holdings)

**What to check:**
- Was there an ETF rebalance? (Check major indices for reconstitution dates.)
- Was there a large block trade on the tape? (Level 2 data or time & sales.)
- Did the drop happen in the last 30 minutes? (Typical for forced liquidation/margin calls.)

## Type F: Fraud/Regulatory — DO NOT TRADE

**What happened:** SEC investigation, accounting fraud, auditor resignation, material
weakness disclosure, DOJ probe, or similar.

**Bounce quality: ★ Terrible.** Fraud stocks have no floor. The initial drop is often
just the beginning — more disclosures follow, lawsuits pile up, and the stock trends to
zero over weeks. Any bounce is a dead cat bounce in the worst sense.

**How to identify:**
- SEC filing (8-K with "investigation" or "material weakness")
- Auditor resignation or going concern opinion
- Short-seller report from known activist (Hindenburg, Muddy Waters, etc.)
- Press coverage mentioning fraud, misrepresentation, or criminal charges

**Rule: If in doubt, classify as F and skip.**

## Type B: Bankruptcy/Insolvency — DO NOT TRADE

**What happened:** Company filed for bankruptcy, missed debt payments, or announced
it cannot continue operations.

**How to identify:** Chapter 11 filing, missed bond coupon, lender acceleration notice.

**Rule: Never trade. Equity is last in the capital structure — often wiped out entirely.**

## Edge Cases

**Biotech FDA rejection:** Classify as E (earnings-equivalent). The pipeline asset was
the "revenue" — its failure is like a massive earnings miss. Bounce quality depends on
whether the company has other pipeline assets.

**SPAC de-SPAC collapse:** Classify as O (dilution-like). SPAC redemptions and warrant
exercises are dilutive. Often combined with fundamental disappointment. Moderate bounce.

**Chinese ADR delisting risk:** Classify as F (regulatory). Delisting risk is existential.
Even if the company is real, you can't trade a delisted ADR. Skip.

**Crypto-related stocks:** Classify based on the underlying cause. If Bitcoin crashed and
MARA dropped in sympathy → Type S. If the company had an exchange hack → Type F.

## Quick Decision Flowchart

```
Was there company-specific news?
├─ NO → Type T (technical/mechanical) → TRADE
├─ YES → What kind?
│  ├─ Earnings/guidance → Type E → TRADE
│  ├─ Offering/dilution → Type O → TRADE (caution)
│  ├─ Peer crashed, no own news → Type S → TRADE
│  ├─ SEC/fraud/audit/legal → Type F → SKIP
│  └─ Bankruptcy/default → Type B → SKIP
└─ Can't determine → SKIP (cost of sitting out = $0)
```
