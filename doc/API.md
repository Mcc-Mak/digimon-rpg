# API Reference — digimon-rpg

| Field | Value |
|---|---|
| **Document** | API.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [Architecture.md](Architecture.md), [Schema.md](Schema.md), [PRD.md](PRD.md) |

---

## 1. Overview

This document provides the module and function API reference for
**digimon-rpg**. It covers all public modules, classes, and functions that
engineers will use when implementing the game. Module paths are relative to
the `src/` package.

---

## 2. Module Index

| Module | Purpose |
|---|---|
| `main` | Entry point — async game loop |
| `src.core.game` | Game class — display, scene manager, input |
| `src.core.scene_manager` | SceneManager — stack-based scene management |
| `src.core.scene` | Scene — abstract base class |
| `src.core.input` | InputHandler — keyboard/mouse abstraction |
| `src.core.assets` | AssetLoader — sprite/font/sound loading and caching |
| `src.core.save` | SaveSystem — localStorage persistence |
| `src.scenes.*` | 20 scene modules (one per scene) |
| `src.systems.battle` | BattleSystem — damage, turns, AI, status |
| `src.systems.evolution` | EvolutionSystem — evolution checks and transforms |
| `src.systems.leveling` | LevelingSystem — XP curve, stat growth |
| `src.systems.encounters` | EncounterSystem — wild encounter selection |
| `src.systems.capture` | CaptureSystem — capture chance calculation |
| `src.systems.items` | ItemSystem — item effects and application |
| `src.data.roster` | ROSTER — all 18 species definitions |
| `src.data.skills` | SKILLS — all skill definitions |
| `src.data.encounters` | ZONES — zone encounter table definitions |
| `src.data.items` | ITEMS — item catalog |
| `src.ui.widgets` | UI widgets — Button, HealthBar, TextBox, etc. |

---

## 3. `main` — Entry Point

### `async def main() -> None`

The game entry point. Initializes pygame, creates the display, instantiates the
`Game` object, and runs the async game loop.

**Called by:** `asyncio.run(main())` at module level.

**Loop structure:**
```python
async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
        await asyncio.sleep(0)  # Yield to browser

    pygame.quit()
```

---

## 4. `src.core.game` — Game Class

### `class Game`

Central game object that owns the display, scene manager, input handler, and
player state.

#### Attributes

| Attribute | Type | Description |
|---|---|---|
| `screen` | `pygame.Surface` | The main display surface |
| `scene_manager` | `SceneManager` | Scene stack manager |
| `input` | `InputHandler` | Input state |
| `player_save` | `PlayerSave \| None` | Current save (None if no game active) |
| `battle_state` | `BattleState \| None` | Transient battle data |
| `settings` | `Settings` | Current settings |
| `assets` | `AssetLoader` | Asset cache (class-level) |
| `running` | `bool` | Whether the game loop is active |

#### Methods

```python
def handle_event(self, event: pygame.event.Event) -> None
```
Forward a pygame event to the active scene.

```python
def update(self, dt: float) -> None
```
Update the active scene. `dt` is delta time in seconds.

```python
def draw(self, screen: pygame.Surface) -> None
```
Draw the active scene to the screen surface.

```python
def start_new_game(self, player_name: str, starter_species_id: str) -> None
```
Create a new `PlayerSave` with the given name and starter creature at Level 1.
Transition to the world map scene.

```python
def load_game(self) -> bool
```
Load save from localStorage. Returns `True` on success. Transitions to world
map at saved position.

```python
def save_game(self) -> bool
```
Serialize `player_save` to localStorage. Returns `True` on success.

---

## 5. `src.core.scene_manager` — SceneManager

### `class SceneManager`

Stack-based scene manager. See [Architecture.md](Architecture.md) §3.2.

#### Methods

```python
def push(self, scene: Scene) -> None
```
Push a scene onto the stack. Calls `on_exit()` on the current top, then
`on_enter()` on the new scene.

```python
def pop(self) -> Scene | None
```
Remove and return the top scene. Calls `on_exit()` on it, then `on_enter()`
on the new top.

```python
def replace(self, scene: Scene) -> None
```
Replace the current top scene with a new one. Calls `on_exit()` on the old,
`on_enter()` on the new.

```python
@property
def current(self) -> Scene | None
```
Return the active (top) scene.

---

## 6. `src.core.scene` — Scene Base Class

### `class Scene`

Abstract base class. All scenes inherit from this.

