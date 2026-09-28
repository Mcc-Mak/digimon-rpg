"""Original Digimon species and move data definitions.

This module is the single source of truth for all creature data in the
digimon-rpg game. It defines:

* ``Move`` — a dataclass describing an individual combat skill.
* ``Digimon`` — a dataclass describing a species (base stats, moves,
  evolution graph, growth curves, and flavor text).
* ``DIGIMON_REGISTRY`` — a dict mapping species name (lowercase) to its
  ``Digimon`` instance.
* ``TYPE_CHART`` — the elemental weakness/resistance matrix.
* Helper functions ``get_digimon`` and ``get_type_multiplier``.

Two evolution lines are defined (Fire and Water), each with Rookie →
Champion → Ultimate stages, plus four additional Rookie-stage creatures used
by encounter tables.

WASM safety: this module is pure data definition with no I/O, imports only
the stdlib ``dataclasses`` module, and is fully serializable. It is safe to
import under pygbag/WASM and on desktop Python alike.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Type aliases to keep signatures readable.
Stage = str  # "Rookie", "Champion", "Ultimate"
Element = str  # "fire", "water", "nature", "electric", "earth", "dark", "normal"


# ---------------------------------------------------------------------------
# Move dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Move:
    """A single combat skill / ability usable by a Digimon.

    Attributes:
        name: Display name of the move.
        power: Base damage/healing power of the move.
        mp_cost: MP consumed when using the move (0 = free).
        move_type: One of ``"attack"``, ``"special"``, ``"defend"``,
            or ``"heal"``.
        element: Effective element of the move. Defaults to ``"normal"``,
            which interacts neutrally with all defenders.
        description: Short human-readable description of the move.
    """

    name: str
    power: int
    mp_cost: int
    move_type: str
    element: str = "normal"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate field values to catch data-entry mistakes at import time."""
        if self.power < 0:
            raise ValueError(f"Move '{self.name}' has negative power {self.power}.")
        if self.mp_cost < 0:
            raise ValueError(f"Move '{self.name}' has negative MP cost {self.mp_cost}.")
        if self.move_type not in ("attack", "defend", "special", "heal"):
            raise ValueError(
                f"Move '{self.name}' has invalid move_type '{self.move_type}'."
            )


# ---------------------------------------------------------------------------
# Digimon dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Digimon:
    """A single Digimon species definition with base stats and growth data.

    Attributes:
        name: Display name of the species (e.g. ``"Emberling"``).
        stage: Evolution stage, one of ``"Rookie"``, ``"Champion"``,
            or ``"Ultimate"``.
        element: Primary elemental affinity (fire, water, nature, ...).
        hp: Base HP at level 1.
        mp: Base MP at level 1.
        attack: Base ATK at level 1.
        defense: Base DEF at level 1.
        speed: Base SPD at level 1.
        moves: List of ``Move`` instances the species knows.
        evolution_target: Species name of the next evolution stage, or
            ``None`` if this creature cannot evolve further.
        evolution_requirements: Dict describing unlock conditions
            (``level``, ``battles_won``, ``boss_defeats``).
        description: Flavor text describing the creature.
        hp_growth: Per-level HP growth multiplier (fraction of base per level).
        mp_growth: Per-level MP growth multiplier.
        atk_growth: Per-level ATK growth multiplier.
        def_growth: Per-level DEF growth multiplier.
        spd_growth: Per-level SPD growth multiplier.
    """

    name: str
    stage: str
    element: str
    hp: int
    mp: int
    attack: int
    defense: int
    speed: int
    moves: List[Move] = field(default_factory=list)
    evolution_target: str | None = None
    evolution_requirements: Dict[str, int] = field(default_factory=dict)
    description: str = ""
    hp_growth: float = 0.0
    mp_growth: float = 0.0
    atk_growth: float = 0.0
    def_growth: float = 0.0
    spd_growth: float = 0.0

    @property
    def key(self) -> str:
        """Return the lowercase registry key for this species."""
        return self.name.lower()

    def get_move(self, move_name: str) -> Move | None:
        """Look up one of this creature's moves by name (case-insensitive).

        Args:
            move_name: The name of the move to find.

        Returns:
            The matching :class:`Move` or ``None`` if not found.
        """
        for m in self.moves:
            if m.name.lower() == move_name.lower():
                return m
        return None


