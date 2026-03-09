# APIs, Data Sources, and Technology for Swing Trading

This document covers the technology landscape for building a swing trading application: market data APIs, broker integrations, backtesting frameworks, technical analysis libraries, screening tools, data storage, and notification systems.

---

## 1. Market Data APIs

Market data is the foundation of any trading system. The choice of data provider affects cost, reliability, data quality, and the types of analysis you can perform.

### 1.1 Yahoo Finance (yfinance)

**Overview:** An unofficial Python library that scrapes Yahoo Finance data. The most popular free option for historical stock data.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free (unofficial, no API key needed) |
| **Language** | Python (`pip install yfinance`) |
| **Data Types** | OHLCV, dividends, splits, financials, options chains, earnings |
| **Timeframes** | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo |
| **Historical Depth** | Intraday: 7-60 days depending on interval. Daily: decades of data |
| **Rate Limits** | Unofficial; aggressive scraping may get IP-blocked |
| **Real-time** | Delayed 15 minutes for US equities |

**Strengths:**
- Zero cost, no registration required
- Extremely easy to use (3 lines of code to get data)
- Covers global markets (US, EU, Asia, crypto, forex, indices)
- Good for historical daily data and fundamental screening
- Active open-source community maintaining the library

**Limitations:**
- Unofficial API; Yahoo can break it at any time (has happened multiple times)
- No guaranteed uptime or SLA
- Data quality issues: occasional gaps, adjusted vs unadjusted confusion
- Rate limiting is unpredictable; no official limits published
- Intraday data limited to recent periods
- Not suitable for production systems requiring high reliability

**Example Usage:**
```python
import yfinance as yf

# Single ticker
msft = yf.Ticker("MSFT")
hist = msft.history(period="1y", interval="1d")

# Multiple tickers
data = yf.download(["AAPL", "GOOGL", "MSFT"], period="6mo", interval="1d")
```

**Swedish stocks:** Yahoo Finance supports Stockholm-listed stocks using the `.ST` ticker suffix. Examples: `VOLV-B.ST` (Volvo B), `ERIC-B.ST` (Ericsson B), `HM-B.ST` (H&M B), `SEB-A.ST` (SEB A). The OMXS30 index is available as `^OMX`. Data quality for Swedish Large Cap stocks is generally good. Some First North stocks may have incomplete data. Dividend adjustment can occasionally be wrong for Swedish stocks with special dividends.

```python
# Swedish stock example
import yfinance as yf
volvo = yf.download("VOLV-B.ST", period="1y")
omxs30 = yf.download("^OMX", period="1y")
```

**Verdict:** Excellent for prototyping, backtesting, and personal projects. Not reliable enough for production trading systems. Use it as a starting point, then migrate to a paid API when the system matures.

---

### 1.2 Alpha Vantage

**Overview:** A popular freemium API providing stock, forex, crypto, and economic indicator data with a structured REST API.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free: 25 requests/day. Premium: $49.99/mo (75 req/min), $99.99/mo (150 req/min), $149.99/mo (300 req/min), $249.99/mo (1200 req/min) |
| **Language** | REST API (any language); official Python wrapper available |
| **Data Types** | OHLCV, technical indicators (50+ built-in), forex, crypto, fundamentals, economic indicators |
| **Timeframes** | 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly |
| **Historical Depth** | 20+ years for daily data; 1-2 months for intraday |
| **Real-time** | Available on premium plans |

**Strengths:**
- Built-in technical indicator calculations (SMA, EMA, RSI, MACD, Bollinger, etc.)
- Clean, well-documented REST API
- Supports multiple asset classes
- Economic indicators (GDP, CPI, unemployment) for macro analysis
- Generous enough free tier for development

**Limitations:**
- Free tier is severely limited (25 requests/day is almost unusable)
- Even paid plans have per-minute rate limits that slow bulk downloads
- Data delivery can be slow compared to WebSocket-based providers
- No streaming/WebSocket support; polling only
- Historical intraday data limited to 1-2 months
- Some data quality issues reported in community forums

**Verdict:** Good middle-ground option. The built-in technical indicators are convenient. However, the rate limits make it painful for scanning large universes of stocks. Better for monitoring a watchlist than for broad market screening.

---

### 1.3 Polygon.io

**Overview:** A professional-grade market data API used by hedge funds and fintech companies. Known for reliability and comprehensive data.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free: 5 API calls/min, delayed data. Starter: $29/mo (unlimited API calls, delayed). Developer: $79/mo (unlimited, real-time). Advanced: $199/mo (full feature set). Business: custom |
| **Language** | REST + WebSocket; official clients for Python, Go, Kotlin, JavaScript |
| **Data Types** | OHLCV, trades, quotes, options, forex, crypto, reference data, news, financials |
| **Timeframes** | Tick-level, 1s, 1min to monthly aggregates |
| **Historical Depth** | Full historical US equities data (decades). Tick data from 2003+ |
| **Real-time** | Yes (Developer plan and above) |

**Strengths:**
- Professional-grade data quality and reliability
- WebSocket streaming for real-time data
- Tick-level granularity available
- Comprehensive: stocks, options, forex, crypto in one API
- Flat-file downloads available for bulk historical data
- Well-maintained Python client library
- Reference data includes ticker details, market status, conditions

**Limitations:**
- Free tier is very limited (5 calls/min, delayed data)
- Real-time data requires $79+/mo
- Options data requires higher-tier plans
- Primarily US markets (limited international coverage)
- Tick data volume can be overwhelming for simple swing trading

**Verdict:** Best overall choice for a serious swing trading application focused on US markets. The $29/mo Starter plan is sufficient for end-of-day swing trading with daily scans. Upgrade to Developer ($79/mo) if you need real-time alerts.

---

### 1.4 IEX Cloud

**Overview:** Data platform from IEX (Investors Exchange). Known for clean APIs and transparent pricing.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free: 50,000 credits/mo. Launch: $9/mo (5M credits). Grow: $49/mo (unlimited core data). Scale: custom |
| **Language** | REST API; Python, JavaScript, R wrappers available |
| **Data Types** | OHLCV, real-time quotes, fundamentals, earnings, news, economic data, CEO compensation |
| **Timeframes** | 1min, 5min, daily, weekly, monthly |
| **Historical Depth** | 15+ years daily; 90 days intraday |
| **Real-time** | Yes (real-time IEX prices are free; consolidated real-time on paid plans) |

**Strengths:**
- Clean, intuitive API design
- Rich fundamental data (financials, earnings, estimates)
- News and sentiment data included
- Good documentation and developer experience
- Credit-based pricing is flexible (pay for what you use)
- Sandbox environment for testing

**Limitations:**
- Credit system can be confusing; some endpoints cost many credits
- Free tier credits burn quickly with regular usage
- Limited international market coverage
- Intraday history limited to 90 days
- Some data formerly available has been moved to premium tiers
- Company underwent restructuring; future uncertain as of 2025

**Verdict:** Good for applications that need both market data and fundamental data in one place. The credit system is flexible but can get expensive if you are not careful about which endpoints you call.

---

### 1.5 Twelve Data

**Overview:** A newer entrant offering comprehensive global market data with competitive pricing.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free: 8 API calls/min, 800/day. Basic: $8/mo (unlimited daily). Pro: $29/mo (real-time US). Ultra: $49/mo. Enterprise: custom |
| **Language** | REST + WebSocket; Python, JavaScript, Go, PHP, Ruby SDKs |
| **Data Types** | OHLCV, 100+ technical indicators, forex, crypto, ETFs, indices, mutual funds |
| **Timeframes** | 1min to monthly |
| **Historical Depth** | 30+ years daily; varying intraday |
| **Real-time** | WebSocket streaming on paid plans |

**Strengths:**
- Very competitive pricing
- Built-in technical indicator API (100+ indicators computed server-side)
- Good global market coverage (100+ exchanges)
- WebSocket support for real-time streaming
- Batch requests supported (multiple symbols in one call)
- Clean documentation

**Limitations:**
- Smaller community compared to older providers
- Free tier rate limits are tight
- Some advanced features only on higher tiers
- Data quality for less liquid instruments can be spotty
- Company is relatively young; track record shorter than competitors

**Verdict:** Strong value for money. The $29/mo Pro plan covers most swing trading needs including real-time US data. Worth considering as a primary or secondary data source.

---

### 1.6 Finnhub

**Overview:** A Finnish fintech company offering real-time stock data, news, and alternative data through a modern API.

