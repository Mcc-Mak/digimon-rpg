# User Stories — digimon-rpg

| Field | Value |
|---|---|
| **Document** | UserStories.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [PRD.md](PRD.md), [SRS.md](SRS.md) |

---

## 1. Overview

This document presents player stories organized by scene and progression
milestone. Each story follows the format:

> **As a** [role], **I want** [feature], **so that** [benefit].

Stories are mapped to functional requirements (FR-IDs from [SRS.md](SRS.md))
and the scenes defined in PRD §10.

---

## 2. Title & Onboarding Stories

### US-01: Start a New Game

**As a** new player, **I want** to start a new game from the title screen, **so
that** I can begin my adventure.

- **Scene**: Title Screen (Scene 1)
- **Requirements**: FR-03, FR-04
- **Acceptance Criteria**:
  - Title screen displays game logo and "Press Start" prompt.
  - Selecting "New Game" transitions to character creation.
  - "Continue" is disabled when no save exists.

### US-02: Continue from Save

**As a** returning player, **I want** to continue my previous game, **so that**
I don't lose progress.

- **Scene**: Title Screen (Scene 1)
- **Requirements**: FR-03, FR-19
- **Acceptance Criteria**:
  - "Continue" is enabled when a save exists.
  - Selecting "Continue" loads the save and transitions to the world map at the
    saved position.

### US-03: Enter My Name

**As a** player, **I want** to enter my tamer name, **so that** the game feels
personalized.

- **Scene**: Character Creation (Scene 2)
- **Requirements**: FR-04
- **Acceptance Criteria**:
  - Text field accepts 1–12 alphanumeric characters.
  - On confirmation, a new save profile is created with the entered name.

### US-04: Choose My Starter

**As a** new player, **I want** to choose my first creature from 3 options, **so
that** I have a partner to begin my journey.

- **Scene**: Starter Selection (Scene 3)
- **Requirements**: FR-05
- **Acceptance Criteria**:
  - Three starters are displayed: Emberling, Aquapup, Seedkit.
  - Each starter shows its element type and base stats.
  - Selected starter is added to party at Level 1.
  - Transition to World Map (Verdant Plains) after selection.

---

## 3. World Exploration Stories

### US-05: Explore the World Map

**As a** player, **I want** to move my character around the map, **so that** I
can explore the world and find encounters.

