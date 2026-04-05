"""
Dasha Interpretation Engine — Laghu Parashari

Generates pedagogically grounded, Lagna-specific narrative interpretations for:
  1. Any Mahadasha / Antardasha combination
  2. The overall Lagna profile
  3. Individual planet functional descriptions

The engine cross-references:
  - Functional nature of both lords (from lordship_engine)
  - Houses owned by each lord (and their significations)
  - Combination quality (YK+YK = extraordinary, Maraka+Maraka = danger, etc.)
"""

from __future__ import annotations
from data.constants import Planet, Sign
from engines.lordship_engine import evaluate_planet, FunctionalNature

# ─────────────────────────────────────────────────────────────────────────────
# Signification dictionaries
# ─────────────────────────────────────────────────────────────────────────────

HOUSE_SIGNIFICATIONS: dict[int, str] = {
    1:  "self, physical body, health, personality, and general vitality",
    2:  "accumulated wealth, speech, family, food, and early education",
    3:  "courage, siblings, short journeys, communication, and self-effort",
    4:  "mother, domestic happiness, home and property, vehicles, and inner peace",
    5:  "children, creative intelligence, speculation, past-life merit (Purva Punya), and romance",
    6:  "enemies, debts, diseases, servants, and competitive struggles",
    7:  "spouse, business partnerships, open enemies, and foreign travel",
    8:  "longevity, sudden events, hidden matters, inheritance, and transformations",
    9:  "father, dharma, higher wisdom, fortune, pilgrimage, and the guru",
    10: "career, fame, authority, public recognition, and one's duty to society",
    11: "income, gains, elder siblings, social networks, and fulfilment of desires",
    12: "foreign lands, liberation (Moksha), hidden losses, hospitals, and spirituality",
}

PLANET_SIGNIFICATIONS: dict[str, str] = {
    "Sun":     "soul, authority, father, government, vitality, and self-confidence",
    "Moon":    "mind, emotions, mother, public life, water, and mental happiness",
    "Mars":    "energy, courage, landed property, siblings, accidents, and the military",
    "Mercury": "intellect, communication, trade, education, skin, and analytical ability",
    "Jupiter": "wisdom, dharma, children, fortune, expansion, teachers, and prosperity",
    "Venus":   "spouse, luxury, arts, beauty, vehicles, sensual pleasures, and relationships",
    "Saturn":  "hard work, discipline, delays, servants, longevity, karma, and justice",
    "Rahu":    "foreign influences, obsession, illusion, technology, amplification, and sudden gains",
    "Ketu":    "spiritual liberation, detachment, psychic ability, sudden accidents, and past-life karma",
}

DASHA_YEARS: dict[str, int] = {
    "Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
    "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17,
}

# Quality matrix: (maha_nature, antar_nature) → quality label + colour hint
_Q = FunctionalNature
QUALITY_MATRIX: dict[tuple, tuple[str, str]] = {
    (_Q.YOGA_KARAKA,  _Q.YOGA_KARAKA):  ("Extraordinary Raja Yoga", "gold"),
    (_Q.YOGA_KARAKA,  _Q.AUSPICIOUS):   ("Highly Auspicious",       "gold"),
    (_Q.YOGA_KARAKA,  _Q.NEUTRAL):      ("Moderately Auspicious",   "indigo"),
    (_Q.YOGA_KARAKA,  _Q.MIXED):        ("Broadly Positive with Some Challenges", "indigo"),
    (_Q.YOGA_KARAKA,  _Q.INAUSPICIOUS): ("Mixed — Yoga tempered by Sub-lord",    "ochre"),
    (_Q.YOGA_KARAKA,  _Q.MARAKA):       ("Beneficial but Watch Health",           "ochre"),
    (_Q.AUSPICIOUS,   _Q.YOGA_KARAKA):  ("Highly Auspicious",       "gold"),
    (_Q.AUSPICIOUS,   _Q.AUSPICIOUS):   ("Good and Supportive",     "indigo"),
    (_Q.AUSPICIOUS,   _Q.NEUTRAL):      ("Moderately Good",         "indigo"),
    (_Q.AUSPICIOUS,   _Q.MIXED):        ("Broadly Positive",        "indigo"),
    (_Q.AUSPICIOUS,   _Q.INAUSPICIOUS): ("Mixed Period",            "ochre"),
    (_Q.AUSPICIOUS,   _Q.MARAKA):       ("Positive Overall, Caution for Health", "ochre"),
    (_Q.NEUTRAL,      _Q.YOGA_KARAKA):  ("Elevated by Sub-lord",   "indigo"),
    (_Q.NEUTRAL,      _Q.AUSPICIOUS):   ("Mildly Positive",        "indigo"),
    (_Q.NEUTRAL,      _Q.NEUTRAL):      ("Ordinary Period",        "ochre"),
    (_Q.NEUTRAL,      _Q.INAUSPICIOUS): ("Mildly Challenging",     "ochre"),
    (_Q.NEUTRAL,      _Q.MARAKA):       ("Watch Health & Finances", "ochre"),
    (_Q.MIXED,        _Q.AUSPICIOUS):   ("Somewhat Positive",      "indigo"),
    (_Q.MIXED,        _Q.INAUSPICIOUS): ("Challenging Period",      "red"),
    (_Q.INAUSPICIOUS, _Q.INAUSPICIOUS): ("Difficult Period",        "red"),
    (_Q.INAUSPICIOUS, _Q.MARAKA):       ("Very Challenging",        "red"),
    (_Q.MARAKA,       _Q.MARAKA):       ("Critical — Danger to Life in Old Age", "red"),
    (_Q.MARAKA,       _Q.INAUSPICIOUS): ("Very Challenging",        "red"),
    (_Q.MARAKA,       _Q.AUSPICIOUS):   ("Mixed — Maraka Softened", "ochre"),
}


