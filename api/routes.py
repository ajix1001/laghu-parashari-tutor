"""
FastAPI route definitions for the Laghu Parashari Astrology Backend.

Routers:
  /dasha      — Vimshottari Dasha calculations
  /lordship   — House lordship rule engine
  /yoga       — Raja Yoga & Maraka identification
  /ascendants — Ascendant-specific planet profiles
"""

from __future__ import annotations

from datetime import date
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from data.constants import Planet, Sign, SIGNS_LIST, SIGN_RULERS, NAKSHATRAS, DASHA_YEARS
from data.ascendant_profiles import ASCENDANT_PROFILES
from data.dasha_tables import ANTARDASHA_TABLE, PRATYANTARDASHA_TABLE, days_to_ymd

from engines.dasha_engine import (
    calculate_birth_balance,
    calculate_mahadasha_timeline,
    calculate_antardasha,
    calculate_pratyantardasha,
    get_current_dasha,
)
from engines.lordship_engine import (
    evaluate_planet,
    evaluate_all_planets,
    get_house_signs,
    get_house_lords,
    FunctionalNature,
)
from engines.yoga_engine import (
    full_yoga_analysis,
    identify_raja_yogas,
    identify_marakas,
    ChartInput,
)

from models.schemas import (
    BirthInput,
    BirthBalanceResponse,
    MahadashaTimelineResponse,
    MahadashaEntry,
    AntardashaRequest,
    AntardashaResponse,
    AntardashaEntry,
    PratyantardashaRequest,
    PratyantardashaResponse,
    PratyantardashaEntry,
    CurrentDashaRequest,
    CurrentDashaResponse,
    PlanetEvaluationRequest,
    PlanetEvaluationResponse,
    LagnaProfileRequest,
    LagnaProfileResponse,
    LagnaHouseEntry,
    YogaAnalysisRequest,
    YogaAnalysisResponse,
    RajaYogaEntry,
    MarakaEntry,
    PlanetSummaryEntry,
    AscendantDatabaseEntry,
    YMD,
)


# ─────────────────────────────────────────────────────────────────────────────
# Dasha router
# ─────────────────────────────────────────────────────────────────────────────

dasha_router = APIRouter(prefix="/dasha", tags=["Vimshottari Dasha"])


@dasha_router.post("/birth-balance", response_model=BirthBalanceResponse)
def birth_balance(body: BirthInput):
    """
    Calculate the Dasha balance at birth (Bhukta / Bhogya) from the
    Moon's sidereal longitude and return the nakshatra, its lord, and
    the exact remaining dasha period at birth.
    """
    result = calculate_birth_balance(body.moon_degrees)
    result["balance_ymd"] = YMD(**result["balance_ymd"])
    return BirthBalanceResponse(**result)


@dasha_router.post("/mahadasha-timeline", response_model=MahadashaTimelineResponse)
def mahadasha_timeline(body: BirthInput):
    """
    Return the complete 120-year Vimshottari Mahadasha timeline from
    the birth date, including the partial first dasha and 8 full cycles.
    """
    raw = calculate_mahadasha_timeline(body.birth_date, body.moon_degrees)
    entries = []
    for r in raw:
        entries.append(MahadashaEntry(
            lord=r["lord"],
            years=r["years"],
            start_date=r["start_date"],
            end_date=r["end_date"],
            is_partial=r.get("is_partial", False),
            balance_ymd=YMD(**r["balance_ymd"]) if r.get("balance_ymd") else None,
        ))
    return MahadashaTimelineResponse(
        birth_date=body.birth_date,
        moon_degrees=body.moon_degrees,
        timeline=entries,
    )


@dasha_router.post("/antardasha", response_model=AntardashaResponse)
def antardasha(body: AntardashaRequest):
    """
    Calculate all 9 Antardashas (sub-periods) for a given Mahadasha lord.

    Formula: Antardasha(A, B) = (A_years × B_years) / 120
    """
    raw = calculate_antardasha(
        body.major_lord,
        body.mahadasha_start,
        body.partial_balance_days,
    )
    entries = [
        AntardashaEntry(
            major_lord=r["major_lord"],
            sub_lord=r["sub_lord"],
            duration_days=r["duration_days"],
            duration_ymd=YMD(**r["duration_ymd"]),
            start_date=r["start_date"],
            end_date=r["end_date"],
        )
        for r in raw
    ]
    return AntardashaResponse(major_lord=body.major_lord, antardashas=entries)


@dasha_router.post("/pratyantardasha", response_model=PratyantardashaResponse)
def pratyantardasha(body: PratyantardashaRequest):
    """
    Calculate all 9 Pratyantardashas (sub-sub-periods) for a given Antardasha.

    Formula: Pratyantardasha(A, B, C) = (A_years × B_years × C_years) / 120²
    """
    raw = calculate_pratyantardasha(
        body.major_lord,
        body.sub_lord,
        body.antardasha_start,
        body.antardasha_days,
    )
    entries = [
        PratyantardashaEntry(
            major_lord=r["major_lord"],
            sub_lord=r["sub_lord"],
            sub2_lord=r["sub2_lord"],
            duration_days=r["duration_days"],
            duration_ymd=YMD(**r["duration_ymd"]),
            start_date=r["start_date"],
            end_date=r["end_date"],
        )
        for r in raw
    ]
    return PratyantardashaResponse(
        major_lord=body.major_lord,
        sub_lord=body.sub_lord,
        pratyantardashas=entries,
    )


