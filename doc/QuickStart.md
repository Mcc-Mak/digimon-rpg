# Quick Start — digimon-rpg

| Field | Value |
|---|---|
| **Document** | QuickStart.md |
| **Version** | 0.3.0 |
| **Date** | 2026-09-28 |
| **Status** | Approved |
| **Dependencies** | [Architecture.md](Architecture.md), [SRS.md](SRS.md), [Governance.md](Governance.md) |

---

## 1. Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| pip | Latest |
| Git | Latest |
| Modern browser | Chrome 100+, Firefox 100+, or Safari 15+ (for web testing) |

---

## 2. Clone the Repository

```bash
git clone https://github.com/Mcc-Mak/digimon-rpg.git
cd digimon-rpg
git checkout dev-001
```

> **Important**: All development work happens on the `dev-001` branch. Do not
> commit to `main`. See [Governance.md](Governance.md).

---

## 3. Set Up the Virtual Environment

### Linux / macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows (CMD)

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

---

## 4. Install Dependencies

```bash
pip install pygame-ce pygbag
```

> **Note**: We use `pygame-ce` (community edition) which has the best pygbag
> compatibility. If you have standard `pygame` installed, uninstall it first:
> `pip uninstall pygame && pip install pygame-ce`

### Optional Development Tools

```bash
pip install pytest          # Test runner
pip install mypy            # Type checking
pip install black ruff      # Code formatting / linting
```

---

## 5. Run the Game Locally (Desktop)

```bash
python main.py
```

This launches the game in a desktop pygame window. The game should display the
title screen.

> **Note**: The async game loop (`asyncio.run(main())`) works on desktop too —
> asyncio is part of the Python standard library. The `await asyncio.sleep(0)`
> call is a no-op on desktop but essential for pygbag/WASM.

---

## 6. Build for Web (pygbag/WASM)

### 6.1 Build the Web Package

```bash
python -m pygbag --build main.py
```

This produces a web-ready package in `./build/web/`.

**Expected output directory:**

```
build/web/
├── index.html
├── main.py               # Your game script (compiled)
├── pygame/               # Pygame WASM bundle
├── assets/               # Your game assets
└── ...
```

### 6.2 Serve Locally for Testing

```bash
# Option A: pygbag's built-in server
python -m pygbag main.py
# Then open: http://localhost:8000

# Option B: Python's built-in HTTP server
cd build/web
python -m http.server 8080
# Then open: http://localhost:8080
```

### 6.3 Verify the Build

Check that:
1. The page loads without console errors.
2. The title screen renders.
3. Input (keyboard/mouse) is responsive.
4. FPS is stable (check browser console for pygbag debug output).

---

## 7. Project Structure

```
digimon-rpg/
├── main.py                 # Game entry point (async loop)
├── src/
│   ├── core/               # Engine: game, scenes, input, assets, save
│   ├── scenes/             # 20 scene modules
│   ├── systems/            # Battle, evolution, leveling, encounters, items
│   ├── data/               # Roster, skills, encounters, items data
│   └── ui/                 # UI widgets, menus, effects
├── assets/                 # Sprites, audio, fonts
├── tests/                  # Test suite
├── doc/                    # Project documentation
├── .github/workflows/      # CI/CD pipeline
│   └── auto-merge.yml
├── main.py
├── README.md
├── TOCTREE.md
├── CHANGELOG.md
├── AGENTS.md
└── LICENSE
```

---

## 8. Development Workflow

### 8.1 Make Changes

1. Ensure you're on `dev-001`: `git checkout dev-001`
2. Make your changes.
3. Test locally: `python main.py`
4. Test web build: `python -m pygbag --build main.py`
5. Run tests: `pytest tests/`

### 8.2 Commit

Follow the commit conventions in [Governance.md](Governance.md):

```bash
git add -A
git commit -m "Add battle damage calculation

Implements the damage formula from PRD §5.3 including type
multipliers, critical hits, and STAB. Needed for the battle
system to function."
```

