"""
Store Profile Manager Plugin for Docx2Shelf.

Provides validation for major ebook retailers including KDP, Apple Books, Kobo, and others.
"""

from .plugin import StoreProfilePlugin

__version__ = "1.0.0"
__all__ = ["StoreProfilePlugin"]


def create_plugin():
    """Plugin entry point."""
    return StoreProfilePlugin()