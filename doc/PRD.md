# Product Requirements Document (PRD) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | PRD.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [ProjectCharter.md](ProjectCharter.md), [SRS.md](SRS.md), [Architecture.md](Architecture.md) |

---

## 1. Overview

**digimon-rpg** is a browser-based, turn-based monster-collection RPG. Players
capture, train, and evolve original creatures across multiple world zones. The
game features a type-effectiveness battle system, a 3-stage evolution
progression, and an XP-based leveling curve.

---

## 2. Original Digimon Roster

All creatures below are **original creations** — original names, original
designs, original abilities. They are inspired by the monster-collection and
evolution mechanics popularized by games like Digimon and Pokémon, but are not
derived from or affiliated with any copyrighted creature, name, artwork, or
mechanic of those franchises.

### 2.1 Roster Summary

| Rookie | Element | Champion | Ultimate |
|--------|---------|----------|----------|
| Emberling | 🔥 Fire | Pyroclaw | Infernosaur |
| Aquapup | 💧 Water | Tsunamut | Leviathore |
| Seedkit | 🌿 Nature | Thornbloom | Verdant Titan |
| Stormwing | ⚡ Electric | Voltalon | Thundergod |
| Rockbash | 🪨 Earth | Mountainhide | Terraroc |
| Chaospuff | 🌑 Dark | Wraithwing | Umbrathrax |

### 2.2 Rookie-Level Creatures (Base Forms, Level 1 Stats)

#### Emberling 🔥 (Fire)

A small, lizard-like creature with glowing ember patches along its spine. Its
tail flickers with a constant flame. Playful and curious.

| Stat | Value |
|---|---|
| HP | 100 |
| MP | 40 |
| Attack | 20 |
| Defense | 14 |
| Speed | 16 |

#### Aquapup 💧 (Water)

A round, seal-like creature with translucent fins that shimmer like water. Its
wide, hopeful eyes belie a fiercely protective nature.

| Stat | Value |
|---|---|
| HP | 110 |
| MP | 45 |
| Attack | 15 |
| Defense | 18 |
| Speed | 14 |

#### Seedkit 🌿 (Nature)

A small, leafy creature resembling a sprouting bulb with stubby legs. A single
flower bud sits atop its head. Calm and patient.

| Stat | Value |
|---|---|
| HP | 95 |
| MP | 55 |
| Attack | 16 |
| Defense | 17 |
| Speed | 13 |

#### Stormwing ⚡ (Electric)

A tiny raptor with crackling feathers that emit faint arcs of static
electricity. Highly energetic and fast.

| Stat | Value |
|---|---|
| HP | 90 |
| MP | 50 |
| Attack | 17 |
| Defense | 12 |
| Speed | 22 |

#### Rockbash 🪨 (Earth)

A stocky, armadillo-like creature covered in overlapping stone plates. When
threatened, it rolls into a near-impenetrable ball. Slow but sturdy.

| Stat | Value |
|---|---|
| HP | 130 |
| MP | 35 |
| Attack | 14 |
| Defense | 24 |
| Speed | 9 |

#### Chaospuff 🌑 (Dark)

A wispy, shadow-like creature that drifts more than it walks. Its body
constantly shifts shape. It thrives in darkness.

| Stat | Value |
|---|---|
| HP | 85 |
| MP | 60 |
| Attack | 18 |
| Defense | 11 |
| Speed | 20 |

### 2.3 Champion-Level Creatures (Stage 2)

#### Pyroclaw 🔥 (Fire) — evolves from Emberling

A muscular, quadrupedal beast with molten veins visible through cracks in its
hide. Its claws glow white-hot.

| Stat | Value |
|---|---|
| HP | 180 |
| MP | 80 |
| Attack | 45 |
| Defense | 32 |
| Speed | 30 |

#### Tsunamut 💧 (Water) — evolves from Aquapup

A powerful, otter-like creature with hundreds of water jets flowing around its
body. It commands water with a swipe of its enormous claws.

| Stat | Value |
|---|---|
| HP | 195 |
| MP | 85 |
| Attack | 35 |
| Defense | 40 |
| Speed | 26 |

#### Thornbloom 🌿 (Nature) — evolves from Seedkit

