# 19 - Python Scanner Bootstrap Implementation

> Research date: 2026-03-10
> Goal: Define the startup sequence, configuration loading, environment validation, and structured logging for the Python scanner that runs under Aspire orchestration.
> Prerequisites: [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md), [15-security-and-secrets-management.md](15-security-and-secrets-management.md), [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md)

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Configuration Contract](#configuration-contract)
4. [Config Loading Strategy](#config-loading-strategy)
5. [Validation and Fail-Fast](#validation-and-fail-fast)
6. [Structured Logging Setup](#structured-logging-setup)
7. [Startup Sequence](#startup-sequence)
8. [Entry Point Design](#entry-point-design)
9. [Error Handling and Exit Codes](#error-handling-and-exit-codes)
10. [Testing Strategy](#testing-strategy)

---

## Overview

The scanner bootstrap is the **foundation layer** that runs before any business logic. Its responsibilities:

1. **Load configuration** from environment variables (injected by Aspire)
2. **Validate configuration** — fail fast if required values missing or invalid
3. **Setup structured logging** — JSON format for production, human-readable for local dev
4. **Report readiness** — log successful startup for Aspire dashboard visibility
5. **Handle errors gracefully** — clear error messages, appropriate exit codes

**Design principles:**
- **Fail fast:** Invalid config should crash immediately with clear error message
- **No magic:** All configuration explicit in environment variables (no defaults for secrets)
- **Observable:** Every startup step logged at INFO level
- **Testable:** Config and logging setup isolated from business logic

---

## Project Structure

### Scanner Directory Layout

```
src/Scanner/
├── main.py                    # Entry point, orchestrates bootstrap → scan
├── config.py                  # Configuration dataclass and validation
├── logging_config.py          # Logging setup (JSON vs human-readable)
├── requirements.txt           # Python dependencies
├── scanner/                   # Business logic package
│   ├── __init__.py
│   ├── repository.py          # Cosmos repository (see file 20)
│   ├── fetcher.py             # Market data ingestion (see file 21)
│   ├── indicators.py          # Indicator engine (see file 22)
│   ├── signals.py             # Signal engine (see file 23)
│   └── notifier.py            # Telegram notifications (see file 24)
└── tests/
    ├── test_config.py         # Config validation tests
    └── test_logging.py        # Logging setup tests
```

**Key separation:**
- `main.py`: Startup orchestration only (bootstrap → execute)
- `config.py`: Configuration loading and validation
- `logging_config.py`: Logging infrastructure
- `scanner/`: Business logic (completely decoupled from bootstrap)

---

## Configuration Contract

### Environment Variables

These are injected by Aspire (see [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md)):

| Variable | Type | Required | Default | Validation |
|----------|------|----------|---------|------------|
| `COSMOS_CONNECTION_STRING` | str | Yes | - | Must start with "AccountEndpoint=" |
| `COSMOS_DATABASE_NAME` | str | Yes | - | Non-empty string |
| `LOG_LEVEL` | str | No | INFO | Must be DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | str | No | human | Must be "json" or "human" |
| `TELEGRAM_BOT_TOKEN` | str | Yes | - | Format: `<digits>:<alphanumeric>` |
| `TELEGRAM_CHAT_ID` | str | Yes | - | Numeric string or @username |
| `SCAN_MODE` | str | No | daily | Must be "daily" or "continuous" |
| `TICKER_UNIVERSE` | str | No | omx_large_cap | Must be valid universe name |
| `DRY_RUN` | str | No | false | Must be "true" or "false" |

### Configuration Dataclass

**Design pattern:** Use Python dataclass with type hints and validation.

```python
from dataclasses import dataclass
from typing import Literal
import os
import re

@dataclass(frozen=True)
class ScannerConfig:
    """Immutable configuration for SwingTrader scanner."""
    
    # Cosmos DB
    cosmos_connection_string: str
    cosmos_database_name: str
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    log_format: Literal["json", "human"]
    
    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Scan behavior
    scan_mode: Literal["daily", "continuous"]
    ticker_universe: str
    dry_run: bool
    
    @classmethod
    def from_environment(cls) -> "ScannerConfig":
        """Load and validate config from environment variables."""
        
        # Required fields with no defaults
        cosmos_connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
        if not cosmos_connection_string:
            raise ValueError("COSMOS_CONNECTION_STRING is required")
        if not cosmos_connection_string.startswith("AccountEndpoint="):
            raise ValueError("COSMOS_CONNECTION_STRING must start with 'AccountEndpoint='")
        
        cosmos_database_name = os.environ.get("COSMOS_DATABASE_NAME")
        if not cosmos_database_name:
            raise ValueError("COSMOS_DATABASE_NAME is required")
        
        telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', telegram_bot_token):
            raise ValueError("TELEGRAM_BOT_TOKEN format invalid (expected: <digits>:<alphanumeric>)")
        
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if not telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        
        # Optional fields with defaults
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"LOG_LEVEL must be DEBUG, INFO, WARNING, or ERROR (got: {log_level})")
        
        log_format = os.environ.get("LOG_FORMAT", "human").lower()
        if log_format not in ["json", "human"]:
            raise ValueError(f"LOG_FORMAT must be 'json' or 'human' (got: {log_format})")
        
        scan_mode = os.environ.get("SCAN_MODE", "daily").lower()
        if scan_mode not in ["daily", "continuous"]:
            raise ValueError(f"SCAN_MODE must be 'daily' or 'continuous' (got: {scan_mode})")
        
        ticker_universe = os.environ.get("TICKER_UNIVERSE", "omx_large_cap")
        
        dry_run_str = os.environ.get("DRY_RUN", "false").lower()
        if dry_run_str not in ["true", "false"]:
            raise ValueError(f"DRY_RUN must be 'true' or 'false' (got: {dry_run_str})")
        dry_run = dry_run_str == "true"
        
        return cls(
            cosmos_connection_string=cosmos_connection_string,
            cosmos_database_name=cosmos_database_name,
            log_level=log_level,
            log_format=log_format,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            scan_mode=scan_mode,
            ticker_universe=ticker_universe,
            dry_run=dry_run,
        )
```

**Key design choices:**

1. **Frozen dataclass:** Immutable config (cannot be modified after creation)
2. **Type hints:** Clear expectations for each field
3. **Validation in constructor:** Fail fast on invalid values
4. **Class method factory:** `from_environment()` encapsulates loading logic
5. **Clear error messages:** ValueError with specific problem (not generic "config invalid")

### Why No .env File?

**In production (Aspire):** Environment variables injected directly → no file needed.

**In local development:** Use `.env` file with python-dotenv for non-Aspire runs:

```python
# Optional: Load .env if running outside Aspire
from dotenv import load_dotenv
load_dotenv()  # Reads .env file into os.environ

config = ScannerConfig.from_environment()
```

**Phase 1 decision:** Skip .env file loading in `main.py` (Aspire provides all vars). Add .env support in Phase 2 for standalone runs.

---

## Config Loading Strategy

### Bootstrap Sequence

```python
# main.py
import sys
import logging
from config import ScannerConfig
from logging_config import setup_logging

def main():
    # Step 1: Load config (fail fast if invalid)
    try:
        config = ScannerConfig.from_environment()
    except ValueError as e:
        # Can't use logger yet (not configured)
        print(f"ERROR: Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 2: Setup logging (now we know log level and format)
    setup_logging(config.log_level, config.log_format)
    logger = logging.getLogger(__name__)
    
    # Step 3: Log successful config load
    logger.info("Scanner configuration loaded successfully", extra={
        "cosmos_database": config.cosmos_database_name,
        "scan_mode": config.scan_mode,
        "ticker_universe": config.ticker_universe,
        "dry_run": config.dry_run,
    })
    
    # Step 4: Proceed to scanner logic
    # ... (see Startup Sequence section)

if __name__ == "__main__":
    main()
```

**Order matters:**
1. Load config first (no logging available yet if this fails)
2. Setup logging using config (now we know log level)
3. Log config validation success (for observability)

---

## Validation and Fail-Fast

### Validation Principles

1. **Validate at startup, not at use**
   - Bad: Check if Cosmos connection string is valid when first query runs
   - Good: Validate connection string format immediately on load

2. **Explicit validation rules**
   - Don't just check "not empty"
   - Check format, allowed values, type constraints

3. **Clear error messages**
   - Bad: "Invalid config"
   - Good: "TELEGRAM_BOT_TOKEN format invalid (expected: <digits>:<alphanumeric>)"

### Validation Patterns

**Format validation:**
```python
# Cosmos connection string must have specific format
if not value.startswith("AccountEndpoint="):
    raise ValueError("COSMOS_CONNECTION_STRING must start with 'AccountEndpoint='")

# Telegram token has known format: numeric ID + colon + secret
if not re.match(r'^\d+:[A-Za-z0-9_-]+$', value):
    raise ValueError("TELEGRAM_BOT_TOKEN format invalid")
```

**Enum validation:**
```python
# LOG_LEVEL must be one of specific values
if value not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
    raise ValueError(f"LOG_LEVEL must be DEBUG, INFO, WARNING, or ERROR (got: {value})")
```

**Type conversion with validation:**
```python
# DRY_RUN is string "true"/"false", convert to bool
if value not in ["true", "false"]:
    raise ValueError(f"DRY_RUN must be 'true' or 'false' (got: {value})")
dry_run = value == "true"
```

### Exit Codes

**Exit code 1:** Configuration validation failed
- Aspire dashboard shows "Exited (1)"
- User checks logs, sees clear error message
- Fix config, restart scanner

**Why this matters:**
- Distinguishes config problems (user error) from runtime problems (bugs)
- Aspire can differentiate between "misconfigured" and "crashed"

---

## Structured Logging Setup

### Logging Design Goals

1. **JSON format in production** — machine-parseable for log aggregation (Azure Log Analytics, etc.)
2. **Human-readable format in local development** — easy to read in Aspire dashboard
3. **Structured context** — attach metadata to log messages (ticker, strategy, duration, etc.)
4. **Appropriate levels** — DEBUG for detailed tracing, INFO for key events, WARNING for recoverable errors, ERROR for failures

### Logging Configuration

```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(level: str, format_type: str):
    """Configure Python logging with structured output.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format_type: "json" for production, "human" for development
    """
    
    log_level = getattr(logging, level)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if format_type == "json":
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("azure.core").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### Structured Logging Usage

**Basic logging:**
```python
logger = logging.getLogger(__name__)
logger.info("Market data fetched successfully")
```

**With context (JSON-friendly):**
```python
logger.info("Market data fetched", extra={
    "ticker_count": 150,
    "duration_seconds": 12.5,
    "failed_tickers": ["ERIC.ST", "ABB.ST"],
})
```

**Output in JSON format:**
```json
{
  "asctime": "2026-03-10T14:32:15",
  "name": "scanner.fetcher",
  "levelname": "INFO",
  "message": "Market data fetched",
  "ticker_count": 150,
  "duration_seconds": 12.5,
  "failed_tickers": ["ERIC.ST", "ABB.ST"]
}
```

**Output in human format:**
```
2026-03-10 14:32:15 [INFO] scanner.fetcher: Market data fetched
```

**Why extra dict?**
- Fields in `extra` are merged into JSON log record
- Easy to query in log aggregation tools: `ticker_count > 100`
- Human format just shows message (no clutter)

### Log Levels Guide

| Level | Use Cases |
|-------|-----------|
| DEBUG | Variable values, iteration progress, retry attempts, detailed flow |
| INFO | Key events: scan started, data fetched, signals generated, scan completed |
| WARNING | Recoverable errors: ticker fetch failed, indicator calc skipped due to missing data |
| ERROR | Unrecoverable errors: Cosmos connection failed, Telegram send failed, scan aborted |

**Example:**
```python
logger.debug(f"Fetching ticker {ticker}")
logger.info("Market data ingestion completed", extra={"duration_seconds": 15})
logger.warning(f"Ticker {ticker} skipped: insufficient history")
logger.error("Failed to connect to Cosmos DB", exc_info=True)
```

---

## Startup Sequence

### Complete Bootstrap Flow

```python
# main.py
import sys
import logging
from config import ScannerConfig
from logging_config import setup_logging
from scanner.repository import CosmosRepository
from scanner.orchestrator import ScanOrchestrator

def main():
    """Scanner entry point."""
    
    # Phase 1: Load and validate configuration
    try:
        config = ScannerConfig.from_environment()
    except ValueError as e:
        print(f"ERROR: Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Phase 2: Setup logging
    setup_logging(config.log_level, config.log_format)
    logger = logging.getLogger(__name__)
    
    logger.info("SwingTrader scanner starting", extra={
        "version": "1.0.0",  # Could read from __version__
        "scan_mode": config.scan_mode,
    })
    
    # Phase 3: Initialize Cosmos repository (with retry)
    try:
        repository = CosmosRepository(
            connection_string=config.cosmos_connection_string,
            database_name=config.cosmos_database_name,
        )
        repository.bootstrap()  # Create containers if missing
        logger.info("Cosmos DB connection established")
    except Exception as e:
        logger.error("Failed to initialize Cosmos DB", exc_info=True)
        sys.exit(2)
    
    # Phase 4: Create orchestrator (wires all components)
    try:
        orchestrator = ScanOrchestrator(config, repository)
        logger.info("Scanner components initialized")
    except Exception as e:
        logger.error("Failed to initialize scanner components", exc_info=True)
        sys.exit(3)
    
    # Phase 5: Execute scan (or enter continuous mode)
    try:
        if config.scan_mode == "daily":
            logger.info("Executing daily scan")
            orchestrator.run_daily_scan()
            logger.info("Daily scan completed successfully")
        else:
            logger.info("Entering continuous mode (not implemented in Phase 1)")
            # Future: Schedule scans, listen for triggers, etc.
    except Exception as e:
        logger.error("Scan execution failed", exc_info=True)
        sys.exit(4)
    
    logger.info("Scanner shutting down gracefully")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Key Observations

**Distinct phases:**
1. Config load (exit 1 if fails)
2. Logging setup (uses config)
3. Cosmos init (exit 2 if fails)
4. Component init (exit 3 if fails)
5. Scan execution (exit 4 if fails)

**Why separate exit codes:**
- Aspire dashboard shows exit code
- Different codes help diagnose failure point
- 0 = success, 1 = config, 2 = cosmos, 3 = components, 4 = scan

**Exception handling:**
- Each phase has try/except
- Log error with full traceback (`exc_info=True`)
- Exit with appropriate code

---

## Entry Point Design

### main() Function Responsibilities

**What main() does:**
- Orchestrate startup phases
- Handle top-level errors
- Set exit codes
- Log lifecycle events (start, shutdown)

**What main() does NOT do:**
- Business logic (that's in `scanner/` package)
- Detailed error handling (components handle their own errors)
- Configuration defaults (that's in `ScannerConfig`)

### Orchestrator Pattern

**Why separate orchestrator:**
- `main()` is infrastructure (startup, shutdown)
- `ScanOrchestrator` is business logic (what to scan, when, how)
- Clear boundary between "running the app" and "doing the work"

**ScanOrchestrator interface:**
```python
class ScanOrchestrator:
    def __init__(self, config: ScannerConfig, repository: CosmosRepository):
        self.config = config
        self.repository = repository
        self.fetcher = MarketDataFetcher(config, repository)
        self.indicator_engine = IndicatorEngine(config, repository)
        self.signal_engine = SignalEngine(config, repository)
        self.notifier = TelegramNotifier(config)
    
    def run_daily_scan(self):
        """Execute one complete scan: fetch → indicators → signals → notify."""
        # Detailed implementation in files 21-24
        pass
```

---

## Error Handling and Exit Codes

### Exit Code Convention

| Code | Meaning | Cause | User Action |
|------|---------|-------|-------------|
| 0 | Success | Scan completed without errors | None |
| 1 | Config validation failed | Missing/invalid environment variable | Fix config in Aspire AppHost, restart |
| 2 | Cosmos connection failed | Emulator not running, bad connection string | Check Cosmos emulator status, verify connection string |
| 3 | Component initialization failed | Missing dependencies, code error | Check logs for specific component error |
| 4 | Scan execution failed | Data fetch error, indicator calc error, etc. | Check logs for specific scan step failure |

### Error Context in Logs

**Bad error log:**
```python
logger.error("Scan failed")
```

**Good error log:**
```python
logger.error("Market data fetch failed", extra={
    "ticker": "ERIC.ST",
    "error_type": "ConnectionTimeout",
    "attempt": 3,
    "max_retries": 3,
}, exc_info=True)
```

**Why:**
- `extra` dict provides structured context (queryable in logs)
- `exc_info=True` includes full stack trace
- User can pinpoint exact failure point

---

## Testing Strategy

### Config Validation Tests

```python
# tests/test_config.py
import pytest
from config import ScannerConfig

def test_from_environment_valid(monkeypatch):
    """Test config loads with all valid environment variables."""
    monkeypatch.setenv("COSMOS_CONNECTION_STRING", "AccountEndpoint=https://localhost:8081/;...")
    monkeypatch.setenv("COSMOS_DATABASE_NAME", "SwingTraderDB")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")
    
    config = ScannerConfig.from_environment()
    
    assert config.cosmos_database_name == "SwingTraderDB"
    assert config.scan_mode == "daily"  # default
    assert config.dry_run is False  # default

def test_from_environment_missing_required(monkeypatch):
    """Test config raises ValueError if required var missing."""
    # Don't set COSMOS_CONNECTION_STRING
    monkeypatch.setenv("COSMOS_DATABASE_NAME", "SwingTraderDB")
    
    with pytest.raises(ValueError, match="COSMOS_CONNECTION_STRING is required"):
        ScannerConfig.from_environment()

def test_from_environment_invalid_format(monkeypatch):
    """Test config raises ValueError if format invalid."""
    monkeypatch.setenv("COSMOS_CONNECTION_STRING", "invalid")
    monkeypatch.setenv("COSMOS_DATABASE_NAME", "SwingTraderDB")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")
    
    with pytest.raises(ValueError, match="must start with 'AccountEndpoint='"):
        ScannerConfig.from_environment()
```

### Logging Setup Tests

```python
# tests/test_logging.py
import logging
from logging_config import setup_logging

def test_setup_logging_json_format():
    """Test JSON formatter applied in json mode."""
    setup_logging("INFO", "json")
    logger = logging.getLogger("test")
    
    # Verify handler has JSON formatter
    handler = logger.handlers[0]
    assert "JsonFormatter" in str(type(handler.formatter))

def test_setup_logging_human_format():
    """Test human formatter applied in human mode."""
    setup_logging("INFO", "human")
    logger = logging.getLogger("test")
    
    handler = logger.handlers[0]
    assert "Formatter" in str(type(handler.formatter))
```

### Integration Test (End-to-End Bootstrap)

```python
# tests/test_bootstrap.py
import subprocess
import os

def test_scanner_bootstrap_success():
    """Test scanner starts successfully with valid config."""
    env = os.environ.copy()
    env.update({
        "COSMOS_CONNECTION_STRING": "AccountEndpoint=https://localhost:8081/;...",
        "COSMOS_DATABASE_NAME": "TestDB",
        "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234",
        "TELEGRAM_CHAT_ID": "987654321",
        "DRY_RUN": "true",  # Don't actually fetch data or send Telegram
    })
    
    # Run scanner (should exit 0 if bootstrap succeeds)
    result = subprocess.run(
        ["python", "main.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "Scanner configuration loaded successfully" in result.stdout
```

---

## Summary

### Key Decisions

1. **Dataclass for config** — type-safe, immutable, validation built-in
2. **from_environment() factory** — encapsulates loading logic
3. **Fail fast on invalid config** — exit code 1, clear error message
4. **Structured logging** — JSON for production, human-readable for dev
5. **Distinct startup phases** — config → logging → cosmos → components → scan
6. **Exit codes for observability** — 0 = success, 1-4 = specific failures
7. **Orchestrator pattern** — separate startup (main.py) from business logic (orchestrator)

### What This Enables

- **Aspire observability:** Clear logs in dashboard, exit codes distinguish failure types
- **Production-ready:** JSON logs integrate with Azure Log Analytics
- **Developer-friendly:** Human-readable logs, clear error messages, fast iteration
- **Testable:** Config and logging setup isolated, easy to unit test

### Next Steps

1. **Implement Cosmos repository** → [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md)
2. **Build scan orchestrator** → Wires fetcher, indicator engine, signal engine (files 21-23)
3. **Test end-to-end locally** → [25-local-development-workflow.md](25-local-development-workflow.md)

---

## References

- [Python logging documentation](https://docs.python.org/3/library/logging.html)
- [python-json-logger](https://github.com/madzak/python-json-logger) — JSON formatter for Python logging
- [dataclasses](https://docs.python.org/3/library/dataclasses.html) — Immutable config classes
- [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md) — Environment variable contract
- [15-security-and-secrets-management.md](15-security-and-secrets-management.md) — Secrets strategy
