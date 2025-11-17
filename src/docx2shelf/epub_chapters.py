"""EPUB chapter processing and heading ID injection.

This module handles all chapter-related processing including:
- Chapter start detection (manual and automatic modes)
- Heading ID injection for navigation
- Figure and table processing within chapters
- ToC link generation
"""

from __future__ import annotations

import re

from .figures import FigureProcessor
from .metadata import BuildOptions, EpubMetadata


def find_chapter_starts(
    html_chunks: list[str], chapter_starts: list[str]
) -> list[tuple[str, int]]:
    """Find user-defined chapter starts in HTML chunks.

    Searches for chapter patterns (text or regex) in HTML chunks and
    returns their locations. Falls back to generic chapter titles if
    patterns are not found.

    Args:
        html_chunks: List of HTML content chunks
        chapter_starts: List of text patterns or regexes to find

    Returns:
        list[tuple[str, int]]: List of (chapter_title, chunk_index) tuples
    """
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


def inject_heading_ids(
    html: str, chap_idx: int, toc_depth: int = 2
) -> tuple[str, str, list[tuple[str, str, int]]]:
    """Inject IDs into headings for navigation and collect ToC data.

    Ensures the first h1 has an ID and assigns hierarchical IDs to all
    headings up to the specified depth. Returns the modified HTML along
    with heading information for ToC generation.

    Args:
        html: HTML content for a chapter
        chap_idx: Chapter index (1-based)
        toc_depth: Maximum heading level to include in ToC (default: 2)

    Returns:
        tuple: (modified_html, h1_id, [(title, id, level), ...])
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
        html_result = re.sub(
            pattern, make_heading_repl(level), html_result, flags=re.IGNORECASE | re.DOTALL
        )

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


def inject_manual_chapter_ids(
    html: str, chap_idx: int, chapter_title: str
) -> tuple[str, str, list[tuple[str, str]]]:
    """Inject IDs for manually defined chapters.

    Similar to inject_heading_ids but designed for manual chapter mode.
    Handles chapters that may not have h1 headings and focuses on h2 subheadings.

    Args:
        html: HTML content for a chapter
        chap_idx: Chapter index (1-based)
        chapter_title: User-defined chapter title

    Returns:
        tuple: (modified_html, h1_id, [(title, id), ...])
    """
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


def process_chapters(
    book,
    html_chunks: list[str],
    meta: EpubMetadata,
    opts: BuildOptions,
    style_item,
    figure_processor: FigureProcessor,
) -> tuple[list, list, list]:
    """Process all HTML chunks into EPUB chapters with navigation data.

    Handles both manual and automatic chapter detection modes. Processes
    figures/tables, injects heading IDs, creates EPUB items, and generates
    navigation links for ToC.

    Args:
        book: EpubBook instance from ebooklib
        html_chunks: List of HTML content chunks to process
        meta: EpubMetadata with language and other metadata
        opts: BuildOptions with chapter_start_mode and chapter_starts
        style_item: CSS item to link to chapters
        figure_processor: FigureProcessor for semantic markup

    Returns:
        tuple: (chapters, chapter_links, chapter_sub_links)
            - chapters: List of EpubHtml chapter items
            - chapter_links: List of main chapter navigation links
            - chapter_sub_links: List of subheading links per chapter
    """
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Import the HTML item creator from epub_pages
    from .epub_pages import create_html_item

    chapters = []
    chapter_links = []
    chapter_sub_links = []

    # Determine chapter processing mode
    if opts.chapter_start_mode in ("manual", "mixed") and opts.chapter_starts:
        # Manual mode: use user-defined chapter starts
        manual_chapters = find_chapter_starts(html_chunks, opts.chapter_starts)

        for chap_num, (chapter_title, chunk_idx) in enumerate(manual_chapters, start=1):
            if chunk_idx < len(html_chunks):
                chunk = html_chunks[chunk_idx]

                # Process figures and tables for semantic markup
                chunk_with_figures = figure_processor.process_content(
                    chunk, chapter_title=chapter_title, chapter_id=f"chap_{chap_num:03d}"
                )

                chunk2, h1_id, subs = inject_manual_chapter_ids(
                    chunk_with_figures, chap_num, chapter_title
                )
                chap_fn = f"text/chap_{chap_num:03d}.xhtml"
                chap = create_html_item(chapter_title, chap_fn, chunk2, meta.language)
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
            chunk2, h1_id, subs = inject_heading_ids(chunk, chap_num, opts.toc_depth)
            chap_fn = f"text/chap_{chap_num:03d}.xhtml"
            chap = create_html_item(f"Chapter {chap_num}", chap_fn, chunk2, meta.language)
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
                chunk, chapter_title=f"Chapter {i}", chapter_id=f"chap_{i:03d}"
            )

            chunk2, h1_id, subs = inject_heading_ids(chunk_with_figures, i, opts.toc_depth)
            chap_fn = f"text/chap_{i:03d}.xhtml"
            chap = create_html_item(f"Chapter {i}", chap_fn, chunk2, meta.language)
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

    return chapters, chapter_links, chapter_sub_links
