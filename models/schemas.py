"""
Pydantic v2 request/response schemas for the Laghu Parashari backend API.
"""

from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from data.constants import Planet, Sign
from engines.lordship_engine import FunctionalNature
from engines.yoga_engine import SambandhaType, YogaType


# ─────────────────────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────────────────────

class YMD(BaseModel):
    years:  int
    months: int
    days:   int


# ─────────────────────────────────────────────────────────────────────────────
# Dasha endpoints
# ─────────────────────────────────────────────────────────────────────────────

class BirthInput(BaseModel):
    birth_date:    date  = Field(..., description="Native's birth date (YYYY-MM-DD).")
    moon_degrees:  float = Field(
        ..., ge=0.0, lt=360.0,
        description="Moon's sidereal longitude in degrees (0–360).",
    )

    @field_validator("moon_degrees")
    @classmethod
    def normalise_moon(cls, v: float) -> float:
        return v % 360.0


class BirthBalanceResponse(BaseModel):
    nakshatra_index:    int
    nakshatra_name:     str
    nakshatra_lord:     Planet
    fraction_elapsed:   float
    fraction_remaining: float
    balance_years:      float
    balance_days:       float
    balance_ymd:        YMD


class MahadashaEntry(BaseModel):
    lord:       Planet
    years:      int
    start_date: date
    end_date:   date
    is_partial: bool
    balance_ymd: Optional[YMD] = None


class MahadashaTimelineResponse(BaseModel):
    birth_date:   date
    moon_degrees: float
    timeline:     list[MahadashaEntry]


class AntardashaEntry(BaseModel):
    major_lord:    Planet
    sub_lord:      Planet
    duration_days: float
    duration_ymd:  YMD
    start_date:    date
    end_date:      date


class AntardashaRequest(BaseModel):
    major_lord:       Planet
    mahadasha_start:  date
    partial_balance_days: Optional[float] = Field(
        None,
        description="Pass the birth-balance days only for the first (partial) Mahadasha.",
    )


class AntardashaResponse(BaseModel):
    major_lord:   Planet
    antardashas:  list[AntardashaEntry]


class PratyantardashaEntry(BaseModel):
    major_lord:    Planet
    sub_lord:      Planet
    sub2_lord:     Planet
    duration_days: float
    duration_ymd:  YMD
    start_date:    date
    end_date:      date


class PratyantardashaRequest(BaseModel):
    major_lord:       Planet
    sub_lord:         Planet
    antardasha_start: date
    antardasha_days:  float


class PratyantardashaResponse(BaseModel):
    major_lord:         Planet
    sub_lord:           Planet
    pratyantardashas:   list[PratyantardashaEntry]


class CurrentDashaRequest(BaseModel):
    birth_date:   date
    moon_degrees: float = Field(..., ge=0.0, lt=360.0)
    query_date:   Optional[date] = None


class CurrentDashaResponse(BaseModel):
    mahadasha:       Optional[MahadashaEntry]
    antardasha:      Optional[AntardashaEntry]
    pratyantardasha: Optional[PratyantardashaEntry]


# ─────────────────────────────────────────────────────────────────────────────
# Lordship endpoints
# ─────────────────────────────────────────────────────────────────────────────

class PlanetEvaluationRequest(BaseModel):
    lagna:  Sign
    planet: Planet


class PlanetEvaluationResponse(BaseModel):
    planet:            Planet
    lagna:             Sign
    owned_houses:      list[int]
    is_lagna_lord:     bool
    is_yoga_karaka:    bool
    is_maraka:         bool
    is_8th_lord:       bool
    trikona_houses:    list[int]
    kendra_houses:     list[int]
    trishadaya_houses: list[int]
    rules_applied:     list[str]
    functional_nature: FunctionalNature
    strength_score:    int
    interpretation:    str


class LagnaProfileRequest(BaseModel):
    lagna: Sign


class LagnaHouseEntry(BaseModel):
    house:  int
    sign:   Sign
    lord:   Planet


class LagnaProfileResponse(BaseModel):
    lagna:       Sign
    lagna_lord:  Planet
    houses:      list[LagnaHouseEntry]
    planet_evaluations: list[PlanetEvaluationResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Yoga / Maraka endpoints
# ─────────────────────────────────────────────────────────────────────────────

class PlanetPosition(BaseModel):
    planet: Planet
    house:  int = Field(..., ge=1, le=12)


class YogaAnalysisRequest(BaseModel):
    lagna:            Sign
    planet_positions: list[PlanetPosition] = Field(
        default_factory=list,
        description=(
            "Planetary house positions (1–12). "
            "Omit if you only need lordship-based yogas (Yoga Karaka detection still works)."
        ),
    )


class RajaYogaEntry(BaseModel):
    yoga_type:      YogaType
    sambandha_type: SambandhaType
    kendra_lord:    Planet
    kendra_house:   int
    trikona_lord:   Planet
    trikona_house:  int
    description:    str


class MarakaEntry(BaseModel):
    planet:                  Planet
    maraka_houses:           list[int]
    is_natural_malefic:      bool
    placed_in_maraka_house:  bool
    severity:                str
    description:             str


class PlanetSummaryEntry(BaseModel):
    functional_nature: FunctionalNature
    owned_houses:      list[int]
    is_yoga_karaka:    bool
    is_maraka:         bool
    strength_score:    int


class YogaAnalysisResponse(BaseModel):
    lagna:          Sign
    raja_yogas:     list[RajaYogaEntry]
    marakas:        list[MarakaEntry]
    planet_summary: dict[str, PlanetSummaryEntry]


# ─────────────────────────────────────────────────────────────────────────────
# Ascendant database endpoint
# ─────────────────────────────────────────────────────────────────────────────

class AscendantDatabaseEntry(BaseModel):
    lagna:        Sign
    lagna_lord:   Planet
    auspicious:   list[Planet]
    inauspicious: list[Planet]
    yoga_karaka:  list[Planet]
    maraka:       list[Planet]
    neutral:      list[Planet]
    notes:        str
    house_lords:  dict[int, Planet]
