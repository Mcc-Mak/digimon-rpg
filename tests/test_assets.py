"""Tests for the asset loader (core/assets.py) and the baked sprite PNGs.

These complement ``tests/test_sprites.py``, which exercises the rendering
surface via ``core.sprite_factory``. What is covered here is the file-backed
half of the pipeline: path resolution, the missing-asset contract, and the
agreement between the committed PNGs and the species registry.
"""

import os

import pygame
import pytest

from core.assets import SPRITE_DIR, AssetLoader
from data.digimon_data import DIGIMON_REGISTRY


def setup_module(module):
    """pygame.image.load needs pygame initialized before use."""
    pygame.init()


def teardown_module(module):
    pygame.quit()


@pytest.fixture(autouse=True)
def _clean_cache():
    """Isolate each test from the shared class-level caches."""
    AssetLoader.clear_cache()
    yield
    AssetLoader.clear_cache()


class TestPathResolution:
    def test_resolve_finds_a_baked_sprite(self):
        path = AssetLoader.resolve(f"{SPRITE_DIR}/emberling_1.png")
        assert path is not None
        assert os.path.isfile(path)

    def test_resolve_returns_none_for_unknown_asset(self):
        assert AssetLoader.resolve(f"{SPRITE_DIR}/definitely-not-a-species.png") is None

    def test_resolve_is_independent_of_cwd(self, tmp_path, monkeypatch):
        # Asset paths are resolved relative to the script, not the process
        # working directory, because the WASM bundle is served from a
        # different directory than the app code.
        monkeypatch.chdir(tmp_path)
        assert AssetLoader.resolve(f"{SPRITE_DIR}/emberling_1.png") is not None


class TestSpriteLoading:
    def test_every_species_has_a_baked_png(self):
        missing = [k for k, d in DIGIMON_REGISTRY.items() if not AssetLoader.has_sprite(d.sprite_key)]
        assert not missing, f"no baked sprite for: {missing}"

    def test_sprite_loads_with_alpha(self):
        surface = AssetLoader.sprite("emberling_1")
        assert isinstance(surface, pygame.Surface)
        assert surface.get_flags() & pygame.SRCALPHA

    def test_sprite_accepts_extension_and_case(self):
        plain = AssetLoader.sprite("emberling_1")
        assert AssetLoader.sprite("emberling_1.png") is plain
        assert AssetLoader.sprite("EMBERLING_1") is plain

    def test_sprite_is_cached(self):
        assert AssetLoader.sprite("seedkit_1") is AssetLoader.sprite("seedkit_1")

    def test_baked_png_loads_successfully(self):
        # The baked PNGs have their own natural dimensions (not the
        # procedural canvas sizes); just verify they load with alpha.
        surface = AssetLoader.sprite("emberling_1")
        assert isinstance(surface, pygame.Surface)
        assert surface.get_size()[0] > 0
        assert surface.get_size()[1] > 0

    def test_missing_sprite_returns_none(self):
        # A missing asset must degrade to the procedural fallback rather than
        # raise (doc/Architecture.md error-handling policy).
        assert AssetLoader.sprite("no_such_species_9") is None

    def test_missing_sprite_is_remembered(self):
        assert AssetLoader.sprite("no_such_species_9") is None
        assert "no_such_species_9" in AssetLoader._missing
        # Second lookup short-circuits without touching the filesystem.
        assert AssetLoader.sprite("no_such_species_9") is None


class TestSpriteKeys:
    def test_sprite_key_format(self):
        stage_number = {"Rookie": 1, "Champion": 2, "Ultimate": 3}
        for species in DIGIMON_REGISTRY.values():
            expected = f"{species.key}_{stage_number[species.stage]}"
            assert species.sprite_key == expected

    def test_sprite_keys_are_unique(self):
        keys = [d.sprite_key for d in DIGIMON_REGISTRY.values()]
        assert len(set(keys)) == len(keys)

    def test_sprite_key_is_lowercase(self):
        for species in DIGIMON_REGISTRY.values():
            assert species.sprite_key == species.sprite_key.lower()


class TestSpriteFactoryIntegration:
    def test_factory_prefers_baked_png(self):
        from core import sprite_factory

        sprite_factory.clear_cache()
        AssetLoader.clear_cache()
        surface = sprite_factory.get_sprite("emberling")
        baked = AssetLoader.sprite("emberling_1")
        if baked is not None:
            assert surface.get_size() == baked.get_size()
        else:
            # If PNG loading is unavailable (no SDL_image), the procedural
            # fallback still produces the correct stage size.
            assert surface.get_size() == (56, 56)
    def test_factory_falls_back_when_asset_missing(self, monkeypatch):
        # With the sprite directory pointed somewhere empty, the factory must
        # still draw the creature rather than return a blank surface.
        from core import sprite_factory
        import core.assets as assets_mod

        monkeypatch.setattr(assets_mod, "SPRITE_DIR", os.path.join("assets", "does-not-exist"))
        AssetLoader.clear_cache()
        sprite_factory.clear_cache()

        surface = sprite_factory.get_sprite("emberling")
        assert surface.get_size() == (56, 56)
        drawn = any(
            surface.get_at((x, y))[3] != 0
            for x in range(0, surface.get_width(), 2)
            for y in range(0, surface.get_height(), 2)
        )
        assert drawn, "procedural fallback drew nothing"
