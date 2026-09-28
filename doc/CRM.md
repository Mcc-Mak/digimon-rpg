# Change Management Process (CRM) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | CRM.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [Governance.md](Governance.md), [AGENTS.md](../AGENTS.md) |

---

## 1. Overview

This document defines the change management process for **digimon-rpg**. It
describes how changes are proposed, evaluated, implemented, verified, and
documented. The process ensures that all changes are traceable, consistent
with the documentation set, and do not break the pygbag/WASM build.

---

## 2. Change Categories

| Category | Description | Examples | Process |
|---|---|---|---|
| **Trivial** | Typo fixes, doc-only edits, formatting | Fix a typo in PRD.md | Self-review → commit → push |
| **Minor** | Small code changes, bug fixes, single-function additions | Fix evolution bonus bug; add a UI widget | Self-review → test → commit → push |
| **Standard** | New features, new scenes, new systems, schema changes | Add battle system; add Zone 3 data | Proposal → implement → test → review → commit → push |
| **Major** | Architecture changes, breaking schema changes, new ADRs | Change save format v1→v2; replace scene manager | Proposal → discuss → ADR → implement → test → review → commit → push |

---

## 3. Change Process

### 3.1 Trivial Changes

```
1. Make the change.
2. Self-review (does it look right?).
3. Commit with proper message format (see Governance.md §2).
4. Update CHANGELOG.md if user-visible.
5. Push to dev-001.
```

### 3.2 Minor Changes

```
1. Make the change.
2. Run locally: python main.py
3. Run tests: pytest tests/
4. Verify pygbag build: python -m pygbag --build main.py
5. Update CHANGELOG.md.
6. Commit with proper message format.
7. Push to dev-001.
```

### 3.3 Standard Changes

```
1. Write a brief change proposal (see §4 below).
2. Implement the change on dev-001 (or a local feature branch).
3. Update all affected documents (see Governance.md §5).
4. Run locally: python main.py
5. Run tests: pytest tests/
6. Verify pygbag build: python -m pygbag --build main.py
7. Update CHANGELOG.md with semantic version bump.
8. Commit with proper message format.
9. Push to dev-001.
10. Monitor CI pipeline for build/deploy success.
```

### 3.4 Major Changes

```
1. Write a change proposal (see §4 below).
2. Write an ADR (Architecture Decision Record) in doc/ADR.md.
3. Discuss with the team (if applicable).
4. Implement the change on a local feature branch.
5. Update ALL affected documents.
6. Run locally: python main.py
7. Run tests: pytest tests/
8. Verify pygbag build: python -m pygbag --build main.py
9. Update CHANGELOG.md with semantic version bump (major or minor).
10. Merge feature branch into dev-001.
11. Commit with proper message format.
12. Push to dev-001.
13. Monitor CI pipeline for build/deploy success.
14. Verify the live site: https://mcc-mak.github.io/digimon-rpg/
```

---

## 4. Change Proposal Template

For Standard and Major changes, write a brief proposal before implementing.
This can be a comment in the commit, a document section, or a discussion item.

```markdown
## Change Proposal: [Title]

**Category**: Standard / Major
**Date**: YYYY-MM-DD
**Proposer**: [Name]

### Summary
[1-2 sentence description of the change]

### Motivation
[Why is this change needed? What problem does it solve?]

### Affected Documents
- [List of documents that will need updating]

### Affected Requirements
- [FR/NFR IDs that are impacted]

### Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Risk Assessment
- [What could go wrong? How to mitigate?]

### Version Impact
- [Expected version bump: patch / minor / major]
```

---

## 5. Document Update Matrix

When a change affects a particular area, these documents must be updated:

| Change Area | Documents to Update |
|---|---|
| Game mechanics (battle, stats, evolution) | PRD.md, SRS.md, Schema.md, RTM.md, CHANGELOG.md |
| New creature/species added | PRD.md (§2), Schema.md (§6.1), ER.md, CHANGELOG.md |
| New zone/encounter table | PRD.md (§9), Schema.md (§6.4), CHANGELOG.md |
| New scene | PRD.md (§10), Architecture.md (§2, §3), API.md (§21), SRS.md, UserStories.md, RTM.md, CHANGELOG.md |
| Schema change (new field/entity) | Schema.md, ER.md, Architecture.md (if data flow), CHANGELOG.md |
| API change (new/modified function) | API.md, Architecture.md (if module structure), CHANGELOG.md |
| Architecture decision | ADR.md, Architecture.md, CHANGELOG.md |
| Save format change | Schema.md (§4.3), ADR.md (if strategy change), SRS.md (FR-19), CHANGELOG.md |
| Branch/workflow change | Governance.md, AGENTS.md, CHANGELOG.md |
| Build/deployment change | QuickStart.md, SRS.md (§4.3), CHANGELOG.md |

