# Governance — digimon-rpg

| Field | Value |
|---|---|
| **Document** | Governance.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [AGENTS.md](../AGENTS.md), [CRM.md](CRM.md), [CHANGELOG.md](../CHANGELOG.md) |

---

## 1. Branch Strategy

### 1.1 Branch Model

This project uses a **single-development-branch** model with automated
cascade merging.

| Branch | Purpose | Who Pushes |
|---|---|---|
| `dev-001` | Active development — all work happens here | All contributors |
| `dev` | Integration branch — auto-merged from `dev-001` | CI only |
| `main` | Release branch — auto-merged from `dev`; deployed to Pages | CI only |

### 1.2 Rules

1. **All development work is done on `dev-001`.** No direct commits to `dev`
   or `main`.
2. **`dev` and `main` are updated only by the CI pipeline** (the `merge` job
   in `.github/workflows/auto-merge.yml`).
3. **Do not modify the `merge` job** in the CI workflow (per
   [AGENTS.md](../AGENTS.md)).
4. **Always pull before pushing** to avoid conflicts:
   ```bash
   git checkout dev-001
   git pull origin dev-001
   # make changes
   git push origin dev-001
   ```
5. **Branch protection**: `main` and `dev` should be protected from direct
   pushes in the GitHub repository settings.

### 1.3 Cascade Flow

```
dev-001 (push)
    │
    ▼
┌─────────────────────────┐
│  CI: merge job          │
│  dev-001 → dev (merge)  │
│  dev → main (merge)     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CI: deploy job         │
│  checkout main          │
│  pygbag --build main.py │
│  deploy to GitHub Pages │
└─────────────────────────┘
```

### 1.4 Feature Branches (Optional)

For larger features, a contributor **may** create a temporary feature branch
from `dev-001`:

```bash
git checkout dev-001
git checkout -b feature/battle-system
# ... work ...
git checkout dev-001
git merge feature/battle-system
git push origin dev-001
git branch -d feature/battle-system
```

Feature branches are **local only** — do not push them to the remote. All
remote pushes must go to `dev-001`.

---

## 2. Commit Conventions

### 2.1 Commit Message Format

Every commit must follow this format:

```
<imperative subject line>

<rationale body explaining why the change was made>
```

### 2.2 Subject Line Rules

- **Imperative mood**: "Add battle system" (not "Added" or "Adds").
- **No period** at the end.
- **Max 72 characters** (soft limit; hard limit 80).
- **Capitalized** first letter.
- **No commit-type prefix** (no `feat:`, `fix:`, etc.) — the rationale body
  provides context.

### 2.3 Body Rules

- **Separated** from the subject line by a blank line.
- **Explains the rationale** — *why* the change was made, not *what* changed
  (the diff shows what).
- **Wrap at 72 characters** per line.
- **May reference** documents: "Implements PRD §5.3 damage formula."

### 2.4 Examples

**Good:**

```
Add battle damage calculation

Implements the damage formula from PRD §5.3 including type
multipliers, critical hits, STAB, and status modifiers. Needed
for the battle system to function and for FR-10 to be satisfied.
```

```
Fix evolution stat bonus not applying on Ultimate stage

The evolution bonus multiplier was only applied for Champion-stage
evolutions. Ultimate-stage evolutions now correctly receive the
+25% primary stat and +20% HP bonus per PRD §4.5.
```

**Bad:**

```
updated battle.py
```
(No rationale, not imperative mood, too vague.)

```
feat: add battle damage calculation
```
(Uses commit-type prefix, no body.)

```
Added battle damage calculation.
```
(Past tense, period at end.)

### 2.5 Commit Size

- **One logical change per commit.** Don't mix unrelated changes.
- **If a commit touches multiple files**, they should all serve the same
  purpose.
- **Tests go with the code they test** in the same commit.

---

## 3. CHANGELOG Rules

### 3.1 When to Update

Every commit that introduces a user-facing or architecturally significant
change must update [CHANGELOG.md](../CHANGELOG.md).

### 3.2 Format

