"""Turn-based battle scene for digimon-rpg.

Integrates ``systems.battle.BattleEngine`` with a full pygame UI: HP/MP bars,
move selection menu, attack animations (shape lunge + screen flash), battle
log, victory rewards (XP, level-up, gold), mid-battle evolution animation,
defeat handling, and flee mechanics.

All graphics use ``pygame.draw`` and ``pygame.font`` — no external assets.
The scene is async-compatible (no blocking operations, timers driven by dt).

WASM safety: no subprocess, no blocking I/O, no threading, no time.sleep.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

import pygame

import config
from core.scene import Scene
from data.digimon_data import Digimon, Move, get_digimon
from systems.battle import BattleDigimon, BattleEngine
from systems.encounter import roll_gold
from systems.progression import (
    calculate_stats_at_level,
    can_evolve,
    check_level_up,
)

# ---------------------------------------------------------------------------
# Phase constants
# ---------------------------------------------------------------------------

PHASE_INTRO: int = 0
PHASE_PLAYER_MENU: int = 1
PHASE_PLAYER_ANIM: int = 2
PHASE_ENEMY_ANIM: int = 3
PHASE_MESSAGE: int = 4
PHASE_VICTORY: int = 5
PHASE_DEFEAT: int = 6
PHASE_EVOLUTION: int = 7
PHASE_FLEE_RESULT: int = 8

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_ELEMENT_COLORS: Dict[str, Tuple[int, int, int]] = {
    "fire": (255, 80, 0),
    "water": (0, 120, 255),
    "nature": (60, 180, 60),
    "electric": (255, 220, 0),
    "earth": (160, 100, 60),
    "dark": (120, 40, 120),
    "normal": (180, 180, 180),
}

_STAGE_RADIUS: Dict[str, int] = {
    "Rookie": 25,
    "Champion": 35,
    "Ultimate": 45,
}

_PLAYER_BASE: Tuple[int, int] = (140, 165)
_ENEMY_BASE: Tuple[int, int] = (500, 95)

_ANIM_DURATION: float = 0.8
_MESSAGE_DURATION: float = 1.2
_INTRO_DURATION: float = 1.5
_EVOLUTION_DURATION: float = 2.5


def _element_color(element: str) -> Tuple[int, int, int]:
    return _ELEMENT_COLORS.get(element, _ELEMENT_COLORS["normal"])


def _stage_radius(stage: str) -> int:
    return _STAGE_RADIUS.get(stage, 25)


def _fwd_factor(progress: float) -> float:
    """Lunge forward factor: 0→1→0 over progress 0→1."""
    if progress < 0.375:
        return progress / 0.375
    elif progress < 0.75:
        return 1.0 - (progress - 0.375) / 0.375
    return 0.0


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    words: List[str] = text.split()
    lines: List[str] = []
    current: str = ""
    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class BattleScene(Scene):
    """Full turn-based battle UI integrated with the BattleEngine."""

    def __init__(self, game: object) -> None:
        super().__init__(game)
        self._rng: random.Random = random.Random()
        self._font_lg = pygame.font.Font(None, 32)
        self._font_md = pygame.font.Font(None, 24)
        self._font_sm = pygame.font.Font(None, 18)
        self._font_xs = pygame.font.Font(None, 16)

        # Engine / combatants (set up in enter())
        self._engine: Optional[BattleEngine] = None
        self._enemy_species_name: str = ""
        self._intro_text: str = ""

        # Phase machine
        self._phase: int = PHASE_INTRO
        self._phase_timer: float = 0.0
        self._phase_duration: float = 0.0

        # Round tracking
        self._turn_order: List[str] = ["player", "enemy"]
        self._player_acted: bool = False
        self._enemy_acted: bool = False
        self._last_result: Optional[Dict[str, Any]] = None
        self._return_to_menu: bool = False

        # Menu
        self._selected: int = 0

        # Animation
        self._anim_side: Optional[str] = None
        self._anim_flash_done: bool = False
        self._flash_alpha: int = 0

        # Flee
        self._flee_success: bool = False
        self._flee_message: str = ""

        # Victory / rewards
        self._reward_processed: bool = False
        self._xp_awarded: int = 0
        self._gold_awarded: int = 0
        self._victory_messages: List[str] = []
        self._pending_evolution: bool = False
        self._evolution_done: bool = False
        self._new_species_def: Optional[Digimon] = None
        self._evolution_message: str = ""

        # Pre-render flash overlay
        self._flash_surf = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def enter(self) -> None:
        encounter = getattr(self.game, "pending_encounter", None) or {
            "species": "seedkit",
            "level": 3,
            "base_xp": 25,
        }
        save = getattr(self.game, "save_data", None)
        if save is None or not save.party:
            # Fallback: create a default emberling at level 5
            from systems.save_system import create_default_save
            save = create_default_save("Player", "emberling")
            save.party[0].level = 5
            self.game.save_data = save

        party_member = save.party[0]

        player_bd = BattleDigimon.from_species(party_member.species_id, party_member.level)
        if party_member.current_hp > 0:
            player_bd.current_hp = min(party_member.current_hp, player_bd.max_hp)
        if party_member.current_mp > 0:
            player_bd.current_mp = min(party_member.current_mp, player_bd.max_mp)
        player_bd.nickname = party_member.nickname or get_digimon(party_member.species_id).name

        enemy_bd = BattleDigimon.from_species(
            encounter["species"],
            encounter["level"],
            base_xp=encounter.get("base_xp", 25),
        )

        self._engine = BattleEngine(player_bd, enemy_bd, rng=self._rng, is_wild=True)
        self._enemy_species_name = encounter["species"]
        enemy_disp = get_digimon(encounter["species"])
        self._intro_text = f"A wild {enemy_disp.name} appeared!"

        self._phase = PHASE_INTRO
        self._phase_duration = _INTRO_DURATION
        self._phase_timer = _INTRO_DURATION

    def exit(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Phase helpers
    # ------------------------------------------------------------------

    def _set_phase(self, phase: int, duration: float) -> None:
        self._phase = phase
        self._phase_duration = duration
        self._phase_timer = duration

    def _start_round(self) -> None:
        self._turn_order = self._engine.determine_turn_order()
        self._player_acted = False
        self._enemy_acted = False
        if self._turn_order[0] == "player":
            self._phase = PHASE_PLAYER_MENU
        else:
            self._begin_enemy_action()

    def _begin_player_action(self, idx: int) -> None:
        engine = self._engine
        move = engine.player.moves[idx]
        if engine.player.current_mp < move.mp_cost:
            self._last_result = {"message": "Not enough MP!"}
            self._return_to_menu = True
            self._set_phase(PHASE_MESSAGE, _MESSAGE_DURATION)
            return
        self._last_result = engine.player_attack(idx)
        self._player_acted = True
        self._anim_side = "player"
        self._anim_flash_done = False
        self._set_phase(PHASE_PLAYER_ANIM, _ANIM_DURATION)

    def _begin_enemy_action(self) -> None:
        self._last_result = self._engine.enemy_turn()
        self._enemy_acted = True
        self._anim_side = "enemy"
        self._anim_flash_done = False
        self._set_phase(PHASE_ENEMY_ANIM, _ANIM_DURATION)

    def _end_anim(self) -> None:
        self._anim_side = None
        self._set_phase(PHASE_MESSAGE, _MESSAGE_DURATION)

    def _advance_from_message(self) -> None:
        if self._return_to_menu:
            self._return_to_menu = False
            self._phase = PHASE_PLAYER_MENU
            return

        winner = self._engine.check_battle_end()
        if winner == "player":
            self._enter_victory()
        elif winner == "enemy":
            self._phase = PHASE_DEFEAT
        else:
            if self._player_acted and not self._enemy_acted:
                self._begin_enemy_action()
            elif self._enemy_acted and not self._player_acted:
                self._phase = PHASE_PLAYER_MENU
            else:
                self._start_round()

    def _try_flee(self) -> None:
        result = self._engine.attempt_flee()
        self._flee_success = bool(result.get("success", False))
        self._flee_message = str(result.get("message", ""))
        self._set_phase(PHASE_FLEE_RESULT, _MESSAGE_DURATION if not self._flee_success else 0.0)

    def _enter_victory(self) -> None:
        self._phase = PHASE_VICTORY
        if not self._reward_processed:
            self._process_rewards()

    def _process_rewards(self) -> None:
        self._reward_processed = True
        party = self.game.save_data.party[0]
        xp = self._engine.award_xp()
        gold = roll_gold("verdant_plains", self._rng)
        self._xp_awarded = xp
        self._gold_awarded = gold
        self._victory_messages.append(f"You won!  XP: {xp}  Gold: {gold}")

        party.xp += xp

        # Level-up check (may chain multiple)
        while True:
            can_lvl, new_level, remaining = check_level_up(party.level, party.xp)
            if not can_lvl:
                break
            old_stats = calculate_stats_at_level(get_digimon(party.species_id), party.level)
            party.level = new_level
            party.xp = remaining
            species_def = get_digimon(party.species_id)
            new_stats = calculate_stats_at_level(species_def, new_level)
            deltas = {k: new_stats[k] - old_stats[k] for k in ("hp", "mp", "attack", "defense", "speed")}
            self._victory_messages.append(
                f"Level up! Now Lv {new_level}!  "
                f"HP+{deltas['hp']} MP+{deltas['mp']} ATK+{deltas['attack']} DEF+{deltas['defense']} SPD+{deltas['speed']}"
            )

        party.battles_won += 1

        # Sync HP/MP from battle (capped to current max).
        final_stats = calculate_stats_at_level(get_digimon(party.species_id), party.level)
        party.current_hp = max(1, min(final_stats["hp"], self._engine.player.current_hp))
        party.current_mp = max(0, min(final_stats["mp"], self._engine.player.current_mp))

        # Evolution check
        if can_evolve(party.species_id, party.level, party.battles_won):
            self._pending_evolution = True
            self._start_evolution()

    def _start_evolution(self) -> None:
        party = self.game.save_data.party[0]
        old_species = get_digimon(party.species_id)
        new_name = old_species.evolution_target
        self._new_species_def = get_digimon(new_name)
        self._evolution_message = f"{old_species.name} evolved into {self._new_species_def.name}!"
        self._set_phase(PHASE_EVOLUTION, _EVOLUTION_DURATION)

    def _finish_evolution(self) -> None:
        if self._evolution_done:
            return
        party = self.game.save_data.party[0]
        new_def = self._new_species_def
        party.species_id = new_def.key
        party.stage = new_def.stage
        new_stats = calculate_stats_at_level(new_def, party.level)
        party.current_hp = new_stats["hp"]
        party.current_mp = new_stats["mp"]
        party.learned_moves = [m.name for m in new_def.moves]
        self._victory_messages.append(self._evolution_message)
        self._evolution_done = True
        self._phase = PHASE_VICTORY

    def _finish_victory(self) -> None:
        self.game.battle_result = {
            "winner": "player",
            "xp": self._xp_awarded,
            "gold": self._gold_awarded,
        }
        self.game.pop()

    def _finish_flee(self) -> None:
        self.game.battle_result = {"winner": "fled"}
        self.game.pop()

    def _go_title(self) -> None:
        from scenes.title_scene import TitleScene
        self.game.clear()
        self.game.push(TitleScene(game=self.game))

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        key = event.key

        if self._phase == PHASE_PLAYER_MENU:
            self._handle_menu_key(key)
        elif self._phase == PHASE_INTRO:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._phase_timer = 0.0
        elif self._phase == PHASE_MESSAGE:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._phase_timer = 0.0
        elif self._phase == PHASE_VICTORY:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._finish_victory()
        elif self._phase == PHASE_DEFEAT:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_title()
        elif self._phase == PHASE_FLEE_RESULT:
            if self._flee_success and key in (pygame.K_RETURN, pygame.K_SPACE):
                self._finish_flee()
        elif self._phase == PHASE_EVOLUTION:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._finish_evolution()

    def _handle_menu_key(self, key: int) -> None:
        num_moves = len(self._engine.player.moves)
        if pygame.K_1 <= key <= pygame.K_9:
            idx = key - pygame.K_1
            if 0 <= idx < num_moves:
                self._begin_player_action(idx)
                return
        if key == pygame.K_f:
            self._try_flee()
            return

        # Arrow navigation within 2×2 grid
        if key in (pygame.K_UP, pygame.K_w):
            self._selected = (self._selected - 2) % max(1, num_moves)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected = (self._selected + 2) % max(1, num_moves)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._selected = (self._selected - 1) % max(1, num_moves)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._selected = (self._selected + 1) % max(1, num_moves)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._begin_player_action(self._selected)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # Flash decay
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, int(self._flash_alpha - 700 * dt))

        self._phase_timer -= dt

        # Trigger anim flash at midpoint
        if self._phase in (PHASE_PLAYER_ANIM, PHASE_ENEMY_ANIM) and self._phase_duration > 0:
            progress = max(0.0, min(1.0, 1.0 - self._phase_timer / self._phase_duration))
            if _fwd_factor(progress) >= 0.5 and not self._anim_flash_done:
                self._anim_flash_done = True
                self._flash_alpha = 180

        if self._phase == PHASE_INTRO and self._phase_timer <= 0:
            self._start_round()
        elif self._phase == PHASE_PLAYER_ANIM and self._phase_timer <= 0:
            self._end_anim()
        elif self._phase == PHASE_ENEMY_ANIM and self._phase_timer <= 0:
            self._end_anim()
        elif self._phase == PHASE_MESSAGE and self._phase_timer <= 0:
            self._advance_from_message()
        elif self._phase == PHASE_FLEE_RESULT:
            if not self._flee_success and self._phase_timer <= 0:
                self._begin_enemy_action()
        elif self._phase == PHASE_EVOLUTION and self._phase_timer <= 0:
            self._finish_evolution()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((20, 20, 40))
        self._draw_title_bar(screen)
        self._draw_combatants(screen)
        self._draw_battle_log(screen)
        self._draw_action_area(screen)

        # Phase-specific overlays
        if self._phase == PHASE_INTRO:
            self._draw_centered_text(screen, self._intro_text, self._font_lg, config.YELLOW, 200)
        elif self._phase == PHASE_MESSAGE:
            msg = self._last_result.get("message", "") if self._last_result else ""
            self._draw_centered_text(screen, msg, self._font_md, config.WHITE, 260)
        elif self._phase == PHASE_VICTORY:
            self._draw_victory(screen)
        elif self._phase == PHASE_DEFEAT:
            self._draw_defeat(screen)
        elif self._phase == PHASE_FLEE_RESULT:
            self._draw_centered_text(screen, self._flee_message, self._font_md, config.WHITE, 240)
        elif self._phase == PHASE_EVOLUTION:
            self._draw_evolution_overlay(screen)

        # Flash overlay
        if self._flash_alpha > 0:
            self._flash_surf.fill((255, 255, 255, self._flash_alpha))
            screen.blit(self._flash_surf, (0, 0))

    def _draw_title_bar(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (10, 10, 20), (0, 0, config.SCREEN_WIDTH, 30))
        pygame.draw.line(screen, config.WHITE, (0, 30), (config.SCREEN_WIDTH, 30), 1)
        text = f"WILD BATTLE  —  Round {self._engine.round}"
        surf = self._font_md.render(text, True, config.WHITE)
        screen.blit(surf, (10, 6))

    def _get_anim_progress(self) -> float:
        if self._phase in (PHASE_PLAYER_ANIM, PHASE_ENEMY_ANIM) and self._phase_duration > 0:
            return max(0.0, min(1.0, 1.0 - self._phase_timer / self._phase_duration))
        return 0.0

    def _draw_combatants(self, screen: pygame.Surface) -> None:
        engine = self._engine
        prog = self._get_anim_progress()
        fwd = _fwd_factor(prog)

        # Player
        p_off_x = 0
        p_off_y = 0
        if self._phase == PHASE_PLAYER_ANIM:
            p_off_x = int(fwd * 120)
            p_off_y = int(-fwd * 60)

        # Determine player display species/element/stage
        if self._phase == PHASE_EVOLUTION and self._new_species_def is not None:
            p_color = _element_color(self._new_species_def.element)
            p_radius = _stage_radius(self._new_species_def.stage)
        else:
            p_species = get_digimon(engine.player.species_name)
            p_color = _element_color(p_species.element)
            p_radius = _stage_radius(p_species.stage)

        self._draw_digimon_shape(
            screen,
            _PLAYER_BASE[0] + p_off_x,
            _PLAYER_BASE[1] + p_off_y,
            p_color,
            p_radius,
        )

        # Enemy
        e_off_x = 0
        e_off_y = 0
        if self._phase == PHASE_ENEMY_ANIM:
            e_off_x = int(-fwd * 120)
            e_off_y = int(fwd * 60)
        e_species = get_digimon(engine.enemy.species_name)
        e_color = _element_color(e_species.element)
        e_radius = _stage_radius(e_species.stage)
        self._draw_digimon_shape(
            screen,
            _ENEMY_BASE[0] + e_off_x,
            _ENEMY_BASE[1] + e_off_y,
            e_color,
            e_radius,
        )

        # Player info bar
        self._draw_info_box(
            screen, 60, 200, 220, 18,
            f"{engine.player.nickname}  Lv{engine.player.level}",
            engine.player.current_hp, engine.player.max_hp,
            engine.player.current_mp, engine.player.max_mp,
        )

        # Enemy info bar
        self._draw_info_box(
            screen, 380, 120, 220, 18,
            f"{engine.enemy.nickname}  Lv{engine.enemy.level}",
            engine.enemy.current_hp, engine.enemy.max_hp,
            None, None,
        )

    def _draw_digimon_shape(
        self, screen: pygame.Surface, cx: int, cy: int,
        color: Tuple[int, int, int], radius: int,
    ) -> None:
        pygame.draw.circle(screen, color, (cx, cy), radius)
        pygame.draw.circle(screen, config.WHITE, (cx, cy), radius, 2)
        # Eyes
        eye_dx = max(5, radius // 3)
        eye_r = max(3, radius // 6)
        pygame.draw.circle(screen, config.WHITE, (cx - eye_dx, cy - eye_dx), eye_r)
        pygame.draw.circle(screen, config.WHITE, (cx + eye_dx, cy - eye_dx), eye_r)
        pygame.draw.circle(screen, config.BLACK, (cx - eye_dx, cy - eye_dx), max(1, eye_r // 2))
        pygame.draw.circle(screen, config.BLACK, (cx + eye_dx, cy - eye_dx), max(1, eye_r // 2))

    def _draw_info_box(
        self, screen: pygame.Surface, x: int, y: int, w: int, h: int,
        label: str, hp: int, max_hp: int,
        mp: Optional[int], max_mp: Optional[int],
    ) -> None:
        # Name label
        name_surf = self._font_sm.render(label, True, config.WHITE)
        screen.blit(name_surf, (x, y))

        bar_y = y + 18
        bar_w = w
        bar_h = 12

        # HP bar background
        pygame.draw.rect(screen, (40, 40, 40), (x, bar_y, bar_w, bar_h))
        # HP bar fill
        if max_hp > 0:
            ratio = max(0.0, min(1.0, hp / max_hp))
            fill_w = int(bar_w * ratio)
            if ratio > 0.5:
                hp_color = config.GREEN
            elif ratio > 0.25:
                hp_color = config.YELLOW
            else:
                hp_color = config.RED
            pygame.draw.rect(screen, hp_color, (x, bar_y, fill_w, bar_h))
        pygame.draw.rect(screen, config.WHITE, (x, bar_y, bar_w, bar_h), 1)
        hp_text = self._font_xs.render(f"HP {hp}/{max_hp}", True, config.WHITE)
        screen.blit(hp_text, (x + 2, bar_y - 1))

        # MP bar (player only)
        if mp is not None and max_mp is not None:
            mp_y = bar_y + bar_h + 2
            pygame.draw.rect(screen, (40, 40, 40), (x, mp_y, bar_w, 8))
            if max_mp > 0:
                mp_ratio = max(0.0, min(1.0, mp / max_mp))
                pygame.draw.rect(screen, config.CYAN, (x, mp_y, int(bar_w * mp_ratio), 8))
            pygame.draw.rect(screen, config.WHITE, (x, mp_y, bar_w, 8), 1)
            mp_text = self._font_xs.render(f"MP {mp}/{max_mp}", True, config.WHITE)
            screen.blit(mp_text, (x + 2, mp_y - 1))

    def _draw_battle_log(self, screen: pygame.Surface) -> None:
        log_y = 260
        log_h = 50
        pygame.draw.rect(screen, (15, 15, 25), (0, log_y, config.SCREEN_WIDTH, log_h))
        pygame.draw.line(screen, config.WHITE, (0, log_y), (config.SCREEN_WIDTH, log_y), 1)
        pygame.draw.line(screen, config.WHITE, (0, log_y + log_h), (config.SCREEN_WIDTH, log_y + log_h), 1)
        recent = self._engine.log[-3:] if self._engine.log else []
        ly = log_y + 6
        for msg in recent:
            lines = _wrap_text(msg, self._font_sm, config.SCREEN_WIDTH - 20)
            for line in lines:
                surf = self._font_sm.render(line, True, config.LIGHT_GRAY)
                screen.blit(surf, (10, ly))
                ly += 16
                if ly > log_y + log_h - 4:
                    break
            if ly > log_y + log_h - 4:
                break

    def _draw_action_area(self, screen: pygame.Surface) -> None:
        area_y = 310
        area_h = config.SCREEN_HEIGHT - area_y
        pygame.draw.rect(screen, (25, 25, 45), (0, area_y, config.SCREEN_WIDTH, area_h))
        pygame.draw.line(screen, config.WHITE, (0, area_y), (config.SCREEN_WIDTH, area_y), 1)

        if self._phase != PHASE_PLAYER_MENU:
            # Dimmed moves
            self._draw_move_grid(screen, area_y, dimmed=True)
            return

        self._draw_move_grid(screen, area_y, dimmed=False)

        # Flee option
        flee_surf = self._font_sm.render("[F] Flee", True, config.YELLOW)
        screen.blit(flee_surf, (config.SCREEN_WIDTH - flee_surf.get_width() - 16, area_y + area_h - 22))

    def _draw_move_grid(self, screen: pygame.Surface, area_y: int, dimmed: bool) -> None:
        moves = self._engine.player.moves
        cell_w = 300
        cell_h = 52
        gap = 8
        start_x = 16
        start_y = area_y + 20

        for i in range(min(4, len(moves))):
            move = moves[i]
            col = i % 2
            row = i // 2
            cx = start_x + col * (cell_w + gap)
            cy = start_y + row * (cell_h + gap)

            affordable = self._engine.player.current_mp >= move.mp_cost
            bg_color = (40, 40, 60) if affordable else (60, 30, 30)
            border_color = config.WHITE if (not dimmed and i == self._selected) else (100, 100, 120)

            pygame.draw.rect(screen, bg_color, (cx, cy, cell_w, cell_h))
            pygame.draw.rect(screen, border_color, (cx, cy, cell_w, cell_h), 2)

            num_text = f"{i + 1}."
            num_surf = self._font_sm.render(num_text, True, config.YELLOW if not dimmed else config.GRAY)
            screen.blit(num_surf, (cx + 8, cy + 4))

            name_color = config.WHITE if (affordable and not dimmed) else (config.GRAY if dimmed else config.RED)
            name_surf = self._font_sm.render(move.name, True, name_color)
            screen.blit(name_surf, (cx + 28, cy + 4))

            detail = f"Pow:{move.power}  MP:{move.mp_cost}  [{move.element}]"
            detail_surf = self._font_xs.render(detail, True, config.LIGHT_GRAY if not dimmed else config.GRAY)
            screen.blit(detail_surf, (cx + 8, cy + 26))

    def _draw_victory(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = self._font_lg.render("VICTORY!", True, config.YELLOW)
        screen.blit(title, ((config.SCREEN_WIDTH - title.get_width()) // 2, 120))

        ly = 160
        for msg in self._victory_messages:
            lines = _wrap_text(msg, self._font_md, config.SCREEN_WIDTH - 60)
            for line in lines:
                surf = self._font_md.render(line, True, config.WHITE)
                screen.blit(surf, (30, ly))
                ly += 24
            ly += 4

        if self._pending_evolution and not self._evolution_done:
            return  # Evolution will take over

        prompt = self._font_sm.render("Press ENTER to continue", True, config.CYAN)
        screen.blit(prompt, ((config.SCREEN_WIDTH - prompt.get_width()) // 2, config.SCREEN_HEIGHT - 40))

    def _draw_defeat(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title = self._font_lg.render("You were defeated...", True, config.RED)
        screen.blit(title, ((config.SCREEN_WIDTH - title.get_width()) // 2, 180))
        prompt = self._font_sm.render("Press ENTER to return to Title", True, config.WHITE)
        screen.blit(prompt, ((config.SCREEN_WIDTH - prompt.get_width()) // 2, 230))

    def _draw_evolution_overlay(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(config.SCREEN_SIZE, pygame.SRCALPHA)
        # Pulsing white flash
        prog = 1.0 - (self._phase_timer / self._phase_duration) if self._phase_duration > 0 else 0.0
        flash = int(abs(math.sin(prog * math.pi * 6)) * 120)
        overlay.fill((255, 255, 255, flash))
        screen.blit(overlay, (0, 0))

        title = self._font_lg.render("EVOLUTION!", True, config.YELLOW)
        screen.blit(title, ((config.SCREEN_WIDTH - title.get_width()) // 2, 60))

        party = self.game.save_data.party[0]
        old_name = get_digimon(party.species_id).name if not self._evolution_done else self._new_species_def.name
        msg = "Your Digimon is evolving!" if not self._evolution_done else self._evolution_message
        surf = self._font_md.render(msg, True, config.WHITE)
        screen.blit(surf, ((config.SCREEN_WIDTH - surf.get_width()) // 2, 340))

    def _draw_centered_text(
        self, screen: pygame.Surface, text: str,
        font: pygame.font.Font, color: Tuple[int, int, int], y: int,
    ) -> None:
        lines = _wrap_text(text, font, config.SCREEN_WIDTH - 60)
        ly = y
        for line in lines:
            surf = font.render(line, True, color)
            screen.blit(surf, ((config.SCREEN_WIDTH - surf.get_width()) // 2, ly))
            ly += font.get_height() + 2
