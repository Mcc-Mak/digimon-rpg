"""World exploration scene — tile-based overworld with random encounters.

The player explores a grid-based map using arrow keys or WASD. Stepping on
grass tiles can trigger wild Digimon encounters via the encounter system.
An NPC provides dialogue when interacted with.

All rendering uses ``pygame.draw`` primitives — no external image assets.

WASM safety: no blocking I/O, no subprocess, no file reads. The tile map is
defined in-code as a list of strings. Safe under pygbag/WASM.
"""

from __future__ import annotations

import random
from typing import Any, List, Optional, Tuple

import pygame

import config
from core.scene import Scene
from systems.encounter import check_encounter, ZONES

# Tile size in pixels.
_TILE_SIZE: int = 32

# Map legend characters.
_TILE_GRASS: str = "."      # low grass — low encounter rate
_TILE_TALL_GRASS: str = ";"  # tall grass — higher encounter rate
_TILE_PATH: str = " "        # path — no encounters, walkable
_TILE_WATER: str = "~"       # water — impassable
_TILE_TREE: str = "T"        # tree — impassable
_TILE_NPC: str = "N"         # NPC — walkable adjacent, triggers dialogue

# Colors per tile type.
_TILE_COLORS = {
    _TILE_GRASS: (34, 120, 34),
    _TILE_TALL_GRASS: (20, 90, 20),
    _TILE_PATH: (180, 170, 140),
    _TILE_WATER: (40, 80, 180),
    _TILE_TREE: (16, 60, 16),
    _TILE_NPC: (200, 200, 200),
}

# 20 wide x 15 tall tile map.
_TILE_MAP: List[str] = [
    "TTTTTTTTTTTTTTTTTTTT",
    "T..................T",
    "T..;;;;............T",
    "T..;;;;....TTTT.....T",
    "T.........T....T...T",
    "T...N.....T....T...T",
    "T.........T....T...T",
    "T.........TTTTTT...T",
    "T..................T",
    "T...;;;;...........T",
    "T...;;;;...........T",
    "T..........~~~~~~..T",
    "T..........~~~~~~..T",
    "T..................T",
    "TTTTTTTTTTTTTTTTTTTT",
]

# Zone assignment for encounters.
_ZONE_ID: str = "verdant_plains"

# Terrain mapping for encounter rates.
_TERRAIN_MAP = {
    _TILE_GRASS: "low_grass",
    _TILE_TALL_GRASS: "tall_grass",
    _TILE_WATER: "water_edge",
}

# Player movement keys.
_MOVE_KEYS = {
    pygame.K_UP: (0, -1),
    pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d: (1, 0),
}

# Player move cooldown in seconds (prevents ultra-fast grid traversal).
_MOVE_COOLDOWN: float = 0.15

# NPC dialogue lines.
_NPC_DIALOGUE = [
    "Welcome to the Verdant Plains!",
    "Wild Digimon lurk in the grass.",
    "Train your partner and evolve!",
]


def _is_walkable(tile_char: str) -> bool:
    """Return True if the player can stand on a tile of this type."""
    return tile_char in (_TILE_GRASS, _TALL_GRASS, _TILE_PATH, _TILE_NPC)


