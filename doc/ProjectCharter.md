# Project Charter — digimon-rpg

| Field | Value |
|---|---|
| **Project Name** | digimon-rpg |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **License** | MIT |
| **Repository** | https://github.com/Mcc-Mak/digimon-rpg |
| **Live Site** | https://mcc-mak.github.io/digimon-rpg/ |

---

## 1. Project Description

**digimon-rpg** is a browser-based monster-collection RPG built with pygame and
deployed to the web via pygbag (WebAssembly). Players capture, train, and
evolve original creatures across multiple world zones, engaging in turn-based
battles with a type-effectiveness system and a 3-stage evolution progression.

The game runs entirely in the browser — no download or installation required —
and is deployed to GitHub Pages via an automated CI/CD pipeline.

---

## 2. Project Objectives

1. **Deliver a playable browser RPG** that loads via GitHub Pages and runs in
   any modern browser through WebAssembly.
2. **Create an original creature roster** of 6+ creatures with full stat blocks,
   3-stage evolution paths, and type-based combat dynamics.
3. **Implement a satisfying progression loop**: explore → battle → gain XP →
   level up → evolve → unlock new zones → repeat.
4. **Ensure pygbag/WASM compatibility** throughout the codebase — no subprocess
   calls, no blocking I/O, async-friendly game loop.
5. **Produce a complete, internally consistent documentation set** that enables
   any engineer to understand and contribute to the project.

---

## 3. Scope

### 3.1 In Scope

- Turn-based battle system with type effectiveness, skills, items, and status
  effects.
- 6 original creatures, each with 3 evolution stages (18 total species).
- 2 fully-implemented world zones with encounter tables (Verdant Plains,
  Storm Peaks).
- 2 additional zones specified in data (Abyssal Depths, Throne of Corruption).
- Party management (up to 6 creatures), box storage, capture mechanics.
- Save/load system using browser localStorage (pygbag-compatible).
- XP curve, level-up stat growth, and evolution requirements.
- Scene system: title, world map, battle, party menu, camp/save, evolution,
  and supporting screens.
- Automated CI/CD pipeline: `dev-001` → `dev` → `main` → GitHub Pages.

### 3.2 Out of Scope (v1.0)

- Multiplayer / online battles.
- Real-time (action) combat — combat is strictly turn-based.
- Mobile native app (responsive browser play is supported).
- Trading between players.
- Procedurally generated content — all zones are hand-designed.
- Voice acting.

---

## 4. Stakeholders

| Role | Responsibility |
|---|---|
| **Project Owner** | Mcc-Mak — owns the repo, CI/CD, and final decisions |
| **Lead Game Designer** | Game mechanics, roster, battle system, progression loop |
| **Pygame Engineer** | Game loop, scenes, input, audio, rendering |
| **Systems Engineer** | Stat data, save system, encounter tables, evolution/leveling |
| **QA Engineer** | Tests, pygbag build verification, regression testing |
| **Players** | End users who play the game via GitHub Pages |

---

## 5. Success Criteria

1. The game loads and runs in Chrome, Firefox, and Safari via the GitHub Pages
   URL without errors.
2. A player can complete a full battle, capture a creature, level up, and
   evolve a creature.
3. The `python -m pygbag --build main.py` command succeeds locally and in CI.
4. All documents in the `doc/` set are internally consistent and
   cross-referenced.
5. The RTM (Requirements Traceability Matrix) covers every functional
   requirement in the SRS.

---

## 6. Milestones

| Milestone | Description | Status |
|---|---|---|
| **M0: Documentation** | Complete design and project docs | ✅ Complete (v0.3.0) |
| **M1: Scaffold** | `main.py` entrypoint + scene system + title screen | Planned |
| **M2: Core Systems** | Battle engine, stat data, save/load, encounter system | Planned |
| **M3: Content** | Zone 1 & 2 playable, all 6 creatures + evolutions | Planned |
| **M4: Polish** | Audio, animations, UX, balance tuning | Planned |
| **M5: Release** | Full game playable on GitHub Pages | Planned |

---

## 7. Constraints

| Constraint | Detail |
|---|---|
| **Platform** | Web browser via pygbag/WASM; no native desktop required |
| **Entry point** | `main.py` at repo root (pygbag and CI expect this) |
| **No subprocess** | WASM sandbox forbids `subprocess` — all logic must be in-process |
| **No blocking I/O** | File operations must be async or use browser storage APIs |
| **Python version** | 3.12 (matches CI setup) |
| **Git workflow** | Work on `dev-001` branch only; do not commit to `main` |
| **CI/CD** | `.github/workflows/auto-merge.yml` — merge job must not be modified |
| **IP** | All creatures, names, and designs must be original (not Bandai Digimon) |

---

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| pygbag/WASM incompatibility with a library | Medium | High | Restrict to pygame-ce + stdlib; test build early |
| Browser performance issues with complex scenes | Medium | Medium | Profile render loop; cap FPS; lazy-load assets |
| Save data loss (localStorage cleared) | Low | Medium | Document browser storage limitations; auto-save on camp visit |
| Scope creep on creature count / zones | Medium | Medium | Lock roster at 6 creatures, 4 zones for v1.0 |

---

## 9. Related Documents

- [PRD.md](PRD.md) — Product Requirements (game design)
- [SRS.md](SRS.md) — Software Requirements
- [Architecture.md](Architecture.md) — System architecture
- [Governance.md](Governance.md) — Branch strategy and conventions
- [QuickStart.md](QuickStart.md) — Development setup
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
