# Changelog

All notable changes to this project are documented in this file.
Entries follow [Semantic Versioning](https://semver.org/) in the form `X.X.X`.

## 0.19.0 - 2026-09-30

### Added

- `core/assets.py` — New `AssetLoader` class with `__file__`-based path
  resolution (`_candidate_roots()`), replacing the fragile CWD-relative
  path logic that broke in the WASM/pygbag bundle. Resolves sprites
  relative to the module file, not the process working directory, so
  paths work identically on desktop and in-browser.
  Includes `_decode_png()` pure-Python PNG decoder as fallback when
  pygame lacks SDL_image (`get_extended() == False`), and a
  `_load_transparent()` dual-strategy loader (pygame.image.load →
  fallback to `_decode_png`).
- `pygbag.ini` — Build configuration that excludes `/doc`, `/tests`,
  `/tools`, `/__pycache__`, `/.venv`, `/build`, and the local
  `/digimon-rpg-svc4` reference directory from the WASM bundle. Prevents
  bloat and keeps local-only franchise art out of the public Pages site.
- `tests/test_assets.py` — New test suite covering path resolution,
  sprite loading, cache behavior, sprite-key uniqueness, and procedural
  fallback integration.

### Changed

- `core/sprite_factory.py` — Fully rewritten to use
  `AssetLoader.sprite(species.sprite_key)` with procedural draw fallback
  via `_draw_procedural()`. Removed all diagnostics machinery
  (`DIAGNOSTICS`, `get_diagnostics`, `_diag`, `_STAGE_NUM`,
  `_load_png_sprite`, `_error_placeholder`, `_init_diagnostics`,
  `_decode_png` (moved to assets.py), `_SPRITE_PATH_CANDIDATES`).
  Procedural fallback uses `_ELEMENT_PALETTE` (7 elements) and
  `_STAGE_SIZE` (Rookie=56, Champion=72, Ultimate=88) canvases with 12
  dedicated draw functions in `_DRAWERS` registry and `_draw_generic`
  fallback for the remaining 128 species. API surface preserved:
  `get_sprite`, `get_battle_sprite`, `get_world_sprite`, `clear_cache`.
- `data/digimon_data.py` — Added `STAGE_NUMBER` dict
  (`{"Rookie": 1, "Champion": 2, "Ultimate": 3}`) and `sprite_key`
  property on `Digimon` (returns `f"{self.key}_{stage_num}"`).
- `tests/test_sprites.py` — Rewritten to exercise the full pipeline
  (baked PNG + procedural fallback) without monkeypatching internal
  loaders. Added `TestProceduralFallback` class that forces AssetLoader
  misses to verify the procedural draw path.
- `tests/test_animator.py` — Updated monkeypatch from
  `sprite_factory._load_png_sprite` (removed) to
  `sprite_factory._build_sprite` (replacement). Added save/restore of
  the original function in `teardown_module` to prevent leak.

## 0.18.0 - 2026-09-29

### Added

- `core/wasm_log.py` — Cross-platform logging helper. Calls
  `js.console.log` under pygbag/WASM (visible in browser DevTools
  console) and falls back to `print()` on desktop.

### Changed

- `core/sprite_factory.py` — `_diag()` now routes to `browser_log()`
  so all sprite-loading diagnostics (CWD, path candidates, load
  success/failure) appear in the browser DevTools console, not just
  the xterm panel.
- `main.py` — Wrapped `main()` in try/except that logs the full
  traceback to the console on any fatal crash. Added `[main] starting`
  and `[main] entering game loop` markers to confirm code execution.

## 0.17.0 - 2026-09-29

### Fixed

- `core/sprite_factory.py` — **Root cause of sprite loading failure found
  and fixed.** `pygame.image.load()` cannot decode PNGs when the pygame
  build lacks SDL_image (`get_extended() == False`), raising "File is not
  a Windows BMP file". Added a pure-Python PNG decoder (`_decode_png()`)
  that uses only `zlib` + `struct` (both stdlib, both WASM-safe) as a
  fallback. The decoder handles 8-bit RGBA (color type 6) and 8-bit RGB
  (color type 2) with all five PNG filter types (None, Sub, Up, Average,
  Paeth). This eliminates the magenta placeholder issue on both desktop
  pygame (no SDL_image) and pygbag/WASM.
- `main.py` — Removed diagnostic overlay and `js.alert` debugging code
  added in 0.16.0. The game loop is now clean.

## 0.16.0 - 2026-09-29

### Changed

- `core/sprite_factory.py` — Rewrote sprite loading for WASM robustness:
  - **Lazy initialization**: Sprite directory detection now happens on
    first sprite load, not at module import time. This avoids running
    filesystem checks before pygbag has fully mounted the archive.
  - **Multiple path candidates**: Tries `assets/sprites/creatures`,
    `assets/assets/sprites/creatures`, and `sprites/creatures` for
    each sprite, covering different CWD layouts pygbag may produce.
  - **File-object fallback**: If `pygame.image.load(path)` fails, tries
    `open(path, "rb")` + `pygame.image.load(io.BytesIO(data))`. This
    uses Python's file I/O layer which may work when SDL2's C-level
    file I/O doesn't in the BrowserFS virtual filesystem.
  - **On-screen diagnostics**: All diagnostic messages are stored in a
    global `DIAGNOSTICS` list (exposed via `get_diagnostics()`).

- `main.py` — Added a debug overlay that draws the last 12 sprite
  diagnostic messages at the top-left of the game canvas. This is
  necessary because pygbag redirects both `print()` and
  `js.console.log()` to its xterm terminal, NOT the browser DevTools
  console — making console-based debugging invisible to the user.

### Verification

- All 101 tests pass.
- pygbag build succeeds.

### Fixed

- `core/sprite_factory.py` — Rewrote sprite loading for WASM diagnostics:
  - **Browser console logging**: All sprite log messages now go to
    `js.console.log()` (browser DevTools console) instead of `print()`
    (which only appears in pygbag's xterm terminal and was invisible
    in DevTools).
  - **Sprite directory auto-detection**: `_find_sprite_dir()` probes
    multiple candidate paths (`assets/sprites/creatures`,
    `assets/assets/sprites/creatures`, `sprites/creatures`) and picks
    the first containing PNGs. This handles the doubled-`assets/`
    path that pygbag's archive mount can create.
  - **CWD and directory listing logged at import time** so the browser
    console shows exactly where the WASM filesystem looks for sprites.

## 0.14.0 - 2026-09-29

### Fixed

- `core/sprite_factory.py` — Removed `os.path.exists()` guard from
  `_load_png_sprite()`. Under pygbag/WASM, `os.path.exists()` returns
  `False` for files in the BrowserFS virtual filesystem, causing every
  PNG to be rejected before `pygame.image.load()` was ever called. Now
  the code attempts `pygame.image.load()` directly and only falls back
  to the error placeholder if the load raises an exception.

### Verification

- All 101 tests pass (`pytest tests/ -v`).
- pygbag build succeeds (189 files packed, 140 PNGs included).

## 0.13.0 - 2026-09-29

### Changed

- `core/sprite_factory.py` — Removed all procedural sprite drawing:
  - Deleted all `_draw_*` functions (12 species-specific + 7
    element-generic), helper functions (`_darken`, `_lighten`,
    `_soft_disc`, `_draw_eyes`, `_draw_flame`, `_draw_droplet`,
    `_draw_lightning`, `_draw_thorn`), color palettes
    (`_ELEMENT_PALETTE`), stage-size tables (`_STAGE_SIZE`,
    `_DEFAULT_SIZE`), and the `_DRAWERS` / `_ELEMENT_DRAWERS`
    dispatch dicts.
  - Deleted `_FORCE_PROCEDURAL` flag — no longer needed.
  - `get_sprite()` now loads PNGs exclusively. If a PNG is missing or
    fails to decode, a solid magenta error placeholder is returned so
    the failure is immediately visible (not hidden behind a circle).
  - `_load_png_sprite()` retains debug `print()` output for browser
    console diagnosis.

- `tests/test_sprites.py` — Replaced `_FORCE_PROCEDURAL = True` with a
  monkeypatch of `_load_png_sprite` that returns synthetic surfaces.
  Fake PNGs are asymmetric so left/right flip tests still work.

- `tests/test_animator.py` — Same monkeypatch approach as test_sprites.

- `doc/Schema.md` — Bumped to v0.7.1; updated sprite system description
  to reflect PNG-only model (no procedural fallback).

### Verification

- All 101 tests pass (`pytest tests/ -v`).
- pygbag build succeeds (189 files packed, 140 PNGs included).

## 0.12.0 - 2026-09-29

### Added

- `core/sprite_factory.py` — Element-specific procedural fallback drawers:
  - Seven new generic drawers replace the single circle-based
    `_draw_generic`: `_draw_generic_fire` (bipedal lizard with flame
    tail), `_draw_generic_water` (fish with fins and bubbles),
    `_draw_generic_nature` (quadruped with leaf adornments),
    `_draw_generic_electric` (mouse-like with spark cheeks),
    `_draw_generic_earth` (bulky quadruped with rocky back plates),
    `_draw_generic_dark` (shadowy creature with wispy tendrils),
    `_draw_generic_normal` (small furry mammal with whiskers).
  - `_ELEMENT_DRAWERS` dict dispatches by element when a species has no
    dedicated drawer, so the 128 species without custom art now get
    distinct, element-themed silhouettes instead of identical circles.
  - Debug logging in `_load_png_sprite`: prints PNG path, existence
    check, load success/failure, and surface size to the browser console
    (via `print(..., flush=True)`) to aid WASM asset-loading diagnosis.

### Changed

- `core/sprite_factory.py` — `_build_sprite` now resolves the drawer via
  `_DRAWERS` (per-species) then `_ELEMENT_DRAWERS` (per-element) before
  falling back to `_draw_generic_normal`. `get_sprite` unknown-species
  path uses `_draw_generic_normal` instead of the removed `_draw_generic`.

### Verification

- All 101 tests pass (`pytest tests/ -v`).
- pygbag build succeeds (189 files packed, 140 PNGs included).

## 0.11.0 - 2026-09-29

### Added

- `core/animator.py` — Frame-based sprite animation system:
  - `AnimationState` enum with five states: `IDLE` (vertical bob,
    looping), `WALK` (bounce + sway, looping), `ATTACK` (forward lunge
    + recoil, one-shot), `HURT` (red tint + shake, one-shot), `FAINT`
    (drop + fade, one-shot).
  - Each state generates 4 procedural frames from the base sprite using
    only `pygame.Surface` / `pygame.draw` / `pygame.transform` (WASM-safe).
  - `Animator` class tracks state and time, returns the correct frame on
    each `update()`. Non-looping animations hold their last frame when
    finished.
  - `get_frames()` caches frames per `(species_key, facing, state)`.

- `tests/test_animator.py` — 30 tests covering frame generation, caching,
  facing, animator state transitions, playback (loop/finish/hold), and
  frame content (bob, lunge, tint, fade).

### Changed

- `scenes/battle_scene.py` — Integrated animator for combatant sprites:
  - Player and enemy each get an `Animator` instance (right/left facing).
  - Attack actions trigger `ATTACK` animation on the attacker; the
    defender receives `HURT` after a 0.25s delay via an animation queue.
  - Battle end triggers `FAINT` on the loser.
  - `_draw_combatants()` now blits `anim.current_frame` instead of a
    static cached sprite; non-looping animations revert to `IDLE` when
    finished (except `FAINT`).
  - Removed unused `get_battle_sprite` import and `_combatant_cache`.

- `scenes/world_scene.py` — Integrated animator for player avatar:
  - Player gets an `Animator` initialized with the player's species.
  - Movement triggers `WALK` animation; returning to idle triggers
    `IDLE` when the move cooldown expires.
  - `_draw_player()` blits `anim.current_frame` scaled to 30px wide.
  - Removed unused `get_world_sprite` import.

- `.github/workflows/auto-merge.yml` — Deploy job patches `browserfs.min.js`
  URL in `build/web/index.html` from the broken pygbag CDN
  (`https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js`) to
  `https://cdn.jsdelivr.net/npm/browserfs@1.4.3/dist/browserfs.min.js`.
  BrowserFS is the virtual filesystem pygbag uses for file I/O in WASM;
  without it, `pygame.image.load()` cannot read packed PNG assets in the
  browser. The merge job is unchanged.

- `doc/Schema.md` — Bumped to v0.6.0; documented the animation system
  (states, frame counts, durations, caching, integration points).

### Verification

- All 101 tests pass (`pytest tests/ -v`).
- pygbag build succeeds (189 files packed, 140 PNGs included).

## 0.10.0 - 2026-09-29

### Changed

- `core/sprite_factory.py` — Switched from purely procedural sprites to
  a hybrid PNG-first / procedural-fallback model:
  - `_build_sprite()` now calls `_load_png_sprite()` first, which
    attempts `pygame.image.load()` on
    `assets/sprites/creatures/{species_key}_{stage_num}.png`.
  - If the PNG is missing or cannot be decoded (e.g. desktop without
    SDL2_image), the original procedural drawer runs instead so
    rendering never crashes.
  - Under pygbag/WASM the browser decodes PNGs natively, so all 140
    sprite assets are displayed at runtime.
  - Added `_STAGE_NUM` mapping (Rookie=1, Champion=2, Ultimate=3),
    `_SPRITE_DIR` constant, `_FORCE_PROCEDURAL` flag (for tests), and
    `import os`.
  - Module docstring updated to document the hybrid approach.

- `tests/test_sprites.py` — Tests now set `_FORCE_PROCEDURAL = True`
  in `setup_module` so the procedural path is exercised deterministically
  regardless of host PNG support. Docstring updated.

### Verification

- All 71 tests pass (`pytest tests/ -v`).
- pygbag build succeeds (187 files packed, 140 PNGs confirmed in
  `digimon-rpg.tar.gz`).

## 0.9.0 - 2026-09-29

### Added

- `data/digimon_data.py` — Roster expanded from 12 to 140 species:
  - 128 new species generated at import time from
    `_EXPANDED_SPECIES_TABLE` — a compact tuple list of
    `(species_id, stage_num, element, evolution_target)`. The
    `_make_expanded_species()` function produces `Digimon` instances
    using element/stage-templated stat blocks (`_STAT_TEMPLATES`),
    per-element growth rates (`_GROWTH_RATES`), shared element move
    lists (`_ELEMENT_MOVES`), and element-themed descriptions
    (`_ELEMENT_DESCRIPTIONS`).
  - 45 evolution lines across 6 elements (fire, water, nature,
    electric, earth, dark). Each line has Rookie → Champion →
    Ultimate stages, each stage a separate species.
  - Evolution requirements: Rookie → Champion (level 10, 5 battles
    won); Champion → Ultimate (level 25, 15 battles won, 1 boss
    defeat).
  - Element distribution: fire=25, water=17, nature=13, electric=25,
    earth=33, dark=27. Stage distribution: Rookie=49, Champion=46,
    Ultimate=45.

- `systems/encounter.py` — Encounter tables expanded:
  - Zone 1 (Verdant Plains): 6 → 17 entries with expanded rookies.
  - Zone 2 (Storm Peaks): 7 → 22 entries with expanded rookies and
    champions.
  - Zone 3 (Ashen Wastes): new zone, levels 30–50, 26 entries with
    champions, ultimates, and high-level rookies.

- `assets/sprites/creatures/` — 140 PNG sprite files organized by
  species ID and stage number (`{species_id}_{stage}.png`). Runtime
  sprites remain procedural via `core/sprite_factory.py`; PNGs are
  for asset management only (pygbag/WASM cannot load extended image
  formats).

### Changed

- `data/digimon_data.py` — Updated 6 existing species with evolution
  targets: Stormwing → Voltalon, Voltalon → Thundergod, Rockbash →
  Mountainhide, Seedkit → Thornbloom, Thornbloom → VerdantTitan,
  Chaospuff → Wraithwing. `DIGIMON_REGISTRY` now includes all 140
  species (12 hand-crafted + 128 generated).

- `tests/test_sprites.py` — Replaced
  `test_all_species_have_dedicated_drawer` with
  `test_all_species_render_non_blank_sprite` to cover all 140
  species (12 dedicated drawers + 128 element-tinted generic
  fallbacks).

- `tests/test_encounter.py` — Added
  `test_all_encounter_species_exist_in_registry` to validate every
  encounter entry resolves in the 140-species registry.

- `doc/Schema.md` — Updated to v0.4.0: documents the two-tier roster
  (12 hand-crafted + 128 templated), element/stage distribution
  table, template approach, and 3 encounter zones (added Ashen
  Wastes).

### Verification

- All sprite tests pass (12 tests in `tests/test_sprites.py`).
- All encounter tests pass (15 tests in `tests/test_encounter.py`).
- 140 species verified in registry; 0 evolution target errors.

## 0.8.0 - 2026-09-28

### Added

- `scenes/world.py` — Tile-based overworld scene (WorldScene):
  - 20×15 tile grid (32px tiles = 640×480) with 7 tile types: grass,
    tall grass, path, water, tree, water_edge, and sign — each rendered
    via `pygame.draw` primitives with decorations (tree canopy circles,
    water arcs, tall-grass blades, sign post + board).
  - Arrow-key / WASD grid-based movement with 0.15s cooldown and
    collision detection against water and tree tiles.
  - Random encounter triggering on grass/tall_grass/water_edge tiles
    via `systems.encounter.check_encounter("verdant_plains", terrain)`.
    On encounter, stores `game.pending_encounter` and pushes
    `BattleScene`.
  - Player rendered as a red circle with white outline.
  - Sign NPC at tile (3,7): pressing ENTER/SPACE when adjacent shows a
    semi-transparent dialogue text box with word-wrapped text and a
    "Press ENTER to close" prompt.
  - HUD bar at bottom showing zone name, step count, and controls hint.
  - 0.5s encounter cooldown after returning from battle (no instant
    re-encounter).
  - ESC key clears scene stack and returns to TitleScene.
  - `enter()` restores player position from `game.player_world_pos`
    and processes/clears `game.battle_result` on return from battle.

- `scenes/battle.py` — Full turn-based battle scene (BattleScene):
  - 9-phase state machine: INTRO → PLAYER_MENU → PLAYER_ANIM →
    ENEMY_ANIM → MESSAGE → VICTORY / DEFEAT / EVOLUTION / FLEE_RESULT.
  - Reads encounter from `game.pending_encounter` and player party
    from `game.save_data.party[0]`; constructs `BattleDigimon` for both
    sides via `from_species()` and a `BattleEngine`.
  - Player Digimon drawn as element-colored circle on left, enemy on
    right; circle radius scales by evolution stage (Rookie 25px,
    Champion 35px, Ultimate 45px). Each shape has a white outline and
    simple "eyes" for character.
  - HP bars (200px) with color-coded thresholds (green >50%, yellow
    25–50%, red <25%) and player MP bar — rendered for both combatants.
  - Move selection menu: 2×2 grid showing all 4 moves with number,
    name, power, MP cost, and element. Select via keys 1–4 or arrow
    navigation + ENTER. Moves with insufficient MP shown in red and
    blocked. "F. Flee" option at bottom.
  - Attack animation: player/enemy circle lunges toward the opponent
    over 0.3s, triggers a white screen flash at the impact midpoint
    (alpha decaying over ~0.3s), then returns over 0.3s.
  - Battle log area showing last 3 messages from `engine.log`.
  - Turn ordering via `engine.determine_turn_order()` (speed + random
    initiative); new order re-rolled each round.
  - Victory: awards XP via `engine.award_xp()`, gold via
    `roll_gold("verdant_plains")`, applies multi-level-up chain via
    `check_level_up()` with stat delta display, increments
    `battles_won`, syncs HP/MP from battle to save, and checks
    evolution via `can_evolve()`.
  - Evolution animation: pulsing white screen flash, shape transform
    (color + size change to new species), evolution message, then
    returns to victory screen. Updates `party_member.species_id`,
    `stage`, stats, and `learned_moves`.
  - Defeat: shows "You were defeated..." message, ENTER clears scene
    stack and returns to TitleScene.
  - Flee: calls `engine.attempt_flee()`; on success shows message and
    pops to world; on failure shows "Couldn't escape!" and enemy gets
    a free turn.
  - All timers driven by `dt` in `update()` — no blocking operations.

### Changed

- `main.py` — `Game` class updated: player starting position changed
  to (10, 6) to match world map walkable tile.
- `scenes/title_scene.py` — ENTER key now creates a default save
  (Emberling starter at level 5 with recalculated stats) via
  `create_default_save()` + `calculate_stats_at_level()`, stores it
  on `game.save_data`, sets `game.player_world_pos = (10, 6)`, and
  transitions to `WorldScene` via `game.replace()`.

### WASM Safety

- All new and modified code verified WASM-safe: no `subprocess`, no
  blocking file I/O (no `open()` calls), no `threading`, no `ctypes`,
  no `time.sleep`, no external image/audio loading. All graphics use
  `pygame.draw` and `pygame.font` primitives only. All timers are
  dt-driven in `update()` (NFR-01, NFR-03).

### Verification

- All files pass `ast.parse` syntax validation.
- All modules import successfully with cross-module dependencies
  resolved.
- Integration tests pass (pygame dummy driver):
  - Title → World scene transition on ENTER.
  - World movement, collision, sign dialogue, encounter triggering.
  - Battle: intro → player menu → attack → animation → message →
    enemy turn → round cycle.
  - Victory with XP, multi-level-up, gold, and stat delta messages.
  - Evolution trigger (Lv 10+, 5 battles): animation + species
    transform (Emberling → Pyroclaw).
  - Defeat: returns to TitleScene on ENTER.
  - Flee: success/fail handling.
  - MP check: unaffordable moves blocked with "Not enough MP!" message.
  - ESC from world returns to TitleScene.

## 0.7.0 - 2026-09-28

### Added

- `core/sprite_factory.py` — Procedural per-species creature sprites:
  - Each of the 12 Digimon species now has a dedicated, recognizable
    silhouette drawn entirely with `pygame.draw` primitives onto a
    transparent `SRCALPHA` surface (no external image assets — WASM-safe).
  - Element-derived palettes (fire/water/nature/electric/earth/dark) drive
    body, accent, and glow colors; evolution stage drives canvas size
    (Rookie 56px < Champion 72px < Ultimate 88px).
  - Per-species features: Emberling tail-flame, Pyroclaw molten veins +
    white-hot claws, Infernosaur wings + flame aura, Aquapup translucent
    fins + big eyes, Tsunamut water jets + enormous claws, Leviathore
    serpentine body + dorsal fins, Stormwing feathered wings + static
    arcs, Rockbash overlapping stone plates, Seedkit flower bud + leaves,
    Chaospuff wispy drifting body + glowing eyes, Thornbloom thorny stem
    + flower head, Voltalon wings shedding lightning + crest horns.
  - `get_sprite(name)`, `get_battle_sprite(name, facing)`,
    `get_world_sprite(name, size, facing)`, `clear_cache()` with module-
    level caching (base sprites, flipped/scaled battle + world variants).
  - Unknown species fall back to a generic elemental blob so rendering
    never crashes.

- `tests/test_sprites.py` — 12 tests: dedicated-drawer coverage for all
  species, surface generation, stage-scaled sizing, transparent
  background, non-blank rendering, generic fallback, cache identity,
  left/right facing flip, world-sprite scaling.

### Changed

- `scenes/battle_scene.py` — Combatants are now rendered as species
  sprites instead of plain colored circles. Player faces right, enemy is
  horizontally flipped to face the player. Sprites scale slightly with
  level (clamped 1.0–1.35) and are cached per battle; a soft drop shadow
  grounds each creature on its platform.
- `scenes/world_scene.py` — The overworld avatar is now the player's
  chosen Digimon species sprite (scaled to 30px) instead of a red circle.
  Avatar flips horizontally based on the last horizontal movement
  direction; soft drop shadow added under the avatar.

### Verification

- All 70 tests pass via `pytest tests/` (58 existing + 12 new sprite
  tests).
- pygbag build verified: `python -m pygbag --build main.py` succeeds,
  45 files packed to `build/web/`.
- Render smoke test: all 12 species generate non-blank sprites with
  stage-scaled sizes; `BattleScene` and `WorldScene` draw end-to-end
  under a dummy video driver.

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