class WorldScene(Scene):
    """Tile-based overworld with player movement and random encounters."""

    def __init__(self, game: Any) -> None:
        super().__init__(game)
        self._map_w: int = len(_TILE_MAP[0])
        self._map_h: int = len(_TILE_MAP)
        self._player_x: int = 5
        self._player_y: int = 5
        self._move_timer: float = 0.0
        self._encounter_rng: random.Random = random.Random()
        self._dialogue_text: str = ""
        self._dialogue_timer: float = 0.0
        self._font: pygame.font.Font = pygame.font.Font(None, 24)
        self._small_font: pygame.font.Font = pygame.font.Font(None, 18)

    def enter(self) -> None:
        self._move_timer = 0.0

    def exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in _MOVE_KEYS and self._move_timer <= 0:
                dx, dy = _MOVE_KEYS[event.key]
                self._try_move(dx, dy)
            elif event.key == pygame.K_e:
                self._try_interact()

    def update(self, dt: float) -> None:
        if self._move_timer > 0:
            self._move_timer -= dt
        if self._dialogue_timer > 0:
            self._dialogue_timer -= dt

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(config.BLACK)
        self._draw_tiles(screen)
        self._draw_player(screen)
        self._draw_hud(screen)
        if self._dialogue_timer > 0:
            self._draw_dialogue(screen)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_tile(self, mx: int, my: int) -> str:
        if 0 <= my < self._map_h and 0 <= mx < self._map_w:
            return _TILE_MAP[my][mx]
        return _TILE_TREE

    def _try_move(self, dx: int, dy: int) -> None:
        nx = self._player_x + dx
        ny = self._player_y + dy
        tile = self._get_tile(nx, ny)
        if not _is_walkable(tile):
            return
        self._player_x = nx
        self._player_y = ny
        self._move_timer = _MOVE_COOLDOWN
        self._check_encounter(tile)

    def _check_encounter(self, tile: str) -> None:
        terrain = _TERRAIN_MAP.get(tile)
        if terrain is None:
            return
        encounter = check_encounter(_ZONE_ID, terrain, self._encounter_rng)
        if encounter is not None:
            self._start_battle(encounter)

    def _start_battle(self, encounter: dict) -> None:
        from scenes.battle_scene import BattleScene

        player_species = getattr(self.game, "_player_species", "emberling")
        player_level = getattr(self.game, "_player_level", 5)

        battle_scene = BattleScene(
            game=self.game,
            player_species=player_species,
            player_level=player_level,
            enemy_species=str(encounter["species"]),
            enemy_level=int(encounter["level"]),
        )
        self.game.push(battle_scene)

    def _try_interact(self) -> None:
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx = self._player_x + dx
            ny = self._player_y + dy
            if self._get_tile(nx, ny) == _TILE_NPC:
                self._dialogue_text = _NPC_DIALOGUE[
                    self._encounter_rng.randint(0, len(_NPC_DIALOGUE) - 1)
                ]
                self._dialogue_timer = 3.0
                return

    def _draw_tiles(self, screen: pygame.Surface) -> None:
        for row_idx, row in enumerate(_TILE_MAP):
            for col_idx, char in enumerate(row):
                color = _TILE_COLORS.get(char, config.GRAY)
                rect = pygame.Rect(
                    col_idx * _TILE_SIZE,
                    row_idx * _TILE_SIZE,
                    _TILE_SIZE,
                    _TILE_SIZE,
                )
                pygame.draw.rect(screen, color, rect)
                if char == _TILE_TREE:
                    trunk = pygame.Rect(
                        col_idx * _TILE_SIZE + 12,
                        row_idx * _TILE_SIZE + 20,
                        8,
                        12,
                    )
                    pygame.draw.rect(screen, (80, 50, 20), trunk)
                elif char == _TILE_NPC:
                    cx = col_idx * _TILE_SIZE + _TILE_SIZE // 2
                    cy = row_idx * _TILE_SIZE + _TILE_SIZE // 2
                    pygame.draw.circle(screen, config.BLUE, (cx, cy), 10)
                    pygame.draw.circle(screen, config.WHITE, (cx, cy - 12), 6)

    def _draw_player(self, screen: pygame.Surface) -> None:
        px = self._player_x * _TILE_SIZE + _TILE_SIZE // 2
        py = self._player_y * _TILE_SIZE + _TILE_SIZE // 2
        pygame.draw.circle(screen, config.RED, (px, py), 11)
        pygame.draw.circle(screen, config.WHITE, (px, py - 12), 6)

    def _draw_hud(self, screen: pygame.Surface) -> None:
        zone_name = ZONES[_ZONE_ID].name
        hud = self._small_font.render(
            f"{zone_name}  |  Arrow keys/WASD: move  |  E: interact",
            True,
            config.WHITE,
        )
        screen.blit(hud, (4, config.SCREEN_HEIGHT - 20))

    def _draw_dialogue(self, screen: pygame.Surface) -> None:
        box_h = 60
        box = pygame.Rect(10, config.SCREEN_HEIGHT - box_h - 25, config.SCREEN_WIDTH - 20, box_h)
        pygame.draw.rect(screen, (20, 20, 40), box)
        pygame.draw.rect(screen, config.WHITE, box, 2)
        text = self._font.render(self._dialogue_text, True, config.WHITE)
        screen.blit(text, (box.x + 12, box.y + 18))
