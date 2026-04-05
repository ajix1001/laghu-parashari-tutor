"""
Ephemeris Engine — PyEphem with Lahiri Ayanamsa

Calculates sidereal planetary positions, Lagna, and house placements
using the pyephem library (VSOP87 planetary theory, accurate to ~1 arcminute).

Ayanamsa: Lahiri (Chitrapaksha) — Indian Astronomical Ephemeris standard.
  Lahiri ayanamsa ≈ 23.85° in J2000; we use the widely-accepted formula
  from Krishnamurti / IAE which is what most Vedic software implements.

House system: Whole Sign — each sign from the Lagna sign is one house.
"""

from __future__ import annotations
import math
import ephem
from datetime import datetime, timezone
from data.constants import Sign, SIGNS_LIST, Planet

# ─────────────────────────────────────────────────────────────────────────────
# Lahiri Ayanamsa
# ─────────────────────────────────────────────────────────────────────────────
# Reference epoch T0 = 21 March 285 CE (Julian Day 1827424.5)
# Rate: 50.2388475 arc-seconds per tropical year

_AYANAMSA_T0_JD   = 1827424.5     # approx zero ayanamsa date (285 CE)
_AYANAMSA_RATE    = 50.2388475    # arc-sec per tropical year
_TROPICAL_YEAR    = 365.242189623  # days

def _lahiri_ayanamsa(jd: float) -> float:
    """Return Lahiri ayanamsa in decimal degrees for a given Julian Day."""
    years_since_t0 = (jd - _AYANAMSA_T0_JD) / _TROPICAL_YEAR
    arcsec = _AYANAMSA_RATE * years_since_t0
    return (arcsec / 3600.0) % 360.0


# ─────────────────────────────────────────────────────────────────────────────
# Ephem planet objects
# ─────────────────────────────────────────────────────────────────────────────

def _ephem_date(year: int, month: int, day: int,
                hour: int, minute: int, tz_offset: float) -> ephem.Date:
    """Convert local time to ephem.Date (UT)."""
    from datetime import timedelta
    # Build local datetime then subtract offset to get UT
    local_dt = datetime(year, month, day, hour, minute, 0)
    # tz_offset is hours east of UTC (e.g. +5.5 for IST)
    ut_dt = local_dt - timedelta(hours=tz_offset)
    return ephem.Date(ut_dt)


def _tropical_longitude(body: ephem.Body) -> float:
    """Return tropical ecliptic longitude in degrees (0-360)."""
    ecl = ephem.Ecliptic(body, epoch=ephem.J2000)
    return math.degrees(ecl.lon) % 360.0


def _body_speed(body_cls, d: ephem.Date) -> float:
    """Approximate daily speed in degrees (for retrograde detection)."""
    b1 = body_cls(); b1.compute(d - 0.5)
    b2 = body_cls(); b2.compute(d + 0.5)
    lon1 = math.degrees(ephem.Ecliptic(b1, epoch=ephem.J2000).lon)
    lon2 = math.degrees(ephem.Ecliptic(b2, epoch=ephem.J2000).lon)
    diff = (lon2 - lon1 + 540) % 360 - 180   # handle 0/360 boundary
    return diff  # deg/day; negative = retrograde


_PLANET_CLASSES: dict[str, type] = {
    "Sun":     ephem.Sun,
    "Moon":    ephem.Moon,
    "Mars":    ephem.Mars,
    "Mercury": ephem.Mercury,
    "Jupiter": ephem.Jupiter,
    "Venus":   ephem.Venus,
    "Saturn":  ephem.Saturn,
}


# ─────────────────────────────────────────────────────────────────────────────
# Ascendant (Lagna) via RAMC
# ─────────────────────────────────────────────────────────────────────────────

def _sidereal_time_to_asc(lst_rad: float, lat_deg: float,
                           obliquity_deg: float) -> float:
    """
    Calculate tropical Ascendant from Local Sidereal Time (radians),
    geographic latitude, and obliquity of the ecliptic.
    Returns tropical longitude in degrees (0-360).
    """
    lat = math.radians(lat_deg)
    eps = math.radians(obliquity_deg)
    # Standard ascendant formula — raw result is the Descendant (western horizon).
    # Add 180° to get the Ascendant (eastern horizon).
    asc = math.atan2(
        -math.cos(lst_rad),
        math.sin(lst_rad) * math.cos(eps) + math.tan(lat) * math.sin(eps)
    )
    return (math.degrees(asc) + 180.0) % 360.0


