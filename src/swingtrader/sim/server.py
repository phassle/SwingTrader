"""HTTP server for the paper-trading sandbox.

External agents authenticate with the shared password, sent either as
``Authorization: Bearer <password>`` or ``X-API-Key: <password>``. The
browser dashboard uses a login form that sets a signed session cookie.
Each agent trades in its own account, chosen with the ``X-Account`` header.
"""

import asyncio
import contextlib
import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict
from importlib.resources import files
from typing import Annotated, Literal

import structlog
from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field

from swingtrader.sim.broker import DEFAULT_CASH, Broker, OrderError
from swingtrader.sim.market import Market

logger = structlog.get_logger()

COOKIE = "sim_session"


class OrderIn(BaseModel):
    ticker: str = Field(examples=["VOLV-B.ST"])
    side: Literal["buy", "sell"]
    quantity: int = Field(gt=0)
    type: Literal["market", "limit", "stop"] = "market"
    limit_price: float | None = Field(default=None, gt=0)
    stop_price: float | None = Field(default=None, gt=0)
    note: str = Field(default="", description="Free-text reason, shown in the trade log")


class ResetIn(BaseModel):
    cash: float = Field(default=DEFAULT_CASH, gt=0)


class ControlIn(BaseModel):
    paused: bool | None = None
    tick_seconds: float | None = Field(default=None, ge=0.05, le=60)
    shock_ticker: str | None = None
    shock_pct: float | None = Field(default=None, ge=-90, le=200)
    new_session: bool = False


AGENT_GUIDE = """\
SwingTrader paper-trading sandbox (all prices are SIMULATED, no real money)

Auth: send header  Authorization: Bearer <password>   (or X-API-Key: <password>)
Account: send header X-Account: <your-agent-name>  (default "agent"). Each name is a
separate account that starts with {cash:,.0f} SEK. Long only, no shorting.
Commission: 0.069 % per trade, min 1 SEK. Market orders fill at ask (buy) / bid (sell).

Endpoints (JSON):
  GET    /api/market                     all quotes + index level + tick counter
  GET    /api/market/{{ticker}}            one quote
  GET    /api/market/{{ticker}}/history?n=200   recent [tick, price] pairs
  GET    /api/account                    cash, equity, positions, open orders
  GET    /api/orders?status=open         orders (open|filled|cancelled|rejected|all)
  POST   /api/orders                     place order, body:
         {{"ticker":"VOLV-B.ST","side":"buy","quantity":10,"type":"market",
          "limit_price":null,"stop_price":null,"note":"why"}}
         type: market | limit | stop
  DELETE /api/orders/{{id}}                cancel an open order
  GET    /api/trades                     filled trades
  POST   /api/account/reset              body {{"cash":100000}}
  GET    /api/events                     recent market events (news jumps, shocks)

Prices tick every ~{tick}s. Tickers use the .ST suffix (VOLV-B or VOLV-B.ST both work).
OpenAPI schema: /openapi.json   Interactive docs: /docs
"""


