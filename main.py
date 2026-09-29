"""Entry point for digimon-rpg — a pygame-based RPG that runs in the browser via pygbag.

This module owns the application lifecycle: pygame initialization, the
async game loop, event dispatch, scene updates/rendering, and display flip.

The game loop is an ``async def main()`` coroutine. A single
``await asyncio.sleep(0)`` per frame yields control back to the browser event
loop, which is **required** for the pygbag/WebAssembly runtime. The same code
runs locally as a normal desktop window via ``python main.py``.

WASM safety:
    * No blocking file I/O at runtime.
    * No ``subprocess`` / ``os.system``.
    * No ``ctypes`` / native modules.
    * No ``threading`` / ``multiprocessing``.
    * No ``time.sleep`` — the loop yields via ``asyncio.sleep``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import pygame

import config
from core.scene_manager import SceneManager
from scenes.title_scene import TitleScene
from systems.save_system import SaveData


class Game(SceneManager):
    """Central game-state object shared across all scenes.

    Extends :class:`SceneManager` so scenes can call ``self.game.push()``,
    ``self.game.pop()``, etc. directly, while also carrying transient state
    that scenes use to communicate (player species/level/xp, encounter data,
    battle results, save data).
    """

    def __init__(self) -> None:
        """Initialize a fresh scene manager with default player state."""
        super().__init__()
        self._player_species: str = "emberling"
        self._player_level: int = 5
        self._player_xp: int = 0
        self.save_data: Optional[SaveData] = None
        self.pending_encounter: Optional[dict] = None
        self.battle_result: Any = None
        self.player_world_pos: tuple = (10, 7)


async def main() -> None:
    """Initialize the display, run the async game loop, and clean up."""
    pygame.init()

    # Display setup using the shared config dimensions.
    screen: pygame.Surface = pygame.display.set_mode(config.SCREEN_SIZE)
    pygame.display.set_caption(config.WINDOW_CAPTION)

    # Clock targets FPS; each tick returns milliseconds since last frame.
    clock: pygame.time.Clock = pygame.time.Clock()

    # Build the game state and push the title scene as the initial state.
    game: Game = Game()
    game.push(TitleScene(game=game))

    running: bool = True

    try:
        while running:
            # dt in seconds since the last frame, clamped to FPS target.
            dt: float = clock.tick(config.FPS) / 1000.0

            # Process all pending pygame events.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    game.handle_event(event)

            # Update the active scene, then render it.
            game.update(dt)
            game.draw(screen)

            pygame.display.flip()

            # CRITICAL: yield to the browser event loop. This is required for
            # pygbag/WASM to remain responsive; it is a cheap no-op on desktop.
            await asyncio.sleep(0)
    except KeyboardInterrupt:
        # Allow Ctrl+C to quit a local session cleanly.
        running = False
    finally:
        pygame.quit()


# Standard pygbag boilerplate — works both locally and under pygbag/WASM.
if __name__ == "__main__":
    asyncio.run(main())
