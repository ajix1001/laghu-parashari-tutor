"""
Prashna (Horary) Engine
=======================

Casts a chart for the moment a question is asked and interprets it using
classical Prashna Shastra rules grounded in the same Laghu Parashari
lordship framework used elsewhere in this project.

Core principles applied:
  • Lagna and its lord  → the querent and their state of mind
  • Moon                → the mind / the question itself
  • Relevant house lord → the matter being asked about
  • Functional benefics (Yoga Karaka / Auspicious lords for the prashna lagna)
    favour the question; functional malefics oppose it.
  • Connection (conjunction, mutual reception, kendra/trikona placement,
    or being in mutual houses) between the lagna lord and the house lord
    of the matter is the strongest "yes" indicator.
  • Sign nature of the lagna gives a timing flavour:
        Movable (Chara) — quick results, change
        Fixed   (Sthira)— delay, status quo, no change
        Dual    (Dwiswabhava) — partial / repeat outcomes
"""

from __future__ import annotations
from datetime import datetime, timezone
import re
from typing import Optional

from data.constants import (
    Sign, SIGNS_LIST, Planet, SIGN_RULERS,
    NATURAL_BENEFICS, NATURAL_MALEFICS,
)
from engines.ephemeris_engine import calculate_chart
from engines.lordship_engine import evaluate_planet, FunctionalNature


# ─────────────────────────────────────────────────────────────────────────────
# Question categories
# Each maps a question theme to the most relevant houses and trigger keywords.
# The first house in `houses` is treated as the primary signifier.
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES: dict[str, dict] = {
    "career": {
        "label":    "Career & Work",
        "houses":   [10, 6, 11],
        "keywords": ["career", "job", "work", "promotion", "salary", "boss",
                     "office", "profession", "business", "employment", "interview"],
    },
    "marriage": {
        "label":    "Marriage",
        "houses":   [7, 2, 11],
        "keywords": ["marry", "marriage", "wedding", "engagement", "spouse",
                     "husband", "wife", "alliance", "matrimony"],
    },
    "relationship": {
        "label":    "Love & Relationship",
        "houses":   [7, 5],
        "keywords": ["love", "romance", "boyfriend", "girlfriend", "crush",
                     "relationship", "partner", "dating", "breakup"],
    },
    "children": {
        "label":    "Children",
        "houses":   [5, 9, 11],
        "keywords": ["child", "children", "baby", "pregnancy", "conceive",
                     "son", "daughter", "kid"],
    },
    "finance": {
        "label":    "Money & Finance",
        "houses":   [2, 11, 5],
        "keywords": ["money", "wealth", "finance", "income", "loan", "debt",
                     "investment", "savings", "rich", "fund", "buy", "afford"],
    },
    "education": {
        "label":    "Education & Exams",
        "houses":   [4, 5, 9],
        "keywords": ["study", "exam", "education", "degree", "admission",
                     "college", "university", "school", "course", "result"],
    },
    "health": {
        "label":    "Health",
        "houses":   [1, 6, 8],
        "keywords": ["health", "disease", "illness", "sick", "surgery",
                     "recover", "cure", "medical", "doctor", "hospital", "pain"],
    },
    "travel": {
        "label":    "Travel & Relocation",
        "houses":   [3, 9, 12],
        "keywords": ["travel", "journey", "trip", "abroad", "foreign", "visa",
                     "relocate", "move", "migration", "immigration"],
    },
    "property": {
        "label":    "Home & Property",
        "houses":   [4, 11],
        "keywords": ["house", "property", "land", "home", "apartment",
                     "real estate", "rent", "buy a house"],
    },
    "litigation": {
        "label":    "Legal & Disputes",
        "houses":   [6, 8, 7],
        "keywords": ["court", "lawsuit", "legal", "litigation", "dispute",
                     "case", "police", "fight", "enemy", "lawyer"],
    },
    "lost_object": {
        "label":    "Lost Object / Missing",
        "houses":   [2, 4, 7],
        "keywords": ["lost", "missing", "stolen", "find", "recover", "where is"],
    },
    "spiritual": {
        "label":    "Spiritual Path",
        "houses":   [9, 12, 5],
        "keywords": ["spiritual", "moksha", "liberation", "guru", "god",
                     "sadhana", "meditation", "dharma"],
    },
    "general": {
        "label":    "General Guidance",
        "houses":   [1, 10, 7],
        "keywords": [],
    },
}


