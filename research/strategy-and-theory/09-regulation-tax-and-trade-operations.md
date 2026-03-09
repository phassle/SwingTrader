# U.S. Swing Trading: Regulation, Tax, And Trade Operations

Prepared by Codex on 2026-03-08. This file is meant to complement strategy, risk, and market-structure research by covering account mechanics and real-world execution constraints for U.S. equity and ETF swing traders.

## 1. Account structure changes what is possible

Swing traders often treat setup quality as the main variable, but account type can be equally important.

- A `margin account` allows borrowed funds, but borrowing amplifies both gains and losses. SEC Investor.gov notes that margin interest applies and brokers can impose maintenance calls or liquidate positions if equity falls too far.
- A `cash account` avoids margin interest and the pattern day trader rule, but it introduces settlement constraints. Since the U.S. equity market moved to `T+1` settlement on `May 28, 2024`, sale proceeds generally settle on the next business day rather than immediately.
- In practice, active swing traders often choose between:
  - margin flexibility with stricter risk discipline
  - cash-account simplicity with tighter trade pacing because unsettled-funds violations can occur

## 2. Pattern day trader rules still matter to swing traders

Even if the intended holding period is multiple days, active management can accidentally cross into day trading.

- FINRA says a `pattern day trader` is generally a margin customer who executes `4 or more` day trades within `5 business days`, provided those day trades are more than `6%` of total trades in the margin account during that period.
- FINRA also states that pattern day traders must maintain at least `$25,000` of equity in the margin account before continuing to day trade.
- This matters to swing traders because partial exits, same-day stop-outs, and same-day re-entries can count as day trades even when the original plan was to hold overnight.

Operational implication:

- If the strategy may involve intraday exits or same-day repairs, it should be modeled with PDT constraints from the start rather than treated as a pure swing strategy.

## 3. Cash-account violations are operational, not theoretical

Swing traders using cash accounts need to understand settlement-related restrictions.

- SEC Investor.gov warns that using unsettled proceeds to buy a security and then selling that new position before the original sale settles can trigger a `good faith violation`.
- SEC Investor.gov also highlights `free riding`, where purchases are effectively paid for by selling the purchased securities rather than with fully settled cash already in the account.

Operational implication:

- A cash-account swing system should track `trade date`, `settlement date`, and `available settled cash` in the trade log.
- Backtests that ignore settlement can materially overstate achievable turnover in smaller accounts.

## 4. Order type choice is part of risk management

Order handling is not a clerical detail. It changes fill quality and realized risk.

- SEC Investor.gov explains that a `market order` prioritizes execution, not price.
- A `limit order` prioritizes price control, but it may not execute.
- A `stop order` can become a market order when triggered. In fast markets or overnight gaps, the execution price can be materially worse than the stop price.
- A `stop-limit order` adds price control, but it can fail to execute entirely if price moves through the limit.

Practical takeaway:

- For liquid names during normal hours, marketable orders can be acceptable when speed matters more than a few cents of slippage.
- For thinner names, large positions, or extended-hours trading, limit-based execution is usually safer.
- A stop is not a guarantee against gap risk. It is only a trigger mechanism.

## 5. Pre-market and after-hours trading raise execution risk

SEC guidance on the modern market structure stresses that trading outside normal hours often comes with:

- lower displayed liquidity
- wider spreads
- less reliable price discovery
- higher volatility around headlines and earnings

Operational implication:

- If a strategy holds through earnings or macro events, the risk model should explicitly assume worse-than-normal exit quality.
- Stop placement rules that look acceptable in regular hours may be ineffective overnight because the next executable price can be far from the prior close.

## 6. Short selling adds separate risk channels

Short-side swing trading is not just the long setup inverted.

- FINRA’s short-selling guidance notes distinct risks, including theoretically unlimited upside risk in the stock price, borrow constraints, and the possibility that brokers may force position closure.
- Hard-to-borrow names can carry stock-loan fees that meaningfully reduce edge.
- Short positions can also be destabilized by squeezes, forced buy-ins, and headline-driven gaps.

Operational implication:

- Short strategies should include `borrow availability`, `borrow cost`, and `gap-to-open` stress testing.
- A backtest that omits borrow friction will usually overstate net performance on the short side.

## 7. Market-wide halts and volatility controls matter for overnight risk

