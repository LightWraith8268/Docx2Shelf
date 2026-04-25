# docx2shelf — Workflow Options

Internal ref. All flags + workflow combos. Caveman-ultra.

## Subcommands

| Cmd | Purpose |
|-----|---------|
| `build` | DOCX/MD/HTML/TXT → EPUB 3 |
| `docx` | MD/HTML/TXT/DOCX → DOCX (Pandoc) |
| `convert` | EPUB → PDF/MOBI/AZW3/Web/TXT |
| `batch` | Multi-file build, dir scan |
| `wizard` | Interactive guided build |
| `interactive` | Menu-driven CLI (Rich UI) |
| `gui` | CustomTkinter desktop |
| `tools` | Install/uninstall Pandoc + EPUBCheck |
| `plugins` | Manage plugins/hooks |
| `connectors` | Doc connectors (Notion/Drive/etc) |
| `ai` | AI metadata/genre/alt-text |
| `theme-editor` | Visual CSS theme editor |
| `list-themes` / `preview-themes` | Show 15 built-in themes |
| `init-metadata` | Emit `metadata.txt` template |
| `list-profiles` | KDP/Kobo/Apple/Generic/Legacy presets |
| `update` | Self-update (skipped offline) |
| `doctor` | Env diagnostics |
| `checklist` | Store compat checks |
| `quality` | Quality score |
| `validate` | EPUBCheck wrapper |

## Build flags (full surface)

### IO
- `--input PATH` — file or dir (.docx/.md/.txt/.html)
- `--cover PATH` — jpg/png; auto-detects `cover.{png,jpg}` in input dir
- `--output PATH` — explicit .epub
- `--output-pattern STR` — placeholders `{title} {series} {index} {index2}`

### Metadata (CLI flags or auto from `metadata.txt`/`metadata.md`)
`--title --author --seriesName --seriesIndex --title-sort --author-sort --description --isbn --language --publisher --pubdate --uuid --subjects --keywords`

### Structure
- `--split-at {h1,h2,h3,pagebreak,mixed}` — chapter split
- `--mixed-split-pattern` — e.g. `h1:main,pagebreak:appendix`
- `--toc-depth N` — 1–6
- `--chapter-start-mode {auto,manual,mixed}`
- `--chapter-starts "Prologue,Chapter 1,..."` — manual TOC
- `--reader-start-chapter "Chapter 1"` — landmark

### Style
- `--theme NAME` — academic/biography/business/childrens/contemporary/dyslexic/fantasy/mystery/night/printlike/romance/sans/scifi/serif/thriller
- `--css PATH` — extra CSS merge
- `--font-size 1rem` `--line-height 1.5`
- `--hyphenate {on,off}` `--justify {on,off}`
- `--page-numbers {on,off}` `--page-list {on,off}`
- `--cover-scale {contain,cover}`
- `--vertical-writing` — CJK
- `--epub-version 3` `--epub2-compat`

### Images
- `--image-quality 1-100`
- `--image-max-width N` `--image-max-height N`
- `--image-format {original,webp,avif}`
- `--enhanced-images` — CMYK/transparency/large

### Fonts
- `--embed-fonts DIR` — TTF/OTF dir

### Front/back matter
- `--dedication PATH` — plain text
- `--ack PATH` — acknowledgements

### Profiles + store
- `--profile {kdp,kobo,apple,generic,legacy}` — preset bundle
- `--store-profile {kdp,apple,kobo,google,bn,generic}` — output tuning

### AI (opt-in, network unless local model)
- `--ai-enhance` — metadata enrichment
- `--ai-genre` — genre + keyword detection
- `--ai-alt-text` — image alt text
- `--ai-interactive` — confirm each suggestion
- `--ai-config PATH` — JSON config

### Validation + output
- `--epubcheck {on,off}` — run EPUBCheck after build
- `--inspect` — emit unzipped tree
- `--dry-run` — manifest/spine only, no write
- `--preview` `--preview-port N` — live browser preview
- `--json-output PATH` — machine-readable results

### Prompts
- `--no-prompt` — flags-only, no stdin
- `--prompt-all` — re-prompt every field
- `--auto-install-tools` / `--no-install-tools`
- `--quiet` `--verbose`

### Automation (offline + watch)
- `--offline` — preflight pandoc + epubcheck local; refuse if missing (exit 5); skips update check
- `--watch` — poll input/cover/metadata mtimes, rebuild on change
- `--watch-interval N` — poll seconds (default 2.0)
- Env: `DOCX2SHELF_OFFLINE=1` — same as `--offline` globally

## docx subcommand flags
- `--input PATH` (req) — md/html/txt/docx
- `--output PATH` — default `<stem>.docx`
- `--reference-doc PATH` — Pandoc styled template
- `--metadata PATH` — metadata.txt/.md → DOCX core props (title/creator/lang/publisher/description/subject/keywords)
- `--quiet`