def _compute_lagna(d: ephem.Date, lat: float, lon: float,
                   obliquity_deg: float) -> float:
    """Return tropical Lagna in degrees."""
    obs = ephem.Observer()
    obs.date = d
    obs.lat  = str(lat)
    obs.lon  = str(lon)
    obs.elevation = 0
    obs.pressure  = 0  # no refraction
    lst_rad = float(obs.sidereal_time())
    return _sidereal_time_to_asc(lst_rad, lat, obliquity_deg)


# ─────────────────────────────────────────────────────────────────────────────
# Main calculation function
# ─────────────────────────────────────────────────────────────────────────────

def calculate_chart(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    tz_offset: float,
) -> dict:
    """
    Calculate a complete sidereal natal chart.

    Returns
    -------
    {
        "julian_day":     float,
        "ayanamsa":       float,
        "lagna_degrees":  float,       # sidereal
        "lagna_sign":     Sign,
        "planets":        {name: {longitude, sign, sign_deg, house, is_retrograde}},
        "house_occupants":{1-12: [planet_names]},
    }
    """
    edate = _ephem_date(year, month, day, hour, minute, tz_offset)
    # ephem epoch is 1899-12-31.5 = JD 2415020.0
    jd    = float(edate) + 2415020.0

    # Obliquity of ecliptic (IAU formula, T in Julian centuries from J2000)
    T = (jd - 2451545.0) / 36525.0
    obliquity = 23.439291111 - 0.013004167 * T - 1.64e-7 * T**2 + 5.04e-7 * T**3

    ayanamsa     = _lahiri_ayanamsa(jd)
    tropical_asc = _compute_lagna(edate, latitude, longitude, obliquity)
    sidereal_asc = (tropical_asc - ayanamsa) % 360.0

    lagna_sign_idx = int(sidereal_asc / 30)
    lagna_sign     = SIGNS_LIST[lagna_sign_idx]

    # ── Planets ───────────────────────────────────────────────────────────
    planet_data: dict[str, dict] = {}

    for name, cls in _PLANET_CLASSES.items():
        body = cls(); body.compute(edate)
        tropical_lon = _tropical_longitude(body)
        sidereal_lon = (tropical_lon - ayanamsa) % 360.0
        speed        = _body_speed(cls, edate)
        sign_idx     = int(sidereal_lon / 30)
        sign         = SIGNS_LIST[sign_idx]
        sign_deg     = sidereal_lon - sign_idx * 30.0
        house        = _whole_sign_house(lagna_sign_idx, sign_idx)

        planet_data[name] = {
            "longitude":     round(sidereal_lon, 4),
            "sign":          sign,
            "sign_deg":      round(sign_deg, 4),
            "house":         house,
            "is_retrograde": speed < 0 and name not in ("Sun", "Moon"),
        }

    # ── Rahu / Ketu (mean lunar node) ────────────────────────────────────
    rahu_tropical = _get_rahu_tropical(edate)
    rahu_sidereal = (rahu_tropical - ayanamsa) % 360.0
    ketu_sidereal = (rahu_sidereal + 180.0) % 360.0

    for name, lon in (("Rahu", rahu_sidereal), ("Ketu", ketu_sidereal)):
        sign_idx = int(lon / 30)
        planet_data[name] = {
            "longitude":     round(lon, 4),
            "sign":          SIGNS_LIST[sign_idx],
            "sign_deg":      round(lon - sign_idx * 30.0, 4),
            "house":         _whole_sign_house(lagna_sign_idx, sign_idx),
            "is_retrograde": True,   # nodes are always retrograde
        }

    # ── House occupants ───────────────────────────────────────────────────
    house_occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for name, info in planet_data.items():
        house_occupants[info["house"]].append(name)

    return {
        "julian_day":      round(jd, 6),
        "ayanamsa":        round(ayanamsa, 4),
        "lagna_degrees":   round(sidereal_asc, 4),
        "lagna_sign":      lagna_sign,
        "planets":         planet_data,
        "house_occupants": house_occupants,
    }


def _get_rahu_tropical(d: ephem.Date) -> float:
    """
    Compute mean Rahu (ascending node) tropical longitude using
    the standard USNO mean-element formula.
    """
    jd = float(d) + 2415020.0  # ephem epoch offset
    T  = (jd - 2451545.0) / 36525.0
    # Mean longitude of ascending node (degrees)
    omega = 125.04452 - 1934.136261 * T + 0.0020708 * T**2 + T**3 / 450000.0
    return omega % 360.0


def _whole_sign_house(lagna_sign_idx: int, planet_sign_idx: int) -> int:
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


def planet_positions_for_yoga(chart: dict) -> list[dict]:
    """Return positions list compatible with the yoga engine."""
    result = []
    for name, info in chart["planets"].items():
        try:
            result.append({"planet": Planet(name), "house": info["house"]})
        except ValueError:
            pass
    return result
