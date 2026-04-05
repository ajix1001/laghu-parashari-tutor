"""
Yoga Karaka & Maraka Identifier Engine — Laghu Parashari

Implements:
  1. Raja Yoga detection — triggered when a kendra lord and a trikona lord
     form a relationship (Sambandha):
       a. Mutual conjunction (same house)
       b. Mutual aspect (7th aspect minimum; full aspects for Mars/Jupiter/Saturn)
       c. Sign exchange (Parivartana Yoga)
       d. A single planet is lord of both a kendra AND a trikona (Yoga Karaka)

  2. Maraka identification:
       • Houses of longevity: 3rd (Ayu Bhava short) and 8th (Ayu Bhava)
       • 12th from each longevity house = 2nd (12th from 3rd) and 7th (12th from 8th)
       • Lords of 2nd and 7th are primary Marakas
       • A natural malefic placed in the 2nd or 7th house also acts as a Maraka

  3. Planetary relationship (Sambandha) types supported:
       CONJUNCTION, MUTUAL_ASPECT, EXCHANGE, YOGA_KARAKA_SINGLE_PLANET
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field

from data.constants import (
    Planet,
    Sign,
    TRIKONA_HOUSES,
    KENDRA_HOUSES,
    MARAKA_HOUSES,
    NATURAL_MALEFICS,
)
from engines.lordship_engine import (
    get_house_lords,
    get_planet_houses,
    evaluate_all_planets,
    FunctionalNature,
)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class SambandhaType(str, Enum):
    CONJUNCTION              = "Conjunction (same house)"
    MUTUAL_ASPECT            = "Mutual Aspect"
    EXCHANGE                 = "Sign Exchange (Parivartana)"
    YOGA_KARAKA_SINGLE       = "Single Planet Yoga Karaka (owns kendra + trikona)"


class YogaType(str, Enum):
    RAJA_YOGA   = "Raja Yoga"
    YOGA_KARAKA = "Yoga Karaka"


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RajaYoga:
    yoga_type:       YogaType
    sambandha_type:  SambandhaType
    kendra_lord:     Planet
    kendra_house:    int
    trikona_lord:    Planet
    trikona_house:   int
    description:     str


@dataclass
class MarakaResult:
    planet:          Planet
    maraka_houses:   list[int]   # 2nd or 7th houses owned
    is_natural_malefic: bool
    placed_in_maraka_house: bool  # True if the planet is posited in 2nd/7th
    severity:        str          # "Primary", "Secondary"
    description:     str


@dataclass
class ChartInput:
    """Minimal chart data needed for yoga / maraka analysis."""
    lagna:           Sign
    # Planetary positions: {Planet: house_number (1-12)}
    planet_positions: dict[Planet, int] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Sambandha (relationship) detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _planets_in_conjunction(
    p1: Planet, p2: Planet, positions: dict[Planet, int]
) -> bool:
    """True if both planets occupy the same house."""
    if p1 not in positions or p2 not in positions:
        return False
    return positions[p1] == positions[p2]


def _planets_in_mutual_aspect(
    p1: Planet, p2: Planet, positions: dict[Planet, int]
) -> bool:
    """
    True if p1 and p2 are in mutual 7th aspect (180° apart in house terms),
    OR if one of them has a special aspect covering the other's house.

    Special aspects (Laghu Parashari / standard Jyotish):
      Mars    : 4th, 7th, 8th from itself
      Jupiter : 5th, 7th, 9th from itself
      Saturn  : 3rd, 7th, 10th from itself
    All planets: 7th aspect.
    """
    if p1 not in positions or p2 not in positions:
        return False

    h1 = positions[p1]
    h2 = positions[p2]

    def aspects(planet: Planet, from_house: int, to_house: int) -> bool:
        diff = ((to_house - from_house) % 12) + 1  # 1-12 counting
        standard = {7}
        special = {
            Planet.MARS:    {4, 7, 8},
            Planet.JUPITER: {5, 7, 9},
            Planet.SATURN:  {3, 7, 10},
        }
        valid = standard | special.get(planet, set())
        return diff in valid

    return aspects(p1, h1, h2) and aspects(p2, h2, h1)


def _planets_in_exchange(
    p1: Planet, p2: Planet,
    lagna: Sign,
    positions: dict[Planet, int],
) -> bool:
    """
    True if p1 is placed in a sign ruled by p2, and p2 is placed in a sign
    ruled by p1 (Parivartana Yoga / sign exchange).
    """
    if p1 not in positions or p2 not in positions:
        return False

    house_lords = get_house_lords(lagna)
    # Determine which planet rules each planet's occupied house
    h1_lord = house_lords.get(positions[p1])
    h2_lord = house_lords.get(positions[p2])

    return h1_lord == p2 and h2_lord == p1


# ─────────────────────────────────────────────────────────────────────────────
# Raja Yoga identifier
# ─────────────────────────────────────────────────────────────────────────────

def identify_raja_yogas(chart: ChartInput) -> list[RajaYoga]:
    """
    Detect all Raja Yogas for the given chart.

    A Raja Yoga forms when a kendra lord and a trikona lord have a Sambandha.
    The 1st house is both a kendra and a trikona; a planet that is solely
    lagna lord does not by itself form a Raja Yoga unless it also lords
    another kendra or trikona.
    """
    lagna     = chart.lagna
    positions = chart.planet_positions
    lords     = get_house_lords(lagna)

    yogas: list[RajaYoga] = []

    # Build sets: which planets lord which categories
    kendra_lords: dict[Planet, list[int]] = {}
    trikona_lords: dict[Planet, list[int]] = {}

    for house, planet in lords.items():
        if planet in (Planet.RAHU, Planet.KETU):
            continue
        if house in KENDRA_HOUSES and house != 1:
            kendra_lords.setdefault(planet, []).append(house)
        if house in TRIKONA_HOUSES and house != 1:
            trikona_lords.setdefault(planet, []).append(house)

    # ── Case 1: Single planet is both a kendra lord and a trikona lord ────
    for planet in set(kendra_lords) & set(trikona_lords):
        yogas.append(RajaYoga(
            yoga_type=YogaType.YOGA_KARAKA,
            sambandha_type=SambandhaType.YOGA_KARAKA_SINGLE,
            kendra_lord=planet,
            kendra_house=kendra_lords[planet][0],
            trikona_lord=planet,
            trikona_house=trikona_lords[planet][0],
            description=(
                f"{planet.value} is a Yoga Karaka for {lagna.value} Lagna — "
                f"it lords kendra house(s) {kendra_lords[planet]} AND "
                f"trikona house(s) {trikona_lords[planet]}. "
                f"Its Dasha bestows the highest Raja Yoga results."
            ),
        ))

    # ── Case 2: Different kendra lord and trikona lord in Sambandha ───────
    checked: set[frozenset] = set()
    for kp, k_houses in kendra_lords.items():
        for tp, t_houses in trikona_lords.items():
            if kp == tp:
                continue
            pair = frozenset({kp, tp})
            if pair in checked:
                continue
            checked.add(pair)

            sambandha = None

            if _planets_in_conjunction(kp, tp, positions):
                sambandha = SambandhaType.CONJUNCTION
            elif _planets_in_mutual_aspect(kp, tp, positions):
                sambandha = SambandhaType.MUTUAL_ASPECT
            elif _planets_in_exchange(kp, tp, lagna, positions):
                sambandha = SambandhaType.EXCHANGE

            if sambandha:
                yogas.append(RajaYoga(
                    yoga_type=YogaType.RAJA_YOGA,
                    sambandha_type=sambandha,
                    kendra_lord=kp,
                    kendra_house=k_houses[0],
                    trikona_lord=tp,
                    trikona_house=t_houses[0],
                    description=(
                        f"Raja Yoga: {kp.value} (lord of kendra house {k_houses[0]}) "
                        f"and {tp.value} (lord of trikona house {t_houses[0]}) "
                        f"are in {sambandha.value} for {lagna.value} Lagna."
                    ),
                ))

    return yogas


# ─────────────────────────────────────────────────────────────────────────────
# Maraka identifier
# ─────────────────────────────────────────────────────────────────────────────

def identify_marakas(chart: ChartInput) -> list[MarakaResult]:
    """
    Identify Maraka planets for the given chart.

    Primary Marakas: lords of 2nd and 7th houses.
    Secondary Marakas: natural malefics posited in 2nd or 7th houses.

    The 8th and 3rd are houses of longevity (Ayu Bhava / Sahaja Bhava).
    Their 12th houses (2nd and 7th respectively) are the Maraka sthanas.
    """
    lagna     = chart.lagna
    positions = chart.planet_positions
    lords     = get_house_lords(lagna)
    marakas:  list[MarakaResult] = []
    seen:     set[Planet] = set()

    # ── Primary Marakas: lords of 2nd and 7th ─────────────────────────────
    for house in (2, 7):
        planet = lords.get(house)
        if planet is None or planet in (Planet.RAHU, Planet.KETU):
            continue

        # Find all maraka houses this planet owns
        owned_maraka = [
            h for h, p in lords.items() if p == planet and h in MARAKA_HOUSES
        ]

        placed_in_maraka = positions.get(planet) in MARAKA_HOUSES

        severity = (
            "Primary Double Maraka" if len(owned_maraka) > 1
            else "Primary Maraka"
        )
        desc = (
            f"{planet.value} is the lord of {house}th house (Maraka Sthana) "
            f"for {lagna.value} Lagna. "
            f"{'Also owns the other Maraka house — double Maraka strength. ' if len(owned_maraka) > 1 else ''}"
            f"{'Posited in a Maraka house — heightened danger. ' if placed_in_maraka else ''}"
            f"Its Dasha/Antardasha can inflict death or severe health crises."
        )
        if planet not in seen:
            marakas.append(MarakaResult(
                planet=planet,
                maraka_houses=owned_maraka,
                is_natural_malefic=(planet in NATURAL_MALEFICS),
                placed_in_maraka_house=placed_in_maraka,
                severity=severity,
                description=desc,
            ))
            seen.add(planet)

    # ── Secondary Marakas: natural malefics placed in 2nd or 7th ──────────
    for planet, house in positions.items():
        if house not in MARAKA_HOUSES:
            continue
        if planet in (Planet.RAHU, Planet.KETU):
            continue
        if planet in seen:
            continue
        if planet in NATURAL_MALEFICS:
            marakas.append(MarakaResult(
                planet=planet,
                maraka_houses=[],
                is_natural_malefic=True,
                placed_in_maraka_house=True,
                severity="Secondary Maraka",
                description=(
                    f"{planet.value} is a natural malefic placed in the {house}th house "
                    f"(Maraka Sthana) for {lagna.value} Lagna — acts as a secondary Maraka."
                ),
            ))
            seen.add(planet)

    return marakas


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: full analysis for a chart
# ─────────────────────────────────────────────────────────────────────────────

def full_yoga_analysis(chart: ChartInput) -> dict:
    """
    Return both Raja Yoga and Maraka analysis plus functional planet summary.
    """
    raja_yogas = identify_raja_yogas(chart)
    marakas    = identify_marakas(chart)
    planet_eval = evaluate_all_planets(chart.lagna)

    return {
        "lagna":        chart.lagna,
        "raja_yogas":   [
            {
                "yoga_type":       y.yoga_type,
                "sambandha_type":  y.sambandha_type,
                "kendra_lord":     y.kendra_lord,
                "kendra_house":    y.kendra_house,
                "trikona_lord":    y.trikona_lord,
                "trikona_house":   y.trikona_house,
                "description":     y.description,
            }
            for y in raja_yogas
        ],
        "marakas": [
            {
                "planet":                m.planet,
                "maraka_houses":         m.maraka_houses,
                "is_natural_malefic":    m.is_natural_malefic,
                "placed_in_maraka_house":m.placed_in_maraka_house,
                "severity":              m.severity,
                "description":           m.description,
            }
            for m in marakas
        ],
        "planet_summary": {
            p.value: {
                "functional_nature": v["functional_nature"],
                "owned_houses":      v["owned_houses"],
                "is_yoga_karaka":    v["is_yoga_karaka"],
                "is_maraka":         v["is_maraka"],
                "strength_score":    v["strength_score"],
            }
            for p, v in planet_eval.items()
        },
    }
