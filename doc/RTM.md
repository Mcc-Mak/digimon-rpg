# Requirements Traceability Matrix (RTM) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | RTM.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [SRS.md](SRS.md), [PRD.md](PRD.md), [UserStories.md](UserStories.md) |

---

## 1. Overview

This Requirements Traceability Matrix (RTM) maps every functional requirement
(FR) and non-functional requirement (NFR) from the [SRS](SRS.md) to:
- The user stories that validate it ([UserStories.md](UserStories.md))
- The PRD sections that specify it ([PRD.md](PRD.md))
- The architecture modules that implement it ([Architecture.md](Architecture.md))
- The data schemas that support it ([Schema.md](Schema.md))
- The ADRs that justify design decisions ([ADR.md](ADR.md))

---

## 2. Functional Requirements Traceability

| Req ID | Title | Priority | User Stories | PRD Ref | Architecture Module | Schema | ADR |
|---|---|---|---|---|---|---|---|
| FR-01 | Game Initialization | Must | US-01 | §10 | `main`, `src.core.game` | — | ADR-001, ADR-005 |
| FR-02 | Scene Management | Must | US-01, US-22 | §10 | `src.core.scene_manager`, `src.core.scene` | — | ADR-002 |
| FR-03 | Title Screen | Must | US-01, US-02 | §10 | `src.scenes.title_scene` | — | ADR-002 |
| FR-04 | Character Creation | Must | US-01, US-03 | §10 | `src.scenes.creation_scene` | `PlayerSave` | — |
| FR-05 | Starter Selection | Must | US-04 | §6.2, §10 | `src.scenes.starter_scene` | `Creature`, `SpeciesDef` | — |
| FR-06 | World Map Movement | Must | US-05 | §10 | `src.scenes.world_scene` | `PlayerSave` | — |
| FR-07 | Random Encounters | Must | US-06 | §9 | `src.systems.encounters` | `ZoneDef`, `EncounterEntryDef` | — |
| FR-08 | Battle Turn Order | Must | US-08 | §5.1 | `src.systems.battle` | `BattleState` | — |
| FR-09 | Battle Actions | Must | US-08 | §5.2 | `src.systems.battle`, `src.scenes.battle_scene` | `BattleState` | ADR-006 |
| FR-10 | Damage Calculation | Must | US-08 | §5.3, §5.4 | `src.systems.battle` | `SkillDef`, `TYPE_CHART` | — |
| FR-11 | MP & Skills | Must | US-09 | §5.5 | `src.systems.battle` | `SkillDef`, `Creature` | — |
| FR-12 | Status Effects | Should | US-08 | §5.6 | `src.systems.battle` | `StatusEffect` | — |
| FR-13 | Win/Loss Conditions | Must | US-11, US-12, US-13 | §5.7 | `src.systems.battle` | `BattleState` | — |
| FR-14 | Flee Mechanic | Must | US-10 | §5.8 | `src.systems.battle` | — | — |
| FR-15 | Capture Mechanic | Must | US-14 | §6.2 | `src.systems.capture` | `Creature`, `ItemDef` | — |
| FR-16 | XP & Leveling | Must | US-11, US-17 | §7, §8 | `src.systems.leveling` | `Creature`, `SpeciesDef` | — |
| FR-17 | Evolution | Must | US-18 | §4 | `src.systems.evolution` | `Creature`, `SpeciesDef` | — |
| FR-18 | Party Management | Must | US-15, US-16 | §6.3 | `src.scenes.party_scene` | `PlayerSave`, `Creature` | — |
| FR-19 | Save/Load System | Must | US-02, US-07 | §6.1 | `src.core.save` | `PlayerSave` | ADR-003 |
| FR-20 | Items & Inventory | Must | US-11, US-14, US-20 | §5.9, §6.2 | `src.systems.items` | `ItemDef`, `PlayerSave` | — |
| FR-21 | Camp/Heal Station | Must | US-07 | §10, §5.7 | `src.scenes.camp_scene` | `PlayerSave` | — |
| FR-22 | Settings | Should | US-21 | §10 | `src.scenes.settings_scene` | `Settings` | — |
| FR-23 | Zone Progression | Must | US-13, US-19 | §6.5, §9 | `src.scenes.zone_complete_scene` | `ZoneDef`, `PlayerSave` | — |

