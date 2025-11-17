"""Build command argument parser.

This module defines the argument parser for the 'build' subcommand,
which handles EPUB generation from manuscript files.
"""

from __future__ import annotations

import argparse


def add_build_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add build subcommand and its arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    b = subparsers.add_parser("build", help="Build an EPUB from inputs")
    b.add_argument(
        "--input",
        type=str,
        help="Path to manuscript file or directory of files (.docx, .md, .txt, .html)",
    )
    b.add_argument("--cover", type=str, help="Path to cover image (jpg/png)")
    b.add_argument("--title", type=str, help="Book title")
    b.add_argument("--author", type=str, help="Author name")
    b.add_argument("--seriesName", type=str, help="Series name (optional)")
    b.add_argument("--seriesIndex", type=str, help="Series index/number (optional)")
    b.add_argument(
        "--title-sort", dest="title_sort", type=str, help="Calibre title sort (optional)"
    )
    b.add_argument(
        "--author-sort", dest="author_sort", type=str, help="Calibre author sort (optional)"
    )
    b.add_argument("--description", type=str, help="Long description (optional)")
    b.add_argument("--isbn", type=str, help="ISBN-13 digits only (optional)")
    b.add_argument("--language", type=str, default="en", help="Language code, e.g., en")
    b.add_argument("--publisher", type=str, help="Publisher (optional)")
    b.add_argument("--pubdate", type=str, help="Publication date ISO YYYY-MM-DD (optional)")
    b.add_argument("--uuid", type=str, help="UUID to use when no ISBN (optional)")
    b.add_argument("--subjects", type=str, help="Comma-separated subjects")
    b.add_argument("--keywords", type=str, help="Comma-separated keywords")

    b.add_argument(
        "--split-at",
        choices=["h1", "h2", "h3", "pagebreak", "mixed"],
        default="h1",
        help="How to split content into XHTML files",
    )
    b.add_argument(
        "--mixed-split-pattern",
        type=str,
        help="Mixed split pattern: 'h1,pagebreak' or 'h1:main,pagebreak:appendix' etc.",
    )

    # Import themes dynamically to get available themes
    try:
        from ..themes import get_available_themes

        available_themes = get_available_themes()
    except ImportError:
        available_themes = ["serif", "sans", "printlike"]  # Fallback

    b.add_argument(
        "--theme",
        choices=available_themes,
        default="serif",
        help="Base CSS theme (use --list-themes to see all options)",
    )
    b.add_argument(
        "--store-profile",
        choices=["kdp", "apple", "kobo", "google", "bn", "generic"],
        help="Optimize EPUB for specific store (Amazon KDP, Apple Books, Kobo, Google Play, B&N, or generic)",
    )
    b.add_argument("--embed-fonts", type=str, help="Directory of TTF/OTF to embed")
    b.add_argument(
        "--image-quality",
        type=int,
        default=85,
        help="JPEG/WebP quality for image compression (1-100)",
    )
    b.add_argument(
        "--image-max-width", type=int, default=1200, help="Maximum image width in pixels"
    )
    b.add_argument(
        "--image-max-height", type=int, default=1600, help="Maximum image height in pixels"
    )
    b.add_argument(
        "--image-format",
        choices=["original", "webp", "avif"],
        default="webp",
        help="Convert images to modern format",
    )
    b.add_argument(
        "--enhanced-images",
        action="store_true",
        help="Enable enhanced image processing for edge cases (CMYK, transparency, large images)",
    )
    b.add_argument(
        "--vertical-writing",
        action="store_true",
        help="Enable vertical writing mode for CJK languages",
    )
    b.add_argument("--hyphenate", choices=["on", "off"], default="on")
    b.add_argument("--justify", choices=["on", "off"], default="on")
    b.add_argument("--toc-depth", type=int, default=2, help="Table of contents depth (1-6)")
    b.add_argument(
        "--chapter-start-mode",
        choices=["auto", "manual", "mixed"],
        default="auto",
        help="TOC chapter detection: auto (scan headings), manual (user-defined), mixed (both)",
    )
    b.add_argument(
        "--chapter-starts",
        type=str,
        help="Comma-separated list of chapter start text patterns for manual TOC mode",
    )
    b.add_argument(
        "--reader-start-chapter",
        type=str,
        help="Chapter title or pattern where reader should start (e.g., 'Chapter 1', 'Prologue')",
    )
    b.add_argument("--page-list", choices=["on", "off"], default="off")
    b.add_argument("--css", type=str, help="Path to extra CSS to merge (optional)")
    b.add_argument("--page-numbers", choices=["on", "off"], default="off")
    b.add_argument("--epub-version", type=str, default="3")
    b.add_argument(
        "--epub2-compat",
        action="store_true",
        help="Enable EPUB 2 compatibility mode (stricter CSS)",
    )
    b.add_argument("--cover-scale", choices=["contain", "cover"], default="contain")
    b.add_argument(
        "--font-size", dest="font_size", type=str, help="Base font size (e.g., 1rem, 12pt)"
    )
    b.add_argument(
        "--line-height", dest="line_height", type=str, help="Base line height (e.g., 1.5)"
    )

    b.add_argument("--dedication", type=str, help="Path to plain-text dedication (optional)")
    b.add_argument("--ack", type=str, help="Path to plain-text acknowledgements (optional)")

    # AI Enhancement Options
    b.add_argument(
        "--ai-enhance", action="store_true", help="Enable AI-powered metadata enhancement"
    )
    b.add_argument(
        "--ai-genre", action="store_true", help="Use AI for genre detection and keyword generation"
    )
    b.add_argument(
        "--ai-alt-text", action="store_true", help="Generate AI-powered alt text for images"
    )
    b.add_argument(
        "--ai-interactive", action="store_true", help="Interactive AI suggestions with user prompts"
    )
    b.add_argument("--ai-config", type=str, help="Path to AI configuration file (optional)")

    b.add_argument("--output", type=str, help="Output .epub path (optional)")
    b.add_argument(
        "--output-pattern",
        dest="output_pattern",
        type=str,
        help="Filename pattern with placeholders {title}, {series}, {index}, {index2}",
    )
    b.add_argument("--inspect", action="store_true", help="Emit inspect folder with sources")
    b.add_argument("--dry-run", action="store_true", help="Print planned manifest/spine only")
    b.add_argument(
        "--preview",
        action="store_true",
        help="Generate live preview in browser instead of EPUB file",
    )
    b.add_argument(
        "--preview-port", type=int, default=8000, help="Port for preview server (default: 8000)"
    )

    # Import profiles for dynamic choices
    try:
        from ..profiles import get_available_profiles

        available_profiles = get_available_profiles()
        profile_help = (
            "Publishing profile to pre-fill settings (use --list-profiles to see all options)"
        )
    except ImportError:
        available_profiles = ["kdp", "kobo", "apple", "generic", "legacy"]
        profile_help = "Publishing profile to pre-fill settings"

    b.add_argument("--profile", choices=available_profiles, help=profile_help)
    b.add_argument("--json-output", help="Output build results in JSON format to specified file")
    b.add_argument(
        "--epubcheck",
        choices=["on", "off"],
        default="on",
        help="Validate with EPUBCheck if available",
    )
    b.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt; use provided defaults and flags only",
    )
    b.add_argument(
        "--auto-install-tools",
        action="store_true",
        help="Automatically install Pandoc/EPUBCheck when missing (no prompts)",
    )
    b.add_argument(
        "--no-install-tools", action="store_true", help="Do not install tools even if missing"
    )
    b.add_argument(
        "--prompt-all", action="store_true", help="Prompt for every field even if prefilled"
    )
    b.add_argument("--quiet", action="store_true", help="Reduce output (errors only)")
    b.add_argument("--verbose", action="store_true", help="Increase output (extra diagnostics)")