# ---------------------------------------------------------------------------
# Shared move definitions (reused across the Fire and Water lines)
# ---------------------------------------------------------------------------

_FIRE_MOVES: List[Move] = [
    Move(
        name="Scorching Tackle",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="fire",
        description="A blazing charge that damages the foe with high-temperature impact.",
    ),
    Move(
        name="Ember Burst",
        power=40,
        mp_cost=10,
        move_type="special",
        element="fire",
        description="Releases a burst of embers that sears all nearby adversaries.",
    ),
    Move(
        name="Flame Lash",
        power=65,
        mp_cost=18,
        move_type="special",
        element="fire",
        description="A whip of concentrated flame lashes out and scorches the target.",
    ),
    Move(
        name="Inferno Crash",
        power=90,
        mp_cost=30,
        move_type="special",
        element="fire",
        description="The ultimate fire strike — a devastating explosion of plasma.",
    ),
]

_WATER_MOVES: List[Move] = [
    Move(
        name="Water Slap",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="water",
        description="A quick splash of pressurized water that stings on impact.",
    ),
    Move(
        name="Bubble Spray",
        power=40,
        mp_cost=10,
        move_type="special",
        element="water",
        description="Fires a volley of bubbles that explode on contact.",
    ),
    Move(
        name="Aqua Jet",
        power=65,
        mp_cost=18,
        move_type="attack",
        element="water",
        description="Propels the user forward at high speed, piercing the defender.",
    ),
    Move(
        name="Tidal Force",
        power=90,
        mp_cost=30,
        move_type="special",
        element="water",
        description="Summons a crushing tidal wave that slams into the foe.",
    ),
]

_ELECTRIC_MOVES: List[Move] = [
    Move(
        name="Spark Bolt",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="electric",
        description="A crackling bolt of electricity zaps the opponent.",
    ),
    Move(
        name="Static Feathers",
        power=40,
        mp_cost=10,
        move_type="special",
        element="electric",
        description="Fires charged feathers that arc between targets.",
    ),
    Move(
        name="Thunderclap",
        power=65,
        mp_cost=18,
        move_type="special",
        element="electric",
        description="A deafening clap of thunder that disorients and damages.",
    ),
    Move(
        name="Storm Dive",
        power=90,
        mp_cost=30,
        move_type="attack",
        element="electric",
        description="Dives from the sky wreathed in lightning for a massive hit.",
    ),
]

_EARTH_MOVES: List[Move] = [
    Move(
        name="Rock Throw",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="earth",
        description="Hurls a heavy rock at the opponent.",
    ),
    Move(
        name="Stone Shell",
        power=40,
        mp_cost=10,
        move_type="defend",
        element="earth",
        description="Hardens the body into stone to drastically reduce incoming damage.",
    ),
    Move(
        name="Quake Stomp",
        power=65,
        mp_cost=18,
        move_type="attack",
        element="earth",
        description="Stomps the ground, sending seismic tremors at the foe.",
    ),
    Move(
        name="Mountain Crush",
        power=90,
        mp_cost=30,
        move_type="attack",
        element="earth",
        description="A cataclysmic slam with the force of an avalanche.",
    ),
]

_NATURE_MOVES: List[Move] = [
    Move(
        name="Vine Whip",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="nature",
        description="Lashes the enemy with flexible, thorny vines.",
    ),
    Move(
        name="Leaf Storm",
        power=40,
        mp_cost=10,
        move_type="special",
        element="nature",
        description="A swirling storm of razor-sharp leaves shreds the target.",
    ),
    Move(
        name="Root Bind",
        power=65,
        mp_cost=18,
        move_type="special",
        element="nature",
        description="Entangles the foe in deep roots and drains vitality.",
    ),
    Move(
        name="Bloom Burst",
        power=90,
        mp_cost=30,
        move_type="special",
        element="nature",
        description="A massive floral explosion of pure botanical energy.",
    ),
]

