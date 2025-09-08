# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv && . .venv/bin/activate  # Linux/macOS
python -m venv .venv && . .venv\Scripts\activate  # Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run tests (preferred)
pytest -q
# Or use platform scripts
scripts/test.sh     # Linux/macOS
scripts/test.ps1    # Windows
```

### Code Quality
```bash
# Lint, format, and type check
ruff check .
black .
mypy src/docx2shelf

# Build packages
python -m build
```

### Installation Scripts
```bash
# Full installation with tools
scripts/install.sh --method pipx --extras all --with-tools all     # Linux/macOS
scripts/install.ps1 -Method pipx -Extras all -WithTools all        # Windows

# Uninstall
scripts/uninstall.sh --remove-tools     # Linux/macOS
scripts/uninstall.ps1 -RemoveTools      # Windows
```

### Tools Management
```bash
# Install optional tools locally (no admin required)
docx2shelf tools install pandoc
docx2shelf tools install epubcheck
docx2shelf tools where
docx2shelf tools uninstall all
```

## Architecture Overview

### Core Components
- **cli.py** (36K LOC) - Main CLI interface with argument parsing and interactive prompts
- **convert.py** - DOCX to HTML conversion (Pandoc preferred, fallback parser)
- **assemble.py** - EPUB assembly from HTML chunks, CSS themes, metadata
- **metadata.py** - Metadata handling and build options
- **tools.py** - Managed tools installer for Pandoc/EPUBCheck
- **utils.py** - Common utilities and prompts

### Data Flow
1. **Input Processing**: DOCX + metadata.txt → structured metadata and build options
2. **Conversion**: DOCX → HTML (via Pandoc or local parser)
3. **Splitting**: HTML → chapters (by headings or pagebreaks)
4. **Assembly**: Chapters + assets → EPUB structure with OPF/NAV/NCX
5. **Output**: Valid EPUB 3 with optional EPUBCheck validation

### Key Features
- **Offline Operation**: No network calls during conversion
- **Graceful Fallbacks**: Pandoc preferred, local parser when unavailable
- **Interactive Metadata**: CLI prompts for missing fields, respects metadata.txt
- **Theme System**: Built-in CSS themes (serif/sans/printlike) with user CSS merging
- **Tools Management**: Local binary installation without admin privileges
- **Cross-Platform**: Windows/macOS/Linux support with platform-specific scripts

### Asset Structure
```
src/docx2shelf/
├── assets/css/          # Built-in themes
├── templates/           # XHTML/XML templates
└── *.py                # Core modules
```

### Configuration Files
- **metadata.txt** - User-facing metadata file (key: value format)
- **pyproject.toml** - Package config, ruff/black settings (line-length: 100)
- **CONTRIBUTING.md** - Detailed dev setup and guidelines

### Testing
- Minimal test suite in `tests/` (pytest framework)
- Focus on core conversion and splitting logic
- Run with `pytest -q` or platform scripts

### Optional Dependencies
- **docx**: python-docx for local DOCX parsing
- **pandoc**: pypandoc for high-fidelity conversion
- **dev**: pytest, ruff, black, mypy, build tools

Tools are managed separately via the built-in tools manager, stored in:
- Windows: `%APPDATA%\Docx2Shelf\bin`
- Unix: `~/.docx2shelf/bin`