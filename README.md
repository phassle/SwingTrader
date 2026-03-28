# SwingTrader

> **This is a test project.** The primary purpose of SwingTrader is to explore and evaluate agentic coding workflows and agentic decision-making using AI-assisted development tools. The trading system itself is secondary to the process of building it.

## What is SwingTrader?

SwingTrader is a swing trading signal scanner targeting Nasdaq Stockholm Large Cap stocks. It scans ~90 tickers, scores them on a 0–20 composite scale, and outputs a ranked watchlist with entry/stop/target levels.

## Quick Start

```bash
# 1. Install dependencies
pip install yfinance pandas ta structlog

# 2. Run the scanner (full universe, top 10) — auto-saves to scans/
PYTHONPATH=src python -m swingtrader

# 3. Or scan a single ticker
PYTHONPATH=src python -m swingtrader --ticker VOLV-B.ST

# 4. Show more/fewer results
PYTHONPATH=src python -m swingtrader --top 20
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `python -m swingtrader` | Scan full universe, auto-save to `scans/` |
| `python -m swingtrader --ticker VOLV-B.ST` | Scan a single ticker |
| `python -m swingtrader --top 20` | Show top N results |
| `python -m swingtrader --review` | Review all past scans |
| `python -m swingtrader --review 2026-03-29` | Review scans from a specific date |
| `python -m swingtrader --evaluate` | Evaluate past signals vs current prices |
| `python -m swingtrader --evaluate 2026-03-29` | Evaluate a specific date's signals |
| `python -m swingtrader --full` | Full workflow: scan + review + evaluate |

Every scan auto-saves to `scans/scan_YYYY-MM-DD_HHMM.json` and exports `scans/scan-data.js` for the visual dashboard (`swingtrader-scanner-playground.html`).

## Automated Daily Scan (launchd)

The scanner runs automatically via macOS `launchd` — no manual intervention needed.

**Schedule:**
- **Primary**: every day at **18:00**
- **Catch-up**: every hour at :05 — if the Mac was asleep/off at 18:00, the next wake-up triggers the scan
- **Idempotent**: the script checks if a scan already exists for today and skips if so (one scan per day)

**What `--full` does each run:**
1. Scans all ~90 tickers and saves the result
2. Evaluates all previous scans with unresolved signals (fetches current prices, marks target hit / stopped out)
3. Exports `scans/scan-data.js` for the dashboard
4. Prints a review of all scan history

**Files:**

| File | Purpose |
|------|---------|
| `scripts/daily-scan.sh` | Wrapper script (idempotent, logs to `scans/logs/`) |
| `~/Library/LaunchAgents/com.swingtrader.daily-scan.plist` | launchd job definition |
| `scans/logs/scan_YYYY-MM-DD.log` | Daily log output |

**Manage the job:**

```bash
# Check status
launchctl list | grep swingtrader

# Pause
launchctl unload ~/Library/LaunchAgents/com.swingtrader.daily-scan.plist

# Resume
launchctl load ~/Library/LaunchAgents/com.swingtrader.daily-scan.plist

# Run manually (skips if already ran today)
./scripts/daily-scan.sh
```

## Visual Dashboard

Open `swingtrader-scanner-playground.html` in a browser to see:

- **Signals tab** — current scan with score bars, grade badges, entry/stop/target, outcome status
- **Performance tab** — win rate by grade (A/B/C/F), by setup type (pullback/breakout), resolved signals timeline
- **Scan history** — sidebar with all past scans, click any date to see its signals and outcomes

The dashboard reads from `scans/scan-data.js` which is auto-generated after every scan and evaluation.

## What the Scanner Does

The scanner runs a four-step pipeline every time you execute it:

1. **Fetch data** — Downloads 1 year of daily + weekly OHLCV from Yahoo Finance for all ~90 Nasdaq Stockholm Large Cap tickers
2. **Calculate indicators** — EMA(20), SMA(50), SMA(200), ATR(14), ADX(14), RSI(14), volume ratios, breakout detection
3. **Score each ticker** — 0–20 composite across 8 categories (trend, level, catalyst, volume, liquidity, market, risk/reward, timing)
4. **Rank and display** — Sorted by score with entry/stop/target levels for the top candidates

### Example Output

```
================================================================================
  SwingTrader Signal Scanner — 2026-03-29 18:30
  Scanned: 78 tickers | Showing top 5