| Aspect | Details |
|--------|---------|
| **Pricing** | Free: 60 calls/min. Starter: $49.99/mo. Professional: $149.99/mo. Enterprise: custom |
| **Language** | REST + WebSocket; Python, JavaScript, Go, Kotlin, Ruby SDKs |
| **Data Types** | OHLCV, real-time quotes, company news, SEC filings, insider transactions, earnings surprises, social sentiment, economic calendar |
| **Timeframes** | 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly |
| **Historical Depth** | 20+ years daily (on paid plans); limited free historical |
| **Real-time** | Free tier includes real-time WebSocket for US stocks |

**Strengths:**
- Free real-time US stock prices via WebSocket (rare)
- Rich alternative data: insider transactions, lobbying, congressional trading, social sentiment
- SEC filing data and earnings calendars
- Pattern recognition API (candlestick patterns detected server-side)
- Generous free tier for real-time streaming
- Economic calendar useful for avoiding news-driven volatility

**Limitations:**
- Free tier historical data is limited
- Some alternative data endpoints are on premium tiers only
- Candle/OHLCV historical depth varies by plan
- Rate limits can be restrictive for large scans
- Documentation could be more detailed for some endpoints

**Verdict:** Excellent complement to another primary data source. The free real-time WebSocket and alternative data (insider trading, sentiment) are uniquely valuable for swing trading signals.

---

### 1.7 Quandl / Nasdaq Data Link

**Overview:** Quandl was acquired by Nasdaq and rebranded as Nasdaq Data Link. Offers curated financial, economic, and alternative datasets.

| Aspect | Details |
|--------|---------|
| **Pricing** | Many free datasets. Premium datasets: $20-$5,000+/mo depending on dataset |
| **Language** | REST API; Python, R, Excel wrappers |
| **Data Types** | Economic data, futures, commodities, alternative data, fundamental data |
| **Timeframes** | Varies by dataset (mostly daily) |
| **Historical Depth** | Extensive (some datasets go back 100+ years) |
| **Real-time** | No (primarily historical/end-of-day data) |

**Strengths:**
- Massive collection of curated datasets
- Excellent for economic and macro data
- Academic-quality data with documented methodologies
- Bulk download support (CSV, JSON, XML)
- Good for fundamental and quantitative research
- Free datasets include FRED economic data, Wiki EOD prices

**Limitations:**
- Not designed for real-time trading
- Premium datasets are expensive
- Wiki EOD dataset (formerly free) has been discontinued
- Primarily a data vendor, not a trading data API
- Not ideal as a primary market data source for a trading app
- Confusing transition from Quandl to Nasdaq Data Link branding

**Verdict:** Best used as a supplementary data source for economic/fundamental data, not as a primary market data feed. The FRED economic dataset is excellent for understanding macro context.

---

### Market Data API Comparison Summary

| Provider | Best For | Monthly Cost | Real-time | Global | Ease of Use |
|----------|---------|-------------|-----------|--------|-------------|
| yfinance | Prototyping | Free | No (15m delay) | Yes | Excellent |
| Alpha Vantage | Built-in indicators | $49-$249 | Paid only | Partial | Good |
| Polygon.io | Production US data | $29-$199 | $79+ | No (US focus) | Excellent |
| IEX Cloud | Fundamentals + market | $9-$49 | Paid plans | No (US focus) | Excellent |
| Twelve Data | Budget-friendly | $8-$49 | $29+ | Yes | Good |
| Finnhub | Alt data + free RT | Free-$150 | Free WS | Partial | Good |
| Nasdaq Data Link | Economic/macro data | Free-$$$$ | No | Yes | Moderate |

**Recommended Stack for Swing Trading:**
1. **Development/Prototyping:** yfinance (free, fast iteration)
2. **Production Data:** Polygon.io Starter ($29/mo) or Twelve Data Pro ($29/mo)
3. **Real-time Alerts:** Finnhub free WebSocket or Polygon.io Developer ($79/mo)
4. **Supplementary:** Finnhub for insider/sentiment data, Nasdaq Data Link for economic data

### Swedish Market Data Sources

> **Full reference:** See `27-swedish-market-adaptation.md` Section 7 for complete details.

For Swedish stocks, the US-centric data providers above (Polygon.io, IEX Cloud) have limited or no coverage. The following sources cover Stockholm-listed stocks:

| Provider | Data Type | Cost | Notes |
|----------|-----------|------|-------|
| **Yahoo Finance (.ST suffix)** | OHLCV, fundamentals | Free | Use `yfinance` with `.ST` suffix tickers. Good for prototyping. See Section 1.1 above. |
| **Borsdata (borsdata.se)** | Fundamental data, screening, financial history | Subscription (~SEK 400-800/mo) | Swedish-focused. Excellent for Swedish stock screening and fundamental analysis. Often called "the Swedish TIKR." |
| **Nasdaq Nordic** | Official trading statistics, index compositions, corporate actions | Free (website) | https://www.nasdaq.com/market-activity/nordic. Official source for listed companies, short selling statistics, and news releases. |
| **Avanza** | Real-time quotes, key ratios, insider alerts, earnings calendar | Free (basic) / subscription (real-time) | Data accessible through unofficial API. See broker section below. |
| **Infront / Millistream** | Real-time and historical Nordic data | Professional pricing | API available. Used by many Nordic financial services. |
| **Riksbanken** | Interest rate decisions, SEK exchange rates | Free | https://www.riksbank.se. Swedish equivalent of Federal Reserve data. |
| **SCB (Statistics Sweden)** | Swedish CPI, GDP, labor market | Free | https://www.scb.se. Official economic statistics. |

**Recommended Swedish stack:**
1. **Development/Prototyping:** yfinance with `.ST` suffix tickers (free)
2. **Screening/Fundamentals:** Borsdata (subscription)
3. **Official market data:** Nasdaq Nordic website (free)
4. **Macro/economic data:** Riksbanken + SCB (free)
5. **Broker integration:** Avanza unofficial API or IBKR official API

---

## 2. Broker APIs

Broker APIs enable automated order execution, portfolio management, and paper trading. The choice of broker determines which markets you can trade, commission structure, and API capabilities.

### 2.1 Interactive Brokers (IBKR)

**Overview:** The gold standard for algorithmic and systematic trading. Used by professional traders, hedge funds, and institutions worldwide.

| Aspect | Details |
|--------|---------|
| **Commission** | $0.005/share (min $1, max 1% of trade value). $0 on IBKR Lite |
| **API Types** | TWS API (socket), Client Portal API (REST), FIX API (institutional) |
| **Languages** | Java, Python, C++, C#. TWS API is the primary interface |
| **Paper Trading** | Yes, full paper trading environment mirroring live |
| **Markets** | 150+ markets in 33 countries. Stocks, options, futures, forex, bonds, funds |
| **Minimum Account** | $0 (IBKR Lite), $0 (IBKR Pro, but $10/mo inactivity fee if < $100K, waived 2024+) |

**Strengths:**
- Most comprehensive market access of any retail broker
- Full-featured TWS API with streaming data, order management, account info
- Paper trading environment is nearly identical to live
- Advanced order types: bracket orders, trailing stops, conditional orders, algorithms
- Market data available through the API (subscription fees apply)
- Margin rates among the lowest in the industry
- Supports algorithmic trading at scale

**Limitations:**
- TWS API is complex and has a steep learning curve
- Requires TWS or IB Gateway running locally (not a pure REST API)
- Connection management is finicky (heartbeats, reconnection logic)
- Rate limits on API requests and market data subscriptions
- Market data subscriptions are additional cost ($1.50-$10+/mo per exchange)
- Documentation is extensive but sometimes outdated
- Python API is a thin wrapper; not Pythonic

**Key Python Libraries:**
- `ib_insync` - High-level async Python wrapper (most recommended)
- `ibapi` - Official IB Python API
- `ib-gateway-docker` - Docker container for headless IB Gateway

**Example with ib_insync:**
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # 7497=paper, 7496=live

contract = Stock('AAPL', 'SMART', 'USD')
order = MarketOrder('BUY', 100)
trade = ib.placeOrder(contract, order)
```

**Verdict:** The best choice for serious traders who need global market access and advanced order types. The learning curve is steep, but `ib_insync` makes it manageable. Essential if you trade options, futures, or international markets.

---

### 2.2 Alpaca Markets

**Overview:** A commission-free, API-first brokerage built specifically for algorithmic trading. The most developer-friendly option.

| Aspect | Details |
|--------|---------|
| **Commission** | $0 for US equities and ETFs |
| **API Types** | REST + WebSocket (streaming) |
| **Languages** | Python, JavaScript, Go, C# official SDKs |
| **Paper Trading** | Yes, excellent paper trading with separate API endpoint |
| **Markets** | US equities, ETFs, crypto. No options, futures, or international |
| **Minimum Account** | $0 |

**Strengths:**
- Zero commission on all trades
- True API-first design; best developer experience of any broker
- Excellent paper trading (separate base URL, same API)
- Clean REST API with WebSocket streaming for real-time data
- Free real-time market data (IEX) included; SIP data for $9/mo
- Bracket orders, trailing stops, OCO orders supported
- Fractional shares supported
- Active Discord community
- Market data API included (can use as both data source and broker)

**Limitations:**
- US equities and crypto only; no options, futures, forex, or international markets
- Relatively new company (founded 2015, launched 2018)
- Limited order types compared to IBKR
- No phone support; mostly email/chat
- Crypto trading has limitations compared to dedicated crypto exchanges
- Account protection: SIPC up to $500K (standard), no excess coverage

**Example Usage:**
```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient('API_KEY', 'SECRET_KEY', paper=True)

