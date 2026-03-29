"""Crash-Bounce Scanner — find extreme gap-down candidates for next-day bounce.

Scans for stocks that dropped ≥40% intraday (close ≤ 0.60 × open),
classifies the drop, and identifies bounce trade candidates.

Usage:
    PYTHONPATH=src python -m swingtrader.crash_bounce
    PYTHONPATH=src python -m swingtrader.crash_bounce --days 30
    PYTHONPATH=src python -m swingtrader.crash_bounce --threshold 0.50
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import structlog
import yfinance as yf

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
logger = structlog.get_logger()

# Suppress yfinance noise
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)

SCANS_DIR = Path("scans/crash-bounce")

# Broad US universe — S&P 500 + mid-caps where crashes actually happen
# We use screener results from Yahoo instead of hardcoding 3000 tickers
SCAN_INDICES = ["^GSPC", "^NDX", "^RUT"]


def scan_today_crashes(drop_pct: float = 25.0) -> list[dict]:
    """Use Yahoo EquityQuery to find today's crashes across the entire US market.

    This searches ALL US equities, not a fixed ticker list.
    Returns quote dicts with symbol, price, change%, volume, marketCap.
    """
    try:
        q = yf.EquityQuery("and", [
            yf.EquityQuery("lt", ["percentchange", -drop_pct]),
            yf.EquityQuery("gt", ["intradaymarketcap", 50_000_000]),  # >$50M mcap
            yf.EquityQuery("gt", ["dayvolume", 500_000]),              # >500k volume
            yf.EquityQuery("eq", ["region", "us"]),
        ])
        result = yf.screen(q, count=200)
        if result and "quotes" in result:
            quotes = result["quotes"]
            logger.info("screener_found", count=len(quotes), threshold=f"-{drop_pct}%")
            return quotes
        return []
    except Exception as e:
        logger.warning("screener_failed", error=str(e))
        return []


def get_full_us_universe(min_mcap: int = 50_000_000) -> list[str]:
    """Get ALL US equities from Yahoo screener via pagination.

    Paginates through Yahoo's screener API (250 per page) to build
    a complete list of US stocks above the market cap threshold.

    Returns ~4000-10000 tickers depending on mcap filter.
    """
    q = yf.EquityQuery("and", [
        yf.EquityQuery("gt", ["intradaymarketcap", min_mcap]),
        yf.EquityQuery("eq", ["region", "us"]),
    ])

    all_tickers: list[str] = []
    max_offset = 10_000  # Yahoo's hard ceiling

    for offset in range(0, max_offset, 250):
        try:
            result = yf.screen(q, size=250, offset=offset,
                               sortField="intradaymarketcap", sortAsc=False)
            if not result or "quotes" not in result:
                break
            batch = [r["symbol"] for r in result["quotes"]]
            all_tickers.extend(batch)
            if offset % 2000 == 0 and offset > 0:
                logger.info("universe_progress", loaded=len(all_tickers))
            if len(batch) < 250:
                break
        except Exception as e:
            logger.warning("universe_page_failed", offset=offset, error=str(e))
            break

    unique = sorted(set(all_tickers))
    logger.info("universe_loaded", count=len(unique), min_mcap=f"${min_mcap/1e6:.0f}M")
    return unique


def get_scan_universe() -> list[str]:
    """Get full US universe for historical scanning."""
    return get_full_us_universe()


def _extract_crash_candidates(
    tickers: list[str],
    raw: pd.DataFrame,
    lookback_days: int,
    drop_threshold: float,
    single_ticker: bool = False,
) -> list[dict]:
    """Extract crash candidates from downloaded data."""
    candidates = []

    for ticker in tickers:
        try:
            if single_ticker:
                df = raw
            else:
                df = raw[ticker]

            df = df.dropna(how="all")
            if df.empty or len(df) < 5:
                continue

            for i in range(max(0, len(df) - lookback_days), len(df)):
                row = df.iloc[i]
                date = df.index[i]

                if pd.isna(row["Open"]) or pd.isna(row["Close"]) or row["Open"] <= 0:
                    continue

                drop_ratio = row["Close"] / row["Open"]
                drop_pct = (1 - drop_ratio) * 100
                volume = row.get("Volume", 0)

                if drop_ratio > drop_threshold:
                    continue
                if volume < 500_000:
                    continue
                if row["Close"] < 0.50:
                    continue

                prior = df.iloc[max(0, i-20):i]
                avg_vol_20d = prior["Volume"].mean() if len(prior) > 0 else 0

                bounce_data = None
                if i + 1 < len(df):
                    next_row = df.iloc[i + 1]
                    if not pd.isna(next_row["Open"]) and not pd.isna(next_row["Close"]):
                        bounce_open = next_row["Open"]
                        bounce_close = next_row["Close"]
                        bounce_high = next_row["High"]
                        bounce_low = next_row["Low"]
                        bounce_from_close = ((bounce_close - row["Close"]) / row["Close"]) * 100
                        bounce_intraday_high = ((bounce_high - bounce_open) / bounce_open) * 100
                        bounce_data = {
                            "next_open": round(float(bounce_open), 2),
                            "next_close": round(float(bounce_close), 2),
                            "next_high": round(float(bounce_high), 2),
                            "next_low": round(float(bounce_low), 2),
                            "bounce_close_pct": round(float(bounce_from_close), 2),
                            "bounce_intraday_high_pct": round(float(bounce_intraday_high), 2),
                            "tp_hit": bool(bounce_intraday_high >= 3.0),
                            "sl_hit": bool(((bounce_low - bounce_open) / bounce_open) * 100 <= -1.5),
                        }

                prior_close = float(df.iloc[i-1]["Close"]) if i > 0 else None
                gap_down = None
                if prior_close and prior_close > 0:
                    gap_down = round(((row["Open"] - prior_close) / prior_close) * 100, 2)

                candidates.append({
                    "ticker": ticker,
                    "date": str(date.date()) if hasattr(date, "date") else str(date)[:10],
                    "open": round(float(row["Open"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "volume": int(volume),
                    "drop_pct": round(float(drop_pct), 1),
                    "gap_down_pct": gap_down,
                    "avg_vol_20d": int(avg_vol_20d) if avg_vol_20d else 0,
                    "vol_ratio": round(float(volume / avg_vol_20d), 1) if avg_vol_20d > 0 else 0,
                    "bounce": bounce_data,
                })

        except (KeyError, TypeError, IndexError):
            continue

    return candidates


def scan_for_crashes(
    tickers: list[str],
    lookback_days: int = 5,
    drop_threshold: float = 0.60,
    batch_size: int = 500,
) -> list[dict]:
    """Scan tickers for extreme intraday drops. Handles large universes in batches.

    Args:
        tickers: List of Yahoo tickers to scan
        lookback_days: How many days back to look
        drop_threshold: Close/Open ratio threshold (0.60 = 40% drop)
        batch_size: Download batch size (default 500)

    Returns:
        List of crash candidate dicts, sorted by drop severity
    """
    if not tickers:
        logger.error("no_tickers")
        return []

    logger.info("crash_scan_start", tickers=len(tickers), lookback_days=lookback_days,
                threshold=f"{(1-drop_threshold)*100:.0f}%",
                batches=len(range(0, len(tickers), batch_size)))

    period = f"{lookback_days + 10}d" if lookback_days <= 30 else "1y"
    candidates = []
    failed_batches = 0

    for batch_start in range(0, len(tickers), batch_size):
        batch = tickers[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(tickers) + batch_size - 1) // batch_size

        if total_batches > 1:
            logger.info("batch_download", batch=f"{batch_num}/{total_batches}",
                        tickers=len(batch), candidates_so_far=len(candidates))

        try:
            raw = yf.download(batch, period=period, interval="1d",
                              progress=False, threads=True, group_by="ticker")
        except Exception as e:
            logger.warning("batch_failed", batch=batch_num, error=str(e))
            failed_batches += 1
            continue

        single = len(batch) == 1
        batch_candidates = _extract_crash_candidates(
            batch, raw, lookback_days, drop_threshold, single_ticker=single
        )
        candidates.extend(batch_candidates)

    candidates.sort(key=lambda c: c["drop_pct"], reverse=True)
    logger.info("crash_scan_complete", candidates=len(candidates),
                failed_batches=failed_batches)
    return candidates


def print_crash_results(candidates: list[dict]) -> None:
    """Print formatted crash-bounce scan results."""
    print("\n" + "=" * 100)
    print("  Crash-Bounce Scanner — Extreme Gap-Down Candidates")
    print(f"  Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Threshold: ≥40% drop | Found: {len(candidates)}")
    print("=" * 100)

    if not candidates:
        print("\n  No crash candidates found in the scan window.")
        print("  (This is normal — ≥40% drops are rare events)\n")
        print("=" * 100)
        return

    # Table header
    print(
        f"  {'Date':<12} {'Ticker':<8} {'Drop%':>6} {'Open':>8} {'Close':>8} "
        f"{'Volume':>10} {'VolX':>5} {'Gap%':>6}  {'Next-Day Bounce'}"
    )
    print("  " + "-" * 92)

    for c in candidates:
        bounce_str = ""
        if c["bounce"]:
            b = c["bounce"]
            color = "\033[32m" if b["bounce_close_pct"] > 0 else "\033[31m"
            reset = "\033[0m"
            tp = " TP!" if b["tp_hit"] else ""
            sl = " SL!" if b["sl_hit"] else ""
            bounce_str = (
                f"{color}{b['bounce_close_pct']:>+5.1f}% close"
                f"  {b['bounce_intraday_high_pct']:>+5.1f}% peak{tp}{sl}{reset}"
            )
        else:
            bounce_str = "\033[33m  (pending — no next-day data)\033[0m"

        gap = f"{c['gap_down_pct']:>+5.1f}%" if c["gap_down_pct"] is not None else "   ---"

        print(
            f"  {c['date']:<12} {c['ticker']:<8} {c['drop_pct']:>5.1f}% "
            f"{c['open']:>8.2f} {c['close']:>8.2f} "
            f"{c['volume']:>10,} {c['vol_ratio']:>4.1f}x {gap}  {bounce_str}"
        )

    print("=" * 100)

    # Bounce stats
    with_bounce = [c for c in candidates if c["bounce"]]
    if with_bounce:
        winners = [c for c in with_bounce if c["bounce"]["tp_hit"]]
        losers = [c for c in with_bounce if c["bounce"]["sl_hit"] and not c["bounce"]["tp_hit"]]
        avg_bounce = sum(c["bounce"]["bounce_close_pct"] for c in with_bounce) / len(with_bounce)
        avg_peak = sum(c["bounce"]["bounce_intraday_high_pct"] for c in with_bounce) / len(with_bounce)

        print(f"\n  BOUNCE STATISTICS ({len(with_bounce)} trades with next-day data):")
        print(f"    TP hit (+3%):       {len(winners)}/{len(with_bounce)} ({len(winners)/len(with_bounce)*100:.0f}%)")
        print(f"    SL hit (-1.5%):     {len(losers)}/{len(with_bounce)} ({len(losers)/len(with_bounce)*100:.0f}%)")
        print(f"    Avg close-to-close: {avg_bounce:+.1f}%")
        print(f"    Avg intraday peak:  {avg_peak:+.1f}%")

        if winners or losers:
            net_wins = len(winners)
            net_losses = len(losers)
            if net_wins + net_losses > 0:
                print(f"    Win rate (TP/SL):   {net_wins/(net_wins+net_losses)*100:.0f}%")
    print()


def save_crash_results(candidates: list[dict]) -> None:
    """Save crash-bounce candidates to JSON."""
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = SCANS_DIR / f"crash_{date_str}.json"
    data = {
        "scan_date": datetime.now().isoformat(),
        "threshold": "40%",
        "candidates": candidates,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    logger.info("crash_results_saved", path=str(path), candidates=len(candidates))


def print_today_crashes(quotes: list[dict]) -> None:
    """Print today's crash candidates from the screener."""
    print("\n" + "=" * 100)
    print("  Crash-Bounce Scanner — TODAY's Extreme Drops (entire US market)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | Found: {len(quotes)} candidates")
    print("=" * 100)

    if not quotes:
        print("\n  No crash candidates today. (Normal — extreme drops are rare.)\n")
        print("=" * 100)
        return

    print(
        f"  {'Ticker':<10} {'Name':<28} {'Drop%':>6} {'Price':>8} "
        f"{'Volume':>12} {'MCap':>10} {'Classification'}"
    )
    print("  " + "-" * 92)

    for q in sorted(quotes, key=lambda x: x.get("regularMarketChangePercent", 0)):
        sym = q.get("symbol", "?")
        name = q.get("shortName", "")[:26]
        pct = q.get("regularMarketChangePercent", 0)
        price = q.get("regularMarketPrice", 0)
        vol = q.get("regularMarketVolume", 0)
        mc = q.get("marketCap", 0)
        mcstr = f"${mc/1e9:.1f}B" if mc >= 1e9 else f"${mc/1e6:.0f}M" if mc else "?"

        # Auto-classify based on available data
        classification = "? — check news"
        if abs(pct) >= 40:
            classification = "EXTREME — verify F/B type before trading"
        elif abs(pct) >= 25:
            classification = "Strong candidate — classify E/O/S/T"

        color = "\033[31m" if pct <= -40 else "\033[33m"
        reset = "\033[0m"

        print(
            f"  {color}{sym:<10}{reset} {name:<28} {pct:>+5.1f}% {price:>8.2f} "
            f"{vol:>12,} {mcstr:>10}  {classification}"
        )

    print("=" * 100)
    print(f"\n  Next steps:")
    print(f"    1. Classify each drop: E(earnings) O(offering) S(sector) T(technical) F(fraud) B(bankruptcy)")
    print(f"    2. Eliminate F and B types")
    print(f"    3. Check next-day calendar for major events")
    print(f"    4. Set alerts for entry window 10:00-10:30 ET tomorrow")
    print(f"    5. Entry only if spread < 2% and stock is NOT making new lows\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crash-Bounce Scanner")
    parser.add_argument("--days", type=int, default=5, help="Lookback days (default 5)")
    parser.add_argument("--threshold", type=float, default=0.60,
                        help="Drop threshold as ratio (0.60 = 40%% drop, 0.50 = 50%% drop)")
    parser.add_argument("--drop-pct", type=float, default=25.0,
                        help="Drop %% for live screener (default 25)")
    parser.add_argument("--ticker", type=str, help="Scan a single ticker historically")
    parser.add_argument("--all-time", action="store_true", help="Scan full year for historical analysis")
    parser.add_argument("--live", action="store_true", help="Scan entire US market for today's crashes (default)")
    args = parser.parse_args()

    # Historical mode: scan specific tickers over time
    if args.ticker or args.all_time:
        if args.ticker:
            tickers = [args.ticker]
        else:
            tickers = get_scan_universe()
            if not tickers:
                print("  Failed to load ticker universe.")
                return

        days = 365 if args.all_time else args.days
        candidates = scan_for_crashes(tickers, lookback_days=days, drop_threshold=args.threshold)
        print_crash_results(candidates)
        if candidates:
            save_crash_results(candidates)
        return

    # Default: live screener mode — searches the ENTIRE US market
    quotes = scan_today_crashes(drop_pct=args.drop_pct)
    print_today_crashes(quotes)

    if quotes:
        # Also fetch OHLCV for the candidates to get full analysis
        tickers = [q["symbol"] for q in quotes]
        candidates = scan_for_crashes(tickers, lookback_days=1, drop_threshold=1.0)
        if candidates:
            save_crash_results(candidates)


if __name__ == "__main__":
    main()
