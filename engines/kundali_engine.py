"""
Kundali SVG Engine — Classical North Indian Kundali chart.

Construction (produces exactly 12 sections):
  1. Outer square  (S × S)
  2. Inner diamond — a square rotated 45°, its 4 vertices touching
     the midpoint of each outer side: MT, MR, MB, ML
  3. Two full diagonals of the outer square: TL→BR and TR→BL

The two diagonals cross the inner diamond boundary at 4 points
(A, B, D, E) and meet at the centre C, dividing the space into:

  ┌─────────────────────────┐
  │ \    12  │   1   │  11/ │
  │   \──────┼───────┼──/   │
  │  3  \    │       │  / 10│
  │──────────┼ center┼──────│
  │  4  /    │       │  \ 9 │
  │   /──────┼───────┼──\   │
  │ /    5   │   7   │   8\ │
  └─────────────────────────┘
  (simplified — real chart has triangular corner sections)

Houses (counterclockwise from H1 at top-centre):
  H1  (kendra)  inner-top    quad  : MT, B, C, A
  H2  (panapara) TL corner  upper  : TL, MT, A
  H3  (apoklima) TL corner  lower  : TL, A,  ML
  H4  (kendra)  inner-left   quad  : ML, A,  C, D
  H5  (panapara) BL corner  upper  : BL, ML, D
  H6  (apoklima) BL corner  lower  : BL, D,  MB
  H7  (kendra)  inner-bottom quad  : MB, D,  C, E
  H8  (apoklima) BR corner  lower  : BR, E,  MB
  H9  (panapara) BR corner  upper  : BR, MR, E
  H10 (kendra)  inner-right  quad  : MR, E,  C, B
  H11 (apoklima) TR corner  lower  : TR, B,  MR
  H12 (panapara) TR corner  upper  : TR, MT, B
"""

from __future__ import annotations
from data.constants import Sign, SIGNS_LIST

SIGN_ABBR: dict[str, str] = {
    "Aries":"Ar","Taurus":"Ta","Gemini":"Ge","Cancer":"Ca",
    "Leo":"Le","Virgo":"Vi","Libra":"Li","Scorpio":"Sc",
    "Sagittarius":"Sg","Capricorn":"Cp","Aquarius":"Aq","Pisces":"Pi",
}
PLANET_ABBR: dict[str, str] = {
    "Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me",
    "Jupiter":"Ju","Venus":"Ve","Saturn":"Sa","Rahu":"Ra","Ketu":"Ke",
}
PLANET_COLOR: dict[str, str] = {
    "Sun":"#b35900","Moon":"#2e3b55","Mars":"#8b0000","Mercury":"#2a6000",
    "Jupiter":"#5c3d00","Venus":"#6b0060","Saturn":"#333333",
    "Rahu":"#555500","Ketu":"#004455",
}


def _mid(p1, p2):
    return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)

def _cen(*pts):
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))


