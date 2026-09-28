# Data Schemas — digimon-rpg

| Field | Value |
|---|---|
| **Document** | Schema.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [ER.md](ER.md), [PRD.md](PRD.md), [Architecture.md](Architecture.md) |

---

## 1. Overview

This document defines the data schemas for **digimon-rpg** using Python
`dataclasses`. These schemas correspond to the entities defined in
[ER.md](ER.md) and the game design specified in [PRD.md](PRD.md).

All schemas are defined as pure Python dataclasses — no runtime parsing,
fully type-safe, and pygbag/WASM compatible (see [ADR-004](ADR.md#adr-004)).

---

## 2. Enumerations

```python
from enum import Enum


class Element(str, Enum):
    """Creature/skill element types."""
    FIRE = "fire"
    WATER = "water"
    NATURE = "nature"
    ELECTRIC = "electric"
    EARTH = "earth"
    DARK = "dark"
    NONE = "none"


class Stage(int, Enum):
    """Evolution stages."""
    ROOKIE = 1
    CHAMPION = 2
    ULTIMATE = 3


class StatusType(str, Enum):
    """Status effect types."""
    BURN = "burn"
    FREEZE = "freeze"
    POISON = "poison"
    PARALYSIS = "paralysis"
    SLEEP = "sleep"
    CONFUSION = "confusion"


class ItemCategory(str, Enum):
    """Item categories."""
    CONSUMABLE = "consumable"
    CAPTURE = "capture"
    KEY = "key"


class TextSpeed(str, Enum):
    """Text display speed."""
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"


class TerrainType(str, Enum):
    """Terrain types for encounter rates."""
    LOW_GRASS = "low_grass"
    TALL_GRASS = "tall_grass"
    WATER_EDGE = "water_edge"
    MOUNTAIN_PATH = "mountain_path"
    LIGHTNING_FIELD = "lightning_field"
    CAVE_INTERIOR = "cave_interior"
```

---

## 3. Core Game Data Schemas (Static)

### 3.1 SkillDef

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDef:
    """Static definition of a battle skill/move.

    Corresponds to ER entity: Skill (E3).
    """
    skill_id: str           # e.g. "scorching_tackle"
    name: str               # e.g. "Scorching Tackle"
    element: Element        # e.g. Element.FIRE
    power: int              # 20–120
    mp_cost: int            # 0 for basic attacks
    is_physical: bool       # True = physical, False = special/magic
    effect: StatusType | None     # Status applied on hit, or None
    effect_chance: float    # 0.0–1.0 probability of applying effect
    learn_level: int        # Level at which this skill is learned
```

### 3.2 SpeciesDef

```python
@dataclass(frozen=True)
class SpeciesDef:
    """Static definition of a creature species.

    Corresponds to ER entity: Species (E1).
    One instance per species (18 total: 6 lines × 3 stages).
    """
    species_id: str              # e.g. "emberling"
    name: str                    # e.g. "Emberling"
    element: Element             # e.g. Element.FIRE
    stage: Stage                 # e.g. Stage.ROOKIE
    base_hp: int                 # Base HP at Level 1
    base_mp: int                 # Base MP at Level 1
    base_attack: int             # Base Attack at Level 1
    base_defense: int            # Base Defense at Level 1
    base_speed: int              # Base Speed at Level 1
    hp_growth: float             # HP growth rate per level (e.g. 0.030)
    mp_growth: float             # MP growth rate per level
    atk_growth: float            # Attack growth rate per level
    def_growth: float            # Defense growth rate per level
    spd_growth: float            # Speed growth rate per level
    description: str             # Lore description
    sprite_key: str              # Asset key, e.g. "emberling_1"
    evolves_from: str | None     # species_id of pre-evolution (None for Rookie)
    evolves_to: str | None       # species_id of next evolution (None for Ultimate)
    evolution_level: int         # Min level to evolve (10 for R→C, 25 for C→U)
    evolution_battles: int       # Min battles won to evolve (5 or 15)
    skill_ids: tuple[str, ...]   # Skill IDs in this species' learnset (max 4)
```

### 3.3 ItemDef

```python
@dataclass(frozen=True)
class ItemDef:
    """Static definition of an item.

    Corresponds to ER entity: Item (E6).
    """
    item_id: str                 # e.g. "potion"
    name: str                    # e.g. "Potion"
    description: str             # e.g. "Restores 50 HP."
    price: int                   # Purchase price in gold
    category: ItemCategory       # CONSUMABLE, CAPTURE, or KEY
    effect_type: str             # "heal_hp", "heal_mp", "cure_status",
                                 # "revive", or "capture"
    effect_value: int            # Magnitude (e.g. 50 for Potion)
```

### 3.4 EncounterEntryDef

```python
@dataclass(frozen=True)
class EncounterEntryDef:
    """A single entry in a zone's encounter table.

    Corresponds to ER entity: EncounterEntry (E8).
    """
    species_id: str              # Wild creature species
    weight: float                # Encounter weight (proportional probability)
    min_level: int               # Minimum level in this zone
    max_level: int               # Maximum level in this zone
    base_xp: int                 # Base XP for defeating this species
```

### 3.5 ZoneDef

```python
@dataclass(frozen=True)
class ZoneDef:
    """Static definition of a world zone.

    Corresponds to ER entity: Zone (E7).
    """
    zone_id: str                       # e.g. "verdant_plains"
    name: str                          # e.g. "Verdant Plains"
    theme: str                         # e.g. "grassy_fields"
    min_level: int                     # Minimum wild level
    max_level: int                     # Maximum wild level
    encounter_entries: tuple[EncounterEntryDef, ...]  # Encounter table
    encounter_rates: dict[str, float]  # TerrainType → encounter chance per step
    gold_min: int                      # Min gold per victory
    gold_max: int                      # Max gold per victory
    boss_species_id: str               # Zone boss species_id
    boss_level: int                    # Zone boss level
    boss_gold_reward: int              # Gold reward for beating boss
    boss_xp_reward: int                # XP reward for beating boss
```

---

## 4. Runtime / Save Schemas (Persisted)

### 4.1 Creature (Instance)

```python
@dataclass
class Creature:
    """A player-owned or wild creature instance.

    Corresponds to ER entity: Creature (E2).
    This is the persisted form stored in PlayerSave.
    """
    uid: str                          # UUID for this instance
    species_id: str                   # Current species (e.g. "emberling")
    nickname: str                     # Player-given name (default: species name)
    level: int                        # 1–50
    stage: int                        # 1, 2, or 3
    xp: int                           # Cumulative XP
    current_hp: int                   # Current HP (can be < max_hp)
    current_mp: int                   # Current MP (can be < max_mp)
    battles_won: int                  # Lifetime battles won (for evolution)
    learned_skill_ids: list[str]      # Currently equipped skill IDs (max 4)
    is_fainted: bool                  # True if current_hp == 0

    # --- Derived stats (computed from SpeciesDef + level, not persisted) ---
    # These are properties computed at runtime:
    #   max_hp, max_mp, attack, defense, speed
    # See LevelingSystem.calculate_stat() in Architecture.md §6.2

    def to_dict(self) -> dict:
        """Serialize to dict for JSON save."""
        return {
            "uid": self.uid,
            "species_id": self.species_id,
            "nickname": self.nickname,
            "level": self.level,
            "stage": self.stage,
            "xp": self.xp,
            "current_hp": self.current_hp,
            "current_mp": self.current_mp,
            "battles_won": self.battles_won,
            "learned_skill_ids": self.learned_skill_ids,
            "is_fainted": self.is_fainted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Creature":
        """Deserialize from dict (JSON save)."""
        return cls(**data)
```

### 4.2 Settings

```python
@dataclass
class Settings:
    """Player display/audio settings.

    Corresponds to ER entity: Settings (E11).
    Persisted inside PlayerSave.
    """
    music_volume: int = 80        # 0–100
    sfx_volume: int = 90          # 0–100
    text_speed: str = "medium"    # "slow", "medium", "fast"
    fullscreen: bool = False

    def to_dict(self) -> dict:
        return {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "text_speed": self.text_speed,
            "fullscreen": self.fullscreen,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(**data)
```

### 4.3 PlayerSave

```python
@dataclass
class PlayerSave:
    """Top-level save object.

    Corresponds to ER entity: PlayerSave (E4).
    Serialized to JSON and stored in browser localStorage.
    """
    version: int = 1                              # Save schema version
    player_name: str = ""
    gold: int = 0
    party: list[Creature] = None                  # Max 6 creatures
    box: list[Creature] = None                    # Unlimited
    inventory: dict[str, int] = None              # item_id → count
    unlocked_zones: list[str] = None              # e.g. ["verdant_plains"]
    zone_progress: dict[str, dict] = None         # {zone_id: {boss_defeated: bool}}
    current_zone: str = "verdant_plains"
    current_x: int = 0
    current_y: int = 0
    flags: dict[str, bool] = None                 # Story/progression flags
    total_battles_won: int = 0
    total_steps: int = 0
    game_cleared: bool = False
    settings: Settings = None

    def __post_init__(self):
        if self.party is None:
            self.party = []
        if self.box is None:
            self.box = []
        if self.inventory is None:
            self.inventory = {}
        if self.unlocked_zones is None:
            self.unlocked_zones = []
        if self.zone_progress is None:
            self.zone_progress = {}
        if self.flags is None:
            self.flags = {}
        if self.settings is None:
            self.settings = Settings()

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "version": self.version,
            "player_name": self.player_name,
            "gold": self.gold,
            "party": [c.to_dict() for c in self.party],
            "box": [c.to_dict() for c in self.box],
            "inventory": self.inventory,
            "unlocked_zones": self.unlocked_zones,
            "zone_progress": self.zone_progress,
            "current_zone": self.current_zone,
            "current_x": self.current_x,
            "current_y": self.current_y,
            "flags": self.flags,
            "total_battles_won": self.total_battles_won,
            "total_steps": self.total_steps,
            "game_cleared": self.game_cleared,
            "settings": self.settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerSave":
        """Deserialize from dict (JSON load)."""
        data = dict(data)  # copy
        data["party"] = [Creature.from_dict(c) for c in data.get("party", [])]
        data["box"] = [Creature.from_dict(c) for c in data.get("box", [])]
        data["settings"] = Settings.from_dict(data.get("settings", {}))
        return cls(**data)
```

---

## 5. Transient Schemas (Not Persisted)

### 5.1 StatusEffect

```python
@dataclass
class StatusEffect:
    """A status condition applied during battle.

    Corresponds to ER entity: StatusEffect (E10).
    Transient — not persisted; cleared on battle end.
    """
    creature_uid: str             # Which creature is affected
    status_type: StatusType       # Type of status
    duration: int                 # Remaining rounds (-1 = until cured)
    stat_stages: dict[str, int]   # {"atk": +1, "def": -2} etc. (-3 to +3)
```

### 5.2 BattleState

```python
@dataclass
class BattleState:
    """Transient battle state.

    Corresponds to ER entity: BattleState (E9).
    Not persisted — exists only during an active battle.
    """
    player_active: Creature           # Player's active creature
    player_bench: list[Creature]      # Benched creatures (max 2)
    enemy_active: Creature            # Enemy's active creature
    round_number: int                 # Current round (starts at 1)
    turn_order: list[str]             # Sorted UIDs by initiative
    status_effects: dict[str, list[StatusEffect]]  # uid → effects
    is_wild: bool                     # Wild encounter (can flee)
    is_boss: bool                     # Boss battle (cannot flee)
    player_participated: list[str]    # UIDs of creatures that participated
```

---

## 6. Concrete Data Instances

### 6.1 Roster — All 18 Species

Below are the concrete species definitions. The full Python code lives in
`src/data/roster.py`.

#### Fire Line

```python
# Emberling (Rookie)
SpeciesDef(
    species_id="emberling", name="Emberling", element=Element.FIRE,
    stage=Stage.ROOKIE,
    base_hp=100, base_mp=40, base_attack=20, base_defense=14, base_speed=16,
    hp_growth=0.030, mp_growth=0.020, atk_growth=0.045,
    def_growth=0.020, spd_growth=0.025,
    description="A small, lizard-like creature with glowing ember patches...",
    sprite_key="emberling_1",
    evolves_from=None, evolves_to="pyroclaw",
    evolution_level=10, evolution_battles=5,
    skill_ids=("scorching_tackle", "ember_burst", "flame_lash", "inferno_crash"),
)

# Pyroclaw (Champion)
SpeciesDef(
    species_id="pyroclaw", name="Pyroclaw", element=Element.FIRE,
    stage=Stage.CHAMPION,
    base_hp=180, base_mp=80, base_attack=45, base_defense=32, base_speed=30,
    hp_growth=0.030, mp_growth=0.020, atk_growth=0.045,
    def_growth=0.020, spd_growth=0.025,
    description="A muscular, quadrupedal beast with molten veins...",
    sprite_key="pyroclaw_2",
    evolves_from="emberling", evolves_to="infernosaur",
    evolution_level=25, evolution_battles=15,
    skill_ids=("scorching_tackle", "ember_burst", "flame_lash", "inferno_crash"),
)

# Infernosaur (Ultimate)
SpeciesDef(
    species_id="infernosaur", name="Infernosaur", element=Element.FIRE,
    stage=Stage.ULTIMATE,
    base_hp=310, base_mp=140, base_attack=85, base_defense=58, base_speed=44,
    hp_growth=0.030, mp_growth=0.020, atk_growth=0.045,
    def_growth=0.020, spd_growth=0.025,
    description="A great, draconic saurian wreathed in perpetual flame...",
    sprite_key="infernosaur_3",
    evolves_from="pyroclaw", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("scorching_tackle", "ember_burst", "flame_lash", "inferno_crash"),
)
```

#### Water Line

```python
# Aquapup (Rookie)
SpeciesDef(
    species_id="aquapup", name="Aquapup", element=Element.WATER,
    stage=Stage.ROOKIE,
    base_hp=110, base_mp=45, base_attack=15, base_defense=18, base_speed=14,
    hp_growth=0.035, mp_growth=0.025, atk_growth=0.025,
    def_growth=0.040, spd_growth=0.015,
    description="A round, seal-like creature with translucent fins...",
    sprite_key="aquapup_1",
    evolves_from=None, evolves_to="tsunamut",
    evolution_level=10, evolution_battles=5,
    skill_ids=("water_slap", "bubble_spray", "aqua_jet", "tidal_force"),
)

# Tsunamut (Champion)
SpeciesDef(
    species_id="tsunamut", name="Tsunamut", element=Element.WATER,
    stage=Stage.CHAMPION,
    base_hp=195, base_mp=85, base_attack=35, base_defense=40, base_speed=26,
    hp_growth=0.035, mp_growth=0.025, atk_growth=0.025,
    def_growth=0.040, spd_growth=0.015,
    description="A powerful, otter-like creature with water jets...",
    sprite_key="tsunamut_2",
    evolves_from="aquapup", evolves_to="leviathore",
    evolution_level=25, evolution_battles=15,
    skill_ids=("water_slap", "bubble_spray", "aqua_jet", "tidal_force"),
)

# Leviathore (Ultimate)
SpeciesDef(
    species_id="leviathore", name="Leviathore", element=Element.WATER,
    stage=Stage.ULTIMATE,
    base_hp=330, base_mp=150, base_attack=65, base_defense=72, base_speed=38,
    hp_growth=0.035, mp_growth=0.025, atk_growth=0.025,
    def_growth=0.040, spd_growth=0.015,
    description="A colossal, serpentine leviathan of living water...",
    sprite_key="leviathore_3",
    evolves_from="tsunamut", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("water_slap", "bubble_spray", "aqua_jet", "tidal_force"),
)
```

#### Nature Line

```python
# Seedkit (Rookie)
SpeciesDef(
    species_id="seedkit", name="Seedkit", element=Element.NATURE,
    stage=Stage.ROOKIE,
    base_hp=95, base_mp=55, base_attack=16, base_defense=17, base_speed=13,
    hp_growth=0.025, mp_growth=0.040, atk_growth=0.025,
    def_growth=0.030, spd_growth=0.015,
    description="A small, leafy creature resembling a sprouting bulb...",
    sprite_key="seedkit_1",
    evolves_from=None, evolves_to="thornbloom",
    evolution_level=10, evolution_battles=5,
    skill_ids=("vine_whip", "leaf_storm", "root_bind", "bloom_burst"),
)

# Thornbloom (Champion)
SpeciesDef(
    species_id="thornbloom", name="Thornbloom", element=Element.NATURE,
    stage=Stage.CHAMPION,
    base_hp=170, base_mp=100, base_attack=38, base_defense=38, base_speed=22,
    hp_growth=0.025, mp_growth=0.040, atk_growth=0.025,
    def_growth=0.030, spd_growth=0.015,
    description="An elegant, plant-humanoid covered in petals and thorn vines...",
    sprite_key="thornbloom_2",
    evolves_from="seedkit", evolves_to="verdant_titan",
    evolution_level=25, evolution_battles=15,
    skill_ids=("vine_whip", "leaf_storm", "root_bind", "bloom_burst"),
)

# Verdant Titan (Ultimate)
SpeciesDef(
    species_id="verdant_titan", name="Verdant Titan", element=Element.NATURE,
    stage=Stage.ULTIMATE,
    base_hp=300, base_mp=165, base_attack=72, base_defense=70, base_speed=28,
    hp_growth=0.025, mp_growth=0.040, atk_growth=0.025,
    def_growth=0.030, spd_growth=0.015,
    description="A towering, ancient tree-golem of petrified wood...",
    sprite_key="verdant_titan_3",
    evolves_from="thornbloom", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("vine_whip", "leaf_storm", "root_bind", "bloom_burst"),
)
```

#### Electric Line

```python
# Stormwing (Rookie)
SpeciesDef(
    species_id="stormwing", name="Stormwing", element=Element.ELECTRIC,
    stage=Stage.ROOKIE,
    base_hp=90, base_mp=50, base_attack=17, base_defense=12, base_speed=22,
    hp_growth=0.015, mp_growth=0.030, atk_growth=0.030,
    def_growth=0.015, spd_growth=0.045,
    description="A tiny raptor with crackling feathers...",
    sprite_key="stormwing_1",
    evolves_from=None, evolves_to="voltalon",
    evolution_level=10, evolution_battles=5,
    skill_ids=("spark_bolt", "static_feathers", "thunderclap", "storm_dive"),
)

# Voltalon (Champion)
SpeciesDef(
    species_id="voltalon", name="Voltalon", element=Element.ELECTRIC,
    stage=Stage.CHAMPION,
    base_hp=165, base_mp=90, base_attack=42, base_defense=25, base_speed=48,
    hp_growth=0.015, mp_growth=0.030, atk_growth=0.030,
    def_growth=0.015, spd_growth=0.045,
    description="A large, eagle-like predator with crackling wings...",
    sprite_key="voltalon_2",
    evolves_from="stormwing", evolves_to="thundergod",
    evolution_level=25, evolution_battles=15,
    skill_ids=("spark_bolt", "static_feathers", "thunderclap", "storm_dive"),
)

# Thundergod (Ultimate)
SpeciesDef(
    species_id="thundergod", name="Thundergod", element=Element.ELECTRIC,
    stage=Stage.ULTIMATE,
    base_hp=285, base_mp=155, base_attack=78, base_defense=48, base_speed=75,
    hp_growth=0.015, mp_growth=0.030, atk_growth=0.030,
    def_growth=0.015, spd_growth=0.045,
    description="A mythical, phoenix-like storm deity...",
    sprite_key="thundergod_3",
    evolves_from="voltalon", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("spark_bolt", "static_feathers", "thunderclap", "storm_dive"),
)
```

#### Earth Line

```python
# Rockbash (Rookie)
SpeciesDef(
    species_id="rockbash", name="Rockbash", element=Element.EARTH,
    stage=Stage.ROOKIE,
    base_hp=130, base_mp=35, base_attack=14, base_defense=24, base_speed=9,
    hp_growth=0.050, mp_growth=0.010, atk_growth=0.015,
    def_growth=0.045, spd_growth=0.005,
    description="A stocky, armadillo-like creature with stone plates...",
    sprite_key="rockbash_1",
    evolves_from=None, evolves_to="mountainhide",
    evolution_level=10, evolution_battles=5,
    skill_ids=("rock_throw", "stone_shell", "quake_stomp", "mountain_crush"),
)

# Mountainhide (Champion)
SpeciesDef(
    species_id="mountainhide", name="Mountainhide", element=Element.EARTH,
    stage=Stage.CHAMPION,
    base_hp=240, base_mp=65, base_attack=34, base_defense=52, base_speed=14,
    hp_growth=0.050, mp_growth=0.010, atk_growth=0.015,
    def_growth=0.045, spd_growth=0.005,
    description="A massive, bear-like colossus with a mountain-carapace...",
    sprite_key="mountainhide_2",
    evolves_from="rockbash", evolves_to="terraroc",
    evolution_level=25, evolution_battles=15,
    skill_ids=("rock_throw", "stone_shell", "quake_stomp", "mountain_crush"),
)

# Terraroc (Ultimate)
SpeciesDef(
    species_id="terraroc", name="Terraroc", element=Element.EARTH,
    stage=Stage.ULTIMATE,
    base_hp=380, base_mp=110, base_attack=60, base_defense=92, base_speed=16,
    hp_growth=0.050, mp_growth=0.010, atk_growth=0.015,
    def_growth=0.045, spd_growth=0.005,
    description="A living mountain given form and fury...",
    sprite_key="terraroc_3",
    evolves_from="mountainhide", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("rock_throw", "stone_shell", "quake_stomp", "mountain_crush"),
)
```

#### Dark Line

```python
# Chaospuff (Rookie)
SpeciesDef(
    species_id="chaospuff", name="Chaospuff", element=Element.DARK,
    stage=Stage.ROOKIE,
    base_hp=85, base_mp=60, base_attack=18, base_defense=11, base_speed=20,
    hp_growth=0.015, mp_growth=0.045, atk_growth=0.035,
    def_growth=0.015, spd_growth=0.030,
    description="A wispy, shadow-like creature that drifts...",
    sprite_key="chaospuff_1",
    evolves_from=None, evolves_to="wraithwing",
    evolution_level=10, evolution_battles=5,
    skill_ids=("shadow_poke", "dark_mist", "void_claw", "eclipse_roar"),
)

# Wraithwing (Champion)
SpeciesDef(
    species_id="wraithwing", name="Wraithwing", element=Element.DARK,
    stage=Stage.CHAMPION,
    base_hp=155, base_mp=115, base_attack=40, base_defense=22, base_speed=38,
    hp_growth=0.015, mp_growth=0.045, atk_growth=0.035,
    def_growth=0.015, spd_growth=0.030,
    description="A haunting, bat-like specter of living shadow...",
    sprite_key="wraithwing_2",
    evolves_from="chaospuff", evolves_to="umbrathrax",
    evolution_level=25, evolution_battles=15,
    skill_ids=("shadow_poke", "dark_mist", "void_claw", "eclipse_roar"),
)

# Umbrathrax (Ultimate)
SpeciesDef(
    species_id="umbrathrax", name="Umbrathrax", element=Element.DARK,
    stage=Stage.ULTIMATE,
    base_hp=280, base_mp=175, base_attack=80, base_defense=50, base_speed=60,
    hp_growth=0.015, mp_growth=0.045, atk_growth=0.035,
    def_growth=0.015, spd_growth=0.030,
    description="A nightmare made manifest — a shadow-dragon...",
    sprite_key="umbrathrax_3",
    evolves_from="wraithwing", evolves_to=None,
    evolution_level=0, evolution_battles=0,
    skill_ids=("shadow_poke", "dark_mist", "void_claw", "eclipse_roar"),
)
```

### 6.2 Skill Definitions

```python
# Fire line skills
SkillDef(skill_id="scorching_tackle", name="Scorching Tackle",
         element=Element.FIRE, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="ember_burst", name="Ember Burst",
         element=Element.FIRE, power=40, mp_cost=10, is_physical=False,
         effect=None, effect_chance=0.0, learn_level=6)
SkillDef(skill_id="flame_lash", name="Flame Lash",
         element=Element.FIRE, power=65, mp_cost=18, is_physical=False,
         effect=StatusType.BURN, effect_chance=0.10, learn_level=14)
SkillDef(skill_id="inferno_crash", name="Inferno Crash",
         element=Element.FIRE, power=90, mp_cost=30, is_physical=False,
         effect=StatusType.BURN, effect_chance=0.20, learn_level=24)

# Water line skills
SkillDef(skill_id="water_slap", name="Water Slap",
         element=Element.WATER, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="bubble_spray", name="Bubble Spray",
         element=Element.WATER, power=40, mp_cost=10, is_physical=False,
         effect=None, effect_chance=0.0, learn_level=6)
SkillDef(skill_id="aqua_jet", name="Aqua Jet",
         element=Element.WATER, power=65, mp_cost=18, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=14)
SkillDef(skill_id="tidal_force", name="Tidal Force",
         element=Element.WATER, power=90, mp_cost=30, is_physical=False,
         effect=StatusType.FREEZE, effect_chance=0.15, learn_level=24)

# Nature line skills
SkillDef(skill_id="vine_whip", name="Vine Whip",
         element=Element.NATURE, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="leaf_storm", name="Leaf Storm",
         element=Element.NATURE, power=40, mp_cost=10, is_physical=False,
         effect=None, effect_chance=0.0, learn_level=6)
SkillDef(skill_id="root_bind", name="Root Bind",
         element=Element.NATURE, power=65, mp_cost=18, is_physical=False,
         effect=StatusType.PARALYSIS, effect_chance=0.15, learn_level=14)
SkillDef(skill_id="bloom_burst", name="Bloom Burst",
         element=Element.NATURE, power=90, mp_cost=30, is_physical=False,
         effect=StatusType.POISON, effect_chance=0.20, learn_level=24)

# Electric line skills
SkillDef(skill_id="spark_bolt", name="Spark Bolt",
         element=Element.ELECTRIC, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="static_feathers", name="Static Feathers",
         element=Element.ELECTRIC, power=40, mp_cost=10, is_physical=False,
         effect=StatusType.PARALYSIS, effect_chance=0.10, learn_level=6)
SkillDef(skill_id="thunderclap", name="Thunderclap",
         element=Element.ELECTRIC, power=65, mp_cost=18, is_physical=False,
         effect=StatusType.PARALYSIS, effect_chance=0.20, learn_level=14)
SkillDef(skill_id="storm_dive", name="Storm Dive",
         element=Element.ELECTRIC, power=90, mp_cost=30, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=24)

# Earth line skills
SkillDef(skill_id="rock_throw", name="Rock Throw",
         element=Element.EARTH, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="stone_shell", name="Stone Shell",
         element=Element.EARTH, power=40, mp_cost=10, is_physical=False,
         effect=None, effect_chance=0.0, learn_level=6)
SkillDef(skill_id="quake_stomp", name="Quake Stomp",
         element=Element.EARTH, power=65, mp_cost=18, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=14)
SkillDef(skill_id="mountain_crush", name="Mountain Crush",
         element=Element.EARTH, power=90, mp_cost=30, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=24)

# Dark line skills
SkillDef(skill_id="shadow_poke", name="Shadow Poke",
         element=Element.DARK, power=20, mp_cost=0, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=1)
SkillDef(skill_id="dark_mist", name="Dark Mist",
         element=Element.DARK, power=40, mp_cost=10, is_physical=False,
         effect=StatusType.CONFUSION, effect_chance=0.15, learn_level=6)
SkillDef(skill_id="void_claw", name="Void Claw",
         element=Element.DARK, power=65, mp_cost=18, is_physical=True,
         effect=None, effect_chance=0.0, learn_level=14)
SkillDef(skill_id="eclipse_roar", name="Eclipse Roar",
         element=Element.DARK, power=90, mp_cost=30, is_physical=False,
         effect=StatusType.SLEEP, effect_chance=0.15, learn_level=24)
```

### 6.3 Item Definitions

```python
ITEMS = {
    "potion": ItemDef(
        item_id="potion", name="Potion",
        description="Restores 50 HP.", price=100,
        category=ItemCategory.CONSUMABLE,
        effect_type="heal_hp", effect_value=50,
    ),
    "super_potion": ItemDef(
        item_id="super_potion", name="Super Potion",
        description="Restores 150 HP.", price=300,
        category=ItemCategory.CONSUMABLE,
        effect_type="heal_hp", effect_value=150,
    ),
    "elixir": ItemDef(
        item_id="elixir", name="Elixir",
        description="Restores 40 MP.", price=200,
        category=ItemCategory.CONSUMABLE,
        effect_type="heal_mp", effect_value=40,
    ),
    "antidote": ItemDef(
        item_id="antidote", name="Antidote",
        description="Cures poison.", price=50,
        category=ItemCategory.CONSUMABLE,
        effect_type="cure_status", effect_value=0,
    ),
    "revive": ItemDef(
        item_id="revive", name="Revive",
        description="Revives a fainted creature at 50% HP.", price=500,
        category=ItemCategory.CONSUMABLE,
        effect_type="revive", effect_value=0,
    ),
    "digi_core": ItemDef(
        item_id="digi_core", name="Digi-Core",
        description="Capture device for wild creatures.", price=300,
        category=ItemCategory.CAPTURE,
        effect_type="capture", effect_value=0,
    ),
    "training_stone": ItemDef(
        item_id="training_stone", name="Training Stone",
        description="Benched creatures gain 50% XP.", price=1000,
        category=ItemCategory.KEY,
        effect_type="buff", effect_value=0,
    ),
}
```

### 6.4 Zone Encounter Tables

```python
# Zone 1: Verdant Plains
ZoneDef(
    zone_id="verdant_plains",
    name="Verdant Plains",
    theme="grassy_fields",
    min_level=1, max_level=12,
    encounter_entries=(
        EncounterEntryDef(species_id="emberling", weight=0.20,
                          min_level=1, max_level=6, base_xp=25),
        EncounterEntryDef(species_id="aquapup", weight=0.20,
                          min_level=1, max_level=6, base_xp=25),
        EncounterEntryDef(species_id="seedkit", weight=0.25,
                          min_level=2, max_level=8, base_xp=25),
        EncounterEntryDef(species_id="rockbash", weight=0.15,
                          min_level=3, max_level=9, base_xp=25),
        EncounterEntryDef(species_id="stormwing", weight=0.10,
                          min_level=4, max_level=10, base_xp=30),
        EncounterEntryDef(species_id="chaospuff", weight=0.10,
                          min_level=5, max_level=12, base_xp=35),
    ),
    encounter_rates={
        "low_grass": 0.15,
        "tall_grass": 0.25,
        "water_edge": 0.12,
    },
    gold_min=8, gold_max=20,
    boss_species_id="verdant_titan",
    boss_level=14,
    boss_gold_reward=200,
    boss_xp_reward=500,
)

# Zone 2: Storm Peaks
ZoneDef(
    zone_id="storm_peaks",
    name="Storm Peaks",
    theme="mountain_lightning",
    min_level=15, max_level=28,
    encounter_entries=(
        EncounterEntryDef(species_id="stormwing", weight=0.25,
                          min_level=15, max_level=22, base_xp=45),
        EncounterEntryDef(species_id="chaospuff", weight=0.20,
                          min_level=16, max_level=24, base_xp=45),
        EncounterEntryDef(species_id="rockbash", weight=0.20,
                          min_level=17, max_level=25, base_xp=45),
        EncounterEntryDef(species_id="pyroclaw", weight=0.10,
                          min_level=18, max_level=26, base_xp=55),
        EncounterEntryDef(species_id="tsunamut", weight=0.10,
                          min_level=20, max_level=27, base_xp=55),
        EncounterEntryDef(species_id="thornbloom", weight=0.10,
                          min_level=20, max_level=28, base_xp=55),
        EncounterEntryDef(species_id="voltalon", weight=0.05,
                          min_level=20, max_level=28, base_xp=75),
    ),
    encounter_rates={
        "mountain_path": 0.22,
        "lightning_field": 0.30,
        "cave_interior": 0.18,
    },
    gold_min=20, gold_max=40,
    boss_species_id="thundergod",
    boss_level=28,
    boss_gold_reward=400,
    boss_xp_reward=1500,
)
```

### 6.5 Type Effectiveness Table

```python
# Type multiplier: attacker_element → {defender_element → multiplier}
TYPE_CHART: dict[Element, dict[Element, float]] = {
    Element.FIRE: {
        Element.FIRE: 1.0, Element.WATER: 0.5, Element.NATURE: 2.0,
        Element.ELECTRIC: 1.0, Element.EARTH: 0.75, Element.DARK: 1.0,
    },
    Element.WATER: {
        Element.FIRE: 2.0, Element.WATER: 1.0, Element.NATURE: 0.75,
        Element.ELECTRIC: 0.5, Element.EARTH: 2.0, Element.DARK: 1.0,
    },
    Element.NATURE: {
        Element.FIRE: 0.75, Element.WATER: 2.0, Element.NATURE: 1.0,
        Element.ELECTRIC: 1.0, Element.EARTH: 2.0, Element.DARK: 1.0,
    },
    Element.ELECTRIC: {
        Element.FIRE: 1.0, Element.WATER: 2.0, Element.NATURE: 1.0,
        Element.ELECTRIC: 0.75, Element.EARTH: 0.5, Element.DARK: 2.0,
    },
    Element.EARTH: {
        Element.FIRE: 2.0, Element.WATER: 0.75, Element.NATURE: 0.75,
        Element.ELECTRIC: 2.0, Element.EARTH: 1.0, Element.DARK: 1.0,
    },
    Element.DARK: {
        Element.FIRE: 1.0, Element.WATER: 1.0, Element.NATURE: 1.0,
        Element.ELECTRIC: 0.5, Element.EARTH: 1.0, Element.DARK: 2.0,
    },
}
```

---

## 7. Formulas Reference

### 7.1 XP Curve

```python
def xp_to_reach_level(level: int) -> int:
    """Total cumulative XP needed to reach `level` from level 1."""
    return int(10 * (level - 1) ** 2.6)
```

### 7.2 Stat at Level

```python
def calculate_stat(base: int, growth_rate: float, level: int) -> int:
    """Calculate a stat at a given level.

    Formula: S(L) = floor(S_base * (1 + growth_rate * (L - 1)))
    """
    return int(base * (1 + growth_rate * (level - 1)))
```

### 7.3 Damage Calculation

```python
def calculate_base_damage(
    attacker_level: int,
    attack_power: int,
    attacker_stat: int,
    defender_stat: int,
) -> float:
    """Base damage before multipliers (PRD §5.3)."""
    return (
        ((2 * attacker_level) / 5 + 2)
        * attack_power
        * (attacker_stat / defender_stat)
        / 50
    ) + 2
```

### 7.4 Flee Chance

```python
def flee_chance(player_speed: int, enemy_speed: int) -> float:
    """Probability of successfully fleeing (PRD §5.8)."""
    return min(0.90, max(0.40, 0.40 + (player_speed - enemy_speed) * 0.01))
```

### 7.5 Capture Chance

```python
def capture_chance(
    target_hp: int,
    target_max_hp: int,
    has_status: bool,
) -> float:
    """Probability of capturing a wild creature (PRD §6.2)."""
    chance = 0.42
    if target_hp <= 0.05 * target_max_hp:
        chance += 0.15
    if has_status:
        chance += 0.05
    return min(chance, 0.90)
```

### 7.6 Evolution Check

```python
def can_evolve(
    creature: Creature,
    species: SpeciesDef,
    boss_defeats: int,
) -> bool:
    """Check if a creature meets evolution requirements (PRD §4)."""
    if species.evolves_to is None:
        return False  # Already at Ultimate stage
    if creature.level < species.evolution_level:
        return False
    if creature.battles_won < species.evolution_battles:
        return False
    if species.stage == Stage.CHAMPION and boss_defeats < 1:
        return False  # Champion→Ultimate requires 1 boss defeat
    return True
```

---

## 8. Related Documents

- [ER.md](ER.md) — Entity-relationship model
- [PRD.md](PRD.md) — Game design (roster, stats, formulas)
- [API.md](API.md) — Module/function API reference
- [Architecture.md](Architecture.md) — System architecture
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