_DARK_MOVES: List[Move] = [
    Move(
        name="Shadow Poke",
        power=20,
        mp_cost=0,
        move_type="attack",
        element="dark",
        description="A quick jab from the shadows that catches foes off guard.",
    ),
    Move(
        name="Dark Mist",
        power=40,
        mp_cost=10,
        move_type="special",
        element="dark",
        description="Unleashes a choking mist of concentrated darkness.",
    ),
    Move(
        name="Void Claw",
        power=65,
        mp_cost=18,
        move_type="attack",
        element="dark",
        description="Rends reality with a claw forged from the void.",
    ),
    Move(
        name="Eclipse Roar",
        power=90,
        mp_cost=30,
        move_type="special",
        element="dark",
        description="A soul-shattering roar that harnesses the power of an eclipse.",
    ),
]


# ---------------------------------------------------------------------------
# Species definitions
# ---------------------------------------------------------------------------

# --- Evolution Line 1: Fire ---

EMBERLING = Digimon(
    name="Emberling",
    stage="Rookie",
    element="fire",
    hp=100,
    mp=40,
    attack=20,
    defense=14,
    speed=16,
    moves=_FIRE_MOVES,
    evolution_target="Pyroclaw",
    evolution_requirements={"level": 10, "battles_won": 5},
    description=(
        "A small, lizard-like creature with glowing ember patches along its "
        "spine. Its tail flickers with a constant flame. Playful and curious."
    ),
    hp_growth=0.030,
    mp_growth=0.020,
    atk_growth=0.045,
    def_growth=0.020,
    spd_growth=0.025,
)

PYROCLAW = Digimon(
    name="Pyroclaw",
    stage="Champion",
    element="fire",
    hp=180,
    mp=80,
    attack=45,
    defense=32,
    speed=30,
    moves=_FIRE_MOVES,
    evolution_target="Infernosaur",
    evolution_requirements={"level": 25, "battles_won": 15, "boss_defeats": 1},
    description=(
        "A muscular, quadrupedal beast with molten veins visible through "
        "cracks in its hide. Its claws glow white-hot."
    ),
    hp_growth=0.030,
    mp_growth=0.020,
    atk_growth=0.045,
    def_growth=0.020,
    spd_growth=0.025,
)

INFERNOSAUR = Digimon(
    name="Infernosaur",
    stage="Ultimate",
    element="fire",
    hp=310,
    mp=140,
    attack=85,
    defense=58,
    speed=44,
    moves=_FIRE_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A great, draconic saurian whose body is wreathed in perpetual flame. "
        "Its breath is a lance of pure plasma."
    ),
    hp_growth=0.028,
    mp_growth=0.022,
    atk_growth=0.042,
    def_growth=0.024,
    spd_growth=0.022,
)


# --- Evolution Line 2: Water ---

AQUAPUP = Digimon(
    name="Aquapup",
    stage="Rookie",
    element="water",
    hp=110,
    mp=45,
    attack=15,
    defense=18,
    speed=14,
    moves=_WATER_MOVES,
    evolution_target="Tsunamut",
    evolution_requirements={"level": 10, "battles_won": 5},
    description=(
        "A round, seal-like creature with translucent fins that shimmer like "
        "water. Its wide, hopeful eyes belie a fiercely protective nature."
    ),
    hp_growth=0.035,
    mp_growth=0.025,
    atk_growth=0.025,
    def_growth=0.040,
    spd_growth=0.015,
)

