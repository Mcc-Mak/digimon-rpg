"""Creature sprites for digimon-rpg.

Sprites are loaded exclusively from PNG files in ``assets/sprites/creatures/``.
There is no procedural fallback — if a PNG is missing or cannot be decoded,
a magenta error placeholder is returned so the failure is immediately visible.

PNG decoding uses a pure-Python fallback (``zlib`` + ``struct``) when
``pygame.image.load()`` fails, which happens when the pygame build lacks
SDL_image support (``get_extended() == False``).  This keeps the code
portable across desktop pygame and pygbag/WASM without external deps.
"""

from __future__ import annotations

import os
import struct
import zlib
from typing import Dict, List

import pygame

from core.wasm_log import browser_log
from data.digimon_data import Digimon, get_digimon

# ---------------------------------------------------------------------------
# Diagnostics buffer (drawn on-screen by main.py debug overlay)
# ---------------------------------------------------------------------------

DIAGNOSTICS: List[str] = []


def get_diagnostics() -> List[str]:
    """Return a copy of the accumulated diagnostic messages."""
    return list(DIAGNOSTICS)


def _diag(msg: str) -> None:
    """Append a diagnostic message and also log it to the browser console."""
    DIAGNOSTICS.append(msg)
    print(msg, flush=True)
    browser_log(msg)


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


def _decode_png(data: bytes) -> pygame.Surface:
    """Decode a PNG from raw bytes using only the standard library.

    Falls back to this when ``pygame.image.load()`` cannot handle PNGs
    (i.e. pygame was built without SDL_image).

    Supports 8-bit RGBA (color type 6) and 8-bit RGB (color type 2).
    """
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a valid PNG file")

    pos = 8
    width = height = bit_depth = color_type = 0
    idat_data = bytearray()

    while pos < len(data):
        chunk_len = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + chunk_len]
        pos += 12 + chunk_len  # 4 len + 4 type + data + 4 CRC

        if chunk_type == b"IHDR":
            (width, height, bit_depth, color_type,
             _comp, _filt, _interlace) = struct.unpack(">IIBBBBB", chunk_data[:13])
        elif chunk_type == b"IDAT":
            idat_data.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    if color_type == 6:  # RGBA
        bpp = 4
    elif color_type == 2:  # RGB
        bpp = 3
    else:
        raise ValueError(f"Unsupported color type: {color_type}")

    raw = zlib.decompress(bytes(idat_data))

    stride = width * bpp
    unfiltered = bytearray(stride * height)

    for y in range(height):
        filter_type = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1 : y * (stride + 1) + 1 + stride])

        if filter_type == 0:  # None
            pass
        elif filter_type == 1:  # Sub
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            if y > 0:
                prev = y * stride - stride
                for x in range(stride):
                    line[x] = (line[x] + unfiltered[prev + x]) & 0xFF
        elif filter_type == 3:  # Average
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = unfiltered[(y - 1) * stride + x] if y > 0 else 0
                line[x] = (line[x] + (a + b) // 2) & 0xFF
        elif filter_type == 4:  # Paeth
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = unfiltered[(y - 1) * stride + x] if y > 0 else 0
                c = unfiltered[(y - 1) * stride + x - bpp] if (y > 0 and x >= bpp) else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc:
                    pred = a
                elif pb <= pc:
                    pred = b
                else:
                    pred = c
                line[x] = (line[x] + pred) & 0xFF
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

        unfiltered[y * stride : (y + 1) * stride] = line

    if color_type == 2:  # RGB -> pad to RGBA
        rgba = bytearray(width * height * 4)
        for i in range(width * height):
            rgba[i * 4] = unfiltered[i * 3]
            rgba[i * 4 + 1] = unfiltered[i * 3 + 1]
            rgba[i * 4 + 2] = unfiltered[i * 3 + 2]
            rgba[i * 4 + 3] = 255
        unfiltered = rgba

    return pygame.image.frombytes(bytes(unfiltered), (width, height), "RGBA")


def _try_load(path: str) -> pygame.Surface | None:
    """Try loading a PNG from *path*.

    Strategy:
      1. ``pygame.image.load(path)`` — works when SDL_image is available.
      2. Pure-Python decoder — reads bytes and decodes with ``zlib``/``struct``.

    Returns the surface or ``None``.
    """
    # Strategy 1: pygame's built-in loader (needs SDL_image for PNG)
    try:
        surf = pygame.image.load(path)
        _diag(f"[sprite] OK (pygame): {path} {surf.get_size()}")
        return surf
    except Exception as exc:
        _diag(f"[sprite] pygame fail: {path} -> {exc}")

    # Strategy 2: pure-Python PNG decoder (no SDL_image needed)
    try:
        with open(path, "rb") as f:
            data = f.read()
        surf = _decode_png(data)
        _diag(f"[sprite] OK (decoder): {path} {surf.get_size()}")
        return surf
    except Exception as exc:
        _diag(f"[sprite] decoder fail: {path} -> {exc}")

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
