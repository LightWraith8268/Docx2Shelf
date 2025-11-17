"""Build command argument parser."""
from __future__ import annotations

import argparse


def add_build_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add build subcommand and its arguments.

    TODO Phase 2: Extract all build arguments from cli.py lines 64-259
    """
    b = subparsers.add_parser("build", help="Build an EPUB from inputs")
    # TODO: Add all build arguments here
    pass
