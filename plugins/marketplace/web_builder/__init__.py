"""
Web Builder Plugin for Docx2Shelf.

Provides web-based interface for EPUB conversion.
"""

from .plugin import WebBuilderPlugin

__version__ = "1.0.0"
__all__ = ["WebBuilderPlugin"]


def create_plugin():
    """Plugin entry point."""
    return WebBuilderPlugin()