================================================================================
   #  Ticker         Score Grade Setup        Entry     Stop   Target  Action
  --------------------------------------------------------------------------
   1  VOLV-B.ST         16     B breakout    265.50   249.80   281.20  BUY — Execute with caution
   2  SAND.ST           15     B pullback    228.40   218.60   238.20  BUY — Execute with caution
   3  SEB-A.ST          14     B breakout    148.90   141.30   156.50  BUY — Execute with caution
   4  ASSA-B.ST         12     C pullback    312.00   298.40   325.60  WATCHLIST — Only if R:R exceptional
   5  NDA-SE.ST         11     C none        131.20   124.80   137.60  WATCHLIST — Only if R:R exceptional
================================================================================
```

### Grade Bands

| Grade | Score | Meaning |
|-------|-------|---------|
| **A** | 17–20 | High conviction — execute with standard sizing |
| **B** | 13–16 | Quality setup — execute with caution |
| **C** | 9–12 | Marginal — only if risk/reward is exceptional |
| **F** | <9 | Skip — insufficient edge |

## Project Structure

```
SwingTrader/
├── src/swingtrader/
│   ├── cli.py                  # Scanner CLI (scan, review, evaluate, full)
│   ├── data/
│   │   ├── fetcher.py          # Yahoo Finance data provider (IBKR later)
│   │   └── universe.py         # Nasdaq Stockholm Large Cap tickers
│   ├── indicators/
│   │   └── technical.py        # ATR, MAs, ADX, RSI, volume, breakouts
│   └── scoring/
│       └── engine.py           # 0-20 scoring system, grade bands, disqualifiers
├── scripts/
│   └── daily-scan.sh           # Idempotent wrapper for launchd cron job
├── scans/                      # Auto-saved scan results (JSON + JS export)
│   ├── scan_YYYY-MM-DD_HHMM.json
│   ├── scan-data.js            # Playground data (auto-generated)
│   └── logs/                   # Daily scan logs
├── swingtrader-scanner-playground.html  # Visual dashboard
├── tests/
│   └── test_scanner.py         # Tests with synthetic market data
├── .claude/
│   ├── skills/                 # 7 AI agent knowledge skills
│   └── learnings.md            # Documented mistakes from past sessions
├── research/                   # 58 swing trading research documents
└── pyproject.toml
```

## Running Tests

```bash
pip install pytest
PYTHONPATH=src pytest tests/ -v
```

## Key Design Principles

The project is governed by a [constitution](.specify/memory/constitution.md) with five core principles:

1. **Signal Integrity Above All** — 30-trade backtest minimum, no look-ahead bias, transparent scoring
2. **Defensive Risk Management** — ATR-based stops, 1–2% risk per trade, portfolio heat limits, drawdown circuit breakers
3. **Clean Python, Tested Thoroughly** — Python 3.11+, type hints, ruff linting, pytest with synthetic data fixtures
4. **Consistent Telegram UX** — Standardized signal format, daily summaries, priority-based routing
5. **Performance Within Bounds** — Full scan <30s, fault isolation per ticker, structured logging

## Target Market

- Nasdaq Stockholm Large Cap (~90 tickers)
- `.ST` suffixed tickers (e.g., `VOLV-B.ST`, `ERIC-B.ST`)
- Swedish trading calendar
- ISK account assumptions

## Tech Stack

- Python 3.11+
- `yfinance` for market data (Yahoo Finance)
- `pandas` + `ta` for technical analysis
- `structlog` for structured logging
- `ruff` for linting and formatting
- `pytest` for testing

## License

Private project — not for distribution.
