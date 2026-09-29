"""Creature sprites for digimon-rpg.

Sprites are loaded exclusively from PNG files in ``assets/sprites/creatures/``.
There is no procedural fallback — if a PNG is missing or cannot be decoded,
a magenta error placeholder is returned so the failure is immediately visible.

Under pygbag/WASM the browser decodes PNGs natively via BrowserFS.
"""

from __future__ import annotations

import os
from typing import Dict

import pygame

from data.digimon_data import Digimon, get_digimon

# ---------------------------------------------------------------------------
# Browser console logging (falls back to print on desktop)
# ---------------------------------------------------------------------------

_console = None


def _log(msg: str) -> None:
    """Log to browser DevTools console (js.console.log) or print on desktop."""
    global _console
    if _console is None:
        try:
            import js
            _console = js.console
        except Exception:
            _console = False
    if _console:
        _console.log(msg)
    else:
        print(msg, flush=True)


# ---------------------------------------------------------------------------
# Sprite directory auto-detection
# ---------------------------------------------------------------------------

#: Evolution stage -> numeric suffix used in PNG filenames.
_STAGE_NUM: Dict[str, int] = {
    "Rookie": 1,
    "Champion": 2,
    "Ultimate": 3,
}

#: Candidate directories to search for creature PNG sprites.
_SPRITE_CANDIDATES = [
    os.path.join("assets", "sprites", "creatures"),
    os.path.join("assets", "assets", "sprites", "creatures"),
    os.path.join("sprites", "creatures"),
    "sprites/creatures",
]


def _find_sprite_dir() -> str | None:
    """Search for the directory containing creature PNG sprites.

    Under pygbag/WASM the CWD and archive mount point may differ from
    desktop, so we probe several candidate paths and pick the first one
    that contains at least one ``.png`` file.
    """
    _log(f"[sprite] CWD = {os.getcwd()}")
    try:
        entries = os.listdir(".")
        _log(f"[sprite] CWD listing: {entries}")
    except Exception as exc:
        _log(f"[sprite] CWD listing failed: {exc}")

    for candidate in _SPRITE_CANDIDATES:
        try:
            files = os.listdir(candidate)
            pngs = [f for f in files if f.endswith(".png")]
            _log(f"[sprite] {candidate}: {len(pngs)} PNGs found")
            if pngs:
                _log(f"[sprite] Using sprite dir: {candidate}")
                return candidate
        except Exception:
            _log(f"[sprite] {candidate}: not found / not readable")

    _log("[sprite] WARNING: no sprite directory found!")
    return None


_SPRITE_DIR: str | None = _find_sprite_dir()


#: species_key -> base sprite (facing right).
_CACHE: Dict[str, pygame.Surface] = {}

#: "species_key|facing" -> battle sprite (optionally flipped / scaled).
_BATTLE_CACHE: Dict[str, pygame.Surface] = {}


def _error_placeholder(size: int = 56) -> pygame.Surface:
    """Return a magenta error placeholder surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((255, 0, 255))
    return surf


def _load_png_sprite(species: Digimon) -> pygame.Surface | None:
    """Load a PNG sprite for *species*.

    Returns the loaded surface (with per-pixel alpha) or ``None`` if the
    file is missing or cannot be decoded.
    """
    stage_num = _STAGE_NUM.get(species.stage)
    if stage_num is None:
        _log(f"[sprite] No stage mapping for {species.key} ({species.stage})")
        return None
    if _SPRITE_DIR is None:
        _log(f"[sprite] No sprite dir — cannot load {species.key}")
        return None
    path = os.path.join(_SPRITE_DIR, f"{species.key}_{stage_num}.png")
    try:
        surf = pygame.image.load(path)
    except Exception as exc:
        _log(f"[sprite] PNG load failed: {path} -> {exc}")
        return None
    try:
        surf = surf.convert_alpha()
    except Exception:
        pass
    _log(f"[sprite] PNG OK: {path} {surf.get_size()}")
    return surf


def get_sprite(name: str) -> pygame.Surface:
    """Return the cached base sprite for a species (facing right).

    Args:
        name: Species display name or lowercase registry key.

    Returns:
        A transparent ``SRCALPHA`` surface with the creature sprite.
        If the PNG cannot be loaded, a magenta error placeholder is returned.
    """
    key = name.strip().lower()
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    try:
        species = get_digimon(key)
    except KeyError:
        _log(f"[sprite] Unknown species: {key}")
        surf = _error_placeholder()
        _CACHE[key] = surf
        return surf

    png = _load_png_sprite(species)
    if png is not None:
        surf = png
    else:
        surf = _error_placeholder()

    _CACHE[key] = surf
    return surf


def get_battle_sprite(name: str, facing: str = "right") -> pygame.Surface:
    """Return a cached battle sprite for a species, optionally flipped.

    Args:
        name: Species display name or lowercase registry key.
        facing: ``"right"`` (player side) or ``"left"`` (enemy side,
            horizontally flipped so the creature faces the player).

    Returns:
        A transparent surface ready to blit into the battle scene.
    """
    facing = "left" if facing == "left" else "right"
    key = f"{name.strip().lower()}|{facing}"
    cached = _BATTLE_CACHE.get(key)
    if cached is not None:
        return cached

    base = get_sprite(name)
    if facing == "left":
        sprite = pygame.transform.flip(base, True, False)
    else:
        sprite = base.copy()
    _BATTLE_CACHE[key] = sprite
    return sprite


def get_world_sprite(name: str, size: int = 30, facing: str = "right") -> pygame.Surface:
    """Return a scaled sprite suitable for the overworld avatar.

    Args:
        name: Species display name or lowercase registry key.
        size: Target edge length in pixels.
        facing: ``"right"`` or ``"left"``.
    """
    base = get_battle_sprite(name, facing=facing)
    cache_key = f"world|{name.strip().lower()}|{facing}|{size}"
    cached = _BATTLE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    scaled = pygame.transform.scale(base, (size, size))
    _BATTLE_CACHE[cache_key] = scaled
    return scaled


def clear_cache() -> None:
    """Empty both sprite caches. Intended for tests."""
    _CACHE.clear()
    _BATTLE_CACHE.clear()


__all__ = [
    "get_sprite",
    "get_battle_sprite",
    "get_world_sprite",
    "clear_cache",
]
