"""EPUB static page generation.

This module handles creation of standard EPUB pages including:
- Title page
- Copyright page
- Front/back matter (dedication, acknowledgements, preface, etc.)
- Landmarks navigation page
"""

from __future__ import annotations

import datetime as _dt
from importlib import resources
from pathlib import Path

from .metadata import BuildOptions, EpubMetadata


def _read_text(path: Path) -> str:
    """Read text file with UTF-8 encoding.

    Args:
        path: Path to text file

    Returns:
        str: File contents
    """
    return path.read_text(encoding="utf-8")


def create_html_item(title: str, file_name: str, content: str, lang: str) -> object:
    """Create an EPUB HTML item.

    Args:
        title: Human-readable title for the item
        file_name: Relative file path in EPUB (e.g., 'text/chapter01.xhtml')
        content: HTML content (str or bytes)
        lang: Language code (e.g., 'en', 'es', 'ja')

    Returns:
        EpubHtml: ebooklib HTML item
    """
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


def create_title_page(book, meta: EpubMetadata) -> object:
    """Create and add title page to EPUB book.

    Attempts to load the title.xhtml template from docx2shelf.templates
    and replaces placeholders with actual title and author. Falls back
    to a simple HTML structure if template is not found.

    Args:
        book: EpubBook instance from ebooklib
        meta: EpubMetadata with title, author, and language

    Returns:
        EpubHtml: Title page item
    """
    try:
        title_path = resources.files("docx2shelf.templates").joinpath("title.xhtml")
        with title_path.open("r", encoding="utf-8") as fh:
            content = (
                fh.read().replace("{{ title }}", meta.title).replace("{{ author }}", meta.author)
            )
    except Exception:
        content = f"<html><body><h1>{meta.title}</h1><p>{meta.author}</p></body></html>"

    title_page = create_html_item("Title Page", "text/title.xhtml", content, meta.language)
    book.add_item(title_page)
    return title_page


def create_copyright_page(book, meta: EpubMetadata) -> object:
    """Create and add copyright page to EPUB book.

    Generates a simple copyright notice with the current year and author name.

    Args:
        book: EpubBook instance from ebooklib
        meta: EpubMetadata with author and language

    Returns:
        EpubHtml: Copyright page item
    """
    year = str(_dt.date.today().year)
    copyright_html = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Copyright</title></head><body>"
        f"<section><h2>Copyright</h2><p>© {year} {meta.author}. All rights reserved.</p></section>"
        "</body></html>"
    )

    copyright_page = create_html_item(
        "Copyright", "text/copyright.xhtml", copyright_html, meta.language
    )
    book.add_item(copyright_page)
    return copyright_page


def create_front_back_matter(book, opts: BuildOptions, meta: EpubMetadata) -> list:
    """Create and add front/back matter pages from text files.

    Processes optional dedication and acknowledgements text files if they exist.

    Args:
        book: EpubBook instance from ebooklib
        opts: BuildOptions with dedication_txt and ack_txt paths
        meta: EpubMetadata with language

    Returns:
        list[EpubHtml]: List of front/back matter items created
    """
    matter_items = []

    # Dedication page
    if opts.dedication_txt and opts.dedication_txt.exists():
        txt = _read_text(opts.dedication_txt)
        ded_html = f"<h2>Dedication</h2><p>{txt}</p>"
        matter_items.append(
            create_html_item("Dedication", "text/dedication.xhtml", ded_html, meta.language)
        )

    # Acknowledgements page
    if opts.ack_txt and opts.ack_txt.exists():
        txt = _read_text(opts.ack_txt)
        matter_items.append(
            create_html_item(
                "Acknowledgements",
                "text/ack.xhtml",
                f"<h2>Acknowledgements</h2><p>{txt}</p>",
                meta.language,
            )
        )

    # Add all matter items to book
    for item in matter_items:
        book.add_item(item)

    return matter_items


def create_landmarks_page(
    book,
    meta: EpubMetadata,
    opts: BuildOptions,
    matter_items: list,
    list_items: list,
    chapters: list,
    start_reading_link: str,
) -> object | None:
    """Create and add landmarks navigation page to EPUB book.

    Landmarks provide structural navigation points for better reader experience.
    Includes cover, title page, TOC, copyright, front matter, and main content start.

    Args:
        book: EpubBook instance from ebooklib
        meta: EpubMetadata with cover_path and language
        opts: BuildOptions with quiet flag
        matter_items: List of front/back matter items
        list_items: List of figure/table list items
        chapters: List of chapter items
        start_reading_link: Link to where main content starts

    Returns:
        EpubHtml | None: Landmarks item if successful, None on error
    """
    try:
        # Build landmarks based on actual spine content
        landmark_entries = []

        # Cover is special - always first if present
        if meta.cover_path and meta.cover_path.exists():
            landmark_entries.append("<li><a epub:type='cover' href='cover.xhtml'>Cover</a></li>")

        # Title page
        landmark_entries.append(
            "<li><a epub:type='titlepage' href='text/title.xhtml'>Title Page</a></li>"
        )

        # Table of contents
        landmark_entries.append(
            "<li><a epub:type='toc' href='nav.xhtml'>Table of Contents</a></li>"
        )

        # Copyright page
        landmark_entries.append(
            "<li><a epub:type='copyright-page' href='text/copyright.xhtml'>Copyright</a></li>"
        )

        # Add other front matter items if they exist
        for item in matter_items:
            if hasattr(item, "file_name") and hasattr(item, "title"):
                # Determine appropriate epub:type based on content
                if "dedication" in item.file_name.lower():
                    epub_type = "dedication"
                elif "acknowledgment" in item.file_name.lower() or "ack" in item.file_name.lower():
                    epub_type = "acknowledgments"
                elif "preface" in item.file_name.lower():
                    epub_type = "preface"
                elif "foreword" in item.file_name.lower():
                    epub_type = "foreword"
                else:
                    epub_type = "frontmatter"
                landmark_entries.append(
                    f"<li><a epub:type='{epub_type}' href='{item.file_name}'>{item.title}</a></li>"
                )

        # Add list items if present
        for item in list_items:
            if hasattr(item, "file_name") and hasattr(item, "title"):
                epub_type = (
                    "loi"
                    if "figure" in item.title.lower()
                    else "lot"
                    if "table" in item.title.lower()
                    else "frontmatter"
                )
                landmark_entries.append(
                    f"<li><a epub:type='{epub_type}' href='{item.file_name}'>{item.title}</a></li>"
                )

        # Start of main content
        if chapters:
            landmark_entries.append(
                f"<li><a epub:type='bodymatter' href='{start_reading_link}'>Start Reading</a></li>"
            )

        landmarks_html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops'>"
            "<head><title>Landmarks</title></head><body>"
            "<nav epub:type='landmarks'><h2>Guide</h2><ol>"
            + "".join(landmark_entries)
            + "</ol></nav>"
            "</body></html>"
        )

        landmarks_item = create_html_item(
            "Landmarks", "text/landmarks.xhtml", landmarks_html, meta.language
        )
        book.add_item(landmarks_item)
        return landmarks_item

    except Exception as e:
        if not opts.quiet:
            print(f"Warning: Could not generate landmarks: {e}")
        return None
