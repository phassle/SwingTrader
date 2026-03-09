# Algorithmic and Systematic Swing Trading

This document covers the design, architecture, and implementation of algorithmic and systematic swing trading systems. It bridges the gap between the discretionary strategies documented in earlier research files and a fully automated or semi-automated trading operation.

**Cross-references:**
- `02-technical-indicators.md` -- indicator formulas used as signal inputs
- `04-swing-trading-strategies.md` -- discretionary strategies to formalize
- `05-risk-management.md` -- position sizing and stop-loss models
- `06-apis-and-technology.md` -- data sources, broker APIs, and libraries
- `07-backtesting-and-performance.md` -- validation methodology
- `08-market-structure-and-conditions.md` -- regime detection for filters
- `10-empirical-evidence-and-edge-quality.md` -- which edges are defensible

---

## Table of Contents

1. [Systematic vs Discretionary Trading](#1-systematic-vs-discretionary-trading)
2. [Building a Rule-Based System](#2-building-a-rule-based-system)
3. [System Architecture](#3-system-architecture)
4. [Signal Generation](#4-signal-generation)
5. [Automation Levels](#5-automation-levels)
6. [Order Management](#6-order-management)
7. [Monitoring and Alerts](#7-monitoring-and-alerts)
8. [Machine Learning Applications](#8-machine-learning-applications)
9. [Walk-Forward Implementation](#9-walk-forward-implementation)
10. [Production Considerations](#10-production-considerations)

---

## 1. Systematic vs Discretionary Trading

### 1.1 Definitions

**Discretionary trading** means that a human makes every decision -- what to buy, when to enter, where to place the stop, and when to exit. The trader may use charts, indicators, and checklists, but the final judgment is subjective. Two discretionary traders looking at the same chart will often reach different conclusions.

**Systematic trading** means that every decision is defined by an explicit, repeatable set of rules that can be expressed in code. Given the same input data, a systematic system always produces the same output. The rules may be simple (e.g., "buy when RSI crosses below 30 and the 50-day SMA is above the 200-day SMA") or complex (e.g., a machine learning model scoring thousands of features), but they are unambiguous.

### 1.2 Key Differences

| Dimension | Discretionary | Systematic |
|-----------|--------------|------------|
| **Decision authority** | Human judgment | Rule set / algorithm |
| **Reproducibility** | Low -- depends on trader's state | High -- deterministic |
| **Backtestability** | Difficult; relies on hindsight honesty | Straightforward; code runs on historical data |
| **Emotional influence** | High; fear and greed affect decisions | None in execution; bias can enter during design |
| **Adaptability** | Can recognize novel situations | Limited to what the rules cover |
| **Scalability** | Limited by attention span | Can scan thousands of instruments simultaneously |
| **Speed to deploy** | Immediate -- just start trading | Requires upfront development investment |
| **Consistency** | Varies with discipline | Perfectly consistent (for better or worse) |

### 1.3 Advantages of Systematic Trading

**Consistency.** The system applies the same rules every day regardless of recent wins, losses, news anxiety, or sleep quality. As documented in `05-risk-management.md` Section 6 (Psychology and Discipline), emotional decision-making is one of the largest sources of retail trading losses. A systematic approach eliminates execution-time emotions entirely.

**Backtestability.** Every rule can be tested against historical data with precise metrics (see `07-backtesting-and-performance.md`). You know, within the limits of historical simulation, what the strategy's win rate, expectancy, maximum drawdown, and Sharpe ratio looked like before risking real money.

**Scalability.** A systematic scanner can evaluate the entire US equity universe (5,000+ stocks) in seconds. A discretionary trader might manually review 50-100 charts per evening.

**Objectivity in position sizing.** The risk calculations from `05-risk-management.md` (1-2% risk per trade, ATR-based stops) can be computed exactly rather than estimated.

**Audit trail.** Every signal, order, fill, and portfolio state change can be logged. This enables rigorous post-trade analysis that discretionary traders rarely maintain.

### 1.4 Disadvantages of Systematic Trading

**Regime blindness.** A rule set optimized for trending markets (see `08-market-structure-and-conditions.md` Section 1 on regime identification) will produce losses in choppy or range-bound conditions unless the system includes regime filters. Novel regimes -- a pandemic crash, a short squeeze, a new regulatory event -- may not appear in historical data.

**Overfitting risk.** The more parameters a system has, the easier it is to fit historical noise rather than genuine edge. This is covered extensively in `07-backtesting-and-performance.md` Section 2 (Common Pitfalls).

**Development cost.** Building, testing, and maintaining a systematic trading system requires programming skills, infrastructure, and ongoing engineering effort.

**False confidence.** A beautiful backtest can make a flawed strategy look appealing. Without proper statistical validation (Monte Carlo simulation, walk-forward analysis, out-of-sample testing), systematic traders can be overconfident in fragile systems.

**Black swan vulnerability.** Systems trained on typical market behavior may behave unpredictably during extreme events. A flash crash, overnight gap, or exchange outage can produce outcomes that were never part of the training data.

### 1.5 Hybrid Approaches

The most practical approach for most swing traders is a hybrid system:

1. **Systematic scanning and signal generation.** The computer does what it does best: screen thousands of instruments, calculate indicators, rank opportunities, and present a shortlist.
2. **Human review and override.** The trader reviews the shortlist, considers context the system cannot capture (upcoming earnings, sector news, unusual macro conditions), and makes the final go/no-go decision.
3. **Systematic execution.** Once the trader approves a trade, the system handles order placement, stop-loss management, position sizing, and exit logic automatically.

This hybrid model captures most of the benefits of systematic trading (consistency in sizing and exits, broad scanning, backtestable core logic) while retaining human judgment for situations that fall outside the model's training data.

**Practical guideline:** Start with systematic scanning and manual execution. Automate execution only after the system has been paper-traded for at least 3-6 months and the trader trusts the rules.

---

## 2. Building a Rule-Based System

### 2.1 Converting Discretionary Strategies to Rules

The strategies in `04-swing-trading-strategies.md` are described with specific entry rules, exit rules, and filters. Converting them to code requires making every condition unambiguous.

**Step-by-step process:**

1. **Document the strategy in plain English.** Write out every condition you check before entering a trade. Be painfully specific. "The stock looks strong" is not a rule. "The stock's 20-day rate of change is above +5% and the stock closed above its 50-day SMA" is a rule.

2. **Identify all inputs.** List every data point the strategy needs: OHLCV data, indicators, volume metrics, fundamental data, sector information, market-wide indicators.

3. **Define the signal logic.** Express each condition as a boolean (true/false) test. The entry signal fires when all conditions are simultaneously true.

4. **Define exit logic.** Exits are typically: (a) stop-loss hit, (b) take-profit hit, (c) trailing stop hit, (d) time-based exit, or (e) a specific indicator condition. Each must be a precise rule.

5. **Define filters.** Conditions that prevent the strategy from trading at all, such as: market regime is bearish, VIX is above 35, the stock's average volume is below 500,000 shares, or earnings are within 3 days.

6. **Backtest the formalized rules.** Compare the systematic backtest results to your discretionary track record. Significant divergence means the rules do not capture what you were actually doing.

7. **Iterate.** Refine the rules, but resist adding parameters to fit the historical data. Every additional parameter increases overfitting risk.

### 2.2 Signal Generation Pipeline

A signal pipeline transforms raw market data into actionable trade signals through a series of stages:

```
Raw Data --> Data Cleaning --> Indicator Calculation --> Condition Evaluation
    --> Signal Generation --> Filter Application --> Signal Ranking
    --> Position Sizing --> Order Generation
```

**Stage 1: Data Ingestion.** Fetch OHLCV data from the data provider (see `06-apis-and-technology.md` for sources like yfinance, Alpaca, Polygon, etc.). Validate for missing bars, splits, dividends.

**Stage 2: Indicator Calculation.** Compute all required technical indicators (see `02-technical-indicators.md`). Store results in a structured format (DataFrame columns or database fields).

**Stage 3: Condition Evaluation.** For each instrument, evaluate every boolean condition in the strategy. Example:

```python
conditions = {
    "trend_up": sma_50 > sma_200,
    "pullback": close < ema_20 and close > sma_50,
    "rsi_not_oversold": rsi_14 > 25,
    "volume_sufficient": avg_volume_20 > 500_000,
    "not_near_earnings": days_to_earnings > 5,
}
signal = all(conditions.values())
```

**Stage 4: Filter Application.** Apply market-level and portfolio-level filters:
- Is the market regime favorable? (see `08-market-structure-and-conditions.md`)
- How many open positions do we already have?
- Is the sector already overweight in the portfolio?
- Is VIX within acceptable range?

**Stage 5: Ranking.** When multiple signals fire simultaneously, rank them by a composite score (more on this in Section 4.5).

**Stage 6: Position Sizing.** Calculate position size using the formulas from `05-risk-management.md` Section 1 (fixed percentage risk model).

**Stage 7: Order Generation.** Produce the specific orders (entry, stop-loss, take-profit) to be sent to the broker.

### 2.3 Entry Rules Formalization

Every entry rule must specify:

| Element | Example |
|---------|---------|
| **Direction** | Long only, short only, or both |
| **Instrument universe** | S&P 500 components, Russell 2000, custom watchlist |
| **Timeframe** | Daily bars for swing trading |
| **Primary condition** | Close crosses above 20-day EMA |
| **Confirmation condition** | Volume > 1.5x 20-day average volume |
| **Trend filter** | 50 SMA > 200 SMA |
| **Volatility filter** | ATR(14) / Close between 1.5% and 8% |
| **Entry type** | Buy stop at today's high + $0.05 (next day) |
| **Maximum entry delay** | Signal valid for 2 trading days; cancel if not triggered |

**Design principle:** Fewer conditions with strong individual logic are better than many weak conditions that together overfit a specific historical pattern.

### 2.4 Exit Rules Formalization

Exits are more important than entries. A systematic system should define all of the following:

**Initial stop-loss:**
```python
# ATR-based stop (from 05-risk-management.md)
stop_loss = entry_price - (atr_14 * 2.0)
```

**Take-profit target:**
```python
# Risk-reward based
take_profit = entry_price + (entry_price - stop_loss) * 2.0  # 1:2 R:R
```

**Trailing stop:**
```python
# ATR-based trailing stop
trailing_stop = highest_close_since_entry - (atr_14 * 2.5)
# Only moves up, never down
trailing_stop = max(trailing_stop, previous_trailing_stop)
```

**Time-based exit:**
```python
# Close position if held longer than N days with no significant move
if days_in_trade > 10 and unrealized_pnl_percent < 2.0:
    exit_signal = True
```

**Indicator-based exit:**
```python
# Exit when the trend condition that justified entry reverses
if sma_50 < sma_200:  # Death cross
    exit_signal = True
```

**Priority order:** Stop-loss > Take-profit > Trailing stop > Indicator exit > Time exit. The stop-loss is non-negotiable and always active.

### 2.5 Filter Rules

Filters prevent the system from trading in unfavorable conditions. They operate at three levels:

**Market-level filters:**
- S&P 500 is above its 200-day SMA (long-only filter)
- VIX is below 30 (volatility filter)
- Market breadth: percentage of S&P 500 stocks above their 50-day SMA > 40%
- Not within 1 day of FOMC announcement, NFP, or CPI release

**Sector-level filters:**
- Sector ETF (XLF, XLK, etc.) is above its 50-day SMA for long entries in that sector
- Maximum 3 positions in any single sector

**Stock-level filters:**
- Average daily dollar volume > $5 million
- Price > $10 (avoid penny stocks)
- No earnings within 5 trading days
- Not recently added to short-sale restricted list
- Spread < 0.1% of price (liquidity check)

### 2.6 Position Sizing Automation

Position sizing rules from `05-risk-management.md` translate directly to code:

```python
def calculate_position_size(
    account_equity: float,
    risk_per_trade: float,      # e.g., 0.01 for 1%
    entry_price: float,
    stop_price: float,
    max_position_pct: float,    # e.g., 0.10 for 10% max per position
) -> int:
    """Calculate shares to buy, respecting both risk and concentration limits."""

    risk_amount = account_equity * risk_per_trade
    risk_per_share = abs(entry_price - stop_price)

    if risk_per_share <= 0:
        return 0

    # Risk-based size
    shares_by_risk = int(risk_amount / risk_per_share)

    # Concentration limit
    max_position_value = account_equity * max_position_pct
    shares_by_concentration = int(max_position_value / entry_price)

    # Take the smaller of the two
    shares = min(shares_by_risk, shares_by_concentration)

    return max(shares, 0)
```

**Additional portfolio-level constraints:**
- Maximum total exposure: e.g., 80% of equity (20% cash buffer)
- Maximum number of simultaneous positions: e.g., 8-12
- Maximum correlated exposure: e.g., no more than 25% in any single sector

---

## 3. System Architecture

### 3.1 High-Level Architecture

A systematic swing trading system consists of six major components connected in a pipeline:

```
+------------------+     +------------------+     +------------------+
|  DATA INGESTION  | --> |  SIGNAL ENGINE   | --> |  RISK ENGINE     |
|                  |     |                  |     |                  |
| - Market data    |     | - Indicators     |     | - Position sizing|
| - Fundamentals   |     | - Pattern detect |     | - Portfolio limits|
| - Calendar events|     | - Scoring/ranking|     | - Correlation    |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
+------------------+     +------------------+     +------------------+
|  MONITORING      | <-- |  LOGGING &       | <-- |  EXECUTION       |
|                  |     |  AUDIT TRAIL     |     |  ENGINE          |
| - Position P&L   |     |                  |     |                  |
| - System health  |     | - Trade log      |     | - Order mgmt    |
| - Alerts         |     | - Signal log     |     | - Broker API    |
| - Dashboard      |     | - Error log      |     | - Fill tracking |
+------------------+     +------------------+     +------------------+
```

For swing trading specifically, this entire pipeline runs once or twice per day (after market close and/or before market open), not in real time. This dramatically simplifies the architecture compared to intraday or high-frequency systems.

### 3.2 Data Ingestion

**Responsibilities:**
- Fetch end-of-day OHLCV data for the instrument universe
- Fetch supplementary data: earnings calendar, economic calendar, sector classifications
- Validate data quality: check for missing bars, stale prices, split adjustments
- Store data in a local database for fast access

**Implementation approach:**

```python
# Pseudocode for the data ingestion module
class DataIngestor:
    def __init__(self, data_sources: list, database: Database):
        self.sources = data_sources
        self.db = database

    def run_daily_update(self, universe: list[str]):
        """Run after market close each day."""
        for symbol in universe:
            bars = self.fetch_ohlcv(symbol, lookback_days=5)
            self.validate(bars)
            self.db.upsert_bars(symbol, bars)

        self.update_earnings_calendar()
        self.update_sector_data()
        self.log_ingestion_summary()

    def validate(self, bars):
        """Check for common data issues."""
        assert len(bars) > 0, "No data returned"
        assert bars["close"].notna().all(), "Missing close prices"
        assert (bars["high"] >= bars["low"]).all(), "High < Low detected"
        assert (bars["volume"] >= 0).all(), "Negative volume"
```

**Data sources** (detailed in `06-apis-and-technology.md`):
- Historical OHLCV: yfinance (free), Polygon (paid, higher quality), Alpha Vantage
- Earnings calendar: Financial Modeling Prep, Earnings Whispers API
- Economic calendar: FRED API, Trading Economics
- Real-time quotes (for order execution): Alpaca, Interactive Brokers API

### 3.3 Signal Engine

The signal engine computes indicators and evaluates strategy conditions.

**Design principle:** The signal engine should be stateless -- given the same input data, it always produces the same output. State (open positions, account equity) belongs in the risk engine.

```python
class SignalEngine:
    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies

    def generate_signals(self, market_data: dict) -> list[Signal]:
        """Evaluate all strategies against current market data."""
        signals = []
        for strategy in self.strategies:
            for symbol in strategy.universe:
                df = market_data[symbol]
                indicators = strategy.compute_indicators(df)
                if strategy.entry_conditions_met(indicators):
                    signal = Signal(
                        symbol=symbol,
                        direction=strategy.direction,
                        strategy_name=strategy.name,
                        entry_price=strategy.suggested_entry(indicators),
                        stop_price=strategy.suggested_stop(indicators),
                        target_price=strategy.suggested_target(indicators),
                        confidence=strategy.score(indicators),
                        timestamp=datetime.utcnow(),
                    )
                    signals.append(signal)
        return signals
```

### 3.4 Risk Engine

The risk engine transforms raw signals into sized orders while enforcing all portfolio constraints.

**Responsibilities:**
- Calculate position size for each signal (Section 2.6)
- Check portfolio-level limits (max positions, max exposure, sector limits)
- Rank signals when more candidates exist than available slots
- Manage existing positions: check for exit signals, update trailing stops

```python
class RiskEngine:
    def __init__(self, portfolio: Portfolio, config: RiskConfig):
        self.portfolio = portfolio
        self.config = config

    def process_signals(self, signals: list[Signal]) -> list[Order]:
        """Convert signals to orders, respecting all risk limits."""
        orders = []

        # First: generate exit orders for existing positions
        exit_orders = self.check_exits()
        orders.extend(exit_orders)

        # Second: filter and rank entry signals
        available_slots = self.config.max_positions - self.portfolio.open_count
        if available_slots <= 0:
            return orders

        # Apply market-level filters
        signals = [s for s in signals if self.market_filter_passes()]

        # Rank by confidence score
        signals.sort(key=lambda s: s.confidence, reverse=True)

        for signal in signals[:available_slots]:
            size = self.calculate_position_size(signal)
            if size > 0 and self.sector_limit_ok(signal.symbol):
                entry_order = self.create_entry_order(signal, size)
                stop_order = self.create_stop_order(signal, size)
                target_order = self.create_target_order(signal, size)
                orders.extend([entry_order, stop_order, target_order])

        return orders
```

### 3.5 Execution Engine

The execution engine translates orders into broker API calls and tracks their status.

**Responsibilities:**
- Submit orders to the broker via API (see `06-apis-and-technology.md`)
- Monitor order status: pending, filled, partially filled, cancelled, rejected
- Handle partial fills (adjust stop/target quantities accordingly)
- Implement safety checks before submission

```python
class ExecutionEngine:
    def __init__(self, broker: BrokerAPI, safety_config: SafetyConfig):
        self.broker = broker
        self.safety = safety_config

    def execute_orders(self, orders: list[Order]) -> list[ExecutionResult]:
        """Submit orders to broker with safety checks."""
        results = []
        for order in orders:
            # Safety checks
            if not self.validate_order(order):
                results.append(ExecutionResult(order, status="REJECTED_SAFETY"))
                continue

            if self.safety.kill_switch_active:
                results.append(ExecutionResult(order, status="BLOCKED_KILL_SWITCH"))
                continue

            try:
                broker_response = self.broker.submit_order(order)
                results.append(ExecutionResult(order, broker_response))
            except BrokerError as e:
                self.alert_manager.send_alert(
                    level="ERROR",
                    message=f"Order submission failed: {order.symbol} - {e}"
                )
                results.append(ExecutionResult(order, status="ERROR", error=str(e)))

        return results

    def validate_order(self, order: Order) -> bool:
        """Pre-submission safety checks."""
        checks = [
            order.quantity > 0,
            order.quantity <= self.safety.max_shares_per_order,
            order.notional_value <= self.safety.max_order_value,
            order.symbol not in self.safety.blocked_symbols,
            self.daily_order_count < self.safety.max_daily_orders,
        ]
        return all(checks)
```

### 3.6 Monitoring and Alerting

See Section 7 for detailed coverage. The monitoring layer runs continuously and watches:
- Position P&L (individual and portfolio)
- System health (data freshness, API connectivity, error rates)
- Risk limit proximity (approaching max drawdown, max positions, etc.)

### 3.7 Logging and Audit Trail

Every action the system takes must be logged:

```
[2026-03-07 16:05:00] DATA   | Updated 4,832 symbols. 3 symbols failed: [XYZ, ABC, DEF]
[2026-03-07 16:06:12] SIGNAL | AAPL: pullback_strategy LONG entry=178.50 stop=174.20 target=186.10 confidence=0.72
[2026-03-07 16:06:12] SIGNAL | MSFT: breakout_strategy LONG entry=412.00 stop=403.50 target=428.00 confidence=0.68
[2026-03-07 16:06:15] RISK   | AAPL: position_size=55 shares ($9,817.50) risk=$236.50 (0.95% of equity)
[2026-03-07 16:06:15] RISK   | MSFT: FILTERED - sector XLK already at max allocation
[2026-03-07 16:06:20] EXEC   | AAPL: BUY STOP 55 shares @ $178.50 submitted. Broker ID: ABC123
[2026-03-07 16:06:20] EXEC   | AAPL: SELL STOP 55 shares @ $174.20 submitted (stop-loss). Broker ID: ABC124
[2026-03-08 09:32:15] FILL   | AAPL: BUY 55 shares filled @ $178.55 (slippage: +$0.05)
```

**What to log:**
- Every signal generated (including those filtered out, with the reason)
- Every order submitted (with broker order ID)
- Every fill received (with actual fill price for slippage tracking)
- Every error or exception (with stack trace)
- Daily portfolio snapshot (positions, equity, drawdown)
- System performance metrics (runtime, data latency)

**Storage:** Use a relational database (PostgreSQL, SQLite for simpler setups) plus flat log files. Keep at least 2 years of history for post-trade analysis.

### 3.8 Database Design

A minimal schema for a systematic swing trading system:

```sql
-- Instrument universe
CREATE TABLE instruments (
    symbol          TEXT PRIMARY KEY,
    name            TEXT,
    sector          TEXT,
    exchange        TEXT,
    avg_volume      INTEGER,
    last_updated    TIMESTAMP
);

-- Daily OHLCV bars
CREATE TABLE daily_bars (
    symbol          TEXT NOT NULL,
    date            DATE NOT NULL,
    open            REAL,
    high            REAL,
    low             REAL,
    close           REAL,
    adj_close       REAL,
    volume          INTEGER,
    PRIMARY KEY (symbol, date)
);

-- Generated signals
CREATE TABLE signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TIMESTAMP NOT NULL,
    symbol          TEXT NOT NULL,
    strategy        TEXT NOT NULL,
    direction       TEXT NOT NULL,  -- 'LONG' or 'SHORT'
    entry_price     REAL,
    stop_price      REAL,
    target_price    REAL,
    confidence      REAL,
    status          TEXT NOT NULL,  -- 'GENERATED', 'APPROVED', 'FILTERED', 'EXECUTED'
    filter_reason   TEXT            -- why it was filtered, if applicable
);

-- Orders
CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       INTEGER REFERENCES signals(id),
    broker_order_id TEXT,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,  -- 'BUY' or 'SELL'
    order_type      TEXT NOT NULL,  -- 'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'
    quantity        INTEGER NOT NULL,
    price           REAL,
    stop_price      REAL,
    status          TEXT NOT NULL,  -- 'PENDING', 'SUBMITTED', 'FILLED', 'PARTIAL', 'CANCELLED', 'REJECTED'
    submitted_at    TIMESTAMP,
    filled_at       TIMESTAMP,
    fill_price      REAL,
    fill_quantity   INTEGER,
    commission      REAL
);

-- Positions
CREATE TABLE positions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,
    entry_date      DATE NOT NULL,
    entry_price     REAL NOT NULL,
    quantity        INTEGER NOT NULL,
    stop_price      REAL NOT NULL,
    target_price    REAL,
    trailing_stop   REAL,
    strategy        TEXT NOT NULL,
    status          TEXT NOT NULL,  -- 'OPEN', 'CLOSED'
    exit_date       DATE,
    exit_price      REAL,
    pnl             REAL,
    pnl_percent     REAL,
    exit_reason     TEXT            -- 'STOP_LOSS', 'TARGET', 'TRAILING', 'TIME', 'MANUAL'
);

-- Daily portfolio snapshots
CREATE TABLE portfolio_snapshots (
    date            DATE PRIMARY KEY,
    equity          REAL NOT NULL,
    cash            REAL NOT NULL,
    open_positions  INTEGER NOT NULL,
    daily_pnl       REAL,
    total_pnl       REAL,
    drawdown        REAL,
    max_drawdown    REAL
);
```

This schema supports full trade lifecycle tracking, performance analysis, and debugging.

---

## 4. Signal Generation

### 4.1 Technical Indicator-Based Signals

The simplest and most common signal generation approach uses the indicators documented in `02-technical-indicators.md` as building blocks.

**Trend signals:**
- Moving average crossover: fast EMA crosses above slow EMA (e.g., 9/21 EMA cross from `04-swing-trading-strategies.md` Section 1.2)
- Price vs moving average: close crosses above the 50-day SMA
- ADX threshold: ADX(14) > 25 indicates a trending market

**Momentum signals:**
- RSI reversal: RSI(14) crosses above 30 from below (oversold bounce)
- MACD signal line cross: MACD line crosses above signal line
- Stochastic: %K crosses above %D below the 20 level

**Volatility signals:**
- Bollinger Band squeeze: bandwidth contracts to 6-month low, then expands (breakout)
- ATR expansion: ATR(14) today > 1.5x ATR(14) average of last 20 days

**Volume signals:**
- Volume spike: today's volume > 2x 20-day average volume
- OBV trend: OBV making new highs while price consolidates (accumulation)

**Composite example -- pullback-in-uptrend signal:**
```python
def pullback_signal(df: pd.DataFrame) -> bool:
    """
    Strategy: Buy a pullback to the 20 EMA in a confirmed uptrend.
    Based on 04-swing-trading-strategies.md Section 1.3.
    """
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Trend confirmation
    uptrend = latest["sma_50"] > latest["sma_200"]
    sma_50_rising = latest["sma_50"] > df.iloc[-10]["sma_50"]

    # Pullback condition: price touched or dipped below 20 EMA
    touched_ema = latest["low"] <= latest["ema_20"]

    # Bounce: closed above the 20 EMA
    bounced = latest["close"] > latest["ema_20"]

    # Not overextended
    not_overextended = latest["rsi_14"] < 70

    # Volume confirmation
    volume_ok = latest["volume"] > latest["volume_sma_20"] * 0.8

    return uptrend and sma_50_rising and touched_ema and bounced and not_overextended and volume_ok
```

### 4.2 Pattern Recognition Algorithms

Chart patterns from `03-chart-patterns.md` can be detected algorithmically, though with varying reliability.

**Algorithmically tractable patterns:**
- **Support/resistance levels:** Identify price levels with multiple touches using peak/trough detection algorithms. Cluster nearby pivots within an ATR-based tolerance.
- **Consolidation breakouts:** Detect when price range (high-low) over the last N bars contracts below a threshold, then expands.
- **Higher highs / higher lows:** Compare successive swing points to confirm trend structure.
- **Gap detection:** Compare today's open vs yesterday's close.

**Harder to automate reliably:**
- **Head and shoulders, cup and handle:** These require flexible shape matching. Rule-based detection produces many false positives. Template matching or dynamic time warping can help but require careful tuning.
- **Wedges and triangles:** Can be detected via converging trendlines fitted to swing highs and lows, but the definition of "converging" involves subjective tolerance parameters.

**Candlestick patterns** (from `11-candlestick-interpretation.md` and `12-candlestick-examples-and-scenarios.md`) are easier to codify:
```python
def is_bullish_engulfing(df: pd.DataFrame) -> bool:
    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    return (
        yesterday["close"] < yesterday["open"]      # Yesterday was red
        and today["close"] > today["open"]           # Today is green
        and today["open"] <= yesterday["close"]      # Today opened at/below yesterday's close
        and today["close"] >= yesterday["open"]      # Today closed at/above yesterday's open
    )
```

**Practical recommendation:** Focus automated pattern detection on simple, well-defined patterns (breakouts from ranges, higher highs/lows, candlestick patterns). Leave complex visual patterns (head and shoulders, wedges) for human review in a hybrid system.

### 4.3 Machine Learning for Signal Generation (Overview)

Machine learning can be applied to signal generation as a complement to rule-based approaches. See Section 8 for detailed coverage.

**Quick summary of approaches:**
- **Classification:** Train a model to predict whether a stock will be up or down over the next N days. Features include technical indicators, volume metrics, and market regime variables.
- **Regression:** Predict the magnitude of the move (price target).
- **Ranking:** Train a model to rank stocks by expected return, then take the top N as signals.

**Key caveat from `10-empirical-evidence-and-edge-quality.md`:** The strongest empirical evidence supports momentum and post-earnings drift as genuine edges. ML models that capture these effects will outperform models that try to learn arbitrary patterns from noise.

### 4.4 Ensemble Methods: Combining Multiple Signals

A single signal source is fragile. Combining multiple independent signals produces more robust decisions.

**Approaches to combination:**

**Voting:** Each strategy gets one vote. Enter when a majority agree.
```python
signals = [
    pullback_strategy.check(data),      # True/False
    breakout_strategy.check(data),      # True/False
    momentum_strategy.check(data),      # True/False
    mean_reversion_strategy.check(data) # True/False
]
# Enter if at least 2 of 4 agree
entry = sum(signals) >= 2
```

**Weighted scoring:** Assign weights based on historical performance or backtest Sharpe ratio.
```python
weights = {
    "pullback": 0.35,     # Best historical Sharpe
    "breakout": 0.25,
    "momentum": 0.25,
    "mean_reversion": 0.15,
}
score = sum(
    weights[name] * strategy.confidence(data)
    for name, strategy in strategies.items()
)
entry = score > 0.60  # Threshold
```

**Conditional ensemble:** Use different strategies depending on the regime (from `08-market-structure-and-conditions.md`):
```python
if regime == "BULL_LOW_VOL":
    active_strategies = [pullback, breakout]
elif regime == "BEAR_HIGH_VOL":
    active_strategies = [mean_reversion_short]
elif regime == "SIDEWAYS":
    active_strategies = [mean_reversion_long, mean_reversion_short]
```

### 4.5 Signal Scoring and Ranking

When the system generates more signals than available position slots, a scoring function ranks them.

**Scoring factors:**

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Strategy confidence score | 30% | Higher-confidence setups first |
| Risk/reward ratio | 20% | Prefer trades with R:R > 2:1 |
| Relative strength vs market | 15% | Stocks outperforming the index tend to continue |
| Volume confirmation | 10% | Higher volume at signal = more conviction |
| Sector momentum | 10% | Favor sectors in uptrends |
| Distance from stop | 10% | Tighter stops = more efficient use of risk capital |
| Days since last trade in symbol | 5% | Avoid re-entering a recent loser immediately |

**Implementation:**
```python
def score_signal(signal: Signal, market_data: dict, portfolio: Portfolio) -> float:
    score = 0.0
    score += 0.30 * signal.confidence
    score += 0.20 * min(signal.reward_risk_ratio / 3.0, 1.0)  # Cap at R:R = 3
    score += 0.15 * relative_strength(signal.symbol, market_data)
    score += 0.10 * volume_confirmation(signal.symbol, market_data)
    score += 0.10 * sector_momentum(signal.symbol, market_data)
    score += 0.10 * (1.0 - stop_distance_pct(signal) / 0.08)  # Closer stop = higher score
    score += 0.05 * recency_penalty(signal.symbol, portfolio)
    return score
```

### 4.6 Confidence Weighting

Beyond binary signal/no-signal, each signal can carry a confidence level from 0 to 1 that affects position sizing:

```python
# Base position size from risk model
base_shares = calculate_position_size(equity, risk_pct, entry, stop)

# Scale by confidence
confidence = signal.confidence  # 0.0 to 1.0
min_scale = 0.5  # Never go below 50% of base size
scale_factor = min_scale + (1.0 - min_scale) * confidence

final_shares = int(base_shares * scale_factor)
```

This means a high-confidence signal gets the full position size, while a marginal signal gets a smaller position, naturally managing risk according to conviction.

---

## 5. Automation Levels

### 5.1 Level 0 -- Manual

**Description:** The trader uses screeners and charting tools to find setups, then places orders manually through a broker's web interface or app.

**What the system does:**
- Nothing automated. Standard charting software, watchlists, maybe a simple screener on a site like Finviz or TradingView.

**Pros:** No code needed. Full human judgment.
**Cons:** Limited scanning capacity. Inconsistent execution. Emotional decisions. No audit trail.

### 5.2 Level 1 -- Semi-Automated Scanning

**Description:** The system automatically scans the market universe each day, applies the indicator and pattern logic, and produces a ranked shortlist of candidates. The trader reviews the list, makes the final decision, and places orders manually.

**What the system does:**
- Fetches end-of-day data for the full universe
- Computes indicators and evaluates strategy conditions
- Filters and ranks candidates
- Sends a daily report (email, Slack, dashboard) with the top signals
- Calculates suggested entry, stop, target, and position size

**What the trader does:**
- Reviews the shortlist each evening or morning
- Checks the chart visually for context the system might miss
- Decides which trades to take
- Places orders manually with the broker

**Example daily report format:**
```
=== SWING SIGNALS: 2026-03-08 ===

LONG SIGNALS (sorted by score):
1. AAPL  | Pullback to 20 EMA | Entry: $178.50 | Stop: $174.20 | Target: $187.10
          Score: 0.82 | R:R: 2.0:1 | Shares: 55 | Risk: $236

2. NVDA  | Breakout above $890 | Entry: $892.00 | Stop: $875.00 | Target: $926.00
          Score: 0.75 | R:R: 2.0:1 | Shares: 14 | Risk: $238

3. JPM   | RSI bounce + support | Entry: $198.50 | Stop: $194.00 | Target: $207.50
          Score: 0.68 | R:R: 2.0:1 | Shares: 52 | Risk: $234

MARKET REGIME: Bull, Low Vol (SPY > 200 SMA, VIX = 14.2)
OPEN POSITIONS: 4 of 8 max
AVAILABLE RISK: $950 (3.8% of $25,000)

EXIT SIGNALS:
- MSFT: Trailing stop moved to $408.50 (was $405.00)
- AMZN: Time exit -- day 11, gain +1.2%. Consider closing.
```

**Recommended starting point for most swing traders.** This level captures 80% of the systematic benefit (consistent scanning, proper sizing, structured exits) while retaining full human oversight.

### 5.3 Level 2 -- Automated Execution

**Description:** The system generates signals, sizes positions, and submits orders to the broker automatically. The trader monitors positions and has override capability.

**What the system does:**
- Everything from Level 1
- Submits entry orders (typically buy-stop or limit orders) to the broker via API
- Attaches stop-loss and take-profit orders automatically
- Manages trailing stops
- Sends notifications on every order submission and fill

**What the trader does:**
- Reviews the system's plan before market open (optional approval step)
- Monitors open positions during the day
- Can cancel or modify any order
- Reviews end-of-day summary

**Additional requirements vs Level 1:**
- Broker API integration (see `06-apis-and-technology.md`)
- Order management logic (see Section 6)
- Safety checks and kill switch (see Section 6.5)
- More robust error handling

### 5.4 Level 3 -- Fully Automated

**Description:** The system runs end-to-end with no required human intervention. A human monitors dashboards and receives alerts only for exceptional situations (errors, max drawdown, system failures).

**What the system does:**
- Everything from Level 2
- Automatically manages the full portfolio lifecycle
- Self-monitors for data quality issues, connectivity problems, and anomalous behavior
- Implements circuit breakers and kill switches
- Produces daily and weekly performance reports

**What the trader does:**
- Reviews weekly performance summaries
- Responds to escalated alerts
- Performs periodic strategy review (monthly/quarterly)
- Decides on strategy parameter updates or additions

**Requirements beyond Level 2:**
- High reliability infrastructure (see Section 10)
- Comprehensive error handling and recovery
- Automated health checks
- Disaster recovery plan

### 5.5 Recommended Progression

```
Level 0 ──> Level 1 ──> Level 2 ──> Level 3
 (weeks)    (months)     (months)     (optional)

Start here   Spend 3-6    Only after    Only if the
              months       trust in      strategy is
              building     the system    proven and
              confidence   is earned     you have
              and fixing               engineering
              edge cases               capacity
```

**Key principle:** Never skip levels. Each level adds complexity and removes human oversight. Errors at higher levels can be costly. Earn trust at each level before advancing.

---

## 6. Order Management

### 6.1 Order Types for Swing Trading

**Limit order:** Buy at a specific price or better. Use for entering positions at support levels or specific pullback prices. Risk: the price may never reach the limit and the trade is missed.

**Stop order (buy stop):** Buy when the price rises above a trigger level. Ideal for breakout entries -- "buy if price breaks above $50." Becomes a market order once triggered, so actual fill may differ from the stop price.

**Stop-limit order:** A stop order that becomes a limit order once triggered. Provides price protection but risk of non-fill if the price gaps through the limit. Use for entries where you want breakout confirmation but are not willing to chase.

**OCO (One-Cancels-Other):** Two orders linked together -- when one fills, the other is cancelled. Classic use: stop-loss and take-profit orders on the same position. When the target is hit, the stop is automatically cancelled (and vice versa). Not all brokers support OCO natively.

**Bracket order:** An entry order with attached stop-loss and take-profit. The entire lifecycle is managed as a unit. Alpaca, Interactive Brokers, and TD Ameritrade support bracket orders. This is the ideal order type for automated swing trading.

**Trailing stop order:** A stop that moves with the price. Set a trail amount (fixed dollar or percentage) and the stop automatically adjusts as the price moves in your favor. Useful but limited -- broker-managed trailing stops cannot use ATR-based logic. For ATR-based trailing stops, manage the stop in your own code and submit updated stop orders daily.

### 6.2 Smart Order Routing

For swing trading with daily holding periods, smart order routing is less critical than for intraday strategies. However:

- **Use limit orders for entries** when the bid-ask spread is wide (> 0.05% of price). Place the limit at the midpoint or slightly above.
- **Use market orders for urgent exits** (stop-loss triggered by a gap). Getting out is more important than getting the best price.
- **Avoid market orders on illiquid stocks.** If average volume is below 500K shares/day, always use limit orders.
- **Time entries after the opening auction** (avoid the first 15-30 minutes of chaotic price discovery) unless the strategy specifically targets opening gaps.

### 6.3 Handling Partial Fills

Partial fills occur when only some of the requested shares are executed, typically due to insufficient liquidity at the limit price.

**Handling rules:**
```python
def handle_partial_fill(order: Order, filled_qty: int, remaining_qty: int):
    if filled_qty == 0:
        return  # No fill yet, keep order active

    # Adjust stop-loss and take-profit quantities to match filled quantity
    adjust_attached_orders(order, filled_qty)

    if remaining_qty > 0:
        # Decision: wait for fill, cancel remainder, or modify price
        if time_since_submission(order) > timedelta(hours=2):
            cancel_remaining(order)
            log(f"{order.symbol}: Partial fill {filled_qty}/{order.quantity}. "
                f"Cancelled remaining {remaining_qty} after 2h timeout.")
        # Else: keep the order active
```

**Policy for swing trading:** If the entry order is not fully filled within the same trading session, cancel the remainder. A partial position is acceptable as long as the stop-loss is adjusted to cover only the filled shares.

### 6.4 Order Validation and Safety Checks

Every order must pass validation before submission:

```python
class OrderValidator:
    def validate(self, order: Order, portfolio: Portfolio, config: SafetyConfig) -> tuple[bool, str]:
        """Return (is_valid, reason) for the order."""

        # Price sanity
        if order.limit_price and order.limit_price <= 0:
            return False, "Invalid price <= 0"

        # Size sanity
        if order.quantity <= 0 or order.quantity > config.max_shares_per_order:
            return False, f"Quantity {order.quantity} outside range [1, {config.max_shares_per_order}]"

        # Notional value limit
        notional = order.quantity * (order.limit_price or order.estimated_price)
        if notional > config.max_single_order_value:
            return False, f"Notional ${notional:.0f} exceeds max ${config.max_single_order_value:.0f}"

        # Daily order count
        if portfolio.daily_order_count >= config.max_daily_orders:
            return False, f"Daily order limit reached ({config.max_daily_orders})"

        # Daily loss limit
        if portfolio.daily_pnl < -config.max_daily_loss:
            return False, f"Daily loss limit exceeded (${portfolio.daily_pnl:.0f})"

        # Fat finger: order price vs last traded price
        last_price = get_last_price(order.symbol)
        if abs(order.limit_price - last_price) / last_price > 0.05:
            return False, f"Price {order.limit_price} deviates >5% from last price {last_price}"

        # Duplicate detection
        if portfolio.has_pending_order(order.symbol, order.side):
            return False, f"Duplicate order: already have pending {order.side} for {order.symbol}"

        return True, "OK"
```

### 6.5 Kill Switch and Circuit Breaker

A kill switch is a mechanism that immediately stops all trading activity. This is a non-negotiable component of any automated system.

**Circuit breaker triggers:**
1. **Daily loss limit:** If the portfolio loses more than X% in a single day (e.g., 3%), halt all new entries.
2. **Drawdown limit:** If the portfolio drawdown from peak exceeds X% (e.g., 10%), halt everything and alert the operator.
3. **Error rate:** If more than 3 order submissions fail in succession, halt and alert.
4. **Data staleness:** If market data has not updated in 30+ minutes during market hours, halt.
5. **Manual trigger:** The operator can activate the kill switch at any time.

**Implementation:**
```python
class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.is_active = False
        self.trigger_reason = None

    def check(self, portfolio: Portfolio, system_health: SystemHealth) -> bool:
        """Return True if the circuit breaker should be activated."""
        if portfolio.daily_pnl_pct < -self.config.max_daily_loss_pct:
            self.activate(f"Daily loss {portfolio.daily_pnl_pct:.1%} exceeds limit")
            return True

        if portfolio.drawdown_pct > self.config.max_drawdown_pct:
            self.activate(f"Drawdown {portfolio.drawdown_pct:.1%} exceeds limit")
            return True

        if system_health.consecutive_errors > self.config.max_consecutive_errors:
            self.activate(f"{system_health.consecutive_errors} consecutive errors")
            return True

        if system_health.data_age_minutes > self.config.max_data_age_minutes:
            self.activate(f"Data stale: {system_health.data_age_minutes} minutes old")
            return True

        return False

    def activate(self, reason: str):
        self.is_active = True
        self.trigger_reason = reason
        cancel_all_pending_orders()
        send_alert(level="CRITICAL", message=f"CIRCUIT BREAKER ACTIVATED: {reason}")
```

**When the circuit breaker fires:**
1. Cancel all pending (unfilled) orders immediately
2. Do NOT automatically close existing positions (that could cause more harm in a flash crash)
3. Alert the operator via all channels (email, SMS, push notification)
4. Require manual reset before trading resumes

---

## 7. Monitoring and Alerts

### 7.1 Real-Time Position Monitoring

Even though swing trading operates on daily timeframes, positions should be monitored intraday for:
- Stop-loss proximity (price approaching stop level)
- Unusual intraday moves (> 3% against the position)
- News events affecting held positions

**Dashboard elements:**
```
PORTFOLIO DASHBOARD - 2026-03-08 10:45 AM ET
═══════════════════════════════════════════════

Account Equity:  $25,450    Daily P&L: +$210 (+0.83%)
Cash:            $9,200     Open Risk: $1,840
Open Positions:  5 of 8     Drawdown:  -1.2% from peak

POSITION          ENTRY    CURRENT   STOP     P&L      STATUS
AAPL  55 shares   178.55   180.20    174.20   +$90.75  OK
NVDA  14 shares   892.00   888.50    875.00   -$49.00  OK
JPM   52 shares   198.50   200.10    194.00   +$83.20  OK
AMZN  12 shares   185.30   186.90    181.50   +$19.20  DAY 11 - TIME EXIT?
META  20 shares   505.00   502.80    495.00   -$44.00  STOP PROXIMITY: 1.5%
```

### 7.2 P&L Tracking

Track P&L at multiple levels:
- **Per-trade:** Entry price, current price, unrealized P&L, realized P&L
- **Per-strategy:** Aggregate performance of each strategy (pullback, breakout, etc.)
- **Per-day:** Daily equity curve
- **Per-week/month:** Rolling performance summaries

Store these in the `portfolio_snapshots` and `positions` tables from Section 3.8.

### 7.3 Risk Limit Monitoring

Continuously check:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Daily P&L | < -2% | Warning alert |
| Daily P&L | < -3% | Circuit breaker: halt new entries |
| Drawdown from peak | > -5% | Reduce position sizes by 50% |
| Drawdown from peak | > -10% | Circuit breaker: halt all trading |
| Single position loss | > -1.5% of equity | Should have been stopped out; investigate |
| Sector concentration | > 30% of equity | Block new entries in that sector |
| Correlation cluster | > 40% of equity | Alert: multiple correlated positions |

### 7.4 System Health Checks

Run automated health checks every 15 minutes during market hours:

```python
class HealthChecker:
    def run_checks(self) -> list[HealthResult]:
        return [
            self.check_data_freshness(),
            self.check_broker_connectivity(),
            self.check_api_rate_limits(),
            self.check_database_connectivity(),
            self.check_disk_space(),
            self.check_process_memory(),
            self.check_pending_order_staleness(),
        ]

    def check_data_freshness(self) -> HealthResult:
        latest_bar = self.db.get_latest_bar_date()
        expected = get_last_trading_day()
        if latest_bar < expected:
            return HealthResult("DATA", "WARNING", f"Latest data: {latest_bar}, expected: {expected}")
        return HealthResult("DATA", "OK", f"Data current as of {latest_bar}")

    def check_broker_connectivity(self) -> HealthResult:
        try:
            account = self.broker.get_account()
            return HealthResult("BROKER", "OK", f"Connected. Equity: ${account.equity:.2f}")
        except Exception as e:
            return HealthResult("BROKER", "ERROR", f"Connection failed: {e}")
```

### 7.5 Error Handling and Recovery

**Error categories and responses:**

| Error Type | Example | Response |
|-----------|---------|----------|
| **Transient** | API timeout, rate limit hit | Retry with exponential backoff (1s, 2s, 4s, max 3 retries) |
| **Data quality** | Missing bars, stale prices | Skip affected symbols, alert operator, continue |
| **Order rejection** | Insufficient buying power | Log rejection, skip trade, alert if repeated |
| **System failure** | Database down, process crash | Activate circuit breaker, alert operator immediately |
| **Broker outage** | API returns 503 | Halt order submission, retry connectivity every 60s, alert |

**Recovery principle:** The system should always be able to restart cleanly. On startup, it should:
1. Load all open positions from the database
2. Reconcile with the broker's reported positions
3. Verify that stop-loss orders are in place for every open position
4. If any stops are missing, re-submit them immediately
5. Resume normal operation

### 7.6 Alert Escalation

Not all alerts deserve the same urgency. Use tiered escalation:

```
INFO    --> Dashboard only, daily summary email
          Examples: Signal generated, order filled, trailing stop updated

WARNING --> Email + push notification
          Examples: Daily loss > -1%, data delay > 15 min, partial fill timeout

ERROR   --> Email + SMS + push notification
          Examples: Order rejection, broker connectivity loss, data feed failure

CRITICAL --> Email + SMS + phone call + circuit breaker activated
          Examples: Daily loss > -3%, drawdown > -10%, system crash,
                    position without stop-loss detected
```

**Implementation with escalation timeout:**
```python
class AlertManager:
    def send_alert(self, level: str, message: str):
        timestamp = datetime.utcnow()
        self.log_alert(level, message, timestamp)

        if level == "INFO":
            self.dashboard.post(message)

        elif level == "WARNING":
            self.dashboard.post(message)
            self.email.send(subject=f"[WARN] {message[:80]}", body=message)
            self.push_notification.send(message)

        elif level == "ERROR":
            self.dashboard.post(message)
            self.email.send(subject=f"[ERROR] {message[:80]}", body=message)
            self.sms.send(message[:160])
            self.push_notification.send(message)

        elif level == "CRITICAL":
            self.dashboard.post(message)
            self.email.send(subject=f"[CRITICAL] {message[:80]}", body=message)
            self.sms.send(f"CRITICAL: {message[:140]}")
            self.push_notification.send(message)
            self.phone_call.initiate(message[:200])
```

---

## 8. Machine Learning Applications

### 8.1 Feature Engineering from Technical Indicators

The raw material for ML models in swing trading is technical features derived from price and volume data. Good features are more important than model choice.

**Feature categories:**

**Price-based features:**
- Returns: 1-day, 5-day, 10-day, 20-day returns
- Relative position: (close - low) / (high - low) over N days
- Distance from moving averages: (close - SMA_50) / SMA_50
- Highs/lows: days since 52-week high, distance from 52-week low

**Indicator features (from `02-technical-indicators.md`):**
- RSI(14), RSI(7)
- MACD histogram value and slope
- Bollinger Band %B position
- ADX(14) value
- Stochastic %K and %D
- ATR(14) / close (normalized volatility)

**Volume features:**
- Volume ratio: today's volume / 20-day average
- OBV slope over 10 days
- Accumulation/Distribution line direction

**Market context features (from `08-market-structure-and-conditions.md`):**
- S&P 500 return over 5, 20 days
- VIX level and VIX change
- Market breadth: % of stocks above 50 SMA
- Sector relative strength

**Calendar features:**
- Day of week (Tuesday-Thursday historically stronger)
- Days to/from earnings
- Days to/from FOMC, CPI, NFP
- Month of year (seasonality)

**Feature engineering principles:**
1. Normalize features to comparable scales (z-scores or percentile ranks)
2. Avoid look-ahead bias: compute every feature using only data available at the time of prediction
3. Prefer features with economic intuition over arbitrary transformations
4. Limit total features to avoid the curse of dimensionality (typically 20-50 features is sufficient for daily swing trading models)

### 8.2 Classification: Buy/Sell/Hold Signals

The most direct ML application: predict whether a stock will go up, down, or stay flat over the next N days.

**Target variable definition:**
```python
# Binary classification: up or not-up over next 5 trading days
df["target"] = (df["close"].shift(-5) / df["close"] - 1 > 0.02).astype(int)

# Three-class: up (>2%), down (<-2%), flat (in between)
future_return = df["close"].shift(-5) / df["close"] - 1
df["target"] = pd.cut(future_return, bins=[-np.inf, -0.02, 0.02, np.inf], labels=[0, 1, 2])
```

**Common model choices:**
- **Random Forest / Gradient Boosted Trees (XGBoost, LightGBM):** Best starting point. Handle non-linear relationships, feature interactions, and mixed feature types. Relatively resistant to overfitting with proper regularization.
- **Logistic Regression:** Baseline model. Interpretable but cannot capture non-linear patterns without manual feature engineering.
- **Neural Networks:** Rarely justified for daily swing trading with limited data. Tend to overfit badly on financial time series.

**Training approach:**
```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit

# IMPORTANT: Use time-series cross-validation, NOT random K-fold
tscv = TimeSeriesSplit(n_splits=5)

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=4,          # Keep shallow to avoid overfitting
    learning_rate=0.05,
    min_samples_leaf=50,  # Require substantial evidence per leaf
    subsample=0.8,
)

for train_idx, test_idx in tscv.split(X):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    predictions = model.predict(X.iloc[test_idx])
    evaluate(y.iloc[test_idx], predictions)
```

### 8.3 Regression: Price Target Prediction

Instead of classifying direction, predict the expected return:

```python
# Target: 5-day forward return
df["target"] = df["close"].shift(-5) / df["close"] - 1
```

**Use cases:**
- Rank stocks by expected return (use as the scoring function in Section 4.5)
- Set dynamic take-profit targets based on predicted move magnitude
- Estimate expected value of each trade for position sizing

**Caution:** Regression on financial returns is notoriously noisy. An R-squared of 0.02-0.05 (explaining 2-5% of variance) is considered useful in finance. Do not expect high accuracy -- even small predictive edges compound into meaningful profits over many trades.

### 8.4 Clustering: Regime Detection

Unsupervised learning can identify market regimes automatically, complementing the manual regime detection in `08-market-structure-and-conditions.md`.

**Approach:**
```python
from sklearn.cluster import KMeans

# Features describing the market state
regime_features = pd.DataFrame({
    "spy_return_20d": spy["close"].pct_change(20),
    "vix_level": vix["close"],
    "breadth": breadth_pct_above_50sma,
    "spy_volatility_20d": spy["close"].pct_change().rolling(20).std(),
    "yield_curve_slope": treasury_10y - treasury_2y,
})

# Standardize
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X = scaler.fit_transform(regime_features.dropna())

# Find 4 regimes
kmeans = KMeans(n_clusters=4, random_state=42)
regime_features["regime"] = kmeans.fit_predict(X)
```

The resulting clusters often naturally correspond to: bull/low-vol, bull/high-vol, bear/low-vol, bear/high-vol -- but the algorithm discovers the boundaries from data rather than from manually set thresholds.

**Use in trading:** Assign different strategy parameters, position sizes, or active strategy sets to each detected regime.

### 8.5 Reinforcement Learning for Trade Management

Reinforcement learning (RL) can optimize trade management decisions -- when to tighten a stop, when to take partial profits, when to add to a position.

**Formulation:**
- **State:** Current position P&L, days in trade, market regime, indicator values
- **Actions:** Hold, tighten stop, take partial profit (25%, 50%), close position
- **Reward:** Realized P&L adjusted for risk

**Practical status:** RL for trade management is an active research area but is difficult to deploy reliably. Key challenges include:
- Sparse rewards (trades last days; feedback is delayed)
- Non-stationary environment (market behavior changes)
- Insufficient training data (a swing trader might execute 200-500 trades per year)

**Recommendation:** RL is intellectually interesting but is not yet practical for most individual swing traders. Rule-based exit management (ATR trailing stops, time-based exits) is more robust and predictable.

### 8.6 Pitfalls of ML in Trading

**Overfitting:** The most common and deadly pitfall. A model with too many parameters and too little data will memorize historical patterns that do not repeat. Defenses:
- Keep models simple (shallow trees, few features)
- Use time-series cross-validation (never random splits)
- Test on truly out-of-sample data (held-out year)
- Walk-forward validation (Section 9)
- Monitor for performance degradation in live trading

**Data leakage:** Accidentally including future information in features. Examples:
- Using the day's close price to predict the day's direction
- Including features computed from the entire dataset (e.g., z-score using the full sample mean)
- Target encoding computed on the training+test set together

**Non-stationarity:** Financial markets are non-stationary -- the statistical properties of returns change over time. A model trained on 2015-2020 data may not work in 2021-2025 because correlations, volatility regimes, and market microstructure evolve. Defense: walk-forward retraining (Section 9).

**Survivorship bias:** Training on current index constituents ignores delisted companies. This biases backtests upward because the training data only includes stocks that survived.

**Transaction costs:** A model that generates frequent trades may appear profitable in a frictionless backtest but lose money after commissions and slippage. Always include realistic transaction costs in evaluation.

### 8.7 When ML Helps vs When It Does Not

**ML is most useful for:**
- Combining many weak signals into a stronger composite signal (ensemble learning)
- Regime detection / market state classification
- Ranking stocks when the strategy generates more candidates than you can trade
- Dynamic feature importance: understanding which indicators matter in different market conditions

**ML is less useful for:**
- Replacing simple, well-understood rules (e.g., "buy when RSI < 30 and price > 200 SMA")
- Predicting exact prices or returns with high accuracy
- Small datasets (< 1,000 training examples)
- Strategies where the edge comes from a single clear catalyst (earnings drift, breakout)

**Practical guideline:** Start with rule-based strategies. Add ML only after you have a working rule-based system and want to optimize signal selection, position sizing, or regime detection. ML should enhance rules, not replace them.

---

## 9. Walk-Forward Implementation

Walk-forward analysis is the gold standard for evaluating systematic strategies. It is covered conceptually in `07-backtesting-and-performance.md`; this section focuses on implementation.

### 9.1 Rolling Window Training

Walk-forward testing divides the historical data into sequential windows:

```
|<--- Training Window --->|<-- Test -->|
|         3 years         |  6 months  |

Window 1: Train 2018-2020, Test Jan-Jun 2021
Window 2: Train 2018.5-2021, Test Jul-Dec 2021
Window 3: Train 2019-2021.5, Test Jan-Jun 2022
Window 4: Train 2019.5-2022, Test Jul-Dec 2022
...
```

**Implementation:**
```python
class WalkForwardEngine:
    def __init__(self, strategy, train_years=3, test_months=6, step_months=6):
        self.strategy = strategy
        self.train_years = train_years
        self.test_months = test_months
        self.step_months = step_months

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        results = []
        start = data.index[0]
        end = data.index[-1]

        train_start = start
        while True:
            train_end = train_start + pd.DateOffset(years=self.train_years)
            test_start = train_end
            test_end = test_start + pd.DateOffset(months=self.test_months)

            if test_end > end:
                break

            # Train / optimize on training window
            train_data = data[train_start:train_end]
            self.strategy.optimize(train_data)

            # Test on out-of-sample window
            test_data = data[test_start:test_end]
            window_results = self.strategy.backtest(test_data)
            window_results["window"] = f"{test_start.date()} to {test_end.date()}"
            results.append(window_results)

            # Step forward
            train_start += pd.DateOffset(months=self.step_months)

        return pd.concat(results)
```

### 9.2 Parameter Re-Optimization Schedule

**How often to re-optimize:**
- For swing trading (multi-day holds): re-optimize every 3-6 months
- Use a rolling 2-3 year training window (enough data for statistical significance, recent enough to capture current regime)

**What to re-optimize:**
- Indicator parameters (RSI period, moving average lengths)
- Entry/exit thresholds (RSI oversold level, ATR multiplier for stops)
- Filter parameters (VIX threshold, volume threshold)
- Signal scoring weights

**What NOT to re-optimize:**
- The fundamental strategy logic itself. If a pullback strategy stops working, do not try to re-fit it to work again; instead, reduce its allocation or pause it.
- Risk per trade (keep at 1-2% regardless of recent performance)

### 9.3 Performance Degradation Detection

A strategy that worked historically will eventually decay. Detection requires monitoring live performance against expected performance:

```python
class DegradationDetector:
    def __init__(self, expected_sharpe: float, expected_win_rate: float, lookback_trades: int = 50):
        self.expected_sharpe = expected_sharpe
        self.expected_win_rate = expected_win_rate
        self.lookback = lookback_trades

    def check(self, recent_trades: list[Trade]) -> dict:
        if len(recent_trades) < self.lookback:
            return {"status": "INSUFFICIENT_DATA"}

        trades = recent_trades[-self.lookback:]
        actual_win_rate = sum(1 for t in trades if t.pnl > 0) / len(trades)
        actual_sharpe = self.compute_sharpe(trades)

        alerts = []

        # Win rate degradation
        if actual_win_rate < self.expected_win_rate * 0.75:
            alerts.append(f"Win rate {actual_win_rate:.1%} is 25%+ below expected {self.expected_win_rate:.1%}")

        # Sharpe degradation
        if actual_sharpe < self.expected_sharpe * 0.5:
            alerts.append(f"Sharpe {actual_sharpe:.2f} is 50%+ below expected {self.expected_sharpe:.2f}")

        # Consecutive losers
        max_consecutive_losses = self.max_consecutive(trades, lambda t: t.pnl < 0)
        if max_consecutive_losses > 8:
            alerts.append(f"{max_consecutive_losses} consecutive losses detected")

        status = "DEGRADED" if alerts else "OK"
        return {"status": status, "alerts": alerts, "actual_win_rate": actual_win_rate, "actual_sharpe": actual_sharpe}
```

**Response to degradation:**
1. First: verify data quality and execution (is the system working correctly?)
2. Second: check if the market regime has shifted (see `08-market-structure-and-conditions.md`)
3. Third: reduce position size by 50% while investigating
4. Fourth: if degradation persists over 50+ trades, consider pausing the strategy or re-optimizing with walk-forward analysis

### 9.4 Strategy Rotation Based on Regime

Rather than using a single strategy in all conditions, rotate strategies based on the detected regime:

```python
STRATEGY_REGIME_MAP = {
    "BULL_LOW_VOL": {
        "pullback_long": 0.40,
        "breakout_long": 0.35,
        "momentum_long": 0.25,
    },
    "BULL_HIGH_VOL": {
        "pullback_long": 0.50,   # Pullbacks are deeper and more frequent
        "mean_reversion_long": 0.30,
        "breakout_long": 0.20,   # Reduced -- false breakouts increase
    },
    "BEAR_LOW_VOL": {
        "mean_reversion_short": 0.40,
        "pullback_short": 0.35,
        "cash": 0.25,            # Stay partially in cash
    },
    "BEAR_HIGH_VOL": {
        "cash": 0.60,            # Mostly cash
        "mean_reversion_long": 0.25,  # Bounce plays only
        "mean_reversion_short": 0.15,
    },
    "SIDEWAYS": {
        "mean_reversion_long": 0.35,
        "mean_reversion_short": 0.35,
        "cash": 0.30,
    },
}
```

The allocation percentages represent the share of risk budget allocated to each strategy type. This ensures the system is always running the strategies most likely to succeed in the current environment.

---

## 10. Production Considerations

### 10.1 Cloud vs Local Deployment

| Factor | Local (Home Server) | Cloud (AWS/GCP/Azure) |
|--------|--------------------|-----------------------|
| **Cost** | Low (existing hardware) | $20-100/month for a small instance |
| **Reliability** | Depends on internet/power | 99.9%+ uptime SLA |
| **Maintenance** | You handle everything | Managed services available |
| **Latency** | Not critical for swing trading | Not critical for swing trading |
| **Scaling** | Limited | Easy to scale up |
| **Security** | Physical control | Cloud provider security + your configuration |

**Recommendation for swing trading:** Start locally. A Raspberry Pi or an old laptop can run a daily swing trading system. Move to cloud only if:
- You need 24/7 reliability (vacation, travel)
- You are running Level 3 automation
- You want to access the system from multiple locations

**Minimal cloud setup:**
- AWS t3.micro or t3.small (sufficient for daily batch processing)
- RDS PostgreSQL for database (or SQLite on the instance for simplicity)
- S3 for backups and log storage
- CloudWatch or a simple cron job for scheduling
- Estimated cost: $15-30/month

### 10.2 Latency Requirements

Swing trading is not latency-sensitive. The relevant timeframe is days, not milliseconds.

**What matters:**
- Data must be updated within 30 minutes of market close before the analysis runs
- Orders should be submitted before the next market open (for buy-stop orders)
- Position monitoring can use 1-5 minute polling intervals

**What does not matter:**
- Sub-second order execution
- Co-location near exchange servers
- Ultra-low-latency data feeds

This is a major advantage over intraday or HFT systems: the engineering is dramatically simpler.

### 10.3 Data Quality and Validation

Bad data leads to bad signals. Implement validation at every stage:

**Daily checks:**
- Compare fetched bar count to expected trading days
- Verify that split adjustments are applied (compare adjusted close to raw close)
- Check for obviously wrong values: close > 2x previous close, volume = 0, negative prices
- Cross-reference data from two sources for critical instruments (e.g., SPY)

**Historical data integrity:**
- Validate that no future data leaks into the feature pipeline
- Check for gaps in the time series (holidays are expected; other gaps are not)
- Verify dividend/split adjustments are consistent

**Data pipeline testing:**
```python
def test_data_quality(df: pd.DataFrame, symbol: str):
    """Run after every data update."""
    assert len(df) > 0, f"{symbol}: No data"
    assert df.index.is_monotonic_increasing, f"{symbol}: Dates not sorted"
    assert (df["high"] >= df["low"]).all(), f"{symbol}: High < Low"
    assert (df["close"] >= df["low"]).all(), f"{symbol}: Close < Low"
    assert (df["close"] <= df["high"]).all(), f"{symbol}: Close > High"
    assert (df["volume"] >= 0).all(), f"{symbol}: Negative volume"
    assert not df["close"].isna().any(), f"{symbol}: Missing close prices"

    # Check for stale data (same close for 5+ consecutive days)
    consecutive_same = (df["close"].diff() == 0).rolling(5).sum()
    assert (consecutive_same < 5).all(), f"{symbol}: 5+ identical closes"

    # Check for extreme moves (> 50% in a single day)
    daily_returns = df["close"].pct_change().abs()
    extreme = daily_returns > 0.50
    if extreme.any():
        logger.warning(f"{symbol}: Extreme daily move(s) detected: {df[extreme].index.tolist()}")
```

### 10.4 Disaster Recovery

**What can go wrong and how to prepare:**

| Scenario | Prevention | Recovery |
|----------|-----------|----------|
| Database corruption | Daily backups (automated) | Restore from backup; reconcile with broker |
| Internet outage | Cellular backup; cloud deployment | System pauses; existing stops remain at broker |
| Broker API outage | Stops placed at broker level (not software-managed) | Wait for restoration; monitor via broker web interface |
| Code bug causes wrong orders | Safety checks, max order limits, kill switch | Kill switch halts trading; manual cleanup via broker |
| Server crash | Process monitoring (systemd, Docker restart policy) | Auto-restart; reconcile state on startup |

**Critical principle:** Stop-loss orders must always be placed at the broker level, not managed in software only. If the system crashes, the broker-held stop orders continue to protect positions.

**Backup strategy:**
- Database: daily automated backup to a separate location (cloud storage or external drive)
- Configuration files: version-controlled in git
- Trade logs: replicated to a secondary storage location
- Recovery test: practice restoring from backup at least quarterly

### 10.5 Cost Considerations

**Development costs:**
- Time investment: 100-300 hours to build a Level 1-2 system from scratch
- Alternative: use existing frameworks (Zipline, Backtrader, QuantConnect) to reduce development time by 50-70%

**Ongoing costs:**

| Item | Free Options | Paid Options |
|------|-------------|-------------|
| Market data | yfinance (delayed) | Polygon ($29-199/mo), Tiingo ($10-30/mo) |
| Broker | Alpaca (no commission), IBKR (low commission) | -- |
| Cloud hosting | Local hardware | AWS ($15-50/mo) |
| Screening tools | Finviz (free tier) | TradingView ($15-60/mo) |
| Total monthly | $0-15 | $50-300 |

**Realistic budget for a serious systematic swing trader:**
- Minimum viable: $0/month (yfinance + Alpaca + local hardware)
- Recommended: $50-100/month (reliable data + cloud hosting)
- Professional: $200-500/month (premium data + multiple data sources + dedicated cloud)

### 10.6 Regulatory Compliance

**Key regulations for US equity swing trading:**

**Pattern Day Trader (PDT) rule:** If you execute 4+ day trades in a 5-business-day period in a margin account with equity below $25,000, your account may be restricted. Swing traders typically hold for 2-10 days and are less affected, but the system should track round trips to avoid accidental PDT violations. See `09-regulation-tax-and-trade-operations.md` for full details.

**Wash sale rule:** Selling a security at a loss and repurchasing within 30 days disallows the loss for tax purposes. A systematic system that trades the same securities repeatedly can easily trigger wash sales. Track and report these for tax compliance.

**Market manipulation:** An automated system must not engage in spoofing (placing orders intended to be cancelled), layering, or other manipulative practices. Ensure the system only places orders it intends to execute.

**Broker-specific rules:** Each broker has its own rules regarding order types, margin requirements, and API usage limits. Thoroughly read the broker's API documentation and terms of service before deploying.

**Record keeping:** Maintain complete records of all orders, fills, and portfolio states. The IRS requires records sufficient to determine the basis and holding period of every security sold. The systematic approach naturally produces these records if logging is implemented correctly.

---

## Summary: Recommended Implementation Roadmap

1. **Week 1-2:** Formalize one strategy from `04-swing-trading-strategies.md` into explicit, codifiable rules. Write entry conditions, exit conditions, and filters as boolean expressions.

2. **Week 3-4:** Build the data ingestion pipeline. Fetch daily OHLCV data for your universe. Store in a database. Validate data quality.

3. **Week 5-8:** Build the signal engine. Compute indicators, evaluate conditions, generate and rank signals. Produce a daily report (Level 1 automation).

4. **Week 9-12:** Backtest the formalized strategy using walk-forward validation (see `07-backtesting-and-performance.md`). Evaluate with realistic transaction costs. Iterate on rules based on results.

5. **Month 4-6:** Paper trade at Level 1 (automated scanning, manual execution). Track results. Compare to backtest expectations. Fix edge cases.

6. **Month 7-9:** If paper trading confirms the backtest, transition to real money at Level 1. Small position sizes initially.

7. **Month 10-12:** After 6 months of live Level 1 trading with consistent results, consider building Level 2 (automated execution) with full safety checks and kill switch.

8. **Ongoing:** Add strategies, implement walk-forward re-optimization, add regime detection. Consider ML for signal ranking only after rule-based systems are stable.

**The most important principle:** A simple, well-tested system that you understand and trust will outperform a complex system that you do not fully understand. Start simple. Add complexity only when it solves a specific, identified problem.
