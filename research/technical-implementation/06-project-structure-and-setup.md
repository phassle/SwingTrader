# 06 - Project Structure and Setup

How to organize the SwingTrader codebase, manage dependencies, and set up a clean development environment from day one.

---

## 1. Recommended Project Structure

```
SwingTrader/
├── research/                    # Research and documentation
│   ├── strategy-and-theory/
│   └── technical-implementation/
├── src/                         # Application source code
│   ├── __init__.py
│   ├── main.py                  # Entry point - daily scan
│   ├── config.py                # Configuration (tickers, thresholds, API keys)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py           # yfinance data fetching
│   │   ├── cleaner.py           # Data validation and cleaning
│   │   └── store.py             # SQLite storage layer
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── calculator.py        # Indicator calculation via pandas-ta
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py              # Base strategy class
│   │   ├── mean_reversion.py    # RSI + Bollinger strategy
│   │   ├── macd_crossover.py    # MACD trend strategy
│   │   ├── breakout.py          # Volume breakout strategy
│   │   └── pullback.py          # MA pullback strategy
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── scorer.py            # Setup quality scoring
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── telegram.py          # Telegram bot notifications
│   └── utils/
│       ├── __init__.py
│       ├── market_calendar.py   # Swedish trading calendar
│       └── logging_config.py    # Logging setup
├── backtest/
│   ├── __init__.py
│   └── runner.py                # Backtesting framework
├── data/                        # Data directory (gitignored)
│   └── swingtrader.db           # SQLite database
├── tests/
│   ├── __init__.py
│   ├── test_strategies.py
│   ├── test_indicators.py
│   ├── test_fetcher.py
│   └── test_scorer.py
├── .env.example                 # Environment variable template
├── .gitignore
├── .dockerignore                # Files excluded from Docker build
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Local Docker testing setup
├── pyproject.toml               # Dependencies and project config
└── README.md
```

### Component Responsibilities

**`src/main.py`** - The daily entry point. Orchestrates the full pipeline: fetch data, calculate indicators, run strategies, score setups, send notifications. This is what cron calls every evening.

**`src/config.py`** - Single source of truth for all configurable values: ticker lists, strategy thresholds (RSI levels, Bollinger band widths), scoring weights, file paths. Loads secrets from `.env`, exposes everything else as module-level constants.

**`src/data/fetcher.py`** - Wraps yfinance to download OHLCV data for Swedish stocks. Handles the `.ST` suffix for Stockholm-listed tickers, manages rate limiting, and returns clean DataFrames.

**`src/data/cleaner.py`** - Validates fetched data: checks for missing dates, fills or flags gaps, removes stocks with insufficient history, ensures data types are correct. Bad data in means bad signals out.

**`src/data/store.py`** - SQLite interface for persisting price data and scan results. Avoids re-downloading data that already exists. Stores historical signals for performance tracking.

**`src/indicators/calculator.py`** - Thin wrapper around pandas-ta. Given a DataFrame of OHLCV data, computes RSI, MACD, Bollinger Bands, moving averages, ATR, and volume metrics. Returns the enriched DataFrame.

**`src/strategies/base.py`** - Abstract base class that all strategies inherit from. Defines the interface: `scan(df) -> list[Signal]`. This ensures every strategy is pluggable and testable in isolation.

**`src/strategies/mean_reversion.py`** through **`pullback.py`** - Each strategy implements one specific pattern detection. They receive indicator-enriched data and return signals when conditions are met.

**`src/scoring/scorer.py`** - Takes raw signals from strategies and assigns quality scores based on multiple factors (trend alignment, volume confirmation, proximity to support). Higher score = higher conviction setup.

**`src/notifications/telegram.py`** - Formats scan results into readable messages and sends them via Telegram Bot API. Handles message length limits, retry on failure, and error alerting.

**`src/utils/market_calendar.py`** - Knows when the Stockholm Stock Exchange is open. Prevents running scans on weekends and Swedish holidays. Used by cron logic to skip non-trading days.

**`src/utils/logging_config.py`** - Configures Python logging for the entire application. Sets up file and console handlers with appropriate formats and levels.

**`backtest/runner.py`** - Runs strategies against historical data to validate performance. Calculates win rate, average return, max drawdown. Used during strategy development, not in production scans.

**`data/`** - Runtime data directory. Contains the SQLite database and any cached files. Entirely gitignored; recreated on first run.

