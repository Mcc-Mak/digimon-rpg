# Entity-Relationship Model (ER) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | ER.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [PRD.md](PRD.md), [Schema.md](Schema.md), [Architecture.md](Architecture.md) |

---

## 1. Overview

This document describes the entity-relationship model for **digimon-rpg**. It
defines the core entities, their attributes, and the relationships between them.
The model informs the data schemas in [Schema.md](Schema.md) and the save system
architecture.

---

## 2. Entities

### 2.1 Entity List

| # | Entity | Description |
|---|---|---|
| E1 | **Species** | A creature species definition (e.g., Emberling, Pyroclaw). Static game data. |
| E2 | **Creature** | A player-owned or wild creature instance. Has level, stats, XP, etc. |
| E3 | **Skill** | A battle skill/move definition. Static game data. |
| E4 | **PlayerSave** | The top-level save object containing all player state. |
| E5 | **Inventory** | Collection of items owned by the player. |
| E6 | **Item** | An item definition (Potion, Digi-Core, etc.). Static game data. |
| E7 | **Zone** | A world zone definition with encounter tables. Static game data. |
| E8 | **EncounterEntry** | A single entry in a zone's encounter table. |
| E9 | **BattleState** | Transient battle state (not persisted). |
| E10 | **StatusEffect** | A status condition applied during battle (not persisted). |
| E11 | **Settings** | Player display/audio settings. |

---

## 3. Entity Details

### E1: Species

| Attribute | Type | Description |
|---|---|---|
| `species_id` | str (PK) | Unique identifier (e.g., `"emberling"`) |
| `name` | str | Display name (e.g., `"Emberling"`) |
| `element` | str | Element type: `fire`, `water`, `nature`, `electric`, `earth`, `dark` |
| `stage` | int | Evolution stage: 1 (Rookie), 2 (Champion), 3 (Ultimate) |
| `base_hp` | int | Base HP stat at Level 1 |
| `base_mp` | int | Base MP stat at Level 1 |
| `base_attack` | int | Base Attack stat at Level 1 |
| `base_defense` | int | Base Defense stat at Level 1 |
| `base_speed` | int | Base Speed stat at Level 1 |
| `hp_growth` | float | HP growth rate per level |
| `mp_growth` | float | MP growth rate per level |
| `atk_growth` | float | Attack growth rate per level |
| `def_growth` | float | Defense growth rate per level |
| `spd_growth` | float | Speed growth rate per level |
| `description` | str | Lore description |
| `sprite_key` | str | Asset key for sprite |
| `evolves_from` | str (FK → Species) | Species this one evolves from (None for Rookie) |
| `evolves_to` | str (FK → Species) | Species this one evolves to (None for Ultimate) |
| `skill_ids` | list[str] (FK → Skill) | Skills available to this species |

**Relationships:**
- A `Species` **evolves from** at most one `Species` (self-referential).
- A `Species` **evolves to** at most one `Species` (self-referential).
- A `Species` **has** 1–4 `Skill` entities.
- A `Species` **appears in** 0+ `EncounterEntry` entities.

### E2: Creature

| Attribute | Type | Description |
|---|---|---|
| `uid` | str (PK) | Unique instance identifier (UUID) |
| `species_id` | str (FK → Species) | Current species |
| `nickname` | str | Player-given nickname (default: species name) |
| `level` | int | Current level (1–50) |
| `stage` | int | Current evolution stage (1–3) |
| `xp` | int | Current total XP |
| `current_hp` | int | Current HP (battle-dynamic) |
| `current_mp` | int | Current MP (battle-dynamic) |
| `battles_won` | int | Lifetime battles won (for evolution tracking) |
| `learned_skills` | list[str] (FK → Skill) | Currently equipped skills (max 4) |
| `is_fainted` | bool | Whether this creature has 0 HP |

**Derived attributes** (computed from Species + level, not stored):
- `max_hp`, `max_mp`, `attack`, `defense`, `speed`

