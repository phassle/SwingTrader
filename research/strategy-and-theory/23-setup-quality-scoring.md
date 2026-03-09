# Setup Quality Scoring For Swing Trading

Prepared by Codex on 2026-03-08. This file proposes a practical scoring framework for ranking swing-trading setups before entry. This is an implementation framework inferred from the broader research pack, not a regulator-defined standard.

## Why this matters

Most traders do not lose because every setup is bad. They lose because they treat mediocre setups and exceptional setups as if they were equal.

A setup score helps with:

- prioritization
- consistency
- journaling
- automation
- reducing impulsive trades

## 1. Core principle

A high-quality setup is one where multiple forms of evidence align:

- trend
- level
- catalyst
- volume
- liquidity
- risk/reward
- market and sector context

Any one factor can help. The edge usually comes from confluence.

## 2. Suggested scoring model

Use a `0 to 20` score with eight categories. A setup does not need a perfect score. It needs to clear the minimum threshold required by the strategy.

### Category 1: Trend alignment `0 to 3`

- `0`: trade fights higher-timeframe trend
- `1`: mixed trend
- `2`: daily trend supports setup
- `3`: daily and weekly trend both support setup

### Category 2: Level quality `0 to 3`

- `0`: setup forms in the middle of noise
- `1`: weak nearby reference level
- `2`: clear support, resistance, breakout level, or pullback zone
- `3`: strong multi-timeframe level with clear prior reaction

### Category 3: Catalyst quality `0 to 3`

- `0`: no catalyst or rumor only
- `1`: weak narrative support
- `2`: real catalyst but moderate significance
- `3`: strong confirmed catalyst such as earnings, guidance, major filing, or broad macro alignment

### Category 4: Volume and participation `0 to 2`

- `0`: low or unconvincing participation
- `1`: adequate volume
- `2`: strong relative volume and convincing price acceptance

### Category 5: Liquidity and execution quality `0 to 2`

- `0`: wide spreads or poor tradeability
- `1`: acceptable tradeability
- `2`: strong liquidity and easy execution

### Category 6: Market and sector alignment `0 to 3`

- `0`: setup opposes both market and sector
- `1`: mixed context
- `2`: either market or sector supports the trade
- `3`: stock, sector, and broad market all align

### Category 7: Risk/reward quality `0 to 2`

- `0`: poor location or unclear invalidation
- `1`: acceptable reward relative to risk
- `2`: clean invalidation and attractive expected reward

### Category 8: Timing and confirmation `0 to 2`

- `0`: early, late, or unconfirmed
- `1`: reasonable timing
- `2`: trigger is clear and confirmation is present

## 3. Example grading bands

- `17 to 20`: A-tier, highest conviction
- `13 to 16`: B-tier, tradable if strategy conditions are met
- `9 to 12`: C-tier, usually pass unless special reason exists
- `<9`: no-trade by default

## 4. Why scoring should be strategy-specific

A mean-reversion setup and a momentum breakout should not be scored exactly the same way.

Examples:

- breakout systems should weight trend, volume, and acceptance more heavily
- mean-reversion systems should weight stretch from mean, exhaustion, and support more heavily
- catalyst systems should weight event quality more heavily

Best practice:

- keep a common base score
- add strategy-specific bonus or penalty fields

## 5. Hard disqualifiers

Some conditions should block a trade even if the score is high.

Examples:

- earnings event inside the forbidden holding window
- spread too wide for intended size
- stop distance too large for allowed risk
- market regime does not permit that strategy
- liquidity too low for reliable exit

## 6. Scoring examples

### Example A: Trend pullback in a leading stock

- Trend alignment: `3`
- Level quality: `3`
- Catalyst quality: `1`
- Volume: `1`
- Liquidity: `2`
- Market and sector alignment: `3`
- Risk/reward: `2`
- Timing and confirmation: `2`

Total: `17`

Interpretation:

- high-quality continuation setup

### Example B: Low-priced breakout with social-media hype

- Trend alignment: `2`
- Level quality: `1`
- Catalyst quality: `0`
- Volume: `2`
- Liquidity: `0`
- Market and sector alignment: `1`
- Risk/reward: `0`
- Timing and confirmation: `1`

Total: `7`

Interpretation:

- high motion, low quality

## 7. App design implications

Each setup record should include:

- `setup_score_total`
- `trend_score`
- `level_score`
- `catalyst_score`
- `volume_score`
- `liquidity_score`
- `context_score`
- `rr_score`
- `timing_score`
- `hard_disqualifier_flags`

This structure makes trade review far more useful than storing only entry and exit.

## 8. What to avoid

- using too many categories until the score becomes performative
- adjusting scores after the trade outcome is known
- letting a single impressive candle override weak context
- scoring without predefined definitions

## Bottom line

A setup score is a discipline tool. It forces the trader or the app to ask whether the trade has multiple aligned reasons to work, or whether it only looks exciting. The scoring model should be simple enough to apply consistently and strict enough to exclude noise.

## Research basis

This framework is an inference built from:

- trend and strategy work in `04-swing-trading-strategies.md`
- risk logic in `05-risk-management.md`
- market-structure work in `08-market-structure-and-conditions.md`
- catalyst and event logic in `21-catalyst-and-event-playbook.md`
- liquidity and execution constraints in `09-regulation-tax-and-trade-operations.md` and `24-execution-and-slippage-playbook.md`
