# Swing Trading Research Map And Sources

Prepared by Codex on 2026-03-08.

This pack is intentionally scoped to complement the parallel files already assigned in `research/`:

- `01-swing-trading-fundamentals.md`
- `02-technical-indicators.md`
- `03-chart-patterns.md`
- `04-swing-trading-strategies.md`
- `05-risk-management.md`
- `06-apis-and-technology.md`
- `07-backtesting-and-performance.md`
- `08-market-structure-and-conditions.md`

To avoid collisions, these notes focus on topics that were not explicitly assigned above:

- U.S. regulatory and account constraints for swing traders
- Tax and settlement issues that change real-world trade design
- Order handling and execution risks
- Empirical evidence on where swing-trading edge is strongest or weakest

## Files added by Codex

- `09-regulation-tax-and-trade-operations.md`
- `10-empirical-evidence-and-edge-quality.md`
- `11-candlestick-interpretation.md`
- `12-candlestick-examples-and-scenarios.md`
- `21-catalyst-and-event-playbook.md`
- `22-watchlist-and-universe-selection.md`
- `23-setup-quality-scoring.md`
- `24-execution-and-slippage-playbook.md`
- `25-regime-to-strategy-mapping.md`
- `26-latest-research-update-and-evidence-review.md`
- `27-swedish-market-adaptation.md`
- `28-trading-psychology-and-behavioral-discipline.md` (2026-03-10)
- `29-position-scaling-and-pyramiding.md` (2026-03-10)
- `30-sector-rotation-and-economic-cycles.md` (2026-03-10)
- `31-gap-trading-strategies.md` (2026-03-10)
- `32-multi-timeframe-analysis.md` (2026-03-10)

## Suggested cross-links for other agents

- `01-swing-trading-fundamentals.md`
  Add the current U.S. pattern day trader threshold, T+1 settlement, and cash-vs-margin account tradeoffs.
  Cross-link to `28-trading-psychology-and-behavioral-discipline.md` for psychological foundations.

- `05-risk-management.md`
  Pull in the execution notes on stop orders, gap risk, after-hours liquidity, and circuit breakers.
  Cross-link to `28-trading-psychology-and-behavioral-discipline.md` for emotional risk management.
  Cross-link to `29-position-scaling-and-pyramiding.md` for advanced position management.
  Cross-link to `31-gap-trading-strategies.md` for gap risk management specifics.

- `07-backtesting-and-performance.md`
  Pull in the evidence notes on momentum, reversal, catalyst drift, and implementation-cost drag.

- `08-market-structure-and-conditions.md`
  Pull in the sections on volatility halts, auction behavior, and overnight/event risk.
  Cross-link to `30-sector-rotation-and-economic-cycles.md` for economic cycle context.

- `03-chart-patterns.md`
  Link to `11-candlestick-interpretation.md` for candle anatomy, context, wick/body reading, and confirmation rules.
  Link to `12-candlestick-examples-and-scenarios.md` for concrete swing-trading examples and decision rules.
  Cross-link to `32-multi-timeframe-analysis.md` for pattern confirmation across timeframes.

- `04-swing-trading-strategies.md`
  Cross-link to `21-catalyst-and-event-playbook.md`, `23-setup-quality-scoring.md`, and `25-regime-to-strategy-mapping.md`.
  Cross-link to `29-position-scaling-and-pyramiding.md` for position management within strategies.
  Cross-link to `30-sector-rotation-and-economic-cycles.md` for sector-based strategy selection.
  Cross-link to `32-multi-timeframe-analysis.md` for setup identification framework.

- `06-apis-and-technology.md`
  Cross-link to `21-catalyst-and-event-playbook.md` and `22-watchlist-and-universe-selection.md` for the data objects an app should track.
  Cross-link to `30-sector-rotation-and-economic-cycles.md` for sector data requirements.

