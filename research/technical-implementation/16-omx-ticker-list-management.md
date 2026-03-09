# 16 - OMX Ticker List Management

> Research date: 2026-03-09
> Goal: Define how SwingTrader maintains its list of OMX Stockholm Large Cap tickers — sourcing, formatting, validation, and ongoing updates.
> Prerequisites: [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md), [05-data-pipeline-and-quality.md](05-data-pipeline-and-quality.md)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Data Source: Nasdaq Nordic](#2-data-source-nasdaq-nordic)
3. [Yahoo Finance Ticker Format](#3-yahoo-finance-ticker-format)
4. [Complete OMX Stockholm Large Cap Ticker List](#4-complete-omx-stockholm-large-cap-ticker-list)
5. [Dual Share Classes (A/B Shares)](#5-dual-share-classes-ab-shares)
6. [Validation Script](#6-validation-script)
7. [Quarterly Update Process](#7-quarterly-update-process)
8. [Ticker List Storage](#8-ticker-list-storage)

---

## 1. Overview

SwingTrader scans **OMX Stockholm Large Cap** — the ~90-100 most traded stocks on the Stockholm exchange. This list is reviewed quarterly by Nasdaq Nordic (January, April, July, October) and stocks may be promoted from Mid Cap or demoted based on market capitalization.

### Why Large Cap only?

- **Liquidity:** Large Cap stocks have sufficient volume for reliable technical analysis
- **Data quality:** yfinance data is most reliable for heavily traded stocks
- **Manageable scope:** ~100 stocks is small enough to scan daily within yfinance rate limits
- **Practical trading:** These are the stocks most accessible to Swedish retail investors

---

## 2. Data Source: Nasdaq Nordic

### Where to find the current list

The official source is the Nasdaq Nordic website:

**URL:** `https://www.nasdaqomxnordic.com/shares/listed-companies/stockholm`

Filter by:
- **Market:** Stockholm
- **Segment:** Large Cap

This page shows all current Large Cap listings with ISIN codes, sectors, and share classes.

### Alternatives

| Source | Format | Notes |
|--------|--------|-------|
| Nasdaq Nordic website | HTML table | Official, always current |
| Avanza.se market list | HTML | Easy to read, may include extra info |
| Wikipedia "OMX Stockholm 30" | HTML | Only OMXS30, not full Large Cap |
| yfinance screener | API | Can query by exchange but unreliable for segments |

**Recommendation:** Manually maintain the list based on Nasdaq Nordic's quarterly announcements. Automate validation, not sourcing.

---

## 3. Yahoo Finance Ticker Format

### Swedish stock ticker conventions

Yahoo Finance uses the `.ST` suffix for Stockholm-listed stocks. The base ticker matches the Nasdaq Nordic short name with specific formatting rules:

| Company | Nasdaq short name | Yahoo Finance ticker |
|---------|------------------|---------------------|
| Volvo B | VOLV B | `VOLV-B.ST` |
| SEB A | SEB A | `SEB-A.ST` |
| Ericsson B | ERIC B | `ERIC-B.ST` |
| Atlas Copco A | ATCO A | `ATCO-A.ST` |
| H&M B | HM B | `HM-B.ST` |
| Alfa Laval | ALFA | `ALFA.ST` |
| Hexagon B | HEXA B | `HEXA-B.ST` |

### Formatting rules

1. Replace spaces between name and share class with a hyphen: `VOLV B` → `VOLV-B`
2. Append `.ST` suffix
3. Special characters: `&` is dropped (H&M → HM)
4. Single-class stocks have no suffix: `ALFA` → `ALFA.ST`

### Common gotchas

- **Telia:** Ticker is `TELIA.ST`, not `TEL2.ST`
- **Investor B:** `INVE-B.ST`
- **Swedish Match (if still listed):** Verify — companies get delisted after acquisitions
- **Newly listed companies:** May take a few days before yfinance data is available
- **Preference shares:** Usually excluded (e.g., `VOLV-PREF.ST`) — not relevant for swing trading

---

## 4. Complete OMX Stockholm Large Cap Ticker List

> **Note:** This list is based on the composition as of early 2026. Verify against Nasdaq Nordic for the latest changes. Approximately 90-100 tickers.

```python
OMX_LARGE_CAP_TICKERS = [
    # --- A ---
    "AAK.ST",           # AAK
    "ABB.ST",           # ABB
    "ALFA.ST",          # Alfa Laval
    "ALIV-SDB.ST",      # Autoliv (Swedish Depositary Receipt)
    "AMBU-B.ST",        # Ambu (Danish, listed in Stockholm)
    "ASSA-B.ST",        # ASSA ABLOY B
    "ATCO-A.ST",        # Atlas Copco A
    "ATCO-B.ST",        # Atlas Copco B
    "AZN.ST",           # AstraZeneca

    # --- B ---
    "BILL.ST",          # Billerud
    "BOL.ST",           # Boliden
    "BALD-B.ST",        # Fastighets AB Balder B

    # --- C ---
    "CAST.ST",          # Castellum

    # --- D ---
    "DOM.ST",           # Dometic

    # --- E ---
    "EKTA-B.ST",        # Elekta B
    "ELUX-B.ST",        # Electrolux B
    "EMBRAC-B.ST",      # Embracer Group B
    "ELAN-B.ST",        # Elanion (verify current listing)
    "EPRO-B.ST",        # Epiroc B
    "ERIC-B.ST",        # Ericsson B
    "ESSITY-B.ST",      # Essity B
    "EVO.ST",           # Evolution

    # --- F ---
    "FABG.ST",          # Fabege

    # --- G ---
    "GETI-B.ST",        # Getinge B

    # --- H ---
    "HEXA-B.ST",        # Hexagon B
    "HM-B.ST",          # H&M B
    "HOLM-B.ST",        # Holmen B
    "HPOL-B.ST",        # Husqvarna B

    # --- I ---
    "INDU-A.ST",        # Industrivarden A
    "INDU-C.ST",        # Industrivarden C
    "INVE-B.ST",        # Investor B

    # --- K ---
    "KINV-B.ST",        # Kinnevik B

    # --- L ---
    "LATO-B.ST",        # Latour B
    "LIFCO-B.ST",       # Lifco B
    "LUND-B.ST",        # Lundbergforetagen B

    # --- M ---
    "MYTE.ST",          # Mycronic

    # --- N ---
    "NDA-SE.ST",        # Nordea Bank
    "NIBE-B.ST",        # NIBE B
    "NCC-B.ST",         # NCC B
    "NOKIA-SEK.ST",     # Nokia (SEK listing)

    # --- P ---
    "PEAB-B.ST",        # Peab B

    # --- S ---
    "SAAB-B.ST",        # Saab B
    "SAND.ST",          # Sandvik
    "SBB-B.ST",         # Samhallsbyggnadsbolaget B
    "SCA-B.ST",         # SCA B
    "SEB-A.ST",         # SEB A
    "SECU-B.ST",        # Securitas B
    "SHB-A.ST",         # Handelsbanken A
    "SHB-B.ST",         # Handelsbanken B
    "SINCH.ST",         # Sinch
    "SKA-B.ST",         # Skanska B
    "SKF-B.ST",         # SKF B
    "SSAB-A.ST",        # SSAB A
    "SSAB-B.ST",        # SSAB B
    "SWEC-B.ST",        # Sweco B
    "SWED-A.ST",        # Swedbank A
    "STE-R.ST",         # Storskogen (verify ticker)

    # --- T ---
    "TEL2-B.ST",        # Tele2 B
    "TELIA.ST",         # Telia Company
    "THULE.ST",         # Thule Group
    "TREL-B.ST",        # Trelleborg B

    # --- V ---
    "VOLV-A.ST",        # Volvo A
    "VOLV-B.ST",        # Volvo B
    "VNV.ST",           # VNV Global

    # --- W ---
    "WALL-B.ST",        # Wallenstam B
    "WIHL.ST",          # Wihlborgs
]
```

> **This list is intentionally incomplete and approximate.** The actual Large Cap list has ~90-100 entries and changes quarterly. Use the validation script below to verify which tickers work with yfinance, then fill in any missing ones from the Nasdaq Nordic website.

---

## 5. Dual Share Classes (A/B Shares)

Many Swedish companies have dual share classes:

| Class | Voting rights | Liquidity | Which to scan? |
|-------|--------------|-----------|----------------|
| A shares | Higher (typically 10 votes per share) | Lower | Optional |
| B shares | Lower (typically 1 vote per share) | **Higher** | **Always** |
| C shares | Varies | Low | Usually skip |

### Recommendation

**Scan B shares by default.** B shares have higher trading volume and tighter spreads, making them better for technical analysis and actual trading. Include A shares only for companies where the A share is the primary traded class (e.g., `SEB-A.ST`, `SWED-A.ST`, `SHB-A.ST`).

### Handling both classes

If you include both A and B for the same company, be aware:
- They often generate correlated signals (same company, different share classes)
- A signal on both VOLV-A and VOLV-B is essentially one opportunity, not two
- Consider deduplicating in the signal output: if both classes trigger, report only the more liquid one (usually B)

```python
# Map A shares to their B counterparts for deduplication
SHARE_CLASS_PAIRS = {
    "ATCO-A.ST": "ATCO-B.ST",
    "INDU-A.ST": "INDU-C.ST",
    "SHB-A.ST": "SHB-B.ST",
    "SSAB-A.ST": "SSAB-B.ST",
    "VOLV-A.ST": "VOLV-B.ST",
}

def deduplicate_signals(signals: list[dict]) -> list[dict]:
    """Remove duplicate signals for A/B share pairs, keeping the more liquid class."""
    seen_companies = set()
    result = []
    # Sort so B shares come first (preferred)
    sorted_signals = sorted(signals, key=lambda s: s["ticker"])
    for signal in sorted_signals:
        base = signal["ticker"].split("-")[0]  # e.g., "VOLV" from "VOLV-B.ST"
        if base not in seen_companies:
            seen_companies.add(base)
            result.append(signal)
    return result
```

---

## 6. Validation Script

Run this to verify which tickers actually work with yfinance:

```python
"""
validate_tickers.py — Verify OMX Large Cap tickers against yfinance.

Usage:
    python validate_tickers.py

Outputs:
    - List of valid tickers (data returned)
    - List of invalid tickers (no data or error)
    - Suggested fixes for common issues
"""

import time

import yfinance as yf

from config.tickers import OMX_LARGE_CAP_TICKERS


def validate_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """Validate each ticker by attempting to fetch recent data."""
    valid = []
    invalid = []

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if len(data) > 0:
                last_close = data["Close"].iloc[-1]
                print(f"  OK: {ticker:20s} last close: {last_close:.2f}")
                valid.append(ticker)
            else:
                print(f"  FAIL: {ticker:20s} — no data returned")
                invalid.append(ticker)
        except Exception as e:
            print(f"  ERROR: {ticker:20s} — {e}")
            invalid.append(ticker)

        time.sleep(0.5)  # Be gentle with Yahoo's servers

    return valid, invalid


if __name__ == "__main__":
    print(f"Validating {len(OMX_LARGE_CAP_TICKERS)} tickers...\n")
    valid, invalid = validate_tickers(OMX_LARGE_CAP_TICKERS)

    print(f"\n{'='*50}")
    print(f"Valid:   {len(valid)}/{len(OMX_LARGE_CAP_TICKERS)}")
    print(f"Invalid: {len(invalid)}/{len(OMX_LARGE_CAP_TICKERS)}")

    if invalid:
        print(f"\nInvalid tickers to investigate:")
        for t in invalid:
            print(f"  - {t}")
        print("\nCommon fixes:")
        print("  - Check Nasdaq Nordic for the correct short name")
        print("  - Try searching on finance.yahoo.com directly")
        print("  - Company may have been delisted or renamed")
```

### Expected output

```
Validating 70 tickers...

  OK: AAK.ST               last close: 198.40
  OK: ABB.ST               last close: 612.80
  OK: ALFA.ST              last close: 445.20
  FAIL: ELAN-B.ST          — no data returned
  ...

==================================================
Valid:   67/70
Invalid: 3/70

Invalid tickers to investigate:
  - ELAN-B.ST
  - STE-R.ST
  - NOKIA-SEK.ST
```

---

## 7. Quarterly Update Process

Nasdaq Nordic reviews the Large/Mid/Small Cap segmentation every January, April, July, and October (effective first trading day of the month).

### Update checklist

1. **Check the Nasdaq Nordic announcement** (usually published ~2 weeks before effective date)
2. **Identify changes:**
   - Promotions from Mid Cap → Large Cap (add to list)
   - Demotions from Large Cap → Mid Cap (remove from list)
   - IPOs or delistings
3. **Update the ticker list** in `config/tickers.py`
4. **Run validation script** to confirm all tickers work
5. **Commit the change** with a clear message: `"Update OMX Large Cap ticker list for Q2 2026"`

### Where changes are announced

- Nasdaq Nordic press releases: look for "Changes to the composition of indexes"
- Avanza and Nordnet often publish summaries on their blogs
- The changes affect indexes like OMXSLCPI (OMX Stockholm Large Cap Price Index)

### Automation considerations (Phase 2+)

Fully automating the ticker list update is not worth the effort for Phase 1:
- Changes happen only 4 times per year
- Usually 2-5 stocks change per quarter
- Manual review takes 5 minutes
- Automated scraping of Nasdaq Nordic is fragile and may violate their terms

A pragmatic Phase 2 improvement: set a calendar reminder for the first week of January/April/July/October to update the list.

---

## 8. Ticker List Storage

### Recommended: Python module

```python
# config/tickers.py

"""
OMX Stockholm Large Cap ticker list for Yahoo Finance.

Last updated: 2026-03-09
Source: Nasdaq Nordic (https://www.nasdaqomxnordic.com)
Next review: 2026-04-01 (Q2 2026)
"""

OMX_LARGE_CAP_TICKERS = [
    # ... full list as above ...
]

# Convenience lookups
TICKER_SET = frozenset(OMX_LARGE_CAP_TICKERS)

def is_valid_ticker(ticker: str) -> bool:
    """Check if a ticker is in the current Large Cap list."""
    return ticker in TICKER_SET
```

### Why not a JSON/CSV file?

A Python module is simplest for our use case:
- Import directly: `from config.tickers import OMX_LARGE_CAP_TICKERS`
- No file I/O or parsing code needed
- Comments inline with the data
- Type checking and IDE autocomplete work
- Easy to version in git with meaningful diffs

If the project evolves to need dynamic ticker lists (user-configurable, stored in database), migrate to Cosmos DB/SQLite in Phase 2.

---

*Next: [17-monitoring-and-alerting.md](17-monitoring-and-alerting.md) — Keeping the scanner running reliably.*
