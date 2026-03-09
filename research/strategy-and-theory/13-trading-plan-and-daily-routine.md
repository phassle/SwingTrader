# Trading Plan and Daily Routine for Swing Trading

A trading plan is the single document that transforms discretionary impulse into systematic execution. Without a written plan, every decision becomes an emotional negotiation with yourself. With one, each decision is a checklist item. This document provides a complete trading plan template and daily/weekly routine framework for swing traders.

**Cross-references:** This document builds on concepts from:
- [01 - Swing Trading Fundamentals](01-swing-trading-fundamentals.md) — holding periods, time commitment, capital requirements
- [02 - Technical Indicators](02-technical-indicators.md) — indicator parameters for screening and analysis
- [03 - Chart Patterns](03-chart-patterns.md) — pattern identification for watchlist building
- [04 - Swing Trading Strategies](04-swing-trading-strategies.md) — specific strategy rules referenced in this plan
- [05 - Risk Management](05-risk-management.md) — position sizing, stop-loss placement, portfolio limits
- [06 - APIs and Technology](06-apis-and-technology.md) — tools and data sources for scanning and alerts
- [07 - Backtesting and Performance](07-backtesting-and-performance.md) — metrics for strategy and performance reviews
- [08 - Market Structure and Conditions](08-market-structure-and-conditions.md) — regime identification and VIX interpretation
- [09 - Regulation, Tax, and Trade Operations](09-regulation-tax-and-trade-operations.md) — account rules, settlement, tax considerations
- [11 - Candlestick Interpretation](11-candlestick-interpretation.md) — candle reading for entry confirmation
- [12 - Candlestick Examples](12-candlestick-examples-and-scenarios.md) — practical candle-based decision rules

---

## Table of Contents

