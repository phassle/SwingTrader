# Watchlist And Universe Selection For Swing Trading

Prepared by Codex on 2026-03-08. This file is separate from any scanner file. The goal here is to define what names should even be eligible before filters and signals are applied.

## Why this matters

Many weak swing-trading systems fail before the signal step. The problem is not the setup logic. The problem is that the strategy is searching the wrong universe.

Universe selection should answer:

- which instruments are allowed
- which names are too illiquid or too noisy
- which names carry special fraud or manipulation risk
- how broad the daily watchlist should be

## 1. Separate universe selection from screening

These are not the same thing.

- `Universe selection` decides the pool of tradable names.
- `Screening` ranks or filters opportunities inside that pool.

If this separation is skipped, scanners often surface low-quality names that look attractive only because they are volatile.

## 2. Default universe for a serious U.S. equity swing trader

A practical default universe is:

- U.S.-listed common stocks
- liquid ETFs
- optionally ADRs only if liquidity and headline risk are acceptable

Usually excluded:

- OTC names
- most microcaps
- extremely low-priced stocks
- names with chronic dilution or promotion behavior

## 3. Why low-priced and low-volume names deserve special caution

FINRA states that low-priced securities often trade in low volumes, can be hard to sell because of a lack of buyers, and can be more vulnerable to manipulation. FINRA also notes that OTC low-priced names often have limited public information.

Investor.gov similarly explains that microcap stocks are among the riskiest securities and that low trading volume can make them difficult to exit when needed.

Swing-trading implication:

- a name is not attractive just because it moves a lot
- if liquidity disappears when the trade goes wrong, the setup quality is overstated

## 4. Core universe filters

The exact thresholds depend on style, but these are the right variables.

### Listing venue

Preferred:

- NYSE
- Nasdaq
- liquid ETFs

Avoid by default:

- OTC securities
- names with limited disclosure quality

### Market cap

Minimum market cap filters out names with higher manipulation risk, poor disclosure, and unreliable technicals.

Conservative default thresholds:

- conservative swing universe (default): `>$2B`
- advanced/optional expansion tier: `>$500M`, must be explicitly enabled
- below $500M: exclude from automated scanning

### Price

Common practice is to exclude extremely low-priced names because spread, manipulation, and slippage become a much larger part of the trade.

Conservative default thresholds:

- conservative swing universe (default): `>$10`
- advanced/optional expansion tier: `>$5`, must be explicitly enabled
- highly speculative bucket: `<$5`, separate and explicit if allowed at all

### Average daily trading volume (ADTV)

Minimum share volume ensures positions can be entered and exited without excessive slippage.

Conservative default thresholds:

- conservative swing universe (default): `>500,000 shares`
- advanced/optional expansion tier: lower thresholds require explicit opt-in and tighter position sizing

### Dollar volume

Average daily dollar volume is often more useful than share volume alone.

Why:

- it scales better across low-priced and high-priced names
- it better reflects real execution capacity

A good working rule:

- define a minimum average daily dollar volume that is comfortably larger than intended position size

### Spread and tradeability

A stock can pass volume filters and still trade poorly.

Track:

- average bid-ask spread
- opening spread behavior
- spread during premarket and after-hours
- whether fills cluster or slip

## 5. Suggested universe tiers

This is a useful app design pattern.

### Tier 1: Core liquid universe

- large caps
- highly liquid mid caps
- major ETFs

Best for:

- breakout systems
- pullback continuation
- market and sector alignment setups

### Tier 2: Secondary momentum universe

- smaller but still liquid names
- event-driven movers with acceptable spreads

Best for:

- catalyst continuation
- post-earnings setups
- higher-volatility swing trades

### Tier 3: Speculative universe

- low-priced names
- thin small caps
- promotion-prone names

Best use:

- separate bucket with stricter size, tighter max exposure, or full exclusion

## 6. Red flags for exclusion

Exclude or quarantine names with:

- persistent low dollar volume
- wide spreads relative to ATR
- unexplained promotional activity
- frequent dilution or financing overhang
- multiple recent SEC suspension or fraud-style warning signs
- price spikes with no primary-source catalyst

FINRA and Investor.gov both emphasize that low-information, low-liquidity names are more vulnerable to fraud and manipulation. That makes them poor default candidates for systematic swing trading.

## 7. Universe maintenance rules

The universe should not be static forever.

Recommended checks:

