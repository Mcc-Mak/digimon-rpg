"""Hybrid creature sprites for digimon-rpg.

Each Digimon species is rendered from a pre-drawn PNG asset when available,
falling back to a procedural ``pygame.draw`` silhouette otherwise. This keeps
the game fully functional on desktop (where SDL2_image may be absent) while
leveraging the 140-sprite asset library under pygbag/WASM (where the browser
decodes PNGs natively).

Asset lookup
------------

PNG files live in ``assets/sprites/creatures/`` and follow the naming
convention ``{species_key}_{stage_num}.png`` where *stage_num* is 1 (Rookie),
2 (Champion), or 3 (Ultimate). If the file is missing or cannot be decoded,
the procedural drawer runs instead.

Procedural fallback
-------------------

* Body color, accent color, and glow color are derived from the species'
  element via :data:`_ELEMENT_PALETTE`.
* Sprite canvas size scales with evolution stage (Rookie < Champion <
  Ultimate) so Ultimates read as larger and more detailed.
* A per-species draw function (registered in :data:`_DRAWERS`) paints the
  creature. Species without a dedicated drawer fall back to a generic
  elemental blob so rendering never crashes on an unknown name.

Caching
-------

Surfaces are cached: the first call builds the sprite, later calls return
the cached instance. Battle sprites are cached per facing direction.

WASM safety: ``pygame.image.load`` is the only I/O call and is wrapped in
try/except so failures degrade gracefully to procedural drawing. No subprocess,
no threads.
"""

from __future__ import annotations

import os
from typing import Callable, Dict, Tuple

import pygame

from data.digimon_data import Digimon, get_digimon

# A draw function takes the target surface, the canvas size S, and the
# (body, accent, glow) color triple and paints the creature centered on it.
_DrawFn = Callable[[pygame.Surface, int, Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]], None]
_RGB = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Palettes and sizing
# ---------------------------------------------------------------------------

#: Element -> (body, accent, glow) color triples.
_ELEMENT_PALETTE: Dict[str, Tuple[_RGB, _RGB, _RGB]] = {
    "fire":     ((224, 80, 40),  (255, 180, 40),  (255, 230, 150)),
    "water":    ((60, 130, 220), (150, 220, 255), (200, 240, 255)),
    "nature":   ((80, 170, 70),  (180, 230, 120), (230, 250, 200)),
    "electric": ((240, 210, 50), (255, 255, 170), (255, 245, 200)),
    "earth":    ((150, 110, 70), (210, 190, 150), (120, 95, 60)),
    "dark":     ((90, 60, 130),  (180, 120, 220), (230, 190, 255)),
    "normal":   ((160, 160, 160),(220, 220, 220), (240, 240, 240)),
}

#: Evolution stage -> canvas size in pixels.
_STAGE_SIZE: Dict[str, int] = {
    "Rookie": 56,
    "Champion": 72,
    "Ultimate": 88,
}

_DEFAULT_SIZE: int = 56

#: Evolution stage -> numeric suffix used in PNG filenames.
_STAGE_NUM: Dict[str, int] = {
    "Rookie": 1,
    "Champion": 2,
    "Ultimate": 3,
}

#: Directory containing creature PNG sprites.
_SPRITE_DIR = os.path.join("assets", "sprites", "creatures")

#: When True, skip PNG loading and always use procedural drawing. Tests set
#: this to True so they exercise the deterministic procedural path regardless
#: of whether SDL2_image is installed on the host.
_FORCE_PROCEDURAL: bool = False


# ---------------------------------------------------------------------------
# Color / draw helpers
# ---------------------------------------------------------------------------

def _darken(color: _RGB, factor: float = 0.6) -> _RGB:
    """Return a darker shade of ``color`` multiplied by ``factor``."""
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def _lighten(color: _RGB, factor: float = 0.3) -> _RGB:
    """Return a lighter shade of ``color`` mixed toward white by ``factor``."""
    return (
        max(0, min(255, int(color[0] + (255 - color[0]) * factor))),
        max(0, min(255, int(color[1] + (255 - color[1]) * factor))),
        max(0, min(255, int(color[2] + (255 - color[2]) * factor))),
    )


def _soft_disc(surf: pygame.Surface, center: Tuple[int, int], radius: int,
               color: _RGB, alpha: int = 70) -> None:
    """Blit a soft, semi-transparent disc (used for auras / glows)."""
    if radius <= 0:
        return
    size = radius * 2 + 4
    tmp = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (color[0], color[1], color[2], alpha),
                       (radius + 2, radius + 2), radius)
    surf.blit(tmp, (center[0] - radius - 2, center[1] - radius - 2))


