# Docx2Shelf

Offline Python CLI for converting manuscripts into valid EPUB 3 ebooks.

Docx2Shelf is designed to be a comprehensive and easy-to-use tool for authors and publishers. It handles various aspects of ebook creation, including cover embedding, metadata management, content splitting, and CSS theming. It prefers Pandoc for high-fidelity conversions but includes a fallback for DOCX when Pandoc isn't available.

## Features

-   **Broad Input Compatibility**: Convert manuscripts from `.docx`, `.txt`, `.md` (Markdown), `.html`, and `.htm` file formats.
-   **Flexible Content Handling**: Process single manuscript files or entire directories of files (e.g., one file per chapter), which the tool intelligently processes as individual sections.
-   **Rich Metadata Support**: Embed comprehensive metadata including title, author, language (BCP-47), ISBN/UUID, publisher, date, and Calibre-compatible series information.
-   **Customizable Output**: Apply various CSS themes (serif, sans, printlike), embed custom fonts, merge user-defined CSS, and control content splitting (at headings or pagebreaks).
-   **Interactive & Automated Workflows**: Use the interactive CLI for guided setup or integrate into automated pipelines for non-interactive builds.
-   **Built-in Tool Management**: Easily install and manage optional tools like Pandoc (for best conversion fidelity) and EPUBCheck (for validation) directly through the CLI.
-   **Automatic Updates**: The tool includes an automatic update checker that notifies you of new releases and provides a simple command to upgrade.

## Installation

Docx2Shelf requires **Python 3.11 or newer**.

### Quick Install Options

Choose the method that works best for your system:

#### PyPI (Recommended for Python users)
```bash
pipx install docx2shelf
# or with pip:
pip install docx2shelf
```

#### Package Managers

**Homebrew (macOS/Linux):**
```bash
brew install docx2shelf
```

**Windows Package Manager (winget):**
```bash
winget install LightWraith8268.Docx2Shelf
```

**Scoop (Windows):**
```bash
scoop install docx2shelf
```

#### Docker
```bash
# Run directly
docker run -v $(pwd):/workspace ghcr.io/lightwraith8268/docx2shelf build --input manuscript.docx --title "My Book" --author "Author"

# Or use as an alias
alias docx2shelf='docker run --rm -v $(pwd):/workspace ghcr.io/lightwraith8268/docx2shelf'
```

#### Windows Install Script (Legacy)

For Windows users who prefer the automated setup script:

1.  **Download `install.bat`**: Get it from the [GitHub Releases page](https://github.com/LightWraith8268/Docx2Shelf/releases).
2.  **Run the script**: Double-click `install.bat` and follow the prompts.

#### Linux / macOS Install Script (Legacy)

```bash
sh scripts/install.sh --method pipx --extras all --with-tools all
```

### Updating Docx2Shelf

To update your installed Docx2Shelf to the latest version, simply run:

```bash
docx2shelf update
```

## Quickstart

To convert a manuscript, navigate to its directory and run `docx2shelf build`. The tool will guide you through the process interactively.

```bash
docx2shelf build \
  --input manuscript.docx \
  --cover cover.jpg \
  --title "Book Title" \
  --author "Author Name" \
  --language en \
  --theme serif \
  --split-at h1 \
  --justify on --hyphenate on
```

-   **Dry run**: Add `--dry-run` to print the planned manifest/spine without creating the EPUB.
-   **Inspect sources**: Add `--inspect` to emit a `.src/` folder next to the EPUB for debugging.

## CLI Options (Selected)

-   **Required**: `--input` (path to manuscript file or directory), `--title`, `--cover` (author defaults are configurable).
-   **Metadata**: `--author`, `--language`, `--isbn`, `--publisher`, `--pubdate YYYY-MM-DD`, `--uuid`, `--seriesName`, `--seriesIndex`, `--title-sort`, `--author-sort`, `--subjects`, `--keywords`.
-   **Conversion**: `--split-at h1|h2|pagebreak`, `--toc-depth N`, `--theme serif|sans|printlike`, `--css EXTRA.css`.
-   **Layout**: `--justify on|off`, `--hyphenate on|off`, `--page-numbers on|off`, `--page-list on|off`, `--embed-fonts DIR`, `--cover-scale contain|cover`, `--font-size`, `--line-height`.
-   **Output**: `--output out.epub`, `--output-pattern "{series}-{index2}-{title}"`, `--inspect`, `--dry-run`.
-   **Non-interactive**: `--no-prompt` (use metadata.txt + flags only), `--auto-install-tools`, `--no-install-tools`, `--prompt-all`, `--quiet`, `--verbose`.

## Tools Manager (Pandoc & EPUBCheck)

Use the built-in tools manager to install optional binaries locally (no admin privileges required):

```bash
# Install Pandoc (for best DOCX → HTML fidelity)
docx2shelf tools install pandoc [--version X.Y.Z]

# Install EPUBCheck (optional validation)
docx2shelf tools install epubcheck [--version A.B.C]

# Show where tools are located/resolved from
docx2shelf tools where
```

## What Gets Produced

Inside the `.epub` (ZIP) you’ll find:

-   `EPUB/content.opf` — metadata, manifest, spine
-   `EPUB/nav.xhtml` + `EPUB/toc.ncx` — modern + legacy Table of Contents
-   `EPUB/text/landmarks.xhtml` — EPUB 3 landmarks (cover, title page, ToC, start)
-   `EPUB/style/base.css` — theme CSS (+ merged user CSS)
-   `EPUB/text/` — title, copyright, optional dedication/acknowledgements, and `chap_###.xhtml` files
-   `EPUB/images/` — cover + extracted images (if any)
-   `EPUB/fonts/` — embedded fonts when provided

## License

MIT

## Changelog

For a detailed list of changes, please refer to the [CHANGELOG.md](CHANGELOG.md) file.