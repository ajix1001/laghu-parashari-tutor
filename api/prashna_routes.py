"""
Prashna API routes — horary chart casting and guidance.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

try:
    from engines.prashna_engine import cast_prashna, CATEGORIES
    from engines.kundali_engine import generate_kundali_svg
    PRASHNA_AVAILABLE = True
except ImportError:
    PRASHNA_AVAILABLE = False


prashna_router = APIRouter(prefix="/prashna", tags=["Prashna (Horary)"])


class PrashnaRequest(BaseModel):
    question:  str   = Field(..., min_length=2, max_length=500,
                             description="The question being asked.")
    latitude:  float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-14.0, le=14.0,
                             description="Hours east of UTC (e.g. 5.5 for IST)")
    asked_at:  Optional[datetime] = Field(
        default=None,
        description="ISO timestamp of the moment of asking. Defaults to now (UTC).",
    )
    category:  Optional[str] = Field(
        default=None,
        description=(
            "Override category. If omitted, auto-detected from the question. "
            f"One of: {', '.join(sorted(CATEGORIES.keys()))}"
            if PRASHNA_AVAILABLE else "Override category."
        ),
    )


@prashna_router.get("/categories")
def list_categories():
    """Return the list of question categories with their primary houses."""
    if not PRASHNA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prashna engine unavailable.")
    return {
        "categories": [
            {
                "key":      key,
                "label":    meta["label"],
                "houses":   meta["houses"],
                "keywords": meta["keywords"],
            }
            for key, meta in CATEGORIES.items()
        ]
    }


@prashna_router.post("/ask")
def ask_prashna(body: PrashnaRequest):
    """
    Cast a Prashna chart for the moment of asking and return a verdict
    with chart data and a narrative interpretation.
    """
    if not PRASHNA_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Prashna engine unavailable (ephemeris dependency missing).",
        )

    if body.category and body.category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{body.category}'. "
                   f"Valid: {sorted(CATEGORIES.keys())}",
        )

    result = cast_prashna(
        question  = body.question,
        latitude  = body.latitude,
        longitude = body.longitude,
        tz_offset = body.tz_offset,
        when      = body.asked_at,
        category  = body.category,
    )

    # Attach a Kundali SVG for convenience
    chart      = result["chart"]
    retrograde = {n for n, info in chart["planets"].items() if info.get("is_retrograde")}
    result["kundali_svg"] = generate_kundali_svg(
        lagna_sign      = chart["lagna_sign"],
        house_occupants = {int(h): v for h, v in chart["house_occupants"].items()},
        retrograde      = retrograde,
    )
    return result
