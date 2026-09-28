"""SceneManager — stack-based scene management for digimon-rpg.

The ``SceneManager`` maintains a stack of ``Scene`` instances. This allows
overlay scenes (dialogue boxes, menus, settings) to be pushed on top of the
current scene without destroying it, and popped off when finished.

The active scene is always the top of the stack. ``update``, ``draw``, and
``handle_event`` are delegated to the current (top) scene.

WASM safety: this module is pure Python state management; no I/O, threads,
or system calls. Safe under pygbag/WASM.
"""

from __future__ import annotations

from typing import Optional

import pygame

from core.scene import Scene


class SceneManager:
    """Manages a stack of scenes and delegates lifecycle calls to the top one."""

    def __init__(self) -> None:
        """Initialize an empty scene stack."""
        self._stack: list[Scene] = []

    def push(self, scene: Scene) -> None:
        """Push a new scene onto the stack, making it active.

        The current top scene (if any) has ``exit()`` called, then the new
        scene is appended and its ``enter()`` called.

        Args:
            scene: The scene to make active.
        """
        if self._stack:
            self._stack[-1].exit()
        self._stack.append(scene)
        scene.enter()

    def pop(self) -> Optional[Scene]:
        """Remove and return the top scene.

        The removed scene has ``exit()`` called. If a scene remains below it,
        that scene's ``enter()`` is called (becoming active again).

        Returns:
            The removed scene, or ``None`` if the stack was empty.
        """
        if not self._stack:
            return None
        scene: Scene = self._stack.pop()
        scene.exit()
        if self._stack:
            self._stack[-1].enter()
        return scene

    def replace(self, scene: Scene) -> None:
        """Replace the current top scene with a new one.

        The current top scene (if any) has ``exit()`` called and is swapped
        out for the new scene in place (its position preserved), then the new
        scene's ``enter()`` is called.

        Args:
            scene: The scene that should replace the current active scene.
        """
        if self._stack:
            self._stack[-1].exit()
            self._stack[-1] = scene
        else:
            self._stack.append(scene)
        scene.enter()

    @property
    def current(self) -> Optional[Scene]:
        """Return the active (top) scene, or ``None`` if the stack is empty."""
        return self._stack[-1] if self._stack else None

    def update(self, dt: float) -> None:
        """Delegate the update tick to the current top scene.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        if self._stack:
            self._stack[-1].update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Delegate rendering to the current top scene.

        Args:
            screen: The pygame surface to draw onto.
        """
        if self._stack:
            self._stack[-1].draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Pass a pygame event to the current top scene.

        Args:
            event: The pygame event to process.
        """
        if self._stack:
            self._stack[-1].handle_event(event)

    def clear(self) -> None:
        """Remove all scenes from the stack, calling ``exit()`` on each.

        Useful for a hard reset (e.g., returning to the title screen).
        """
        while self._stack:
            self.pop()

    def __len__(self) -> int:
        """Return the number of scenes currently on the stack."""
        return len(self._stack)

    def __repr__(self) -> str:
        """Return a readable representation of the scene stack for debugging."""
        return f"SceneManager(stack={self._stack})"