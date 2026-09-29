"""Tests for the frame-based animation system (core/animator.py).

Tests force the procedural sprite rendering path so they are deterministic
regardless of whether SDL2_image / PNG support is available on the host.
"""

import pygame

from core import sprite_factory
from core.animator import (
    Animator,
    AnimationState,
    get_frames,
    clear_cache,
    _FRAME_COUNTS,
    _FRAME_DURATIONS,
    _LOOPS,
)


def setup_module(module):
    """pygame.draw needs pygame to be initialized before use."""
    pygame.init()
    sprite_factory._FORCE_PROCEDURAL = True


def teardown_module(module):
    sprite_factory._FORCE_PROCEDURAL = False
    pygame.quit()


class TestFrameGeneration:
    def test_idle_frames_generated(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.IDLE)
        assert len(frames) == _FRAME_COUNTS[AnimationState.IDLE]
        for f in frames:
            assert isinstance(f, pygame.Surface)
            assert f.get_size()[0] > 0
            assert f.get_size()[1] > 0

    def test_attack_frames_generated(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.ATTACK)
        assert len(frames) == _FRAME_COUNTS[AnimationState.ATTACK]

    def test_hurt_frames_generated(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("aquapup", "right", AnimationState.HURT)
        assert len(frames) == _FRAME_COUNTS[AnimationState.HURT]

    def test_faint_frames_generated(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("stormwing", "right", AnimationState.FAINT)
        assert len(frames) == _FRAME_COUNTS[AnimationState.FAINT]

    def test_walk_frames_generated(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("rockbash", "right", AnimationState.WALK)
        assert len(frames) == _FRAME_COUNTS[AnimationState.WALK]

    def test_frames_are_non_blank(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.IDLE)
        for f in frames:
            drawn = any(
                f.get_at((x, y))[3] != 0
                for x in range(0, f.get_width(), 4)
                for y in range(0, f.get_height(), 4)
            )
            assert drawn, "animation frame is blank"

    def test_frames_have_transparent_background(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.IDLE)
        for f in frames:
            assert f.get_flags() & pygame.SRCALPHA

    def test_frames_cached(self):
        clear_cache()
        sprite_factory.clear_cache()
        a = get_frames("emberling", "right", AnimationState.IDLE)
        b = get_frames("emberling", "right", AnimationState.IDLE)
        assert a is b

    def test_left_facing_frames_differ_from_right(self):
        clear_cache()
        sprite_factory.clear_cache()
        right = get_frames("emberling", "right", AnimationState.IDLE)
        left = get_frames("emberling", "left", AnimationState.IDLE)
        assert len(right) == len(left)
        # Frames should differ because the base sprite is flipped.
        same = all(
            right[0].get_at((x, y)) == left[0].get_at((x, y))
            for x in range(0, right[0].get_width(), 4)
            for y in range(0, right[0].get_height(), 4)
        )
        assert not same, "left-facing frames identical to right-facing"


class TestAnimatorBasics:
    def test_default_state_is_idle(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        assert anim.state == AnimationState.IDLE

    def test_default_facing_is_right(self):
        anim = Animator("emberling")
        assert anim.facing == "right"

    def test_current_frame_returns_surface(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        frame = anim.current_frame
        assert isinstance(frame, pygame.Surface)
        assert frame.get_size()[0] > 0

    def test_frame_size_property(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        w, h = anim.frame_size
        assert w > 0 and h > 0


class TestAnimatorStateTransitions:
    def test_play_changes_state(self):
        anim = Animator("emberling")
        anim.play(AnimationState.ATTACK)
        assert anim.state == AnimationState.ATTACK

    def test_play_resets_timer(self):
        anim = Animator("emberling")
        anim.update(1.0)
        anim.play(AnimationState.HURT)
        # After play(), the timer is reset so finished is False.
        assert not anim.finished

    def test_play_same_state_no_restart(self):
        anim = Animator("emberling")
        anim.update(0.5)
        timer_before = anim._time
        anim.play(AnimationState.IDLE)
        assert anim._time == timer_before

    def test_set_facing_resets_timer(self):
        anim = Animator("emberling", facing="right")
        anim.update(1.0)
        anim.set_facing("left")
        assert anim.facing == "left"
        assert anim._time == 0.0

    def test_set_facing_same_no_reset(self):
        anim = Animator("emberling", facing="right")
        anim.update(1.0)
        timer_before = anim._time
        anim.set_facing("right")
        assert anim._time == timer_before


class TestAnimatorPlayback:
    def test_update_advances_timer(self):
        anim = Animator("emberling")
        anim.update(0.1)
        assert anim._time == pytest_approx(0.1)

    def test_idle_loops_indefinitely(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        duration = _FRAME_DURATIONS[AnimationState.IDLE] * _FRAME_COUNTS[AnimationState.IDLE]
        anim.update(duration + 1.0)
        assert not anim.finished

    def test_attack_finishes(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.ATTACK)
        duration = _FRAME_DURATIONS[AnimationState.ATTACK] * _FRAME_COUNTS[AnimationState.ATTACK]
        anim.update(duration + 0.01)
        assert anim.finished

    def test_hurt_finishes(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.HURT)
        duration = _FRAME_DURATIONS[AnimationState.HURT] * _FRAME_COUNTS[AnimationState.HURT]
        anim.update(duration + 0.01)
        assert anim.finished

    def test_faint_finishes(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.FAINT)
        duration = _FRAME_DURATIONS[AnimationState.FAINT] * _FRAME_COUNTS[AnimationState.FAINT]
        anim.update(duration + 0.01)
        assert anim.finished

    def test_finished_holds_last_frame(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.ATTACK)
        duration = _FRAME_DURATIONS[AnimationState.ATTACK] * _FRAME_COUNTS[AnimationState.ATTACK]
        anim.update(duration + 0.01)
        last_frame = get_frames("emberling", "right", AnimationState.ATTACK)[-1]
        assert anim.current_frame is last_frame

    def test_update_after_finished_is_noop(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.ATTACK)
        duration = _FRAME_DURATIONS[AnimationState.ATTACK] * _FRAME_COUNTS[AnimationState.ATTACK]
        anim.update(duration + 0.01)
        time_after_finish = anim._time
        anim.update(1.0)
        assert anim._time == time_after_finish

    def test_frame_advances_with_time(self):
        clear_cache()
        sprite_factory.clear_cache()
        anim = Animator("emberling")
        anim.play(AnimationState.ATTACK)
        frame0 = anim.current_frame
        anim.update(_FRAME_DURATIONS[AnimationState.ATTACK] + 0.01)
        frame1 = anim.current_frame
        assert frame0 is not frame1


class TestAnimatorFrameContent:
    def test_idle_frames_differ_in_position(self):
        """Idle bob frames should not all be pixel-identical."""
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.IDLE)
        f0 = frames[0]
        f1 = frames[1]
        same = all(
            f0.get_at((x, y)) == f1.get_at((x, y))
            for x in range(0, f0.get_width(), 3)
            for y in range(0, f0.get_height(), 3)
        )
        assert not same, "idle frames 0 and 1 are identical (no bob)"

    def test_attack_frames_differ_in_position(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.ATTACK)
        f0 = frames[0]
        f2 = frames[2]
        same = all(
            f0.get_at((x, y)) == f2.get_at((x, y))
            for x in range(0, f0.get_width(), 3)
            for y in range(0, f0.get_height(), 3)
        )
        assert not same, "attack frames 0 and 2 are identical (no lunge)"

    def test_hurt_frames_have_red_tint(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.HURT)
        tinted = frames[0]
        idle = get_frames("emberling", "right", AnimationState.IDLE)[0]
        # The hurt frame should differ from the idle frame (red tint + shake).
        same = all(
            tinted.get_at((x, y)) == idle.get_at((x, y))
            for x in range(0, tinted.get_width(), 3)
            for y in range(0, tinted.get_height(), 3)
        )
        assert not same, "hurt frame identical to idle (no tint/shake)"

    def test_faint_last_frame_is_faded(self):
        clear_cache()
        sprite_factory.clear_cache()
        frames = get_frames("emberling", "right", AnimationState.FAINT)
        first = frames[0]
        last = frames[-1]
        # The last frame should be more transparent than the first.
        first_alpha = sum(
            first.get_at((x, y))[3]
            for x in range(0, first.get_width(), 4)
            for y in range(0, first.get_height(), 4)
            if first.get_at((x, y))[3] > 0
        )
        last_alpha = sum(
            last.get_at((x, y))[3]
            for x in range(0, last.get_width(), 4)
            for y in range(0, last.get_height(), 4)
            if last.get_at((x, y))[3] > 0
        )
        assert last_alpha < first_alpha, "faint last frame not more faded than first"


def pytest_approx(expected, rel=1e-6):
    """Tiny float approx helper to avoid importing pytest just for this."""
    class _Approx:
        def __init__(self, expected, rel):
            self.expected = expected
            self.rel = rel
        def __eq__(self, other):
            return abs(other - self.expected) < self.rel * max(abs(self.expected), 1.0)
        def __repr__(self):
            return f"approx({self.expected})"
    return _Approx(expected, rel)
