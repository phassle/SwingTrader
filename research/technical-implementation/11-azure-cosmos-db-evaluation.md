# 11 - Azure Cosmos DB Evaluation

> Research date: 2026-03-08
> Goal: Evaluate whether Azure Cosmos DB is a sensible replacement for SQLite in the SwingTrader Python scanner. Covers pricing reality, data modeling, Python SDK usage, and a clear recommendation.
> Prerequisite: Read [09-azure-container-apps-deep-dive.md](09-azure-container-apps-deep-dive.md) for the Container Apps hosting context, and [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md) for the overall system design.

---

## Table of Contents

1. [Cosmos DB Overview](#1-cosmos-db-overview)
2. [Cosmos DB Pricing Reality](#2-cosmos-db-pricing-reality)
3. [Cosmos DB vs SQLite for This Project](#3-cosmos-db-vs-sqlite-for-this-project)
4. [When Cosmos DB Makes Sense for This Project](#4-when-cosmos-db-makes-sense-for-this-project)
5. [When Cosmos DB Does NOT Make Sense](#5-when-cosmos-db-does-not-make-sense)
6. [Which Cosmos DB API to Use](#6-which-cosmos-db-api-to-use)
7. [Data Modeling for Cosmos DB](#7-data-modeling-for-cosmos-db)
8. [Python SDK Usage](#8-python-sdk-usage)
9. [Local Development with Cosmos DB](#9-local-development-with-cosmos-db)
10. [Migration Path: SQLite to Cosmos DB](#10-migration-path-sqlite-to-cosmos-db)
11. [Complete Integration Example](#11-complete-integration-example)
12. [Recommendation](#12-recommendation)

---

## 1. Cosmos DB Overview

Azure Cosmos DB is Microsoft's globally distributed, multi-model NoSQL database service. It was designed from the ground up for planet-scale workloads: think global e-commerce, IoT telemetry, gaming leaderboards with millions of operations per second across multiple continents.

### What It Offers

- **Global distribution:** Replicate data to any number of Azure regions with single-digit millisecond reads/writes.
- **Multi-model:** Supports multiple APIs on the same underlying engine.
- **Guaranteed SLAs:** 99.999% availability for multi-region accounts, 99.99% for single-region.
- **Automatic indexing:** Every field in every document is indexed by default.
- **Tunable consistency:** Five consistency levels from strong to eventual.

### Available APIs

| API | Model | Best For |
|-----|-------|----------|
| NoSQL (Core) | JSON documents | New applications, flexible schemas |
| MongoDB | BSON documents | Existing MongoDB applications |
| PostgreSQL | Relational (Citus-based) | Relational workloads needing scale |
| Table | Key-value pairs | Simple structured data |
| Gremlin | Graph | Relationship-heavy data |

### The Elephant in the Room

Cosmos DB is engineered for workloads that are orders of magnitude larger than what SwingTrader needs. It is like renting a 747 to fly from Stockholm to Gothenburg. The question is whether the serverless pricing tier makes the 747 cheap enough that it does not matter.

---

## 2. Cosmos DB Pricing Reality

This is the most important section. Cosmos DB pricing is built around **Request Units (RU)** — an abstraction that bundles CPU, IOPS, and memory into a single currency. A 1 KB point read by ID costs 1 RU. A 1 KB write costs roughly 5-10 RU depending on indexing.

### Provisioned Throughput

You reserve a fixed number of RU/s (request units per second) and pay for that capacity whether you use it or not.

- **Minimum:** 400 RU/s per container
- **Cost:** ~$0.008/hour per 100 RU/s
- **400 RU/s = ~$23/month per container**
- With 3-4 containers (prices, indicators, signals, journal), you are looking at **$70-90/month minimum**

**Verdict for SwingTrader:** Absolutely not. The scanner runs for 5 minutes a day and sits idle the other 23 hours and 55 minutes. Paying for reserved throughput 24/7 is throwing money away.

### Autoscale Provisioned Throughput

Automatically scales between 10% and 100% of a configured maximum RU/s. Still has a minimum of 400 RU/s max (which means 40 RU/s minimum actual), still ~$23/month per container at the floor.

**Verdict for SwingTrader:** Same problem. Still paying for idle capacity.

### Serverless

This is the interesting one. No reserved capacity. You pay only for the RUs you actually consume.

**Pricing:**
- **Request Units:** $0.25 per 1 million RU consumed
- **Storage:** $0.25 per GB per month

**Estimating SwingTrader's actual RU consumption:**

| Operation | Count | RU per op | Total RU |
|-----------|-------|-----------|----------|
| Daily price inserts | 150 stocks | ~10 RU | 1,500 |
| Indicator writes | 150 stocks | ~15 RU | 2,250 |
| Signal writes | ~10 signals | ~10 RU | 100 |
| Dashboard reads (prices) | ~50 queries | ~5 RU | 250 |
| Dashboard reads (signals) | ~20 queries | ~5 RU | 100 |
| Dashboard reads (indicators) | ~30 queries | ~10 RU | 300 |
| **Daily total** | | | **~4,500 RU** |

Monthly total: ~4,500 × 30 = **~135,000 RU**

That is 0.135 million RU. Cost: **$0.03/month** for request units.

Storage: 150 stocks × 365 days × ~1 KB per document × 3 containers = ~160 MB after a year. At $0.25/GB: **$0.04/month** after a full year of data.

**Total monthly cost for serverless: roughly $0.05-$0.10/month.** Essentially nothing.

### Serverless Limitations

Before getting excited, know the constraints:
- **Maximum 5,000 RU/s burst capacity** — not an issue for this workload
- **Maximum 50 GB storage per container** — years of data before hitting this
- **No geo-replication** — irrelevant for a single-user tool
- **No dedicated throughput guarantees** — fine, we do not need them
- **Max 1 million RU per single request** — will never come close

For this workload, none of these limitations matter.

### Free Tier

Azure offers a Cosmos DB free tier:
- **1,000 RU/s provisioned throughput** (not serverless, but free)
- **25 GB storage**
- **One per Azure subscription, forever (not a trial)**

If you have not used your free tier on this subscription, Cosmos DB is literally free for SwingTrader. The 1,000 RU/s is 20x more than this workload needs, and 25 GB is 100x more storage than needed.

**Check if your free tier is available:** Go to Azure Portal > Cosmos DB > Create > look for the "Apply Free Tier Discount" toggle. If it says "1 free tier account available," you are golden.

---

## 3. Cosmos DB vs SQLite for This Project

An honest side-by-side comparison for the SwingTrader workload specifically:

| Factor | SQLite | Cosmos DB Serverless |
|--------|--------|---------------------|
| **Monthly cost** | $0 | ~$0.10 (or free with free tier) |
| **Setup complexity** | Zero — it is a file | Medium — Azure resource, connection strings, SDK |
| **Schema changes** | ALTER TABLE migrations | Just add fields to documents |
| **Query power** | Full SQL with joins, CTEs, window functions | SQL-like but no joins across containers |
| **Analytical queries** | Excellent (SQLite is surprisingly fast) | Possible but more expensive (each query costs RU) |
| **Backup** | Manual: copy the .db file | Automatic: continuous backups, point-in-time restore |
| **Multi-service access** | Need shared volume or file copy | Any service connects with a connection string |
| **Local development** | Just works, no setup | Need emulator or dev account |
| **Dashboard access** | Must mount the same file or copy it | Direct connection from any Streamlit app |
| **Vendor lock-in** | None | Azure-specific (data export is easy, but code changes) |
| **Tooling** | DB Browser for SQLite, any SQL client | Azure Portal Data Explorer, limited tooling |
| **Python libraries** | `sqlite3` (built-in, zero dependencies) | `azure-cosmos` (additional dependency) |
| **Data inspection** | Open the file, run SQL | Azure Portal or SDK |
| **Offline capability** | Full | None |
| **Learning curve** | Minimal if you know SQL | Medium: partition keys, RU, document modeling |

### Where SQLite Wins

- **Simplicity.** It is a file. You `import sqlite3` and you are done. No accounts, no connection strings, no SDKs, no configuration.
- **Query power.** SQLite supports full SQL including joins, subqueries, window functions, CTEs. Want to find stocks where RSI crossed below 30 while MACD is above signal and the 20-day SMA is above the 50-day SMA? One SQL query. In Cosmos DB, you might need multiple queries and client-side joins.
- **Local development.** The database is just a file in your project folder. No emulator needed, no internet connection needed, no Azure account needed.
- **Zero cost, guaranteed.** Not "probably free" or "almost free." Actually zero.

### Where Cosmos DB Wins

- **Multi-service access.** This is the real advantage. If you have a Container Apps Job running the scanner AND a separate Streamlit Container App for the dashboard, both can connect to Cosmos DB with a connection string. With SQLite, you need shared Azure File storage or some other mechanism to share the database file between containers.
- **Managed backups.** Continuous backup with point-in-time restore. No need to set up backup scripts.
- **No file system concerns.** No worrying about SQLite file corruption if the container crashes mid-write. No need for Azure Files mounts, which add latency and cost ($0.06/GB/month for the mount).

---

## 4. When Cosmos DB Makes Sense for This Project

1. **You want both scanner and dashboard to access the same data.** This is the killer feature. SQLite on Azure Container Apps means dealing with Azure File Share mounts, which add complexity and latency. Cosmos DB gives both services direct access with a connection string.

2. **You have the free tier available.** If your Azure subscription's Cosmos DB free tier is unused, there is literally no cost. Use it.

3. **You plan to add more services.** A Telegram bot that queries data? An API for a mobile app? Each new service can just connect to Cosmos DB without any file-sharing infrastructure.

4. **You value managed operations.** Automatic backups, automatic indexing, no file system to manage.

5. **You are already committed to Azure.** If the rest of the stack is on Azure, adding Cosmos DB is natural. The Azure Portal lets you browse data, run queries, and monitor usage.

---

## 5. When Cosmos DB Does NOT Make Sense

1. **You want to keep it as simple as possible.** SQLite is objectively simpler. Fewer moving parts, fewer things that can go wrong, no Azure dependency for the database.

2. **You want to run everything locally without Azure.** SQLite works offline. Cosmos DB requires an internet connection (or the emulator, which is heavy).

3. **You want zero vendor lock-in.** Your data access code will be Cosmos DB-specific. Switching to another database later means rewriting the storage layer. (This can be mitigated with a repository pattern, covered in section 11.)

4. **You need complex analytical queries.** If you plan to do things like "find all stocks where RSI was below 30 on the same day that volume was 2x above average, and the next day's close was higher than open," SQL is far more natural and powerful than Cosmos DB's query language.

5. **You do not have the free tier, and you are extremely cost-sensitive.** The ~$0.10/month serverless cost is trivial, but SQLite is still free-er.

---

## 6. Which Cosmos DB API to Use

### NoSQL API (Document/JSON) — RECOMMENDED

The NoSQL API (sometimes called Core API or SQL API) is the native Cosmos DB API. It stores JSON documents and queries them with a SQL-like syntax.

**Why it is the best fit:**
- Most mature API with the best SDK support
- Serverless mode is fully supported
- SQL-like query language is familiar
- JSON documents map naturally to Python dictionaries and pandas DataFrames
- Best documentation and community support
- Feature parity — all new Cosmos DB features land here first

**Query example:**
```sql
SELECT c.ticker, c.close, c.volume
FROM c
WHERE c.ticker = 'VOLV-B.ST'
AND c.date >= '2026-01-01'
ORDER BY c.date DESC
```

### PostgreSQL API (Cosmos DB for PostgreSQL) — NOT RECOMMENDED

This is actually a completely different product under the Cosmos DB umbrella. It runs Citus (distributed PostgreSQL) and is designed for multi-tenant SaaS applications.

- **Minimum cost: ~$30/month** for a single-node cluster
- This is a server that runs 24/7, not serverless
- Vastly over-engineered for this workload
- If you want PostgreSQL, use Azure Database for PostgreSQL Flexible Server instead (~$13/month for the cheapest tier)

**Verdict:** Hard no.

### Table API — NOT RECOMMENDED

Simple key-value storage with limited query capabilities.

- Cannot query by arbitrary fields efficiently
- No support for complex filters
- Limited to key-based lookups and range scans
- Too restrictive for stock data analysis

**Verdict:** Too limited.

### MongoDB API — VIABLE ALTERNATIVE

The MongoDB API runs on the same Cosmos DB engine but speaks the MongoDB wire protocol.

- Serverless mode is supported
- Familiar if you know MongoDB
- Can use `pymongo` instead of the Cosmos SDK
- Good query capabilities

However:
- Slightly less feature-complete than the NoSQL API
- Not the "native" API, so some features lag
- If you do not already know MongoDB, there is no advantage

**Verdict:** Fine if you prefer MongoDB, but NoSQL API is the better default.

### Gremlin API — NOT APPLICABLE

Graph database API. Stock price data is not a graph problem.

### Recommendation: NoSQL API with serverless capacity mode

---

## 7. Data Modeling for Cosmos DB

Cosmos DB stores JSON documents in **containers** (analogous to tables). Each container has a **partition key** — the field used to distribute data across physical partitions. Choosing the right partition key is the single most important modeling decision.

### Key Principles

1. **No joins across containers.** Unlike SQL, you cannot JOIN between containers. Design your documents to be self-contained for common queries.
2. **Partition key determines data locality.** Documents with the same partition key are stored together and can be queried efficiently.
3. **Document ID + partition key must be unique.** The `id` field is required and must be unique within a partition.

### Container: daily_prices

**Partition key:** `/ticker`

This is the right choice because the most common query is "get price history for a specific stock." All price data for VOLV-B.ST lives in the same partition, making range queries by date fast and cheap.

```json
{
  "id": "VOLV-B.ST_2026-03-08",
  "ticker": "VOLV-B.ST",
  "date": "2026-03-08",
  "open": 245.50,
  "high": 248.30,
  "low": 244.10,
  "close": 247.80,
  "volume": 3450000,
  "adjusted_close": 247.80
}
```

**Why this partition key works:**
- Query by ticker: single-partition query (fast, cheap — ~1 RU)
- Query by date across all tickers: cross-partition query (more expensive, but rare)
- 150 stocks means 150 logical partitions — well within limits
- Each stock with 10 years of daily data: ~2,500 documents × ~0.5 KB = ~1.25 MB per partition, nowhere near the 20 GB partition limit

### Container: indicators

**Partition key:** `/ticker`

Same reasoning as prices. Most queries are "get indicators for stock X over time period Y."

```json
{
  "id": "VOLV-B.ST_2026-03-08",
  "ticker": "VOLV-B.ST",
  "date": "2026-03-08",
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
  "atr_14": 4.20,
  "adx_14": 28.5,
  "obv": 15234000,
  "volume_ratio": 1.15
}
```

**Alternative: Embed indicators in the price document.** Since you almost always want prices and indicators together, you could store them in a single document. This saves a separate query and reduces RU cost. The trade-off is slightly larger documents (~1 KB vs ~0.5 KB each). For this workload, either approach is fine.

### Container: signals

**Partition key:** `/date`

Signals are queried differently. The primary question is "what signals were generated today?" not "what signals has VOLV-B.ST had over time." Partitioning by date makes the most common query efficient.

```json
{
  "id": "signal_VOLV-B.ST_2026-03-08_mean_reversion",
  "date": "2026-03-08",
  "ticker": "VOLV-B.ST",
  "strategy": "mean_reversion",
  "direction": "buy",
  "score": 17,
  "entry_price": 247.80,
  "stop_price": 240.90,
  "target_price": 258.50,
  "risk_reward_ratio": 2.46,
  "reasoning": "RSI oversold + near lower Bollinger Band + MACD crossover"
}
```

**Why date as partition key:**
- "Show me today's signals" = single-partition query (fast, cheap)
- "Show me all signals for VOLV-B.ST" = cross-partition query (slightly more expensive, but infrequent)
- Each day has at most ~10-20 signals, so partitions are small

### Container: trade_journal (optional)

**Partition key:** `/ticker` or `/year_month`

```json
{
  "id": "trade_VOLV-B.ST_2026-03-08_001",
  "ticker": "VOLV-B.ST",
  "year_month": "2026-03",
  "entry_date": "2026-03-08",
  "entry_price": 247.80,
  "exit_date": null,
  "exit_price": null,
  "direction": "long",
  "quantity": 100,
  "strategy": "mean_reversion",
  "signal_id": "signal_VOLV-B.ST_2026-03-08_mean_reversion",
  "status": "open",
  "notes": "Entered based on RSI + BB signal, strong sector momentum",
  "pnl": null,
  "pnl_percent": null
}
```

### Partition Key Strategy Summary

| Container | Partition Key | Primary Query Pattern |
|-----------|--------------|----------------------|
| daily_prices | `/ticker` | Price history for a stock |
| indicators | `/ticker` | Indicator history for a stock |
| signals | `/date` | Today's signals |
| trade_journal | `/ticker` | Trade history for a stock |

---

## 8. Python SDK Usage

### Installation

```bash
pip install azure-cosmos
```

### Connection Setup

```python
from azure.cosmos import CosmosClient, PartitionKey
import os

# Connection string from Azure Portal or .env file
COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
# Or use endpoint + key:
# COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
# COSMOS_KEY = os.getenv("COSMOS_KEY")

# Initialize client
client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
# Or: client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
```

### Create Database and Containers

Run this once during initial setup:

```python
def setup_cosmos_db(client: CosmosClient, database_name: str = "swingtrader"):
    """Create database and containers if they don't exist."""

    # Create database
    database = client.create_database_if_not_exists(id=database_name)

    # Create containers with appropriate partition keys
    containers = {
        "daily_prices": "/ticker",
        "indicators": "/ticker",
        "signals": "/date",
        "trade_journal": "/ticker",
    }

    for container_name, partition_key in containers.items():
        database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key),
        )
        print(f"Container '{container_name}' ready (partition key: {partition_key})")

    return database
```

### Insert Daily Price Data

```python
def store_daily_prices(database, ticker: str, prices: list[dict]):
    """
    Store daily OHLCV data for a ticker.
    prices: list of dicts with keys: date, open, high, low, close, volume, adjusted_close
    """
    container = database.get_container_client("daily_prices")

    for price in prices:
        document = {
            "id": f"{ticker}_{price['date']}",
            "ticker": ticker,
            "date": price["date"],
            "open": price["open"],
            "high": price["high"],
            "low": price["low"],
            "close": price["close"],
            "volume": price["volume"],
            "adjusted_close": price.get("adjusted_close", price["close"]),
        }
        # upsert = insert or replace if exists
        container.upsert_item(document)
```

### Insert Indicator Data

```python
def store_indicators(database, ticker: str, date: str, indicators: dict):
    """
    Store calculated indicators for a ticker on a specific date.
    indicators: dict with keys like rsi_14, macd, sma_20, etc.
    """
    container = database.get_container_client("indicators")

    document = {
        "id": f"{ticker}_{date}",
        "ticker": ticker,
        "date": date,
        **indicators,
    }
    container.upsert_item(document)
```

### Insert Signals

```python
def store_signal(database, signal: dict):
    """
    Store a generated signal.
    signal: dict with ticker, date, strategy, direction, score, etc.
    """
    container = database.get_container_client("signals")

    document = {
        "id": f"signal_{signal['ticker']}_{signal['date']}_{signal['strategy']}",
        "date": signal["date"],
        "ticker": signal["ticker"],
        "strategy": signal["strategy"],
        "direction": signal["direction"],
        "score": signal["score"],
        "entry_price": signal.get("entry_price"),
        "stop_price": signal.get("stop_price"),
        "target_price": signal.get("target_price"),
        "reasoning": signal.get("reasoning", ""),
    }
    container.upsert_item(document)
```

### Query Price History for a Ticker

```python
def get_price_history(database, ticker: str, start_date: str = None, end_date: str = None):
    """
    Get price history for a stock. Returns list of dicts sorted by date.
    This is a single-partition query (cheap: ~3-5 RU).
    """
    container = database.get_container_client("daily_prices")

    query = "SELECT * FROM c WHERE c.ticker = @ticker"
    params = [{"name": "@ticker", "value": ticker}]

    if start_date:
        query += " AND c.date >= @start"
        params.append({"name": "@start", "value": start_date})
    if end_date:
        query += " AND c.date <= @end"
        params.append({"name": "@end", "value": end_date})

    query += " ORDER BY c.date ASC"

    results = list(container.query_items(
        query=query,
        parameters=params,
        partition_key=ticker,
    ))
    return results
```

### Query Today's Signals

```python
def get_signals_for_date(database, date: str):
    """
    Get all signals generated on a specific date.
    Single-partition query since signals are partitioned by date.
    """
    container = database.get_container_client("signals")

    query = "SELECT * FROM c WHERE c.date = @date ORDER BY c.score DESC"
    params = [{"name": "@date", "value": date}]

    results = list(container.query_items(
        query=query,
        parameters=params,
        partition_key=date,
    ))
    return results
```

### Query Indicators with Price Data (Cross-Container)

Since Cosmos DB does not support joins across containers, you query each container separately and merge client-side:

```python
def get_stock_analysis(database, ticker: str, date: str):
    """
    Get price + indicators for a stock on a date.
    Two point reads by ID (1 RU each = 2 RU total).
    """
    prices_container = database.get_container_client("daily_prices")
    indicators_container = database.get_container_client("indicators")

    doc_id = f"{ticker}_{date}"

    try:
        price = prices_container.read_item(item=doc_id, partition_key=ticker)
    except Exception:
        price = None

    try:
        indicator = indicators_container.read_item(item=doc_id, partition_key=ticker)
    except Exception:
        indicator = None

    return {"price": price, "indicators": indicator}
```

### Batch Operations for Efficiency

When inserting 150 stocks worth of data, use batch operations to reduce overhead:

```python
def store_daily_batch(database, all_prices: dict[str, dict]):
    """
    Store prices for all stocks. all_prices: {ticker: {date, open, high, ...}}
    Cosmos DB doesn't have true batch across partitions, but we can be efficient.
    """
    container = database.get_container_client("daily_prices")

    for ticker, price_data in all_prices.items():
        document = {
            "id": f"{ticker}_{price_data['date']}",
            "ticker": ticker,
            **price_data,
        }
        container.upsert_item(document)

    # For same-partition batches (e.g., multiple dates for one ticker),
    # Cosmos DB supports transactional batch:
    # container.execute_item_batch(operations, partition_key=ticker)
```

---

## 9. Local Development with Cosmos DB

### Option A: Azure Cosmos DB Emulator

The emulator runs a local instance of Cosmos DB for development and testing.

**Docker (Linux/macOS):**

```bash
# Pull the emulator image
docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest

# Run it
docker run -d \
  --name cosmos-emulator \
  -p 8081:8081 \
  -p 10250-10255:10250-10255 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

**Connection details for emulator:**
```
Endpoint: https://localhost:8081
Key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

**Downsides:**
- The Linux emulator can be resource-hungry (~2 GB RAM)
- SSL certificate issues on macOS (need to disable SSL verification in dev)
- Not 100% feature-complete vs the real service
- Can be flaky

### Option B: Use Cosmos DB Serverless Directly During Development

If you are on the free tier or serverless, just use the real Cosmos DB during development. The cost is negligible (your development queries will cost fractions of a cent), and you avoid all emulator hassles.

```bash
# .env file
COSMOS_CONNECTION_STRING=AccountEndpoint=https://your-account.documents.azure.com:443/;AccountKey=your-key;
```

This is the simplest option and the one most likely to save you time.

### Option C: SQLite Locally, Cosmos DB in Production

Use a repository pattern (covered in section 11) to abstract the storage layer. Run SQLite locally and Cosmos DB in production. Switch based on an environment variable.

```python
# Determined by environment
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "sqlite")  # "sqlite" or "cosmosdb"
```

This gives you the best of both worlds but adds code complexity. Only worth it if you value local-first development AND want Cosmos DB in production.

### Recommendation

**Use Option B** (real Cosmos DB during development) if you are on the free tier. It is the simplest approach and eliminates any emulator vs production behavior differences.

**Use Option C** (repository pattern) if you want the flexibility to run without Azure access. This is more code but gives you independence.

---

## 10. Migration Path: SQLite to Cosmos DB

If you start with SQLite and decide to migrate later, the process is straightforward:

### Step 1: Export SQLite Data to JSON

```python
import sqlite3
import json

def export_sqlite_to_json(db_path: str, output_dir: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Export prices
    cursor = conn.execute("SELECT * FROM daily_prices")
    prices = [dict(row) for row in cursor.fetchall()]
    with open(f"{output_dir}/prices.json", "w") as f:
        json.dump(prices, f, indent=2)

    # Export indicators
    cursor = conn.execute("SELECT * FROM indicators")
    indicators = [dict(row) for row in cursor.fetchall()]
    with open(f"{output_dir}/indicators.json", "w") as f:
        json.dump(indicators, f, indent=2)

    # Similarly for signals, trade_journal
    conn.close()
    print(f"Exported {len(prices)} prices, {len(indicators)} indicators")
```

### Step 2: Import to Cosmos DB

```python
import json

def import_to_cosmos(database, data_dir: str):
    # Import prices
    with open(f"{data_dir}/prices.json") as f:
        prices = json.load(f)

    container = database.get_container_client("daily_prices")
    for price in prices:
        price["id"] = f"{price['ticker']}_{price['date']}"
        container.upsert_item(price)

    print(f"Imported {len(prices)} price records")

    # Repeat for indicators, signals, etc.
```

### Step 3: Update Connection Code

Replace your SQLite storage class with the Cosmos DB storage class (same interface, different backend — see section 11).

### How Long Does This Take?

For 150 stocks × 1 year of data: ~55,000 price documents + ~55,000 indicator documents. At ~10 documents/second (single-threaded), this takes about 3 hours. With async operations or parallelism, under 30 minutes.

This is a one-time operation. Do not over-plan it.

---

## 11. Complete Integration Example

The cleanest approach is a repository pattern — an abstract interface for data storage with concrete implementations for SQLite and Cosmos DB.

### Abstract Interface

```python
from abc import ABC, abstractmethod
from datetime import date


class DataStore(ABC):
    """Abstract base class for SwingTrader data storage."""

    @abstractmethod
    def store_prices(self, ticker: str, prices: list[dict]) -> None:
        """Store daily OHLCV data for a ticker."""
        ...

    @abstractmethod
    def store_indicators(self, ticker: str, date: str, indicators: dict) -> None:
        """Store calculated indicators for a ticker on a date."""
        ...

    @abstractmethod
    def store_signal(self, signal: dict) -> None:
        """Store a generated signal."""
        ...

    @abstractmethod
    def get_price_history(
        self, ticker: str, start_date: str = None, end_date: str = None
    ) -> list[dict]:
        """Get price history for a ticker."""
        ...

    @abstractmethod
    def get_signals(self, date: str) -> list[dict]:
        """Get all signals for a specific date."""
        ...
```

### SQLite Implementation (~60 lines)

```python
import sqlite3


class SQLiteStore(DataStore):
    def __init__(self, db_path: str = "swingtrader.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_prices (
                ticker TEXT, date TEXT, open REAL, high REAL,
                low REAL, close REAL, volume INTEGER, adjusted_close REAL,
                PRIMARY KEY (ticker, date)
            );
            CREATE TABLE IF NOT EXISTS indicators (
                ticker TEXT, date TEXT,
                rsi_14 REAL, macd REAL, macd_signal REAL,
                sma_20 REAL, sma_50 REAL, sma_200 REAL,
                bb_upper REAL, bb_middle REAL, bb_lower REAL,
                atr_14 REAL, adx_14 REAL, obv REAL, volume_ratio REAL,
                PRIMARY KEY (ticker, date)
            );
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY, date TEXT, ticker TEXT,
                strategy TEXT, direction TEXT, score INTEGER,
                entry_price REAL, stop_price REAL, target_price REAL,
                reasoning TEXT
            );
        """)
        self.conn.commit()

    def store_prices(self, ticker: str, prices: list[dict]) -> None:
        for p in prices:
            self.conn.execute(
                """INSERT OR REPLACE INTO daily_prices
                   (ticker, date, open, high, low, close, volume, adjusted_close)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (ticker, p["date"], p["open"], p["high"], p["low"],
                 p["close"], p["volume"], p.get("adjusted_close", p["close"])),
            )
        self.conn.commit()

    def store_indicators(self, ticker: str, date: str, indicators: dict) -> None:
        cols = ", ".join(indicators.keys())
        placeholders = ", ".join(["?"] * len(indicators))
        self.conn.execute(
            f"""INSERT OR REPLACE INTO indicators (ticker, date, {cols})
                VALUES (?, ?, {placeholders})""",
            (ticker, date, *indicators.values()),
        )
        self.conn.commit()

    def store_signal(self, signal: dict) -> None:
        signal_id = f"signal_{signal['ticker']}_{signal['date']}_{signal['strategy']}"
        self.conn.execute(
            """INSERT OR REPLACE INTO signals
               (id, date, ticker, strategy, direction, score,
                entry_price, stop_price, target_price, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (signal_id, signal["date"], signal["ticker"], signal["strategy"],
             signal["direction"], signal["score"], signal.get("entry_price"),
             signal.get("stop_price"), signal.get("target_price"),
             signal.get("reasoning", "")),
        )
        self.conn.commit()

    def get_price_history(self, ticker, start_date=None, end_date=None):
        query = "SELECT * FROM daily_prices WHERE ticker = ?"
        params = [ticker]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date ASC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def get_signals(self, date: str):
        return [
            dict(r) for r in self.conn.execute(
                "SELECT * FROM signals WHERE date = ? ORDER BY score DESC", (date,)
            ).fetchall()
        ]
```

### Cosmos DB Implementation (~55 lines)

```python
from azure.cosmos import CosmosClient, PartitionKey


class CosmosStore(DataStore):
    def __init__(self, connection_string: str, database_name: str = "swingtrader"):
        client = CosmosClient.from_connection_string(connection_string)
        self.db = client.create_database_if_not_exists(id=database_name)
        self._ensure_containers()

    def _ensure_containers(self):
        specs = {
            "daily_prices": "/ticker",
            "indicators": "/ticker",
            "signals": "/date",
        }
        self.containers = {}
        for name, pk in specs.items():
            self.db.create_container_if_not_exists(
                id=name, partition_key=PartitionKey(path=pk)
            )
            self.containers[name] = self.db.get_container_client(name)

    def store_prices(self, ticker: str, prices: list[dict]) -> None:
        container = self.containers["daily_prices"]
        for p in prices:
            doc = {"id": f"{ticker}_{p['date']}", "ticker": ticker, **p}
            container.upsert_item(doc)

    def store_indicators(self, ticker: str, date: str, indicators: dict) -> None:
        container = self.containers["indicators"]
        doc = {"id": f"{ticker}_{date}", "ticker": ticker, "date": date, **indicators}
        container.upsert_item(doc)

    def store_signal(self, signal: dict) -> None:
        container = self.containers["signals"]
        doc = {
            "id": f"signal_{signal['ticker']}_{signal['date']}_{signal['strategy']}",
            **signal,
        }
        container.upsert_item(doc)

    def get_price_history(self, ticker, start_date=None, end_date=None):
        container = self.containers["daily_prices"]
        query = "SELECT * FROM c WHERE c.ticker = @ticker"
        params = [{"name": "@ticker", "value": ticker}]

        if start_date:
            query += " AND c.date >= @start"
            params.append({"name": "@start", "value": start_date})
        if end_date:
            query += " AND c.date <= @end"
            params.append({"name": "@end", "value": end_date})
        query += " ORDER BY c.date ASC"

        return list(container.query_items(
            query=query, parameters=params, partition_key=ticker
        ))

    def get_signals(self, date: str):
        container = self.containers["signals"]
        return list(container.query_items(
            query="SELECT * FROM c WHERE c.date = @date ORDER BY c.score DESC",
            parameters=[{"name": "@date", "value": date}],
            partition_key=date,
        ))
```

### Factory Function

```python
import os


def create_store() -> DataStore:
    """Create the appropriate data store based on environment configuration."""
    backend = os.getenv("STORAGE_BACKEND", "sqlite")

    if backend == "cosmosdb":
        connection_string = os.getenv("COSMOS_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("COSMOS_CONNECTION_STRING environment variable is required")
        return CosmosStore(connection_string)
    else:
        db_path = os.getenv("SQLITE_DB_PATH", "swingtrader.db")
        return SQLiteStore(db_path)
```

### Usage in the Scanner

```python
# In the main scanner entry point
store = create_store()

# Everything else uses the store interface — no knowledge of the backend
store.store_prices("VOLV-B.ST", daily_prices)
store.store_indicators("VOLV-B.ST", "2026-03-08", calculated_indicators)
store.store_signal(generated_signal)

# In the Streamlit dashboard
store = create_store()
signals = store.get_signals("2026-03-08")
prices = store.get_price_history("VOLV-B.ST", start_date="2025-01-01")
```

The scanner and dashboard code never knows or cares whether it is talking to a file or a cloud database.

---

## 12. Recommendation

### The Short Answer

**Start with SQLite.** It is simpler, faster to iterate on, and costs nothing. You can always migrate later.

### The Nuanced Answer

The decision depends on one thing: **do you plan to run a separate Streamlit dashboard alongside the scanner on Azure Container Apps?**

**If no dashboard (scanner + Telegram only):**
Use SQLite. Store the database in an Azure File Share mount. No reason to add Cosmos DB complexity.

**If you want a dashboard that reads the same data:**
Cosmos DB starts to make sense. The alternative — mounting the same Azure File Share in both the scanner job and the dashboard app — works but has caveats:
- SQLite does not handle concurrent readers/writers well over network file systems
- Azure Files adds latency (~5-10 ms per I/O operation)
- If the scanner is writing while the dashboard is reading, you risk lock contention

Cosmos DB eliminates all of these issues. Both services connect via connection string, no shared file system needed.

**If you have the Cosmos DB free tier available:**
Just use Cosmos DB from the start. It is free, it solves the multi-service access problem, and you get automatic backups. The only cost is the slightly higher initial setup complexity (create the Azure resource, configure connection strings, install the SDK).

### Decision Tree

```
Do you need a dashboard reading the same data?
├── No → Use SQLite. Done.
└── Yes →
    Is the Cosmos DB free tier available on your subscription?
    ├── Yes → Use Cosmos DB. It's free and solves the access problem.
    └── No →
        Do you want to pay ~$0.10/month for simpler architecture?
        ├── Yes → Use Cosmos DB serverless.
        └── No → Use SQLite with Azure File Share mount.
```

### If You Choose Cosmos DB

1. Use the **NoSQL API** with **serverless** capacity mode
2. Use the **repository pattern** from section 11 so you can always switch back
3. Partition prices and indicators by `/ticker`, signals by `/date`
4. Use `upsert_item` for all writes (idempotent, handles re-runs gracefully)
5. Set up the connection string as a Container Apps secret

### If You Start with SQLite and Migrate Later

That is fine too. The migration is a few hours of work (section 10). Do not over-engineer the initial version. Build the scanner, get it working, then decide if the multi-service access problem is real enough to warrant Cosmos DB.