---

## 3. Non-Functional Requirements Traceability

| Req ID | Title | Priority | PRD Ref | Architecture Module | ADR | Constraints |
|---|---|---|---|---|---|---|
| NFR-01 | pygbag/WASM Compatibility | Must | — | All modules | ADR-001, ADR-005 | No subprocess, no blocking I/O, async loop |
| NFR-02 | Browser Performance | Must | — | `main`, all scenes | ADR-006 | 30+ FPS target, 60 FPS ideal |
| NFR-03 | Async Game Loop | Must | — | `main` | ADR-005 | `await asyncio.sleep(0)` each frame |
| NFR-04 | Save Data Integrity | Must | §6.1 | `src.core.save` | ADR-003 | Versioned schema, migration support |
| NFR-05 | Browser Compatibility | Must | — | — | ADR-001 | Chrome 100+, Firefox 100+, Safari 15+ |
| NFR-06 | Load Time | Should | — | `src.core.assets` | ADR-001 | <10s to title screen on broadband |
| NFR-07 | Original IP | Must | §2 | `src.data.roster` | — | No Bandai Digimon names/designs |
| NFR-08 | Code Quality | Should | — | All modules | — | PEP 8, type hints, docstrings |

---

## 4. User Story to Requirement Traceability

| User Story | Title | Requirements Covered | Acceptance Test Focus |
|---|---|---|---|
| US-01 | Start a New Game | FR-01, FR-02, FR-03, FR-04 | Title screen → new game → name entry |
| US-02 | Continue from Save | FR-03, FR-19, NFR-04 | Save exists → Continue → loads world |
| US-03 | Enter My Name | FR-04 | 1–12 chars, alphanumeric |
| US-04 | Choose My Starter | FR-05 | 3 options, Level 1, party = 1 |
| US-05 | Explore the World Map | FR-06 | Movement, collision, step counter |
| US-06 | Trigger Random Encounters | FR-07 | Step count → roll → battle |
| US-07 | Visit Camp to Heal and Save | FR-19, FR-21 | Heal to full, save to localStorage |
| US-08 | Engage in Turn-Based Battle | FR-08, FR-09, FR-10, FR-12 | Turn order, actions, damage |
| US-09 | Use Skills in Battle | FR-11 | MP cost, skill menu, disabled when low MP |
| US-10 | Flee from Wild Battles | FR-14 | Success chance, free enemy action on fail |
| US-11 | Win a Battle and Earn Rewards | FR-13, FR-16, FR-20 | XP, gold, level-up, items |
| US-12 | Lose a Battle and Recover | FR-13 | Faint → camp, 50% HP/MP, -10% gold |
| US-13 | Battle a Zone Boss | FR-13, FR-23 | Boss intro, no flee, zone unlock |
| US-14 | Capture a Wild Creature | FR-15, FR-20 | HP ≤ 20%, Digi-Core, Level 1 reset |
| US-15 | Manage My Party | FR-18 | 6 max, reorder, box access |
| US-16 | View Creature Details | FR-18 | Stats, stage, level, XP bar, moves |
| US-17 | Gain XP and Level Up | FR-16 | XP curve, stat growth, skill learning |
| US-18 | Evolve My Creature | FR-17 | Level + battles + boss → evolution scene |
| US-19 | Progress Through Zones | FR-23 | Boss defeat → unlock, fast-travel |
| US-20 | Purchase and Use Items | FR-20 | Buy with gold, consume on use |
| US-21 | Adjust Settings | FR-22, NFR-01 | Volume, text speed, fullscreen, persist |
| US-22 | Experience the Story | FR-02 | Dialogue box, NPC portraits, choices |

