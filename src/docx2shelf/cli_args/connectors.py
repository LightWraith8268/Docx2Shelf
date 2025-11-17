"""Connectors command argument parser."""
from __future__ import annotations

import argparse


def add_connectors_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add connectors subcommand and its arguments.

    TODO Phase 2: Extract all connectors arguments from cli.py lines 500-518
    """
    c = subparsers.add_parser("connectors", help="Manage document connectors")
    # TODO: Add all connectors arguments here
    pass