def generate_kundali_svg(
    lagna_sign: str,
    house_occupants: dict[int, list[str]],
    size: int = 360,
    retrograde: set[str] | None = None,
) -> str:
    retrograde = retrograde or set()
    S = float(size)
    M = S / 2   # half
    Q = S / 4   # quarter

    # ── Structural coordinates ────────────────────────────────────────────
    TL = (0, 0);  TR = (S, 0);  BR = (S, S);  BL = (0, S)
    MT = (M, 0);  MR = (S, M);  MB = (M, S);  ML = (0, M)
    # Diagonal intersections with inner diamond boundary
    A = (Q,   Q)    # TL→BR diagonal ∩ ML–MT side
    B = (S-Q, Q)    # TR→BL diagonal ∩ MT–MR side
    C = (M,   M)    # centre (both diagonals cross here)
    D = (Q,   S-Q)  # TR→BL diagonal ∩ ML–MB side
    E = (S-Q, S-Q)  # TL→BR diagonal ∩ MR–MB side

    # ── 12 house sections ─────────────────────────────────────────────────
    # Polygon vertices + best text-anchor point for each house
    HOUSES: dict[int, dict] = {
        # kendra (inner quadrilaterals)
        1:  {"pts": [MT, B,  C,  A ], "tc": _cen(MT, B, C, A)},
        4:  {"pts": [ML, A,  C,  D ], "tc": _cen(ML, A, C, D)},
        7:  {"pts": [MB, D,  C,  E ], "tc": _cen(MB, D, C, E)},
        10: {"pts": [MR, E,  C,  B ], "tc": _cen(MR, E, C, B)},
        # panapara / apoklima (corner triangles) — text on inner edge midpoint
        2:  {"pts": [TL, MT, A     ], "tc": _mid(MT, A)},
        3:  {"pts": [TL, A,  ML    ], "tc": _mid(A,  ML)},
        5:  {"pts": [BL, ML, D     ], "tc": _mid(ML, D)},
        6:  {"pts": [BL, D,  MB    ], "tc": _mid(D,  MB)},
        8:  {"pts": [BR, E,  MB    ], "tc": _mid(E,  MB)},
        9:  {"pts": [BR, MR, E     ], "tc": _mid(MR, E)},
        11: {"pts": [TR, B,  MR    ], "tc": _mid(B,  MR)},
        12: {"pts": [TR, MT, B     ], "tc": _mid(MT, B)},
    }

    lagna_idx = SIGNS_LIST.index(Sign(lagna_sign))

    svg: list[str] = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {S} {S}" style="font-family:\'Crimson Pro\',serif">'
    )

    # ── Background ────────────────────────────────────────────────────────
    svg.append(f'<rect width="{S}" height="{S}" fill="#f4ead5" rx="2"/>')

    # ── House polygon fills ───────────────────────────────────────────────
    for house, hd in HOUSES.items():
        pts_s = " ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in hd["pts"])
        fill  = "rgba(255,244,220,1)" if house == 1 else "#f4ead5"
        svg.append(
            f'<polygon points="{pts_s}" fill="{fill}" stroke="none"/>'
        )

    # ── Structural lines ──────────────────────────────────────────────────
    lw, lc = "1.3", "#4b3621"

    def line(p1, p2, w=lw, c=lc):
        svg.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" '
            f'x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{c}" stroke-width="{w}"/>'
        )

    # Inner diamond sides
    line(MT, MR); line(MR, MB); line(MB, ML); line(ML, MT)
    # Two main diagonals
    line(TL, BR); line(TR, BL)
    # Outer border (drawn last, on top)
    svg.append(
        f'<rect x="1" y="1" width="{S-2:.0f}" height="{S-2:.0f}" '
        f'fill="none" stroke="{lc}" stroke-width="1.8"/>'
    )

    # ── Labels for each house ─────────────────────────────────────────────
    for house, hd in HOUSES.items():
        cx, cy = hd["tc"]
        sign_idx = (lagna_idx + house - 1) % 12
        abbr     = SIGN_ABBR.get(SIGNS_LIST[sign_idx].value, "?")

        # Lagna marker: filled red circle at MT (apex of H1 polygon)
        if house == 1:
            svg.append(
                f'<circle cx="{MT[0]:.2f}" cy="{MT[1]:.2f}" r="4.5" '
                f'fill="#8b0000" opacity="0.85"/>'
            )

        # House number
        svg.append(
            f'<text x="{cx:.2f}" y="{cy-4:.2f}" text-anchor="middle" '
            f'font-size="8.5" fill="#9b7b5b" '
            f'font-family="\'IM Fell English SC\',serif">{house}</text>'
        )

        # Sign abbreviation
        sc = "#8b0000" if house == 1 else "#4b3621"
        svg.append(
            f'<text x="{cx:.2f}" y="{cy+7:.2f}" text-anchor="middle" '
            f'font-size="7.5" fill="{sc}" opacity="0.7">{abbr}</text>'
        )

        # Planets
        planets = house_occupants.get(house, [])
        py = cy + 18.0
        for planet in planets:
            pa    = PLANET_ABBR.get(planet, planet[:2])
            color = PLANET_COLOR.get(planet, "#333333")
            retro = "℞" if planet in retrograde else ""
            svg.append(
                f'<text x="{cx:.2f}" y="{py:.2f}" text-anchor="middle" '
                f'font-size="9" font-weight="600" fill="{color}">'
                f'{pa}{retro}</text>'
            )
            py += 10.5

    svg.append("</svg>")
    return "\n".join(svg)


def generate_kundali_svg_from_chart(chart: dict, size: int = 360) -> str:
    """Convenience wrapper — takes ephemeris_engine output dict."""
    retrograde = {
        name for name, info in chart["planets"].items()
        if info.get("is_retrograde")
    }
    return generate_kundali_svg(
        lagna_sign=chart["lagna_sign"].value,
        house_occupants={int(h): v for h, v in chart["house_occupants"].items()},
        size=size,
        retrograde=retrograde,
    )
