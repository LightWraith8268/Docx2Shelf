"""Conversion and metadata initialization handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_init_metadata(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file() or input_path.suffix.lower() not in {
        ".docx",
        ".md",
        ".txt",
        ".html",
        ".htm",
    }:
        print(f"Error: Input file not found or not a supported type: {input_path}", file=sys.stderr)
        return 2
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.parent / "metadata.txt"
    )
    if out_path.exists() and not args.force:
        print(
            f"Refusing to overwrite existing file: {out_path}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 2

    title_guess = input_path.stem.replace("_", " ").replace("-", " ").strip().title()
    from ..metadata import build_output_filename

    output_guess = build_output_filename(title_guess, None, None)

    lines = [
        "# Docx2Shelf metadata template",
        "# Lines starting with # are ignored. Keys are case-insensitive.",
        "# Use key: value or key=value. Paths can be relative to this DOCX folder.",
        "# Output naming (optional): you can pass --output-pattern on the CLI",
        '# Example: --output-pattern "{series}-{index2}-{title}"',
        "",
        f"Title: {title_guess}",
        "Author:",
        "Language: en",
        "",
        "# Basic metadata",
        "SeriesName:",
        "SeriesIndex:",
        "Title-Sort:",
        "Author-Sort:",
        "Description:",
        "ISBN:",
        "Publisher:",
        "PubDate: 2024-01-01",
        "UUID:",
        "Subjects: ",
        "Keywords: ",
        "",
        "# Extended metadata (roles, classifications, etc.)",
        "Editor:",
        "Illustrator:",
        "Translator:",
        "Narrator:",
        "Designer:",
        "Contributor:",
        "BISAC-Codes: ",
        "Age-Range:",
        "Reading-Level:",
        "Copyright-Holder:",
        "Copyright-Year:",
        "Rights:",
        "Price:",
        "Currency:",
        "Print-ISBN:",
        "Audiobook-ISBN:",
        "Series-Type:",
        "Series-Position:",
        "Publication-Type:",
        "Target-Audience:",
        "Content-Warnings: ",
        "",
        "# Assets",
        f"Cover: {args.cover or ''}",
        "CSS:",
        "Embed-Fonts:",
        "",
        "# Conversion & layout",
        "Theme: serif",
        "Split-At: h1",
        "ToC_Depth: 2",
        "Chapter-Start-Mode: auto",
        "Chapter-Starts:",
        "Hyphenate: on",
        "Justify: on",
        "Page-List: off",
        "Page-Numbers: off",
        "Cover-Scale: contain",
        "",
        "# Output & validation",
        f"Output: {output_guess}",
        "EPUBCheck: on",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote template: {out_path}")
    return 0


def run_convert(args) -> int:
    """Handle EPUB format conversion."""
    from pathlib import Path

    from ..conversion import check_format_dependencies, convert_epub

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    if not input_path.suffix.lower() == ".epub":
        print(f"Error: Input file must be an EPUB file, got: {input_path.suffix}")
        return 1

    # Check format dependencies if requested
    if args.check_deps:
        print(f"Checking dependencies for {args.format} format...")
        deps = check_format_dependencies(args.format)

        if not deps:
            print(f"No external dependencies required for {args.format}")
            return 0

        print("Dependencies:")
        for dep, available in deps.items():
            status = "✓ Available" if available else "✗ Not found"
            print(f"  {dep}: {status}")

        # Check if any required dependencies are missing
        if args.format == "pdf" and not any(deps.values()):
            print("\nError: PDF conversion requires either weasyprint or prince")
            print("Install with: pip install weasyprint")
            return 1
        elif args.format in ["mobi", "azw3"] and not deps.get("calibre"):
            print(f"\nError: {args.format.upper()} conversion requires Calibre")
            print("Install from: https://calibre-ebook.com/download")
            return 1

        return 0

    # Generate output path if not specified
    if args.output:
        output_path = Path(args.output)
    else:
        # Auto-generate based on format
        if args.format == "web":
            output_path = input_path.parent / f"{input_path.stem}_web"
        else:
            ext_map = {
                "pdf": ".pdf",
                "mobi": ".mobi",
                "azw3": ".azw3",
                "txt": ".txt",
                "text": ".txt",
            }
            ext = ext_map.get(args.format, f".{args.format}")
            output_path = input_path.parent / f"{input_path.stem}{ext}"

    # Read custom CSS if provided
    custom_css = None
    if args.css:
        css_path = Path(args.css)
        if css_path.exists():
            custom_css = css_path.read_text(encoding="utf-8")
        else:
            print(f"Warning: CSS file not found: {css_path}")

    # Extract metadata from args for conversion
    metadata = {
        "title": getattr(args, "title", None),
        "author": getattr(args, "author", None),
    }

    print(f"Converting {input_path} to {args.format.upper()}...")
    print(f"Output: {output_path}")

    # Perform conversion
    success = convert_epub(
        epub_path=input_path,
        format_type=args.format,
        output_path=output_path,
        quality=args.quality,
        compression=args.compression,
        metadata=metadata,
        custom_css=custom_css,
        page_size=args.page_size,
        margin=args.margin,
        font_size=getattr(args, "font_size", "12pt"),
        font_family=args.font_family,
        include_toc=args.include_toc,
        include_cover=args.include_cover,
    )

    if success:
        print("✓ Conversion completed successfully!")
        if args.format == "web":
            print(f"Open {output_path / 'index.html'} in your browser to view")
        return 0
    else:
        print("✗ Conversion failed")
        return 1