#### Methods (override in subclasses)

```python
def on_enter(self) -> None
```
Called when this scene becomes active.

```python
def on_exit(self) -> None
```
Called when this scene is deactivated or removed.

```python
def handle_event(self, event: pygame.event.Event) -> None
```
Handle a pygame event.

```python
def update(self, dt: float) -> None
```
Update scene logic. `dt` = seconds since last frame.

```python
def draw(self, screen: pygame.Surface) -> None
```
Render the scene.

---

## 7. `src.core.input` — InputHandler

### `class InputHandler`

Abstraction over pygame keyboard/mouse input. See [Architecture.md](Architecture.md) §8.

#### Methods

```python
def is_pressed(self, key: int) -> bool
```
Returns `True` if `key` is currently held down.

```python
def just_pressed(self, key: int) -> bool
```
Returns `True` if `key` was pressed this frame (edge-triggered).

```python
def mouse_pos(self) -> tuple[int, int]
```
Returns current mouse position.

```python
def mouse_clicked(self) -> bool
```
Returns `True` if mouse was clicked this frame.

```python
def update(self) -> None
```
Call at end of each frame to clear per-frame state.

---

## 8. `src.core.assets` — AssetLoader

### `class AssetLoader`

Loads and caches game assets. Class-level singleton.

#### Methods

```python
@classmethod
def sprite(cls, name: str) -> pygame.Surface
```
Load and cache a sprite by name. Looks in `assets/sprites/`.

```python
@classmethod
def font(cls, name: str, size: int) -> pygame.font.Font
```
Load and cache a font. Looks in `assets/fonts/`.

```python
@classmethod
def sound(cls, name: str) -> pygame.mixer.Sound
```
Load and cache a sound effect. Looks in `assets/audio/sfx/`.

```python
@classmethod
def music(cls, name: str) -> None
```
Load and play a music track (streamed, not cached). Looks in
`assets/audio/music/`.

---

## 9. `src.core.save` — SaveSystem

### `class SaveSystem`