Format: imperative subject line, blank line, rationale body.

### 8.3 Update CHANGELOG

Add an entry to [CHANGELOG.md](../CHANGELOG.md) under a new or existing
semantic version heading:

```markdown
## 0.4.0 - 2026-09-29

### Added

- Battle damage calculation in `src/systems/battle.py` implementing
  the PRD §5.3 formula with type multipliers, crits, and STAB.
```

### 8.4 Push

```bash
git push origin dev-001
```

The CI pipeline (`.github/workflows/auto-merge.yml`) will:
1. Merge `dev-001` → `dev` → `main`.
2. Build the web package with pygbag.
3. Deploy to GitHub Pages.

---

## 9. CI/CD Pipeline

The pipeline runs automatically on every push to `dev-001`:

```
push to dev-001
    │
    ├── merge job:
    │     dev-001 → dev (fast-forward merge)
    │     dev → main (fast-forward merge)
    │
    └── deploy job (needs: merge):
          checkout main
          setup Python 3.12
          pip install pygbag
          python -m pygbag --build main.py
          upload ./build/web as Pages artifact
          deploy to GitHub Pages
```

**Live URL**: https://mcc-mak.github.io/digimon-rpg/

> **Note**: Do not modify the `merge` job in
> `.github/workflows/auto-merge.yml` (per [AGENTS.md](../AGENTS.md)).

---

## 10. Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pygame'`

**Cause**: pygame not installed or wrong virtual environment.

**Fix**:
```bash
pip install pygame-ce
```

### Problem: Browser tab freezes when running the game

**Cause**: The game loop is not yielding to the browser event loop.

**Fix**: Ensure `await asyncio.sleep(0)` is called every frame in the main
loop. See [Architecture.md](Architecture.md) §4.2.

### Problem: `pygbag --build` fails with import errors

**Cause**: A dependency is not WASM-compatible (e.g., uses C extensions or
`subprocess`).

**Fix**: Check that all imports are from `pygame`, `asyncio`, or the Python
stdlib. Remove any prohibited imports. See [SRS.md](SRS.md) §4.

### Problem: Save data disappears on page reload

**Cause**: localStorage was cleared, or the save key is wrong.

**Fix**: Check that `SaveSystem.SAVE_KEY` matches the key used in
`localStorage.setItem()`. Verify the browser's localStorage is not being
cleared by privacy settings.

### Problem: `python main.py` works locally but `pygbag --build` fails

**Cause**: Desktop Python supports modules that WASM doesn't (e.g.,
`subprocess`, `threading`, `os.system`).

**Fix**: Audit all imports for WASM compatibility. See [SRS.md](SRS.md) §4.1
for the full list of prohibited patterns.

### Problem: Assets not loading in web build

**Cause**: Asset paths are not relative to the script, or assets are not in
the expected directory.

**Fix**: Ensure all `pygame.image.load()` calls use paths relative to
`__file__` or the project root. Place assets in `assets/` and reference them
as `assets/sprites/...`.

---

## 11. Key File Reference

| File | Purpose |
|---|---|
| `main.py` | Game entry point — must exist at repo root for pygbag/CI |
| `src/core/game.py` | Game class — owns display, scenes, input, state |
| `src/data/roster.py` | All 18 creature species definitions |
| `src/data/skills.py` | All 24 skill definitions |
| `src/data/encounters.py` | Zone encounter tables |
| `.github/workflows/auto-merge.yml` | CI/CD pipeline — do not modify merge job |
| `AGENTS.md` | AI agent workflow conventions |
| `CHANGELOG.md` | Semantic version changelog |

---

## 12. Related Documents

- [Architecture.md](Architecture.md) — System architecture
- [SRS.md](SRS.md) — Technical constraints (pygbag/WASM)
- [Governance.md](Governance.md) — Branch strategy and commit conventions
- [ADR.md](ADR.md) — Architecture decisions (including pygbag choice)
- [TOCTREE.md](../TOCTREE.md) — Master table of contents
