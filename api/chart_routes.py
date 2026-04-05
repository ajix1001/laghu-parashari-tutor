"""
Chart API routes — natal chart persistence, ephemeris, Kundali SVG,
Dasha interpretations, and lesson progress tracking.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from models.db_models import NatalChart, LessonProgress
from data.constants import Sign, Planet
from data.ascendant_profiles import ASCENDANT_PROFILES

from engines.dasha_engine import (
    calculate_birth_balance,
    calculate_mahadasha_timeline,
    get_current_dasha,
    calculate_antardasha,
)
from engines.lordship_engine import evaluate_all_planets
from engines.yoga_engine import full_yoga_analysis, ChartInput
from engines.interpretation_engine import interpret_dasha, interpret_lagna_profile
from engines.kundali_engine import generate_kundali_svg

# pyswisseph is optional — graceful degradation if not installed
try:
    from engines.ephemeris_engine import calculate_chart, planet_positions_for_yoga
    EPHEMERIS_AVAILABLE = True
except ImportError:
    EPHEMERIS_AVAILABLE = False


chart_router = APIRouter(prefix="/charts", tags=["Charts & Ephemeris"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (chart-specific)
# ─────────────────────────────────────────────────────────────────────────────

class ChartCreateRequest(BaseModel):
    name:         str   = Field(..., min_length=1, max_length=120)
    birth_date:   date
    birth_hour:   int   = Field(default=0, ge=0, le=23)
    birth_minute: int   = Field(default=0, ge=0, le=59)
    birth_place:  str   = Field(default="")
    latitude:     float = Field(..., ge=-90.0,  le=90.0)
    longitude:    float = Field(..., ge=-180.0, le=180.0)
    tz_offset:    float = Field(..., ge=-14.0,  le=14.0,
                                description="Hours east of UTC (e.g. 5.5 for IST)")
    # Optional manual override (if user knows their sidereal positions)
    lagna_sign:   Optional[str]   = None
    moon_degrees: Optional[float] = None


class ChartUpdateRequest(BaseModel):
    name:         Optional[str]   = None
    birth_place:  Optional[str]   = None
    lagna_sign:   Optional[str]   = None
    moon_degrees: Optional[float] = None


class EphemerisRequest(BaseModel):
    birth_date:   date
    birth_hour:   int   = Field(default=12, ge=0, le=23)
    birth_minute: int   = Field(default=0,  ge=0, le=59)
    latitude:     float = Field(..., ge=-90.0,  le=90.0)
    longitude:    float = Field(..., ge=-180.0, le=180.0)
    tz_offset:    float = Field(..., ge=-14.0,  le=14.0)


class DashaInterpretRequest(BaseModel):
    lagna:      Sign
    maha_lord:  Planet
    antar_lord: Optional[Planet] = None


class LessonProgressUpsertRequest(BaseModel):
    lesson_index: int   = Field(..., ge=0, le=4)
    completed:    bool  = False
    score:        int   = Field(default=0, ge=0)
    max_score:    int   = Field(default=0, ge=0)
    time_spent_s: int   = Field(default=0, ge=0)
    notes:        str   = Field(default="")


class KundaliRequest(BaseModel):
    lagna_sign:      str
    house_occupants: dict[int, list[str]]
    retrograde:      list[str] = Field(default_factory=list)
    size:            int       = Field(default=360, ge=200, le=800)


# ─────────────────────────────────────────────────────────────────────────────
# Ephemeris endpoint (no DB)
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.post("/ephemeris")
def compute_ephemeris(body: EphemerisRequest):
    """
    Calculate sidereal planetary positions using Swiss Ephemeris (Lahiri ayanamsa).
    Returns full chart data including Lagna, all 9 planets, and house placements.
    """
    if not EPHEMERIS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Ephemeris not available. Install pyswisseph: pip install pyswisseph",
        )
    chart = calculate_chart(
        body.birth_date.year, body.birth_date.month, body.birth_date.day,
        body.birth_hour, body.birth_minute,
        body.latitude, body.longitude, body.tz_offset,
    )
    # Convert Sign enums to strings for JSON
    chart["lagna_sign"] = chart["lagna_sign"].value
    chart["planets"] = {
        name: {**info, "sign": info["sign"].value}
        for name, info in chart["planets"].items()
    }
    return chart


# ─────────────────────────────────────────────────────────────────────────────
# Kundali SVG endpoint (no DB)
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.post("/kundali-svg")
def kundali_svg(body: KundaliRequest):
    """
    Generate a North Indian Kundali chart as an SVG string.
    Returns Content-Type: image/svg+xml.
    """
    svg = generate_kundali_svg(
        lagna_sign=body.lagna_sign,
        house_occupants=body.house_occupants,
        size=body.size,
        retrograde=set(body.retrograde),
    )
    return Response(content=svg, media_type="image/svg+xml")


# ─────────────────────────────────────────────────────────────────────────────
# Dasha interpretation endpoint (no DB)
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.post("/interpret-dasha")
def interpret_dasha_endpoint(body: DashaInterpretRequest):
    """
    Generate a narrative Dasha interpretation for a Maha/Antardasha
    combination for the given Lagna.
    """
    result = interpret_dasha(
        body.lagna,
        body.maha_lord.value,
        body.antar_lord.value if body.antar_lord else None,
    )
    return result


@chart_router.post("/interpret-lagna")
def interpret_lagna_endpoint(lagna: Sign):
    """
    Generate a narrative summary of the Lagna's planetary landscape.
    """
    profile = ASCENDANT_PROFILES.get(lagna)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No profile for lagna: {lagna}")
    text = interpret_lagna_profile(lagna, profile)
    return {"lagna": lagna, "narrative": text}


# ─────────────────────────────────────────────────────────────────────────────
# Full chart analysis (ephemeris + all engines, no DB save)
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.post("/full-analysis")
def full_chart_analysis(body: EphemerisRequest):
    """
    One-shot endpoint: runs ephemeris, all Dasha engines, lordship, yoga/maraka,
    interpretation, and returns the complete chart analysis.
    """
    if not EPHEMERIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="pyswisseph not installed.")

    eph = calculate_chart(
        body.birth_date.year, body.birth_date.month, body.birth_date.day,
        body.birth_hour, body.birth_minute,
        body.latitude, body.longitude, body.tz_offset,
    )

    lagna      = eph["lagna_sign"]
    moon_deg   = eph["planets"]["Moon"]["longitude"]
    birth_date = body.birth_date
    positions  = planet_positions_for_yoga(eph)

    # Dasha
    balance  = calculate_birth_balance(moon_deg)
    timeline = calculate_mahadasha_timeline(birth_date, moon_deg)
    current  = get_current_dasha(birth_date, moon_deg)

    # Antardasha for active Mahadasha
    antar_data = None
    if current.get("mahadasha"):
        pb = balance["balance_days"] if current["mahadasha"].get("is_partial") else None
        antar_data = calculate_antardasha(
            Planet(current["mahadasha"]["lord"]),
            current["mahadasha"]["start_date"],
            pb,
        )

    # Lordship
    planet_evals = evaluate_all_planets(lagna)

    # Yoga / Maraka
    chart_input = ChartInput(
        lagna=lagna,
        planet_positions={p["planet"]: p["house"] for p in positions},
    )
    yoga_result = full_yoga_analysis(chart_input)

    # Interpretation
    maha_lord  = current["mahadasha"]["lord"]  if current.get("mahadasha")  else None
    antar_lord = current["antardasha"]["sub_lord"] if current.get("antardasha") else None
    interpretation = interpret_dasha(lagna, maha_lord, antar_lord) if maha_lord else None

    # Lagna narrative
    asc_profile = ASCENDANT_PROFILES.get(lagna, {})
    lagna_narrative = interpret_lagna_profile(lagna, asc_profile)

    # Kundali SVG
    retro = {n for n, info in eph["planets"].items() if info.get("is_retrograde")}
    svg = generate_kundali_svg(
        lagna_sign=lagna.value,
        house_occupants={int(h): v for h, v in eph["house_occupants"].items()},
        retrograde=retro,
    )

    return {
        "ephemeris": {
            "lagna_sign":    lagna.value,
            "lagna_degrees": eph["lagna_degrees"],
            "ayanamsa":      eph["ayanamsa"],
            "planets": {
                name: {**info, "sign": info["sign"].value}
                for name, info in eph["planets"].items()
            },
            "house_occupants": {int(h): v for h, v in eph["house_occupants"].items()},
        },
        "dasha": {
            "birth_balance":  balance,
            "timeline":       [
                {**r, "lord": r["lord"].value,
                 "start_date": r["start_date"].isoformat(),
                 "end_date":   r["end_date"].isoformat()}
                for r in timeline
            ],
            "current":        current,
            "antardasha":     antar_data,
        },
        "lordship":      {p.value: v for p, v in planet_evals.items()},
        "yoga":          yoga_result,
        "interpretation":interpretation,
        "lagna_narrative": lagna_narrative,
        "kundali_svg":   svg,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chart CRUD
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.post("/", status_code=201)
def create_chart(body: ChartCreateRequest, db: Session = Depends(get_db)):
    """Save a natal chart to the database. Runs the ephemeris if pyswisseph is available."""
    planet_data     = None
    house_occupants = None
    lagna_sign      = body.lagna_sign
    moon_degrees    = body.moon_degrees
    ayanamsa        = None
    lagna_degrees   = None

    if EPHEMERIS_AVAILABLE:
        eph = calculate_chart(
            body.birth_date.year, body.birth_date.month, body.birth_date.day,
            body.birth_hour, body.birth_minute,
            body.latitude, body.longitude, body.tz_offset,
        )
        lagna_sign    = eph["lagna_sign"].value
        moon_degrees  = eph["planets"]["Moon"]["longitude"]
        ayanamsa      = eph["ayanamsa"]
        lagna_degrees = eph["lagna_degrees"]
        planet_data   = {
            name: {**info, "sign": info["sign"].value}
            for name, info in eph["planets"].items()
        }
        house_occupants = {str(h): v for h, v in eph["house_occupants"].items()}

    chart = NatalChart(
        name=body.name,
        birth_date=body.birth_date,
        birth_hour=body.birth_hour,
        birth_minute=body.birth_minute,
        birth_place=body.birth_place,
        latitude=body.latitude,
        longitude=body.longitude,
        tz_offset=body.tz_offset,
        lagna_sign=lagna_sign,
        lagna_degrees=lagna_degrees,
        moon_degrees=moon_degrees,
        ayanamsa=ayanamsa,
        planet_data=planet_data,
        house_occupants=house_occupants,
    )
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart.to_dict()


@chart_router.get("/")
def list_charts(db: Session = Depends(get_db)):
    """List all saved natal charts."""
    return [c.to_dict() for c in db.query(NatalChart).order_by(NatalChart.created_at.desc()).all()]


@chart_router.get("/{chart_id}")
def get_chart(chart_id: int, db: Session = Depends(get_db)):
    chart = db.query(NatalChart).filter(NatalChart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")
    return chart.to_dict()


@chart_router.delete("/{chart_id}", status_code=204)
def delete_chart(chart_id: int, db: Session = Depends(get_db)):
    chart = db.query(NatalChart).filter(NatalChart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")
    db.delete(chart)
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Lesson progress CRUD
# ─────────────────────────────────────────────────────────────────────────────

@chart_router.put("/{chart_id}/progress/{lesson_index}")
def upsert_progress(
    chart_id: int,
    lesson_index: int,
    body: LessonProgressUpsertRequest,
    db: Session = Depends(get_db),
):
    """Save or update lesson progress for a chart."""
    chart = db.query(NatalChart).filter(NatalChart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")

    prog = db.query(LessonProgress).filter(
        LessonProgress.chart_id == chart_id,
        LessonProgress.lesson_index == lesson_index,
    ).first()

    if not prog:
        prog = LessonProgress(chart_id=chart_id, lesson_index=lesson_index)
        db.add(prog)

    prog.completed    = body.completed
    prog.score        = body.score
    prog.max_score    = body.max_score
    prog.time_spent_s = body.time_spent_s
    prog.notes        = body.notes
    if body.completed and not prog.completed_at:
        prog.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(prog)
    return prog.to_dict()


@chart_router.get("/{chart_id}/progress")
def get_progress(chart_id: int, db: Session = Depends(get_db)):
    """Return all lesson progress records for a chart."""
    chart = db.query(NatalChart).filter(NatalChart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")
    records = db.query(LessonProgress).filter(
        LessonProgress.chart_id == chart_id
    ).order_by(LessonProgress.lesson_index).all()
    return [r.to_dict() for r in records]
