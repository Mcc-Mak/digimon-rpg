# Table of Contents — digimon-rpg

Master table of contents for the **digimon-rpg** project documentation set.
This file is referenced by [`README.md`](README.md) and serves as the canonical
index for all project documents.

---

## Root Documents

| Document | Description |
|---|---|
| [README.md](README.md) | Project overview, quick links, and GitHub Pages entrypoint |
| [TOCTREE.md](TOCTREE.md) | This file — master table of contents |
| [CHANGELOG.md](CHANGELOG.md) | Semantic-version changelog of all notable changes |
| [AGENTS.md](AGENTS.md) | Agent/AI workflow conventions and project status |
| [LICENSE](LICENSE) | MIT License |

---

## Design & Requirements (`doc/`)

| Document | Description |
|---|---|
| [doc/ProjectCharter.md](doc/ProjectCharter.md) | Project scope, objectives, stakeholders, and success criteria |
| [doc/PRD.md](doc/PRD.md) | Product Requirements: game mechanics, roster, battle system, evolution/progression |
| [doc/SRS.md](doc/SRS.md) | Software Requirements: functional/non-functional, pygbag/WASM constraints |
| [doc/UserStories.md](doc/UserStories.md) | Player stories for each scene and progression milestone |

---

## Architecture & Engineering (`doc/`)

| Document | Description |
|---|---|
| [doc/Architecture.md](doc/Architecture.md) | Module structure, scene system, data flow, async game loop |
| [doc/ADR.md](doc/ADR.md) | Architecture Decision Records |
| [doc/ER.md](doc/ER.md) | Entity-Relationship diagram and descriptions |
| [doc/Schema.md](doc/Schema.md) | Data schemas using Python dataclasses |
| [doc/API.md](doc/API.md) | Module and function API reference |

---

## Operations & Governance (`doc/`)

| Document | Description |
|---|---|
| [doc/QuickStart.md](doc/QuickStart.md) | Local development and pygbag build instructions |
| [doc/RTM.md](doc/RTM.md) | Requirements Traceability Matrix |
| [doc/Governance.md](doc/Governance.md) | Branch strategy, commit conventions, CHANGELOG rules |
| [doc/CRM.md](doc/CRM.md) | Change Management Process |

---

## Document Dependency Graph

```
ProjectCharter.md
    │
    ├── PRD.md ──────────────────┐
    │       │                     │
    │       └── UserStories.md    │
    │                               │
    ├── SRS.md ────────────────────┤
    │                               │
    ├── Architecture.md ──┐         │
    │       │              │         │
    │       ├── ADR.md     │         │
    │       ├── ER.md ─────┤         │
    │       ├── Schema.md ─┤         │
    │       └── API.md ────┘         │
    │                               │
    ├── QuickStart.md                │
    │                               │
    └── RTM.md ◄────────────────────┘ (traces all requirements)
    
    Governance.md ──► CHANGELOG.md
    CRM.md ────────► Governance.md
```

## Reading Order

1. **New team members**: `README.md` → `TOCTREE.md` → `ProjectCharter.md` → `PRD.md`
2. **Engineers**: `Architecture.md` → `ADR.md` → `Schema.md` → `API.md` → `QuickStart.md`
3. **QA**: `SRS.md` → `RTM.md` → `UserStories.md`
4. **Project managers**: `ProjectCharter.md` → `Governance.md` → `CRM.md` → `CHANGELOG.md`
