# Swedish Stock Contracts on IBKR

## The golden rule

Swedish stocks on Nasdaq Stockholm always use: `Stock(symbol, 'SFB', 'SEK')`

- **SFB** = IBKR's exchange code for Nasdaq Stockholm
- **SEK** = Swedish kronor (always specify — omitting can match wrong exchange)

## Ticker conversion: SwingTrader → IBKR

Rule: remove `.ST` suffix, replace `-` with space.

| SwingTrader | IBKR Symbol | Notes |
|-------------|-------------|-------|
| VOLV-B.ST   | VOLV B      | Hyphen → space, drop .ST |
| ERIC-B.ST   | ERIC B      | Same pattern |
| SEB-A.ST    | SEB A       | Same pattern |
| ASSA-B.ST   | ASSA B      | Same pattern |
| HM-B.ST     | HM B        | Same pattern |
| INVE-B.ST   | INVE B      | Same pattern |
| SAND.ST     | SAND        | No share class — just drop .ST |
| ABB.ST      | ABB         | No share class |

```python
def swingtrader_to_ibkr(ticker: str) -> str:
    """Convert SwingTrader ticker to IBKR symbol.
    'VOLV-B.ST' -> 'VOLV B'
    'SAND.ST'   -> 'SAND'
    """
    return ticker.replace('.ST', '').replace('-', ' ')
```

## Wrong exchange codes (common mistakes)

- `XETRA` = Frankfurt, Germany — wrong country
- `NASDAQ` = Nasdaq US — wrong continent
- `OMX` = not a valid IBKR exchange code
- `SMART` = IBKR smart routing — may work but doesn't guarantee Stockholm

## Contract qualification

Always qualify contracts before using them — this lets IBKR fill in conId and
validate the contract exists:

```python
contract = Stock('VOLV B', 'SFB', 'SEK')
ib.qualifyContracts(contract)
# contract.conId is now populated
```

## Searching for unknown contracts

```python
matches = ib.reqMatchingSymbols('Volvo')
for m in matches:
    c = m.contract
    print(f"{c.symbol} | {c.secType} | {c.primaryExchange} | {c.currency}")
```

## Market data

Paper trading accounts get 15-minute delayed data by default.
For real-time Nasdaq Stockholm data, subscribe to "Nordic Equity" in Account
Management (small monthly fee). Delayed data is fine for testing signal logic.

```python
contract = Stock('VOLV B', 'SFB', 'SEK')
ib.qualifyContracts(contract)

# Snapshot
ticker = ib.reqMktData(contract, '', False, False)
ib.sleep(2)
print(f"Last: {ticker.last}, Bid: {ticker.bid}, Ask: {ticker.ask}")

# Historical daily bars
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='30 D',
    barSizeSetting='1 day',
    whatToShow='TRADES',
    useRTH=True
)
```

## Market hours

Nasdaq Stockholm: 09:00–17:30 CET. Orders outside hours queue until open.
