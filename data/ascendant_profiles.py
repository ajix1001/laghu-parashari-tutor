"""
Ascendant-specific planet classifications for all 12 lagnas.

Rules applied per Laghu Parashari:
  1. Trikona lords (1, 5, 9) are always auspicious (Shubha).
  2. Trishadaya lords (3, 6, 11) are inauspicious (Ashubha).
  3. Kendradhipati Dosha: natural benefics owning a kendra lose beneficence;
     natural malefics owning a kendra lose maleficence (become more neutral/good).
  4. 8th lord is inauspicious UNLESS it is also the lagna lord.
  5. 2nd and 7th lords are primary Marakas.
  6. A planet ruling both a kendra AND a trikona is a Yoga Karaka.
  7. Lagna lord is always auspicious regardless of other lordship.
"""

from data.constants import Planet, Sign

# ─────────────────────────────────────────────────────────────────────────────
# Schema for each ascendant profile
# Each entry in ASCENDANT_PROFILES maps a lagna Sign to a dict with:
#   auspicious   — planets that promote good results
#   inauspicious — planets that give bad results
#   yoga_karaka  — planet(s) simultaneously ruling kendra + trikona
#   maraka       — primary death-inflicting lords (2nd and 7th house lords)
#   neutral      — planets with mixed/neutral results
#   notes        — key textual observations from Laghu Parashari
# ─────────────────────────────────────────────────────────────────────────────