def _draw_eyes(surf: pygame.Surface, cx: int, cy: int, sep: int, r: int,
               white: _RGB = (255, 255, 255), pupil: _RGB = (25, 25, 35)) -> None:
    """Draw a pair of forward-facing eyes centered above (cx, cy)."""
    r = max(1, r)
    pygame.draw.circle(surf, white, (cx - sep, cy), r)
    pygame.draw.circle(surf, white, (cx + sep, cy), r)
    pr = max(1, r - 2)
    pygame.draw.circle(surf, pupil, (cx - sep + 1, cy), pr)
    pygame.draw.circle(surf, pupil, (cx + sep + 1, cy), pr)


def _draw_flame(surf: pygame.Surface, x: int, y: int, scale: int,
                color: _RGB, hot: _RGB) -> None:
    """Draw a stylized flame at (x, y) used for fire-type tails/auras."""
    s = scale
    # Outer flame.
    pygame.draw.polygon(surf, color, [
        (x, y - 3 * s),
        (x - s, y - s),
        (x - 2 * s, y + s),
        (x - s, y),
        (x, y + 2 * s),
        (x + s, y),
        (x + 2 * s, y + s),
        (x + s, y - s),
    ])
    # Inner hot core.
    pygame.draw.polygon(surf, hot, [
        (x, y - 2 * s),
        (x - s, y),
        (x, y + s),
        (x + s, y),
    ])


def _draw_droplet(surf: pygame.Surface, x: int, y: int, r: int,
                  color: _RGB) -> None:
    """Draw a water droplet (circle + pointed top)."""
    pygame.draw.circle(surf, color, (x, y), r)
    pygame.draw.polygon(surf, color, [(x - r, y), (x, y - r * 2), (x + r, y)])


def _draw_lightning(surf: pygame.Surface, x: int, y: int, s: int,
                    color: _RGB) -> None:
    """Draw a small zigzag lightning bolt."""
    pygame.draw.lines(surf, color, False, [
        (x, y - 2 * s),
        (x - s, y),
        (x + s, y),
        (x - s, y + 2 * s),
    ], 2)


def _draw_thorn(surf: pygame.Surface, x: int, y: int, length: int,
                color: _RGB, angle: int = 0) -> None:
    """Draw a triangular thorn pointing outward from (x, y)."""
    if angle == 0:  # pointing right
        pts = [(x, y - 3), (x + length, y), (x, y + 3)]
    elif angle == 180:  # pointing left
        pts = [(x, y - 3), (x - length, y), (x, y + 3)]
    elif angle == 90:  # pointing up
        pts = [(x - 3, y), (x, y - length), (x + 3, y)]
    else:  # pointing down
        pts = [(x - 3, y), (x, y + length), (x + 3, y)]
    pygame.draw.polygon(surf, color, pts)


# ---------------------------------------------------------------------------
# Per-species draw functions
# ---------------------------------------------------------------------------

def _draw_emberling(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.6)
    # Tail flame (behind body).
    _draw_flame(surf, cx + 16, S - 22, 4, accent, glow)
    # Legs.
    pygame.draw.rect(surf, dark, (cx - 8, S - 16, 5, 10))
    pygame.draw.rect(surf, dark, (cx + 4, S - 16, 5, 10))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 14, S - 28, 28, 18))
    # Ember patches along the spine.
    pygame.draw.circle(surf, accent, (cx - 6, S - 24), 3)
    pygame.draw.circle(surf, accent, (cx + 4, S - 22), 3)
    # Head.
    pygame.draw.circle(surf, body, (cx - 2, S - 38), 11)
    pygame.draw.ellipse(surf, body, (cx + 4, S - 40, 10, 8))  # snout
    # Eyes + mouth.
    _draw_eyes(surf, cx - 2, S - 40, 4, 3)
    pygame.draw.line(surf, dark, (cx + 6, S - 33), (cx + 12, S - 33), 1)


def _draw_pyroclaw(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.55)
    # Quadruped legs.
    for lx in (cx - 14, cx - 4, cx + 6, cx + 14):
        pygame.draw.rect(surf, dark, (lx, S - 18, 6, 14))
        # White-hot claws.
        pygame.draw.polygon(surf, (255, 250, 220),
                            [(lx, S - 4), (lx + 2, S - 1), (lx + 4, S - 4)])
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 18, S - 30, 36, 20))
    # Molten veins (glowing cracks).
    pygame.draw.line(surf, glow, (cx - 8, S - 24), (cx + 6, S - 18), 2)
    pygame.draw.line(surf, glow, (cx + 2, S - 26), (cx + 12, S - 22), 2)
    # Head.
    pygame.draw.circle(surf, body, (cx + 16, S - 36), 11)
    pygame.draw.ellipse(surf, body, (cx + 20, S - 38, 12, 9))  # jaw
    # Glowing eye.
    pygame.draw.circle(surf, glow, (cx + 18, S - 38), 3)
    pygame.draw.circle(surf, (40, 20, 0), (cx + 19, S - 38), 1)
    # Horns.
    pygame.draw.polygon(surf, dark,
                        [(cx + 12, S - 44), (cx + 10, S - 50), (cx + 15, S - 45)])
    pygame.draw.polygon(surf, dark,
                        [(cx + 20, S - 44), (cx + 22, S - 50), (cx + 17, S - 45)])


