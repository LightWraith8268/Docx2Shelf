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


def _arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands.

    This is a placeholder that will be populated in Phase 2.
    For now, it just creates the base parser.
    """
    from ..cli import get_version_string

    p = argparse.ArgumentParser(
        prog="docx2shelf",
        description="Convert a DOCX manuscript into a valid EPUB 3 (offline)",
    )

    p.add_argument(
        "--version",
        action="version",
        version=get_version_string(),
        help="Show version information and exit",
    )

    sub = p.add_subparsers(dest="command", required=False)

    # TODO Phase 2: Add all subcommand parsers here
    # add_build_parser(sub)
    # add_tools_parser(sub)
    # add_ai_parser(sub)
    # add_enterprise_parser(sub)
    # add_plugins_parser(sub)
    # add_connectors_parser(sub)
    # add_themes_parser(sub)
    # add_misc_parsers(sub)

    return p


__all__ = ["_arg_parser"]