def create_app(
    password: str,
    tick_seconds: float = 1.0,
    seed: int | None = None,
    market: Market | None = None,
    start_ticker: bool = True,
) -> FastAPI:
    if not password:
        raise ValueError("password must not be empty")

    state = {"paused": False, "tick_seconds": tick_seconds}
    mkt = market or Market(seed=seed)
    broker = Broker(mkt)
    session_secret = secrets.token_bytes(32)
    session_token = hmac.new(session_secret, password.encode(), hashlib.sha256).hexdigest()

    async def run_ticks() -> None:
        while True:
            await asyncio.sleep(state["tick_seconds"])
            if not state["paused"]:
                mkt.step()
                broker.on_tick()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        task = asyncio.create_task(run_ticks()) if start_ticker else None
        logger.info("sim_started", instruments=len(mkt.instruments), tick_seconds=tick_seconds)
        yield
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="SwingTrader Paper-Trading Sandbox",
        description="Simulated Nasdaq Stockholm market for AI agents. See /api/guide.",
        lifespan=lifespan,
    )
    app.state.market = mkt
    app.state.broker = broker
    app.state.sim = state

    def check_password(candidate: str | None) -> bool:
        return candidate is not None and hmac.compare_digest(candidate.encode(), password.encode())

    async def require_auth(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
        x_api_key: Annotated[str | None, Header()] = None,
    ) -> None:
        bearer = None
        if authorization and authorization.lower().startswith("bearer "):
            bearer = authorization[7:].strip()
        cookie = request.cookies.get(COOKIE)
        if check_password(bearer) or check_password(x_api_key):
            return
        if cookie and hmac.compare_digest(cookie, session_token):
            return
        logger.warning("auth_failed", client=request.client.host if request.client else None)
        raise HTTPException(401, "invalid or missing password", {"WWW-Authenticate": "Bearer"})

    def account_name(x_account: Annotated[str | None, Header()] = None) -> str:
        name = (x_account or "agent").strip()[:40]
        return name or "agent"

    Auth = Depends(require_auth)
    AccountName = Annotated[str, Depends(account_name)]

    def get_inst(ticker: str):
        try:
            return mkt.get(ticker)
        except KeyError as e:
            raise HTTPException(404, f"unknown ticker {ticker!r}") from e

    # -- public -----------------------------------------------------------

    @app.get("/api/guide", response_class=PlainTextResponse)
    async def guide() -> str:
        return AGENT_GUIDE.format(cash=DEFAULT_CASH, tick=state["tick_seconds"])

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(error: str = "") -> str:
        msg = '<p class="err">Fel lösenord</p>' if error else ""
        return LOGIN_HTML.replace("{{msg}}", msg)

    @app.post("/login")
    async def login(request: Request, password_in: Annotated[str, Form(alias="password")]):
        if not check_password(password_in):
            logger.warning("login_failed", client=request.client.host if request.client else None)
            return RedirectResponse("/login?error=1", status_code=303)
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(COOKIE, session_token, httponly=True, samesite="strict")
        return resp

    @app.get("/logout")
    async def logout():
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie(COOKIE)
        return resp

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        cookie = request.cookies.get(COOKIE)
        if not (cookie and hmac.compare_digest(cookie, session_token)):
            return RedirectResponse("/login", status_code=303)
        return files("swingtrader.sim").joinpath("dashboard.html").read_text(encoding="utf-8")

    # -- market -----------------------------------------------------------

    @app.get("/api/market", dependencies=[Auth])
    async def market_quotes() -> dict:
        return {"tick": mkt.tick_count, "index": round(mkt.index_level, 2), "quotes": mkt.quotes()}

    @app.get("/api/market/{ticker}", dependencies=[Auth])
    async def market_quote(ticker: str) -> dict:
        return get_inst(ticker).quote()

    @app.get("/api/market/{ticker}/history", dependencies=[Auth])
    async def market_history(ticker: str, n: int = 200) -> dict:
        inst = get_inst(ticker)
        n = max(1, min(n, len(inst.history)))
        return {"ticker": inst.ticker, "history": list(inst.history)[-n:]}

    @app.get("/api/events", dependencies=[Auth])
    async def events() -> list[dict]:
        return list(mkt.events)

    # -- trading ----------------------------------------------------------

    @app.get("/api/account", dependencies=[Auth])
    async def account(name: AccountName) -> dict:
        return broker.snapshot(broker.account(name))

    @app.post("/api/account/reset", dependencies=[Auth])
    async def reset(name: AccountName, body: ResetIn | None = None) -> dict:
        return broker.snapshot(broker.reset(name, (body or ResetIn()).cash))

    @app.get("/api/orders", dependencies=[Auth])
    async def orders(name: AccountName, status: str = "open") -> list[dict]:
        acct = broker.account(name)
        return [asdict(o) for o in acct.orders if status == "all" or o.status == status]

    @app.post("/api/orders", dependencies=[Auth], status_code=201)
    async def place(name: AccountName, body: OrderIn) -> dict:
        try:
            order = broker.place_order(name, **body.model_dump())
        except OrderError as e:
            raise HTTPException(400, str(e)) from e
        return asdict(order)

    @app.delete("/api/orders/{order_id}", dependencies=[Auth])
    async def cancel(name: AccountName, order_id: int) -> dict:
        try:
            return asdict(broker.cancel_order(name, order_id))
        except OrderError as e:
            raise HTTPException(400, str(e)) from e

    @app.get("/api/trades", dependencies=[Auth])
    async def trades(name: AccountName, limit: int = 200) -> list[dict]:
        return broker.account(name).trades[-limit:]

    # -- dashboard / control ---------------------------------------------

    @app.get("/api/state", dependencies=[Auth])
    async def full_state() -> dict:
        """Everything the dashboard needs in one call."""
        return {
            "market": mkt.summary(),
            "sim": state,
            "quotes": mkt.quotes(),
            "sparks": {
                t: [p for _, p in list(i.history)[-60:]] for t, i in mkt.instruments.items()
            },
            "events": list(mkt.events)[:15],
            "accounts": {
                n: {
                    **broker.snapshot(a),
                    "trades": a.trades[-50:],
                    "equity_curve": a.equity_curve[-300:],
                }
                for n, a in broker.accounts.items()
            },
        }

    @app.post("/api/control", dependencies=[Auth])
    async def control(body: ControlIn) -> dict:
        if body.paused is not None:
            state["paused"] = body.paused
        if body.tick_seconds is not None:
            state["tick_seconds"] = body.tick_seconds
        if body.shock_pct is not None:
            if body.shock_ticker:
                get_inst(body.shock_ticker)
            mkt.shock(body.shock_ticker or None, body.shock_pct)
            broker.on_tick()
        if body.new_session:
            mkt.new_session()
        logger.info("sim_control", **body.model_dump(exclude_none=True))
        return {"sim": state, "market": mkt.summary()}

    return app