TSUNAMUT = Digimon(
    name="Tsunamut",
    stage="Champion",
    element="water",
    hp=195,
    mp=85,
    attack=35,
    defense=40,
    speed=26,
    moves=_WATER_MOVES,
    evolution_target="Leviathore",
    evolution_requirements={"level": 25, "battles_won": 15, "boss_defeats": 1},
    description=(
        "A powerful, otter-like creature with hundreds of water jets flowing "
        "around its body. It commands water with a swipe of its enormous claws."
    ),
    hp_growth=0.035,
    mp_growth=0.025,
    atk_growth=0.025,
    def_growth=0.040,
    spd_growth=0.015,
)

LEVIATHORE = Digimon(
    name="Leviathore",
    stage="Ultimate",
    element="water",
    hp=330,
    mp=150,
    attack=65,
    defense=72,
    speed=38,
    moves=_WATER_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A colossal, serpentine leviathan whose form is composed almost "
        "entirely of living, pressurized water. It summons tidal waves with "
        "a thought."
    ),
    hp_growth=0.033,
    mp_growth=0.027,
    atk_growth=0.028,
    def_growth=0.038,
    spd_growth=0.018,
)


# --- Additional encounter creatures ---

STORMWING = Digimon(
    name="Stormwing",
    stage="Rookie",
    element="electric",
    hp=90,
    mp=50,
    attack=17,
    defense=12,
    speed=22,
    moves=_ELECTRIC_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A tiny raptor with crackling feathers that emit faint arcs of static "
        "electricity. Highly energetic and fast."
    ),
    hp_growth=0.015,
    mp_growth=0.030,
    atk_growth=0.030,
    def_growth=0.015,
    spd_growth=0.045,
)

ROCKBASH = Digimon(
    name="Rockbash",
    stage="Rookie",
    element="earth",
    hp=130,
    mp=35,
    attack=14,
    defense=24,
    speed=9,
    moves=_EARTH_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A stocky, armadillo-like creature covered in overlapping stone "
        "plates. When threatened, it rolls into a near-impenetrable ball. "
        "Slow but sturdy."
    ),
    hp_growth=0.050,
    mp_growth=0.010,
    atk_growth=0.015,
    def_growth=0.045,
    spd_growth=0.005,
)

SEEDKIT = Digimon(
    name="Seedkit",
    stage="Rookie",
    element="nature",
    hp=95,
    mp=55,
    attack=16,
    defense=17,
    speed=13,
    moves=_NATURE_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A small, leafy creature resembling a sprouting bulb with stubby legs. "
        "A single flower bud sits atop its head. Calm and patient."
    ),
    hp_growth=0.025,
    mp_growth=0.040,
    atk_growth=0.025,
    def_growth=0.030,
    spd_growth=0.015,
)

CHAOSPUFF = Digimon(
    name="Chaospuff",
    stage="Rookie",
    element="dark",
    hp=85,
    mp=60,
    attack=18,
    defense=11,
    speed=20,
    moves=_DARK_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A wispy, shadow-like creature that drifts more than it walks. Its "
        "body constantly shifts shape. It thrives in darkness."
    ),
    hp_growth=0.015,
    mp_growth=0.045,
    atk_growth=0.035,
    def_growth=0.015,
    spd_growth=0.030,
)


# Thornbloom and Voltalon are referenced by Zone 2 encounter tables.
# They are natural evolution flavour variants; for now they reuse existing
# species stat blocks so they can appear in encounters without a dedicated
# evolution path.

THORNBLOOM = Digimon(
    name="Thornbloom",
    stage="Champion",
    element="nature",
    hp=210,
    mp=95,
    attack=48,
    defense=42,
    speed=28,
    moves=_NATURE_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A towering plant creature draped in razor thorns and heavy blossoms. "
        "Its petals can spray needles at surprising range."
    ),
    hp_growth=0.030,
    mp_growth=0.035,
    atk_growth=0.030,
    def_growth=0.028,
    spd_growth=0.020,
)