An elegant, plant-humanoid creature covered in layered petals and thick thorn
vines. The bud on its head has bloomed into a large flower.

| Stat | Value |
|---|---|
| HP | 170 |
| MP | 100 |
| Attack | 38 |
| Defense | 38 |
| Speed | 22 |

#### Voltalon ⚡ (Electric) — evolves from Stormwing

A large, eagle-like predator with wings that constantly crackle with arcs of
blue lightning. Its dive produces a sonic boom.

| Stat | Value |
|---|---|
| HP | 165 |
| MP | 90 |
| Attack | 42 |
| Defense | 25 |
| Speed | 48 |

#### Mountainhide 🪨 (Earth) — evolves from Rockbash

A massive, bear-like colossus whose stone plating has grown into a full
mountain-carapace. Small crystals glitter across its body.

| Stat | Value |
|---|---|
| HP | 240 |
| MP | 65 |
| Attack | 34 |
| Defense | 52 |
| Speed | 14 |

#### Wraithwing 🌑 (Dark) — evolves from Chaospuff

A haunting, bat-like specter formed of living shadow. Its wings fade into
darkness, and its eyes are two points of pale, cold light.

| Stat | Value |
|---|---|
| HP | 155 |
| MP | 115 |
| Attack | 40 |
| Defense | 22 |
| Speed | 38 |

### 2.4 Ultimate-Level Creatures (Stage 3)

#### Infernosaur 🔥 (Fire) — evolves from Pyroclaw

A great, draconic saurian whose body is wreathed in perpetual flame. Its breath
is a lance of pure plasma.

| Stat | Value |
|---|---|
| HP | 310 |
| MP | 140 |
| Attack | 85 |
| Defense | 58 |
| Speed | 44 |

#### Leviathore 💧 (Water) — evolves from Tsunamut

A colossal, serpentine leviathan whose form is composed almost entirely of
living, pressurized water. It summons tidal waves with a thought.

| Stat | Value |
|---|---|
| HP | 330 |
| MP | 150 |
| Attack | 65 |
| Defense | 72 |
| Speed | 38 |

#### Verdant Titan 🌿 (Nature) — evolves from Thornbloom

A towering, ancient tree-golem whose bark is petrified wood and whose canopy
forms a crown of flowers. When it walks, forests grow in its footsteps.

| Stat | Value |
|---|---|
| HP | 300 |
| MP | 165 |
| Attack | 72 |
| Defense | 70 |
| Speed | 28 |

#### Thundergod ⚡ (Electric) — evolves from Voltalon

A mythical, phoenix-like storm deity with feathers of pure ionized light. When
it cries, the sky answers.

| Stat | Value |
|---|---|
| HP | 285 |
| MP | 155 |
| Attack | 78 |
| Defense | 48 |
| Speed | 75 |

#### Terraroc 🪨 (Earth) — evolves from Mountainhide

A living mountain given form and fury. Its body is a continent of stone, and
crevasses split across its back. Every step is an earthquake.

| Stat | Value |
|---|---|
| HP | 380 |
| MP | 110 |
| Attack | 60 |
| Defense | 92 |
| Speed | 16 |

#### Umbrathrax 🌑 (Dark) — evolves from Wraithwing

A nightmare made manifest — a massive, shadow-dragon whose form swallows light.
Its wings blot out the sun, and it feeds on fear.

| Stat | Value |
|---|---|
| HP | 280 |
| MP | 175 |
| Attack | 80 |
| Defense | 50 |
| Speed | 60 |

### 2.5 All Stats Summary Table

