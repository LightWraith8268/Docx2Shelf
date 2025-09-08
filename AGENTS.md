# Repository Guidelines

Docx2Shelf is a Python 3.11, offline CLI that converts DOCX manuscripts into valid EPUB 3 files.

## Project Structure & Modules
- Source package: `src/docx2shelf/`
  - `cli.py`, `convert.py`, `assemble.py`, `metadata.py`, `utils.py`
  - Assets: `css/` (themes: serif, sans, printlike), `templates/` (title, cover, nav, ncx)
- Tests: `tests/` mirroring `src/` (e.g., `tests/test_metadata.py`, `tests/convert/test_split.py`), fixtures in `tests/fixtures/`.
- Packaging: `pyproject.toml`, `packaging/docx2shelf.spec` (PyInstaller), `README.md`, `examples/`.

## Build, Test, and Dev Commands
- Environment: Python 3.11. Install: `python -m venv .venv && . .venv/bin/activate` (or `./.venv/Scripts/activate` on Windows).
- Editable install + dev deps: `pip install -e ".[dev]"`.
- CLI help: `docx2shelf --help`.
- Build EPUB (example):
  `docx2shelf build --docx manuscript.docx --cover cover.jpg --title "Book" --author "Author Name" --theme serif --justify on --hyphenate on`
- Dry run / inspect: `--dry-run`, `--inspect`.
- Tests: `pytest -q` (coverage: `pytest --cov=docx2shelf`).
- Lint/format/type-check: `ruff check . && black . && mypy src/docx2shelf`.
- Package wheels: `python -m build`. Single-file app: `pyinstaller packaging/docx2shelf.spec`.
- Optional tools: Pandoc (`pypandoc`) preferred; fallback `python-docx`. EPUBCheck used if found on PATH.

## Coding Style & Naming
- 4-space indentation, ~100-char line wrap, snake_case modules/functions, PascalCase classes, UPPER_CASE constants.
- Type hints + docstrings required on public functions. Keep functions small; prefer composition.
- No network calls or telemetry; all processing offline.

## Testing Guidelines
- Use `pytest`. Cover: metadata mapping, TOC depth, split-at logic, non-Pandoc fallback, cover handling, filename sanitization.
- Name tests `test_*.py`; co-locate fixtures in `tests/fixtures/`. Run full suite before PR.

## Commit & Pull Requests
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Small, atomic commits; subject ≤72 chars; include rationale.
- PRs: clear description, sample CLI command used, expected output filename, and notes on EPUBCheck result; link issues.

## Security & Configuration
- Never commit secrets. Use `.env` only for local paths (e.g., fonts dir); add `.env.example`.
- Validate inputs (DOCX, cover type, ISBN). Warn users that page numbers are reader-dependent; provide page-list optionally.
