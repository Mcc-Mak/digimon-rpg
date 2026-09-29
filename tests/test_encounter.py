"""Tests for the encounter system (systems/encounter.py)."""

import random

import pytest

from data.digimon_data import DIGIMON_REGISTRY
from systems.encounter import (
    ZONES,
    check_encounter,
    get_zone,
    roll_encounter,
    roll_gold,
)


class TestZones:
    def test_zones_exist(self):
        assert "verdant_plains" in ZONES
        assert "storm_peaks" in ZONES

    def test_get_zone(self):
        zone = get_zone("verdant_plains")
        assert zone.name == "Verdant Plains"

    def test_get_unknown_zone_raises(self):
        with pytest.raises(KeyError):
            get_zone("nonexistent")

    def test_zone_has_encounter_entries(self):
        for zone_id, zone in ZONES.items():
            assert len(zone.encounter_entries) > 0, f"{zone_id} has no entries"

    def test_all_encounter_species_exist_in_registry(self):
        for zone_id, zone in ZONES.items():
            for entry in zone.encounter_entries:
                assert entry.species_id in DIGIMON_REGISTRY, (
                    f"zone '{zone_id}' references unknown species '{entry.species_id}'"
                )


class TestRollEncounter:
    def test_returns_dict_with_required_keys(self):
        result = roll_encounter("verdant_plains", rng=random.Random(42))
        assert result is not None
        assert "species" in result
        assert "level" in result
        assert "base_xp" in result

    def test_species_in_zone_table(self):
        zone = ZONES["verdant_plains"]
        valid_species = {e.species_id for e in zone.encounter_entries}
        for _ in range(50):
            result = roll_encounter("verdant_plains", rng=random.Random())
            assert result["species"] in valid_species

    def test_level_in_range(self):
        zone = ZONES["verdant_plains"]
        for _ in range(50):
            result = roll_encounter("verdant_plains", rng=random.Random())
            entry = next(
                e for e in zone.encounter_entries if e.species_id == result["species"]
            )
            assert entry.min_level <= result["level"] <= entry.max_level

    def test_unknown_zone_raises(self):
        with pytest.raises(KeyError):
            roll_encounter("nonexistent")


class TestCheckEncounter:
    def test_terrain_not_in_zone_raises(self):
        with pytest.raises(KeyError):
            check_encounter("verdant_plains", "nonexistent_terrain")

    def test_no_encounter_with_high_rng(self):
        rng = random.Random()
        rng.random = lambda: 0.99
        result = check_encounter("verdant_plains", "tall_grass", rng=rng)
        assert result is None

    def test_encounter_with_low_rng(self):
        rng = random.Random()
        rng.random = lambda: 0.01
        result = check_encounter("verdant_plains", "tall_grass", rng=rng)
        assert result is not None

    def test_unknown_zone_raises(self):
        with pytest.raises(KeyError):
            check_encounter("nonexistent", "tall_grass")


class TestRollGold:
    def test_gold_in_range(self):
        zone = ZONES["verdant_plains"]
        for _ in range(50):
            gold = roll_gold("verdant_plains", rng=random.Random())
            assert zone.gold_min <= gold <= zone.gold_max

    def test_unknown_zone_raises(self):
        with pytest.raises(KeyError):
            roll_gold("nonexistent")