def _draw_infernosaur(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.5)
    # Flame aura.
    _soft_disc(surf, (cx, S - 28), 30, accent, alpha=60)
    # Wings.
    pygame.draw.polygon(surf, dark, [
        (cx - 14, S - 40), (cx - 34, S - 50), (cx - 30, S - 34), (cx - 10, S - 32)])
    pygame.draw.polygon(surf, dark, [
        (cx + 14, S - 40), (cx + 34, S - 50), (cx + 30, S - 34), (cx + 10, S - 32)])
    # Tail with flame.
    pygame.draw.polygon(surf, body,
                        [(cx - 18, S - 22), (cx - 32, S - 14), (cx - 16, S - 16)])
    _draw_flame(surf, cx - 30, S - 16, 5, accent, glow)
    # Legs.
    pygame.draw.rect(surf, dark, (cx - 12, S - 14, 7, 14))
    pygame.draw.rect(surf, dark, (cx + 5, S - 14, 7, 14))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 18, S - 34, 36, 24))
    # Neck + head.
    pygame.draw.polygon(surf, body,
                        [(cx + 8, S - 32), (cx + 22, S - 48), (cx + 14, S - 30)])
    pygame.draw.circle(surf, body, (cx + 22, S - 48), 10)
    pygame.draw.polygon(surf, dark,
                        [(cx + 28, S - 50), (cx + 36, S - 48), (cx + 28, S - 46)])  # snout
    # Eye.
    pygame.draw.circle(surf, glow, (cx + 22, S - 50), 3)
    pygame.draw.circle(surf, (60, 20, 0), (cx + 23, S - 50), 1)
    # Dorsal flame crest.
    for i, fx in enumerate((cx - 8, cx, cx + 8)):
        _draw_flame(surf, fx, S - 38, 3, accent, glow)


def _draw_aquapup(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.6)
    # Translucent side fins.
    _soft_disc(surf, (cx - 16, S - 22), 10, accent, alpha=90)
    _soft_disc(surf, (cx + 16, S - 22), 10, accent, alpha=90)
    # Tail flipper.
    pygame.draw.ellipse(surf, accent, (cx + 16, S - 20, 12, 8))
    # Round body.
    pygame.draw.circle(surf, body, (cx, S - 22), 16)
    # Belly highlight.
    pygame.draw.ellipse(surf, accent, (cx - 8, S - 16, 16, 10))
    # Head (merged).
    pygame.draw.circle(surf, body, (cx - 4, S - 34), 11)
    # Ears.
    pygame.draw.circle(surf, dark, (cx - 12, S - 42), 4)
    pygame.draw.circle(surf, dark, (cx + 2, S - 42), 4)
    # Big hopeful eyes.
    _draw_eyes(surf, cx - 4, S - 36, 4, 4)
    # Whiskers.
    pygame.draw.line(surf, dark, (cx - 10, S - 30), (cx - 18, S - 30), 1)
    pygame.draw.line(surf, dark, (cx + 2, S - 30), (cx + 10, S - 30), 1)
    # Nose.
    pygame.draw.circle(surf, dark, (cx - 4, S - 30), 2)


def _draw_tsunamut(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.55)
    # Water jets around body.
    for dx, dy, r in ((-22, -6, 4), (20, -10, 5), (-14, 12, 3), (22, 8, 4)):
        _draw_droplet(surf, cx + dx, S - 24 + dy, r, accent)
    # Legs with claws.
    for lx in (cx - 12, cx + 4):
        pygame.draw.rect(surf, dark, (lx, S - 16, 7, 14))
        for i in range(3):
            pygame.draw.polygon(surf, (240, 250, 255),
                                [(lx + i * 2, S - 2), (lx + i * 2 + 1, S + 1), (lx + i * 2 + 2, S - 2)])
    # Elongated body.
    pygame.draw.ellipse(surf, body, (cx - 18, S - 30, 36, 20))
    pygame.draw.ellipse(surf, accent, (cx - 12, S - 22, 24, 10))  # belly
    # Head.
    pygame.draw.circle(surf, body, (cx + 16, S - 34), 11)
    pygame.draw.ellipse(surf, body, (cx + 20, S - 36, 12, 8))  # snout
    # Enormous claws on forelimb.
    pygame.draw.rect(surf, dark, (cx - 16, S - 16, 7, 12))
    for i in range(3):
        pygame.draw.polygon(surf, (240, 250, 255),
                            [(cx - 16 + i * 2, S - 4), (cx - 16 + i * 2 + 1, S - 1), (cx - 16 + i * 2 + 2, S - 4)])
    # Eyes.
    _draw_eyes(surf, cx + 16, S - 36, 4, 3)