1. [Trading Plan Template](#1-trading-plan-template)
   - [1.1 Mission Statement and Trading Goals](#11-mission-statement-and-trading-goals)
   - [1.2 Market and Instrument Selection Criteria](#12-market-and-instrument-selection-criteria)
   - [1.3 Strategy Rules and Selection Framework](#13-strategy-rules-and-selection-framework)
   - [1.4 Risk Parameters](#14-risk-parameters)
   - [1.5 Entry and Exit Rules Checklist](#15-entry-and-exit-rules-checklist)
   - [1.6 Account Management Rules](#16-account-management-rules)
2. [Pre-Market Routine](#2-pre-market-routine)
3. [During Market Hours](#3-during-market-hours)
4. [Post-Market Routine](#4-post-market-routine)
5. [Weekend Routine](#5-weekend-routine)
6. [Monthly and Quarterly Reviews](#6-monthly-and-quarterly-reviews)
7. [Templates and Checklists Summary](#7-templates-and-checklists-summary)

---

## 1. Trading Plan Template

A trading plan is not a suggestion — it is a contract with yourself. Print it, sign it, and review it before every trading session. The plan should answer every question you might face during live trading so that no decision is made under emotional pressure.

### 1.1 Mission Statement and Trading Goals

#### Mission Statement

Write a clear, honest statement about why you are trading and what you expect from it. This anchors every decision and prevents scope creep.

**Template:**

> I am a [part-time / full-time] swing trader focused on [U.S. equities / ETFs / options]. My primary objective is to [grow capital / generate supplemental income / build a track record]. I commit to following my written plan, managing risk above all else, and continuously improving through disciplined review.

**Key principles to include:**
- Capital preservation comes before capital growth
- Process over outcomes — a losing trade executed according to plan is a good trade
- Continuous improvement through journaling and review
- No trade is better than a bad trade

#### Trading Goals

Goals must be specific, measurable, and realistic. Avoid outcome-based goals (e.g., "make $50,000") in favor of process-based goals that you can control.

**Monthly Goals:**

| Category | Goal | Metric |
|----------|------|--------|
| Process | Follow trading plan on every trade | % of trades compliant with plan |
| Process | Journal every trade within 24 hours | % of trades journaled |
| Process | Complete pre-market routine every trading day | Days completed / total trading days |
| Risk | Stay within max daily loss limit | Number of limit breaches |
| Risk | Never exceed max position size | Number of violations |
| Performance | Achieve positive expectancy | (Win rate x avg win) - (Loss rate x avg loss) |
| Performance | Maintain minimum 1:2 risk/reward on entries | Average R-multiple of closed trades |
| Education | Review one strategy or concept per week | Topics reviewed |

**Quarterly Goals:**

| Category | Goal | Metric |
|----------|------|--------|
| Performance | Positive account return after commissions | Net P&L |
| Performance | Sharpe ratio above 0.5 | Rolling 3-month Sharpe |
| Process | Trading plan compliance above 90% | Compliance percentage |
| Development | Backtest one new strategy or variation | Backtests completed |
| Risk | Maximum drawdown under 10% | Peak-to-trough equity decline |

**Yearly Goals:**

| Category | Goal | Metric |
|----------|------|--------|
| Performance | Outperform buy-and-hold S&P 500 on risk-adjusted basis | Sharpe ratio comparison |
| Performance | Positive annual return | Net P&L |
| Development | Complete full strategy review and optimization | Strategies reviewed |
| Risk | No single month loss exceeding 5% of starting equity | Monthly returns |
| Growth | Increase position sizes only after 6-month profitable track record | Account growth progression |

**Goal-setting rules:**
1. Never set dollar-amount targets — they encourage overtrading and excess risk
2. Focus on process metrics in your first year; performance metrics become meaningful only after 100+ trades
3. Review and adjust goals quarterly, not monthly
4. If you miss a process goal consistently, diagnose why before adjusting the goal downward

---

### 1.2 Market and Instrument Selection Criteria

Not every stock is suitable for swing trading. Defining clear selection criteria prevents you from trading illiquid, over-volatile, or unfamiliar instruments.

#### Universe Definition

**Primary universe:** U.S.-listed equities and ETFs on NYSE, NASDAQ, and AMEX.

**Sweden:** Nasdaq Stockholm Large Cap and top Mid Cap stocks (see `27-swedish-market-adaptation.md` Section 5 for equivalent thresholds). Use `.ST` suffix tickers in yfinance (e.g., `VOLV-B.ST`).

**Inclusion criteria:**

| Filter | Minimum Requirement | Rationale |
|--------|---------------------|-----------|
| Average daily volume | 500,000 shares (1M+ preferred) | Ensures liquidity for clean entries and exits |
| Price | $10 - $500 | Below $10: too volatile, wide spreads. Above $500: large position sizes required |
| Market cap | $2 billion+ (mid-cap and above) | Smaller caps are more prone to manipulation and gaps |
| Spread | Bid-ask spread < 0.1% of price | Tight spreads reduce execution cost |
| Float | 50M+ shares | Adequate supply prevents squeezes that invalidate technical setups |
| Optionable | Preferred but not required | Options availability indicates institutional interest |

**Exclusion criteria:**
- Stocks with upcoming earnings within 5 trading days (unless trading an earnings-specific strategy)
- Stocks with pending FDA decisions, merger votes, or other binary events
- ADR/foreign listings with limited after-hours liquidity
- Stocks currently halted or with a history of frequent halts
- SPACs, penny stocks, and recently IPO'd companies (less than 6 months of trading history)

**ETF universe for sector and market exposure:**
- SPY, QQQ, IWM — broad market
- XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLRE, XLC, XLB, XLY — sector ETFs
- TLT, HYG — bond market proxies
- GLD, SLV — precious metals
- USO — energy
- VIX-related: UVXY, SVXY (short-term tactical only)

> **Cross-reference:** See [06 - APIs and Technology](06-apis-and-technology.md) for data sources and screening tools to filter this universe programmatically.

---

### 1.3 Strategy Rules and Selection Framework

A swing trader should have 2-4 well-tested strategies and know exactly when to deploy each one. Switching strategies based on market conditions is systematic; switching based on emotion is gambling.

#### Strategy Inventory

Define each strategy you trade with clear rules. Below is a framework — fill in with your specific strategies from [04 - Swing Trading Strategies](04-swing-trading-strategies.md).

**Strategy 1: Trend-Following Pullback**
- **Market regime:** Bull market, low-to-moderate volatility (VIX 12-20)
- **Setup:** Stock in established uptrend (above rising 20 EMA and 50 SMA) pulls back to 20 EMA on declining volume
- **Entry trigger:** Bullish reversal candle at 20 EMA with volume expansion (see [11 - Candlestick Interpretation](11-candlestick-interpretation.md))
- **Stop-loss:** Below the pullback low or 1.5x ATR below entry
- **Target:** Previous swing high or 2-3x ATR above entry
- **Position size:** Per 1% risk model (see [05 - Risk Management](05-risk-management.md))

**Strategy 2: Mean Reversion (Bollinger Band Bounce)**
- **Market regime:** Sideways market or range-bound conditions
- **Setup:** Stock touches or pierces lower Bollinger Band (20,2) while RSI(14) < 30
- **Entry trigger:** Close back inside the Bollinger Band with bullish candle
- **Stop-loss:** Below the lower Bollinger Band extreme or recent swing low
- **Target:** Middle Bollinger Band (20 SMA) or upper band
- **Position size:** Per 1% risk model, reduced by 25% in high-volatility regimes

**Strategy 3: Breakout**
- **Market regime:** Transitional market, emerging trend (ADX rising through 20)
- **Setup:** Stock consolidating at resistance with narrowing range (inside days, tight Bollinger Bands)
- **Entry trigger:** Close above resistance on volume 1.5x+ above 20-day average
- **Stop-loss:** Below the breakout level or the consolidation midpoint
- **Target:** Measured move (height of consolidation projected above breakout)
- **Position size:** Per 1% risk model

#### Strategy Selection Decision Tree

```
START: What is the current market regime?
│
├── BULL MARKET (SPY above rising 20 EMA > 50 SMA > 200 SMA)
│   ├── VIX < 20: Deploy Strategy 1 (Trend Pullback) — full size
│   ├── VIX 20-30: Deploy Strategy 1 — reduced size (75%)
│   └── VIX > 30: Reduce exposure to 50%. Tighten stops. Consider cash.
│
├── BEAR MARKET (SPY below falling 20 EMA < 50 SMA < 200 SMA)
│   ├── VIX < 25: Short-side Strategy 1 (short rallies to falling 20 EMA)
│   ├── VIX 25-35: Minimal trading. Cash is a position.
│   └── VIX > 35: No new positions. Manage existing only.
│
├── SIDEWAYS (MAs flat and intertwined, ADX < 20)
│   ├── Narrow range: Deploy Strategy 2 (Mean Reversion) — reduced size
│   └── Wide range: Deploy Strategy 2 at extremes only — half size
│
└── TRANSITIONAL (MAs starting to separate, ADX rising through 20)
    └── Deploy Strategy 3 (Breakout) — standard size
```

> **Cross-reference:** See [08 - Market Structure and Conditions](08-market-structure-and-conditions.md) for detailed regime identification using ADX, VIX, and moving average analysis.

---

### 1.4 Risk Parameters

These are hard limits. They are not guidelines. When a limit is hit, the action is mandatory, not optional.

#### Per-Trade Risk

| Parameter | Limit | Action When Breached |
|-----------|-------|---------------------|
| Maximum risk per trade | 1% of account equity | Do not enter the trade. Recalculate position size. |
| Maximum position size | 20% of account equity | Reduce shares until within limit. |
| Minimum risk/reward ratio | 1:2 | Do not enter unless R:R >= 2.0 |
| Maximum holding period | 15 trading days (3 weeks) | Reassess. Close if thesis is no longer valid. |

#### Daily Limits

| Parameter | Limit | Action When Breached |
|-----------|-------|---------------------|
| Maximum daily loss | 2% of account equity | Stop trading for the day. No new entries. |
| Maximum new entries per day | 3 | Wait until tomorrow. |
| Maximum losing trades per day | 2 consecutive | Stop trading. Review the trades. Resume only after diagnosis. |

#### Weekly Limits

| Parameter | Limit | Action When Breached |
|-----------|-------|---------------------|
| Maximum weekly loss | 4% of account equity | Reduce position sizes by 50% the following week. |
| Maximum new entries per week | 8 | Only enter A+ setups beyond this. |

#### Portfolio Limits

| Parameter | Limit | Action When Breached |
|-----------|-------|---------------------|
| Maximum open positions | 6-8 | Close weakest position before opening new one. |
| Maximum sector concentration | 3 positions in same sector | Diversify or skip. |
| Maximum correlation | No more than 3 highly correlated positions | Check sector/industry overlap before entry. |
| Minimum cash reserve | 25% of account (beginners: 40%) | No new positions until cash threshold restored. |
| Maximum drawdown (circuit breaker) | 10% from equity peak | Stop all trading for 1 week. Full review required. |

**Position sizing formula (repeated from [05 - Risk Management](05-risk-management.md) for quick reference):**

```
Shares = (Account Equity x Risk %) / (Entry Price - Stop Price)

Example:
  Account: $50,000
  Risk: 1% = $500
  Entry: $45.00
  Stop: $43.00
  Risk per share: $2.00
  Shares: $500 / $2.00 = 250 shares
  Position value: 250 x $45 = $11,250 (22.5% of account)
```

If the position value exceeds the 20% maximum position size limit, reduce shares accordingly.

---

### 1.5 Entry and Exit Rules Checklist

Print this checklist and run through it before every trade. If any "Required" item fails, do not take the trade.

#### Pre-Entry Checklist

| # | Check | Required? | Status |
|---|-------|-----------|--------|
| 1 | Market regime identified and favorable for this strategy | Required | [ ] |
| 2 | No major news event within next 24 hours (earnings, FOMC, etc.) | Required | [ ] |
| 3 | Stock meets universe criteria (volume, price, market cap) | Required | [ ] |
| 4 | Setup matches one of my defined strategies exactly | Required | [ ] |
| 5 | Stop-loss level identified before entry | Required | [ ] |
| 6 | Position size calculated using risk model | Required | [ ] |
| 7 | Risk/reward ratio >= 2:1 | Required | [ ] |
| 8 | Target level identified (support/resistance, measured move) | Required | [ ] |
| 9 | No more than max concurrent positions already open | Required | [ ] |
| 10 | Daily and weekly loss limits not breached | Required | [ ] |
| 11 | Not already exposed to same sector (check concentration) | Recommended | [ ] |
| 12 | Volume confirms the setup (above average on signal day) | Recommended | [ ] |
| 13 | Multiple timeframe alignment (weekly trend supports daily entry) | Recommended | [ ] |
| 14 | Not entering in the first 15 minutes of market open | Recommended | [ ] |
| 15 | Written trade thesis: why this trade, why now | Required | [ ] |

#### Exit Rules

**Planned exits (set at entry time):**

| Exit Type | Rule | Order Type |
|-----------|------|------------|
| Stop-loss | At predetermined level from pre-entry checklist | Stop-market order (guaranteed exit). Use stop-limit only for thin/illiquid names where a market order risks severe slippage. |
| Target | At predetermined target level | Limit order |
| Trailing stop | Activated when trade reaches 1R profit | Trail at 1.5-2x ATR below highest close |
| Time stop | 15 trading days maximum | Manual close at market |

**Conditional exits (monitored during hold period):**

| Condition | Action |
|-----------|--------|
| Original thesis invalidated (e.g., trend breaks, volume dries up) | Close immediately regardless of P&L |
| Market regime changes unfavorably | Tighten stops on all positions by 50% |
| Earnings announcement moved into holding period | Close before earnings (unless earnings strategy) |
| Stock halted | Set GTC stop-market order; reassess on resumption. Use stop-limit only for thin/illiquid names. |
| Gap through stop-loss | Close at market open. Do not hold and hope. |
| Position reaches 3R profit | Take 50% off, trail remaining |

---

### 1.6 Account Management Rules

#### Capital Allocation

| Phase | Account Action | Criteria to Advance |
|-------|---------------|-------------------|
| Paper trading | $0 real capital. Full plan execution on simulator. | 100+ trades, positive expectancy, plan compliance > 90% |
| Starter | 25% of intended capital. Reduced position sizes. | 3 months profitable, max drawdown < 5% |
| Intermediate | 50% of intended capital. Standard position sizes. | 6 months profitable, Sharpe > 0.5 |
| Full | 100% of intended capital. | 12 months track record, documented edge |
| Growth | Increase capital. May add strategies. | Consistent returns, emotional stability confirmed |

#### Withdrawal and Addition Rules

- Never add capital to offset losses ("throwing good money after bad")
- Withdraw profits quarterly to realize gains (at least 25% of net profits)
- Only add new capital at the start of a quarter after a profitable period
- If account drops 20% from peak, reduce to Starter-phase sizing until recovery

#### Account Type Considerations

> **Cross-reference:** See [09 - Regulation, Tax, and Trade Operations](09-regulation-tax-and-trade-operations.md) for detailed PDT rules, margin requirements, and tax implications.

| Account Type | Key Constraints for Swing Trading |
|-------------|----------------------------------|
| Cash account | No PDT rule. Subject to T+1 settlement. Cannot short. Limited to settled funds. |
| Margin account (under $25K) | PDT rule: max 3 day trades per 5 rolling business days. Swing trades (held overnight) are not day trades. |
| Margin account (over $25K) | No PDT restriction. 2:1 overnight margin. Can short. |
| IRA / tax-advantaged | No margin (typically). No shorting. Tax-free growth but contribution limits. |

**Swedish account types:**

| Account Type | Key Constraints for Swing Trading |
|-------------|----------------------------------|
| ISK (Investeringssparkonto) | No PDT rule. No capital gains tax (flat ~0.9%/year schablonbeskattning instead). Immediate buying power. No margin. No loss deductions. Default choice for most Swedish traders. |
| KF (Kapitalforsakring) | Similar to ISK. Insurance-based wrapper. Slightly different rules for foreign dividends. |
| Regular depot | 30% flat capital gains tax. Losses deductible. No PDT rule. Margin lending available (belaning). |

> **Cross-reference:** See `09-regulation-tax-and-trade-operations.md` Swedish Market section and `27-swedish-market-adaptation.md` for full details.

---

## 2. Pre-Market Routine

**Time required:** 30-60 minutes before market open (complete by 9:15 AM ET).

**Sweden:** Stockholm opens at 09:00 CET (continuous trading 09:00-17:25, closing auction 17:25-17:30). Complete the pre-market routine by 08:45 CET. There is no extended pre-market or after-hours session comparable to the US. The call auction is 08:45-09:00 CET.

The pre-market routine transforms you from "someone who just woke up" into "a prepared trader with a plan." Never skip it. If you cannot complete the routine, do not trade that day.

### 2.1 Economic Calendar Review (5-10 minutes)

Check what macroeconomic events are scheduled for today and the rest of the week. Events move markets, and markets move individual stocks.

**Sources:**
- ForexFactory economic calendar (forexfactory.com/calendar)
- Investing.com economic calendar
- Earnings Whispers (earningswhispers.com) for earnings schedule
- Fed calendar (federalreserve.gov) for FOMC dates

**What to check:**

| Event Type | Impact Level | Action |
|-----------|-------------|--------|
| FOMC rate decision / statement | Critical | No new entries day of. Reduce exposure day before. |
| FOMC minutes release | High | Be cautious with entries after 2:00 PM ET. |
| Non-Farm Payrolls (first Friday) | High | Expect volatility at 8:30 AM. Wait for dust to settle. |
| CPI / PPI inflation data | High | Pre-market move often reverses. Wait for first 30 min. |
| GDP report | Medium | Usually priced in. Monitor for surprises. |
| Retail sales | Medium | Impacts consumer sector stocks. |
| ISM Manufacturing / Services | Medium | Impacts industrial/services sectors. |
| Jobless claims (weekly) | Low-Medium | Matters most in deteriorating labor market. |
| Fed speakers | Low-High | Depends on who. Chair = High. Regional = Low. |
| Earnings (watchlist stocks) | Critical | Do not hold through unless planned earnings strategy. |

**Swedish/European macro events to add for Stockholm-traded stocks:**

| Event Type | Impact Level | Action |
|-----------|-------------|--------|
| Riksbanken rate decision (5-6/year) | Critical | Announced at 09:30 CET. Affects all Swedish stocks, especially banks and real estate. |
| Swedish CPI (SCB) | High | Key inflation metric. Published monthly by Statistiska Centralbyran. |
| ECB rate decision | High | Affects European sentiment broadly; Swedish export-heavy economy is sensitive to eurozone conditions. |
| Eurozone PMI | Medium | Impacts Swedish industrials (Volvo, Atlas Copco, Sandvik, etc.). |
| Konjunkturinstitutet (NIER) tendency survey | Medium | Swedish economic confidence indicator. |
| Swedish reporting season | Critical | Many companies report on concentrated "super Tuesday" / "super Thursday" dates. Check Avanza's earnings calendar. |
| Swedish ex-dividend season (April-May) | High | Large dividend yields (3-5%) create noticeable price drops on ex-dates. |

**Pre-market calendar checklist:**

- [ ] Checked today's economic events and their scheduled times
- [ ] Checked this week's remaining events
- [ ] Identified any watchlist stocks reporting earnings this week
- [ ] Noted any FOMC or major Fed activity
- [ ] Adjusted exposure plan if critical event is today

### 2.2 Market Regime Assessment (5-10 minutes)

Before looking at individual stocks, assess the overall market environment. As noted in [08 - Market Structure and Conditions](08-market-structure-and-conditions.md), 60-80% of stocks follow the broad market direction.

**Check these in order:**

1. **S&P 500 futures (ES) / NASDAQ futures (NQ):**
   - Where are futures trading relative to yesterday's close?
   - Significant gap up/down (> 0.5%)? Note it.
   - Are futures trending or range-bound in the pre-market?

2. **VIX level and direction:**

   | VIX Level | Interpretation | Trading Adjustment |
   |-----------|---------------|-------------------|
   | < 15 | Low fear, complacency | Normal trading. Watch for breakouts. |
   | 15-20 | Normal volatility | Standard operations. |
   | 20-25 | Elevated concern | Reduce position sizes by 25%. Tighten stops. |
   | 25-35 | High fear | Reduce to 50% sizing. Only A+ setups. |
   | > 35 | Panic / crisis | Mostly cash. Manage existing positions only. |

3. **Global markets overnight:**
   - European markets (DAX, FTSE, STOXX): strong, weak, or mixed?
   - Asian markets (Nikkei, Shanghai, Hang Seng): any notable moves?
   - Any overnight geopolitical events or surprises?

4. **Treasury yields / US Dollar:**
   - 10-year yield (TNX): rising, falling, or stable?
   - US Dollar Index (DXY): significant move impacts multinational earnings
   - Yield curve: any inversion changes?

5. **Market regime classification (from yesterday's close):**
   - [ ] Bull: SPY above rising 20 EMA > 50 SMA > 200 SMA
   - [ ] Bear: SPY below falling 20 EMA < 50 SMA < 200 SMA
   - [ ] Sideways: MAs flat and intertwined
   - [ ] Transitional: MAs beginning to cross
   - Current regime: _______________
   - Strategy to deploy today: _______________

### 2.3 Overnight Gap Analysis (5 minutes)

Gaps provide critical information about overnight sentiment and potential opening moves.

**What to scan for:**

| Gap Type | Definition | Implication |
|----------|-----------|-------------|
| Gap up > 2% on high volume | Strong buying pressure overnight | Possible continuation. Watch for pullback entry. |
| Gap up > 2% on low volume | Weak gap, likely to fade | Watch for reversal and short opportunity. |
| Gap down > 2% on high volume | Strong selling pressure | Possible continuation lower. Avoid catching falling knife. |
| Gap down > 2% on low volume | Weak gap, possible buying opportunity | Watch for support and reversal signal. |
| Gap into major support/resistance | Key technical interaction | High-probability setup if confirms with volume. |

**Gap analysis checklist:**
- [ ] Scanned watchlist for gaps > 1%
- [ ] Identified any watchlist stocks gapping through key levels
- [ ] Noted gap direction vs. current trend (continuation vs. exhaustion)
- [ ] Checked news/catalyst for any gapping stocks
- [ ] Updated watchlist priorities based on gaps

> **Cross-reference:** See [04 - Swing Trading Strategies](04-swing-trading-strategies.md), Section 4.4 (Gap Trading Strategies) for specific gap trading rules.

### 2.4 Sector Heat Map Review (3-5 minutes)

Identify which sectors are leading and lagging. Sector rotation provides context for individual stock selection.

**Tools:**
- Finviz heat map (finviz.com/map.ashx)
- TradingView sector performance
- Custom sector ETF dashboard

**What to look for:**
- Which sectors are green/red in pre-market?
- Any sector showing unusual strength or weakness (> 1% divergence from SPY)?
- Are defensive sectors (XLU, XLP, XLV) outperforming? (Risk-off signal)
- Are cyclical sectors (XLK, XLI, XLY) outperforming? (Risk-on signal)
- Any sector rotation pattern emerging (money flowing from one sector to another)?

**Record today's sector stance:**
- Leading sectors: _______________
- Lagging sectors: _______________
- Rotation signal: [ ] Risk-on [ ] Risk-off [ ] Mixed

### 2.5 Watchlist Review and Updates (10-15 minutes)

Your watchlist is your universe of actionable opportunities. It should contain 10-20 stocks that are approaching setups, not 100 tickers that you will never monitor properly.

**Watchlist tiers:**

| Tier | Description | Count | Action |
|------|-------------|-------|--------|
| A-list (Active) | Stocks with setups forming today or tomorrow | 3-5 | Set alerts at trigger levels. Ready to trade. |
| B-list (Developing) | Stocks building toward a setup in 2-5 days | 5-10 | Monitor daily. Move to A-list when setup triggers. |
| C-list (Radar) | Stocks that passed initial screen but need more time | 10-15 | Weekly check. Remove if setup deteriorates. |

**For each A-list stock, identify:**
- [ ] Current trend direction (up, down, sideways)
- [ ] Key support level (nearest)
- [ ] Key resistance level (nearest)
- [ ] Which strategy applies
- [ ] Entry trigger price
- [ ] Stop-loss price
- [ ] Target price
- [ ] Position size (shares)
- [ ] Any news/earnings within holding period

### 2.6 Pre-Market Scanner Setup (5 minutes)

Configure scanners to find new opportunities and confirm watchlist setups.

**Essential scans:**

| Scan Name | Criteria | Purpose |
|-----------|----------|---------|
| Volume surge | Pre-market volume > 3x average | Identify unusual activity |
| Gap scan | Stocks gapping > 1.5% on volume | Gap trading candidates |
| Pullback to 20 EMA | Stock above 50 SMA, RSI < 40, price within 1% of 20 EMA | Trend pullback entries |
| Bollinger squeeze | Bollinger Band width at 6-month low | Breakout candidates |
| RSI oversold + uptrend | RSI(14) < 30, price above 200 SMA | Mean reversion in uptrend |
| New 52-week high on volume | Price at 52-week high, volume > 1.5x average | Momentum breakouts |
| Relative strength leaders | Stock up > 2x SPY return over 20 days | Sector/stock leadership |

> **Cross-reference:** See [06 - APIs and Technology](06-apis-and-technology.md) for implementing these scans programmatically using Python, Finviz, or broker APIs.

### 2.7 Key Levels Identification (5-10 minutes)

For each A-list watchlist stock, mark the key levels on your chart.

**Levels to identify:**

| Level Type | How to Find | Importance |
|-----------|-------------|------------|
| Previous day high/low | Yesterday's candle extremes | Intraday reference points |
| Pre-market high/low | Current session's pre-market range | Opening range context |
| 20 EMA, 50 SMA, 200 SMA | Plot on daily chart | Dynamic support/resistance |
| Horizontal support/resistance | Prior swing highs/lows with multiple touches | Key decision points |
| VWAP (if available) | Volume-weighted average price | Institutional fair value reference |
| Fibonacci levels | Key retracements of recent swing (38.2%, 50%, 61.8%) | Pullback targets |
| Round numbers | $50, $100, $150, etc. | Psychological support/resistance |
| Gap fill levels | Unfilled gaps from recent sessions | Magnet effect for price |

> **Cross-reference:** See [02 - Technical Indicators](02-technical-indicators.md) for calculation methods and [03 - Chart Patterns](03-chart-patterns.md) for pattern-based level identification.

### Pre-Market Routine Master Checklist

Complete this entire checklist before 9:15 AM ET (or 08:45 CET for Swedish market):

- [ ] Economic calendar reviewed — no surprises
- [ ] Market regime assessed — strategy selected
- [ ] Futures and VIX checked — exposure level set
- [ ] Global markets reviewed — no overnight shocks
- [ ] Gap analysis completed — gaps noted on watchlist
- [ ] Sector heat map reviewed — leaders and laggers identified
- [ ] Watchlist reviewed — A/B/C tiers updated
- [ ] Key levels marked on A-list charts
- [ ] Pre-market scanners running
- [ ] Alerts set at trigger levels for A-list stocks
- [ ] Position sizes pre-calculated for all A-list setups
- [ ] Trading journal open and ready
- [ ] Mental state check: Am I focused, calm, and prepared? If not, reduce size or sit out.

---

## 3. During Market Hours

**Sweden:** For Stockholm market hours, the equivalent time windows are: First 30 minutes = 09:00-09:30 CET, Primary window = 09:30-12:00 CET, Mid-day lull = 12:00-14:00 CET, Afternoon = 14:00-17:00 CET, Close = 17:00-17:30 CET (including closing auction at 17:25). Note that US market opens at 15:30 CET, which can cause volatility in Swedish stocks during the last 2 hours of the Stockholm session.

### 3.1 First 30 Minutes (9:30 - 10:00 AM ET): Observation Period

The first 30 minutes of trading are the most volatile and deceptive period of the day. Retail traders get trapped by false moves during this window. Professional swing traders observe and let the noise settle.

**Rules for the first 30 minutes:**

1. **Do not enter new swing positions.** The opening range is being established. Moves often reverse.
2. **Observe how your A-list stocks behave relative to the market.** Stocks that hold up during a market dip show relative strength. Stocks that lag during a market rally show relative weakness.
3. **Note opening volume.** If a stock opens on massive volume and trends, it may offer an entry after the first pullback. If it opens on massive volume and immediately reverses, the gap may be fading.
4. **Watch for gap fills.** Many gaps fill within the first 30 minutes. A gap that does not fill often signals a strong directional move for the day.
5. **Set the opening range.** The high and low of the first 30 minutes define the opening range. Breakouts above or below this range after 10:00 AM are more reliable than moves within it.

**Exception to the 30-minute rule:** If you have a pre-planned swing entry based on a limit order at a specific support level, and the stock opens and immediately touches that level, the limit order can fill. This is acceptable because the decision was made pre-market, not reactively.

### 3.2 Primary Trading Window (10:00 AM - 12:00 PM ET)

This is the highest-probability window for swing trade entries. The opening noise has subsided, trends are established, and volume is still healthy.

**Order management workflow:**

1. **Confirm the setup is still valid.** A stock that looked perfect pre-market may have gapped through your entry level or the market may have shifted. Re-confirm before acting.

2. **Choose order type:**

   | Order Type | When to Use | Advantage | Risk |
   |-----------|-------------|-----------|------|
   | Limit order | Entry at a specific price (pullback to support) | Guaranteed price or better | May not fill if price doesn't reach level |
   | Stop-limit (buy stop) | Breakout entries above resistance | Only enters if breakout occurs | May miss fill in fast breakout; gap risk |
   | Market order | Urgent exit (stop-loss triggered, thesis broken) | Guaranteed fill | Price uncertainty, especially on volatile stocks |
   | Stop-market (sell stop) | Stop-loss placement (default) | Guaranteed execution; the purpose of a stop is to get you out | Potential slippage in fast moves or gaps |
   | Stop-limit (sell stop) | Stop-loss for thin/illiquid names only | Better price control than market stop | May not fill in gap-down scenario |

3. **Place the entry order.**
4. **Immediately set the stop-loss order** (OCO if your broker supports it — one-cancels-other with profit target).
5. **Set the profit target order.**
6. **Log the trade in your journal** with entry price, stop, target, and thesis.

**Limit order placement guidelines:**
- For pullback entries: set limit at the support level or slightly above (1-2 ticks)
- For breakout entries: set buy-stop above resistance with a limit 0.10-0.20 above the stop price
- Do not chase entries. If the stock has already moved past your entry zone, wait for the next pullback or pass on the trade.

### 3.3 Mid-Day Period (12:00 - 2:00 PM ET)

The "lunch lull." Volume drops, spreads can widen, and moves are less reliable. This is not a good time for new entries.

**Mid-day review process (5-10 minutes around 12:30 PM):**

- [ ] Review all open positions. Are they behaving as expected?
- [ ] Check if any stops need adjustment (only move stops in a favorable direction, never widen)
- [ ] Check if any positions have reached partial profit targets
- [ ] Review market regime — has anything changed since the morning?
- [ ] Check for any breaking news affecting open positions
- [ ] Update alerts for B-list stocks that may be approaching setups
- [ ] Do NOT enter new positions during lunch unless a pre-planned limit order fills at a well-defined level

### 3.4 Afternoon Session (2:00 - 3:30 PM ET)

Volume returns as institutional traders begin their afternoon activity. This is the second-best window for entries and a good time for position management.

**Afternoon actions:**
- Review any positions that are near targets — consider taking profits before the close
- Watch for late-day breakdowns or breakouts that confirm the day's direction
- If market reverses in the afternoon, note how your stocks respond — this informs tomorrow's bias
- Be aware that FOMC announcements (2:00 PM) and Fed minutes releases cause volatility through close

### 3.5 Last 30 Minutes (3:30 - 4:00 PM ET)

The "power hour" or "closing auction." Institutional order flow creates significant moves. This is a good time to manage positions but generally not to initiate new ones.

**End-of-day actions:**

- [ ] Review all open positions one final time
- [ ] Decide whether to hold overnight or close any positions (consider next-day catalysts)
- [ ] For positions held overnight: are stops still in the right place? Should they be tightened?
- [ ] Note the closing price and volume of all watchlist stocks
- [ ] Note how the major indices closed (above/below key levels, volume vs. average)
- [ ] Check after-hours earnings announcements that could impact holdings

**When to close before the end of the day:**
- Position has reached your target — take the profit
- Thesis has been invalidated during the day
- A negative earnings report is coming after hours for that stock
- Market regime changed significantly during the day
- You have reached your daily loss limit

---

## 4. Post-Market Routine

**Time required:** 20-30 minutes after market close.

The post-market routine is where learning happens. Without it, you are repeating the same mistakes without knowing it.

### 4.1 Trade Journaling (10-15 minutes)

Journal every trade within 24 hours. The more detail you capture while the trade is fresh, the more useful your reviews will be.

**For each trade closed today, record:**

| Field | What to Record |
|-------|---------------|
| Date/Time | Entry and exit timestamps |
| Symbol | Ticker traded |
| Direction | Long or short |
| Strategy | Which strategy from your plan |
| Setup quality | A+, A, B, C (honest self-assessment) |
| Entry price | Actual fill price |
| Stop-loss | Original stop level |
| Target | Original target level |
| Exit price | Actual exit price |
| Shares / position size | Number of shares traded |
| P&L (dollar) | Gross profit or loss |
| P&L (R-multiple) | Result expressed as multiples of initial risk |
| Plan compliance | Did you follow your plan? Yes/No |
| If No, what did you deviate on? | Specific rule violation |
| Emotional state at entry | Calm, anxious, overconfident, revenge-trading |
| Emotional state at exit | Calm, panicked, relieved, frustrated |
| What I did well | One thing done correctly |
| What I could improve | One thing to do better next time |
| Screenshot | Annotated chart at entry and exit |

**For open positions, update:**
- Current unrealized P&L
- Whether the thesis is still intact
- Whether stops should be adjusted (only tightened)
- Any new information (news, technical development)

**R-Multiple calculation:**

```
R-Multiple = (Exit Price - Entry Price) / (Entry Price - Stop Price)

Example:
  Entry: $50.00, Stop: $48.00, Exit: $54.00
  R = ($54 - $50) / ($50 - $48) = $4 / $2 = 2.0R (a 2R winner)
```

R-multiples allow you to compare trades regardless of position size. A 2R winner on a small position is equally well-executed as a 2R winner on a large position.

> **Cross-reference:** See [07 - Backtesting and Performance](07-backtesting-and-performance.md) for the complete set of performance metrics (Sharpe ratio, profit factor, max drawdown, etc.).

### 4.2 Daily P&L Review (5 minutes)

| Metric | Value |
|--------|-------|
| Today's realized P&L | $ |
| Today's unrealized P&L change | $ |
| Number of trades taken | |
| Number of winners | |
| Number of losers | |
| Largest winner (R-multiple) | |
| Largest loser (R-multiple) | |
| Plan compliance rate today | % |
| Running weekly P&L | $ |
| Distance from daily loss limit | $ |
| Distance from weekly loss limit | $ |

**Red flags to watch for:**
- More than 2 consecutive losing days — reduce size tomorrow
- Average loss bigger than average win — review stop placement
- Plan compliance below 80% — focus on discipline, not strategy
- Emotional notes showing anxiety or revenge-trading — consider taking a day off

### 4.3 Scanner Runs for Next Day (5-10 minutes)

Run your end-of-day scans with updated data. These scans use closing prices and are more reliable than pre-market scans.

**End-of-day scans:**

| Scan | Purpose |
|------|---------|
| Pullback to 20 EMA in uptrend | Tomorrow's pullback entry candidates |
| RSI(14) crossing below 30 with price above 200 SMA | Oversold bounce candidates |
| Inside day (today's range within yesterday's range) | Consolidation/breakout candidates |
| Volume spike > 2x average with bullish close | Institutional accumulation |
| Bullish engulfing at support | Reversal candidates |
| New 20-day high with above-average volume | Momentum continuation |
| Bollinger Band width at 6-month low | Squeeze/breakout setups |

### 4.4 Watchlist Updates (5 minutes)

- Move stocks from B-list to A-list if setup is now imminent
- Remove stocks from watchlist if setup has failed or the stock has moved away from levels
- Add new stocks from scanner results to B-list or C-list
- Check earnings dates for all watchlist stocks — remove any reporting within 3 days (unless earnings strategy)
- Target watchlist size: 15-25 total across all tiers

### Post-Market Routine Checklist

- [ ] All trades journaled with screenshots
- [ ] P&L updated in tracking spreadsheet
- [ ] Plan compliance self-assessed
- [ ] End-of-day scans completed
- [ ] Watchlist updated (additions, removals, tier changes)
- [ ] Alerts set for tomorrow's A-list stocks
- [ ] Preliminary notes for tomorrow's pre-market review
- [ ] Checked after-hours earnings/news for holdings and watchlist stocks

---

## 5. Weekend Routine

**Time required:** 1-2 hours on Saturday or Sunday.

The weekend routine is the most important routine for swing traders. It is when you step back from the daily noise, assess your performance objectively, and prepare for the week ahead.

### 5.1 Weekly Performance Review (20-30 minutes)

**Weekly metrics to calculate and record:**

| Metric | This Week | 4-Week Average | Target |
|--------|-----------|----------------|--------|
| Net P&L ($) | | | Positive |
| Net P&L (%) | | | > 0% |
| Number of trades | | | 3-8 |
| Win rate | | | > 45% |
| Average winner (R) | | | > 1.5R |
| Average loser (R) | | | < -1.0R |
| Profit factor | | | > 1.5 |
| Largest winner (R) | | | |
| Largest loser (R) | | | < -1.0R |
| Plan compliance (%) | | | > 90% |
| Max drawdown this week | | | < 4% |
| Expectancy per trade ($) | | | Positive |

**Expectancy formula:**

```
Expectancy = (Win Rate x Avg Win) - (Loss Rate x Avg Loss)

Example:
  Win rate: 50%, Avg win: $600, Avg loss: $300
  Expectancy = (0.50 x $600) - (0.50 x $300) = $300 - $150 = $150 per trade
```

**Weekly review questions:**

1. Did I follow my trading plan on every trade? If not, which rules did I break and why?
2. Were my entries at good prices, or did I chase?
3. Did I let winners run to target, or did I cut them short out of fear?
4. Did I cut losers at my stop, or did I hold hoping for recovery?
5. Was my position sizing correct for every trade?
6. Did the strategies I used match the market regime?
7. Were there any A+ setups I missed? Why?
8. Was my emotional state stable throughout the week?
9. What is the one thing I will focus on improving next week?

### 5.2 Sector Rotation Analysis (15-20 minutes)

Understanding where institutional money is flowing helps you be on the right side of the market.

**Weekly sector performance table:**

Track each sector ETF's weekly performance and compare to SPY:

| Sector | ETF | This Week % | vs. SPY | 4-Week Trend | Flow Signal |
|--------|-----|-------------|---------|--------------|-------------|
| Technology | XLK | | | | |
| Financials | XLF | | | | |
| Energy | XLE | | | | |
| Healthcare | XLV | | | | |
| Industrials | XLI | | | | |
| Cons. Discretionary | XLY | | | | |
| Cons. Staples | XLP | | | | |
| Utilities | XLU | | | | |
| Real Estate | XLRE | | | | |
| Communication | XLC | | | | |
| Materials | XLB | | | | |

**Rotation signals:**
- Money flowing into cyclicals (XLK, XLI, XLY) = risk-on environment. Favor long swing trades.
- Money flowing into defensives (XLU, XLP, XLV) = risk-off environment. Reduce long exposure, consider shorts.
- Broad-based strength across sectors = healthy bull market. Full trading activity.
- Broad-based weakness = deteriorating market. Reduce exposure.
- Narrow leadership (only 1-2 sectors rising) = fragile rally. Be selective.

> **Cross-reference:** See [04 - Swing Trading Strategies](04-swing-trading-strategies.md), Section 3.3 (Sector Rotation) for the complete sector rotation trading strategy.

### 5.3 Watchlist Rebuilding (20-30 minutes)

The weekend is when you build your watchlist from scratch rather than just updating it. This prevents staleness and forces you to look at the entire market objectively.

**Watchlist building process:**

1. **Run broad scans** on the full U.S. equity universe:
   - Stocks within 5% of 52-week high in an uptrend (momentum leaders)
   - Stocks pulling back to rising 50 SMA on declining volume (pullback candidates)
   - Stocks forming tight bases (Bollinger squeeze, narrow range) near resistance (breakout candidates)
   - Stocks at major support levels with bullish weekly candles (bounce candidates)

2. **Filter scan results** through your instrument selection criteria (Section 1.2):
   - Volume > 500K average
   - Price $10-$500
   - Market cap > $2B
   - No earnings within 5 days

3. **Chart review:** Open each candidate on the weekly chart, then daily, then optionally 4-hour:
   - Weekly: Is the trend clear? Are you trading with or against the primary trend?
   - Daily: Is the setup forming? What are the key levels?
   - Is the setup from your strategy inventory? If not, skip it.

4. **Tier assignment:**
   - A-list (3-5): Setup triggers Monday or Tuesday
   - B-list (5-10): Setup developing, triggers later in the week
   - C-list (10-15): Interesting but needs more time

5. **For each A-list stock, prepare a complete trade plan:**
   - Entry trigger and price
   - Stop-loss price
   - Target price
   - Position size (shares)
   - R:R ratio
   - Strategy name
   - Write a 1-2 sentence thesis

### 5.4 Strategy Performance Review (10-15 minutes)

Track how each of your strategies is performing over time. A strategy that worked last month may not work in the current regime.

**Strategy performance table (updated weekly):**

| Strategy | Trades (4 wk) | Win Rate | Avg R | Expectancy | Current Regime Fit |
|----------|---------------|----------|-------|------------|-------------------|
| Trend pullback | | | | | |
| Mean reversion | | | | | |
| Breakout | | | | | |

**Questions to answer:**
- Is each strategy producing positive expectancy?
- Is any strategy consistently losing? Should it be paused?
- Do the win rates and R-multiples match backtest expectations? (See [07 - Backtesting and Performance](07-backtesting-and-performance.md))
- Does the current market regime favor any strategy shift?
- Am I deploying the right strategy for current conditions?

**Action rules:**
- If a strategy has negative expectancy over 20+ trades, stop trading it and re-backtest
- If a strategy has positive expectancy but you are losing money on it, the problem is execution (discipline, timing, position sizing) — not the strategy
- Never abandon a proven strategy after 3-5 losses; evaluate over 20+ trades minimum

### 5.5 Next Week Preparation (10-15 minutes)

**Next week preparation checklist:**

- [ ] Weekly market regime confirmed: Bull / Bear / Sideways / Transitional
- [ ] Primary strategy for the week selected based on regime
- [ ] Economic calendar for next week reviewed and key dates noted
- [ ] Earnings announcements for watchlist stocks checked
- [ ] Watchlist finalized with A/B/C tiers
- [ ] A-list trade plans written (entry, stop, target, size, thesis)
- [ ] Alerts set for all A-list trigger levels
- [ ] Any expiring options or position management needed Monday?
- [ ] Maximum exposure level set for the week based on conditions
- [ ] One improvement focus identified for the week: _______________

### Weekend Routine Master Checklist

- [ ] Weekly P&L and metrics calculated
- [ ] Weekly performance review questions answered honestly
- [ ] Trade journal reviewed for patterns (recurring mistakes, emotional triggers)
- [ ] Sector rotation analysis completed
- [ ] Watchlist rebuilt from scratch (not just carried forward)
- [ ] Strategy performance reviewed
- [ ] Next week's economic calendar reviewed
- [ ] Next week's plan written
- [ ] Charts prepared with key levels for A-list stocks
- [ ] Alerts set for Monday
- [ ] Mental/emotional reset — took time away from screens

---

## 6. Monthly and Quarterly Reviews

### 6.1 Monthly Review (1-2 hours, first weekend of each month)

The monthly review provides statistical significance that weekly reviews cannot. Patterns in your trading behavior become visible over 20-40 trades.

**Monthly metrics dashboard:**

| Metric | Month Value | 3-Month Avg | 6-Month Avg | Target |
|--------|------------|-------------|-------------|--------|
| Net P&L ($) | | | | Positive |
| Net P&L (%) | | | | > 2% |
| Total trades | | | | 15-30 |
| Win rate (%) | | | | > 45% |
| Avg winner ($) | | | | |
| Avg loser ($) | | | | < Avg winner |
| Profit factor | | | | > 1.5 |
| Sharpe ratio | | | | > 0.5 |
| Max drawdown (%) | | | | < 5% |
| Expectancy ($/trade) | | | | Positive |
| Plan compliance (%) | | | | > 90% |
| Avg holding period (days) | | | | 3-10 |
| Best trade (R) | | | | |
| Worst trade (R) | | | | > -1.0R |

**Monthly analysis tasks:**

1. **Equity curve review:** Plot your equity curve. Is it trending up with manageable drawdowns, or erratic? A smooth, upward-sloping curve indicates consistency.

2. **Trade distribution:** Plot the distribution of R-multiples. Are your wins significantly larger than losses? Are there any outlier losses that skew results?

3. **Day-of-week analysis:** Are you consistently losing on certain days (e.g., Mondays, Fridays)? If so, consider reducing activity on those days.

4. **Time-of-day analysis:** Are your entries at certain times outperforming others? Optimize your trading window.

5. **Strategy comparison:** Which strategy contributed most to P&L? Which detracted? Should allocation shift?

6. **Risk management audit:** Did you breach any risk limits? How many times? What were the consequences?

### 6.2 Quarterly Review (2-3 hours)

The quarterly review is a strategic assessment. It determines whether to continue, adjust, or overhaul your trading approach.

**Quarterly review agenda:**

1. **Performance vs. goals:** Compare actual performance against the quarterly goals set in Section 1.1. Score each goal as Met, Partially Met, or Not Met.

2. **Strategy audit:** For each strategy, compute the full statistics over the quarter. Compare to backtest expectations. Decide: continue as-is, adjust parameters, or retire.

3. **Risk parameter review:** Are current limits appropriate? If max drawdown was never approached, limits may be too conservative. If limits were breached, they may need tightening or the trading approach needs adjustment.

4. **Market regime retrospective:** How accurately did you identify regime changes? Were you in the right strategies at the right times?

5. **Goal setting for next quarter:** Based on what you learned, set new quarterly goals. Emphasize process goals that address your biggest weaknesses.

6. **Plan update:** Revise the trading plan document itself if needed. Add new rules for situations that arose unexpectedly. Remove rules that proved unnecessary.

7. **Capital allocation decision:** Based on performance, decide whether to increase, maintain, or decrease trading capital per the Account Management Rules (Section 1.6).

---

## 7. Templates and Checklists Summary

This section consolidates all checklists from this document for quick reference.

### Daily Schedule at a Glance

| Time (ET) | Activity | Duration |
|-----------|----------|----------|
| 8:30 - 9:15 AM | Pre-market routine | 30-45 min |
| 9:15 - 9:30 AM | Final preparation, alerts confirmed | 15 min |
| 9:30 - 10:00 AM | Observation (no new entries) | 30 min |
| 10:00 - 12:00 PM | Primary trading window | 2 hrs |
| 12:00 - 12:30 PM | Mid-day review | 15-30 min |
| 12:30 - 2:00 PM | Monitoring only (lunch lull) | Passive |
| 2:00 - 3:30 PM | Afternoon trading / position management | 1.5 hrs |
| 3:30 - 4:00 PM | End-of-day actions | 30 min |
| 4:00 - 5:00 PM | Post-market routine | 30-45 min |

**Total active time: approximately 2-3 hours per day** (consistent with the part-time commitment described in [01 - Swing Trading Fundamentals](01-swing-trading-fundamentals.md)).

### Trade Plan Card Template

Use this card for every A-list setup. Fill it out before the market opens.

```
┌─────────────────────────────────────────────────┐
│ TRADE PLAN CARD                                 │
├─────────────────────────────────────────────────┤
│ Date: ________     Symbol: ________             │
│ Strategy: ________________________________      │
│ Direction: [ ] Long  [ ] Short                  │
│                                                 │
│ THESIS (1-2 sentences):                         │
│ ________________________________________________│
│ ________________________________________________│
│                                                 │
│ ENTRY                                           │
│   Trigger: ____________  Order type: __________  │
│   Entry price: $________                         │
│                                                 │
│ RISK                                            │
│   Stop-loss: $________  Risk/share: $________    │
│   Shares: ________  Total risk: $________        │
│   % of account risked: ________%                 │
│                                                 │
│ REWARD                                          │
│   Target 1: $________  (partial: ____%)          │
│   Target 2: $________  (remaining)               │
│   R:R ratio: ________                            │
│                                                 │
│ CHECKLIST                                       │
│   [ ] Market regime favorable                    │
│   [ ] No earnings/events within hold period      │
│   [ ] Meets instrument criteria                  │
│   [ ] Position size within limits                │
│   [ ] R:R >= 2:1                                 │
│   [ ] Stop set before entry                      │
│                                                 │
│ RESULT                                          │
│   Exit price: $________  Exit date: ________     │
│   P&L: $________  R-multiple: ________           │
│   Plan followed: [ ] Yes  [ ] No                 │
│   Notes: ____________________________________    │
└─────────────────────────────────────────────────┘
```

### Weekly Review Card Template

```
┌─────────────────────────────────────────────────┐
│ WEEKLY REVIEW — Week of: _______________        │
├─────────────────────────────────────────────────┤
│ PERFORMANCE                                     │
│   Net P&L: $________  (________%)               │
│   Trades: ________  Wins: ________  Losses: ____ │
│   Win rate: ________%                            │
│   Avg winner: ________R  Avg loser: ________R    │
│   Profit factor: ________                        │
│   Plan compliance: ________%                     │
│                                                 │
│ MARKET CONDITIONS                               │
│   Regime: ________________________________      │
│   VIX range: ________ - ________                 │
│   Strategy used: ____________________________    │
│                                                 │
│ SELF-ASSESSMENT                                 │
│   Best decision this week:                       │
│   ________________________________________________│
│   Worst decision this week:                      │
│   ________________________________________________│
│   Key lesson learned:                            │
│   ________________________________________________│
│   Focus for next week:                           │
│   ________________________________________________│
│                                                 │
│ NEXT WEEK PLAN                                  │
│   Regime expectation: ________________________   │
│   Strategy to deploy: ________________________   │
│   A-list stocks: ____________________________    │
│   Key events: ________________________________   │
│   Max exposure: ________%                        │
└─────────────────────────────────────────────────┘
```

### Emergency Rules (Laminate This)

These rules override everything else. Follow them without hesitation.

| Situation | Immediate Action |
|-----------|-----------------|
| Daily loss limit hit (2%) | Stop trading. Close screens. Review tomorrow. |
| Weekly loss limit hit (4%) | Reduce size 50% next week. Full review this weekend. |
| 10% drawdown from equity peak | Stop all trading for 1 week. Complete full review. Resume at Starter-phase sizing. |
| 3 consecutive losing days | Take 1 day off. Return with reduced size. |
| Emotional trading detected (revenge, FOMO, overconfidence) | Close any impulsive positions. Take a 30-minute break. |
| Technology failure (platform down, internet out) | Call broker to manage open positions by phone. Have broker phone number saved. |
| Flash crash / circuit breaker halt | Do not panic sell. Wait for resumption. Assess after dust settles. |
| Unexpected gap through stop | Close at market open. Accept the loss. Do not average down. |

---

## Final Notes

A trading plan is a living document. It should be updated quarterly based on your reviews, but it should not be changed impulsively after a losing streak. The plan protects you from your own worst impulses — the impulse to revenge-trade, to over-size, to skip the stop, to trade during events you know are dangerous.

The daily and weekly routines may feel tedious at first. Within a few weeks, they become automatic. Within a few months, you will not be able to imagine trading without them. The traders who survive long enough to become profitable are the ones who treat trading as a business with repeatable processes, not as a series of exciting bets.

**The one rule that encompasses all others: when in doubt, sit out.** Missing a trade costs nothing. Taking a bad trade costs capital and confidence.
