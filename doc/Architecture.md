# Architecture — digimon-rpg

| Field | Value |
|---|---|
| **Document** | Architecture.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [PRD.md](PRD.md), [SRS.md](SRS.md), [ADR.md](ADR.md) |

---

## 1. Overview

This document describes the software architecture of **digimon-rpg** — a
pygame-based RPG that runs in the browser via pygbag (WebAssembly). The
architecture is designed around three key principles:

1. **Async-first**: The game loop is an async coroutine, required by pygbag's
   WASM runtime.
2. **Scene-based state management**: All game states (title, world, battle,
   etc.) are discrete scenes managed by a central scene manager.
3. **Data-driven design**: Creature stats, encounters, skills, and zones are
   defined as data (dataclasses/JSON), not hardcoded in logic.

---

## 2. Module Structure

```
digimon-rpg/
├── main.py                      # Entry point — async game loop
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── game.py              # Game class — owns display, scene manager, input
│   │   ├── scene_manager.py     # SceneManager — stack-based scene transitions
│   │   ├── scene.py             # Abstract Scene base class
│   │   ├── input.py             # Input handler — keyboard + mouse abstraction
│   │   ├── assets.py            # Asset loader — sprites, fonts, audio
│   │   └── save.py              # Save system — localStorage via pygbag bridge
│   ├── scenes/
│   │   ├── __init__.py
│   │   ├── title_scene.py       # Scene 1: Title screen
│   │   ├── creation_scene.py    # Scene 2: Character creation
│   │   ├── starter_scene.py     # Scene 3: Starter selection
│   │   ├── world_scene.py       # Scene 4: World map / overworld
│   │   ├── battle_scene.py      # Scene 5: Battle
│   │   ├── transition_scene.py  # Scene 6: Battle transition
│   │   ├── party_scene.py       # Scene 7: Party menu
│   │   ├── creature_info_scene.py  # Scene 8: Creature detail
│   │   ├── skill_scene.py       # Scene 9: Skill/move grid
│   │   ├── inventory_scene.py   # Scene 10: Items/inventory
│   │   ├── capture_scene.py     # Scene 11: Digi-Core/capture
│   │   ├── camp_scene.py        # Scene 12: Save/camp/heal
│   │   ├── evolution_scene.py   # Scene 13: Evolution animation
│   │   ├── gameover_scene.py    # Scene 14: Game over
│   │   ├── victory_scene.py     # Scene 15: Victory/post-battle
│   │   ├── boss_intro_scene.py  # Scene 16: Boss fight intro
│   │   ├── zone_complete_scene.py  # Scene 17: Zone completion
│   │   ├── dialogue_scene.py    # Scene 18: Dialogue/cutscene
│   │   ├── settings_scene.py    # Scene 19: Settings
│   │   └── credits_scene.py     # Scene 20: Credits
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── battle.py            # Battle engine — damage, turns, AI, status
│   │   ├── evolution.py         # Evolution logic — checks, stat transforms
│   │   ├── leveling.py          # XP curve, level-up stat growth
│   │   ├── encounters.py        # Encounter table logic — weighted selection
│   │   ├── capture.py           # Capture chance calculation
│   │   └── items.py             # Item definitions and effects
│   ├── data/
│   │   ├── __init__.py
│   │   ├── roster.py            # All 18 species definitions (6 lines × 3 stages)
│   │   ├── skills.py            # Skill definitions per species
│   │   ├── encounters.py        # Zone encounter table definitions
│   │   ├── zones.py             # Zone metadata and terrain rates
│   │   └── items.py             # Item catalog
│   └── ui/
│       ├── __init__.py
│       ├── widgets.py           # UI widgets — buttons, bars, text boxes
│       ├── menus.py             # Menu systems — command menus, lists
│       └── effects.py           # Visual effects — particles, transitions
├── assets/
│   ├── sprites/                 # Creature and tile sprites
│   ├── audio/                   # Music and SFX
│   └── fonts/                   # Custom fonts
├── tests/                       # Test suite
└── doc/                         # Documentation (this file)
```

---

## 3. Scene System

### 3.1 Scene Base Class

All scenes inherit from an abstract `Scene` base class:

