# Docx2Shelf

Offline Python 3.11 CLI that converts a DOCX manuscript plus metadata into a valid EPUB 3. No network calls required. Prefers Pandoc for high‑fidelity conversion and gracefully falls back to a local parser when Pandoc isn’t available.

## Features
- DOCX → EPUB 3 with OPF, NAV, NCX, spine/manifest and CSS themes (serif, sans, printlike)
- Cover embedding, title and copyright pages; optional dedication/acknowledgements
- Metadata: title, author, language (BCP‑47), ISBN/UUID, publisher, date, series (Calibre‑compatible)
- Split at headings or pagebreaks; nested ToC depth control
- Optional page list and page‑number counters (reader support varies)
- Fonts embedding; user CSS merge; inspect mode for debugging
- Optional EPUBCheck validation when available on PATH

## Install
Recommended (isolated global CLI):
- Linux/macOS: `sh scripts/install.sh --method pipx --extras all`
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Method pipx -Extras all`

Alternative:
- From source (dev): `python -m venv .venv && . .venv/bin/activate` (Windows: `./.venv/Scripts/activate`), then `pip install -e ".[dev]"` (optionally `.[docx]`, `.[pandoc]`).
- User install: `python -m pip install --user .`

Optional tools: Install Pandoc (for best DOCX conversion) and EPUBCheck (for validation).

### Metadata file (optional)
Place a `metadata.txt` next to your `.docx` to auto-fill prompts. Example:

```
Title: Book Title
Author: Riley E. Antrobus
Language: en
SeriesName: The Starborn Legacy
SeriesIndex: 01
Description: ...
ISBN: 9780306406157
Publisher: Example House
PubDate: 2024-07-01
UUID: 123e4567-e89b-12d3-a456-426614174000
Subjects: Space, Adventure
Keywords: sci-fi, epic
Title-Sort: Book Title, The
Author-Sort: Antrobus, Riley E.
Theme: serif
Split-At: h1
Page-List: on
Page-Numbers: off
Cover-Scale: contain
CSS: extras/book.css
Embed-Fonts: fonts/
Dedication: dedication.txt
Ack: ack.txt
EPUBCheck: on
Output: out/BookTitle.epub
```

Keys are case-insensitive; `key: value` or `key=value` are accepted. Paths can be relative to the DOCX folder. CLI flags still override if you pass them explicitly.

Note: If `--cover` is a relative path (e.g., `cover.jpg`), it resolves relative to the DOCX file's folder. For metadata.txt, prefer `Cover: cover.jpg` when the cover sits alongside the DOCX. Relative `CSS`, `Embed-Fonts`, `Dedication`, and `Ack` paths also resolve relative to the DOCX directory.

### Generate a template metadata.txt
Create a ready-to-edit template positioned next to your DOCX:

```
docx2shelf init-metadata --docx path/to/manuscript.docx --cover path/to/cover.jpg
```

Options:
- `--output` to write somewhere else (defaults to `DOCX_DIR/metadata.txt`)
- `--force` to overwrite if it exists

Behavior:
- The template infers a Title from the DOCX filename.
- If you pass `--cover` and it lives next to the DOCX, the template writes just the basename (e.g., `Cover: cover.jpg`) so it resolves relative to the DOCX folder.
- The template includes placeholders for `CSS`, `Embed-Fonts`, `Dedication`, and `Ack` paths, which also resolve relative to the DOCX directory when left as relative paths.

## Uninstall
- Linux/macOS: `sh scripts/uninstall.sh` (auto-detect) or `sh scripts/uninstall.sh --method pipx`
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/uninstall.ps1` or with `-Method pipx`

Manual pip uninstall: `python -m pip uninstall docx2shelf`

## Quickstart
```
docx2shelf build \
  --docx manuscript.docx \
  --cover cover.jpg \
  --title "Book Title" \
  --author "Riley E. Antrobus" \
  --language en \
  --theme serif \
  --split-at h1 \
  --justify on --hyphenate on
```
- Dry run: add `--dry-run` to print planned manifest/spine
- Inspect sources: add `--inspect` to emit a `.src/` folder next to the EPUB

