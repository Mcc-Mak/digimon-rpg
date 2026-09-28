# AGENTS.md

## Project status

Greenfield repository for `digimon-rpg`. No code, build tooling, package manifest, or tests exist yet — do not assume or invent build/lint/test commands. Verify any toolchain before running it.

## Git workflow

- Work on and push to the `dev-001` branch. Do not commit to or push `main`.
- Commits must be standardized and formatted: a concise imperative subject line followed by a body that explains the rationale for the change.
- Every change must update `CHANGELOG.md` with a semantic-version entry in the form `X.X.X`.

## Required documents

Keep these documents consistent with the code on any substantial change. They live at the repo root and under `doc/`:

- `TOCTREE.md` (root) — master table of contents; must be referenced by `README.md`.
- `doc/ProjectCharter.md`, `doc/PRD.md`, `doc/SRS.md`, `doc/UserStories.md`
- `doc/Architecture.md`, `doc/ADR.md`, `doc/ER.md`, `doc/Schema.md`
- `doc/API.md`, `doc/QuickStart.md`, `doc/RTM.md`, `doc/Governance.md`, `doc/CRM.md`

## README requirements

`README.md` must:

- Reference `TOCTREE.md`.
- Include the GitHub Pages web access entrypoint. The Pages site serves the pygame app packaged to WebAssembly via [pygbag](https://github.com/pygame-org/pygbag); the build runs in CI (see `.github/workflows/auto-merge.yml`) and expects a `main.py` entrypoint.

## CrewAI build workflow

The primary way to build or reconstruct the game is the `crewai_run_project` MCP tool (CrewAI orchestrator). It plans a team of agents and asks for plan endorsement before executing; coding agents get file + shell tools and write real files in the repo.

### Recommended crew composition

- **Lead designer / architect** (reasoning) — owns game mechanics, Digimon roster, battle system, evolution/progression loop; outputs feed `doc/PRD.md`, `doc/SRS.md`, `doc/UserStories.md`.
- **Pygame engineer** (coding) — implements the `main.py` entrypoint, game loop, scenes (title, world, battle), input/audio. Must keep code pygbag/WASM-compatible.
- **Systems engineer** (coding) — Digimon stat data, save system, encounter tables, evolution/leveling logic.
- **QA engineer** (coding) — writes tests and runs `python -m pygbag --build main.py` locally to verify the CI build path before commit.

### Task flow

1. Design (mechanics, roster, loop) → 2. Scaffold (`main.py` + scene/asset layout) → 3. Implement systems (battle, world, progression) → 4. Verify (pygbag build + entrypoint runs).

### Crew constraints (include in the project description)

- Entry point must be `main.py` at the repo root (pygbag + CI expect it).
- Code must run under pygbag/WASM: avoid blocking filesystem or OS calls that break in-browser.
- Honor the git workflow (work on `dev-001` only) and the required-doc set above.
- Do not modify the `merge` job in `.github/workflows/auto-merge.yml`.

### Invocation

Call `crewai_run_project` with `working_directory` set to the repo root and a project description that includes the constraints above. Use `auto_approve: false` so the generated plan is endorsed before agents run.