def _draw_leviathore(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.5)
    # Water aura.
    _soft_disc(surf, (cx, S - 26), 32, accent, alpha=55)
    # Serpentine body: chain of decreasing circles curving across canvas.
    nodes = [(cx - 26, S - 14), (cx - 14, S - 20), (cx - 2, S - 18),
             (cx + 10, S - 24), (cx + 20, S - 20)]
    for i, (nx, ny) in enumerate(nodes):
        r = 13 - i
        pygame.draw.circle(surf, body, (nx, ny), r)
        pygame.draw.circle(surf, accent, (nx, ny - r // 3), max(2, r // 2))  # belly
    # Dorsal fins along the spine.
    for fx, fy in ((cx - 18, S - 30), (cx - 6, S - 32), (cx + 8, S - 36)):
        pygame.draw.polygon(surf, dark,
                            [(fx, fy), (fx + 4, fy - 8), (fx + 8, fy)])
    # Head at the leading end.
    pygame.draw.circle(surf, body, (cx + 26, S - 20), 12)
    pygame.draw.polygon(surf, dark,
                        [(cx + 34, S - 22), (cx + 42, S - 20), (cx + 34, S - 18)])  # jaw
    # Eye.
    pygame.draw.circle(surf, (255, 255, 255), (cx + 28, S - 23), 3)
    pygame.draw.circle(surf, dark, (cx + 29, S - 23), 1)
    # Side flipper.
    pygame.draw.ellipse(surf, dark, (cx - 4, S - 12, 14, 6))


def _draw_stormwing(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.55)
    # Static arcs around body.
    _draw_lightning(surf, cx - 18, S - 26, 3, glow)
    _draw_lightning(surf, cx + 18, S - 26, 3, glow)
    # Wings (feathered).
    pygame.draw.polygon(surf, accent, [
        (cx - 6, S - 30), (cx - 22, S - 40), (cx - 18, S - 26), (cx - 4, S - 24)])
    pygame.draw.polygon(surf, accent, [
        (cx + 6, S - 30), (cx + 22, S - 40), (cx + 18, S - 26), (cx + 4, S - 24)])
    # Thin legs.
    pygame.draw.line(surf, dark, (cx - 4, S - 14), (cx - 6, S - 2), 2)
    pygame.draw.line(surf, dark, (cx + 4, S - 14), (cx + 6, S - 2), 2)
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 8, S - 28, 16, 16))
    # Head.
    pygame.draw.circle(surf, body, (cx, S - 36), 8)
    # Beak.
    pygame.draw.polygon(surf, (255, 180, 40),
                        [(cx + 6, S - 38), (cx + 12, S - 36), (cx + 6, S - 34)])
    # Eye.
    _draw_eyes(surf, cx, S - 38, 3, 2)
    # Crest feather.
    pygame.draw.line(surf, dark, (cx, S - 44), (cx, S - 48), 2)


def _draw_rockbash(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.5)
    stone = (130, 120, 110)
    # Short legs.
    pygame.draw.rect(surf, dark, (cx - 12, S - 14, 6, 12))
    pygame.draw.rect(surf, dark, (cx + 6, S - 14, 6, 12))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 16, S - 28, 32, 18))
    # Overlapping stone plates on the back.
    for i, px in enumerate((cx - 12, cx - 4, cx + 4, cx + 12)):
        r = 7 - abs(i - 1)
        pygame.draw.circle(surf, stone, (px, S - 30), r)
        pygame.draw.circle(surf, _darken(stone, 0.7), (px, S - 30), r, 1)
    # Head.
    pygame.draw.circle(surf, body, (cx - 16, S - 30), 9)
    # Snout.
    pygame.draw.ellipse(surf, body, (cx - 24, S - 30, 10, 8))
    # Eyes.
    _draw_eyes(surf, cx - 16, S - 32, 3, 2)
    # Snout nostril.
    pygame.draw.circle(surf, dark, (cx - 20, S - 30), 1)


def _draw_seedkit(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.55)
    # Stubby legs.
    pygame.draw.rect(surf, dark, (cx - 8, S - 14, 6, 10))
    pygame.draw.rect(surf, dark, (cx + 2, S - 14, 6, 10))
    # Bulb body.
    pygame.draw.ellipse(surf, body, (cx - 14, S - 28, 28, 20))
    # Belly highlight.
    pygame.draw.ellipse(surf, accent, (cx - 8, S - 20, 16, 10))
    # Side leaves.
    pygame.draw.ellipse(surf, dark, (cx - 22, S - 24, 10, 6))
    pygame.draw.ellipse(surf, dark, (cx + 12, S - 24, 10, 6))
    # Sprout stem.
    pygame.draw.line(surf, dark, (cx, S - 30), (cx, S - 40), 2)
    # Flower bud on top.
    pygame.draw.circle(surf, (240, 150, 180), (cx, S - 42), 6)
    pygame.draw.circle(surf, (255, 220, 120), (cx, S - 42), 3)
    # Eyes.
    _draw_eyes(surf, cx, S - 22, 4, 3)
    # Smile.
    pygame.draw.arc(surf, dark, (cx - 4, S - 20, 8, 6), 3.4, 6.0, 1)