order = MarketOrderRequest(
    symbol="AAPL",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)
client.submit_order(order)
```

**Verdict:** The top recommendation for a Python-based swing trading system focused on US equities. The developer experience is unmatched, paper trading is seamless, and zero commission means no friction cost. Start here unless you need options or international markets.

---

### 2.3 TD Ameritrade / Charles Schwab

**Overview:** TD Ameritrade had one of the best retail trading APIs. After the Schwab acquisition (2023-2024), the API landscape is in transition.

| Aspect | Details |
|--------|---------|
| **Commission** | $0 for stocks/ETFs. $0.65/contract for options |
| **API Types** | REST API (Schwab Developer Portal) |
| **Languages** | REST (any language); community Python wrappers |
| **Paper Trading** | Yes, via thinkorswim platform |
| **Markets** | US equities, ETFs, options, futures, forex |
| **Minimum Account** | $0 |

**Strengths:**
- Well-established brokerage with strong regulatory standing
- thinkorswim platform is excellent for manual analysis
- Options and futures trading available
- Large customer base means good community support
- Paper trading through thinkorswim

**Limitations:**
- API transition from TD Ameritrade to Schwab is ongoing and disruptive
- New Schwab API has different authentication flow (OAuth 2.0)
- Community wrappers may be outdated during the transition
- Documentation quality has decreased during migration
- Some features from the old TDA API may not be available in the new Schwab API
- Not API-first; the API is secondary to the brokerage platform

**Verdict:** Wait for the Schwab API to stabilize before building new integrations. If you already have a TDA integration, plan for migration. Not recommended for new projects until the transition is complete.

---

### 2.4 Tradier

**Overview:** A brokerage platform designed for developers, offering a modern REST API with competitive pricing. Popular with options traders.

| Aspect | Details |
|--------|---------|
| **Commission** | $0 for stocks/ETFs. $0.35/contract for options |
| **API Types** | REST + WebSocket (streaming) |
| **Languages** | REST (any language); community Python wrappers |
| **Paper Trading** | Yes, sandbox environment available |
| **Markets** | US equities, ETFs, options |
| **Minimum Account** | $0 |

**Strengths:**
- Clean REST API with good documentation
- Excellent options chain data and trading
- WebSocket streaming for real-time data
- Sandbox/paper trading environment
- Competitive options pricing ($0.35/contract)
- OAuth 2.0 authentication
- Market data included with brokerage account

**Limitations:**
- Smaller company than IBKR or Schwab
- No futures, forex, or international markets
- Community smaller than Alpaca or IBKR
- Fewer advanced order types than IBKR
- Limited educational resources

**Verdict:** Good choice if options trading is central to your swing trading strategy. The API is clean and the options pricing is competitive. However, for equities-only swing trading, Alpaca is more feature-rich and commission-free.

---

### 2.5 OANDA (Forex)

**Overview:** A leading forex broker with a well-designed REST API. The standard choice for algorithmic forex trading.

| Aspect | Details |
|--------|---------|
| **Commission** | Spread-based (no separate commission). EUR/USD spread ~1.0-1.4 pips |
| **API Types** | REST v20 + Streaming API |
| **Languages** | REST (any language); `oandapyV20` Python wrapper |
| **Paper Trading** | Yes, free practice account with virtual funds |
| **Markets** | 70+ forex pairs, CFDs on indices/commodities/bonds, crypto (limited) |
| **Minimum Account** | $0 (practice), varies by jurisdiction for live |

**Strengths:**
- Industry-standard forex API
- Clean REST API design (v20)
- Streaming API for real-time price updates
- Historical candle data available through API
- Practice account for paper trading
- Well-documented with code examples
- Regulated in multiple jurisdictions

**Limitations:**
- Forex/CFDs only; no equities
- CFDs not available to US residents
- Spreads widen during volatile periods
- Limited crypto offerings
- Some advanced features jurisdiction-dependent
- v20 API replaced the older v1 API; ensure using current version

**Verdict:** The go-to choice for forex swing trading. If your strategy involves currency pairs, OANDA's API is mature and reliable. Not applicable for equity swing trading.

---

### 2.6 Binance (Crypto)

**Overview:** The world's largest cryptocurrency exchange by volume, with a comprehensive trading API.

| Aspect | Details |
|--------|---------|
| **Commission** | 0.1% maker/taker (discounts with BNB or volume tiers) |
| **API Types** | REST + WebSocket (spot, futures, margin) |
| **Languages** | Official Python (`python-binance`), JavaScript, Java, Go SDKs |
| **Paper Trading** | Yes, Testnet environment for spot and futures |
| **Markets** | 600+ crypto trading pairs, spot, futures, margin, options |
| **Minimum Account** | $0 |

**Strengths:**
- Highest liquidity for most crypto pairs
- Comprehensive API: spot, margin, futures, options
- WebSocket streaming for real-time orderbook, trades, candles
- Testnet for paper trading
- Rich historical data through API
- Low trading fees with volume discounts
- Well-maintained Python SDK

**Limitations:**
- Regulatory uncertainty (not available in all US states via Binance.US)
- US users must use Binance.US (limited features compared to global Binance)
- API rate limits require careful management
- Security requires careful key management (IP whitelisting recommended)
- High volatility in crypto markets increases risk
- API changes with little notice during extreme market conditions

**Verdict:** The best API for crypto swing trading if you are outside the US. US-based traders should consider Binance.US (limited) or Alpaca's crypto offering. The API is comprehensive but requires careful security practices.

---

### Broker API Comparison Summary

| Broker | Commission | Markets | API Quality | Paper Trading | Best For |
|--------|-----------|---------|-------------|---------------|----------|
| IBKR | $0.005/share | Global (all asset classes) | Complex but powerful | Excellent | Multi-asset, global |
| Alpaca | $0 | US equities, crypto | Excellent | Excellent | US equity algo trading |
| Schwab | $0 equities | US equities, options, futures | In transition | Via thinkorswim | Existing TDA users |
| Tradier | $0 equities, $0.35/opt | US equities, options | Good | Yes | Options-focused |
| OANDA | Spread-based | Forex, CFDs | Excellent | Yes | Forex |
| Binance | 0.1% | Crypto (600+ pairs) | Excellent | Yes (testnet) | Crypto |

**Recommended for a Swing Trading App:**
1. **US Equities:** Alpaca (primary), IBKR (if you need more markets or order types)
2. **Paper Trading Phase:** Alpaca (seamless switch between paper and live)
3. **Multi-Asset:** IBKR (the only option covering everything)
4. **Forex:** OANDA
5. **Crypto:** Binance (non-US) or Alpaca (US)
6. **Swedish Equities:** Avanza (primary Swedish broker) or IBKR (for broader Nordic/EU access and official API)

### Swedish Market: Avanza (Unofficial API)

> **Full reference:** See `27-swedish-market-adaptation.md` Section 3 for complete Avanza details.

**Overview:** Avanza is the largest online broker in Sweden. It does not offer an official API, but unofficial community-maintained wrappers exist.

| Aspect | Details |
|--------|---------|
| **Commission** | Courtage: 0.049% (highest tier, > SEK 50K/month turnover) to 0.25% (lowest tier). Not zero-commission. |
| **API Types** | Unofficial REST wrappers only. No official API. |
| **Languages** | Python (`pip install avanza-api` or github.com/Qluxzz/avanza), Node.js (github.com/fhqvst/avanza) |
| **Paper Trading** | No paper trading environment. |
| **Markets** | Swedish equities (Nasdaq Stockholm), Nordic equities, some US/EU stocks. ISK, KF, and depot account types. |
| **Minimum Account** | SEK 0 |

**Strengths:**
- ISK (Investeringssparkonto) account type with favorable flat-rate tax (no capital gains tax on individual trades)
- Real-time quotes (with subscription), insider transaction alerts, earnings calendar
- The broker most Swedish retail traders use; deep integration with Swedish market structure
- Basic stop-loss orders supported

**Limitations:**
- No official API -- unofficial wrappers may break without notice
- No OCO, bracket orders, or conditional orders
- No paper trading environment
- No options on US stocks (only Swedish OMXS30 and ~20-30 Swedish Large Cap single-stock options)
- Courtage is not zero -- must be modeled in backtests
- Stop-loss triggers a market order (not stop-limit)

**Verdict:** The default choice for Swedish retail swing traders due to ISK tax advantages. For algorithmic trading or advanced order types, consider Interactive Brokers (IBKR) which supports Nordic markets and has an official API. IBKR does not offer ISK accounts directly, however.

---

## 3. Backtesting Frameworks

Backtesting is essential for validating trading strategies against historical data before risking real capital. The framework choice affects speed, flexibility, and accuracy of simulations.

### 3.1 Backtrader

**Overview:** The most popular Python backtesting framework. Event-driven architecture that simulates real market conditions including order execution, commissions, and slippage.

| Aspect | Details |
|--------|---------|
| **Language** | Python |
| **Architecture** | Event-driven |
| **License** | GPL v3 (open source) |
| **Live Trading** | Yes (IBKR, Oanda, Alpaca via plugins) |
| **Documentation** | Extensive, with examples |
| **Community** | Large, active (GitHub, forums) |

**Strengths:**
- Mature and battle-tested framework
- Built-in indicators (200+) and analyzers (Sharpe, drawdown, trade stats)
- Supports multiple data feeds, timeframes, and strategies simultaneously
- Built-in commission and slippage models
- Can connect to live brokers for paper/live trading
- Supports portfolio-level strategies (multi-asset)
- Visualization built-in (uses matplotlib)
- Cerebro engine handles the event loop cleanly

**Limitations:**
- Slow for large backtests (pure Python, not vectorized)
- Learning curve: the framework has many abstractions
- Project maintenance has slowed (creator less active since 2021)
- Debugging can be difficult due to the event-driven architecture
- Memory-intensive for large datasets
- Not ideal for high-frequency strategies

**Example:**
```python
import backtrader as bt

