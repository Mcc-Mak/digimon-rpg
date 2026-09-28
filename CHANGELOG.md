# Changelog

All notable changes to this project are documented in this file.
Entries follow [Semantic Versioning](https://semver.org/) in the form `X.X.X`.

## 0.1.0 - 2026-09-28

### Added

- `AGENTS.md` with project workflow conventions: `dev-001` branch workflow,
  required document set, and README/Pages requirements.

### Changed

- Switched the GitHub Pages deployment in `.github/workflows/auto-merge.yml`
  from a Node.js build (`npm ci` / `npm run build` -> `./dist`) to a pygame
  pipeline: the app is packaged to WebAssembly via pygbag
  (`python -m pygbag --build main.py` -> `./build/web`). The `merge` job
  (dev-001 -> dev -> main) is unchanged.
