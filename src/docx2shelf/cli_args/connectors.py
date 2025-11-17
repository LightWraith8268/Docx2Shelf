"""Connectors command argument parser.

This module defines the argument parser for the 'connectors' subcommand,
which handles document connector management and operations.
"""

from __future__ import annotations

import argparse


def add_connectors_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add connectors subcommand and its arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    c = subparsers.add_parser("connectors", help="Manage document connectors")
    c_sub = c.add_subparsers(dest="connector_cmd", required=True)

    # List connectors
    c_sub.add_parser("list", help="List available connectors")

    # Enable connector
    ce = c_sub.add_parser("enable", help="Enable a connector")
    ce.add_argument("name", help="Connector name")
    ce.add_argument(
        "--allow-network", action="store_true", help="Allow network access for connector"
    )

    # Disable connector
    cd = c_sub.add_parser("disable", help="Disable a connector")
    cd.add_argument("name", help="Connector name")

    # Authenticate with connector
    ca = c_sub.add_parser("auth", help="Authenticate with a connector")
    ca.add_argument("name", help="Connector name")
    ca.add_argument("--credentials", help="Path to credentials file")

    # Fetch document from connector
    cf = c_sub.add_parser("fetch", help="Fetch document from connector")
    cf.add_argument("connector", help="Connector name")
    cf.add_argument("document_id", help="Document ID")
    cf.add_argument("--output", help="Output path")