Save/load using browser localStorage via pygbag JS bridge. See
[ADR-003](ADR.md#adr-003).

#### Class Attributes

| Attribute | Value |
|---|---|
| `SAVE_KEY` | `"digimon_rpg_save"` |
| `SAVE_VERSION` | `1` |

#### Methods

```python
@staticmethod
async def save(player_save: PlayerSave) -> bool
```
Serialize `PlayerSave` to JSON and write to localStorage. Returns `True` on
success.

```python
@staticmethod
async def load() -> PlayerSave | None
```
Read and deserialize from localStorage. Returns `None` if no save or corrupt.
Performs schema version migration if needed.

```python
@staticmethod
def has_save() -> bool
```
Returns `True` if a save exists in localStorage.

```python
@staticmethod
def delete_save() -> None
```
Remove the save from localStorage.

---

## 10. `src.systems.battle` — BattleSystem

### `class BattleSystem`

Manages all battle logic. See [PRD.md](PRD.md) §5.

#### Methods

```python
@staticmethod
def calculate_damage(
    attacker: Creature,
    defender: Creature,
    skill: SkillDef,
    type_chart: dict,
) -> int
```
Calculate final damage per PRD §5.3. Applies:
- Base damage formula
- Type multiplier (from `type_chart`)
- Random variance (0.9–1.1)
- Critical hit (6.25% chance, 2.0× multiplier)
- STAB (1.5× if skill element matches creature element)
- Status modifiers (e.g., Burn reduces Attack 25%)
- Floor at 1

Returns: integer damage value.

```python
@staticmethod
def determine_turn_order(
    combatants: list[Creature],
) -> list[str]
```
Roll initiative (`speed + random(0, 20)`) for each combatant. Returns list of
creature UIDs sorted by initiative descending. Applies speed threshold bonus
(2.5× → 1.5× initiative in first round).

```python
@staticmethod
def apply_status(
    creature_uid: str,
    status: StatusType,
    duration: int,
    battle_state: BattleState,
) -> None
```
Apply a status effect to a creature in the battle state.

```python
@staticmethod
def process_status_effects(
    battle_state: BattleState,
) -> list[str]
```
Process all active status effects at end of round. Returns list of log messages
(e.g., "Emberling is hurt by burn!").

```python
@staticmethod
def check_battle_end(
    battle_state: BattleState,
) -> str | None
```
Check win/loss conditions. Returns `"win"`, `"loss"`, or `None`.

```python
@staticmethod
def execute_ai_turn(
    enemy: Creature,
    player_active: Creature,
    battle_state: BattleState,
    enemy_skills: list[SkillDef],
) -> tuple[str, any]
```
Execute enemy AI turn per PRD §5.10. Returns `(action_type, action_data)`
where `action_type` is `"attack"`, `"skill"`, or `"item"`.

```python
@staticmethod
def calculate_flee_chance(
    player_speed: int,
    enemy_speed: int,
) -> float
```
Returns flee success probability, clamped to [0.40, 0.90]. Formula:
`min(0.90, max(0.40, 0.40 + (player_spd - enemy_spd) * 0.01))`.

---

## 11. `src.systems.leveling` — LevelingSystem

### `class LevelingSystem`

XP curve and level-up stat growth. See [PRD.md](PRD.md) §7–8.

#### Methods

```python
@staticmethod
def xp_to_reach_level(level: int) -> int
```
Total cumulative XP needed to reach `level` from level 1.
Formula: `floor(10 * (level - 1) ** 2.6)`.

```python
@staticmethod
def xp_for_next_level(current_level: int) -> int
```
XP needed to advance from `current_level` to `current_level + 1`.
Returns `xp_to_reach_level(current_level + 1) - xp_to_reach_level(current_level)`.

```python
@staticmethod
def add_xp(creature: Creature, xp: int) -> list[int]
```
Add XP to a creature. Returns a list of levels gained (may be empty, or contain
multiple if large XP award). Updates `creature.level` and recalculates
`current_hp`/`current_mp` to new maximums.

```python
@staticmethod
def calculate_stat(
    base: int,
    growth_rate: float,
    level: int,
) -> int
```
Calculate a stat at a given level.
Formula: `floor(base * (1 + growth_rate * (level - 1)))`.

```python
@staticmethod
def get_max_hp(creature: Creature, species: SpeciesDef) -> int
```
Returns the creature's max HP at its current level.

```python
@staticmethod
def get_max_mp(creature: Creature, species: SpeciesDef) -> int
```
Returns the creature's max MP at its current level.

```python
@staticmethod
def get_attack(creature: Creature, species: SpeciesDef) -> int
```
Returns the creature's Attack stat at its current level.

```python
@staticmethod
def get_defense(creature: Creature, species: SpeciesDef) -> int
```
Returns the creature's Defense stat at its current level.

```python
@staticmethod
def get_speed(creature: Creature, species: SpeciesDef) -> int
```
Returns the creature's Speed stat at its current level.

```python
@staticmethod
def get_stat_growth_display(
    creature: Creature,
    species: SpeciesDef,
    from_level: int,
    to_level: int,
) -> dict[str, int]
```
Returns a dict of stat name → delta for display on the level-up screen.
Example: `{"hp": 3, "mp": 1, "attack": 1, "defense": 0, "speed": 0}`.

---

## 12. `src.systems.evolution` — EvolutionSystem

### `class EvolutionSystem`

Evolution logic and stat transformations. See [PRD.md](PRD.md) §4.

#### Methods

```python
@staticmethod
def check_evolution(
    creature: Creature,
    species: SpeciesDef,
    boss_defeats: int,
) -> str | None
```
Check if a creature can evolve. Returns the `species_id` of the evolution
target, or `None` if evolution conditions are not met.

Conditions checked:
- `species.evolves_to` is not `None`
- `creature.level >= species.evolution_level`
- `creature.battles_won >= species.evolution_battles`
- If evolving to Ultimate: `boss_defeats >= 1`

```python
@staticmethod
def evolve(creature: Creature, new_species: SpeciesDef) -> None
```
Transform a creature to its evolution. Updates:
- `creature.species_id` → `new_species.species_id`
- `creature.stage` → `new_species.stage.value`
- Recalculates `current_hp` / `current_mp` to new maximums (preserving
  percentage)
- Applies evolution stat bonus (Champion: +20% Atk, +15% HP; Ultimate: +25%
  Atk, +20% HP — handled by recalculating from new base stats)

```python
@staticmethod
def get_evolution_stage_name(stage: int) -> str
```
Returns `"Rookie"`, `"Champion"`, or `"Ultimate"` for stage 1, 2, or 3.

---

## 13. `src.systems.encounters` — EncounterSystem

### `class EncounterSystem`

Wild encounter selection. See [PRD.md](PRD.md) §9.

#### Methods

```python
@staticmethod
def check_encounter(
    steps: int,
    zone: ZoneDef,
    terrain: str,
) -> bool
```
Returns `True` if an encounter triggers this step. Logic:
- If `steps < min_steps` for terrain, return `False`.
- Roll `random() < zone.encounter_rates[terrain]`.

```python
@staticmethod
def select_enemy(
    zone: ZoneDef,
) -> Creature
```
Select a wild creature from the zone's encounter table. Performs weighted
random selection based on `EncounterEntryDef.weight`. Creates a `Creature`
instance at a random level within the entry's `[min_level, max_level]` range.

```python
@staticmethod
def generate_wild_creature(
    species_id: str,
    min_level: int,
    max_level: int,
) -> Creature
```
Create a wild `Creature` instance of the given species at a random level in
the specified range.

---

## 14. `src.systems.capture` — CaptureSystem

### `class CaptureSystem`

Capture chance calculation. See [PRD.md](PRD.md) §6.2.

#### Methods

```python
@staticmethod
def calculate_capture_chance(
    target_hp: int,
    target_max_hp: int,
    has_status: bool,
) -> float
```
Returns capture probability.
Formula: `min(0.90, 0.42 + bonuses)` where bonuses are +0.15 if HP ≤ 5% max,
+0.05 if statused.

```python
@staticmethod
def attempt_capture(
    target: Creature,
    battle_state: BattleState,
) -> bool
```
Rolls capture chance and returns `True` on success. On success, the target
creature is added to the player's party (or box if party is full). The captured
creature's level is reset to 1.

---

## 15. `src.systems.items` — ItemSystem

### `class ItemSystem`

Item effects and application. See [PRD.md](PRD.md) §5.9.

#### Methods

```python
@staticmethod
def use_item(
    item_id: str,
    target: Creature,
    player_save: PlayerSave,
) -> tuple[bool, str]
```
Use an item on a target creature. Returns `(success, message)`.
Decrements item count from `player_save.inventory`.

Item effects:
- `"heal_hp"`: Restore HP (clamped to max).
- `"heal_mp"`: Restore MP (clamped to max).
- `"cure_status"`: Remove all status effects.
- `"revive"`: Revive fainted creature at 50% max HP.
- `"capture"`: Handled by `CaptureSystem`, not this method.

```python
@staticmethod
def buy_item(
    item_id: str,
    player_save: PlayerSave,
    quantity: int = 1,
) -> tuple[bool, str]
```
Purchase `quantity` of an item. Checks if player has enough gold. Returns
`(success, message)`.

```python
@staticmethod
def get_item_price(item_id: str) -> int
```
Returns the purchase price of an item.

---

## 16. `src.data.roster` — Roster Data

### `ROSTER: dict[str, SpeciesDef]`

Dictionary mapping `species_id` → `SpeciesDef` for all 18 species.

```python
ROSTER: dict[str, SpeciesDef] = {
    "emberling": ...,
    "pyroclaw": ...,
    "infernosaur": ...,
    "aquapup": ...,
    "tsunamut": ...,
    "leviathore": ...,
    "seedkit": ...,
    "thornbloom": ...,
    "verdant_titan": ...,
    "stormwing": ...,
    "voltalon": ...,
    "thundergod": ...,
    "rockbash": ...,
    "mountainhide": ...,
    "terraroc": ...,
    "chaospuff": ...,
    "wraithwing": ...,
    "umbrathrax": ...,
}
```

### Helper Functions

```python
def get_species(species_id: str) -> SpeciesDef
```
Returns the `SpeciesDef` for the given ID. Raises `KeyError` if not found.

```python
def get_evolution_line(species_id: str) -> list[SpeciesDef]
```
Returns the full evolution line (3 species) for any species in the line.

```python
def get_starters() -> list[SpeciesDef]
```
Returns the 3 starter species: Emberling, Aquapup, Seedkit.

---

## 17. `src.data.skills` — Skill Data

### `SKILLS: dict[str, SkillDef]`

Dictionary mapping `skill_id` → `SkillDef` for all 24 skills (6 lines × 4
skills each).

```python
def get_skill(skill_id: str) -> SkillDef
```
Returns the `SkillDef` for the given ID.

```python
def get_skills_for_species(species_id: str) -> list[SkillDef]
```
Returns the 4 skills for the given species, sorted by `learn_level`.

---

## 18. `src.data.encounters` — Zone Data

### `ZONES: dict[str, ZoneDef]`

Dictionary mapping `zone_id` → `ZoneDef` for all zones.

```python
ZONES: dict[str, ZoneDef] = {
    "verdant_plains": ...,
    "storm_peaks": ...,
}
```

### Helper Functions

```python
def get_zone(zone_id: str) -> ZoneDef
```
Returns the `ZoneDef` for the given ID.

```python
def get_encounter_table(zone_id: str) -> list[EncounterEntryDef]
```
Returns the encounter entries for a zone.

---

## 19. `src.data.items` — Item Data

### `ITEMS: dict[str, ItemDef]`

Dictionary mapping `item_id` → `ItemDef` for all items.

### Helper Functions

```python
def get_item(item_id: str) -> ItemDef
```
Returns the `ItemDef` for the given ID.

---

## 20. `src.ui.widgets` — UI Widgets

### `class Button`

A clickable button widget.

```python
Button(
    rect: pygame.Rect,
    text: str,
    callback: callable,
    font: pygame.font.Font | None = None,
)
```

#### Methods

```python
def handle_event(self, event: pygame.event.Event) -> None
def update(self, dt: float) -> None
def draw(self, screen: pygame.Surface) -> None
```

### `class HealthBar`

An HP/MP bar widget.

```python
HealthBar(
    rect: pygame.Rect,
    current: int,
    maximum: int,
    color: tuple[int, int, int] = (0, 255, 0),
    label: str | None = None,
)
```

#### Methods

```python
def set_value(self, current: int, maximum: int) -> None
def draw(self, screen: pygame.Surface) -> None
```

### `class TextBox`

A text display box (for dialogue, log, etc.).

```python
TextBox(
    rect: pygame.Rect,
    text: str = "",
    font: pygame.font.Font | None = None,
    text_speed: str = "medium",
)
```

#### Methods

```python
def set_text(self, text: str) -> None
def update(self, dt: float) -> None
def draw(self, screen: pygame.Surface) -> None
def is_complete(self) -> bool  # True when all text is displayed
```

### `class MenuList`

A scrollable menu list for selecting options.

```python
MenuList(
    rect: pygame.Rect,
    options: list[str],
    font: pygame.font.Font | None = None,
)
```

#### Methods

```python
def handle_event(self, event: pygame.event.Event) -> int | None  # Returns selected index or None
def update(self, dt: float) -> None
def draw(self, screen: pygame.Surface) -> None
def selected_index(self) -> int
```

---

## 21. Scene Module APIs

Each scene module exports a class inheriting from `Scene`. The constructor
signature is uniform:

```python
class TitleScene(Scene):
    def __init__(self, game: Game):
        super().__init__(game)
```

### Scene Module List

| Module | Class | Scene # |
|---|---|---|
| `src.scenes.title_scene` | `TitleScene` | 1 |
| `src.scenes.creation_scene` | `CreationScene` | 2 |
| `src.scenes.starter_scene` | `StarterScene` | 3 |
| `src.scenes.world_scene` | `WorldScene` | 4 |
| `src.scenes.battle_scene` | `BattleScene` | 5 |
| `src.scenes.transition_scene` | `TransitionScene` | 6 |
| `src.scenes.party_scene` | `PartyScene` | 7 |
| `src.scenes.creature_info_scene` | `CreatureInfoScene` | 8 |
| `src.scenes.skill_scene` | `SkillScene` | 9 |
| `src.scenes.inventory_scene` | `InventoryScene` | 10 |
| `src.scenes.capture_scene` | `CaptureScene` | 11 |
| `src.scenes.camp_scene` | `CampScene` | 12 |
| `src.scenes.evolution_scene` | `EvolutionScene` | 13 |
| `src.scenes.gameover_scene` | `GameOverScene` | 14 |
| `src.scenes.victory_scene` | `VictoryScene` | 15 |
| `src.scenes.boss_intro_scene` | `BossIntroScene` | 16 |
| `src.scenes.zone_complete_scene` | `ZoneCompleteScene` | 17 |
| `src.scenes.dialogue_scene` | `DialogueScene` | 18 |
| `src.scenes.settings_scene` | `SettingsScene` | 19 |
| `src.scenes.credits_scene` | `CreditsScene` | 20 |

---

## 22. Related Documents

- [Architecture.md](Architecture.md) — System architecture and data flow
- [Schema.md](Schema.md) — Data schemas (dataclass definitions)
- [ER.md](ER.md) — Entity relationships
- [SRS.md](SRS.md) — Software requirements
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
