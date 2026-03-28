# Claude Instructions for SwingTrader

## First thing: Read learnings

At the start of every session, read `.claude/learnings.md`. It contains documented mistakes and insights from previous sessions. Following these learnings prevents repeating the same errors.

## Project context

SwingTrader is a swing trading signal scanner for Nasdaq Stockholm Large Cap (~90 tickers). The trading system itself is secondary — the primary goal is exploring agentic coding workflows. See `README.md` for full context and `.specify/memory/constitution.md` for the five core principles.

## Research documents

Before creating new files, check `research/strategy-and-theory/` and `research/technical-implementation/` for existing coverage. Prefer extending existing documents over creating duplicates. Follow the numbered filename pattern (e.g., `27-swedish-market-adaptation.md`).

## Code standards

- Python 3.11+ with type hints
- Linting and formatting via `ruff`
- Testing via `pytest` with synthetic data fixtures
- Structured logging, not print statements
- All commit messages and console output in English

## Git workflow

- Always use git flow with feature branches
- Never commit directly to main
- Pull requests required for all merges
- Descriptive branch names (e.g., `feature/tws-integration`)

## Skills available

- `tws-paper-trading` — Interactive Brokers TWS integration for paper trading Swedish stocks via ib_async
- `signal-scoring` — 0-20 composite scoring system for trade setups (8 categories, grade bands, hard disqualifiers)
- `risk-management` — Position sizing, ATR stops, portfolio heat, drawdown protocols, partial exits
- `market-regime` — 4-regime classification (A/B/C/D), strategy-regime matrix, sector rotation
- `swedish-market` — ISK accounts, .ST tickers, Avanza rules, trading hours, liquidity specifics
- `trading-discipline` — Pre-trade checklists, hard limits, journaling, daily routines, mistake flagging
- `backtesting` — Validation framework: data splits, WFA, performance targets, go-live checklist

## After completing work

When finishing a session or significant piece of work, reflect on whether any mistakes were made or unexpected issues arose. If so, append a new entry to `.claude/learnings.md` following the existing format:

```markdown
## YYYY-MM-DD: Brief description of the issue

**What happened:** Describe what went wrong or what was unexpected.

**Learning:** The takeaway that would prevent this in future sessions.
```
