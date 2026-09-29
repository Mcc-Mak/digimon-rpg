"""Tests for the creature sprite factory (core/sprite_factory.py).

Tests monkeypatch ``_load_png_sprite`` to return synthetic surfaces so they
are deterministic regardless of whether SDL2_image / PNG support is available
on the host.
"""

import pygame

from data.digimon_data import DIGIMON_REGISTRY, get_digimon
from core import sprite_factory


def _make_fake_png(species) -> pygame.Surface:
    """Return a small synthetic surface that varies by stage size."""
    from core.sprite_factory import _STAGE_NUM
    stage_num = _STAGE_NUM.get(species.stage, 1)
    size = 40 + stage_num * 10
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((100, 150, 200))
    pygame.draw.circle(surf, (255, 0, 0), (size // 2, size // 2), size // 3)
    pygame.draw.rect(surf, (0, 255, 0), (size // 2 + 3, size // 2 - 3, 8, 5))
    return surf


def setup_module(module):
    pygame.init()
    original = sprite_factory._load_png_sprite
    def _fake(species):
        return _make_fake_png(species)
    sprite_factory._load_png_sprite = _fake


def teardown_module(module):
    pygame.quit()


class TestSpriteGeneration:
    def test_all_species_render_non_blank_sprite(self):
        sprite_factory.clear_cache()
        for key in DIGIMON_REGISTRY:
            surf = sprite_factory.get_sprite(key)
            drawn = any(
                surf.get_at((x, y))[3] != 0
                for x in range(0, surf.get_width(), 4)
                for y in range(0, surf.get_height(), 4)
            )
            assert drawn, f"species '{key}' renders a blank sprite"

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

    def test_sprite_is_not_blank(self):
        sprite_factory.clear_cache()
        surf = sprite_factory.get_sprite("aquapup")
        drawn = any(
            surf.get_at((x, y))[3] != 0
            for x in range(0, surf.get_width(), 4)
            for y in range(0, surf.get_height(), 4)
        )
        assert drawn, "sprite appears to be blank"

    def test_unknown_species_returns_error_placeholder(self):
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
        assert right is not base
        assert right.get_size() == base.get_size()

    def test_battle_sprite_left_is_flipped(self):
        sprite_factory.clear_cache()
        right = sprite_factory.get_battle_sprite("seedkit", facing="right")
        left = sprite_factory.get_battle_sprite("seedkit", facing="left")
        assert right.get_size() == left.get_size()
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
