"""
Laghu Parashari Astrology Tutoring Backend
==========================================

FastAPI application implementing the complete Laghu Parashari engine suite:

  • Vimshottari Dasha Calculator  (/dasha)
  • House Lordship Rule Engine    (/lordship)
  • Yoga Karaka & Maraka Engine   (/yoga)
  • Ascendant Profiles DB         (/ascendants)
  • Charts, Ephemeris & Kundali   (/charts)

Run:
    uvicorn main:app --reload --port 8000

Docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes import dasha_router, lordship_router, yoga_router, ascendant_router
from api.chart_routes import chart_router

app = FastAPI(
    title="Laghu Parashari Astrology API",
    description=(
        "Complete backend for an astrology tutoring app based on the classical "
        "**Laghu Parashari** text. Includes Vimshottari Dasha calculation, "
        "House Lordship rules, Yoga Karaka & Maraka identification, Swiss Ephemeris "
        "integration (Lahiri ayanamsa), Kundali SVG generation, Dasha interpretations, "
        "natal chart persistence, and lesson progress tracking."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(dasha_router)
app.include_router(lordship_router)
app.include_router(yoga_router)
app.include_router(ascendant_router)
app.include_router(chart_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status":  "online",
        "version": "2.0.0",
        "endpoints": {
            "dasha":      "/dasha",
            "lordship":   "/lordship",
            "yoga":       "/yoga",
            "ascendants": "/ascendants",
            "charts":     "/charts",
            "docs":       "/docs",
        },
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
