"""Nasdaq Stockholm Large Cap ticker universe.

All tickers use Yahoo Finance format: SYMBOL.ST
For dual-class stocks, prefer B-shares (higher liquidity).
"""

# Nasdaq Stockholm Large Cap — ~90 most liquid tickers
# Last updated: 2026-03-29
# Source: Nasdaq Nordic Large Cap list
LARGE_CAP_TICKERS: list[str] = [
    # Industrials
    "ABB.ST",
    "ALFA.ST",
    "ASSA-B.ST",
    "ATCO-A.ST",
    "ATCO-B.ST",
    "SAND.ST",
    "VOLV-B.ST",
    "HEXA-B.ST",
    "EPIROC-A.ST",
    "EPIROC-B.ST",
    "TREL-B.ST",
    "SKF-B.ST",
    "HUFV-A.ST",
    "INDU-A.ST",
    "INDU-C.ST",
    "NIBE-B.ST",
    "SWEC-B.ST",
    "AFRY.ST",
    # Financials
    "SEB-A.ST",
    "SWED-A.ST",
    "SHB-A.ST",
    "NDA-SE.ST",
    "INVE-B.ST",
    "KINV-B.ST",
    "LATO-B.ST",
    "SAGA-B.ST",
    "CRED-A.ST",
    "SAMPO.ST",
    "LIFCO-B.ST",
    # Technology
    "ERIC-B.ST",
    "HM-B.ST",
    "SINCH.ST",
    "SAAB-B.ST",
    "ELUX-B.ST",
    "SSAB-A.ST",
    "SSAB-B.ST",
    "SOBI.ST",
    "GETI-B.ST",
    # Healthcare
    "AZN.ST",
    "ESSITY-B.ST",
    "GETI-B.ST",
    "STO3.ST",
    # Telecom
    "TEL2-B.ST",
    "TELIA.ST",
    # Consumer
    "AXFO.ST",
    "BILL.ST",
    "BOL.ST",
    "CAST.ST",
    "DOM.ST",
    "EQT.ST",
    "FABG.ST",
    "HTRO.ST",
    "HUSQ-B.ST",
    "KIND-SDB.ST",
    "LUND-B.ST",
    "LOOM-B.ST",
    "MTRS.ST",
    "NCC-B.ST",
    "PEAB-B.ST",
    "SCA-B.ST",
    "SKA-B.ST",
    "SWMA.ST",
    "WALL-B.ST",
    "WIHL.ST",
    # Real Estate
    "BALD-B.ST",
    "CAST.ST",
    "FABG.ST",
    "SAGA-D.ST",
    "SBB-B.ST",
    "WALL-B.ST",
    # Energy / Materials
    "LUNE.ST",
    "SSAB-B.ST",
    "BOLS.ST",
    "STOR-B.ST",
    # Gaming
    "EVO.ST",
    "EMBRACE-B.ST",
]


def get_universe() -> list[str]:
    """Return deduplicated ticker universe sorted alphabetically."""
    return sorted(set(LARGE_CAP_TICKERS))
