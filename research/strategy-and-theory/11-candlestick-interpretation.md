# How To Interpret Candlesticks

Prepared by Codex on 2026-03-08. This file complements `03-chart-patterns.md` by focusing on how candlesticks should be interpreted in context, not just what the patterns are called.

## Short conclusion

A candlestick should not be interpreted as a standalone buy or sell signal. It should be read as a compressed expression of:

- where price opened
- how far price traveled
- who had control near the close
- whether the move happened at trend, support, resistance, a gap, or high volume

The practical point is simple: the same candle can be bullish, bearish, or neutral depending on context.

## 1. What a candlestick actually shows

A candlestick shows `open`, `high`, `low`, and `close` for a chosen time period.

- `Body` shows the distance between open and close.
- `Upper wick` shows how far price traded above the body.
- `Lower wick` shows how far price traded below the body.
- Color usually shows whether the candle closed above or below the open, but color schemes vary across platforms.

Nasdaq describes candlesticks as a way to display open, close, high, and low for each period. CME emphasizes that the body and wicks together make it easier to see buying and selling pressure.

## 2. Always start with context, not the pattern name

Charles Schwab emphasizes that candles should be read in terms of how they behave at `support` and `resistance`. Fidelity's technical material describes candlestick and multi-bar patterns as `supplementary`, meaning supportive information rather than the full analysis.

That means the first questions should be:

1. Is the market in an uptrend, downtrend, or range?
2. Did the candle appear at an important level?
3. Did it appear after a gap, news release, or earnings event?
4. Is volume higher or lower than normal?
5. Is the signal confirmed by the next candle?

If you start with "this is a hammer, therefore buy," you skip the part that actually determines whether the signal is usable.

## 3. How to interpret the candle body

### Large body

A large body means price moved clearly between open and close during the period. CME describes a long body as a sign of stronger price movement and more intense buying or selling pressure.

Interpretation:

- large green body: buyers had clear control
- large red body: sellers had clear control
- several large bodies in the same direction: momentum or trend pressure

But:

- a large candle directly into resistance can be exhaustion, not continuation
- a large candle after news can be an overreaction that quickly reverses

### Small body

A small body means open and close were close together. That often signals balance or hesitation rather than clear control.

Interpretation:

- consolidation
- uncertainty
- pause in trend
- possible turning point if it appears after a strong move and gets confirmation

## 4. How to interpret the wicks

CME notes that long wicks show that both buyers and sellers were active during the period.

### Long upper wick

Interpretation:

- price traded higher but could not stay there
- sellers pushed price back before the close
- often a sign of rejection from higher levels

It becomes more bearish if:

- it appears after an advance
- it hits resistance
- volume is high
- the next candle closes lower

### Long lower wick

Interpretation:

- price was pushed lower but buyers stepped back in
- the area below the candle may act as support
- often a sign of absorption of selling pressure

It becomes more bullish if:

- it appears after a decline
- it forms at support
- the next candle closes higher

### Short or no wicks

When the wicks are very small, that often means the side that won also held control into the close. CME specifically notes that a short or nonexistent wick reflects strong price action into the close.

Interpretation:

- full body near the high: strong bullish control
- full body near the low: strong bearish control

## 5. Close matters more than open

In practical candlestick interpretation, `close` is usually the most important data point because it shows who had control when the period ended.

Examples:

- a candle that closes near its high signals stronger buyer control than a candle that closes in the middle of its range
- a candle that closes near its low signals stronger seller control
- a doji or small body near the middle of the range signals hesitation

This is especially important on daily charts, where the close is often used as confirmation for breakout, reversal, or continuation.

## 6. Common candle types and how they should be interpreted

This file does not replace the pattern catalog in `03-chart-patterns.md`, but here is the practical interpretation.

### Doji

A doji means open and close are very close together.

Interpretation:

- indecision
- balance between buyers and sellers
- potential reversal only if it appears after a clear trend move and receives confirmation

Nasdaq uses the doji as an example of uncertainty in an uptrend that can come before trend change. On its own, it is not enough.

### Hammer

A hammer has a small body near the top of the candle and a long lower wick.

Interpretation:

- sellers pushed price down first
- buyers regained control before the close
- most interesting after a downtrend or at support

A bullish interpretation ideally requires:

- a preceding decline
- a clear lower wick
- confirmation from the next candle

### Shooting Star / Hanging Man

These candles show a small body with a clear upper wick.

Interpretation:

- buyers managed to push price higher
- but sellers took control back toward the end

It becomes a more relevant bearish signal when it appears:

