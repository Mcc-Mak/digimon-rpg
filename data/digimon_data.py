"""Digimon species and move data definitions.

This module is the single source of truth for all creature data in the
digimon-rpg game. It defines:

* ``Move`` — a dataclass describing an individual combat skill.
* ``Digimon`` — a dataclass describing a species (base stats, moves,
  evolution graph, growth curves, and flavor text).
* ``DIGIMON_REGISTRY`` — a dict mapping species name (lowercase) to its
  ``Digimon`` instance.
* ``TYPE_CHART`` — the elemental weakness/resistance matrix.
* Helper functions ``get_digimon`` and ``get_type_multiplier``.

Twelve species are hand-crafted with bespoke stats, descriptions, and
procedural sprite drawers. An additional 128 species are generated from a
compact data table (``_EXPANDED_SPECIES_TABLE``) using element- and
stage-templated stats, moves, and growth curves, for a total of 140
species across 45 evolution lines and 6 elements.

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
    evolution_target="Voltalon",
    evolution_requirements={"level": 10, "battles_won": 5},
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
    evolution_target="Mountainhide",
    evolution_requirements={"level": 10, "battles_won": 5},
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
    evolution_target="Thornbloom",
    evolution_requirements={"level": 10, "battles_won": 5},
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
    evolution_target="Wraithwing",
    evolution_requirements={"level": 10, "battles_won": 5},
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


# Thornbloom and Voltalon are Champion-stage evolutions of Seedkit and
# Stormwing respectively, completing the nature and electric lines.

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
    evolution_target="VerdantTitan",
    evolution_requirements={"level": 25, "battles_won": 15, "boss_defeats": 1},
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
    evolution_target="Thundergod",
    evolution_requirements={"level": 25, "battles_won": 15, "boss_defeats": 1},
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
# Data-driven expanded species roster
# ---------------------------------------------------------------------------
#
# The 12 hand-crafted species above cover the original evolution lines.
# The expanded roster below adds 128 additional species derived from the
# 140-sprite asset library, grouped into evolution lines by element.
# Stats, moves, growth, and descriptions are templated by element and stage
# so the data stays compact and maintainable.

#: (species_id, stage_num, element, evolution_target_display_name_or_None)
#: stage_num: 1=Rookie, 2=Champion, 3=Ultimate
_EXPANDED_SPECIES_TABLE: List[tuple] = [
    ("ashenkit", 1, "fire", "Flarecrest"),
    ("blazekit", 1, "fire", "Blazehorn"),
    ("cinderpup", 1, "fire", "Magmaclaw"),
    ("emberwraith", 1, "fire", None),
    ("flaretad", 1, "fire", "Tinderjaw"),
    ("magmapup", 1, "fire", "Pyrefang"),
    ("pyrelarva", 1, "fire", "Ashentusk"),
    ("scorchimp", 1, "fire", "Scorchmane"),
    ("ashentusk", 2, "fire", "Ashentitan"),
    ("blazehorn", 2, "fire", "Blazosaur"),
    ("flarecrest", 2, "fire", "Flarewyrm"),
    ("magmaclaw", 2, "fire", "Infernodrake"),
    ("pyrefang", 2, "fire", "Pyrebeast"),
    ("scorchmane", 2, "fire", "Scorchlord"),
    ("tinderjaw", 2, "fire", "Magmathrax"),
    ("ashentitan", 3, "fire", None),
    ("blazosaur", 3, "fire", None),
    ("flarewyrm", 3, "fire", None),
    ("infernodrake", 3, "fire", None),
    ("magmathrax", 3, "fire", None),
    ("pyrebeast", 3, "fire", None),
    ("scorchlord", 3, "fire", None),
    ("deepspawn", 1, "water", None),
    ("mistpup", 1, "water", "Mistshell"),
    ("tideflip", 1, "water", "Tidescale"),
    ("torrentsprat", 1, "water", "Torrentwhirl"),
    ("waveminnow", 1, "water", "Wavecrest"),
    ("abyssalclaw", 2, "water", None),
    ("mistshell", 2, "water", "Mistmaelstrom"),
    ("tidescale", 2, "water", "Tideleviathan"),
    ("torrentwhirl", 2, "water", "Torrentserpent"),
    ("wavecrest", 2, "water", "Wavedepths"),
    ("mistmaelstrom", 3, "water", None),
    ("tideleviathan", 3, "water", None),
    ("torrentserpent", 3, "water", None),
    ("wavedepths", 3, "water", None),
    ("barksprout", 1, "nature", "Barkblossom"),
    ("rootbud", 1, "nature", "Rootbark"),
    ("vinepod", 1, "nature", "Vinethorn"),
    ("wildbloom", 1, "nature", None),
    ("barkblossom", 2, "nature", "Barkwarden"),
    ("rootbark", 2, "nature", "Rootguardian"),
    ("vinethorn", 2, "nature", "Vineancient"),
    ("barkwarden", 3, "nature", None),
    ("rootguardian", 3, "nature", None),
    ("verdant_titan", 3, "nature", None),
    ("vineancient", 3, "nature", None),
    ("arctad", 1, "electric", "Arctalons"),
    ("boltrat", 1, "electric", "Bolttalon"),
    ("chargepip", 1, "electric", "Chargewing"),
    ("staticmouse", 1, "electric", "Staticclaw"),
    ("stormphantom", 1, "electric", None),
    ("surgespark", 1, "electric", "Surgefeather"),
    ("voltkit", 1, "electric", "Voltcrest"),
    ("zapchick", 1, "electric", "Zapbeak"),
    ("arctalons", 2, "electric", "Arctempest"),
    ("bolttalon", 2, "electric", "Boltstorm"),
    ("chargewing", 2, "electric", "Chargegod"),
    ("staticclaw", 2, "electric", "Staticdeity"),
    ("surgefeather", 2, "electric", "Surgezenith"),
    ("voltcrest", 2, "electric", "Volttempest"),
    ("zapbeak", 2, "electric", "Zapzenith"),
    ("arctempest", 3, "electric", None),
    ("boltstorm", 3, "electric", None),
    ("chargegod", 3, "electric", None),
    ("staticdeity", 3, "electric", None),
    ("surgezenith", 3, "electric", None),
    ("thundergod", 3, "electric", None),
    ("volttempest", 3, "electric", None),
    ("zapzenith", 3, "electric", None),
    ("boulderpebble", 1, "earth", "Boulderplate"),
    ("clayworm", 1, "earth", "Clayguard"),
    ("crystalcub", 1, "earth", "Crystalcrush"),
    ("gempup", 1, "earth", "Gemhide"),
    ("gravelpip", 1, "earth", "Gravelguard"),
    ("oreworm", 1, "earth", "Orehide"),
    ("sandtad", 1, "earth", "Sandwall"),
    ("slatekit", 1, "earth", "Slateplate"),
    ("stonelarva", 1, "earth", "Stonewall"),
    ("terramole", 1, "earth", "Terrabulwark"),
    ("boulderplate", 2, "earth", "Boulderbehemoth"),
    ("clayguard", 2, "earth", "Claycolossus"),
    ("crystalcrush", 2, "earth", "Crystalroc"),
    ("gemhide", 2, "earth", "Gemmonolith"),
    ("gravelguard", 2, "earth", "Gravelmonolith"),
    ("mountainhide", 2, "earth", "Terraroc"),
    ("orehide", 2, "earth", "Oreroc"),
    ("sandwall", 2, "earth", "Sandbehemoth"),
    ("slateplate", 2, "earth", "Slatetitan"),
    ("stonewall", 2, "earth", "Stonecolossus"),
    ("terrabulwark", 2, "earth", "Terratitan"),
    ("boulderbehemoth", 3, "earth", None),
    ("claycolossus", 3, "earth", None),
    ("crystalroc", 3, "earth", None),
    ("gemmonolith", 3, "earth", None),
    ("gravelmonolith", 3, "earth", None),
    ("oreroc", 3, "earth", None),
    ("sandbehemoth", 3, "earth", None),
    ("slatetitan", 3, "earth", None),
    ("stonecolossus", 3, "earth", None),
    ("terraroc", 3, "earth", None),
    ("terratitan", 3, "earth", None),
    ("duskling", 1, "dark", "Duskveil"),
    ("eclipsewisp", 1, "dark", "Eclipseveil"),
    ("nightpip", 1, "dark", "Nightwraith"),
    ("phantommin", 1, "dark", "Phantomwing"),
    ("shadepuff", 1, "dark", "Shadewraith"),
    ("shadowimp", 1, "dark", "Shadowphantom"),
    ("umbratad", 1, "dark", "Umbrashroud"),
    ("voidling", 1, "dark", "Voidshroud"),
    ("duskveil", 2, "dark", "Duskttyrant"),
    ("eclipseveil", 2, "dark", "Eclipsedevourer"),
    ("nightwraith", 2, "dark", "Nightdragon"),
    ("phantomwing", 2, "dark", "Phantomtyrant"),
    ("shadewraith", 2, "dark", "Shadedragon"),
    ("shadowphantom", 2, "dark", "Shadowlord"),
    ("umbrashroud", 2, "dark", "Umbralord"),
    ("voidshroud", 2, "dark", "Voidtyrant"),
    ("wraithwing", 2, "dark", "Umbrathrax"),
    ("duskttyrant", 3, "dark", None),
    ("eclipsedevourer", 3, "dark", None),
    ("nightdragon", 3, "dark", None),
    ("phantomtyrant", 3, "dark", None),
    ("shadedragon", 3, "dark", None),
    ("shadowlord", 3, "dark", None),
    ("umbralord", 3, "dark", None),
    ("umbrathrax", 3, "dark", None),
    ("voidtyrant", 3, "dark", None),
]

_STAGE_MAP: Dict[int, str] = {1: "Rookie", 2: "Champion", 3: "Ultimate"}

_STAT_TEMPLATES: Dict[str, Dict[int, Dict[str, int]]] = {
    "fire": {
        1: {"hp": 100, "mp": 40, "attack": 20, "defense": 14, "speed": 16},
        2: {"hp": 180, "mp": 80, "attack": 45, "defense": 32, "speed": 30},
        3: {"hp": 310, "mp": 140, "attack": 85, "defense": 58, "speed": 44},
    },
    "water": {
        1: {"hp": 110, "mp": 45, "attack": 15, "defense": 18, "speed": 14},
        2: {"hp": 195, "mp": 85, "attack": 35, "defense": 40, "speed": 26},
        3: {"hp": 330, "mp": 150, "attack": 65, "defense": 72, "speed": 38},
    },
    "nature": {
        1: {"hp": 95, "mp": 55, "attack": 16, "defense": 17, "speed": 13},
        2: {"hp": 170, "mp": 100, "attack": 38, "defense": 38, "speed": 22},
        3: {"hp": 300, "mp": 165, "attack": 72, "defense": 70, "speed": 28},
    },
    "electric": {
        1: {"hp": 90, "mp": 50, "attack": 17, "defense": 12, "speed": 22},
        2: {"hp": 165, "mp": 90, "attack": 42, "defense": 25, "speed": 48},
        3: {"hp": 285, "mp": 155, "attack": 78, "defense": 48, "speed": 75},
    },
    "earth": {
        1: {"hp": 130, "mp": 35, "attack": 14, "defense": 24, "speed": 9},
        2: {"hp": 240, "mp": 65, "attack": 34, "defense": 52, "speed": 14},
        3: {"hp": 380, "mp": 110, "attack": 60, "defense": 92, "speed": 16},
    },
    "dark": {
        1: {"hp": 85, "mp": 60, "attack": 18, "defense": 11, "speed": 20},
        2: {"hp": 155, "mp": 115, "attack": 40, "defense": 22, "speed": 38},
        3: {"hp": 280, "mp": 175, "attack": 80, "defense": 50, "speed": 60},
    },
}

_GROWTH_RATES: Dict[str, Dict[str, float]] = {
    "fire":     {"hp": 0.030, "mp": 0.020, "atk": 0.045, "def": 0.020, "spd": 0.025},
    "water":    {"hp": 0.035, "mp": 0.025, "atk": 0.025, "def": 0.040, "spd": 0.015},
    "nature":   {"hp": 0.025, "mp": 0.040, "atk": 0.025, "def": 0.030, "spd": 0.015},
    "electric": {"hp": 0.015, "mp": 0.030, "atk": 0.030, "def": 0.015, "spd": 0.045},
    "earth":    {"hp": 0.050, "mp": 0.010, "atk": 0.015, "def": 0.045, "spd": 0.005},
    "dark":     {"hp": 0.015, "mp": 0.045, "atk": 0.035, "def": 0.015, "spd": 0.030},
}

_ELEMENT_MOVES: Dict[str, List[Move]] = {
    "fire": _FIRE_MOVES,
    "water": _WATER_MOVES,
    "nature": _NATURE_MOVES,
    "electric": _ELECTRIC_MOVES,
    "earth": _EARTH_MOVES,
    "dark": _DARK_MOVES,
}

_ELEMENT_DESCRIPTIONS: Dict[str, str] = {
    "fire":     "A fiery creature born from molten depths, its body radiating intense heat.",
    "water":    "An aquatic being flowing with tidal energy, adapted to life beneath the waves.",
    "nature":   "A botanical entity rooted in ancient forests, drawing power from the earth.",
    "electric": "A spark-charged creature crackling with voltage, moving at blistering speed.",
    "earth":    "A rocky titan forged from the earth itself, slow but nearly indestructible.",
    "dark":     "A shadowy being drifting through the void, feeding on darkness and despair.",
}


def _make_expanded_species() -> List[Digimon]:
    """Build :class:`Digimon` instances from the expanded species table."""
    result: List[Digimon] = []
    for sid, stage_num, elem, evo_target in _EXPANDED_SPECIES_TABLE:
        stats = _STAT_TEMPLATES[elem][stage_num]
        growth = _GROWTH_RATES[elem]
        display = "".join(w.capitalize() for w in sid.split("_"))
        if evo_target and stage_num == 1:
            evo_reqs: Dict[str, int] = {"level": 10, "battles_won": 5}
        elif evo_target and stage_num == 2:
            evo_reqs = {"level": 25, "battles_won": 15, "boss_defeats": 1}
        else:
            evo_reqs = {}
        result.append(Digimon(
            name=display,
            stage=_STAGE_MAP[stage_num],
            element=elem,
            hp=stats["hp"],
            mp=stats["mp"],
            attack=stats["attack"],
            defense=stats["defense"],
            speed=stats["speed"],
            moves=_ELEMENT_MOVES[elem],
            evolution_target=evo_target,
            evolution_requirements=evo_reqs,
            description=_ELEMENT_DESCRIPTIONS[elem],
            hp_growth=growth["hp"],
            mp_growth=growth["mp"],
            atk_growth=growth["atk"],
            def_growth=growth["def"],
            spd_growth=growth["spd"],
        ))
    return result


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
        *_make_expanded_species(),
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