**Relationships:**
- A `Creature` **is an instance of** one `Species`.
- A `Creature` **belongs to** one `PlayerSave` (either in `party` or `box`).
- A `Creature` **knows** 1–4 `Skill` entities.

### E3: Skill

| Attribute | Type | Description |
|---|---|---|
| `skill_id` | str (PK) | Unique identifier (e.g., `"scorching_tackle"`) |
| `name` | str | Display name |
| `element` | str | Element type: `fire`, `water`, `nature`, `electric`, `earth`, `dark`, `none` |
| `power` | int | Move power (20–120) |
| `mp_cost` | int | MP cost (0 for basic attacks) |
| `is_physical` | bool | True = physical, False = special/magic |
| `effect` | str (nullable) | Status effect: `burn`, `freeze`, `poison`, `paralysis`, `sleep`, `confusion`, or None |
| `effect_chance` | float | Probability of applying effect (0.0–1.0) |
| `learn_level` | int | Level at which this skill is learned |

**Relationships:**
- A `Skill` **is learned by** 1+ `Species` entities.
- A `Skill` **is known by** 0+ `Creature` instances.

### E4: PlayerSave

| Attribute | Type | Description |
|---|---|---|
| `version` | int | Save schema version |
| `player_name` | str | Tamer name |
| `gold` | int | Current gold |
| `party` | list[Creature] (FK → Creature) | Active party (max 6) |
| `box` | list[Creature] (FK → Creature) | Stored creatures (unlimited) |
| `inventory` | dict[str, int] (FK → Item) | Item ID → count |
| `unlocked_zones` | list[str] (FK → Zone) | Zone IDs the player can access |
| `zone_progress` | dict[str, dict] | Per-zone progress flags |
| `current_zone` | str (FK → Zone) | Current zone ID |
| `current_x` | int | Player X position on map |
| `current_y` | int | Player Y position on map |
| `flags` | dict[str, bool] | Story/progression flags |
| `total_battles_won` | int | Lifetime battles won |
| `total_steps` | int | Lifetime steps walked |
| `game_cleared` | bool | Whether final boss is defeated |
| `settings` | Settings (FK → Settings) | Display/audio settings |

**Relationships:**
- A `PlayerSave` **owns** 0–6 `Creature` entities (party).
- A `PlayerSave` **owns** 0+ `Creature` entities (box).
- A `PlayerSave` **has** one `Inventory` (embedded).
- A `PlayerSave` **has** one `Settings` (embedded).
- A `PlayerSave` **references** 1+ `Zone` entities (unlocked zones).
- A `PlayerSave` **is currently in** one `Zone`.

### E5: Inventory (embedded in PlayerSave)

| Attribute | Type | Description |
|---|---|---|
| `items` | dict[str, int] | Mapping of item_id → count |

**Relationships:**
- An `Inventory` **contains** 0+ `Item` types with quantities.

### E6: Item

| Attribute | Type | Description |
|---|---|---|
| `item_id` | str (PK) | Unique identifier (e.g., `"potion"`) |
| `name` | str | Display name |
| `description` | str | Effect description |
| `price` | int | Purchase price in gold |
| `category` | str | `consumable`, `capture`, `key` |
| `effect_type` | str | `heal_hp`, `heal_mp`, `cure_status`, `revive`, `capture` |
| `effect_value` | int | Magnitude (e.g., 50 HP for Potion) |

**Relationships:**
- An `Item` **appears in** 0+ `Inventory` instances.

### E7: Zone

| Attribute | Type | Description |
|---|---|---|
| `zone_id` | str (PK) | Unique identifier (e.g., `"verdant_plains"`) |
| `name` | str | Display name |
| `theme` | str | Visual theme |
| `min_level` | int | Minimum wild creature level |
| `max_level` | int | Maximum wild creature level |
| `encounter_entries` | list[EncounterEntry] (FK → EncounterEntry) | Encounter table |
| `encounter_rates` | dict[str, float] | Terrain → encounter chance |
| `gold_min` | int | Minimum gold per victory |
| `gold_max` | int | Maximum gold per victory |
| `boss_species_id` | str (FK → Species) | Zone boss species |
| `boss_level` | int | Zone boss level |