| Species | Stage | HP | MP | Atk | Def | Spd |
|---|---|---|---|---|---|---|
| Emberling | Rookie | 100 | 40 | 20 | 14 | 16 |
| Aquapup | Rookie | 110 | 45 | 15 | 18 | 14 |
| Seedkit | Rookie | 95 | 55 | 16 | 17 | 13 |
| Stormwing | Rookie | 90 | 50 | 17 | 12 | 22 |
| Rockbash | Rookie | 130 | 35 | 14 | 24 | 9 |
| Chaospuff | Rookie | 85 | 60 | 18 | 11 | 20 |
| Pyroclaw | Champion | 180 | 80 | 45 | 32 | 30 |
| Tsunamut | Champion | 195 | 85 | 35 | 40 | 26 |
| Thornbloom | Champion | 170 | 100 | 38 | 38 | 22 |
| Voltalon | Champion | 165 | 90 | 42 | 25 | 48 |
| Mountainhide | Champion | 240 | 65 | 34 | 52 | 14 |
| Wraithwing | Champion | 155 | 115 | 40 | 22 | 38 |
| Infernosaur | Ultimate | 310 | 140 | 85 | 58 | 44 |
| Leviathore | Ultimate | 330 | 150 | 65 | 72 | 38 |
| Verdant Titan | Ultimate | 300 | 165 | 72 | 70 | 28 |
| Thundergod | Ultimate | 285 | 155 | 78 | 48 | 75 |
| Terraroc | Ultimate | 380 | 110 | 60 | 92 | 16 |
| Umbrathrax | Ultimate | 280 | 175 | 80 | 50 | 60 |

---

## 3. Type Effectiveness

Six elements: 🔥 Fire, 💧 Water, 🌿 Nature, ⚡ Electric, 🪨 Earth, 🌑 Dark.

### Type Multiplier Table

| Attacker ↓ / Defender → | Fire | Water | Nature | Electric | Earth | Dark |
|---|---|---|---|---|---|---|
| **Fire**    | 1.0 | **0.5** | **2.0** | 1.0 | 0.75 | 1.0 |
| **Water**   | **2.0** | 1.0 | 0.75 | **0.5** | **2.0** | 1.0 |
| **Nature**  | 0.75 | **2.0** | 1.0 | 1.0 | **2.0** | 1.0 |
| **Electric**| 1.0 | **2.0** | 1.0 | 0.75 | **0.5** | **2.0** |
| **Earth**   | **2.0** | 0.75 | 0.75 | **2.0** | 1.0 | 1.0 |
| **Dark**    | 1.0 | 1.0 | 1.0 | **0.5** | 1.0 | **2.0** |

Legend: **2.0** = Super Effective, **0.5** = Not Very Effective, **0.75** =
Slightly Resisted, 1.0 = Neutral.

---

## 4. Evolution Stages & Requirements

### 4.1 Overview

Each creature has exactly 3 evolution stages:
- **Rookie** (Stage 1) → **Champion** (Stage 2) → **Ultimate** (Stage 3)

Evolution is **irreversible**. Once a creature evolves, its species permanently
changes.

### 4.2 Fields Tracked Per Creature

- `stage` (int 1–3)
- `level` (int 1–50)
- `battles_won` (int) — lifetime battles won by this creature

### 4.3 Per-Stage Evolution Requirements

#### Rookie → Champion (Stage 1 → Stage 2)

| Condition | Value |
|---|---|
| Minimum Level | **Level 10** |
| Minimum Battles Won | **5** |
| Additional Condition | None |

#### Champion → Ultimate (Stage 2 → Stage 3)

| Condition | Value |
|---|---|
| Minimum Level | **Level 25** |
| Minimum Battles Won | **15 total** (cumulative, since capture) |
| Additional Condition | Defeat at least **1 Rival Tamer boss battle** |

### 4.4 Evolution Check Timing

Evolution checks occur:
1. After battle victory.
2. On the level-up screen.
3. At the world/camp screen.

Evolution does **not** occur mid-battle.

### 4.5 Stat Changes on Evolution

When a creature evolves, its base stats are replaced with the new stage's base
stats, then its current level-up growth is recomputed from the new base.
Percentage health/MP are preserved proportionally.

**Evolution stat transformation model:**

```
new_current_stat = floor(new_base_stat + (new_base_stat * growth_per_level * (level - 1)))
```

**Evolution bonus:**
- Champion forms: **+20%** to primary offensive stat, **+15%** HP bonus.
- Ultimate forms: **+25%** primary stat, **+20%** HP bonus.

This creates a satisfying "evolution jump" reward.

### 4.6 Evolution Sequence Table

