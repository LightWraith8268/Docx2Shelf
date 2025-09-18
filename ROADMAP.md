# Docx2Shelf Improvement Roadmap

This document outlines the planned improvements for Docx2Shelf, categorized by impact area. As sections are completed, their status will be updated, and a new patch version will be released.

## 1) Formatting fidelity (DOCX → clean XHTML)
Status: Completed

### Robust DOCX fallback parser ✓
Expand coverage for tracked changes, comments, complex tables, text boxes/shapes, equations, headers/footers, footnotes/endnotes.
Why now: you already prefer Pandoc but promise a graceful fallback; that's core to quality when Pandoc isn't present.

### Style mapping ✓
Expose a styles.json to map Word styles → CSS classes, with user-override.

### "Rasterize-on-escape" ✓
Optional image fallback for layout elements the parser can't translate cleanly (preserves author intention).

## 2) Table of contents & splitting
Status: Completed

### Arbitrary ToC depth (≥3) and mixed split strategy ✓
(e.g., h1 plus pagebreaks in appendices). Current docs mention --split-at and toc depth control; extend flexibility.

### Per-section start markers ✓
(reader start page + landmarks are already emitted; let users choose "start" chapter via metadata flag).

## 3) Typography, CSS, and assets
Status: Completed

### Theme pack system ✓
Beyond serif/sans/printlike (genre presets; night-mode friendly). Existing themes are noted; formalize a discoverable theme API.

### Font subsetting ✓
(via fontTools) when --embed-fonts is used to shrink EPUBs; warn on licensing.

### Image pipeline ✓
Cover scaling is supported now; add auto-resize/compress (long-edge cap, WebP/AVIF with fallback), and per-image DPI rules.

## 4) Accessibility & compliance
Status: Completed

### EPUB Accessibility 1.1 pass ✓
Auto-prompt for missing alt text, add ARIA landmarks and accessMode/accessibilityFeature metadata.

### Default EPUBCheck run ✓
(opt-out instead of opt-in) with friendly summary; you already integrate EPUBCheck when present/on PATH and via Tools Manager—flip the default and surface actionable hints.

### Language/script support ✓
RTL (Arabic/Hebrew), CJK vertical options, hyphenation dictionaries; you already have --hyphenate/--justify. Make language-aware defaults.

### EPUB 2 compatibility mode ✓
For old readers (dual-nav/NCX already present; add stricter CSS constraints).

## 5) UX & workflow
Status: Completed

### Live preview ✓
--preview builds .src/ (you already support --inspect) and opens a local viewer to catch layout issues pre-zip.

### Profiles & presets ✓
--profile kdp|kobo|apple|generic to pre-fill metadata and CSS knobs. Your metadata/template flow is strong—extend it to full presets.

### Batch mode ✓
docx2shelf build --dir manuscripts/ --pattern *.docx --parallel with shared defaults.

### Machine-readable logs ✓
--json output for CI pipelines.

## 6) Metadata & publishing
Status: ✓ Complete

### Richer metadata keys in metadata.txt ✓
Extended metadata.txt template with roles (editor, illustrator, translator, narrator, designer, contributor), BISAC codes validation, age ranges, reading levels, copyright information, pricing, and content warnings. Full schema validation with detailed error reporting.

### KDP/Apple/Kobo checklists ✓
Comprehensive publishing store compatibility system with `docx2shelf checklist` command. Store-specific validation for cover dimensions, file formats, metadata requirements, and platform-specific pitfalls. Supports JSON output for CI integration.

## 7) Automation & ecosystem
Status: ✓ Complete

### First-party GitHub Action ✓
Matrix (Windows/macOS/Linux), with/without Pandoc, Python 3.11+. Artifacts: .epub, .src/, EPUBCheck report. Reusable action.yml with comprehensive input parameters and artifact management.

### Plugins ✓
Hooks for pre-convert (sanitize DOCX), post-convert (html transforms), and metadata resolvers. Full plugin management CLI with load/enable/disable commands.

### Optional connectors ✓
(kept offline by default): local Markdown → EPUB; gated cloud imports (Google Docs/OneDrive) via explicit opt-in to preserve the project's offline stance. Network consent system maintains "No network calls required" default.

## 8) Packaging & distribution
Status: ✓ Complete

### Publish to PyPI ✓
Automated PyPI publishing via GitHub Actions with trusted publishing. pipx install path documented in README, plus Homebrew, winget, Scoop, and Docker image support.

### Signed tool downloads ✓
Enhanced tool download system with SHA-256 verification (existing) plus optional GPG signature verification for supported tools.

## 9) Tools Manager polish
Status: To Do

### Version pin sets
(docx2shelf tools pin preset stable|latest)

### Health check
(tools doctor) with PATH diagnostics

### Offline bundle mode
(pre-downloaded zips in a cache dir) for air-gapped machines.

## 10) Tests & QA
Status: To Do

### Golden EPUB fixtures
Snapshot tests over known DOCX patterns (simple, footnotes, tables, poetry, images, RTL).

### Property-based tests
For split logic, naming patterns (you already support {index2} zero-pad, etc.).

### Reader smoke tests
CI step that opens the built EPUB with a headless renderer (or checks CSS support lists) to catch regressions.

## 11) Docs & onboarding
Status: To Do

### Screenshots/GIFs
(interactive prompts, preview, tools install)

### “Quality cookbook”
(how to structure DOCX styles; common pitfalls; before/after)

### Sample theme gallery and starter metadata.txt variants
(KDP/Kobo/Apple).

## 12) Governance & community
Status: To Do

### Add LICENSE (if missing), CONTRIBUTING.md, Code of Conduct, and a “good first issue” board.

### Issue templates
For bug reports with a redacted DOCX + produced .src/