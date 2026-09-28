"""Turn-based battle engine for digimon-rpg.

This module implements the core combat loop: turn ordering, damage
calculation with elemental type multipliers, move execution, enemy AI, fleeing,
battle-end detection, and XP/gold awards.

The system is partitioned into:

* :class:`BattleDigimon` — a per-battle wrapper around a species definition
  that tracks live HP/MP, buffs, and status.
* :class:`BattleResult` — the outcome summary returned at battle end.
* :class:`BattleEngine` — orchestrates rounds, turns, AI, and state queries.

Damage model follows the task spec:

    ``damage = (attacker_attack * move_power / defender_defense) * random_factor``

where ``random_factor ~ uniform(0.85, 1.15)`` and the result is then
multiplied by the elemental type multiplier from ``TYPE_CHART``.

WASM safety: this module uses only the stdlib ``random`` module plus the
project's own data/progression modules. No I/O, no threads, no subprocess.
Safe under pygbag/WASM.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from data.digimon_data import (
    Digimon,
    Move,
    TYPE_CHART,
    get_digimon,
    get_type_multiplier,
)
from systems.progression import calculate_stat, calculate_stats_at_level


# ---------------------------------------------------------------------------
# BattleDigimon
# ---------------------------------------------------------------------------

@dataclass
class BattleDigimon:
    """A live combatant in a battle.

    Wraps a :class:`Digimon` species at a concrete level, with mutable battle
    state (current HP/MP, defending flag, status effects).

    Attributes:
        species_name: Lowercase registry key of the species.
        level: Combat level.
        current_hp: Live HP during the battle.
        max_hp: Max HP derived from species + level.
        current_mp: Live MP during the battle.
        max_mp: Max MP derived from species + level.
        attack: Current ATK stat (from species + level, may be buffed later).
        defense: Current DEF stat.
        speed: Current SPD stat.
        moves: List of :class:`Move` instances available to this combatant.
        element: Element of the species.
        is_defending: ``True`` if the creature used a defend move last turn.
        status_effects: Active status-effect labels (e.g. ``"burn"``,
            ``"paralyze"``). Currently maintained for future hooks.
        nickname: Optional display name separate from the species name.
        base_xp: Base XP of the species (for award math).
    """

    species_name: str
    level: int
    current_hp: int = 0
    max_hp: int = 0
    current_mp: int = 0
    max_mp: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0
    moves: List[Move] = field(default_factory=list)
    element: str = "normal"
    is_defending: bool = False
    status_effects: List[str] = field(default_factory=list)
    nickname: str = ""
    base_xp: int = 25

    def __post_init__(self) -> None:
        """Compute derived stats from the species definition if level is set.

        The constructor computes max HP/MP and derived ATK/DEF/SPD when
        ``max_hp`` is still 0 (i.e. the caller did not supply explicit
        stat values), pulling the species from the registry.
        """
        try:
            digimon: Digimon = get_digimon(self.species_name)
        except KeyError:
            # Allow construction of a skeleton combatant without a registry
            # entry (e.g. for tutorials); caller must set stats manually.
            self.max_hp = self.max_hp or self.current_hp or 1
            self.max_mp = self.max_mp or self.current_mp or 0
            return

        stats = calculate_stats_at_level(digimon, self.level)

        self.max_hp = self.max_hp if self.max_hp > 0 else stats["hp"]
        self.max_mp = self.max_mp if self.max_mp > 0 else stats["mp"]
        self.attack = self.attack if self.attack > 0 else stats["attack"]
        self.defense = self.defense if self.defense > 0 else stats["defense"]
        self.speed = self.speed if self.speed > 0 else stats["speed"]

        if self.current_hp <= 0:
            self.current_hp = self.max_hp
        if self.current_mp <= 0:
            self.current_mp = self.max_mp

        if not self.moves:
            self.moves = [m for m in digimon.moves]
        if not self.element or self.element == "normal":
            self.element = digimon.element
        if not self.nickname:
            self.nickname = digimon.name

    @classmethod
    def from_species(
        cls,
        species_name: str,
        level: int,
        hp_override: Optional[int] = None,
        mp_override: Optional[int] = None,
        base_xp: Optional[int] = None,
    ) -> "BattleDigimon":
        """Construct a :class:`BattleDigimon` from a species name + level.

        A convenience factory that computes all derived stats from the
        species definition at the given level and returns a fully populated
        combatant.

        Args:
            species_name: Lowercase species key (e.g. ``"emberling"``).
            level: Combat level (>= 1).
            hp_override: Optional explicit HP value over the computed max.
            mp_override: Optional explicit MP value over the computed max.
            base_xp: Optional explicit base_xp (fallback to species default).

        Returns:
            A new :class:`BattleDigimon` at full HP/MP.
        """
        instance = cls(species_name=species_name, level=level)

        if hp_override is not None:
            instance.max_hp = hp_override
            instance.current_hp = hp_override
        if mp_override is not None:
            instance.max_mp = mp_override
            instance.current_mp = mp_override
        if base_xp is not None:
            instance.base_xp = base_xp

        return instance

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        """Apply damage to this creature and return actual HP lost.

        Args:
            amount: Damage amount (already rounded).

        Returns:
            The actual HP lost (may be less than ``amount`` if HP hits 0).
        """
        amount = max(0, int(amount))
        lost = min(self.current_hp, amount)
        self.current_hp -= lost
        return lost

    def heal(self, amount: int) -> int:
        """Restore HP up to max and return the amount restored.

        Args:
            amount: Raw heal amount.

        Returns:
            Actual HP restored (capped at max_hp).
        """
        amount = max(0, int(amount))
        before = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - before

    def spend_mp(self, cost: int) -> bool:
        """Deduct MP if available and return whether the cost was paid.

        Args:
            cost: MP cost (>= 0).

        Returns:
            ``True`` if MP was deducted, ``False`` if insufficient MP.
        """
        cost = max(0, int(cost))
        if self.current_mp < cost:
            return False
        self.current_mp -= cost
        return True

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def strongest_move(self) -> Optional[Move]:
        """Return the move with the highest power, if any.

        Returns:
            The strongest available move, or ``None`` if the combatant has
            no damaging moves.
        """
        candidates = [m for m in self.moves if m.move_type in ("attack", "special")]
        if not candidates:
            return None
        return max(candidates, key=lambda m: m.power)

    def heal_move(self) -> Optional[Move]:
        """Return the first heal-type move, if any.

        Returns:
            A heal move or ``None``.
        """
        for m in self.moves:
            if m.move_type == "heal":
                return m
        return None


# ---------------------------------------------------------------------------
# BattleResult
# ---------------------------------------------------------------------------

@dataclass
class BattleResult:
    """Summary of a completed battle.

    Attributes:
        winner: ``"player"``, ``"enemy"``, or ``"fled"``.
        xp_awarded: Total XP granted to the player (0 if not won).
        gold_awarded: Gold granted to the player (0 if not won).
        rounds: Number of full turns taken.
        log: Chronological list of human-readable event messages.
    """

    winner: str = "enemy"
    xp_awarded: int = 0
    gold_awarded: int = 0
    rounds: int = 0
    log: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# BattleEngine
# ---------------------------------------------------------------------------

class BattleEngine:
    """Orchestrates a single wild or boss battle between two combatants.

    The engine owns the round counter, turn order, live HP/MP, and the battle
    log. Call ``player_attack`` for the player's action and ``enemy_turn``
    for the AI response; query :meth:`check_battle_end` between actions.

    Attributes:
        player: The player's :class:`BattleDigimon`.
        enemy: The enemy's :class:`BattleDigimon`.
        rng: Seeded :class:`random.Random` (or module random when ``None``).
        is_wild: Whether this is a wild encounter (enables fleeing).
        is_boss: Whether the enemy is a boss (doubles XP award).
        round: Current round counter (starts at 1 on first action).
        log: List of event messages appended each action.
    """

    def __init__(
        self,
        player_digimon: BattleDigimon,
        enemy_digimon: BattleDigimon,
        rng: Optional[random.Random] = None,
        is_wild: bool = True,
        is_boss: bool = False,
    ) -> None:
        """Initialize a battle.

        Args:
            player_digimon: The player's combatant.
            enemy_digimon: The enemy combatant.
            rng: Optional seeded RNG for deterministic testing.
            is_wild: Whether this is a wild encounter (default ``True``).
            is_boss: Whether the enemy is a boss (default ``False``).
        """
        self.player: BattleDigimon = player_digimon
        self.enemy: BattleDigimon = enemy_digimon
        self.rng: random.Random = rng if rng is not None else random.Random()
        self.is_wild: bool = is_wild
        self.is_boss: bool = is_boss
        self.round: int = 1
        self.log: List[str] = []

        if not self.player.nickname:
            self.player.nickname = self.player.species_name.title()
        if not self.enemy.nickname:
            self.enemy.nickname = self.enemy.species_name.title()

        self._turn_order: List[str] = self.determine_turn_order()

    # ------------------------------------------------------------------
    # Turn ordering
    # ------------------------------------------------------------------

    def determine_turn_order(self) -> List[str]:
        """Compute the initiative order for the current round.

        Initiative = speed + random.uniform(0, 20). Higher initiative acts
        first; ties resolve to player first.

        Returns:
            A list ``["player", "enemy"]`` or ``["enemy", "player"]``.
        """
        player_init = self.player.speed + self.rng.uniform(0.0, 20.0)
        enemy_init = self.enemy.speed + self.rng.uniform(0.0, 20.0)

        if enemy_init > player_init:
            return ["enemy", "player"]
        return ["player", "enemy"]

    # ------------------------------------------------------------------
    # Damage calculation
    # ------------------------------------------------------------------

    def calculate_damage(
        self,
        attacker: BattleDigimon,
        defender: BattleDigimon,
        move: Move,
    ) -> int:
        """Compute damage from a move against a defender.

        Formula:
            ``raw = (attacker.attack * move.power / defender.defense)``
            ``damage = raw * random_factor``  (factor in [0.85, 1.15])
            ``damage *= type_multiplier``
            ``if defender.is_defending: damage *= 0.5``
            ``final = max(1, floor(damage))``

        Args:
            attacker: The combatant using the move.
            defender: The target combatant.
            move: The :class:`Move` being used.

        Returns:
            Final integer damage (always at least 1).
        """
        if defender.defense <= 0:
            defender_defense = 1  # Prevent zero-division.
        else:
            defender_defense = defender.defense

        raw: float = (attacker.attack * move.power) / defender_defense
        factor: float = self.rng.uniform(0.85, 1.15)
        damage: float = raw * factor

        # Type multiplier from the attacker's move element vs defender element.
        multiplier = get_type_multiplier(move.element, defender.element)
        damage *= multiplier

        # Defensive stance halves incoming damage.
        if defender.is_defending:
            damage *= 0.5

        # Minimum 1, floor the final amount.
        return max(1, int(damage))

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def execute_move(
        self,
        attacker: BattleDigimon,
        defender: BattleDigimon,
        move: Move,
    ) -> Dict[str, object]:
        """Execute a single move and return its outcome.

        Args:
            attacker: The creature using the move.
            defender: The target creature (for damaging moves).
            move: The move being executed.

        Returns:
            A dict with keys:

            * ``damage`` — HP lost by the defender (0 for heal/defend).
            * ``mp_cost`` — MP consumed (0 if insufficient / not enough).
            * ``effect`` — short effect tag (``"damage"``, ``"heal"``,
              ``"defend"``, ``"status"``, ``"failed"``).
            * ``message`` — Human-readable log message.
        """
        if move.move_type == "heal":
            # Heal moves cost MP and restore the *attacker's* HP.
            ok = attacker.spend_mp(move.mp_cost)
            if not ok:
                return {
                    "damage": 0,
                    "mp_cost": 0,
                    "effect": "failed",
                    "message": f"{attacker.nickname} lacks MP for {move.name}!",
                }
            healed = attacker.heal(move.power)
            return {
                "damage": 0,
                "mp_cost": move.mp_cost,
                "effect": "heal",
                "message": (
                    f"{attacker.nickname} healed {healed} HP with {move.name}!"
                ),
            }

        if move.move_type == "defend":
            attacker.is_defending = True
            return {
                "damage": 0,
                "mp_cost": move.mp_cost,
                "effect": "defend",
                "message": f"{attacker.nickname} braces and defends!",
            }

        # attack / special
        ok = attacker.spend_mp(move.mp_cost)
        if not ok:
            return {
                "damage": 0,
                "mp_cost": 0,
                "effect": "failed",
                "message": f"{attacker.nickname} lacks MP for {move.name}!",
            }

        if attacker.is_defending:
            attacker.is_defending = False  # Can't defend while attacking.

        damage = self.calculate_damage(attacker, defender, move)
        actual = defender.take_damage(damage)

        # Build a message that shows type effectiveness for flavour.
        mult = get_type_multiplier(move.element, defender.element)
        flavor = ""
        if mult > 1.0:
            flavor = "It's super effective!"
        elif mult < 1.0:
            flavor = "It's not very effective..."

        message_parts: List[str] = [
            f"{attacker.nickname} used {move.name}!",
            f"{defender.nickname} took {actual} damage.",
        ]
        if flavor:
            message_parts.append(flavor)

        return {
            "damage": actual,
            "mp_cost": move.mp_cost,
            "effect": "damage",
            "message": " ".join(message_parts),
        }

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def player_attack(self, move_index: int) -> Dict[str, object]:
        """Have the player use a move at the given index.

        Args:
            move_index: Index into the player's ``moves`` list.

        Returns:
            The outcome dict from :meth:`execute_move`, plus a ``"side"``
            marker.
        """
        if move_index < 0 or move_index >= len(self.player.moves):
            return {
                "damage": 0,
                "mp_cost": 0,
                "effect": "failed",
                "message": "Invalid move selection.",
            }

        move: Move = self.player.moves[move_index]
        result = self.execute_move(self.player, self.enemy, move)
        result["side"] = "player"
        self._track_round()
        self.log.append(str(result["message"]))
        return result

    def enemy_turn(self) -> Dict[str, object]:
        """Execute the enemy's AI turn.

        AI decisions (using ``self.rng``):

        * If enemy HP < 25% and a heal move exists, 40% chance to heal.
        * Otherwise 60% chance to use the strongest move.
        * 30% chance to pick a random move.
        * 10% chance to use the basic (first) attack.

        Returns:
            The outcome dict from :meth:`execute_move`, plus a ``"side"``
            marker set to ``"enemy"``.
        """
        # Check low-HP heal trigger first.
        heal_move = self.enemy.heal_move()
        hp_ratio = (
            self.enemy.current_hp / self.enemy.max_hp if self.enemy.max_hp else 0.0
        )
        if heal_move is not None and hp_ratio < 0.25:
            roll = self.rng.random()
            if roll < 0.40:
                result = self.execute_move(self.enemy, self.player, heal_move)
                result["side"] = "enemy"
                self._track_round()
                self.log.append(str(result["message"]))
                return result

        strong = self.enemy.strongest_move()
        if strong is None:
            # No damaging move — fall back to first move or a basic attack.
            chosen = self.enemy.moves[0] if self.enemy.moves else None
            if chosen is None:
                result = {
                    "damage": 0,
                    "mp_cost": 0,
                    "effect": "failed",
                    "message": f"{self.enemy.nickname} has no moves to use!",
                }
                result["side"] = "enemy"
                self._track_round()
                self.log.append(str(result["message"]))
                return result
            roll = self.rng.random()
            if roll < 0.60:
                chosen = strong
            elif roll < 0.90:
                chosen = self.rng.choice(self.enemy.moves)
            else:
                chosen = self.enemy.moves[0]

            result = self.execute_move(self.enemy, self.player, chosen)
        else:
            roll = self.rng.random()
            if roll < 0.60:
                chosen: Move = strong
            elif roll < 0.90:
                chosen = self.rng.choice(self.enemy.moves)
            else:
                chosen = self.enemy.moves[0]

            result = self.execute_move(self.enemy, self.player, chosen)

        result["side"] = "enemy"
        self._track_round()
        self.log.append(str(result["message"]))
        return result

    def attempt_flee(self) -> Dict[str, object]:
        """Attempt to flee a wild battle.

        Chance = clamp(0.40 + (player_speed - enemy_speed) * 0.01, 0.40, 0.90).
        Only valid for wild battles.

        Returns:
            A dict ``{"success": bool, "message": str}``.
        """
        if not self.is_wild:
            return {
                "success": False,
                "message": "You cannot flee from a boss battle!",
            }

        chance = 0.40 + (self.player.speed - self.enemy.speed) * 0.01
        chance = max(0.40, min(0.90, chance))

        roll = self.rng.random()
        if roll < chance:
            self._track_round()
            self.log.append(f"{self.player.nickname} successfully fled!")
            return {
                "success": True,
                "message": f"{self.player.nickname} fled the battle!",
            }

        self._track_round()
        self.log.append("Flee attempt failed!")
        return {
            "success": False,
            "message": "Unable to flee!",
        }

    # ------------------------------------------------------------------
    # State and end-of-battle
    # ------------------------------------------------------------------

    def check_battle_end(self) -> Optional[str]:
        """Return the winner if the battle has ended, else ``None``.

        Priority: if enemy HP <= 0 → ``"player"``. If player HP <= 0 →
        ``"enemy"``.

        Returns:
            ``"player"``, ``"enemy"``, or ``None`` if battle continues.
        """
        if self.enemy.current_hp <= 0:
            return "player"
        if self.player.current_hp <= 0:
            return "enemy"
        return None

    def get_battle_state(self) -> Dict[str, object]:
        """Return a snapshot of the current battle state.

        Returns:
            A dict containing player/enemy HP, MP, moves, element, level,
            turn order, and round number. Useful for UI rendering and
            serialization.
        """
        player_moves = [
            {"name": m.name, "power": m.power, "mp_cost": m.mp_cost}
            for m in self.player.moves
        ]
        enemy_moves = [
            {"name": m.name, "power": m.power, "mp_cost": m.mp_cost}
            for m in self.enemy.moves
        ]

        return {
            "player": {
                "name": self.player.nickname,
                "species": self.player.species_name,
                "level": self.player.level,
                "hp": self.player.current_hp,
                "max_hp": self.player.max_hp,
                "mp": self.player.current_mp,
                "max_mp": self.player.max_mp,
                "attack": self.player.attack,
                "defense": self.player.defense,
                "speed": self.player.speed,
                "element": self.player.element,
                "is_defending": self.player.is_defending,
                "moves": player_moves,
            },
            "enemy": {
                "name": self.enemy.nickname,
                "species": self.enemy.species_name,
                "level": self.enemy.level,
                "hp": self.enemy.current_hp,
                "max_hp": self.enemy.max_hp,
                "mp": self.enemy.current_mp,
                "max_mp": self.enemy.max_mp,
                "attack": self.enemy.attack,
                "defense": self.enemy.defense,
                "speed": self.enemy.speed,
                "element": self.enemy.element,
                "is_defending": self.enemy.is_defending,
                "moves": enemy_moves,
            },
            "turn_order": self._turn_order,
            "round": self.round,
            "is_wild": self.is_wild,
            "is_boss": self.is_boss,
            "log": list(self.log),
        }

    def award_xp(self) -> int:
        """Compute the XP awarded to the player for winning this battle.

        Uses the enemy's ``base_xp`` if greater than 0, else defaults to 25.
        Applies the standard formula then doubles for bosses.

        Returns:
            The integer XP amount to award.
        """
        enemy_base = self.enemy.base_xp if self.enemy.base_xp and self.enemy.base_xp > 0 else 25
        enemy_level = max(1, self.enemy.level)
        player_level = max(1, self.player.level)
        is_boss = self.is_boss

        raw = (enemy_base * (enemy_level / player_level) * 1.2)
        xp = int(raw)
        if is_boss:
            xp *= 2
        return max(1, xp)

    # ------------------------------------------------------------------
    # Round tracking
    # ------------------------------------------------------------------

    def _track_round(self) -> None:
        """Increment the round counter after both sides act.

        The round counter advances once after each **pair** of actions
        (player + enemy), or a single action if only one side acts
        (e.g. a solo flee attempt). This is a lightweight heuristic:
        for full two-action rounds, callers pass through both and we only
        increment on the second.
        """
        # Simple approach: each public action increments an internal counter
        # and we store "round" as actions-since-start; a more precise model
        # would track per-side turn counts. For gameplay purposes we expose
        # the count of actions taken so far as the "round".
        self.round += 1

    # ------------------------------------------------------------------
    # High-level battle result helper
    # ------------------------------------------------------------------

    def resolve(
        self,
        gold_awarded: int = 0,
        player_fled: bool = False,
    ) -> BattleResult:
        """Build a :class:`BattleResult` based on current state.

        Call after the battle is complete (winner determined or player fled).

        Args:
            gold_awarded: Gold for the player (set by caller).
            player_fled: Whether the player fled the battle.

        Returns:
            A fully-populated :class:`BattleResult`.
        """
        if player_fled:
            return BattleResult(
                winner="fled",
                xp_awarded=0,
                gold_awarded=0,
                rounds=self.round,
                log=list(self.log),
            )

        end_state = self.check_battle_end()
        if end_state == "player":
            return BattleResult(
                winner="player",
                xp_awarded=self.award_xp(),
                gold_awarded=max(0, int(gold_awarded)),
                rounds=self.round,
                log=list(self.log),
            )

        # Enemy won (or unknown -> default enemy).
        return BattleResult(
            winner="enemy",
            xp_awarded=0,
            gold_awarded=0,
            rounds=self.round,
            log=list(self.log),
        )