def _quality(maha_nat: FunctionalNature, antar_nat: FunctionalNature) -> tuple[str, str]:
    key = (maha_nat, antar_nat)
    if key in QUALITY_MATRIX:
        return QUALITY_MATRIX[key]
    # Fallback
    for k, v in QUALITY_MATRIX.items():
        if k[0] == maha_nat:
            return ("Mixed Period", "ochre")
    return ("Ordinary Period", "ochre")


# ─────────────────────────────────────────────────────────────────────────────
# Dasha interpretation
# ─────────────────────────────────────────────────────────────────────────────

def interpret_dasha(
    lagna: Sign,
    maha_lord: str,
    antar_lord: str | None = None,
) -> dict:
    """
    Generate a narrative interpretation for a Maha/Antardasha combination.

    Returns
    -------
    {
        "quality":       str,   # e.g. "Highly Auspicious"
        "quality_color": str,   # "gold" | "indigo" | "ochre" | "red"
        "maha_summary":  str,
        "antar_summary": str | None,
        "combined":      str,
        "areas_activated": list[str],  # house significations in play
        "cautions":      list[str],
    }
    """
    maha_eval = evaluate_planet(lagna, Planet(maha_lord))
    antar_eval = evaluate_planet(lagna, Planet(antar_lord)) if antar_lord else None

    maha_nat  = maha_eval["functional_nature"]
    antar_nat = antar_eval["functional_nature"] if antar_eval else FunctionalNature.NEUTRAL

    quality, quality_color = _quality(maha_nat, antar_nat)

    # ── Mahadasha summary ─────────────────────────────────────────────────
    maha_houses = maha_eval["owned_houses"]
    maha_house_desc = " and ".join(
        f"the {_ordinal(h)} house ({HOUSE_SIGNIFICATIONS[h]})"
        for h in maha_houses
    )
    maha_sig = PLANET_SIGNIFICATIONS.get(maha_lord, maha_lord)

    maha_special = ""
    if maha_eval["is_yoga_karaka"]:
        maha_special = (
            f" As the Yoga Karaka for {lagna.value} Lagna, {maha_lord} is the "
            f"most powerful auspicious planet — its Mahadasha reliably produces "
            f"Raja Yoga results: elevation, prosperity, and dharmic fulfilment."
        )
    elif maha_nat == FunctionalNature.MARAKA:
        maha_special = (
            f" As a Maraka lord for {lagna.value} Lagna, {maha_lord}'s Dasha "
            f"can bring significant health challenges or loss in advanced age."
        )
    elif maha_nat == FunctionalNature.INAUSPICIOUS:
        maha_special = (
            f" As a functionally inauspicious planet for {lagna.value} Lagna, "
            f"{maha_lord}'s Dasha tends to bring obstacles related to its houses."
        )

    maha_summary = (
        f"{maha_lord} ({DASHA_YEARS.get(maha_lord,'?')} years) Mahadasha is "
        f"{maha_nat.value} for {lagna.value} Lagna. "
        f"It lords {maha_house_desc if maha_house_desc else 'no sign (shadow planet)'}. "
        f"{maha_lord} signifies {maha_sig}.{maha_special}"
    )

    # ── Antardasha summary ────────────────────────────────────────────────
    antar_summary = None
    if antar_eval and antar_lord:
        antar_houses = antar_eval["owned_houses"]
        antar_house_desc = " and ".join(
            f"the {_ordinal(h)} house ({HOUSE_SIGNIFICATIONS[h]})"
            for h in antar_houses
        )
        antar_sig = PLANET_SIGNIFICATIONS.get(antar_lord, antar_lord)
        antar_special = ""
        if antar_eval["is_yoga_karaka"]:
            antar_special = (
                f" The Yoga Karaka Antardasha within this Mahadasha triggers "
                f"the highest Raja Yoga results of the entire Dasha cycle."
            )
        elif antar_eval["is_maraka"]:
            antar_special = (
                f" As a Maraka sub-lord, this Antardasha period warrants "
                f"heightened attention to health and longevity matters."
            )

        antar_summary = (
            f"{antar_lord} Antardasha is {antar_nat.value} for {lagna.value} Lagna. "
            f"It activates {antar_house_desc if antar_house_desc else 'shadow-planet themes'}. "
            f"{antar_lord} signifies {antar_sig}.{antar_special}"
        )

    # ── Combined interpretation ───────────────────────────────────────────
    if antar_lord:
        combined = _combined_text(
            lagna, maha_lord, antar_lord,
            maha_eval, antar_eval, quality
        )
    else:
        combined = (
            f"During the {maha_lord} Mahadasha, life events revolve around "
            f"the themes signified by its lordship: "
            f"{', '.join(HOUSE_SIGNIFICATIONS[h] for h in maha_houses) if maha_houses else maha_sig}. "
            f"The overall quality is {quality}."
        )

    # ── Areas activated ───────────────────────────────────────────────────
    active_houses = set(maha_houses)
    if antar_eval:
        active_houses |= set(antar_eval["owned_houses"])
    areas = [HOUSE_SIGNIFICATIONS[h] for h in sorted(active_houses)]

    # ── Cautions ──────────────────────────────────────────────────────────
    cautions = []
    if maha_eval["is_maraka"]:
        cautions.append(f"{maha_lord} is a Maraka lord — monitor health, especially in later life.")
    if antar_eval and antar_eval["is_maraka"]:
        cautions.append(f"{antar_lord} Antardasha is a Maraka sub-period — exercise caution.")
    if 6 in maha_houses or (antar_eval and 6 in antar_eval["owned_houses"]):
        cautions.append("6th house activation — possible health issues, legal disputes, or debts.")
    if 8 in maha_houses or (antar_eval and 8 in antar_eval["owned_houses"]):
        cautions.append("8th house activation — sudden events, hidden matters, or transformations.")
    if 12 in maha_houses or (antar_eval and 12 in antar_eval["owned_houses"]):
        cautions.append("12th house activation — possible losses, foreign travel, or spiritual retreat.")

    return {
        "quality":         quality,
        "quality_color":   quality_color,
        "maha_summary":    maha_summary,
        "antar_summary":   antar_summary,
        "combined":        combined,
        "areas_activated": areas,
        "cautions":        cautions,
    }


