# Software Requirements Specification (SRS) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | SRS.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [PRD.md](PRD.md), [Architecture.md](Architecture.md), [ProjectCharter.md](ProjectCharter.md) |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for **digimon-rpg**, a
browser-based monster-collection RPG built with pygame and deployed via pygbag
(WebAssembly) to GitHub Pages. It covers functional requirements, non-functional
requirements, and the critical technical constraints imposed by the pygbag/WASM
target.

### 1.2 Scope

The game provides: turn-based battles with type effectiveness, 6 original
creatures with 3-stage evolution, 2+ world zones with encounter tables, party
management, capture mechanics, save/load, and a scene-based UI.

### 1.3 Definitions & Acronyms

| Term | Definition |
|---|---|
| **pygbag** | Python packaging tool that compiles pygame apps to WebAssembly |
| **WASM** | WebAssembly — the bytecode format the browser executes |
| **Scene** | A discrete game state (title, world, battle, etc.) managed by the scene manager |
| **Async game loop** | A game loop structured as an async coroutine, required by pygbag's WASM runtime |
| **localStorage** | Browser-provided persistent key-value storage, used for saves |
| **Digi-Core** | In-game capture device item |
| **STAB** | Same-Type Attack Bonus (1.5× damage when move type matches creature type) |

---

## 2. Functional Requirements

### FR-01: Game Initialization

| Field | Value |
|---|---|
| **ID** | FR-01 |
| **Title** | Game Initialization |
| **Description** | The game shall initialize from `main.py` at the repo root, create a pygame display surface, and enter the title screen scene. |
| **Priority** | Must |
| **Source** | ProjectCharter.md §7, PRD.md §10 |

### FR-02: Scene Management

| Field | Value |
|---|---|
| **ID** | FR-02 |
| **Title** | Scene Management |
| **Description** | The game shall implement a scene manager that supports transitioning between all scenes defined in PRD §10 (20 scenes). Only one scene is active at a time. Scenes shall support `on_enter()`, `on_exit()`, `handle_event(event)`, `update(dt)`, and `draw(screen)` methods. |
| **Priority** | Must |
| **Source** | PRD.md §10, Architecture.md §3 |

### FR-03: Title Screen

| Field | Value |
|---|---|
| **ID** | FR-03 |
| **Title** | Title Screen |
| **Description** | The title screen shall display the game logo, a "Press Start" prompt, and menu options: New Game, Continue, Settings, Credits. If no save exists, Continue is disabled. |
| **Priority** | Must |
| **Source** | PRD.md §10 |

### FR-04: Character Creation

| Field | Value |
|---|---|
| **ID** | FR-04 |
| **Title** | Character Creation |
| **Description** | The player shall enter a name (1–12 characters, alphanumeric) for their tamer. On confirmation, a new save profile is created. |
| **Priority** | Must |
| **Source** | PRD.md §10 |

### FR-05: Starter Selection

| Field | Value |
|---|---|
| **ID** | FR-05 |
| **Title** | Starter Selection |
| **Description** | The player shall choose 1 of 3 starter creatures (Emberling, Aquapup, Seedkit) at Level 1. The selected creature is added to the party as the first member. |
| **Priority** | Must |
| **Source** | PRD.md §6.2, §10 |

### FR-06: World Map — Movement

| Field | Value |
|---|---|
| **ID** | FR-06 |
| **Title** | World Map Movement |
| **Description** | The player shall move their character sprite on a top-down tile-based map using arrow keys or WASD. Movement triggers a step counter for random encounters. |
| **Priority** | Must |
| **Source** | PRD.md §10, §9 |

### FR-07: Random Encounters

| Field | Value |
|---|---|
| **ID** | FR-07 |
| **Title** | Random Encounters |
| **Description** | When the step counter reaches a zone-defined threshold, the game shall roll against the zone's encounter rate. On success, a wild creature is selected from the zone's encounter table (weighted random) and a battle begins. |
| **Priority** | Must |
| **Source** | PRD.md §9 |

### FR-08: Battle System — Turn Order

| Field | Value |
|---|---|
| **ID** | FR-08 |
| **Title** | Battle Turn Order |
| **Description** | At the start of each battle round, the system shall compute initiative as `speed + random(0, 20)` for each combatant, sort descending, and execute actions in that order. |
| **Priority** | Must |
| **Source** | PRD.md §5.1 |

