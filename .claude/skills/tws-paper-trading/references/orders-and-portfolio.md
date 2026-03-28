# Orders and Portfolio Tracking

## Placing orders from SwingTrader signals

A SwingTrader signal looks like:
```python
signal = {
    'ticker': 'VOLV-B.ST',
    'direction': 'BUY',
    'entry_price': 265.50,
    'stop_loss': 258.00,
    'target': 280.00,
    'shares': 40,
    'score': 16
}
```

### Basic limit order + stop-loss

```python
from ib_async import IB, Stock, LimitOrder, StopOrder

def execute_signal(ib: IB, signal: dict) -> None:
    symbol = swingtrader_to_ibkr(signal['ticker'])
    contract = Stock(symbol, 'SFB', 'SEK')
    ib.qualifyContracts(contract)

    entry_order = LimitOrder(
        action=signal['direction'],
        totalQuantity=signal['shares'],
        lmtPrice=signal['entry_price']
    )
    ib.placeOrder(contract, entry_order)

    stop_order = StopOrder(
        action='SELL' if signal['direction'] == 'BUY' else 'BUY',
        totalQuantity=signal['shares'],
        stopPrice=signal['stop_loss']
    )
    ib.placeOrder(contract, stop_order)
```

### Bracket order (recommended)

A bracket order links entry + stop-loss + take-profit. When the stop-loss
triggers, the take-profit auto-cancels (and vice versa).

```python
def execute_bracket_signal(ib: IB, signal: dict) -> list:
    symbol = swingtrader_to_ibkr(signal['ticker'])
    contract = Stock(symbol, 'SFB', 'SEK')
    ib.qualifyContracts(contract)

    bracket = ib.bracketOrder(
        action=signal['direction'],
        quantity=signal['shares'],
        limitPrice=signal['entry_price'],
        takeProfitPrice=signal['target'],
        stopLossPrice=signal['stop_loss']
    )

    trades = []
    for order in bracket:
        trades.append(ib.placeOrder(contract, order))
    return trades
```

## Tracking positions

```python
positions = ib.positions()
for pos in positions:
    print(f"{pos.contract.symbol}: {pos.position} shares @ {pos.avgCost:.2f}")
```

## Account summary

```python
for av in ib.accountSummary():
    if av.tag in ('NetLiquidation', 'TotalCashValue', 'UnrealizedPnL'):
        print(f"{av.tag}: {av.value} {av.currency}")
```

## P&L tracking

```python
# Portfolio-level
pnl = ib.pnl()

# Per-position
pnl_single = ib.pnlSingle(conId=contract.conId)
```

## Error handling

```python
from ib_async import IB
import logging

log = logging.getLogger('tws_integration')

def create_resilient_connection() -> IB:
    ib = IB()

    def on_disconnected():
        log.warning("Disconnected from TWS")

    def on_error(reqId, errorCode, errorString, contract):
        log.error(f"TWS Error {errorCode}: {errorString}")
        # 1100 = Connectivity lost
        # 1102 = Connectivity restored (data lost)
        # 2104 = Market data farm OK
        # 2106 = HMDS data farm OK

    ib.disconnectedEvent += on_disconnected
    ib.errorEvent += on_error
    return ib
```