- Interactive flow shows a checklist of metadata found (from flags/metadata.txt) and prompts for anything missing. Press Enter to skip and keep current/blank.
 - Confirmation step: after showing a Metadata Summary and plan, you are asked to confirm before writing the EPUB (skipped with `--no-prompt`).
## CLI Options (selected)
- Required: `--docx`, `--title`, `--cover` (author defaults to Riley E. Antrobus). The CLI interactively asks for all metadata if not provided.
- Metadata: `--author`, `--language`, `--isbn`, `--publisher`, `--pubdate YYYY-MM-DD`, `--uuid`, `--seriesName`, `--seriesIndex`, `--title-sort`, `--author-sort`, `--subjects`, `--keywords`
- Conversion: `--split-at h1|h2|pagebreak`, `--toc-depth N`, `--theme serif|sans|printlike`, `--css EXTRA.css` (optional, will be asked)
- Layout: `--justify on|off`, `--hyphenate on|off`, `--page-numbers on|off`, `--page-list on|off`, `--embed-fonts DIR` (optional, will be asked), `--cover-scale contain|cover`
  - Typography: `--font-size 1rem|12pt|14px`, `--line-height 1.5|1.6`
- Output: `--output out.epub`, `--inspect`, `--dry-run`
  - Naming: `--output-pattern "{series}-{index2}-{title}"` (placeholders: `{title}`, `{series}`, `{index}` raw, `{index2}` zero‑padded)
- Non-interactive: `--no-prompt` (use metadata.txt + flags only)
 - Tools: `--auto-install-tools` (install Pandoc/EPUBCheck automatically when missing), `--no-install-tools` (never install during build)
 - Prompt control & logs: `--prompt-all` (ask everything), `--quiet`, `--verbose`

## Cheat Sheet
- Interactive (recommended):
  - `docx2shelf` (in the DOCX folder)
  - Or: `docx2shelf build --docx manuscript.docx --cover cover.jpg --title "Book"`
- Non-interactive (CI):
  - `docx2shelf build --docx manuscript.docx --cover cover.jpg --title "Book" --language en --no-prompt`
- Dry run / plan only: `--dry-run`
- Inspect sources: `--inspect` (emits a `.src/` folder)
- Template metadata: `docx2shelf init-metadata --docx manuscript.docx --cover cover.jpg`

## Environment Setup
- pipx (global, isolated):
  - Linux/macOS: `sh scripts/install.sh --method pipx --extras all`
  - Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Method pipx -Extras all`
- venv (local dev):
  - Create + activate: `python -m venv .venv && . .venv/bin/activate` (Windows: `./.venv/Scripts/activate`)
  - Install: `pip install -e ".[dev,docx]"` (or `.[dev,pandoc]`)
- Run tests: `scripts/test.sh` or `scripts/test.ps1`

### Tools Manager (Pandoc & EPUBCheck)
Use the built‑in tools manager to install optional binaries locally (no admin):

```
# Install Pandoc (for best DOCX → HTML fidelity)
docx2shelf tools install pandoc [--version X.Y.Z]

# Install EPUBCheck (optional validation)
docx2shelf tools install epubcheck [--version A.B.C]

