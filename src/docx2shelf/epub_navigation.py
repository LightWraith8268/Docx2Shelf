"""EPUB navigation and structure generation.

This module handles EPUB navigation elements including:
- Table of Contents (ToC) generation with nested structure
- Spine (reading order) setup
- Navigation document generation
- List of Figures and Tables
- Page list generation
- ToC/spine consistency validation
"""

from __future__ import annotations

import re

from .figures import FigureConfig, FigureProcessor
from .metadata import BuildOptions, EpubMetadata


def build_nested_toc(chap_link, sub_links, depth: int = 2, current_depth: int = 2):
    """Build nested ToC structure supporting arbitrary depth.

    Args:
        chap_link: Main chapter link
        sub_links: List of subheading links
        depth: Maximum ToC depth
        current_depth: Current nesting depth (default: 2)

    Returns:
        object | tuple: Single link or tuple of (link, nested_links)
    """
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
        if hasattr(link_info, "href"):  # It's already an epub.Link
            epub_sub_links.append(link_info)

    if epub_sub_links:
        return (chap_link, epub_sub_links)
    else:
        return chap_link


def determine_reader_start_link(chapter_links: list, opts: BuildOptions) -> str:
    """Determine where the main reading content starts.

    Args:
        chapter_links: List of chapter navigation links
        opts: BuildOptions with reader_start_chapter pattern

    Returns:
        str: Link to the start of main content
    """
    start_reading_link = "text/chap_001.xhtml#ch001"  # Default start

    if opts.reader_start_chapter:
        # Find the chapter that matches the start pattern
        for i, chap_link in enumerate(chapter_links):
            if opts.reader_start_chapter.lower() in chap_link.title.lower():
                # Extract chapter number from the link href
                match = re.search(r"chap_(\d+)\.xhtml#(ch\d+)", chap_link.href)
                if match:
                    start_reading_link = chap_link.href
                break

    return start_reading_link


def generate_figure_table_lists(
    book, figure_processor: FigureProcessor, figure_config: FigureConfig, meta: EpubMetadata
) -> list:
    """Generate List of Figures and List of Tables pages.

    Args:
        book: EpubBook instance from ebooklib
        figure_processor: FigureProcessor with figure/table data
        figure_config: FigureConfig with list titles
        meta: EpubMetadata with language

    Returns:
        list: List items (List of Figures and/or List of Tables)
    """
    from .epub_pages import create_html_item

    list_items = []

    # List of Figures
    if figure_processor.get_figure_count() > 0:
        lof_html = figure_processor.generate_list_of_figures()
        if lof_html:
            lof_item = create_html_item(
                figure_config.list_of_figures_title,
                "text/list-of-figures.xhtml",
                lof_html,
                meta.language,
            )
            book.add_item(lof_item)
            list_items.append(lof_item)

    # List of Tables
    if figure_processor.get_table_count() > 0:
        lot_html = figure_processor.generate_list_of_tables()
        if lot_html:
            lot_item = create_html_item(
                figure_config.list_of_tables_title,
                "text/list-of-tables.xhtml",
                lot_html,
                meta.language,
            )
            book.add_item(lot_item)
            list_items.append(lot_item)

    return list_items


def setup_book_navigation(
    book,
    chapters: list,
    chapter_links: list,
    chapter_sub_links: list,
    opts: BuildOptions,
    title_page,
    copyright_page,
    matter_items: list,
    list_items: list,
) -> None:
    """Setup EPUB navigation including ToC, spine, and navigation documents.

    This function orchestrates the complete navigation setup for an EPUB:
    1. Builds the spine (reading order)
    2. Constructs the ToC with nested structure
    3. Adds NCX and Nav items
    4. Validates ToC/spine consistency
    5. Optionally generates page list

    Args:
        book: EpubBook instance from ebooklib
        chapters: List of chapter items
        chapter_links: List of main chapter navigation links
        chapter_sub_links: List of subheading links per chapter
        opts: BuildOptions with toc_depth and page_list settings
        title_page: Title page item
        copyright_page: Copyright page item
        matter_items: Front/back matter items
        list_items: List of Figures/Tables items
    """
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Import HTML item creator for page list
    from .epub_pages import create_html_item

    depth = max(1, min(6, opts.toc_depth))

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
            toc_items.append(build_nested_toc(chap_link, chapter_sub_links[i], depth))

    book.toc = tuple(toc_items)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Validate TOC and spine consistency
    validate_toc_spine_consistency(book, spine_items, toc_items, opts.quiet)

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
        # Note: We need meta for language, so we'll pass it in
        # For now, use 'en' as default or get from book metadata
        page_list_item = create_html_item(
            "Page List",
            "text/page-list.xhtml",
            page_list_html,
            book.language if hasattr(book, "language") else "en",
        )
        book.add_item(page_list_item)


def validate_toc_spine_consistency(book, spine_items, toc_items, quiet: bool = False) -> bool:
    """Validate that TOC entries match spine order and provide warnings for inconsistencies.

    Args:
        book: EpubBook instance from ebooklib
        spine_items: List of items in reading order
        toc_items: List of ToC navigation items
        quiet: Suppress warning output if True

    Returns:
        bool: True if no warnings, False if inconsistencies found
    """
    warnings = []

    # Get spine order (excluding 'nav' which is first)
    spine_order = [item for item in book.spine if item != "nav"]

    # Create mapping of spine items to their filenames
    spine_filenames = []
    for spine_ref in spine_order:
        # Find the actual item in the book
        for item in book.items:
            if hasattr(item, "id") and item.id == spine_ref:
                if hasattr(item, "file_name"):
                    spine_filenames.append(item.file_name)
                break

    # Extract TOC filenames in order
    toc_filenames = []
    for toc_item in toc_items:
        if hasattr(toc_item, "href") and toc_item.href:
            # Remove fragment identifier if present
            href = toc_item.href.split("#")[0]
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
