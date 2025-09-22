"""
GUI module for Docx2Shelf.

Provides cross-platform graphical user interface for EPUB conversion.
"""

from .app import MainWindow, create_context_menu_windows, main

__all__ = ["main", "MainWindow", "create_context_menu_windows"]