Swing traders are exposed to more than normal stop-loss behavior.

- SEC Investor.gov describes market-wide circuit breakers tied to S&P 500 declines of `7%`, `13%`, and `20%`.
- Regulators can also halt individual names for news-pending events, order imbalances, or volatility controls.

Operational implication:

- Position size should reflect the possibility that a stock cannot be exited exactly when the trader wants.
- Concentrated overnight exposure into earnings, biotech catalysts, or macro announcements is not equivalent to ordinary overnight exposure.

## 8. Tax treatment penalizes high turnover

Tax drag is one of the most under-modeled costs in swing trading.

- IRS Topic No. 409 explains that gains on positions held `1 year or less` are typically `short-term capital gains`, generally taxed at ordinary income tax rates.
- IRS Publication 550 explains the `wash sale` rule: if a loss position is sold and a substantially identical security is purchased within `30 days before or after` the sale, the loss is generally disallowed at that time and added to basis.

Operational implication:

- Mean-reversion systems that repeatedly re-enter the same ticker can create accounting complexity and deferred-loss recognition.
- Post-tax returns can differ substantially from pre-tax backtests, especially in taxable accounts with frequent turnover.

## 9. Trader tax status and mark-to-market elections are specialized topics

Frequent traders sometimes discuss trader tax status and Section 475 mark-to-market treatment. Those topics are real, but they are not default outcomes.

- IRS Publication 550 documents mark-to-market treatment and related election mechanics.
- The election process is timing-sensitive and fact-specific.

Operational implication:

- Any strategy expected to generate very high turnover should be reviewed with a qualified tax professional before assuming mark-to-market treatment is available.

## 10. What this means for system design

A robust swing-trading workflow should include rules outside pure signal generation:

- account type: cash or margin
- turnover ceiling imposed by settlement or PDT rules
- allowed trading session: regular hours only, or extended hours with different order logic
- execution type by instrument liquidity
- earnings and event exposure policy
- short-side borrow and fee checks
- tax-lot and wash-sale awareness for taxable accounts

---

## Swedish Market: Regulation, Tax, and Trade Operations

> **Full reference:** See `27-swedish-market-adaptation.md` for complete details on Swedish market adaptation.

### Swedish regulatory framework

Swedish trading is regulated by **Finansinspektionen (FI)** and governed by EU-wide regulations (MiFID II, MAR, EU SSR). Key differences from the US framework:

- **No Pattern Day Trader (PDT) rule.** There are no restrictions on day trade frequency, no minimum equity requirements for active trading, and no distinction between cash and margin accounts for PDT purposes. Sections 2 and 3 above are US-specific and do not apply to Swedish traders.
- **No good faith violations or free riding rules.** ISK accounts (see below) provide immediate buying power even before settlement.
- **Settlement is T+2** (the EU is expected to move to T+1 around late 2027). In practice, Avanza grants immediate buying power on ISK accounts regardless.
- **Short selling** is governed by the EU Short Selling Regulation (EU 236/2012). Naked shorting is prohibited. Net short positions above 0.1% of issued share capital must be reported to FI; positions above 0.5% are publicly disclosed.
- **Insider trade reporting** follows MAR (Market Abuse Regulation). PDMRs (Persons Discharging Managerial Responsibilities) must notify FI within 3 business days (vs. 2 business days for SEC Form 4 in the US).
- **Circuit breakers** are per-stock dynamic volatility interruptions on Nasdaq Nordic, not the market-wide S&P 500-based halts used in the US.

### Swedish tax treatment

Swedish tax rules are fundamentally different from the US system described in sections 8-9 above.

**Investeringssparkonto (ISK) -- the default choice for most Swedish traders:**

- ISK is a tax-advantaged account type with **no capital gains tax** on individual trades.
- Instead, the entire account value is subject to an annual flat-rate tax (schablonbeskattning): statslanerantan + 1 percentage point, applied to the account's average value. In practice this is approximately **0.9% of account value per year** (varies with the government borrowing rate).
- Losses on individual trades are irrelevant for tax purposes -- there is no deduction for losses and no tax on gains.
- Dividends received in an ISK are included in the schablonbeskattning calculation; no additional dividend tax on Swedish dividends.
- Foreign dividends (e.g., US stocks held in ISK) are subject to withholding tax (typically 15% after treaty reduction), which is **not** recoverable.
- ISK has no withdrawal restrictions, no age requirements, and no contribution limits.

