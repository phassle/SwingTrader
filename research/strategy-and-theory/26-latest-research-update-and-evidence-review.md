# Latest Research Update And Evidence Review

Prepared by Codex on 2026-03-08.

This file updates the research pack with newer or higher-signal evidence where multiple claims existed. The purpose is not to replace the whole pack, but to clarify which conclusions are best supported by recent research and official sources.

Primary focus areas:

- protective order handling
- calendar effects and seasonality
- sentiment indicators
- technical patterns and candlestick evidence

## 1. Canonical conclusion on protective exits

This is the clearest area where the pack needed a stronger source hierarchy.

### Best-supported conclusion

For protective exits, the default rule should be:

- use `limit-based logic` for entries
- use `marketable exit logic` or `stop-market logic` for protective exits in normal liquid trading
- do **not** use `stop-limit` as the default protective stop for swing trading

### Why

The SEC and Investor.gov are explicit on the tradeoff:

- a `stop order` becomes a market order when triggered
- a `stop-limit order` can fail to execute if the market moves through the limit price

That means a stop-limit may control price better, but it can fail at the exact moment the trader most needs protection. For swing trading, where gap risk and fast-moving opens matter, execution certainty is usually more important than price precision on a protective exit.

### Operational implication for the pack

If the app or written playbook needs one canonical default:

- `entry`: limit or marketable limit
- `protective stop`: stop-market or alert plus fast manual/marketable exit in thin names
- `stop-limit`: advanced exception, not default behavior

## 2. Seasonality: newer evidence is more mixed than classic trading lore

Some seasonality effects still appear in the literature, but the stronger conclusion from recent work is:

- broad, simple seasonal rules are weaker than older trading folklore implies
- sector-specific and context-specific seasonal effects look more defensible than universal calendar slogans

### January effect

Recent work continues to find that January-type effects can appear in some markets or subgroups, but the effect is not a stable universal rule. The newer evidence looks mixed across countries and market segments rather than uniformly strong.

Implication:

- `January effect` should be treated as a weak contextual prior, not as a standalone swing signal

### Santa Claus rally and year-end effects

Recent research still finds evidence for Christmas/Santa-Claus-type effects in some contexts, but this is better treated as a descriptive tendency than a trading rule with standalone edge.

Implication:

- year-end seasonality may be useful for context and watchlist bias
- it should not override trend, regime, catalyst, and execution quality

### Sector-specific seasonality

A stronger recent line of evidence is that seasonal effects may differ by sector. This is more actionable than saying "the whole market does X in month Y."

Implication:

- if seasonality is used in the app, it should be modeled by `sector + regime + month`, not by a universal market rule alone

## 3. Sentiment indicators: useful, but mostly as supplementary context

Recent research supports the idea that sentiment measures can carry predictive information, but the predictive strength is usually:

- time-varying
- horizon-dependent
- stronger in some subperiods than others

### CNN Fear and Greed Index

Recent evidence suggests the CNN Fear and Greed Index had predictive power for U.S. equity returns in earlier parts of its sample, but that power is time-varying rather than stable.

Implication:

- treat Fear and Greed as a `context indicator`, not a primary trigger
- avoid hard-coding simplistic rules like "Extreme Fear equals buy"

### AAII and related investor sentiment measures

Recent sentiment research still supports the general idea that investor sentiment matters, especially in uncertain periods, but these measures are not reliable enough to be used as standalone trade entries.

Implication:

- sentiment belongs in the `context score` or `regime score`
- it should not outrank price, liquidity, catalyst, and risk structure

## 4. Technical patterns still show value, but the strongest recent evidence is conditional

The most important update here is not "patterns are fake" or "patterns are magic." It is:

- technical patterns can still have predictive value
- that value appears stronger when patterns are combined with other information, especially sentiment and momentum context
- standalone rule-based candlestick or chart-pattern trading is still weaker than many retail materials suggest

### Recent research direction

Recent papers continue to find predictive value in technical patterns, including image-based pattern detection and candlestick-derived predictors. But the strongest recent results tend to come from:

- combining technical patterns with sentiment information
- combining patterns with broader momentum context
- using richer model-based detection rather than loose visual naming alone

