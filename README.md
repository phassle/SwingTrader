# SwingTrader

> **This is a test project.** The primary purpose of SwingTrader is to explore and evaluate agentic coding workflows and agentic decision-making using AI-assisted development tools. The trading system itself is secondary to the process of building it.

## What is SwingTrader?

SwingTrader is a swing trading signal scanner targeting Nasdaq Stockholm Large Cap stocks. It scans ~90 tickers, scores them on a 0–20 composite scale, and delivers actionable signals via Telegram — complete with ATR-based stop-losses, position sizing, and risk/reward ratios.

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
- `ruff` for linting and formatting
- `pytest` for testing
- Telegram Bot API for signal delivery
- Healthchecks.io for uptime monitoring

## Development

This project follows git flow. All development happens on feature branches.

```bash
# Install dependencies (TBD)
# Run linting
ruff check .
ruff format --check .

# Run tests
pytest
```

## License

Private project — not for distribution.
