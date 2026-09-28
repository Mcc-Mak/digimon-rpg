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
