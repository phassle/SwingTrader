# Trading Journal Framework for Swing Trading

## Reference Document for Implementation

A trading journal is not a nice-to-have accessory. It is the primary feedback loop that separates traders who improve from those who repeat the same mistakes indefinitely. This document provides a complete framework for journaling, reviewing, and analyzing swing trades, with concrete schemas, templates, and implementation guidance for the SwingTrader application.

Cross-references:
- Strategy names and setup types: `04-swing-trading-strategies.md`
- Risk metrics and position sizing formulas: `05-risk-management.md`
- Performance metrics and statistical validation: `07-backtesting-and-performance.md`
- Market regime classification: `08-market-structure-and-conditions.md`
- Edge quality and empirical evidence: `10-empirical-evidence-and-edge-quality.md`

---

## Table of Contents

1. [Why Journal (The Evidence)](#1-why-journal-the-evidence)
2. [Trade Log Structure](#2-trade-log-structure)
3. [Database Schema](#3-database-schema)
4. [Analysis and Review](#4-analysis-and-review)
5. [Analytics and Metrics](#5-analytics-and-metrics)
6. [Psychological Journaling](#6-psychological-journaling)
7. [Implementation for the App](#7-implementation-for-the-app)

---

## 1. Why Journal (The Evidence)

### 1.1 Studies on Journaling and Trading Performance

The evidence connecting structured self-review to improved performance comes from multiple disciplines:

**Deliberate practice research (Ericsson, 1993):** Peak performance in any skill domain requires not just repetition but structured reflection on outcomes. Trading is a probabilistic skill, and without a journal, there is no structured reflection. Most traders "practice" by placing trades and hoping to learn through osmosis. This does not work.

**Decision journaling (Kahneman, "Thinking, Fast and Slow"):** Kahneman's research on cognitive biases demonstrates that humans consistently misremember their reasoning after the fact. Without a written record, traders reconstruct their decision-making process to match outcomes (hindsight bias). A trade that worked becomes "I knew the setup was strong" and a trade that failed becomes "the market was irrational." A journal captures the actual reasoning at the time of the decision.

**Behavioral finance evidence:** Barber and Odean (2000, 2001) showed that individual traders systematically overtrade, hold losers too long, sell winners too early, and overestimate their own skill. A journal with honest data makes these patterns visible and undeniable.

**Proprietary trading firm practices:** Nearly every professional prop trading firm requires traders to maintain detailed trade logs. SMB Capital, for example, requires daily journals including emotional state, setup quality, and post-trade review. Firms that manage real capital consider journaling non-optional because the data consistently shows that traders who journal outperform those who do not, controlling for strategy quality.

**Brett Steenbarger's clinical research:** Steenbarger, a clinical psychologist who has worked with professional traders at hedge funds and prop firms, has documented extensively that structured journaling is one of the most effective interventions for improving trading performance. His work shows that traders who review their journals systematically can identify behavioral patterns that are invisible during live trading.

### 1.2 Self-Awareness and Pattern Recognition

A journal turns subjective experience into objective data. Without it, a trader cannot answer basic questions:

- "Do I actually make money on breakout trades, or do I just remember the winners?"
- "Am I more profitable on Tuesdays than Fridays?"
- "Does my win rate drop when I trade more than 3 positions simultaneously?"
- "Do I consistently exit too early on trending moves?"

These questions can only be answered with data. A journal is the data collection mechanism.

**Pattern recognition is retrospective.** During live trading, the brain is in execution mode and pattern recognition is compromised by stress, excitement, and time pressure. Patterns only become visible in the calm of after-hours review, with a complete dataset laid out in front of you.

### 1.3 Identifying Strengths and Weaknesses

After 50-100 logged trades, a well-structured journal reveals:

| What You Learn | Example Finding |
|---|---|
| Best strategy | Pullback trades produce 2.1R average vs. 0.8R for breakouts |
| Worst setup | Counter-trend reversal trades lose money 65% of the time |
| Best market condition | Bull/low-vol regime produces 78% of annual profits |
| Worst emotional state | Trades taken when emotional state is 4-5 have 32% win rate vs. 58% baseline |
| Optimal holding period | Trades held 3-7 days outperform trades held 1-2 days or 8+ days |
| Position sizing issues | Oversized positions correlate with panic exits |

This information is worth more than any new indicator or strategy. Most traders spend 90% of their development time searching for better entries and 10% reviewing what actually works for them personally. The ratio should be inverted.

### 1.4 Accountability and Discipline

A journal creates accountability through two mechanisms:

**Self-accountability:** Writing "I violated my stop-loss rule for the third time this week" is uncomfortable. That discomfort is the point. The act of documenting rule violations creates an emotional cost that discourages future violations. Over time, the journal becomes a mirror that reflects actual behavior, not the idealized version a trader carries in their head.

**External accountability:** If a trader shares journal summaries with a mentor, trading group, or accountability partner, the effect is amplified. Knowing that someone will see the data creates additional motivation to follow the plan.

**Discipline as a measurable metric:** Without a journal, "discipline" is an abstract concept. With a journal, it becomes a number: "I followed my rules on 87% of trades this month, up from 74% last month." This transforms discipline from a personality trait into a skill that can be tracked and improved.

---

## 2. Trade Log Structure

### 2.1 Essential Fields for Each Trade

Every trade entry must capture the complete context of the decision, not just the outcome. The fields below are organized by category.

#### Identification Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `trade_id` | Auto-increment | Unique identifier | 1047 |
| `date_entered` | Datetime | Timestamp of entry order fill | 2026-03-05 10:32:00 |
| `date_exited` | Datetime | Timestamp of exit order fill | 2026-03-10 14:15:00 |
| `symbol` | String | Ticker symbol | AAPL |
| `direction` | Enum | Long or Short | LONG |

#### Price and Risk Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `entry_price` | Decimal | Actual fill price at entry | 178.45 |
| `stop_loss` | Decimal | Initial stop-loss level | 174.20 |
| `target_price` | Decimal | Initial profit target | 186.90 |
| `exit_price` | Decimal | Actual fill price at exit | 185.30 |
| `position_size` | Integer | Number of shares | 235 |
| `risk_amount` | Decimal | Dollar risk at entry: `position_size * abs(entry_price - stop_loss)` | $999.25 |
| `risk_percent` | Decimal | Percentage of account risked | 1.0% |

#### Strategy and Setup Fields

Reference `04-swing-trading-strategies.md` for strategy definitions.

| Field | Type | Description | Example |
|---|---|---|---|
| `strategy` | Enum | Strategy category used | EMA_CROSSOVER |
| `setup_type` | Enum | Specific setup pattern | PULLBACK_TO_21EMA |
| `timeframe` | Enum | Primary chart timeframe | DAILY |
| `entry_trigger` | Text | The specific signal that triggered entry | "Price bounced off 21 EMA with bullish engulfing candle; RSI at 45 turning up; volume 30% above average" |

Setup type enum values (aligned with `04-swing-trading-strategies.md`):
- `PULLBACK_TO_MA` - Pullback to moving average in a trend
- `BREAKOUT_RESISTANCE` - Breakout above horizontal resistance
- `BREAKOUT_RANGE` - Breakout from consolidation range
- `EMA_CROSSOVER` - Moving average crossover signal
- `BOLLINGER_BOUNCE` - Bounce off Bollinger Band
- `RSI_REVERSAL` - RSI oversold/overbought reversal
- `SUPPORT_BOUNCE` - Bounce off key support level
- `MACD_DIVERGENCE` - MACD divergence signal
- `GAP_CONTINUATION` - Gap and go / gap fill play
- `SWING_FAILURE` - Swing failure pattern
- `SUPPLY_DEMAND` - Supply/demand zone reaction
- `SECTOR_ROTATION` - Relative strength sector rotation

#### Market Context Fields

Reference `08-market-structure-and-conditions.md` for regime definitions.

| Field | Type | Description | Example |
|---|---|---|---|
| `market_regime` | Enum | Current market regime at entry | BULL_LOW_VOL |
| `market_trend` | Enum | SPY trend at entry (UP/DOWN/SIDEWAYS) | UP |
| `vix_at_entry` | Decimal | VIX level at time of entry | 16.4 |
| `sector` | String | Stock sector | Technology |
| `sector_strength` | Enum | Sector relative strength (LEADING/LAGGING/NEUTRAL) | LEADING |

Market regime enum values (from `08-market-structure-and-conditions.md`):
- `BULL_LOW_VOL` - Uptrend, low volatility
- `BULL_HIGH_VOL` - Uptrend, high volatility
- `BEAR_LOW_VOL` - Downtrend, low volatility
- `BEAR_HIGH_VOL` - Downtrend, high volatility
- `SIDEWAYS_LOW_VOL` - Range-bound, low volatility
- `SIDEWAYS_HIGH_VOL` - Range-bound, high volatility

#### Exit Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `exit_reason` | Enum | Why the trade was closed | TARGET_HIT |
| `exit_notes` | Text | Additional exit context | "Sold at target as price hit resistance zone with bearish divergence on RSI" |

Exit reason enum values:
- `TARGET_HIT` - Price reached profit target
- `STOP_HIT` - Stop-loss triggered
- `TRAILING_STOP` - Trailing stop triggered
- `TIME_EXIT` - Held too long without movement; time-based exit
- `DISCRETIONARY` - Manual exit based on changed thesis
- `PARTIAL_EXIT` - Scaled out partial position
- `GAP_THROUGH_STOP` - Price gapped through stop level

#### Outcome Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `pnl_dollars` | Decimal | Net profit/loss in dollars | $1,609.75 |
| `pnl_percent` | Decimal | Return on position | 3.84% |
| `r_multiple` | Decimal | `pnl_dollars / risk_amount` | 1.61R |
| `holding_days` | Integer | Calendar days held | 5 |
| `holding_bars` | Integer | Trading bars held | 4 |
| `commissions` | Decimal | Total commissions paid | $0.00 |
| `slippage` | Decimal | Estimated slippage cost | $12.50 |

**R-multiple explanation:** The R-multiple (from Van Tharp's work, referenced in `05-risk-management.md`) normalizes trade results by initial risk. A 2R trade means you made twice your initial risk. A -1R trade means you lost your full initial risk. This allows comparing trades with different position sizes and risk levels on a common scale. Expectancy = average R-multiple across all trades.

#### Screenshot Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `screenshot_entry` | File path | Chart screenshot at time of entry | /screenshots/1047_entry.png |
| `screenshot_exit` | File path | Chart screenshot at time of exit | /screenshots/1047_exit.png |

Screenshots should include:
- The primary timeframe chart with entry/exit marked
- Key indicators visible (moving averages, RSI, volume)
- Support/resistance levels drawn
- At least 60 bars of context before the trade

#### Psychological Fields

| Field | Type | Description | Example |
|---|---|---|---|
| `emotional_state` | Integer (1-5) | Emotional state at entry: 1=calm/focused, 5=anxious/agitated | 2 |
| `confidence_level` | Integer (1-5) | Confidence in the setup: 1=low, 5=high | 4 |
| `mistakes` | Text | Any rule violations or errors | "Entered slightly before confirmation candle closed" |
| `lessons_learned` | Text | Key takeaway from this trade | "Patience to wait for candle close would have given a better entry by $0.30" |
| `fomo_flag` | Boolean | Was this a FOMO-driven entry? | false |
| `revenge_flag` | Boolean | Was this a revenge trade? | false |

### 2.2 Trade Entry Template (Markdown Format)

For manual journaling or export, each trade can be rendered as:

```markdown
## Trade #1047 — AAPL LONG

**Entry:** 2026-03-05 10:32 @ $178.45
**Exit:** 2026-03-10 14:15 @ $185.30
**Stop:** $174.20 | **Target:** $186.90
**Shares:** 235 | **Risk:** $999.25 (1.0%)

**Strategy:** EMA Crossover — Pullback to 21 EMA
**Timeframe:** Daily
**Entry Trigger:** Price bounced off 21 EMA with bullish engulfing candle; RSI at 45 turning up; volume 30% above average.

**Market Context:** Bull/Low Vol | SPY uptrend | VIX: 16.4
**Sector:** Technology (Leading)

**Result:** +$1,609.75 (+3.84%) | **R-Multiple:** +1.61R
**Held:** 5 days (4 trading bars)
**Exit Reason:** Target hit

**Emotional State:** 2/5 (calm)
**Confidence:** 4/5
**Mistakes:** Entered slightly before confirmation candle closed.
**Lesson:** Patience to wait for candle close would have given a better entry by $0.30.

**Grade:** B+ (valid setup, slight execution error)
```

---

## 3. Database Schema

### 3.1 Relational Database Design

The schema below uses SQL (compatible with PostgreSQL or SQLite). It is normalized to support flexible querying, tagging, and review workflows.

### 3.2 Core Tables

#### `trades` Table

```sql
CREATE TABLE trades (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Identification
    symbol          VARCHAR(10) NOT NULL,
    direction       VARCHAR(5) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),

    -- Timing
    date_entered    TIMESTAMP NOT NULL,
    date_exited     TIMESTAMP,
    holding_days    INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM date_exited - date_entered)
    ) STORED,

    -- Price and risk
    entry_price     DECIMAL(12,4) NOT NULL,
    stop_loss       DECIMAL(12,4) NOT NULL,
    target_price    DECIMAL(12,4),
    exit_price      DECIMAL(12,4),
    position_size   INTEGER NOT NULL,
    risk_amount     DECIMAL(12,2) GENERATED ALWAYS AS (
        position_size * ABS(entry_price - stop_loss)
    ) STORED,
    risk_percent    DECIMAL(5,2),

    -- Strategy and setup
    strategy        VARCHAR(50) NOT NULL,
    setup_type      VARCHAR(50) NOT NULL,
    timeframe       VARCHAR(10) NOT NULL DEFAULT 'DAILY',
    entry_trigger   TEXT,

    -- Market context
    market_regime   VARCHAR(20),
    market_trend    VARCHAR(10),
    vix_at_entry    DECIMAL(6,2),
    sector          VARCHAR(50),
    sector_strength VARCHAR(10),

    -- Exit
    exit_reason     VARCHAR(30),
    exit_notes      TEXT,

    -- Outcome (computed after exit)
    pnl_dollars     DECIMAL(12,2) GENERATED ALWAYS AS (
        CASE
            WHEN direction = 'LONG'
                THEN position_size * (exit_price - entry_price)
            WHEN direction = 'SHORT'
                THEN position_size * (entry_price - exit_price)
        END
    ) STORED,
    pnl_percent     DECIMAL(8,4) GENERATED ALWAYS AS (
        CASE
            WHEN direction = 'LONG'
                THEN (exit_price - entry_price) / entry_price * 100
            WHEN direction = 'SHORT'
                THEN (entry_price - exit_price) / entry_price * 100
        END
    ) STORED,
    r_multiple      DECIMAL(8,2),
    commissions     DECIMAL(8,2) DEFAULT 0,
    slippage        DECIMAL(8,2) DEFAULT 0,

    -- Psychology
    emotional_state INTEGER CHECK (emotional_state BETWEEN 1 AND 5),
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 5),
    fomo_flag       BOOLEAN DEFAULT FALSE,
    revenge_flag    BOOLEAN DEFAULT FALSE,
    mistakes        TEXT,
    lessons_learned TEXT,

    -- Review
    trade_grade     CHAR(2),
    review_notes    TEXT,
    reviewed        BOOLEAN DEFAULT FALSE,

    -- Status
    status          VARCHAR(10) NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED'))
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_setup_type ON trades(setup_type);
CREATE INDEX idx_trades_date_entered ON trades(date_entered);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_market_regime ON trades(market_regime);
```

#### `tags` Table

Tags allow flexible categorization beyond fixed fields. Examples: "earnings_play", "high_volume", "gap_up", "sector_leader", "after_hours_news".

```sql
CREATE TABLE tags (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE trade_tags (
    trade_id    INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (trade_id, tag_id)
);
```

#### `screenshots` Table

```sql
CREATE TABLE screenshots (
    id          SERIAL PRIMARY KEY,
    trade_id    INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    type        VARCHAR(10) NOT NULL CHECK (type IN ('ENTRY', 'EXIT', 'SETUP', 'CONTEXT')),
    file_path   TEXT NOT NULL,
    caption     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_screenshots_trade_id ON screenshots(trade_id);
```

#### `daily_notes` Table

Daily notes capture the broader context of each trading day, independent of individual trades.

```sql
CREATE TABLE daily_notes (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL UNIQUE,
    market_summary  TEXT,
    market_regime   VARCHAR(20),
    spy_change      DECIMAL(6,2),
    vix_close       DECIMAL(6,2),
    pre_market_plan TEXT,
    end_of_day_review TEXT,
    emotional_state INTEGER CHECK (emotional_state BETWEEN 1 AND 5),
    sleep_hours     DECIMAL(3,1),
    exercise        BOOLEAN DEFAULT FALSE,
    stress_level    INTEGER CHECK (stress_level BETWEEN 1 AND 5),
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### `weekly_reviews` Table

```sql
CREATE TABLE weekly_reviews (
    id                  SERIAL PRIMARY KEY,
    week_start          DATE NOT NULL,
    week_end            DATE NOT NULL,

    -- Summary stats
    total_trades        INTEGER,
    wins                INTEGER,
    losses              INTEGER,
    win_rate            DECIMAL(5,2),
    total_pnl           DECIMAL(12,2),
    total_r             DECIMAL(8,2),
    avg_r               DECIMAL(8,2),
    largest_win_r       DECIMAL(8,2),
    largest_loss_r      DECIMAL(8,2),

    -- Qualitative
    best_trade_id       INTEGER REFERENCES trades(id),
    worst_trade_id      INTEGER REFERENCES trades(id),
    rule_violations     INTEGER DEFAULT 0,
    emotional_patterns  TEXT,
    market_conditions   TEXT,

    -- Planning
    goals_for_next_week TEXT,
    areas_to_improve    TEXT,

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(week_start)
);
```

#### `monthly_reviews` Table

```sql
CREATE TABLE monthly_reviews (
    id                      SERIAL PRIMARY KEY,
    month                   DATE NOT NULL UNIQUE,

    -- Performance
    total_trades            INTEGER,
    win_rate                DECIMAL(5,2),
    total_pnl               DECIMAL(12,2),
    total_r                 DECIMAL(8,2),
    avg_r                   DECIMAL(8,2),
    max_drawdown_pct        DECIMAL(5,2),
    max_drawdown_dollars    DECIMAL(12,2),

    -- Strategy breakdown (stored as JSON)
    strategy_performance    JSONB,
    setup_performance       JSONB,
    day_of_week_performance JSONB,

    -- Review
    what_worked             TEXT,
    what_didnt_work         TEXT,
    strategy_adjustments    TEXT,
    goal_progress           TEXT,

    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 3.3 Entity Relationship Summary

```
trades (1) ----< (many) trade_tags >---- (1) tags
trades (1) ----< (many) screenshots
daily_notes (independent, linked by date)
weekly_reviews (1) ---- references best/worst trades
monthly_reviews (independent, aggregation layer)
```

### 3.4 Key Queries

**Win rate by strategy:**
```sql
SELECT
    strategy,
    COUNT(*) AS total_trades,
    SUM(CASE WHEN pnl_dollars > 0 THEN 1 ELSE 0 END) AS wins,
    ROUND(SUM(CASE WHEN pnl_dollars > 0 THEN 1 ELSE 0 END)::DECIMAL
        / COUNT(*) * 100, 1) AS win_rate,
    ROUND(AVG(r_multiple), 2) AS avg_r,
    ROUND(SUM(r_multiple), 2) AS total_r
FROM trades
WHERE status = 'CLOSED'
GROUP BY strategy
ORDER BY total_r DESC;
```

**Performance by emotional state:**
```sql
SELECT
    emotional_state,
    COUNT(*) AS total_trades,
    ROUND(AVG(r_multiple), 2) AS avg_r,
    ROUND(SUM(CASE WHEN pnl_dollars > 0 THEN 1 ELSE 0 END)::DECIMAL
        / COUNT(*) * 100, 1) AS win_rate
FROM trades
WHERE status = 'CLOSED'
GROUP BY emotional_state
ORDER BY emotional_state;
```

**Performance by day of week:**
```sql
SELECT
    TO_CHAR(date_entered, 'Dy') AS day_of_week,
    EXTRACT(DOW FROM date_entered) AS dow_num,
    COUNT(*) AS total_trades,
    ROUND(AVG(r_multiple), 2) AS avg_r,
    ROUND(SUM(r_multiple), 2) AS total_r
FROM trades
WHERE status = 'CLOSED'
GROUP BY day_of_week, dow_num
ORDER BY dow_num;
```

**Consecutive wins and losses:**
```sql
WITH ordered_trades AS (
    SELECT
        id,
        pnl_dollars,
        CASE WHEN pnl_dollars > 0 THEN 'W' ELSE 'L' END AS result,
        ROW_NUMBER() OVER (ORDER BY date_exited) AS rn
    FROM trades
    WHERE status = 'CLOSED'
),
streaks AS (
    SELECT
        result,
        rn - ROW_NUMBER() OVER (PARTITION BY result ORDER BY rn) AS grp
    FROM ordered_trades
)
SELECT
    result,
    COUNT(*) AS streak_length
FROM streaks
GROUP BY result, grp
ORDER BY streak_length DESC
LIMIT 10;
```

---

## 4. Analysis and Review

### 4.1 Per-Trade Analysis

Every closed trade gets a post-trade review. This should happen the same day the trade is closed, while context is fresh. The review answers four questions and assigns a grade.

#### Four Questions Framework

| # | Question | What It Reveals |
|---|---|---|
| 1 | **Was the setup valid?** | Did the trade meet all the criteria defined in the strategy rules (`04-swing-trading-strategies.md`)? A valid setup that lost money is acceptable. An invalid setup that made money is a problem. |
| 2 | **Did I follow my rules?** | Entry, stop, target, position sizing, exit — were all rules followed? Count any deviations as rule violations. |
| 3 | **What could I have done better?** | Regardless of outcome, was there a better entry point, tighter stop, earlier exit signal, or better position size? |
| 4 | **What is the key lesson?** | One concrete, actionable takeaway that can improve future trading. Not "be more patient" but "wait for the candle to close before entering pullback trades on daily timeframe." |

#### Trade Grading System

| Grade | Criteria |
|---|---|
| **A** | Valid setup + all rules followed + good execution. Outcome is irrelevant. An A-trade that lost money is still an A-trade. |
| **B** | Valid setup + rules mostly followed + minor execution issues (slightly early entry, moved stop a few cents, etc.) |
| **C** | Setup was marginal or rules were partially violated. The trade may have worked, but the process was flawed. |
| **D** | Invalid setup, significant rule violations, or emotionally-driven entry/exit. Regardless of P&L, this is a problem trade. |
| **F** | FOMO trade, revenge trade, no plan at all, or gross position sizing violation. These trades threaten account survival. |

**The critical insight:** Grade trades on process, not outcome. A D-grade trade that made $500 is worse for long-term development than an A-grade trade that lost $200. Over hundreds of trades, good process produces good outcomes. The journal must reinforce process quality.

#### Per-Trade Review Template

```markdown
### Trade #1047 Review

**Setup Valid?** Yes — clean pullback to rising 21 EMA with volume confirmation.
**Rules Followed?** Mostly — entered 5 minutes before daily close instead of waiting.
**What Could Be Better?** Wait for the daily candle to close to confirm the bounce.
**Key Lesson:** Pre-close entries on daily timeframe add unnecessary risk of a late-day reversal.
**Grade:** B+
```

### 4.2 Weekly Review Process

The weekly review is the most important recurring analysis. It aggregates individual trade data into patterns and identifies areas for improvement. Schedule it for the same time each week (e.g., Sunday evening or Monday morning before market open).

#### Weekly Review Template

```markdown
# Weekly Review: 2026-03-02 to 2026-03-06

## Performance Summary
| Metric | Value |
|---|---|
| Total Trades | 6 |
| Wins | 4 |
| Losses | 2 |
| Win Rate | 66.7% |
| Total P&L | +$2,847.50 |
| Total R | +5.3R |
| Avg R per Trade | +0.88R |
| Largest Win | +2.1R (AAPL pullback) |
| Largest Loss | -1.0R (TSLA breakout failure) |

## Rule Compliance
| Metric | Value |
|---|---|
| Rule Violations | 1 |
| Violation Detail | Moved stop on NVDA trade to avoid being stopped out |
| A/B Trades | 4 |
| C/D Trades | 2 |

## Emotional Patterns
- Average emotional state at entry: 2.2/5
- Trades taken with emotional state >= 4: 1 (loss)
- Average confidence: 3.5/5
- FOMO trades: 0
- Revenge trades: 0

## Market Conditions
- SPY: +1.8% for the week, above all major MAs
- VIX: 15.2 -> 14.8 (declining, bullish)
- Regime: Bull/Low Vol
- Winning sectors: Technology, Consumer Discretionary
- Losing sectors: Energy, Utilities

## Best Trade
AAPL pullback to 21 EMA. Clean setup, patient entry, held to target.
Grade: A. This is what every trade should look like.

## Worst Trade
TSLA breakout. Entered on breakout but volume was below average.
Grade: C. Should have waited for volume confirmation.

## Key Takeaways
1. Pullback trades continue to outperform breakout trades for me.
2. The one rule violation (moving stop) happened on a day when I slept poorly.
3. Market conditions were favorable all week; do not confuse a rising tide with skill.

## Goals for Next Week
1. Zero rule violations.
2. Only take breakout trades with above-average volume.
3. No trades on days when sleep was < 6 hours.
```

### 4.3 Monthly Review

The monthly review zooms out to look at strategy-level performance and longer-term patterns. It connects back to the performance metrics in `07-backtesting-and-performance.md` and validates whether live results match backtested expectations.

#### Monthly Review Template

```markdown
# Monthly Review: February 2026

## Performance Overview
| Metric | Value | vs. Last Month |
|---|---|---|
| Total Trades | 22 | +3 |
| Win Rate | 59.1% | +4.1% |
| Total P&L | +$8,450.00 | +$2,100 |
| Total R | +14.7R | +3.2R |
| Avg R | +0.67R | +0.05R |
| Max Drawdown | -4.2% | -0.8% |
| Expectancy | 0.67R | +0.05R |

## Strategy Performance Breakdown
| Strategy | Trades | Win Rate | Avg R | Total R |
|---|---|---|---|---|
| Pullback to MA | 8 | 75.0% | +1.2R | +9.6R |
| Breakout | 6 | 50.0% | +0.5R | +3.0R |
| RSI Reversal | 4 | 50.0% | +0.3R | +1.2R |
| EMA Crossover | 4 | 50.0% | +0.2R | +0.9R |

## Setup Type Performance
| Setup | Trades | Win Rate | Avg R |
|---|---|---|---|
| Pullback to 21 EMA | 6 | 83.3% | +1.4R |
| Resistance Breakout | 4 | 50.0% | +0.6R |
| Support Bounce | 4 | 50.0% | +0.3R |
| Bollinger Bounce | 3 | 66.7% | +0.4R |

## Day of Week Performance
| Day | Trades | Avg R |
|---|---|---|
| Monday | 5 | +0.9R |
| Tuesday | 6 | +0.8R |
| Wednesday | 4 | +0.5R |
| Thursday | 4 | +0.3R |
| Friday | 3 | +0.1R |

## Market Conditions
- Primary regime: Bull/Low Vol (18 of 20 trading days)
- VIX range: 13.2 - 17.8
- SPY return: +3.2%
- Best performing days aligned with strong market up-days

## Drawdown Analysis
- Maximum drawdown: -4.2% (occurred Feb 12-15, a 3-day losing streak)
- Drawdown recovered in 4 trading days
- Drawdown was within acceptable limits per risk management rules (05-risk-management.md)

## Equity Curve
- Smooth upward trajectory with one pullback mid-month
- No new equity highs stalled for more than 5 days

## Goal Progress
| Goal | Status |
|---|---|
| Achieve 0.5R average expectancy | Met (+0.67R) |
| < 3 rule violations per month | Met (2 violations) |
| Log every trade within 24 hours | Met (100%) |

## Adjustments for Next Month
1. Allocate more focus to pullback strategies — they are producing the strongest results.
2. Reduce breakout trading until volume confirmation rule is consistently applied.
3. Consider avoiding Friday entries — data shows weakest performance.
```

### 4.4 Quarterly Review

The quarterly review is strategic. It evaluates whether your edge is still intact and whether structural changes are needed. This connects directly to edge validation concepts in `10-empirical-evidence-and-edge-quality.md`.

#### Quarterly Review Template

```markdown
# Quarterly Review: Q1 2026 (January - March)

## Performance Summary
| Metric | Q1 2026 | Q4 2025 | Change |
|---|---|---|---|
| Total Trades | 64 | 58 | +6 |
| Win Rate | 57.8% | 55.2% | +2.6% |
| Total R | +38.4R | +29.1R | +9.3R |
| Avg R | +0.60R | +0.50R | +0.10R |
| Max Drawdown | -6.1% | -8.3% | Improved |
| Sharpe Ratio | 1.82 | 1.45 | +0.37 |

## Edge Validation
- Backtested expectancy for primary strategy: 0.55R
- Live expectancy this quarter: 0.60R
- Conclusion: Edge is performing in line with or better than backtested expectations.
- No evidence of edge degradation.

## Strategy Adjustments
1. **Promote:** Pullback to MA strategy elevated to primary strategy. Allocate 50% of trades.
2. **Demote:** Pure breakout strategy underperforming. Limit to max 2 trades per week.
3. **Test:** Begin paper-trading supply/demand zone strategy for potential live introduction in Q2.

## Position Sizing Adjustments
- Current risk per trade: 1.0%
- Recommendation: Increase to 1.25% based on:
  - Documented edge sustained over 120+ trades
  - Emotional stability (avg emotional state: 2.1/5)
  - Max drawdown within acceptable bounds
  - Kelly criterion calculation suggests 3.2%, so 1.25% is safely below half-Kelly

## New Strategy Candidates
- Supply/demand zones (from 04-swing-trading-strategies.md, section 4.2)
- Begin backtesting with framework from 07-backtesting-and-performance.md
- Paper trade for 30 trades before live allocation

## Personal Development
- Strengths identified: Patience on pullback entries, consistent position sizing
- Weaknesses identified: Tendency to overtrade in sideways markets, Friday entries
- Action items:
  1. Implement a "sideways market" filter — reduce trade frequency by 50% when ADX < 20
  2. No new entries on Fridays unless setup is A-grade
  3. Begin tracking sleep and stress correlation with monthly data

## Goals for Q2
1. Maintain 0.55R or better expectancy
2. Successfully paper-trade supply/demand strategy (30+ trades)
3. Zero F-grade trades
4. Implement sideways market filter
```

---

## 5. Analytics and Metrics

### 5.1 Performance by Strategy

Track cumulative R-multiple for each strategy over time. This shows which strategies contribute to the equity curve and which detract from it.

**Metrics per strategy:**
- Total trades
- Win rate (%)
- Average R-multiple
- Total R-multiple
- Profit factor (gross profit / gross loss)
- Maximum consecutive losses
- Average holding period (days)
- Best R-multiple
- Worst R-multiple

### 5.2 Performance by Setup Type

Drill down within each strategy to see which specific setup types perform best. A strategy may have an overall positive expectancy, but specific setup types within it may be negative.

### 5.3 Performance by Day of Week

Many swing traders find consistent patterns in day-of-week performance. Common findings:
- Monday entries often benefit from weekend gap resolution
- Friday entries carry weekend gap risk and often underperform
- Mid-week entries (Tuesday-Wednesday) tend to be the most consistent

Track entries by day of week, not exits.

### 5.4 Performance by Market Condition

Using the regime classifications from `08-market-structure-and-conditions.md`:

| Regime | Trades | Win Rate | Avg R | Notes |
|---|---|---|---|---|
| Bull/Low Vol | 42 | 64.3% | +0.85R | Best conditions for long swing trades |
| Bull/High Vol | 12 | 50.0% | +0.40R | Wider stops needed, lower expectancy |
| Sideways | 8 | 37.5% | -0.20R | Should avoid or reduce size |
| Bear | 2 | 50.0% | +0.10R | Insufficient sample |

This data is essential for knowing when to be aggressive and when to sit on hands. If your system produces negative expectancy in sideways markets, you need a regime filter, not a better indicator.

### 5.5 Performance by Holding Period

Group trades by holding period (1 day, 2-3 days, 4-7 days, 8-14 days, 15+ days) and calculate win rate and average R for each bucket. This reveals optimal holding periods and whether you are exiting too early or too late.

### 5.6 Win Rate and Average R by Category

The two numbers that define a trading system are win rate and average R. These should be tracked for every slice of data:

**Expectancy formula (from `05-risk-management.md`):**
```
Expectancy = (Win Rate * Avg Win R) - (Loss Rate * Avg Loss R)
```

A system with 40% win rate and 2.5R average win vs. 1.0R average loss:
```
Expectancy = (0.40 * 2.5) - (0.60 * 1.0) = 1.0 - 0.6 = +0.40R per trade
```

### 5.7 Equity Curve and Drawdown Chart

The equity curve is the single most important visualization. It plots cumulative P&L over time (or cumulative R-multiple over time).

**Key features to display:**
- Cumulative R-multiple line (primary)
- High-water mark line (maximum cumulative R achieved)
- Drawdown area chart (shaded area between equity curve and high-water mark)
- 20-trade rolling average R (smoothed performance trend)

**Drawdown metrics:**
- Current drawdown (from peak)
- Maximum drawdown (largest peak-to-trough decline, ever)
- Average drawdown duration (days to recover)
- Maximum drawdown duration (longest recovery period)

### 5.8 Consecutive Wins/Losses Tracking

Tracking streaks serves two purposes:
1. **Risk management:** Knowing your historical maximum losing streak helps set realistic expectations and prevents panic during normal variance.
2. **Psychological preparedness:** If your system historically has 6-loss streaks, and you are currently on a 5-loss streak, the journal data prevents you from concluding "the system is broken" and abandoning it prematurely.

### 5.9 Expectancy Over Time (Rolling)

Plot a rolling expectancy calculated over the most recent 20, 50, and 100 trades. This reveals:
- Whether your edge is stable, improving, or degrading
- Seasonal patterns in performance
- The impact of strategy changes on overall expectancy

A declining rolling expectancy is an early warning signal that requires investigation. Possible causes:
- Market regime shift (your strategy may work in trending markets but not in ranges)
- Behavioral drift (gradually loosening rules)
- Genuine edge degradation (the market has adapted)

Cross-reference with regime data from `08-market-structure-and-conditions.md` to separate market-driven from behavior-driven performance changes.

---

## 6. Psychological Journaling

### 6.1 Pre-Trade Emotional Check-In

Before placing any trade, answer three questions and log the answers:

1. **How do I feel right now?** (1-5 scale: 1 = calm/focused, 5 = anxious/agitated)
2. **Why am I taking this trade?** (Must reference a specific setup from the trading plan)
3. **Am I reacting to something?** (Recent loss, recent win, news headline, social media, boredom?)

**Rule:** If emotional state is 4 or 5, do not trade. Walk away. This rule alone can prevent the majority of catastrophic trading errors.

**Implementation:** The app should present this check-in as a mandatory step before trade entry can be logged. It should not be possible to skip this step.

### 6.2 FOMO and Revenge Trade Flagging

Two of the most destructive emotional patterns in trading:

**FOMO (Fear of Missing Out):**
- Entering a trade because the price is "running away" without a proper setup
- Chasing a move after missing the original entry signal
- Taking a position because "everyone else is making money on this"
- Identifiers: entry above the intended zone, no clear stop level, elevated emotional state

**Revenge Trading:**
- Taking an impulsive trade immediately after a loss to "make it back"
- Increasing position size after a loss
- Abandoning the trading plan to take a different kind of trade
- Identifiers: trade occurs within 30 minutes of closing a losing trade, position size is larger than normal, no clear setup

**Flagging system:** Both FOMO and revenge trades should be explicitly flagged in the journal with boolean fields. Over time, the data will show:
- What percentage of trades are FOMO/revenge trades
- What the win rate is on FOMO/revenge trades (it is almost always significantly lower)
- What the average R-multiple is on FOMO/revenge trades (it is almost always negative)

This data provides the empirical justification for the discipline to avoid these trades.

### 6.3 Confidence Calibration

A powerful analysis: compare confidence level at entry to actual trade outcome.

| Confidence Level | Trades | Win Rate | Avg R |
|---|---|---|---|
| 1 (Low) | 8 | 37.5% | -0.3R |
| 2 | 15 | 46.7% | +0.1R |
| 3 | 25 | 60.0% | +0.6R |
| 4 | 20 | 65.0% | +0.9R |
| 5 (High) | 12 | 58.3% | +0.5R |

**Typical findings:**
- Low-confidence trades underperform (should not be taken)
- High-confidence trades sometimes underperform medium-confidence trades (overconfidence bias)
- The "sweet spot" is often confidence 3-4

If confidence has no correlation with outcome, that itself is useful information — it means the trader's subjective confidence is not a reliable signal and should not influence position sizing.

If confidence does correlate (e.g., confidence 4 trades have 1.5x the expectancy of confidence 2 trades), consider sizing up on high-confidence setups (within risk limits from `05-risk-management.md`).

### 6.4 Stress and Sleep Correlation

The daily notes table captures sleep hours and stress level. Over time, correlate these with trading performance:

```sql
SELECT
    dn.sleep_hours,
    COUNT(t.id) AS trades,
    ROUND(AVG(t.r_multiple), 2) AS avg_r,
    ROUND(SUM(CASE WHEN t.pnl_dollars > 0 THEN 1 ELSE 0 END)::DECIMAL
        / COUNT(*) * 100, 1) AS win_rate
FROM trades t
JOIN daily_notes dn ON DATE(t.date_entered) = dn.date
WHERE t.status = 'CLOSED'
GROUP BY dn.sleep_hours
ORDER BY dn.sleep_hours;
```

**Common findings:**
- Traders with < 6 hours of sleep have measurably worse performance
- Elevated stress (4-5) correlates with more rule violations
- Exercise days often correlate with better emotional regulation and fewer impulsive trades

This data transforms "get more sleep" from generic advice into a personal, evidence-based trading rule.

### 6.5 Identifying Emotional Triggers

After 100+ trade entries, review all D and F grade trades and look for common triggers:

| Trigger | Frequency | Pattern |
|---|---|---|
| After a losing streak (3+ losses) | 8 trades | Revenge trading; forcing trades to recover |
| Monday morning after a bad weekend | 4 trades | Emotional carryover; distracted |
| After a big win | 6 trades | Overconfidence; taking marginal setups |
| Market news / social media | 5 trades | FOMO; abandoning the plan for "hot tips" |
| End of month (near performance benchmarks) | 3 trades | Pressure to hit targets; forcing trades |

Once triggers are identified, create specific countermeasures:
- "After 3 consecutive losses, I take the rest of the day off."
- "I do not check social media during trading hours."
- "After a trade that makes > 3R, I wait 24 hours before the next entry."

---

## 7. Implementation for the App

### 7.1 Data Model Recommendations

The database schema in Section 3 serves as the foundation. Additional implementation considerations:

**Account tracking:**
```sql
CREATE TABLE accounts (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    broker          VARCHAR(50),
    account_type    VARCHAR(20),  -- CASH, MARGIN, PAPER
    initial_balance DECIMAL(12,2),
    current_balance DECIMAL(12,2),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add account_id to trades table
ALTER TABLE trades ADD COLUMN account_id INTEGER REFERENCES accounts(id);
```

**Strategy rules library:**
```sql
CREATE TABLE strategy_rules (
    id              SERIAL PRIMARY KEY,
    strategy        VARCHAR(50) NOT NULL,
    setup_type      VARCHAR(50) NOT NULL,
    entry_rules     TEXT NOT NULL,
    exit_rules      TEXT NOT NULL,
    stop_rules      TEXT NOT NULL,
    position_sizing TEXT NOT NULL,
    market_filter   TEXT,
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

This table stores the trading plan rules so that per-trade reviews can programmatically compare actual behavior against the plan.

**Equity snapshots:**
```sql
CREATE TABLE equity_snapshots (
    id              SERIAL PRIMARY KEY,
    account_id      INTEGER REFERENCES accounts(id),
    date            DATE NOT NULL,
    balance         DECIMAL(12,2) NOT NULL,
    open_pnl        DECIMAL(12,2) DEFAULT 0,
    closed_pnl      DECIMAL(12,2) DEFAULT 0,
    high_water_mark DECIMAL(12,2),
    drawdown_pct    DECIMAL(5,2),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 7.2 Dashboard Mockup Descriptions

#### Main Dashboard

The main dashboard shows at-a-glance performance and is the first screen a trader sees.

**Top row — Key metrics cards:**
- Total P&L (MTD) with green/red color
- Win rate (MTD) with trend arrow vs. last month
- Average R-multiple (MTD)
- Current drawdown from peak
- Open positions count

**Middle row — Charts (left to right):**
1. **Equity curve** (large, spanning ~60% width): Cumulative R-multiple over time with high-water mark overlay and drawdown shading. Toggle between 1M, 3M, 6M, 1Y, ALL views.
2. **Win rate by strategy** (bar chart, ~40% width): Horizontal bar chart showing win rate for each strategy with trade count labels.

**Bottom row — Recent trades table:**
- Last 10 closed trades showing: symbol, direction, entry/exit dates, P&L, R-multiple, grade, emotional state icon
- Click to expand into full trade detail view
- Color-coded rows: green for wins, red for losses, yellow for breakeven

#### Trade Entry Form

**Step 1 — Emotional Check-in (mandatory, cannot be skipped):**
- Emotional state slider (1-5)
- Confidence level slider (1-5)
- "Why am I taking this trade?" text box (required)
- FOMO/Revenge trade checkboxes (if checked, a warning dialog appears)

**Step 2 — Trade Details:**
- Symbol (autocomplete from watchlist)
- Direction toggle (Long/Short)
- Entry price, stop-loss, target price
- Position size (auto-calculated from risk rules)
- Strategy dropdown (from strategy_rules table)
- Setup type dropdown (filtered by selected strategy)
- Entry trigger text area
- Screenshot upload (drag and drop)

**Step 3 — Market Context (auto-populated where possible):**
- Market regime (dropdown, with suggestion based on current SPY/VIX data)
- VIX at entry (auto-filled from market data API, see `06-apis-and-technology.md`)
- Sector (auto-filled from symbol data)
- Sector strength (dropdown)

**Step 4 — Confirmation:**
- Summary card showing all details
- Calculated risk amount and risk percentage
- R:R ratio display
- "Confirm Entry" button

#### Trade Review Form (at exit)

- Exit price and exit reason (dropdown)
- Screenshot upload for exit chart
- The four review questions (see Section 4.1)
- Trade grade dropdown (A through F)
- Mistakes text area
- Lessons learned text area

#### Analytics Page

**Tab 1 — Performance Overview:**
- Equity curve with overlaid SPY benchmark
- Rolling 20-trade expectancy line chart
- Monthly P&L bar chart
- Drawdown waterfall chart

**Tab 2 — Strategy Analysis:**
- Strategy comparison table (win rate, avg R, total R, profit factor)
- Setup type heatmap (rows = setup types, columns = market regimes, cells = avg R, color intensity = trade count)
- Strategy equity curves (one line per strategy, overlaid)

**Tab 3 — Timing Analysis:**
- Day of week performance bar chart
- Holding period distribution histogram with avg R overlay
- Time of day entry analysis (if intraday timestamps are available)

**Tab 4 — Psychology:**
- Emotional state vs. win rate scatter plot
- Confidence calibration chart (confidence level vs. actual win rate)
- FOMO/revenge trade statistics card
- Sleep hours vs. performance chart (if daily notes data available)
- Rule violations trend line (weekly count over time)

**Tab 5 — Calendar View:**
- Monthly calendar grid where each day is colored by P&L (green gradient for profit, red gradient for loss, grey for no trades)
- Click on a day to see all trades and the daily note for that day
- Weekly and monthly P&L summaries in the margins

### 7.3 Key Charts and Visualizations

| Chart | Type | Purpose |
|---|---|---|
| Equity curve | Line chart | Overall performance trajectory |
| Drawdown chart | Area chart (inverted) | Visualize risk and recovery periods |
| Win rate by strategy | Horizontal bar chart | Identify best-performing strategies |
| R-multiple distribution | Histogram | Visualize the distribution of trade outcomes |
| Rolling expectancy | Line chart (20/50/100-trade windows) | Detect edge degradation or improvement |
| Day of week performance | Bar chart | Identify optimal trading days |
| Emotional state vs. R-multiple | Box plot or scatter | Quantify the impact of emotions on performance |
| Confidence calibration | Line chart (confidence vs. actual win rate) | Assess subjective confidence accuracy |
| Monthly P&L | Bar chart (positive/negative bars) | Track month-over-month progress |
| Strategy equity curves | Multi-line chart | Compare strategy contributions over time |
| Setup heatmap | Heatmap grid | Cross-tabulate setup types against market regimes |
| Calendar heatmap | Grid/calendar | Quick visual of daily P&L across months |

### 7.4 Export and Reporting Features

**Export formats:**
- CSV export of all trades with all fields (for external analysis in Excel or Python)
- PDF report generation for weekly, monthly, and quarterly reviews
- JSON export for API integrations or backup

**Automated reports:**
- Weekly summary email/notification with key metrics
- Monthly report auto-generated from trade data (pre-filled template from Section 4.3)
- Quarterly review template auto-populated with aggregated data

**Tax reporting:**
- Generate trade list compatible with Schedule D / Form 8949 format
- Wash sale identification (flag trades where the same symbol was bought within 30 days of a loss)
- Reference `09-regulation-tax-and-trade-operations.md` for tax rules

### 7.5 Tagging System for Categorization

Tags provide flexible, user-defined categorization beyond the fixed fields. Tags should be:

**System tags (auto-applied based on trade data):**
- `winner` / `loser` — based on P&L
- `big_winner` — R-multiple > 2.0
- `big_loser` — R-multiple < -1.5
- `gap_risk` — held overnight and gap > 2%
- `rule_violation` — has mistakes field filled
- `fomo` / `revenge` — based on flag fields

**User-defined tags (custom, per trade):**

Examples:
- `earnings_play` — trade around earnings event
- `sector_rotation` — trade based on sector relative strength
- `high_volume` — unusually high volume at entry
- `news_catalyst` — trade triggered by news event
- `dividend_play` — trade around ex-dividend date
- `after_hours` — significant after-hours price action involved
- `gap_up` / `gap_down` — trade involved a gap
- `low_float` — stock with low float/high short interest
- `large_cap` / `mid_cap` / `small_cap` — market cap classification

**Tag analytics:**
- Filter all metrics and charts by any combination of tags
- "Show me win rate for all trades tagged `earnings_play` + `gap_up` in `BULL_LOW_VOL` regime"
- Tag frequency analysis: which tags appear most often in winning vs. losing trades

---

## Appendix A: Quick-Start Checklist

For traders setting up a journal for the first time:

1. **Choose a medium.** Spreadsheet for simplicity, database for power, or the SwingTrader app for both.
2. **Log every trade.** No exceptions. Paper trades too. The journal is only useful with complete data.
3. **Log immediately.** Fill in entry details at the time of entry, exit details at the time of exit. Do not batch entries at the end of the week.
4. **Take screenshots.** At minimum, one chart screenshot at entry showing the setup and one at exit showing the result.
5. **Do the emotional check-in.** Before every trade. Every time. No exceptions.
6. **Grade every trade.** On process, not outcome.
7. **Do the weekly review.** Every week. Even if you had zero trades. A week with no trades is worth reviewing — why did you not trade? Was it discipline or avoidance?
8. **Wait for data.** Do not draw conclusions from fewer than 30 trades. Statistical significance requires sample size. See `07-backtesting-and-performance.md` for statistical validation methods.
9. **Be honest.** A journal that flatters your ego is useless. Log the mistakes, the FOMO trades, the revenge trades. The uncomfortable data is the most valuable data.
10. **Use the data.** A journal that is never reviewed is just busywork. The review process is where improvement happens.

## Appendix B: Minimum Viable Trade Log (Spreadsheet Version)

For traders who want to start immediately with a simple spreadsheet before building a full database:

| Column | Example |
|---|---|
| Date In | 2026-03-05 |
| Date Out | 2026-03-10 |
| Symbol | AAPL |
| Long/Short | L |
| Entry | 178.45 |
| Stop | 174.20 |
| Target | 186.90 |
| Exit | 185.30 |
| Shares | 235 |
| Risk $ | 999 |
| P&L $ | 1610 |
| R-Multiple | 1.61 |
| Strategy | Pullback |
| Setup | 21 EMA bounce |
| Regime | Bull/LV |
| Exit Reason | Target |
| Emotion (1-5) | 2 |
| Confidence (1-5) | 4 |
| Grade | B |
| Notes | Entered slightly early |

This captures 90% of the value with minimal overhead. Upgrade to the full database schema when trade volume or analysis needs warrant it.