**Kapitalforsakring (KF):**

- Similar to ISK in tax treatment (schablonbeskattning), but the account is technically an insurance product.
- Cannot hold all instrument types. Slightly different rules for foreign dividends.
- Less common than ISK for active trading.

**Regular depot (vanligt aktie- och fondkonto):**

- Capital gains are taxed at a **flat 30%** rate (inkomst av kapital).
- Losses are deductible: 70% of losses can offset other capital income. Losses on listed securities can be deducted fully against gains on listed securities.
- **No wash sale rule.** Swedish tax law has no equivalent of the US 30-day wash sale rule (IRS Pub 550, Section 8 above). A loss is deductible immediately even if the same security is repurchased the next day.
- No distinction between short-term and long-term capital gains. The 30% rate applies regardless of holding period.
- Sections 9 (Trader tax status / Section 475 mark-to-market) above are US-only and have no Swedish equivalent.

**Tax summary comparison:**

| Feature | United States | Sweden (ISK) | Sweden (Depot) |
|---------|--------------|-------------|----------------|
| Capital gains tax | 0-37% (holding period dependent) | 0% (schablonbeskattning instead) | 30% flat |
| Annual account-value tax | Does not exist | ~0.9%/year | Does not exist |
| Wash sale rule | Yes (30-day window) | No | No |
| Loss deductibility | Yes (with wash sale limits) | No (irrelevant in ISK) | Yes (70-100%) |
| Short-term vs long-term rates | Yes | No | No |

### Avanza-specific operational notes

- **Order types:** Avanza supports market orders, limit orders, and basic stop-loss orders. No OCO (one-cancels-other), bracket orders, or conditional orders. Stop-loss orders on Avanza trigger a market order (not stop-limit).
- **Courtage (commission):** Trading is not commission-free. Avanza charges courtage ranging from 0.049% (highest tier) to 0.25% (lowest tier) per trade. This is a material cost that should be included in all backtest and performance calculations.
- **No official API.** Avanza does not provide an official trading API. Unofficial Python and Node.js wrappers exist (see `06-apis-and-technology.md`) but are unsupported and may break without notice.

### System design implications for Swedish traders

For section 10 above, Swedish traders should modify the system design checklist:

- **Account type:** ISK (default) or regular depot (if loss deductions are needed for specific tax situations).
- **PDT constraints:** Not applicable. Remove from system design.
- **Settlement constraints:** Effectively not applicable on ISK accounts (immediate buying power).
- **Wash sale awareness:** Not applicable. Remove from system design.
- **Tax-lot tracking:** Not needed on ISK. On depot accounts, FIFO (first-in, first-out) is the default method.
- **Commission modeling:** Add Avanza courtage (0.049-0.25%) plus spread cost (wider than US for Mid/Small Cap Swedish stocks).

---

## Bottom line

For real-world swing trading, the edge is not only in finding direction. It is in designing a process that survives settlement rules, order-routing reality, overnight gaps, short-side friction, and tax drag. Any serious research pack should treat these as first-class design constraints, not as afterthoughts.

## Sources

- SEC Investor.gov, "Margin: Borrowing Money to Pay for Stocks"
  https://www.investor.gov/introduction-investing/investing-basics/glossary/margin-borrowing-money-pay-stocks

- FINRA, "Day Trading"
  https://www.finra.org/investors/investing/investment-products/stocks/day-trading

- SEC Investor.gov, "Trading in Cash Accounts"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/trading-cash-accounts

- SEC, "An Introduction to Limit Orders"
  https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/introduction-limit-orders

- SEC, "The New Stock Market: Sense and Nonsense"
  https://www.sec.gov/about/reports-publications/investorpubsnewstockmkt

- FINRA, "Understanding Short Selling"
  https://www.finra.org/investors/insights/understanding-short-selling

- SEC Investor.gov, "Investor Bulletin: Trading Halts"
  https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/investor-10

- IRS Topic No. 409, "Capital Gains and Losses"
  https://www.irs.gov/taxtopics/tc409

- IRS Publication 550, "Investment Income and Expenses"
  https://www.irs.gov/forms-pubs/about-publication-550