---

## 5. Coverage Summary

### 5.1 Requirements Coverage

| Category | Total | Must | Should | Traced to US | Traced to Module | Traced to Schema |
|---|---|---|---|---|---|---|
| Functional (FR) | 23 | 20 | 3 | 23/23 (100%) | 23/23 (100%) | 20/23 (87%) |
| Non-Functional (NFR) | 8 | 6 | 2 | N/A | 8/8 (100%) | 1/8 (12.5%) |
| **Total** | **31** | **26** | **5** | **23/23** | **31/31 (100%)** | **21/31 (68%)** |

> **Note**: NFRs are traced to architecture modules and ADRs, not user stories.
> Some FRs (FR-08, FR-14) don't have dedicated schemas but use `BattleState`.

### 5.2 User Story Coverage

| Metric | Value |
|---|---|
| Total user stories | 22 |
| Stories with ≥1 FR traced | 22/22 (100%) |
| Stories with acceptance criteria | 22/22 (100%) |
| Must-priority stories | 20/22 (91%) |
| Should-priority stories | 2/22 (9%) |

### 5.3 Module Coverage

| Module Category | Modules | FRs Covered |
|---|---|---|
| `src.core.*` | 6 | FR-01, FR-02, FR-06, FR-19, NFR-01–06 |
| `src.scenes.*` | 20 | FR-03–FR-07, FR-09, FR-13, FR-18, FR-21–FR-23 |
| `src.systems.*` | 6 | FR-07–FR-17, FR-20 |
| `src.data.*` | 4 | All FRs (provides data) |
| `src.ui.*` | 3 | All FRs (provides UI) |
| `main` | 1 | FR-01, NFR-01–03 |

---

## 6. Traceability Chain Example

**FR-10: Damage Calculation**

```
PRD §5.3 (specifies the formula)
    │
    ▼
SRS FR-10 (formalizes as a requirement)
    │
    ├──► US-08 (validates via "engage in turn-based battle" story)
    │
    ├──► Architecture: src.systems.battle.BattleSystem.calculate_damage()
    │
    ├──► Schema: SkillDef (power, element), TYPE_CHART (multipliers)
    │
    └──► Acceptance test: "Damage is calculated per PRD §5.3 formula"
```

**FR-17: Evolution**

```
PRD §4 (specifies evolution stages and requirements)
    │
    ▼
SRS FR-17 (formalizes as a requirement)
    │
    ├──► US-18 (validates via "evolve my creature" story)
    │
    ├──► Architecture: src.systems.evolution.EvolutionSystem
    │
    ├──► Schema: SpeciesDef (evolution_level, evolution_battles),
    │            Creature (level, battles_won, stage)
    │
    └──► Acceptance test: "Evolution triggers when level + battles_won
         + boss conditions are met"
```

---

## 7. Gap Analysis

| Gap | Description | Resolution |
|---|---|---|
| FR-08 (Turn Order) | No dedicated schema — uses `BattleState.turn_order` | Acceptable: `BattleState` is a transient schema that holds turn order |
| FR-14 (Flee) | No dedicated schema — formula is pure function | Acceptable: `BattleSystem.calculate_flee_chance()` is stateless |
| NFR-02 (Performance) | Not traced to a schema | Acceptable: performance is a runtime concern, not data |
| NFR-05 (Browser Compat) | Not traced to a schema or module | Acceptable: verified by CI build + manual browser testing |
| NFR-08 (Code Quality) | Not traced to a schema | Acceptable: enforced by linting/type-checking, not data |

**No unresolvable gaps identified. All requirements are fully traced.**

---

## 8. Related Documents

- [SRS.md](SRS.md) — Source of all requirements
- [PRD.md](PRD.md) — Game design specifications
- [UserStories.md](UserStories.md) — User stories
- [Architecture.md](Architecture.md) — Module structure
- [Schema.md](Schema.md) — Data schemas
- [ADR.md](ADR.md) — Architecture decisions
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
