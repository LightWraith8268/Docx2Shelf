from __future__ import annotations

import re
import uuid as _uuid
from importlib import resources
from pathlib import Path

from .accessibility import process_accessibility_features
from .figures import FigureConfig, FigureProcessor
from .fonts import process_embedded_fonts, warn_about_font_licensing
from .images import get_media_type_for_image, process_images
from .language import (
    add_language_attributes_to_html,
    generate_language_css,
)
from .metadata import BuildOptions, EpubMetadata
from .tools import epubcheck_cmd


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_epubcheck_validation(epub_path: Path, quiet: bool = False) -> None:
    """Run EPUBCheck validation with enhanced reporting."""
    try:
        import subprocess

        cmd = epubcheck_cmd()
        if not cmd:
            if not quiet:
                print("[EPUBCHECK] EPUBCheck: Not available (install via 'docx2shelf tools install epubcheck')")
            return

        if not quiet:
            print("[EPUBCHECK] Running EPUBCheck validation...")

        # Run EPUBCheck with JSON output if supported
        proc = subprocess.run(
            cmd + [str(epub_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

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


def _generate_epub2_compat_css() -> str:
    """Generate CSS rules for EPUB 2 compatibility mode."""
    return """
/* EPUB 2 compatibility constraints */
/* Remove modern CSS features that may not be supported */
body {
    /* Avoid CSS Grid and Flexbox */
    display: block !important;
}

/* Simpler font stacks for better compatibility */
h1, h2, h3, h4, h5, h6 {
    font-family: serif !important;
}

/* Avoid advanced selectors and properties */
* {
    /* Remove CSS transforms and animations */
    transform: none !important;
    transition: none !important;
    animation: none !important;

    /* Remove modern layout properties */
    display: inline, block, inline-block, list-item, table, table-cell !important;
}

/* Conservative image sizing */
img {
    max-width: 100% !important;
    height: auto !important;
    /* Remove object-fit and other modern properties */
    object-fit: initial !important;
}

/* Simple table styling */
table {
    border-collapse: collapse !important;
    width: 100% !important;
}

/* Conservative text formatting */
p {
    /* Avoid advanced text properties */
    text-overflow: clip !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Remove advanced pseudo-elements and selectors */
::before, ::after {
    content: none !important;
}

/* Avoid CSS counters and generated content */
ol, ul {
    list-style-type: decimal !important;
}

ul {
    list-style-type: disc !important;
}
"""


def _load_css(theme: str, extra_css: Path | None, opts: BuildOptions, styles_css: str = "", language: str = "en") -> bytes:
    # Load theme CSS using the theme discovery system
    css = ""
    try:
        from .themes import get_theme_css_path, validate_theme

        if validate_theme(theme):
            theme_path = get_theme_css_path(theme)
            if theme_path:
                with theme_path.open("r", encoding="utf-8") as fh:
                    css = fh.read()
        else:
            # Fallback to direct file loading for backwards compatibility
            css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme}.css")
            with css_path.open("r", encoding="utf-8") as fh:
                css = fh.read()
    except Exception:
        # Final fallback - try direct file access
        try:
            css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme}.css")
            with css_path.open("r", encoding="utf-8") as fh:
                css = fh.read()
        except Exception:
            css = ""
    if opts.font_size:
        css += f"\nhtml {{ font-size: {opts.font_size}; }}\n"
    if opts.line_height:
        css += f"\nhtml {{ line-height: {opts.line_height}; }}\n"
    if opts.justify:
        css += "\n" + "p { text-align: justify; }\n"
    if not opts.hyphenate:
        css += "\n" + "html { hyphens: manual; }\n"
    # Ensure images fit viewport and preserve aspect ratio
    css += "\nimg { max-width: 100%; height: auto; }\n"
    if opts.cover_scale == "contain":
        css += "\nimg[alt='Cover'] { max-width: 100%; height: auto; }\n"
    elif opts.cover_scale == "cover":
        css += (
            "\n/* 'cover' scaling hint; support varies across readers */\n"
            "img[alt='Cover'] { width: 100%; height: auto; }\n"
        )
    if opts.page_numbers:
        css += (
            "\n/* page number counters on h1/h2 (informational) */\n"
            "h1::before, h2::before { counter-increment: page; content: counter(page) '\\a0'; }\n"
        )
    # Add styles from styles.json
    if styles_css:
        css += "\n/* styles from styles.json */\n" + styles_css

    # Add language-specific CSS
    language_css = generate_language_css(language, opts.vertical_writing)
    if language_css:
        css += "\n/* language-specific styles */\n" + language_css

    # Add EPUB 2 compatibility CSS if enabled
    if opts.epub2_compat:
        epub2_css = _generate_epub2_compat_css()
        css += "\n/* EPUB 2 compatibility styles */\n" + epub2_css

    if extra_css and extra_css.exists():
        css += "\n/* user css */\n" + extra_css.read_text(encoding="utf-8")
    return css.encode("utf-8")


def _html_item(title: str, file_name: str, content: str, lang: str):
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e
    item = epub.EpubHtml(title=title, file_name=file_name, lang=lang)
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content
    item.set_content(content_bytes)
    return item


def _inject_heading_ids(html: str, chap_idx: int, toc_depth: int = 2) -> tuple[str, str, list[tuple[str, str, int]]]:
    """Ensure first h1 has an id and collect headings with ids up to specified depth.

    Returns: (html, h1_id, [(heading_title, heading_id, level), ...])
    """
    h1_id = f"ch{chap_idx:03d}"

    # Add id to first h1 if missing
    def h1_repl(match):
        tag_open = match.group(1)
        inside = match.group(2)
        if re.search(r"\bid=\"[^\"]+\"", tag_open):
            # keep existing attributes and id
            return f"<h1{tag_open}>{inside}</h1>"
        # inject id preserving other attributes
        return f'<h1{tag_open} id="{h1_id}">{inside}</h1>'

    pattern_h1 = r"<h1([^>]*)>(.*?)</h1>"
    html_result = re.sub(pattern_h1, h1_repl, html, count=1, flags=re.IGNORECASE | re.DOTALL)

    # Collect all headings from h2 to h{toc_depth} and assign IDs
    all_headings = []
    heading_counters = {}  # Track counters for each level

    for level in range(2, min(toc_depth + 1, 7)):  # h2 to h6, limited by toc_depth
        heading_counters[level] = 0

        def make_heading_repl(heading_level):
            def heading_repl(match):
                nonlocal heading_counters
                heading_counters[heading_level] += 1
                tag_open = match.group(1)
                inside = match.group(2)

                if re.search(r"\bid=\"[^\"]+\"", tag_open):
                    return f"<h{heading_level}{tag_open}>{inside}</h{heading_level}>"

                # Generate hierarchical ID
                id_parts = [h1_id]
                for level_num in range(2, heading_level + 1):
                    id_parts.append(f"s{heading_counters.get(level_num, 0):02d}")
                hid = "-".join(id_parts)

                return f'<h{heading_level}{tag_open} id="{hid}">{inside}</h{heading_level}>'
            return heading_repl

        pattern = rf"<h{level}([^>]*?)>(.*?)</h{level}>"
        html_result = re.sub(pattern, make_heading_repl(level), html_result, flags=re.IGNORECASE | re.DOTALL)

    # Extract all headings with their IDs and levels for ToC
    for level in range(2, min(toc_depth + 1, 7)):
        pattern = rf"<h{level}[^>]*?>(.*?)</h{level}>"
        titles = re.findall(pattern, html_result, flags=re.IGNORECASE | re.DOTALL)

        pattern_ids = rf"<h{level}[^>]*?id=\"([^\"]+)\"[^>]*?>"
        ids = re.findall(pattern_ids, html_result, flags=re.IGNORECASE)

        for i, title in enumerate(titles):
            if i < len(ids):
                clean_title = re.sub(r"<[^>]+>", "", title)
                all_headings.append((clean_title, ids[i], level))

    # Determine h1 id actually present
    m = re.search(r"<h1[^>]*id=\"([^\"]+)\"[^>]*>", html_result, flags=re.IGNORECASE)
    if m:
        h1_id = m.group(1)

    return html_result, h1_id, all_headings


def _find_chapter_starts(
    html_chunks: list[str], chapter_starts: list[str]
) -> list[tuple[str, int]]:
    """Find user-defined chapter starts in HTML chunks.

    Returns list of (chapter_title, chunk_index) tuples.
    Falls back to generic titles if patterns not found.
    """
    import re

    found_chapters = []

    # Pre-process HTML chunks to text-only content (performance optimization)
    text_chunks = [re.sub(r"<[^>]+>", "", chunk) for chunk in html_chunks]

    for pattern in chapter_starts:
        pattern_found = False
        # Try to find this pattern in any chunk
        for i, text_content in enumerate(text_chunks):
            # Try both exact match and regex-style matching
            if pattern.lower() in text_content.lower():
                found_chapters.append((pattern.strip(), i))
                pattern_found = True
                break

            # Try as a regex pattern (single execution with better validation)
            try:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match and match.group(0).strip():  # Ensure meaningful match
                    title = match.group(0).strip()
                    found_chapters.append((title, i))
                    pattern_found = True
                    break
            except re.error:
                pass  # Invalid regex, skip

        # If pattern not found, create a generic chapter name
        if not pattern_found:
            # Ensure we don't exceed available chunks or create invalid indices
            chunk_idx = min(len(found_chapters), len(html_chunks) - 1)
            if chunk_idx >= 0 and chunk_idx < len(html_chunks):  # Ensure valid index
                found_chapters.append((f"Chapter {len(found_chapters) + 1}", chunk_idx))

    return found_chapters


def _inject_manual_chapter_ids(
    html: str, chap_idx: int, chapter_title: str
) -> tuple[str, str, list[tuple[str, str]]]:
    """Inject IDs for manually defined chapters, similar to _inject_heading_ids."""
    import re

    # Create a unique ID for this chapter
    h1_id = f"ch{chap_idx:03d}"

    # Look for existing h1/h2 headings to preserve them
    h2_items = []

    # Ensure h2 have ids; collect titles + ids
    sec_idx = 0

    def h2_repl(match):
        nonlocal sec_idx
        sec_idx += 1
        tag_open = match.group(1)
        inside = match.group(2)
        if re.search(r"\bid=\"[^\"]+\"", tag_open):
            return f"<h2{tag_open}>{inside}</h2>"
        hid = f"{h1_id}-s{sec_idx:02d}"
        return f'<h2{tag_open} id="{hid}">{inside}</h2>'

    html_with_h2_ids = re.sub(
        r"<h2([^>]*)>(.*?)</h2>", h2_repl, html, flags=re.IGNORECASE | re.DOTALL
    )

    # Extract h2 titles and IDs for TOC
    titles = re.findall(r"<h2[^>]*>(.*?)</h2>", html_with_h2_ids, flags=re.IGNORECASE | re.DOTALL)
    ids = re.findall(r"<h2[^>]*id=\"([^\"]+)\"[^>]*>", html_with_h2_ids, flags=re.IGNORECASE)
    h2_items = [(re.sub(r"<[^>]+>", "", t), ids[i]) for i, t in enumerate(titles) if i < len(ids)]

    # Add chapter anchor at the beginning if no h1 exists
    if not re.search(r"<h1[^>]*>", html_with_h2_ids, re.IGNORECASE):
        html_with_h2_ids = f'<div id="{h1_id}"></div>' + html_with_h2_ids
    else:
        # Add ID to existing h1
        def h1_repl(match):
            tag_open = match.group(1)
            inside = match.group(2)
            if re.search(r"\bid=\"[^\"]+\"", tag_open):
                return f"<h1{tag_open}>{inside}</h1>"
            return f'<h1{tag_open} id="{h1_id}">{inside}</h1>'

        html_with_h2_ids = re.sub(
            r"<h1([^>]*)>(.*?)</h1>",
            h1_repl,
            html_with_h2_ids,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    return html_with_h2_ids, h1_id, h2_items


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

        identifier = meta.isbn or meta.uuid or str(_uuid.uuid4())
        book.set_identifier(identifier)
        book.set_title(meta.title)
        book.set_language(meta.language or "en")
        book.add_author(meta.author)
        if meta.publisher:
            book.add_metadata("DC", "publisher", meta.publisher)
        if meta.pubdate:
            book.add_metadata("DC", "date", meta.pubdate.isoformat())
        if meta.description:
            book.add_metadata("DC", "description", meta.description)
        if meta.title_sort:
            book.add_metadata(None, "meta", meta.title_sort, {"name": "calibre:title_sort"})
        if meta.author_sort:
            book.add_metadata(None, "meta", meta.author_sort, {"name": "calibre:author_sort"})
        for subj in meta.subjects:
            book.add_metadata("DC", "subject", subj)
        for kw in meta.keywords:
            book.add_metadata("DC", "subject", kw)
        # Calibre series metadata
        if meta.series:
            book.add_metadata(None, "meta", meta.series, {"name": "calibre:series"})
            if meta.series_index:
                book.add_metadata(
                    None,
                    "meta",
                    str(meta.series_index),
                    {"name": "calibre:series_index"},
                )

    # Cover processing phase
    with performance_monitor.phase_timer("cover_processing"):
        cover_bytes = meta.cover_path.read_bytes()
        # Let ebooklib create the cover page automatically
        book.set_cover(meta.cover_path.name, cover_bytes)

    # CSS processing phase
    with performance_monitor.phase_timer("css_processing"):
        css_bytes = _load_css(opts.theme, opts.extra_css, opts, styles_css, meta.language or "en")
    style_item = epub.EpubItem(
        uid="style_base",
        file_name="style/base.css",
        media_type="text/css",
        content=css_bytes,
    )
    book.add_item(style_item)

    # Title page
    # Load packaged title template
    try:
        title_path = resources.files("docx2shelf.templates").joinpath("title.xhtml")
        with title_path.open("r", encoding="utf-8") as fh:
            content = (
                fh.read().replace("{{ title }}", meta.title).replace("{{ author }}", meta.author)
            )
    except Exception:
        content = f"<html><body><h1>{meta.title}</h1><p>{meta.author}</p></body></html>"
    title_page = _html_item("Title Page", "text/title.xhtml", content, meta.language)
    book.add_item(title_page)

    # Copyright page (auto)
    import datetime as _dt

    year = str(_dt.date.today().year)
    copyright_html = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Copyright</title></head><body>"
        f"<section><h2>Copyright</h2><p>© {year} {meta.author}. All rights reserved.</p></section>"
        "</body></html>"
    )
    copyright_page = _html_item("Copyright", "text/copyright.xhtml", copyright_html, meta.language)
    book.add_item(copyright_page)

    # Optional front/back matter
    matter_items = []
    if opts.dedication_txt and opts.dedication_txt.exists():
        txt = _read_text(opts.dedication_txt)
        ded_html = f"<h2>Dedication</h2><p>{txt}</p>"
        matter_items.append(
            _html_item("Dedication", "text/dedication.xhtml", ded_html, meta.language)
        )
    if opts.ack_txt and opts.ack_txt.exists():
        txt = _read_text(opts.ack_txt)
        matter_items.append(
            _html_item(
                "Acknowledgements",
                "text/ack.xhtml",
                f"<h2>Acknowledgements</h2><p>{txt}</p>",
                meta.language,
            )
        )
    for it in matter_items:
        book.add_item(it)

    # Add extracted resources (images) under images/
    if resources:
        import tempfile

        # Process images with optimization
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Filter image files
            image_files = [
                res for res in resources
                if res.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.bmp', '.tiff', '.tif'}
            ]

            if image_files:
                # Process images with auto-resize and optional format conversion
                modern_format = None if opts.image_format == "original" else opts.image_format
                processed_images = process_images(
                    image_files,
                    temp_path,
                    max_width=opts.image_max_width,
                    max_height=opts.image_max_height,
                    quality=opts.image_quality,
                    modern_format=modern_format,
                    quiet=opts.quiet,
                    enhanced_processing=opts.enhanced_images
                )

                # Add processed images to EPUB
                for img_path in processed_images:
                    mt = get_media_type_for_image(img_path)
                    item = epub.EpubItem(
                        uid=f"img_{img_path.stem}",
                        file_name=f"images/{img_path.name}",
                        media_type=mt,
                        content=img_path.read_bytes(),
                    )
                    book.add_item(item)

            # Handle non-image resources
            for res in resources:
                if res.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.bmp', '.tiff', '.tif'}:
                    # Keep non-image resources as-is
                    item = epub.EpubItem(
                        uid=f"res_{res.stem}",
                        file_name=f"images/{res.name}",
                        media_type="application/octet-stream",
                        content=res.read_bytes(),
                    )
                    book.add_item(item)

    # Initialize figure processor for semantic markup
    figure_config = FigureConfig(
        auto_number=True,
        generate_lists=opts.generate_figure_lists if hasattr(opts, 'generate_figure_lists') else True
    )
    figure_processor = FigureProcessor(figure_config)

    # Process accessibility features
    if not opts.quiet:
        print("🔍 Processing EPUB Accessibility features...")

    html_chunks, accessibility_meta = process_accessibility_features(
        html_chunks,
        meta,
        interactive=not opts.quiet,
        quiet=opts.quiet
    )

    # Add accessibility metadata to EPUB
    for key, value in accessibility_meta.items():
        book.add_metadata(None, "meta", value, {"property": key})

    # Add language-specific attributes to HTML
    language_code = meta.language or "en"
    html_chunks = add_language_attributes_to_html(html_chunks, language_code)

    if not opts.quiet:
        print(f"🌐 Applied language settings for: {language_code}")
        if opts.vertical_writing:
            print("📝 Vertical writing mode enabled")

    # Chapters from html_chunks
    chapters = []
    chapter_links = []
    chapter_sub_links = []

    # Determine chapter processing mode
    if opts.chapter_start_mode in ("manual", "mixed") and opts.chapter_starts:
        # Manual mode: use user-defined chapter starts
        manual_chapters = _find_chapter_starts(html_chunks, opts.chapter_starts)

        for chap_num, (chapter_title, chunk_idx) in enumerate(manual_chapters, start=1):
            if chunk_idx < len(html_chunks):
                chunk = html_chunks[chunk_idx]

                # Process figures and tables for semantic markup
                chunk_with_figures = figure_processor.process_content(
                    chunk,
                    chapter_title=chapter_title,
                    chapter_id=f"chap_{chap_num:03d}"
                )

                chunk2, h1_id, subs = _inject_manual_chapter_ids(chunk_with_figures, chap_num, chapter_title)
                chap_fn = f"text/chap_{chap_num:03d}.xhtml"
                chap = _html_item(chapter_title, chap_fn, chunk2, meta.language)
                chap.add_item(style_item)
                book.add_item(chap)
                chapters.append(chap)
                # Build links for TOC using custom title
                chap_link = epub.Link(chap_fn + f"#{h1_id}", chapter_title, f"chap{chap_num:03d}")
                chapter_links.append(chap_link)
                sub_links = []
                if opts.toc_depth > 1:  # Include subheadings in manual mode too
                    for idx, (title, hid) in enumerate(subs):
                        sub_links.append(
                            epub.Link(chap_fn + f"#{hid}", title, f"chap{chap_num:03d}-{idx+1:02d}")
                        )
                chapter_sub_links.append(sub_links)

        # Add remaining chunks as additional chapters if there are more chunks than defined chapters
        for i in range(len(manual_chapters), len(html_chunks)):
            chunk = html_chunks[i]
            chap_num = i + 1
            chunk2, h1_id, subs = _inject_heading_ids(chunk, chap_num, opts.toc_depth)
            chap_fn = f"text/chap_{chap_num:03d}.xhtml"
            chap = _html_item(f"Chapter {chap_num}", chap_fn, chunk2, meta.language)
            chap.add_item(style_item)
            book.add_item(chap)
            chapters.append(chap)
            chap_link = epub.Link(
                chap_fn + f"#{h1_id}", f"Chapter {chap_num}", f"chap{chap_num:03d}"
            )
            chapter_links.append(chap_link)
            sub_links = []
            for idx, (title, hid, level) in enumerate(subs):
                sub_links.append(
                    epub.Link(chap_fn + f"#{hid}", title, f"chap{chap_num:03d}-{idx+1:02d}")
                )
            chapter_sub_links.append(sub_links)

    else:
        # Auto mode (default): scan headings as before
        for i, chunk in enumerate(html_chunks, start=1):
            # Process figures and tables for semantic markup
            chunk_with_figures = figure_processor.process_content(
                chunk,
                chapter_title=f"Chapter {i}",
                chapter_id=f"chap_{i:03d}"
            )

            chunk2, h1_id, subs = _inject_heading_ids(chunk_with_figures, i, opts.toc_depth)
            chap_fn = f"text/chap_{i:03d}.xhtml"
            chap = _html_item(f"Chapter {i}", chap_fn, chunk2, meta.language)
            chap.add_item(style_item)
            book.add_item(chap)
            chapters.append(chap)
            # Build links for TOC
            chap_link = epub.Link(chap_fn + f"#{h1_id}", f"Chapter {i}", f"chap{i:03d}")
            chapter_links.append(chap_link)
            sub_links = []
            for idx, (title, hid, level) in enumerate(subs):
                sub_links.append(epub.Link(chap_fn + f"#{hid}", title, f"chap{i:03d}-{idx+1:02d}"))
            chapter_sub_links.append(sub_links)

    # Initialize list_items for later use
    list_items = []
    depth = max(1, min(6, opts.toc_depth))

    def build_nested_toc(chap_link, sub_links, current_depth=2):
        """Build nested ToC structure supporting arbitrary depth."""
        if current_depth > depth or not sub_links:
            return chap_link

        # Group sub_links by level
        grouped_links = {}
        for link_info in sub_links:
            if len(link_info) >= 3:  # (title, hid, level)
                level = link_info[2] if len(link_info) > 2 else 2
                if level not in grouped_links:
                    grouped_links[level] = []
                grouped_links[level].append(link_info)

        # For now, create flat structure for all sub-headings
        # More sophisticated nesting could be implemented later
        epub_sub_links = []
        for link_info in sub_links:
            if hasattr(link_info, 'href'):  # It's already an epub.Link
                epub_sub_links.append(link_info)

        if epub_sub_links:
            return (chap_link, epub_sub_links)
        else:
            return chap_link

    # Chapter links will be added to toc_items after it's defined
    # Determine reader start chapter
    start_reading_link = "text/chap_001.xhtml#ch001"  # Default start
    if opts.reader_start_chapter:
        # Find the chapter that matches the start pattern
        for i, chap_link in enumerate(chapter_links):
            if opts.reader_start_chapter.lower() in chap_link.title.lower():
                # Extract chapter number from the link href
                import re
                match = re.search(r'chap_(\d+)\.xhtml#(ch\d+)', chap_link.href)
                if match:
                    start_reading_link = chap_link.href
                break

    # Generate List of Figures and Tables pages if figures/tables were found
    list_items = []
    if figure_processor.get_figure_count() > 0:
        lof_html = figure_processor.generate_list_of_figures()
        if lof_html:
            lof_item = _html_item(
                figure_config.list_of_figures_title,
                "text/list-of-figures.xhtml",
                lof_html,
                meta.language
            )
            book.add_item(lof_item)
            list_items.append(lof_item)

    if figure_processor.get_table_count() > 0:
        lot_html = figure_processor.generate_list_of_tables()
        if lot_html:
            lot_item = _html_item(
                figure_config.list_of_tables_title,
                "text/list-of-tables.xhtml",
                lot_html,
                meta.language
            )
            book.add_item(lot_item)
            list_items.append(lot_item)

    # TOC and spine - ensuring consistent ordering
    # The spine order must match the TOC order for proper navigation

    # Build spine order first to ensure consistency
    spine_items = [title_page, copyright_page] + matter_items
    if list_items:
        spine_items.extend(list_items)
    spine_items.extend(chapters)

    # Build TOC items in same order as spine (excluding nav itself)
    toc_items = [title_page, copyright_page] + matter_items

    # Add List of Figures/Tables to TOC if they exist (matching spine order)
    if list_items:
        toc_items.extend(list_items)

    # Set spine using consistent ordering (nav comes first in spine)
    book.spine = ["nav"] + spine_items

    # Build TOC with chapters (must happen after toc_items is defined)
    for i, chap_link in enumerate(chapter_links):
        if depth == 1 or not chapter_sub_links[i]:
            toc_items.append(chap_link)
        else:
            toc_items.append(build_nested_toc(chap_link, chapter_sub_links[i]))

    book.toc = tuple(toc_items)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Validate TOC and spine consistency
    _validate_toc_spine_consistency(book, spine_items, toc_items, opts.quiet)

    # Optional page-list nav (informational; support varies)
    if opts.page_list:
        items = []
        for i, chap in enumerate(chapters, start=1):
            frag = f"#ch{i:03d}"
            items.append(f"<li><a href='{chap.file_name}{frag}'>Page {i}</a></li>")
        page_list_html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops'>"
            "<head><title>Page List</title></head><body>"
            "<nav epub:type='page-list'><h2>Pages</h2><ol>" + "".join(items) + "</ol></nav>"
            "</body></html>"
        )
        page_list_item = _html_item(
            "Page List",
            "text/page-list.xhtml",
            page_list_html,
            meta.language,
        )
        book.add_item(page_list_item)

    # Landmarks nav for better reader navigation - consistent with spine order
    try:
        # Build landmarks based on actual spine content
        landmark_entries = []

        # Cover is special - always first if present
        if meta.cover_path and meta.cover_path.exists():
            landmark_entries.append("<li><a epub:type='cover' href='cover.xhtml'>Cover</a></li>")

        # Title page
        landmark_entries.append("<li><a epub:type='titlepage' href='text/title.xhtml'>Title Page</a></li>")

        # Table of contents
        landmark_entries.append("<li><a epub:type='toc' href='nav.xhtml'>Table of Contents</a></li>")

        # Copyright page
        landmark_entries.append("<li><a epub:type='copyright-page' href='text/copyright.xhtml'>Copyright</a></li>")

        # Add other front matter items if they exist
        for item in matter_items:
            if hasattr(item, 'file_name') and hasattr(item, 'title'):
                # Determine appropriate epub:type based on content
                if 'dedication' in item.file_name.lower():
                    epub_type = 'dedication'
                elif 'acknowledgment' in item.file_name.lower() or 'ack' in item.file_name.lower():
                    epub_type = 'acknowledgments'
                elif 'preface' in item.file_name.lower():
                    epub_type = 'preface'
                elif 'foreword' in item.file_name.lower():
                    epub_type = 'foreword'
                else:
                    epub_type = 'frontmatter'
                landmark_entries.append(f"<li><a epub:type='{epub_type}' href='{item.file_name}'>{item.title}</a></li>")

        # Add list items if present
        for item in list_items:
            if hasattr(item, 'file_name') and hasattr(item, 'title'):
                epub_type = 'loi' if 'figure' in item.title.lower() else 'lot' if 'table' in item.title.lower() else 'frontmatter'
                landmark_entries.append(f"<li><a epub:type='{epub_type}' href='{item.file_name}'>{item.title}</a></li>")

        # Start of main content
        if chapters:
            landmark_entries.append(f"<li><a epub:type='bodymatter' href='{start_reading_link}'>Start Reading</a></li>")

        landmarks_html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops'>"
            "<head><title>Landmarks</title></head><body>"
            "<nav epub:type='landmarks'><h2>Guide</h2><ol>"
            + "".join(landmark_entries) +
            "</ol></nav>"
            "</body></html>"
        )
        landmarks_item = _html_item(
            "Landmarks", "text/landmarks.xhtml", landmarks_html, meta.language
        )
        book.add_item(landmarks_item)
    except Exception as e:
        if not opts.quiet:
            print(f"Warning: Could not generate landmarks: {e}")
        pass

    # Embed fonts (optional)
    if opts.embed_fonts_dir and opts.embed_fonts_dir.exists():
        import tempfile

        # Display font licensing warning
        warn_about_font_licensing(opts.embed_fonts_dir, opts.quiet)

        # Process fonts with subsetting
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Collect all HTML content for character analysis
            html_chunks = []
            for item in book.items:
                if hasattr(item, 'content') and hasattr(item, 'file_name') and item.file_name.endswith('.xhtml'):
                    if isinstance(item.content, bytes):
                        html_chunks.append(item.content.decode('utf-8'))
                    else:
                        html_chunks.append(str(item.content))

            # Process and subset fonts
            processed_fonts = process_embedded_fonts(
                opts.embed_fonts_dir,
                html_chunks,
                temp_path,
                opts.quiet
            )

            # Add processed fonts to EPUB
            for font_path in processed_fonts:
                data = font_path.read_bytes()
                item = epub.EpubItem(
                    uid=f"font_{font_path.stem}",
                    file_name=f"fonts/{font_path.name}",
                    media_type="font/otf" if font_path.suffix.lower() == ".otf" else "font/ttf",
                    content=data,
                )
                book.add_item(item)

    # Write EPUB
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)

    # Inspect output (dump sources)
    if opts.inspect:
        folder = output_path.with_suffix("")
        folder = folder.parent / (folder.name + ".src")
        folder.mkdir(parents=True, exist_ok=True)
        # Save HTML chunks for debugging
        for i, chunk in enumerate(html_chunks, start=1):
            (folder / f"chap_{i:03d}.xhtml").write_text(chunk, encoding="utf-8")
        (folder / "meta.txt").write_text(
            "\n".join(
                [
                    f"title={meta.title}",
                    f"author={meta.author}",
                    f"language={meta.language}",
                    f"identifier={identifier}",
                ]
            ),
            encoding="utf-8",
        )

    # EPUBCheck validation (default enabled)
    if opts.epubcheck:
        _run_epubcheck_validation(output_path, opts.quiet)


