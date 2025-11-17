"""Enterprise command argument parser."""
from __future__ import annotations

import argparse


def add_enterprise_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add enterprise subcommand and its arguments.

    TODO Phase 2: Extract all enterprise arguments from cli.py
    """
    ent = subparsers.add_parser("enterprise", help="Enterprise features")
    # TODO: Add all enterprise arguments here
    pass
