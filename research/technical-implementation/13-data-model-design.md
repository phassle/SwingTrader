# 13 - Data Model Design

> Research date: 2026-03-08
> Goal: Define the complete data model for SwingTrader — all containers, document schemas, partition strategies, and SQLite equivalents. Designed for all three phases from day one, built incrementally starting with Phase 1.
> Prerequisites: [11-azure-cosmos-db-evaluation.md](11-azure-cosmos-db-evaluation.md), [23-setup-quality-scoring.md](../strategy-and-theory/23-setup-quality-scoring.md), [17-trading-journal-framework.md](../strategy-and-theory/17-trading-journal-framework.md)

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Cosmos DB Concepts (Brief)](#2-cosmos-db-concepts-brief)
3. [Container: stocks (Reference Data)](#3-container-stocks-reference-data)
4. [Container: daily_prices (OHLCV Data)](#4-container-daily_prices-ohlcv-data)
5. [Container: indicators (Calculated Indicators)](#5-container-indicators-calculated-indicators)
6. [Container: signals (Buy/Sell Signals)](#6-container-signals-buysell-signals)
7. [Container: scan_runs (Pipeline Metadata)](#7-container-scan_runs-pipeline-metadata)
8. [Phase 2 Containers (Design Now, Build Later)](#8-phase-2-containers-design-now-build-later)
9. [Phase 3 Considerations](#9-phase-3-considerations)
10. [SQLite Equivalent Schema](#10-sqlite-equivalent-schema)
11. [Data Volume Estimates](#11-data-volume-estimates)
12. [Partition Key Summary](#12-partition-key-summary)
13. [Indexing Strategy](#13-indexing-strategy)
14. [Migration and Versioning](#14-migration-and-versioning)

---

## 1. Design Principles

### Design for all 3 phases now, build Phase 1 first

The data model must support the full application lifecycle from the start. Retrofitting a data model onto a NoSQL database is painful — unlike relational databases, you cannot just add a JOIN later. The cost of including Phase 2 and Phase 3 containers in the schema design is zero (empty containers cost nothing in Cosmos DB serverless). The cost of redesigning partition keys and document structures later is high.

**Phase 1 (MVP):** Daily scanner — fetch OHLCV data for ~100 OMX Large Cap stocks, calculate indicators, run strategies, generate buy signals, send via Telegram. Store everything for historical lookup.

**Phase 2:** Trade journal — log actual trades, track P&L, compare signals vs results. Builds on the journal framework defined in `17-trading-journal-framework.md`.

**Phase 3:** Dashboard — web UI showing charts, performance, strategy comparison, portfolio overview.

### NoSQL document model (Cosmos DB)

- **No JOINs.** Every query hits exactly one container. If a document needs data from another container, denormalize it (copy the relevant fields into the document).
- **Denormalize where practical.** A signal document should include a snapshot of the indicators that triggered it, not a reference to the indicators container. This makes each signal self-contained and readable without cross-referencing.
- **Keep documents reasonably sized.** Cosmos DB has a 2 MB document limit, but documents should stay well under that. Avoid huge nested arrays. A portfolio snapshot with 10 positions is fine. A document with 10,000 historical prices is not.

### Data format conventions

- **Dates:** ISO 8601 format. Date-only fields use `YYYY-MM-DD`. Timestamps use `YYYY-MM-DDTHH:MM:SSZ`.
- **Prices:** Local currency (SEK for Swedish stocks). No currency conversion. The `currency` field in the stocks container records which currency applies.
- **Timestamps:** All timestamps in UTC. The `Z` suffix makes this explicit. No local time zones in stored data. Convert to local time only at the presentation layer.
- **IDs:** Composite keys using `ticker_date` or `ticker_date_strategy` patterns. This makes IDs human-readable and deterministic (the same input always produces the same ID, which makes upserts natural).

### Repository pattern abstraction

The data access layer uses a repository pattern (see `11-azure-cosmos-db-evaluation.md`, section 10-11) so that swapping between Cosmos DB and SQLite requires changing only the repository implementation, not the business logic. Every container maps to one repository interface.

---

## 2. Cosmos DB Concepts (Brief)

For full details, see `11-azure-cosmos-db-evaluation.md`. This section covers only what is needed to understand the data model decisions.

### Hierarchy

```
Azure Cosmos DB Account
  └── Database (e.g., "swingtrader")
        ├── Container: stocks
        ├── Container: daily_prices
        ├── Container: indicators
        ├── Container: signals
        ├── Container: scan_runs
        ├── Container: trades          (Phase 2)
        └── Container: portfolio_snapshots  (Phase 2)
```

### Partition keys

Every container has a **partition key** — a field in each document that determines which logical partition the document belongs to. This is the single most important design decision in Cosmos DB.

- **Queries within a single partition** are cheap and fast (1-5 RU for a simple query).
- **Cross-partition queries** (queries that do not filter on the partition key) fan out to every partition, which is slower and costs more RU.
- **The partition key cannot be changed** after the container is created (without recreating the container and migrating data).

**Rule of thumb:** Choose a partition key that matches the most common query pattern. If you almost always query "get all prices for VOLV-B.ST," then `/ticker` is the right partition key for prices. If you almost always query "get all signals from today," then `/date` is the right partition key for signals.

### Document structure

Each document is a JSON object with a required `id` field (unique within a partition) and the partition key field. Cosmos DB adds system properties (`_rid`, `_self`, `_etag`, `_ts`) automatically. The `id` field combined with the partition key must be unique across the container.

### RU cost reference

At this project's scale (see `11-azure-cosmos-db-evaluation.md`, section 2), every operation costs fractions of a penny. The partition key strategy matters more for query correctness and simplicity than for cost optimization.

---

## 3. Container: stocks (Reference Data)

**Purpose:** Master list of all tracked stocks. This is reference data that changes rarely — stocks are added or removed from the scan universe, but the data itself is mostly static.

**Build phase:** Phase 1.

### Document schema

```json
{
  "id": "VOLV-B.ST",
  "ticker": "VOLV-B.ST",
  "name": "Volvo Group B",
  "isin": "SE0000115446",
  "sector": "Industrials",
  "market_cap_tier": "large_cap",
  "exchange": "OMX Stockholm",
  "currency": "SEK",
  "is_active": true,
  "added_date": "2026-03-08",
  "notes": "",
  "schema_version": 1
}
```

### Field descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Same as ticker. Cosmos DB requires an `id` field. |
| `ticker` | string | Yes | Yahoo Finance ticker symbol (e.g., `VOLV-B.ST`). |
| `name` | string | Yes | Human-readable company name. |
| `isin` | string | No | International Securities Identification Number. Useful for cross-referencing with brokers. |
| `sector` | string | Yes | GICS sector classification. |
| `market_cap_tier` | string | Yes | One of: `large_cap`, `mid_cap`, `small_cap`. |
| `exchange` | string | Yes | Exchange name. |
| `currency` | string | Yes | Trading currency (always `SEK` for OMX stocks). |
| `is_active` | boolean | Yes | Whether the stock is currently in the scan universe. Set to `false` rather than deleting to preserve history. |
| `added_date` | string | Yes | ISO 8601 date when the stock was added to the universe. |
| `notes` | string | No | Free-text notes (e.g., "Delisted 2026-06-01"). |
| `schema_version` | integer | Yes | Document version for migration support. |

### Partition key: `/ticker`

With ~100 documents that are read infrequently, partition key choice barely matters. Using `/ticker` is natural because the most common operation is "look up stock by ticker." Listing all active stocks is a cross-partition query, but with only ~100 documents the fan-out cost is negligible.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Get stock by ticker | `WHERE c.ticker = 'VOLV-B.ST'` | Single partition |
| List all active stocks | `WHERE c.is_active = true` | Cross-partition (fine at this scale) |
| List stocks by sector | `WHERE c.sector = 'Industrials'` | Cross-partition (fine at this scale) |

---

## 4. Container: daily_prices (OHLCV Data)

**Purpose:** Historical daily price data. This is the foundation — every indicator, signal, and strategy decision is derived from this data. Raw price data is sacred and should never be modified after insertion (except to correct data quality issues).

**Build phase:** Phase 1.

### Document schema

```json
{
  "id": "VOLV-B.ST_2026-03-07",
  "ticker": "VOLV-B.ST",
  "date": "2026-03-07",
  "open": 245.50,
  "high": 248.30,
  "low": 244.10,
  "close": 247.80,
  "adjusted_close": 247.80,
  "volume": 3450000,
  "source": "yfinance",
  "fetched_at": "2026-03-07T17:15:00Z",
  "schema_version": 1
}
```

### Field descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Composite key: `{ticker}_{date}`. Deterministic — inserting the same ticker+date overwrites cleanly. |
| `ticker` | string | Yes | Yahoo Finance ticker symbol. |
| `date` | string | Yes | Trading date in ISO 8601 format. |
| `open` | number | Yes | Opening price in SEK. |
| `high` | number | Yes | Highest price during the session in SEK. |
| `low` | number | Yes | Lowest price during the session in SEK. |
| `close` | number | Yes | Closing price in SEK. |
| `adjusted_close` | number | Yes | Split- and dividend-adjusted closing price. For most Swedish stocks, this equals `close` unless there was a recent corporate action. |
| `volume` | integer | Yes | Number of shares traded. |
| `source` | string | Yes | Data provider (e.g., `yfinance`, `nasdaq_nordic`). Useful if data sources are swapped later. |
| `fetched_at` | string | Yes | UTC timestamp when the data was retrieved. |
| `schema_version` | integer | Yes | Document version. |

### Partition key: `/ticker`

This is a clear choice. The dominant access pattern is "get price history for a specific stock" — pulling 50-200 days of prices for one ticker to calculate indicators or draw a chart. This query stays within a single partition.

The secondary pattern — "get latest price for all stocks" — is a cross-partition query, but it runs once per scan (not in a loop) and touches only the latest document per partition. At 100 partitions, this costs roughly 100-200 RU, which is fine.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Price history for one stock | `WHERE c.ticker = 'VOLV-B.ST' AND c.date >= '2026-01-01' ORDER BY c.date` | Single partition |
| Latest price for one stock | `WHERE c.ticker = 'VOLV-B.ST' ORDER BY c.date DESC OFFSET 0 LIMIT 1` | Single partition |
| Latest prices for all stocks | `WHERE c.date = '2026-03-07'` | Cross-partition (acceptable) |

### Size estimate

100 stocks x 252 trading days x 3 years = ~75,600 documents. At roughly 200 bytes per document (after compression), this is approximately 15 MB. Well within any storage limit.

### Why `adjusted_close` matters

When a stock splits or pays a dividend, historical prices need adjustment to remain comparable. Yahoo Finance provides adjusted close prices automatically. Storing both `close` (the actual price traded that day) and `adjusted_close` (the retroactively adjusted price) preserves both perspectives. Indicator calculations should use `adjusted_close` for accuracy.

---

## 5. Container: indicators (Calculated Indicators)

**Purpose:** Pre-calculated technical indicators per stock per day. Stored separately from prices so they can be recalculated without touching raw data.

**Build phase:** Phase 1.

### Document schema

```json
{
  "id": "VOLV-B.ST_2026-03-07",
  "ticker": "VOLV-B.ST",
  "date": "2026-03-07",
  "rsi_14": 42.3,
  "macd": 1.25,
  "macd_signal": 0.89,
  "macd_histogram": 0.36,
  "bb_upper": 252.10,
  "bb_middle": 246.50,
  "bb_lower": 240.90,
  "sma_20": 246.50,
  "sma_50": 243.20,
  "sma_200": 238.90,
  "ema_9": 247.10,
  "ema_21": 246.80,
  "atr_14": 4.20,
  "adx_14": 28.5,
  "obv": 15234000,
  "volume_sma_20": 3200000,
  "volume_ratio": 1.08,
  "calculated_at": "2026-03-07T17:20:00Z",
  "schema_version": 1
}
```

### Field descriptions

| Field | Type | Description | Reference |
|-------|------|-------------|-----------|
| `rsi_14` | number | Relative Strength Index (14-period) | `02-technical-indicators.md` |
| `macd` | number | MACD line (12, 26) | `02-technical-indicators.md` |
| `macd_signal` | number | MACD signal line (9-period EMA of MACD) | `02-technical-indicators.md` |
| `macd_histogram` | number | MACD minus signal | `02-technical-indicators.md` |
| `bb_upper` | number | Upper Bollinger Band (20, 2) | `02-technical-indicators.md` |
| `bb_middle` | number | Middle Bollinger Band (20-period SMA) | `02-technical-indicators.md` |
| `bb_lower` | number | Lower Bollinger Band (20, 2) | `02-technical-indicators.md` |
| `sma_20` | number | 20-day Simple Moving Average | `02-technical-indicators.md` |
| `sma_50` | number | 50-day Simple Moving Average | `02-technical-indicators.md` |
| `sma_200` | number | 200-day Simple Moving Average | `02-technical-indicators.md` |
| `ema_9` | number | 9-day Exponential Moving Average | `02-technical-indicators.md` |
| `ema_21` | number | 21-day Exponential Moving Average | `02-technical-indicators.md` |
| `atr_14` | number | Average True Range (14-period) | `05-risk-management.md` |
| `adx_14` | number | Average Directional Index (14-period) | `02-technical-indicators.md` |
| `obv` | number | On-Balance Volume | `02-technical-indicators.md` |
| `volume_sma_20` | number | 20-day volume moving average | Derived |
| `volume_ratio` | number | Today's volume divided by `volume_sma_20` | Derived |
| `calculated_at` | string | UTC timestamp when indicators were computed | System |

### Partition key: `/ticker`

Same rationale as daily_prices. The primary access pattern is "get indicator history for one stock" for charting or analysis. The scanner's "get latest indicators for all stocks" is a cross-partition query that runs once daily and is acceptable at this scale.

### Why separate from daily_prices?

**Trade-off: embedded vs. separate container.**

| Approach | Pros | Cons |
|----------|------|------|
| **Embed indicators in daily_prices** | One query gets everything. Simpler code for chart rendering. Fewer containers to manage. | Recalculating indicators means rewriting price documents. Tighter coupling — changing indicator parameters requires touching "sacred" price data. Larger documents even when you only need prices. |
| **Separate indicators container** | Clean separation of raw data (prices) vs. derived data (indicators). Can recalculate indicators without touching prices. Can add or remove indicators without document migration. Each document stays small and focused. | Two queries needed to get prices + indicators for a chart. Slightly more complex data pipeline. |

**Recommendation: Separate container.** The separation is worth it. Prices are immutable facts. Indicators are derived computations that may need recalculation when parameters change, new indicators are added, or bugs are found. Keeping them separate means recalculation is a clean "drop and rebuild" operation on the indicators container without any risk to the price data.

For the Phase 3 dashboard, the chart rendering component can query both containers in parallel and merge the results client-side. This is a one-time implementation cost that pays for itself in operational simplicity.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Indicator history for one stock | `WHERE c.ticker = 'VOLV-B.ST' AND c.date >= '2026-01-01'` | Single partition |
| Latest indicators for one stock | `WHERE c.ticker = 'VOLV-B.ST' ORDER BY c.date DESC OFFSET 0 LIMIT 1` | Single partition |
| Latest indicators for all stocks (scanner) | `WHERE c.date = '2026-03-07'` | Cross-partition (acceptable) |

### Adding new indicators

One of the advantages of a schemaless document database: adding a new indicator is as simple as including a new field in the next calculation run. Old documents will not have the field (which queries should handle gracefully), and new documents will include it. No schema migration needed.

If backward-filling is required (calculating a new indicator for historical dates), run the indicator calculation pipeline against historical price data and upsert the results.

---

## 6. Container: signals (Buy/Sell Signals)

**Purpose:** Every signal generated by the scanner, with full scoring breakdown. This is the core output of Phase 1 — what gets sent to Telegram — and the foundation for Phase 2 trade tracking and Phase 3 performance analysis.

**Build phase:** Phase 1.

### Document schema

```json
{
  "id": "sig_VOLV-B.ST_2026-03-07_mean_reversion",
  "ticker": "VOLV-B.ST",
  "date": "2026-03-07",
  "strategy": "mean_reversion",
  "direction": "buy",
  "score_total": 17,
  "scores": {
    "trend_alignment": 3,
    "level_quality": 3,
    "catalyst_quality": 1,
    "volume_participation": 1,
    "liquidity_execution": 2,
    "market_sector_alignment": 3,
    "risk_reward": 2,
    "timing_confirmation": 2
  },
  "score_grade": "A",
  "entry_price": 247.80,
  "stop_price": 240.90,
  "target_price": 258.50,
  "risk_reward_ratio": 1.55,
  "reasoning": "RSI(14) at 28.3 (oversold) + price at lower Bollinger Band + MACD histogram turning positive",
  "indicators_snapshot": {
    "rsi_14": 28.3,
    "macd_histogram": 0.36,
    "bb_lower": 240.90,
    "close": 247.80,
    "volume_ratio": 1.15,
    "sma_200": 238.90,
    "atr_14": 4.20
  },
  "regime": "trending_orderly",
  "disqualified": false,
  "disqualification_reason": null,
  "sent_to_telegram": true,
  "telegram_sent_at": "2026-03-07T17:26:00Z",
  "created_at": "2026-03-07T17:25:00Z",
  "schema_version": 1
}
```

### Scoring fields

The `scores` object maps directly to the 8-category scoring model defined in `23-setup-quality-scoring.md`:

| Score field | Max | Source reference |
|-------------|-----|-----------------|
| `trend_alignment` | 3 | Category 1: Trend alignment |
| `level_quality` | 3 | Category 2: Level quality |
| `catalyst_quality` | 3 | Category 3: Catalyst quality |
| `volume_participation` | 2 | Category 4: Volume and participation |
| `liquidity_execution` | 2 | Category 5: Liquidity and execution quality |
| `market_sector_alignment` | 3 | Category 6: Market and sector alignment |
| `risk_reward` | 2 | Category 7: Risk/reward quality |
| `timing_confirmation` | 2 | Category 8: Timing and confirmation |
| **Total possible** | **20** | |

The `score_grade` field maps the total to the grading bands from `23-setup-quality-scoring.md`:

- `A`: 17-20 (highest conviction)
- `B`: 13-16 (tradable if conditions are met)
- `C`: 9-12 (usually pass)
- `F`: below 9 (no-trade by default)

### Hard disqualifiers

The `disqualified` and `disqualification_reason` fields implement the hard disqualifier logic from `23-setup-quality-scoring.md`, section 5. Even if a signal scores well, it can be blocked by conditions such as:

- Earnings event inside the forbidden holding window
- Spread too wide for intended size
- Stop distance too large for allowed risk
- Market regime does not permit that strategy (see `25-regime-to-strategy-mapping.md`)
- Liquidity too low for reliable exit

Disqualified signals are still stored (for analysis of "what would have happened") but not sent to Telegram.

### Indicators snapshot (denormalization)

The `indicators_snapshot` object is a deliberate denormalization. It copies the key indicator values that influenced this signal from the indicators container. This makes each signal document self-contained: when reviewing a signal weeks later, or when the Phase 3 dashboard displays signal details, the relevant indicator values are right there in the document. No cross-container query needed.

Only include indicators relevant to the signal's strategy. A mean reversion signal includes RSI, Bollinger Bands, and MACD. A momentum breakout signal would include different indicators. The snapshot does not need to duplicate every indicator — just the ones that matter for understanding why this signal fired.

### Partition key: `/date`

**This is the key design decision for the signals container.** Two viable options exist:

| Partition key | Best for | Weakness |
|---------------|----------|----------|
| `/date` | "Show me all signals from today" — the daily Telegram summary, the daily dashboard view. | "Show me all signals for VOLV-B ever" requires a cross-partition query. |
| `/ticker` | "Show me all signals for VOLV-B" — stock-specific analysis. | "Show me all signals from today" requires a cross-partition query. |

**Recommendation: `/date`.**

Rationale:
1. **Phase 1 primary access pattern:** The scanner generates signals and immediately queries "what signals did we generate today?" to compose the Telegram message. This is the most frequent operation and should be cheap.
2. **Phase 2 access pattern:** When logging a trade, the user looks up "what signal triggered this trade?" — this is a point read by `id`, which is cheap regardless of partition key.
3. **Phase 3 dashboard:** The most common dashboard view is "today's signals" or "this week's signals." Date-based partitioning makes these queries fast.
4. **Stock-specific signal history** (e.g., "show me all signals for VOLV-B in 2026") is a less frequent, analytical query. A cross-partition query here is acceptable because it runs infrequently and the total number of signals is small (thousands, not millions).

With date-based partitioning and roughly 3-10 signals per day, each partition contains a small number of documents — efficient to query and well within Cosmos DB's partition size limits.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Today's signals | `WHERE c.date = '2026-03-07'` | Single partition |
| Signal by ID | Point read by `id` + partition key | Single partition |
| Signals for a stock | `WHERE c.ticker = 'VOLV-B.ST'` | Cross-partition (acceptable) |
| Signals by strategy | `WHERE c.strategy = 'mean_reversion' AND c.date >= '2026-01-01'` | Cross-partition (acceptable) |
| Unqualified signals only | `WHERE c.date = '2026-03-07' AND c.disqualified = false` | Single partition |

---

## 7. Container: scan_runs (Pipeline Metadata)

**Purpose:** Track each daily scan run for monitoring and debugging. If signals look wrong or are missing, the first place to look is the scan run record. This container also supports Phase 3's operational monitoring dashboard.

**Build phase:** Phase 1.

### Document schema

```json
{
  "id": "run_2026-03-07",
  "date": "2026-03-07",
  "started_at": "2026-03-07T17:15:00Z",
  "completed_at": "2026-03-07T17:19:34Z",
  "duration_seconds": 274,
  "stocks_scanned": 98,
  "stocks_failed": 2,
  "failed_tickers": ["KINV-B.ST", "SAND.ST"],
  "failure_reasons": {
    "KINV-B.ST": "yfinance timeout after 30s",
    "SAND.ST": "insufficient data: only 45 trading days available, need 200 for SMA_200"
  },
  "signals_generated": 5,
  "signals_qualified": 3,
  "signals_disqualified": 2,
  "signals_sent": 3,
  "regime_snapshot": {
    "market_regime": "trending_orderly",
    "volatility_regime": "moderate",
    "omxs30_trend": "bullish",
    "omxs30_rsi": 55.2,
    "omxs30_close": 2345.67
  },
  "strategies_run": ["mean_reversion", "momentum_breakout", "trend_pullback"],
  "status": "completed",
  "error_message": null,
  "schema_version": 1
}
```

### Field descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `run_{date}`. One scan per day. If re-runs are needed, overwrite the same document. |
| `date` | string | The trading date being scanned. |
| `started_at` / `completed_at` | string | UTC timestamps for the scan pipeline. |
| `duration_seconds` | number | Wall clock time for the full pipeline. |
| `stocks_scanned` | integer | Number of stocks successfully processed. |
| `stocks_failed` | integer | Number of stocks that failed during processing. |
| `failed_tickers` | array | List of tickers that failed. |
| `failure_reasons` | object | Map of ticker to failure description. |
| `signals_generated` | integer | Total signals produced (before disqualification). |
| `signals_qualified` | integer | Signals that passed hard disqualifier checks. |
| `signals_disqualified` | integer | Signals blocked by hard disqualifiers. |
| `signals_sent` | integer | Signals actually sent to Telegram. |
| `regime_snapshot` | object | Market regime at the time of the scan. Denormalized from whatever market analysis the pipeline performs. |
| `strategies_run` | array | Which strategy modules were executed. |
| `status` | string | One of: `running`, `completed`, `failed`, `partial`. |
| `error_message` | string | Top-level error if the scan failed entirely. |

### Partition key: `/date`

Natural choice. One document per day, queried by date. The dashboard shows "today's scan status" or "scan history for the last 30 days."

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Today's scan status | `WHERE c.date = '2026-03-07'` | Single partition |
| Scan history | `WHERE c.date >= '2026-02-01' ORDER BY c.date DESC` | Cross-partition (small range) |
| Failed scans | `WHERE c.status = 'failed'` | Cross-partition (rare query) |

---

## 8. Phase 2 Containers (Design Now, Build Later)

These containers support the trade journal (Phase 2). The schemas are defined now to ensure Phase 1 documents (especially signals) include the fields needed for Phase 2 integration. The containers themselves can be created when Phase 2 development begins.

### Container: trades (Trade Journal)

**Purpose:** Log actual trades taken, track P&L, compare signals vs outcomes. This is the core of the feedback loop described in `17-trading-journal-framework.md`.

The schema below aligns with the trade log structure from `17-trading-journal-framework.md` section 2, adapted for a NoSQL document model with Swedish market context.

```json
{
  "id": "trade_001",
  "ticker": "VOLV-B.ST",
  "direction": "long",
  "status": "closed",
  "signal_id": "sig_VOLV-B.ST_2026-03-07_mean_reversion",
  "strategy": "mean_reversion",
  "setup_type": "bollinger_bounce",
  "entry_date": "2026-03-08",
  "entry_price": 248.20,
  "entry_order_type": "limit",
  "position_size_shares": 40,
  "position_size_sek": 9928.00,
  "risk_amount_sek": 292.00,
  "risk_percent": 1.0,
  "stop_price": 240.90,
  "target_price": 258.50,
  "exit_date": "2026-03-15",
  "exit_price": 256.30,
  "exit_reason": "target_reached",
  "pnl_sek": 324.00,
  "pnl_percent": 3.26,
  "r_multiple": 1.11,
  "commission_sek": 9.72,
  "slippage_entry_sek": 0.40,
  "slippage_exit_sek": -0.20,
  "hold_days": 5,
  "market_regime_at_entry": "trending_orderly",
  "sector": "Industrials",
  "score_at_entry": 17,
  "score_grade_at_entry": "A",
  "emotional_state": 2,
  "confidence_level": 4,
  "fomo_flag": false,
  "revenge_flag": false,
  "mistakes": "",
  "lessons_learned": "Clean setup, followed plan exactly",
  "trade_grade": "A",
  "review_notes": "",
  "reviewed": true,
  "notes": "Clean setup, followed plan",
  "tags": ["mean_reversion", "q1_2026", "industrials"],
  "created_at": "2026-03-08T09:15:00Z",
  "updated_at": "2026-03-15T16:45:00Z",
  "schema_version": 1
}
```

### Key fields from the journal framework

The following fields come directly from the trade log structure in `17-trading-journal-framework.md`:

- **Psychological fields:** `emotional_state` (1-5), `confidence_level` (1-5), `fomo_flag`, `revenge_flag`, `mistakes`, `lessons_learned`. These are what make a trade journal useful beyond simple P&L tracking.
- **R-multiple:** `pnl_sek / risk_amount_sek`. Normalizes trade results by initial risk, enabling comparison across different position sizes (from Van Tharp's framework, referenced in `05-risk-management.md`).
- **Exit reason:** Enum values aligned with `17-trading-journal-framework.md` section 2: `target_reached`, `stop_hit`, `trailing_stop`, `time_exit`, `discretionary`, `partial_exit`, `gap_through_stop`.
- **Trade grade:** Post-trade evaluation of execution quality, independent of outcome. A trade can be graded "A" (perfect execution) but lose money, or graded "C" (poor execution) but make money.

### Signal linkage

The `signal_id` field links the trade back to the original signal that triggered it. This is a soft reference (not a foreign key — NoSQL has no foreign keys). The signal document contains the full scoring breakdown and indicator snapshot at the time of the signal, so Phase 3's dashboard can display "signal → trade → outcome" flows.

Not every trade has a `signal_id`. Manual trades (taken without a scanner signal) will have `signal_id: null`.

### Partition key: `/status`

**Trade-off analysis:**

| Partition key | Best for | Weakness |
|---------------|----------|----------|
| `/ticker` | "All trades for VOLV-B" — stock-specific analysis. | "Show all open trades" requires cross-partition query. |
| `/status` | "Show all open trades" — the most frequent Phase 2 query. Portfolio management needs to quickly find open positions. | Only 3 partition values (`open`, `closed`, `cancelled`), leading to uneven partition sizes over time. |
| `/entry_date` | Date-based analysis. | Neither stock nor status queries are efficient. |

**Recommendation: `/status`.**

Rationale:
1. The most frequent operational query is "what are my open trades?" — this must be fast.
2. The "hot" partition (`open`) stays small (typically 3-8 trades at any time for a swing trader).
3. The "cold" partition (`closed`) grows over time but is queried less frequently and usually with additional filters (date range, strategy, ticker).
4. With at most a few thousand trades per year, even the `closed` partition is small enough that cross-partition queries are cheap.

**Alternative considered:** A composite approach using `/ticker` with a separate "open positions" document could work, but adds complexity. At this data volume, `/status` is simpler and fast enough.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| All open trades | `WHERE c.status = 'open'` | Single partition |
| Trade by ID | Point read by `id` | Single partition (if status known) |
| Trade history for a stock | `WHERE c.ticker = 'VOLV-B.ST'` | Cross-partition |
| Trades by strategy | `WHERE c.strategy = 'mean_reversion'` | Cross-partition |
| Closed trades in date range | `WHERE c.status = 'closed' AND c.exit_date >= '2026-01-01'` | Single partition |
| Win rate calculation | `WHERE c.status = 'closed' AND c.pnl_sek > 0` | Single partition |

---

### Container: portfolio_snapshots (Daily Portfolio State)

**Purpose:** Daily snapshot of the entire portfolio — total value, cash, positions, exposure. This supports Phase 3's equity curve and portfolio analytics.

```json
{
  "id": "portfolio_2026-03-07",
  "date": "2026-03-07",
  "total_value_sek": 250000,
  "cash_sek": 75000,
  "invested_sek": 175000,
  "cash_percent": 30.0,
  "open_positions": 4,
  "daily_pnl_sek": 1250,
  "daily_pnl_percent": 0.50,
  "cumulative_pnl_sek": 12500,
  "cumulative_pnl_percent": 5.26,
  "positions": [
    {
      "ticker": "VOLV-B.ST",
      "shares": 40,
      "entry_price": 248.20,
      "current_price": 247.80,
      "value_sek": 9912,
      "unrealized_pnl_sek": -16,
      "unrealized_pnl_percent": -0.16,
      "weight_percent": 3.96
    },
    {
      "ticker": "ERIC-B.ST",
      "shares": 100,
      "entry_price": 80.00,
      "current_price": 78.50,
      "value_sek": 7850,
      "unrealized_pnl_sek": -150,
      "unrealized_pnl_percent": -1.88,
      "weight_percent": 3.14
    }
  ],
  "exposure_percent": 70.0,
  "max_drawdown_sek": -3200,
  "max_drawdown_percent": -1.28,
  "created_at": "2026-03-07T17:30:00Z",
  "schema_version": 1
}
```

### Partition key: `/date`

One snapshot per day, queried by date. The dashboard shows the equity curve (query a date range) or today's portfolio state (query today's date). Both patterns align with date-based partitioning.

### Design note on the positions array

The `positions` array is embedded directly in the snapshot document. This is a deliberate denormalization. A swing trader typically holds 3-8 positions simultaneously, so the array stays small. Each snapshot is a self-contained point-in-time record — it does not reference other documents.

If the portfolio grew to 50+ simultaneous positions (unlikely for swing trading), the positions could be moved to a separate container. At expected scale, embedding is simpler and cheaper.

### Access patterns

| Operation | Query | Partition hit |
|-----------|-------|---------------|
| Today's portfolio | `WHERE c.date = '2026-03-07'` | Single partition |
| Equity curve (date range) | `WHERE c.date >= '2026-01-01' AND c.date <= '2026-03-07' ORDER BY c.date` | Cross-partition (one per day) |
| Worst drawdown | `ORDER BY c.max_drawdown_percent ASC OFFSET 0 LIMIT 1` | Cross-partition |

---

## 9. Phase 3 Considerations

### Dashboard access patterns

The Phase 3 dashboard needs to answer these questions efficiently:

| Question | Data source | Query type |
|----------|-------------|------------|
| "What signals fired today?" | signals | Single partition (date) |
| "Show me VOLV-B's chart with indicators" | daily_prices + indicators | Two single-partition queries (ticker) |
| "What is my current portfolio?" | portfolio_snapshots | Single partition (today's date) |
| "What is my equity curve this year?" | portfolio_snapshots | Cross-partition range query |
| "Which strategy has the best win rate?" | trades | Cross-partition aggregation |
| "Show my P&L by month" | trades | Cross-partition aggregation |
| "Compare signal score vs actual trade outcome" | signals + trades | Cross-container, client-side join |

### Aggregated views: compute on read vs. pre-aggregate

For Phase 3 analytics, some queries aggregate across many documents (e.g., "win rate by strategy for 2026"). Two approaches exist:

**Option A: Compute on read (simpler)**

Query all relevant trades, compute aggregates in application code (Python/pandas).

- Pros: No additional containers. Always up to date. Simple to implement.
- Cons: Slower for large datasets. Costs more RU for repeated queries.
- At SwingTrader's scale (hundreds of trades per year, not millions): this is fine.

**Option B: Pre-aggregate (faster reads)**

Create a `strategy_performance` container with pre-computed aggregates that are updated whenever a trade is closed.

```json
{
  "id": "perf_mean_reversion_2026",
  "strategy": "mean_reversion",
  "year": 2026,
  "total_trades": 45,
  "wins": 28,
  "losses": 17,
  "win_rate": 62.2,
  "avg_r_multiple": 1.35,
  "total_pnl_sek": 15230,
  "avg_hold_days": 4.8,
  "best_trade_r": 3.2,
  "worst_trade_r": -1.0,
  "updated_at": "2026-03-07T17:00:00Z"
}
```

- Pros: Dashboard queries are instant (single point read). No aggregation needed at query time.
- Cons: Must be updated whenever trades change. Can get out of sync. More complex pipeline.

**Recommendation: Start with Option A (compute on read).** At SwingTrader's data volume, aggregating a few hundred trades takes milliseconds in Python. Pre-aggregation is premature optimization. If the dashboard feels slow after a year of data (unlikely), add pre-aggregated documents then.

### Materialized views for common dashboard queries

If Option A proves too slow, create a `dashboard_cache` container with materialized views:

- Daily performance summary
- Weekly/monthly P&L rollups
- Strategy comparison table
- Sector heat map data

These can be rebuilt nightly by a background job after the scan completes. But again — wait until the need is proven.

---

## 10. SQLite Equivalent Schema

For local development without Cosmos DB, the repository pattern abstracts the storage layer. Below are the SQLite CREATE TABLE statements for all containers. SQLite does not support generated columns in the same way as PostgreSQL, so computed fields are handled in application code.

### stocks

```sql
CREATE TABLE IF NOT EXISTS stocks (
    ticker          TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    isin            TEXT,
    sector          TEXT NOT NULL,
    market_cap_tier TEXT NOT NULL CHECK (market_cap_tier IN ('large_cap', 'mid_cap', 'small_cap')),
    exchange        TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'SEK',
    is_active       INTEGER NOT NULL DEFAULT 1,
    added_date      TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    schema_version  INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_stocks_active ON stocks(is_active);
CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);
```

### daily_prices

```sql
CREATE TABLE IF NOT EXISTS daily_prices (
    id              TEXT PRIMARY KEY,   -- '{ticker}_{date}'
    ticker          TEXT NOT NULL,
    date            TEXT NOT NULL,
    open            REAL NOT NULL,
    high            REAL NOT NULL,
    low             REAL NOT NULL,
    close           REAL NOT NULL,
    adjusted_close  REAL NOT NULL,
    volume          INTEGER NOT NULL,
    source          TEXT NOT NULL DEFAULT 'yfinance',
    fetched_at      TEXT NOT NULL,
    schema_version  INTEGER NOT NULL DEFAULT 1,
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker ON daily_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_daily_prices_date ON daily_prices(date);
CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date ON daily_prices(ticker, date);
```

### indicators

```sql
CREATE TABLE IF NOT EXISTS indicators (
    id              TEXT PRIMARY KEY,   -- '{ticker}_{date}'
    ticker          TEXT NOT NULL,
    date            TEXT NOT NULL,
    rsi_14          REAL,
    macd            REAL,
    macd_signal     REAL,
    macd_histogram  REAL,
    bb_upper        REAL,
    bb_middle       REAL,
    bb_lower        REAL,
    sma_20          REAL,
    sma_50          REAL,
    sma_200         REAL,
    ema_9           REAL,
    ema_21          REAL,
    atr_14          REAL,
    adx_14          REAL,
    obv             REAL,
    volume_sma_20   REAL,
    volume_ratio    REAL,
    calculated_at   TEXT NOT NULL,
    schema_version  INTEGER NOT NULL DEFAULT 1,
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_indicators_ticker ON indicators(ticker);
CREATE INDEX IF NOT EXISTS idx_indicators_date ON indicators(date);
CREATE INDEX IF NOT EXISTS idx_indicators_ticker_date ON indicators(ticker, date);
```

### signals

```sql
CREATE TABLE IF NOT EXISTS signals (
    id                      TEXT PRIMARY KEY,   -- 'sig_{ticker}_{date}_{strategy}'
    ticker                  TEXT NOT NULL,
    date                    TEXT NOT NULL,
    strategy                TEXT NOT NULL,
    direction               TEXT NOT NULL CHECK (direction IN ('buy', 'sell')),
    score_total             INTEGER NOT NULL,
    score_trend_alignment   INTEGER NOT NULL DEFAULT 0,
    score_level_quality     INTEGER NOT NULL DEFAULT 0,
    score_catalyst_quality  INTEGER NOT NULL DEFAULT 0,
    score_volume_participation INTEGER NOT NULL DEFAULT 0,
    score_liquidity_execution INTEGER NOT NULL DEFAULT 0,
    score_market_sector_alignment INTEGER NOT NULL DEFAULT 0,
    score_risk_reward       INTEGER NOT NULL DEFAULT 0,
    score_timing_confirmation INTEGER NOT NULL DEFAULT 0,
    score_grade             TEXT NOT NULL CHECK (score_grade IN ('A', 'B', 'C', 'F')),
    entry_price             REAL NOT NULL,
    stop_price              REAL NOT NULL,
    target_price            REAL,
    risk_reward_ratio       REAL,
    reasoning               TEXT,
    indicators_snapshot     TEXT,   -- JSON string
    regime                  TEXT,
    disqualified            INTEGER NOT NULL DEFAULT 0,
    disqualification_reason TEXT,
    sent_to_telegram        INTEGER NOT NULL DEFAULT 0,
    telegram_sent_at        TEXT,
    created_at              TEXT NOT NULL,
    schema_version          INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(date);
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_strategy ON signals(strategy);
CREATE INDEX IF NOT EXISTS idx_signals_date_disqualified ON signals(date, disqualified);
```

Note: In SQLite, the `scores` object from Cosmos DB is flattened into individual columns (`score_trend_alignment`, `score_level_quality`, etc.) because SQLite does not natively support nested objects. The `indicators_snapshot` is stored as a JSON string and can be queried using SQLite's JSON functions (`json_extract`).

### scan_runs

```sql
CREATE TABLE IF NOT EXISTS scan_runs (
    id                  TEXT PRIMARY KEY,   -- 'run_{date}'
    date                TEXT NOT NULL UNIQUE,
    started_at          TEXT NOT NULL,
    completed_at        TEXT,
    duration_seconds    REAL,
    stocks_scanned      INTEGER NOT NULL DEFAULT 0,
    stocks_failed       INTEGER NOT NULL DEFAULT 0,
    failed_tickers      TEXT,   -- JSON array string
    failure_reasons     TEXT,   -- JSON object string
    signals_generated   INTEGER NOT NULL DEFAULT 0,
    signals_qualified   INTEGER NOT NULL DEFAULT 0,
    signals_disqualified INTEGER NOT NULL DEFAULT 0,
    signals_sent        INTEGER NOT NULL DEFAULT 0,
    regime_snapshot     TEXT,   -- JSON object string
    strategies_run      TEXT,   -- JSON array string
    status              TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    error_message       TEXT,
    schema_version      INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_scan_runs_date ON scan_runs(date);
CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON scan_runs(status);
```

### trades (Phase 2)

```sql
CREATE TABLE IF NOT EXISTS trades (
    id                      TEXT PRIMARY KEY,
    ticker                  TEXT NOT NULL,
    direction               TEXT NOT NULL CHECK (direction IN ('long', 'short')),
    status                  TEXT NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open', 'closed', 'cancelled')),
    signal_id               TEXT,   -- FK to signals(id), soft reference
    strategy                TEXT NOT NULL,
    setup_type              TEXT,
    entry_date              TEXT NOT NULL,
    entry_price             REAL NOT NULL,
    entry_order_type        TEXT,
    position_size_shares    INTEGER NOT NULL,
    position_size_sek       REAL NOT NULL,
    risk_amount_sek         REAL,
    risk_percent            REAL,
    stop_price              REAL NOT NULL,
    target_price            REAL,
    exit_date               TEXT,
    exit_price              REAL,
    exit_reason             TEXT CHECK (exit_reason IN (
                                'target_reached', 'stop_hit', 'trailing_stop',
                                'time_exit', 'discretionary', 'partial_exit',
                                'gap_through_stop', NULL)),
    pnl_sek                 REAL,
    pnl_percent             REAL,
    r_multiple              REAL,
    commission_sek          REAL DEFAULT 0,
    slippage_entry_sek      REAL DEFAULT 0,
    slippage_exit_sek       REAL DEFAULT 0,
    hold_days               INTEGER,
    market_regime_at_entry  TEXT,
    sector                  TEXT,
    score_at_entry          INTEGER,
    score_grade_at_entry    TEXT,
    emotional_state         INTEGER CHECK (emotional_state BETWEEN 1 AND 5),
    confidence_level        INTEGER CHECK (confidence_level BETWEEN 1 AND 5),
    fomo_flag               INTEGER DEFAULT 0,
    revenge_flag            INTEGER DEFAULT 0,
    mistakes                TEXT,
    lessons_learned         TEXT,
    trade_grade             TEXT,
    review_notes            TEXT,
    reviewed                INTEGER DEFAULT 0,
    notes                   TEXT,
    tags                    TEXT,   -- JSON array string
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL,
    schema_version          INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
CREATE INDEX IF NOT EXISTS idx_trades_entry_date ON trades(entry_date);
CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id);
CREATE INDEX IF NOT EXISTS idx_trades_status_exit_date ON trades(status, exit_date);
```

### portfolio_snapshots (Phase 2)

```sql
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id                      TEXT PRIMARY KEY,   -- 'portfolio_{date}'
    date                    TEXT NOT NULL UNIQUE,
    total_value_sek         REAL NOT NULL,
    cash_sek                REAL NOT NULL,
    invested_sek            REAL NOT NULL,
    cash_percent            REAL NOT NULL,
    open_positions          INTEGER NOT NULL,
    daily_pnl_sek           REAL,
    daily_pnl_percent       REAL,
    cumulative_pnl_sek      REAL,
    cumulative_pnl_percent  REAL,
    positions               TEXT,   -- JSON array string
    exposure_percent        REAL,
    max_drawdown_sek        REAL,
    max_drawdown_percent    REAL,
    created_at              TEXT NOT NULL,
    schema_version          INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(date);
```

### Repository pattern mapping

The SQLite schema above maps 1:1 to the Cosmos DB containers. The repository interface defines operations like:

```python
class PriceRepository(Protocol):
    def get_prices(self, ticker: str, start_date: str, end_date: str) -> list[dict]: ...
    def get_latest_price(self, ticker: str) -> dict | None: ...
    def upsert_price(self, price: dict) -> None: ...
    def upsert_prices_bulk(self, prices: list[dict]) -> None: ...
```

Two implementations exist: `CosmosPriceRepository` and `SqlitePriceRepository`. Business logic depends only on the Protocol, not on either implementation. Switching storage backends is a configuration change, not a code change.

---

## 11. Data Volume Estimates

| Container | Docs/Day | Docs/Year | Avg Doc Size | Size/Year |
|-----------|----------|-----------|--------------|-----------|
| stocks | 0 (static) | ~100 | ~500 bytes | ~50 KB |
| daily_prices | ~100 | ~25,200 | ~200 bytes | ~5 MB |
| indicators | ~100 | ~25,200 | ~400 bytes | ~10 MB |
| signals | ~3-10 | ~750-2,500 | ~800 bytes | ~2 MB |
| scan_runs | 1 | ~252 | ~1 KB | ~250 KB |
| trades (Ph2) | ~2-5 | ~500-1,250 | ~1 KB | ~1.25 MB |
| portfolio_snapshots (Ph2) | 1 | ~252 | ~2 KB | ~500 KB |
| **Total** | | | | **~19 MB/year** |

This is tiny — well within Cosmos DB's free tier (25 GB storage) and serverless tier ($0.25/GB/month). A SQLite database file would stay under 100 MB even after 5 years of data.

### Cosmos DB RU cost at this scale

From `11-azure-cosmos-db-evaluation.md`: estimated daily consumption is ~4,500 RU, costing approximately $0.03-0.10/month on serverless. Effectively free, and literally free with the Cosmos DB free tier.

### Growth projections

| Scenario | Year 1 | Year 3 | Year 5 |
|----------|--------|--------|--------|
| 100 stocks, 1 scan/day | ~19 MB | ~57 MB | ~95 MB |
| 150 stocks, 1 scan/day | ~28 MB | ~84 MB | ~140 MB |
| 150 stocks + more indicators | ~40 MB | ~120 MB | ~200 MB |

Even the most aggressive growth scenario stays well under any meaningful storage limit.

---

## 12. Partition Key Summary

| Container | Partition Key | Rationale |
|-----------|--------------|-----------|
| stocks | `/ticker` | Lookup by ticker. Small dataset makes this a non-critical choice. |
| daily_prices | `/ticker` | Query price history per stock. The dominant access pattern. |
| indicators | `/ticker` | Query indicators per stock. Same pattern as prices. |
| signals | `/date` | Query "today's signals" — the most frequent operation in Phase 1. |
| scan_runs | `/date` | One document per day, queried by date. |
| trades | `/status` | Query open vs closed trades. "Show open positions" is the hottest query. |
| portfolio_snapshots | `/date` | Query by date for equity curve and daily portfolio state. |

### Partition key immutability warning

Cosmos DB partition keys cannot be changed after container creation. If access patterns change significantly (e.g., the dashboard's most frequent query becomes "all signals for a ticker" instead of "today's signals"), the container must be recreated with a new partition key and data migrated. The choices above are based on the expected access patterns described for each phase.

---

## 13. Indexing Strategy

### Cosmos DB

Cosmos DB indexes every field in every document by default. This is the correct configuration for SwingTrader's workload:

- The data volume is tiny (megabytes, not gigabytes).
- The indexing overhead per write is negligible (a few extra RU).
- The benefit of default indexing is that any query works efficiently without manual index management.

**Do not disable or customize indexing** unless profiling shows a specific query is slow and an index policy change would help. At this scale, that will not happen.

If the Phase 3 dashboard reveals slow queries on compound filters (e.g., "signals where strategy = X AND score_total >= 15 AND date >= Y"), a **composite index** can be added:

```json
{
  "compositeIndexes": [
    [
      { "path": "/strategy", "order": "ascending" },
      { "path": "/score_total", "order": "descending" },
      { "path": "/date", "order": "descending" }
    ]
  ]
}
```

But wait until the need is proven. Default indexing handles most query patterns at this scale.

### SQLite

SQLite requires explicit indexes. The CREATE INDEX statements in section 10 cover the essential access patterns. The key indexes are:

| Table | Index | Purpose |
|-------|-------|---------|
| daily_prices | `(ticker, date)` | Price history for a stock over a date range |
| indicators | `(ticker, date)` | Indicator history for a stock over a date range |
| signals | `(date)` | Today's signals |
| signals | `(date, disqualified)` | Today's qualified signals |
| trades | `(status)` | Open vs closed trades |
| trades | `(status, exit_date)` | Closed trades in a date range |

**Covering indexes** (indexes that include all queried columns) are not needed at this scale. SQLite is fast enough with simple indexes on filter/sort columns.

### SQLite JSON queries

For columns stored as JSON strings (e.g., `indicators_snapshot`, `positions`, `tags`), SQLite's built-in JSON functions can extract values:

```sql
-- Find signals where RSI was below 30
SELECT * FROM signals
WHERE json_extract(indicators_snapshot, '$.rsi_14') < 30;

-- Find trades tagged with 'mean_reversion'
SELECT * FROM trades
WHERE EXISTS (
    SELECT 1 FROM json_each(tags)
    WHERE json_each.value = 'mean_reversion'
);
```

These JSON queries are slower than indexed column queries but adequate for analytical use cases on small datasets.

---

## 14. Migration and Versioning

### Schema versioning

Every document includes a `schema_version` field (integer, starting at 1). This enables:

1. **Detection:** Application code can check the version and handle old and new document formats.
2. **Lazy migration:** When reading an old document, the application can upgrade it in memory (and optionally write it back in the new format).
3. **Bulk migration:** A migration script can query documents by `schema_version` and update them.

### Cosmos DB migration approach

Cosmos DB is schemaless, so "schema changes" are really just application-level conventions:

**Adding a new field:** Just start writing it. Old documents will not have the field. Application code must handle `None`/missing gracefully. Example: adding `ema_50` to indicators.

```python
# Safe access pattern for potentially missing fields
ema_50 = doc.get("ema_50")  # Returns None if field does not exist
```

**Removing a field:** Stop writing it. Old documents still have it but it is ignored. No migration needed unless storage is a concern (it is not at this scale).

**Renaming a field:** This is the only change that requires migration. Write a script that reads all documents, renames the field, and writes them back. Bump `schema_version`.

**Changing a field's meaning:** Bump `schema_version`. Application code branches on the version number. Example: if `risk_reward_ratio` changes from "reward/risk" to "risk/reward," old documents need to be interpreted differently.

### SQLite migration approach

SQLite schema changes are more rigid. Two options:

**Option A: Alembic (recommended for production)**

Alembic is the standard migration tool for SQLAlchemy. It generates migration scripts that can be applied in order. This is the right choice if SQLite becomes a long-term production database.

**Option B: Simple migration scripts (fine for local dev)**

A `migrations/` folder with numbered SQL scripts:

```
migrations/
  001_initial_schema.sql
  002_add_ema_50_to_indicators.sql
  003_add_score_grade_to_signals.sql
```

A simple migration runner checks which scripts have been applied (tracked in a `_migrations` table) and runs any new ones:

```sql
CREATE TABLE IF NOT EXISTS _migrations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL UNIQUE,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Backward compatibility

The repository pattern ensures that migration complexity is contained within the repository implementation. Business logic never sees raw documents or SQL rows — it works with Python dataclasses or dictionaries that the repository produces. When a schema change occurs, only the repository's read/write methods need to handle the version difference.

---

## Cross-reference summary

| This document's section | References |
|--------------------------|-----------|
| Scoring fields in signals | `23-setup-quality-scoring.md` — 8-category scoring model, 0-20 scale, grade bands |
| Trade journal fields | `17-trading-journal-framework.md` — trade log structure, psychological fields, exit reasons |
| R-multiple calculation | `05-risk-management.md` via `17-trading-journal-framework.md` |
| Market regime values | `08-market-structure-and-conditions.md`, `25-regime-to-strategy-mapping.md` |
| Hard disqualifiers | `23-setup-quality-scoring.md` section 5, `25-regime-to-strategy-mapping.md` |
| Cosmos DB evaluation | `11-azure-cosmos-db-evaluation.md` — pricing, partition keys, Python SDK |
| Indicator definitions | `02-technical-indicators.md` |
| Repository pattern | `11-azure-cosmos-db-evaluation.md` sections 10-11 |
