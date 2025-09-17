# Project Overview

This project contains `Docx2Shelf`, a command-line tool written in Python for converting DOCX files into EPUB 3 ebooks. It is designed to work completely offline. The tool can use Pandoc for high-quality conversion but also includes a fallback mechanism if Pandoc is not installed.

The project is structured as a standard Python package with the main source code located in the `src/docx2shelf` directory. It uses `pyproject.toml` to manage project metadata and dependencies. The core dependencies include `ebooklib` for creating the EPUB file, with optional dependencies for `python-docx` (for the fallback converter) and `pypandoc` (for Pandoc integration).

The application is feature-rich, supporting:
-   EPUB 3 creation with customizable CSS themes.
-   Embedding covers, fonts, and other assets.
-   Rich metadata support, including Calibre-compatible fields.
-   Automatic chapter splitting based on headings or page breaks.
-   An interactive mode that prompts the user for missing information.
-   A built-in tool manager for installing and managing Pandoc and EPUBCheck.

# Building and Running

The project includes scripts for installation and testing on both Windows and Linux/macOS.

## Installation

The recommended way to install the tool is using `pipx`, which installs the package in an isolated environment.

-   **Windows (PowerShell)**:
    ```powershell
    powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Method pipx -Extras all -WithTools all
    ```
-   **Linux/macOS**:
    ```bash
    sh scripts/install.sh --method pipx --extras all --with-tools all
    ```

For development, you can set up a virtual environment:

1.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv && . .venv/bin/activate
    ```
    (On Windows, use `.venv\Scripts\activate`)
2.  Install the project in editable mode with development dependencies:
    ```bash
    pip install -e ".[dev]"
    ```

## Running the Tool

Once installed, the tool can be run using the `docx2shelf` command. The main entry point is the `main` function in `src/docx2shelf/cli.py`.

The tool has three main subcommands:
-   `build`: The primary command for converting a DOCX file to EPUB.
-   `init-metadata`: Creates a template `metadata.txt` file.
-   `tools`: Manages optional tools like Pandoc and EPUBCheck.

A typical `build` command looks like this:
```bash
docx2shelf build \
  --docx manuscript.docx \
  --cover cover.jpg \
  --title "Book Title" \
  --author "Author Name"
```

If run without arguments, the tool will enter an interactive mode to guide the user through the process.

## Running Tests

The project uses `pytest` for testing. Test files are located in the `tests/` directory. You can run the tests using the provided scripts:

-   **Windows (PowerShell)**: `scripts\test.ps1`
-   **Linux/macOS**: `scripts/test.sh`

# Development Conventions

-   **Linting and Formatting**: The project uses `ruff` for linting and `black` for code formatting. The configuration for these tools can be found in `pyproject.toml`.
-   **Typing**: The project uses type hints, and `mypy` is included in the development dependencies for static type checking.
-   **Contribution**: The `CONTRIBUTING.md` file (if it existed) would likely contain guidelines for contributing to the project.
-   **Dependencies**: Project dependencies are managed in `pyproject.toml`.
-   **CLI**: The command-line interface is built using Python's `argparse` module.
