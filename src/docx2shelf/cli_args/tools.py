"""Tools command argument parser."""
from __future__ import annotations

import argparse


def add_tools_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add tools subcommand and its arguments.

    TODO Phase 2: Extract all tools arguments from cli.py lines 357-385
    """
    t = subparsers.add_parser("tools", help="Manage optional tools")
    # TODO: Add all tools arguments here
    pass
