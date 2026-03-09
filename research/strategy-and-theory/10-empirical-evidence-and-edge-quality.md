# Swing Trading Empirical Evidence And Edge Quality

Prepared by Codex on 2026-03-08. This file summarizes what academic evidence says about the parts of swing trading that are most defensible and where retail implementations usually overstate edge.

## 1. The strongest broad evidence supports momentum, not arbitrary indicator crosses

The most durable empirical result connected to swing trading is `momentum`.

- Jegadeesh and Titman showed that buying stocks with strong prior relative performance and selling weak ones produced positive abnormal returns over subsequent `3- to 12-month` holding windows.
- Later work summarized by NBER shows momentum remains one of the most persistent cross-sectional return patterns across markets and long sample periods.

Why this matters for swing trading:

- Trend-following and breakout systems have a stronger research foundation than rules built only on isolated indicator events.
- A pullback-within-trend setup is usually easier to defend empirically than a pure "RSI crossed X" setup with no trend or catalyst context.

## 2. Short-horizon reversal also exists, but it is more fragile

Academic work also finds short-term reversals.

- Lehmann documented that recent short-term losers tended to outperform recent winners over the following week.
- In practice, this type of effect is often strongest where temporary liquidity pressure, overreaction, or forced flows distort price.

Why this matters:

- Mean-reversion swing trading can work, but it is not a free substitute for momentum.
- Reversal edges are usually more sensitive to spreads, slippage, borrow costs, and exact execution timing.
- The weaker the liquidity and the faster the holding period, the more implementation cost matters.

## 3. Earnings and news catalysts create one of the clearest swing-trading opportunities

Evidence around `post-earnings announcement drift` and slow information diffusion is highly relevant.

- NBER research on momentum and information diffusion shows that bad news often travels slowly, especially for smaller-cap names and companies with lower analyst coverage.
- This is consistent with the broader post-earnings-announcement-drift literature: prices do not always fully incorporate earnings news immediately, and a portion of the move can continue over days or weeks.

Why this matters:

- Catalyst-based swing trading is more defensible than signal-only trading with no information event behind it.
- Earnings gaps, guidance changes, analyst revisions, and major news can justify continuation setups that would otherwise look "overextended" on a chart.
- The tradeoff is that event-driven setups carry much higher overnight and gap risk.

## 4. Momentum is real, but momentum crashes are real too

A major implementation mistake is to treat momentum as a smooth edge.

- NBER’s research summaries emphasize that momentum is persistent, but not stable in every regime.
- Momentum strategies can experience sharp reversals, especially after market turning points when previously weak names rebound violently.

Why this matters:

- Trend-following swing systems need exposure controls, not just entry rules.
- A book concentrated in the same crowded factor can suffer correlated failure even if each single-name chart looked acceptable.
- Regime awareness is not optional when trading momentum-heavy baskets.

## 5. Evidence quality differs by setup type

Not all common swing-trading ideas have equal support.

## Evidence grading

`Higher support`

- relative-strength momentum
- breakout or pullback continuation in established trends
- catalyst continuation after earnings or major news

`Moderate support, but implementation-sensitive`

- short-horizon mean reversion after extreme moves
- volatility contraction and expansion setups
- moving-average trend filters

`Weaker support without extra context`

- standalone oscillator signals
- chart patterns with loose or subjective identification rules
- highly parameterized systems tuned to one market regime

## 6. Backtests often overstate what a trader can actually capture

There is a large gap between academic return patterns and retail execution.

Common sources of overstatement:

- ignoring spread and slippage
- assuming fills at signal price instead of executable price
- ignoring borrow fees on shorts
- ignoring halts and overnight gaps
- ignoring T+1 settlement constraints in cash accounts
- using survivorship-biased universes
- tuning parameters until the strategy fits one regime

Implication:

- A valid swing-trading backtest should test net returns after realistic friction, not just gross signal quality.

## 7. Practical conclusions for strategy design

The research base supports a specific hierarchy of ideas:

1. Start with `cross-sectional momentum`, `trend continuation`, or `catalyst drift`.
2. Add risk controls for factor crowding, volatility expansion, and overnight event exposure.
3. Treat short-term mean reversion as a narrower, more execution-sensitive playbook.
4. Be skeptical of indicator-only systems that do not explain why the order flow should persist or reverse.

## 8. Good research questions for the other files

For `04-swing-trading-strategies.md`:

- Which strategies are explicitly momentum-based versus reversal-based?
- What market regime tends to help or hurt each?

For `05-risk-management.md`:

- How is portfolio concentration controlled when several names express the same factor bet?
- Are gaps and halts modeled separately from ordinary stop-loss behavior?

For `07-backtesting-and-performance.md`:

- Are costs modeled at the order type and liquidity level?
- Is the test isolating signal edge from universe-selection bias?

## Bottom line

The most defensible swing-trading edges come from a small set of repeatable market behaviors: medium-term momentum, short-lived overreaction, and slow post-news repricing. Most retail underperformance comes from trying to monetize these effects with too much turnover, too much discretion, or too little respect for implementation cost.

## Sources

- NBER Working Paper 7159, "Profitability of Momentum Strategies: An Evaluation of Alternative Explanations"
  https://www.nber.org/papers/w7159

- NBER Reporter, "Momentum and the Cross-Section of Stock Returns"
  https://www.nber.org/reporter/2021number4/momentum-and-cross-section-stock-returns

- NBER Digest, "Bad News Travels Slowly: Size, Analyst Coverage, and the Profitability of Momentum Strategies"
  https://www.nber.org/digest/nov04/bad-news-travels-slowly-size-analyst-coverage-and-profitability-momentum-strategies

- JSTOR abstract, Lehmann (1990), "Fads, Martingales, and Market Efficiency"
  https://www.jstor.org/stable/2938266

- Charles Schwab, "Average True Range Indicator and Volatility"
  https://www.schwab.com/learn/story/average-true-range-indicator-and-volatility

- Fidelity, "Simple Moving Average"
  https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/sma
