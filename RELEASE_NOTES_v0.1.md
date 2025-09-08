# Docx2Shelf 0.1

Initial public release of the Docx2Shelf CLI.

## Highlights
- Interactive by default: runs a guided flow (checklist → prompts → summary → confirm).
- Numeric pickers for all interactive choices (files and options), scoped to the DOCX folder.
- metadata.txt support: auto-load and auto-generate (template next to DOCX).
- Output naming patterns: `--output-pattern "{series}-{index2}-{title}"`.
- Typography flags: `--font-size`, `--line-height` merged into the theme CSS.
- Calibre metadata: writes `calibre:series`, `calibre:series_index`, optional `calibre:title_sort`, `calibre:author_sort`.
- EPUB structure: OPF, NAV, NCX, landmarks, optional page-list; stable heading anchors; CSS theme + user CSS.
- Relative paths resolve relative to the DOCX directory (cover, CSS, fonts, dedication/ack, output).
- Tools Manager: `docx2shelf tools install pandoc|epubcheck` (with checksum verification + retry) and `docx2shelf tools where`.
- Interactive auto-install offers, plus flags: `--auto-install-tools`, `--no-install-tools`.

## Install
- Linux/macOS: `sh scripts/install.sh --method pipx --extras all [--with-tools all]`
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Method pipx -Extras all -WithTools all`

Alternative: `pip install -e ".[dev,docx]"` (or `.[dev,pandoc]`) in a venv.

## Quickstart
```
# Run in the manuscript folder
# Will auto-detect a single .docx and cover.jpg/png; otherwise pick by number

# Interactive
docx2shelf
# or
docx2shelf build --docx manuscript.docx --cover cover.jpg --title "Book Title"

# Non-interactive (CI)
docx2shelf build \
  --docx manuscript.docx --cover cover.jpg \
  --title "Book Title" --language en \
  --no-prompt --auto-install-tools
```

## Known Limitations
- EPUB page numbers are not universal; counters and page‑list may be ignored by some readers.
- Fallback converter via python‑docx does not yet handle extremely complex DOCX features (advanced tables, embedded objects);
  install Pandoc for best fidelity.

## Troubleshooting
- Install Pandoc for high fidelity: use the Tools Manager or install system-wide.
- Install EPUBCheck for validation; summary prints after build (respects `--quiet/--verbose`).
- If `docx2shelf` is not on PATH after install, ensure pipx/user scripts directory is on PATH and restart terminal.

## Tag
- v0.1

## Next
- CI pipeline (tests + artifacts), EPUBCheck summary improvements, table handling in fallback path, output pattern extensions.
