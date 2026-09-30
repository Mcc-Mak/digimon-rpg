"""Asset loading and caching for digimon-rpg.

This module implements the ``AssetLoader`` described in ``doc/Architecture.md``
section 7.1 and ``doc/API.md`` section 8: a class-level singleton that loads
image assets from ``assets/`` once and hands back cached ``pygame.Surface``
instances.

Path resolution
----------------

``pygame.image.load`` needs a path that resolves correctly in three very
different environments: a desktop checkout, the pygbag dev server, and the
WASM bundle served to a browser. Rather than guess one convention,
:func:`_candidate_roots` yields the plausible roots in priority order and the
first one that contains the requested file wins. The roots are derived from
``__file__`` so they are independent of the process working directory
(``doc/SRS.md`` requires asset paths be relative to the script, not the cwd).

Missing assets are not fatal
----------------------------

A missing file returns ``None`` from :meth:`AssetLoader.sprite` rather than
raising, so callers can fall back to procedural art.

WASM safety: this module performs only ``pygame.image.load`` (non-blocking,
backed by the browser's virtual filesystem) and dict lookups. No
``subprocess``, no threads, no C extensions.
"""

from __future__ import annotations

import os
import struct
import zlib
from typing import Dict, Iterable, List, Optional

import pygame

from core.wasm_log import browser_log

#: Directory names searched for under the project root.
SPRITE_DIR: str = os.path.join("assets", "sprites", "creatures")


def _candidate_roots() -> Iterable[str]:
    """Yield plausible project roots, most specific first.

    ``__file__`` is ``<root>/core/assets.py``, so the parent of this
    module's directory is the project root in a source checkout and inside
    the pygbag bundle alike.
    """
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(module_dir)
    browser_log(f"[assets] __file__={os.path.abspath(__file__)}")
    browser_log(f"[assets] module_dir={module_dir}")
    browser_log(f"[assets] project_root={project_root}")
    browser_log(f"[assets] cwd={os.path.abspath(os.getcwd())}")
    # In the pygbag bundle the app is unpacked under a hashed build dir, so
    # also consider the cwd the browser serves from.
    seen: List[str] = []
    for root in (project_root, os.path.abspath(os.getcwd())):
        if root not in seen:
            seen.append(root)
            browser_log(f"[assets] candidate root: {root}")
            yield root


def _decode_png(data: bytes) -> pygame.Surface:
    """Decode a PNG from raw bytes using only the standard library.

    Falls back to this when ``pygame.image.load()`` cannot handle PNGs
    (i.e. pygame was built without SDL_image, ``get_extended() == False``).

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


def _load_transparent(path: str) -> pygame.Surface:
    """Load an image and guarantee it has per-pixel alpha.

    PNGs are already decoded with an alpha channel, so the surface usually
    arrives as ``SRCALPHA`` and no conversion is needed. ``convert_alpha()``
    is only attempted when a display exists: it re-quantizes the surface
    against the current display format, and it raises ``pygame.error`` when
    ``pygame.display`` has not been initialised. Skipping it in that case
    keeps the loader usable from tests and from headless bake tooling.

    When SDL_image is available (``pygame.image.get_extended()`` returns
    True — the normal case in pygbag/WASM), ``pygame.image.load`` is used
    directly. Any exception propagates to the caller so the procedural
    fallback in ``sprite_factory`` can draw a substitute.

    On desktop builds without SDL_image, a pure-Python ``zlib``+``struct``
    decoder is used instead. This decoder is far too slow for WASM
    (pixel-by-pixel Python loops freeze the browser), so it is gated on
    ``get_extended() == False`` and never runs in the deployed build.
    """
    if pygame.image.get_extended():
        # SDL_image is available — pygame.image.load handles PNGs.
        browser_log(f"[assets] get_extended=True, using pygame.image.load")
        surface = pygame.image.load(path)
        browser_log(f"[assets] loaded: {path} size={surface.get_size()}")
        if surface.get_flags() & pygame.SRCALPHA:
            return surface
        if not pygame.display.get_init():
            surface.set_alpha(None)
            return surface
        return surface.convert_alpha()

    # Desktop fallback: pure-Python PNG decoder (no SDL_image needed).
    # Never runs in WASM — get_extended() is True there.
    browser_log(f"[assets] get_extended=False, using pure-Python decoder")
    with open(path, "rb") as f:
        data = f.read()
    return _decode_png(data)


class AssetLoader:
    """Loads and caches game assets. Class-level singleton.

    All methods are ``classmethod``s operating on shared caches, so any call
    site gets the same ``pygame.Surface`` instance and the image is decoded
    at most once per process.
    """

    #: sprite key (e.g. ``"emberling_1"``) -> loaded surface.
    _sprites: Dict[str, pygame.Surface] = {}

    #: sprite keys that were looked up and found missing. Prevents repeated
    #: filesystem probes (and repeated warnings) for a known-absent asset.
    _missing: set[str] = set()

    @classmethod
    def resolve(cls, relative: str) -> Optional[str]:
        """Return an existing absolute path for ``relative``, or ``None``.

        Args:
            relative: Path relative to the project root, e.g.
                ``"assets/sprites/creatures/emberling_1.png"``.
        """
        relative = relative.replace("\\", "/").lstrip("/")
        for root in _candidate_roots():
            candidate = os.path.join(root, *relative.split("/"))
            exists = os.path.isfile(candidate)
            browser_log(f"[assets] resolve: {candidate} exists={exists}")
            if exists:
                return candidate
        browser_log(f"[assets] resolve: NOT FOUND for {relative}")
        return None

    @classmethod
    def sprite(cls, name: str) -> Optional[pygame.Surface]:
        """Load and cache a creature sprite by name.

        Args:
            name: Sprite key with or without the ``.png`` extension, e.g.
                ``"emberling_1"`` or ``"emberling_1.png"``. Case-insensitive.

        Returns:
            A surface with per-pixel alpha, or ``None`` when the asset is not
            present on disk. Returning ``None`` lets the caller fall back to
            procedural drawing rather than crash.
        """
        key = name.strip().lower()
        if key.endswith(".png"):
            key = key[:-4]
        browser_log(f"[assets] sprite requested: key={key}")
        cached = cls._sprites.get(key)
        if cached is not None:
            browser_log(f"[assets] sprite cache hit: {key}")
            return cached
        if key in cls._missing:
            browser_log(f"[assets] sprite known missing: {key}")
            return None

        path = cls.resolve(f"{SPRITE_DIR}/{key}.png")
        if path is None:
            browser_log(f"[assets] sprite file not found: {key}")
            cls._missing.add(key)
            return None

        try:
            browser_log(f"[assets] loading sprite: {key} from {path}")
            surface = _load_transparent(path)
            browser_log(f"[assets] sprite loaded OK: {key} size={surface.get_size()}")
        except Exception as exc:
            browser_log(f"[assets] sprite load FAILED: {key} error={exc!r}")
            cls._missing.add(key)
            return None

        cls._sprites[key] = surface
        return surface

    @classmethod
    def has_sprite(cls, name: str) -> bool:
        """Return whether a sprite can be loaded, without loading it."""
        key = name.strip().lower()
        if key.endswith(".png"):
            key = key[:-4]
        if key in cls._sprites:
            return True
        return cls.resolve(f"{SPRITE_DIR}/{key}.png") is not None

    @classmethod
    def clear_cache(cls) -> None:
        """Empty the asset caches. Intended for tests."""
        cls._sprites.clear()
        cls._missing.clear()


__all__ = ["AssetLoader", "SPRITE_DIR"]