### Implication for the existing pattern files

The research pack should interpret pattern material this way:

- `03-chart-patterns.md` is most useful as a pattern library and structural reference
- `11-candlestick-interpretation.md` and `12-candlestick-examples-and-scenarios.md` are directionally aligned with current evidence because they emphasize context, volume, confirmation, and location
- standalone reliability scores should be treated carefully unless tied to clearly documented methodology

## 5. Strongest current evidence hierarchy for the pack

If the research pack is turned into app logic, this is the best-supported hierarchy:

### Highest-confidence building blocks

- trend and momentum context
- catalyst awareness
- liquidity and execution quality
- explicit risk sizing
- regime filtering

### Medium-confidence building blocks

- chart structures
- sector rotation
- relative strength leadership
- volatility compression and expansion logic

### Lower-confidence standalone signals

- isolated candlestick names
- broad calendar slogans
- raw sentiment extremes without market-structure confirmation

## 6. Recommended canonical decisions

To reduce contradictions across the pack, the following defaults are best supported:

1. `Protective exits`
   Default to stop-market or execution-first protective logic, not stop-limit by default.

2. `Seasonality`
   Use as context only. Prefer sector-specific or regime-specific seasonality over universal slogans.

3. `Sentiment`
   Use as a supplementary context variable, not as a primary signal.

4. `Technical patterns`
   Treat them as conditional tools that need context, confirmation, and liquidity filters.

## 7. Practical app-design implications

If this research becomes product logic, the app should:

- rank execution certainty above ideal theoretical fill price for stops
- tag seasonality as `weak prior`, not `hard trigger`
- store sentiment as a contextual feature, not a direct trade command
- score patterns more highly only when they align with trend, catalyst, and volume

## Bottom line

The latest evidence does not invalidate swing trading. It narrows where the real edge is. The strongest support remains with momentum, trend continuation, catalyst-backed repricing, and disciplined execution. Newer research is more skeptical of simple standalone heuristics such as universal January rules, isolated candlestick names, or sentiment extremes used without context.

## Sources

- Investor.gov, "Investor Bulletin: Stop, Stop-Limit, and Trailing Stop Orders"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15

- Investor.gov, "Investor Bulletin: Understanding Order Types"
  https://www.investor.gov/index.php/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14

- SEC, "Stop Order"
  https://www.sec.gov/answers/stopord.htm

- Leippold, Wang, Yang, "Technical patterns and news sentiment in stock markets"
  Journal of Finance and Data Science, 2024
  https://www.sciencedirect.com/science/article/pii/S2405918824000308

- Swiss Finance Institute working paper page for the same research
  https://www.sfi.ch/en/publications/n-24-88-technical-patterns-and-news-sentiment-in-stock-markets

- Dai et al., "Forecasting stock returns: the role of VIX-based upper and lower shadow of Japanese candlestick"
  Financial Innovation, published 2025-01-04
  https://link.springer.com/article/10.1186/s40854-024-00682-8

- Mersal, Karaoğlan, Kutucu, "Enhancing market trend prediction using convolutional neural networks on Japanese candlestick patterns"
  PeerJ Computer Science, published 2025-02-27
  https://peerj.com/articles/cs-2719/

- "Sector-specific calendar anomalies in the US equity market"
  International Review of Financial Analysis, 2024
  https://www.sciencedirect.com/science/article/pii/S1057521924002795

- "Comparative analysis of stochastic seasonality, January effect and market efficiency between emerging and industrialized markets"
  Heliyon, 2024
  https://www.sciencedirect.com/science/article/pii/S2405844024043329

- "January effect, Lunar New Year effect, and liquidity preference"
  Global Finance Journal, 2025
  https://www.sciencedirect.com/science/article/pii/S1044028325000912

- "The CNN Fear and Greed Index as a predictor of US equity index returns: Static and time-varying Granger causality"
  Finance Research Letters, 2025
  https://www.sciencedirect.com/science/article/abs/pii/S1544612324015216

- Sakowski, "Investor sentiment, stock returns and trading volume"
  University of Warsaw Working Paper 2024-18
  https://econpapers.repec.org/paper/warwpaper/2024-18.htm
