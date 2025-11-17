"""Plugins command argument parser."""
from __future__ import annotations

import argparse


def add_plugins_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add plugins subcommand and its arguments.

    TODO Phase 2: Extract all plugins arguments from cli.py lines 386-499
    """
    p = subparsers.add_parser("plugins", help="Manage plugins and hooks")
    # TODO: Add all plugins arguments here
    pass
