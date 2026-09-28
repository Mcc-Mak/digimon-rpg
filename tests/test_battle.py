"""Tests for the battle engine (systems/battle.py)."""

import random

import pytest

from systems.battle import BattleEngine, BattleDigimon, BattleResult
from data.digimon_data import get_digimon


class TestBattleDigimon:
    def test_from_species_populates_stats(self):
        bd = BattleDigimon.from_species("emberling", 5)
        assert bd.max_hp > 0
        assert bd.current_hp == bd.max_hp
        assert bd.current_mp == bd.max_mp
        assert len(bd.moves) > 0
        assert bd.nickname == "Emberling"

    def test_take_damage(self):
        bd = BattleDigimon.from_species("emberling", 1)
        lost = bd.take_damage(10)
        assert lost == 10
        assert bd.current_hp == bd.max_hp - 10

    def test_take_damage_capped(self):
        bd = BattleDigimon.from_species("emberling", 1)
        lost = bd.take_damage(99999)
        assert lost == bd.max_hp
        assert bd.current_hp == 0

    def test_heal(self):
        bd = BattleDigimon.from_species("emberling", 1)
        bd.take_damage(20)
        healed = bd.heal(10)
        assert healed == 10
        assert bd.current_hp == bd.max_hp - 10

    def test_heal_capped(self):
        bd = BattleDigimon.from_species("emberling", 1)
        healed = bd.heal(99999)
        assert healed == 0

    def test_spend_mp_success(self):
        bd = BattleDigimon.from_species("emberling", 10)
        initial = bd.current_mp
        assert bd.spend_mp(5) is True
        assert bd.current_mp == initial - 5

    def test_spend_mp_insufficient(self):
        bd = BattleDigimon.from_species("emberling", 1)
        bd.current_mp = 2
        assert bd.spend_mp(5) is False
        assert bd.current_mp == 2


class TestBattleEngine:
    def _make_engine(self, p_level=5, e_level=3):
        player = BattleDigimon.from_species("emberling", p_level)
        enemy = BattleDigimon.from_species("aquapup", e_level)
        rng = random.Random(42)
        return BattleEngine(player, enemy, rng=rng)

    def test_turn_order_returns_two_sides(self):
        engine = self._make_engine()
        order = engine._turn_order
        assert set(order) == {"player", "enemy"}
        assert len(order) == 2

    def test_calculate_damage_minimum_one(self):
        engine = self._make_engine()
        move = engine.player.moves[0]
        damage = engine.calculate_damage(engine.player, engine.enemy, move)
        assert damage >= 1

    def test_player_attack_reduces_enemy_hp(self):
        engine = self._make_engine()
        enemy_hp_before = engine.enemy.current_hp
        engine.player_attack(0)
        assert engine.enemy.current_hp <= enemy_hp_before

    def test_check_battle_end_player_wins(self):
        engine = self._make_engine()
        engine.enemy.current_hp = 0
        assert engine.check_battle_end() == "player"

    def test_check_battle_end_enemy_wins(self):
        engine = self._make_engine()
        engine.player.current_hp = 0
        assert engine.check_battle_end() == "enemy"

    def test_check_battle_end_ongoing(self):
        engine = self._make_engine()
        assert engine.check_battle_end() is None

    def test_award_xp_positive(self):
        engine = self._make_engine()
        xp = engine.award_xp()
        assert xp >= 1

    def test_award_xp_boss_doubles(self):
        player = BattleDigimon.from_species("emberling", 5)
        enemy = BattleDigimon.from_species("aquapup", 3)
        normal = BattleEngine(player, enemy, rng=random.Random(42), is_boss=False)
        boss = BattleEngine(player, enemy, rng=random.Random(42), is_boss=True)
        assert boss.award_xp() == normal.award_xp() * 2

    def test_flee_wild_battle(self):
        player = BattleDigimon.from_species("emberling", 20)
        enemy = BattleDigimon.from_species("aquapup", 1)
        engine = BattleEngine(player, enemy, rng=random.Random(1), is_wild=True)
        result = engine.attempt_flee()
        assert "success" in result

    def test_flee_boss_fails(self):
        player = BattleDigimon.from_species("emberling", 5)
        enemy = BattleDigimon.from_species("aquapup", 3)
        engine = BattleEngine(player, enemy, is_wild=False, is_boss=True)
        result = engine.attempt_flee()
        assert result["success"] is False

    def test_resolve_player_win(self):
        engine = self._make_engine()
        engine.enemy.current_hp = 0
        result = engine.resolve()
        assert result.winner == "player"
        assert result.xp_awarded >= 1

    def test_resolve_enemy_win(self):
        engine = self._make_engine()
        engine.player.current_hp = 0
        result = engine.resolve()
        assert result.winner == "enemy"
        assert result.xp_awarded == 0

    def test_resolve_fled(self):
        engine = self._make_engine()
        result = engine.resolve(player_fled=True)
        assert result.winner == "fled"
        assert result.xp_awarded == 0

    def test_get_battle_state(self):
        engine = self._make_engine()
        state = engine.get_battle_state()
        assert "player" in state
        assert "enemy" in state
        assert "turn_order" in state
        assert "round" in state
