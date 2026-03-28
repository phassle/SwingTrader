---
name: tws-paper-trading
description: >
  Guide for connecting SwingTrader's signal engine to Interactive Brokers (IBKR)
  TWS for paper trading Swedish stocks on Nasdaq Stockholm. Covers account setup,
  Python integration via ib_async, contract lookups for .ST tickers, order placement,
  position tracking, and result logging. Use this skill whenever the user mentions
  Interactive Brokers, IBKR, TWS, paper trading, simulated trading, trade execution,
  broker API, or wants to test trading signals against a real broker — even if they
  don't say "TWS" explicitly. Also trigger when the user asks about connecting signals
  to a broker, automating trades, or testing a strategy with fake/simulated money.
---

# TWS Paper Trading for SwingTrader

Paper trading = trading with fake money against real market prices. Think of it
as a flight simulator for your trading system: real instruments, real weather,
zero risk of crashing.

## Non-negotiable rules

These three rules exist because without them, code will silently target the wrong
exchange, use a deprecated library, or risk real money.

1. **Library: `ib_async` only.** Never `ibapi`. If you see `from ibapi.client import EClient` — rewrite it. See `references/library-choice.md` for why.

2. **Exchange: `SFB` + currency `SEK`.** Always `Stock('VOLV B', 'SFB', 'SEK')`. Never XETRA (Germany), NASDAQ (US), or SMART. See `references/swedish-contracts.md`.

3. **Port: `7497` for paper trading.** Port 7496 = live/real money. Double-check every connection string.

## Key concepts

- **TWS** = Interactive Brokers' desktop app — your code's "control tower"
- **IB Gateway** = lightweight headless alternative to TWS
- **Contract** = IBKR's word for a tradeable instrument
- **ib_async** = modern Python library for TWS (successor to unmaintained ib_insync)
- **Bracket order** = entry + stop-loss + take-profit as one linked package

## Quick reference: ticker conversion

SwingTrader uses `VOLV-B.ST`, IBKR uses `VOLV B`. Rule: remove `.ST`, replace `-` with space.

```python
def swingtrader_to_ibkr(ticker: str) -> str:
    return ticker.replace('.ST', '').replace('-', ' ')
```

## Quick reference: connection

```python
from ib_async import IB, Stock
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # paper trading
```

## Quick reference: bracket order from signal

```python
contract = Stock(swingtrader_to_ibkr('VOLV-B.ST'), 'SFB', 'SEK')
ib.qualifyContracts(contract)
bracket = ib.bracketOrder('BUY', 40, limitPrice=265.50,
                          takeProfitPrice=280.00, stopLossPrice=258.00)
for order in bracket:
    ib.placeOrder(contract, order)
```

## Quick reference: positions & P&L

```python
for pos in ib.positions():
    print(f"{pos.contract.symbol}: {pos.position} shares @ {pos.avgCost:.2f}")
for av in ib.accountSummary():
    if av.tag in ('NetLiquidation', 'TotalCashValue', 'UnrealizedPnL'):
        print(f"{av.tag}: {av.value}")
```

## Module structure

```
swingtrader/broker/
├── connection.py  — Owns the IB() object, reconnection, error handlers
├── contracts.py   — Ticker conversion, SFB/SEK enforcement, qualification
├── orders.py      — Signal → bracket order translation
├── portfolio.py   — Position tracking, P&L reporting
└── logger.py      — Trade journal (JSON/CSV)
```

Signal flow: Scanner → Signals → Telegram + Broker → TWS → Nasdaq Stockholm

## Reference files (read when needed)

Read these files for detailed guidance on specific topics:

- **`references/setup-guide.md`** — Account creation, TWS install, API config, first connection test. Read when: user is setting up from scratch.
- **`references/swedish-contracts.md`** — Ticker conversion table, contract qualification, market data, SFB exchange details. Read when: working with Swedish stocks.
- **`references/orders-and-portfolio.md`** — Order types, bracket orders, position tracking, P&L, error handling. Read when: placing orders or checking results.
- **`references/library-choice.md`** — Why ib_async over ibapi, migration patterns. Read when: someone asks about library choice or you see ibapi code.
- **`references/architecture.md`** — Module structure, code skeletons, async patterns, integration flow. Read when: building the full integration.

## Prerequisites checklist

1. Free IBKR trial account (no money needed): https://www.interactivebrokers.com/en/trading/free-trial.php
2. TWS installed and configured for API on port 7497
3. `pip install ib_async` (Python 3.10+)

## Common pitfalls

- Wrong port (7496 = live money, 7497 = paper)
- TWS not running (code can't connect without it)
- Auto-logoff (use IB Gateway for automation)
- Missing currency `SEK` (may match wrong exchange)
- Rate limits (~50 msg/sec — use `ib.sleep()` between operations)
- Market hours: Nasdaq Stockholm 09:00–17:30 CET
