"""Tests for the procedural creature sprite factory (core/sprite_factory.py)."""

import pygame

from data.digimon_data import DIGIMON_REGISTRY
from core import sprite_factory


def setup_module(module):
    """pygame.draw needs pygame to be initialized before use."""
    pygame.init()


def teardown_module(module):
    pygame.quit()


class TestSpriteGeneration:
    def test_all_species_have_dedicated_drawer(self):
        # Every registered species should map to a dedicated draw function
        # (no silent fallback to the generic blob).
        for key in DIGIMON_REGISTRY:
            assert key in sprite_factory._DRAWERS, (
                f"species '{key}' has no dedicated drawer"
            )

    def test_get_sprite_returns_surface_for_every_species(self):
        sprite_factory.clear_cache()
        for key in DIGIMON_REGISTRY:
            surf = sprite_factory.get_sprite(key)
            assert isinstance(surf, pygame.Surface)
            assert surf.get_size()[0] > 0
            assert surf.get_size()[1] > 0

    def test_sprite_size_scales_with_stage(self):
        sprite_factory.clear_cache()
        rookie = sprite_factory.get_sprite("emberling").get_size()[0]
        champion = sprite_factory.get_sprite("pyroclaw").get_size()[0]
        ultimate = sprite_factory.get_sprite("infernosaur").get_size()[0]
        assert rookie < champion < ultimate

    def test_sprite_has_transparent_background(self):
        sprite_factory.clear_cache()
        surf = sprite_factory.get_sprite("emberling")
        assert surf.get_flags() & pygame.SRCALPHA
        # Corner pixel should be fully transparent (nothing drawn there).
        assert surf.get_at((0, 0))[3] == 0

    def test_sprite_is_not_blank(self):
        sprite_factory.clear_cache()
        surf = sprite_factory.get_sprite("aquapup")
        # At least one non-transparent pixel must have been drawn.
        drawn = any(
            surf.get_at((x, y))[3] != 0
            for x in range(0, surf.get_width(), 4)
            for y in range(0, surf.get_height(), 4)
        )
        assert drawn, "sprite appears to be blank"

    def test_unknown_species_returns_generic_blob(self):
        sprite_factory.clear_cache()
        surf = sprite_factory.get_sprite("does-not-exist")
        assert isinstance(surf, pygame.Surface)
        drawn = any(
            surf.get_at((x, y))[3] != 0
            for x in range(0, surf.get_width(), 4)
            for y in range(0, surf.get_height(), 4)
        )
        assert drawn


class TestCachingAndFacing:
    def test_get_sprite_caches(self):
        sprite_factory.clear_cache()
        a = sprite_factory.get_sprite("stormwing")
        b = sprite_factory.get_sprite("stormwing")
        assert a is b

    def test_battle_sprite_right_equals_base_copy(self):
        sprite_factory.clear_cache()
        base = sprite_factory.get_sprite("rockbash")
        right = sprite_factory.get_battle_sprite("rockbash", facing="right")
        # Right-facing battle sprite is a distinct object but same pixels.
        assert right is not base
        assert right.get_size() == base.get_size()

    def test_battle_sprite_left_is_flipped(self):
        sprite_factory.clear_cache()
        right = sprite_factory.get_battle_sprite("seedkit", facing="right")
        left = sprite_factory.get_battle_sprite("seedkit", facing="left")
        assert right.get_size() == left.get_size()
        # A horizontally flipped sprite is not pixel-identical to the original
        # (the creature is asymmetric: eyes/snout on one side).
        same = all(
            right.get_at((x, y)) == left.get_at((x, y))
            for x in range(0, right.get_width(), 3)
            for y in range(0, right.get_height(), 3)
        )
        assert not same, "left-facing sprite was not flipped"

    def test_battle_sprite_caches_per_facing(self):
        sprite_factory.clear_cache()
        a = sprite_factory.get_battle_sprite("voltalon", facing="left")
        b = sprite_factory.get_battle_sprite("voltalon", facing="left")
        assert a is b

    def test_world_sprite_is_scaled(self):
        sprite_factory.clear_cache()
        sprite = sprite_factory.get_world_sprite("emberling", size=30)
        assert sprite.get_size() == (30, 30)

    def test_world_sprite_facing_left(self):
        sprite_factory.clear_cache()
        sprite = sprite_factory.get_world_sprite("emberling", size=24, facing="left")
        assert sprite.get_size() == (24, 24)