### FR-09: Battle System — Actions

| Field | Value |
|---|---|
| **ID** | FR-09 |
| **Title** | Battle Actions |
| **Description** | The player shall choose one action per turn: Attack, Skill, Item, Switch, or Flee. Each action consumes the turn. |
| **Priority** | Must |
| **Source** | PRD.md §5.2 |

### FR-10: Battle System — Damage Calculation

| Field | Value |
|---|---|
| **ID** | FR-10 |
| **Title** | Damage Calculation |
| **Description** | The system shall calculate damage per PRD §5.3, applying type multiplier, random variance (0.9–1.1), critical hit multiplier (2.0× at 6.25% chance), STAB (1.5×), and status modifiers. Minimum damage is 1. |
| **Priority** | Must |
| **Source** | PRD.md §5.3, §5.4 |

### FR-11: Battle System — MP & Skills

| Field | Value |
|---|---|
| **ID** | FR-11 |
| **Title** | MP and Skill Usage |
| **Description** | Skills shall consume MP. A skill cannot be used if current MP < skill MP cost. MP does not regenerate during battle. Each species has exactly 4 skills learned at fixed levels. |
| **Priority** | Must |
| **Source** | PRD.md §5.5 |

### FR-12: Battle System — Status Effects

| Field | Value |
|---|---|
| **ID** | FR-12 |
| **Title** | Status Effects |
| **Description** | The system shall support status conditions: Burn, Freeze, Poison, Paralysis, Sleep, Confusion, and stat buff/debuff stages (±3, each ±25%). Status effects are cleared on battle end and on switch. |
| **Priority** | Should |
| **Source** | PRD.md §5.6 |

### FR-13: Battle System — Win/Loss

| Field | Value |
|---|---|
| **ID** | FR-13 |
| **Title** | Battle Win/Loss Conditions |
| **Description** | Battle is won when all enemy creatures reach 0 HP. Battle is lost when all player party creatures reach 0 HP. On loss, player returns to nearest camp with 50% HP/MP and loses 10% gold. |
| **Priority** | Must |
| **Source** | PRD.md §5.7 |

### FR-14: Battle System — Flee

| Field | Value |
|---|---|
| **ID** | FR-14 |
| **Title** | Flee Mechanic |
| **Description** | The player may attempt to flee in wild encounters only. Flee chance is `min(0.90, 0.40 + (player_spd - enemy_spd) * 0.01)`, clamped to [0.40, 0.90]. Failed flee = free enemy action. Boss battles: flee disabled. |
| **Priority** | Must |
| **Source** | PRD.md §5.8 |

### FR-15: Capture Mechanic

| Field | Value |
|---|---|
| **ID** | FR-15 |
| **Title** | Capture Mechanic |
| **Description** | The player may use a Digi-Core item to capture a wild creature whose HP is ≤20% max. Capture chance: 42% base + 15% if ≤5% HP + 5% if statused, capped at 90%. Captured creatures start at Level 1. |
| **Priority** | Must |
| **Source** | PRD.md §6.2 |

### FR-16: XP & Leveling

| Field | Value |
|---|---|
| **ID** | FR-16 |
| **Title** | XP and Leveling |
| **Description** | Participating creatures receive full XP from battles. XP follows `xp_total(L) = floor(10 * (L-1)^2.6)`. Max level is 50. On level-up, stats are recalculated using per-species growth rates. |
| **Priority** | Must |
| **Source** | PRD.md §7, §8 |

### FR-17: Evolution

| Field | Value |
|---|---|
| **ID** | FR-17 |
| **Title** | Evolution System |
| **Description** | Evolution checks occur after battle, on level-up, and at camp. Rookie→Champion requires Level 10+ and 5 battles won. Champion→Ultimate requires Level 25+, 15 battles won, and 1 Rival boss defeat. Evolution is irreversible and applies stat bonuses. |
| **Priority** | Must |
| **Source** | PRD.md §4 |

### FR-18: Party Management

| Field | Value |
|---|---|
| **ID** | FR-18 |
| **Title** | Party Management |
| **Description** | The player shall manage a party of up to 6 creatures and a Box of unlimited storage. Up to 3 creatures participate in battle (1 active, 2 bench). Switching costs a turn. |
| **Priority** | Must |
| **Source** | PRD.md §6.3 |