def _draw_chaospuff(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.45)
    # Wispy aura.
    _soft_disc(surf, (cx, S - 26), 24, accent, alpha=45)
    # Drifting tendrils below.
    for tx in (cx - 10, cx, cx + 10):
        pygame.draw.lines(surf, dark, False,
                          [(tx, S - 16), (tx - 3, S - 8), (tx + 3, S - 4)], 2)
    # Irregular wispy body: overlapping circles of varying size.
    for ox, oy, r in ((-8, 0, 11), (8, 0, 11), (0, -6, 12),
                      (-4, 8, 9), (6, 8, 9), (0, 2, 13)):
        pygame.draw.circle(surf, body, (cx + ox, S - 26 + oy), r)
    # Wavy bottom edge.
    pygame.draw.polygon(surf, body, [
        (cx - 14, S - 16), (cx - 8, S - 12), (cx - 2, S - 16),
        (cx + 4, S - 12), (cx + 10, S - 16), (cx + 14, S - 12),
        (cx + 14, S - 8), (cx - 14, S - 8)])
    # Glowing purple eyes (no pupils — shadowy).
    pygame.draw.circle(surf, glow, (cx - 5, S - 30), 3)
    pygame.draw.circle(surf, glow, (cx + 5, S - 30), 3)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 5, S - 30), 1)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 5, S - 30), 1)


def _draw_thornbloom(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.5)
    # Tall stem.
    pygame.draw.rect(surf, dark, (cx - 4, S - 30, 8, 26))
    # Thorns along the stem.
    for ty in (S - 26, S - 18, S - 10):
        _draw_thorn(surf, cx + 4, ty, 7, dark, angle=0)
        _draw_thorn(surf, cx - 4, ty + 4, 7, dark, angle=180)
    # Leaves.
    pygame.draw.ellipse(surf, body, (cx - 18, S - 22, 12, 6))
    pygame.draw.ellipse(surf, body, (cx + 6, S - 16, 12, 6))
    # Flower head: petals around a center.
    center = (cx, S - 38)
    for i in range(8):
        import math
        a = i * (math.pi / 4)
        px = int(center[0] + math.cos(a) * 10)
        py = int(center[1] + math.sin(a) * 10)
        pygame.draw.circle(surf, accent, (px, py), 6)
    pygame.draw.circle(surf, (255, 220, 120), center, 7)
    # Eyes on the flower center.
    _draw_eyes(surf, cx, S - 40, 3, 2, white=(60, 40, 20), pupil=(255, 240, 200))


def _draw_voltalon(surf, S, body, accent, glow):
    cx = S // 2
    dark = _darken(body, 0.5)
    # Lightning shed from wings.
    _draw_lightning(surf, cx - 20, S - 18, 4, glow)
    _draw_lightning(surf, cx + 20, S - 18, 4, glow)
    # Wings.
    pygame.draw.polygon(surf, accent, [
        (cx - 6, S - 32), (cx - 26, S - 44), (cx - 22, S - 28), (cx - 4, S - 26)])
    pygame.draw.polygon(surf, accent, [
        (cx + 6, S - 32), (cx + 26, S - 44), (cx + 22, S - 28), (cx + 4, S - 26)])
    # Strong legs with claws.
    for lx in (cx - 8, cx + 4):
        pygame.draw.rect(surf, dark, (lx, S - 16, 7, 14))
        for i in range(3):
            pygame.draw.polygon(surf, (250, 240, 180),
                                [(lx + i * 2, S - 2), (lx + i * 2 + 1, S + 1), (lx + i * 2 + 2, S - 2)])
    # Tail.
    pygame.draw.polygon(surf, body,
                        [(cx - 14, S - 22), (cx - 26, S - 14), (cx - 12, S - 18)])
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 14, S - 32, 28, 20))
    # Head with snout.
    pygame.draw.circle(surf, body, (cx + 12, S - 36), 10)
    pygame.draw.polygon(surf, body,
                        [(cx + 18, S - 38), (cx + 28, S - 36), (cx + 18, S - 34)])
    # Crest horns.
    pygame.draw.polygon(surf, dark,
                        [(cx + 8, S - 44), (cx + 6, S - 50), (cx + 12, S - 44)])
    # Eye.
    pygame.draw.circle(surf, (255, 255, 255), (cx + 12, S - 38), 3)
    pygame.draw.circle(surf, dark, (cx + 13, S - 38), 1)