| Rookie | → | Champion | → | Ultimate |
|---|---|---|---|---|
| Emberling (Lv 10+, 5 wins) | → | Pyroclaw (Lv 25+, 15 wins, 1 boss) | → | Infernosaur |
| Aquapup (Lv 10+, 5 wins) | → | Tsunamut (Lv 25+, 15 wins, 1 boss) | → | Leviathore |
| Seedkit (Lv 10+, 5 wins) | → | Thornbloom (Lv 25+, 15 wins, 1 boss) | → | Verdant Titan |
| Stormwing (Lv 10+, 5 wins) | → | Voltalon (Lv 25+, 15 wins, 1 boss) | → | Thundergod |
| Rockbash (Lv 10+, 5 wins) | → | Mountainhide (Lv 25+, 15 wins, 1 boss) | → | Terraroc |
| Chaospuff (Lv 10+, 5 wins) | → | Wraithwing (Lv 25+, 15 wins, 1 boss) | → | Umbrathrax |

---

## 5. Battle System Rules

### 5.1 Turn Structure

The battle system uses a **speed-based turn queue**. At the start of each
battle round:

1. Each participant contributes an **initiative score**:

   ```
   initiative = creature.speed + random_uniform(0, 20)
   ```

2. Participants are sorted by initiative (highest first). They act in that
   order.
3. After all participants have acted once, the round ends and a new initiative
   roll happens for the next round.
4. Faster creatures act sooner within a round — they do not get multiple
   actions per round.

**Speed threshold bonus:** If one participant's `speed` is at least **2.5×**
the other's, it gains a **first-round priority bonus**: its initiative roll is
multiplied by 1.5 for the first round only.

**Speed tie:** If two combatants have the same initiative, the one with higher
`speed` stat acts first. If still tied, the player's creature acts first.

### 5.2 Action Options

When it is a creature's turn, the player (or AI) chooses **one** of:

1. **Attack** — Basic physical strike. Uses no MP.
2. **Skill** — Spend MP to use one of up to 4 learned skills.
3. **Item** — Use one consumable item from inventory.
4. **Switch** — Swap active creature to a benched creature (costs the turn).
5. **Flee** — Attempt to run from battle (wild encounters only).

### 5.3 Damage Formula

```
base_damage = (
    ( (2 * attacker_level) / 5 + 2 )
    * attack_power
    * ( attacker_stat / defender_stat )
    / 50
) + 2
```

Where:
- `attacker_level` = level of the attacking creature
- `attack_power` = the power of the move being used (range: 20–120)
- `attacker_stat` = attacker's Attack (physical moves) or MP-derived Magic stat
  (special/skill moves)
- `defender_stat` = defender's Defense (physical) or Defense × 0.85 (magic
  defense)

Multipliers applied:

```
final_damage = floor(
    base_damage
    * type_multiplier        # from the type-effectiveness table (§3)
    * random_multiplier       # uniform random 0.9 to 1.1 (±10% variance)
    * critical_multiplier     # 1.0 normally, 2.0 on critical hit
    * stab_multiplier         # 1.5 if move type matches creature type, else 1.0
    * status_multiplier       # 1.0 normally, reduced by certain statuses
)
```

`final_damage` is clamped to a **minimum of 1**.

### 5.4 Critical Hits

- Base critical hit chance: **6.25%** (1 in 16).
- Critical multiplier: **2.0×**.
- Some skills may increase crit chance by a flat additive modifier (e.g., +5%).

### 5.5 MP and Skill Usage

- Each skill has an **MP cost**.
- A skill cannot be used if current MP is less than the skill's cost.
- Each skill has a **power** value used in the damage formula.
- Skills are learned by level. Each species has a **skill learnset** of exactly
  4 skills, learned at fixed levels.
- **MP does not regenerate during battle.** It can only be restored via items or
  certain skills.

#### Example Skill Learnset — Emberling → Pyroclaw → Infernosaur (Fire line)

| Level Learned | Skill Name | Type | Power | MP Cost | Effect |
|---|---|---|---|---|---|
| 1 | Scorching Tackle | Physical (Fire) | 20 | 0 | Basic fire tackle |
| 6 | Ember Burst | Special (Fire) | 40 | 10 | Small fire AoE |
| 14 | Flame Lash | Special (Fire) | 65 | 18 | Strong fire strike, 10% burn chance |
| 24 | Inferno Crash | Special (Fire) | 90 | 30 | Massive fire hit, 20% burn chance |