### FR-19: Save/Load System

| Field | Value |
|---|---|
| **ID** | FR-19 |
| **Title** | Save and Load |
| **Description** | The game shall save player progress to browser localStorage as a JSON-serialized object. The save includes: player name, gold, inventory, party, box, unlocked zones, zone progress, map position, flags, and settings. Loading restores all state. |
| **Priority** | Must |
| **Source** | PRD.md §6.1, Schema.md |

### FR-20: Items & Inventory

| Field | Value |
|---|---|
| **ID** | FR-20 |
| **Title** | Items and Inventory |
| **Description** | The game shall support items: Potion, Super Potion, Elixir, Antidote, Revive, Digi-Core, Training Stone. Items are purchased with gold and consumed on use. |
| **Priority** | Must |
| **Source** | PRD.md §5.9, §6.2 |

### FR-21: Camp/Heal Station

| Field | Value |
|---|---|
| **ID** | FR-21 |
| **Title** | Camp and Heal Station |
| **Description** | At camp, the player shall: heal all party creatures to full HP/MP, access the Box, and save the game. Camp is also the return point on battle loss. |
| **Priority** | Must |
| **Source** | PRD.md §10, §5.7 |

### FR-22: Settings

| Field | Value |
|---|---|
| **ID** | FR-22 |
| **Title** | Settings |
| **Description** | The settings screen shall allow adjusting music volume, SFX volume, text speed, and fullscreen toggle. Settings persist via localStorage. |
| **Priority** | Should |
| **Source** | PRD.md §10 |

### FR-23: Zone Progression

| Field | Value |
|---|---|
| **ID** | FR-23 |
| **Title** | Zone Progression |
| **Description** | Defeating a zone boss shall unlock the next zone and enable fast-travel to the cleared zone's camp. Zone access is gated by progression flags. |
| **Priority** | Must |
| **Source** | PRD.md §6.5, §9 |

---

## 3. Non-Functional Requirements

### NFR-01: pygbag/WASM Compatibility

| Field | Value |
|---|---|
| **ID** | NFR-01 |
| **Title** | pygbag/WASM Compatibility |
| **Description** | All code must be compatible with pygbag's WASM packaging. This means: (a) **no `subprocess` module** — the WASM sandbox forbids spawning processes; (b) **no blocking I/O** — file reads, network calls, or any operation that blocks the event loop must use async alternatives or browser storage APIs; (c) the game loop must be structured as an `async def` coroutine; (d) only `pygame-ce` and Python stdlib modules known to work under WASM are permitted. |
| **Priority** | Must |
| **Source** | ProjectCharter.md §7, AGENTS.md |

### NFR-02: Performance

| Field | Value |
|---|---|
| **ID** | NFR-02 |
| **Title** | Browser Performance |
| **Description** | The game shall maintain at least 30 FPS (target: 60 FPS) in Chrome, Firefox, and Safari on a mid-range laptop. Battle scene with 2 sprites and effects must not drop below 30 FPS. |
| **Priority** | Must |
| **Source** | ProjectCharter.md §5 |

### NFR-03: Async Game Loop

| Field | Value |
|---|---|
| **ID** | NFR-03 |
| **Title** | Async Game Loop |
| **Description** | The main game loop shall be an `async def` function that yields control to the browser event loop each frame using `await asyncio.sleep(0)`. This is required by pygbag's WASM runtime — a blocking `while True` loop will freeze the browser tab. |
| **Priority** | Must |
| **Source** | Architecture.md §4 |

### NFR-04: Save Data Integrity

| Field | Value |
|---|---|
| **ID** | NFR-04 |
| **Title** | Save Data Integrity |
| **Description** | Save data shall be JSON-serializable and survive page reloads. The save schema shall be versioned to support future migrations. Corrupt or incompatible saves shall be detected and the player warned, not crash the game. |
| **Priority** | Must |
| **Source** | PRD.md §6.1 |

### NFR-05: Browser Compatibility

| Field | Value |
|---|---|
| **ID** | NFR-05 |
| **Title** | Browser Compatibility |
| **Description** | The game shall run in Chrome 100+, Firefox 100+, and Safari 15+ via the GitHub Pages URL. No browser extensions or plugins required. |
| **Priority** | Must |
| **Source** | ProjectCharter.md §5 |

### NFR-06: Load Time