def detect_category(question: str) -> str:
    """Map a free-text question to one of the CATEGORIES keys."""
    q = question.lower()
    best_cat = "general"
    best_hits = 0
    for cat, meta in CATEGORIES.items():
        hits = sum(1 for kw in meta["keywords"] if re.search(rf"\b{re.escape(kw)}", q))
        if hits > best_hits:
            best_hits = hits
            best_cat  = cat
    return best_cat


# ─────────────────────────────────────────────────────────────────────────────
# Sign nature & helpers
# ─────────────────────────────────────────────────────────────────────────────

MOVABLE_SIGNS = {Sign.ARIES, Sign.CANCER, Sign.LIBRA, Sign.CAPRICORN}
FIXED_SIGNS   = {Sign.TAURUS, Sign.LEO, Sign.SCORPIO, Sign.AQUARIUS}
DUAL_SIGNS    = {Sign.GEMINI, Sign.VIRGO, Sign.SAGITTARIUS, Sign.PISCES}


def _sign_nature(sign: Sign) -> tuple[str, str]:
    """Return (label, timing_hint) for a sign's chara/sthira/dwiswabhava nature."""
    if sign in MOVABLE_SIGNS:
        return ("Movable (Chara)",
                "Quick results, change is favoured — outcome unfolds soon.")
    if sign in FIXED_SIGNS:
        return ("Fixed (Sthira)",
                "Delay or status-quo — the situation resists change; outcome is slow.")
    return ("Dual (Dwiswabhava)",
            "Partial or repeat results — the matter resolves in stages, not at once.")


def _ordinal(n: int) -> str:
    return {1:"1st",2:"2nd",3:"3rd"}.get(n, f"{n}th")


def _angular_distance(h1: int, h2: int) -> int:
    """Houses-apart distance (1..12) from h1 to h2."""
    return ((h2 - h1) % 12) or 12


def _has_classical_aspect(from_house: int, to_house: int, planet: Planet) -> bool:
    """
    Classical Vedic graha drishti: every planet aspects its 7th.
    Mars also aspects 4 and 8; Jupiter also 5 and 9; Saturn also 3 and 10;
    Rahu/Ketu also 5 and 9 (per most schools).
    """
    d = _angular_distance(from_house, to_house)
    if d == 7:
        return True
    if planet == Planet.MARS    and d in (4, 8):  return True
    if planet == Planet.JUPITER and d in (5, 9):  return True
    if planet == Planet.SATURN  and d in (3, 10): return True
    if planet in (Planet.RAHU, Planet.KETU) and d in (5, 9): return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Verdict scoring
# ─────────────────────────────────────────────────────────────────────────────

def _score_to_verdict(score: int) -> tuple[str, str, str]:
    """
    Map a raw integer score to (verdict, color, headline).
    Bands tuned for typical score ranges produced by _evaluate().
    """
    if score >= 6:
        return ("Yes — Strongly Favoured", "gold",
                "The chart speaks clearly in your favour.")
    if score >= 3:
        return ("Yes — Favoured", "indigo",
                "The signs lean toward a positive outcome.")
    if score >= 1:
        return ("Mixed — Cautiously Hopeful", "indigo",
                "Some support, but expect partial results or effort.")
    if score >= -2:
        return ("Uncertain — Wait & Watch", "ochre",
                "The picture is unclear. Avoid major commitments now.")
    if score >= -5:
        return ("Unfavourable — Likely No", "ochre",
                "The signs are against the matter at this time.")
    return ("No — Strongly Against", "red",
            "The chart strongly counsels against this path.")


