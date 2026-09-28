"""Progression system: leveling, XP math, and evolution rules.

This module encapsulates all numeric growth logic for digimon-rpg:

* XP curves — how much XP is required to reach each level.
* Stat-at-level calculation via the linear growth model
  ``S(L) = floor(S_base * (1 + growth_rate * (L - 1)))``.
* Level-up application that recalculates a creature's stats and reports the
  stat deltas.
* Evolution eligibility checks driven by ``Digimon.evolution_requirements``.
* Battle XP award math (shared with ``systems.battle``).

All functions are pure, deterministic, and side-effect free wherever RNG is
not required — making the module trivially unit-testable.

WASM safety: this module performs no I/O, no subprocess calls, and uses only
the stdlib ``math`` module. Safe under pygbag/WASM.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from data.digimon_data import Digimon, get_digimon

#: Maximum level a creature can reach.
LEVEL_CAP: int = 50

#: Stats that are tracked in per-level stat blocks.
_STAT_KEYS: Tuple[str, ...] = ("hp", "mp", "attack", "defense", "speed")


# ---------------------------------------------------------------------------
# XP curve
# ---------------------------------------------------------------------------

def xp_to_reach_level(level: int) -> int:
    """Compute the total cumulative XP needed to reach ``level`` from level 1.

    Implements the formula ``int(10 * (level - 1) ** 2.6)``.

    Args:
        level: The target level (>= 1). Level 1 returns 0.

    Returns:
        Total XP needed to reach that level.

    Raises:
        ValueError: If ``level`` is less than 1.
    """
    if level < 1:
        raise ValueError(f"Level must be >= 1, got {level}")
    return int(10 * (level - 1) ** 2.6)


def xp_for_next_level(current_level: int) -> int:
    """Return the delta XP needed to advance from ``current_level`` to the next.

    Args:
        current_level: The current level (>= 1).

    Returns:
        The number of additional XP required to reach
        ``current_level + 1``.
    """
    return xp_to_reach_level(current_level + 1) - xp_to_reach_level(current_level)


# ---------------------------------------------------------------------------
# Stat math
# ---------------------------------------------------------------------------

def calculate_stat(base: int, growth_rate: float, level: int) -> int:
    """Compute a single stat value at a given level.

    Implements the formula:
        ``S(L) = floor(S_base * (1 + growth_rate * (L - 1)))``

    Args:
        base: The base stat value at level 1.
        growth_rate: Fractional growth per level (e.g. ``0.03`` = 3%).
        level: The level to compute the stat for (>= 1).

    Returns:
        The computed stat, floored to an integer.
    """
    level = max(1, int(level))
    return int(base * (1 + growth_rate * (level - 1)))


def calculate_stats_at_level(digimon: Digimon, level: int) -> Dict[str, int]:
    """Compute the full six-stat block for a species at a given level.

    Args:
        digimon: The :class:`Digimon` species definition containing base stats
            and growth rates.
        level: The level to compute stats for (>= 1).

    Returns:
        Dict with keys ``"hp"``, ``"mp"``, ``"attack"``, ``"defense"``,
        and ``"speed"``.
    """
    return {
        "hp": calculate_stat(digimon.hp, digimon.hp_growth, level),
        "mp": calculate_stat(digimon.mp, digimon.mp_growth, level),
        "attack": calculate_stat(digimon.attack, digimon.atk_growth, level),
        "defense": calculate_stat(digimon.defense, digimon.def_growth, level),
        "speed": calculate_stat(digimon.speed, digimon.spd_growth, level),
    }


# ---------------------------------------------------------------------------
# Level up
# ---------------------------------------------------------------------------

def level_up(
    digimon: Digimon,
    current_level: int,
    current_xp: int,
) -> Dict[str, object]:
    """Apply one level-up to a Digimon, computing old/new stats and deltas.

    This is a *calculation helper*: it does not mutate any persistent game
    state (saves / party). The caller is responsible for actually updating
    the saved creature's level and stats.

    Args:
        digimon: The :class:`Digimon` species definition.
        current_level: The creature's level before the level-up.
        current_xp: The creature's current total XP.

    Returns:
        Dict with the following keys:

        * ``old_level`` — the level before the level-up.
        * ``new_level`` — the level after applying one level-up (capped at
          :data:`LEVEL_CAP`).
        * ``old_stats`` — dict of stats at ``current_level``.
        * ``new_stats`` — dict of stats at the new level.
        * ``stat_deltas`` — dict of per-stat increases.
        * ``remaining_xp`` — XP left after the level's cost is deducted.
    """
    new_level = min(current_level + 1, LEVEL_CAP)

    old_stats = calculate_stats_at_level(digimon, current_level)
    new_stats = calculate_stats_at_level(digimon, new_level)

    deltas: Dict[str, int] = {}
    for key in _STAT_KEYS:
        deltas[key] = new_stats[key] - old_stats[key]

    # Deduct the cost to reach the new level and keep whatever XP remains.
    cost = xp_to_reach_level(new_level) - xp_to_reach_level(current_level)
    remaining_xp = max(0, current_xp - cost) if new_level > current_level else current_xp

    return {
        "old_level": current_level,
        "new_level": new_level,
        "old_stats": old_stats,
        "new_stats": new_stats,
        "stat_deltas": deltas,
        "remaining_xp": remaining_xp,
    }


def check_level_up(current_level: int, current_xp: int) -> Tuple[bool, int, int]:
    """Check whether a creature can level up, and compute the new state.

    A creature gains a level when its total XP meets the threshold for
    ``current_level + 1`` and it is below the :data:`LEVEL_CAP`.

    Args:
        current_level: The creature's current level (>= 1).
        current_xp: The creature's current accumulated total XP.

    Returns:
        A tuple ``(can_level_up, new_level, remaining_xp)``:

        * ``can_level_up`` — ``True`` if a level-up should occur.
        * ``new_level`` — the resulting level after applying the level-up
          (equal to ``current_level`` if no level-up occurs).
        * ``remaining_xp`` — the XP that remains after the level cost is
          deducted (unchanged if no level-up).
    """
    if current_level >= LEVEL_CAP:
        return False, current_level, current_xp

    next_threshold = xp_to_reach_level(current_level + 1)
    if current_xp < next_threshold:
        return False, current_level, current_xp

    remaining = current_xp - (next_threshold - xp_to_reach_level(current_level))
    return True, current_level + 1, remaining


# ---------------------------------------------------------------------------
# Evolution
# ---------------------------------------------------------------------------

def can_evolve(
    creature_name: str,
    level: int,
    battles_won: int,
    boss_defeats: int = 0,
) -> bool:
    """Check whether a creature meets its evolution requirements.

    Evolution requirements are read from the species definition's
    ``evolution_requirements`` dict. If a creature has ``evolution_target``
    set to ``None`` (Ultimate tier), it cannot evolve.

    Args:
        creature_name: Name of the creature (case-insensitive).
        level: The creature's current level.
        battles_won: Total battles the creature has won.
        boss_defeats: Total boss encounters the creature has defeated
            (default 0).

    Returns:
        ``True`` if all requirement thresholds are met, otherwise ``False``.

    Raises:
        KeyError: If ``creature_name`` is not in the registry.
    """
    digimon: Digimon = get_digimon(creature_name)

    if digimon.evolution_target is None:
        return False

    reqs = digimon.evolution_requirements
    if not reqs:
        # Requirement dict exists but is empty — not evolvable.
        return False

    if "level" in reqs and level < reqs["level"]:
        return False
    if "battles_won" in reqs and battles_won < reqs["battles_won"]:
        return False
    if "boss_defeats" in reqs and boss_defeats < reqs["boss_defeats"]:
        return False

    return True


# ---------------------------------------------------------------------------
# Battle XP
# ---------------------------------------------------------------------------

def xp_from_battle(
    enemy_base_xp: int,
    enemy_level: int,
    player_level: int,
    is_boss: bool = False,
) -> int:
    """Compute the XP awarded for defeating an enemy.

    Formula: ``floor(base_xp * (enemy_level / player_level) * 1.2)``.
    If ``is_boss`` is ``True``, the result is doubled.

    Args:
        enemy_base_xp: Base XP value of the enemy species.
        enemy_level: Level of the defeated enemy.
        player_level: Level of the victorious player creature.
        is_boss: Whether the enemy was a boss (gives double XP).

    Returns:
        The integer XP awarded (never negative; minimum 1).
    """
    if player_level < 1:
        player_level = 1
    if enemy_level < 1:
        enemy_level = 1
    if enemy_base_xp < 0:
        enemy_base_xp = 0

    base = math.floor(enemy_base_xp * (enemy_level / player_level) * 1.2)
    if is_boss:
        base *= 2
    return max(1, base)


# ---------------------------------------------------------------------------
# Helper: universal stat-name list
# ---------------------------------------------------------------------------

def stat_keys() -> Tuple[str, ...]:
    """Return the canonical order of tracked stat names.

    This is exposed so other modules (battle, save, UI) can iterate stats
    in a stable order without hardcoding string literals.

    Returns:
        A tuple ``("hp", "mp", "attack", "defense", "speed")``.
    """
    return _STAT_KEYS