def _validate_toc_spine_consistency(book, spine_items, toc_items, quiet: bool = False) -> None:
    """Validate that TOC entries match spine order and provide warnings for inconsistencies."""
    warnings = []

    # Get spine order (excluding 'nav' which is first)
    spine_order = [item for item in book.spine if item != 'nav']

    # Create mapping of spine items to their filenames
    spine_filenames = []
    for spine_ref in spine_order:
        # Find the actual item in the book
        for item in book.items:
            if hasattr(item, 'id') and item.id == spine_ref:
                if hasattr(item, 'file_name'):
                    spine_filenames.append(item.file_name)
                break

    # Extract TOC filenames in order
    toc_filenames = []
    for toc_item in toc_items:
        if hasattr(toc_item, 'href') and toc_item.href:
            # Remove fragment identifier if present
            href = toc_item.href.split('#')[0]
            toc_filenames.append(href)

    # Check for missing spine items in TOC
    missing_in_toc = []
    for filename in spine_filenames:
        if filename not in toc_filenames:
            missing_in_toc.append(filename)

    # Check for TOC items not in spine
    missing_in_spine = []
    for filename in toc_filenames:
        if filename not in spine_filenames:
            missing_in_spine.append(filename)

    # Check order consistency for common items
    order_mismatches = []

    for i, spine_file in enumerate(spine_filenames):
        if spine_file in toc_filenames:
            toc_index = toc_filenames.index(spine_file)
            # Check if relative order is preserved
            for j in range(i + 1, len(spine_filenames)):
                if spine_filenames[j] in toc_filenames:
                    next_toc_index = toc_filenames.index(spine_filenames[j])
                    if next_toc_index < toc_index:
                        order_mismatches.append((spine_file, spine_filenames[j]))
                    break

    # Report warnings
    if missing_in_toc and not quiet:
        warnings.append(f"Files in spine but missing from TOC: {', '.join(missing_in_toc)}")

    if missing_in_spine and not quiet:
        warnings.append(f"Files in TOC but missing from spine: {', '.join(missing_in_spine)}")

    if order_mismatches and not quiet:
        for file1, file2 in order_mismatches:
            warnings.append(
                f"Order mismatch: {file1} appears before {file2} in spine but after in TOC"
            )

    # Print warnings
    if warnings and not quiet:
        print("\nTOC/Spine Consistency Warnings:")
        for warning in warnings:
            print(f"  Warning: {warning}")

        # Provide guidance
        if missing_in_toc or missing_in_spine or order_mismatches:
            print("  Tip: Consider using consistent heading structure for automatic TOC generation")

    return len(warnings) == 0