def _draw_generic_fire(surf, S, body, accent, glow):
    """Fire-type fallback: bipedal lizard with flame tail."""
    cx = S // 2
    dark = _darken(body, 0.55)
    # Tail flame.
    _draw_flame(surf, cx + 14, S - 22, 3, accent, glow)
    # Legs.
    pygame.draw.rect(surf, dark, (cx - 7, S - 16, 5, 10))
    pygame.draw.rect(surf, dark, (cx + 3, S - 16, 5, 10)
)
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 12, S - 28, 24, 18))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 6, S - 22, 12, 8))
    # Neck + head.
    pygame.draw.rect(surf, body, (cx - 3, S - 34, 6, 8))
    pygame.draw.circle(surf, body, (cx, S - 38), 9)
    # Snout.
    pygame.draw.ellipse(surf, body, (cx + 4, S - 40, 8, 6))
    # Ears (flame-like).
    pygame.draw.polygon(surf, accent, [(cx - 5, S - 46), (cx - 8, S - 52), (cx - 2, S - 47)])
    pygame.draw.polygon(surf, accent, [(cx + 5, S - 46), (cx + 8, S - 52), (cx + 2, S - 47)])
    _draw_eyes(surf, cx, S - 40, 3, 2)
    # Mouth.
    pygame.draw.line(surf, dark, (cx + 5, S - 36), (cx + 10, S - 36), 1)


def _draw_generic_water(surf, S, body, accent, glow):
    """Water-type fallback: fish with fins and tail."""
    cx = S // 2
    dark = _darken(body, 0.55)
    # Tail fin.
    pygame.draw.polygon(surf, accent, [(cx - 16, S - 22), (cx - 26, S - 30), (cx - 26, S - 14)])
    # Body (teardrop shape).
    pygame.draw.ellipse(surf, body, (cx - 14, S - 30, 28, 18))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 8, S - 22, 16, 8))
    # Dorsal fin.
    pygame.draw.polygon(surf, dark, [(cx - 4, S - 30), (cx + 2, S - 38), (cx + 6, S - 30)])
    # Side fin.
    pygame.draw.ellipse(surf, dark, (cx - 2, S - 18, 10, 5))
    # Head.
    pygame.draw.circle(surf, body, (cx + 12, S - 24), 9)
    # Snout.
    pygame.draw.ellipse(surf, body, (cx + 16, S - 26, 8, 6))
    # Eye.
    _draw_eyes(surf, cx + 12, S - 26, 3, 2)
    # Bubbles.
    pygame.draw.circle(surf, accent, (cx + 22, S - 36), 3, 1)
    pygame.draw.circle(surf, accent, (cx + 26, S - 42), 2, 1)


def _draw_generic_nature(surf, S, body, accent, glow):
    """Nature-type fallback: quadruped with leaf adornments."""
    cx = S // 2
    dark = _darken(body, 0.55)
    # Legs.
    for lx in (cx - 12, cx - 2, cx + 6, cx + 14):
        pygame.draw.rect(surf, dark, (lx, S - 18, 5, 12))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 16, S - 30, 32, 18))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 10, S - 22, 20, 8))
    # Leaf on back.
    pygame.draw.polygon(surf, dark, [(cx - 6, S - 30), (cx, S - 40), (cx + 6, S - 30)])
    pygame.draw.line(surf, accent, (cx, S - 30), (cx, S - 38), 1)
    # Head.
    pygame.draw.circle(surf, body, (cx + 16, S - 30), 9)
    # Snout.
    pygame.draw.ellipse(surf, body, (cx + 20, S - 32, 8, 6))
    # Ears (leaf-shaped).
    pygame.draw.polygon(surf, dark, [(cx + 12, S - 38), (cx + 10, S - 44), (cx + 16, S - 39)])
    pygame.draw.polygon(surf, dark, [(cx + 20, S - 38), (cx + 22, S - 44), (cx + 16, S - 39)])
    _draw_eyes(surf, cx + 16, S - 32, 3, 2)
    # Nostril.
    pygame.draw.circle(surf, dark, (cx + 24, S - 31), 1)


def _draw_generic_electric(surf, S, body, accent, glow):
    """Electric-type fallback: mouse-like creature with spark cheeks."""
    cx = S // 2
    dark = _darken(body, 0.5)
    # Tail with lightning bolt tip.
    pygame.draw.lines(surf, dark, False, [(cx - 10, S - 22), (cx - 18, S - 16), (cx - 22, S - 10)], 2)
    _draw_lightning(surf, cx - 22, S - 10, 3, glow)
    # Legs.
    pygame.draw.rect(surf, dark, (cx - 6, S - 14, 4, 8))
    pygame.draw.rect(surf, dark, (cx + 2, S - 14, 4, 8)
)
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 10, S - 26, 20, 16))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 6, S - 20, 12, 8))
    # Ears (pointed).
    pygame.draw.polygon(surf, body, [(cx - 6, S - 34), (cx - 10, S - 44), (cx - 2, S - 36)])
    pygame.draw.polygon(surf, body, [(cx + 6, S - 34), (cx + 10, S - 44), (cx + 2, S - 36)])
    pygame.draw.polygon(surf, dark, [(cx - 6, S - 34), (cx - 8, S - 40), (cx - 4, S - 36)])
    pygame.draw.polygon(surf, dark, [(cx + 6, S - 34), (cx + 8, S - 40), (cx + 4, S - 36)])
    # Head.
    pygame.draw.circle(surf, body, (cx, S - 30), 9)
    # Cheek sparks.
    pygame.draw.circle(surf, glow, (cx - 7, S - 28), 3)
    pygame.draw.circle(surf, glow, (cx + 7, S - 28), 3)
    _draw_eyes(surf, cx, S - 32, 3, 2)
    # Nose.
    pygame.draw.circle(surf, dark, (cx, S - 26), 1)


