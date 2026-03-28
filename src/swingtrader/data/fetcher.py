"""Market data fetcher with provider abstraction.

Currently implements Yahoo Finance. Designed to add IBKR (ib_async) later
via the same interface.
"""

from __future__ import annotations

import logging
import structlog
import pandas as pd
import yfinance as yf
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class TickerData:
    """Container for a single ticker's OHLCV data."""

    ticker: str
    daily: pd.DataFrame  # columns: Open, High, Low, Close, Volume
    weekly: pd.DataFrame | None = None


class DataProvider(ABC):
    """Abstract base for market data providers."""

    @abstractmethod
    def fetch(self, tickers: list[str], period: str = "1y") -> dict[str, TickerData]:
        """Fetch OHLCV data for a list of tickers."""
        ...


class YahooFinanceProvider(DataProvider):
    """Fetch data via yfinance. Free, no API key needed."""

    def fetch(self, tickers: list[str], period: str = "1y") -> dict[str, TickerData]:
        """Fetch daily + weekly OHLCV for all tickers.

        Args:
            tickers: List of Yahoo Finance tickers (e.g. ['VOLV-B.ST'])
            period: Lookback period (default '1y')

        Returns:
            Dict mapping ticker -> TickerData with daily and weekly frames.
        """
        result: dict[str, TickerData] = {}
        log = logger.bind(provider="yahoo", ticker_count=len(tickers))
        log.info("fetching_market_data", period=period)

        # Suppress noisy yfinance/peewee warnings that flood the terminal
        yf_logger = logging.getLogger("yfinance")
        yf_logger.setLevel(logging.CRITICAL)
        logging.getLogger("peewee").setLevel(logging.CRITICAL)

        # Batch download for efficiency
        try:
            daily_data = yf.download(
                tickers,
                period=period,
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            log.error("batch_download_failed", error=str(e))
            return result

        try:
            weekly_data = yf.download(
                tickers,
                period=period,
                interval="1wk",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            log.warning("weekly_download_failed", error=str(e))
            weekly_data = None

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    daily_df = daily_data
                    weekly_df = weekly_data if weekly_data is not None else None
                else:
                    daily_df = daily_data[ticker].dropna(how="all")
                    weekly_df = (
                        weekly_data[ticker].dropna(how="all")
                        if weekly_data is not None
                        else None
                    )

                if daily_df.empty or len(daily_df) < 50:
                    log.warning("insufficient_data", ticker=ticker, rows=len(daily_df))
                    continue

                result[ticker] = TickerData(
                    ticker=ticker,
                    daily=daily_df,
                    weekly=weekly_df,
                )
            except (KeyError, TypeError) as e:
                log.warning("ticker_extraction_failed", ticker=ticker, error=str(e))
                continue

        log.info("fetch_complete", tickers_loaded=len(result), tickers_failed=len(tickers) - len(result))
        return result


def get_provider(name: str = "yahoo") -> DataProvider:
    """Factory for data providers."""
    providers: dict[str, type[DataProvider]] = {
        "yahoo": YahooFinanceProvider,
    }
    if name not in providers:
        raise ValueError(f"Unknown provider '{name}'. Available: {list(providers.keys())}")
    return providers[name]()
