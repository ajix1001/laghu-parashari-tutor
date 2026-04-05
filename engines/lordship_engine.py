"""
House Lordship (Bhavadhipati) Rule Engine — Laghu Parashari

Evaluates a planet's functional nature for a given ascendant by applying
the four canonical rules from the text:

  Rule A — Trikona lords (1, 5, 9) are always Shubha (auspicious).
  Rule B — Trishadaya lords (3, 6, 11) are always Ashubha (inauspicious).
  Rule C — Kendradhipati Dosha: natural benefics owning a kendra lose
            auspiciousness; natural malefics owning a kendra shed maleficence.
  Rule D — 8th lord is generally Ashubha, EXCEPT when the 8th lord is also
            the lagna lord (e.g., Mars for Aries, Venus for Libra).

Additional rules:
  • Lagna (1st house) lord is always auspicious — it is simultaneously a
    trikona AND a kendra lord; trikona nature dominates.
  • Yoga Karaka: a planet that is lord of both a kendra AND a trikona
    (exclusive of the 1st house counting as both) becomes a Yoga Karaka —
    the most powerful benefic for that lagna.
  • Maraka: 2nd and 7th lords are primary death-inflicters.
"""

from __future__ import annotations
from enum import Enum

from data.constants import (
    Planet,
    Sign,
    SIGNS_LIST,
    SIGN_RULERS,
    TRIKONA_HOUSES,
    KENDRA_HOUSES,
    TRISHADAYA_HOUSES,
    DUSTHANA_HOUSES,
    MARAKA_HOUSES,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class FunctionalNature(str, Enum):
    AUSPICIOUS     = "Auspicious"
    YOGA_KARAKA    = "Yoga Karaka"   # Most powerful auspicious
    INAUSPICIOUS   = "Inauspicious"
    MARAKA         = "Maraka"        # Death-inflicting
    NEUTRAL        = "Neutral"
    MIXED          = "Mixed"         # Conflicting lordships


# ─────────────────────────────────────────────────────────────────────────────
# House derivation
# ─────────────────────────────────────────────────────────────────────────────

def get_house_signs(lagna: Sign) -> dict[int, Sign]:
    """Return {house_number: sign} for the given ascendant (1-12)."""
    lagna_idx = SIGNS_LIST.index(lagna)
    return {
        house: SIGNS_LIST[(lagna_idx + house - 1) % 12]
        for house in range(1, 13)
    }


def get_house_lords(lagna: Sign) -> dict[int, Planet]:
    """Return {house_number: lord_planet} for the given ascendant."""
    signs = get_house_signs(lagna)
    return {house: SIGN_RULERS[sign] for house, sign in signs.items()}


def get_planet_houses(lagna: Sign, planet: Planet) -> list[int]:
    """Return all house numbers owned by planet for the given ascendant."""
    lords = get_house_lords(lagna)
    return [house for house, lord in lords.items() if lord == planet]


# ─────────────────────────────────────────────────────────────────────────────
# Core rule engine
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_planet(lagna: Sign, planet: Planet) -> dict:
    """
    Evaluate a planet's functional nature for the given ascendant.

    Returns
    -------
    {
        "planet":            Planet,
        "lagna":             Sign,
        "owned_houses":      list[int],
        "is_lagna_lord":     bool,
        "is_yoga_karaka":    bool,
        "is_maraka":         bool,
        "is_8th_lord":       bool,
        "trikona_houses":    list[int],   # owned trikona houses
        "kendra_houses":     list[int],   # owned kendra houses
        "trishadaya_houses": list[int],   # owned trishadaya houses
        "rules_applied":     list[str],   # human-readable rule log
        "functional_nature": FunctionalNature,
        "strength_score":    int,         # +ve = auspicious, -ve = inauspicious
        "interpretation":    str,
    }
    """
    owned = get_planet_houses(lagna, planet)
    rules_applied: list[str] = []
    score = 0  # positive = auspicious, negative = inauspicious

    is_lagna_lord     = 1 in owned
    trikona_owned     = [h for h in owned if h in TRIKONA_HOUSES]
    kendra_owned      = [h for h in owned if h in KENDRA_HOUSES]
    trishadaya_owned  = [h for h in owned if h in TRISHADAYA_HOUSES]
    dusthana_owned    = [h for h in owned if h in DUSTHANA_HOUSES]
    maraka_owned      = [h for h in owned if h in MARAKA_HOUSES]
    eighth_owned      = 8 in owned

    # ── Rule A: Trikona lordship ──────────────────────────────────────────
    if trikona_owned:
        score += 3 * len(trikona_owned)
        rules_applied.append(
            f"Rule A: Lords trikona house(s) {trikona_owned} — Shubha (+{3*len(trikona_owned)})."
        )

    # ── Rule B: Trishadaya lordship ───────────────────────────────────────
    if trishadaya_owned:
        score -= 2 * len(trishadaya_owned)
        rules_applied.append(
            f"Rule B: Lords trishadaya house(s) {trishadaya_owned} — Ashubha ({-2*len(trishadaya_owned)})."
        )

    # ── Rule C: Kendradhipati Dosha ───────────────────────────────────────
    # Kendra lords that are NOT the lagna lord (1st house is trikona too)
    pure_kendra_owned = [h for h in kendra_owned if h != 1]
    if pure_kendra_owned:
        if planet in NATURAL_BENEFICS:
            score -= 1 * len(pure_kendra_owned)
            rules_applied.append(
                f"Rule C: Natural benefic lords kendra(s) {pure_kendra_owned} — "
                f"Kendradhipati Dosha reduces beneficence ({-len(pure_kendra_owned)})."
            )
        elif planet in NATURAL_MALEFICS:
            score += 1 * len(pure_kendra_owned)
            rules_applied.append(
                f"Rule C: Natural malefic lords kendra(s) {pure_kendra_owned} — "
                f"Kendradhipati Dosha reduces maleficence (+{len(pure_kendra_owned)})."
            )

    # ── Rule D: 8th house lordship ────────────────────────────────────────
    if eighth_owned:
        if is_lagna_lord:
            rules_applied.append(
                "Rule D: 8th lord — but also lagna lord; 8th lordship does NOT afflict the lagna lord."
            )
        else:
            score -= 2
            rules_applied.append(
                "Rule D: 8th lord (not lagna lord) — Ashubha (-2)."
            )

    # ── Maraka assessment ─────────────────────────────────────────────────
    is_maraka = bool(maraka_owned)
    if is_maraka:
        rules_applied.append(
            f"Maraka: Lords 2nd/7th house(s) {maraka_owned} — primary death-inflicting planet."
        )
        score -= 1  # mild penalty; Maraka is a separate functional category

    # ── Yoga Karaka check ─────────────────────────────────────────────────
    # A planet must own at least one kendra AND at least one trikona
    # The 1st house counts as both but is the lagna lord — a pure Yoga Karaka
    # owns a non-1st kendra + a non-1st trikona (5th or 9th)
    trikona_non_lagna = [h for h in trikona_owned if h != 1]
    kendra_non_lagna  = [h for h in kendra_owned  if h != 1]
    is_yoga_karaka = bool(trikona_non_lagna) and bool(kendra_non_lagna)
    if is_yoga_karaka:
        score += 3  # Yoga Karaka bonus
        rules_applied.append(
            f"Yoga Karaka: Lords kendra {kendra_non_lagna} AND trikona {trikona_non_lagna} — "
            f"most powerful benefic for this lagna (+3)."
        )

    # ── Lagna lord override ───────────────────────────────────────────────
    if is_lagna_lord:
        score = max(score, 2)  # Lagna lord is always at least modestly auspicious
        rules_applied.append("Lagna lord override: always auspicious (score floored at 2).")

    # ── Classify final nature ─────────────────────────────────────────────
    if is_yoga_karaka:
        nature = FunctionalNature.YOGA_KARAKA
    elif score >= 3:
        nature = FunctionalNature.AUSPICIOUS
    elif score > 0:
        nature = FunctionalNature.MIXED if is_maraka else FunctionalNature.AUSPICIOUS
    elif score == 0:
        nature = FunctionalNature.NEUTRAL
    elif score >= -2:
        nature = FunctionalNature.MIXED if trikona_owned else FunctionalNature.INAUSPICIOUS
    else:
        nature = FunctionalNature.INAUSPICIOUS

    # Maraka overrides Neutral/Mixed when there is no trikona lord benefit
    if is_maraka and not trikona_owned and nature in (FunctionalNature.NEUTRAL, FunctionalNature.MIXED):
        nature = FunctionalNature.MARAKA

    interpretation = _build_interpretation(
        planet, lagna, nature, owned, is_yoga_karaka, is_maraka, rules_applied
    )

    return {
        "planet":            planet,
        "lagna":             lagna,
        "owned_houses":      owned,
        "is_lagna_lord":     is_lagna_lord,
        "is_yoga_karaka":    is_yoga_karaka,
        "is_maraka":         is_maraka,
        "is_8th_lord":       eighth_owned,
        "trikona_houses":    trikona_owned,
        "kendra_houses":     kendra_owned,
        "trishadaya_houses": trishadaya_owned,
        "rules_applied":     rules_applied,
        "functional_nature": nature,
        "strength_score":    score,
        "interpretation":    interpretation,
    }


def evaluate_all_planets(lagna: Sign) -> dict[Planet, dict]:
    """Return evaluate_planet() results for all 9 Jyotish planets."""
    planets = [
        Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
        Planet.JUPITER, Planet.VENUS, Planet.SATURN,
        Planet.RAHU, Planet.KETU,
    ]
    # Rahu/Ketu don't own signs in classical Jyotish; skip house ownership
    result = {}
    for p in planets:
        if p in (Planet.RAHU, Planet.KETU):
            result[p] = {
                "planet": p,
                "lagna": lagna,
                "owned_houses": [],
                "is_lagna_lord": False,
                "is_yoga_karaka": False,
                "is_maraka": False,
                "is_8th_lord": False,
                "trikona_houses": [],
                "kendra_houses": [],
                "trishadaya_houses": [],
                "rules_applied": ["Rahu/Ketu are shadow planets; functional nature determined by sign/house placement."],
                "functional_nature": FunctionalNature.NEUTRAL,
                "strength_score": 0,
                "interpretation": (
                    f"{p.value} is a shadow planet (Chhaya Graha). Its results derive "
                    "from the sign it occupies and its dispositor, not from sign lordship."
                ),
            }
        else:
            result[p] = evaluate_planet(lagna, p)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Interpretation builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_interpretation(
    planet: Planet,
    lagna: Sign,
    nature: FunctionalNature,
    owned_houses: list[int],
    is_yoga_karaka: bool,
    is_maraka: bool,
    rules: list[str],
) -> str:
    parts = [
        f"For {lagna.value} Lagna, {planet.value} owns house(s) {owned_houses}.",
        f"Functional nature: {nature.value}.",
    ]
    if is_yoga_karaka:
        parts.append(
            f"{planet.value} is a Yoga Karaka — the most potent auspicious planet "
            f"for {lagna.value} Lagna. Its Dasha grants Raja Yoga results."
        )
    if is_maraka:
        parts.append(
            f"{planet.value} is a Maraka (death-inflicting) lord. "
            "Exercise caution during its Dasha/Antardasha, especially in old age."
        )
    return " ".join(parts)
