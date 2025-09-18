# Docx2Shelf

Offline Python CLI for converting manuscripts into valid EPUB 3 ebooks.

Docx2Shelf is designed to be a comprehensive and easy-to-use tool for authors and publishers. It handles various aspects of ebook creation, including cover embedding, metadata management, content splitting, and CSS theming. It prefers Pandoc for high-fidelity conversions but includes a fallback for DOCX when Pandoc isn't available.

## Features

-   **Multiple Input Formats**: Convert from DOCX, Markdown, TXT, and HTML files
-   **Professional EPUB Output**: Creates valid EPUB 3 files with proper metadata and structure
-   **Smart Content Organization**: Automatically splits content into chapters based on headings or page breaks
-   **Beautiful Typography**: Choose from built-in themes (serif, sans, printlike) or add custom CSS
-   **Comprehensive Metadata**: Full support for title, author, ISBN, series info, and publishing details
-   **Publishing-Ready**: Built-in validation and compatibility checks for major ebook stores
-   **Plugin Support**: Extend functionality with custom plugins for specialized workflows
-   **No Internet Required**: Works completely offline - your manuscripts never leave your computer

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

**Windows Package Manager:**
```bash
winget install LightWraith8268.Docx2Shelf
```

**Scoop (Windows):**
```bash
scoop install docx2shelf
```

#### Docker (Advanced Users)
```bash
docker run -v $(pwd):/workspace ghcr.io/lightwraith8268/docx2shelf build --input manuscript.docx --title "My Book" --author "Author"
```

#### Quick Install Script

**Windows**: Download and run `install.bat` from the [releases page](https://github.com/LightWraith8268/Docx2Shelf/releases)

**macOS/Linux**:
```bash
curl -sSL https://raw.githubusercontent.com/LightWraith8268/Docx2Shelf/main/scripts/install.sh | bash
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

## Advanced Features

### Tools Manager
Install optional tools locally (no admin privileges required):

```bash
# Install Pandoc for better DOCX conversion
docx2shelf tools install pandoc

# Install EPUBCheck for validation
docx2shelf tools install epubcheck
```

### Plugins & Extensions
Extend Docx2Shelf with custom functionality:

```bash
# List available plugins
docx2shelf plugins list

# Load a custom plugin
docx2shelf plugins load my_plugin.py
```

### Document Connectors
Import from various sources (requires explicit opt-in):

```bash
# List available connectors
docx2shelf connectors list

# Convert local Markdown files
docx2shelf connectors fetch local_markdown document.md
```

### Publishing Compatibility
Check your EPUB against store requirements:

```bash
# Run compatibility checks for major stores
docx2shelf checklist --epub my-book.epub --store kdp
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