Each of the 6 species lines has a distinct learnset of exactly 4 moves
distributed across levels 1–30.

### 5.6 Status Conditions

| Status | Effect |
|---|---|
| **Burn** | Takes 1/16 max HP damage at end of each round; Attack stat reduced 25% |
| **Freeze** | Cannot act; 25% chance to thaw each round |
| **Poison** | Takes 1/16 max HP damage at end of each round |
| **Paralysis** | 25% chance to skip action each turn; Speed reduced to 50% |
| **Sleep** | Cannot act for 2–4 rounds |
| **Confusion** | 33% chance to hit self with a power-20 attack each turn |
| **Atk↑ / Def↑** | Stat buff stacks up to +3 stages (each stage = +25%) |
| **Atk↓ / Def↓** | Stat debuff stacks down to -3 stages (each stage = -25%) |

Status effects are **cleared on battle end** and when switching creatures out.

### 5.7 Win/Loss Conditions

#### Win Conditions (Player)

- All enemy creatures reach 0 HP.

**Victory rewards:**
- XP awarded to all party members that participated.
- Gold awarded.
- Chance of item drop from wild enemies.

#### Loss Conditions (Player)

- The player's entire active party (all creatures in roster) reaches 0 HP.

**On loss:**
- Player is sent back to the nearest Trainer Camp / Heal Station.
- All fainted creatures are revived to 50% HP and 50% MP.
- Player loses 10% of their gold (rounded down, minimum 0).
- No XP penalty.

### 5.8 Flee Mechanics

- Flee is only available in **wild encounters** (not boss/rival/story battles).
- **Success chance:**

  ```
  flee_chance = min(
      0.90,
      0.40 + (player_creature_speed - enemy_creature_speed) * 0.01
  )
  ```

  Clamped to minimum **40%**, maximum **90%**.
- If flee fails, the enemy attacks for free.
- Each flee attempt costs the player's turn.

### 5.9 Items in Battle

| Item | Effect | Cost |
|---|---|---|
| Potion | Restore 50 HP | 100g |
| Super Potion | Restore 150 HP | 300g |
| Elixir | Restore 40 MP | 200g |
| Antidote | Cure Poison | 50g |
| Revive | Revive 1 fainted creature at 50% HP | 500g |
| Digi-Core | Capture device (consumable) | 300g |

Items are consumed on use. Using an item costs the creature's turn.

### 5.10 Battle AI

Simple but effective AI for enemy creatures:

1. If enemy HP < 25% and has a healing option, 40% chance to heal.
2. If a move type is super-effective against the player's active creature, 70%
   chance to use the best such move.
3. Otherwise, 60% chance to use the strongest available move, 30% chance to use
   a random move, 10% chance to use basic attack.
4. AI never uses items in wild encounters; boss/rival battles may use 1–2
   items.

---

## 6. Evolution / Progression Loop

### 6.1 Core Game Loop

```
[Explore World Map Zone]
        │
        ├── [Random Wild Encounter]
        │        ├── [Fight / Flee]
        │        ├── [Win → Gain XP + Gold + maybe item]
        │        └── [Faint → Return to camp, lose 10% gold]
        │
        ├── [Encounter Wild Creature → Weaken → Capture]
        │
        ├── [Find Trainer / Boss → Rival Battle]
        │
        └── [Visit Camp/Save Point → Heal all, save game]
                │
                └── [Check Evolution conditions → Maybe Evolve]
```

Macro loop:

```
Train (fight wild creatures)
  → Gain XP & Levels
  → Meet evolution thresholds
  → Evolve (battles + level)
  → Build stronger party
  → Beat zone boss
  → Unlock next zone
  → Repeat with higher-level wilds
```

### 6.2 Catching Wild Creatures

- A wild creature is **catchable** when:
  1. Its current HP is ≤ 20% of its max HP, **and**
  2. The player has an empty party slot or has a **Digi-Core** capture device.

- **Capture mechanic:** Use a Digi-Core item from the battle menu.
  - Base capture chance: **42%**
  - +15% if target is at 1 HP (≤5% max HP)
  - +5% if the target is paralyzed, asleep, or frozen

  ```
  capture_chance = 0.42
  if target_hp <= 0.05 * target_max_hp: capture_chance += 0.15
  if target_has_sleep_or_freeze_or_paralysis: capture_chance += 0.05
  capture_chance = min(capture_chance, 0.90)
  ```

