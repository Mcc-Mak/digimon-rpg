"""Title screen scene for digimon-rpg.

Presents the game title, a blinking "Press ENTER to Start" prompt, and an
animated geometric/pattern background. Rendered entirely with ``pygame.draw``
primitives so no external image assets are required (WASM-safe).

Pressing ENTER currently prints a message to the console — a placeholder for
the eventual transition to the next scene (character creation / world map).
"""

from __future__ import annotations

import math
import random
from typing import Any

import pygame

import config
from core.scene import Scene

# How long (seconds) the prompt stays visible before blinking off, and the
# animation period helpers. Blink period in seconds.
_PROMPT_BLINK_PERIOD: float = 0.6

# Stripe animation travel period in seconds.
_STRIPE_PERIOD: float = 2.0

# Number of diagonal stripes used in the background pattern.
_NUM_STRIPES: int = 18


class TitleScene(Scene):
    """The title screen shown when the game first launches."""

    def __init__(self, game: Any) -> None:
        """Initialize the title scene state.

        Args:
            game: The central game/application object (used to trigger
                scene transitions later).
        """
        super().__init__(game)
        self._elapsed: float = 0.0

        # Pre-render the static text surfaces once (cheap, avoids per-frame
        # font rendering) for the title and subtitle.
        self._title_font = pygame.font.Font(None, 72)
        self._prompt_font = pygame.font.Font(None, 36)
        self._subtitle_font = pygame.font.Font(None, 20)

        self._title_surface = self._title_font.render(
            config.GAME_TITLE, True, config.TITLE_COLOR
        )
        self._title_shadow = self._title_font.render(
            config.GAME_TITLE, True, config.TITLE_SHADOW_COLOR
        )

        self._subtitle_surface = self._subtitle_font.render(
            f"v{config.GAME_VERSION}", True, config.SUBTITLE_COLOR
        )

        # Seed a small random generator used only for the decorative pattern
        # (deterministic enough; no blocking I/O involved).
        self._rng = random.Random(42)
        self._title_rect = self._title_surface.get_rect()

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def enter(self) -> None:
        """Reset animation timers when the scene becomes active."""
        self._elapsed = 0.0

    def exit(self) -> None:
        """No special teardown needed for the title scene."""
        pass

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Respond to key presses — ENTER starts the game placeholder.

        Args:
            event: The pygame event to process.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # FIXME: Replace with a real scene transition once the next
                # scene (world / character creation) is implemented.
                print("Enter pressed — starting game (next scene not built yet).")

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance animation timers.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        self._elapsed += dt

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        """Render the animated title background, title, and prompt.

        Args:
            screen: The pygame surface to draw onto.
        """
        screen.fill(config.TITLE_BACKGROUND)

        self._draw_animated_background(screen)
        self._draw_title(screen)
        self._draw_version(screen)

        if self._prompt_visible():
            self._draw_prompt(screen)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prompt_visible(self) -> bool:
        """Return whether the blinking prompt should be shown right now.

        Returns:
            ``True`` when the prompt is on, ``False`` while it is blinked off.
        """
        phase = (self._elapsed % (_PROMPT_BLINK_PERIOD * 2)) / _PROMPT_BLINK_PERIOD
        # Phase in [0,1) => brightness ramps; simplest is a square wave.
        return phase < 1.0

    def _draw_animated_background(self, screen: pygame.Surface) -> None:
        """Draw the animated diagonal-stripe geometric background.

        The stripes translate over time (driven by ``_elapsed``) and the color
        shifts with a sine wave to produce a lively cosmic/digital feel. All
        drawing uses ``pygame.draw`` primitives.

        Args:
            screen: The surface to draw the background onto.
        """
        width, height = config.SCREEN_SIZE

        # Slow base color cycle based on elapsed time.
        cycle = (math.sin(self._elapsed * 0.8) + 1.0) / 2.0  # 0..1
        base_r = int(12 + 24 * cycle)
        base_g = int(16 + 40 * cycle)
        base_b = int(40 + 80 * (1.0 - cycle))
        base_color = (base_r, base_g, base_b)
        screen.fill(base_color)

        # Diagonal stripes that scroll horizontally over time.
        stripe_spacing = width // _NUM_STRIPES
        offset = int(self._elapsed * 40.0)

        for i in range(-1, _NUM_STRIPES + 2):
            x0 = (i * stripe_spacing) + offset
            stripe_cycle = (i + self._elapsed * 0.5) % _NUM_STRIPES / _NUM_STRIPES
            r = base_r + int(20 * (1.0 - stripe_cycle))
            g = base_g + int(30 * (1.0 - stripe_cycle))
            b = base_b + int(60 * (1.0 - stripe_cycle))
            stripe_color = (min(255, r), min(255, g), min(255, b))

            # Diagonal band anchored at (x0, 0) sloping down-right.
            pts = [
                (x0, 0),
                (x0 + stripe_spacing, 0),
                (x0 + stripe_spacing + height, height),
                (x0 + height, height),
            ]
            pygame.draw.polygon(screen, stripe_color, pts)

        # A few pulsing accent dots for extra visual interest.
        for dot in range(6):
            px = int((self._rng.randint(0, width)) * (0.25) + 40)
            py = int((self._rng.randint(0, height)) * (0.25) + 40)
            radius = int(2 + (math.sin(self._elapsed * 2 + dot) + 1) * 2)
            pygame.draw.circle(screen, config.CYAN, (px, py), radius)

    def _draw_title(self, screen: pygame.Surface) -> None:
        """Draw the game title with a drop shadow, centered horizontally.

        Args:
            screen: The surface to draw the title onto.
        """
        width = config.SCREEN_WIDTH
        title_w = self._title_surface.get_width()

        x = (width - title_w) // 2
        y = int(config.SCREEN_HEIGHT * 0.22)

        # Drop shadow (offset by 3 pixels).
        screen.blit(self._title_shadow, (x + 3, y + 3))
        screen.blit(self._title_surface, (x, y))

    def _draw_version(self, screen: pygame.Surface) -> None:
        """Draw the version string below the main title.

        Args:
            screen: The surface to draw the version onto.
        """
        width = config.SCREEN_WIDTH
        v_w = self._subtitle_surface.get_width()
        x = (width - v_w) // 2
        y = int(config.SCREEN_HEIGHT * 0.22) + self._title_surface.get_height() + 8
        screen.blit(self._subtitle_surface, (x, y))

    def _draw_prompt(self, screen: pygame.Surface) -> None:
        """Draw the centered 'Press ENTER to Start' prompt near screen bottom.

        Args:
            screen: The surface to draw the prompt onto.
        """
        prompt_text = "Press ENTER to Start"
        prompt_surface = self._prompt_font.render(
            prompt_text, True, config.PROMPT_COLOR
        )

        width, height = config.SCREEN_SIZE
        tw = prompt_surface.get_width()
        th = prompt_surface.get_height()

        x = (width - tw) // 2
        y = int(height * 0.78) - th // 2
        screen.blit(prompt_surface, (x, y))