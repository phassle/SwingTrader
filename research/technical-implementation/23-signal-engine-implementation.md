# 23 - Signal Engine Implementation

> Research date: 2026-03-10
> Goal: Define the implementation approach for the signal engine that executes swing trading strategies, generates buy signals, scores setups based on quality framework, applies disqualifiers, ranks recommendations, and persists results to Cosmos DB.
> Prerequisites: [03-signal-engine-design.md](03-signal-engine-design.md), [23-setup-quality-scoring.md](../strategy-and-theory/23-setup-quality-scoring.md), [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md), [22-indicator-engine-implementation.md](22-indicator-engine-implementation.md)

## Table of Contents

1. [Overview](#overview)
2. [Strategy Interface](#strategy-interface)
3. [Signal Dataclass](#signal-dataclass)
4. [Phase 1 Strategy Implementations](#phase-1-strategy-implementations)
5. [Quality Scoring](#quality-scoring)
6. [Disqualifier Filtering](#disqualifier-filtering)
7. [Ranking and Top-N Selection](#ranking-and-top-n-selection)
8. [Cosmos Persistence](#cosmos-persistence)
9. [Execution Flow](#execution-flow)
10. [Testing Strategy](#testing-strategy)

---

## Overview

The signal engine is the **core trading logic** that transforms price and indicator data into actionable buy recommendations. Key responsibilities:

1. **Execute strategies** — run 4 Phase 1 strategies on each ticker
2. **Generate signals** — detect setups, calculate entry/stop/target
3. **Score signals** — apply quality framework (setup quality, trend alignment, risk/reward)
4. **Filter disqualifiers** — remove low-liquidity, poor risk/reward, weak trend
5. **Rank signals** — sort by score, select top N recommendations
6. **Persist results** — save signals and scan summary to Cosmos

**Design principles:**
- **Strategy pattern:** Each strategy implements common interface
- **Separation of concerns:** Signal generation → scoring → filtering → ranking
- **Observable:** Log each strategy's signal count, final recommendation count
- **Reproducible:** All signals persisted for post-scan analysis

---

## Strategy Interface

### Strategy Base Class

From [03-signal-engine-design.md](03-signal-engine-design.md):

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

class Strategy(ABC):
    """Base class for all swing trading strategies."""
    
    def __init__(self, name: str, repository):
        self.name = name
        self.repository = repository
    
    @abstractmethod
    def generate_signal(self, ticker: str, scan_date: date) -> Optional['Signal']:
        """Generate buy signal for ticker if setup detected.
        
        Returns Signal if setup found, None otherwise.
        """
        pass
    
    def _load_context(self, ticker: str, scan_date: date) -> dict:
        """Load price, indicators, and metadata for ticker.
        
        Returns dict with keys: price, indicators, stock_info
        """
        
        # Load latest price
        price = self.repository.daily_prices.get_price(ticker, scan_date)
        
        # Load latest indicators
        indicators_doc = self.repository.indicators.get_indicators(ticker, scan_date)
        indicators = indicators_doc['indicators'] if indicators_doc else {}
        
        # Load stock metadata
        stock = self.repository.stocks.get_stock(ticker)
        
        return {
            'price': price,
            'indicators': indicators,
            'stock': stock,
        }
```

**Key methods:**

1. **generate_signal():** Core strategy logic (abstract, must implement)
2. **_load_context():** Helper to load all data for ticker (reduces duplication)

---

## Signal Dataclass

### Signal Structure

```python
@dataclass
class Signal:
    """Trading signal with entry, exit, and scoring metadata."""
    
    # Identification
    ticker: str
    date: date
    strategy: str
    
    # Price levels
    entry_price: float
    stop_loss: float
    target_price: float
    
    # Metrics
    risk_reward_ratio: float  # (target - entry) / (entry - stop)
    risk_percent: float       # (entry - stop) / entry * 100
    
    # Quality scores (from setup quality framework)
    setup_quality_score: float   # 0-10: pattern strength
    trend_alignment_score: float # 0-10: trend confirmation
    risk_reward_score: float     # 0-10: R:R quality
    total_score: float           # Sum of above (0-30)
    
    # Context (for analysis)
    close_price: float
    volume: int
    atr: float | None
    
    # Disqualifiers (flags)
    low_liquidity: bool = False
    weak_trend: bool = False
    poor_risk_reward: bool = False
    
    @property
    def is_disqualified(self) -> bool:
        """Check if signal has any disqualifiers."""
        return self.low_liquidity or self.weak_trend or self.poor_risk_reward
```

**Design rationale:**

1. **Rich metadata:** All info needed for filtering, ranking, and reporting
2. **Explicit disqualifiers:** Clear why signal was filtered out
3. **Separate scores:** Setup, trend, risk/reward scored independently
4. **Calculated fields:** Risk/reward ratio derived from price levels

---

## Phase 1 Strategy Implementations

### 1. Mean Reversion Strategy

**Setup criteria:**
- RSI < 30 (oversold)
- Price near lower Bollinger Band (< 1.05 × BB lower)
- Price above SMA 200 (long-term uptrend)

**Entry/Exit:**
- Entry: Current close
- Stop: 2 × ATR below entry (or BB lower, whichever tighter)
- Target: BB middle (mean reversion target)

```python
class MeanReversionStrategy(Strategy):
    """Buy oversold stocks near support in uptrends."""
    
    def __init__(self, repository):
        super().__init__("Mean Reversion", repository)
    
    def generate_signal(self, ticker: str, scan_date: date) -> Optional[Signal]:
        ctx = self._load_context(ticker, scan_date)
        
        price = ctx['price']
        indicators = ctx['indicators']
        
        # Check required data
        if not price or not indicators:
            return None
        
        close = price['close']
        rsi = indicators.get('rsi_14')
        bb_lower = indicators.get('bb_lower')
        bb_middle = indicators.get('bb_middle')
        sma_200 = indicators.get('sma_200')
        atr = indicators.get('atr_14')
        
        # Validate required indicators
        if any(x is None for x in [rsi, bb_lower, bb_middle, sma_200]):
            return None
        
        # Setup detection
        is_oversold = rsi < 30
        near_bb_lower = close < bb_lower * 1.05
        above_sma_200 = close > sma_200
        
        if not (is_oversold and near_bb_lower and above_sma_200):
            return None  # No setup
        
        # Calculate entry/exit
        entry = close
        stop = bb_lower if atr is None else max(bb_lower, entry - 2 * atr)
        target = bb_middle
        
        risk = entry - stop
        reward = target - entry
        
        if risk <= 0 or reward <= 0:
            return None  # Invalid setup
        
        # Create signal
        signal = Signal(
            ticker=ticker,
            date=scan_date,
            strategy=self.name,
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            risk_reward_ratio=reward / risk,
            risk_percent=(risk / entry) * 100,
            setup_quality_score=self._score_setup(rsi, close, bb_lower),
            trend_alignment_score=self._score_trend(close, sma_200, indicators),
            risk_reward_score=self._score_risk_reward(reward / risk),
            total_score=0,  # Calculated below
            close_price=close,
            volume=price['volume'],
            atr=atr,
        )
        
        signal.total_score = (signal.setup_quality_score + 
                              signal.trend_alignment_score + 
                              signal.risk_reward_score)
        
        return signal
    
    def _score_setup(self, rsi: float, close: float, bb_lower: float) -> float:
        """Score setup quality (0-10).
        
        Lower RSI = better (more oversold).
        Closer to BB lower = better (stronger support).
        """
        # RSI score: 30 → 5, 20 → 8, 10 → 10
        rsi_score = max(0, min(10, (30 - rsi) / 2))
        
        # BB distance score: at BB lower → 10, 5% above → 0
        distance_pct = (close - bb_lower) / bb_lower
        bb_score = max(0, 10 - distance_pct * 200)
        
        return (rsi_score + bb_score) / 2
    
    def _score_trend(self, close: float, sma_200: float, indicators: dict) -> float:
        """Score trend alignment (0-10).
        
        Price far above SMA 200 = stronger trend.
        """
        distance_pct = (close - sma_200) / sma_200 * 100
        
        # 0% above → 5, 10% above → 8, 20%+ above → 10
        return min(10, 5 + distance_pct * 0.5)
    
    def _score_risk_reward(self, rr_ratio: float) -> float:
        """Score risk/reward ratio (0-10).
        
        2:1 → 6, 3:1 → 8, 4:1+ → 10
        """
        return min(10, rr_ratio * 2)
```

---

### 2. MACD Crossover Strategy

**Setup criteria:**
- MACD crosses above signal line (bullish crossover)
- MACD histogram > 0 (confirms bullish momentum)
- Price above SMA 50 (intermediate uptrend)

**Entry/Exit:**
- Entry: Current close
- Stop: Recent swing low (approximated as close - 2 × ATR)
- Target: 3:1 risk/reward

```python
class MACDCrossoverStrategy(Strategy):
    """Buy on bullish MACD crossover in uptrends."""
    
    def __init__(self, repository):
        super().__init__("MACD Crossover", repository)
    
    def generate_signal(self, ticker: str, scan_date: date) -> Optional[Signal]:
        ctx = self._load_context(ticker, scan_date)
        
        price = ctx['price']
        indicators = ctx['indicators']
        
        if not price or not indicators:
            return None
        
        close = price['close']
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')
        sma_50 = indicators.get('sma_50')
        atr = indicators.get('atr_14')
        
        if any(x is None for x in [macd, macd_signal, macd_histogram, sma_50]):
            return None
        
        # Setup detection
        bullish_crossover = macd > macd_signal and macd_histogram > 0
        above_sma_50 = close > sma_50
        
        if not (bullish_crossover and above_sma_50):
            return None
        
        # Calculate entry/exit
        entry = close
        stop = entry - (2 * atr) if atr else entry * 0.95  # Fallback: 5% stop
        target = entry + 3 * (entry - stop)  # 3:1 R:R
        
        risk = entry - stop
        reward = target - entry
        
        if risk <= 0:
            return None
        
        signal = Signal(
            ticker=ticker,
            date=scan_date,
            strategy=self.name,
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            risk_reward_ratio=reward / risk,
            risk_percent=(risk / entry) * 100,
            setup_quality_score=self._score_setup(macd_histogram),
            trend_alignment_score=self._score_trend(close, sma_50),
            risk_reward_score=10 if reward / risk >= 3 else 6,  # Fixed 3:1 R:R
            total_score=0,
            close_price=close,
            volume=price['volume'],
            atr=atr,
        )
        
        signal.total_score = (signal.setup_quality_score + 
                              signal.trend_alignment_score + 
                              signal.risk_reward_score)
        
        return signal
    
    def _score_setup(self, macd_histogram: float) -> float:
        """Score setup quality based on MACD histogram strength."""
        # Larger positive histogram = stronger momentum
        return min(10, abs(macd_histogram) * 10)
    
    def _score_trend(self, close: float, sma_50: float) -> float:
        """Score trend alignment."""
        distance_pct = (close - sma_50) / sma_50 * 100
        return min(10, 5 + distance_pct * 0.5)
```

---

### 3. Volume Breakout Strategy

**Setup criteria:**
- Close > SMA 50 (uptrend)
- Volume > 1.5 × volume SMA 20 (high volume)
- Price breaks above recent resistance (approximated as SMA 50 + 1 × ATR)

**Entry/Exit:**
- Entry: Current close
- Stop: SMA 50 (support)
- Target: Entry + 2 × (entry - stop)

```python
class VolumeBreakoutStrategy(Strategy):
    """Buy volume breakouts above resistance."""
    
    def __init__(self, repository):
        super().__init__("Volume Breakout", repository)
    
    def generate_signal(self, ticker: str, scan_date: date) -> Optional[Signal]:
        ctx = self._load_context(ticker, scan_date)
        
        price = ctx['price']
        indicators = ctx['indicators']
        
        if not price or not indicators:
            return None
        
        close = price['close']
        volume = price['volume']
        sma_50 = indicators.get('sma_50')
        volume_sma_20 = indicators.get('volume_sma_20')
        atr = indicators.get('atr_14')
        
        if any(x is None for x in [sma_50, volume_sma_20]):
            return None
        
        # Setup detection
        above_sma_50 = close > sma_50
        high_volume = volume > volume_sma_20 * 1.5
        resistance = sma_50 + (atr if atr else sma_50 * 0.02)
        breaks_resistance = close > resistance
        
        if not (above_sma_50 and high_volume and breaks_resistance):
            return None
        
        # Calculate entry/exit
        entry = close
        stop = sma_50
        target = entry + 2 * (entry - stop)
        
        risk = entry - stop
        reward = target - entry
        
        if risk <= 0:
            return None
        
        signal = Signal(
            ticker=ticker,
            date=scan_date,
            strategy=self.name,
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            risk_reward_ratio=reward / risk,
            risk_percent=(risk / entry) * 100,
            setup_quality_score=self._score_setup(volume, volume_sma_20),
            trend_alignment_score=self._score_trend(close, sma_50),
            risk_reward_score=8,  # Fixed 2:1 R:R
            total_score=0,
            close_price=close,
            volume=volume,
            atr=atr,
        )
        
        signal.total_score = (signal.setup_quality_score + 
                              signal.trend_alignment_score + 
                              signal.risk_reward_score)
        
        return signal
    
    def _score_setup(self, volume: int, volume_sma: float) -> float:
        """Score based on volume surge magnitude."""
        volume_ratio = volume / volume_sma
        # 1.5× → 5, 2× → 7, 3×+ → 10
        return min(10, volume_ratio * 3)
    
    def _score_trend(self, close: float, sma_50: float) -> float:
        """Score trend alignment."""
        distance_pct = (close - sma_50) / sma_50 * 100
        return min(10, 5 + distance_pct * 0.5)
```

---

### 4. Pullback Strategy

**Setup criteria:**
- Price in uptrend (close > SMA 200)
- Price pulls back to EMA 20 (support)
- RSI > 40 (not oversold, healthy pullback)

**Entry/Exit:**
- Entry: Current close
- Stop: EMA 20 - 1.5 × ATR
- Target: Entry + 2.5 × (entry - stop)

```python
class PullbackStrategy(Strategy):
    """Buy pullbacks to moving average support in uptrends."""
    
    def __init__(self, repository):
        super().__init__("Pullback", repository)
    
    def generate_signal(self, ticker: str, scan_date: date) -> Optional[Signal]:
        ctx = self._load_context(ticker, scan_date)
        
        price = ctx['price']
        indicators = ctx['indicators']
        
        if not price or not indicators:
            return None
        
        close = price['close']
        sma_200 = indicators.get('sma_200')
        ema_20 = indicators.get('ema_20')
        rsi = indicators.get('rsi_14')
        atr = indicators.get('atr_14')
        
        if any(x is None for x in [sma_200, ema_20, rsi]):
            return None
        
        # Setup detection
        in_uptrend = close > sma_200
        at_ema_20 = abs(close - ema_20) / ema_20 < 0.02  # Within 2% of EMA
        healthy_pullback = rsi > 40  # Not oversold
        
        if not (in_uptrend and at_ema_20 and healthy_pullback):
            return None
        
        # Calculate entry/exit
        entry = close
        stop = ema_20 - (1.5 * atr) if atr else ema_20 * 0.97
        target = entry + 2.5 * (entry - stop)
        
        risk = entry - stop
        reward = target - entry
        
        if risk <= 0:
            return None
        
        signal = Signal(
            ticker=ticker,
            date=scan_date,
            strategy=self.name,
            entry_price=entry,
            stop_loss=stop,
            target_price=target,
            risk_reward_ratio=reward / risk,
            risk_percent=(risk / entry) * 100,
            setup_quality_score=self._score_setup(close, ema_20, rsi),
            trend_alignment_score=self._score_trend(close, sma_200),
            risk_reward_score=9,  # Fixed 2.5:1 R:R
            total_score=0,
            close_price=close,
            volume=price['volume'],
            atr=atr,
        )
        
        signal.total_score = (signal.setup_quality_score + 
                              signal.trend_alignment_score + 
                              signal.risk_reward_score)
        
        return signal
    
    def _score_setup(self, close: float, ema_20: float, rsi: float) -> float:
        """Score based on proximity to EMA and RSI."""
        distance_pct = abs(close - ema_20) / ema_20 * 100
        proximity_score = max(0, 10 - distance_pct * 5)  # Closer = better
        
        rsi_score = min(10, (rsi - 40) / 3)  # RSI 40 → 0, 70 → 10
        
        return (proximity_score + rsi_score) / 2
    
    def _score_trend(self, close: float, sma_200: float) -> float:
        """Score trend alignment."""
        distance_pct = (close - sma_200) / sma_200 * 100
        return min(10, 5 + distance_pct * 0.5)
```

---

## Quality Scoring

### Scoring Framework

From [23-setup-quality-scoring.md](../strategy-and-theory/23-setup-quality-scoring.md):

**Three dimensions (0-10 each):**

1. **Setup Quality:** Pattern strength, indicator alignment
2. **Trend Alignment:** Position within larger trend
3. **Risk/Reward:** Expected profit vs risk ratio

**Total score:** 0-30 (sum of three dimensions)

**Thresholds:**
- 20+: Excellent setup (prioritize)
- 15-19: Good setup (acceptable)
- <15: Weak setup (disqualify)

---

## Disqualifier Filtering

### Disqualifier Rules

```python
def apply_disqualifiers(signal: Signal) -> Signal:
    """Apply disqualifier flags to signal.
    
    Returns signal with disqualifier flags set.
    """
    
    # Disqualifier 1: Low liquidity (volume < 100K average)
    if signal.volume < 100000:
        signal.low_liquidity = True
    
    # Disqualifier 2: Weak trend (total score < 15)
    if signal.total_score < 15:
        signal.weak_trend = True
    
    # Disqualifier 3: Poor risk/reward (< 1.5:1)
    if signal.risk_reward_ratio < 1.5:
        signal.poor_risk_reward = True
    
    return signal
```

**Why explicit flags:**
- Log why signal disqualified (for analysis)
- Persist flagged signals (for post-scan review)
- Allow manual override (e.g., "show me low-liquidity setups too")

---

## Ranking and Top-N Selection

### Ranking Logic

```python
def rank_signals(signals: list[Signal], top_n: int = 5) -> list[Signal]:
    """Rank signals by total score, return top N non-disqualified.
    
    Returns list of top N signals sorted by score (descending).
    """
    
    # Filter out disqualified signals
    valid_signals = [s for s in signals if not s.is_disqualified]
    
    # Sort by total score (descending)
    ranked = sorted(valid_signals, key=lambda s: s.total_score, reverse=True)
    
    # Return top N
    return ranked[:top_n]
```

**Phase 1 decision:** Top 5 recommendations per scan.

**Rationale:**
- Focus on best setups (avoid dilution)
- Manageable for manual review
- Telegram notification fits 5 signals comfortably

---

## Cosmos Persistence

### Persistence Pattern

```python
def persist_signals(repository, signals: list[Signal], scan_date: date):
    """Persist all signals (including disqualified) to Cosmos."""
    
    for signal in signals:
        repository.signals.upsert_signal(
            ticker=signal.ticker,
            date=scan_date,
            strategy=signal.strategy,
            signal_data={
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'target_price': signal.target_price,
                'risk_reward_ratio': signal.risk_reward_ratio,
                'risk_percent': signal.risk_percent,
                'setup_quality_score': signal.setup_quality_score,
                'trend_alignment_score': signal.trend_alignment_score,
                'risk_reward_score': signal.risk_reward_score,
                'total_score': signal.total_score,
                'close_price': signal.close_price,
                'volume': signal.volume,
                'atr': signal.atr,
                'low_liquidity': signal.low_liquidity,
                'weak_trend': signal.weak_trend,
                'poor_risk_reward': signal.poor_risk_reward,
            },
        )
```

**Why persist all signals:**
- Analyze disqualified signals (are rules too strict?)
- Historical record (did we miss opportunities?)
- Backtesting (re-rank with different rules)

---

## Execution Flow

### SignalEngine Orchestration

```python
class SignalEngine:
    """Orchestrates signal generation across strategies."""
    
    def __init__(self, repository):
        self.repository = repository
        self.strategies = [
            MeanReversionStrategy(repository),
            MACDCrossoverStrategy(repository),
            VolumeBreakoutStrategy(repository),
            PullbackStrategy(repository),
        ]
    
    def generate_recommendations(self, tickers: list[str], scan_date: date) -> list[Signal]:
        """Generate top N recommendations from all strategies."""
        
        logger.info(f"Generating signals for {len(tickers)} tickers")
        
        all_signals = []
        
        for ticker in tickers:
            for strategy in self.strategies:
                try:
                    signal = strategy.generate_signal(ticker, scan_date)
                    if signal:
                        signal = apply_disqualifiers(signal)
                        all_signals.append(signal)
                except Exception as e:
                    logger.error(f"Strategy {strategy.name} failed for {ticker}", exc_info=True)
        
        # Persist all signals
        persist_signals(self.repository, all_signals, scan_date)
        
        logger.info(f"Generated {len(all_signals)} total signals", extra={
            "valid_signals": sum(1 for s in all_signals if not s.is_disqualified),
            "disqualified_signals": sum(1 for s in all_signals if s.is_disqualified),
        })
        
        # Rank and return top N
        recommendations = rank_signals(all_signals, top_n=5)
        
        logger.info(f"Top {len(recommendations)} recommendations selected")
        
        return recommendations
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_signal_engine.py
def test_mean_reversion_detects_setup():
    """Test mean reversion strategy detects valid setup."""
    # Mock data
    price = {'close': 95, 'volume': 1000000}
    indicators = {
        'rsi_14': 28,
        'bb_lower': 94,
        'bb_middle': 100,
        'sma_200': 90,
        'atr_14': 2.0,
    }
    
    # Execute
    strategy = MeanReversionStrategy(mock_repository)
    # ... set up mock repository to return price and indicators
    signal = strategy.generate_signal("TEST.ST", date.today())
    
    # Verify
    assert signal is not None
    assert signal.strategy == "Mean Reversion"
    assert signal.entry_price == 95
    assert signal.stop_loss < 95
    assert signal.target_price > 95

def test_disqualifier_flags_low_liquidity():
    """Test disqualifier correctly flags low liquidity."""
    signal = Signal(
        ticker="TEST.ST",
        date=date.today(),
        strategy="Test",
        entry_price=100,
        stop_loss=95,
        target_price=110,
        risk_reward_ratio=2.0,
        risk_percent=5.0,
        setup_quality_score=8,
        trend_alignment_score=7,
        risk_reward_score=8,
        total_score=23,
        close_price=100,
        volume=50000,  # Below 100K threshold
        atr=2.0,
    )
    
    signal = apply_disqualifiers(signal)
    
    assert signal.low_liquidity is True
    assert signal.is_disqualified is True
```

---

## Summary

### Key Decisions

1. **Strategy pattern with common interface** — easy to add new strategies
2. **Rich Signal dataclass** — all metadata for filtering, ranking, reporting
3. **Three-dimensional scoring** — setup quality + trend + risk/reward
4. **Explicit disqualifiers** — clear why signal filtered out
5. **Top 5 recommendations** — focus on best setups
6. **Persist all signals** — including disqualified, for analysis

### What This Enables

- **Consistent signal generation:** All strategies follow same interface
- **Observable:** Log signal counts, scores, disqualifications
- **Analyzable:** Persist all signals for backtesting and review
- **Extensible:** Add new strategies without changing orchestration

### Next Steps

1. **Implement Telegram notifications** → [24-telegram-notification-implementation.md](24-telegram-notification-implementation.md)
2. **Test end-to-end locally** → [25-local-development-workflow.md](25-local-development-workflow.md)
3. **Deploy to Azure** → [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md)

---

## References

- [03-signal-engine-design.md](03-signal-engine-design.md) — Signal engine architecture
- [23-setup-quality-scoring.md](../strategy-and-theory/23-setup-quality-scoring.md) — Quality scoring framework
- [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md) — Cosmos persistence
- [22-indicator-engine-implementation.md](22-indicator-engine-implementation.md) — Indicator calculations