- A captured creature starts at **Level 1** but retains its species.
- Rival/boss/story creatures **cannot** be captured.

### 6.3 Party & Box System

- **Party size**: Up to **6 creatures** in the active party.
- **Box**: Unlimited storage of captured-but-not-in-party creatures (accessible
  at camp/save points).
- Up to **3** creatures participate in a single battle (1 active + 2 on bench).

### 6.4 XP & Leveling

- XP is shared among all creatures that **participated** in a battle. Each
  participating creature receives **full XP** (no split).
- Benched (non-participating) creatures receive **50% XP** if a "Training
  Stone" item is active, else 0%.
- A creature cannot gain XP if it is at **max level (50)**.

### 6.5 Progression Milestones

| Milestone | Requirement | Unlocks |
|---|---|---|
| First Capture | Capture 1st creature | Full party management |
| First Evolution | Evolve 1st creature to Champion | Advanced skills; Zone 2 access |
| Zone 1 Boss | Beat Nature Warden boss | Zone 2 (Storm Peaks) unlocked |
| Champion Evolution | Evolve to Champion stage | Zone 3 (Abyssal Depths) unlocked |
| Zone 2 Boss | Beat Storm King boss | Zone 3 fast-travel |
| Ultimate Evolution | Evolve to Ultimate stage | Post-game content, Rival Master battles |
| Zone 3 Boss | Beat Abyssal Overlord | Final dungeon |
| Final Boss | Beat The Corruption | Ending; New Game+ hints |

---

## 7. XP Curve

### 7.1 Leveling Formula

The total XP required to reach **level L** (cumulative XP from level 1):

```
xp_total(L) = floor( 10 * (L - 1)^2.6 )
```

### 7.2 XP-to-Next-Level Table

| Level (L→L+1) | XP Needed | Level (L→L+1) | XP Needed |
|---|---|---|---|
| 1 → 2 | 10 | 26 → 27 | 1,023 |
| 2 → 3 | 21 | 27 → 28 | 1,090 |
| 3 → 4 | 37 | 28 → 29 | 1,159 |
| 4 → 5 | 57 | 29 → 30 | 1,230 |
| 5 → 6 | 79 | 30 → 31 | 1,303 |
| 6 → 7 | 103 | 31 → 32 | 1,378 |
| 7 → 8 | 130 | 32 → 33 | 1,455 |
| 8 → 9 | 159 | 33 → 34 | 1,534 |
| 9 → 10 | **190** ← Evo 1 | 34 → 35 | 1,615 |
| 10 → 11 | 223 | 35 → 36 | 1,698 |
| 11 → 12 | 258 | 36 → 37 | 1,783 |
| 12 → 13 | 295 | 37 → 38 | 1,870 |
| 13 → 14 | 334 | 38 → 39 | 1,959 |
| 14 → 15 | 375 | 39 → 40 | 2,050 |
| 15 → 16 | 418 | 40 → 41 | 2,143 |
| 16 → 17 | 463 | 41 → 42 | 2,238 |
| 17 → 18 | 510 | 42 → 43 | 2,335 |
| 18 → 19 | 559 | 43 → 44 | 2,434 |
| 19 → 20 | 610 | 44 → 45 | 2,535 |
| 20 → 21 | 663 | 45 → 46 | 2,638 |
| 21 → 22 | 718 | 46 → 47 | 2,743 |
| 22 → 23 | 775 | 47 → 48 | 2,850 |
| 23 → 24 | 834 | 48 → 49 | 2,959 |
| 24 → 25 | 895 | 49 → 50 | 3,070 |
| 25 → 26 | **958** ← Evo 2 | | |

**Total XP to reach Level 50: ~56,766 XP.**

### 7.3 Growth Pattern Characteristics

- **Shape**: Polynomial (exponent 2.6) — a "gentle cubic" curve.
- **Early game (L1–10)**: Fast leveling (10–190 XP per level).
- **Mid game (L10–25)**: Moderate curve — the "grind" zone.
- **Late game (L25–50)**: Steeper — rewards dedication.
- **Cap**: Level 50 hard cap.