CHANGELOG.md uses [Semantic Versioning](https://semver.org/) and follows the
[Keep a Changelog](https://keepachangelog.com/) structure:

```markdown
## X.X.X - YYYY-MM-DD

### Added
- New features.

### Changed
- Changes to existing functionality.

### Deprecated
- Soon-to-be removed features.

### Removed
- Removed features.

### Fixed
- Bug fixes.

### Security
- Security-related fixes.
```

### 3.3 Version Numbering

| Version Change | When to Use | Example |
|---|---|---|
| **Major (X.0.0)** | Breaking changes to save schema, API, or architecture | Save format v1 → v2 |
| **Minor (0.X.0)** | New features, new content, new scenes | Add battle system; add Zone 3 |
| **Patch (0.0.X)** | Bug fixes, typo fixes, doc updates | Fix evolution bonus bug |

> **Current version**: 0.3.0. The project is in 0.x.x (pre-1.0) development.
> Breaking changes may occur in minor versions until 1.0.0.

### 3.4 Entry Rules

1. **One entry per change** — be specific. "Add battle damage calculation in
   `src/systems/battle.py`" not "Add battle stuff."
2. **Group by category** — Added, Changed, Fixed, etc.
3. **Reference documents** where relevant: "per PRD §5.3", "satisfies FR-10".
4. **Date format**: `YYYY-MM-DD`.
5. **Newest version at the top** of the file.

### 3.5 Example Entry

```markdown
## 0.4.0 - 2026-09-29

### Added

- Battle damage calculation in `src/systems/battle.py` implementing
  the PRD §5.3 formula with type multipliers, critical hits, STAB,
  and status modifiers. Satisfies FR-10.
- Turn order initiative system with speed-based sorting and
  first-round priority bonus per PRD §5.1. Satisfies FR-08.

### Fixed

- Evolution stat bonus now correctly applies for Ultimate-stage
  evolutions (was only applying for Champion). Fixes PRD §4.5
  regression.
```

---

## 4. Code Review

### 4.1 Self-Review Checklist

Before pushing to `dev-001`, verify:

- [ ] Code follows PEP 8 with type hints on public functions.
- [ ] No `subprocess`, `threading`, `os.system`, or blocking I/O (NFR-01).
- [ ] Game loop uses `await asyncio.sleep(0)` (NFR-03).
- [ ] `python main.py` runs without errors.
- [ ] `python -m pygbag --build main.py` succeeds.
- [ ] Tests pass: `pytest tests/`.
- [ ] CHANGELOG.md updated with semantic version entry.
- [ ] Commit message follows conventions (§2).
- [ ] No copyrighted material (NFR-07).

### 4.2 Review Process

Since this project uses a single development branch (`dev-001`) without pull
requests, code review happens:

1. **Pre-push self-review** (checklist above).
2. **Post-push CI verification** — the pipeline builds and deploys; failures
   are visible immediately.
3. **Post-hoc review** — contributors should review the commit history on
   `dev-001` and raise issues if problems are found.

---

## 5. Document Maintenance

### 5.1 Required Documents

The following documents must be kept consistent with the code on any
substantial change (per [AGENTS.md](../AGENTS.md)):

| Document | Update When |
|---|---|
| `CHANGELOG.md` | Every commit with user-visible change |
| `doc/PRD.md` | Game mechanics change |
| `doc/SRS.md` | Requirements change |
| `doc/Architecture.md` | Module structure or data flow changes |
| `doc/Schema.md` | Data schemas change |
| `doc/API.md` | Public function signatures change |
| `doc/ER.md` | Entities or relationships change |
| `doc/RTM.md` | Requirements or modules change |
| `doc/UserStories.md` | New user stories or acceptance criteria change |
| `doc/ADR.md` | New architecture decisions made |
| `doc/QuickStart.md` | Setup or build process changes |
| `doc/Governance.md` | Process or conventions change |
| `doc/CRM.md` | Change management process changes |
| `TOCTREE.md` | Documents added or removed |
| `README.md` | Project overview, links, or URLs change |

### 5.2 Consistency Rule

If a code change affects any document's content, that document must be updated
in the same commit. For example, if a new species is added to the roster:
- Update `doc/PRD.md` (§2 roster tables)
- Update `doc/Schema.md` (§6.1 species definitions)
- Update `doc/ER.md` (if new entity/relationship)
- Update `CHANGELOG.md` (new version entry)

---

## 6. Related Documents

- [AGENTS.md](../AGENTS.md) — Agent/AI workflow conventions
- [CRM.md](CRM.md) — Change management process
- [CHANGELOG.md](../CHANGELOG.md) — Version history
- [QuickStart.md](QuickStart.md) — Development setup
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