---

## 6. Emergency Changes (Hotfixes)

If a critical bug is found in production (on the live GitHub Pages site):

```
1. Identify the bug and its cause.
2. Fix on dev-001 immediately.
3. Run: python main.py (verify fix)
4. Run: python -m pygbag --build main.py (verify build)
5. Update CHANGELOG.md (patch version, e.g., 0.3.1).
6. Commit: "Fix [bug description]

[Rationale: what caused the bug, why this fix works]"
7. Push to dev-001.
8. Wait for CI cascade (dev-001 → dev → main → Pages deploy).
9. Verify fix on live site.
10. Post-hoc: update any affected docs if the bug revealed a doc gap.
```

---

## 7. Rollback Procedure

If a deployed change causes a regression:

```
1. Identify the commit that caused the issue.
2. Revert on dev-001:
   git revert <commit-hash>
   git push origin dev-001
3. The CI cascade will deploy the reverted version.
4. Update CHANGELOG.md with a "Fixed" or "Reverted" entry.
5. Investigate root cause before re-attempting the change.
```

> **Note**: Because `dev-001 → dev → main` is a cascade, reverting on
> `dev-001` will propagate through the pipeline automatically. Do not attempt
> to revert on `dev` or `main` directly.

---

## 8. Versioning Rules

### 8.1 Semantic Versioning

| Version Part | When to Bump | Example |
|---|---|---|
| **Major** (X.0.0) | Breaking change to save schema, public API, or architecture | 0.3.0 → 1.0.0 (first stable release) |
| **Minor** (0.X.0) | New features, new content, new scenes, new systems | 0.3.0 → 0.4.0 (add battle system) |
| **Patch** (0.0.X) | Bug fixes, typo fixes, doc-only updates | 0.3.0 → 0.3.1 (fix evolution bug) |

### 8.2 Pre-1.0 Rules

While the project version is below 1.0.0:
- Minor versions may include breaking changes (e.g., 0.3.0 → 0.4.0 could
  change the save schema).
- Patch versions are strictly non-breaking.
- The first stable release will be 1.0.0.

### 8.3 Version in CHANGELOG.md

```markdown
## 0.4.0 - 2026-09-29

### Added
- [New features]

### Changed
- [Modified functionality]

### Fixed
- [Bug fixes]
```

The version number must be reflected in:
- `CHANGELOG.md` (version heading)
- `doc/ProjectCharter.md` (version field, if major/minor)
- Any ADRs that reference the version

---

## 9. Compliance Checklist

Before pushing any change to `dev-001`, verify:

- [ ] **Branch**: Working on `dev-001` (not `main` or `dev`).
- [ ] **Commit message**: Imperative subject + rationale body (Governance §2).
- [ ] **CHANGELOG.md**: Updated with semantic version entry.
- [ ] **Documents**: All affected docs updated (§5 above).
- [ ] **Tests**: `pytest tests/` passes.
- [ ] **Local run**: `python main.py` works.
- [ ] **Web build**: `python -m pygbag --build main.py` succeeds.
- [ ] **No subprocess**: No `subprocess`, `os.system`, `threading`, blocking
      I/O (NFR-01).
- [ ] **Async loop**: `await asyncio.sleep(0)` present in game loop (NFR-03).
- [ ] **Original IP**: No copyrighted material (NFR-07).
- [ ] **CI workflow**: `merge` job in `auto-merge.yml` not modified.

---

## 10. Related Documents

- [Governance.md](Governance.md) — Branch strategy, commit conventions, CHANGELOG rules
- [AGENTS.md](../AGENTS.md) — AI agent workflow and project status
- [CHANGELOG.md](../CHANGELOG.md) — Version history
- [QuickStart.md](QuickStart.md) — Development and build instructions
- [ProjectCharter.md](ProjectCharter.md) — Project scope and constraints
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
