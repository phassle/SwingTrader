"""Paper-trading broker: accounts, orders, fills and commission.

Long-only (ISK-style, no shorting). Market orders fill immediately at bid/ask.
Limit and stop orders rest until a later tick crosses their price.
"""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

import structlog

from swingtrader.sim.market import Market

logger = structlog.get_logger()

Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit", "stop"]

DEFAULT_CASH = 100_000.0
COMMISSION_RATE = 0.00069  # Avanza "Small" style: 0.069 %
COMMISSION_MIN = 1.0


class OrderError(ValueError):
    """Raised when an order is rejected."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def commission(value: float) -> float:
    return round(max(COMMISSION_MIN, value * COMMISSION_RATE), 2)


@dataclass
class Order:
    id: int
    ticker: str
    side: Side
    quantity: int
    type: OrderType
    limit_price: float | None
    stop_price: float | None
    note: str
    created_at: str
    created_tick: int
    status: str = "open"  # open, filled, cancelled, rejected
    fill_price: float | None = None
    filled_at: str | None = None
    reason: str | None = None


@dataclass
class Position:
    quantity: int = 0
    avg_cost: float = 0.0


@dataclass
class Account:
    name: str
    starting_cash: float = DEFAULT_CASH
    cash: float = DEFAULT_CASH
    positions: dict[str, Position] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    equity_curve: list[tuple[int, float]] = field(default_factory=list)
    realized_pnl: float = 0.0
    commission_paid: float = 0.0


class Broker:
    def __init__(self, market: Market) -> None:
        self.market = market
        self.accounts: dict[str, Account] = {}
        self._ids = itertools.count(1)

    # -- accounts ---------------------------------------------------------

    def account(self, name: str) -> Account:
        if name not in self.accounts:
            self.accounts[name] = Account(name=name)
            logger.info("account_created", account=name)
        return self.accounts[name]

    def reset(self, name: str, cash: float = DEFAULT_CASH) -> Account:
        self.accounts[name] = Account(name=name, starting_cash=cash, cash=cash)
        logger.info("account_reset", account=name, cash=cash)
        return self.accounts[name]

    def equity(self, acct: Account) -> float:
        value = sum(pos.quantity * self.market.get(t).bid for t, pos in acct.positions.items())
        return round(acct.cash + value, 2)

    def snapshot(self, acct: Account) -> dict:
        positions = []
        for t, pos in sorted(acct.positions.items()):
            price = self.market.get(t).bid
            value = pos.quantity * price
            positions.append(
                {
                    "ticker": t,
                    "quantity": pos.quantity,
                    "avg_cost": round(pos.avg_cost, 2),
                    "price": price,
                    "market_value": round(value, 2),
                    "unrealized_pnl": round(value - pos.quantity * pos.avg_cost, 2),
                    "unrealized_pct": round((price / pos.avg_cost - 1) * 100, 2),
                }
            )
        equity = self.equity(acct)
        reserved = self._reserved_cash(acct)
        return {
            "account": acct.name,
            "cash": round(acct.cash, 2),
            "buying_power": round(acct.cash - reserved, 2),
            "equity": equity,
            "starting_cash": acct.starting_cash,
            "total_return_pct": round((equity / acct.starting_cash - 1) * 100, 3),
            "realized_pnl": round(acct.realized_pnl, 2),
            "commission_paid": round(acct.commission_paid, 2),
            "positions": positions,
            "open_orders": [asdict(o) for o in acct.orders if o.status == "open"],
        }

    # -- orders -----------------------------------------------------------

    def _reserved_cash(self, acct: Account) -> float:
        total = 0.0
        for o in acct.orders:
            if o.status == "open" and o.side == "buy":
                ref = o.limit_price or o.stop_price or self.market.get(o.ticker).ask
                total += o.quantity * ref * (1 + COMMISSION_RATE) + COMMISSION_MIN
        return total

    def _reserved_qty(self, acct: Account, ticker: str) -> int:
        return sum(
            o.quantity
            for o in acct.orders
            if o.status == "open" and o.side == "sell" and o.ticker == ticker
        )

    def place_order(
        self,
        account: str,
        ticker: str,
        side: Side,
        quantity: int,
        type: OrderType = "market",
        limit_price: float | None = None,
        stop_price: float | None = None,
        note: str = "",
    ) -> Order:
        acct = self.account(account)
        try:
            inst = self.market.get(ticker)
        except KeyError as e:
            raise OrderError(f"unknown ticker {ticker!r}") from e
        if side not in ("buy", "sell"):
            raise OrderError("side must be 'buy' or 'sell'")
        if quantity <= 0:
            raise OrderError("quantity must be a positive integer")
        if type == "limit" and not limit_price:
            raise OrderError("limit orders need limit_price")
        if type == "stop" and not stop_price:
            raise OrderError("stop orders need stop_price")
        if type not in ("market", "limit", "stop"):
            raise OrderError("type must be market, limit or stop")

        if side == "buy":
            ref = limit_price or stop_price or inst.ask
            cost = quantity * ref
            needed = cost + commission(cost)
            available = acct.cash - self._reserved_cash(acct)
            if needed > available:
                raise OrderError(
                    f"insufficient buying power: need {needed:.2f}, have {available:.2f}"
                )
        else:
            held = acct.positions.get(inst.ticker, Position()).quantity
            free = held - self._reserved_qty(acct, inst.ticker)
            if quantity > free:
                raise OrderError(f"cannot sell {quantity}, only {free} shares free (no shorting)")

        order = Order(
            id=next(self._ids),
            ticker=inst.ticker,
            side=side,
            quantity=quantity,
            type=type,
            limit_price=limit_price,
            stop_price=stop_price,
            note=note[:200],
            created_at=_now(),
            created_tick=self.market.tick_count,
        )
        acct.orders.append(order)
        logger.info("order_placed", account=account, **{k: v for k, v in asdict(order).items()})
        if type == "market":
            self._fill(acct, order, inst.ask if side == "buy" else inst.bid)
        else:
            self._try_fill(acct, order)
        return order

    def cancel_order(self, account: str, order_id: int) -> Order:
        acct = self.account(account)
        for o in acct.orders:
            if o.id == order_id:
                if o.status != "open":
                    raise OrderError(f"order {order_id} is {o.status}")
                o.status = "cancelled"
                logger.info("order_cancelled", account=account, order_id=order_id)
                return o
        raise OrderError(f"order {order_id} not found")

    def _try_fill(self, acct: Account, o: Order) -> None:
        inst = self.market.get(o.ticker)
        if o.type == "limit":
            if o.side == "buy" and inst.ask <= o.limit_price:
                self._fill(acct, o, inst.ask)
            elif o.side == "sell" and inst.bid >= o.limit_price:
                self._fill(acct, o, inst.bid)
        elif o.type == "stop":
            if o.side == "buy" and inst.ask >= o.stop_price:
                self._fill(acct, o, inst.ask)
            elif o.side == "sell" and inst.bid <= o.stop_price:
                self._fill(acct, o, inst.bid)

    def _fill(self, acct: Account, o: Order, price: float) -> None:
        value = o.quantity * price
        fee = commission(value)
        pos = acct.positions.setdefault(o.ticker, Position())
        realized = 0.0
        if o.side == "buy":
            if value + fee > acct.cash:
                o.status, o.reason = "rejected", "insufficient cash at fill time"
                return
            acct.cash -= value + fee
            pos.avg_cost = (pos.avg_cost * pos.quantity + value + fee) / (pos.quantity + o.quantity)
            pos.quantity += o.quantity
        else:
            if o.quantity > pos.quantity:
                o.status, o.reason = "rejected", "position too small at fill time"
                return
            acct.cash += value - fee
            realized = (price - pos.avg_cost) * o.quantity - fee
            acct.realized_pnl += realized
            pos.quantity -= o.quantity
            if pos.quantity == 0:
                del acct.positions[o.ticker]
        acct.commission_paid += fee
        o.status, o.fill_price, o.filled_at = "filled", price, _now()
        trade = {
            "order_id": o.id,
            "ticker": o.ticker,
            "side": o.side,
            "quantity": o.quantity,
            "price": price,
            "commission": fee,
            "realized_pnl": round(realized, 2) if o.side == "sell" else None,
            "tick": self.market.tick_count,
            "time": o.filled_at,
            "note": o.note,
        }
        acct.trades.append(trade)
        logger.info("order_filled", account=acct.name, **trade)

    # -- tick -------------------------------------------------------------

    def on_tick(self) -> None:
        """Check resting orders and sample equity. Call after Market.step()."""
        for acct in self.accounts.values():
            for o in acct.orders:
                if o.status == "open":
                    self._try_fill(acct, o)
            if self.market.tick_count % 5 == 0:
                acct.equity_curve.append((self.market.tick_count, self.equity(acct)))
                del acct.equity_curve[:-1000]
