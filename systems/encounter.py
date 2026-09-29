"""Wild encounter system: zones, weighted tables, and encounter rolling.

This module defines the encounter data and the RNG-driven logic that decides
whether a player runs into a wild Digimon while walking through a zone, what
species appears, at what level, and how much gold is found.

The system is data-driven and uses a seeded :class:`random.Random` instance
so tests and save/load restores can reproduce identical encounter sequences.

WASM safety: this module uses only the stdlib ``random`` and ``dataclasses``
modules, performs no I/O, and makes no system calls. Safe under pygbag/WASM.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EncounterEntry:
    """A single weighted row in a zone's encounter table.

    Attributes:
        species_id: Lowercase registry key of the species (e.g.
            ``"emberling"``).
        weight: Relative probability weight (higher = more common).
        min_level: Minimum level the species can appear at in this zone.
        max_level: Maximum level the species can appear at in this zone.
        base_xp: Base XP awarded for defeating this species.
    """

    species_id: str
    weight: float
    min_level: int
    max_level: int
    base_xp: int

    def __post_init__(self) -> None:
        """Validate field values to catch data-entry mistakes at import time."""
        if self.weight <= 0:
            raise ValueError(
                f"Encounter '{self.species_id}' has non-positive weight {self.weight}."
            )
        if self.min_level < 1 or self.max_level < self.min_level:
            raise ValueError(
                f"Encounter '{self.species_id}' has invalid level range "
                f"{self.min_level}..{self.max_level}."
            )
        if self.base_xp < 0:
            raise ValueError(
                f"Encounter '{self.species_id}' has negative base_xp {self.base_xp}."
            )


@dataclass(frozen=True)
class Zone:
    """A game area with an encounter table, encounter rates, and gold range.

    Attributes:
        zone_id: Unique string identifier (e.g. ``"verdant_plains"``).
        name: Human-readable zone name.
        min_level: Minimum monster level in this zone.
        max_level: Maximum monster level in this zone.
        encounter_entries: List of :class:`EncounterEntry` rows.
        encounter_rates: Dict mapping terrain type → encounter probability
            (float in [0, 1]).
        gold_min: Minimum gold awarded for a battle in this zone.
        gold_max: Maximum gold awarded for a battle in this zone.
    """

    zone_id: str
    name: str
    min_level: int
    max_level: int
    encounter_entries: List[EncounterEntry] = field(default_factory=list)
    encounter_rates: Dict[str, float] = field(default_factory=dict)
    gold_min: int = 0
    gold_max: int = 0

    def __post_init__(self) -> None:
        """Validate that rates are probabilities and gold range is sane."""
        for terrain, rate in self.encounter_rates.items():
            if not 0.0 <= rate <= 1.0:
                raise ValueError(
                    f"Zone '{self.zone_id}' terrain '{terrain}' has invalid "
                    f"encounter rate {rate} (must be in [0, 1])."
                )
        if self.gold_min < 0 or self.gold_max < self.gold_min:
            raise ValueError(
                f"Zone '{self.zone_id}' has invalid gold range "
                f"{self.gold_min}..{self.gold_max}."
            )

    def weighted_choices(self) -> List[tuple]:
        """Return a precomputed ``(entry, weight)`` list for random.choices.

        Returns:
            A list of ``(EncounterEntry, float)`` tuples ready to be fed to
            :func:`random.choices` via ``populations``/``weights`` unpacking.
        """
        return [(entry, entry.weight) for entry in self.encounter_entries]


# ---------------------------------------------------------------------------
# Zone definitions
# ---------------------------------------------------------------------------

# Zone 1: Verdant Plains (levels 1-12)
VERDANT_PLAINS = Zone(
    zone_id="verdant_plains",
    name="Verdant Plains",
    min_level=1,
    max_level=12,
    encounter_entries=[
        EncounterEntry("emberling", weight=0.12, min_level=1, max_level=6, base_xp=25),
        EncounterEntry("aquapup", weight=0.12, min_level=1, max_level=6, base_xp=25),
        EncounterEntry("seedkit", weight=0.10, min_level=2, max_level=8, base_xp=25),
        EncounterEntry("rockbash", weight=0.08, min_level=3, max_level=9, base_xp=25),
        EncounterEntry("stormwing", weight=0.06, min_level=4, max_level=10, base_xp=30),
        EncounterEntry("chaospuff", weight=0.06, min_level=5, max_level=12, base_xp=35),
        EncounterEntry("cinderpup", weight=0.06, min_level=2, max_level=7, base_xp=25),
        EncounterEntry("mistpup", weight=0.06, min_level=2, max_level=7, base_xp=25),
        EncounterEntry("barksprout", weight=0.06, min_level=3, max_level=8, base_xp=25),
        EncounterEntry("boltrat", weight=0.05, min_level=4, max_level=10, base_xp=30),
        EncounterEntry("duskling", weight=0.05, min_level=5, max_level=12, base_xp=35),
        EncounterEntry("boulderpebble", weight=0.06, min_level=3, max_level=9, base_xp=25),
        EncounterEntry("flaretad", weight=0.04, min_level=3, max_level=8, base_xp=25),
        EncounterEntry("tideflip", weight=0.04, min_level=3, max_level=8, base_xp=25),
        EncounterEntry("shadepuff", weight=0.04, min_level=5, max_level=12, base_xp=35),
        EncounterEntry("sandtad", weight=0.03, min_level=4, max_level=10, base_xp=30),
        EncounterEntry("arctad", weight=0.03, min_level=4, max_level=10, base_xp=30),
    ],
    encounter_rates={
        "low_grass": 0.15,
        "tall_grass": 0.25,
        "water_edge": 0.12,
    },
    gold_min=8,
    gold_max=20,
)

# Zone 2: Storm Peaks (levels 15-28)
STORM_PEAKS = Zone(
    zone_id="storm_peaks",
    name="Storm Peaks",
    min_level=15,
    max_level=28,
    encounter_entries=[
        EncounterEntry("stormwing", weight=0.08, min_level=15, max_level=22, base_xp=45),
        EncounterEntry("chaospuff", weight=0.06, min_level=16, max_level=24, base_xp=45),
        EncounterEntry("rockbash", weight=0.06, min_level=17, max_level=25, base_xp=45),
        EncounterEntry("pyroclaw", weight=0.06, min_level=18, max_level=26, base_xp=55),
        EncounterEntry("tsunamut", weight=0.05, min_level=20, max_level=27, base_xp=55),
        EncounterEntry("thornbloom", weight=0.05, min_level=20, max_level=28, base_xp=55),
        EncounterEntry("voltalon", weight=0.04, min_level=20, max_level=28, base_xp=75),
        EncounterEntry("scorchimp", weight=0.05, min_level=15, max_level=22, base_xp=45),
        EncounterEntry("waveminnow", weight=0.05, min_level=15, max_level=22, base_xp=45),
        EncounterEntry("staticmouse", weight=0.05, min_level=16, max_level=23, base_xp=45),
        EncounterEntry("gempup", weight=0.05, min_level=17, max_level=24, base_xp=45),
        EncounterEntry("voidling", weight=0.05, min_level=18, max_level=25, base_xp=50),
        EncounterEntry("magmapup", weight=0.05, min_level=18, max_level=25, base_xp=50),
        EncounterEntry("crystalcub", weight=0.05, min_level=17, max_level=24, base_xp=45),
        EncounterEntry("blazehorn", weight=0.04, min_level=20, max_level=27, base_xp=65),
        EncounterEntry("tidescale", weight=0.04, min_level=20, max_level=27, base_xp=65),
        EncounterEntry("bolttalon", weight=0.04, min_level=20, max_level=27, base_xp=65),
        EncounterEntry("slateplate", weight=0.04, min_level=20, max_level=27, base_xp=65),
        EncounterEntry("nightwraith", weight=0.04, min_level=21, max_level=28, base_xp=70),
        EncounterEntry("mountainhide", weight=0.03, min_level=22, max_level=28, base_xp=75),
        EncounterEntry("wraithwing", weight=0.03, min_level=22, max_level=28, base_xp=75),
        EncounterEntry("mistshell", weight=0.03, min_level=22, max_level=28, base_xp=70),
    ],
    encounter_rates={
        "mountain_path": 0.22,
        "lightning_field": 0.30,
        "cave_interior": 0.18,
    },
    gold_min=20,
    gold_max=40,
)

# Zone 3: Ashen Wastes (levels 30-50)
ASHEN_WASTES = Zone(
    zone_id="ashen_wastes",
    name="Ashen Wastes",
    min_level=30,
    max_level=50,
    encounter_entries=[
        EncounterEntry("pyroclaw", weight=0.06, min_level=30, max_level=38, base_xp=80),
        EncounterEntry("tsunamut", weight=0.06, min_level=30, max_level=38, base_xp=80),
        EncounterEntry("voltalon", weight=0.05, min_level=30, max_level=38, base_xp=80),
        EncounterEntry("thornbloom", weight=0.05, min_level=30, max_level=38, base_xp=80),
        EncounterEntry("wraithwing", weight=0.05, min_level=32, max_level=40, base_xp=90),
        EncounterEntry("mountainhide", weight=0.05, min_level=32, max_level=40, base_xp=90),
        EncounterEntry("flarecrest", weight=0.05, min_level=32, max_level=40, base_xp=85),
        EncounterEntry("torrentwhirl", weight=0.04, min_level=32, max_level=40, base_xp=85),
        EncounterEntry("chargewing", weight=0.04, min_level=32, max_level=40, base_xp=85),
        EncounterEntry("barkblossom", weight=0.04, min_level=32, max_level=40, base_xp=85),
        EncounterEntry("phantomwing", weight=0.04, min_level=34, max_level=42, base_xp=90),
        EncounterEntry("crystalcrush", weight=0.04, min_level=34, max_level=42, base_xp=90),
        EncounterEntry("magmaclaw", weight=0.04, min_level=34, max_level=42, base_xp=90),
        EncounterEntry("duskveil", weight=0.04, min_level=35, max_level=44, base_xp=95),
        EncounterEntry("boulderplate", weight=0.04, min_level=35, max_level=44, base_xp=95),
        EncounterEntry("infernosaur", weight=0.03, min_level=40, max_level=48, base_xp=120),
        EncounterEntry("leviathore", weight=0.03, min_level=40, max_level=48, base_xp=120),
        EncounterEntry("thundergod", weight=0.02, min_level=42, max_level=50, base_xp=130),
        EncounterEntry("verdanttitan", weight=0.02, min_level=42, max_level=50, base_xp=130),
        EncounterEntry("terraroc", weight=0.02, min_level=42, max_level=50, base_xp=130),
        EncounterEntry("umbrathrax", weight=0.02, min_level=42, max_level=50, base_xp=130),
        EncounterEntry("ashentitan", weight=0.02, min_level=44, max_level=50, base_xp=140),
        EncounterEntry("blazosaur", weight=0.02, min_level=44, max_level=50, base_xp=140),
        EncounterEntry("tideleviathan", weight=0.02, min_level=44, max_level=50, base_xp=140),
        EncounterEntry("boltstorm", weight=0.02, min_level=44, max_level=50, base_xp=140),
        EncounterEntry("voidtyrant", weight=0.02, min_level=44, max_level=50, base_xp=140),
    ],
    encounter_rates={
        "volcanic_rock": 0.25,
        "ash_field": 0.20,
        "ruined_temple": 0.30,
    },
    gold_min=35,
    gold_max=70,
)

#: Maps zone_id → :class:`Zone` instance.
ZONES: Dict[str, Zone] = {
    VERDANT_PLAINS.zone_id: VERDANT_PLAINS,
    STORM_PEAKS.zone_id: STORM_PEAKS,
    ASHEN_WASTES.zone_id: ASHEN_WASTES,
}


# ---------------------------------------------------------------------------
# Encounter rolling functions
# ---------------------------------------------------------------------------

def roll_encounter(
    zone_id: str,
    rng: Optional[random.Random] = None,
) -> Optional[Dict[str, object]]:
    """Roll a random wild encounter from a zone's weighted table.

    This function does **not** apply terrain rate checks; it simply picks a
    random species/level/xp based on the zone's encounter table. Use
    :func:`check_encounter` for the full trigger roll.

    Args:
        zone_id: The zone to pull the encounter from.
        rng: Optional seeded :class:`random.Random`. If ``None``, module-level
            :mod:`random` is used (non-deterministic).

    Returns:
        A dict ``{"species": str, "level": int, "base_xp": int}`` describing
        the rolled encounter, or ``None`` if the zone has no encounter table.

    Raises:
        KeyError: If ``zone_id`` does not exist in :data:`ZONES`.
    """
    if zone_id not in ZONES:
        raise KeyError(f"Unknown zone id: '{zone_id}'")

    zone: Zone = ZONES[zone_id]
    if not zone.encounter_entries:
        return None

    weights = [entry.weight for entry in zone.encounter_entries]
    if rng is not None:
        entry: EncounterEntry = rng.choices(
            zone.encounter_entries, weights=weights, k=1
        )[0]
    else:
        entry = random.choices(zone.encounter_entries, weights=weights, k=1)[0]

    if rng is not None:
        level = rng.randint(entry.min_level, entry.max_level)
    else:
        level = random.randint(entry.min_level, entry.max_level)

    return {
        "species": entry.species_id,
        "level": level,
        "base_xp": entry.base_xp,
    }


def check_encounter(
    zone_id: str,
    terrain_type: str,
    rng: Optional[random.Random] = None,
) -> Optional[Dict[str, object]]:
    """Check whether an encounter triggers on the given terrain, and roll it.

    This is the full "walking in tall grass" trigger:

    1. Look up the terrain's encounter rate for the zone.
    2. If a uniform random draw in [0, 1) is below the rate, roll a weighted
       encounter via :func:`roll_encounter`.
    3. Otherwise return ``None``.

    Args:
        zone_id: The zone the player is in.
        terrain_type: One of the zone's terrain keys (e.g. ``"tall_grass"``).
        rng: Optional seeded :class:`random.Random` for deterministic testing.

    Returns:
        An encounter dict from :func:`roll_encounter` if triggered, else
        ``None``.

    Raises:
        KeyError: If ``zone_id`` is unknown or ``terrain_type`` has no rate.
    """
    if zone_id not in ZONES:
        raise KeyError(f"Unknown zone id: '{zone_id}'")

    zone: Zone = ZONES[zone_id]
    if terrain_type not in zone.encounter_rates:
        raise KeyError(
            f"Zone '{zone_id}' has no encounter rate for terrain '{terrain_type}'."
        )

    rate: float = zone.encounter_rates[terrain_type]
    if rng is not None:
        draw = rng.random()
    else:
        draw = random.random()

    if draw >= rate:
        return None

    return roll_encounter(zone_id, rng)


def roll_gold(
    zone_id: str,
    rng: Optional[random.Random] = None,
) -> int:
    """Roll a random gold amount for a battle win in a zone.

    Args:
        zone_id: The zone where the battle occurred.
        rng: Optional seeded :class:`random.Random`.

    Returns:
        A random integer in the zone's ``[gold_min, gold_max]`` inclusive
        range.

    Raises:
        KeyError: If ``zone_id`` does not exist in :data:`ZONES`.
    """
    if zone_id not in ZONES:
        raise KeyError(f"Unknown zone id: '{zone_id}'")

    zone: Zone = ZONES[zone_id]
    if rng is not None:
        return rng.randint(zone.gold_min, zone.gold_max)
    return random.randint(zone.gold_min, zone.gold_max)


def get_zone(zone_id: str) -> Zone:
    """Look up a :class:`Zone` by its id.

    Args:
        zone_id: The zone identifier.

    Returns:
        The matching :class:`Zone` instance.

    Raises:
        KeyError: If the zone does not exist.
    """
    return ZONES[zone_id]