**`tests/`** - Unit and integration tests. Every strategy gets tested with known data to verify it produces expected signals.

---

## 2. Dependency Management

### pyproject.toml

Use `pyproject.toml` as the single source for project metadata, dependencies, and tool configuration. This is the modern standard, replacing `setup.py` and `requirements.txt`.

For installing dependencies, use **uv** - it is dramatically faster than pip and handles virtual environments cleanly.

```toml
[project]
name = "swingtrader"
version = "0.1.0"
description = "Swing trading scanner for Swedish stocks"
requires-python = ">=3.11"

dependencies = [
    "yfinance>=0.2.36",
    "pandas>=2.2.0",
    "pandas-ta>=0.3.14b1",
    "python-telegram-bot>=21.0",
    "python-dotenv>=1.0.0",
    "schedule>=1.2.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.3.0",
]

[project.scripts]
swingtrader = "src.main:main"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # bugbear
    "UP",   # pyupgrade
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

### Installing with uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Why These Dependencies

| Package | Purpose | Why This One |
|---------|---------|-------------|
| yfinance | Market data | Free, covers Stockholm stocks via Yahoo Finance |
| pandas | Data manipulation | Industry standard for tabular data |
| pandas-ta | Technical indicators | 130+ indicators, works directly on DataFrames |
| python-telegram-bot | Notifications | Official Telegram library, async support |
| python-dotenv | Secret management | Simple .env file loading |
| schedule | Job scheduling | Lightweight, human-readable scheduling syntax |
| requests | HTTP calls | For any API calls beyond yfinance |
| pytest | Testing | Standard Python test framework |
| ruff | Linting + formatting | Fast, replaces flake8 + isort + black |

---

## 3. Configuration Management

### config.py

Everything configurable lives here. Strategy parameters are tunable without touching strategy code.

```python
"""
Application configuration.

Loads secrets from .env file and defines all tunable parameters
for strategies, scoring, and notifications.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "swingtrader.db"
LOG_DIR = PROJECT_ROOT / "logs"

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Data Fetching ---
# Swedish Large Cap + Mid Cap tickers (Yahoo Finance format)
TICKERS = [
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-A.ST", "ATCO-B.ST",
    "AZN.ST", "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST",
    "EVO.ST", "GETI-B.ST", "HEXA-B.ST", "HM-B.ST", "INVE-B.ST",
    "KINV-B.ST", "LUND-B.ST", "NIBE-B.ST", "SAND.ST", "SBB-B.ST",
    "SCA-B.ST", "SEB-A.ST", "SHB-A.ST", "SKA-B.ST", "SKF-B.ST",
    "SSAB-A.ST", "SWED-A.ST", "SWMA.ST", "TEL2-B.ST", "TELIA.ST",
    "VOLV-B.ST",
]

# How many days of history to fetch for indicator calculation
LOOKBACK_DAYS = 365

# Pause between API calls to avoid rate limiting (seconds)
FETCH_DELAY = 0.5

# --- Strategy Parameters ---
STRATEGY_PARAMS = {
    "mean_reversion": {
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "bb_period": 20,
        "bb_std": 2.0,
    },
    "macd_crossover": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
    },
    "breakout": {
        "volume_multiplier": 2.0,      # Volume must be 2x the 20-day average
        "price_change_threshold": 0.02,  # Minimum 2% price move
        "consolidation_days": 10,        # Days of low volatility before breakout
    },
    "pullback": {
        "ma_period": 50,
        "pullback_threshold": 0.03,      # Within 3% of the MA
        "trend_ma_period": 200,          # Must be above 200 MA for uptrend
    },
}

# --- Scoring ---
SCORING_WEIGHTS = {
    "trend_alignment": 0.25,
    "volume_confirmation": 0.20,
    "rsi_position": 0.15,
    "proximity_to_support": 0.15,
    "multi_strategy_agreement": 0.15,
    "risk_reward_ratio": 0.10,
}

# Minimum score (0-100) to include in notifications
MIN_SCORE_THRESHOLD = 60

# --- Scheduling ---
# When to run the daily scan (Stockholm time, after market close)
SCAN_TIME = "18:30"
```

### .env.example

```env
# Telegram Bot Configuration
# Create a bot via @BotFather on Telegram to get these values
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here

# Optional: Override default paths
# DATA_DIR=/path/to/custom/data/dir
# LOG_DIR=/path/to/custom/log/dir
```

### How Config Flows Through the App

1. `.env` holds secrets (tokens, keys) - never committed to git.
2. `config.py` loads `.env` and defines all parameters as module constants.
3. Strategy classes receive their specific parameters from `STRATEGY_PARAMS`.
4. To tune a strategy, edit `config.py` and re-run. No code changes needed.

---

## 4. Logging Setup

### logging_config.py

```python
"""
Logging configuration for SwingTrader.