## convert (EPUB → other)
- `input` (positional) — .epub
- `--format {pdf,mobi,azw3,web,txt,text}`
- `--output PATH`
- `--quality {standard,high,web}`
- `--compression`

## batch
- `--dir PATH` (req)
- `--pattern "*.docx"`
- `--output-dir PATH`
- `--parallel` `--max-workers N`
- `--report PATH`
- `--profile --theme --store-profile --epub-version --image-format --epubcheck`

## tools
- `install {pandoc,epubcheck}` — bundles to `%LOCALAPPDATA%\docx2shelf\bin\` (Win) or platformdirs equiv
- `uninstall {pandoc,epubcheck}`
- `where` — show paths
- `doctor` — health check
- `bundle` — emit offline installer pack

## Workflow recipes

### Recipe 1 — One-shot build (CLI flags only)
```
docx2shelf build --input book.docx --cover cover.png \
  --title "T" --author "A" --no-prompt --quiet
```

### Recipe 2 — Auto-metadata (drop file conventions)
Layout:
```
book/
  Manuscript.md
  metadata.md          # or metadata.txt
  cover.png
```
Cmd:
```
docx2shelf build --input book/Manuscript.md --no-prompt --quiet
```
Auto-detects cover + metadata. Zero flags beyond input.

### Recipe 3 — Offline preflight (CI / airgap)
```
docx2shelf tools install pandoc
docx2shelf tools install epubcheck
DOCX2SHELF_OFFLINE=1 docx2shelf build --input M.md --no-prompt --offline
```
Exit 5 if tools missing. Zero net calls (update check skipped).

### Recipe 4 — Watch loop (Claude Code idle)
```
DOCX2SHELF_OFFLINE=1 docx2shelf build \
  --input book/Manuscript.md --cover book/cover.png \
  --no-prompt --quiet --offline --watch --watch-interval 2
```
Tracks input + cover + metadata. Rebuilds on mtime change. Ctrl-C clean exit.

### Recipe 5 — Batch dir
```
docx2shelf batch --dir manuscripts/ --pattern "*.docx" \
  --output-dir epubs/ --parallel --max-workers 4 \
  --profile kdp --theme serif --report batch.json
```

### Recipe 6 — Profile + store target (KDP)
```
docx2shelf build --input M.md --profile kdp --store-profile kdp \
  --image-format webp --epubcheck on --no-prompt
```

### Recipe 7 — Preview before build
```
docx2shelf build --input M.md --preview --preview-port 8000
```
Browser opens; no .epub written.

### Recipe 8 — DOCX gen from Markdown
```
docx2shelf docx --input M.md --metadata metadata.md \
  --reference-doc styles.docx --output Book.docx
```

### Recipe 9 — EPUB → PDF
```
docx2shelf convert book.epub --format pdf --quality high --output book.pdf
```

### Recipe 10 — JSON output (CI parse)
```
docx2shelf build --input M.md --no-prompt --json-output result.json
```
Parse `result.json` for pass/fail + warnings.

### Recipe 11 — Custom themes + fonts
```
docx2shelf build --input M.md --theme fantasy --css extra.css \
  --embed-fonts fonts/ --font-size 1.05rem --line-height 1.6
```

### Recipe 12 — Mixed split (multi-section book)
```
docx2shelf build --input M.md --split-at mixed \
  --mixed-split-pattern "h1:main,pagebreak:appendix"
```

## Exit codes
- `0` success
- `1` user cancel / generic
- `2` validation/arg error
- `3` EPUB validation failed (EPUBCheck errors)
- `4` Pandoc/conversion failure (docx subcmd)
- `5` offline preflight failed (missing local tools)

## Metadata file format
Plain `key: value` lines. Both `metadata.txt` + `metadata.md` accepted. Auto-loaded from input dir or CWD.
```
title: My Book
author: Jane Doe
language: en
description: ...
isbn:
series:
series_index:
publisher:
pubdate: 2026-04-24
keywords: epic, fantasy
subjects: Fiction, Fantasy
```

## Auto-discovery rules
1. Cover: `cover.png` / `cover.jpg` / `cover.jpeg` in input dir
2. Metadata: `metadata.txt` then `metadata.md` (input dir → CWD fallback)
3. Tools: `pandoc_path()` checks tools dir → PATH; `epubcheck_cmd()` checks wrapper → versioned subdir → bare jar → PATH

## Offline guarantees
With `--offline` or `DOCX2SHELF_OFFLINE=1`:
- No update check thread
- Preflight blocks if pandoc/epubcheck not local
- AI flags will still attempt net unless local model configured
- Plugins may fetch — depends on plugin
- `pypandoc` uses `PYPANDOC_PANDOC` env → bundled binary

## Globals
- `DOCX2SHELF_OFFLINE=1` — global offline gate
- `PYTHONIOENCODING=utf-8` — fallback if stdout reconfigure fails (already handled in `error_handler.py`)
- `HYPOTHESIS_PROFILE=ci` — caps property-test examples
