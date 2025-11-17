"""EPUB metadata and cover setup.

This module handles all EPUB metadata configuration including:
- Book identifiers (ISBN, UUID)
- Basic metadata (title, author, language, publisher)
- Publication dates and descriptions
- Sorting metadata for Calibre
- Subjects and keywords
- Series information
- Cover image processing
"""

from __future__ import annotations

import uuid as _uuid

from .metadata import EpubMetadata


def setup_book_metadata(book, meta: EpubMetadata) -> str:
    """Configure all EPUB metadata for the book.

    Args:
        book: EpubBook instance from ebooklib
        meta: EpubMetadata instance with all metadata fields

    Returns:
        str: The identifier used for the book (ISBN, UUID, or generated UUID)
    """
    # Generate or use provided identifier
    identifier = meta.isbn or meta.uuid or str(_uuid.uuid4())
    book.set_identifier(identifier)

    # Basic metadata
    book.set_title(meta.title)
    book.set_language(meta.language or "en")
    book.add_author(meta.author)

    # Optional metadata
    if meta.publisher:
        book.add_metadata("DC", "publisher", meta.publisher)
    if meta.pubdate:
        book.add_metadata("DC", "date", meta.pubdate.isoformat())
    if meta.description:
        book.add_metadata("DC", "description", meta.description)

    # Calibre sorting metadata
    if meta.title_sort:
        book.add_metadata(None, "meta", meta.title_sort, {"name": "calibre:title_sort"})
    if meta.author_sort:
        book.add_metadata(None, "meta", meta.author_sort, {"name": "calibre:author_sort"})

    # Subjects and keywords
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

    return identifier


def add_cover_to_book(book, meta: EpubMetadata) -> None:
    """Add cover image to the EPUB book.

    Args:
        book: EpubBook instance from ebooklib
        meta: EpubMetadata instance with cover_path
    """
    cover_bytes = meta.cover_path.read_bytes()
    # Let ebooklib create the cover page automatically
    book.set_cover(meta.cover_path.name, cover_bytes)
