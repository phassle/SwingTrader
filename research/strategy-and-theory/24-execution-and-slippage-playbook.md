# Execution And Slippage Playbook For Swing Trading

Prepared by Codex on 2026-03-08. This file focuses on how orders should actually be executed in live swing trading. It complements `09-regulation-tax-and-trade-operations.md` and any future trade-management research.

## Why this matters

Many swing strategies look strong in backtests and weak in live trading because execution was treated as an afterthought. Live P&L depends on the difference between the theoretical trade and the executable trade.

## 1. First principle

Execution quality is a function of:

- order type
- liquidity
- spread
- time of day
- catalyst environment
- position size relative to available volume

If any of those variables changes, the same signal may require a different execution method.

## 2. Order types are risk tools

Investor.gov explains that:

- a `market order` prioritizes execution but not price
- a `limit order` sets a maximum buy price or minimum sell price, but may not execute
- a `stop order` becomes a market order when triggered
- a `stop-limit order` adds price control but can fail to execute

Operational meaning:

- market orders are most acceptable in highly liquid names during normal hours
- limit orders are safer in thinner names or when spread matters
- stop orders protect process, not price certainty
- stop-limit orders reduce price surprise but increase non-execution risk

## 3. When slippage is likely to be worst

Slippage usually expands:

- near the open
- near the close
- during extended hours
- during halts or resumptions
- after earnings and macro releases
- in low-float or low-volume names
- when size is too large relative to liquidity

The SEC's extended-hours bulletin notes that limit orders are often required in extended hours, partly because investors otherwise face unexpectedly bad prices.

## 4. Extended-hours execution deserves separate rules

Investor.gov warns that consolidated quote and trade data may not be as available during extended-hours trading, and that many firms accept only limit orders in those sessions.

Fidelity's extended-hours material also emphasizes that lower liquidity can widen bid-ask spreads enough to materially change profitability.

Practical rules:

- use separate execution logic for premarket and after-hours
- default to limit-based orders in extended hours
- reduce size when spreads widen materially
- treat extended-hours price as less reliable than regular-session price

## 5. Opening range and closing range behavior

### At the open

The first minutes of the session often contain:

- overnight repricing
- order imbalances
- spread dislocation
- false breakouts

Best use:

- wait for initial price discovery in names with elevated event risk
- avoid forcing entries in the first minutes unless the strategy explicitly depends on opening momentum

### Near the close

The close often carries:

- more stable volume than premarket
- portfolio rebalancing flows
- better confirmation for daily-chart setups

Best use:

- entries tied to daily confirmation often make more sense near the close than intraday guessing at the same level

## 6. Gap handling

Gap behavior changes execution logic.

### Gap in your favor

Questions to ask:

- is the gap likely to hold?
- is the name overextended relative to planned stop distance?
- is taking partial profit immediately better than waiting for continuation?

### Gap against you

Important reality:

- if the stock opens beyond the stop, the theoretical stop price is gone
- the trade must be managed from the open price and available liquidity, not from the original plan alone

Best practice:

- predefine what happens if the open gaps beyond the stop
- record realized gap slippage separately from ordinary stop-outs

## 7. Size relative to liquidity

A workable execution rule should consider position size relative to normal liquidity.

Examples:

- if the intended position is trivial relative to average daily dollar volume, execution friction may be acceptable
- if the order is meaningful relative to typical displayed liquidity, the trade should be sized down or skipped

This is why universe selection and execution cannot be separated.

## 8. Marketable limit orders are often a practical compromise

For many swing traders, the best balance is not a pure market order or a passive limit order. It is a `marketable limit order`, meaning a limit order placed at a price likely to execute immediately while still capping worst-case price.

Why it helps:

- improves price control
- reduces the chance of a shock fill
- still gives fast execution in liquid names

## 9. Execution decision tree

### Entry

- highly liquid, regular hours, urgent trigger: marketable order may be acceptable
- moderate liquidity: marketable limit order preferred
- thin liquidity or event tape: limit order or pass

### Stop exit

- ordinary liquid name: stop or alert-based marketable exit
- thin name: consider alert plus manual exit logic instead of blind stop-market dependence
- extended-hours or binary event risk: assume stop quality may be poor

### Profit-taking

- partial exits can use passive limits if liquidity is strong and urgency is low
- in fast event-driven moves, passive limits may miss fills while price reverses

## 10. Metrics to track in a journal

Execution quality should be measurable.

Track:

- intended entry price
- actual fill price
- intended exit price
- actual exit price
- spread at execution
- time of day
- order type used
- catalyst state
- slippage in cents and basis points

## 11. What to avoid

- market orders in illiquid names without a strong reason
- using stop price as if it were guaranteed execution price
- treating premarket prices as fully trustworthy
- sizing up in a name just because the setup looks attractive on a chart
- backtesting on close prices and assuming equivalent live fills

## Bottom line

Execution is part of the strategy, not an implementation detail. A swing system that does not specify order type, timing, session rules, and gap handling is incomplete.

## Sources

- Investor.gov, "Types of Orders"
  https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders

- Investor.gov, "Investor Bulletin: Understanding Order Types"
  https://www.investor.gov/index.php/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14

- Investor.gov, "Investor Bulletin: Stop, Stop-Limit, and Trailing Stop Orders"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15

- Investor.gov, "Extended-Hours Trading: Investor Bulletin"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-42

- Fidelity, "After Hours Trading"
  https://www.fidelity.com/viewpoints/active-investor/extended-hours-trading
