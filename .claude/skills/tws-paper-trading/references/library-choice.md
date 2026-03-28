# Why ib_async, not ibapi

## The two libraries

- **`ib_async`** — High-level async/sync framework. Clean API where you write
  `ib.positions()` and get a list back. Handles threading, callbacks, and state
  sync automatically. Install: `pip install ib_async`.

- **`ibapi`** — IBKR's official low-level API. Requires subclassing EWrapper +
  EClient, managing threads, writing callback methods for every response. Code is
  ~3x longer for the same result.

## Why ib_async wins

Think of it like this: `ibapi` is assembly language — full control, but you
manage every detail. `ib_async` is Python — same power, 3x less code, and it
handles the plumbing for you.

| Task | ib_async | ibapi |
|------|----------|-------|
| Get positions | `ib.positions()` | Subclass EWrapper, implement positionEnd callback, manage threading |
| Place order | `ib.placeOrder(contract, order)` | Subclass, implement orderStatus/openOrder callbacks, track state |
| Lines of code for "hello world" | ~10 | ~50 |

## History

ib_insync was created by Ewald de Wit in 2017 and became the most popular IBKR
Python library. After his passing in early 2024, the project was forked as
`ib_async` under new maintainership (Matt Stancliff, github.com/ib-api-reloaded).

The API is nearly identical to ib_insync. If you see tutorials using
`from ib_insync import *`, replace with `from ib_async import *`.

## Migration from ibapi code

If you encounter ibapi-style code:

```python
# OLD (ibapi) — don't use
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
class App(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
    def nextValidId(self, orderId):
        ...

# NEW (ib_async) — use this
from ib_async import IB
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
```