- **Scene**: World Map (Scene 4)
- **Requirements**: FR-06
- **Acceptance Criteria**:
  - Arrow keys / WASD move the player sprite.
  - Movement is smooth and collision-aware (can't walk through walls/water).
  - A step counter increments with movement.

### US-06: Trigger Random Encounters

**As a** player, **I want** to encounter wild creatures as I explore, **so that**
I can battle and gain XP.

- **Scene**: World Map → Battle Transition → Battle (Scenes 4, 6, 5)
- **Requirements**: FR-07
- **Acceptance Criteria**:
  - Step counter triggers encounter check at zone-defined intervals.
  - Wild creature is selected from zone encounter table (weighted random).
  - Battle transition animation plays before battle scene.

### US-07: Visit Camp to Heal and Save

**As a** player, **I want** to visit a camp to heal my party and save my game,
**so that** I can recover and preserve my progress.

- **Scene**: Save/Camp Scene (Scene 12)
- **Requirements**: FR-21, FR-19
- **Acceptance Criteria**:
  - Entering camp heals all party creatures to full HP/MP.
  - Save option writes current game state to localStorage.
  - Box management accessible from camp.

---

## 4. Battle Stories

### US-08: Engage in Turn-Based Battle

**As a** player, **I want** to battle wild creatures in turn-based combat, **so
that** I can test my creature's strength and earn rewards.

- **Scene**: Battle Scene (Scene 5)
- **Requirements**: FR-08, FR-09, FR-10
- **Acceptance Criteria**:
  - Turn order determined by initiative (speed + random).
  - Player can choose Attack, Skill, Item, Switch, or Flee.
  - Damage is calculated per the formula in PRD §5.3.
  - HP/MP bars update in real-time.

### US-09: Use Skills in Battle

**As a** player, **I want** to use my creature's skills, **so that** I can deal
more damage or apply status effects.

- **Scene**: Battle Scene (Scene 5)
- **Requirements**: FR-11
- **Acceptance Criteria**:
  - Skill menu shows up to 4 learned skills with name, type, power, MP cost.
  - Skills with insufficient MP are disabled.
  - Using a skill consumes MP and calculates damage/effects.

### US-10: Flee from Wild Battles

**As a** player, **I want** to flee from wild encounters, **so that** I can
avoid unwanted battles.

- **Scene**: Battle Scene (Scene 5)
- **Requirements**: FR-14
- **Acceptance Criteria**:
  - Flee option available in wild encounters only.
  - Flee success calculated per formula, clamped to [40%, 90%].
  - Failed flee results in a free enemy action.
  - Flee disabled in boss battles.

### US-11: Win a Battle and Earn Rewards

**As a** player, **I want** to win battles and earn XP and gold, **so that** I
can level up my creatures and buy items.

- **Scene**: Victory/Post-Battle Screen (Scene 15)
- **Requirements**: FR-13, FR-16, FR-20
- **Acceptance Criteria**:
  - Victory screen displays XP gained per participating creature.
  - Gold awarded.
  - Level-up notifications displayed if applicable.
  - Item drops shown if applicable.

### US-12: Lose a Battle and Recover

**As a** player, **I want** to recover from a battle loss without losing
everything, **so that** the game remains fair.

- **Scene**: Game Over Screen (Scene 14) → Save/Camp Scene (Scene 12)
- **Requirements**: FR-13
- **Acceptance Criteria**:
  - When all party creatures faint, Game Over screen appears.
  - Player is returned to nearest camp.
  - All creatures revived to 50% HP/MP.
  - 10% of gold is lost.
  - No XP penalty.

### US-13: Battle a Zone Boss

**As a** player, **I want** to challenge and defeat zone bosses, **so that** I
can unlock new zones and progress.

- **Scene**: Boss Fight Intro (Scene 16) → Battle Scene (Scene 5) → Zone
  Completion (Scene 17)
- **Requirements**: FR-13, FR-23
- **Acceptance Criteria**:
  - Boss intro animation plays before battle.
  - Boss battle cannot be fled from.
  - On victory, zone completion screen shows unlocked content.
  - Next zone is accessible.

---

## 5. Capture & Party Management Stories

### US-14: Capture a Wild Creature

**As a** player, **I want** to capture wild creatures using Digi-Cores, **so
that** I can expand my party roster.

- **Scene**: Battle Scene (Scene 5) → Digi-Core/Capture Screen (Scene 11)
- **Requirements**: FR-15, FR-20
- **Acceptance Criteria**:
  - Digi-Core usable when wild creature HP ≤ 20% max.
  - Capture chance calculated per formula (42% base + bonuses).
  - On success, creature joins party (or Box if party full).
  - Captured creature starts at Level 1.

### US-15: Manage My Party

**As a** player, **I want** to view and reorder my party, **so that** I can
choose which creatures to bring into battle.

- **Scene**: Party Menu (Scene 7)
- **Requirements**: FR-18
- **Acceptance Criteria**:
  - Party menu shows up to 6 creatures with HP/MP bars, levels, species.
  - Player can reorder party members.
  - Player can switch active/bench designations.
  - Box accessible for transferring creatures in/out.

### US-16: View Creature Details

**As a** player, **I want** to view detailed stats for my creatures, **so that**
I can plan my strategy.

- **Scene**: Creature Info Screen (Scene 8), Skill/Move Grid (Scene 9)
- **Requirements**: FR-18
- **Acceptance Criteria**:
  - Detail view shows all stats (HP, MP, Atk, Def, Spd), stage, level, XP bar.
  - Learned moves displayed with type, power, MP cost.
  - Evolution readiness indicator shown.

---

## 6. Progression & Evolution Stories

### US-17: Gain XP and Level Up

**As a** player, **I want** my creatures to gain XP and level up from battles,
**so that** they become stronger.

- **Scene**: Victory/Post-Battle Screen (Scene 15)
- **Requirements**: FR-16
- **Acceptance Criteria**:
  - XP awarded to participating creatures after battle.
  - When XP threshold reached, level-up notification displays stat increases.
  - Stats recalculated using per-species growth rates.
  - New skills learned at appropriate levels.

### US-18: Evolve My Creature

**As a** player, **I want** to evolve my creatures to their next stage, **so
that** they gain new abilities and higher stats.

- **Scene**: Evolution Scene (Scene 13)
- **Requirements**: FR-17
- **Acceptance Criteria**:
  - Evolution triggers when level + battles_won + boss conditions are met.
  - Evolution animation plays (silhouette → glow → new form).
  - New stats displayed with comparison to old stats.
  - Evolution is irreversible.
  - New species skills become available.

### US-19: Progress Through Zones

**As a** player, **I want** to unlock new zones by defeating bosses, **so that**
I can explore new areas and find new creatures.

- **Scene**: Zone Completion Screen (Scene 17) → World Map (Scene 4)
- **Requirements**: FR-23
- **Acceptance Criteria**:
  - Defeating Zone 1 boss (Nature Warden) unlocks Storm Peaks.
  - Defeating Zone 2 boss (Storm King) unlocks Abyssal Depths.
  - Fast-travel unlocked to cleared zone camps.
  - New zones have higher-level wild encounters.

---

## 7. Economy & Item Stories

### US-20: Purchase and Use Items

**As a** player, **I want** to buy and use items, **so that** I can heal and
support my creatures in and out of battle.

- **Scene**: Items/Inventory Screen (Scene 10), Battle Scene (Scene 5)
- **Requirements**: FR-20
- **Acceptance Criteria**:
  - Items available: Potion, Super Potion, Elixir, Antidote, Revive, Digi-Core,
    Training Stone.
  - Items purchased with gold at shops (in camp/world).
  - Items consumed on use.
  - Items usable in battle (costs the turn).

---

## 8. Meta & Settings Stories

### US-21: Adjust Settings

**As a** player, **I want** to adjust audio volume and display settings, **so
that** I can customize my experience.

- **Scene**: Settings Screen (Scene 19)
- **Requirements**: FR-22
- **Acceptance Criteria**:
  - Music volume slider (0–100%).
  - SFX volume slider (0–100%).
  - Text speed option (slow/medium/fast).
  - Fullscreen toggle.
  - Settings persist via localStorage.

### US-22: Experience the Story

**As a** player, **I want** to experience the game's narrative through dialogue
and cutscenes, **so that** I feel immersed in the world.

- **Scene**: Dialogue/Cutscene Overlay (Scene 18)
- **Requirements**: FR-02
- **Acceptance Criteria**:
  - NPC dialogue appears in a text box at the bottom of the screen.
  - Player advances text with Enter/Space.
  - Branching dialogue choices supported (arrows + Enter).
  - NPC portraits displayed.

---

## 9. Story Arc — Player Journey Summary

| Story | Milestone | Key Scene |
|---|---|---|
| **The Journey Begins** | First creature acquired | Title → Creation → Starter Selection |
| **First Steps** | First wild battle; first capture; first faint/recovery | World Map → Battle |
| **The Nature Warden** | Zone 1 boss defeated; Zone 2 unlocked | Boss Intro → Battle → Zone Completion |
| **Scaling the Storm Peaks** | Champion-stage party; Rival battles | World Map → Battle |
| **The Storm King** | Zone 2 boss defeated; Zone 3 unlocked | Boss Intro → Battle → Zone Completion |
| **Into the Abyss** | Ultimate-stage creature; Zone 3 explored | World Map → Battle |
| **The Abyssal Overlord** | Zone 3 boss defeated; final dungeon unlocked | Boss Intro → Battle → Zone Completion |
| **The Throne of Corruption** | Final boss defeated; game cleared | Boss Intro → Battle → Credits |
| **Post-Game** | Master Tamer challenges; 100% completion | World Map → Battle |

---

## 10. Story-to-Requirement Traceability

| User Story | Requirement IDs | Priority |
|---|---|---|
| US-01 | FR-03, FR-04 | Must |
| US-02 | FR-03, FR-19 | Must |
| US-03 | FR-04 | Must |
| US-04 | FR-05 | Must |
| US-05 | FR-06 | Must |
| US-06 | FR-07 | Must |
| US-07 | FR-21, FR-19 | Must |
| US-08 | FR-08, FR-09, FR-10 | Must |
| US-09 | FR-11 | Must |
| US-10 | FR-14 | Must |
| US-11 | FR-13, FR-16, FR-20 | Must |
| US-12 | FR-13 | Must |
| US-13 | FR-13, FR-23 | Must |
| US-14 | FR-15, FR-20 | Must |
| US-15 | FR-18 | Must |
| US-16 | FR-18 | Must |
| US-17 | FR-16 | Must |
| US-18 | FR-17 | Must |
| US-19 | FR-23 | Must |
| US-20 | FR-20 | Must |
| US-21 | FR-22 | Should |
| US-22 | FR-02 | Should |

---

## 11. Related Documents

- [PRD.md](PRD.md) — Game design and mechanics
- [SRS.md](SRS.md) — Software requirements
- [RTM.md](RTM.md) — Requirements traceability matrix
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
