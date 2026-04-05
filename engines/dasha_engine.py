"""
Vimshottari Dasha Calculator Engine — Laghu Parashari

Implements the full 120-year cycle including:
  • Birth balance (Bhukta / Bhogya) from Moon's Nakshatra
  • Full Mahadasha timeline from birth date
  • Antardasha (sub-periods) for any given Mahadasha
  • Pratyantardasha (sub-sub-periods) for any given Antardasha

All formulas follow Laghu Parashari (S.R. Jha).
"""

from __future__ import annotations

import math
from datetime import date, timedelta

from data.constants import (
    Planet,
    VIMSHOTTARI_SEQUENCE,
    DASHA_YEARS,
    TOTAL_DASHA_YEARS,
    DAYS_PER_YEAR,
    NAKSHATRA_SPAN_DEGREES,
    NAKSHATRA_LORD,
    NAKSHATRAS,
)
from data.dasha_tables import (
    ANTARDASHA_TABLE,
    PRATYANTARDASHA_TABLE,
    days_to_ymd,
)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _nakshatra_index(moon_degrees: float) -> int:
    """Return 0-based nakshatra index (0 = Ashwini) from Moon's sidereal longitude."""
    moon_degrees = moon_degrees % 360.0
    return int(moon_degrees / NAKSHATRA_SPAN_DEGREES)


def _elapsed_fraction(moon_degrees: float) -> float:
    """Fraction of the current Nakshatra already traversed by the Moon (0-1)."""
    moon_degrees = moon_degrees % 360.0
    nak_index = _nakshatra_index(moon_degrees)
    nak_start = nak_index * NAKSHATRA_SPAN_DEGREES
    elapsed = moon_degrees - nak_start
    return elapsed / NAKSHATRA_SPAN_DEGREES


def _dasha_sequence_from(start_planet: Planet) -> list[Planet]:
    """Return the 9-planet Vimshottari sequence beginning at start_planet."""
    idx = VIMSHOTTARI_SEQUENCE.index(start_planet)
    return VIMSHOTTARI_SEQUENCE[idx:] + VIMSHOTTARI_SEQUENCE[:idx]


