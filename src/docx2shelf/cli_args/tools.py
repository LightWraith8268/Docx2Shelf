"""Tools command argument parser.

This module defines the argument parser for the 'tools' subcommand,
which handles installation and management of optional tools (Pandoc, EPUBCheck).
"""

from __future__ import annotations

import argparse


def add_tools_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add tools subcommand and its arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    m = subparsers.add_parser("tools", help="Manage optional tools (Pandoc, EPUBCheck)")
    m_sub = m.add_subparsers(dest="tool_cmd", required=True)

    # Install subcommand
    mi = m_sub.add_parser("install", help="Install a tool")
    mi.add_argument("name", choices=["pandoc", "epubcheck"], help="Tool name")
    mi.add_argument("--version", dest="version", help="Tool version (optional)")
    mi.add_argument(
        "--preset",
        choices=["stable", "latest", "bleeding"],
        default="stable",
        help="Version preset to use",
    )

    # Uninstall subcommand
    mu = m_sub.add_parser("uninstall", help="Uninstall a tool")
    mu.add_argument("name", choices=["pandoc", "epubcheck", "all"], help="Tool name")

    # Where subcommand
    m_sub.add_parser("where", help="Show tool locations")

    # Health check command
    m_sub.add_parser("doctor", help="Run comprehensive health check on tools setup")

    # Offline bundle commands
    mb = m_sub.add_parser("bundle", help="Create offline installation bundle")
    mb.add_argument("--output", help="Output directory for bundle (default: user data dir)")
    mb.add_argument(
        "--preset",
        choices=["stable", "latest", "bleeding"],
        default="stable",
        help="Version preset for bundled tools",
    )