- `16-stock-screening-playbook.md`
  Cross-link to `22-watchlist-and-universe-selection.md` so the scanner operates on a defined universe instead of the whole market.
  Cross-link to `30-sector-rotation-and-economic-cycles.md` for sector-filtered screening.

- `18-correlation-and-portfolio-construction.md`
  Cross-link to `25-regime-to-strategy-mapping.md` where strategy mix should change with regime.
  Cross-link to `30-sector-rotation-and-economic-cycles.md` for sector diversification and correlation.

- `13-trading-plan-and-daily-routine.md`
  Cross-link to `26-latest-research-update-and-evidence-review.md` for the canonical order-handling recommendation based on official SEC/Investor.gov guidance.
  Cross-link to `28-trading-psychology-and-behavioral-discipline.md` for daily routines and psychological preparation.

- `14-trade-management.md`
  Cross-link to `29-position-scaling-and-pyramiding.md` for scaling in/out techniques.
  Cross-link to `31-gap-trading-strategies.md` for managing positions through gaps.
  Cross-link to `32-multi-timeframe-analysis.md` for stop placement and trade management frameworks.

- `17-trading-journal-framework.md`
  Cross-link to `28-trading-psychology-and-behavioral-discipline.md` for psychological journaling components.

## Scope assumptions

- Primary focus: U.S.-listed equities and ETFs
- Date sensitivity: current as of 2026-03-08
- This is research support, not legal, tax, or investment advice

## Source set

### U.S. regulation, settlement, and execution

- SEC Investor.gov, "Margin: Borrowing Money to Pay for Stocks"
  https://www.investor.gov/introduction-investing/investing-basics/glossary/margin-borrowing-money-pay-stocks

- FINRA, "Day Trading"
  https://www.finra.org/investors/investing/investment-products/stocks/day-trading

- SEC, "The New Stock Market: Sense and Nonsense"
  https://www.sec.gov/about/reports-publications/investorpubsnewstockmkt

- SEC, "An Introduction to Limit Orders"
  https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/introduction-limit-orders

- SEC Investor.gov, "Trading in Cash Accounts"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/trading-cash-accounts

- SEC, "Investor Bulletin: Trading Halts"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/investor-10

- FINRA, "Understanding Margin Accounts"
  https://www.finra.org/investors/learn-to-invest/advanced-investing/understanding-margin-accounts

- FINRA, "Understanding Short Selling"
  https://www.finra.org/investors/insights/understanding-short-selling

### Tax treatment

- IRS, Topic No. 409, Capital Gains and Losses
  https://www.irs.gov/taxtopics/tc409

- IRS, Publication 550, Investment Income and Expenses
  https://www.irs.gov/forms-pubs/about-publication-550

### Empirical evidence

- NBER Working Paper 7159, "Profitability of Momentum Strategies: An Evaluation of Alternative Explanations"
  https://www.nber.org/papers/w7159

- NBER Reporter, "Momentum and the Cross-Section of Stock Returns"
  https://www.nber.org/reporter/2021number4/momentum-and-cross-section-stock-returns

- NBER Digest, "Bad News Travels Slowly: Size, Analyst Coverage, and the Profitability of Momentum Strategies"
  https://www.nber.org/digest/nov04/bad-news-travels-slowly-size-analyst-coverage-and-profitability-momentum-strategies

- JSTOR abstract, Lehmann (1990), "Fads, Martingales, and Market Efficiency"
  https://www.jstor.org/stable/2938266

### Catalysts, event calendars, liquidity, and concentration

- SEC final rule on Form 8-K disclosure timing
  https://www.sec.gov/rules-regulations/2004/03/additional-form-8-k-disclosure-requirements-acceleration-filing-date

- Federal Reserve, FOMC meeting calendars and information
  https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

- Federal Reserve calendar pages
  https://www.federalreserve.gov/newsevents/

- U.S. Bureau of Labor Statistics, CPI
  https://www.bls.gov/cpi/

- FDA Advisory Committee Calendar
  https://www.fda.gov/advisory-committees/advisory-committee-calendar