### 7.4 XP Rewards from Battles

```
xp_earned = floor(
    base_xp_of_enemy
    * (enemy_level / player_level)
    * 1.2
)
```

- Rookie wild enemy base XP: **25**
- Champion wild enemy base XP: **45**
- Ultimate wild enemy base XP: **80**
- Rival/boss enemy award **2×** base XP.

---

## 8. Level-Up Stat Growth

### 8.1 Per-Stat Growth Formula

```
S(L) = floor( S_base * (1 + growth_rate * (L - 1)) )
```

Where:
- `S_base` = the base stat value (from the roster tables).
- `growth_rate` = species-specific modifier per stat (ranges 0.010 to 0.050).
- `L` = current level (1–50).

### 8.2 Growth Rate Table (per Species Family)

| Species Family | HP Growth | MP Growth | Atk Growth | Def Growth | Spd Growth | Profile |
|---|---|---|---|---|---|---|
| Emberling (Fire) | 0.030 | 0.020 | **0.045** | 0.020 | 0.025 | Glass cannon / physical attacker |
| Aquapup (Water) | 0.035 | 0.025 | 0.025 | **0.040** | 0.015 | Balanced tank/off-tank |
| Seedkit (Nature) | 0.025 | **0.040** | 0.025 | 0.030 | 0.015 | Magic sniper / support |
| Stormwing (Electric) | 0.015 | 0.030 | 0.030 | 0.015 | **0.045** | Speedy glass cannon |
| Rockbash (Earth) | **0.050** | 0.010 | 0.015 | **0.045** | 0.005 | Pure physical wall |
| Chaospuff (Dark) | 0.015 | **0.045** | 0.035 | 0.015 | 0.030 | Magic glass cannon |

### 8.3 Worked Example

**Emberling at Level 10** (just before Champion evolution):

```
HP  = floor(100 * (1 + 0.030 * 9)) = floor(100 * 1.27)   = 127
MP  = floor(40  * (1 + 0.020 * 9)) = floor(40 * 1.18)    = 47
Atk = floor(20  * (1 + 0.045 * 9)) = floor(20 * 1.405)   = 28
Def = floor(14  * (1 + 0.020 * 9)) = floor(14 * 1.18)    = 16
Spd = floor(16  * (1 + 0.025 * 9)) = floor(16 * 1.225)   = 19
```

**Pyroclaw (Champion) at Level 10** (with evolution bonus):

```
HP  = floor(180 * (1 + 0.030*9) * 1.15) = floor(180 * 1.27 * 1.15) = 262
MP  = floor(80  * (1 + 0.020*9))         = floor(80 * 1.18)        = 94
Atk = floor(45  * (1 + 0.045*9) * 1.20) = floor(45 * 1.405 * 1.20) = 75
Def = floor(32  * (1 + 0.020*9))         = floor(32 * 1.18)        = 37
Spd = floor(30  * (1 + 0.025*9))         = floor(30 * 1.225)       = 36
```

### 8.4 Per-Level-Up Display

On each level-up, the game displays:

```
Emberling grew to Level 7!
HP +3
MP +1
Attack +1
Defense +0
Speed +0
```

(Calculated from the discrete delta between `S(L-1)` and `S(L)`.)

---

## 9. Encounter Tables

### 9.1 World Zones Overview

| Zone # | Zone Name | Theme | Wild Level Range | Zone Boss |
|---|---|---|---|---|
| 1 | Verdant Plains | Grassy fields, low hills | 1–12 | Nature Warden (Verdant Titan, Lv 14) |
| 2 | Storm Peaks | Mountains, lightning storms | 15–28 | Storm King (Thundergod, Lv 28) |
| 3 | Abyssal Depths | Underwater caverns | 30–45 | Abyssal Overlord (Leviathore, Lv 45) |
| 4 | Throne of Corruption | Final dungeon | 46–50 | The Corruption (Lv 50, multi-phase) |

### 9.2 Zone 1: Verdant Plains

| Enemy Species | Encounter Weight | Level Range | Base XP |
|---|---|---|---|
| Emberling | 20% | 1–6 | 25 |
| Aquapup | 20% | 1–6 | 25 |
| Seedkit | 25% | 2–8 | 25 |
| Rockbash | 15% | 3–9 | 25 |
| Stormwing | 10% | 4–10 | 30 |
| Chaospuff | 10% | 5–12 | 35 |