ASCENDANT_PROFILES: dict[Sign, dict] = {

    # ── 1. ARIES (Mesha) ──────────────────────────────────────────────────
    Sign.ARIES: {
        "lagna_lord": Planet.MARS,
        "house_lords": {
            1:  Planet.MARS,    # Aries
            2:  Planet.VENUS,   # Taurus
            3:  Planet.MERCURY, # Gemini
            4:  Planet.MOON,    # Cancer
            5:  Planet.SUN,     # Leo
            6:  Planet.MERCURY, # Virgo
            7:  Planet.VENUS,   # Libra
            8:  Planet.MARS,    # Scorpio
            9:  Planet.JUPITER, # Sagittarius
            10: Planet.SATURN,  # Capricorn
            11: Planet.SATURN,  # Aquarius
            12: Planet.JUPITER, # Pisces
        },
        "auspicious":   [Planet.SUN, Planet.MARS, Planet.JUPITER],
        "inauspicious": [Planet.MERCURY, Planet.VENUS, Planet.SATURN],
        "yoga_karaka":  [],  # No single planet lords both kendra and trikona
        "maraka":       [Planet.VENUS],  # 2nd & 7th lord; Venus is primary/double Maraka
        "neutral":      [Planet.MOON],
        "notes": (
            "Sun is the 5th (trikona) lord — highly auspicious. "
            "Jupiter rules 9th (trikona) and 12th — net auspicious due to 9th. "
            "Mars is lagna lord; also 8th lord, but 8th lordship does not afflict the lagna lord. "
            "Mercury rules both 3rd and 6th (dual trishadaya) — strongly inauspicious. "
            "Venus rules 2nd and 7th — double Maraka; primary killer. "
            "Saturn rules 10th (kendra) and 11th (trishadaya) — mixed but net inauspicious. "
            "Moon rules 4th (kendra); as a natural benefic it suffers Kendradhipati Dosha."
        ),
    },

    # ── 2. TAURUS (Vrishabha) ────────────────────────────────────────────
    Sign.TAURUS: {
        "lagna_lord": Planet.VENUS,
        "house_lords": {
            1:  Planet.VENUS,   # Taurus
            2:  Planet.MERCURY, # Gemini
            3:  Planet.MOON,    # Cancer
            4:  Planet.SUN,     # Leo
            5:  Planet.MERCURY, # Virgo
            6:  Planet.VENUS,   # Libra
            7:  Planet.MARS,    # Scorpio
            8:  Planet.JUPITER, # Sagittarius
            9:  Planet.SATURN,  # Capricorn
            10: Planet.SATURN,  # Aquarius
            11: Planet.JUPITER, # Pisces
            12: Planet.MARS,    # Aries
        },
        "auspicious":   [Planet.SATURN, Planet.SUN],
        "inauspicious": [Planet.JUPITER, Planet.VENUS, Planet.MOON],
        "yoga_karaka":  [Planet.SATURN],  # Rules 9th (trikona) + 10th (kendra)
        "maraka":       [Planet.MARS],    # 7th lord; also Mercury (2nd lord)
        "neutral":      [Planet.MERCURY],
        "notes": (
            "Saturn rules 9th (trikona) AND 10th (kendra) — prime Yoga Karaka. "
            "Sun rules 4th (kendra); as natural malefic it sheds maleficence — auspicious. "
            "Jupiter rules 8th and 11th — inauspicious (8th lord + trishadaya). "
            "Moon rules 3rd (trishadaya) — inauspicious. "
            "Venus is lagna lord but also 6th — mixed, but lagna lordship dominates. "
            "Mercury rules 2nd (maraka) + 5th (trikona) — mixed; 5th gives good results. "
            "Mars rules 7th (kendra, Maraka) + 12th — primary Maraka."
        ),
    },

    # ── 3. GEMINI (Mithuna) ──────────────────────────────────────────────
    Sign.GEMINI: {
        "lagna_lord": Planet.MERCURY,
        "house_lords": {
            1:  Planet.MERCURY, # Gemini
            2:  Planet.MOON,    # Cancer
            3:  Planet.SUN,     # Leo
            4:  Planet.MERCURY, # Virgo
            5:  Planet.VENUS,   # Libra
            6:  Planet.MARS,    # Scorpio
            7:  Planet.JUPITER, # Sagittarius
            8:  Planet.SATURN,  # Capricorn
            9:  Planet.SATURN,  # Aquarius
            10: Planet.JUPITER, # Pisces
            11: Planet.MARS,    # Aries
            12: Planet.VENUS,   # Taurus
        },
        "auspicious":   [Planet.VENUS, Planet.SATURN],
        "inauspicious": [Planet.SUN, Planet.MARS, Planet.JUPITER],
        "yoga_karaka":  [],
        "maraka":       [Planet.JUPITER, Planet.MOON],
        "neutral":      [Planet.MERCURY],
        "notes": (
            "Venus rules 5th (trikona) + 12th — net auspicious for trikona lordship. "
            "Saturn rules 8th and 9th — 9th trikona partially redeems 8th lordship. "
            "Jupiter rules 7th (kendra, Maraka) + 10th (kendra) — Kendradhipati Dosha + Maraka. "
            "Mars rules 6th + 11th (dual trishadaya) — strongly inauspicious. "
            "Sun rules 3rd (trishadaya) — inauspicious. "
            "Moon rules 2nd — primary Maraka. "
            "Mercury is lagna lord + 4th (kendra) — Kendradhipati affects it but lagna lordship holds."
        ),
    },

    # ── 4. CANCER (Karka) ────────────────────────────────────────────────
    Sign.CANCER: {
        "lagna_lord": Planet.MOON,
        "house_lords": {
            1:  Planet.MOON,    # Cancer
            2:  Planet.SUN,     # Leo
            3:  Planet.MERCURY, # Virgo
            4:  Planet.VENUS,   # Libra
            5:  Planet.MARS,    # Scorpio
            6:  Planet.JUPITER, # Sagittarius
            7:  Planet.SATURN,  # Capricorn
            8:  Planet.SATURN,  # Aquarius
            9:  Planet.JUPITER, # Pisces
            10: Planet.MARS,    # Aries
            11: Planet.VENUS,   # Taurus
            12: Planet.MERCURY, # Gemini
        },
        "auspicious":   [Planet.MARS, Planet.MOON, Planet.JUPITER],
        "inauspicious": [Planet.MERCURY, Planet.SATURN],
        "yoga_karaka":  [Planet.MARS],  # Rules 5th (trikona) + 10th (kendra)
        "maraka":       [Planet.SUN, Planet.SATURN],
        "neutral":      [Planet.VENUS],
        "notes": (
            "Mars rules 5th (trikona) AND 10th (kendra) — supreme Yoga Karaka. "
            "Moon is lagna lord — inherently auspicious. "
            "Jupiter rules 6th (trishadaya) + 9th (trikona) — 9th trikona is stronger; mixed but auspicious. "
            "Saturn rules 7th (Maraka) + 8th — doubly afflicted; primary Maraka. "
            "Mercury rules 3rd (trishadaya) + 12th — very inauspicious. "
            "Sun rules 2nd — Maraka. "
            "Venus rules 4th (kendra) + 11th (trishadaya) — Kendradhipati Dosha; mixed."
        ),
    },

    # ── 5. LEO (Simha) ───────────────────────────────────────────────────
    Sign.LEO: {
        "lagna_lord": Planet.SUN,
        "house_lords": {
            1:  Planet.SUN,     # Leo
            2:  Planet.MERCURY, # Virgo
            3:  Planet.VENUS,   # Libra
            4:  Planet.MARS,    # Scorpio
            5:  Planet.JUPITER, # Sagittarius
            6:  Planet.SATURN,  # Capricorn
            7:  Planet.SATURN,  # Aquarius
            8:  Planet.JUPITER, # Pisces
            9:  Planet.MARS,    # Aries
            10: Planet.VENUS,   # Taurus
            11: Planet.MERCURY, # Gemini
            12: Planet.MOON,    # Cancer
        },
        "auspicious":   [Planet.SUN, Planet.MARS, Planet.JUPITER],
        "inauspicious": [Planet.MERCURY, Planet.SATURN, Planet.VENUS],
        "yoga_karaka":  [Planet.MARS],  # Rules 4th (kendra) + 9th (trikona)
        "maraka":       [Planet.MERCURY, Planet.SATURN],
        "neutral":      [Planet.MOON],
        "notes": (
            "Mars rules 4th (kendra) AND 9th (trikona) — excellent Yoga Karaka. "
            "Sun is lagna lord — auspicious. "
            "Jupiter rules 5th (trikona) + 8th — 5th lordship dominates; net auspicious. "
            "Saturn rules 6th (trishadaya) + 7th (Maraka) — inauspicious and Maraka. "
            "Mercury rules 2nd (Maraka) + 11th (trishadaya) — Maraka + inauspicious. "
            "Venus rules 3rd (trishadaya) + 10th (kendra) — Kendradhipati; net inauspicious. "
            "Moon rules 12th — house of loss."
        ),
    },

    # ── 6. VIRGO (Kanya) ─────────────────────────────────────────────────
    Sign.VIRGO: {
        "lagna_lord": Planet.MERCURY,
        "house_lords": {
            1:  Planet.MERCURY, # Virgo
            2:  Planet.VENUS,   # Libra
            3:  Planet.MARS,    # Scorpio
            4:  Planet.JUPITER, # Sagittarius
            5:  Planet.SATURN,  # Capricorn
            6:  Planet.SATURN,  # Aquarius
            7:  Planet.JUPITER, # Pisces
            8:  Planet.MARS,    # Aries
            9:  Planet.VENUS,   # Taurus
            10: Planet.MERCURY, # Gemini
            11: Planet.MOON,    # Cancer
            12: Planet.SUN,     # Leo
        },
        "auspicious":   [Planet.VENUS, Planet.MERCURY],
        "inauspicious": [Planet.MARS, Planet.JUPITER, Planet.MOON, Planet.SUN],
        "yoga_karaka":  [],
        "maraka":       [Planet.VENUS, Planet.JUPITER],
        "neutral":      [Planet.SATURN],
        "notes": (
            "Venus rules 2nd (Maraka) + 9th (trikona) — 9th trikona is powerful; net auspicious, "
            "but also a Maraka — must be watched during its dasha. "
            "Mercury is lagna lord + 10th (kendra) — Kendradhipati Dosha applies but lagna holds. "
            "Saturn rules 5th (trikona) + 6th (trishadaya) — 5th trikona is stronger; mixed. "
            "Jupiter rules 4th (kendra) + 7th (kendra, Maraka) — Kendradhipati + Maraka; very inauspicious. "
            "Mars rules 3rd (trishadaya) + 8th — very inauspicious. "
            "Moon rules 11th (trishadaya) — inauspicious. "
            "Sun rules 12th — house of loss."
        ),
    },

    # ── 7. LIBRA (Tula) ──────────────────────────────────────────────────
    Sign.LIBRA: {
        "lagna_lord": Planet.VENUS,
        "house_lords": {
            1:  Planet.VENUS,   # Libra
            2:  Planet.MARS,    # Scorpio
            3:  Planet.JUPITER, # Sagittarius
            4:  Planet.SATURN,  # Capricorn
            5:  Planet.SATURN,  # Aquarius
            6:  Planet.JUPITER, # Pisces
            7:  Planet.MARS,    # Aries
            8:  Planet.VENUS,   # Taurus
            9:  Planet.MERCURY, # Gemini
            10: Planet.MOON,    # Cancer
            11: Planet.SUN,     # Leo
            12: Planet.MERCURY, # Virgo
        },
        "auspicious":   [Planet.SATURN, Planet.MERCURY, Planet.VENUS],
        "inauspicious": [Planet.JUPITER, Planet.SUN],
        "yoga_karaka":  [Planet.SATURN],  # Rules 4th (kendra) + 5th (trikona)
        "maraka":       [Planet.MARS],    # Rules 2nd + 7th — double Maraka
        "neutral":      [Planet.MOON],
        "notes": (
            "Saturn rules 4th (kendra) AND 5th (trikona) — supreme Yoga Karaka. "
            "Venus is lagna lord + 8th — lagna lordship prevails; 8th does not harm lagna lord. "
            "Mercury rules 9th (trikona) + 12th — 9th trikona dominates; auspicious. "
            "Mars rules 2nd + 7th — double Maraka; primary killer. "
            "Jupiter rules 3rd + 6th (dual trishadaya) — very inauspicious. "
            "Sun rules 11th (trishadaya) — inauspicious. "
            "Moon rules 10th (kendra); natural benefic suffers Kendradhipati Dosha."
        ),
    },

    # ── 8. SCORPIO (Vrishchika) ──────────────────────────────────────────
    Sign.SCORPIO: {
        "lagna_lord": Planet.MARS,
        "house_lords": {
            1:  Planet.MARS,    # Scorpio
            2:  Planet.JUPITER, # Sagittarius
            3:  Planet.SATURN,  # Capricorn
            4:  Planet.SATURN,  # Aquarius
            5:  Planet.JUPITER, # Pisces
            6:  Planet.MARS,    # Aries
            7:  Planet.VENUS,   # Taurus
            8:  Planet.MERCURY, # Gemini
            9:  Planet.MOON,    # Cancer
            10: Planet.SUN,     # Leo
            11: Planet.MERCURY, # Virgo
            12: Planet.VENUS,   # Libra
        },
        "auspicious":   [Planet.MOON, Planet.SUN, Planet.MARS, Planet.JUPITER],
        "inauspicious": [Planet.MERCURY, Planet.VENUS],
        "yoga_karaka":  [],
        "maraka":       [Planet.VENUS, Planet.JUPITER],
        "neutral":      [Planet.SATURN],
        "notes": (
            "Moon rules 9th (trikona) — auspicious. "
            "Sun rules 10th (kendra); as natural malefic it sheds maleficence via Kendradhipati — auspicious. "
            "Mars is lagna lord; also 6th lord — lagna lordship dominates. "
            "Jupiter rules 2nd (Maraka) + 5th (trikona) — 5th trikona is positive; mixed but also Maraka. "
            "Venus rules 7th (kendra, Maraka) + 12th — primary Maraka. "
            "Mercury rules 8th + 11th (trishadaya) — inauspicious. "
            "Saturn rules 3rd (trishadaya) + 4th (kendra) — malefic in kendra loses maleficence; mixed."
        ),
    },

    # ── 9. SAGITTARIUS (Dhanu) ───────────────────────────────────────────
    Sign.SAGITTARIUS: {
        "lagna_lord": Planet.JUPITER,
        "house_lords": {
            1:  Planet.JUPITER, # Sagittarius
            2:  Planet.SATURN,  # Capricorn
            3:  Planet.SATURN,  # Aquarius
            4:  Planet.JUPITER, # Pisces
            5:  Planet.MARS,    # Aries
            6:  Planet.VENUS,   # Taurus
            7:  Planet.MERCURY, # Gemini
            8:  Planet.MOON,    # Cancer
            9:  Planet.SUN,     # Leo
            10: Planet.MERCURY, # Virgo
            11: Planet.VENUS,   # Libra
            12: Planet.MARS,    # Scorpio
        },
        "auspicious":   [Planet.SUN, Planet.MARS, Planet.JUPITER],
        "inauspicious": [Planet.VENUS, Planet.MERCURY, Planet.SATURN],
        "yoga_karaka":  [],
        "maraka":       [Planet.SATURN, Planet.MERCURY],
        "neutral":      [Planet.MOON],
        "notes": (
            "Sun rules 9th (trikona) — auspicious. "
            "Mars rules 5th (trikona) + 12th — 5th trikona dominates; net auspicious. "
            "Jupiter is lagna lord + 4th (kendra) — Kendradhipati Dosha; still auspicious as lagna lord. "
            "Saturn rules 2nd (Maraka) + 3rd (trishadaya) — Maraka + inauspicious. "
            "Mercury rules 7th (kendra, Maraka) + 10th (kendra) — Kendradhipati + Maraka; inauspicious. "
            "Venus rules 6th (trishadaya) + 11th (trishadaya) — dual trishadaya; very inauspicious. "
            "Moon rules 8th — inauspicious."
        ),
    },

    # ── 10. CAPRICORN (Makara) ───────────────────────────────────────────
    Sign.CAPRICORN: {
        "lagna_lord": Planet.SATURN,
        "house_lords": {
            1:  Planet.SATURN,  # Capricorn
            2:  Planet.SATURN,  # Aquarius
            3:  Planet.JUPITER, # Pisces
            4:  Planet.MARS,    # Aries
            5:  Planet.VENUS,   # Taurus
            6:  Planet.MERCURY, # Gemini
            7:  Planet.MOON,    # Cancer
            8:  Planet.SUN,     # Leo
            9:  Planet.MERCURY, # Virgo
            10: Planet.VENUS,   # Libra
            11: Planet.MARS,    # Scorpio
            12: Planet.JUPITER, # Sagittarius
        },
        "auspicious":   [Planet.VENUS, Planet.SATURN, Planet.MERCURY],
        "inauspicious": [Planet.JUPITER, Planet.SUN, Planet.MARS],
        "yoga_karaka":  [Planet.VENUS],  # Rules 5th (trikona) + 10th (kendra)
        "maraka":       [Planet.MOON],   # 7th lord; also Saturn (2nd lord, but lagna lord too)
        "neutral":      [Planet.MARS],
        "notes": (
            "Venus rules 5th (trikona) AND 10th (kendra) — supreme Yoga Karaka. "
            "Saturn is lagna lord + 2nd — lagna lordship dominates; also 2nd Maraka but protected. "
            "Mercury rules 6th (trishadaya) + 9th (trikona) — 9th partially redeems; mixed/auspicious. "
            "Moon rules 7th (kendra, Maraka) — primary Maraka; natural benefic with Kendradhipati. "
            "Jupiter rules 3rd (trishadaya) + 12th — inauspicious. "
            "Sun rules 8th — inauspicious. "
            "Mars rules 4th (kendra) + 11th (trishadaya); malefic in kendra is mixed."
        ),
    },

    # ── 11. AQUARIUS (Kumbha) ────────────────────────────────────────────
    Sign.AQUARIUS: {
        "lagna_lord": Planet.SATURN,
        "house_lords": {
            1:  Planet.SATURN,  # Aquarius
            2:  Planet.JUPITER, # Pisces
            3:  Planet.MARS,    # Aries
            4:  Planet.VENUS,   # Taurus
            5:  Planet.MERCURY, # Gemini
            6:  Planet.MOON,    # Cancer
            7:  Planet.SUN,     # Leo
            8:  Planet.MERCURY, # Virgo
            9:  Planet.VENUS,   # Libra
            10: Planet.MARS,    # Scorpio
            11: Planet.JUPITER, # Sagittarius
            12: Planet.SATURN,  # Capricorn
        },
        "auspicious":   [Planet.VENUS, Planet.SATURN, Planet.MERCURY],
        "inauspicious": [Planet.MOON, Planet.JUPITER, Planet.SUN],
        "yoga_karaka":  [Planet.VENUS],  # Rules 4th (kendra) + 9th (trikona)
        "maraka":       [Planet.JUPITER, Planet.SUN],
        "neutral":      [Planet.MARS],
        "notes": (
            "Venus rules 4th (kendra) AND 9th (trikona) — excellent Yoga Karaka. "
            "Saturn is lagna lord + 12th — lagna lordship holds. "
            "Mercury rules 5th (trikona) + 8th — 5th trikona dominates; net auspicious. "
            "Jupiter rules 2nd (Maraka) + 11th (trishadaya) — Maraka + inauspicious. "
            "Sun rules 7th (kendra, Maraka) — Maraka. "
            "Moon rules 6th (trishadaya) — inauspicious. "
            "Mars rules 3rd (trishadaya) + 10th (kendra) — malefic in kendra is mixed."
        ),
    },

    # ── 12. PISCES (Meena) ───────────────────────────────────────────────
    Sign.PISCES: {
        "lagna_lord": Planet.JUPITER,
        "house_lords": {
            1:  Planet.JUPITER, # Pisces
            2:  Planet.MARS,    # Aries
            3:  Planet.VENUS,   # Taurus
            4:  Planet.MERCURY, # Gemini
            5:  Planet.MOON,    # Cancer
            6:  Planet.SUN,     # Leo
            7:  Planet.MERCURY, # Virgo
            8:  Planet.VENUS,   # Libra
            9:  Planet.MARS,    # Scorpio
            10: Planet.JUPITER, # Sagittarius
            11: Planet.SATURN,  # Capricorn
            12: Planet.SATURN,  # Aquarius
        },
        "auspicious":   [Planet.MOON, Planet.MARS, Planet.JUPITER],
        "inauspicious": [Planet.SATURN, Planet.SUN, Planet.MERCURY, Planet.VENUS],
        "yoga_karaka":  [],
        "maraka":       [Planet.MERCURY, Planet.MARS],
        "neutral":      [],
        "notes": (
            "Moon rules 5th (trikona) — auspicious. "
            "Mars rules 2nd (Maraka) + 9th (trikona) — 9th trikona is positive; mixed but net beneficial, "
            "though also a Maraka. "
            "Jupiter is lagna lord + 10th (kendra) — Kendradhipati applies; still auspicious as lagna lord. "
            "Saturn rules 11th (trishadaya) + 12th — inauspicious. "
            "Sun rules 6th (trishadaya) — inauspicious. "
            "Mercury rules 4th (kendra) + 7th (kendra, Maraka) — Kendradhipati + Maraka; very inauspicious. "
            "Venus rules 3rd (trishadaya) + 8th — very inauspicious."
        ),
    },
}
