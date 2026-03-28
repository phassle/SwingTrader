"""Signal scoring engine — 0-20 composite system.

Implements the SwingTrader signal-scoring skill:
8 categories, grade bands (A/B/C/D/F), hard disqualifiers.

This is a quantitative approximation. The full scoring system also
includes qualitative judgments (chart pattern quality, catalyst type)
that require human or LLM review. This engine handles the computable parts.
"""

from __future__ import annotations

import structlog
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class ScoreBreakdown:
    """Detailed scoring for a single ticker."""

    ticker: str
    trend_alignment: int = 0  # 0-3
    level_quality: int = 0  # 0-3
    catalyst_quality: int = 0  # 0-3
    volume: int = 0  # 0-2
    liquidity: int = 0  # 0-2
    market_sector: int = 0  # 0-3
    risk_reward: int = 0  # 0-2
    timing: int = 0  # 0-2
    disqualified: bool = False
    disqualify_reason: str = ""
    setup_type: str = ""  # breakout, pullback, mean_reversion
    entry_price: float = 0.0
    stop_price: float = 0.0
    target_price: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        if self.disqualified:
            return 0
        return (
            self.trend_alignment
            + self.level_quality
            + self.catalyst_quality
            + self.volume
            + self.liquidity
            + self.market_sector
            + self.risk_reward
            + self.timing
        )

    @property
    def grade(self) -> str:
        score = self.total
        if score >= 17:
            return "A"
        if score >= 13:
            return "B"
        if score >= 9:
            return "C"
        return "F"

    @property
    def action(self) -> str:
        grade = self.grade
        if grade == "A":
            return "STRONG BUY — Execute with standard sizing"
        if grade == "B":
            return "BUY — Execute with caution"
        if grade == "C":
            return "WATCHLIST — Only if R:R exceptional"
        return "SKIP — Insufficient edge"


