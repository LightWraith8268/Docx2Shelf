"""Themes command argument parser.

This module defines the argument parser for theme-related subcommands,
which handle CSS theme management, customization, and preview functionality.
"""

from __future__ import annotations

import argparse


def add_themes_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add theme-related subcommands and their arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    # Theme Editor subcommand
    theme_editor = subparsers.add_parser(
        "theme-editor", help="Advanced theme editor with visual customization"
    )
    theme_editor.add_argument(
        "--base-theme",
        type=str,
        default="serif",
        help="Base theme to start from (serif, sans, printlike)",
    )
    theme_editor.add_argument("--themes-dir", type=str, help="Directory to store custom themes")

    # List themes subcommand
    list_themes = subparsers.add_parser("list-themes", help="List available CSS themes")
    list_themes.add_argument(
        "--genre",
        help="Filter themes by genre (fantasy, romance, mystery, scifi, academic, general)",
    )

    # Preview themes subcommand
    preview_themes = subparsers.add_parser("preview-themes", help="Preview themes in browser")
    preview_themes.add_argument(
        "--sample-text", type=str, help="Custom sample text file to use for preview"
    )
    preview_themes.add_argument(
        "--themes", nargs="+", help="Specific themes to preview (defaults to all)"
    )
    preview_themes.add_argument(
        "--output-dir", type=str, help="Directory to save preview HTML files"
    )
    preview_themes.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )
