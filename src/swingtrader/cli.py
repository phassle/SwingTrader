"""SwingTrader CLI — Run the evening scan.

Usage:
    python -m swingtrader.cli              # Scan full universe (auto-saves)
    python -m swingtrader.cli --top 10     # Show top 10 only
    python -m swingtrader.cli --ticker VOLV-B.ST  # Scan single ticker
    python -m swingtrader.cli --review             # Review past scans
    python -m swingtrader.cli --review 2026-03-29  # Review specific date
    python -m swingtrader.cli --evaluate           # Evaluate signals vs current prices
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import structlog

from swingtrader.data.fetcher import get_provider
from swingtrader.data.universe import get_universe
from swingtrader.indicators.technical import add_all_indicators
from swingtrader.scoring.engine import ScoreBreakdown, score_ticker

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger()

SCANS_DIR = Path("scans")


def run_scan(
    tickers: list[str] | None = None,
    top_n: int = 10,
) -> list[ScoreBreakdown]:
    """Run the full scan pipeline: fetch → indicators → score → rank → save."""

    if tickers is None:
        tickers = get_universe()

    logger.info("scan_start", tickers=len(tickers))

    # 1. Fetch data
    provider = get_provider("yahoo")
    data = provider.fetch(tickers, period="1y")

    if not data:
        logger.error("no_data_fetched")
        return []

    # 2. Calculate indicators + score each ticker
    scores: list[ScoreBreakdown] = []
    for ticker, ticker_data in data.items():
        try:
            daily = add_all_indicators(ticker_data.daily)
            weekly = ticker_data.weekly
            score = score_ticker(ticker, daily, weekly)
            scores.append(score)
        except Exception as e:
            logger.warning("scoring_failed", ticker=ticker, error=str(e))

    # 3. Sort by score descending
    scores.sort(key=lambda s: s.total, reverse=True)

    # 4. Display results
    print_results(scores, top_n)

    # 5. Always auto-save for later evaluation
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    save_path = SCANS_DIR / f"scan_{date_str}.json"
    save_results(scores, save_path)

    logger.info("scan_complete", scored=len(scores), top_score=scores[0].total if scores else 0)
    return scores


def print_results(scores: list[ScoreBreakdown], top_n: int = 10) -> None:
    """Print formatted scan results to terminal."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("\n" + "=" * 80)
    print(f"  SwingTrader Signal Scanner — {now}")
    print(f"  Scanned: {len(scores)} tickers | Showing top {min(top_n, len(scores))}")
    print("=" * 80)

    # Header
    print(
        f"  {'#':>2}  {'Ticker':<14} {'Score':>5} {'Grade':>5} "
        f"{'Setup':<12} {'Entry':>8} {'Stop':>8} {'Target':>8}  {'Action'}"
    )
    print("  " + "-" * 76)

    for i, s in enumerate(scores[:top_n], 1):
        if s.disqualified:
            print(f"  {i:>2}  {s.ticker:<14} {'DQ':>5} {'---':>5} {'---':<12} {'---':>8} {'---':>8} {'---':>8}  {s.disqualify_reason}")
        else:
            print(
                f"  {i:>2}  {s.ticker:<14} {s.total:>5} {s.grade:>5} "
                f"{s.setup_type:<12} {s.entry_price:>8.2f} {s.stop_price:>8.2f} "
                f"{s.target_price:>8.2f}  {s.action}"
            )

    print("=" * 80)

    # Show detail for top 3
    print("\n  TOP SIGNALS — Detail:")
    for s in scores[:3]:
        if s.disqualified:
            continue
        print(f"\n  {s.ticker} ({s.grade}-tier, {s.total}/20)")
        for note in s.notes:
            print(f"    • {note}")

    print()


