"""Tests for the save system (systems/save_system.py)."""

import pytest

from systems.save_system import SaveData, PartyMemberData


class TestPartyMemberData:
    def test_to_dict_roundtrip(self):
        member = PartyMemberData(
            species_id="emberling",
            nickname="Ember",
            level=5,
            stage="Rookie",
            xp=120,
            current_hp=45,
            current_mp=20,
            battles_won=3,
            learned_moves=["Tackle", "Fireball"],
        )
        d = member.to_dict()
        assert d["species_id"] == "emberling"
        assert d["level"] == 5
        assert "Tackle" in d["learned_moves"]

        restored = PartyMemberData.from_dict(d)
        assert restored.species_id == "emberling"
        assert restored.level == 5
        assert restored.learned_moves == ["Tackle", "Fireball"]


class TestSaveData:
    def test_default_save_data(self):
        save = SaveData()
        assert save.player_name == "Player"
        assert save.gold == 0
        assert len(save.party) == 0
        assert save.player_position == (0, 0)
        assert save.current_zone == "verdant_plains"

    def test_to_dict_and_from_dict(self):
        save = SaveData(
            player_name="Tai",
            gold=150,
            party=[
                PartyMemberData(
                    species_id="emberling",
                    nickname="Ember",
                    level=7,
                    stage="Rookie",
                    xp=200,
                    current_hp=50,
                    current_mp=25,
                    battles_won=5,
                )
            ],
            player_position=(10, 5),
            current_zone="storm_peaks",
            defeated_encounters=8,
            game_flags={"boss_defeated": True},
        )
        d = save.to_dict()
        assert d["player_name"] == "Tai"
        assert d["gold"] == 150
        assert len(d["party"]) == 1
        assert d["player_position"]["x"] == 10
        assert d["current_zone"] == "storm_peaks"

        restored = SaveData.from_dict(d)
        assert restored.player_name == "Tai"
        assert restored.gold == 150
        assert len(restored.party) == 1
        assert restored.party[0].species_id == "emberling"
        assert restored.player_position == (10, 5)
        assert restored.current_zone == "storm_peaks"
        assert restored.defeated_encounters == 8
        assert restored.game_flags.get("boss_defeated") is True

    def test_empty_party_serialization(self):
        save = SaveData()
        d = save.to_dict()
        restored = SaveData.from_dict(d)
        assert len(restored.party) == 0

    def test_flags_roundtrip(self):
        save = SaveData(game_flags={"encountered_boss": True, "tutorial_done": False})
        d = save.to_dict()
        restored = SaveData.from_dict(d)
        assert restored.game_flags["encountered_boss"] is True
        assert restored.game_flags["tutorial_done"] is False