# Show where tools are located/resolved from
docx2shelf tools where
```

Details:
- Tools are stored under:
  - Windows: `%APPDATA%\Docx2Shelf\bin`
  - macOS/Linux: `~/.docx2shelf/bin`
- The installer attempts to verify SHA‑256 checksums (when available from releases) and retries up to 3 times on transient failures.
- The CLI prefers managed tools first, then PATH.
- During interactive builds, if Pandoc or EPUBCheck is not found, Docx2Shelf offers to install them on the spot via the tools manager.
 - You can also control install behavior from `build` with flags:
   - `--auto-install-tools` installs missing tools automatically without prompts.
   - `--no-install-tools` prevents any install attempts during the build.

## What Gets Produced
Inside the `.epub` (ZIP) you’ll see:
- `EPUB/content.opf` — metadata, manifest, spine
- `EPUB/nav.xhtml` + `EPUB/toc.ncx` — modern + legacy ToC
- `EPUB/text/landmarks.xhtml` — EPUB 3 landmarks (cover, title page, ToC, start)
- `EPUB/style/base.css` — theme CSS (+ merged user CSS)
- `EPUB/text/` — title, copyright, optional dedication/ack, and `chap_###.xhtml`
- `EPUB/images/` — cover + extracted images (if any)
- `EPUB/fonts/` — embedded fonts when provided

Notes:
- Calibre fields written: `calibre:series`, `calibre:series_index`, optional `calibre:title_sort`, `calibre:author_sort`.
- Optional page-list nav and CSS page counters (reader support varies).
- If `epubcheck` is on PATH, it runs after writing.
 - ToC depth (NAV/NCX) reflects `--toc-depth` (1–2).

## Troubleshooting Tips
- Pandoc not found / low fidelity output
  - Install Pandoc (recommended):
    - macOS (Homebrew): `brew install pandoc`
    - Linux: use your package manager or download from pandoc.org
    - Windows: install from pandoc.org and reopen your terminal
  - Add `pypandoc`: `pip install pypandoc`
- EPUBCheck not running
  - Install EPUBCheck and ensure `epubcheck` is on PATH.
    - macOS (Homebrew): `brew install epubcheck`
    - Manual: download from GitHub releases, add the wrapper script to PATH.
- Module not found `docx2shelf` when running tests
  - Set PYTHONPATH to `src`:
    - Bash: `PYTHONPATH=src pytest`
    - PowerShell: `$env:PYTHONPATH='src'; pytest`
- `docx2shelf` not found after install
  - pipx: run `pipx ensurepath`, then restart terminal.
  - pip --user: add user Scripts dir to PATH (Linux/macOS: `~/.local/bin`, Windows: `%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts`).
- Cover or paths not found
  - Run in the DOCX folder; relative paths (`cover.jpg`, `extras.css`) resolve relative to the DOCX directory.
- Invalid ISBN / Language
  - ISBN must be 13 digits with a valid checksum; language must be a BCP‑47 tag (e.g., `en`, `en-us`).
- Debugging builds
  - Use `--dry-run` to print the planned manifest/spine.
  - Use `--inspect` to emit a `.src/` folder with HTML sources.

## FAQ
- Does it work offline?
  - Yes. No telemetry. Optional tools (Pandoc, EPUBCheck) run locally if available.
- What EPUB version?
  - Targets EPUB 3 with NAV; also includes NCX for broad compatibility.
- Can it add page numbers?
  - EPUB has no universal pages. We provide optional CSS counters and an optional page‑list nav; many readers ignore them.
- Can I embed custom fonts?
  - Yes, pass `--embed-fonts DIR` (ensure you have redistribution rights). Fonts are embedded under `EPUB/fonts/`.
- How do I add custom CSS?
  - Provide `--css EXTRA.css` or set `CSS:` in metadata.txt; it merges after the selected theme.
- How are filenames and paths resolved?
  - Relative paths for cover/CSS/fonts/dedication/ack/output resolve relative to the DOCX folder.
- Can I skip prompts?
  - Yes, use `--no-prompt` with flags and/or metadata.txt.
- How do I change the output filename?
  - Use `--output MyTitle.epub` (or set `Output:` in metadata.txt). Default is series‑aware when available.
- Where does metadata live?
  - In `metadata.txt` next to the DOCX (auto‑generated on first run). CLI flags override.

## Common Errors
- Error: DOCX not found or not a .docx file
  - Ensure you’re in the manuscript’s folder and the file ends with `.docx`.