class SwingStrategy(bt.Strategy):
    params = (('sma_period', 20), ('rsi_period', 14))

    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)

    def next(self):
        if not self.position:
            if self.data.close > self.sma and self.rsi < 30:
                self.buy(size=100)
        elif self.rsi > 70:
            self.sell(size=100)

cerebro = bt.Cerebro()
cerebro.addstrategy(SwingStrategy)
cerebro.adddata(bt.feeds.YahooFinanceData(dataname='AAPL', fromdate=datetime(2020,1,1)))
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.001)
cerebro.run()
cerebro.plot()
```

**Verdict:** The best starting point for swing trading backtests. The event-driven model accurately simulates real trading conditions. Accept the speed limitation unless you are testing thousands of parameter combinations.

---

### 3.2 Zipline

**Overview:** Originally developed by Quantopian (now defunct), Zipline is an event-driven backtesting library that powered one of the most popular quant research platforms.

| Aspect | Details |
|--------|---------|
| **Language** | Python |
| **Architecture** | Event-driven |
| **License** | Apache 2.0 |
| **Live Trading** | Limited (community plugins) |
| **Documentation** | Good but partially outdated |
| **Community** | Declining since Quantopian shut down |

**Strengths:**
- Institutional-quality pipeline system for factor analysis
- Built-in data bundle system (Quandl, custom bundles)
- Strong integration with pyfolio for performance analysis
- Pipeline API enables sophisticated screening logic
- Handles splits, dividends, and corporate actions correctly
- Good for portfolio-level strategies

**Limitations:**
- Installation is painful (C dependencies, version conflicts)
- Quantopian shut down in 2020; official development stopped
- Community fork `zipline-reloaded` exists but development is slow
- Data bundle system is rigid; hard to use custom data
- Not compatible with latest pandas/numpy without patches
- No built-in live trading support
- Learning curve is steep for the Pipeline API

**Verdict:** Historical significance but not recommended for new projects. The installation issues and maintenance uncertainty make it a poor choice. Use Backtrader or VectorBT instead.

---

### 3.3 VectorBT

**Overview:** A high-performance vectorized backtesting library built on NumPy and Numba. Designed for speed and parameter optimization.

| Aspect | Details |
|--------|---------|
| **Language** | Python (NumPy/Numba under the hood) |
| **Architecture** | Vectorized |
| **License** | Free: Apache 2.0. Pro: paid ($49-$199/mo) |
| **Live Trading** | Limited (community plugins) |
| **Documentation** | Good, with examples |
| **Community** | Growing, active Discord |

**Strengths:**
- Extremely fast: 100-1000x faster than event-driven frameworks
- Ideal for parameter optimization and walk-forward analysis
- Built-in portfolio optimization
- Rich visualization and analysis tools
- NumPy/Pandas integration is natural for data scientists
- Can test thousands of parameter combinations in seconds
- Memory-efficient through vectorized operations
- Excellent for Monte Carlo simulations and statistical analysis

**Limitations:**
- Vectorized approach cannot model complex order logic (e.g., conditional orders based on portfolio state)
- Free version lacks some advanced features
- Not suitable for strategies requiring tick-by-tick execution simulation
- Assumes instant execution (no realistic order fill simulation)
- Does not handle live trading natively
- Steeper learning curve for the vectorized paradigm

**Example:**
```python
import vectorbt as vbt
import numpy as np

# Download data
price = vbt.YFData.download("AAPL", period="5y").get("Close")

# Test all SMA crossover combinations
fast_ma = vbt.MA.run(price, np.arange(5, 50, 5))
slow_ma = vbt.MA.run(price, np.arange(20, 100, 10))

# Generate entry/exit signals for all combinations
entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

# Run all backtests at once
portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000)
portfolio.total_return().max()  # Best combination
```

**Verdict:** The best choice for parameter optimization and rapid strategy exploration. Use VectorBT for research and initial strategy development, then validate final strategies in Backtrader for more realistic execution simulation. The two complement each other well.

---

### 3.4 QuantConnect / Lean

**Overview:** QuantConnect is a cloud-based algorithmic trading platform powered by the open-source Lean engine. Supports multiple languages and asset classes.

| Aspect | Details |
|--------|---------|
| **Language** | Python, C# |
| **Architecture** | Event-driven |
| **License** | Lean: Apache 2.0 (open source). Cloud: free tier + paid plans |
| **Live Trading** | Yes (multiple brokers) |
| **Documentation** | Excellent |
| **Community** | Large, active forums |

**Strengths:**
- Full lifecycle: research, backtest, paper trade, live trade in one platform
- Cloud-based: no local setup needed (or run Lean locally)
- Supports equities, options, futures, forex, crypto
- Historical data included (Polygon, Morningstar, etc.)
- Alpha Streams marketplace for strategy monetization
- Institutional-grade: handles corporate actions, margin, multi-asset
- Active development and growing community
- Free cloud tier generous for learning

**Limitations:**
- Cloud-based means your code runs on their servers (IP concerns)
- Running Lean locally requires significant setup
- C# documentation is more complete than Python
- Cloud execution has resource limits on free tier
- Data is cloud-hosted; cannot easily use your own data sources
- Learning curve for the Lean engine's abstractions

**Verdict:** Excellent for traders who want a complete platform without managing infrastructure. The free cloud tier is generous enough for swing trading strategy development. Consider running Lean locally if you want full control over your data and execution.

---

### 3.5 Custom Backtesting Approach

For swing trading specifically, a custom backtester can be simpler and more transparent than using a full framework.

**When to Build Custom:**
- Strategy logic is simple (entry/exit based on daily indicators)
- You want full transparency and control over the simulation
- You need to integrate with custom data sources
- You want to learn how backtesting works under the hood

**Architecture:**
```python
import pandas as pd

def backtest_swing(df, entry_condition, exit_condition, capital=100000, risk_pct=0.02):
    """Simple swing trading backtester."""
    trades = []
    position = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        if position is None and entry_condition(df, i):
            stop_loss = row['close'] * 0.95  # Example: 5% stop
            risk_per_share = row['close'] - stop_loss
            shares = int((capital * risk_pct) / risk_per_share)
            position = {
                'entry_date': row.name,
                'entry_price': row['close'],
                'shares': shares,
                'stop_loss': stop_loss
            }

        elif position is not None:
            if row['low'] <= position['stop_loss']:
                # Stopped out
                position['exit_date'] = row.name
                position['exit_price'] = position['stop_loss']
                trades.append(position)
                position = None
            elif exit_condition(df, i):
                position['exit_date'] = row.name
                position['exit_price'] = row['close']
                trades.append(position)
                position = None

    return pd.DataFrame(trades)
