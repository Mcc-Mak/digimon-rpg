# digimon-rpg

A browser-based monster-collection RPG built with [pygame](https://www.pygame.org/)
and deployed to the web via [pygbag](https://github.com/pygame-org/pygbag)
(WebAssembly). Battle, capture, train, and evolve original creatures across
multiple world zones.

---

## Play the Game

The game is deployed to GitHub Pages and runs entirely in your browser — no
installation required:

### 🌐 Web Access (GitHub Pages)

> **https://mcc-mak.github.io/digimon-rpg/**

The build pipeline (`.github/workflows/auto-merge.yml`) packages the pygame app
to WebAssembly using `python -m pygbag --build main.py` and deploys the
`./build/web` artifact to GitHub Pages automatically on every push to `dev-001`.

---

## Documentation

The complete documentation set is indexed in **[TOCTREE.md](TOCTREE.md)**.
Start there for a full table of contents.

Key documents:

| What | Where |
|---|---|
| Project scope & objectives | [doc/ProjectCharter.md](doc/ProjectCharter.md) |
| Game design & mechanics | [doc/PRD.md](doc/PRD.md) |
| Software requirements | [doc/SRS.md](doc/SRS.md) |
| Architecture overview | [doc/Architecture.md](doc/Architecture.md) |
| Quick start guide | [doc/QuickStart.md](doc/QuickStart.md) |

---

## Quick Start (Local Development)

```bash
# Clone the repository
git clone https://github.com/Mcc-Mak/digimon-rpg.git
cd digimon-rpg

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pygame-ce pygbag

# Run locally (desktop)
python main.py

# Build for web (WASM via pygbag)
python -m pygbag --build main.py
# Output: ./build/web/
```

See [doc/QuickStart.md](doc/QuickStart.md) for detailed instructions and
troubleshooting.

---

## Tech Stack

| Component | Technology |
|---|---|
| Game engine | pygame (pygame-ce) |
| Web packaging | pygbag (WebAssembly) |
| Deployment | GitHub Pages (via CI) |
| Language | Python 3.12 |
| Entry point | `main.py` (repo root) |

---

## Project Structure

```
digimon-rpg/
├── main.py                 # Game entry point (pygbag/CI expect this)
├── README.md               # This file
├── TOCTREE.md              # Master table of contents
├── CHANGELOG.md            # Semantic version changelog
├── AGENTS.md               # AI agent workflow conventions
├── LICENSE                 # MIT License
├── doc/                    # All project documentation
│   ├── ProjectCharter.md
│   ├── PRD.md
│   ├── SRS.md
│   ├── UserStories.md
│   ├── Architecture.md
│   ├── ADR.md
│   ├── ER.md
│   ├── Schema.md
│   ├── API.md
│   ├── QuickStart.md
│   ├── RTM.md
│   ├── Governance.md
│   └── CRM.md
├── src/                    # Game source code (planned)
│   ├── scenes/             # Scene modules
│   ├── systems/            # Battle, evolution, save systems
│   ├── data/               # Roster, encounters, skills data
│   └── core/               # Engine, input, rendering
├── assets/                 # Sprites, audio, fonts (planned)
└── .github/workflows/      # CI/CD pipeline
    └── auto-merge.yml
```

---

## License

[MIT](LICENSE) — Copyright © 2026 Mcc-Mak