Sets up dual output: console (INFO+) and rotating file (DEBUG+).
Call setup_logging() once at application startup.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: Path, level: int = logging.DEBUG) -> None:
    """Configure application-wide logging.

    Args:
        log_dir: Directory to store log files. Created if it does not exist.
        level: Root logger level. Defaults to DEBUG.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "swingtrader.log"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Prevent duplicate handlers on repeated calls
    root_logger.handlers.clear()

    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)

    # File handler - DEBUG and above, rotating at 5 MB, keep 3 backups
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use __name__ as the argument.

    Example:
        logger = get_logger(__name__)
        logger.info("Scanning %d tickers", len(tickers))
    """
    return logging.getLogger(name)
```

### Using It

```python
# In main.py
from src.utils.logging_config import setup_logging, get_logger
from src.config import LOG_DIR

setup_logging(LOG_DIR)
logger = get_logger(__name__)

logger.info("Starting daily scan for %d tickers", len(TICKERS))

# In any other module
from src.utils.logging_config import get_logger
logger = get_logger(__name__)

logger.debug("Fetching data for %s", ticker)      # Only in log file
logger.info("Found 3 setups above threshold")      # Console + file
logger.warning("Missing data for KINV-B.ST")       # Data quality issue
logger.error("Telegram send failed: %s", str(e))   # Something broke
```

### Log Level Guidelines

| Level | When to Use | Example |
|-------|------------|---------|
| DEBUG | Detailed execution flow | "Calculating RSI for ABB.ST with period=14" |
| INFO | Normal operations worth noting | "Scan complete: 5 setups found" |
| WARNING | Something unexpected but recoverable | "Ticker SBB-B.ST returned only 30 days of data" |
| ERROR | Something failed | "Failed to send Telegram notification" |
| CRITICAL | Application cannot continue | "Database file is corrupted" |

---

## 5. Error Handling Patterns

### What Can Go Wrong

1. **Network failures** - yfinance API is down or your server has no internet.
2. **API rate limiting** - Too many requests in a short period.
3. **Bad data** - Missing OHLCV fields, NaN values, stock delisted.
4. **Missing tickers** - A ticker in the config no longer exists.
5. **Telegram failures** - Bot token expired, chat not found.
6. **Database corruption** - SQLite file locked or corrupted.

### Retry Logic for Network Calls

```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """Decorator that retries a function on exception.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiply delay by this factor after each retry.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            "%s failed (attempt %d/%d): %s. Retrying in %.1fs",
                            func.__name__, attempt, max_attempts, e, current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, e,
                        )

            raise last_exception

        return wrapper
    return decorator
```

### Graceful Degradation in the Scanner

```python
def run_scan(tickers: list[str]) -> list[Signal]:
    """Scan all tickers. If individual tickers fail, skip them and continue."""
    all_signals = []
    failed_tickers = []

    for ticker in tickers:
        try:
            df = fetch_data(ticker)
            df = calculate_indicators(df)
            signals = run_strategies(df, ticker)
            all_signals.extend(signals)
        except Exception as e:
            logger.error("Failed to process %s: %s", ticker, e)
            failed_tickers.append(ticker)
            continue

    if failed_tickers:
        logger.warning(
            "Scan completed with %d failures: %s",
            len(failed_tickers),
            ", ".join(failed_tickers),
        )

    return all_signals
```

### Error Alerting via Telegram

```python
def run_daily_scan():
    """Top-level function called by the scheduler."""
    try:
        signals = run_scan(TICKERS)
        scored = score_signals(signals)
        send_results(scored)
        logger.info("Daily scan completed successfully")
    except Exception as e:
        logger.critical("Daily scan failed: %s", e, exc_info=True)
        try:
            send_error_alert(f"SwingTrader scan failed: {e}")
        except Exception:
            logger.critical("Could not send error alert via Telegram")
```

### Key Principles

- **Never let one stock kill the entire scan.** Wrap individual ticker processing in try/except.
- **Always log the error before retrying.** You need to know what is failing.
- **Send yourself an alert when the whole scan fails.** You want to know the same day, not a week later when you notice you have not received signals.
- **Use exponential backoff for retries.** Starting at 2 seconds, then 4, then 8. This respects rate limits.

---

## 6. Testing Strategy

### What to Test

| Test Type | What It Covers | Example |
|-----------|---------------|---------|
| Unit tests | Individual functions in isolation | Given OHLCV data with RSI=25, mean_reversion should produce a BUY signal |
| Integration tests | Multi-component pipelines | Fetch real data for one ticker, calculate indicators, verify DataFrame shape |
| Backtest validation | Strategy performance on historical data | Mean reversion on ABB.ST over 2 years: win rate, avg return |

### pytest Setup

The `pyproject.toml` already configures pytest (see section 2). Tests live in `tests/` and follow the naming convention `test_*.py`.

### Example Unit Tests

```python
# tests/test_strategies.py

import pandas as pd
import pytest
from src.strategies.mean_reversion import MeanReversionStrategy


@pytest.fixture
def oversold_data() -> pd.DataFrame:
    """Create synthetic data where RSI is oversold and price is below lower BB."""
    return pd.DataFrame({
        "close": [100, 98, 95, 92, 88, 85, 83, 80, 78, 76],
        "rsi_14": [45, 40, 38, 35, 32, 30, 28, 25, 23, 22],
        "bb_lower": [82, 82, 82, 82, 82, 82, 82, 82, 82, 82],
        "bb_mid": [90, 90, 90, 90, 90, 90, 90, 90, 90, 90],
        "bb_upper": [98, 98, 98, 98, 98, 98, 98, 98, 98, 98],
        "volume": [100000] * 10,
        "sma_200": [85] * 10,
    })


@pytest.fixture
def neutral_data() -> pd.DataFrame:
    """Create synthetic data with no clear signal."""
    return pd.DataFrame({
        "close": [90, 91, 90, 91, 90, 91, 90, 91, 90, 91],
        "rsi_14": [50, 51, 50, 51, 50, 51, 50, 51, 50, 51],
        "bb_lower": [85, 85, 85, 85, 85, 85, 85, 85, 85, 85],
        "bb_mid": [90, 90, 90, 90, 90, 90, 90, 90, 90, 90],
        "bb_upper": [95, 95, 95, 95, 95, 95, 95, 95, 95, 95],
        "volume": [100000] * 10,
        "sma_200": [85] * 10,
    })


class TestMeanReversionStrategy:
    def setup_method(self):
        self.strategy = MeanReversionStrategy(
            rsi_oversold=30,
            bb_period=20,
            bb_std=2.0,
        )

    def test_generates_signal_when_oversold(self, oversold_data):
        signals = self.strategy.scan(oversold_data, ticker="TEST.ST")
        assert len(signals) >= 1
        assert signals[0].direction == "BUY"
        assert signals[0].strategy_name == "mean_reversion"

    def test_no_signal_when_neutral(self, neutral_data):
        signals = self.strategy.scan(neutral_data, ticker="TEST.ST")
        assert len(signals) == 0

    def test_signal_includes_metadata(self, oversold_data):
        signals = self.strategy.scan(oversold_data, ticker="ABB.ST")
        if signals:
            signal = signals[0]
            assert signal.ticker == "ABB.ST"
            assert signal.entry_price > 0
            assert signal.stop_loss > 0
            assert signal.stop_loss < signal.entry_price
```

### Example Integration Test

```python
# tests/test_fetcher.py

import pytest
from src.data.fetcher import fetch_ticker_data


@pytest.mark.integration
class TestFetcher:
    def test_fetches_valid_ticker(self):
        """Fetch real data for a well-known stock. Requires internet."""
        df = fetch_ticker_data("ABB.ST", days=30)
        assert len(df) > 15  # Roughly 20 trading days in a month
        assert "close" in df.columns
        assert "volume" in df.columns
        assert df["close"].notna().all()

    def test_handles_invalid_ticker(self):
        """Invalid ticker should raise or return empty, not crash."""
        with pytest.raises(ValueError):
            fetch_ticker_data("DOESNOTEXIST123.ST", days=30)
```

### Running Tests

```bash
# Run all unit tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only tests NOT marked as integration (fast, no network)
pytest -m "not integration"

# Run a specific test file
pytest tests/test_strategies.py -v
```

---

## 7. Git and Version Control

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# Virtual environment
.venv/
venv/
env/

# Environment variables and secrets
.env

# Data files (regenerated on run)
data/
*.db

# Logs
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Pytest cache
.pytest_cache/

# Ruff cache
.ruff_cache/

# Coverage reports
htmlcov/
.coverage
```

### What to Commit

**Yes, commit:**
- All source code in `src/`
- Tests in `tests/`
- `pyproject.toml`
- `.env.example` (template, no real secrets)
- `.gitignore`
- Research files in `research/`
- Backtest code in `backtest/`

**Never commit:**
- `.env` (contains real tokens)
- `data/` directory (SQLite database, cached data)
- `logs/` directory
- `__pycache__/` directories

### Branch Strategy

Use a simple git flow approach:

```
main              ← stable, always runnable
  └── feature/*   ← new work branches off main
```

Examples:
- `feature/macd-strategy` - Adding a new strategy
- `feature/scoring-system` - Implementing the scorer
- `feature/telegram-formatting` - Improving notification messages
- `fix/yfinance-rate-limit` - Fixing a bug

Workflow:
1. Create a feature branch from `main`.
2. Make changes, commit with clear messages.
3. Test locally (unit tests + manual scan).
4. Merge to `main` when satisfied.

---

## 8. Development Workflow

### Local Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the scanner manually for a quick test
python -m src.main

# Run the scanner for a single ticker (useful during development)
python -m src.main --ticker ABB.ST

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Run tests
pytest -v
```

### Adding a New Strategy

This is the typical cycle when building a new strategy:

1. **Write the strategy class** - Create `src/strategies/new_strategy.py`, inheriting from `BaseStrategy`. Implement the `scan()` method.

2. **Write unit tests** - Create test cases with synthetic data in `tests/test_strategies.py`. Ensure the strategy fires when it should and stays silent when it should not.

3. **Run unit tests** - `pytest tests/test_strategies.py -v`

4. **Backtest** - Run the strategy against 1-2 years of historical data for several tickers. Check win rate, average return, and maximum drawdown. If numbers look bad, go back to step 1.

5. **Register the strategy** - Add it to the strategy list in `main.py` so it is included in daily scans.

6. **Add parameters to config** - Put all tunable values in `config.py` under `STRATEGY_PARAMS`.

7. **Manual test** - Run the full scanner once and inspect the output. Do the signals make sense?

8. **Commit and merge** - Feature branch to main.

### Deployment to VPS

Once the code is working locally:

1. Push to your Git remote.
2. SSH into the VPS and pull.
3. Install dependencies with `uv pip install -e .`
4. Copy `.env` with your real Telegram credentials.
5. Set up the cron job (see research file 02 for details).
6. Monitor the first few runs via logs and Telegram.

---

## 9. Docker Support

The application runs identically in Docker and locally. Docker is the recommended deployment method (Azure Container Apps, any Docker host, or a simple VPS with Docker installed). Local development without Docker is the recommended approach for fast iteration.

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install .
COPY src/ src/
COPY data/ data/
CMD ["python", "src/main.py"]
```

The image installs dependencies first (leveraging Docker layer caching), then copies source code. This means rebuilds after code changes are fast because the dependency layer is cached.

### docker-compose.yml

For local Docker testing, `docker-compose.yml` mounts the `data/` directory as a volume so the SQLite database persists across container restarts, and passes the `.env` file for configuration.

```yaml
version: "3.8"

services:
  swingtrader:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### .dockerignore

Keep the Docker build context small and avoid leaking secrets into the image:

```
.venv/
venv/
__pycache__/
*.pyc
.env
.git/
.gitignore
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
logs/
tests/
research/
backtest/
.DS_Store
```

### Build and Run

```bash
# Build the image
docker build -t swingtrader .

# Run with .env file and persistent data volume
docker run --env-file .env -v $(pwd)/data:/app/data swingtrader

# Or use docker-compose for convenience
docker compose up --build

# Run in the background
docker compose up -d --build
```

For deployment to Azure Container Apps or similar platforms, push the image to a container registry and configure the environment variables through the platform's secrets management instead of an `.env` file.

---

## 10. Local Development (No Docker)

For day-to-day development, running without Docker is faster and simpler. No container builds, no image layers, just Python.

```bash
# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install in editable mode (changes take effect immediately)
pip install -e ".[dev]"

# Run the scanner
python src/main.py
```

The same `.env` file, the same `config.py`, and the same source code are used in both modes. The SQLite database lives at `./data/swingtrader.db` regardless of whether you run locally or inside Docker.

There is no separate configuration for Docker vs local. The codebase does not need to know which environment it is running in.

---

## 11. Environment Detection

The config module uses a pattern that works transparently in both Docker containers and local development. The key is using environment variables with sensible defaults that resolve to the correct paths in either case.

```python
import os
from pathlib import Path

# Works in both Docker and local
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
DB_PATH = os.path.join(DATA_DIR, "swingtrader.db")
```

How this resolves in each environment:

| Environment | `BASE_DIR` | `DATA_DIR` (default) | `DB_PATH` |
|-------------|-----------|---------------------|-----------|
| Local | `/Users/you/source/SwingTrader` | `.../SwingTrader/data` | `.../SwingTrader/data/swingtrader.db` |
| Docker | `/app` | `/app/data` | `/app/data/swingtrader.db` |
| Custom override | any | value of `DATA_DIR` env var | `$DATA_DIR/swingtrader.db` |

Because Docker mounts `./data` to `/app/data`, the SQLite file is the same physical file in both cases when using `docker-compose`. You can develop locally, then deploy with Docker, and the data directory structure is identical.

If you need to override paths for a specific deployment (for example, a mounted Azure Files share), set the `DATA_DIR` environment variable and the application adapts automatically without any code changes.

---

## 12. Quick Start Guide

From zero to a running scanner in 10 minutes.

### Step 1: Clone and Enter the Repo

```bash
cd ~/source
git clone <your-repo-url> SwingTrader
cd SwingTrader
```

### Step 2: Create Virtual Environment and Install Dependencies

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using standard pip
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 3: Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in your Telegram bot token and chat ID
```

To get Telegram credentials:
1. Message `@BotFather` on Telegram, create a new bot, copy the token.
2. Message `@userinfobot` to get your chat ID.
3. Paste both values into `.env`.

### Step 4: Create Data Directory

```bash
mkdir -p data logs
```

### Step 5: Run Initial Data Fetch

```bash
# Fetch historical data for all configured tickers
python -m src.main --fetch-only
```

This downloads one year of daily OHLCV data for each ticker and stores it in `data/swingtrader.db`. Takes about 30 seconds depending on your internet connection and the number of tickers.

### Step 6: Run the Scanner Manually

```bash
python -m src.main
```

You should see output like:

```
18:30:01 | INFO     | Starting daily scan for 31 tickers
18:30:15 | INFO     | Data fetched for 31/31 tickers
18:30:16 | INFO     | Indicators calculated
18:30:16 | INFO     | Running 4 strategies...
18:30:17 | INFO     | Found 7 raw signals
18:30:17 | INFO     | Scored and filtered to 3 setups above threshold
18:30:18 | INFO     | Telegram notification sent
18:30:18 | INFO     | Scan complete
```

### Step 7: Set Up Daily Execution

```bash
# Open crontab
crontab -e

# Add this line to run at 18:30 Stockholm time every weekday
30 18 * * 1-5 cd /home/user/SwingTrader && /home/user/SwingTrader/.venv/bin/python -m src.main >> /home/user/SwingTrader/logs/cron.log 2>&1
```

### Verification Checklist

- [ ] Virtual environment is active and dependencies are installed
- [ ] `.env` contains valid Telegram credentials
- [ ] `python -m src.main` runs without errors
- [ ] You receive a Telegram message with scan results (or "no setups found")
- [ ] Cron job is scheduled and the log file is being written to
- [ ] `pytest` passes all tests

---

## Summary

The project structure separates concerns cleanly: data fetching, indicator calculation, strategy logic, scoring, and notifications are all independent modules. Configuration is centralized. Logging replaces print statements. Error handling ensures one bad ticker does not kill the entire scan.

Start with the structure, get `main.py` fetching data and printing results to the console. Then add strategies one at a time, each in its own file with its own tests. Add Telegram notifications last, once you have confidence the signals are meaningful.
