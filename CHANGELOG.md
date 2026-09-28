# Changelog

All notable changes to this project are documented in this file.
Entries follow [Semantic Versioning](https://semver.org/) in the form `X.X.X`.

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