# ─────────────────────────────────────────────────────────────────────────────
# Birth balance (Bhukta / Bhogya)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_birth_balance(moon_degrees: float) -> dict:
    """
    Calculate the Dasha balance at birth from Moon's sidereal longitude.

    Returns
    -------
    {
        "nakshatra_index": int,
        "nakshatra_name":  str,
        "nakshatra_lord":  Planet,
        "fraction_elapsed":  float,   # Bhukta — portion of Nakshatra consumed
        "fraction_remaining": float,  # Bhogya — portion remaining
        "balance_years":   float,     # Bhogya dasha years remaining at birth
        "balance_days":    float,
        "balance_ymd":     dict,      # {years, months, days}
    }
    """
    moon_degrees = moon_degrees % 360.0
    nak_idx      = _nakshatra_index(moon_degrees)
    nak_lord     = NAKSHATRA_LORD[nak_idx]
    nak_name     = NAKSHATRAS[nak_idx]["name"]

    fraction_elapsed   = _elapsed_fraction(moon_degrees)
    fraction_remaining = 1.0 - fraction_elapsed

    balance_years = fraction_remaining * DASHA_YEARS[nak_lord]
    balance_days  = balance_years * DAYS_PER_YEAR

    return {
        "nakshatra_index":    nak_idx,
        "nakshatra_name":     nak_name,
        "nakshatra_lord":     nak_lord,
        "fraction_elapsed":   round(fraction_elapsed, 6),
        "fraction_remaining": round(fraction_remaining, 6),
        "balance_years":      round(balance_years, 6),
        "balance_days":       round(balance_days, 4),
        "balance_ymd":        days_to_ymd(balance_days),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Full Mahadasha timeline
# ─────────────────────────────────────────────────────────────────────────────

def calculate_mahadasha_timeline(
    birth_date: date,
    moon_degrees: float,
) -> list[dict]:
    """
    Return the complete Vimshottari Mahadasha timeline from birth.

    Each entry:
    {
        "lord":       Planet,
        "years":      int,      # canonical dasha years
        "start_date": date,
        "end_date":   date,
    }
    """
    balance = calculate_birth_balance(moon_degrees)
    nak_lord = balance["nakshatra_lord"]

    sequence = _dasha_sequence_from(nak_lord)
    timeline = []
    current_date = birth_date

    # First dasha — only the remaining balance
    first_end = current_date + timedelta(days=balance["balance_days"])
    timeline.append({
        "lord":       sequence[0],
        "years":      DASHA_YEARS[sequence[0]],
        "start_date": current_date,
        "end_date":   first_end,
        "is_partial": True,
        "balance_ymd": balance["balance_ymd"],
    })
    current_date = first_end

    # Subsequent full dashas (cycle repeats after 120 years)
    for planet in sequence[1:]:
        duration_days = DASHA_YEARS[planet] * DAYS_PER_YEAR
        end_date = current_date + timedelta(days=duration_days)
        timeline.append({
            "lord":       planet,
            "years":      DASHA_YEARS[planet],
            "start_date": current_date,
            "end_date":   end_date,
            "is_partial": False,
        })
        current_date = end_date

    return timeline


# ─────────────────────────────────────────────────────────────────────────────
# Antardasha (sub-period) calculator
# ─────────────────────────────────────────────────────────────────────────────

def calculate_antardasha(
    major_lord: Planet,
    mahadasha_start: date,
    partial_balance_days: float | None = None,
) -> list[dict]:
    """
    Return all 9 Antardashas for a given Mahadasha.

    The sub-period sequence always starts with the major lord itself.

    Formula: Antardasha(A, B) = (A_years * B_years) / 120  [years]

    Parameters
    ----------
    major_lord           : The Mahadasha lord.
    mahadasha_start      : Start date of the Mahadasha.
    partial_balance_days : If this is the first (partial) dasha at birth,
                           pass the birth balance in days. The antardashas
                           will be calculated proportionally.
    """
    sub_sequence = _dasha_sequence_from(major_lord)
    result = []
    current = mahadasha_start

    for sub_lord in sub_sequence:
        full_days = ANTARDASHA_TABLE[major_lord][sub_lord]

        if partial_balance_days is not None:
            # Scale: total antardasha days sum = dasha_years * 365.25
            total_full_days = DASHA_YEARS[major_lord] * DAYS_PER_YEAR
            ratio = partial_balance_days / total_full_days
            duration_days = full_days * ratio
        else:
            duration_days = full_days

        end_date = current + timedelta(days=duration_days)
        result.append({
            "major_lord":     major_lord,
            "sub_lord":       sub_lord,
            "duration_days":  round(duration_days, 2),
            "duration_ymd":   days_to_ymd(duration_days),
            "start_date":     current,
            "end_date":       end_date,
        })
        current = end_date

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Pratyantardasha (sub-sub-period) calculator
# ─────────────────────────────────────────────────────────────────────────────

def calculate_pratyantardasha(
    major_lord: Planet,
    sub_lord: Planet,
    antardasha_start: date,
    antardasha_days: float,
) -> list[dict]:
    """
    Return all 9 Pratyantardashas for a given Antardasha.

    Formula: Pratyantardasha(A, B, C) = (A_years * B_years * C_years) / 120^2

    Parameters
    ----------
    major_lord        : Mahadasha lord.
    sub_lord          : Antardasha lord.
    antardasha_start  : Start date of this Antardasha.
    antardasha_days   : Actual duration of this Antardasha in days.
    """
    sub2_sequence = _dasha_sequence_from(sub_lord)
    result = []
    current = antardasha_start

    # Total theoretical pratyantardasha days for this (major, sub) pair
    total_theory = ANTARDASHA_TABLE[major_lord][sub_lord]

    for sub2_lord in sub2_sequence:
        full_days = PRATYANTARDASHA_TABLE[major_lord][sub_lord][sub2_lord]
        # Scale to actual antardasha length (handles partial birth dasha)
        if total_theory > 0:
            duration_days = full_days * (antardasha_days / total_theory)
        else:
            duration_days = full_days

        end_date = current + timedelta(days=duration_days)
        result.append({
            "major_lord":    major_lord,
            "sub_lord":      sub_lord,
            "sub2_lord":     sub2_lord,
            "duration_days": round(duration_days, 4),
            "duration_ymd":  days_to_ymd(duration_days),
            "start_date":    current,
            "end_date":      end_date,
        })
        current = end_date

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: find current Dasha at a given date
# ─────────────────────────────────────────────────────────────────────────────

def get_current_dasha(
    birth_date: date,
    moon_degrees: float,
    query_date: date | None = None,
) -> dict:
    """
    Return the active Mahadasha, Antardasha, and Pratyantardasha on query_date.

    If query_date is None, today's date is used.
    """
    query_date = query_date or date.today()
    timeline = calculate_mahadasha_timeline(birth_date, moon_degrees)

    active_maha = None
    for entry in timeline:
        if entry["start_date"] <= query_date < entry["end_date"]:
            active_maha = entry
            break

    if active_maha is None:
        return {"error": "Query date is outside the 120-year cycle from birth."}

    # Antardasha
    balance_days = (
        active_maha["balance_ymd"] and
        active_maha.get("is_partial") and
        active_maha["balance_days"]
        if active_maha.get("is_partial") else None
    )
    balance_days = active_maha.get("balance_ymd") and active_maha.get("is_partial") and (
        active_maha["balance_days"] if "balance_days" in active_maha
        else None
    )
    # Recalculate cleanly
    bday_balance = calculate_birth_balance(moon_degrees)
    pb_days = bday_balance["balance_days"] if active_maha.get("is_partial") else None

    antardashas = calculate_antardasha(
        active_maha["lord"], active_maha["start_date"], pb_days
    )

    active_antar = None
    for ad in antardashas:
        if ad["start_date"] <= query_date < ad["end_date"]:
            active_antar = ad
            break

    if active_antar is None:
        return {
            "mahadasha": active_maha,
            "antardasha": None,
            "pratyantardasha": None,
        }

    # Pratyantardasha
    pratyantardashas = calculate_pratyantardasha(
        active_antar["major_lord"],
        active_antar["sub_lord"],
        active_antar["start_date"],
        active_antar["duration_days"],
    )

    active_pratyantar = None
    for pad in pratyantardashas:
        if pad["start_date"] <= query_date < pad["end_date"]:
            active_pratyantar = pad
            break

    return {
        "mahadasha":      active_maha,
        "antardasha":     active_antar,
        "pratyantardasha": active_pratyantar,
    }
