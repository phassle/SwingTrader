# Setup Guide: From Zero to First Paper Trade

## 1. Create an IBKR account (free)

IBKR offers a free trial pre-funded with $1,000,000 simulated money.
No real money or credit card needed.

Sign up: https://www.interactivebrokers.com/en/trading/free-trial.php

After creating the account, request a Paper Trading Account from Account Management.
This gives you a separate login for simulated trading.

## 2. Install TWS

Download: https://www.interactivebrokers.com/en/trading/tws.php

## 3. Configure API access

1. Open TWS → log in with **paper trading** credentials
2. Edit → Global Configuration → API → Settings
3. Check "Enable ActiveX and Socket Clients"
4. Confirm port is **7497** (paper trading default)
5. Optionally check "Allow connections from localhost only"
6. Check "Download open orders on connection"

**Port reference:**
- 7496 = live trading (REAL MONEY — never use for testing)
- 7497 = paper trading (simulated — use this)
- 4001 = IB Gateway live
- 4002 = IB Gateway paper

## 4. Install ib_async

```bash
pip install ib_async
```

Requires Python 3.10+. Replaces the older `ib_insync` package.

## 5. Test your connection

```python
from ib_async import IB

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
print(f"Connected: {ib.isConnected()}")
print(f"Account: {ib.managedAccounts()}")
ib.disconnect()
```

If this prints your account ID, you're ready.

## 6. Look up a Swedish stock

```python
from ib_async import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('VOLV B', 'SFB', 'SEK')
ib.qualifyContracts(contract)
print(f"Qualified: {contract}")
print(f"ConId: {contract.conId}")

ib.disconnect()
```

## 7. Place your first paper trade

```python
from ib_async import IB, Stock, LimitOrder

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('VOLV B', 'SFB', 'SEK')
ib.qualifyContracts(contract)

order = LimitOrder('BUY', 10, 265.00)
trade = ib.placeOrder(contract, order)
print(f"Order placed: {trade}")

# Check it appeared in TWS before disconnecting
ib.sleep(5)
ib.disconnect()
```

Open TWS and verify the order appears in the order panel.

## Useful links

- IBKR Free Trial: https://www.interactivebrokers.com/en/trading/free-trial.php
- TWS API Docs: https://interactivebrokers.github.io/tws-api/
- ib_async GitHub: https://github.com/ib-api-reloaded/ib_async
- ib_async Docs: https://ib-api-reloaded.github.io/ib_async/
- IBKR Campus: https://www.interactivebrokers.com/campus/
- Stockholm exchange: https://www.interactivebrokers.com/en/index.php?f=2626&p=stockholm