def save_results(scores: list[ScoreBreakdown], path: Path) -> None:
    """Save scan results to JSON for history tracking."""
    results = {
        "scan_date": datetime.now().isoformat(),
        "tickers_scanned": len(scores),
        "signals": [
            {
                "ticker": s.ticker,
                "score": s.total,
                "grade": s.grade,
                "setup_type": s.setup_type,
                "entry": s.entry_price,
                "stop": s.stop_price,
                "target": s.target_price,
                "disqualified": s.disqualified,
                "disqualify_reason": s.disqualify_reason,
                "breakdown": {
                    "trend_alignment": s.trend_alignment,
                    "level_quality": s.level_quality,
                    "catalyst_quality": s.catalyst_quality,
                    "volume": s.volume,
                    "liquidity": s.liquidity,
                    "market_sector": s.market_sector,
                    "risk_reward": s.risk_reward,
                    "timing": s.timing,
                },
                "notes": s.notes,
                "outcome": None,  # filled in by --evaluate
            }
            for s in scores
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info("results_saved", path=str(path))
    export_playground_data()


def list_scans() -> list[Path]:
    """Return all saved scan files, newest first."""
    if not SCANS_DIR.exists():
        return []
    return sorted(SCANS_DIR.glob("scan_*.json"), reverse=True)


def load_scan(path: Path) -> dict:
    """Load a saved scan from JSON."""
    return json.loads(path.read_text())


def review_scans(date_filter: str | None = None) -> None:
    """Show past scans. Optionally filter by date prefix (e.g. '2026-03-29')."""
    scans = list_scans()
    if not scans:
        print("  No saved scans found in scans/")
        return

    if date_filter:
        scans = [s for s in scans if date_filter in s.name]
        if not scans:
            print(f"  No scans matching '{date_filter}'")
            return

    print("\n" + "=" * 80)
    print("  SwingTrader — Scan History")
    print("=" * 80)

    for scan_path in scans[:20]:
        data = load_scan(scan_path)
        scan_date = data["scan_date"][:16].replace("T", " ")
        signals = data["signals"]
        actionable = [s for s in signals if s["grade"] in ("A", "B") and not s["disqualified"]]
        watchlist = [s for s in signals if s["grade"] == "C" and not s["disqualified"]]
        evaluated = sum(1 for s in signals if s.get("outcome"))

        status = ""
        if evaluated > 0:
            wins = sum(1 for s in signals if s.get("outcome") == "target_hit")
            losses = sum(1 for s in signals if s.get("outcome") == "stopped_out")
            status = f"  [{wins}W/{losses}L/{evaluated} evaluated]"

        print(f"\n  {scan_date}  ({data['tickers_scanned']} scanned)")
        if actionable:
            tickers_str = ", ".join(f"{s['ticker']}({s['score']})" for s in actionable)
            print(f"    BUY:       {tickers_str}")
        if watchlist:
            tickers_str = ", ".join(f"{s['ticker']}({s['score']})" for s in watchlist)
            print(f"    WATCHLIST: {tickers_str}")
        if status:
            print(f"    Results:  {status}")

    print("\n" + "=" * 80)
    print(f"  {len(list_scans())} total scans saved")
    print("  Use --evaluate to check signals against current prices")
    print("=" * 80 + "\n")


def evaluate_scan(date_filter: str | None = None, top_n: int = 10) -> None:
    """Fetch current prices and compare against saved signal entries."""
    scans = list_scans()
    if not scans:
        print("  No saved scans to evaluate.")
        return

    # Pick the scan to evaluate
    if date_filter:
        matches = [s for s in scans if date_filter in s.name]
        if not matches:
            print(f"  No scans matching '{date_filter}'")
            return
        scan_path = matches[0]
    else:
        # Default: most recent scan that isn't from today
        today = datetime.now().strftime("%Y-%m-%d")
        older = [s for s in scans if today not in s.name]
        scan_path = older[0] if older else scans[0]

    data = load_scan(scan_path)
    signals = [s for s in data["signals"] if not s["disqualified"]][:top_n]

    if not signals:
        print("  No actionable signals in this scan.")
        return

    # Fetch current prices — use yfinance directly to avoid the 50-row minimum in our provider
    import yfinance as yf
    import logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    logging.getLogger("peewee").setLevel(logging.CRITICAL)

    tickers = [s["ticker"] for s in signals]
    current_data: dict[str, float] = {}
    try:
        raw = yf.download(tickers, period="5d", interval="1d", progress=False, threads=True)
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    close_series = raw["Close"]
                else:
                    close_series = raw[("Close", ticker)]
                close_series = close_series.dropna()
                if len(close_series) > 0:
                    current_data[ticker] = float(close_series.iloc[-1])
            except (KeyError, TypeError, IndexError):
                continue
    except Exception as e:
        logger.error("evaluate_fetch_failed", error=str(e))
        return

    scan_date = data["scan_date"][:10]
    print("\n" + "=" * 90)
    print(f"  SwingTrader — Evaluate Scan from {scan_date}")
    print("=" * 90)
    print(
        f"  {'Ticker':<14} {'Grade':>5} {'Entry':>8} {'Stop':>8} {'Target':>8} "
        f"{'Now':>8} {'P&L%':>7} {'Status'}"
    )
    print("  " + "-" * 82)

    updated_signals = {s["ticker"]: s for s in data["signals"]}

    for sig in signals:
        ticker = sig["ticker"]
        entry = sig["entry"]
        stop = sig["stop"]
        target = sig["target"]

        if ticker in current_data:
            current_price = current_data[ticker]
            pnl_pct = ((current_price - entry) / entry) * 100

            # Determine outcome
            if current_price >= target:
                status = "TARGET HIT"
                color = "\033[32m"  # green
                outcome = "target_hit"
            elif current_price <= stop:
                status = "STOPPED OUT"
                color = "\033[31m"  # red
                outcome = "stopped_out"
            elif current_price > entry:
                status = "open (profit)"
                color = "\033[33m"  # yellow
                outcome = "open"
            elif current_price < entry:
                status = "open (loss)"
                color = "\033[33m"
                outcome = "open"
            else:
                status = "open (flat)"
                color = "\033[0m"
                outcome = "open"

            reset = "\033[0m"
            print(
                f"  {ticker:<14} {sig['grade']:>5} {entry:>8.2f} {stop:>8.2f} {target:>8.2f} "
                f"{color}{current_price:>8.2f} {pnl_pct:>+6.1f}%  {status}{reset}"
            )

            # Auto-update outcome if target/stop hit
            if outcome in ("target_hit", "stopped_out"):
                updated_signals[ticker]["outcome"] = outcome
        else:
            print(f"  {ticker:<14} {sig['grade']:>5} {entry:>8.2f} {stop:>8.2f} {target:>8.2f} {'---':>8} {'---':>7}  fetch failed")

    # Summary
    outcomes = [s.get("outcome") for s in updated_signals.values() if s.get("outcome")]
    wins = outcomes.count("target_hit")
    losses = outcomes.count("stopped_out")
    if wins + losses > 0:
        print("\n  " + "-" * 82)
        print(f"  Resolved: {wins}W / {losses}L — Win rate: {wins/(wins+losses)*100:.0f}%")

    print("=" * 90 + "\n")

    # Save updated outcomes back
    data["signals"] = list(updated_signals.values())
    scan_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    logger.info("outcomes_updated", path=str(scan_path))
    export_playground_data()


def evaluate_all_pending(top_n: int = 10) -> None:
    """Evaluate all past scans that have unresolved signals."""
    today = datetime.now().strftime("%Y-%m-%d")
    for scan_path in list_scans():
        if today in scan_path.name:
            continue  # skip today's scan — no price movement yet
        data = load_scan(scan_path)
        unresolved = [
            s for s in data["signals"]
            if not s["disqualified"] and s.get("outcome") in (None, "open")
        ]
        if unresolved:
            scan_date = scan_path.name.replace("scan_", "").replace(".json", "")
            evaluate_scan(date_filter=scan_date, top_n=top_n)


def export_playground_data() -> None:
    """Write all scan history to scans/scan-data.js for the playground."""
    scans = list_scans()
    if not scans:
        return

    all_data = []
    for scan_path in scans:
        all_data.append(load_scan(scan_path))

    js_content = "// Auto-generated by SwingTrader CLI — do not edit\n"
    js_content += f"window.SCAN_HISTORY = {json.dumps(all_data, indent=2, ensure_ascii=False)};\n"

    out = SCANS_DIR / "scan-data.js"
    out.write_text(js_content)
    logger.info("playground_data_exported", path=str(out), scans=len(all_data))


def main() -> None:
    parser = argparse.ArgumentParser(description="SwingTrader Signal Scanner")
    parser.add_argument("--top", type=int, default=10, help="Number of top signals to show")
    parser.add_argument("--ticker", type=str, help="Scan a single ticker (e.g. VOLV-B.ST)")
    parser.add_argument("--review", nargs="?", const="", default=None, help="Review past scans (optional date filter, e.g. 2026-03-29)")
    parser.add_argument("--evaluate", nargs="?", const="", default=None, help="Evaluate past signals vs current prices (optional date filter)")
    parser.add_argument("--full", action="store_true", help="Run full workflow: scan → review history → evaluate previous signals")
    args = parser.parse_args()

    if args.full:
        tickers = [args.ticker] if args.ticker else None
        run_scan(tickers=tickers, top_n=args.top)
        evaluate_all_pending(top_n=args.top)
        review_scans()
        return

    if args.review is not None:
        review_scans(date_filter=args.review or None)
        return

    if args.evaluate is not None:
        evaluate_scan(date_filter=args.evaluate or None, top_n=args.top)
        return

    tickers = [args.ticker] if args.ticker else None
    run_scan(tickers=tickers, top_n=args.top)


if __name__ == "__main__":
    main()