@dasha_router.post("/current", response_model=CurrentDashaResponse)
def current_dasha(body: CurrentDashaRequest):
    """
    Return the active Mahadasha, Antardasha, and Pratyantardasha on a
    given date (defaults to today).
    """
    result = get_current_dasha(body.birth_date, body.moon_degrees, body.query_date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    def _to_maha(r: dict | None) -> MahadashaEntry | None:
        if r is None:
            return None
        return MahadashaEntry(
            lord=r["lord"], years=r["years"],
            start_date=r["start_date"], end_date=r["end_date"],
            is_partial=r.get("is_partial", False),
            balance_ymd=YMD(**r["balance_ymd"]) if r.get("balance_ymd") else None,
        )

    def _to_antar(r: dict | None) -> AntardashaEntry | None:
        if r is None:
            return None
        return AntardashaEntry(
            major_lord=r["major_lord"], sub_lord=r["sub_lord"],
            duration_days=r["duration_days"],
            duration_ymd=YMD(**r["duration_ymd"]),
            start_date=r["start_date"], end_date=r["end_date"],
        )

    def _to_pratyantar(r: dict | None) -> PratyantardashaEntry | None:
        if r is None:
            return None
        return PratyantardashaEntry(
            major_lord=r["major_lord"], sub_lord=r["sub_lord"],
            sub2_lord=r["sub2_lord"],
            duration_days=r["duration_days"],
            duration_ymd=YMD(**r["duration_ymd"]),
            start_date=r["start_date"], end_date=r["end_date"],
        )

    return CurrentDashaResponse(
        mahadasha=_to_maha(result.get("mahadasha")),
        antardasha=_to_antar(result.get("antardasha")),
        pratyantardasha=_to_pratyantar(result.get("pratyantardasha")),
    )


@dasha_router.get("/antardasha-table")
def antardasha_table_endpoint():
    """
    Return the pre-calculated Antardasha duration table for all
    81 major-lord / sub-lord combinations (in days and Y/M/D).
    """
    table = {}
    for major, subs in ANTARDASHA_TABLE.items():
        table[major.value] = {}
        for sub, days in subs.items():
            table[major.value][sub.value] = {
                "days":  round(days, 2),
                "ymd":   days_to_ymd(days),
            }
    return {"antardasha_table": table}


@dasha_router.get("/nakshatra-reference")
def nakshatra_reference():
    """Return the full 27-nakshatra reference table with Dasha lords."""
    return {
        "nakshatras": [
            {
                "id":        n["id"],
                "name":      n["name"],
                "lord":      n["lord"].value,
                "start_deg": round(n["start_deg"], 3),
                "end_deg":   round(n["start_deg"] + 13.333, 3),
                "dasha_years": DASHA_YEARS[n["lord"]],
            }
            for n in NAKSHATRAS
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lordship router
# ─────────────────────────────────────────────────────────────────────────────

lordship_router = APIRouter(prefix="/lordship", tags=["House Lordship"])


@lordship_router.post("/evaluate-planet", response_model=PlanetEvaluationResponse)
def evaluate_planet_endpoint(body: PlanetEvaluationRequest):
    """
    Evaluate a single planet's functional nature for the given ascendant
    by applying all four Laghu Parashari lordship rules.
    """
    if body.planet in (Planet.RAHU, Planet.KETU):
        return PlanetEvaluationResponse(
            planet=body.planet,
            lagna=body.lagna,
            owned_houses=[],
            is_lagna_lord=False,
            is_yoga_karaka=False,
            is_maraka=False,
            is_8th_lord=False,
            trikona_houses=[],
            kendra_houses=[],
            trishadaya_houses=[],
            rules_applied=["Rahu/Ketu are shadow planets; no sign lordship in classical Jyotish."],
            functional_nature=FunctionalNature.NEUTRAL,
            strength_score=0,
            interpretation=(
                f"{body.planet.value} is a shadow planet. "
                "Its results depend on placement and dispositor, not sign lordship."
            ),
        )
    result = evaluate_planet(body.lagna, body.planet)
    result["lagna"] = body.lagna
    return PlanetEvaluationResponse(**result)


@lordship_router.post("/lagna-profile", response_model=LagnaProfileResponse)
def lagna_profile(body: LagnaProfileRequest):
    """
    Return the complete house-lord map and functional planet evaluation
    for all 9 planets for the given ascendant.
    """
    lagna      = body.lagna
    house_sigs = get_house_signs(lagna)
    house_lrds = get_house_lords(lagna)
    planet_evals = evaluate_all_planets(lagna)

    houses = [
        LagnaHouseEntry(house=h, sign=s, lord=house_lrds[h])
        for h, s in house_sigs.items()
    ]

    evaluations = []
    for p, ev in planet_evals.items():
        evaluations.append(PlanetEvaluationResponse(
            planet=p,
            lagna=lagna,
            owned_houses=ev["owned_houses"],
            is_lagna_lord=ev["is_lagna_lord"],
            is_yoga_karaka=ev["is_yoga_karaka"],
            is_maraka=ev["is_maraka"],
            is_8th_lord=ev["is_8th_lord"],
            trikona_houses=ev["trikona_houses"],
            kendra_houses=ev["kendra_houses"],
            trishadaya_houses=ev["trishadaya_houses"],
            rules_applied=ev["rules_applied"],
            functional_nature=ev["functional_nature"],
            strength_score=ev["strength_score"],
            interpretation=ev["interpretation"],
        ))

    return LagnaProfileResponse(
        lagna=lagna,
        lagna_lord=house_lrds[1],
        houses=houses,
        planet_evaluations=evaluations,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Yoga router
# ─────────────────────────────────────────────────────────────────────────────

yoga_router = APIRouter(prefix="/yoga", tags=["Yoga & Maraka"])


@yoga_router.post("/analyse", response_model=YogaAnalysisResponse)
def yoga_analyse(body: YogaAnalysisRequest):
    """
    Perform full Raja Yoga + Maraka analysis for the given chart.

    Provide `planet_positions` (house 1–12 for each planet) to also detect
    conjunction, mutual-aspect, and exchange Yogas.  If positions are omitted,
    only single-planet Yoga Karaka (lordship-based) yogas are detected.
    """
    positions = {pp.planet: pp.house for pp in body.planet_positions}
    chart = ChartInput(lagna=body.lagna, planet_positions=positions)
    raw   = full_yoga_analysis(chart)

    return YogaAnalysisResponse(
        lagna=raw["lagna"],
        raja_yogas=[RajaYogaEntry(**y) for y in raw["raja_yogas"]],
        marakas=[MarakaEntry(**m) for m in raw["marakas"]],
        planet_summary={
            name: PlanetSummaryEntry(**v)
            for name, v in raw["planet_summary"].items()
        },
    )


@yoga_router.post("/raja-yogas")
def raja_yogas_only(body: YogaAnalysisRequest):
    """Return only Raja Yoga analysis (without full planet summary)."""
    positions = {pp.planet: pp.house for pp in body.planet_positions}
    chart     = ChartInput(lagna=body.lagna, planet_positions=positions)
    yogas     = identify_raja_yogas(chart)
    return {
        "lagna":      body.lagna,
        "raja_yogas": [
            {
                "yoga_type":      y.yoga_type,
                "sambandha_type": y.sambandha_type,
                "kendra_lord":    y.kendra_lord,
                "kendra_house":   y.kendra_house,
                "trikona_lord":   y.trikona_lord,
                "trikona_house":  y.trikona_house,
                "description":    y.description,
            }
            for y in yogas
        ],
    }


@yoga_router.post("/marakas")
def marakas_only(body: YogaAnalysisRequest):
    """Return only Maraka analysis for the given chart."""
    positions = {pp.planet: pp.house for pp in body.planet_positions}
    chart     = ChartInput(lagna=body.lagna, planet_positions=positions)
    marakas   = identify_marakas(chart)
    return {
        "lagna":   body.lagna,
        "marakas": [
            {
                "planet":                 m.planet,
                "maraka_houses":          m.maraka_houses,
                "is_natural_malefic":     m.is_natural_malefic,
                "placed_in_maraka_house": m.placed_in_maraka_house,
                "severity":               m.severity,
                "description":            m.description,
            }
            for m in marakas
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Ascendant database router
# ─────────────────────────────────────────────────────────────────────────────

ascendant_router = APIRouter(prefix="/ascendants", tags=["Ascendant Profiles"])


@ascendant_router.get("/", response_model=list[AscendantDatabaseEntry])
def all_ascendant_profiles():
    """Return the complete ascendant database for all 12 lagnas."""
    result = []
    for sign, profile in ASCENDANT_PROFILES.items():
        result.append(AscendantDatabaseEntry(
            lagna=sign,
            lagna_lord=profile["lagna_lord"],
            auspicious=profile["auspicious"],
            inauspicious=profile["inauspicious"],
            yoga_karaka=profile["yoga_karaka"],
            maraka=profile["maraka"],
            neutral=profile["neutral"],
            notes=profile["notes"],
            house_lords=profile["house_lords"],
        ))
    return result


@ascendant_router.get("/{lagna}", response_model=AscendantDatabaseEntry)
def ascendant_profile(lagna: Sign):
    """Return the profile for a specific ascendant (e.g. Aries, Taurus …)."""
    profile = ASCENDANT_PROFILES.get(lagna)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No profile found for lagna: {lagna}")
    return AscendantDatabaseEntry(
        lagna=lagna,
        lagna_lord=profile["lagna_lord"],
        auspicious=profile["auspicious"],
        inauspicious=profile["inauspicious"],
        yoga_karaka=profile["yoga_karaka"],
        maraka=profile["maraka"],
        neutral=profile["neutral"],
        notes=profile["notes"],
        house_lords=profile["house_lords"],
    )
