"""Creature sprites for digimon-rpg.

Sprites are loaded exclusively from PNG files in ``assets/sprites/creatures/``.
There is no procedural fallback — if a PNG is missing or cannot be decoded,
a magenta error placeholder is returned so the failure is immediately visible.

Under pygbag/WASM the browser decodes PNGs natively via BrowserFS.
"""

from __future__ import annotations

import io
import os
from typing import Dict, List

import pygame

from data.digimon_data import Digimon, get_digimon

# ---------------------------------------------------------------------------
# Diagnostics buffer (drawn on-screen by main.py debug overlay)
# ---------------------------------------------------------------------------

DIAGNOSTICS: List[str] = []


def get_diagnostics() -> List[str]:
    """Return a copy of the accumulated diagnostic messages."""
    return list(DIAGNOSTICS)


def _diag(msg: str) -> None:
    """Append a diagnostic message and also print it (goes to xterm in WASM)."""
    DIAGNOSTICS.append(msg)
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Sprite loading
# ---------------------------------------------------------------------------

#: Evolution stage -> numeric suffix used in PNG filenames.
_STAGE_NUM: Dict[str, int] = {
    "Rookie": 1,
    "Champion": 2,
    "Ultimate": 3,
}

#: Candidate relative paths for the sprite directory.
#: pygbag's archive mount can create different CWD layouts, so we try
#: all of these when loading a sprite.
_SPRITE_PATH_CANDIDATES = [
    "assets/sprites/creatures",
    "assets/assets/sprites/creatures",
    "sprites/creatures",
]

#: species_key -> base sprite (facing right).
_CACHE: Dict[str, pygame.Surface] = {}

#: "species_key|facing" -> battle sprite (optionally flipped / scaled).
_BATTLE_CACHE: Dict[str, pygame.Surface] = {}

#: Tracks whether we've logged the CWD / path diagnostics already.
_DIAG_INITIALIZED: bool = False


def _init_diagnostics() -> None:
    """Log CWD and directory listing once (lazily on first sprite load)."""
    global _DIAG_INITIALIZED
    if _DIAG_INITIALIZED:
        return
    _DIAG_INITIALIZED = True
    try:
        cwd = os.getcwd()
    except Exception as exc:
        cwd = f"<error: {exc}>"
    _diag(f"[sprite] CWD={cwd}")
    try:
        entries = os.listdir(".")
        _diag(f"[sprite] CWD entries: {entries}")
    except Exception as exc:
        _diag(f"[sprite] CWD listdir error: {exc}")
    for cand in _SPRITE_PATH_CANDIDATES:
        try:
            files = os.listdir(cand)
            pngs = [f for f in files if f.endswith(".png")]
            _diag(f"[sprite] {cand}: {len(pngs)} PNGs")
        except Exception:
            _diag(f"[sprite] {cand}: not readable")


def _error_placeholder(size: int = 56) -> pygame.Surface:
    """Return a magenta error placeholder surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((255, 0, 255))
    return surf


def _try_load(path: str) -> pygame.Surface | None:
    """Try loading a PNG from *path* using two strategies.

    1. Direct ``pygame.image.load(path)``.
    2. File-object: ``open(path, 'rb')`` + ``pygame.image.load(BytesIO)``.

    Returns the surface or ``None``.
    """
    # Strategy 1: direct path load
    try:
        surf = pygame.image.load(path)
        _diag(f"[sprite] OK (direct): {path} {surf.get_size()}")
        return surf
    except Exception as exc:
        _diag(f"[sprite] direct fail: {path} -> {exc}")

    # Strategy 2: file-object load
    try:
        with open(path, "rb") as f:
            data = f.read()
        _diag(f"[sprite] read {len(data)} bytes from {path}")
        surf = pygame.image.load(io.BytesIO(data))
        _diag(f"[sprite] OK (fileobj): {path} {surf.get_size()}")
        return surf
    except Exception as exc:
        _diag(f"[sprite] fileobj fail: {path} -> {exc}")

    return None


def _load_png_sprite(species: Digimon) -> pygame.Surface | None:
    """Load a PNG sprite for *species*.

    Tries multiple candidate directories and two loading strategies.
    Returns the loaded surface (with per-pixel alpha) or ``None``.
    """
    _init_diagnostics()

    stage_num = _STAGE_NUM.get(species.stage)
    if stage_num is None:
        _diag(f"[sprite] No stage mapping for {species.key} ({species.stage})")
        return None

    filename = f"{species.key}_{stage_num}.png"

    for base in _SPRITE_PATH_CANDIDATES:
        path = os.path.join(base, filename)
        surf = _try_load(path)
        if surf is not None:
            try:
                surf = surf.convert_alpha()
            except Exception:
                pass
            return surf

    _diag(f"[sprite] All paths failed for {species.key}")
    return None


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
        _diag(f"[sprite] Unknown species: {key}")
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
    "get_diagnostics",
    "DIAGNOSTICS",
]
