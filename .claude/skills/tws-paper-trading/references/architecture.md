# SwingTrader TWS Integration Architecture

## System overview

```
SwingTrader Signal Engine
        |
        | (signals: ticker, score, direction, stop-loss, target)
        v
  TWS Integration Layer (broker/)
        |
        | (ib_async: connect, look up contracts, place orders)
        v
  TWS / IB Gateway (running locally or on server)
        |
        | (IBKR network)
        v
  Nasdaq Stockholm (real market data, simulated execution)
```

## Module structure

```
swingtrader/broker/
├── __init__.py
├── connection.py  — Owns IB(), reconnection, error handlers
├── contracts.py   — Ticker conversion, SFB/SEK, qualification
├── orders.py      — Signal → bracket order translation
├── portfolio.py   — Position tracking, P&L reporting
└── logger.py      — Trade journal (JSON/CSV)
```

## Module skeletons

### connection.py

```python
from ib_async import IB
import logging

log = logging.getLogger(__name__)

async def connect_paper(
    host: str = '127.0.0.1',
    port: int = 7497,
    client_id: int = 1
) -> IB:
    ib = IB()
    ib.errorEvent += lambda reqId, code, msg, contract: (
        log.error(f"TWS {code}: {msg}")
    )
    ib.disconnectedEvent += lambda: log.warning("Disconnected from TWS")
    await ib.connectAsync(host, port, clientId=client_id)
    log.info(f"Connected to paper trading, account: {ib.managedAccounts()}")
    return ib
```

### contracts.py

```python
from ib_async import IB, Stock

def swingtrader_to_ibkr(ticker: str) -> str:
    return ticker.replace('.ST', '').replace('-', ' ')

async def lookup(ib: IB, ticker: str) -> Stock:
    contract = Stock(swingtrader_to_ibkr(ticker), 'SFB', 'SEK')
    await ib.qualifyContractsAsync(contract)
    return contract
```

### orders.py

```python
from ib_async import IB, Trade
from .contracts import lookup

async def execute_bracket(ib: IB, signal: dict) -> list[Trade]:
    contract = await lookup(ib, signal['ticker'])
    bracket = ib.bracketOrder(
        action=signal['direction'],
        quantity=signal['shares'],
        limitPrice=signal['entry_price'],
        takeProfitPrice=signal['target'],
        stopLossPrice=signal['stop_loss']
    )
    return [ib.placeOrder(contract, o) for o in bracket]
```

### portfolio.py

```python
from ib_async import IB

def report(ib: IB) -> dict:
    positions = ib.positions()
    summary = {av.tag: av.value for av in ib.accountSummary()
               if av.tag in ('NetLiquidation', 'TotalCashValue', 'UnrealizedPnL')}
    return {'positions': positions, 'account': summary}
```

## Signal flow

1. Scanner runs → produces scored signals (existing)
2. Signals above threshold → sent to Telegram AND broker module
3. Broker module → converts to IBKR orders → places on paper account
4. Portfolio tracker → monitors fills, P&L, stop-loss triggers
5. Daily summary → aggregates results → sends to Telegram

## Async pattern

ib_async is built on asyncio. For long-running processes:

```python
import asyncio
from .connection import connect_paper

async def main():
    ib = await connect_paper()
    while True:
        # Check for new signals, place orders, update portfolio
        await asyncio.sleep(60)

asyncio.run(main())
```

For one-shot scripts (test connection, place single order), the sync API works:

```python
from ib_async import IB
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
# do work
ib.disconnect()
```
