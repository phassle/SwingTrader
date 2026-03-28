# 20 - Cosmos Repository Implementation

> Research date: 2026-03-10
> Goal: Define the repository pattern for accessing Cosmos DB containers (stocks, daily_prices, indicators, signals, scan_runs) with idempotent writes, deterministic IDs, and container bootstrap logic.
> Prerequisites: [13-data-model-design.md](13-data-model-design.md), [11-azure-cosmos-db-evaluation.md](11-azure-cosmos-db-evaluation.md), [19-python-scanner-bootstrap-implementation.md](19-python-scanner-bootstrap-implementation.md)

## Table of Contents

1. [Overview](#overview)
2. [Repository Pattern Design](#repository-pattern-design)
3. [Container Bootstrap Strategy](#container-bootstrap-strategy)
4. [Deterministic ID Generation](#deterministic-id-generation)
5. [Base Repository Implementation](#base-repository-implementation)
6. [Container-Specific Repositories](#container-specific-repositories)
7. [Query Patterns](#query-patterns)
8. [Error Handling and Retries](#error-handling-and-retries)
9. [Testing Against Emulator](#testing-against-emulator)
10. [Performance Considerations](#performance-considerations)

---

## Overview

The repository layer provides **structured access to Cosmos DB** while hiding low-level SDK details. Key responsibilities:

1. **Container bootstrap:** Create database and containers if they don't exist (idempotent)
2. **CRUD operations:** Create, read, update, delete documents with proper partition keys
3. **Deterministic IDs:** Generate stable document IDs for upsert operations
4. **Query abstractions:** Common query patterns (get by ticker, get latest signals, etc.)
5. **Error handling:** Retry transient failures, log errors with context

**Design principles:**
- **Repository per container:** Explicit interfaces (not generic CRUD)
- **Idempotent writes:** Use upsert (insert or replace) for most operations
- **Partition key awareness:** Always provide partition key for reads/writes
- **Immutable documents:** Never modify documents in place, create new versions

---

## Repository Pattern Design

### Why Repository Pattern?

**Without repository:**
```python
# Business logic coupled to Cosmos SDK
from azure.cosmos import CosmosClient

client = CosmosClient.from_connection_string(connection_string)
database = client.get_database_client("SwingTraderDB")
container = database.get_container_client("daily_prices")

# Direct SDK calls scattered throughout codebase
container.upsert_item({"id": "...", "ticker": "...", ...})
```

**Problems:**
- Business logic knows Cosmos SDK details
- Partition key logic repeated everywhere
- Hard to test (need real Cosmos or complex mocking)
- No central place for query patterns

**With repository:**
```python
# Business logic uses clean interface
repository = CosmosRepository(connection_string, database_name)
repository.daily_prices.upsert(ticker="ERIC.ST", date="2026-03-10", data=price_data)
```

**Benefits:**
- Business logic decoupled from Cosmos SDK
- Partition keys and IDs handled by repository
- Easy to test (mock repository interface)
- Query patterns centralized and reusable

---

### Repository Architecture

```
CosmosRepository (root)
    ├── bootstrap() → Create database and containers
    ├── stocks: StocksRepository
    ├── daily_prices: DailyPricesRepository
    ├── indicators: IndicatorsRepository
    ├── signals: SignalsRepository
    └── scan_runs: ScanRunsRepository
```

**Each container has dedicated repository:**
- Knows schema and partition key
- Exposes domain-specific methods (not generic CRUD)
- Generates deterministic IDs internally

---

## Container Bootstrap Strategy

### Bootstrap Requirements

From [13-data-model-design.md](13-data-model-design.md), Phase 1 containers:

| Container | Partition Key | Notes |
|-----------|---------------|-------|
| stocks | /ticker | Static universe (~150 docs) |
| daily_prices | /ticker | High volume (150 tickers × 250 days = 37,500 docs/year) |
| indicators | /ticker | Medium volume (1 doc per ticker per day) |
| signals | /ticker | Low volume (only tickers with signals) |
| scan_runs | /id | Very low volume (1 doc per scan) |

### Bootstrap Implementation

```python
# repository.py
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import logging

logger = logging.getLogger(__name__)

class CosmosRepository:
    """Root repository for Cosmos DB access."""
    
    def __init__(self, connection_string: str, database_name: str):
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database_name = database_name
        self.database = None  # Initialized in bootstrap()
        
        # Container clients (initialized in bootstrap)
        self._stocks_container = None
        self._daily_prices_container = None
        self._indicators_container = None
        self._signals_container = None
        self._scan_runs_container = None
        
        # Sub-repositories (initialized after bootstrap)
        self.stocks = None
        self.daily_prices = None
        self.indicators = None
        self.signals = None
        self.scan_runs = None
    
    def bootstrap(self):
        """Create database and containers if they don't exist (idempotent)."""
        
        logger.info(f"Bootstrapping Cosmos DB: {self.database_name}")
        
        # Create database (idempotent)
        self.database = self.client.create_database_if_not_exists(self.database_name)
        logger.info(f"Database '{self.database_name}' ready")
        
        # Create containers (idempotent)
        self._stocks_container = self._create_container("stocks", "/ticker")
        self._daily_prices_container = self._create_container("daily_prices", "/ticker")
        self._indicators_container = self._create_container("indicators", "/ticker")
        self._signals_container = self._create_container("signals", "/ticker")
        self._scan_runs_container = self._create_container("scan_runs", "/id")
        
        # Initialize sub-repositories
        self.stocks = StocksRepository(self._stocks_container)
        self.daily_prices = DailyPricesRepository(self._daily_prices_container)
        self.indicators = IndicatorsRepository(self._indicators_container)
        self.signals = SignalsRepository(self._signals_container)
        self.scan_runs = ScanRunsRepository(self._scan_runs_container)
        
        logger.info("Cosmos DB bootstrap complete")
    
    def _create_container(self, name: str, partition_key_path: str):
        """Create container if not exists, return container client."""
        
        try:
            container = self.database.create_container_if_not_exists(
                id=name,
                partition_key=PartitionKey(path=partition_key_path),
                # Throughput: Default 400 RU/s (sufficient for Phase 1)
            )
            logger.info(f"Container '{name}' ready (partition key: {partition_key_path})")
            return container
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create container '{name}'", exc_info=True)
            raise
```

**Key patterns:**

1. **Idempotent operations:** `create_database_if_not_exists()`, `create_container_if_not_exists()`
2. **Centralized initialization:** All containers created in one place
3. **Lazy sub-repository init:** Sub-repositories created after containers exist
4. **Clear logging:** Each step logged for observability

---

## Deterministic ID Generation

### Why Deterministic IDs?

**Problem with random IDs:**
```python
# Random UUID
doc_id = str(uuid.uuid4())  # "a3b2c1d4-..."

# Can't upsert — every write creates new document
container.upsert_item({"id": doc_id, "ticker": "ERIC.ST", ...})
```

**Solution with deterministic IDs:**
```python
# ID based on business key: ticker + date
doc_id = f"ERIC.ST_2026-03-10"

# Upsert replaces existing document with same ID
container.upsert_item({"id": doc_id, "ticker": "ERIC.ST", "date": "2026-03-10", ...})
```

**Benefits:**
- Idempotent writes (re-run scan, no duplicates)
- Easy to query by ID: `container.read_item(id="ERIC.ST_2026-03-10", partition_key="ERIC.ST")`
- Natural versioning (date in ID)

### ID Patterns by Container

| Container | ID Format | Example | Rationale |
|-----------|-----------|---------|-----------|
| stocks | `{ticker}` | `ERIC.ST` | Ticker is unique identifier |
| daily_prices | `{ticker}_{date}` | `ERIC.ST_2026-03-10` | One price record per ticker per day |
| indicators | `{ticker}_{date}` | `ERIC.ST_2026-03-10` | One indicator snapshot per ticker per day |
| signals | `{ticker}_{date}_{strategy}` | `ERIC.ST_2026-03-10_mean-reversion` | Multiple signals per ticker per day (one per strategy) |
| scan_runs | `{timestamp}` | `2026-03-10T14:30:00Z` | One run per scan execution |

### ID Generation Functions

```python
from datetime import datetime, date

def generate_stock_id(ticker: str) -> str:
    """Generate deterministic ID for stocks container."""
    return ticker

def generate_daily_price_id(ticker: str, date: date) -> str:
    """Generate deterministic ID for daily_prices container."""
    return f"{ticker}_{date.isoformat()}"

def generate_indicator_id(ticker: str, date: date) -> str:
    """Generate deterministic ID for indicators container."""
    return f"{ticker}_{date.isoformat()}"

def generate_signal_id(ticker: str, date: date, strategy: str) -> str:
    """Generate deterministic ID for signals container."""
    # Strategy name normalized: lowercase, no spaces
    strategy_slug = strategy.lower().replace(" ", "-")
    return f"{ticker}_{date.isoformat()}_{strategy_slug}"

def generate_scan_run_id(timestamp: datetime) -> str:
    """Generate deterministic ID for scan_runs container."""
    return timestamp.isoformat()
```

---

## Base Repository Implementation

### Shared Functionality

All container repositories share common patterns:

```python
from typing import Optional, Dict, Any
from azure.cosmos import ContainerProxy, exceptions
import logging

logger = logging.getLogger(__name__)

class BaseRepository:
    """Base class for container-specific repositories."""
    
    def __init__(self, container: ContainerProxy):
        self.container = container
    
    def upsert(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or replace document (idempotent)."""
        try:
            result = self.container.upsert_item(document)
            logger.debug(f"Upserted document: {document['id']}")
            return result
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to upsert document: {document.get('id')}", exc_info=True)
            raise
    
    def read(self, doc_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Read document by ID and partition key."""
        try:
            result = self.container.read_item(item=doc_id, partition_key=partition_key)
            return result
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Document not found: {doc_id} (partition: {partition_key})")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to read document: {doc_id}", exc_info=True)
            raise
    
    def query(self, query: str, parameters: list = None, partition_key: str = None) -> list:
        """Execute parameterized query."""
        try:
            items = self.container.query_items(
                query=query,
                parameters=parameters or [],
                partition_key=partition_key,  # Single-partition query (more efficient)
                enable_cross_partition_query=(partition_key is None),
            )
            return list(items)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Query failed: {query}", exc_info=True)
            raise
```

**Key methods:**

1. **upsert():** Insert or replace (idempotent)
2. **read():** Get by ID and partition key
3. **query():** SQL query with parameters and partition key support

---

## Container-Specific Repositories

### StocksRepository

```python
from datetime import date

class StocksRepository(BaseRepository):
    """Repository for stocks container (ticker universe)."""
    
    def upsert_stock(self, ticker: str, name: str, sector: str = None, market_cap: float = None):
        """Upsert stock metadata."""
        doc_id = generate_stock_id(ticker)
        document = {
            "id": doc_id,
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "market_cap": market_cap,
            "last_updated": datetime.utcnow().isoformat(),
        }
        return self.upsert(document)
    
    def get_stock(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get stock by ticker."""
        doc_id = generate_stock_id(ticker)
        return self.read(doc_id, partition_key=ticker)
    
    def get_all_stocks(self) -> list:
        """Get all stocks in universe."""
        query = "SELECT * FROM stocks"
        return self.query(query)
```

### DailyPricesRepository

```python
class DailyPricesRepository(BaseRepository):
    """Repository for daily_prices container (OHLCV data)."""
    
    def upsert_price(self, ticker: str, date: date, open: float, high: float, low: float, 
                     close: float, volume: int, adjusted_close: float = None):
        """Upsert daily price record."""
        doc_id = generate_daily_price_id(ticker, date)
        document = {
            "id": doc_id,
            "ticker": ticker,
            "date": date.isoformat(),
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "adjusted_close": adjusted_close or close,
        }
        return self.upsert(document)
    
    def get_price(self, ticker: str, date: date) -> Optional[Dict[str, Any]]:
        """Get price for specific ticker and date."""
        doc_id = generate_daily_price_id(ticker, date)
        return self.read(doc_id, partition_key=ticker)
    
    def get_price_history(self, ticker: str, start_date: date, end_date: date) -> list:
        """Get price history for ticker in date range."""
        query = """
            SELECT * FROM daily_prices p
            WHERE p.ticker = @ticker 
              AND p.date >= @start_date 
              AND p.date <= @end_date
            ORDER BY p.date DESC
        """
        parameters = [
            {"name": "@ticker", "value": ticker},
            {"name": "@start_date", "value": start_date.isoformat()},
            {"name": "@end_date", "value": end_date.isoformat()},
        ]
        return self.query(query, parameters, partition_key=ticker)
```

### IndicatorsRepository

```python
class IndicatorsRepository(BaseRepository):
    """Repository for indicators container (calculated indicators)."""
    
    def upsert_indicators(self, ticker: str, date: date, indicators: Dict[str, float]):
        """Upsert indicator snapshot."""
        doc_id = generate_indicator_id(ticker, date)
        document = {
            "id": doc_id,
            "ticker": ticker,
            "date": date.isoformat(),
            "indicators": indicators,  # {"rsi_14": 45.2, "macd": -1.5, ...}
            "calculated_at": datetime.utcnow().isoformat(),
        }
        return self.upsert(document)
    
    def get_indicators(self, ticker: str, date: date) -> Optional[Dict[str, Any]]:
        """Get indicators for specific ticker and date."""
        doc_id = generate_indicator_id(ticker, date)
        return self.read(doc_id, partition_key=ticker)
```

### SignalsRepository

```python
class SignalsRepository(BaseRepository):
    """Repository for signals container (trading signals)."""
    
    def upsert_signal(self, ticker: str, date: date, strategy: str, signal_data: Dict[str, Any]):
        """Upsert trading signal."""
        doc_id = generate_signal_id(ticker, date, strategy)
        document = {
            "id": doc_id,
            "ticker": ticker,
            "date": date.isoformat(),
            "strategy": strategy,
            **signal_data,  # entry_price, stop_loss, target, score, etc.
            "generated_at": datetime.utcnow().isoformat(),
        }
        return self.upsert(document)
    
    def get_signals_for_date(self, scan_date: date) -> list:
        """Get all signals for a specific date (cross-partition query)."""
        query = """
            SELECT * FROM signals s
            WHERE s.date = @date
            ORDER BY s.score DESC
        """
        parameters = [{"name": "@date", "value": scan_date.isoformat()}]
        return self.query(query, parameters)  # Cross-partition (no partition_key)
```

### ScanRunsRepository

```python
class ScanRunsRepository(BaseRepository):
    """Repository for scan_runs container (scan execution metadata)."""
    
    def create_scan_run(self, timestamp: datetime, scan_mode: str, ticker_universe: str):
        """Create new scan run record."""
        doc_id = generate_scan_run_id(timestamp)
        document = {
            "id": doc_id,
            "timestamp": timestamp.isoformat(),
            "scan_mode": scan_mode,
            "ticker_universe": ticker_universe,
            "status": "running",
            "tickers_processed": 0,
            "tickers_failed": [],
            "signals_generated": 0,
        }
        return self.upsert(document)
    
    def update_scan_run(self, doc_id: str, updates: Dict[str, Any]):
        """Update scan run with results."""
        # Read existing document
        existing = self.read(doc_id, partition_key=doc_id)
        if not existing:
            raise ValueError(f"Scan run not found: {doc_id}")
        
        # Merge updates
        updated = {**existing, **updates}
        return self.upsert(updated)
    
    def get_latest_scan_run(self) -> Optional[Dict[str, Any]]:
        """Get most recent scan run."""
        query = "SELECT TOP 1 * FROM scan_runs ORDER BY scan_runs.timestamp DESC"
        results = self.query(query)
        return results[0] if results else None
```

---

## Query Patterns

### Single-Partition Queries (Efficient)

**Pattern:** Provide partition key → query scoped to single partition.

```python
# Get all prices for ERIC.ST in date range
prices = repository.daily_prices.get_price_history(
    ticker="ERIC.ST",  # Partition key
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
)
```

**Performance:** ~1-5 RU, fast (single partition read)

### Cross-Partition Queries (Expensive)

**Pattern:** No partition key provided → query scans all partitions.

```python
# Get all signals for a specific date (across all tickers)
signals = repository.signals.get_signals_for_date(scan_date=date(2026, 3, 10))
```

**Performance:** ~5-50 RU depending on data volume, slower

**When to use:** Acceptable for low-volume queries (scan results, latest run, etc.)

### Parameterized Queries (Safe)

**Always use parameters** (prevents SQL injection, optimizes query plan):

```python
# Good: Parameterized
query = "SELECT * FROM stocks WHERE stocks.sector = @sector"
parameters = [{"name": "@sector", "value": "Technology"}]
results = container.query_items(query, parameters=parameters)

# Bad: String interpolation
sector = "Technology"
query = f"SELECT * FROM stocks WHERE stocks.sector = '{sector}'"
results = container.query_items(query)  # Unsafe, no query plan caching
```

---

## Error Handling and Retries

### Transient vs Permanent Errors

**Transient (retry):**
- 429 Too Many Requests (rate limit exceeded)
- 503 Service Unavailable (temporary outage)
- Connection timeout

**Permanent (don't retry):**
- 404 Not Found (document doesn't exist)
- 400 Bad Request (invalid document schema)
- 409 Conflict (partition key mismatch)

### Retry Strategy

```python
from azure.cosmos import exceptions
import time

def upsert_with_retry(container, document, max_retries=3):
    """Upsert with exponential backoff for transient errors."""
    
    for attempt in range(max_retries):
        try:
            return container.upsert_item(document)
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 429:  # Rate limit
                retry_after = int(e.headers.get("x-ms-retry-after-ms", 1000)) / 1000
                logger.warning(f"Rate limited, retrying after {retry_after}s (attempt {attempt + 1})")
                time.sleep(retry_after)
            elif e.status_code in [503, 408]:  # Service unavailable, timeout
                backoff = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Transient error {e.status_code}, retrying after {backoff}s")
                time.sleep(backoff)
            else:
                # Permanent error, don't retry
                raise
    
    raise Exception(f"Failed after {max_retries} retries")
```

**Cosmos SDK built-in retries:**
The Python SDK automatically retries 429 errors. The above pattern is for additional control/logging.

---

## Testing Against Emulator

### Test Setup

```python
# tests/test_repository.py
import pytest
from datetime import date
from repository import CosmosRepository

@pytest.fixture
def repository():
    """Create repository connected to local emulator."""
    connection_string = "AccountEndpoint=https://localhost:8081/;AccountKey=C2y6..."
    database_name = "TestDB"
    
    repo = CosmosRepository(connection_string, database_name)
    repo.bootstrap()
    
    yield repo
    
    # Cleanup: Delete test database
    repo.client.delete_database(database_name)

def test_upsert_stock(repository):
    """Test stock upsert is idempotent."""
    # First upsert
    repository.stocks.upsert_stock(ticker="TEST.ST", name="Test Corp")
    
    # Second upsert (same ticker)
    repository.stocks.upsert_stock(ticker="TEST.ST", name="Test Corp Updated")
    
    # Verify only one document exists
    stock = repository.stocks.get_stock("TEST.ST")
    assert stock["name"] == "Test Corp Updated"

def test_daily_price_query(repository):
    """Test price history query."""
    # Insert multiple prices
    repository.daily_prices.upsert_price("ERIC.ST", date(2026, 3, 8), 100, 105, 99, 103, 1000000)
    repository.daily_prices.upsert_price("ERIC.ST", date(2026, 3, 9), 103, 106, 102, 105, 1200000)
    repository.daily_prices.upsert_price("ERIC.ST", date(2026, 3, 10), 105, 108, 104, 107, 1100000)
    
    # Query range
    prices = repository.daily_prices.get_price_history(
        ticker="ERIC.ST",
        start_date=date(2026, 3, 8),
        end_date=date(2026, 3, 10),
    )
    
    assert len(prices) == 3
    assert prices[0]["date"] == "2026-03-10"  # Ordered DESC
```

---

## Performance Considerations

### RU Consumption Patterns

| Operation | RU Cost | Notes |
|-----------|---------|-------|
| Point read (by ID + partition key) | ~1 RU | Most efficient |
| Single-partition query | ~2-5 RU | Efficient if indexed |
| Cross-partition query | ~10-50 RU | Scales with data volume |
| Upsert 1KB document | ~5 RU | Depends on document size |

**Phase 1 estimate:**
- Daily scan: 150 tickers × (fetch price ~1 RU + upsert indicator ~5 RU + upsert signal ~5 RU) ≈ 1,650 RU
- Monthly consumption: 1,650 RU × 22 trading days = 36,300 RU
- Cost: Negligible (well under 400 RU/s minimum)

### Indexing Strategy

**Default indexing:** Cosmos indexes all fields by default (convenient but expensive for writes).

**Phase 1 decision:** Use default indexing (simple, sufficient for low volume).

**Phase 2 optimization:** Custom indexing policy if write costs become significant:
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {"path": "/ticker/?"},
    {"path": "/date/?"},
    {"path": "/strategy/?"}
  ],
  "excludedPaths": [
    {"path": "/*"}
  ]
}
```

---

## Summary

### Key Decisions

1. **Repository per container** — explicit interfaces, not generic CRUD
2. **Deterministic IDs** — enable idempotent upserts (ticker_date pattern)
3. **Idempotent bootstrap** — `create_if_not_exists` for database and containers
4. **Partition key awareness** — always provide partition key for efficient queries
5. **Parameterized queries** — safe from injection, optimized query plans
6. **Retry transient errors** — handle 429 rate limits automatically
7. **Test against emulator** — validate repository logic locally

### What This Enables

- **Idempotent scans:** Re-run scan, no duplicates (deterministic IDs)
- **Clean business logic:** No Cosmos SDK details in scanner code
- **Testable:** Mock repository interface, test against emulator
- **Observable:** All operations logged with context
- **Scalable:** Partition keys chosen for efficient queries

### Next Steps

1. **Implement market data fetcher** → [21-market-data-ingestion-implementation.md](21-market-data-ingestion-implementation.md)
2. **Build indicator engine** → [22-indicator-engine-implementation.md](22-indicator-engine-implementation.md)
3. **Test repository locally** → [25-local-development-workflow.md](25-local-development-workflow.md)

---

## References

- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/sdk-python)
- [Cosmos DB partition keys](https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview)
- [Cosmos DB indexing policies](https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy)
- [13-data-model-design.md](13-data-model-design.md) — Complete schema definitions
- [11-azure-cosmos-db-evaluation.md](11-azure-cosmos-db-evaluation.md) — SDK usage and pricing
