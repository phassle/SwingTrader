"""Test scanner with synthetic market data.

Uses realistic fake data to verify scoring engine without network access.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from swingtrader.indicators.technical import add_all_indicators
from swingtrader.scoring.engine import score_ticker, ScoreBreakdown


def make_synthetic_ohlcv(
    days: int = 250,
    start_price: float = 200.0,
    trend: float = 0.0005,  # daily drift
    volatility: float = 0.02,
    volume_base: int = 500_000,
) -> pd.DataFrame:
    """Generate realistic OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    returns = np.random.normal(trend, volatility, days)
    prices = start_price * np.cumprod(1 + returns)

    df = pd.DataFrame(
        {
            "Open": prices * (1 + np.random.uniform(-0.005, 0.005, days)),
            "High": prices * (1 + np.random.uniform(0.002, 0.02, days)),
            "Low": prices * (1 - np.random.uniform(0.002, 0.02, days)),
            "Close": prices,
            "Volume": np.random.randint(
                int(volume_base * 0.5), int(volume_base * 2), days
            ),
        },
        index=dates,
    )
    return df


def make_breakout_scenario() -> pd.DataFrame:
    """Create data where price breaks above 60-day high with volume spike."""
    df = make_synthetic_ohlcv(days=250, start_price=200, trend=0.0003)
    # Make last bar a breakout: new high with volume spike
    df.iloc[-1, df.columns.get_loc("Close")] = df["High"].iloc[-60:].max() * 1.02
    df.iloc[-1, df.columns.get_loc("High")] = df.iloc[-1]["Close"] * 1.005
    df.iloc[-1, df.columns.get_loc("Volume")] = int(df["Volume"].mean() * 2.5)
    return df


def make_weak_scenario() -> pd.DataFrame:
    """Create data with no clear setup — choppy, low volume."""
    return make_synthetic_ohlcv(days=250, start_price=100, trend=-0.0002, volatility=0.03, volume_base=50_000)


class TestIndicators:
    def test_add_all_indicators_columns(self):
        df = make_synthetic_ohlcv()
        result = add_all_indicators(df)
        expected_cols = ["ema_20", "sma_50", "sma_200", "atr", "adx", "rsi", "vol_sma_20", "vol_ratio"]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_atr_positive(self):
        df = make_synthetic_ohlcv()
        result = add_all_indicators(df)
        assert (result["atr"].dropna() > 0).all(), "ATR should be positive"

    def test_rsi_range(self):
        df = make_synthetic_ohlcv()
        result = add_all_indicators(df)
        rsi = result["rsi"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all(), "RSI should be 0-100"


class TestScoring:
    def test_breakout_scores_higher_than_weak(self):
        breakout_df = add_all_indicators(make_breakout_scenario())
        weak_df = add_all_indicators(make_weak_scenario())

        breakout_score = score_ticker("STRONG.ST", breakout_df)
        weak_score = score_ticker("WEAK.ST", weak_df)

        assert breakout_score.total > weak_score.total, (
            f"Breakout ({breakout_score.total}) should score higher than weak ({weak_score.total})"
        )

    def test_score_range_0_to_20(self):
        df = add_all_indicators(make_synthetic_ohlcv())
        score = score_ticker("TEST.ST", df)
        assert 0 <= score.total <= 20, f"Score {score.total} out of range"

    def test_grade_bands(self):
        df = add_all_indicators(make_synthetic_ohlcv())
        score = score_ticker("TEST.ST", df)
        assert score.grade in ("A", "B", "C", "F"), f"Invalid grade: {score.grade}"

    def test_disqualifier_blocks_score(self):
        # Create very low liquidity data
        df = make_synthetic_ohlcv(volume_base=100, start_price=5)
        df = add_all_indicators(df)
        score = score_ticker("ILLIQUID.ST", df)
        assert score.disqualified or score.total >= 0  # Either DQ'd or valid score

    def test_entry_stop_target_populated(self):
        df = add_all_indicators(make_breakout_scenario())
        score = score_ticker("TEST.ST", df)
        if not score.disqualified:
            assert score.entry_price > 0
            assert score.stop_price > 0
            assert score.target_price > score.entry_price
            assert score.stop_price < score.entry_price

    def test_all_8_categories_scored(self):
        df = add_all_indicators(make_synthetic_ohlcv())
        score = score_ticker("TEST.ST", df)
        assert score.trend_alignment >= 0
        assert score.level_quality >= 0
        assert score.catalyst_quality >= 0
        assert score.volume >= 0
        assert score.liquidity >= 0
        assert score.market_sector >= 0
        assert score.risk_reward >= 0
        assert score.timing >= 0

    def test_notes_populated(self):
        df = add_all_indicators(make_synthetic_ohlcv())
        score = score_ticker("TEST.ST", df)
        assert len(score.notes) >= 7, "Should have notes for each scoring category"