def _combined_text(
    lagna: Sign,
    maha_lord: str, antar_lord: str,
    maha_eval: dict, antar_eval: dict,
    quality: str,
) -> str:
    maha_nat  = maha_eval["functional_nature"]
    antar_nat = antar_eval["functional_nature"]

    if maha_eval["is_yoga_karaka"] and antar_eval["is_yoga_karaka"]:
        return (
            f"This is the most powerful dasha combination possible for {lagna.value} Lagna. "
            f"Both {maha_lord} (Mahadasha) and {antar_lord} (Antardasha) are Yoga Karakas — "
            f"expect peak career advancement, recognition, and prosperity during this window. "
            f"Decisions made now have lasting positive consequences."
        )

    if maha_eval["is_yoga_karaka"]:
        if antar_eval["is_maraka"]:
            return (
                f"The {maha_lord} Yoga Karaka Mahadasha promises broad prosperity, but the "
                f"{antar_lord} Antardasha (a Maraka lord) introduces health-related interruptions "
                f"or losses during this sub-period. Enjoy the Raja Yoga period while protecting "
                f"wellbeing."
            )
        return (
            f"The Yoga Karaka {maha_lord} Mahadasha elevates the {antar_lord} Antardasha's "
            f"themes considerably. Even if {antar_lord} is not inherently auspicious for "
            f"{lagna.value} Lagna, the Yoga Karaka umbrella ensures a broadly positive period. "
            f"Focus especially on the {_ordinal(maha_eval['trikona_houses'][0])} house themes."
        )

    if maha_nat == FunctionalNature.INAUSPICIOUS and antar_nat == FunctionalNature.INAUSPICIOUS:
        return (
            f"Both {maha_lord} and {antar_lord} are functionally inauspicious for "
            f"{lagna.value} Lagna. This sub-period may bring difficulties related to "
            f"{', '.join(HOUSE_SIGNIFICATIONS[h] for h in antar_eval['owned_houses']) or 'general matters'}. "
            f"Avoid major decisions; focus on spiritual practice and consolidation."
        )

    if maha_nat in (FunctionalNature.MARAKA,) and antar_nat in (FunctionalNature.MARAKA,):
        return (
            f"Both {maha_lord} (Mahadasha) and {antar_lord} (Antardasha) are Maraka lords "
            f"for {lagna.value} Lagna. In old age, this combination is the primary indicator "
            f"of death in classical Jyotish. In younger years, it may manifest as severe illness, "
            f"major loss, or a profound life crisis. Consult a qualified astrologer for timing."
        )

    # General case
    quality_adj = {
        "gold":   "an exceptionally favourable",
        "indigo": "a broadly positive",
        "ochre":  "a mixed",
        "red":    "a challenging",
    }.get(
        "gold" if "Extraordinary" in quality or "Highly" in quality
        else "indigo" if "Good" in quality or "Positive" in quality or "Auspicious" in quality
        else "red" if "Difficult" in quality or "Critical" in quality or "Very Chall" in quality
        else "ochre", "ochre"
    )

    return (
        f"{maha_lord} Mahadasha / {antar_lord} Antardasha is {quality_adj} period "
        f"for {lagna.value} Lagna natives. "
        f"The Mahadasha lord ({maha_nat.value}) sets the overall tone, while the "
        f"Antardasha lord ({antar_nat.value}) colours the sub-period's specific events. "
        f"Key life areas activated: {', '.join(HOUSE_SIGNIFICATIONS[h] for h in (set(maha_eval['owned_houses']) | set(antar_eval['owned_houses'])) if h in HOUSE_SIGNIFICATIONS) or 'general life themes'}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Lagna narrative
# ─────────────────────────────────────────────────────────────────────────────

def interpret_lagna_profile(lagna: Sign, ascendant_profile: dict) -> str:
    """
    Return a concise narrative paragraph summarising the Lagna's planetary
    landscape from a Laghu Parashari perspective.
    """
    yk    = ascendant_profile.get("yoga_karaka", [])
    aus   = ascendant_profile.get("auspicious",  [])
    inas  = ascendant_profile.get("inauspicious",[])
    mara  = ascendant_profile.get("maraka",      [])
    lord  = ascendant_profile.get("lagna_lord",  "")

    yk_str   = ", ".join(p.value if hasattr(p, "value") else p for p in yk)
    aus_str  = ", ".join(p.value if hasattr(p, "value") else p for p in aus)
    inas_str = ", ".join(p.value if hasattr(p, "value") else p for p in inas)
    mara_str = ", ".join(p.value if hasattr(p, "value") else p for p in mara)
    lord_str = lord.value if hasattr(lord, "value") else lord

    parts = [
        f"For {lagna.value} Lagna, the Lagna lord is {lord_str}, "
        f"which is always auspicious by definition."
    ]
    if yk:
        parts.append(
            f"{yk_str} {'is' if len(yk)==1 else 'are'} the Yoga Karaka "
            f"{'planet' if len(yk)==1 else 'planets'} — "
            f"ruling both a Kendra and a Trikona simultaneously. "
            f"{'Its' if len(yk)==1 else 'Their'} Dasha periods are the most rewarding of the 120-year cycle."
        )
    if aus:
        parts.append(
            f"The auspicious planets are {aus_str}, "
            f"whose Dashas generally bring positive results in the areas of their house lordship."
        )
    if inas:
        parts.append(
            f"The functionally inauspicious planets are {inas_str} — "
            f"their Dashas tend to bring obstacles, delays, or struggles in their signified areas."
        )
    if mara:
        parts.append(
            f"The primary Maraka {'lord is' if len(mara)==1 else 'lords are'} {mara_str}. "
            f"In advanced age, their combined Dasha/Antardasha periods are the classical "
            f"indicators of life's end per Laghu Parashari."
        )

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def _ordinal(n: int) -> str:
    suf = {1:"1st",2:"2nd",3:"3rd"}.get(n, f"{n}th")
    return suf