**Encounter Rates:**
- Low grass: 15% chance per step, triggers every 30–50 steps
- Tall grass: 25% chance per step, triggers every 20–40 steps
- Water edge: 12% chance per step, triggers every 35–50 steps

**Gold reward per victory:** `8 + random(0, 12)` gold.

**Zone 1 Boss:**
- **Nature Warden** — a Verdant Titan at Lv 14.
- Uses 4 moves, gets 1 free healing item (heals 25% once at <50% HP).
- Reward: 500 XP to all, 200 gold, unlocks Zone 2 fast-travel.

### 9.3 Zone 2: Storm Peaks

| Enemy Species | Encounter Weight | Level Range | Base XP |
|---|---|---|---|
| Stormwing | 25% | 15–22 | 45 |
| Chaospuff | 20% | 16–24 | 45 |
| Rockbash | 20% | 17–25 | 45 |
| Emberling (Champion: Pyroclaw) | 10% | 18–26 | 55 |
| Aquapup (Champion: Tsunamut) | 10% | 20–27 | 55 |
| Seedkit (Champion: Thornbloom) | 10% | 20–28 | 55 |
| Voltalon (rare, Champion) | 5% | 20–28 | 75 |

**Encounter Rates:**
- Mountain path: 22% chance per step, triggers every 25–40 steps
- Lightning field (hazard area): 30% chance per step, triggers every 15–30 steps
- Cave interior: 18% chance per step, triggers every 30–45 steps

**Gold reward per victory:** `20 + random(0, 20)` gold.

**Zone 2 Boss:**
- **Storm King** — a Thundergod at Lv 28.
- Uses 4 moves, moves at increased speed, has 1 healing item.
- Reward: 1500 XP to all, 400 gold, unlocks Zone 3.

---

## 10. Scenes

The game requires the following scenes, managed by the scene system (see
[Architecture.md](Architecture.md) §3):

| # | Scene | Description |
|---|---|---|
| 1 | Title Screen | Game logo, "Press Start" prompt, ambient background |
| 2 | Character Creation | Text field for player name entry |
| 3 | Starter Selection | Choose 1 of 3 starters (Emberling / Aquapup / Seedkit) |
| 4 | World Map (Overworld) | Top-down tile-based map; movement, encounters, NPCs |
| 5 | Battle Scene | Turn-based battle with HP/MP bars, command menu, effects |
| 6 | Battle Transition | Quick screen-flash/vortex animation (~0.8s, skippable) |
| 7 | Party Menu | Grid/list of up to 6 party members with HP/MP bars |
| 8 | Creature Info Screen | Detailed view: stats, stage, level, XP bar, moves |
| 9 | Skill/Move Grid Screen | Lists learned moves; replace old moves on new learn |
| 10 | Items/Inventory Screen | List of all items with counts; use/discard |
| 11 | Digi-Core/Capture Screen | In-battle submenu for capture devices + consumables |
| 12 | Save/Camp Scene | Heal party, box management, save game |
| 13 | Evolution Scene | Full-screen animated evolution sequence |
| 14 | Game Over Screen | Fade to black, fainted message, return to camp |
| 15 | Victory/Post-Battle Screen | XP gained, level-ups, gold, item drops |
| 16 | Boss Fight Intro Screen | Dramatic boss reveal (~2s, skippable) |
| 17 | Zone Completion Screen | Zone-clear banner, unlocked fast-travel, next-zone teaser |
| 18 | Dialogue/Cutscene Overlay | Text box at bottom, NPC portrait, choices |
| 19 | Settings Screen | Volume sliders, text speed, fullscreen toggle |
| 20 | Credits Screen | Scrollable credits; return to title |

---

## 11. Related Documents

- [SRS.md](SRS.md) — Software requirements (functional/non-functional)
- [UserStories.md](UserStories.md) — Player stories per scene and milestone
- [Schema.md](Schema.md) — Data schemas for roster, encounters, saves
- [ER.md](ER.md) — Entity relationships
- [Architecture.md](Architecture.md) — Scene system and game loop
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