```

**Verdict:** Recommended as a learning exercise and for simple strategies. Migrate to a framework when you need multi-asset, complex order logic, or realistic commission/slippage modeling.

---

### Backtesting Framework Comparison

| Framework | Speed | Realism | Ease of Use | Live Trading | Best For |
|-----------|-------|---------|-------------|-------------|----------|
| Backtrader | Slow | High | Medium | Yes (plugins) | Realistic simulation |
| Zipline | Slow | High | Difficult | Limited | Legacy / not recommended |
| VectorBT | Very Fast | Low-Medium | Medium | Limited | Parameter optimization |
| QuantConnect | Medium | High | Medium | Yes | Full lifecycle |
| Custom | Medium | Customizable | Easy (simple) | DIY | Learning, simple strategies |

**Recommended Approach:**
1. **Exploration Phase:** VectorBT for rapid testing of indicator combinations
2. **Validation Phase:** Backtrader for realistic simulation with commissions/slippage
3. **Production Phase:** Alpaca paper trading for real market conditions, then go live

---

## 4. Technical Analysis Libraries

These libraries compute the indicators and oscillators used to generate swing trading signals.

### 4.1 TA-Lib

**Overview:** The industry-standard technical analysis library, written in C with Python bindings. Used by quantitative analysts and trading firms worldwide.

| Aspect | Details |
|--------|---------|
| **Language** | C core with Python, Java, .NET, etc. wrappers |
| **Indicators** | 200+ (candlestick patterns, overlap studies, momentum, volume, volatility, cycle) |
| **License** | BSD |
| **Performance** | Excellent (C implementation) |
| **Installation** | Requires C library to be installed first |

**Strengths:**
- Fastest implementation of most technical indicators
- Most comprehensive indicator library available
- Battle-tested in production systems for decades
- 61 candlestick pattern recognition functions
- Consistent API across all indicators
- Handles edge cases (NaN, insufficient data) correctly
- Used as the reference implementation for indicator accuracy

**Limitations:**
- Installation is the primary pain point: requires the C library (not just `pip install`)
  - macOS: `brew install ta-lib` then `pip install ta-lib`
  - Linux: build from source or use conda
  - Windows: download pre-built binary
- Python wrapper is thin; returns NumPy arrays, not labeled DataFrames
- No streaming/incremental calculation support
- Fixed lookback periods; some flexibility limitations
- Documentation is functional but sparse

**Example:**
```python
import talib
import numpy as np

close = np.array(df['close'].values, dtype=float)

# Indicators
sma_20 = talib.SMA(close, timeperiod=20)
rsi = talib.RSI(close, timeperiod=14)
macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
upper, middle, lower = talib.BBANDS(close, timeperiod=20)

# Candlestick patterns
patterns = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
```

**Verdict:** Install it despite the hassle. The speed and accuracy make it the right choice for production systems. Use `conda install -c conda-forge ta-lib` for the easiest installation path.

---

### 4.2 pandas-ta

**Overview:** A modern, pure-Python technical analysis library built as a Pandas DataFrame extension. The most Pythonic option.

| Aspect | Details |
|--------|---------|
| **Language** | Pure Python (Pandas/NumPy) |
| **Indicators** | 130+ indicators in categories: overlap, momentum, trend, volatility, volume, statistics |
| **License** | MIT |
| **Performance** | Good (NumPy vectorized, but slower than TA-Lib's C) |
| **Installation** | Simple: `pip install pandas-ta` |

**Strengths:**
- `pip install` and go. No C dependency headaches
- DataFrame extension: `df.ta.rsi()` adds RSI column directly
- Returns labeled Pandas DataFrames/Series (not raw arrays)
- Strategy class for applying multiple indicators at once
- Active development and responsive maintainer
- Good documentation with examples
- Supports custom indicator creation
- Built-in multiprocessing for strategy calculations

**Limitations:**
- Slower than TA-Lib for computationally intensive operations (2-5x typical)
- Some indicator calculations may differ slightly from TA-Lib
- Fewer candlestick patterns than TA-Lib
- Community smaller than TA-Lib
- Some indicators may have subtle bugs (less battle-tested)

**Example:**
```python
import pandas_ta as ta

# Single indicators
df['rsi'] = df.ta.rsi(length=14)
df['sma_20'] = df.ta.sma(length=20)

# Strategy: apply multiple indicators at once
strategy = ta.Strategy(
    name="Swing Trading",
    ta=[
        {"kind": "sma", "length": 20},
        {"kind": "sma", "length": 50},
        {"kind": "rsi", "length": 14},
        {"kind": "macd"},
        {"kind": "bbands", "length": 20},
        {"kind": "atr", "length": 14},
        {"kind": "adx", "length": 14}
    ]
)
df.ta.strategy(strategy)
```

**Verdict:** The best default choice for Python projects. Use this unless you specifically need TA-Lib's speed or candlestick pattern recognition. The DataFrame integration makes it natural to work with.

---

### 4.3 ta (Technical Analysis Library)

**Overview:** A pure-Python library with a clean class-based API. Focuses on simplicity and readability.

| Aspect | Details |
|--------|---------|
| **Language** | Pure Python (Pandas/NumPy) |
| **Indicators** | 40+ indicators organized by category |
| **License** | MIT |
| **Performance** | Good |
| **Installation** | Simple: `pip install ta` |

**Strengths:**
- Clean class-based API with consistent interface
- Easy to understand source code
- `add_all_ta_features()` function to add everything at once
- Good for quick feature engineering for ML models
- Minimal dependencies

**Limitations:**
- Fewer indicators than pandas-ta or TA-Lib
- Less active development
- No candlestick pattern recognition
- Documentation is minimal
- Community is smaller

**Example:**
```python
import ta

# Add all indicators at once
df = ta.add_all_ta_features(
    df, open="open", high="high", low="low", close="close", volume="volume"
)

# Or individual indicators
df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
df['macd'] = ta.trend.MACD(close=df['close']).macd()
```

**Verdict:** Good for quick prototyping or when you want to add all indicators at once for machine learning feature engineering. For more control, use pandas-ta.

---

### 4.4 tulipy

**Overview:** Python bindings for Tulip Indicators, a C library for technical analysis. Aims to be a simpler alternative to TA-Lib.

| Aspect | Details |
|--------|---------|
| **Language** | C core with Python bindings |
| **Indicators** | 100+ indicators |
| **License** | LGPL |
| **Performance** | Excellent (C implementation) |
| **Installation** | Requires C compiler; `pip install tulipy` may work directly |

**Strengths:**
- C performance without TA-Lib's installation complexity
- Clean Python API
- Lightweight library
- Often installs from pip without manual C library setup

**Limitations:**
- Smaller community than TA-Lib
- Fewer indicators than TA-Lib (no candlestick patterns)
- Less documentation
- Returns NumPy arrays (not DataFrame-integrated)
- Less common in production systems

**Verdict:** Consider as an alternative if TA-Lib installation fails. Otherwise, TA-Lib or pandas-ta are better choices.

---

### Technical Analysis Library Comparison

| Library | Indicators | Speed | Installation | API Design | Candlestick Patterns |
|---------|-----------|-------|-------------|------------|---------------------|
| TA-Lib | 200+ | Fastest | Difficult | Functional (arrays) | Yes (61 patterns) |
| pandas-ta | 130+ | Good | Easy | DataFrame extension | Limited |
| ta | 40+ | Good | Easy | Class-based | No |
| tulipy | 100+ | Fast | Moderate | Functional (arrays) | No |

**Recommended Stack:**
1. **Primary:** pandas-ta for development (easy, Pythonic)
2. **Production:** TA-Lib for speed-critical calculations
3. **Candlestick Patterns:** TA-Lib (the only comprehensive option)
4. **ML Feature Engineering:** ta library's `add_all_ta_features()` for quick feature generation

---

## 5. Screening and Scanning

A stock screener filters the entire market universe down to a manageable watchlist based on specific criteria. This is essential for swing trading, where you need to find the right stocks to trade each day.

### 5.1 Building a Stock Screener

**Architecture:**

```
[Universe] -> [Fundamental Filters] -> [Price/Volume Filters] -> [Technical Filters] -> [Watchlist]
  ~8000          ~2000                    ~500                     ~20-50              ~5-15
```

**Step 1: Define the Universe**
- S&P 500 (large caps, high liquidity)
- Russell 2000 (small caps, more volatility)
- Full US equities (~8000 tickers)
- Sector-specific (e.g., technology only)

**Step 2: Fundamental Filters (Optional)**
```python
# Minimum market cap (avoid penny stocks)
df = df[df['market_cap'] > 1_000_000_000]  # > $1B

# Minimum average volume (ensure liquidity)
df = df[df['avg_volume_30d'] > 500_000]  # > 500K shares/day