- weekly liquidity review
- monthly removal of names that no longer meet thresholds
- event-based inclusion for temporary catalyst names
- hard removal after splits, delisting risk, or repeated tradeability problems

## 8. Watchlist construction

The universe may contain hundreds of names. The daily watchlist should be much smaller.

Suggested watchlist buckets:

- market leaders
- sector leaders
- catalyst names
- technical setups nearing trigger
- defensive or hedge candidates

The watchlist should reflect both `what is tradable` and `what is close to actionable`.

## 9. What an app should store

Useful universe-level fields:

- `listing_exchange`
- `instrument_type`
- `average_daily_dollar_volume`
- `average_spread`
- `price_bucket`
- `market_cap_bucket`
- `earnings_date`
- `is_otc`
- `is_leveraged_etf`
- `has_recent_promotion_risk`
- `universe_tier`

## 10. Practical default policy

If no other policy exists, a strong default for swing trading is:

- U.S.-listed stocks and ETFs only
- no OTC
- no low-information microcaps
- minimum price: >$10
- minimum market cap: >$2B
- minimum average daily trading volume (ADTV): >500,000 shares
- separate tagging for event-driven names
- separate sizing rules for thinner names even if they remain eligible

## Swedish market: universe adaptation

> **Full reference:** See `27-swedish-market-adaptation.md` Section 5 for complete details.

All thresholds above are calibrated for the US market. For Swedish stocks traded on Nasdaq Stockholm, the following equivalent thresholds apply:

### Equivalent universe filters

| Filter | US Default | Swedish Equivalent | Rationale |
|--------|-----------|-------------------|-----------|
| **Market cap (conservative)** | > $2B | > SEK 20B (~EUR 1.8B) = Large Cap | Focuses on the most liquid segment |
| **Market cap (expanded)** | > $500M | > SEK 5B (~EUR 450M) = Upper Mid Cap | Adds liquid Mid Cap names |
| **Minimum price** | > $10 | > SEK 20 | Filters out penny stocks; spread as % of price becomes manageable |
| **ADTV (daily value traded)** | > $1M/day | > SEK 10M/day | Ensures positions can be entered/exited without excessive slippage |
| **ADTV (volume in shares)** | > 500,000 shares/day | > 100,000 shares/day | Lower threshold reflects smaller Swedish market |

### Listing venue

| Venue | Include | Notes |
|-------|---------|-------|
| Nasdaq Stockholm Large Cap | Yes | Primary universe. ~100 stocks. |
| Nasdaq Stockholm Mid Cap | Selective | Include top names with ADTV > SEK 5M/day. |
| Nasdaq Stockholm Small Cap | No (default) | Requires explicit opt-in. Low liquidity, wide spreads. |
| First North (Premier and Growth Market) | No (default) | Higher risk, less regulated. Only for speculative tier with strict sizing. |

### Recommended Swedish default universe

- **Conservative:** Nasdaq Stockholm Large Cap with ADTV > SEK 10M/day (~60-80 tradable names).
- **Expanded:** Add top Mid Cap names with ADTV > SEK 5M/day (~90-130 total names).
- **Speculative:** First North Premier names with ADTV > SEK 2M/day (explicit opt-in, stricter position sizing).

### Key differences from US universe

- The total Swedish universe is much smaller (~350 listed companies on Nasdaq Stockholm vs. ~4,000+ on NYSE/Nasdaq).
- Swedish Large Cap stocks have comparable liquidity to US Mid Caps, not US Large Caps.
- OTC risks (Section 3 above) are less relevant since Sweden does not have an equivalent of US OTC/Pink Sheet markets. However, First North serves a similar function for earlier-stage companies.
- Spreads are wider across all Swedish market cap segments. Factor spread cost into position sizing and backtest assumptions.

## Bottom line

The watchlist should be built from a defined tradable universe, not from whatever is moving the most today. Universe quality controls the reliability of every downstream scanner, setup score, and backtest.

## Sources

- FINRA, "Low-Priced Stocks Can Spell Big Problems"
  https://www.finra.org/investors/insights/low-priced-stocks-big-problems

- Investor.gov, "Microcap Stock Basics (Part 1 of 3: General Information)"
  https://www.investor.gov/index.php/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/investor-3

- Investor.gov, "Microcap Fraud"
  https://www.investor.gov/additional-resources/spotlight/microcap-fraud

- Investor Alert, "Fraudulent Stock Promotions"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/updated