- after an uptrend
- at resistance
- with high volume
- followed by a weak next candle

### Engulfing

Engulfing is a relationship between two candles where the second one dominates the first.

Interpretation:

- bullish engulfing after a decline can show that buyers abruptly took control
- bearish engulfing after an advance can show that sellers took control

Important point:

- engulfing in the middle of a sideways range means less than engulfing at a key level

## 7. Timeframe changes the meaning

CME emphasizes that candlesticks can be read on different time resolutions. A 5-minute candle and a daily candle show the same kind of data, but with very different signal value.

In practice:

- `weekly` gives stronger structural signal but fewer opportunities
- `daily` is often best for swing trading
- `intraday` is noisier and requires more volume and level context

A bullish daily hammer into weekly resistance is not as strong as a bullish daily hammer that also appears at weekly support.

## 8. Volume determines whether the candle signal is credible

Nasdaq points out that volume often confirms the strength of a trend change or breakout.

That means:

- a bullish candle on high volume is stronger than the same candle on low volume
- bearish rejection from resistance on high volume is more relevant
- a breakout candle without volume confirmation fails more often

A candle shows the shape of price. Volume helps determine whether the market actually cared about the move.

## 9. Gaps change the interpretation

CME highlights gaps as special signals of momentum. A candle after a gap should therefore be read differently from a normal candle.

Examples:

- gap up plus strong close near the high: continuation until proven otherwise
- gap up plus long upper wick: risk of a gap fade
- gap down plus long lower wick: possible capitulation or short-term bottom candidate

Gaps are especially important around earnings, press releases, and macro events.

## 10. Confirmation is a rule, not a detail

Fidelity's material describes short-term candlestick patterns as supportive information. That is a good operating rule: candle first, decision after confirmation.

Common forms of confirmation:

- the next candle continues in the same direction
- breakout above the high or below the low of the signal candle
- volume expansion
- alignment with trend, support/resistance, or momentum indicators

Without confirmation, candlestick reading easily turns into hindsight analysis.

## 11. Common misreadings

### Mistake 1: Interpreting every candle in isolation

A hammer in the middle of a range often means much less than a hammer at long-term support.

### Mistake 2: Ignoring the inbound trend

A reversal candle without a prior move often carries limited information.

### Mistake 3: Ignoring larger levels

Schwab's focus on support and resistance is central. Candles become most useful when they appear where many market participants are already watching.

### Mistake 4: Overestimating single candle names

Fidelity's Recognia material describes candlestick patterns as short-term and often supplementary. That is a clear warning against building an entire system on single pattern names.

### Mistake 5: Confusing strong movement with a good entry

A strong bullish candle can mean strength, but it can also mean price is already too extended from a sensible risk level.

## 12. Practical checklist for swing trading

When reading a candle, go through this in order:

1. What timeframe am I analyzing?
2. Is the broader trend up, down, or sideways?
3. Is the candle at support, resistance, a trendline, or a prior gap?
4. How large is the body relative to prior candles?
5. Where does the candle close within its own range?
6. Are the wicks long enough to show rejection?
7. Is there volume confirmation?
8. Does the next candle need to confirm before entry?
9. Where does the stop logically belong if the interpretation is wrong?

If you cannot answer those questions, it is too early to call the candle a trading signal.

## Bottom line

The correct way to interpret candlesticks is not to memorize the most pattern names. It is to read `body`, `wick`, `close`, `trend`, `level`, `volume`, and `confirmation` as a whole. Candlesticks work best as a language for order flow and market psychology, not as standalone answers.

## Sources

- CME Group, "Chart Types: candlestick, line, bar"
  https://www.cmegroup.com/education/courses/technical-analysis/chart-types-candlestick-line-bar

- Charles Schwab, "Getting Started with Technical Analysis | Lesson 4"
  https://www.schwab.com/learn/story/getting-started-with-technical-analysis-lesson-4

- Nasdaq, "Candlestick chart" glossary
  https://www.nasdaq.com/glossary/c/candlestick-chart

- Nasdaq, "How to Identify Changes in Market Trends"
  https://www.nasdaq.com/articles/how-identify-changes-market-trends

- Fidelity, "Research Help: Technical Analysis"
  https://scs.fidelity.com/webcontent/ap010098-etf-content/17.04/help/research/learn_er_technical_analysis.shtml

- Fidelity, "Help - Research Glossary: A through E"
  https://www.fidelity.com/webcontent/ap010098-etf-content/18.09.0/help/research/learn_er_glossary_1.shtml
