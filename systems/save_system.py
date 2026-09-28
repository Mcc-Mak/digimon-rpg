"""Save / load system with pygbag (WebAssembly) compatibility.

This module provides asynchronous persistence for player progress. When
running under pygbag/WASM, data is stored in the browser's
``localStorage``. When running on desktop Python, an in-memory dict is used
(no blocking file I/O, keeping everything WASM-safe).

The core data type is :class:`SaveData`, a fully serializable dataclass that
round-trips through JSON via ``to_dict()`` / ``from_dict()``.

All storage functions are ``async`` and yield control via
``await asyncio.sleep(0)`` so the browser event loop stays responsive while
serializing/deserializing.

WASM safety: no subprocess, no blocking file writes, no threads, no ctypes.
Depends only on the stdlib ``json``, ``asyncio``, and ``dataclasses`` modules.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from data.digimon_data import get_digimon


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Prefix for all localStorage keys used by this module.
_STORAGE_PREFIX: str = "digimon_rpg_"

#: Empty flagged key used to detect whether we are in a browser context.
_MEMORY_STORE: Dict[str, str] = {}


# ---------------------------------------------------------------------------
# SaveData dataclass
# ---------------------------------------------------------------------------

@dataclass
class PartyMemberData:
    """Serializable representation of a single party Digimon.

    Attributes:
        species_id: Lowercase registry key of the species.
        nickname: Optional player-given nickname (defaults to species name).
        level: Current level.
        stage: Evolution stage string ("Rookie", "Champion", "Ultimate").
        xp: Current total XP accumulated.
        current_hp: Current HP (for the home party, untouched by battle).
        current_mp: Current MP (for the home party, untouched by battle).
        battles_won: Number of battles this creature has won (evolution).
        learned_moves: List of move names the creature knows.
    """

    species_id: str
    nickname: str
    level: int
    stage: str
    xp: int
    current_hp: int
    current_mp: int
    battles_won: int
    learned_moves: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return {
            "species_id": self.species_id,
            "nickname": self.nickname,
            "level": self.level,
            "stage": self.stage,
            "xp": self.xp,
            "current_hp": self.current_hp,
            "current_mp": self.current_mp,
            "battles_won": self.battles_won,
            "learned_moves": list(self.learned_moves),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartyMemberData":
        """Reconstruct a :class:`PartyMemberData` from a serialized dict."""
        return cls(
            species_id=str(data.get("species_id", "")),
            nickname=str(data.get("nickname", "")),
            level=int(data.get("level", 1)),
            stage=str(data.get("stage", "Rookie")),
            xp=int(data.get("xp", 0)),
            current_hp=int(data.get("current_hp", 0)),
            current_mp=int(data.get("current_mp", 0)),
            battles_won=int(data.get("battles_won", 0)),
            learned_moves=list(data.get("learned_moves", [])),
        )


@dataclass
class SaveData:
    """The complete, serializable player save state.

    Attributes:
        player_name: The player's chosen name.
        player_position: ``(x, y)`` world-map coordinates stored as a tuple.
        current_zone: Zone id the player is currently in.
        party: List of :class:`PartyMemberData` for the player's team.
        defeated_encounters: Running total of battles won (all sources).
        game_flags: Arbitrary string-keyed flags (bool/str/int values).
        gold: Amount of gold / currency the player holds.
    """

    player_name: str = "Player"
    player_position: Tuple[int, int] = (0, 0)
    current_zone: str = "verdant_plains"
    party: List[PartyMemberData] = field(default_factory=list)
    defeated_encounters: int = 0
    game_flags: Dict[str, Any] = field(default_factory=dict)
    gold: int = 0

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation of this save.

        Returns:
            A plain Python dict with only JSON-friendly primitives — safe to
            pass to :func:`json.dumps` for storage.
        """
        return {
            "version": 1,
            "player_name": self.player_name,
            "player_position": {
                "x": int(self.player_position[0]),
                "y": int(self.player_position[1]),
            },
            "current_zone": self.current_zone,
            "party": [member.to_dict() for member in self.party],
            "defeated_encounters": self.defeated_encounters,
            "game_flags": dict(self.game_flags),
            "gold": int(self.gold),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveData":
        """Reconstruct a :class:`SaveData` instance from a serialized dict.

        Args:
            data: The dict returned by :meth:`to_dict` (e.g. parsed from JSON).

        Returns:
            A fully populated :class:`SaveData` instance.
        """
        pos_data = data.get("player_position", {})
        if isinstance(pos_data, dict):
            x = int(pos_data.get("x", 0))
            y = int(pos_data.get("y", 0))
        else:
            # Fallback: maybe it's a list/tuple [x, y].
            x = int(pos_data[0]) if len(pos_data) > 0 else 0
            y = int(pos_data[1]) if len(pos_data) > 1 else 0

        party_raw: List[Dict[str, Any]] = list(data.get("party", []))
        party = [
            PartyMemberData.from_dict(member_data) for member_data in party_raw
        ]

        return cls(
            player_name=str(data.get("player_name", "Player")),
            player_position=(x, y),
            current_zone=str(data.get("current_zone", "verdant_plains")),
            party=party,
            defeated_encounters=int(data.get("defeated_encounters", 0)),
            game_flags=dict(data.get("game_flags", {})),
            gold=int(data.get("gold", 0)),
        )


# ---------------------------------------------------------------------------
# Runtime environment detection
# ---------------------------------------------------------------------------

def _is_browser() -> bool:
    """Detect whether we are running under pygbag/WASM in a browser.

    Returns ``True`` if the ``js`` module (a pygbag shim) is importable.
    This is evaluated lazily on each call via a try/except import.

    Returns:
        ``True`` if running in a browser context, else ``False``.
    """
    try:
        import js  # type: ignore  # noqa: F401  (pygbag-provided shim)

        return True
    except ImportError:
        return False


def _storage_key(slot: str) -> str:
    """Construct the deterministic localStorage/in-memory key for a slot.

    Args:
        slot: Save slot identifier (e.g. ``"auto"``, ``"slot1"``).

    Returns:
        A namespaced string guaranteed unique per slot.
    """
    return f"{_STORAGE_PREFIX}{slot}"


def _store_get(key: str) -> Optional[str]:
    """Read a raw JSON string from the active storage backend.

    Args:
        key: Fully-qualified storage key.

    Returns:
        The stored string, or ``None`` if absent.
    """
    if _is_browser():
        import js  # type: ignore

        try:
            return js.localStorage.getItem(key)
        except Exception:
            return None
    return _MEMORY_STORE.get(key)


def _store_set(key: str, value: str) -> None:
    """Write a JSON string to the active storage backend.

    Args:
        key: Fully-qualified storage key.
        value: JSON-encoded string to persist.
    """
    if _is_browser():
        import js  # type: ignore

        try:
            js.localStorage.setItem(key, value)
        except Exception:
            # Fall back to memory if localStorage is unavailable.
            _MEMORY_STORE[key] = value
    else:
        _MEMORY_STORE[key] = value


def _store_delete(key: str) -> None:
    """Remove a key from the active storage backend.

    Args:
        key: Fully-qualified storage key.
    """
    if _is_browser():
        import js  # type: ignore

        try:
            js.localStorage.removeItem(key)
        except Exception:
            _MEMORY_STORE.pop(key, None)
    else:
        _MEMORY_STORE.pop(key, None)


def _store_has(key: str) -> bool:
    """Whether a key exists in the active storage backend.

    Args:
        key: Fully-qualified storage key.

    Returns:
        ``True`` if the key exists.
    """
    return _store_get(key) is not None


# ---------------------------------------------------------------------------
# Public async save / load API
# ---------------------------------------------------------------------------

async def save_game(data: SaveData, slot: str = "auto") -> bool:
    """Persist a :class:`SaveData` to storage asynchronously.

    Serializes the save to JSON and writes it to localStorage (browser) or
    the in-memory store (desktop). Yields control to the event loop before
    and after the write so pygbag stays responsive.

    Args:
        data: The save state to write.
        slot: Save slot identifier (default ``"auto"``).

    Returns:
        ``True`` on success, ``False`` on serialization failure.
    """
    await asyncio.sleep(0)  # yield before potentially-heavy work

    try:
        payload: str = json.dumps(data.to_dict())
    except (TypeError, ValueError):
        return False

    key: str = _storage_key(slot)
    _store_set(key, payload)

    await asyncio.sleep(0)  # yield after to let browser flush
    return True


async def load_game(slot: str = "auto") -> Optional[SaveData]:
    """Load a save from storage asynchronously.

    Args:
        slot: Save slot identifier (default ``"auto"``).

    Returns:
        A reconstructed :class:`SaveData`, or ``None`` if no save exists in
        that slot or the stored JSON is corrupt.
    """
    await asyncio.sleep(0)

    key: str = _storage_key(slot)
    raw: Optional[str] = _store_get(key)
    if raw is None:
        return None

    try:
        payload: Dict[str, Any] = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    await asyncio.sleep(0)
    return SaveData.from_dict(payload)


# ---------------------------------------------------------------------------
# Synchronous convenience helpers
# ---------------------------------------------------------------------------

def has_save(slot: str = "auto") -> bool:
    """Check whether a save exists in a slot.

    Args:
        slot: Save slot identifier (default ``"auto"``).

    Returns:
        ``True`` if a save is stored in that slot.
    """
    return _store_has(_storage_key(slot))


def delete_save(slot: str = "auto") -> bool:
    """Delete a save from a slot.

    Args:
        slot: Save slot identifier (default ``"auto"``).

    Returns:
        ``True`` if a save existed and was deleted, ``False`` otherwise.
    """
    key: str = _storage_key(slot)
    if not _store_has(key):
        return False
    _store_delete(key)
    return True


def list_save_slots() -> list[str]:
    """List all currently available save slot identifiers.

    In the browser, this enumerates ``localStorage`` keys matching the
    digest-prefix. On desktop, it mirrors the in-memory store.

    Returns:
        A list of slot identifiers (without the prefix), sorted.
    """
    slots: List[str] = []

    if _is_browser():
        import js  # type: ignore

        try:
            length: int = js.localStorage.length
            for i in range(length):
                key = js.localStorage.key(i)
                if key is not None and str(key).startswith(_STORAGE_PREFIX):
                    slots.append(str(key)[len(_STORAGE_PREFIX):])
        except Exception:
            pass
    else:
        for key in _MEMORY_STORE:
            if key.startswith(_STORAGE_PREFIX):
                slots.append(key[len(_STORAGE_PREFIX):])

    return sorted(set(slots))


# ---------------------------------------------------------------------------
# Default save factory
# ---------------------------------------------------------------------------

def create_default_save(
    player_name: str = "Player",
    starter_species: str = "emberling",
) -> SaveData:
    """Create a fresh, level-1 starter save.

    Builds a :class:`SaveData` with a single party creature at level 1,
    full HP/MP, no battles won, starting zone at ``verdant_plains``, and
    zero gold.

    Args:
        player_name: Player-chosen name (default ``"Player"``).
        starter_species: Lowercase species id of the starting Digimon
            (default ``"emberling"``).

    Returns:
        A ready-to-save :class:`SaveData` instance.

    Raises:
        KeyError: If ``starter_species`` is not in the digimon registry.
    """
    digimon = get_digimon(starter_species)

    member = PartyMemberData(
        species_id=digimon.key,
        nickname=digimon.name,
        level=1,
        stage=digimon.stage,
        xp=0,
        current_hp=digimon.hp,
        current_mp=digimon.mp,
        battles_won=0,
        learned_moves=[move.name for move in digimon.moves],
    )

    return SaveData(
        player_name=player_name,
        player_position=(0, 0),
        current_zone="verdant_plains",
        party=[member],
        defeated_encounters=0,
        game_flags={"starter_chosen": True, "intro_seen": False},
        gold=0,
    )


# ---------------------------------------------------------------------------
# Class-based wrapper (alternative API)
# ---------------------------------------------------------------------------

class SaveSystem:
    """Object-oriented convenience wrapper around the module-level functions.

    Use this if your game prefers a single shared ``SaveSystem`` instance
    with slot-aware thread/async semantics, or call the module functions
    directly. Both APIs access the same underlying storage.
    """

    def __init__(self, default_slot: str = "auto") -> None:
        """Initialize with a default slot.

        Args:
            default_slot: Slot used when a method is called without an
                explicit ``slot`` argument.
        """
        self.default_slot: str = default_slot

    async def save(self, data: SaveData, slot: Optional[str] = None) -> bool:
        """Save ``data`` to the given slot (or the default slot).

        Args:
            data: The :class:`SaveData` to persist.
            slot: Override slot, or ``None`` to use the default.

        Returns:
            ``True`` on success.
        """
        target = slot if slot is not None else self.default_slot
        return await save_game(data, target)

    async def load(self, slot: Optional[str] = None) -> Optional[SaveData]:
        """Load from the given slot (or the default slot).

        Args:
            slot: Override slot, or ``None`` to use the default.

        Returns:
            The loaded :class:`SaveData`, or ``None`` if absent/corrupt.
        """
        target = slot if slot is not None else self.default_slot
        return await load_game(target)

    def delete(self, slot: Optional[str] = None) -> bool:
        """Delete the save in the given slot (or the default slot).

        Args:
            slot: Override slot, or ``None`` to use the default.

        Returns:
            ``True`` if a save was removed.
        """
        target = slot if slot is not None else self.default_slot
        return delete_save(target)

    def exists(self, slot: Optional[str] = None) -> bool:
        """Check whether a save exists in the given slot (or default slot).

        Args:
            slot: Override slot, or ``None`` to use the default.

        Returns:
            ``True`` if the save exists.
        """
        target = slot if slot is not None else self.default_slot
        return has_save(target)

    def slots(self) -> list[str]:
        """List all save slot identifiers currently available.

        Returns:
            Sorted list of slot ids.
        """
        return list_save_slots()