```python
class Scene:
    """Abstract base class for all game scenes."""

    def __init__(self, game: "Game"):
        self.game = game

    def on_enter(self) -> None:
        """Called when this scene becomes active."""
        pass

    def on_exit(self) -> None:
        """Called when this scene is deactivated."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a pygame event (key press, mouse click, etc.)."""
        pass

    def update(self, dt: float) -> None:
        """Update scene state. dt = delta time in seconds."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the scene to the screen surface."""
        pass
```

### 3.2 Scene Manager

The `SceneManager` maintains a **stack** of scenes. This allows overlay scenes
(like dialogue or settings) to be pushed on top of the current scene without
destroying it.

```python
class SceneManager:
    """Manages a stack of scenes."""

    def __init__(self):
        self._stack: list[Scene] = []

    def push(self, scene: Scene) -> None:
        """Push a new scene onto the stack (becomes active)."""
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> Scene | None:
        """Remove and return the top scene."""
        if not self._stack:
            return None
        scene = self._stack.pop()
        scene.on_exit()
        if self._stack:
            self._stack[-1].on_enter()
        return scene

    def replace(self, scene: Scene) -> None:
        """Replace the current scene with a new one."""
        if self._stack:
            self._stack[-1].on_exit()
            self._stack[-1] = scene
        else:
            self._stack.append(scene)
        scene.on_enter()

    @property
    def current(self) -> Scene | None:
        """Return the active (top) scene, or None."""
        return self._stack[-1] if self._stack else None
```

### 3.3 Scene Transition Flow

```
Title Scene
    │
    ├──[New Game]──► Character Creation ──► Starter Selection ──► World Map
    │
    └──[Continue]──► World Map (load save)

World Map
    │
    ├──[step trigger]──► Battle Transition ──► Battle Scene
    │                                            │
    │                                            ├──[Win]──► Victory Scene ──► World Map
    │                                            ├──[Lose]──► Game Over ──► Camp Scene
    │                                            └──[Flee]──► World Map
    │
    ├──[enter camp]──► Camp Scene
    │                       ├──[Save]──► (writes localStorage)
    │                       ├──[Heal]──► (restores HP/MP)
    │                       └──[Box]──► Party/Box management
    │
    ├──[open menu]──► Party Menu
    │                    ├──[Creature]──► Creature Info ──► Skill Grid
    │                    └──[Items]──► Inventory
    │
    └──[NPC interact]──► Dialogue Overlay

Evolution triggers from: Victory Scene, Camp Scene, or Level-Up display
```

### 3.4 Scene Data Passing

Scenes share state through the `Game` singleton object, which holds:
- `player_save: PlayerSave` — the current save state
- `scene_manager: SceneManager`
- `battle_state: BattleState | None` — transient battle data
- `settings: Settings`

When a scene needs to pass data to the next scene (e.g., battle results to the
victory screen), it sets the appropriate field on `game` before transitioning.

---

## 4. Async Game Loop

### 4.1 Why Async?

pygbag compiles Python to WebAssembly and runs it inside the browser's
JavaScript event loop. A traditional blocking `while True` loop would freeze
the browser tab. The game loop **must** be an `async def` that yields control
back to the browser each frame.

### 4.2 Loop Structure

```python
# main.py (simplified)
import asyncio
import pygame

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("digimon-rpg")
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # delta time in seconds, target 60 FPS

        # Process all pending events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        # Update current scene
        game.update(dt)

        # Render current scene
        game.draw(screen)
        pygame.display.flip()

        # CRITICAL: yield to browser event loop
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
```

### 4.3 Frame Budget

| Phase | Budget | Notes |
|---|---|---|
| Event processing | ~2ms | Typically <10 events per frame |
| Scene update | ~5ms | Game logic, AI, stat calculations |
| Scene draw | ~5ms | Blit sprites, UI widgets, effects |
| `pygame.display.flip()` | ~2ms | Present backbuffer to canvas |
| `await asyncio.sleep(0)` | — | Yields to browser |
| **Total** | **~14ms** | Leaves ~2.7ms headroom at 60 FPS (16.7ms budget) |

---

## 5. Data Flow

### 5.1 Overall Data Flow

