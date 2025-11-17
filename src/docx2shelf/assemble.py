from __future__ import annotations

import re
from pathlib import Path

from .accessibility import process_accessibility_features
from .content_security import ContentSanitizer
from .epub_chapters import process_chapters
from .epub_css import setup_book_css
from .epub_metadata import add_cover_to_book, setup_book_metadata
from .epub_navigation import (
    determine_reader_start_link,
    generate_figure_table_lists,
    setup_book_navigation,
)
from .epub_pages import (
    create_copyright_page,
    create_front_back_matter,
    create_landmarks_page,
    create_title_page,
)
from .epub_resources import process_and_add_fonts, process_and_add_images
from .figures import FigureConfig, FigureProcessor
from .language import add_language_attributes_to_html
from .metadata import BuildOptions, EpubMetadata
from .path_utils import safe_filename, write_text_safe
from .tools import epubcheck_cmd


def _run_epubcheck_validation(epub_path: Path, quiet: bool = False) -> None:
    """Run EPUBCheck validation with enhanced reporting."""
    try:
        import subprocess

        cmd = epubcheck_cmd()
        if not cmd:
            if not quiet:
                print(
                    "[EPUBCHECK] EPUBCheck: Not available (install via 'docx2shelf tools install epubcheck')"
                )
            return

        if not quiet:
            print("[EPUBCHECK] Running EPUBCheck validation...")

        # Run EPUBCheck with JSON output if supported
        proc = subprocess.run(cmd + [str(epub_path)], capture_output=True, text=True, timeout=60)

        output = (proc.stdout or "") + "\n" + (proc.stderr or "")

        # Parse output for issues
        errors = []
        warnings = []
        info_messages = []

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if "ERROR" in line.upper():
                errors.append(line)
            elif "WARNING" in line.upper():
                warnings.append(line)
            elif "INFO" in line.upper():
                info_messages.append(line)

        # Generate summary
        if not quiet:
            if errors or warnings:
                print(f"[EPUBCHECK] EPUBCheck: {len(errors)} error(s), {len(warnings)} warning(s)")

                # Show first few critical issues
                critical_issues = errors[:3] + warnings[:3]
                if critical_issues:
                    print("   Top issues:")
                    for issue in critical_issues:
                        # Clean up the issue message
                        clean_issue = issue.replace("ERROR", "").replace("WARNING", "").strip()
                        if clean_issue:
                            print(f"   • {clean_issue}")

                if len(errors) > 3 or len(warnings) > 3:
                    print(f"   ... and {max(0, len(errors) - 3 + len(warnings) - 3)} more issues")

                # Suggest actionable fixes
                if errors:
                    print("   💡 Fix errors for better reader compatibility")
                if warnings and not errors:
                    print("   💡 Address warnings for optimal EPUB quality")

            else:
                print("[EPUBCHECK] EPUBCheck: [SUCCESS] No issues found")

    except subprocess.TimeoutExpired:
        if not quiet:
            print("[EPUBCHECK] EPUBCheck: Timeout (file may be too large)")
    except Exception as e:
        if not quiet:
            print(f"[EPUBCHECK] EPUBCheck: Error during validation ({e})")


def plan_build(
    meta: EpubMetadata,
    opts: BuildOptions,
    html_chunks: list[str],
    resources: list[Path],
) -> list[str]:
    plan: list[str] = []
    plan.append(f"Title: {meta.title}")
    plan.append(f"Author: {meta.author}")
    if meta.series:
        plan.append(f"Series: {meta.series} #{meta.series_index or '?'}")
    plan.append(f"Language: {meta.language}")
    if meta.isbn:
        plan.append(f"Identifier: ISBN {meta.isbn}")
    plan.append(f"Cover: {meta.cover_path}")
    plan.append(f"Theme: {opts.theme}, Split: {opts.split_at}, ToC depth: {opts.toc_depth}")
    plan.append(f"Chunks: {len(html_chunks)}, Resources: {len(resources)}")
    if opts.page_numbers:
        plan.append("Page numbers: CSS counters (informational)")
    if opts.page_list:
        plan.append("EPUB page-list: enabled (reader support varies)")
    return plan


