"""Scene base class for digimon-rpg.

A ``Scene`` represents one discrete state of the game (title screen, world map,
battle, menu, ...). Scenes are managed by a stack-based ``SceneManager``. Each
scene receives a reference to the central ``Game``/application object in its
constructor so it can trigger scene transitions and share state.

Subclasses override the lifecycle and per-frame hooks as needed:

* ``enter`` / ``exit``   - lifecycle transition points
* ``handle_event``       - pygame event dispatch
* ``update``             - per-frame logic, ``dt`` in seconds
* ``draw``               - render to the provided screen surface

WASM safety: this module does no I/O or system calls. Safe under pygbag/WASM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    # Imported lazily only for static type checking to avoid a hard
    # circular import between the engine and the application object.
    pass


class Scene:
    """Abstract base class for all game scenes."""

    def __init__(self, game: Any) -> None:
        """Initialize the scene with a reference to the game application.

        Args:
            game: The central application/game object. Provides access to the
                ``SceneManager`` and shared game state.
        """
        self.game = game

    def enter(self) -> None:
        """Called when this scene becomes active (top of the scene stack).

        Subclasses may override to run setup logic or begin side effects.
        """
        pass

    def exit(self) -> None:
        """Called when this scene is deactivated or removed.

        Subclasses may override to tear down resources or stop effects.
        """
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a single pygame event.

        Args:
            event: The pygame event to process (key press, mouse click, etc.).
        """
        pass

    def update(self, dt: float) -> None:
        """Update the scene's state for the current frame.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the scene onto the given screen surface.

        Args:
            screen: The pygame surface (display/backbuffer) to draw onto.
        """
        pass

    def __repr__(self) -> str:
        """Return a readable representation of this scene for debugging."""
        return f"{self.__class__.__name__}(game={self.game})"