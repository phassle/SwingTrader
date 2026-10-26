"""Start the sandbox: SIM_PASSWORD=... python -m swingtrader.sim [--host H] [--port P]."""

from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="SwingTrader paper-trading sandbox")
    parser.add_argument("--host", default=os.environ.get("SIM_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SIM_PORT") or os.environ.get("PORT") or "8000"),
    )
    args = parser.parse_args()
    uvicorn.run("swingtrader.sim.server:app_from_env", factory=True, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