VOLTALON = Digimon(
    name="Voltalon",
    stage="Champion",
    element="electric",
    hp=170,
    mp=90,
    attack=40,
    defense=25,
    speed=48,
    moves=_ELECTRIC_MOVES,
    evolution_target=None,
    evolution_requirements={},
    description=(
        "A ferocious raptor whose wings shed constant lightning. It hunts "
        "during thunderstorms, using the ambient energy to charge its attacks."
    ),
    hp_growth=0.020,
    mp_growth=0.030,
    atk_growth=0.040,
    def_growth=0.018,
    spd_growth=0.045,
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

#: Maps species name (lowercase) → :class:`Digimon` instance.
DIGIMON_REGISTRY: Dict[str, Digimon] = {
    digimon.key: digimon
    for digimon in (
        EMBERLING,
        PYROCLAW,
        INFERNOSAUR,
        AQUAPUP,
        TSUNAMUT,
        LEVIATHORE,
        STORMWING,
        ROCKBASH,
        SEEDKIT,
        CHAOSPUFF,
        THORNBLOOM,
        VOLTALON,
    )
}


# ---------------------------------------------------------------------------
# Type chart
# ---------------------------------------------------------------------------

#: Elemental effectiveness matrix. ``TYPE_CHART[attacker][defender]`` gives
#: the damage multiplier. All values are floats in ``[0.5, 2.0]``.
TYPE_CHART: Dict[str, Dict[str, float]] = {
    "fire": {
        "fire": 1.0,
        "water": 0.5,
        "nature": 2.0,
        "electric": 1.0,
        "earth": 0.75,
        "dark": 1.0,
        "normal": 1.0,
    },
    "water": {
        "fire": 2.0,
        "water": 1.0,
        "nature": 0.75,
        "electric": 0.5,
        "earth": 2.0,
        "dark": 1.0,
        "normal": 1.0,
    },
    "nature": {
        "fire": 0.75,
        "water": 2.0,
        "nature": 1.0,
        "electric": 1.0,
        "earth": 2.0,
        "dark": 1.0,
        "normal": 1.0,
    },
    "electric": {
        "fire": 1.0,
        "water": 2.0,
        "nature": 1.0,
        "electric": 0.75,
        "earth": 0.5,
        "dark": 2.0,
        "normal": 1.0,
    },
    "earth": {
        "fire": 2.0,
        "water": 0.75,
        "nature": 0.75,
        "electric": 2.0,
        "earth": 1.0,
        "dark": 1.0,
        "normal": 1.0,
    },
    "dark": {
        "fire": 1.0,
        "water": 1.0,
        "nature": 1.0,
        "electric": 0.5,
        "earth": 1.0,
        "dark": 2.0,
        "normal": 1.0,
    },
    "normal": {
        "fire": 1.0,
        "water": 1.0,
        "nature": 1.0,
        "electric": 1.0,
        "earth": 1.0,
        "dark": 1.0,
        "normal": 1.0,
    },
}


# ---------------------------------------------------------------------------
# Public lookup helpers
# ---------------------------------------------------------------------------

def get_digimon(name: str) -> Digimon:
    """Look up a Digimon species by name (case-insensitive).

    Args:
        name: The display name or lowercase registry key of the species.

    Returns:
        The matching :class:`Digimon` instance.

    Raises:
        KeyError: If no species with that name exists in the registry.
    """
    try:
        return DIGIMON_REGISTRY[name.strip().lower()]
    except KeyError:
        raise KeyError(f"Unknown Digimon species: '{name}'") from None


def get_type_multiplier(attacker_element: str, defender_element: str) -> float:
    """Return the type-effectiveness damage multiplier.

    Args:
        attacker_element: Element of the attacking move. Falls back to
            ``"normal"`` if unknown.
        defender_element: Element of the defending creature.

    Returns:
        A float multiplier in ``[0.5, 2.0]``. Unknown attacker or defender
        elements are treated as ``"normal"`` (neutral 1.0).
    """
    atk = attacker_element if attacker_element in TYPE_CHART else "normal"
    defn = defender_element if defender_element in TYPE_CHART[atk] else "normal"
    return TYPE_CHART[atk][defn]
