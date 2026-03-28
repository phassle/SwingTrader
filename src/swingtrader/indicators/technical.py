"""Technical indicator calculations for swing trading signals.

All functions take a pandas DataFrame with OHLCV columns and return
the DataFrame with new indicator columns added.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA(20), SMA(50), SMA(200) for trend analysis."""
    df = df.copy()
    df["ema_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["sma_50"] = df["Close"].rolling(50).mean()
    df["sma_200"] = df["Close"].rolling(200).mean()
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add ATR(14) — Average True Range for stop-loss calculation."""
    df = df.copy()
    high = df["High"]
    low = df["Low"]
    close = df["Close"].shift(1)

    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = true_range.ewm(span=period, adjust=False).mean()
    return df


def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add ADX(14) — Average Directional Index for trend strength."""
    df = df.copy()
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # Directional movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    # True range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Smoothed averages
    atr_smooth = true_range.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr_smooth)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr_smooth)

    # ADX
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    df["adx"] = dx.ewm(span=period, adjust=False).mean()
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add RSI(14) — Relative Strength Index."""
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add volume-based indicators for signal confirmation."""
    df = df.copy()
    df["vol_sma_20"] = df["Volume"].rolling(20).mean()
    df["vol_ratio"] = df["Volume"] / df["vol_sma_20"]
    # Average daily value traded (price × volume) for liquidity check
    df["adv_sek"] = df["Close"] * df["Volume"]
    df["adv_sek_20"] = df["adv_sek"].rolling(20).mean()
    return df


def add_breakout_signals(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """Detect breakouts above N-day high and pullbacks to MA."""
    df = df.copy()
    df["high_60d"] = df["High"].rolling(lookback).max()
    df["low_60d"] = df["Low"].rolling(lookback).min()

    # Breakout: close above 60-day high
    df["breakout"] = df["Close"] > df["high_60d"].shift(1)

    # Pullback to 20 EMA: price within 1 ATR of EMA20
    if "ema_20" in df.columns and "atr" in df.columns:
        distance_to_ema = (df["Close"] - df["ema_20"]).abs()
        df["pullback_to_ema"] = distance_to_ema < df["atr"]
    else:
        df["pullback_to_ema"] = False

    return df


def add_ma_slope(df: pd.DataFrame, periods: int = 5) -> pd.DataFrame:
    """Add moving average slope indicators for trend direction."""
    df = df.copy()
    if "ema_20" in df.columns:
        df["ema_20_slope"] = df["ema_20"].pct_change(periods) * 100
    if "sma_50" in df.columns:
        df["sma_50_slope"] = df["sma_50"].pct_change(periods) * 100
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators in the correct order."""
    df = add_moving_averages(df)
    df = add_atr(df)
    df = add_adx(df)
    df = add_rsi(df)
    df = add_volume_indicators(df)
    df = add_ma_slope(df)
    df = add_breakout_signals(df)
    return df