- Error: cover not found
  - Place `cover.jpg`/`cover.png` next to the DOCX or pass `--cover` (relative to the DOCX folder).
- Conversion error: No converter found
  - Install either `pypandoc` with Pandoc or `python-docx`.
- Invalid ISBN-13
  - Supply 13 digits (hyphens allowed) with a valid checksum.
- Language must be BCP‑47
  - Use tags like `en`, `en-us`, `zh-Hant-TW`.
- docx2shelf: command not found
  - After pipx: run `pipx ensurepath` and restart terminal; after pip --user: add the user scripts dir to PATH.

## Known Limitations
- EPUB page numbers are not universal
  - CSS counters and page‑list are best‑effort; many readers ignore them.
- Fallback converter fidelity
  - When Pandoc is not used, extremely complex DOCX features may not map perfectly (custom styles, intricate tables, embedded objects). The python‑docx path covers headings, paragraphs, lists, quotes, images (with alt), hyperlinks, foot/endnotes, and simple captions.
- Reader rendering differences
  - CSS support and NAV/page‑list handling vary by reading system.
- Fonts licensing
  - Embedding fonts requires you to ensure redistribution rights.
Other commands:
- `init-metadata` — generate a metadata.txt template next to a DOCX.

Output naming: If not provided, it suggests `SeriesName-##-BookTitle.epub` or `BookTitle.epub`.

## Notes & Limits
- Page numbers in EPUB are not universal; counters and page-list are best-effort and may be ignored by some readers.
- With Pandoc installed, conversion preserves more formatting; fallback covers headings, basic styling, links, lists, images (with alt), foot/endnotes, captions, quotes, and manual page breaks.
 - Calibre compatibility: writes `calibre:series`, `calibre:series_index`, and (if provided) `calibre:title_sort`, `calibre:author_sort`.

## Development
- Run tests: `pytest -q` (coverage: `pytest --cov=docx2shelf`)
- Lint/format/type‑check: `ruff check . && black . && mypy src/docx2shelf`
- Build wheel: `python -m build`
- Single‑file binary: `pyinstaller packaging/docx2shelf.spec`

## Project Layout
- `src/docx2shelf/{cli,convert,assemble,metadata,utils}.py`
- `src/docx2shelf/assets/css/*.css`, `src/docx2shelf/templates/*`
- `tests/`, `scripts/` (installers), `packaging/docx2shelf.spec`

## Troubleshooting
- "Pandoc not found": Install Pandoc or rely on the fallback (`python-docx`).
- "ebooklib required": `python -m pip install ebooklib` (included when installing the package).
- `docx2shelf` not on PATH: ensure your user scripts directory is on PATH (Linux/macOS: `~/.local/bin`; Windows: `%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts`).

## License
MIT




\n\n### Interactive by default\nRun `docx2shelf` with no arguments to start a guided, interactive build (it will read metadata.txt if present, show a checklist, prompt for missing fields, summarize, and ask to confirm before writing). Use `--no-prompt` for non-interactive runs.\n


### Auto-generation of metadata.txt
In interactive mode, if no `metadata.txt` is found next to your DOCX, the CLI creates a template automatically (after you provide the DOCX path). It may include a Cover line if you already provided it. You can edit and re-run to reuse it later.



### Run from the manuscript folder
Change into the folder that contains your `.docx` (and `cover.jpg`/`cover.png`) and run `docx2shelf`. The CLI auto-detects the only `.docx` in the folder; if there are multiple, it lets you pick one. It also auto-detects a cover named `cover.jpg`/`cover.png`. If anything is missing, it prompts you and shows a checklist.

All interactive choices use numeric pickers:
- File selections (DOCX, cover, CSS, dedication/ack, fonts dir) show numbered lists of actual filenames found in the DOCX folder only.
- Options (split-at, theme, hyphenate, justify, ToC depth, page-list, page-numbers, cover-scale, EPUBCheck) use numeric pickers with sensible defaults.

