"""Battle scene — turn-based combat UI.

Displays player Digimon vs wild Digimon with HP bars, a move selection menu,
and a scrolling battle log. Integrates with ``systems.battle.BattleEngine``
for all combat logic. On win, awards XP and returns to the world scene; on
loss, returns to the title scene.

All rendering uses ``pygame.draw`` and ``pygame.font`` — no external assets.

WASM safety: no blocking I/O, no subprocess. Safe under pygbag/WASM.
"""

from __future__ import annotations

import random
from typing import Any, List, Optional

import pygame

import config
from core.scene import Scene
from core.sprite_factory import get_battle_sprite
from systems.battle import BattleEngine, BattleDigimon, BattleResult
from systems.progression import check_level_up, xp_to_reach_level


class BattleScene(Scene):
    """Turn-based battle UI driven by :class:`BattleEngine`."""

    def __init__(
        self,
        game: Any,
        player_species: str,
        player_level: int,
        enemy_species: str,
        enemy_level: int,
    ) -> None:
        super().__init__(game)

        self._engine: BattleEngine = BattleEngine(
            player_digimon=BattleDigimon.from_species(player_species, player_level),
            enemy_digimon=BattleDigimon.from_species(enemy_species, enemy_level),
            is_wild=True,
        )

        self._player_species: str = player_species
        self._selected_move: int = 0
        self._battle_log: List[str] = ["A wild Digimon appeared!"]
        self._max_log_lines: int = 5
        self._flash_timer: float = 0.0
        self._flash_color: tuple = (0, 0, 0)
        self._result: Optional[str] = None
        self._result_timer: float = 0.0
        self._awaiting_enemy: bool = False
        self._enemy_delay: float = 0.0

        self._font_lg: pygame.font.Font = pygame.font.Font(None, 28)
        self._font_md: pygame.font.Font = pygame.font.Font(None, 22)
        self._font_sm: pygame.font.Font = pygame.font.Font(None, 18)

        # Cache for level-scaled combatant sprites so we don't re-scale every
        # frame. Keyed by (species, facing, scale_bucket).
        self._combatant_cache: dict = {}

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._result is not None:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE
            ):
                self._finish_battle()
            return

        if self._awaiting_enemy:
            return

        if event.type == pygame.KEYDOWN:
            moves = self._engine.player.moves
            if event.key == pygame.K_UP:
                self._selected_move = (self._selected_move - 1) % max(len(moves), 1)
            elif event.key == pygame.K_DOWN:
                self._selected_move = (self._selected_move + 1) % max(len(moves), 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._player_action(self._selected_move)
            elif event.key == pygame.K_f:
                self._player_flee()

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt

        if self._awaiting_enemy:
            self._enemy_delay -= dt
            if self._enemy_delay <= 0:
                self._awaiting_enemy = False
                self._do_enemy_turn()

        if self._result is not None:
            self._result_timer -= dt

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((15, 15, 25))

        if self._flash_timer > 0:
            overlay = pygame.Surface(config.SCREEN_SIZE)
            overlay.fill(self._flash_color)
            overlay.set_alpha(80)
            screen.blit(overlay, (0, 0))

        self._draw_platforms(screen)
        self._draw_combatants(screen)
        self._draw_hp_bars(screen)
        self._draw_move_menu(screen)
        self._draw_log(screen)

        if self._result is not None:
            self._draw_result(screen)

    # ------------------------------------------------------------------
    # Combat actions
    # ------------------------------------------------------------------

    def _player_action(self, move_index: int) -> None:
        result = self._engine.player_attack(move_index)
        self._add_log(str(result["message"]))
        if result.get("effect") == "damage":
            self._trigger_flash((255, 80, 80))

        winner = self._engine.check_battle_end()
        if winner is not None:
            self._end_battle(winner)
            return

        self._awaiting_enemy = True
        self._enemy_delay = 0.8

    def _player_flee(self) -> None:
        result = self._engine.attempt_flee()
        self._add_log(str(result["message"]))
        if result.get("success"):
            self._result = "fled"
            self._result_timer = 1.5

    def _do_enemy_turn(self) -> None:
        result = self._engine.enemy_turn()
        self._add_log(str(result["message"]))
        if result.get("effect") == "damage":
            self._trigger_flash((80, 80, 255))

        winner = self._engine.check_battle_end()
        if winner is not None:
            self._end_battle(winner)

    def _end_battle(self, winner: str) -> None:
        self._result = winner
        self._result_timer = 2.0
        if winner == "player":
            xp = self._engine.award_xp()
            self._add_log(f"Victory! Gained {xp} XP!")
            self._award_xp(xp)
        elif winner == "enemy":
            self._add_log("Defeat...")

    def _award_xp(self, xp: int) -> None:
        player_level = getattr(self.game, "_player_level", 5)
        total_xp = getattr(self.game, "_player_xp", 0) + xp
        setattr(self.game, "_player_xp", total_xp)

        can_level, new_level, remaining = check_level_up(player_level, total_xp)
        if can_level:
            setattr(self.game, "_player_level", new_level)
            setattr(self.game, "_player_xp", remaining)
            self._add_log(f"Level up! Now level {new_level}!")

    def _finish_battle(self) -> None:
        if self._result == "enemy":
            from scenes.title_scene import TitleScene
            self.game.clear()
            self.game.push(TitleScene(game=self.game))
        else:
            self.game.pop()

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _trigger_flash(self, color: tuple) -> None:
        self._flash_timer = 0.15
        self._flash_color = color

    def _add_log(self, message: str) -> None:
        self._battle_log.append(message)
        if len(self._battle_log) > self._max_log_lines:
            self._battle_log = self._battle_log[-self._max_log_lines:]

    def _draw_platforms(self, screen: pygame.Surface) -> None:
        pw, ph = 120, 16
        pygame.draw.ellipse(screen, (50, 50, 60), (60, 280, pw, ph))
        pygame.draw.ellipse(screen, (50, 50, 60), (460, 180, pw, ph))

    def _draw_combatants(self, screen: pygame.Surface) -> None:
        p = self._engine.player
        e = self._engine.enemy

        # Player on the left platform (feet rest near platform center y=288),
        # enemy on the right platform (y=188), flipped to face the player.
        self._blit_combatant(screen, p.species_name, 120, 290, "right", p.level)
        self._blit_combatant(screen, e.species_name, 520, 190, "left", e.level)

    def _blit_combatant(
        self,
        screen: pygame.Surface,
        species: str,
        x: int,
        bottom_y: int,
        facing: str,
        level: int,
    ) -> None:
        """Draw a grounded creature sprite with a soft drop shadow.

        The sprite is scaled up slightly with level (clamped) so higher-level
        combatants read as heftier. Scaled sprites are cached per battle.
        """
        scale = max(1.0, min(1.35, 1.0 + (max(1, level) - 1) * 0.015))
        # Bucket the scale to the nearest 5% so the cache stays tiny.
        bucket = round(scale * 20) / 20
        cache_key = (species, facing, bucket)
        scaled = self._combatant_cache.get(cache_key)
        if scaled is None:
            base = get_battle_sprite(species, facing=facing)
            w = max(1, int(base.get_width() * bucket))
            h = max(1, int(base.get_height() * bucket))
            scaled = pygame.transform.scale(base, (w, h))
            self._combatant_cache[cache_key] = scaled

        # Soft drop shadow on the platform.
        sw = scaled.get_width()
        shadow_w = max(16, sw // 2)
        shadow_h = max(5, shadow_w // 5)
        shadow = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110),
                            (0, 0, shadow_w * 2, shadow_h * 2))
        screen.blit(shadow, (x - shadow_w, bottom_y - shadow_h))

        rect = scaled.get_rect(midbottom=(x, bottom_y))
        screen.blit(scaled, rect)

    def _draw_hp_bars(self, screen: pygame.Surface) -> None:
        p = self._engine.player
        e = self._engine.enemy

        self._draw_hp_bar(screen, 20, 230, p.nickname, p.level, p.current_hp, p.max_hp, p.current_mp, p.max_mp)
        self._draw_hp_bar(screen, 360, 130, e.nickname, e.level, e.current_hp, e.max_hp, e.current_mp, e.max_mp)

    def _draw_hp_bar(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        name: str,
        level: int,
        hp: int,
        max_hp: int,
        mp: int,
        max_mp: int,
    ) -> None:
        name_surf = self._font_md.render(f"{name} Lv{level}", True, config.WHITE)
        screen.blit(name_surf, (x, y))

        bar_w, bar_h = 180, 12
        hp_rect = pygame.Rect(x, y + 26, bar_w, bar_h)
        pygame.draw.rect(screen, (60, 60, 60), hp_rect)
        hp_fill = int(bar_w * max(0, hp) / max(1, max_hp))
        hp_color = config.GREEN if hp > max_hp * 0.5 else (config.YELLOW if hp > max_hp * 0.25 else config.RED)
        pygame.draw.rect(screen, hp_color, (x, y + 26, hp_fill, bar_h))
        pygame.draw.rect(screen, config.WHITE, hp_rect, 1)

        hp_text = self._font_sm.render(f"HP {hp}/{max_hp}", True, config.WHITE)
        screen.blit(hp_text, (x + bar_w + 6, y + 25))

        mp_rect = pygame.Rect(x, y + 42, bar_w, 6)
        pygame.draw.rect(screen, (60, 60, 60), mp_rect)
        mp_fill = int(bar_w * max(0, mp) / max(1, max_mp))
        pygame.draw.rect(screen, config.BLUE, (x, y + 42, mp_fill, 6))

    def _draw_move_menu(self, screen: pygame.Surface) -> None:
        if self._result is not None:
            return

        box = pygame.Rect(0, config.SCREEN_HEIGHT - 140, config.SCREEN_WIDTH, 140)
        pygame.draw.rect(screen, (20, 20, 35), box)
        pygame.draw.rect(screen, config.WHITE, box, 2)

        moves = self._engine.player.moves
        title = self._font_md.render("Moves (Up/Down + Enter | F=Flee):", True, config.CYAN)
        screen.blit(title, (box.x + 10, box.y + 6))

        for i, move in enumerate(moves):
            y = box.y + 32 + i * 22
            prefix = ">" if i == self._selected_move else " "
            text = f"{prefix} {move.name}  (Pow:{move.power} MP:{move.mp_cost} {move.move_type})"
            color = config.YELLOW if i == self._selected_move else config.WHITE
            surf = self._font_sm.render(text, True, color)
            screen.blit(surf, (box.x + 16, y))

    def _draw_log(self, screen: pygame.Surface) -> None:
        box = pygame.Rect(200, config.SCREEN_HEIGHT - 140, config.SCREEN_WIDTH - 200, 100)
        for i, line in enumerate(self._battle_log):
            surf = self._font_sm.render(line, True, config.LIGHT_GRAY)
            screen.blit(surf, (box.x + 8, box.y + 6 + i * 18))

    def _draw_result(self, screen: pygame.Surface) -> None:
        if self._result == "player":
            text, color = "VICTORY!", config.YELLOW
        elif self._result == "fled":
            text, color = "Got away safely!", config.WHITE
        else:
            text, color = "DEFEAT...", config.RED

        overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        surf = self._font_lg.render(text, True, color)
        x = (config.SCREEN_WIDTH - surf.get_width()) // 2
        y = config.SCREEN_HEIGHT // 2 - 20
        screen.blit(surf, (x, y))

        hint = self._font_sm.render("Press ENTER to continue", True, config.WHITE)
        screen.blit(hint, ((config.SCREEN_WIDTH - hint.get_width()) // 2, y + 36))