def _draw_generic_earth(surf, S, body, accent, glow):
    """Earth-type fallback: bulky quadruped with rocky back plates."""
    cx = S // 2
    dark = _darken(body, 0.5)
    stone = (130, 120, 110)
    # Thick legs.
    for lx in (cx - 14, cx - 2, cx + 8, cx + 16):
        pygame.draw.rect(surf, dark, (lx, S - 18, 7, 14))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 18, S - 32, 36, 20))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 12, S - 22, 24, 8))
    # Rocky back plates.
    for i, px in enumerate((cx - 12, cx - 4, cx + 4, cx + 12)):
        r = 6 - abs(i - 1)
        pygame.draw.circle(surf, stone, (px, S - 32), max(3, r))
        pygame.draw.circle(surf, _darken(stone, 0.7), (px, S - 32), max(3, r), 1)
    # Head.
    pygame.draw.circle(surf, body, (cx - 16, S - 30), 9)
    # Snout.
    pygame.draw.ellipse(surf, body, (cx - 24, S - 30, 10, 7))
    _draw_eyes(surf, cx - 16, S - 32, 3, 2)
    # Horn.
    pygame.draw.polygon(surf, stone, [(cx - 18, S - 38), (cx - 16, S - 44), (cx - 14, S - 38)])
    # Nostril.
    pygame.draw.circle(surf, dark, (cx - 20, S - 29), 1)


def _draw_generic_dark(surf, S, body, accent, glow):
    """Dark-type fallback: shadowy creature with wispy tendrils."""
    cx = S // 2
    dark = _darken(body, 0.4)
    # Wispy aura.
    _soft_disc(surf, (cx, S - 24), 22, accent, alpha=40)
    # Tendrils below.
    for tx in (cx - 10, cx - 3, cx + 4, cx + 10):
        pygame.draw.lines(surf, dark, False,
                          [(tx, S - 14), (tx - 3, S - 8), (tx + 2, S - 4)], 2)
    # Body (irregular blob — not a perfect circle).
    for ox, oy, r in ((-7, 0, 9), (7, 0, 9), (0, -5, 10), (-3, 6, 8), (4, 6, 8)):
        pygame.draw.circle(surf, body, (cx + ox, S - 24 + oy), r)
    # Head.
    pygame.draw.circle(surf, body, (cx, S - 34), 9)
    # Pointed ears.
    pygame.draw.polygon(surf, dark, [(cx - 6, S - 40), (cx - 10, S - 48), (cx - 2, S - 42)])
    pygame.draw.polygon(surf, dark, [(cx + 6, S - 40), (cx + 10, S - 48), (cx + 2, S - 42)])
    # Glowing eyes (no pupils — shadowy).
    pygame.draw.circle(surf, glow, (cx - 4, S - 36), 3)
    pygame.draw.circle(surf, glow, (cx + 4, S - 36), 3)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 4, S - 36), 1)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 4, S - 36), 1)


def _draw_generic_normal(surf, S, body, accent, glow):
    """Normal-type fallback: small furry mammal."""
    cx = S // 2
    dark = _darken(body, 0.6)
    # Legs.
    pygame.draw.rect(surf, dark, (cx - 8, S - 16, 5, 10))
    pygame.draw.rect(surf, dark, (cx + 3, S - 16, 5, 10)
)
    # Tail.
    pygame.draw.ellipse(surf, accent, (cx + 12, S - 22, 12, 6))
    # Body.
    pygame.draw.ellipse(surf, body, (cx - 12, S - 28, 24, 18))
    # Belly.
    pygame.draw.ellipse(surf, accent, (cx - 6, S - 22, 12, 8))
    # Head.
    pygame.draw.circle(surf, body, (cx, S - 36), 10)
    # Round ears.
    pygame.draw.circle(surf, body, (cx - 9, S - 42), 5)
    pygame.draw.circle(surf, body, (cx + 9, S - 42), 5)
    pygame.draw.circle(surf, dark, (cx - 9, S - 42), 2)
    pygame.draw.circle(surf, dark, (cx + 9, S - 42), 2)
    _draw_eyes(surf, cx, S - 38, 4, 3)
    # Nose.
    pygame.draw.circle(surf, dark, (cx, S - 32), 2)
    # Whiskers.
    pygame.draw.line(surf, dark, (cx - 4, S - 32), (cx - 12, S - 31), 1)
    pygame.draw.line(surf, dark, (cx + 4, S - 32), (cx + 12, S - 31), 1)


