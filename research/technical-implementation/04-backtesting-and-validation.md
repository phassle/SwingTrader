# 04 - Backtesting and Validation

> Research date: 2026-03-08
> Goal: Practical guide to backtesting swing trading strategies on Swedish stocks using Python, yfinance, pandas-ta, and SQLite.

---

## Table of Contents

1. [Why Backtest Before Going Live](#1-why-backtest-before-going-live)
2. [Backtesting Libraries for Python](#2-backtesting-libraries-for-python)
3. [How to Structure a Backtest](#3-how-to-structure-a-backtest)
4. [Realistic Assumptions (Critical)](#4-realistic-assumptions-critical)
5. [Key Metrics to Calculate](#5-key-metrics-to-calculate)
6. [Walk-Forward Testing](#6-walk-forward-testing)
7. [Overfitting Warning](#7-overfitting-warning)
8. [Complete Backtest Example](#8-complete-backtest-example)
9. [From Backtest to Live](#9-from-backtest-to-live)

---

## 1. Why Backtest Before Going Live

A strategy that "makes sense" on paper may fail when applied to real price history. Until you test it against actual data, you have a hypothesis, not a strategy.

Backtesting reveals concrete numbers:

- **Win rate** — what percentage of trades are profitable?
- **Average gain vs average loss** — is the risk/reward ratio acceptable?
- **Max drawdown** — what is the worst peak-to-trough decline? Could you psychologically handle it?
- **Risk-adjusted returns** — does the strategy beat a simple buy-and-hold of OMXS30 after adjusting for risk?
- **Trade frequency** — are there enough trades per year to be statistically meaningful?

**Important caveat:** A good backtest is necessary but not sufficient. Past performance does not guarantee future results. Markets change. But a strategy that does not work historically has almost no chance of working going forward. Backtesting is the minimum sanity check before risking real money.

The theoretical foundation for backtesting methodology is covered in depth in [../strategy-and-theory/07-backtesting-and-performance.md](../strategy-and-theory/07-backtesting-and-performance.md). This document focuses on the practical Python implementation.

---

## 2. Backtesting Libraries for Python

### 2.1 Backtrader

The most mature and feature-rich backtesting framework in Python. Active community, extensive documentation.

**Installation:**

```bash
pip install backtrader
```

**Simple mean-reversion backtest on a Swedish stock:**

```python
import backtrader as bt
import yfinance as yf
import datetime


class RSIMeanReversion(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("rsi_oversold", 30),
        ("rsi_overbought", 70),
        ("stop_loss_pct", 0.05),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.entry_price = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # Buy when RSI drops below oversold threshold
            if self.rsi[0] < self.params.rsi_oversold:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
        else:
            # Sell when RSI rises above overbought or stop-loss hit
            stop_price = self.entry_price * (1 - self.params.stop_loss_pct)
            if self.rsi[0] > self.params.rsi_overbought or self.data.close[0] < stop_price:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None


# Fetch data
data_df = yf.download("VOLV-B.ST", start="2022-01-01", end="2025-01-01")
data_feed = bt.feeds.PandasData(dataname=data_df)

# Run backtest
cerebro = bt.Cerebro()
cerebro.addstrategy(RSIMeanReversion)
cerebro.adddata(data_feed)
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.0025)  # 0.25% Avanza mini tier

cerebro.run()
print(f"Final portfolio value: {cerebro.broker.getvalue():.2f} SEK")
```

**Pros:**

- Full event-driven simulation (realistic order fills)
- Built-in analyzers for Sharpe, drawdown, trade stats
- Supports multiple data feeds (run multiple Swedish stocks simultaneously)
- Large community, many examples online
- Plotting built in

**Cons:**

- Steep learning curve; the OOP API is verbose
- Documentation can be hard to navigate
- Performance can be slow for large universes or parameter sweeps
- Not actively maintained (last major release was 2020, though it still works fine)

### 2.2 Backtesting.py

A simpler, lighter alternative. Good for quick validation of ideas.

**Installation:**

```bash
pip install backtesting
```

**Same strategy with Backtesting.py:**

```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas_ta as ta
import yfinance as yf


class RSIMeanReversion(Strategy):
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    stop_loss_pct = 0.05

    def init(self):
        close = self.data.Close
        self.rsi = self.I(ta.rsi, close, length=self.rsi_period)

    def next(self):
        if not self.position:
            if self.rsi[-1] < self.rsi_oversold:
                self.buy(sl=self.data.Close[-1] * (1 - self.stop_loss_pct))
        else:
            if self.rsi[-1] > self.rsi_overbought:
                self.position.close()


# Fetch and prepare data
df = yf.download("VOLV-B.ST", start="2022-01-01", end="2025-01-01")
# Backtesting.py expects columns: Open, High, Low, Close, Volume
# yfinance multi-level columns need flattening
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

bt = Backtest(
    df, RSIMeanReversion,
    cash=100000,
    commission=0.0025,  # 0.25%
    exclusive_orders=True,
)
stats = bt.run()
print(stats)
# bt.plot()  # Generates interactive HTML chart
```

**Pros:**

- Much simpler API — fewer lines of code for the same result
- Built-in parameter optimization with `bt.optimize()`
- Beautiful interactive HTML plots
- Good documentation

**Cons:**

- Single-asset only (no multi-stock portfolio backtests)
- Less flexible than Backtrader for complex strategies
- Fewer built-in indicators (but integrates with pandas-ta as shown above)

### 2.3 vectorbt

Vectorized backtesting — extremely fast, designed for parameter optimization and large-scale testing.

**Installation:**

```bash
pip install vectorbt
```

**When to use it:**

- You want to test thousands of parameter combinations quickly
- You need to backtest across a large stock universe simultaneously
- You are comfortable with a more complex, NumPy-heavy API

**Brief example:**

```python
import vectorbt as vbt
import yfinance as yf

# Fetch data
price = yf.download("VOLV-B.ST", start="2022-01-01", end="2025-01-01")["Close"]

# Quick RSI backtest with parameter sweep
rsi = vbt.RSI.run(price, window=[10, 14, 20])
entries = rsi.rsi_crossed_below(30)
exits = rsi.rsi_crossed_above(70)

pf = vbt.Portfolio.from_signals(price, entries, exits, fees=0.0025)
print(pf.stats())
```

**Pros:**

- 10-100x faster than event-driven frameworks
- Excellent for parameter optimization
- Good visualization tools

**Cons:**

- Steep learning curve, NumPy/pandas fluency required
- Harder to model realistic execution (slippage, partial fills)
- Less intuitive for strategy logic that depends on portfolio state

### 2.4 Custom Pandas-Based Backtest

Sometimes a framework is overkill. For a simple strategy, you can simulate trades in pure pandas in about 50 lines. This is often the best starting point to understand exactly what is happening.

```python
import pandas as pd
import pandas_ta as ta
import yfinance as yf


def simple_backtest(ticker: str, start: str, end: str,
                    rsi_period: int = 14, rsi_buy: int = 30,
                    rsi_sell: int = 70, stop_loss_pct: float = 0.05,
                    commission_pct: float = 0.0025) -> pd.DataFrame:
    """Simple RSI mean-reversion backtest using pandas only."""
    df = yf.download(ticker, start=start, end=end)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["RSI"] = ta.rsi(df["Close"], length=rsi_period)

    trades = []
    in_trade = False
    entry_price = 0.0
    entry_date = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        rsi_val = row["RSI"]
        close = row["Close"]
        date = df.index[i]

        if not in_trade:
            if rsi_val < rsi_buy:
                entry_price = close
                entry_date = date
                in_trade = True
        else:
            stop_hit = close < entry_price * (1 - stop_loss_pct)
            target_hit = rsi_val > rsi_sell

            if stop_hit or target_hit:
                gross_return = (close - entry_price) / entry_price
                net_return = gross_return - 2 * commission_pct  # buy + sell
                trades.append({
                    "entry_date": entry_date,
                    "exit_date": date,
                    "entry_price": entry_price,
                    "exit_price": close,
                    "gross_return": gross_return,
                    "net_return": net_return,
                    "exit_reason": "stop" if stop_hit else "target",
                })
                in_trade = False

    return pd.DataFrame(trades)


# Run it
trades_df = simple_backtest("VOLV-B.ST", "2022-01-01", "2025-01-01")
if not trades_df.empty:
    print(f"Total trades: {len(trades_df)}")
    print(f"Win rate: {(trades_df['net_return'] > 0).mean():.1%}")
    print(f"Avg return: {trades_df['net_return'].mean():.2%}")
    print(f"Total return: {trades_df['net_return'].sum():.2%}")
```

**When this is good enough:**

- You are testing a single-stock, single-position strategy
- You want full transparency into every calculation
- You are in the early exploration phase

**When to use a framework instead:**

- You need to manage multiple concurrent positions
- You want portfolio-level metrics (overall equity curve, portfolio drawdown)
- You need realistic order simulation (limit orders, partial fills)

### 2.5 Recommendation: Where to Start

**Start with the custom pandas approach** (section 2.4). It forces you to understand every step of the backtest. There is no magic, no hidden assumptions. Once you have validated your strategy logic and are confident the signals are correct, move to **Backtesting.py** for nicer visualization and parameter optimization, or **Backtrader** if you need multi-stock portfolio simulation.

| Need | Tool |
|---|---|
| Quick signal validation | Custom pandas |
| Single-stock with nice plots | Backtesting.py |
| Multi-stock portfolio | Backtrader |
| Parameter optimization at scale | vectorbt |

---

## 3. How to Structure a Backtest

Follow these steps in order. Skipping any step leads to unreliable results.

### Step 1: Define Strategy Rules Precisely

Before writing any code, write down in plain text:

- **Entry rule:** "Buy when daily RSI(14) drops below 30 and the stock is above its 200-day SMA"
- **Exit rule:** "Sell when RSI(14) rises above 70, or after 10 trading days, whichever comes first"
- **Stop-loss:** "Sell if price drops 5% below entry price"
- **Position sizing:** "Risk 2% of portfolio per trade" or "Equal weight, max 5 positions"

If you cannot state the rules in a single paragraph, the strategy is probably too complex.

### Step 2: Load Historical Data (1-3 Years Minimum)

```python
import yfinance as yf

tickers = ["VOLV-B.ST", "SEB-A.ST", "ERIC-B.ST", "ASSA-B.ST", "SAND.ST"]
data = yf.download(tickers, start="2022-01-01", end="2025-01-01", group_by="ticker")
```

Why 1-3 years minimum:
- Need to capture different market regimes (bull, bear, sideways)
- Need enough trades for statistical significance (30+ trades minimum)
- Going back further risks regime changes making data less relevant

### Step 3: Generate Signals on Historical Data

Apply your indicator calculations and generate buy/sell signals. This should produce the same signals your live scanner would produce.

```python
import pandas_ta as ta

df["RSI"] = ta.rsi(df["Close"], length=14)
df["SMA200"] = ta.sma(df["Close"], length=200)

df["buy_signal"] = (df["RSI"] < 30) & (df["Close"] > df["SMA200"])
df["sell_signal"] = df["RSI"] > 70
```

### Step 4: Simulate Trades with Realistic Assumptions

See section 4 below for what "realistic" means. At minimum: include commission, assume next-day execution (not same-bar), apply slippage.

### Step 5: Calculate Performance Metrics

See section 5 below. At minimum: win rate, average win/loss, max drawdown, total return.

### Step 6: Analyze Results

Ask yourself:
- Would I actually trade this? Could I handle the max drawdown?
- Are there enough trades to trust the statistics?
- Does it work across multiple stocks, or just one?
- Does it work in different market conditions, or only in bull markets?

---

## 4. Realistic Assumptions (Critical)

The gap between a backtest and live trading is almost always about assumptions. Unrealistic assumptions produce backtests that look great but fail in practice. See [../strategy-and-theory/24-execution-and-slippage-playbook.md](../strategy-and-theory/24-execution-and-slippage-playbook.md) for a thorough treatment of execution reality.

### 4.1 Commission: Avanza Courtage

Avanza's commission structure (as of 2025):

| Tier | Commission | Minimum |
|---|---|---|
| Mini (most common for retail) | 0.25% | 1 SEK |
| Small | 0.15% | 39 SEK |
| Medium | 0.069% | 99 SEK |
| Large | 0.049% | 99 SEK |

For backtesting, use **0.25%** unless you know you will qualify for a lower tier. This is a round-trip cost of 0.50%, which matters significantly for short-duration trades.

```python
# In your backtest, apply commission on both entry and exit
commission_pct = 0.0025
net_return = gross_return - 2 * commission_pct
```

### 4.2 Slippage

Slippage is the difference between the price you expect and the price you actually get.

- **Swedish large caps (OMXS30 components):** assume 0.1% slippage per trade
- **Swedish mid caps:** assume 0.2% slippage per trade
- **Swedish small caps:** assume 0.3-0.5% or more

```python
# Conservative: apply slippage to both entry and exit
slippage_pct = 0.001  # 0.1% for large caps
effective_entry = signal_price * (1 + slippage_pct)  # Bought slightly higher
effective_exit = signal_price * (1 - slippage_pct)   # Sold slightly lower
```

### 4.3 Fill Assumptions

Your backtest generates a signal at the close. Can you actually trade at that price?

- **Most realistic:** assume you trade at the next day's open, not the signal bar's close
- **Reasonable alternative:** assume you trade at the signal bar's close + slippage

```python
# Next-day execution (more realistic)
df["entry_price"] = df["Open"].shift(-1)  # Trade at next day's open
```

### 4.4 No Look-Ahead Bias

This is the most common backtest error. Your signal at time T must only use data available at time T, never future data.

Common mistakes:
- Using today's close to decide today's trade (you do not know the close until the bar is complete)
- Computing a moving average that includes future data (pandas `.rolling()` is safe, but watch out for custom calculations)
- Using earnings results to generate signals on the day before the announcement

### 4.5 Survivorship Bias

Your stock universe today only includes stocks that survived. Companies that went bankrupt or were delisted are missing from yfinance.

- For Swedish stocks, this is less severe than for US small caps, but still matters
- Practical mitigation: be aware that your backtest likely overstates performance slightly
- If possible, include delisted stocks (hard with yfinance; Nasdaq Nordic historical data may help)

---

## 5. Key Metrics to Calculate

Here is Python code to calculate each key metric from a list of trade results:

```python
import numpy as np
import pandas as pd


def calculate_metrics(trades: pd.DataFrame) -> dict:
    """
    Calculate key performance metrics from a DataFrame of trades.

    Expected columns:
        - net_return: float (e.g., 0.05 for a 5% gain)
        - entry_date: datetime
        - exit_date: datetime
    """
    if trades.empty:
        return {"error": "No trades to analyze"}

    returns = trades["net_return"]
    winners = returns[returns > 0]
    losers = returns[returns <= 0]

    # Win rate
    win_rate = len(winners) / len(returns)

    # Average win vs average loss
    avg_win = winners.mean() if len(winners) > 0 else 0.0
    avg_loss = losers.mean() if len(losers) > 0 else 0.0

    # Profit factor = gross profits / gross losses
    gross_profit = winners.sum() if len(winners) > 0 else 0.0
    gross_loss = abs(losers.sum()) if len(losers) > 0 else 0.001
    profit_factor = gross_profit / gross_loss

    # Max drawdown (from cumulative returns)
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # Sharpe ratio (annualized, assuming ~250 trading days)
    # Approximate: mean daily return / std daily return * sqrt(250)
    # For trade-level returns, adjust by average holding period
    avg_holding_days = (trades["exit_date"] - trades["entry_date"]).dt.days.mean()
    trades_per_year = 250 / max(avg_holding_days, 1)
    sharpe = (returns.mean() / returns.std()) * np.sqrt(trades_per_year) if returns.std() > 0 else 0.0

    return {
        "total_trades": len(returns),
        "win_rate": f"{win_rate:.1%}",
        "avg_win": f"{avg_win:.2%}",
        "avg_loss": f"{avg_loss:.2%}",
        "profit_factor": f"{profit_factor:.2f}",
        "max_drawdown": f"{max_drawdown:.2%}",
        "sharpe_ratio": f"{sharpe:.2f}",
        "total_return": f"{returns.sum():.2%}",
        "avg_holding_days": f"{avg_holding_days:.1f}",
    }


# Usage
metrics = calculate_metrics(trades_df)
for k, v in metrics.items():
    print(f"{k:>20}: {v}")
```

### Interpreting the Metrics

| Metric | Poor | Acceptable | Good |
|---|---|---|---|
| Win rate | < 40% | 40-55% | > 55% |
| Profit factor | < 1.0 | 1.0-1.5 | > 1.5 |
| Max drawdown | > -30% | -15% to -30% | < -15% |
| Sharpe ratio | < 0.5 | 0.5-1.0 | > 1.0 |
| Total trades (3yr) | < 20 | 20-50 | > 50 |

**Statistical significance:** With fewer than 30 trades, the metrics are unreliable. With fewer than 20, they are nearly meaningless. If your strategy produces very few trades, you need more historical data or a broader stock universe.

---

## 6. Walk-Forward Testing

### 6.1 Why In-Sample/Out-of-Sample Split Matters

If you optimize parameters on the full dataset, you are fitting to noise. The strategy will look great on historical data and fail on new data.

**Simple split approach:**

```
|--- In-sample (train) ---|--- Out-of-sample (test) ---|
     2022-01-01 to 2024-01-01    2024-01-01 to 2025-01-01
```

- Develop and tune on the in-sample period
- Test once on the out-of-sample period
- If it works OOS, you have more confidence

### 6.2 Walk-Forward: Rolling Window Approach

More robust than a single split. Simulates how you would actually use the strategy over time.

```
Window 1: Train [2022-01 to 2023-06] → Test [2023-07 to 2023-12]
Window 2: Train [2022-07 to 2024-01] → Test [2024-01 to 2024-06]
Window 3: Train [2023-01 to 2024-06] → Test [2024-07 to 2024-12]
```

### 6.3 Simple Python Implementation

```python
import pandas as pd
from typing import Callable


def walk_forward_test(
    df: pd.DataFrame,
    strategy_fn: Callable,
    train_months: int = 18,
    test_months: int = 6,
) -> pd.DataFrame:
    """
    Walk-forward test with rolling windows.

    Args:
        df: Price DataFrame with DatetimeIndex
        strategy_fn: Function(df_train, df_test) -> pd.DataFrame of trades
        train_months: Length of training window
        test_months: Length of test window

    Returns:
        DataFrame of all out-of-sample trades across windows
    """
    all_trades = []
    start = df.index.min()
    end = df.index.max()

    window_start = start
    while True:
        train_end = window_start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)

        if test_end > end:
            break

        df_train = df[window_start:train_end]
        df_test = df[train_end:test_end]

        if len(df_train) < 100 or len(df_test) < 20:
            window_start += pd.DateOffset(months=test_months)
            continue

        # Run strategy: train on in-sample, generate trades on out-of-sample
        trades = strategy_fn(df_train, df_test)
        if not trades.empty:
            trades["window"] = f"{window_start.date()} to {test_end.date()}"
            all_trades.append(trades)

        window_start += pd.DateOffset(months=test_months)

    return pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
```

The `strategy_fn` receives training data (to compute indicator thresholds or parameters) and test data (to generate signals and simulate trades). This separation enforces the in-sample/out-of-sample boundary.

---

## 7. Overfitting Warning

Overfitting is the most dangerous trap in backtesting. It means your strategy has learned the noise in historical data rather than a genuine pattern.

### Signs of Overfitting

- Backtest shows extraordinary returns (30%+ per year with no losing months)
- Strategy has many parameters (5+ tunable values)
- Performance drops dramatically on out-of-sample data
- Optimal parameters are at extreme values (RSI threshold of 4, or a 3-day SMA)
- Small changes to parameters cause large changes in results

### How to Avoid It

1. **Keep strategies simple.** Fewer parameters = less room to overfit. A strategy with 2 parameters is far more robust than one with 8.
2. **Always test out-of-sample.** If you only report in-sample results, you are fooling yourself.
3. **Be suspicious of perfection.** Real strategies have losing streaks and drawdowns.
4. **Use walk-forward testing** (section 6) rather than a single optimized backtest.
5. **Prefer well-known, theoretically grounded strategies** over data-mined patterns.

For a deeper treatment of overfitting and statistical validation, see [../strategy-and-theory/07-backtesting-and-performance.md](../strategy-and-theory/07-backtesting-and-performance.md), particularly sections on common pitfalls and statistical validation.

---

## 8. Complete Backtest Example

A full, runnable example that fetches data for 5 Swedish large caps, runs an RSI mean-reversion strategy, and reports performance metrics.

```python
"""
Complete RSI Mean-Reversion Backtest for Swedish Large Caps
-----------------------------------------------------------
Fetches 3 years of daily data, simulates trades with realistic
commission and slippage, and reports key performance metrics.

Requirements:
    pip install yfinance pandas-ta pandas numpy
"""

import numpy as np
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime


# --- Configuration ---
TICKERS = ["VOLV-B.ST", "SEB-A.ST", "ERIC-B.ST", "ASSA-B.ST", "SAND.ST"]
START_DATE = "2022-01-01"
END_DATE = "2025-01-01"

RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
RSI_SELL_THRESHOLD = 70
STOP_LOSS_PCT = 0.05

COMMISSION_PCT = 0.0025   # Avanza Mini tier
SLIPPAGE_PCT = 0.001      # 0.1% for large caps


def fetch_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data and compute RSI."""
    df = yf.download(ticker, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df["RSI"] = ta.rsi(df["Close"], length=RSI_PERIOD)
    df.dropna(subset=["RSI"], inplace=True)
    return df


def run_backtest(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Simulate RSI mean-reversion trades on a single stock.

    Entry: RSI < RSI_BUY_THRESHOLD (buy at next day's open + slippage)
    Exit:  RSI > RSI_SELL_THRESHOLD or stop-loss hit (sell at next day's open - slippage)
    """
    trades = []
    in_trade = False
    entry_price = 0.0
    entry_date = None

    for i in range(len(df) - 1):  # -1 because we use next day's open
        today = df.iloc[i]
        tomorrow = df.iloc[i + 1]
        rsi_val = today["RSI"]
        date = df.index[i]

        if not in_trade:
            if rsi_val < RSI_BUY_THRESHOLD:
                # Execute at next day's open + slippage
                entry_price = tomorrow["Open"] * (1 + SLIPPAGE_PCT)
                entry_date = df.index[i + 1]
                in_trade = True
        else:
            current_price = today["Close"]
            stop_hit = current_price < entry_price * (1 - STOP_LOSS_PCT)
            target_hit = rsi_val > RSI_SELL_THRESHOLD

            if stop_hit or target_hit:
                # Execute at next day's open - slippage
                exit_price = tomorrow["Open"] * (1 - SLIPPAGE_PCT)
                exit_date = df.index[i + 1]

                gross_return = (exit_price - entry_price) / entry_price
                net_return = gross_return - 2 * COMMISSION_PCT

                trades.append({
                    "ticker": ticker,
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "gross_return": gross_return,
                    "net_return": net_return,
                    "exit_reason": "stop" if stop_hit else "target",
                    "holding_days": (exit_date - entry_date).days,
                })
                in_trade = False

    return pd.DataFrame(trades)


def calculate_metrics(trades: pd.DataFrame) -> dict:
    """Calculate key performance metrics from trade results."""
    if trades.empty:
        return {"total_trades": 0}

    returns = trades["net_return"]
    winners = returns[returns > 0]
    losers = returns[returns <= 0]

    win_rate = len(winners) / len(returns) if len(returns) > 0 else 0
    avg_win = winners.mean() if len(winners) > 0 else 0
    avg_loss = losers.mean() if len(losers) > 0 else 0

    gross_profit = winners.sum() if len(winners) > 0 else 0
    gross_loss = abs(losers.sum()) if len(losers) > 0 else 0.001
    profit_factor = gross_profit / gross_loss

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    max_drawdown = ((cumulative - running_max) / running_max).min()

    avg_hold = trades["holding_days"].mean()
    trades_per_year = 250 / max(avg_hold, 1)
    sharpe = (
        (returns.mean() / returns.std()) * np.sqrt(trades_per_year)
        if returns.std() > 0 else 0.0
    )

    return {
        "total_trades": len(returns),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe,
        "total_return": returns.sum(),
        "avg_holding_days": avg_hold,
    }


def print_metrics(label: str, metrics: dict):
    """Pretty-print performance metrics."""
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    if metrics["total_trades"] == 0:
        print("  No trades generated.")
        return
    print(f"  Total trades:      {metrics['total_trades']}")
    print(f"  Win rate:          {metrics['win_rate']:.1%}")
    print(f"  Avg win:           {metrics['avg_win']:.2%}")
    print(f"  Avg loss:          {metrics['avg_loss']:.2%}")
    print(f"  Profit factor:     {metrics['profit_factor']:.2f}")
    print(f"  Max drawdown:      {metrics['max_drawdown']:.2%}")
    print(f"  Sharpe ratio:      {metrics['sharpe_ratio']:.2f}")
    print(f"  Total return:      {metrics['total_return']:.2%}")
    print(f"  Avg holding days:  {metrics['avg_holding_days']:.1f}")


# --- Main Execution ---
if __name__ == "__main__":
    print("RSI Mean-Reversion Backtest — Swedish Large Caps")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Parameters: RSI({RSI_PERIOD}), Buy<{RSI_BUY_THRESHOLD}, Sell>{RSI_SELL_THRESHOLD}")
    print(f"Commission: {COMMISSION_PCT:.2%} | Slippage: {SLIPPAGE_PCT:.2%}")

    all_trades = []

    for ticker in TICKERS:
        print(f"\nFetching {ticker}...", end=" ")
        try:
            df = fetch_data(ticker, START_DATE, END_DATE)
            trades = run_backtest(df, ticker)
            all_trades.append(trades)
            print(f"{len(trades)} trades found.")
            print_metrics(ticker, calculate_metrics(trades))
        except Exception as e:
            print(f"Error: {e}")

    # Combined results across all stocks
    if all_trades:
        combined = pd.concat(all_trades, ignore_index=True)
        combined.sort_values("entry_date", inplace=True)
        print_metrics("ALL STOCKS COMBINED", calculate_metrics(combined))

        # Show individual trades
        print(f"\n{'='*50}")
        print("  All Trades (chronological)")
        print(f"{'='*50}")
        for _, t in combined.iterrows():
            emoji = "W" if t["net_return"] > 0 else "L"
            print(
                f"  [{emoji}] {t['ticker']:>12} | "
                f"{t['entry_date'].strftime('%Y-%m-%d')} -> "
                f"{t['exit_date'].strftime('%Y-%m-%d')} | "
                f"{t['net_return']:+.2%} | {t['exit_reason']}"
            )
```

### Running the Example

```bash
pip install yfinance pandas-ta pandas numpy
python backtest_example.py
```

Expected output: a per-stock breakdown and combined metrics. The results will vary depending on the actual market data, but expect to see a mix of winning and losing trades. If the strategy shows a profit factor above 1.0 with 30+ trades, it is worth further investigation. If not, adjust parameters or try a different strategy.

---

## 9. From Backtest to Live

### 9.1 When Is a Backtest "Good Enough"?

A backtest is worth moving forward with if:

- **Profit factor > 1.2** after commission and slippage
- **Win rate reasonable** (not suspiciously high like 90%)
- **30+ trades** in the out-of-sample period for statistical confidence
- **Max drawdown tolerable** — could you actually sit through a 20% drawdown?
- **Results consistent** across multiple stocks, not just one outlier
- **Walk-forward results** similar to in-sample results (no dramatic degradation)

### 9.2 Paper Trading Phase

Before risking real capital, run your strategy live but without placing orders:

```python
"""
Paper trading: run your scanner daily, log signals to SQLite,
compare recommended trades to actual price outcomes.
"""
import sqlite3
from datetime import datetime

def log_signal(db_path: str, ticker: str, signal_type: str,
               signal_price: float, rsi_value: float):
    """Log a buy/sell signal for later comparison."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            signal_type TEXT,
            signal_price REAL,
            rsi_value REAL,
            actual_next_open REAL,
            outcome TEXT
        )
    """)
    conn.execute(
        "INSERT INTO paper_trades (timestamp, ticker, signal_type, signal_price, rsi_value) "
        "VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), ticker, signal_type, signal_price, rsi_value),
    )
    conn.commit()
    conn.close()
```

Run this for 2-4 weeks. Go back and fill in `actual_next_open` with real data. Compare the signal price to what you would have actually paid. This reveals the real-world execution gap.

### 9.3 Going Live with Minimum Size

When you start trading for real:

1. **Use minimum position sizes.** On Avanza, this might be 5,000-10,000 SEK per trade.
2. **Trade for at least 20-30 trades** before increasing size.
3. **Compare live results to backtest.** If live win rate is dramatically lower, investigate why.
4. **Scale up gradually.** Double position size only after consistent positive results.

The goal is not to make money immediately — it is to validate that your live results match your backtest results. If they do, you can confidently increase size. If they diverge, you need to understand why before risking more capital.

---

## References

- [../strategy-and-theory/07-backtesting-and-performance.md](../strategy-and-theory/07-backtesting-and-performance.md) — Backtesting theory, pitfalls, and statistical validation
- [../strategy-and-theory/24-execution-and-slippage-playbook.md](../strategy-and-theory/24-execution-and-slippage-playbook.md) — Execution and slippage in practice
- [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md) — Tech stack decisions (yfinance, pandas-ta, SQLite)
- [Backtrader documentation](https://www.backtrader.com/docu/)
- [Backtesting.py documentation](https://kernc.github.io/backtesting.py/)
- [vectorbt documentation](https://vectorbt.dev/)
