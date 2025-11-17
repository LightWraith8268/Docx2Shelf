"""Modular argument parser for docx2shelf CLI.

This package splits the monolithic _arg_parser() function into focused modules:
- build.py: Build command arguments
- tools.py: Tools management arguments
- ai.py: AI command arguments
- enterprise.py: Enterprise command arguments
- plugins.py: Plugin management arguments
- connectors.py: Connector arguments
- themes.py: Theme-related arguments
- misc.py: Miscellaneous commands (wizard, batch, etc.)
"""
from __future__ import annotations

import argparse

from .ai import add_ai_parser
from .build import add_build_parser
from .connectors import add_connectors_parser
from .misc import add_misc_parsers
from .plugins import add_plugins_parser
from .themes import add_themes_parser
from .tools import add_tools_parser


def _arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands.

    Returns:
        Fully configured ArgumentParser with all subcommands.
    """
    from ..version import get_version

    p = argparse.ArgumentParser(
        prog="docx2shelf",
        description="Convert a DOCX manuscript into a valid EPUB 3 (offline)",
    )

    p.add_argument(
        "--version",
        action="version",
        version=get_version(),
        help="Show version information and exit",
    )

    sub = p.add_subparsers(dest="command", required=False)

    # Add all subcommand parsers
    add_build_parser(sub)
    add_tools_parser(sub)
    add_plugins_parser(sub)
    add_connectors_parser(sub)
    add_ai_parser(sub)
    add_themes_parser(sub)
    add_misc_parsers(sub)

    return p


__all__ = ["_arg_parser"]
