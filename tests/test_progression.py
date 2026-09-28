"""Tests for the progression system (systems/progression.py)."""

import pytest

from systems.progression import (
    LEVEL_CAP,
    calculate_stat,
    calculate_stats_at_level,
    check_level_up,
    can_evolve,
    level_up,
    xp_to_reach_level,
    xp_for_next_level,
    xp_from_battle,
    stat_keys,
)
from data.digimon_data import get_digimon


class TestXPCurve:
    def test_level_1_requires_zero_xp(self):
        assert xp_to_reach_level(1) == 0

    def test_xp_increases_with_level(self):
        assert xp_to_reach_level(5) > xp_to_reach_level(4)

    def test_xp_for_next_level_positive(self):
        assert xp_for_next_level(1) > 0

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError):
            xp_to_reach_level(0)


class TestStatCalculation:
    def test_level_1_returns_base(self):
        d = get_digimon("emberling")
        assert calculate_stat(d.hp, d.hp_growth, 1) == d.hp

    def test_stats_increase_with_level(self):
        d = get_digimon("emberling")
        low = calculate_stats_at_level(d, 1)
        high = calculate_stats_at_level(d, 10)
        assert high["hp"] > low["hp"]
        assert high["attack"] > low["attack"]

    def test_stat_keys(self):
        keys = stat_keys()
        assert "hp" in keys
        assert "attack" in keys
        assert len(keys) == 5


class TestLevelUp:
    def test_level_up_increments_level(self):
        d = get_digimon("emberling")
        result = level_up(d, 1, 100)
        assert result["new_level"] == 2
        assert result["old_level"] == 1

    def test_level_up_stat_deltas_positive(self):
        d = get_digimon("emberling")
        result = level_up(d, 1, 100)
        for key in stat_keys():
            assert result["stat_deltas"][key] >= 0

    def test_level_cap(self):
        d = get_digimon("emberling")
        result = level_up(d, LEVEL_CAP, 999999)
        assert result["new_level"] == LEVEL_CAP


class TestCheckLevelUp:
    def test_can_level_with_enough_xp(self):
        can, new_level, _ = check_level_up(1, xp_to_reach_level(2) + 10)
        assert can is True
        assert new_level == 2

    def test_cannot_level_with_insufficient_xp(self):
        can, new_level, _ = check_level_up(1, 0)
        assert can is False
        assert new_level == 1

    def test_cannot_level_at_cap(self):
        can, new_level, _ = check_level_up(LEVEL_CAP, 999999)
        assert can is False
        assert new_level == LEVEL_CAP


class TestEvolution:
    def test_rookie_can_evolve_at_requirements(self):
        d = get_digimon("emberling")
        reqs = d.evolution_requirements
        can = can_evolve("emberling", reqs.get("level", 1), reqs.get("battles_won", 0))
        assert can is True

    def test_cannot_evolve_below_level_req(self):
        can = can_evolve("emberling", 1, 0)
        assert can is False

    def test_ultimate_cannot_evolve(self):
        inferno = get_digimon("infernosaur")
        if inferno.evolution_target is None:
            can = can_evolve("infernosaur", 99, 99, 99)
            assert can is False


class TestBattleXP:
    def test_xp_positive(self):
        xp = xp_from_battle(25, 3, 5)
        assert xp >= 1

    def test_boss_doubles_xp(self):
        normal = xp_from_battle(25, 3, 5, is_boss=False)
        boss = xp_from_battle(25, 3, 5, is_boss=True)
        assert boss == normal * 2