def _evaluate(
    chart: dict,
    category: str,
) -> dict:
    """
    Run the full prashna interpretation. Pure function — no I/O.
    """
    cat_meta    = CATEGORIES[category]
    primary_h   = cat_meta["houses"][0]
    other_hs    = cat_meta["houses"][1:]
    lagna       = chart["lagna_sign"]
    lagna_idx   = SIGNS_LIST.index(lagna)
    planets     = chart["planets"]
    occupants   = chart["house_occupants"]

    # ── 1. Lagna & lagna lord ────────────────────────────────────────────────
    lagna_lord    = SIGN_RULERS[lagna]
    lagna_eval    = evaluate_planet(lagna, lagna_lord)
    lagna_lord_h  = planets[lagna_lord.value]["house"]

    # ── 2. The relevant house lord (the matter) ──────────────────────────────
    # Sign on the cusp of the primary house under whole-sign houses.
    matter_sign     = SIGNS_LIST[(lagna_idx + primary_h - 1) % 12]
    matter_lord     = SIGN_RULERS[matter_sign]
    matter_lord_h   = planets[matter_lord.value]["house"]
    matter_eval     = evaluate_planet(lagna, matter_lord)

    # ── 3. Moon — the mind ───────────────────────────────────────────────────
    moon_h          = planets["Moon"]["house"]
    moon_eval       = evaluate_planet(lagna, Planet.MOON)

    # ── 4. Connection between lagna lord and matter lord ─────────────────────
    connections: list[str] = []
    if lagna_lord == matter_lord:
        connections.append(
            f"{lagna_lord.value} rules both the lagna and the matter — "
            f"the querent IS the matter; very direct involvement."
        )
    else:
        if lagna_lord_h == matter_lord_h:
            connections.append(
                f"{lagna_lord.value} (lagna lord) and {matter_lord.value} "
                f"(lord of {_ordinal(primary_h)}) are conjunct in the "
                f"{_ordinal(lagna_lord_h)} house — strong yoga of querent and matter."
            )
        if _has_classical_aspect(lagna_lord_h, matter_lord_h, lagna_lord) or \
           _has_classical_aspect(matter_lord_h, lagna_lord_h, matter_lord):
            connections.append(
                f"{lagna_lord.value} and {matter_lord.value} are in mutual aspect — "
                f"the querent and the matter are linked."
            )
        # Parivartana / mutual reception (whole-sign):
        ll_sign_idx = (lagna_idx + lagna_lord_h - 1) % 12
        ml_sign_idx = (lagna_idx + matter_lord_h - 1) % 12
        if SIGN_RULERS[SIGNS_LIST[ll_sign_idx]] == matter_lord and \
           SIGN_RULERS[SIGNS_LIST[ml_sign_idx]] == lagna_lord:
            connections.append(
                f"{lagna_lord.value} and {matter_lord.value} are in parivartana "
                f"(mutual exchange) — the highest form of yoga; outcome strongly tied to wish."
            )

    # ── 5. Influences on the primary house (occupants + aspects) ─────────────
    primary_occupants = occupants.get(primary_h, [])
    primary_pos_inf:   list[str] = []
    primary_neg_inf:   list[str] = []

    for p_name in primary_occupants:
        p_enum = Planet(p_name) if p_name in [pl.value for pl in Planet] else None
        if not p_enum:
            continue
        ev = evaluate_planet(lagna, p_enum)
        nat = ev["functional_nature"]
        if ev["is_yoga_karaka"]:
            primary_pos_inf.append(
                f"{p_name} (Yoga Karaka) sits in the {_ordinal(primary_h)} house — "
                f"a powerful blessing on the matter."
            )
        elif nat == FunctionalNature.AUSPICIOUS:
            primary_pos_inf.append(
                f"{p_name} (functional benefic) occupies the {_ordinal(primary_h)} house."
            )
        elif nat in (FunctionalNature.INAUSPICIOUS, FunctionalNature.MARAKA):
            primary_neg_inf.append(
                f"{p_name} (functional malefic) afflicts the {_ordinal(primary_h)} house."
            )
        elif p_name in [pl.value for pl in NATURAL_BENEFICS]:
            primary_pos_inf.append(
                f"{p_name} (natural benefic) sits in the {_ordinal(primary_h)} house."
            )
        elif p_name in [pl.value for pl in NATURAL_MALEFICS]:
            primary_neg_inf.append(
                f"{p_name} (natural malefic) sits in the {_ordinal(primary_h)} house."
            )

    # Aspects on the primary house from elsewhere
    for p_name, info in planets.items():
        if p_name in primary_occupants:
            continue
        try:
            p_enum = Planet(p_name)
        except ValueError:
            continue
        if _has_classical_aspect(info["house"], primary_h, p_enum):
            ev = evaluate_planet(lagna, p_enum)
            if ev["is_yoga_karaka"]:
                primary_pos_inf.append(
                    f"{p_name} (Yoga Karaka) aspects the {_ordinal(primary_h)} house — "
                    f"a strong supporting influence."
                )
            elif ev["functional_nature"] == FunctionalNature.AUSPICIOUS:
                primary_pos_inf.append(
                    f"{p_name} (functional benefic) aspects the {_ordinal(primary_h)} house."
                )
            elif ev["functional_nature"] in (FunctionalNature.INAUSPICIOUS, FunctionalNature.MARAKA):
                primary_neg_inf.append(
                    f"{p_name} (functional malefic) aspects the {_ordinal(primary_h)} house."
                )

    # ── 6. Score the prashna ─────────────────────────────────────────────────
    score = 0
    factors: list[dict] = []

    def f(text: str, delta: int):
        factors.append({"factor": text, "weight": delta})
        return delta

    # Lagna lord strength
    if lagna_eval["is_yoga_karaka"]:
        score += f(f"{lagna_lord.value} (lagna lord) is the Yoga Karaka — querent's position is strong.", 3)
    elif lagna_lord_h in (1, 4, 5, 7, 9, 10, 11):
        score += f(f"{lagna_lord.value} (lagna lord) sits in a supportive {_ordinal(lagna_lord_h)} house.", 2)
    elif lagna_lord_h in (6, 8, 12):
        score += f(f"{lagna_lord.value} (lagna lord) is afflicted in the {_ordinal(lagna_lord_h)} house — querent is under stress.", -2)

    # Matter lord strength
    if matter_eval["is_yoga_karaka"]:
        score += f(f"{matter_lord.value} (lord of the {_ordinal(primary_h)}) is the Yoga Karaka — exceptional support for the matter.", 3)
    elif matter_lord_h in (1, 4, 5, 7, 9, 10, 11):
        score += f(f"{matter_lord.value} (lord of the {_ordinal(primary_h)}) is well-placed in the {_ordinal(matter_lord_h)} house.", 2)
    elif matter_lord_h in (6, 8, 12):
        # 12th from primary house is loss of the matter — extra penalty if matter lord falls there
        if (matter_lord_h - primary_h) % 12 in (5, 7, 11):
            score += f(f"{matter_lord.value} (lord of the {_ordinal(primary_h)}) falls in the {_ordinal(matter_lord_h)} — loss/affliction of the matter.", -3)
        else:
            score += f(f"{matter_lord.value} (lord of the {_ordinal(primary_h)}) is in a dusthana ({_ordinal(matter_lord_h)}).", -2)

    # Connections
    if connections:
        score += f("Lagna lord is connected to the lord of the matter (yoga of querent + matter).", 3 * len(connections[:1]))

    # Primary house influences
    score += f(f"Functional benefic influences on the {_ordinal(primary_h)} house: {len(primary_pos_inf)}.", len(primary_pos_inf))
    score -= len(primary_neg_inf)
    if primary_neg_inf:
        factors.append({
            "factor": f"Functional malefic influences on the {_ordinal(primary_h)} house: {len(primary_neg_inf)}.",
            "weight": -len(primary_neg_inf),
        })

    # Moon (mind) state
    if moon_h in (6, 8, 12):
        score += f(f"Moon is in the {_ordinal(moon_h)} house — the mind is anxious or unsettled at the moment of asking.", -1)
    elif moon_eval["functional_nature"] == FunctionalNature.AUSPICIOUS or moon_eval["is_yoga_karaka"]:
        score += f("Moon is functionally auspicious — the mind is clear and the question is sincere.", 1)

    # Jupiter to Lagna or Moon — pivotal in prashna
    jup_h = planets["Jupiter"]["house"]
    if _has_classical_aspect(jup_h, 1, Planet.JUPITER) or jup_h == 1:
        score += f("Jupiter aspects or sits in the lagna — divine grace upholds the question.", 2)
    if _has_classical_aspect(jup_h, moon_h, Planet.JUPITER) or jup_h == moon_h:
        score += f("Jupiter influences the Moon — the mind is supported by wisdom.", 1)

    # ── 7. Verdict + timing ──────────────────────────────────────────────────
    verdict, color, headline = _score_to_verdict(score)
    nat_label, timing_hint   = _sign_nature(lagna)

    # Category-specific addendum
    addendum = None
    if category == "lost_object":
        # 4th house in prashna = where the object is. Direction by sign element:
        item_house = (lagna_idx + 3) % 12  # 4th sign index
        ELEM_DIR = {
            Sign.ARIES: "East", Sign.LEO: "East", Sign.SAGITTARIUS: "East",
            Sign.TAURUS: "South", Sign.VIRGO: "South", Sign.CAPRICORN: "South",
            Sign.GEMINI: "West", Sign.LIBRA: "West", Sign.AQUARIUS: "West",
            Sign.CANCER: "North", Sign.SCORPIO: "North", Sign.PISCES: "North",
        }
        item_sign = SIGNS_LIST[item_house]
        addendum = (
            f"Lost-object hint: the 4th house from lagna ({item_sign.value}) "
            f"suggests the object is in the {ELEM_DIR.get(item_sign, '?')} direction "
            f"or near a place with that element's qualities."
        )

    return {
        "category":       category,
        "category_label": cat_meta["label"],
        "primary_house":  primary_h,
        "other_houses":   other_hs,
        "lagna_sign":     lagna.value,
        "lagna_nature":   nat_label,
        "lagna_lord":     lagna_lord.value,
        "lagna_lord_house": lagna_lord_h,
        "matter_lord":    matter_lord.value,
        "matter_lord_house": matter_lord_h,
        "moon_house":     moon_h,
        "connections":    connections,
        "supports":       primary_pos_inf,
        "afflictions":    primary_neg_inf,
        "factors":        factors,
        "score":          score,
        "verdict":        verdict,
        "color":          color,
        "headline":       headline,
        "timing_hint":    timing_hint,
        "addendum":       addendum,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def cast_prashna(
    question:    str,
    latitude:    float,
    longitude:   float,
    tz_offset:   float,
    when:        Optional[datetime] = None,
    category:    Optional[str]      = None,
) -> dict:
    """
    Cast a prashna chart for the given question and return interpretation.

    Parameters
    ----------
    question : str
        The question being asked.
    latitude, longitude, tz_offset : float
        Location of the querent at the moment of asking.
    when : datetime, optional
        Moment of asking. Defaults to "now" in the given tz_offset.
    category : str, optional
        One of the CATEGORIES keys. If None, auto-detected from `question`.

    Returns
    -------
    dict — full chart + interpretation, JSON-serialisable.
    """
    # Default to "now" in the user's stated tz
    if when is None:
        when = datetime.now(timezone.utc)
    # Convert to local civil clock by adding tz_offset
    from datetime import timedelta
    local = when.astimezone(timezone.utc) + timedelta(hours=tz_offset)

    chart = calculate_chart(
        local.year, local.month, local.day,
        local.hour, local.minute,
        latitude, longitude, tz_offset,
    )

    # Resolve category
    cat = category if (category and category in CATEGORIES) else detect_category(question)

    interpretation = _evaluate(chart, cat)

    # Make chart JSON-friendly
    chart_out = {
        "julian_day":      chart["julian_day"],
        "ayanamsa":        chart["ayanamsa"],
        "lagna_degrees":   chart["lagna_degrees"],
        "lagna_sign":      chart["lagna_sign"].value,
        "planets": {
            name: {**info, "sign": info["sign"].value}
            for name, info in chart["planets"].items()
        },
        "house_occupants": {int(h): v for h, v in chart["house_occupants"].items()},
    }

    return {
        "question":      question,
        "asked_at_utc":  when.astimezone(timezone.utc).isoformat(),
        "location":      {"latitude": latitude, "longitude": longitude, "tz_offset": tz_offset},
        "chart":         chart_out,
        "interpretation": interpretation,
    }