#: Species registry key (lowercase) -> dedicated draw function.
_DRAWERS: Dict[str, _DrawFn] = {
    "emberling": _draw_emberling,
    "pyroclaw": _draw_pyroclaw,
    "infernosaur": _draw_infernosaur,
    "aquapup": _draw_aquapup,
    "tsunamut": _draw_tsunamut,
    "leviathore": _draw_leviathore,
    "stormwing": _draw_stormwing,
    "rockbash": _draw_rockbash,
    "seedkit": _draw_seedkit,
    "chaospuff": _draw_chaospuff,
    "thornbloom": _draw_thornbloom,
    "voltalon": _draw_voltalon,
}

#: Element -> fallback draw function for species without a dedicated drawer.
_ELEMENT_DRAWERS: Dict[str, _DrawFn] = {
    "fire": _draw_generic_fire,
    "water": _draw_generic_water,
    "nature": _draw_generic_nature,
    "electric": _draw_generic_electric,
    "earth": _draw_generic_earth,
    "dark": _draw_generic_dark,
    "normal": _draw_generic_normal,
}


# ---------------------------------------------------------------------------
# Cache + public API
# ---------------------------------------------------------------------------

#: species_key -> base sprite (facing right).
_CACHE: Dict[str, pygame.Surface] = {}

#: "species_key|facing" -> battle sprite (optionally flipped / scaled).
_BATTLE_CACHE: Dict[str, pygame.Surface] = {}


def _palette_for(element: str) -> Tuple[_RGB, _RGB, _RGB]:
    """Return the (body, accent, glow) triple for an element."""
    return _ELEMENT_PALETTE.get(element, _ELEMENT_PALETTE["normal"])


def _size_for(stage: str) -> int:
    """Return the canvas size for an evolution stage."""
    return _STAGE_SIZE.get(stage, _DEFAULT_SIZE)


def _load_png_sprite(species: Digimon) -> pygame.Surface | None:
    """Attempt to load a PNG sprite for *species*.

    Returns the loaded surface (with per-pixel alpha) or ``None`` if the
    file is missing or cannot be decoded. Under pygbag/WASM the browser's
    native PNG decoder handles the load; on desktop without SDL2_image the
    call raises and ``None`` is returned so the caller falls back to
    procedural drawing.
    """
    if _FORCE_PROCEDURAL:
        return None
    stage_num = _STAGE_NUM.get(species.stage)
    if stage_num is None:
        return None
    path = os.path.join(_SPRITE_DIR, f"{species.key}_{stage_num}.png")
    if not os.path.exists(path):
        print(f"[sprite] PNG not found: {path}  (cwd={os.getcwd()})", flush=True)
        return None
    try:
        surf = pygame.image.load(path)
    except Exception as exc:
        print(f"[sprite] PNG load failed: {path} -> {exc}", flush=True)
        return None
    try:
        surf = surf.convert_alpha()
    except Exception:
        pass
    print(f"[sprite] PNG loaded OK: {path} {surf.get_size()}", flush=True)
    return surf


def _build_sprite(species: Digimon) -> pygame.Surface:
    """Build (but not cache) the base sprite surface for a species.

    Tries the PNG asset first; if that fails, falls back to the procedural
    drawer so rendering never crashes.
    """
    png = _load_png_sprite(species)
    if png is not None:
        return png
    S = _size_for(species.stage)
    body, accent, glow = _palette_for(species.element)
    surf = pygame.Surface((S, S), pygame.SRCALPHA)
    drawer = _DRAWERS.get(species.key)
    if drawer is None:
        drawer = _ELEMENT_DRAWERS.get(species.element, _draw_generic_normal)
    drawer(surf, S, body, accent, glow)
    return surf


def get_sprite(name: str) -> pygame.Surface:
    """Return the cached base sprite for a species (facing right).

    Args:
        name: Species display name or lowercase registry key.

    Returns:
        A transparent ``SRCALPHA`` surface with the creature drawn on it.
        Unknown species return a generic elemental blob.
    """
    key = name.strip().lower()
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    try:
        species = get_digimon(key)
    except KeyError:
        species = None

    if species is None:
        S = _DEFAULT_SIZE
        body, accent, glow = _ELEMENT_PALETTE["normal"]
        surf = pygame.Surface((S, S), pygame.SRCALPHA)
        _draw_generic_normal(surf, S, body, accent, glow)
    else:
        surf = _build_sprite(species)

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
        # Return a distinct copy so callers can scale freely without
        # mutating the shared base sprite in the cache.
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
