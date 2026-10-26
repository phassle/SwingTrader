"""Tests for the paper-trading sandbox (simulated market, broker, HTTP API)."""

import pytest

from swingtrader.sim.broker import COMMISSION_MIN, Broker, OrderError
from swingtrader.sim.market import Market

TICKERS = ["VOLV-B.ST", "ERIC-B.ST", "SAND.ST"]
PASSWORD = "test-pw"


@pytest.fixture
def market() -> Market:
    return Market(tickers=TICKERS, seed=7, jump_prob=0.0, regime_switch_prob=0.0)


@pytest.fixture
def broker(market: Market) -> Broker:
    return Broker(market)


def test_market_is_deterministic_with_seed():
    a = Market(tickers=TICKERS, seed=1)
    b = Market(tickers=TICKERS, seed=1)
    for _ in range(50):
        a.step()
        b.step()
    assert [q["last"] for q in a.quotes()] == [q["last"] for q in b.quotes()]


def test_prices_move_and_stay_positive(market: Market):
    start = market.get("VOLV-B").price
    for _ in range(200):
        market.step()
    assert market.get("VOLV-B").price != start
    assert all(i.price > 0 for i in market.instruments.values())
    assert len(market.get("VOLV-B").history) == 201


def test_bid_below_ask(market: Market):
    q = market.get("SAND.ST").quote()
    assert q["bid"] < q["last"] < q["ask"]


def test_market_buy_then_sell_round_trip(broker: Broker, market: Market):
    inst = market.get("VOLV-B.ST")
    order = broker.place_order("a", "VOLV-B", "buy", 10)
    assert order.status == "filled"
    assert order.fill_price == inst.ask
    acct = broker.account("a")
    assert acct.positions["VOLV-B.ST"].quantity == 10

    sell = broker.place_order("a", "VOLV-B.ST", "sell", 10)
    assert sell.status == "filled"
    assert "VOLV-B.ST" not in acct.positions
    # Spread plus two commissions make an instant round trip lose money
    assert acct.cash < acct.starting_cash
    assert acct.commission_paid >= 2 * COMMISSION_MIN


def test_insufficient_cash_rejected(broker: Broker):
    with pytest.raises(OrderError, match="buying power"):
        broker.place_order("a", "VOLV-B", "buy", 10_000_000)


def test_no_shorting(broker: Broker):
    with pytest.raises(OrderError, match="no shorting"):
        broker.place_order("a", "SAND", "sell", 1)


def test_unknown_ticker(broker: Broker):
    with pytest.raises(OrderError, match="unknown ticker"):
        broker.place_order("a", "NOPE", "buy", 1)


def test_limit_order_fills_when_price_crosses(broker: Broker, market: Market):
    inst = market.get("ERIC-B.ST")
    limit = round(inst.ask * 0.95, 2)
    order = broker.place_order("a", "ERIC-B", "buy", 5, type="limit", limit_price=limit)
    assert order.status == "open"
    market.shock("ERIC-B.ST", -10)
    broker.on_tick()
    assert order.status == "filled"
    assert order.fill_price <= limit


def test_stop_loss_triggers(broker: Broker, market: Market):
    broker.place_order("a", "SAND", "buy", 20)
    inst = market.get("SAND.ST")
    stop = broker.place_order("a", "SAND", "sell", 20, type="stop", stop_price=inst.bid * 0.97)
    assert stop.status == "open"
    market.shock("SAND.ST", -6)
    broker.on_tick()
    assert stop.status == "filled"
    assert broker.account("a").realized_pnl < 0


def test_sell_orders_reserve_shares(broker: Broker, market: Market):
    broker.place_order("a", "SAND", "buy", 10)
    price = market.get("SAND").bid
    broker.place_order("a", "SAND", "sell", 10, type="limit", limit_price=price * 2)
    with pytest.raises(OrderError, match="only 0 shares free"):
        broker.place_order("a", "SAND", "sell", 1)


def test_cancel_order(broker: Broker, market: Market):
    price = market.get("SAND").ask * 0.5
    order = broker.place_order("a", "SAND", "buy", 1, type="limit", limit_price=price)
    broker.cancel_order("a", order.id)
    assert order.status == "cancelled"
    with pytest.raises(OrderError, match="cancelled"):
        broker.cancel_order("a", order.id)


def test_accounts_are_isolated(broker: Broker):
    broker.place_order("alice", "SAND", "buy", 1)
    assert broker.account("bob").positions == {}


# -- HTTP API -------------------------------------------------------------

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from swingtrader.sim.server import create_app  # noqa: E402


@pytest.fixture
def client(market: Market) -> TestClient:
    app = create_app(PASSWORD, market=market, start_ticker=False)
    with TestClient(app) as c:
        yield c


AUTH = {"Authorization": f"Bearer {PASSWORD}", "X-Account": "bot1"}


def test_api_requires_password(client: TestClient):
    assert client.get("/api/market").status_code == 401
    assert client.get("/api/market", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/market", headers={"X-API-Key": PASSWORD}).status_code == 200


def test_guide_is_public(client: TestClient):
    r = client.get("/api/guide")
    assert r.status_code == 200
    assert "X-Account" in r.text


def test_api_trade_flow(client: TestClient):
    quotes = client.get("/api/market", headers=AUTH).json()["quotes"]
    assert {q["ticker"] for q in quotes} == set(TICKERS)

    r = client.post(
        "/api/orders",
        headers=AUTH,
        json={"ticker": "VOLV-B", "side": "buy", "quantity": 3, "note": "test"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "filled"

    acct = client.get("/api/account", headers=AUTH).json()
    assert acct["account"] == "bot1"
    assert acct["positions"][0]["quantity"] == 3
    assert client.get("/api/trades", headers=AUTH).json()[0]["note"] == "test"

    bad = client.post(
        "/api/orders", headers=AUTH, json={"ticker": "SAND", "side": "sell", "quantity": 1}
    )
    assert bad.status_code == 400


def test_dashboard_login_flow(client: TestClient):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"

    r = client.post("/login", data={"password": "wrong"}, follow_redirects=False)
    assert "error" in r.headers["location"]

    r = client.post("/login", data={"password": PASSWORD}, follow_redirects=False)
    assert r.headers["location"] == "/"
    page = client.get("/")
    assert page.status_code == 200
    assert "Paper-Trading Sandbox" in page.text
    assert client.get("/api/state").status_code == 200


def test_control_shock(client: TestClient, market: Market):
    before = market.get("SAND").price
    r = client.post("/api/control", headers=AUTH, json={"shock_ticker": "SAND", "shock_pct": -20})
    assert r.status_code == 200
    assert market.get("SAND").price == pytest.approx(before * 0.8)
