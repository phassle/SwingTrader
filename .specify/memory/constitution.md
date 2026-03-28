# SwingTrader Constitution

## Core Principles

### I. Signal Integrity Above All

Every trading signal must be grounded in verified, reproducible analysis. Minimum 30-trade backtest required before any strategy is deployed. No look-ahead bias permitted in any indicator or scoring logic. All scoring criteria must be transparent — every point in the 0–20 composite scale must trace to a documented rule.

### II. Defensive Risk Management

Risk is the only variable we fully control. ATR-based stop-losses are mandatory on every signal. Risk per trade is capped at 1–2% of portfolio value. Portfolio heat (total open risk) must respect defined limits. Drawdown circuit breakers must halt new signals when cumulative losses exceed thresholds. Position sizing is calculated, never discretionary.

### III. Clean Python, Tested Thoroughly

All code targets Python 3.11+ with type hints throughout. Linting and formatting enforced via `ruff` — no exceptions. Tests written with `pytest` using synthetic data fixtures to ensure deterministic, repeatable results. Code must be readable, modular, and independently testable per component.

### IV. Consistent Telegram UX

Signals delivered via Telegram follow a standardized format: ticker, score, direction, entry zone, stop-loss, target, position size, and risk/reward ratio. Daily summaries aggregate the top signals. Priority-based routing ensures high-scoring signals are highlighted. The user experience must be predictable — a trader should know exactly where to look in every message.

### V. Performance Within Bounds

A full scan of ~90 Nasdaq Stockholm Large Cap tickers must complete in under 30 seconds. Faults are isolated per ticker — one bad data feed must not halt the entire scan. Structured logging (not print statements) is required for all runtime output. Monitoring via Healthchecks.io ensures uptime visibility.

## Technology Stack

- **Language**: Python 3.11+
- **Linting/Formatting**: `ruff`
- **Testing**: `pytest` with synthetic data fixtures
- **Signal Delivery**: Telegram Bot API
- **Monitoring**: Healthchecks.io
- **Target Market**: Nasdaq Stockholm Large Cap (~90 `.ST` tickers)
- **Account Assumption**: ISK (Investeringssparkonto)
- **Version Control**: Git flow with feature branches

## Development Workflow

- All development happens on feature branches — never directly on `main`.
- Pull requests are required for all merges to `main`.
- Code review is required before merging.
- Commit messages and console output must be in English.
- Agent-specific setup files (`.specify/`) are kept isolated per worktree.
- Shared specs and source code are merged through normal PR review.

## Governance

This constitution supersedes all other development practices in the SwingTrader project. Any amendments require documentation of the change, rationale, and a migration plan if existing code or processes are affected. All pull requests and code reviews must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: 2026-03-28 | **Last Amended**: 2026-03-28
