# Architecture Decision Records (ADR) — digimon-rpg

| Field | Value |
|---|---|
| **Document** | ADR.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [Architecture.md](Architecture.md), [SRS.md](SRS.md) |

---

## ADR-001: Use pygbag for WebAssembly Deployment

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Project Owner, Lead Game Designer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

The game must run in a web browser with zero installation for the player.
The game is written in Python using pygame. We need a way to deploy a pygame
application to the web.

### Options Considered

1. **pygbag (WebAssembly)** — Compiles pygame apps to WASM using the Pyodide
   runtime. Runs entirely in-browser. No server-side runtime needed.
2. **PyScript** — Runs Python in the browser via Pyodide. Less optimized for
   game loops; no built-in pygame support.
3. **Server-side rendering** — Run pygame on a server, stream frames to client.
   Requires server infrastructure, high latency, not viable for real-time games.
4. **Rewrite in JavaScript** — Port the entire game to JS/Canvas. Discards the
   Python codebase entirely.

### Decision

**Use pygbag.** It is the only option that preserves the Python/pygame codebase
while enabling browser deployment. It is officially supported by the pygame
organization and has the best compatibility story.

### Consequences

**Positive:**
- Single codebase for desktop and web.
- No server infrastructure needed — static hosting on GitHub Pages.
- Official pygame community support.

**Negative:**
- WASM constraints: no `subprocess`, no blocking I/O, no threading.
- Game loop must be `async def`.
- Asset loading is bundled at build time (no dynamic downloads).
- Slightly larger initial download (Pyodide runtime + game).

**Mitigations:**
- Document all WASM constraints in [SRS.md](SRS.md) §4.
- Design save system around `localStorage` instead of file I/O.
- Structure game loop as async coroutine from day one (see
  [Architecture.md](Architecture.md) §4).

---

## ADR-002: Scene Manager with Stack-Based Transitions

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Lead Game Designer, Pygame Engineer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

The game has 20 distinct scenes (title, world, battle, menus, etc.). Some
scenes are overlays (dialogue, settings) that should appear on top of the
current scene without destroying it. We need a scene management strategy.

### Options Considered

1. **Stack-based scene manager** — Scenes are pushed/popped from a stack.
   Overlay scenes push on top; popping restores the previous scene.
2. **Flat scene manager** — Only one scene active at a time. Transitions
   replace the current scene entirely. Overlays must save and restore state
   manually.
3. **State machine** — Scenes are states with explicit transition rules.
   More structured but more rigid; harder to add overlay scenes.

### Decision

**Use a stack-based scene manager.** The stack naturally supports overlay
scenes (push dialogue on top of world map; pop to return to world map) without
manual state save/restore. The `replace()` method handles full transitions
(battle → victory → world map).

### Consequences

**Positive:**
- Overlay scenes (dialogue, settings, capture) are trivial.
- Previous scene state is preserved during overlays.
- Clean separation: each scene manages its own `on_enter`/`on_exit`.
- Only the top scene receives `update()`/`draw()` calls.

**Negative:**
- Memory: all scenes in the stack are retained. Mitigated by the fact that
  stacks are typically shallow (2–3 scenes).
- Must be careful to pop scenes correctly (resource cleanup in `on_exit()`).

### Implementation

See [Architecture.md](Architecture.md) §3.2 for the `SceneManager` class
definition.

---

## ADR-003: Save Strategy — Browser localStorage via pygbag Bridge

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Systems Engineer, Pygame Engineer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

The game needs a persistent save system. Traditional file I/O (`open()` /
`json.dump()`) is problematic under pygbag/WASM because the browser sandbox
does not provide a traditional filesystem. We need a save strategy that works
in the browser.

### Options Considered

1. **Browser localStorage via pygbag JS bridge** — pygbag provides a bridge to
   the browser's `localStorage` API. Data is stored as a JSON string under a
   single key. Persists across page reloads.
2. **IndexedDB** — More structured browser storage with larger capacity. More
   complex API; requires async access patterns.
3. **File download/upload** — Export save as a `.json` file download; player
   manually re-imports. Cumbersome UX.
4. **pygbag's `platform.storage`** — pygbag may expose a storage abstraction.
   Documentation is sparse; uncertain reliability.

### Decision

**Use browser localStorage via pygbag JS bridge.** It is the simplest reliable
option. The save data (one `PlayerSave` object) is small (estimated <50KB),
well within localStorage's 5–10MB limit. JSON serialization is straightforward.

### Consequences

**Positive:**
- Simple: `localStorage.setItem(key, json_string)` /
  `localStorage.getItem(key)`.
- Synchronous read, which simplifies the load flow.
- Persists across browser sessions.
- No server required.

**Negative:**
- **5–10MB limit** — not a concern for this game's save size.
- **User can clear browser data** — save is lost. Must document this in the
  game (camp screen warning).
- **Not cross-device** — save is per-browser. No cloud sync.
- **Save versioning** — must handle schema migrations for future updates.

### Save Schema