def score_trend_alignment(daily: pd.DataFrame, weekly: pd.DataFrame | None) -> tuple[int, str]:
    """Score trend alignment (0-3) based on MA structure."""
    latest = daily.iloc[-1]
    note = ""

    # Check daily MA alignment: EMA20 > SMA50 > SMA200
    ema20 = latest.get("ema_20", np.nan)
    sma50 = latest.get("sma_50", np.nan)
    sma200 = latest.get("sma_200", np.nan)
    price = latest["Close"]

    if pd.isna(sma200):
        return 1, "Insufficient data for 200 SMA"

    daily_aligned = price > ema20 > sma50 > sma200
    daily_above_50 = price > sma50 > sma200

    # Check weekly trend if available
    weekly_aligned = False
    if weekly is not None and len(weekly) >= 20:
        w_latest = weekly.iloc[-1]
        w_ema20 = weekly["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
        w_sma50 = weekly["Close"].rolling(50).mean().iloc[-1] if len(weekly) >= 50 else np.nan
        if not pd.isna(w_sma50):
            weekly_aligned = w_latest["Close"] > w_ema20
        else:
            weekly_aligned = w_latest["Close"] > w_ema20

    if daily_aligned and weekly_aligned:
        return 3, "Full MA alignment: daily + weekly"
    if daily_aligned or (daily_above_50 and weekly_aligned):
        return 2, "Daily aligned; weekly partial"
    if daily_above_50:
        return 1, "Daily above 50 SMA but structure imperfect"
    return 0, "No trend alignment"


def score_level_quality(daily: pd.DataFrame) -> tuple[int, str, str]:
    """Score level quality (0-3) and identify setup type."""
    latest = daily.iloc[-1]
    atr = latest.get("atr", 0)
    close = latest["Close"]

    breakout = latest.get("breakout", False)
    pullback = latest.get("pullback_to_ema", False)

    if breakout and latest.get("vol_ratio", 0) > 1.2:
        return 3, "Breakout above 60d high with volume", "breakout"
    if breakout:
        return 2, "Breakout above 60d high, soft volume", "breakout"
    if pullback and latest.get("ema_20_slope", 0) > 0.5:
        return 2, "Pullback to rising EMA20", "pullback"
    if pullback:
        return 1, "Near EMA20 but trend unclear", "pullback"
    return 0, "No clear level or setup", "none"


def score_catalyst(daily: pd.DataFrame) -> tuple[int, str]:
    """Score catalyst quality (0-3) based on volume and RSI."""
    latest = daily.iloc[-1]
    vol_ratio = latest.get("vol_ratio", 1.0)
    rsi = latest.get("rsi", 50)

    # Check for RSI divergence (oversold turning up)
    rsi_series = daily["rsi"] if "rsi" in daily.columns else pd.Series()
    rsi_divergence = False
    if len(rsi_series) >= 5:
        rsi_rising = rsi_series.iloc[-1] > rsi_series.iloc[-3]
        price_falling = daily["Close"].iloc[-1] < daily["Close"].iloc[-3]
        rsi_divergence = rsi_rising and price_falling and rsi < 40

    if vol_ratio > 1.5 and rsi_divergence:
        return 3, "Volume spike + RSI divergence"
    if vol_ratio > 1.5:
        return 2, "Volume spike >150%"
    if vol_ratio > 1.2 or rsi_divergence:
        return 1, f"Moderate catalyst (vol {vol_ratio:.1f}x)"
    return 0, "No catalyst"


def score_volume(daily: pd.DataFrame) -> tuple[int, str]:
    """Score volume (0-2) based on entry bar vs 20-day SMA."""
    vol_ratio = daily.iloc[-1].get("vol_ratio", 1.0)
    if vol_ratio > 1.2:
        return 2, f"Strong volume ({vol_ratio:.1f}x baseline)"
    if vol_ratio >= 1.0:
        return 1, f"Adequate volume ({vol_ratio:.1f}x baseline)"
    return 0, f"Weak volume ({vol_ratio:.1f}x baseline)"


def score_liquidity(daily: pd.DataFrame) -> tuple[int, str]:
    """Score liquidity (0-2) based on average daily value traded."""
    latest = daily.iloc[-1]
    adv = latest.get("adv_sek_20", 0)

    # ADV thresholds for Swedish large cap (SEK)
    if adv > 200_000_000:  # >200M SEK
        return 2, f"High liquidity ({adv/1e6:.0f}M SEK/day)"
    if adv > 50_000_000:  # >50M SEK
        return 1, f"Adequate liquidity ({adv/1e6:.0f}M SEK/day)"
    return 0, f"Low liquidity ({adv/1e6:.0f}M SEK/day)"


def score_market_sector(daily: pd.DataFrame, market_adx: float | None = None) -> tuple[int, str]:
    """Score market/sector alignment (0-3).

    Uses ADX as a proxy for market regime. Full regime assessment
    requires the market-regime skill (OMXS30 data, sector breadth).
    """
    latest = daily.iloc[-1]
    adx = latest.get("adx", 20)
    plus_di = latest.get("plus_di", 0)
    minus_di = latest.get("minus_di", 0)

    trend_up = plus_di > minus_di
    strong_trend = adx > 25

    if trend_up and strong_trend:
        return 3, f"Strong uptrend (ADX {adx:.0f}, +DI > -DI)"
    if trend_up and adx > 20:
        return 2, f"Moderate uptrend (ADX {adx:.0f})"
    if trend_up:
        return 1, f"Weak uptrend (ADX {adx:.0f})"
    return 0, f"No uptrend (ADX {adx:.0f}, -DI leads)"


def score_risk_reward(
    entry: float, stop: float, atr: float, account_size: float = 500_000
) -> tuple[int, str]:
    """Score risk/reward (0-2) based on stop distance and implied target."""
    if stop <= 0 or entry <= 0:
        return 0, "Invalid entry/stop"

    risk = entry - stop
    if risk <= 0:
        return 0, "Stop above entry"

    # Target = 2× risk (minimum acceptable R:R)
    target = entry + (risk * 2)
    rr_ratio = (target - entry) / risk

    # Position risk as % of account
    shares = (account_size * 0.015) / risk  # 1.5% risk
    position_value = shares * entry
    position_pct = position_value / account_size

    if rr_ratio >= 2.5 and position_pct < 0.25:
        return 2, f"R:R 1:{rr_ratio:.1f}, position {position_pct:.0%} of account"
    if rr_ratio >= 1.5:
        return 1, f"R:R 1:{rr_ratio:.1f}, position {position_pct:.0%} of account"
    return 0, f"R:R too low (1:{rr_ratio:.1f})"


def score_timing(daily: pd.DataFrame) -> tuple[int, str]:
    """Score timing/confirmation (0-2) based on RSI and candle structure."""
    if len(daily) < 3:
        return 0, "Insufficient data"

    latest = daily.iloc[-1]
    prev = daily.iloc[-2]
    rsi = latest.get("rsi", 50)

    # Clean candle: body > 50% of range (no long wicks)
    body = abs(latest["Close"] - latest["Open"])
    full_range = latest["High"] - latest["Low"]
    clean_candle = body > (full_range * 0.5) if full_range > 0 else False

    # RSI in favorable zone (not overbought)
    rsi_ok = 40 < rsi < 70

    if clean_candle and rsi_ok:
        return 2, f"Clean candle + RSI {rsi:.0f} (favorable zone)"
    if clean_candle or rsi_ok:
        return 1, f"Partial confirmation (candle={'clean' if clean_candle else 'weak'}, RSI {rsi:.0f})"
    return 0, f"Poor timing (RSI {rsi:.0f}, weak candle)"


def check_disqualifiers(daily: pd.DataFrame) -> tuple[bool, str]:
    """Check hard disqualifiers. Returns (disqualified, reason)."""
    latest = daily.iloc[-1]

    # Liquidity too low
    adv = latest.get("adv_sek_20", 0)
    if adv < 10_000_000:  # <10M SEK/day
        return True, f"Liquidity too low ({adv/1e6:.0f}M SEK/day)"

    # Spread proxy: if close and open are identical on high volume, data may be stale
    # (Real spread check requires Level 2 data from IBKR)

    return False, ""


def score_ticker(
    ticker: str,
    daily: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> ScoreBreakdown:
    """Run full 0-20 scoring on a single ticker."""
    score = ScoreBreakdown(ticker=ticker)

    # Check disqualifiers first
    disqualified, reason = check_disqualifiers(daily)
    if disqualified:
        score.disqualified = True
        score.disqualify_reason = reason
        return score

    # Score each category
    trend_pts, trend_note = score_trend_alignment(daily, weekly)
    score.trend_alignment = trend_pts
    score.notes.append(f"Trend: {trend_note}")

    level_pts, level_note, setup = score_level_quality(daily)
    score.level_quality = level_pts
    score.setup_type = setup
    score.notes.append(f"Level: {level_note}")

    cat_pts, cat_note = score_catalyst(daily)
    score.catalyst_quality = cat_pts
    score.notes.append(f"Catalyst: {cat_note}")

    vol_pts, vol_note = score_volume(daily)
    score.volume = vol_pts
    score.notes.append(f"Volume: {vol_note}")

    liq_pts, liq_note = score_liquidity(daily)
    score.liquidity = liq_pts
    score.notes.append(f"Liquidity: {liq_note}")

    mkt_pts, mkt_note = score_market_sector(daily)
    score.market_sector = mkt_pts
    score.notes.append(f"Market: {mkt_note}")

    timing_pts, timing_note = score_timing(daily)
    score.timing = timing_pts
    score.notes.append(f"Timing: {timing_note}")

    # Calculate entry/stop/target
    latest = daily.iloc[-1]
    atr = latest.get("atr", 0)
    score.entry_price = round(float(latest["Close"]), 2)
    score.stop_price = round(float(latest["Close"] - 2.0 * atr), 2)
    score.target_price = round(float(latest["Close"] + 4.0 * atr), 2)  # 2:1 R:R

    # Score risk/reward
    rr_pts, rr_note = score_risk_reward(score.entry_price, score.stop_price, atr)
    score.risk_reward = rr_pts
    score.notes.append(f"R:R: {rr_note}")

    return score
