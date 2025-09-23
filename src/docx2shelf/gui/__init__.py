"""
GUI module for Docx2Shelf.

Provides cross-platform graphical user interface for EPUB conversion.
"""

from .modern_app import main

# Legacy support
from .app import MainWindow, create_context_menu_windows
from .app import main as traditional_main

__all__ = ["main", "traditional_main", "MainWindow", "create_context_menu_windows"]