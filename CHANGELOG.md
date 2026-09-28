# Changelog

All notable changes to this project are documented in this file.
Entries follow [Semantic Versioning](https://semver.org/) in the form `X.X.X`.

## 0.6.0 - 2026-09-28

### Added

- `scenes/world_scene.py` — Tile-based overworld scene:
  - 20×15 tile grid with grass, tall grass, water, path, tree, rock, and
    building tile types rendered via `pygame.draw` primitives.
  - Arrow-key / WASD player movement with collision detection against
    solid tiles (water, trees, rocks, buildings).
  - Random encounter triggering on tall-grass tiles via
    `systems.encounter.check_encounter()`; pushes `BattleScene` on
    encounter.
  - NPC dialogue overlay with proximity-triggered text box.
  - HUD showing zone name, player coordinates, and controls hint.

- `scenes/battle_scene.py` — Turn-based battle UI:
  - HP/MP bars for player and enemy with color-coded HP thresholds
    (green > 50%, yellow > 25%, red below).
  - Move selection menu (Up/Down to navigate, Enter to select) showing
    move name, power, MP cost, and type for each available move.
  - Scrolling battle log (last 5 messages) driven by `BattleEngine`
    result messages.
  - Damage flash overlay (red for player hit, blue for enemy hit).
  - Flee option (F key) for wild encounters.
  - Victory: awards XP via `BattleEngine.award_xp()`, applies level-up
    checks via `systems.progression.check_level_up()`, returns to world.
  - Defeat: clears scene stack and returns to title scene.

- `tests/` — Pytest test suite (58 tests, all passing):
  - `tests/test_battle.py` — `BattleDigimon` stats, damage/heal/MP,
    `BattleEngine` turn order, damage calc, player/enemy attacks,
    battle-end detection, XP award, flee mechanics, `resolve()`.
  - `tests/test_progression.py` — XP curve, stat calculation, level-up
    with stat deltas, level cap, evolution requirements, battle XP.
  - `tests/test_encounter.py` — Zone definitions, encounter rolling,
    species/level range validation, terrain-based encounter checks,
    gold rolling.
  - `tests/test_save.py` — `PartyMemberData` and `SaveData`
    serialization round-trips, default values, flags persistence.

- `.gitignore` — Ignores `__pycache__/`, `*.pyc`, `build/`, `dist/`,
  `.pytest_cache/`, venv dirs, and editor swap files.

### Changed

- `main.py` — `Game` class now extends `SceneManager` so scenes can call
  `self.game.push()`/`pop()`/`replace()` directly. Initializes player
  state (`_player_species`, `_player_level`, `_player_xp`). Game loop
  delegates events/updates/draws to `game` directly.
- `scenes/title_scene.py` — ENTER key now transitions to `WorldScene`
  via `self.game.replace()` instead of printing a debug message.

### Removed

- Committed `__pycache__/*.pyc` files removed from git tracking (now
  gitignored).

### Verification

- All 58 tests pass via `pytest tests/`.
- pygbag build verified: `python -m pygbag --build main.py` succeeds,
  43 files packed to `build/web/`.
- Full game loop simulation tested: title → world → battle (win/lose)
  → return to world/title.

## 0.5.0 - 2026-09-28

### Added

- Core game data and systems — 5 importable, testable, pygbag-compatible modules:

  - `data/digimon_data.py` — Original Digimon species and move definitions
    using `@dataclass(frozen=True)`:
    - `Move` dataclass (name, power, mp_cost, move_type, element, description)
      with validation; move_type supports "attack", "special", "defend", "heal".
    - `Digimon` dataclass (name, stage, element, hp, mp, attack, defense,
      speed, moves, evolution_target, evolution_requirements, description,
      growth rates) with `key` property and `get_move()` lookup.
    - 12 species defined: 2 complete evolution lines (Fire: Emberling →
      Pyroclaw → Infernosaur; Water: Aquapup → Tsunamut → Leviathore) plus
      6 additional encounter creatures (Stormwing, Rockbash, Seedkit,
      Chaospuff, Thornbloom, Voltalon).
    - `DIGIMON_REGISTRY` dict mapping lowercase species name → Digimon.
    - `TYPE_CHART` 7×7 elemental effectiveness matrix (fire, water, nature,
      electric, earth, dark, normal).
    - `get_digimon(name)` and `get_type_multiplier(attacker, defender)`
      helper functions.
    - 24 move definitions across 6 element families.

  - `systems/progression.py` — XP, leveling, stat growth, and evolution:
    - `xp_to_reach_level(level)` — XP curve formula `int(10 * (L-1)^2.6)`.
    - `xp_for_next_level(current_level)` — delta XP to next level.
    - `calculate_stat(base, growth_rate, level)` — `floor(base * (1 + growth_rate * (L-1)))`.
    - `calculate_stats_at_level(digimon, level)` — full 5-stat block.
    - `level_up(digimon, current_level, current_xp)` — computes old/new stats
      and deltas; capped at `LEVEL_CAP = 50`.
    - `check_level_up(current_level, current_xp)` — returns
      (can_level_up, new_level, remaining_xp).
    - `can_evolve(creature_name, level, battles_won, boss_defeats)` — validates
      evolution requirements from species definition (Rookie→Champion: Lv 10+,
      5 battles; Champion→Ultimate: Lv 25+, 15 battles, 1 boss).
    - `xp_from_battle(enemy_base_xp, enemy_level, player_level, is_boss)` —
      `floor(base_xp * (enemy_lvl/player_lvl) * 1.2)`, boss = 2×.

  - `systems/encounter.py` — Zone encounter tables and rolling:
    - `EncounterEntry` dataclass (species_id, weight, min_level, max_level,
      base_xp) with validation.
    - `Zone` dataclass (zone_id, name, min_level, max_level, encounter_entries,
      encounter_rates, gold_min, gold_max) with validation.
    - 2 zones: Verdant Plains (6 species, levels 1–12, 3 terrain types) and
      Storm Peaks (7 species, levels 15–28, 3 terrain types).
    - `roll_encounter(zone_id, rng)` — weighted random species/level/xp.
    - `check_encounter(zone_id, terrain_type, rng)` — terrain rate check +
      encounter roll.
    - `roll_gold(zone_id, rng)` — random gold in zone range.
    - `get_zone(zone_id)` — zone lookup.
    - Seedable `random.Random` for deterministic testing.

  - `systems/save_system.py` — Async save/load with WASM localStorage support:
    - `PartyMemberData` dataclass (species_id, nickname, level, stage, xp,
      current_hp, current_mp, battles_won, learned_moves) with
      `to_dict()`/`from_dict()`.
    - `SaveData` dataclass (player_name, player_position, current_zone, party,
      defeated_encounters, game_flags, gold) with `to_dict()`/`from_dict()`.
    - `save_game(data, slot)` — async, serializes to JSON, writes to
      `js.localStorage` (browser) or in-memory dict (desktop).
    - `load_game(slot)` — async, reads and deserializes.
    - `has_save(slot)`, `delete_save(slot)`, `list_save_slots()`.
    - `create_default_save(player_name, starter_species)` — fresh level-1 save.
    - `SaveSystem` class wrapper for OOP usage.
    - Detects browser via `import js`; falls back to memory store on desktop.
    - All async functions use `await asyncio.sleep(0)` for WASM yield.

  - `systems/battle.py` — Turn-based battle engine:
    - `BattleDigimon` dataclass — wraps species + level with live HP/MP,
      attack, defense, speed, moves, element, is_defending, status_effects.
      Auto-computes stats from species + level via progression formulas.
      `from_species()` factory classmethod.
    - `BattleResult` dataclass (winner, xp_awarded, gold_awarded, rounds, log).
    - `BattleEngine` class:
      - `determine_turn_order()` — speed + random(0,20) initiative, player
        wins ties.
      - `calculate_damage(attacker, defender, move)` — formula
        `(atk * move_power / def) * random(0.85..1.15) * type_mult`,
        defender defending halves damage, min 1.
      - `execute_move(attacker, defender, move)` — handles attack, special,
        defend, heal move types; MP cost validation.
      - `player_attack(move_index)` — player action with round tracking.
      - `enemy_turn()` — AI: 60% strongest, 30% random, 10% basic; heals
        at <25% HP with 40% chance if heal move available.
      - `check_battle_end()` — returns "player"/"enemy"/None.
      - `attempt_flee()` — flee chance clamped 0.40–0.90, wild only.
      - `get_battle_state()` — full snapshot dict for UI.
      - `award_xp()` — XP formula, boss = 2×.
      - `resolve(gold_awarded, player_fled)` — builds BattleResult.

### WASM Safety

- All 5 modules verified WASM-safe: no `subprocess`, no blocking file I/O,
  no `threading`, no `ctypes`, no `time.sleep`, no native modules. Only
  Python stdlib (`dataclasses`, `random`, `json`, `math`, `asyncio`,
  `typing`) used — no external dependencies. Save system uses
  `await asyncio.sleep(0)` for browser yield, with localStorage fallback
  to in-memory dict (NFR-01, NFR-03).

### Verification

- All 5 files pass `ast.parse` syntax validation.
- All 5 modules import successfully with cross-module dependencies resolved
  (`data.digimon_data` ← `systems.progression` ← `systems.battle`;
  `data.digimon_data` ← `systems.save_system`;
  `systems.encounter` standalone).
- Functional smoke tests pass: evolution checks, XP curve, stat growth,
  save/load round-trip, encounter rolling, battle engine (player attack,
  enemy AI, flee, boss XP).

## 0.4.0 - 2026-09-28

### Added

- Game engine scaffold — pygbag-compatible async game loop and scene system:
  - `main.py` — async entry point with `async def main()`, pygame init,
    `await asyncio.sleep(0)` per-frame yield, and standard pygbag boilerplate.
    Runs locally via `python main.py` and under pygbag/WASM.
  - `config.py` — screen dimensions (640×480), FPS target (60), game metadata
    (title, version), and full RGB color palette constants.
  - `core/scene.py` — `Scene` abstract base class with `enter()`, `exit()`,
    `update(dt)`, `draw(screen)`, and `handle_event(event)` lifecycle hooks.
  - `core/scene_manager.py` — `SceneManager` with stack-based `push()`,
    `pop()`, `replace()`, `current` property, and delegation of
    `update`/`draw`/`handle_event` to the active scene.
  - `scenes/title_scene.py` — Title scene with game title rendered via
    `pygame.font`, a blinking "Press ENTER to Start" prompt, and an animated
    diagonal-stripe geometric background using `pygame.draw` primitives.
  - `core/__init__.py`, `scenes/__init__.py`, `systems/__init__.py`,
    `data/__init__.py` — package init files with module docstrings.
  - `assets/.gitkeep` — placeholder for future asset directories.

### WASM Safety

- All code verified WASM-safe: no `subprocess`, no blocking file I/O, no
  `threading`, no `ctypes`, no `time.sleep`, no native modules. Game loop
  uses `await asyncio.sleep(0)` as required by pygbag (NFR-01, NFR-03).

## 0.3.0 - 2026-09-28

### Added

- Complete project documentation set created under `doc/` and repo root:
  - `TOCTREE.md` — master table of contents referenced by `README.md`.
  - `README.md` — project overview with GitHub Pages web access entrypoint
    URL (https://mcc-mak.github.io/digimon-rpg/) and TOCTREE.md reference.
  - `doc/ProjectCharter.md` — scope, objectives, stakeholders, milestones.
  - `doc/PRD.md` — game mechanics, original 6-creature roster (Emberling,
    Aquapup, Seedkit, Stormwing, Rockbash, Chaospuff) with full stat blocks,
    3-stage evolution (Rookie → Champion → Ultimate), battle system rules,
    type effectiveness, XP curve formula, level-up stat growth, encounter
    tables for Verdant Plains and Storm Peaks, evolution requirements, and
    progression loop.
  - `doc/SRS.md` — functional/non-functional requirements with pygbag/WASM
    constraints (no subprocess, no blocking I/O, async game loop).
  - `doc/UserStories.md` — player stories for each scene and progression
    milestone.
  - `doc/Architecture.md` — module structure, scene system, data flow,
    async game loop design.
  - `doc/ADR.md` — architecture decision records for pygbag compatibility,
    scene management, and save strategy.
  - `doc/ER.md` — entity-relationship model for Digimon, stats, saves,
    encounters.
  - `doc/Schema.md` — data schemas using Python dataclasses for roster,
    encounters, saves.
  - `doc/API.md` — module and function API reference.
  - `doc/QuickStart.md` — local dev and pygbag build instructions.
  - `doc/RTM.md` — requirements traceability matrix.
  - `doc/Governance.md` — branch strategy (dev-001 only), commit conventions,
    CHANGELOG rules.
  - `doc/CRM.md` — change management process.

### Changed

- `README.md` expanded to reference `TOCTREE.md`, include GitHub Pages
  entrypoint URL, tech stack, project structure, and quick start guide.

## 0.2.0 - 2026-09-28

### Added

- "CrewAI build workflow" section to `AGENTS.md`: recommended crew composition
  (lead designer, pygame engineer, systems engineer, QA engineer), task flow
  (design -> scaffold -> implement -> verify), crew constraints, and how to
  invoke the `crewai_run_project` orchestrator for building the game.

## 0.1.0 - 2026-09-28

### Added

- `AGENTS.md` with project workflow conventions: `dev-001` branch workflow,
  required document set, and README/Pages requirements.

### Changed

- Switched the GitHub Pages deployment in `.github/workflows/auto-merge.yml`
  from a Node.js build (`npm ci` / `npm run build` -> `./dist`) to a pygame
  pipeline: the app is packaged to WebAssembly via pygbag
  (`python -m pygbag --build main.py` -> `./build/web`). The `merge` job
  (dev-001 -> dev -> main) is unchanged.
