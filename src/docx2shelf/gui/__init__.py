"""
GUI module for Docx2Shelf.

Provides modern cross-platform graphical user interface for EPUB conversion.
"""

try:
    from .modern_app import ModernDocx2ShelfApp
    __all__ = ["ModernDocx2ShelfApp"]
except ImportError:
    # Fallback if module cannot be imported
    __all__ = []