def assemble_epub(
    meta: EpubMetadata,
    opts: BuildOptions,
    html_chunks: list[str],
    resources: list[Path],
    output_path: Path,
    styles_css: str = "",
    performance_monitor=None,
) -> None:
    """Assemble the EPUB with ebooklib and write to output_path."""
    from .performance import PerformanceMonitor

    # Initialize performance monitoring if not provided
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()
        performance_monitor.start_monitoring()

    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Metadata setup phase
    with performance_monitor.phase_timer("metadata_setup"):
        book = epub.EpubBook()
        identifier = setup_book_metadata(book, meta)

    # Cover processing phase
    with performance_monitor.phase_timer("cover_processing"):
        add_cover_to_book(book, meta)

    # CSS processing phase
    with performance_monitor.phase_timer("css_processing"):
        style_item = setup_book_css(book, opts, styles_css, meta.language or "en")

    # Title page, copyright page, and front/back matter
    title_page = create_title_page(book, meta)
    copyright_page = create_copyright_page(book, meta)
    matter_items = create_front_back_matter(book, opts, meta)

    # Process and add resources (images) to EPUB
    with performance_monitor.phase_timer("resource_processing"):
        if resources:
            process_and_add_images(book, resources, opts)

    # Initialize figure processor for semantic markup
    figure_config = FigureConfig(
        auto_number=True,
        generate_lists=(
            opts.generate_figure_lists if hasattr(opts, "generate_figure_lists") else True
        ),
    )
    figure_processor = FigureProcessor(figure_config)

    # Process accessibility features
    if not opts.quiet:
        print("🔍 Processing EPUB Accessibility features...")

    html_chunks, accessibility_meta = process_accessibility_features(
        html_chunks, meta, interactive=not opts.quiet, quiet=opts.quiet
    )

    # Add accessibility metadata to EPUB
    for key, value in accessibility_meta.items():
        book.add_metadata(None, "meta", value, {"property": key})

    # Content security: sanitize HTML to remove dangerous scripts and elements
    if not opts.quiet:
        print("🔒 Applying content security sanitization...")

    sanitizer = ContentSanitizer(strict_mode=True)
    sanitized_chunks = []
    security_warnings = []

    for i, chunk in enumerate(html_chunks):
        try:
            sanitized_chunk = sanitizer.sanitize_html(chunk)
            sanitized_chunks.append(sanitized_chunk)

            # Check if anything was sanitized
            report = sanitizer.get_sanitization_report()
            if report["removed_elements"] or report["modified_attributes"]:
                security_warnings.append(
                    f"Chapter {i+1}: Removed {len(report['removed_elements'])} dangerous elements, "
                    f"modified {len(report['modified_attributes'])} attributes"
                )
        except Exception as e:
            if not opts.quiet:
                print(f"Warning: Error sanitizing chunk {i+1}: {e}")
            sanitized_chunks.append(chunk)  # Use original if sanitization fails

    html_chunks = sanitized_chunks

    # Report security sanitization results
    if security_warnings and not opts.quiet:
        print(
            f"🛡️  Content security applied: {len(security_warnings)} chunks had dangerous content removed"
        )
        for warning in security_warnings[:3]:  # Show first 3 warnings
            print(f"   {warning}")
        if len(security_warnings) > 3:
            print(f"   ... and {len(security_warnings) - 3} more")

    # Add language-specific attributes to HTML
    language_code = meta.language or "en"
    html_chunks = add_language_attributes_to_html(html_chunks, language_code)

    if not opts.quiet:
        print(f"🌐 Applied language settings for: {language_code}")
        if opts.vertical_writing:
            print("📝 Vertical writing mode enabled")

    # Process chapters with heading IDs and navigation data
    with performance_monitor.phase_timer("chapter_processing"):
        chapters, chapter_links, chapter_sub_links = process_chapters(
            book, html_chunks, meta, opts, style_item, figure_processor
        )

    # Determine where the main reading content starts
    start_reading_link = determine_reader_start_link(chapter_links, opts)

    # Generate List of Figures and Tables pages
    list_items = generate_figure_table_lists(book, figure_processor, figure_config, meta)

    # Setup EPUB navigation (ToC, spine, NCX, Nav)
    with performance_monitor.phase_timer("navigation_setup"):
        setup_book_navigation(
            book,
            chapters,
            chapter_links,
            chapter_sub_links,
            opts,
            title_page,
            copyright_page,
            matter_items,
            list_items,
        )

    # Create landmarks navigation page
    create_landmarks_page(book, meta, opts, matter_items, list_items, chapters, start_reading_link)

    # Embed fonts with subsetting (optional)
    with performance_monitor.phase_timer("font_processing"):
        # Note: html_content parameter is empty string because process_and_add_fonts
        # collects HTML from all book items internally for character analysis
        process_and_add_fonts(book, opts, "")

    # Write EPUB
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)

    # Inspect output (dump sources)
    if opts.inspect:
        folder = output_path.with_suffix("")
        folder = folder.parent / (folder.name + ".src")
        folder.mkdir(parents=True, exist_ok=True)
        # Save HTML chunks for debugging with safe path handling
        for i, chunk in enumerate(html_chunks, start=1):
            safe_chunk_path = folder / safe_filename(f"chap_{i:03d}.xhtml")
            write_text_safe(safe_chunk_path, chunk)

        meta_content = "\n".join(
            [
                f"title={meta.title}",
                f"author={meta.author}",
                f"language={meta.language}",
                f"identifier={identifier}",
            ]
        )
        write_text_safe(folder / "meta.txt", meta_content)

    # EPUBCheck validation (default enabled)
    if opts.epubcheck:
        _run_epubcheck_validation(output_path, opts.quiet)
