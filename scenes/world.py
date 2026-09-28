"""World exploration scene — tile-based overworld for digimon-rpg.

A grid-based overworld (20×15 tiles, 32 px each = 640×480) where the player
walks around, triggers random encounters on grass tiles, reads a sign, and
transitions to the battle scene when an encounter fires.

All graphics use ``pygame.draw`` primitives and ``pygame.font`` — no external
images or audio. The scene is fully async-compatible (no blocking operations).

WASM safety: no subprocess, no blocking I/O, no threading, no time.sleep.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

import pygame

import config
from core.scene import Scene
from systems.encounter import check_encounter, ZONES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TILE_SIZE: int = 32
_MAP_W: int = 20
_MAP_H: int = 15

# Tile characters
_CHAR_TREE: str = "X"
_CHAR_GRASS: str = "G"
_CHAR_TALL: str = "T"
_CHAR_PATH: str = "P"
_CHAR_WATER: str = "W"
_CHAR_WATER_EDGE: str = "E"
_CHAR_SIGN: str = "S"

# Tile colors
_COLOR_GRASS = (74, 160, 74)
_COLOR_TALL = (34, 110, 40)
_COLOR_PATH = (200, 190, 150)
_COLOR_WATER = (60, 120, 200)
_COLOR_TREE = (20, 80, 20)
_COLOR_WATER_EDGE = (140, 170, 95)
_COLOR_SIGN_BG = (200, 190, 150)

# Encounter terrain mapping
_TERRAIN_ENCOUNTER = {
    _CHAR_GRASS: "low_grass",
    _CHAR_TALL: "tall_grass",
    _CHAR_WATER_EDGE: "water_edge",
}

# Map data (20 wide × 15 tall)
_MAP_DATA: List[str] = [
    "XXXXXXXXXXXXXXXXXXXX",
    "XTTTGGGGGGGGGGGGGGGX",
    "XTTTGGGGGGGGGGGGGGGX",
    "XGGGGGGGGGGGGGGGGGGX",
    "XGGGGGPPPPPPGGGGGGGX",
    "XGGGGGPGGGGPGGGGGGGX",
    "XGGGGGPGGGGPGGGGGGGX",
    "XGGSGGPGGGGPGGGGGGGX",
    "XGGGGGPGGGGPPPPPGGGX",
    "XGGGGGPGGGGGGGGPGGGX",
    "XGGGGGPGGGGGGGGPGGGX",
    "XWWWWWPGGGGGGGGPGGGX",
    "XWWWWWPPPPPPPPPPGGGX",
    "XEEEEEGGGGGGGGGGGGGX",
    "XXXXXXXXXXXXXXXXXXXX",
]

_ZONE_ID: str = "verdant_plains"
_MOVE_COOLDOWN: float = 0.15
_ENCOUNTER_COOLDOWN: float = 0.5

_SIGN_TEXT: str = (
    "WELCOME TO VERDANT PLAINS!  Wild Digimon roam the grass here. "
    "Tread carefully — taller grass means more encounters. Press ENTER to continue."
)


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap *text* into lines that fit within *max_width* pixels."""
    words: List[str] = text.split()
    lines: List[str] = []
    current: str = ""
    for word in words:
        test: str = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class WorldScene(Scene):
    """Tile-based overworld scene with movement, encounters, and dialogue."""

    def __init__(self, game: object) -> None:
        super().__init__(game)
        self._rng: random.Random = random.Random()
        self._player_x: int = 10
        self._player_y: int = 6
        self._move_cooldown: float = 0.0
        self._encounter_cooldown: float = 0.0
        self._step_count: int = 0
        self._dialogue_active: bool = False
        self._font_lg = pygame.font.Font(None, 36)
        self._font_md = pygame.font.Font(None, 24)
        self._font_sm = pygame.font.Font(None, 18)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def enter(self) -> None:
        """Called when the world becomes active (including after battle)."""
        # Restore position from shared state.
        pos = getattr(self.game, "player_world_pos", None)
        if pos is not None and isinstance(pos, tuple) and len(pos) == 2:
            self._player_x = int(pos[0])
            self._player_y = int(pos[1])

        # If returning from battle, process and clear the result.
        if getattr(self.game, "battle_result", None) is not None:
            self.game.battle_result = None
            self._encounter_cooldown = _ENCOUNTER_COOLDOWN

    def exit(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Map helpers
    # ------------------------------------------------------------------

    def _tile_at(self, x: int, y: int) -> str:
        if 0 <= y < len(_MAP_DATA) and 0 <= x < len(_MAP_DATA[y]):
            return _MAP_DATA[y][x]
        return _CHAR_TREE

    def _is_walkable(self, x: int, y: int) -> bool:
        char = self._tile_at(x, y)
        return char in (
            _CHAR_GRASS,
            _CHAR_TALL,
            _CHAR_PATH,
            _CHAR_WATER_EDGE,
            _CHAR_SIGN,
        )

    def _is_encounter_tile(self, x: int, y: int) -> bool:
        return self._tile_at(x, y) in _TERRAIN_ENCOUNTER

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        # Dialogue mode
        if self._dialogue_active:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._dialogue_active = False
            return

        # ESC → return to title
        if event.key == pygame.K_ESCAPE:
            self._go_title()
            return

        # Sign interaction
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self._near_sign():
                self._dialogue_active = True
            return

        # Movement (only if cooldown elapsed)
        if self._move_cooldown > 0:
            return

        dx: int = 0
        dy: int = 0
        if event.key in (pygame.K_UP, pygame.K_w):
            dy = -1
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            dy = 1
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            dx = -1
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            dx = 1

        if dx != 0 or dy != 0:
            self._try_move(dx, dy)

    def _try_move(self, dx: int, dy: int) -> None:
        nx = self._player_x + dx
        ny = self._player_y + dy
        if not self._is_walkable(nx, ny):
            return
        self._player_x = nx
        self._player_y = ny
        self._move_cooldown = _MOVE_COOLDOWN
        self._step_count += 1
        # Save position for battle return.
        self.game.player_world_pos = (self._player_x, self._player_y)

        # Encounter check
        if self._encounter_cooldown > 0:
            return
        if not self._is_encounter_tile(self._player_x, self._player_y):
            return
        char = self._tile_at(self._player_x, self._player_y)
        terrain = _TERRAIN_ENCOUNTER.get(char)
        if terrain is None:
            return
        encounter = check_encounter(_ZONE_ID, terrain, self._rng)
        if encounter is not None:
            self._start_battle(encounter)

    def _near_sign(self) -> bool:
        """Return True if the player is standing on or adjacent to the sign."""
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if self._tile_at(self._player_x + dx, self._player_y + dy) == _CHAR_SIGN:
                    return True
        return False

    def _start_battle(self, encounter: dict) -> None:
        """Store encounter data and push the battle scene."""
        self.game.pending_encounter = encounter
        from scenes.battle import BattleScene
        self.game.push(BattleScene(game=self.game))

    def _go_title(self) -> None:
        from scenes.title_scene import TitleScene
        self.game.clear()
        self.game.push(TitleScene(game=self.game))

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._move_cooldown > 0:
            self._move_cooldown -= dt
        if self._encounter_cooldown > 0:
            self._encounter_cooldown -= dt

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(config.BLACK)
        self._draw_map(screen)
        self._draw_player(screen)
        self._draw_hud(screen)
        if self._dialogue_active:
            self._draw_dialogue(screen)

    def _draw_map(self, screen: pygame.Surface) -> None:
        for row_idx, row in enumerate(_MAP_DATA):
            for col_idx, char in enumerate(row):
                x = col_idx * _TILE_SIZE
                y = row_idx * _TILE_SIZE
                self._draw_tile(screen, char, x, y)

    def _draw_tile(self, screen: pygame.Surface, char: str, x: int, y: int) -> None:
        rect = pygame.Rect(x, y, _TILE_SIZE, _TILE_SIZE)

        if char == _CHAR_TREE:
            pygame.draw.rect(screen, _COLOR_TREE, rect)
            # Canopy circle
            pygame.draw.circle(screen, (30, 100, 30), (x + 16, y + 14), 12)
            pygame.draw.circle(screen, (20, 80, 20), (x + 16, y + 14), 12, 2)
            # Trunk
            pygame.draw.rect(screen, (100, 70, 40), (x + 13, y + 22, 6, 8))
        elif char == _CHAR_GRASS:
            pygame.draw.rect(screen, _COLOR_GRASS, rect)
        elif char == _CHAR_TALL:
            pygame.draw.rect(screen, _COLOR_TALL, rect)
            # Blade lines
            for bx in (8, 16, 24):
                pygame.draw.line(screen, (20, 90, 20), (x + bx, y + 24), (x + bx, y + 12), 2)
        elif char == _CHAR_PATH:
            pygame.draw.rect(screen, _COLOR_PATH, rect)
        elif char == _CHAR_WATER:
            pygame.draw.rect(screen, _COLOR_WATER, rect)
            pygame.draw.arc(screen, (120, 180, 240), (x + 4, y + 8, 24, 16), 0, 3.14, 2)
        elif char == _CHAR_WATER_EDGE:
            pygame.draw.rect(screen, _COLOR_WATER_EDGE, rect)
        elif char == _CHAR_SIGN:
            pygame.draw.rect(screen, _COLOR_SIGN_BG, rect)
            # Sign post
            pygame.draw.rect(screen, (120, 90, 50), (x + 14, y + 16, 4, 14))
            pygame.draw.rect(screen, (220, 200, 120), (x + 6, y + 6, 20, 12))
            pygame.draw.rect(screen, (140, 110, 60), (x + 6, y + 6, 20, 12), 2)
        else:
            pygame.draw.rect(screen, config.DARK_GRAY, rect)

    def _draw_player(self, screen: pygame.Surface) -> None:
        cx = self._player_x * _TILE_SIZE + _TILE_SIZE // 2
        cy = self._player_y * _TILE_SIZE + _TILE_SIZE // 2
        pygame.draw.circle(screen, config.WHITE, (cx, cy), 13)
        pygame.draw.circle(screen, config.RED, (cx, cy), 11)
        pygame.draw.circle(screen, config.WHITE, (cx, cy), 11, 2)

    def _draw_hud(self, screen: pygame.Surface) -> None:
        zone_name = ZONES.get(_ZONE_ID)
        zone_label = zone_name.name if zone_name else _ZONE_ID
        hud_y = config.SCREEN_HEIGHT - 24
        pygame.draw.rect(screen, (0, 0, 0), (0, hud_y, config.SCREEN_WIDTH, 24))
        pygame.draw.line(screen, config.WHITE, (0, hud_y), (config.SCREEN_WIDTH, hud_y), 1)
        text = f"{zone_label}  |  Steps: {self._step_count}  |  Arrows/WASD: Move  ENTER: Interact  ESC: Title"
        surf = self._font_sm.render(text, True, config.WHITE)
        screen.blit(surf, (8, hud_y + 4))

    def _draw_dialogue(self, screen: pygame.Surface) -> None:
        box_w = config.SCREEN_WIDTH - 40
        box_h = 120
        box_x = 20
        box_y = config.SCREEN_HEIGHT - box_h - 30
        overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (box_x, box_y))
        pygame.draw.rect(screen, config.WHITE, (box_x, box_y, box_w, box_h), 2)

        lines = _wrap_text(_SIGN_TEXT, self._font_md, box_w - 30)
        ly = box_y + 12
        for line in lines:
            surf = self._font_md.render(line, True, config.WHITE)
            screen.blit(surf, (box_x + 15, ly))
            ly += 22

        prompt = self._font_sm.render("Press ENTER to close", True, config.YELLOW)
        screen.blit(prompt, (box_x + box_w - prompt.get_width() - 12, box_y + box_h - 20))