# Price range (avoid very cheap or expensive stocks)
df = df[(df['close'] > 5) & (df['close'] < 500)]
```

**Step 3: Price and Volume Filters**
```python
# Unusual volume (today's volume > 2x average)
df['volume_ratio'] = df['volume'] / df['avg_volume_30d']
high_volume = df[df['volume_ratio'] > 2.0]

# Price near support (within 3% of 50-day SMA)
df['sma_distance'] = abs(df['close'] - df['sma_50']) / df['sma_50']
near_support = df[df['sma_distance'] < 0.03]

# Consolidation breakout (range contraction then expansion)
df['atr_ratio'] = df['atr_5'] / df['atr_20']
breakouts = df[df['atr_ratio'] > 1.5]  # Recent ATR expanding

# Gap ups/downs
df['gap_pct'] = (df['open'] - df['prev_close']) / df['prev_close']
gaps = df[abs(df['gap_pct']) > 0.03]  # > 3% gap
```

**Step 4: Technical Indicator Filters**
```python
# RSI oversold (potential bounce)
oversold = df[df['rsi_14'] < 30]

# MACD bullish crossover
bullish_macd = df[(df['macd'] > df['macd_signal']) &
                   (df['macd_prev'] <= df['macd_signal_prev'])]

# Price above 200-day SMA (long-term uptrend)
uptrend = df[df['close'] > df['sma_200']]

# Bollinger Band squeeze (low volatility, pending breakout)
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
squeeze = df[df['bb_width'] < df['bb_width'].rolling(120).quantile(0.1)]
```

### 5.2 Scanner Implementation Pattern

```python
class SwingScanner:
    def __init__(self, data_provider):
        self.provider = data_provider
        self.filters = []

    def add_filter(self, name, condition_fn, description=""):
        self.filters.append({
            'name': name,
            'condition': condition_fn,
            'description': description
        })

    def scan(self, universe_df):
        results = universe_df.copy()
        filter_log = []

        for f in self.filters:
            before_count = len(results)
            results = results[f['condition'](results)]
            after_count = len(results)
            filter_log.append(f"{f['name']}: {before_count} -> {after_count}")

        return results, filter_log
```

### 5.3 Data Sources for Screening

| Source | Universe Size | Speed | Cost | Best For |
|--------|--------------|-------|------|----------|
| yfinance + S&P 500 list | 500 tickers | ~5 min | Free | Development |
| Polygon.io snapshot | Full US market | Seconds | $29/mo | Production |
| Alpaca snapshot API | Full US market | Seconds | Free | Production (Alpaca users) |
| Finnhub screener | Configurable | Seconds | Free-$50/mo | Quick screening |
| IEX Cloud | Full US market | Seconds | $9-$49/mo | Fundamental screening |

### 5.4 Pre-built Screening Services

- **Finviz:** Free web screener with export capability. Good for manual research but no API
- **TradingView Screener:** Comprehensive with Pine Script integration. Export requires paid plan
- **Stock Analysis (stockanalysis.com):** Good free screener with fundamental data
- **Barchart:** Advanced screening with options data

**Verdict:** Build a custom screener using Polygon.io or Alpaca snapshot data for maximum flexibility. Use Finviz for manual validation and idea generation. The custom approach lets you implement exactly the filters your strategy requires and integrate them into your automated pipeline.

---

## 6. Data Storage

Efficient data storage is crucial for a swing trading system. You need fast reads for backtesting, reliable writes for data collection, and efficient querying for screening.

### 6.1 Time-Series Databases

#### InfluxDB

**Overview:** A purpose-built time-series database designed for high-throughput writes and fast reads on time-based data.

| Aspect | Details |
|--------|---------|
| **License** | Open source (MIT) + commercial (InfluxDB Cloud) |
| **Language** | Go (server); Python, JavaScript, Go, etc. (clients) |
| **Query Language** | Flux (v2) or InfluxQL (v1, SQL-like) |
| **Best For** | Real-time data ingestion, monitoring, high-write workloads |

**Strengths:**
- Designed for time-series from the ground up
- Excellent write performance (millions of points/second)
- Built-in retention policies (auto-delete old data)
- Continuous queries for automatic downsampling
- Good for real-time dashboards (Grafana integration)
- Schema-less: flexible field and tag structure
- Cloud-hosted option available

**Limitations:**
- Flux query language has a learning curve
- Not ideal for complex joins or relational queries
- Cardinality limits (too many unique tag values degrades performance)
- Resource-hungry for large datasets
- InfluxDB v1 to v2 migration is non-trivial
- Overkill for end-of-day swing trading data

**Verdict:** Best suited if you are ingesting real-time tick or minute data continuously. Overkill for a swing trading system that primarily uses daily data. Consider if you plan to expand into intraday strategies.

---

#### TimescaleDB

**Overview:** A PostgreSQL extension that adds time-series capabilities. Combines the power of PostgreSQL with time-series optimizations.

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 (community) + Timescale License (cloud features) |
| **Language** | C (extension for PostgreSQL) |
| **Query Language** | Standard SQL |
| **Best For** | When you need both relational and time-series capabilities |

**Strengths:**
- Full SQL support (it is PostgreSQL)
- No new query language to learn
- Can store relational data alongside time-series (trade logs, portfolio, settings)
- Hypertables auto-partition by time for query performance
- Continuous aggregates (materialized views that auto-update)
- Compression: 10-20x compression on time-series data
- Rich ecosystem: any PostgreSQL tool works (pgAdmin, SQLAlchemy, etc.)
- Excellent for complex analytical queries (JOINs, window functions, CTEs)

**Limitations:**
- Requires PostgreSQL setup and management
- Write throughput lower than InfluxDB for pure time-series
- Compression adds complexity
- More resource-intensive than SQLite
- Requires database administration knowledge

**Verdict:** The best database choice if you want a single database for everything: market data, trade logs, portfolio tracking, and configuration. The SQL interface means no new query language, and the PostgreSQL ecosystem is mature.

---

### 6.2 Traditional Databases

#### SQLite

**Overview:** A serverless, embedded SQL database stored in a single file. Zero configuration required.

| Aspect | Details |
|--------|---------|
| **License** | Public domain |
| **Language** | C (built into Python standard library) |
| **Query Language** | SQL |
| **Best For** | Small to medium datasets, single-user applications |

**Strengths:**
- Zero setup: no server, no configuration, just a file
- Built into Python (`import sqlite3`)
- Perfect for development and single-user applications
- Supports millions of rows efficiently for daily OHLCV data
- Portable: copy the file to move the database
- No administration overhead
- Good enough for daily data of the entire US market

**Limitations:**
- Single-writer limitation (concurrent writes are serialized)
- No built-in time-series optimizations
- Not suitable for high-throughput real-time data ingestion
- Limited scalability beyond a few GB
- No built-in compression
- No user management or access control

**Performance Reference:** A SQLite database with 10 years of daily OHLCV data for 5,000 stocks (~12.5M rows) fits in ~1 GB and queries in milliseconds for single-stock lookups.

**Verdict:** The recommended starting point. Use SQLite until you have a specific reason to upgrade. For a daily-timeframe swing trading system, SQLite handles the data volume easily and requires zero infrastructure.

---

#### PostgreSQL

**Overview:** The most advanced open-source relational database. Robust, standards-compliant, and extensible.

| Aspect | Details |
|--------|---------|
| **License** | PostgreSQL License (permissive open source) |
| **Language** | C |
| **Query Language** | SQL (with extensions) |
| **Best For** | Multi-user applications, complex queries, production systems |

**Strengths:**
- Rock-solid reliability with ACID compliance
- Advanced SQL features: window functions, CTEs, JSON support, full-text search
- Extensible: TimescaleDB, PostGIS, pg_trgm, etc.
- Concurrent read/write support
- Excellent with SQLAlchemy and Django ORM
- Scales to terabytes
- Rich indexing options (B-tree, GIN, BRIN for time-series)

**Limitations:**
- Requires server setup and management
- More complex than SQLite
- Resource overhead for small datasets
- Needs regular maintenance (VACUUM, index maintenance)
- Docker simplifies setup but adds another dependency

**Verdict:** Upgrade to PostgreSQL when you need concurrent access, multi-user support, or want to add TimescaleDB for time-series features. For a production swing trading system, PostgreSQL (with or without TimescaleDB) is the enterprise-ready choice.

---

### 6.3 In-Memory and Cache: Redis

**Overview:** An in-memory data structure store used as a cache, message broker, and real-time data store.

| Aspect | Details |
|--------|---------|
| **License** | BSD (Redis 7+: RSALv2/SSPLv1 dual license) |
| **Language** | C (server); clients for every language |
| **Best For** | Caching, real-time data, pub/sub messaging, rate limiting |

**Use Cases for Swing Trading:**
- Cache frequently accessed data (latest prices, indicator values)
- Real-time price streaming buffer
- Pub/sub for distributing signals across system components
- Rate limit tracking for API calls
- Session storage for web dashboard
- Job queue for async tasks (data download, scan execution)

**Strengths:**
- Sub-millisecond read/write latency
- Rich data structures: strings, lists, sets, sorted sets, hashes, streams
- Pub/sub messaging built-in
- Redis Streams for event streaming
- Persistence options (RDB snapshots, AOF logging)
- Lua scripting for atomic operations

**Limitations:**
- Data must fit in memory
- Not suitable as primary data storage (persistence is secondary)
- Adds infrastructure complexity
- Requires separate server process

**Verdict:** Not essential for a basic swing trading system, but valuable as the system grows. Use Redis when you need caching, real-time data buffering, or inter-component messaging. Add it when you have performance or architecture needs that justify the complexity.

---

### 6.4 File-Based Storage: Parquet

**Overview:** Apache Parquet is a columnar storage format optimized for analytical workloads. The standard format for data science and quantitative finance.

| Aspect | Details |
|--------|---------|
| **License** | Apache 2.0 |
| **Language** | Supported by Python (PyArrow, fastparquet), Java, C++, Rust |
| **Best For** | Large analytical datasets, bulk reads, archival storage |

**Strengths:**
- Columnar format: extremely fast for analytical queries (read only the columns you need)
- Excellent compression: 5-10x smaller than CSV
- Type-safe: preserves data types (no CSV parsing issues)
- Partitioning support: partition by date, symbol for fast filtered reads
- Direct integration with Pandas: `df.to_parquet()` / `pd.read_parquet()`
- Works with big data tools (Spark, DuckDB, Polars)
- No server required; just files on disk
- DuckDB can query Parquet files directly with SQL

**Limitations:**
- Not suitable for frequent small updates (append-only is efficient; random updates are not)
- No built-in indexing (relies on partitioning and column pruning)
- Not a database: no transactions, no concurrent write safety
- Requires schema management for evolving data structures

**Recommended File Organization:**
```
data/
  market_data/
    daily/
      symbol=AAPL/
        2024.parquet
        2025.parquet
      symbol=GOOGL/
        2024.parquet
        2025.parquet
    intraday/
      date=2025-01-15/
        AAPL.parquet
        GOOGL.parquet
  indicators/
    rsi_14.parquet
    sma_20.parquet
  scans/
    2025-01-15_swing_candidates.parquet
  trades/
    trade_log.parquet
