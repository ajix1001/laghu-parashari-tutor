"""
Pre-calculated Antardasha tables for all 81 major-lord / sub-lord combinations.

Formula (Laghu Parashari):
    Antardasha_years(A, B) = (dasha_years[A] * dasha_years[B]) / 120

Values are stored in days for exact date arithmetic.
"""

from data.constants import Planet, DASHA_YEARS, TOTAL_DASHA_YEARS, VIMSHOTTARI_SEQUENCE, DAYS_PER_YEAR

# ─────────────────────────────────────────────────────────────────────────────
# Antardasha duration in days for every (major_lord, sub_lord) pair
# ─────────────────────────────────────────────────────────────────────────────

def _compute_antardasha_days(major: Planet, sub: Planet) -> float:
    """Return Antardasha duration in days.
    Formula: (A_years * B_years / 120) * 365.25
    """
    years = (DASHA_YEARS[major] * DASHA_YEARS[sub]) / TOTAL_DASHA_YEARS
    return years * DAYS_PER_YEAR


def _compute_pratyantardasha_days(major: Planet, sub: Planet, sub2: Planet) -> float:
    """Return Pratyantardasha duration in days.
    Formula: (A_years * B_years * C_years / 120^2) * 365.25
    """
    years = (DASHA_YEARS[major] * DASHA_YEARS[sub] * DASHA_YEARS[sub2]) / (TOTAL_DASHA_YEARS ** 2)
    return years * DAYS_PER_YEAR


# Pre-computed Antardasha table  {major: {sub: days}}
ANTARDASHA_TABLE: dict[Planet, dict[Planet, float]] = {}

for _major in VIMSHOTTARI_SEQUENCE:
    ANTARDASHA_TABLE[_major] = {}
    for _sub in VIMSHOTTARI_SEQUENCE:
        ANTARDASHA_TABLE[_major][_sub] = _compute_antardasha_days(_major, _sub)


# Pre-computed Pratyantardasha table  {major: {sub: {sub2: days}}}
PRATYANTARDASHA_TABLE: dict[Planet, dict[Planet, dict[Planet, float]]] = {}

for _major in VIMSHOTTARI_SEQUENCE:
    PRATYANTARDASHA_TABLE[_major] = {}
    for _sub in VIMSHOTTARI_SEQUENCE:
        PRATYANTARDASHA_TABLE[_major][_sub] = {}
        for _sub2 in VIMSHOTTARI_SEQUENCE:
            PRATYANTARDASHA_TABLE[_major][_sub][_sub2] = _compute_pratyantardasha_days(
                _major, _sub, _sub2
            )


# ─────────────────────────────────────────────────────────────────────────────
# Human-readable summary (years, months, days) helper
# ─────────────────────────────────────────────────────────────────────────────

def days_to_ymd(total_days: float) -> dict:
    """Convert a float number of days to {years, months, days}."""
    years = int(total_days // 365.25)
    remainder = total_days - years * 365.25
    months = int(remainder // 30.4375)
    days = int(remainder - months * 30.4375)
    return {"years": years, "months": months, "days": days}
