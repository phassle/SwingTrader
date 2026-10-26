"""Simulated price engine for the paper-trading sandbox.

Prices follow a one-factor model: every tick each ticker moves by
beta * market_return + idiosyncratic noise, with a slowly switching market
regime (bull, bear, chop) and rare jump events ("news"). Nothing here touches
real market data. All prices are fake.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

from swingtrader.data.universe import get_universe

HISTORY_LEN = 600

# Per-tick drift and market volatility for each regime
REGIMES: dict[str, tuple[float, float]] = {
    "bull": (0.00025, 0.0012),
    "bear": (-0.00030, 0.0020),
    "chop": (0.0, 0.0010),
}


def _stable_unit(ticker: str, salt: str) -> float:
    """Deterministic value in [0, 1) derived from the ticker name."""
    digest = hashlib.sha256(f"{salt}:{ticker}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


@dataclass
class Instrument:
    ticker: str
    price: float
    open_price: float
    beta: float
    idio_vol: float
    spread_pct: float
    volume: int = 0
    history: deque[tuple[int, float]] = field(default_factory=lambda: deque(maxlen=HISTORY_LEN))

    @property
    def bid(self) -> float:
        return round(self.price * (1 - self.spread_pct / 2), 2)

    @property
    def ask(self) -> float:
        return round(self.price * (1 + self.spread_pct / 2), 2)

    def quote(self) -> dict:
        return {
            "ticker": self.ticker,
            "last": round(self.price, 2),
            "bid": self.bid,
            "ask": self.ask,
            "open": round(self.open_price, 2),
            "change_pct": round((self.price / self.open_price - 1) * 100, 3),
            "volume": self.volume,
        }


class Market:
    """Holds all instruments and advances prices one tick at a time."""

    def __init__(
        self,
        tickers: list[str] | None = None,
        seed: int | None = None,
        jump_prob: float = 0.0008,
        regime_switch_prob: float = 0.004,
    ) -> None:
        self.rng = random.Random(seed)
        self.jump_prob = jump_prob
        self.regime_switch_prob = regime_switch_prob
        self.tick_count = 0
        self.regime = "chop"
        self.index_level = 1000.0
        self.events: deque[dict] = deque(maxlen=50)
        self.instruments: dict[str, Instrument] = {}
        for t in tickers or get_universe():
            price = round(40 + _stable_unit(t, "price") * 760, 2)
            inst = Instrument(
                ticker=t,
                price=price,
                open_price=price,
                beta=round(0.6 + _stable_unit(t, "beta") * 0.9, 2),
                idio_vol=0.0008 + _stable_unit(t, "vol") * 0.0022,
                spread_pct=0.0004 + _stable_unit(t, "spread") * 0.0016,
            )
            inst.history.append((0, price))
            self.instruments[t] = inst

    def get(self, ticker: str) -> Instrument:
        key = ticker.upper()
        if key not in self.instruments and not key.endswith(".ST"):
            key = f"{key}.ST"
        if key not in self.instruments:
            raise KeyError(ticker)
        return self.instruments[key]

    def _log_event(self, kind: str, **data: object) -> None:
        self.events.appendleft(
            {"tick": self.tick_count, "time": datetime.now(UTC).isoformat(), "kind": kind, **data}
        )

    def step(self) -> None:
        """Advance every price by one tick."""
        self.tick_count += 1
        if self.rng.random() < self.regime_switch_prob:
            self.regime = self.rng.choice([r for r in REGIMES if r != self.regime])
            self._log_event("regime", regime=self.regime)

        drift, mkt_vol = REGIMES[self.regime]
        market_ret = self.rng.gauss(drift, mkt_vol)
        self.index_level *= math.exp(market_ret)

        for inst in self.instruments.values():
            ret = inst.beta * market_ret + self.rng.gauss(0.0, inst.idio_vol)
            if self.rng.random() < self.jump_prob:
                jump = self.rng.choice([-1, 1]) * self.rng.uniform(0.03, 0.09)
                ret += jump
                self._log_event("news", ticker=inst.ticker, move_pct=round(jump * 100, 2))
            inst.price = max(0.5, inst.price * math.exp(ret))
            inst.volume += int(self.rng.expovariate(1 / 800) * (1 + abs(ret) * 200))
            inst.history.append((self.tick_count, round(inst.price, 2)))

    def shock(self, ticker: str | None, pct: float) -> None:
        """Apply an instant move: one ticker, or the whole market when ticker is None."""
        targets = [self.get(ticker)] if ticker else list(self.instruments.values())
        for inst in targets:
            inst.price = max(0.5, inst.price * (1 + pct / 100))
            inst.history.append((self.tick_count, round(inst.price, 2)))
        self._log_event("shock", ticker=ticker or "ALL", move_pct=pct)

    def new_session(self) -> None:
        """Reset the session open so change_pct starts from zero."""
        for inst in self.instruments.values():
            inst.open_price = inst.price
            inst.volume = 0
        self._log_event("session_open")

    def quotes(self) -> list[dict]:
        return [inst.quote() for inst in self.instruments.values()]

    def summary(self) -> dict:
        return {
            "tick": self.tick_count,
            "regime": self.regime,
            "index": round(self.index_level, 2),
            "instruments": len(self.instruments),
        }