```

**Example:**
```python
import pandas as pd

# Write
df.to_parquet('data/market_data/daily/AAPL.parquet', engine='pyarrow')

# Read
df = pd.read_parquet('data/market_data/daily/AAPL.parquet')

# Read specific columns only (fast)
df = pd.read_parquet('data/market_data/daily/AAPL.parquet', columns=['close', 'volume'])

# Query with DuckDB (no loading into memory)
import duckdb
result = duckdb.sql("""
    SELECT * FROM 'data/market_data/daily/*.parquet'
    WHERE close > sma_50 AND volume > 1000000
    ORDER BY volume DESC
    LIMIT 20
""").df()
```

**Verdict:** Excellent complementary storage format. Use Parquet for bulk historical data (backtesting datasets, indicator precalculations). Combine with SQLite or PostgreSQL for transactional data (trade logs, portfolio state, settings).

---

### Data Storage Comparison and Recommendations

| Storage | Setup | Query Speed | Write Speed | Concurrent | Best For |
|---------|-------|-------------|-------------|------------|----------|
| SQLite | Zero | Good | Good | Single writer | Development, single-user |
| PostgreSQL | Moderate | Excellent | Excellent | Yes | Production, multi-user |
| TimescaleDB | Moderate | Excellent (TS) | Excellent | Yes | Time-series + relational |
| InfluxDB | Moderate | Good (TS) | Excellent | Yes | Real-time ingestion |
| Redis | Easy | Fastest | Fastest | Yes | Caching, real-time |
| Parquet | Zero | Excellent (bulk) | Good (batch) | Read-only | Bulk analysis, archival |

**Recommended Architecture:**

**Phase 1 (Development):**
- SQLite for trade logs, portfolio, configuration
- Parquet files for historical market data
- No Redis, no server databases

**Phase 2 (Production):**
- PostgreSQL for trade logs, portfolio, configuration
- Parquet files for historical market data (bulk analysis)
- Redis for caching and real-time price buffering (optional)

**Phase 3 (Scale):**
- PostgreSQL + TimescaleDB for all time-series and relational data
- Redis for caching, pub/sub, and job queuing
- Parquet for data lake / archival

---

## 7. Notification Systems

Notifications are essential for a swing trading system: you need to know when signals trigger, orders fill, or errors occur. The system should support multiple channels with configurable urgency levels.

### 7.1 Email Notifications

**Overview:** The most basic notification channel. Reliable and universally accessible.

**Implementation Options:**

| Method | Complexity | Cost | Reliability |
|--------|-----------|------|-------------|
| `smtplib` (Python built-in) | Low | Free (with Gmail/Outlook) | Good |
| SendGrid API | Low | Free tier: 100 emails/day | Excellent |
| Amazon SES | Low | $0.10/1000 emails | Excellent |
| Mailgun | Low | Free tier: 100 emails/day | Excellent |

**Example with smtplib (Gmail):**
```python
import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, to_email):
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = 'your_trading_bot@gmail.com'
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('your_trading_bot@gmail.com', 'app_password')
        server.send_message(msg)
```

**Best Practices:**
- Use App Passwords (not your main password) for Gmail
- Send HTML emails for formatted trade summaries
- Rate limit to avoid spam filters
- Include unsubscribe mechanism if sharing with others
- Use SendGrid/SES for production (better deliverability)

**Verdict:** Use for daily summaries, weekly reports, and non-urgent alerts. Not fast enough for time-sensitive signals (1-5 second delivery delay typical).

---

### 7.2 Telegram Bot

**Overview:** The most popular notification channel for trading bots. Fast, reliable, supports rich formatting, and accessible on all devices.

| Aspect | Details |
|--------|---------|
| **Cost** | Free |
| **Latency** | Sub-second delivery |
| **Setup** | Create bot via @BotFather, get token |
| **Python Library** | `python-telegram-bot` (async) or direct HTTP API |
| **Message Limits** | 30 messages/second (to different chats), 20 messages/min (to same chat) |

**Strengths:**
- Instant push notifications on mobile and desktop
- Rich formatting: Markdown, HTML, images, documents
- Inline keyboards for interactive responses (e.g., "Approve Trade" button)
- Group chats for team notifications
- Channel support for broadcast-style updates
- File sharing (charts, reports)
- Free and reliable

**Example:**
```python
import requests

TELEGRAM_TOKEN = "your_bot_token"
CHAT_ID = "your_chat_id"

