---
name: Signal Scoring for SwingTrader
description: Evaluate and score swing trading setups across eight dimensions. Use when analyzing signal quality, evaluating technical setups, discussing multi-timeframe alignment, assessing risk/reward, or determining "is this a good trade?"
trigger_keywords:
  - evaluating signals
  - scoring setups
  - setup quality
  - technical indicators
  - chart patterns
  - candlestick analysis
  - multi-timeframe analysis
  - "is this a good trade"
---

# Signal Scoring System

Systematic evaluation framework for swing trading setups on Nasdaq Stockholm Large Cap (.ST tickers). All scores are agent-facing diagnostic tools—not black-box ratings, but structured inputs for execution decisions.

## 0-20 Scoring System

Score setups across eight categories. Each category has defined points available.

| Category | Max | Criteria |
|----------|-----|----------|
| **Trend Alignment** | 3 | Weekly + Daily trend structure, higher timeframe bias |
| **Level Quality** | 3 | Support/resistance structure, breakout clarity, pullback setup |
| **Catalyst Quality** | 3 | Volume spike, oscillator divergence, pattern completion |
| **Volume** | 2 | Entry bar volume vs baseline, breakout confirmation |
| **Liquidity** | 2 | Spread, bid-ask depth, slippage risk |
| **Market/Sector Alignment** | 3 | OMX30 regime, sector rotation, correlation risk |
| **Risk/Reward** | 2 | Stop placement, target distance, R/R ratio ≥ 1:2 |
| **Timing/Confirmation** | 2 | 4H-1H alignment, oscillator confirmation, candle structure |
| **TOTAL** | **20** | |

## Grade Bands

| Grade | Range | Action |
|-------|-------|--------|
| A-tier | 17–20 | High conviction setups. Execute with standard position sizing. |
| B-tier | 13–16 | Quality setups with minor gaps. Execute with caution. Monitor entries. |
| C-tier | 9–12 | Marginal setups. Trade only if risk/reward is exceptional. Consider pass. |
| <9 | Below 9 | No-trade zone. Insufficient edge. Wait for better setup. |

## Hard Disqualifiers (Score = 0)

These conditions invalidate a setup regardless of other scores:

1. **Earnings Window** — Stock reports earnings within 5 trading days. Volatility risk exceeds position R/R.
2. **Spread Too Wide** — Bid-ask spread >1% on entry. Slippage eats edge.
3. **Stop Exceeds Risk Budget** — Required stop places position risk >2% portfolio (or >1R on this trade). Unacceptable loss magnitude.
4. **Regime Prohibits** — OMX30 in confirmed downtrend + stock in sector weakness + no divergence signal. Regime override required.
5. **Liquidity Too Low** — ADV <50K shares or 10-day VWAP volume <100M SEK. Execution risk too high.

If ANY disqualifier is true: **Score = 0. Do not trade.**

## Scoring Guidelines by Category

### Trend Alignment (0–3)

- **3 pts**: Weekly trend supports entry direction + Daily in aligned pullback. All higher timeframes green.
- **2 pts**: Daily trend aligned; Weekly mixed but not opposed. One higher timeframe compromise.
- **1 pt**: Daily aligned but Weekly unclear or slightly opposing. Lower timeframe saves setup.
- **0 pts**: Weekly + Daily opposed or no clear trend structure.

### Level Quality (0–3)

- **3 pts**: Clear prior swing high/low, breakout on first touch with acceptance, OR textbook pullback to defined level.
- **2 pts**: Level exists but breakout is softer OR pullback is into general zone rather than exact level.
- **1 pt**: Level is approximate; breakout or pullback is unclear.
- **0 pts**: No defined level structure.

### Catalyst Quality (0–3)

- **3 pts**: Volume spike >150% baseline on entry bar + Oscillator divergence (RSI/MACD) OR completed chart pattern (flag, channel breakout).
- **2 pts**: One catalyst present in full (volume spike OR confirmed divergence OR pattern).
- **1 pt**: Weak catalyst (volume +50%, or oscillator hint, or pattern forming).
- **0 pts**: No catalyst; passive breakout or pullback.

### Volume (0–2)

- **2 pts**: Entry bar volume >120% of 20-bar SMA. Breakout bar shows spike.
- **1 pt**: Entry bar volume 100–120% of baseline. Acceptable but not exceptional.
- **0 pts**: Entry bar volume <100% baseline. Low participation.

