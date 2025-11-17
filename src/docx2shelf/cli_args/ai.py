"""AI command argument parser."""
from __future__ import annotations

import argparse


def add_ai_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add AI subcommand and its arguments.

    TODO Phase 2: Extract all AI arguments from cli.py lines 519-602
    """
    ai = subparsers.add_parser("ai", help="AI-powered document analysis")
    # TODO: Add all AI arguments here
    pass
