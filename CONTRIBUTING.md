# Contributing to Docx2Shelf

Thanks for your interest in contributing! This guide covers local setup, project layout, CI, and the release process.

## Project Layout
- `src/docx2shelf/{cli,convert,assemble,metadata,utils,tools}.py`
- `src/docx2shelf/assets/css/*.css`, `src/docx2shelf/templates/*`
- `tests/` — unit tests (run with `pytest`)
- `scripts/` — install/uninstall/test helpers
- `packaging/docx2shelf.spec` — PyInstaller spec (optional bundling)

## Local Development
- Create venv and install dev extras:
  - Linux/macOS: `python -m venv .venv && . .venv/bin/activate`
  - Windows: `python -m venv .venv && . .venv\Scripts\activate`
  - Install: `pip install -e ".[dev]"`
- Run tests:
  - `pytest -q` or `scripts/test.sh` / `scripts/test.ps1`
- Lint/format/type-check (optional):
  - `ruff check . && black . && mypy src/docx2shelf`
- Build packages:
  - `python -m build` → `dist/`

## Tools Manager (dev)
- Managed tools cache:
  - Windows: `%APPDATA%\Docx2Shelf\bin`
  - macOS/Linux: `~/.docx2shelf/bin`
- Install tools:
  - `docx2shelf tools install pandoc|epubcheck`
- Show paths:
  - `docx2shelf tools where`
- Uninstall tools:
  - `docx2shelf tools uninstall pandoc|epubcheck|all`

## CI
- GitHub Actions run tests on Windows/macOS/Linux for pushes and PRs (`.github/workflows/ci.yml`).

## Releases
- Tagging a release (e.g., `v0.1`) triggers the release workflow (`.github/workflows/release.yml`):
  - Tests → build → GitHub Release with artifacts
  - CHANGELOG.md auto-update from `RELEASE_NOTES_<tag>.md`
- To prepare a release:
  1) Write `RELEASE_NOTES_<tag>.md`
  2) Tag: `git tag -a vX.Y -m "Release X.Y" && git push origin vX.Y`

## Coding Guidelines
- Keep changes minimal and focused on the task.
- Prefer readable code and explicit names over cleverness.
- Avoid one-letter variables; add docstrings for public functions.
- Respect existing style (run ruff/black/mypy if needed).

## Issue Reporting
- Include OS, Python version, commands run, and minimal examples.
- Attach `--dry-run` output for build issues if possible.

## Pull Requests
- Keep commits small and focused; use clear titles/descriptions.
- Include tests when reasonable.
- Ensure `pytest -q` passes locally before opening a PR.