| Field | Value |
|---|---|
| **ID** | NFR-06 |
| **Title** | Load Time |
| **Description** | The game shall load to a playable title screen within 10 seconds on a broadband connection. Assets shall be lazy-loaded where possible. |
| **Priority** | Should |
| **Source** | ProjectCharter.md §5 |

### NFR-07: Original IP

| Field | Value |
|---|---|
| **ID** | NFR-07 |
| **Title** | Original Intellectual Property |
| **Description** | All creature names, designs, abilities, and assets must be original. No copyrighted Bandai Digimon names, designs, or trademarks may appear. |
| **Priority** | Must |
| **Source** | ProjectCharter.md §7 |

### NFR-08: Code Quality

| Field | Value |
|---|---|
| **ID** | NFR-08 |
| **Title** | Code Quality |
| **Description** | Code shall follow PEP 8 with type hints on all public functions. Modules shall have docstrings. The codebase shall pass `pygbag --build main.py` without errors. |
| **Priority** | Should |
| **Source** | AGENTS.md |

---

## 4. Technical Constraints (pygbag/WASM)

### 4.1 Prohibited Patterns

The following are **prohibited** because they break under pygbag/WASM:

| Pattern | Why | Alternative |
|---|---|---|
| `subprocess.run()`, `os.system()` | WASM sandbox forbids process spawning | Pure Python; no external commands |
| `open()` with blocking read/write (synchronous file I/O) | Blocks the browser event loop | Use `localStorage` via JS bridge or `asyncio`-compatible storage |
| `input()` / `print()` to stdin/stdout | No terminal in browser | Use pygame UI for all I/O |
| `threading` module | WASM is single-threaded | Use `asyncio` coroutines |
| `multiprocessing` | No process support in WASM | N/A — design around it |
| `socket` / network libraries | Browser security sandbox | Use `fetch()` via JS bridge if needed |
| `time.sleep()` | Blocks the event loop | `await asyncio.sleep(seconds)` |
| C extensions / native modules | Must be WASM-compatible | Use pure-Python or pygbag-supported packages |

### 4.2 Required Patterns

| Pattern | Requirement |
|---|---|
| **Async entry point** | `main.py` must contain an `async def main()` or use `pygame.run_async()` |
| **Event loop yielding** | Game loop must `await asyncio.sleep(0)` or use pygbag's clock |
| **localStorage for saves** | Use pygbag's JS bridge or browser `localStorage` API for persistence |
| **pygame-ce** | Use `pygame-ce` (community edition) which has best pygbag support |
| **Asset loading** | All assets loaded via `pygame.image.load()` with paths relative to the script |

### 4.3 CI/CD Pipeline

The `.github/workflows/auto-merge.yml` pipeline:
1. On push to `dev-001`: merges `dev-001` → `dev` → `main`.
2. Checks out `main`, sets up Python 3.12, installs pygbag.
3. Runs `python -m pygbag --build main.py`.
4. Uploads `./build/web` as a Pages artifact.
5. Deploys to GitHub Pages.

The `merge` job must not be modified (per AGENTS.md).

---

## 5. External Interfaces

### 5.1 User Interface

- **Display**: pygame surface rendered to browser canvas via pygbag.
- **Input**: Keyboard (arrow keys, WASD, Enter, Esc, Space) and mouse click.
- **Audio**: pygame mixer (music + SFX), volume controlled via settings.

### 5.2 Storage Interface

- **Save data**: Browser `localStorage`, accessed via pygbag JS bridge.
- **Format**: JSON object matching `PlayerSave` schema (see [Schema.md](Schema.md)).

### 5.3 Deployment Interface

- **Hosting**: GitHub Pages at `https://mcc-mak.github.io/digimon-rpg/`.
- **Build**: `python -m pygbag --build main.py` → `./build/web/`.

---

## 6. Requirements Summary

| Category | Count | Must | Should |
|---|---|---|---|
| Functional (FR) | 23 | 20 | 3 |
| Non-Functional (NFR) | 8 | 6 | 2 |
| **Total** | **31** | **26** | **5** |

---

## 7. Related Documents

- [PRD.md](PRD.md) — Game design and mechanics
- [Architecture.md](Architecture.md) — System architecture and async loop
- [Schema.md](Schema.md) — Data schemas
- [RTM.md](RTM.md) — Requirements traceability matrix
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
