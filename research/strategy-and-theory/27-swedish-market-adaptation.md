# Swedish Market Adaptation for Swing Trading

Prepared 2026-03-08. This file adapts the swing trading research pack (originally US-focused) for the Swedish stock market and trading through Avanza. It covers regulatory differences, tax treatment, broker mechanics, market structure, and data sources relevant to a Sweden-based swing trader.

**Cross-references:**
- US regulation and tax: `09-regulation-tax-and-trade-operations.md`
- Market structure and conditions: `08-market-structure-and-conditions.md`
- APIs and technology: `06-apis-and-technology.md`
- Watchlist and universe selection: `22-watchlist-and-universe-selection.md`
- Options for swing trading: `15-options-for-swing-trading.md`
- Execution and slippage: `24-execution-and-slippage-playbook.md`
- Stock screening playbook: `16-stock-screening-playbook.md`
- Catalyst and event playbook: `21-catalyst-and-event-playbook.md`
- Trading plan and daily routine: `13-trading-plan-and-daily-routine.md`

---

## Table of Contents

1. [Swedish Regulatory Framework](#1-swedish-regulatory-framework)
2. [Swedish Tax Rules for Trading](#2-swedish-tax-rules-for-trading)
3. [Avanza as Broker](#3-avanza-as-broker)
4. [Swedish Market Structure](#4-swedish-market-structure)
5. [Universe Adaptation for Swedish Stocks](#5-universe-adaptation-for-swedish-stocks)
6. [Swedish Options and Derivatives Market](#6-swedish-options-and-derivatives-market)
7. [Data Sources for Swedish Stocks](#7-data-sources-for-swedish-stocks)
8. [Key Differences Summary Table](#8-key-differences-summary-table)
9. [Files That Need Patching](#9-files-that-need-patching)

---

## 1. Swedish Regulatory Framework

### 1.1 Finansinspektionen (FI) instead of SEC/FINRA

The Swedish financial market is supervised by Finansinspektionen (FI), the Swedish Financial Supervisory Authority. FI is the equivalent of both the SEC and FINRA combined into a single regulator. FI supervises banks, securities companies, insurance companies, and fund management companies operating in Sweden.

Key differences from the US regulatory structure:

- **Single regulator:** FI handles both market oversight and broker-dealer supervision. In the US, the SEC sets rules while FINRA is the self-regulatory organization for broker-dealers. Sweden has no equivalent of FINRA.
- **EU-level regulation:** Sweden is an EU member, so many financial regulations come from EU directives and regulations that are then implemented into Swedish law. The most important is MiFID II.
- **Investor protection:** Swedish investors are protected by the Swedish Investor Compensation Scheme (investerarskyddet), which covers up to SEK 250,000 per person per institution if a broker becomes insolvent. The Swedish Deposit Guarantee (insattningsgarantin) covers cash deposits up to SEK 1,050,000.

Source: Finansinspektionen, https://www.fi.se/en/

### 1.2 MiFID II Implications

MiFID II (Markets in Financial Instruments Directive II) is the EU framework that governs securities trading across Europe, including Sweden. Key implications for Swedish swing traders:

- **Best execution:** Brokers must take all sufficient steps to obtain the best possible result for clients when executing orders, considering price, costs, speed, likelihood of execution, and settlement.
- **Product governance:** Investment firms must identify a target market for each product and ensure distribution is appropriate.
- **Transaction reporting:** Investment firms must report transactions to FI. This is handled by the broker, not the retail trader.
- **Cost transparency:** Brokers must provide clear ex-ante and ex-post cost disclosures, including all fees, commissions, and third-party costs.
- **Inducement rules:** Restrictions on brokers receiving third-party payments (affects research distribution and payment for order flow).

Practical impact for swing traders: MiFID II mostly affects the broker, not the individual trader directly. The main visible effects are more detailed cost reports and the requirement for brokers to classify clients (retail vs professional).

### 1.3 No Pattern Day Trader (PDT) Rule

This is one of the most significant advantages for Swedish swing traders.

The US Pattern Day Trader rule (FINRA Rule 4210) requires a minimum of $25,000 equity in a margin account for traders who execute 4 or more day trades within 5 business days. **This rule does not exist in Sweden or anywhere in the EU.**

Implications:

- Swedish traders can freely mix intraday and multi-day trades without worrying about PDT classification.
- There is no minimum account size imposed by regulation for active trading.
- A Swedish swing trader who occasionally exits a position the same day it was entered faces no regulatory penalty or restriction.
- This removes a major constraint discussed in `09-regulation-tax-and-trade-operations.md` Section 2.

### 1.4 Short Selling Rules in Sweden/EU

Short selling in Sweden is governed by the EU Short Selling Regulation (EU 236/2012), supervised by FI and coordinated by ESMA (European Securities and Markets Authority).

Key rules:

- **Naked short selling is prohibited.** Any short sale must be covered: the seller must have borrowed the shares, have an arrangement to borrow them, or have another enforceable claim to obtain them before settlement.
- **Disclosure thresholds:** Net short positions of 0.1% of issued share capital must be reported to FI (private notification). Positions of 0.5% or more are publicly disclosed on FI's register.
- **Incremental reporting:** Each additional 0.1% above 0.5% triggers a new public disclosure.
- **Emergency bans:** ESMA and FI can impose temporary short-selling bans during periods of extreme market stress (this was done during March 2020 by several EU countries, though Sweden did not impose a ban at that time).

Practical differences from the US:

- The US locating requirement (Reg SHO) is similar to the EU covered short requirement, but the EU disclosure regime is more granular.
- Swedish retail traders can short sell through their broker if shares are available for borrowing, but availability on Avanza is more limited than on US brokers like Interactive Brokers.
- Borrow costs and availability vary significantly by stock. Large Cap Swedish stocks are generally available; smaller names often are not.

Source: FI short selling register, https://www.fi.se/en/our-registers/net-short-positions/

### 1.5 Insider Trading Rules

Insider trading rules in Sweden are governed by the EU Market Abuse Regulation (MAR, EU 596/2014).

Key points:

- **Insider dealing is a criminal offense** in Sweden, punishable by fines or imprisonment (up to 4 years for serious offenses under Swedish law).
- **Insider information** is defined as information of a precise nature that has not been made public and which, if made public, would be likely to have a significant effect on the price of the financial instrument.
- **Insider lists:** Companies must maintain insider lists and notify FI of transactions by persons discharging managerial responsibilities (PDMRs) and their closely associated persons. These notifications are public and published by FI within 3 business days.
- **Closed periods:** PDMRs are prohibited from trading during the 30 calendar days before the announcement of interim or year-end reports.

For swing traders, the PDMR transaction notifications (analogous to SEC Form 4 filings) are a useful data source. They are published on FI's website and often reported by financial media.

Source: FI insider trading register, https://www.fi.se/en/our-registers/insider-register/

---

## 2. Swedish Tax Rules for Trading

Tax treatment is arguably the single biggest structural advantage for Swedish swing traders compared to US-based traders. The ISK account fundamentally changes the relationship between trading activity and tax liability.

### 2.1 ISK (Investeringssparkonto) - The Default Choice for Swedish Swing Traders

The ISK (Investment Savings Account) is a tax-advantaged account type introduced in Sweden in 2012. It uses schablonbeskattning (standardized/flat-rate taxation) instead of taxing actual capital gains and losses.

**How it works:**

1. Each quarter, the total value of the account (market value of securities + cash) is measured on January 1, April 1, July 1, and October 1.
2. Deposits made during the year are also added to the calculation (proportionally based on when they were made).
3. A kapitalunderlag (capital base) is calculated as the average of the four quarterly values plus deposits.
4. The kapitalunderlag is multiplied by the statslåneränta (government borrowing rate) from November 30 of the previous year, plus 1 percentage point, to produce the schablonintäkt (standardized income). From 2025 onward, the floor for this rate is 1.25%.
5. The schablonintäkt is taxed at 30% (the standard capital income tax rate in Sweden).

**Effective tax rate example (2025/2026 rates):**

If the statslåneränta is approximately 2.0%:
- Schablonintäkt = kapitalunderlag x (2.0% + 1.0%) = 3.0%
- Tax = 3.0% x 30% = 0.90% of account value per year

This means a swing trader pays roughly 0.9% of the total account value per year regardless of how many trades are made or how much profit is generated.

**Why this matters enormously for swing trading:**

- **No capital gains tax on individual trades.** A trader who makes 500 trades per year and generates 50% returns pays the same tax as someone who makes 2 trades and generates 5%.
- **No wash sale rule.** There is no equivalent of the US 30-day wash sale rule (IRS Publication 550). A Swedish trader can sell a losing position and immediately buy it back without any tax consequence inside an ISK.
- **No tax on dividends** received within the ISK (they are already covered by the schablonbeskattning).
- **No K4 declaration needed.** The trader does not need to report individual trades. Avanza reports the schablonintäkt directly to Skatteverket.
- **Losses are not deductible.** This is the tradeoff: in a bad year, the trader still pays the schablonbeskattning on the account value.

**What can be held in an ISK:**

- Stocks listed on regulated markets (Nasdaq Stockholm, First North, etc.)
- ETFs and funds
- Certain structured products and warrants (if they meet the requirements)
- Foreign stocks listed on regulated markets (e.g., US stocks on NYSE/Nasdaq)
- Cash

**What cannot be held in an ISK:**

- Unlisted shares (onoterade aktier) unless traded on a regulated market or MTF
- Certain complex derivatives
- Shares in closely held companies (fåmansbolag) where the account holder has significant control

**Bottom line:** For any active swing trader in Sweden, the ISK is almost always the correct account type. The tax simplicity and the elimination of per-trade tax friction is a major structural advantage over US traders using taxable accounts.

Source: Skatteverket, https://www.skatteverket.se/privat/skatter/vardepapper/investeringssparkonto

### 2.2 KF (Kapitalforsakring) - Capital Insurance Account

A kapitalforsakring is a tax wrapper structured as an insurance policy. It works similarly to an ISK in many ways but has some important differences.

**Similarities to ISK:**
- Uses schablonbeskattning (same formula and rate as ISK)
- No tax on individual capital gains or dividends within the account
- No need to report individual trades

**Key differences from ISK:**

| Feature | ISK | KF |
|---------|-----|-----|
| **Ownership of securities** | You own the securities directly | The insurance company technically owns the securities |
| **Voting rights** | You have voting rights at shareholder meetings | No voting rights (the insurance company is the legal owner) |
| **Beneficiary designation** | Not applicable | Can designate beneficiaries (useful for estate planning) |
| **Transfer between providers** | Can transfer ISK between brokers | Generally cannot transfer a KF between providers |
| **Tax on interest** | Interest above statslåneränta + 1% is taxed separately (from 2025) | All interest is part of the schablonbeskattning |
| **Provider insolvency** | Securities held in your name | Securities held by the insurance company; different protection |
| **Yield tax** | Paid by the individual (reported as schablonintäkt on tax return) | Paid by the insurance company (avkastningsskatt); may use slightly different rate formula |

**When to choose KF over ISK:**
- Estate planning with beneficiary designation
- Situations where you do not want securities in your own name
- For most active swing traders, ISK is the simpler and more common choice

### 2.3 Aktie- och Fondkonto (Regular Depot Account)

A regular depot account (sometimes called AF-konto or vanligt depåkonto) is the equivalent of a US taxable brokerage account.

**Tax treatment:**

- Capital gains are taxed at 30% (kapitalvinstskatt).
- Losses are deductible against gains. Losses on listed securities are 70% deductible against other capital income if there are no offsetting gains.
- Dividends are taxed at 30%.
- The trader must file a K4 form with Skatteverket for each tax year, reporting all sales.
- Avanza provides a K4 helper that pre-fills most of the information.

**When a regular depot makes sense:**

- When the trader expects significant losses (since losses are deductible, unlike in ISK).
- For holding unlisted shares that cannot be in an ISK.
- For extremely large accounts where the schablonbeskattning exceeds expected gains (very rare for active traders).

**Tax loss harvesting in Sweden:**

- There is **no wash sale rule** in Sweden. A trader can sell a stock at a loss, immediately buy it back, and still claim the loss as a deduction on a regular depot account. This is a significant difference from the US 30-day wash sale rule.
- However, since most Swedish swing traders use ISK accounts, tax loss harvesting is irrelevant within the ISK because losses are not deductible and gains are not taxed.

### 2.4 Currency Considerations for Trading US Stocks from Sweden

Swedish traders using Avanza can trade US stocks, but currency adds a layer of complexity:

- **Currency conversion:** When buying US stocks, SEK is converted to USD at the prevailing exchange rate plus a currency conversion fee (Avanza charges approximately 0.25% on currency conversion).
- **Currency risk:** Profits on a US stock can be eroded (or amplified) by SEK/USD movements. A US stock that rises 5% in USD may return more or less than 5% in SEK terms.
- **Double exposure:** A Swedish trader holding US stocks is exposed to both the stock's price movement and the USD/SEK exchange rate. This is an additional risk factor not present when trading Swedish stocks.
- **Tax treatment of currency gains:** In a regular depot, currency gains on foreign holdings are part of the capital gain/loss calculation. In ISK, this is irrelevant since individual trades are not taxed.
- **US withholding tax on dividends:** US stocks pay dividends subject to US withholding tax (typically 15% under the US-Sweden tax treaty, reduced from the default 30%). Within an ISK, this withholding is a real cost since it cannot be reclaimed through a foreign tax credit (the ISK already provides a flat tax treatment). On a regular depot, the withholding can be credited against Swedish tax.

**Practical implication for swing traders:** Currency conversion costs (0.25% each way, so ~0.50% round-trip) add meaningful friction to short-term US stock trades. For multi-day swing trades with small expected gains, this can significantly reduce edge. Swedish Large Cap stocks avoid this friction entirely.

---

## 3. Avanza as Broker

Avanza is Sweden's largest online broker by number of customers (approximately 3 million accounts as of 2025). It is the default choice for most Swedish retail traders and investors.

### 3.1 Available Order Types

Avanza supports the following order types on the Stockholm exchange:

| Order Type | Availability | Notes |
|-----------|-------------|-------|
| **Market order** | Yes | Executes at best available price. Called "bästa pris" on Avanza. |
| **Limit order** | Yes | Set a maximum buy price or minimum sell price. The standard order type. |
| **Stop-loss** | Yes | Triggers a market order when the stop price is reached. |
| **Stop-limit** | Yes | Triggers a limit order when the stop price is reached. Available on Stockholm. |
| **Trailing stop** | No (not natively) | Avanza does not offer a native trailing stop order type. Traders must manage trailing stops manually or via third-party tools/API. |

**Important Avanza stop-loss specifics:**

- Stop-loss orders on Avanza are **valid only during regular trading hours** (09:00-17:30 CET for Stockholm). They do not protect against overnight gaps.
- Stop-loss orders are **day orders or good-till-date orders**. There is no native good-till-canceled (GTC) indefinite stop.
- Stop-loss triggers are based on the last traded price, not the bid price. This matters in illiquid stocks where the spread is wide.
- For US stocks traded through Avanza, stop-loss orders are available but follow the US exchange rules.

### 3.2 Fee Structure (Courtage)

Avanza uses a courtage class system. The class determines the commission per trade.

As of the most recent published rates (subject to change; always verify at avanza.se):

| Courtage Class | Eligible If | Nordic Stocks | US/Canada Stocks | Other Markets |
|---------------|-------------|--------------|-----------------|---------------|
| **Mini** | Default for new accounts | 0.25% (min SEK 1) | Not available | Not available |
| **Small** | Quarterly trading volume > SEK 50,000 | 0.15% (min SEK 39) | 0.15% (min USD 1) | Varies |
| **Medium** | Quarterly volume > SEK 500,000 | 0.069% (min SEK 39) | 0.15% (min USD 1) | Varies |
| **Large** | Quarterly volume > SEK 2,000,000 or by negotiation | 0.049% (min SEK 39) | 0.15% (min USD 1) | Varies |
| **Fast-pris** (fixed price) | Available at request | SEK 99/trade flat | Not applicable | Not applicable |

**Additional fees:**

- **Currency conversion:** ~0.25% on FX conversion for non-SEK trades.
- **Real-time data:** Nordic real-time data is included for customers with active trading. US real-time data costs approximately SEK 33/month for NYSE and SEK 33/month for Nasdaq (Level 1). Without subscription, US data is delayed 15 minutes.
- **Account fees:** No annual account fee for ISK, KF, or regular depot.
- **Inactivity fee:** None.

**Comparison to US brokers:**

Most major US brokers (Schwab, Fidelity, Robinhood) offer zero-commission trading on US stocks. Avanza's courtage, while low by European standards, is a real cost that must be factored into swing trade edge calculations. For a SEK 100,000 trade at the Mini class, courtage is SEK 250 (0.25%). Round-trip: SEK 500, or 0.50% of the position. At Medium class: approximately SEK 69 per side, or SEK 138 round-trip (0.14%).

Source: Avanza prislista, https://www.avanza.se/priser-villkor/prislista.html

### 3.3 Available Markets Through Avanza

| Market | Currency | Trading Hours (Local) | Notes |
|--------|----------|----------------------|-------|
| **Nasdaq Stockholm** (Large/Mid/Small Cap) | SEK | 09:00-17:30 CET | Primary market. Full order type support. |
| **Nasdaq First North** (Growth Market) | SEK | 09:00-17:30 CET | Higher risk; less liquidity; lighter listing requirements. |
| **Nasdaq Helsinki** | EUR | 10:00-18:30 EET | Finnish stocks. |
| **Nasdaq Copenhagen** | DKK | 09:00-17:00 CET | Danish stocks. |
| **Oslo Bors** | NOK | 09:00-16:20 CET | Norwegian stocks. |
| **NYSE / Nasdaq US** | USD | 15:30-22:00 CET | US stocks. Currency conversion applies. |
| **Toronto (TSX)** | CAD | 15:30-22:00 CET | Canadian stocks. |
| **Xetra (Frankfurt)** | EUR | 09:00-17:30 CET | German stocks. |
| **London Stock Exchange** | GBP | 09:00-17:30 GMT | UK stocks. |

Note: Avanza periodically adds or removes markets. Pre-market and after-hours trading on US exchanges is generally not available through Avanza for retail clients.

### 3.4 Avanza API Possibilities

Avanza does not offer an official public API for retail customers. However, unofficial community-maintained API wrappers exist:

**Python:**
- `avanza` package (PyPI): An unofficial Python wrapper that uses Avanza's internal web API. Supports authentication via BankID/TOTP, fetching account data, placing orders, and receiving real-time price updates via websockets.
- GitHub: https://github.com/Qluxzz/avanza (one of several forks/implementations)
- Capabilities: Get positions, place buy/sell orders, fetch instrument data, get historical prices, real-time quotes via websocket.
- Risk: Since it is unofficial, Avanza can change their internal API at any time, breaking the wrapper. Use at your own risk.

**Node.js/TypeScript:**
- `avanza` package (npm): Similar to the Python package; provides programmatic access to Avanza's internal API.
- GitHub: https://github.com/fhqvst/avanza
- Capabilities: Authentication, order placement, account overview, instrument search, real-time data subscription.

**Important caveats:**

- These are **unofficial** and **unsupported** by Avanza. There is no SLA, no guaranteed uptime, and no official documentation.
- Avanza's terms of service may or may not explicitly allow automated API access. Aggressive automated trading could theoretically lead to account restrictions.
- Authentication requires TOTP (Time-based One-Time Password) setup, which is the same 2FA mechanism used for the Avanza app.
- For a swing trading application that places trades, the unofficial API is functional but should be used with appropriate error handling and rate limiting.
- For data-only use cases (fetching prices, positions), the risk is lower.

**Alternative approach:** Use Avanza's web/app interface for order execution and a separate data source (Yahoo Finance, Nasdaq Nordic) for analysis and screening. This avoids API dependency risk while still enabling systematic analysis.

### 3.5 Real-Time vs Delayed Data

| Data Type | Cost | Details |
|-----------|------|---------|
| Nordic stocks (real-time) | Free with active trading | Included if you have at least one trade or an active subscription. Level 1 (bid/ask/last). |
| Nordic stocks (delayed) | Free | 15-minute delay. Default for inactive accounts. |
| US stocks (real-time) | ~SEK 33/month per exchange | Separate subscriptions for NYSE and Nasdaq. |
| US stocks (delayed) | Free | 15-minute delay. |
| Level 2 / Market depth | Additional cost | Available for Nordic stocks. Useful for assessing liquidity before placing larger orders. |

---

## 4. Swedish Market Structure

### 4.1 Nasdaq OMX Stockholm

Nasdaq Stockholm (formally Nasdaq OMX Stockholm) is the main stock exchange in Sweden. It is part of the Nasdaq Nordic group, which also operates exchanges in Helsinki, Copenhagen, Reykjavik, and the Baltic states.

**Market segments:**

| Segment | Market Cap Threshold (EUR) | Approximate SEK Equivalent | Number of Companies (approx.) |
|---------|---------------------------|---------------------------|------------------------------|
| **Large Cap** | > EUR 1 billion | > ~SEK 11 billion | ~100 |
| **Mid Cap** | EUR 150 million - 1 billion | ~SEK 1.7-11 billion | ~130 |
| **Small Cap** | < EUR 150 million | < ~SEK 1.7 billion | ~170 |

Note: The segment classification is reviewed annually by Nasdaq Nordic. A company can move between segments based on its average market cap.

**First North:**

First North is Nasdaq's growth market (an MTF - Multilateral Trading Facility, not a regulated market). It has lighter listing requirements than the main market.

| Feature | Main Market | First North |
|---------|-------------|-------------|
| Listing requirements | Full prospectus, 3 years financial history, profitability requirements | Lighter; company description document; no profitability requirement |
| Regulation | EU Regulated Market | MTF (lighter regulation) |
| Market surveillance | Full Nasdaq surveillance | Certified Adviser required |
| Typical companies | Established companies | Growth companies, smaller companies, pre-profit companies |
| ISK eligibility | Yes | Yes (if traded on Nasdaq First North) |
| Liquidity | Generally good for Large/Mid Cap | Often thin; wide spreads common |

### 4.2 Trading Hours

| Session | Time (CET) | Notes |
|---------|-----------|-------|
| **Pre-open / Call auction** | 08:45-09:00 | Orders can be entered but do not execute until the opening auction. |
| **Continuous trading** | 09:00-17:25 | Normal trading session. All order types active. |
| **Closing auction** | 17:25-17:30 | Orders matched at a single closing price. |
| **Post-close** | 17:30-17:40 | Trade reporting only; no new orders. |

**Comparison to US hours:**

| Feature | Sweden (Stockholm) | US (NYSE/Nasdaq) |
|---------|-------------------|------------------|
| Regular hours | 09:00-17:30 CET (8.5 hours) | 09:30-16:00 ET (6.5 hours) |
| Pre-market | 08:45-09:00 (call auction only) | 04:00-09:30 ET (extended) |
| After-hours | Minimal (17:30-17:40 reporting) | 16:00-20:00 ET |
| Total accessible hours | ~8.5 hours | ~12 hours (with extended) |

**Important implication:** Swedish stocks have very limited extended-hours trading. This means overnight gap risk from news cannot be managed by pre-market or after-hours exits the way US traders can. However, it also means Swedish stocks are less prone to the wild pre-market swings that affect US names.

### 4.3 Settlement

- **Settlement cycle:** T+2 (two business days after the trade date). The US moved to T+1 on May 28, 2024, but the EU (including Sweden) has been working toward T+1 and is expected to transition by late 2027 (ESMA recommendation).
- **Practical impact:** On a cash account (or within an ISK), sale proceeds are not settled for 2 business days. This is less restrictive than the old US T+2 was, because ISK accounts do not have the "good faith violation" or "free riding" rules that US cash accounts have. On Avanza, buying power is generally available immediately on ISK accounts even before settlement.

### 4.4 Currency and Settlement Currency

- All Stockholm-listed stocks settle in SEK.
- Dividends from Swedish companies are paid in SEK.
- No currency risk when trading Swedish stocks from a Swedish account.

### 4.5 Key Indices

| Index | Description | Components | Use |
|-------|-------------|-----------|-----|
| **OMXS30** | The 30 most traded stocks on Nasdaq Stockholm | 30 stocks, weighted by market cap and liquidity | The primary benchmark index. Equivalent to the Dow or S&P 500 for Swedish market regime analysis. Futures and options trade on OMXS30. |
| **OMXSPI** | Stockholm All-Share Index | All stocks on Nasdaq Stockholm | Broader market barometer. Better for breadth analysis. |
| **OMXS30GI** | OMXS30 Gross Index (total return including dividends) | Same 30 stocks | Better for performance comparison since it includes dividends. |
| **SX indices** | Sector indices (SX10 Energy, SX20 Industrials, etc.) | Sector-specific | Useful for sector rotation analysis on the Swedish market. |

**Regime analysis adaptation:**

Where `08-market-structure-and-conditions.md` references the S&P 500 for regime identification, Swedish traders should use:

- **OMXS30** for the primary trend and regime assessment (equivalent to S&P 500).
- **OMXSPI** for breadth analysis (equivalent to NYSE composite).
- Sector SX-indices for sector rotation analysis (equivalent to XLK, XLF, XLE, etc.).

### 4.6 Liquidity Characteristics vs US

Swedish market liquidity is substantially lower than the US market. This has major implications for swing trading.

| Metric | US Large Cap (e.g., AAPL) | Swedish Large Cap (e.g., Volvo B) | Swedish Mid Cap | Swedish Small Cap |
|--------|--------------------------|----------------------------------|-----------------|-------------------|
| Daily volume (shares) | 50-100 million | 5-15 million | 500K-5M | 50K-500K |
| Daily volume (value) | Billions of USD | Hundreds of millions SEK | Tens of millions SEK | Single-digit millions SEK |
| Typical spread | 0.01-0.02% | 0.05-0.15% | 0.10-0.50% | 0.50-3.00% |
| Market depth (shares at best bid/ask) | Tens of thousands | Hundreds to low thousands | Tens to hundreds | Often single-digit lots |

**Implications:**

- **Position sizing:** Larger positions relative to daily volume are common in Sweden. A position that would be trivial in a US Large Cap stock might represent a meaningful portion of daily volume in a Swedish Mid Cap.
- **Slippage:** Market orders in Mid and Small Cap Swedish stocks will frequently experience meaningful slippage. Limit orders are essential.
- **Exit risk:** In a panic or after bad news, liquidity in Swedish Mid/Small Cap names can evaporate. Stop-loss orders may execute far from the stop price.
- **Spread cost:** The typical round-trip spread cost on a Swedish Mid Cap stock is 0.20-1.00% (compared to 0.02-0.04% on US Large Caps). This must be added to courtage when calculating total trading friction.

### 4.7 Typical Market-Moving Events for Swedish Stocks

The catalyst framework in `21-catalyst-and-event-playbook.md` applies broadly, but Swedish-specific catalysts include:

- **Riksbanken (Swedish Central Bank) rate decisions:** The Swedish equivalent of FOMC decisions. Typically 5-6 decisions per year. Announced at 09:30 CET.
- **Swedish CPI (SCB):** Published by Statistiska Centralbyran (SCB). Key inflation metric for Sweden.
- **Konjunkturinstitutet (NIER):** Publishes economic tendency surveys and forecasts.
- **Reporting season:** Swedish companies typically report quarterly. Many report on the same "super Tuesday" or "super Thursday" dates, creating concentrated news flow.
- **Ex-dividend dates:** Swedish companies often have their AGM and go ex-dividend in April-May. Dividend yields on Swedish stocks are often 3-5%, creating noticeable price adjustments on ex-dates.
- **European macro:** ECB decisions, eurozone PMI, German Ifo index all affect Swedish stocks given the export-heavy nature of the Swedish economy.

---

## 5. Universe Adaptation for Swedish Stocks

### 5.1 Equivalent Thresholds for Swedish Market

The universe selection framework in `22-watchlist-and-universe-selection.md` uses US-based thresholds. Here are the Swedish equivalents:

| Filter | US Default | Swedish Equivalent | Rationale |
|--------|-----------|-------------------|-----------|
| **Market cap (conservative)** | > $2B | > SEK 20B (~EUR 1.8B) = Large Cap | Focuses on the most liquid segment |
| **Market cap (expanded)** | > $500M | > SEK 5B (~EUR 450M) = Upper Mid Cap | Adds liquid Mid Cap names |
| **Minimum price** | > $5 | > SEK 20 | Filters out penny stocks; spread as % of price becomes manageable |
| **ADTV (daily value traded)** | > $1M/day | > SEK 10M/day | Ensures positions can be entered/exited without excessive slippage |
| **ADTV (volume in shares)** | > 200,000 shares/day | > 100,000 shares/day | Lower threshold reflects smaller Swedish market |
| **Listing venue** | NYSE, Nasdaq | Nasdaq Stockholm Large Cap, Mid Cap | Avoid First North and Small Cap for default universe |

### 5.2 Recommended Default Universe

**Conservative default (recommended for most swing traders):**

- Nasdaq Stockholm Large Cap (~100 stocks)
- Filter for ADTV > SEK 10M/day
- This produces a universe of approximately 60-80 tradable names

**Expanded universe (for experienced traders):**

- Add top Mid Cap names with ADTV > SEK 5M/day
- This adds approximately 30-50 additional names
- Total universe: 90-130 stocks

**Aggressive/Speculative tier (high risk):**

- First North Premier names with ADTV > SEK 2M/day
- Small Cap names with specific catalysts
- Requires explicit opt-in and stricter position sizing

### 5.3 Notable Liquid Swedish Stocks for Swing Trading

The most liquid Swedish stocks (by trading value) include:

- **Financials:** SEB, Handelsbanken, Swedbank, Investor AB
- **Industrials:** Volvo, Atlas Copco, Sandvik, Epiroc, ABB (listed in Stockholm and Zurich)
- **Technology:** Ericsson, Hexagon, Sinch
- **Healthcare:** AstraZeneca (listed in Stockholm and London), Getinge
- **Consumer:** H&M, Essity
- **Real Estate:** Castellum, Sagax
- **Gaming/Digital:** Evolution, Embracer (higher volatility)

These names generally have tight spreads, deep order books, and sufficient volume for meaningful swing positions.

---

## 6. Swedish Options and Derivatives Market

### 6.1 OMX Derivatives

The Swedish options and derivatives market is operated by Nasdaq Stockholm.

**Available products:**

| Product | Underlying | Notes |
|---------|-----------|-------|
| **OMXS30 Index Options** | OMXS30 index | European style. Monthly and weekly expirations. The most liquid Swedish derivatives product. |
| **OMXS30 Index Futures** | OMXS30 index | Standard and mini contracts. Used for hedging and speculation. |
| **Single Stock Options** | Selected Large Cap stocks | Limited set of underlyings (typically 20-30 of the most traded stocks). American style. |
| **Single Stock Futures** | Selected stocks | Limited liquidity. |

### 6.2 Availability on Avanza

Avanza offers access to OMX derivatives, but with significant limitations compared to US options trading:

- **OMXS30 options:** Available. This is the most commonly traded options product.
- **Single stock options:** Available for a limited set of Swedish Large Cap stocks. The number of available strike prices and expirations is much smaller than for US stocks.
- **US options:** Avanza does **not** offer trading in US-listed options (no options on AAPL, TSLA, etc.). For US options, Swedish traders typically use Interactive Brokers or Saxo Bank.
- **Spreads and multi-leg strategies:** Avanza supports basic options trading but does not offer sophisticated multi-leg order entry. Spreads must be legged in manually.

### 6.3 Practical Limitations for Swing Traders

The options strategies described in `15-options-for-swing-trading.md` have limited applicability on the Swedish market through Avanza:

| Strategy from File 15 | Feasibility in Sweden (via Avanza) |
|----------------------|----------------------------------|
| Long calls/puts on individual stocks | Limited to the ~20-30 stocks with listed options. Liquidity is often poor. |
| Vertical spreads | Technically possible but must be legged manually. Wide bid-ask spreads reduce edge. |
| Protective puts | Available only for optionable stocks. OMXS30 puts can hedge the overall portfolio. |
| LEAPS | Availability varies. Long-dated options exist on OMXS30 but are limited on single stocks. |
| Options-based income (covered calls, etc.) | Feasible on optionable stocks, but limited universe. |

**Workaround:** Swedish traders who want full options capability typically open an account at Interactive Brokers (IBKR), which offers US options, European options, and supports complex order types. IBKR also supports ISK-like tax wrappers through certain structures, though direct ISK accounts are only available at Swedish banks/brokers.

### 6.4 Warrants and Structured Products

Sweden has a large market for warrants and other structured products (turbo certificates, mini futures, bull/bear certificates) issued by banks like SEB, Nordea, Commerzbank, and Societe Generale.

- These are available on Avanza and provide leveraged exposure to indices, stocks, and commodities.
- They are **not options** in the traditional sense: they are issued by a bank, have issuer credit risk, and pricing is set by the issuer (not by supply/demand on an exchange).
- Spreads are typically wider than listed options.
- They can be held in an ISK.
- For swing trading purposes, they can serve as a substitute for options when leveraged or hedged exposure is needed, but the pricing transparency is inferior to exchange-traded options.

---

## 7. Data Sources for Swedish Stocks

### 7.1 Yahoo Finance

Yahoo Finance works for Swedish stocks using the `.ST` ticker suffix:

- Volvo B: `VOLV-B.ST`
- Ericsson B: `ERIC-B.ST`
- H&M: `HM-B.ST`
- SEB A: `SEB-A.ST`
- OMXS30 index: `^OMX`

Using `yfinance` in Python:

```python
import yfinance as yf
volvo = yf.download("VOLV-B.ST", period="1y")
```

**Caveats:**
- Data quality for Swedish stocks on Yahoo Finance is generally good but not perfect.
- Dividend adjustment can occasionally be wrong for Swedish stocks with special dividends or splits.
- Real-time data is delayed (typically 15 minutes).
- Some First North stocks may not be available or may have incomplete data.

### 7.2 Avanza's Own Data

Avanza provides:
- Real-time quotes (with subscription) and delayed quotes (free)
- Historical price data on instrument pages
- Key ratios (P/E, P/S, dividend yield, etc.)
- Insider transaction notifications
- Earnings calendar for Swedish companies
- Technical analysis tools (basic charting with common indicators)

Data can be accessed programmatically through the unofficial API (see Section 3.4).

### 7.3 Nasdaq Nordic Website

https://www.nasdaq.com/market-activity/nordic

Provides:
- Official trading statistics
- Listed companies with market cap segments
- Corporate actions (dividends, splits)
- News releases
- Index compositions and weightings
- Short selling statistics (aggregated)

### 7.4 Alternative Data Providers

| Provider | Data Type | Notes |
|---------|-----------|-------|
| **Börsdata (borsdata.se)** | Fundamental data, screening, financial history | Swedish-focused. Subscription-based. Excellent for Swedish stock screening and fundamental analysis. Often called "the Swedish TIKR." |
| **Infront/Millistream** | Real-time and historical Nordic data | Professional-grade. Used by many Nordic financial services. API available. |
| **Refinitiv/LSEG** | Comprehensive market data | Enterprise-level. Covers Swedish stocks. Expensive. |
| **Bloomberg** | Full market data and analytics | Enterprise-level. Covers Swedish stocks. Very expensive. |
| **Trading Economics** | Swedish macro data | Free tier available. Riksbanken rate, CPI, GDP, etc. |
| **SCB (Statistics Sweden)** | Official Swedish statistics | Free. CPI, labor market, GDP components. https://www.scb.se |
| **Riksbanken** | Monetary policy, rates, FX | Free. Interest rate decisions, SEK exchange rates. https://www.riksbank.se |
| **Financial Times** | Global coverage including Swedish stocks | Search by stock name; FT covers most Stockholm Large Cap names. |

### 7.5 Swedish-Specific Data for Screening

For the stock screening playbook (`16-stock-screening-playbook.md`), the following Swedish adaptations apply:

| US Data Source | Swedish Equivalent |
|---------------|-------------------|
| SEC EDGAR (filings) | FI registers + company IR pages |
| FINRA short interest | FI short selling register (net short positions > 0.5%) |
| Form 4 (insider trades) | FI insider register (PDMR transactions under MAR) |
| AAII Sentiment Survey | No direct equivalent. Avanza's own customer statistics (most bought/sold) provide a rough proxy. |
| IBD RS Rating | No direct equivalent. Must be calculated manually from price data. |
| Earnings Whisper | No equivalent. Use Avanza's earnings calendar and company guidance. |
| Sector ETFs (XLK, XLF, etc.) | SX sector indices on Nasdaq Stockholm. Some Swedish sector ETFs exist but liquidity is limited. |

---

## 8. Key Differences Summary Table

| Topic | United States | Sweden |
|-------|--------------|--------|
| **Regulator** | SEC + FINRA | Finansinspektionen (FI) + EU/ESMA |
| **Pattern Day Trader rule** | Yes ($25K minimum, 4 day trades / 5 days) | No. No restrictions on day trade frequency. |
| **Short selling** | Reg SHO locate requirement; FINRA reporting | EU SSR: naked short ban; 0.1% private / 0.5% public disclosure |
| **Insider trade reporting** | SEC Form 4 (2 business days) | MAR PDMR notifications (3 business days) |
| **Settlement** | T+1 (since May 2024) | T+2 (T+1 expected ~2027) |
| **Primary tax-advantaged account** | IRA / Roth IRA (retirement only) | ISK (no restrictions on withdrawals or age) |
| **Capital gains tax (taxable account)** | 0-37% (short-term = ordinary income) | 30% flat rate |
| **ISK-type flat tax on account value** | Does not exist | ~0.9% of account value/year (varies with statslåneränta) |
| **Wash sale rule** | Yes (30-day window, IRS Pub 550) | No. Does not exist in Swedish tax law. |
| **Zero-commission trading** | Standard at major US brokers | Not available. Courtage applies (0.049-0.25%). |
| **Currency risk on domestic trades** | None (USD) | None (SEK) |
| **Options market depth** | Very deep. Options on thousands of stocks. | Limited. Options on ~20-30 Swedish Large Caps + OMXS30. |
| **Pre/post-market trading** | Extensive (04:00-20:00 ET) | Minimal (08:45-09:00 call auction; 17:25-17:30 closing auction) |
| **Trading hours** | 6.5 hours (regular session) | 8.5 hours (continuous trading) |
| **Primary index** | S&P 500 | OMXS30 |
| **Typical Large Cap spread** | 0.01-0.02% | 0.05-0.15% |
| **Typical daily volume (Large Cap)** | Billions USD | Hundreds of millions SEK |
| **Broker API** | Official APIs common (IBKR, Alpaca, etc.) | No official Avanza API. Unofficial wrappers only. |
| **Data sources** | Abundant (free and paid) | More limited. Yahoo Finance (.ST), Börsdata, Avanza, Nasdaq Nordic. |
| **Circuit breakers** | S&P 500 based (7%, 13%, 20%) | Nasdaq Nordic volatility interruptions (per-stock dynamic thresholds) |
| **Dividends (withholding)** | No withholding for domestic investors | No withholding in ISK. 30% withholding on foreign dividends (reduced by treaty). |
| **Sentiment data** | AAII, put/call ratio, Fear & Greed | Limited. Avanza most-bought/sold lists. No equivalent of AAII or Fear & Greed. |
| **VIX equivalent** | VIX (CBOE) | No Swedish VIX. Use VIX or VSTOXX (Euro STOXX 50 volatility). |

---

## 9. Files That Need Patching

The following research files contain US-only assumptions that should be updated with Swedish alternatives or dual-market notes:

### High priority (contain US-specific rules that differ materially in Sweden)

1. **`09-regulation-tax-and-trade-operations.md`**
   - Section 2: PDT rules - add note that this does not apply in Sweden/EU.
   - Section 3: Cash-account violations - different settlement rules in Sweden; ISK accounts eliminate this concern.
   - Section 8: Tax treatment - entirely US-specific (IRS, wash sale rule, short-term vs long-term gains). Add Swedish ISK treatment.
   - Section 9: Trader tax status / Section 475 - US-only; not applicable in Sweden.
   - Section 10: System design checklist - add ISK as account type; remove PDT constraint for Swedish users.

2. **`22-watchlist-and-universe-selection.md`**
   - Section 2: "Default universe for a serious U.S. equity swing trader" - add Swedish equivalent (Large Cap + top Mid Cap).
   - Section 4: Core universe filters - all thresholds are in USD and reference NYSE/Nasdaq. Add SEK thresholds and Stockholm segments.
   - Listing venue section references NYSE, Nasdaq, OTC - add Nasdaq Stockholm, First North.

3. **`08-market-structure-and-conditions.md`**
   - Section 1.3: VIX references - note that no Swedish VIX exists; use VIX or VSTOXX.
   - Section 3.2: Sector ETF table - entirely US ETFs (XLK, XLF, etc.). Add SX sector indices for Swedish context.
   - Section 4.1: Seasonality data is S&P 500 specific. Note that Swedish market seasonality broadly follows but with some differences (ex-dividend season in April-May).
   - Section 4.3: Options expiration effects - OMXS30 options follow a different cycle.
   - Section 4.5: FOMC - add Riksbanken decisions as the Swedish equivalent.
   - Section 5.3: AAII sentiment survey - US only; no Swedish equivalent.
   - Section 5.5: Short interest data - FINRA-specific. FI has a different disclosure regime.
   - Section 5.6: Insider trading data - SEC Form 4 references. Swedish traders use FI's PDMR register.

4. **`24-execution-and-slippage-playbook.md`**
   - Section 4: Extended-hours execution - Swedish market has minimal extended hours.
   - General: Spread and slippage assumptions throughout are calibrated to US liquidity. Swedish stocks have wider spreads.

### Medium priority (contain US references that should be noted)

5. **`06-apis-and-technology.md`**
   - Broker API section covers US brokers (Alpaca, IBKR, Schwab). Add Avanza unofficial API.
   - Data source section covers US-centric providers. Add Börsdata, Nasdaq Nordic, Avanza data.
   - Yahoo Finance section should note the `.ST` suffix for Stockholm stocks.

6. **`16-stock-screening-playbook.md`**
   - Scanner parameters use USD-denominated thresholds. Add SEK equivalents.
   - Sector ETF references (SPY, QQQ, XLK) need Swedish equivalents.
   - IBD RS Rating references - not available for Swedish stocks; must be calculated.

7. **`21-catalyst-and-event-playbook.md`**
   - Section 2: SEC filings / Form 8-K - Swedish companies use different disclosure frameworks.
   - Section 3: Macro catalysts reference FOMC, NFP, CPI (US). Add Riksbanken, Swedish CPI, ECB.
   - FDA references - relevant only for US-listed pharma; Swedish pharma follows EMA.

8. **`13-trading-plan-and-daily-routine.md`**
   - Trading hours and session timing references are US-based. Swedish hours differ.
   - Pre-market routine references US economic calendar. Add Swedish/European calendar.
   - Account rules reference PDT and cash-account settlement constraints that do not apply in Sweden.

9. **`15-options-for-swing-trading.md`**
   - Entire file assumes deep US options markets. Swedish options are far more limited.
   - Section 1.1: "Most U.S. equity and ETF options are American style" - OMXS30 options are European style.
   - Add note about limited single-stock options availability in Sweden.

### Lower priority (minor US references)

10. **`05-risk-management.md`**
    - Any references to margin requirements should note that Swedish/EU margin rules differ from Reg T.
    - Position sizing examples using USD should include SEK examples.

11. **`01-swing-trading-fundamentals.md`**
    - Account structure references (cash vs margin) should note ISK as the primary Swedish account type.
    - PDT references should note non-applicability in Sweden.

12. **`00-research-map-and-sources.md`**
    - "Primary focus: U.S.-listed equities and ETFs" should be expanded to include Swedish/Nordic equities.
    - Source set is entirely US-centric. Add Swedish/EU sources.

---

## Sources

### Swedish regulatory and tax sources

- Finansinspektionen (FI), main website
  https://www.fi.se/en/

- Skatteverket, Investeringssparkonto (ISK)
  https://www.skatteverket.se/privat/skatter/vardepapper/investeringssparkonto

- Skatteverket, Kapitalvinst och kapitalförlust (Capital gains/losses)
  https://www.skatteverket.se/privat/skatter/vardepapper

- EU Short Selling Regulation (EU 236/2012)
  https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32012R0236

- EU Market Abuse Regulation (MAR, EU 596/2014)
  https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32014R0596

- MiFID II Directive (2014/65/EU)
  https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32014L0065

### Avanza sources

- Avanza, Prislista (fee schedule)
  https://www.avanza.se/priser-villkor/prislista.html

- Avanza, ISK information
  https://www.avanza.se/konton-lan-rantor/konton/investeringssparkonto-isk.html

- Avanza, Help pages (order types, stop-loss)
  https://www.avanza.se/kundservice.html

### Market structure sources

- Nasdaq Nordic, market information
  https://www.nasdaq.com/market-activity/nordic

- Riksbanken (Swedish Central Bank)
  https://www.riksbank.se/en-gb/

- Statistiska Centralbyran (SCB), Swedish statistics
  https://www.scb.se/en/

### Unofficial API sources

- Avanza Python API (unofficial)
  https://github.com/Qluxzz/avanza

- Avanza Node.js API (unofficial)
  https://github.com/fhqvst/avanza

### Data provider sources

- Börsdata (Swedish stock screening and fundamentals)
  https://borsdata.se

- Yahoo Finance (Swedish stocks via .ST suffix)
  https://finance.yahoo.com