**Relationships:**
- A `Zone` **contains** 1+ `EncounterEntry` entities.
- A `Zone` **has** one boss `Species`.

### E8: EncounterEntry

| Attribute | Type | Description |
|---|---|---|
| `species_id` | str (FK → Species) | Wild creature species |
| `weight` | float | Encounter weight (probability proportion) |
| `min_level` | int | Minimum level for this species in this zone |
| `max_level` | int | Maximum level for this species in this zone |
| `base_xp` | int | Base XP awarded for defeating this species |

**Relationships:**
- An `EncounterEntry` **references** one `Species`.
- An `EncounterEntry` **belongs to** one `Zone`.

### E9: BattleState (transient, not persisted)

| Attribute | Type | Description |
|---|---|---|
| `player_active` | Creature (FK → Creature) | Player's active creature |
| `player_bench` | list[Creature] | Benched creatures (max 2) |
| `enemy_active` | Creature | Enemy's active creature |
| `round_number` | int | Current round |
| `turn_order` | list[Creature] | Sorted initiative order |
| `status_effects` | dict[str, StatusEffect] | Active status effects per creature UID |
| `is_wild` | bool | Whether this is a wild encounter |
| `is_boss` | bool | Whether this is a boss battle |

**Relationships:**
- A `BattleState` **involves** 1 `Creature` (player active) + 0–2 (bench).
- A `BattleState` **involves** 1 `Creature` (enemy).
- A `BattleState` **has** 0+ `StatusEffect` entities.

### E10: StatusEffect (transient, not persisted)

| Attribute | Type | Description |
|---|---|---|
| `creature_uid` | str (FK → Creature) | Affected creature |
| `status_type` | str | `burn`, `freeze`, `poison`, `paralysis`, `sleep`, `confusion` |
| `duration` | int | Remaining rounds (−1 for permanent until cured) |
| `stat_stages` | dict[str, int] | Stat buff/debuff stages (atk, def: −3 to +3) |

**Relationships:**
- A `StatusEffect` **affects** one `Creature`.

### E11: Settings (embedded in PlayerSave)

| Attribute | Type | Description |
|---|---|---|
| `music_volume` | int | Music volume (0–100) |
| `sfx_volume` | int | SFX volume (0–100) |
| `text_speed` | str | `slow`, `medium`, `fast` |
| `fullscreen` | bool | Fullscreen mode |

**Relationships:**
- `Settings` **belongs to** one `PlayerSave`.

---

## 4. ER Diagram (ASCII)

