# Catalyst And Event Playbook For Swing Trading

Prepared by Codex on 2026-03-08. This file focuses on the events that most often change the quality, timing, and risk of swing trades in U.S. equities and ETFs. It is designed to complement `04-swing-trading-strategies.md`, `08-market-structure-and-conditions.md`, and any future daily routine or scanner files.

## Why this matters

Many swing trades work best when price movement is tied to a reason. Pure chart signals can still work, but catalyst-backed moves are usually easier to defend because they explain why repricing or follow-through may continue.

In practice, catalysts do four things:

- increase attention and liquidity
- change volatility and gap risk
- improve the odds of directional follow-through in some setups
- invalidate normal stop and target assumptions

## 1. Major catalyst categories

### Earnings and guidance

This is the most important catalyst class for most swing traders.

What to track:

- earnings date and time
- whether the report is before open or after close
- guidance changes
- management commentary on demand, margins, and outlook

Why it matters:

- earnings can create overnight repricing through gaps
- strong earnings reactions can lead to post-earnings drift
- failed earnings breakouts can produce some of the cleanest reversal trades

Base rule:

- treat every earnings-adjacent trade as a separate risk class from an ordinary chart setup

## 2. SEC filings and company-specific disclosures

The SEC's Form 8-K framework matters because many material corporate events are disclosed there. The SEC's final rule states that most reportable events on Form 8-K must be filed within `four business days` after the triggering event.

Events worth tracking:

- earnings releases and related disclosures
- management changes
- mergers, acquisitions, and strategic transactions
- financing announcements
- debt covenant issues
- restatements or non-reliance notices
- major customer, contract, or litigation developments

Swing-trading implication:

- if a stock is moving on headlines, check whether the move is supported by an actual filing or only by social-media interpretation
- the best primary sources are the company's investor relations page and SEC EDGAR filings

## 3. Macro catalysts

Some swings fail not because the stock setup was bad, but because the macro calendar dominated the tape.

### FOMC

The Federal Reserve publishes official `FOMC meeting calendars and information`, including meeting dates, statements, minutes, and press conferences.

Why it matters:

- FOMC days can change index direction, rates expectations, and sector leadership
- high-beta and growth-heavy setups often become more fragile around Fed decisions

### CPI and major labor data

The Bureau of Labor Statistics publishes CPI release timing on its official site. As of `March 8, 2026`, the BLS page states that `February 2026 CPI data are scheduled to be released on March 11, 2026, at 8:30 A.M. Eastern Time`.

Why it matters:

- CPI can reprice rates-sensitive equities, index futures, and sector leadership before the cash session opens
- high-conviction overnight swings into CPI carry materially different gap risk than ordinary overnight holds

Operational rule:

- every weekly watchlist should include the next dates for FOMC, CPI, jobs, and any major scheduled macro release relevant to the strategy

## 4. Sector and industry catalysts

Stocks often move first as a group and only second as individual stories.

Examples:

- crude oil moves affecting energy names
- biotech regulatory decisions affecting a drug theme
- semiconductor export or policy headlines affecting chip names
- retail sales and consumer commentary affecting consumer discretionary names

What to monitor:

- sector ETFs
- leading names in the group
- news affecting the whole industry, not just one ticker

Swing-trading implication:

- a long setup is stronger when the stock, sector, and market are aligned
- a single-stock breakout inside a weak sector deserves a lower quality score

## 5. FDA and biotech catalysts

Biotech and med-tech names need special treatment. The FDA states that its `Advisory Committee Calendar` contains notices of advisory committee meetings, and those meetings are often important event markers for affected stocks.

What to track:

- advisory committee meetings
- approval decisions
- trial readouts
- safety updates

Why it matters:

- these events can produce binary gaps
- normal technical stop logic is often meaningless across the event itself

Base rule:

- biotech catalyst trades should be tagged separately from ordinary momentum or mean-reversion setups

## 6. Event quality hierarchy

Not all catalysts are equal.

`Higher-quality catalysts`

- confirmed earnings surprise plus guidance
- filed merger or strategic transaction
- filed management or financing event with clear financial impact
- official macro release with broad market significance

`Medium-quality catalysts`

- analyst upgrade or downgrade
- conference commentary
- large customer or product announcement without filing support

`Lower-quality catalysts`

- rumor-only headlines
- social media promotion without primary-source confirmation
- unexplained volume spikes in low-information names

## 7. Event-trade playbook

### Pre-event

Before entering:

- identify the exact event date and time
- decide whether holding through the event is allowed
- decide whether size should be reduced before the event
- define whether the setup is continuation, fade, or post-event digestion

### Event day

On the event day:

- expect wider spreads and faster tape
- require higher quality for market orders in thinner names
- avoid assuming that intraday support and resistance will behave normally

### Post-event

After the event:

- decide whether the move is accepted or rejected
- look for hold above gap midpoint, hold above breakout level, or failure back into prior range
- compare volume and closing location to normal price behavior

## 8. Practical classification for an app

Each swing setup should carry catalyst metadata:

- `catalyst_type`
- `event_date`
- `event_time`
- `confirmed_source`
- `hold_through_event_allowed`
- `event_risk_level`
- `post_event_status`

This matters because a breakout without earnings risk is not the same object as a breakout one hour before an earnings release.

## 9. What to avoid

- treating all gaps as identical
- holding full size through binary events without explicit permission in the plan
- trusting rumor-driven price action in low-liquidity names
- ignoring macro calendars while trading index-sensitive setups
- confusing social-media promotion with institutional-quality catalyst flow

## Bottom line

If trend, structure, and risk management explain `how` to trade, catalysts explain `why now`. A serious swing-trading process should maintain an event calendar and classify trades by catalyst type before entry. That improves setup quality, sizing discipline, and post-trade review.

## Sources

- SEC final rule, "Additional Form 8-K Disclosure Requirements and Acceleration of Filing Date"
  https://www.sec.gov/rules-regulations/2004/03/additional-form-8-k-disclosure-requirements-acceleration-filing-date

- Federal Reserve, "Meeting calendars and information"
  https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

- Federal Reserve, April 2026 calendar page
  https://www.federalreserve.gov/newsevents/2026-04.htm

- U.S. Bureau of Labor Statistics, CPI
  https://www.bls.gov/cpi/

- FDA Advisory Committee Calendar
  https://www.fda.gov/advisory-committees/advisory-committee-calendar

- NBER Digest, "Bad News Travels Slowly: Size, Analyst Coverage, and the Profitability of Momentum Strategies"
  https://www.nber.org/digest/nov04/bad-news-travels-slowly-size-analyst-coverage-and-profitability-momentum-strategies
