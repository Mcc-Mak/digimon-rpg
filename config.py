"""Configuration constants for the digimon-rpg game.

This module centralizes all configuration values used across the game:
screen dimensions, color palette, frame-rate target, and game metadata.
All values are module-level constants so they can be imported and referenced
anywhere without duplicating magic numbers.

WASM safety: this module performs no blocking I/O, no subprocess calls, and
no runtime system calls. It is safe to import under pygbag/WASM.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Screen / display
# ---------------------------------------------------------------------------

#: Width of the game window in pixels.
SCREEN_WIDTH: int = 640

#: Height of the game window in pixels.
SCREEN_HEIGHT: int = 480

#: Tuple describing the full screen size: (width, height).
SCREEN_SIZE: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)

#: Target frames-per-second for the game loop.
FPS: int = 60

#: Number of milliseconds in a single target frame (16.7ms at 60 FPS).
FRAME_MS: int = 1000 // FPS

# ---------------------------------------------------------------------------
# Game metadata
# ---------------------------------------------------------------------------

#: Displayed title of the game on the title screen.
GAME_TITLE: str = "DIGIMON RPG"

#: Short version string shown to the player.
GAME_VERSION: str = "0.1.0"

#: Window caption shown by the OS/browser.
WINDOW_CAPTION: str = f"{GAME_TITLE} v{GAME_VERSION}"

#: Author / studio credit string.
GAME_AUTHOR: str = "digimon-rpg team"

# ---------------------------------------------------------------------------
# Base color palette
# ---------------------------------------------------------------------------

#: RGB value for pure black.
BLACK: tuple[int, int, int] = (0, 0, 0)

#: RGB value for pure white.
WHITE: tuple[int, int, int] = (255, 255, 255)

#: RGB value for pure red.
RED: tuple[int, int, int] = (255, 0, 0)

#: RGB value for pure green.
GREEN: tuple[int, int, int] = (0, 255, 0)

#: RGB value for pure blue.
BLUE: tuple[int, int, int] = (0, 0, 255)

#: RGB value for yellow.
YELLOW: tuple[int, int, int] = (255, 255, 0)

#: RGB value for cyan.
CYAN: tuple[int, int, int] = (0, 255, 255)

#: RGB value for magenta.
MAGENTA: tuple[int, int, int] = (255, 0, 255)

#: RGB value for a medium gray.
GRAY: tuple[int, int, int] = (128, 128, 128)

#: RGB value for a dark gray.
DARK_GRAY: tuple[int, int, int] = (64, 64, 64)

#: RGB value for a light gray.
LIGHT_GRAY: tuple[int, int, int] = (192, 192, 192)

#: RGB value for orange.
ORANGE: tuple[int, int, int] = (255, 165, 0)

#: RGB value for purple.
PURPLE: tuple[int, int, int] = (128, 0, 128)

# ---------------------------------------------------------------------------
# Game-specific colors
# ---------------------------------------------------------------------------

#: Color used for the main title text.
TITLE_COLOR: tuple[int, int, int] = YELLOW

#: Color used for the title text drop-shadow outline.
TITLE_SHADOW_COLOR: tuple[int, int, int] = (80, 60, 0)

#: Color used for interactive prompt text (e.g., "Press ENTER").
PROMPT_COLOR: tuple[int, int, int] = WHITE

#: Background color for the title screen.
TITLE_BACKGROUND: tuple[int, int, int] = (10, 10, 30)

#: Secondary background color used for gradients / stripe animation.
TITLE_BACKGROUND_ALT: tuple[int, int, int] = (20, 40, 80)

#: Color used for side info / version text on the title screen.
SUBTITLE_COLOR: tuple[int, int, int] = LIGHT_GRAY

#: Generic background color used across most scenes.
BACKGROUND: tuple[int, int, int] = BLACK

#: Generic color for a primary "button" / action highlight.
PRIMARY_COLOR: tuple[int, int, int] = CYAN

#: Generic color for a secondary "cancel" action.
SECONDARY_COLOR: tuple[int, int, int] = GRAY