```json
{
  "version": 1,
  "player_name": "Ash",
  "gold": 1500,
  "inventory": {"potion": 5, "digi_core": 3},
  "party": [ { "species_id": "emberling", ... } ],
  "box": [],
  "unlocked_zones": ["verdant_plains"],
  "zone_progress": {"verdant_plains": {"boss_defeated": false}},
  "current_map": {"zone_id": "verdant_plains", "x": 100, "y": 200},
  "flags": {"tutorial_complete": true},
  "total_battles_won": 12,
  "total_steps": 3420,
  "game_cleared": false,
  "settings": {"music_vol": 80, "sfx_vol": 90, "text_speed": "medium", "fullscreen": false}
}
```

### Implementation

See [Architecture.md](Architecture.md) §6.4 for the `SaveSystem` interface.
The save is versioned (`SAVE_VERSION = 1`) to support future migrations.

### Migration Strategy

```python
MIGRATIONS = {
    1: migrate_v1_to_v2,
    2: migrate_v2_to_v3,
    # ...
}

def load() -> PlayerSave | None:
    raw = localStorage.getItem(SAVE_KEY)
    if raw is None:
        return None
    data = json.loads(raw)
    version = data.get("version", 0)
    while version < SAVE_VERSION:
        data = MIGRATIONS[version](data)
        version += 1
    return PlayerSave.from_dict(data)
```

---

## ADR-004: Data-Driven Roster Using Python Dataclasses

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Systems Engineer, Lead Game Designer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

The game has 18 species (6 evolution lines × 3 stages), each with base stats,
growth rates, skills, and descriptions. This data must be defined, maintained,
and referenced throughout the codebase.

### Options Considered

1. **Python dataclasses in `src/data/roster.py`** — Define species as
   dataclass instances in Python code. Type-safe, IDE-autocompletable, easy to
   validate.
2. **JSON/YAML data files** — External data files loaded at runtime. More
   flexible for non-programmers to edit, but loses type safety and requires
   runtime validation.
3. **SQLite database** — Overkill for static game data. Adds complexity and
   potential WASM compatibility concerns.

### Decision

**Use Python dataclasses in `src/data/`.** The roster is static game design
data, not user-generated content. Dataclasses provide type safety, are easy to
maintain alongside code, and require no runtime parsing. They are fully
compatible with pygbag/WASM.

### Consequences

**Positive:**
- Type-safe: IDE catches typos in stat names.
- No runtime parsing overhead.
- Data and code live together — version-controlled, reviewable.
- Easily serializable for save system (via `dataclasses.asdict()`).

**Negative:**
- Non-programmers can't easily edit data. Mitigated by clear structure and
  documentation.
- Changes to roster require code changes (not just data file edits).

### Implementation

See [Schema.md](Schema.md) for the full dataclass definitions.

---

## ADR-005: Async Game Loop with `asyncio.sleep(0)` Yielding

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Pygame Engineer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

pygbag runs Python inside the browser's JavaScript event loop. A traditional
blocking `while True` game loop would freeze the browser tab, making the page
unresponsive.

### Options Considered

1. **`async def` loop with `await asyncio.sleep(0)`** — Yields to the browser
   event loop each frame. The browser can process input, paint, and run other
   tasks.
2. **`async def` loop with `await asyncio.sleep(1/60)`** — Same as above but
   with an explicit frame delay. Redundant with `clock.tick(60)`.
3. **pygbag's built-in `pygame.run()`** — pygbag may provide a runner that
   handles the async loop internally. Less control over frame timing.

### Decision

**Use `async def` loop with `await asyncio.sleep(0)`.** The `sleep(0)` yields
control without adding delay — the frame rate is controlled by
`clock.tick(60)`. This gives us full control over the game loop while remaining
browser-friendly.

### Consequences

**Positive:**
- Full control over frame timing, event processing, and rendering order.
- Browser remains responsive (can handle tab switches, resize, etc.).
- Standard asyncio patterns usable for any async operations.

**Negative:**
- Must remember to `await asyncio.sleep(0)` every frame. Forgetting it causes
  a browser freeze.
- All I/O operations must be async-compatible (no blocking calls).

### Implementation

See [Architecture.md](Architecture.md) §4.2 for the loop structure.

---

## ADR-006: Single-Party Active Battle with Bench Support

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-28 |
| **Deciders** | Lead Game Designer |
| **Supersedes** | — |
| **Superseded by** | — |

### Context

The PRD specifies a party of up to 6 creatures, but battles need a defined
number of active participants. We need to decide how many creatures are in
battle simultaneously.

### Options Considered

1. **1v1 with bench of 2** — One active creature per side; up to 2 on bench,
   swappable mid-battle. Simple, classic.
2. **2v2 double battles** — Two active creatures per side. More complex AI and
  UI; more strategic but harder to balance.
3. **3v3 or larger** — Too complex for a browser game; UI clutter; performance
  concerns.

### Decision

**1v1 with bench of 2.** This is the classic monster-battler format. It keeps
the UI clean (two sprites, two HP bars), the AI simple, and the performance
budget manageable. The bench adds strategic depth without complexity.

### Consequences

**Positive:**
- Clean, readable battle UI.
- Simple AI (one target).
- Good performance (minimal sprites and effects).
- Familiar to genre fans.

**Negative:**
- Less tactical depth than multi-creature battles.
- Bench switching must be carefully balanced (switching costs a turn).

---

## Related Documents

- [Architecture.md](Architecture.md) — System architecture
- [SRS.md](SRS.md) — Software requirements (constraints)
- [Schema.md](Schema.md) — Data schemas
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