```
┌─────────────────────────────────────────────────────┐
│                    main.py (async loop)              │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Events   │─►│  Game.update │─►│  Game.draw   │  │
│  └───────────┘  └──────┬───────┘  └──────┬───────┘  │
│                        │                  │          │
│                 ┌──────▼───────┐  ┌──────▼───────┐  │
│                 │ SceneManager │  │ SceneManager  │  │
│                 │  .update(dt)  │  │  .draw(scr)   │  │
│                 └──────┬───────┘  └──────┬───────┘  │
│                        │                  │          │
│                 ┌──────▼───────┐  ┌──────▼───────┐  │
│                 │Active Scene  │  │Active Scene  │  │
│                 │ .update(dt)  │  │ .draw(scr)   │  │
│                 └──────┬───────┘  └──────────────┘  │
└────────────────────────┼────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼───────┐
   │  Systems   │ │   Data     │ │  PlayerSave│
   │ (battle,   │ │ (roster,   │ │ (localStorage│
   │  evolve,   │ │  skills,   │ │  via bridge)│
   │  level)    │ │  zones)    │ │             │
   └────────────┘ └────────────┘ └─────────────┘
```

### 5.2 Battle Data Flow

```
World Scene (step trigger)
    │
    ▼
EncounterSystem.select_enemy(zone_id, terrain)
    │  reads: Zone encounter table + weights
    │  returns: Creature (wild enemy instance)
    ▼
BattleState created:
    - player_active: Creature (from party)
    - enemy: Creature (wild)
    - round: int
    - turn_order: list[Creature]
    - status_effects: dict
    │
    ▼
BattleScene.update(dt):
    - Processes player command
    - Calls BattleSystem.calculate_damage(attacker, defender, skill)
    - Applies status effects
    - Checks win/loss
    │
    ├──[Win]──► XP awarded (LevelingSystem.add_xp)
    │            │
    │            ├──[Level up]──► Stats recalculated
    │            │                  │
    │            │                  └──[Evolution check]──► EvolutionScene
    │            │
    │            └──► VictoryScene (rewards display)
    │
    └──[Lose]──► GameOverScene → CampScene (penalty applied)
```

### 5.3 Save Data Flow

```
Camp Scene → "Save" selected
    │
    ▼
SaveSystem.save(player_save)
    │
    ├── Serialize PlayerSave to JSON
    ├── Write to browser localStorage via pygbag JS bridge
    │   (or platform.storage if available)
    └── Confirm success

Load:
    Title Screen → "Continue" selected
    │
    ▼
SaveSystem.load()
    │
    ├── Read JSON from localStorage
    ├── Deserialize to PlayerSave
    ├── Validate schema version
    └── Return PlayerSave or None (no save / corrupt)
```

---

## 6. Key System Interfaces

### 6.1 BattleSystem

```python
class BattleSystem:
    """Manages all battle logic."""

    def calculate_damage(
        self,
        attacker: Creature,
        defender: Creature,
        skill: Skill,
    ) -> int:
        """Calculate final damage per PRD §5.3 formula."""
        ...

    def determine_turn_order(
        self,
        combatants: list[Creature],
    ) -> list[Creature]:
        """Roll initiative and return sorted turn order."""
        ...

    def apply_status(
        self,
        creature: Creature,
        status: str,
        duration: int,
    ) -> None:
        """Apply a status effect to a creature."""
        ...

    def check_battle_end(
        self,
        battle_state: BattleState,
    ) -> str | None:
        """Return 'win', 'loss', or None if battle continues."""
        ...

    def execute_ai_turn(
        self,
        enemy: Creature,
        player_active: Creature,
        battle_state: BattleState,
    ) -> tuple[str, any]:
        """Execute enemy AI turn, return (action_type, action_data)."""
        ...
```

### 6.2 LevelingSystem

```python
class LevelingSystem:
    """XP curve and level-up stat growth."""

    @staticmethod
    def xp_to_reach_level(level: int) -> int:
        """Total XP needed to reach `level` from level 1."""
        ...

    @staticmethod
    def xp_for_next_level(current_level: int) -> int:
        """XP needed to go from current_level to current_level+1."""
        ...

    @staticmethod
    def add_xp(creature: Creature, xp: int) -> list[int]:
        """Add XP to creature. Returns list of levels gained."""
        ...

    @staticmethod
    def calculate_stat(
        base: int,
        growth_rate: float,
        level: int,
    ) -> int:
        """Calculate stat at given level per PRD §8.1."""
        ...
```

### 6.3 EvolutionSystem

```python
class EvolutionSystem:
    """Evolution logic and stat transformations."""

    @staticmethod
    def check_evolution(
        creature: Creature,
        boss_defeats: int,
    ) -> str | None:
        """Check if creature can evolve. Returns new species_id or None."""
        ...

    @staticmethod
    def evolve(creature: Creature, new_species: Species) -> None:
        """Transform creature to new species, recalculate stats."""
        ...
```