- FINRA, "Low-Priced Stocks Can Spell Big Problems"
  https://www.finra.org/investors/insights/low-priced-stocks-big-problems

- FINRA, "Concentrate on Concentration Risk"
  https://www.finra.org/investors/insights/concentration-risk

- Fidelity, "Do you hold too much in one investment?"
  https://www.fidelity.com/learning-center/trading-investing/too-much-one-investment

- Investor.gov, "Types of Orders"
  https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders

- Investor.gov, "Extended-Hours Trading: Investor Bulletin"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-42

### Trading psychology and behavioral finance

- Trading Psychology: Mind Over Market, Faster Capital
  https://fastercapital.com/content/Trading-Psychology--Mind-Over-Market--The-Psychology-of-Swing-Trading.html

- Trading Psychology: Control Emotions for Better Trades, eVest Blog
  https://www.evest.blog/trading-blog/trading-psychology/

- Behavioral Finance / Psychology Trading Articles, TradingHabits
  https://www.tradinghabits.com/articles/behavioral-finance

- Swing Trading Psychology Mastery, Traders Mastermind
  https://tradersmastermind.com/swing-trading-psychology-mastery/

- Market Psychology in Swing Trading, Disfold Blog
  https://blog.disfold.com/market-psychology-swing-trading/

### Position management and pyramiding

- Pyramiding Strategies: Scaling Into Trades To Boost Returns, LuxAlgo
  https://www.luxalgo.com/blog/pyramiding-strategies-scaling-into-trades-to-boost-returns/

- The Ultimate Guide to Pyramiding in Trading, QuantStrategy
  https://quantstrategy.io/blog/the-ultimate-guide-to-pyramiding-in-trading-how-to-scale/

- Mastering Position Sizing: Advanced Strategies, QuantStrategy
  https://quantstrategy.io/blog/mastering-position-sizing-advanced-strategies-for-scaling/

### Sector rotation and economic cycles

- Sector Rotation Strategy: Complete Guide, Market Gauge
  https://marketgauge.com/resources/sector-rotation/

- Sector Rotation Strategy: How to Time Market Cycles, One Portfolio
  https://oneportfolio.io/en/blog/sector-rotation-strategy-guide/

- Sector Rotation Analysis for Swing Traders, OpenSwingTrading
  https://www.openswingtrading.com/blog/sector-rotation-analysis-how-it-works-for-swing-traders

### Gap trading

- Overnight Gap Trading Strategies, BluSky Blog
  https://blog.blusky.pro/blusky-blog/overnight-gap-trading-strategies

- The Complete Gap Trading Strategy Guide, Mind Math Money
  https://www.mindmathmoney.com/articles/the-complete-gap-trading-strategy-guide-how-to-identify-and-trade-price-gaps-like-a-professional

- Weekend Risk Management, Volatility Box
  https://volatilitybox.com/docs/managing-overnight-weekend-risk/

### Multi-timeframe analysis

- How To Perform A Multi TimeFrame Analysis, Tradeciety
  https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis

- Multi Timeframe Analysis Trading Strategy, Mind Math Money
  https://www.mindmathmoney.com/articles/multi-timeframe-analysis-trading-strategy-the-complete-guide-to-trading-multiple-timeframes

- The Essential Guide To Multi-Timeframe Analysis, TradingWithRayner
  https://www.tradingwithrayner.com/multi-timeframe-analysis/

### Practitioner references used only for implementation context

- Charles Schwab, "Average True Range Indicator and Volatility"
  https://www.schwab.com/learn/story/average-true-range-indicator-and-volatility

- Fidelity, "Simple Moving Average"
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/sma

## Notes on evidence quality

- Regulator and IRS sources were used for rules, account mechanics, and tax treatment.
- Academic sources were used for edge quality and expected behavior, not for exact retail implementation rules.
- Broker education pages were used only for common implementation conventions around indicators and volatility sizing.
