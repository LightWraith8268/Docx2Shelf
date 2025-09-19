"""
GUI module for Docx2Shelf.

Provides cross-platform graphical user interface for EPUB conversion.
"""

from .app import main, MainWindow, create_context_menu_windows

__all__ = ["main", "MainWindow", "create_context_menu_windows"]