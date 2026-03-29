# Data Sources — 5-Min OHLCV for Small-Cap / OTC Stocks

## Why 5-Minute Data Is Hard to Get

Most free data APIs provide daily OHLCV only. Intraday data (1-min, 5-min) is
expensive because exchanges charge redistribution fees. For small-cap and OTC
stocks specifically, coverage is even spottier — many providers focus on large-cap.

Think of it like satellite imagery: daily data is Google Maps (free, everyone has it),
while 5-min data is high-res satellite (expensive, restricted access).

## Provider Comparison

### Polygon.io
```
COVERAGE:    All US exchanges + OTC (best small-cap coverage)
GRANULARITY: 1-min, 5-min, hourly, daily
HISTORY:     5+ years of intraday for most tickers
COST:        Free tier: 5 API calls/min, 2 years history, delayed
             Starter ($29/mo): real-time, unlimited calls
             Developer ($79/mo): unlimited everything + websockets
LATENCY:     Real-time with paid plan, 15-min delay on free
API EXAMPLE:
  GET https://api.polygon.io/v2/aggs/ticker/MULN/range/5/minute/2024-01-15/2024-01-15
  ?apiKey=YOUR_KEY
  Returns: [{o, h, l, c, v, t, n}, ...]

PROS: Best coverage for sub-$10 stocks, reliable history
CONS: Free tier is very limited, OTC data may have gaps
VERDICT: ★★★★★ Best choice for this strategy
```

### Alpaca Markets
```
COVERAGE:    US equities (NYSE, NASDAQ, AMEX) — NO OTC
GRANULARITY: 1-min, 5-min, 15-min, 1-hour, daily
HISTORY:     5+ years with paid data plan
COST:        Free tier: IEX data only (limited)
             Algo Trader Plus ($99/mo): full SIP data
             Or included with funded brokerage account
LATENCY:     Real-time with SIP subscription
API EXAMPLE:
  GET https://data.alpaca.markets/v2/stocks/MULN/bars
  ?timeframe=5Min&start=2024-01-15&end=2024-01-15
  Headers: APCA-API-KEY-ID, APCA-API-SECRET-KEY

PROS: Free with brokerage account, clean API, good docs
CONS: No OTC coverage (misses many parabolic stocks), IEX-only on free tier
VERDICT: ★★★☆☆ Good if you already use Alpaca for trading
```

### FirstRate Data
```
COVERAGE:    US equities including delisted and OTC
GRANULARITY: 1-min, tick-level available
HISTORY:     20+ years (best historical depth)
COST:        $20-50 per dataset (one-time purchase)
             Full US intraday: ~$200
LATENCY:     Not real-time — bulk historical data only
FORMAT:      CSV files, downloadable

PROS: Includes delisted stocks (critical for backtesting survivorship bias),
      deepest history, clean data
CONS: Not real-time, bulk purchase model, manual download
VERDICT: ★★★★☆ Best for backtesting, not for live trading
```

### Yahoo Finance (yfinance)
```
COVERAGE:    Most US equities, limited OTC
GRANULARITY: 1-min (7 days), 5-min (60 days), daily (unlimited)
HISTORY:     Very limited for intraday — max 60 days for 5-min
COST:        Free (unofficial API, may break)
API EXAMPLE:
  import yfinance as yf
  data = yf.download("MULN", interval="5m", period="5d")

PROS: Free, easy to use, no API key needed
CONS: Only 60 days of 5-min data, unreliable for OTC,
      unofficial API that breaks periodically
VERDICT: ★★☆☆☆ OK for quick checks, not for systematic use
```

### Interactive Brokers (TWS API)
```
COVERAGE:    Everything IBKR trades (very broad)
GRANULARITY: 1-sec to daily
HISTORY:     1 year of intraday via API, more via data subscriptions
COST:        Free with IBKR account, market data subscriptions extra ($4.50-10/mo)
LATENCY:     Real-time
API:         Via ib_async (Python) or native TWS API

PROS: Real-time + historical, covers everything, integrated with broker
CONS: Requires IBKR account, API is complex, rate-limited (60 req/10min),
      pacing violations if you request too much historical data
VERDICT: ★★★★☆ Great for live trading, painful for bulk backtesting
```

## Recommended Setup by Use Case

### For Backtesting (historical analysis)
```
PRIMARY:   FirstRate Data — buy the 5-min US equity dataset
           Includes delisted stocks (prevents survivorship bias)
BACKUP:    Polygon Developer plan — API access to 5+ years
BUDGET:    ~$200 one-time (FirstRate) or $79/mo (Polygon)
```

### For Paper Trading (real-time, no money at risk)
```
PRIMARY:   Alpaca free tier + paper trading account
           Limited to IEX data but sufficient for paper trading
BACKUP:    Polygon Starter ($29/mo) for broader coverage
BUDGET:    $0-29/mo
```

### For Live Trading
```
PRIMARY:   Polygon Developer ($79/mo) for scanning + data
           + Alpaca or IBKR for order execution
ALTERNATIVE: IBKR with market data subscription
             Use TWS API for both data and execution
BUDGET:    $79-100/mo
```

## Data Quality Considerations

### Survivorship Bias
```
PROBLEM:  If your data provider only has currently-listed stocks,
          you miss all the stocks that went to zero — which are
          EXACTLY the stocks this strategy trades.

EXAMPLE:  MULN went parabolic in 2022, crashed, eventually delisted.
          A backtest without MULN data would miss this trade entirely.

FIX:      Use FirstRate Data (includes delisted) for backtesting.
          For live trading, survivorship bias isn't relevant —
          you're trading what's listed today.
```

### Adjusted vs Unadjusted Prices
```
PROBLEM:  Some providers adjust historical prices for splits.
          A stock that was $8 pre-split (2:1) shows as $4 in
          adjusted data. Your $0.50-$10 price filter may
          include/exclude the wrong stocks.

FIX:      Use UNADJUSTED prices for the universe filter.
          Use ADJUSTED prices for return calculations.
          Polygon and FirstRate both offer unadjusted data.
```

### Trading Halt Gaps in 5-Min Data
```
PROBLEM:  When a stock is halted (LULD halt, T12 regulatory halt),
          the 5-min bar spanning the halt contains the pre-halt
          and post-halt price. This creates an artificially large
          candle that can trigger false capitulation signals.

FIX:      Check NYSE halt data for each ticker on each day.
          If a 5-min bar spans a halt, either:
          a) Split the bar at the halt boundary (if you have tick data)
          b) Skip the bar entirely (simpler, recommended)

SOURCE:   NYSE halt data: ftp.nyxdata.com/NYSEGroupSSRCircuitBreakers/
          Also available via Polygon reference data API.
```

## API Rate Limits and Batching

```
POLYGON:
  Free: 5 calls/min
  Starter: unlimited calls, 5 concurrent connections
  Strategy: batch requests by date range, not per-bar

ALPACA:
  200 calls/min for data API
  Strategy: use multi-symbol endpoint to fetch several tickers at once

IBKR:
  60 historical data requests per 10 minutes (hard limit)
  6 concurrent market data lines on free tier
  Strategy: queue requests, respect pacing, cache aggressively

GENERAL TIPS:
  - Cache all historical data locally (SQLite or Parquet files)
  - Only fetch new data incrementally (last bar forward)
  - For backtesting: download once, query locally forever
  - For live: stream via websocket, don't poll REST
```