### 6.4 SaveSystem

```python
class SaveSystem:
    """Save/load using browser localStorage."""

    SAVE_KEY = "digimon_rpg_save"
    SAVE_VERSION = 1

    @staticmethod
    async def save(player_save: PlayerSave) -> bool:
        """Serialize and save to localStorage. Returns success."""
        ...

    @staticmethod
    async def load() -> PlayerSave | None:
        """Load and deserialize from localStorage. Returns None if no save."""
        ...

    @staticmethod
    def has_save() -> bool:
        """Check if a save exists."""
        ...
```

### 6.5 EncounterSystem

```python
class EncounterSystem:
    """Wild encounter selection."""

    @staticmethod
    def select_enemy(
        zone_id: str,
        terrain: str,
    ) -> Creature:
        """Select a wild creature from the zone's encounter table."""
        ...

    @staticmethod
    def check_encounter(
        steps: int,
        zone: Zone,
        terrain: str,
    ) -> bool:
        """Roll for encounter based on step count and terrain rate."""
        ...
```

---

## 7. Asset Management

### 7.1 Asset Loading

All assets are loaded at startup or lazily on first use:

```python
class AssetLoader:
    """Loads and caches game assets."""

    _sprites: dict[str, pygame.Surface] = {}
    _fonts: dict[str, pygame.font.Font] = {}
    _sounds: dict[str, pygame.mixer.Sound] = {}

    @classmethod
    def sprite(cls, name: str) -> pygame.Surface:
        """Load and cache a sprite by name."""
        ...

    @classmethod
    def font(cls, name: str, size: int) -> pygame.font.Font:
        """Load and cache a font by name and size."""
        ...

    @classmethod
    def sound(cls, name: str) -> pygame.mixer.Sound:
        """Load and cache a sound effect by name."""
        ...
```

### 7.2 Asset Naming Convention

| Type | Path | Naming |
|---|---|---|
| Creature sprite | `assets/sprites/creatures/` | `{species_id}_{stage}.png` (e.g., `emberling_1.png`) |
| Tile sprite | `assets/sprites/tiles/` | `{tile_name}.png` |
| UI sprite | `assets/sprites/ui/` | `{widget_name}.png` |
| Music | `assets/audio/music/` | `{zone_id}_theme.ogg` |
| SFX | `assets/audio/sfx/` | `{effect_name}.ogg` |
| Font | `assets/fonts/` | `{font_name}.ttf` |

---

## 8. Input Handling

### 8.1 Input Abstraction

```python
class InputHandler:
    """Abstracts keyboard and mouse input into game actions."""

    def __init__(self):
        self._keys_pressed: set[int] = set()
        self._keys_just_pressed: set[int] = set()
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._mouse_clicked: bool = False

    def update(self) -> None:
        """Call at end of frame to clear just-pressed state."""
        self._keys_just_pressed.clear()
        self._mouse_clicked = False

    def is_pressed(self, key: int) -> bool:
        """Key is currently held down."""
        ...

    def just_pressed(self, key: int) -> bool:
        """Key was pressed this frame (edge-triggered)."""
        ...
```

### 8.2 Key Bindings

| Action | Key(s) |
|---|---|
| Move up | ↑ / W |
| Move down | ↓ / S |
| Move left | ← / A |
| Move right | → / D |
| Confirm / interact | Enter / Space |
| Cancel / back | Esc |
| Menu | Tab |
| Quick save | Ctrl+S (camp only) |

---

## 9. Error Handling

### 9.1 Strategy

- **Asset missing**: Log warning, use placeholder (magenta square for sprites,
  silence for audio).
- **Save corrupt**: Display warning, offer "New Game" only.
- **Invalid game state**: Log error, transition to title screen.
- **pygbag build failure**: CI fails; developer must fix before merge.

### 9.2 Logging

```python
import logging

logger = logging.getLogger("digimon-rpg")
logger.setLevel(logging.DEBUG)
```

In WASM, logs go to the browser console via pygbag's bridge.

---

## 10. Related Documents

- [ADR.md](ADR.md) — Architecture decision records
- [ER.md](ER.md) — Entity relationships
- [Schema.md](Schema.md) — Data schemas
- [API.md](API.md) — Module and function API reference
- [SRS.md](SRS.md) — Software requirements
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