### Liquidity (0–2)

- **2 pts**: Spread <0.3%, 10-day VWAP volume >200M SEK, ADV >100K.
- **1 pt**: Spread 0.3–0.6%, volume acceptable, ADV 50–100K.
- **0 pts**: Spread >0.6%, low volume, or ADV <50K.

### Market/Sector Alignment (0–3)

- **3 pts**: OMX30 in uptrend + Stock sector in rotation in + Stock shows relative strength.
- **2 pts**: OMX30 neutral + Sector tailwind, OR OMX30 up but sector choppy.
- **1 pt**: OMX30 in confirmed downtrend but stock diverging positively, OR sector headwind but setup is isolated strength.
- **0 pts**: OMX30 down + Sector down + Stock correlated to both.

### Risk/Reward (0–2)

- **2 pts**: R/R ≥ 1:2.5. Stop is tight and logical. Position risk <1% portfolio.
- **1 pt**: R/R = 1:1.5 to 1:2.4. Stop is reasonable; position risk 1–1.5% portfolio.
- **0 pts**: R/R <1:1.5 or position risk >1.5% portfolio.

### Timing/Confirmation (0–2)

- **2 pts**: 4H oscillator aligned with 1H entry + Candle shows clean structure (no wick rejection).
- **1 pt**: 4H-1H alignment partial, or candle structure shows slight hesitation.
- **0 pts**: 4H oscillator diverging from 1H, or candle shows rejection (long wick on entry bar).

## Multi-Timeframe Decision Gates

**Sequential alignment required. Reject if any gate fails.**

### Gate 1: Weekly Structure
- Does the weekly chart support entry direction (or at minimum not oppose)?
- If weekly is in severe downtrend and stock is correlated: FAIL (unless divergence signal present).
- **Pass criteria**: Weekly trend neutral or favorable, or weekly is choppy but daily pullback is clean.

### Gate 2: Daily Trend & Pullback
- Is the daily in trend (uptrend for longs, downtrend for shorts)?
- Is the pullback reasonable (not 80%+ retracing the move)?
- **Pass criteria**: Daily trend clear, pullback <60% of prior move.

### Gate 3: 4H/1H Alignment
- Does 4H oscillator (RSI, MACD) align with 1H setup?
- Is 1H candle structure clean on entry bar?
- **Pass criteria**: Both oscillators aligned (not diverging), candle closes on entry (not wick-rejected).

**If all three gates pass**: Proceed to point-based scoring.
**If any gate fails**: Score cannot exceed 8 (C-tier ceiling). Consider pass.

## Reference Documents

Deeper guidance on scoring inputs:

- **Setup Quality Scoring Framework**: `research/strategy-and-theory/23-setup-quality-scoring.md` — Foundational methodology.
- **Technical Indicators**: `research/strategy-and-theory/02-technical-indicators.md` — RSI, MACD, Bollinger Bands applied to Swedish large cap.
- **Chart Patterns**: `research/strategy-and-theory/03-chart-patterns.md` — Flags, channels, consolidation patterns.
- **Candlestick Analysis**: `research/strategy-and-theory/11-candlestick-interpretation.md` — Entry candle structure, rejection signals.
- **Multi-Timeframe Analysis**: `research/strategy-and-theory/32-multi-timeframe-analysis.md` — Coherence across weekly/daily/4H/1H.
- **Empirical Evidence**: `research/strategy-and-theory/10-empirical-evidence-and-edge-quality.md` — Edge validation, sample size requirements.

## Practical Notes

- **Scoring is for edge measurement, not confidence inflation.** A B-tier setup is a B-tier setup. Sizing and discipline matter more than raw score.
- **Hard disqualifiers override score.** If earnings are in 3 days, the score is irrelevant—do not trade.
- **Use scores to compare setups within the same session.** Compare signal A (16) vs signal B (12) to prioritize execution order.
- **Oscillator confirmation is not required but valuable.** A clean level + volume is tradeable even without RSI/MACD alignment; alignment just adds confirmation.
- **On Swedish large cap, liquidity gates are strict.** Most .ST tickers are less liquid than US peers. Poor liquidity is non-negotiable disqualifier.
