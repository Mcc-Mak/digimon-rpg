"""Frame-based sprite animation system for digimon-rpg.

Generates animation frames procedurally from a base sprite surface and
cycles through them based on elapsed time. No external image files are
loaded — frames are created by applying pygame transforms (shift, scale,
tint, flip) to the base sprite returned by :mod:`core.sprite_factory`.

Animation states
----------------

* **idle** – gentle vertical bob (breathing / floating).
* **walk** – bouncier vertical bob with a slight forward lean.
* **attack** – forward lunge then recoil.
* **hurt** – red tint flash + horizontal shake.
* **faint** – drop down + fade out.

Frame generation is cached per ``(species_key, facing)`` pair so the
cost is paid once. The :class:`Animator` class tracks state and time,
returning the correct frame on each :meth:`update` call.

WASM safety: only ``pygame.Surface`` / ``pygame.draw`` / ``pygame.transform``
are used. No I/O, no subprocess, no threads.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Dict, List, Tuple

import pygame

from core.wasm_log import browser_log


class AnimationState(Enum):
    """Supported animation states."""
    IDLE = "idle"
    WALK = "walk"
    ATTACK = "attack"
    HURT = "hurt"
    FAINT = "faint"


#: Number of frames per animation state.
_FRAME_COUNTS: Dict[AnimationState, int] = {
    AnimationState.IDLE: 4,
    AnimationState.WALK: 4,
    AnimationState.ATTACK: 4,
    AnimationState.HURT: 4,
    AnimationState.FAINT: 4,
}

#: Seconds per frame for each state (controls playback speed).
_FRAME_DURATIONS: Dict[AnimationState, float] = {
    AnimationState.IDLE: 0.18,
    AnimationState.WALK: 0.10,
    AnimationState.ATTACK: 0.07,
    AnimationState.HURT: 0.06,
    AnimationState.FAINT: 0.12,
}

#: Whether each state loops or plays once and holds the last frame.
_LOOPS: Dict[AnimationState, bool] = {
    AnimationState.IDLE: True,
    AnimationState.WALK: True,
    AnimationState.ATTACK: False,
    AnimationState.HURT: False,
    AnimationState.FAINT: False,
}

#: Extra vertical padding (px) added to animation canvases so shifted
#: sprites are never clipped during bob / lunge.
_PAD = 6

#: Extra horizontal padding (px) for lunge / shake.
_PAD_X = 16


# ---------------------------------------------------------------------------
# Frame generation
# ---------------------------------------------------------------------------

def _new_canvas(w: int, h: int) -> pygame.Surface:
    """Create a transparent canvas of the given size."""
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _blit_centered(canvas: pygame.Surface, sprite: pygame.Surface,
                   dx: int, dy: int) -> None:
    """Blit *sprite* onto *canvas* centered, offset by (dx, dy)."""
    cw, ch = canvas.get_size()
    sw, sh = sprite.get_size()
    x = (cw - sw) // 2 + dx
    y = (ch - sh) // 2 + dy
    canvas.blit(sprite, (x, y))


def _apply_red_tint(sprite: pygame.Surface) -> pygame.Surface:
    """Return a copy of *sprite* with a red damage tint overlay."""
    tinted = sprite.copy()
    overlay = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 40, 40, 120))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return tinted


def _apply_fade(sprite: pygame.Surface, alpha: int) -> pygame.Surface:
    """Return a copy of *sprite* with the given alpha applied uniformly."""
    faded = sprite.copy()
    faded.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    return faded


def _gen_idle_frames(sprite: pygame.Surface, facing: str) -> List[pygame.Surface]:
    """Generate idle animation: gentle vertical bob."""
    sw, sh = sprite.get_size()
    w, h = sw + _PAD_X * 2, sh + _PAD * 2
    # Bob offsets: 0, -2, 0, -1 (subtle breathing)
    offsets = [0, -2, 0, -1]
    frames = []
    for off in offsets:
        canvas = _new_canvas(w, h)
        _blit_centered(canvas, sprite, 0, off)
        frames.append(canvas)
    return frames


def _gen_walk_frames(sprite: pygame.Surface, facing: str) -> List[pygame.Surface]:
    """Generate walk animation: bouncier bob with slight sway."""
    sw, sh = sprite.get_size()
    w, h = sw + _PAD_X * 2, sh + _PAD * 2
    # Bounce: 0, -3, 0, -3 with a 1px sway
    sway_dir = 1 if facing == "right" else -1
    offsets = [(0, 0), (sway_dir, -3), (0, 0), (-sway_dir, -3)]
    frames = []
    for sx, sy in offsets:
        canvas = _new_canvas(w, h)
        _blit_centered(canvas, sprite, sx, sy)
        frames.append(canvas)
    return frames


def _gen_attack_frames(sprite: pygame.Surface, facing: str) -> List[pygame.Surface]:
    """Generate attack animation: forward lunge then recoil."""
    sw, sh = sprite.get_size()
    w, h = sw + _PAD_X * 2, sh + _PAD * 2
    lunge_dir = 1 if facing == "right" else -1
    # Lunge: 0, +8, +12, 0 (dash forward, peak, retreat)
    offsets = [0, lunge_dir * 8, lunge_dir * 12, 0]
    frames = []
    for off in offsets:
        canvas = _new_canvas(w, h)
        _blit_centered(canvas, sprite, off, -1)
        frames.append(canvas)
    return frames


def _gen_hurt_frames(sprite: pygame.Surface, facing: str) -> List[pygame.Surface]:
    """Generate hurt animation: red tint + horizontal shake."""
    sw, sh = sprite.get_size()
    w, h = sw + _PAD_X * 2, sh + _PAD * 2
    tinted = _apply_red_tint(sprite)
    # Shake: -4, +4, -2, 0
    offsets = [-4, 4, -2, 0]
    frames = []
    for i, off in enumerate(offsets):
        canvas = _new_canvas(w, h)
        src = tinted if i < 3 else sprite
        _blit_centered(canvas, src, off, 0)
        frames.append(canvas)
    return frames


def _gen_faint_frames(sprite: pygame.Surface, facing: str) -> List[pygame.Surface]:
    """Generate faint animation: drop down + fade out."""
    sw, sh = sprite.get_size()
    w, h = sw + _PAD_X * 2, sh + _PAD * 2 + 10
    # Drop: 0, +4, +8, +12 with decreasing alpha
    drops = [0, 4, 8, 12]
    alphas = [255, 180, 100, 30]
    frames = []
    for drop, alpha in zip(drops, alphas):
        canvas = _new_canvas(w, h)
        src = _apply_fade(sprite, alpha) if alpha < 255 else sprite
        _blit_centered(canvas, src, 0, drop)
        frames.append(canvas)
    return frames


#: State -> frame generator function.
_GENERATORS = {
    AnimationState.IDLE: _gen_idle_frames,
    AnimationState.WALK: _gen_walk_frames,
    AnimationState.ATTACK: _gen_attack_frames,
    AnimationState.HURT: _gen_hurt_frames,
    AnimationState.FAINT: _gen_faint_frames,
}


# ---------------------------------------------------------------------------
# Frame cache
# ---------------------------------------------------------------------------

#: Key: (species_key, facing, state) -> list of frames.
_FRAME_CACHE: Dict[Tuple[str, str, AnimationState], List[pygame.Surface]] = {}


def get_frames(species_key: str, facing: str = "right",
               state: AnimationState = AnimationState.IDLE) -> List[pygame.Surface]:
    """Return the cached list of animation frames for a species/state.

    Args:
        species_key: Lowercase species name (e.g. ``"emberling"``).
        facing: ``"right"`` or ``"left"``.
        state: The animation state to generate frames for.

    Returns:
        A list of :class:`pygame.Surface` frames. The list has at least
        one frame.
    """
    facing = "left" if facing == "left" else "right"
    cache_key = (species_key, facing, state)
    cached = _FRAME_CACHE.get(cache_key)
    if cached is not None:
        return cached

    browser_log(f"[animator] get_frames: species={species_key} facing={facing} state={state.value}")

    # Import here to avoid circular import at module load time.
    from core.sprite_factory import get_battle_sprite

    base = get_battle_sprite(species_key, facing=facing)
    browser_log(f"[animator] base sprite size={base.get_size()}, generating frames")
    generator = _GENERATORS.get(state, _gen_idle_frames)
    frames = generator(base, facing)
    if not frames:
        frames = [base.copy()]
    browser_log(f"[animator] generated {len(frames)} frames for {species_key}")
    _FRAME_CACHE[cache_key] = frames
    return frames


def clear_cache() -> None:
    """Empty the frame cache. Intended for tests."""
    _FRAME_CACHE.clear()


# ---------------------------------------------------------------------------
# Animator
# ---------------------------------------------------------------------------

class Animator:
    """Drives frame selection for a single animated sprite.

    Tracks the current :class:`AnimationState`, accumulated time, and
    returns the correct frame surface on each :meth:`update` call.

    Usage::

        anim = Animator("emberling", facing="right")
        anim.update(dt)
        screen.blit(anim.current_frame, (x, y))
    """

    def __init__(self, species_key: str, facing: str = "right",
                 start_state: AnimationState = AnimationState.IDLE) -> None:
        self._species_key: str = species_key.strip().lower()
        self._facing: str = "left" if facing == "left" else "right"
        self._state: AnimationState = start_state
        self._time: float = 0.0
        self._finished: bool = False

    @property
    def state(self) -> AnimationState:
        """Current animation state."""
        return self._state

    @property
    def facing(self) -> str:
        """Current facing direction (``"left"`` or ``"right"``)."""
        return self._facing

    @property
    def finished(self) -> bool:
        """True if a non-looping animation has played to completion."""
        return self._finished

    @property
    def current_frame(self) -> pygame.Surface:
        """The surface that should be drawn right now."""
        frames = get_frames(self._species_key, self._facing, self._state)
        if len(frames) == 1:
            return frames[0]
        duration = _FRAME_DURATIONS.get(self._state, 0.15)
        frame_idx = int(self._time / duration) % len(frames)
        if self._finished:
            frame_idx = len(frames) - 1
        return frames[frame_idx]

    @property
    def frame_size(self) -> Tuple[int, int]:
        """Size of the animation canvas (consistent across all frames)."""
        return self.current_frame.get_size()

    def set_facing(self, facing: str) -> None:
        """Change the facing direction. Resets the animation timer."""
        facing = "left" if facing == "left" else "right"
        if facing != self._facing:
            self._facing = facing
            self._time = 0.0
            self._finished = False

    def play(self, state: AnimationState) -> None:
        """Switch to a new animation state, resetting the timer.

        If *state* is the same as the current state and the animation is
        still playing, this is a no-op (avoids restarting a looping idle).
        """
        if state == self._state and not self._finished:
            return
        self._state = state
        self._time = 0.0
        self._finished = False

    def update(self, dt: float) -> None:
        """Advance the animation clock by *dt* seconds."""
        if self._finished:
            return
        self._time += dt
        frames = get_frames(self._species_key, self._facing, self._state)
        duration = _FRAME_DURATIONS.get(self._state, 0.15)
        total = duration * len(frames)
        if not _LOOPS.get(self._state, True) and self._time >= total:
            self._time = total
            self._finished = True


__all__ = [
    "AnimationState",
    "Animator",
    "get_frames",
    "clear_cache",
]