```
┌──────────────┐     evolves_from     ┌──────────────┐
│   Species    │◄─────────────────────│   Species    │
│──────────────│     evolves_to       │  (Champion)  │
│ species_id PK│─────────────────────►│              │
│ name         │                      │              │
│ element      │                      └──────────────┘
│ stage        │                            │
│ base_*       │                            │ evolves_to
│ *_growth     │                            ▼
│ skill_ids ───┼─►┌──────────┐        ┌──────────────┐
│ sprite_key   │   │  Skill   │        │   Species    │
└──────┬───────┘   │──────────│        │  (Ultimate)  │
       │           │ skill_id │        └──────────────┘
       │ 1         │ name     │
       │           │ element  │
       ▼           │ power    │
┌──────────────┐   │ mp_cost  │
│   Creature   │   │ effect   │
│──────────────│   └──────────┘
│ uid PK       │
│ species_id FK│
│ nickname     │
│ level        │
│ stage        │
│ xp           │
│ current_hp   │
│ current_mp   │
│ battles_won  │
│ learned_skls │
│ is_fainted   │
└──────┬───────┘
       │
       │ N (party: max 6, box: unlimited)
       │
       ▼
┌──────────────────┐     has     ┌──────────────┐
│   PlayerSave     │────────────►│   Settings   │
│──────────────────│             │──────────────│
│ version          │             │ music_volume │
│ player_name      │             │ sfx_volume   │
│ gold             │             │ text_speed   │
│ party [Creature] │             │ fullscreen   │
│ box [Creature]   │             └──────────────┘
│ inventory ───────┼─►┌──────────────┐
│ unlocked_zones   │   │  Inventory   │
│ zone_progress    │   │──────────────│
│ current_zone FK  │   │ items{}      │──►┌──────────┐
│ current_x/y      │   └──────────────┘   │   Item   │
│ flags            │                      │──────────│
│ settings ────────┤                      │ item_id  │
│ game_cleared     │                      │ name     │
└──────────────────┘                      │ price    │
       │                                  │ category │
       │ currently in                     │ effect   │
       ▼                                  └──────────┘
┌──────────────┐    contains    ┌──────────────────┐
│    Zone      │───────────────►│ EncounterEntry   │
│──────────────│                │──────────────────│
│ zone_id PK   │                │ species_id FK    │──► Species
│ name         │                │ weight           │
│ min_level    │                │ min_level        │
│ max_level    │                │ max_level        │
│ entries ─────┤                │ base_xp          │
│ encounter_rt │                └──────────────────┘
│ gold_min/max │
│ boss_species │──► Species
│ boss_level   │
└──────────────┘
```

---

## 5. Cardinality Summary

| Relationship | Cardinality |
|---|---|
| Species → Species (evolves_from) | N:1 (each species evolves from at most 1) |
| Species → Species (evolves_to) | 1:1 (each species evolves to at most 1) |
| Species → Skill | 1:N (each species has 1–4 skills) |
| Species → Creature | 1:N (one species, many instances) |
| Species → EncounterEntry | 1:N (one species, many encounter entries) |
| PlayerSave → Creature (party) | 1:N (1 save owns 0–6 party creatures) |
| PlayerSave → Creature (box) | 1:N (1 save owns 0+ box creatures) |
| PlayerSave → Inventory | 1:1 (embedded) |
| PlayerSave → Settings | 1:1 (embedded) |
| PlayerSave → Zone | 1:N (1 save references 1+ unlocked zones) |
| Zone → EncounterEntry | 1:N (1 zone has 1+ encounter entries) |
| EncounterEntry → Species | N:1 (many entries reference 1 species) |
| BattleState → Creature | 1:N (1 battle involves 2–4 creatures) |
| BattleState → StatusEffect | 1:N (1 battle has 0+ status effects) |
| StatusEffect → Creature | N:1 (many effects on 1 creature) |
| Item → Inventory | 1:N (1 item type in many inventories) |

---

## 6. Persistence Model

| Entity | Persisted? | Storage |
|---|---|---|
| Species | No (static game data) | `src/data/roster.py` |
| Skill | No (static game data) | `src/data/skills.py` |
| Item | No (static game data) | `src/data/items.py` |
| Zone | No (static game data) | `src/data/zones.py` |
| EncounterEntry | No (static game data) | `src/data/encounters.py` |
| Creature | **Yes** | Inside `PlayerSave.party` or `PlayerSave.box` |
| PlayerSave | **Yes** | browser localStorage (JSON) |
| Settings | **Yes** | Inside `PlayerSave.settings` |
| BattleState | No (transient) | In-memory only |
| StatusEffect | No (transient) | Inside `BattleState` |

---

## 7. Related Documents

- [Schema.md](Schema.md) — Python dataclass definitions for all entities
- [Architecture.md](Architecture.md) — System architecture and data flow
- [PRD.md](PRD.md) — Game design (roster, stats, encounters)
- [API.md](API.md) — Module/function API reference
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