def send_telegram(message, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    requests.post(url, json=payload)

# Trading signal notification
send_telegram(
    "<b>BUY Signal: AAPL</b>\n"
    "Price: $185.50\n"
    "RSI: 28.5 (oversold)\n"
    "Stop Loss: $180.00 (-2.96%)\n"
    "Target: $195.00 (+5.12%)\n"
    "R:R Ratio: 1:1.73"
)
```

**Advanced Features:**
- Send chart images with `sendPhoto`
- Interactive buttons with `InlineKeyboardMarkup`
- Bot commands for querying portfolio status, running manual scans
- Webhook mode for receiving commands from Telegram to your bot

**Verdict:** The recommended primary notification channel for trading signals. Fast, reliable, rich formatting, and accessible everywhere. Use the simple HTTP API for notifications; use `python-telegram-bot` library for interactive bot features.

---

### 7.3 Discord Bot

**Overview:** Similar to Telegram but with richer community features. Popular in trading communities and for team collaboration.

| Aspect | Details |
|--------|---------|
| **Cost** | Free |
| **Latency** | Sub-second delivery |
| **Setup** | Create application on Discord Developer Portal, add bot to server |
| **Python Library** | `discord.py` or simple webhook URL |
| **Message Limits** | 50 requests/second per bot |

**Strengths:**
- Rich embeds: formatted cards with colors, fields, thumbnails, footers
- Multiple channels for different alert types (signals, fills, errors)
- Thread support for discussing specific trades
- Role-based permissions for different alert levels
- Webhook integration (no bot needed for simple notifications)
- Active community platform for sharing strategies

**Webhook (Simple) Example:**
```python
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

def send_discord(content, embeds=None):
    payload = {"content": content}
    if embeds:
        payload["embeds"] = embeds
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

# Rich embed notification
send_discord("", embeds=[{
    "title": "BUY Signal: AAPL",
    "color": 0x00FF00,  # Green
    "fields": [
        {"name": "Price", "value": "$185.50", "inline": True},
        {"name": "RSI", "value": "28.5", "inline": True},
        {"name": "Stop Loss", "value": "$180.00 (-2.96%)", "inline": True},
        {"name": "Target", "value": "$195.00 (+5.12%)", "inline": True},
    ],
    "footer": {"text": "SwingTrader Bot | 2025-01-15 09:35:00 ET"}
}])
```

**Verdict:** Choose Discord over Telegram if you want a community-oriented platform with richer message formatting (embeds). Webhooks are the simplest path for one-way notifications. Use `discord.py` if you want interactive commands.

---

### 7.4 Webhooks (Generic)

**Overview:** HTTP POST requests to a URL when an event occurs. The universal integration pattern.

**Use Cases:**
- Trigger actions in external systems (IFTTT, Zapier, n8n)
- Send data to custom dashboards
- Integrate with any service that accepts HTTP requests
- Chain multiple notification systems together

**Implementation:**
```python
import requests

def send_webhook(url, payload, headers=None):
    """Generic webhook sender with retry logic."""
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            if attempt == 2:
                logging.error(f"Webhook failed after 3 attempts: {e}")
                return False
```

**Integration Targets:**
- **Slack:** Incoming Webhooks for team communication
- **IFTTT:** Trigger any IFTTT applet (SMS, smart home, etc.)
- **Zapier/n8n:** Connect to 1000+ services
- **PagerDuty:** For critical alerts (account protection, system failures)
- **Custom Dashboard:** POST data to your own web application

**Verdict:** Webhooks are the glue that connects your trading system to the rest of the world. Implement a generic webhook sender and use it to integrate with any service.

---

### 7.5 Notification Architecture

**Recommended Design:**

```python
class NotificationManager:
    """Route notifications to appropriate channels based on urgency and type."""

    URGENCY_LEVELS = {
        'critical': ['telegram', 'email', 'discord'],   # System errors, margin calls
        'high': ['telegram', 'discord'],                  # Trade signals, order fills
        'medium': ['discord'],                            # Scan results, daily summaries
        'low': ['email'],                                 # Weekly reports, performance stats
    }

    def __init__(self):
        self.channels = {}

    def register_channel(self, name, sender_fn):
        self.channels[name] = sender_fn

    def notify(self, message, urgency='medium', category='general'):
        channels = self.URGENCY_LEVELS.get(urgency, ['discord'])
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    self.channels[channel_name](message)
                except Exception as e:
                    logging.error(f"Failed to send via {channel_name}: {e}")
```

**Notification Types for Swing Trading:**

| Event | Urgency | Channels | Timing |
|-------|---------|----------|--------|
| New trade signal | High | Telegram + Discord | Real-time |
| Order filled | High | Telegram | Real-time |
| Stop loss hit | High | Telegram | Real-time |
| Daily scan results | Medium | Discord | End of day |
| Portfolio summary | Medium | Discord + Email | Daily morning |
| Weekly performance | Low | Email | Weekly |
| System error | Critical | All channels | Immediate |
| API rate limit warning | Medium | Discord | Real-time |
| Data quality issue | Medium | Discord | Real-time |

---

### Notification System Comparison

| Channel | Latency | Rich Format | Mobile | Setup | Cost | Best For |
|---------|---------|-------------|--------|-------|------|----------|
| Email | 1-5s | HTML | Yes | Easy | Free | Summaries, reports |
| Telegram | <1s | Markdown/HTML | Yes | Easy | Free | Real-time signals |
| Discord | <1s | Rich embeds | Yes | Easy | Free | Community, detailed alerts |
| Webhooks | <1s | JSON | Via integration | Easy | Free | System integration |
| Slack | <1s | Blocks/attachments | Yes | Easy | Free tier | Team collaboration |

**Recommended Setup:**
1. **Telegram Bot:** Primary channel for real-time trade signals and order fills
2. **Discord Server:** Secondary channel for scan results, daily summaries, and discussion
3. **Email (SendGrid):** Weekly performance reports and non-urgent summaries
4. **Webhooks:** Integration with custom dashboard and external services

---

## 8. Recommended Technology Stack

Based on the analysis above, here is the recommended technology stack for building a swing trading application in Python.

### Development Phase

| Component | Technology | Cost | Notes |
|-----------|-----------|------|-------|
| **Language** | Python 3.11+ | Free | asyncio support, performance improvements |
| **Market Data** | yfinance | Free | Prototyping and backtesting |
| **Technical Analysis** | pandas-ta | Free | Easy installation, Pythonic API |
| **Backtesting** | VectorBT (exploration) + Backtrader (validation) | Free | Speed + realism |
| **Data Storage** | SQLite + Parquet | Free | Zero infrastructure |
| **Notifications** | Telegram Bot | Free | Quick feedback loop |
| **Paper Trading** | Alpaca (paper mode) | Free | Realistic execution |

### Production Phase

| Component | Technology | Cost | Notes |
|-----------|-----------|------|-------|
| **Language** | Python 3.11+ | Free | Same as dev |
| **Market Data** | Polygon.io (Starter/Developer) | $29-$79/mo | Reliable, comprehensive |
| **Supplementary Data** | Finnhub (alt data) | Free-$50/mo | Insider transactions, sentiment |
| **Technical Analysis** | TA-Lib + pandas-ta | Free | Speed + convenience |
| **Data Storage** | PostgreSQL + Parquet | Free (self-hosted) | Robust, scalable |
| **Cache** | Redis | Free (self-hosted) | Optional, add when needed |
| **Broker** | Alpaca (live) | Free | Commission-free US equities |
| **Notifications** | Telegram + Discord + Email | Free | Multi-channel |
| **Scheduling** | APScheduler or cron | Free | Daily scans, data collection |
| **Monitoring** | Grafana + Prometheus | Free | System health dashboards |

### Cost Summary

| Phase | Monthly Cost |
|-------|-------------|
| Development | $0 |
| Production (minimal) | $29/mo (Polygon.io Starter) |
| Production (full) | $79-$130/mo (Polygon.io Developer + Finnhub) |

### Architecture Overview

```
[Data Collection]     [Analysis Engine]      [Execution]          [Monitoring]

Polygon.io ──┐       ┌── Scanner ──────┐    ┌── Alpaca ───┐     ┌── Telegram
Finnhub ─────┤       │   (daily scan)  │    │   (orders)  │     │   (signals)
yfinance ────┘       │                 │    │             │     │
     │               ├── Backtester    │    ├── Paper     │     ├── Discord
     ▼               │   (validation)  │    │   Trading   │     │   (summaries)
[PostgreSQL]────────►│                 ├───►│             ├────►│
[Parquet] ──────────►├── Indicators    │    ├── Risk      │     ├── Email
                     │   (TA-Lib)      │    │   Manager   │     │   (reports)
                     │                 │    │             │     │
                     └── ML Models     │    └── Portfolio  │     └── Dashboard
                         (optional)    │        Tracker    │         (Grafana)
                                       │                   │
                     [Redis Cache] ◄───┘                   │
                                                           │
                     [APScheduler] ── cron triggers ───────┘
```

---

## 9. Key Takeaways

1. **Start Free, Scale Paid:** Use yfinance and Alpaca paper trading during development. Add Polygon.io when you go to production. The total cost of a production swing trading system can be under $100/month.

2. **Alpaca is the Best Broker API for Beginners:** Zero commission, excellent developer experience, seamless paper-to-live transition. Only upgrade to IBKR if you need options, futures, or international markets.

3. **pandas-ta Over TA-Lib for Development:** The installation ease and Pandas integration outweigh the speed difference for daily-timeframe swing trading. Use TA-Lib when speed matters (large parameter optimization).

4. **SQLite + Parquet is Enough to Start:** Do not over-engineer the data layer. SQLite handles trade logs and configuration; Parquet handles bulk market data. Upgrade to PostgreSQL when you need concurrent access.

5. **Telegram for Real-Time, Email for Summaries:** Two notification channels cover 90% of needs. Add Discord if you want community features or richer formatting.

6. **Build a Custom Screener:** No off-the-shelf screener will match your specific strategy criteria. Build a modular scanner using Polygon.io or Alpaca snapshot data that runs daily.

7. **Backtest in Layers:** Use VectorBT for fast exploration, Backtrader for realistic validation, and Alpaca paper trading for live market validation before committing real capital.

8. **API Rate Limits are Real:** Every data provider has rate limits. Build rate limiting and caching into your system from the start. A Redis cache for frequently accessed data prevents unnecessary API calls and keeps you within limits.