def app_from_env() -> FastAPI:
    """Factory for ``uvicorn --factory``. Reads SIM_PASSWORD from the environment."""
    password = os.environ.get("SIM_PASSWORD", "")
    if not password:
        raise SystemExit("Set SIM_PASSWORD before starting the sandbox")
    return create_app(
        password=password,
        tick_seconds=float(os.environ.get("SIM_TICK_SECONDS", "1.0")),
        seed=int(os.environ["SIM_SEED"]) if os.environ.get("SIM_SEED") else None,
    )


LOGIN_HTML = """<!doctype html>
<html lang="sv"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sandbox login</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--muted:#5d6670;--line:#d9dde3;--acc:#2563eb;--err:#c0392b}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#171b21;--fg:#e6e9ee;--muted:#98a1ad;
--line:#2a3039;--acc:#5b8cff;--err:#ff6b5b}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;
display:grid;place-items:center;min-height:100vh;padding:16px;box-sizing:border-box}
form{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:28px;
width:100%;max-width:320px}
h1{font-size:18px;margin:0 0 4px}p{color:var(--muted);margin:0 0 18px;font-size:13px}
input{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--line);border-radius:6px;
background:var(--bg);color:var(--fg);font-size:15px;margin-bottom:12px}
button{width:100%;padding:10px;border:0;border-radius:6px;background:var(--acc);color:#fff;
font-size:15px;cursor:pointer}.err{color:var(--err)}
</style></head><body>
<form method="post" action="/login"><h1>Paper-trading sandbox</h1>
<p>Simulerade kurser. Inga riktiga pengar.</p>{{msg}}
<input type="password" name="password" placeholder="Lösenord" autofocus required>
<button>Logga in</button></form></body></html>"""
