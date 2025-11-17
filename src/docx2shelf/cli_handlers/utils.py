"""Utility functions for CLI handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..metadata import EpubMetadata, BuildOptions


def apply_metadata_dict(args: argparse.Namespace, md: dict, base_dir: Path | None) -> None:
    """Apply metadata dictionary to argparse namespace.

    This function takes a metadata dictionary (usually from metadata.txt) and applies
    it to the argument namespace, handling aliases and path resolution.

    Args:
        args: The argument namespace to update
        md: Dictionary of metadata key-value pairs
        base_dir: Base directory for resolving relative paths
    """
    if not md:
        return

    def get(k: str):
        # allow simple aliases
        aliases = {
            "series": "seriesName",
            "seriesname": "seriesName",
            "series_index": "seriesIndex",
            "seriesindex": "seriesIndex",
            "title-sort": "title_sort",
            "author-sort": "author_sort",
        }
        k2 = aliases.get(k.lower(), k)
        return md.get(k, md.get(k.lower(), md.get(k2, md.get(k2.lower()))))

    def pathify(val: str | None) -> str | None:
        if not val:
            return None
        p = Path(val)
        if not p.is_absolute() and base_dir:
            p = (base_dir / p).resolve()
        return str(p)

    # Core (file overrides defaults; CLI may still override if passed explicitly)
    if (not args.input) and get("input"):
        args.input = get("input")
    if (not args.cover) and get("cover"):
        args.cover = pathify(get("cover"))
    if (not args.title) and get("title"):
        args.title = get("title")
    if (not args.author) and get("author"):
        args.author = get("author")
    if (not args.language) and get("language"):
        args.language = get("language")
    # Optional metadata
    if get("seriesname") or get("series"):
        args.seriesName = get("seriesname") or get("series")
    if get("seriesindex"):
        args.seriesIndex = get("seriesindex")
    if get("title_sort") or get("title-sort"):
        setattr(args, "title_sort", get("title_sort") or get("title-sort"))
    if get("author_sort") or get("author-sort"):
        setattr(args, "author_sort", get("author_sort") or get("author-sort"))
    if get("description"):
        args.description = get("description")
    if get("isbn"):
        args.isbn = get("isbn")
    if get("publisher"):
        args.publisher = get("publisher")
    if get("pubdate"):
        args.pubdate = get("pubdate")
    if get("uuid"):
        args.uuid = get("uuid")
    if get("subjects"):
        args.subjects = get("subjects")
    if get("keywords"):
        args.keywords = get("keywords")

    # Extended metadata fields
    if get("editor"):
        setattr(args, "editor", get("editor"))
    if get("illustrator"):
        setattr(args, "illustrator", get("illustrator"))
    if get("translator"):
        setattr(args, "translator", get("translator"))
    if get("narrator"):
        setattr(args, "narrator", get("narrator"))
    if get("designer"):
        setattr(args, "designer", get("designer"))
    if get("contributor"):
        setattr(args, "contributor", get("contributor"))
    if get("bisac_codes") or get("bisac-codes"):
        setattr(args, "bisac_codes", get("bisac_codes") or get("bisac-codes"))
    if get("age_range") or get("age-range"):
        setattr(args, "age_range", get("age_range") or get("age-range"))
    if get("reading_level") or get("reading-level"):
        setattr(args, "reading_level", get("reading_level") or get("reading-level"))
    if get("copyright_holder") or get("copyright-holder"):
        setattr(args, "copyright_holder", get("copyright_holder") or get("copyright-holder"))
    if get("copyright_year") or get("copyright-year"):
        setattr(args, "copyright_year", get("copyright_year") or get("copyright-year"))
    if get("rights"):
        setattr(args, "rights", get("rights"))
    if get("price"):
        setattr(args, "price", get("price"))
    if get("currency"):
        setattr(args, "currency", get("currency"))
    if get("print_isbn") or get("print-isbn"):
        setattr(args, "print_isbn", get("print_isbn") or get("print-isbn"))
    if get("audiobook_isbn") or get("audiobook-isbn"):
        setattr(args, "audiobook_isbn", get("audiobook_isbn") or get("audiobook-isbn"))
    if get("series_type") or get("series-type"):
        setattr(args, "series_type", get("series_type") or get("series-type"))
    if get("series_position") or get("series-position"):
        setattr(args, "series_position", get("series_position") or get("series-position"))
    if get("publication_type") or get("publication-type"):
        setattr(args, "publication_type", get("publication_type") or get("publication-type"))
    if get("target_audience") or get("target-audience"):
        setattr(args, "target_audience", get("target_audience") or get("target-audience"))
    if get("content_warnings") or get("content-warnings"):
        setattr(args, "content_warnings", get("content_warnings") or get("content-warnings"))
    # Conversion/layout
    if (args.split_at in (None, "", "h1")) and (get("split_at") or get("split-at")):
        args.split_at = get("split_at") or get("split-at")
    if (args.theme in (None, "", "serif")) and get("theme"):
        args.theme = get("theme")
    if (args.hyphenate in (None, "", "on")) and get("hyphenate"):
        args.hyphenate = get("hyphenate")
    if (args.justify in (None, "", "on")) and get("justify"):
        args.justify = get("justify")
    try:
        if get("toc_depth") and not getattr(args, "toc_depth_set", False):
            args.toc_depth = int(get("toc_depth"))
            setattr(args, "toc_depth_set", True)
    except Exception:
        pass
    if (getattr(args, "toc_depth", None) in (None, 2)) and get("toc_depth"):
        try:
            args.toc_depth = int(get("toc_depth"))
        except Exception:
            pass
    # Chapter start mode and patterns
    if (getattr(args, "chapter_start_mode", None) in (None, "auto")) and (
        get("chapter_start_mode") or get("chapter-start-mode")
    ):
        setattr(args, "chapter_start_mode", get("chapter_start_mode") or get("chapter-start-mode"))
    if (getattr(args, "chapter_starts", None) in (None, "")) and (
        get("chapter_starts") or get("chapter-starts")
    ):
        setattr(args, "chapter_starts", get("chapter_starts") or get("chapter-starts"))
    if (args.page_list in (None, "", "off")) and (get("page_list") or get("page-list")):
        args.page_list = get("page_list") or get("page-list")
    if (args.page_numbers in (None, "", "off")) and (get("page_numbers") or get("page-numbers")):
        args.page_numbers = get("page_numbers") or get("page-numbers")
    if (args.cover_scale in (None, "", "contain")) and (get("cover_scale") or get("cover-scale")):
        args.cover_scale = get("cover_scale") or get("cover-scale")
    # Typography options
    if getattr(args, "font_size", None) in (None, "") and (get("font_size") or get("font-size")):
        setattr(args, "font_size", get("font_size") or get("font-size"))
    if getattr(args, "line_height", None) in (None, "") and (
        get("line_height") or get("line-height")
    ):
        setattr(args, "line_height", get("line_height") or get("line-height"))
    # Assets
    if (getattr(args, "css", None) in (None, "")) and get("css"):
        args.css = pathify(get("css"))
    if (getattr(args, "embed_fonts", None) in (None, "")) and (
        get("embed_fonts") or get("embed-fonts")
    ):
        args.embed_fonts = pathify(get("embed_fonts") or get("embed-fonts"))
    if (getattr(args, "dedication", None) in (None, "")) and get("dedication"):
        args.dedication = pathify(get("dedication"))
    if (getattr(args, "ack", None) in (None, "")) and (
        get("ack") or get("acknowledgements") or get("acknowledgments")
    ):
        args.ack = pathify(get("ack") or get("acknowledgements") or get("acknowledgments"))
    # Output
    if (getattr(args, "output", None) in (None, "")) and get("output"):
        args.output = pathify(get("output"))
    if (getattr(args, "epubcheck", None) in (None, "on")) and get("epubcheck"):
        args.epubcheck = get("epubcheck")


def print_checklist(args: argparse.Namespace) -> None:
    """Print a checklist of provided metadata fields.

    Args:
        args: The argument namespace to display
    """
    def checked(val) -> str:
        return "[x]" if (val is not None and str(val).strip() != "") else "[ ]"

    items = [
        ("Input", args.input),
        ("Cover", args.cover),
        ("Title", args.title),
        ("Author", args.author),
        ("Language", args.language),
        ("Series", args.seriesName),
        ("Description", getattr(args, "description", None)),
        ("ISBN", getattr(args, "isbn", None)),
        ("Publisher", getattr(args, "publisher", None)),
        ("PubDate", getattr(args, "pubdate", None)),
    ]
    print("\n== Quick Checklist ==")
    for name, val in items:
        display = str(val) if val is not None and str(val).strip() != "" else "-"
        print(f" {checked(val)} {name}: {display}")
    print("")


def print_metadata_summary(meta: EpubMetadata, opts: BuildOptions, output: Path | None) -> None:
    """Print a summary of the metadata that will be used for building.

    Args:
        meta: The EPUB metadata object
        opts: The build options object
        output: The output path (if known)
    """
    def mark(val):
        return "[x]" if val else "[ ]"

    print("\n== Metadata Summary ==")
    print(f" {mark(meta.title)} Title: {meta.title or '—'}")
    print(f" {mark(meta.author)} Author: {meta.author or '—'}")
    print(f" {mark(meta.language)} Language: {meta.language or '—'}")
    print(f" {mark(meta.publisher)} Publisher: {meta.publisher or '—'}")
    print(f" {mark(meta.description)} Description: {meta.description or '—'}")
    print(f" {mark(meta.isbn)} ISBN: {meta.isbn or '—'}")
    print(f" {mark(meta.series_name)} Series: {meta.series_name or '—'}")
    if meta.series_name and meta.series_index:
        print(f"                 Index: {meta.series_index}")
    print("\n== Build Options ==")
    print(f" Split at: {opts.split_at}")
    print(f" Theme: {opts.theme}")
    print(f" ToC Depth: {opts.toc_depth}")
    print(f" Hyphenate: {opts.hyphenate}")
    print(f" Justify: {opts.justify}")
    print(f" Page List: {opts.page_list}")
    if output:
        print(f"\n Output: {output}")
    print("")


def read_document_content(file_path: Path) -> str:
    """Read content from a document file for preview purposes.

    Args:
        file_path: Path to the document file

    Returns:
        The document content as a string
    """
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"


def save_metadata_to_file(metadata: EpubMetadata, output_path: Path):
    """Save metadata to a metadata.txt file.

    Args:
        metadata: The EPUB metadata object to save
        output_path: Path where to save the metadata file
    """
    lines = []
    lines.append(f"title: {metadata.title or ''}")
    lines.append(f"author: {metadata.author or ''}")
    lines.append(f"language: {metadata.language or 'en'}")
    if metadata.publisher:
        lines.append(f"publisher: {metadata.publisher}")
    if metadata.description:
        lines.append(f"description: {metadata.description}")
    if metadata.isbn:
        lines.append(f"isbn: {metadata.isbn}")
    if metadata.series_name:
        lines.append(f"series: {metadata.series_name}")
    if metadata.series_index:
        lines.append(f"series_index: {metadata.series_index}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_preview_mode(
    meta: EpubMetadata,
    opts: BuildOptions,
    html_chunks: list[str],
    resources: list[Path],
    args,
) -> int:
    """Run live preview mode instead of generating EPUB.

    This function creates a temporary EPUB structure, generates the content,
    and launches a live preview server that allows viewing the EPUB content
    in a web browser.

    Args:
        meta: The EPUB metadata object
        opts: Build options containing preview settings
        html_chunks: List of HTML content chunks
        resources: List of resource file paths (images, fonts, etc.)
        args: Command-line arguments namespace

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import signal
    import sys
    import tempfile
    import time

    from ..assemble import assemble_epub
    from ..preview import run_live_preview

    try:
        # Create temporary directory for preview content
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate EPUB content in temporary location (but don't zip it)
            epub_temp = temp_path / "temp.epub"

            # Generate the EPUB content structure
            if not opts.quiet:
                print("📚 Generating preview content...")

            assemble_epub(
                meta=meta,
                opts=opts,
                html_chunks=html_chunks,
                resources=resources,
                output_path=epub_temp,
                styles_css="",  # Will be populated by conversion process
                performance_monitor=None,  # Preview mode doesn't need monitoring
            )

            # Check if inspect folder was created (contains the EPUB content structure)
            inspect_dir = epub_temp.parent / f"{epub_temp.stem}.src"
            if not inspect_dir.exists():
                # Force inspect mode for preview
                opts.inspect = True
                assemble_epub(
                    meta=meta,
                    opts=opts,
                    html_chunks=html_chunks,
                    resources=resources,
                    output_path=epub_temp,
                    styles_css="",
                )

            if not inspect_dir.exists():
                print("Error: Could not generate preview content", file=sys.stderr)
                return 1

            # Create output directory for preview
            output_dir = Path.cwd() / "preview_output"
            output_dir.mkdir(exist_ok=True)

            # Run live preview
            port = run_live_preview(
                epub_content_dir=inspect_dir,
                output_dir=output_dir,
                title=meta.title or "EPUB Preview",
                port=opts.preview_port,
                auto_open=True,
                quiet=opts.quiet,
            )

            if port is None:
                return 1

            # Set up signal handlers for graceful shutdown
            def signal_handler(sig, frame):
                if not opts.quiet:
                    print("\n\n🛑 Stopping preview server...")
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Keep the server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                if not opts.quiet:
                    print("\n\n🛑 Preview server stopped")
                return 0

    except Exception as e:
        if not opts.quiet:
            print(f"Error running preview: {e}", file=sys.stderr)
        return 1
