"""
Core Jyotish constants derived from Laghu Parashari (S.R. Jha).

All planetary sequences, nakshatra data, and period lengths are
sourced directly from the text's canonical Vimshottari Dasha tables.
"""

from enum import Enum


# ─────────────────────────────────────────────
# Planets
# ─────────────────────────────────────────────

class Planet(str, Enum):
    SUN      = "Sun"
    MOON     = "Moon"
    MARS     = "Mars"
    RAHU     = "Rahu"
    JUPITER  = "Jupiter"
    SATURN   = "Saturn"
    MERCURY  = "Mercury"
    KETU     = "Ketu"
    VENUS    = "Venus"


# ─────────────────────────────────────────────
# Vimshottari Dasha — 120-year cycle
# Sequence and fixed period in years (Laghu Parashari, Chapter 1)
# ─────────────────────────────────────────────

VIMSHOTTARI_SEQUENCE: list[Planet] = [
    Planet.KETU,
    Planet.VENUS,
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.RAHU,
    Planet.JUPITER,
    Planet.SATURN,
    Planet.MERCURY,
]

DASHA_YEARS: dict[Planet, int] = {
    Planet.KETU:    7,
    Planet.VENUS:   20,
    Planet.SUN:     6,
    Planet.MOON:    10,
    Planet.MARS:    7,
    Planet.RAHU:    18,
    Planet.JUPITER: 16,
    Planet.SATURN:  19,
    Planet.MERCURY: 17,
}

TOTAL_DASHA_YEARS = 120  # Sum of all dasha periods

# Days in a year used for dasha calculations (sidereal / civil)
DAYS_PER_YEAR = 365.25


# ─────────────────────────────────────────────
# Nakshatras — 27 lunar mansions
# Each spans exactly 13°20' (= 800 arc-minutes = 13.3333...°)
# Ruling planet follows the Vimshottari sequence
# ─────────────────────────────────────────────

NAKSHATRA_SPAN_DEGREES = 360 / 27  # 13.333...°

NAKSHATRAS: list[dict] = [
    # idx  name                  lord            pada_span   deity
    {"id": 0,  "name": "Ashwini",          "lord": Planet.KETU,    "start_deg": 0.000},
    {"id": 1,  "name": "Bharani",          "lord": Planet.VENUS,   "start_deg": 13.333},
    {"id": 2,  "name": "Krittika",         "lord": Planet.SUN,     "start_deg": 26.667},
    {"id": 3,  "name": "Rohini",           "lord": Planet.MOON,    "start_deg": 40.000},
    {"id": 4,  "name": "Mrigashira",       "lord": Planet.MARS,    "start_deg": 53.333},
    {"id": 5,  "name": "Ardra",            "lord": Planet.RAHU,    "start_deg": 66.667},
    {"id": 6,  "name": "Punarvasu",        "lord": Planet.JUPITER, "start_deg": 80.000},
    {"id": 7,  "name": "Pushya",           "lord": Planet.SATURN,  "start_deg": 93.333},
    {"id": 8,  "name": "Ashlesha",         "lord": Planet.MERCURY, "start_deg": 106.667},
    {"id": 9,  "name": "Magha",            "lord": Planet.KETU,    "start_deg": 120.000},
    {"id": 10, "name": "Purva Phalguni",   "lord": Planet.VENUS,   "start_deg": 133.333},
    {"id": 11, "name": "Uttara Phalguni",  "lord": Planet.SUN,     "start_deg": 146.667},
    {"id": 12, "name": "Hasta",            "lord": Planet.MOON,    "start_deg": 160.000},
    {"id": 13, "name": "Chitra",           "lord": Planet.MARS,    "start_deg": 173.333},
    {"id": 14, "name": "Swati",            "lord": Planet.RAHU,    "start_deg": 186.667},
    {"id": 15, "name": "Vishakha",         "lord": Planet.JUPITER, "start_deg": 200.000},
    {"id": 16, "name": "Anuradha",         "lord": Planet.SATURN,  "start_deg": 213.333},
    {"id": 17, "name": "Jyeshtha",         "lord": Planet.MERCURY, "start_deg": 226.667},
    {"id": 18, "name": "Mula",             "lord": Planet.KETU,    "start_deg": 240.000},
    {"id": 19, "name": "Purva Ashadha",    "lord": Planet.VENUS,   "start_deg": 253.333},
    {"id": 20, "name": "Uttara Ashadha",   "lord": Planet.SUN,     "start_deg": 266.667},
    {"id": 21, "name": "Shravana",         "lord": Planet.MOON,    "start_deg": 280.000},
    {"id": 22, "name": "Dhanishtha",       "lord": Planet.MARS,    "start_deg": 293.333},
    {"id": 23, "name": "Shatabhisha",      "lord": Planet.RAHU,    "start_deg": 306.667},
    {"id": 24, "name": "Purva Bhadrapada", "lord": Planet.JUPITER, "start_deg": 320.000},
    {"id": 25, "name": "Uttara Bhadrapada","lord": Planet.SATURN,  "start_deg": 333.333},
    {"id": 26, "name": "Revati",           "lord": Planet.MERCURY, "start_deg": 346.667},
]

# Quick lookup: nakshatra index -> lord
NAKSHATRA_LORD: dict[int, Planet] = {n["id"]: n["lord"] for n in NAKSHATRAS}


# ─────────────────────────────────────────────
# Zodiac Signs & their rulers
# ─────────────────────────────────────────────

class Sign(str, Enum):
    ARIES       = "Aries"
    TAURUS      = "Taurus"
    GEMINI      = "Gemini"
    CANCER      = "Cancer"
    LEO         = "Leo"
    VIRGO       = "Virgo"
    LIBRA       = "Libra"
    SCORPIO     = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN   = "Capricorn"
    AQUARIUS    = "Aquarius"
    PISCES      = "Pisces"


SIGN_RULERS: dict[Sign, Planet] = {
    Sign.ARIES:       Planet.MARS,
    Sign.TAURUS:      Planet.VENUS,
    Sign.GEMINI:      Planet.MERCURY,
    Sign.CANCER:      Planet.MOON,
    Sign.LEO:         Planet.SUN,
    Sign.VIRGO:       Planet.MERCURY,
    Sign.LIBRA:       Planet.VENUS,
    Sign.SCORPIO:     Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN:   Planet.SATURN,
    Sign.AQUARIUS:    Planet.SATURN,
    Sign.PISCES:      Planet.JUPITER,
}

# Sign index (0-based) for house calculations
SIGNS_LIST: list[Sign] = list(Sign)


# ─────────────────────────────────────────────
# Natural benefics and malefics (naisargika)
# ─────────────────────────────────────────────

NATURAL_BENEFICS: set[Planet] = {
    Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON
}

NATURAL_MALEFICS: set[Planet] = {
    Planet.SUN, Planet.MARS, Planet.SATURN, Planet.RAHU, Planet.KETU
}


# ─────────────────────────────────────────────
# House categories
# ─────────────────────────────────────────────

TRIKONA_HOUSES  = {1, 5, 9}    # Dharma trines — inherently auspicious lords
KENDRA_HOUSES   = {1, 4, 7, 10} # Angular houses — Kendradhipati Dosha applies
TRISHADAYA_HOUSES = {3, 6, 11} # Upachaya (dusthanas subset) — inherently inauspicious lords
DUSTHANA_HOUSES = {6, 8, 12}   # Houses of affliction
MARAKA_HOUSES   = {2, 7}       # 12th from houses of longevity (3, 8)
