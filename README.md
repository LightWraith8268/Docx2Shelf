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
- Linux/macOS: `sh scripts/install.sh --method pipx --extras all [--with-tools all]`
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Method pipx -Extras all -WithTools all`

Alternative:
- From source (dev): `python -m venv .venv && . .venv/bin/activate` (Windows: `./.venv/Scripts/activate`), then `pip install -e ".[dev]"` (optionally `.[docx]`, `.[pandoc]`).
- User install: `python -m pip install --user .`

Optional tooling via installer:
- `--with-tools pandoc|epubcheck|all` will pre-install tools using `docx2shelf tools install ...` after the app is installed.

Optional tools: Install Pandoc (for best DOCX conversion) and EPUBCheck (for validation).

### Metadata file (optional)
Place a `metadata.txt` next to your `.docx` to auto-fill prompts. Example:

```
Title: Book Title
Author: Author Name
Language: en
SeriesName: Series Name
SeriesIndex: 01
Description: ...
ISBN: 9780306406157
Publisher: Example House
PubDate: 2024-07-01
UUID: 123e4567-e89b-12d3-a456-426614174000
Subjects: Space, Adventure
Keywords: sci-fi, epic
Title-Sort: Book Title, The
Author-Sort: Last, First
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

Managed tools removal (optional):
- Linux/macOS: `sh scripts/uninstall.sh --remove-tools`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts/uninstall.ps1 -RemoveTools`
  - This clears the Docx2Shelf tools cache (Pandoc/EPUBCheck) from the user profile.

## Quickstart
```
docx2shelf build \
  --docx manuscript.docx \
  --cover cover.jpg \
  --title "Book Title" \
  --author "Author Name" \
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
- Required: `--docx`, `--title`, `--cover` (author defaults are configurable). The CLI interactively asks for all metadata if not provided.
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

Uninstalling managed tools:
```
docx2shelf tools uninstall pandoc|epubcheck|all
```

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

## License
MIT




\n\n

