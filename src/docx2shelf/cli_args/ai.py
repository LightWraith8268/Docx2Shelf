"""AI command argument parser.

This module defines the argument parser for the 'ai' subcommand,
which handles AI-powered document analysis and enhancement features.
"""

from __future__ import annotations

import argparse


def add_ai_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add AI subcommand and its arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    ai = subparsers.add_parser("ai", help="AI-powered document analysis and enhancement")
    ai_sub = ai.add_subparsers(dest="ai_action", required=True)

    # AI metadata enhancement
    ai_meta = ai_sub.add_parser("metadata", help="Enhance metadata using AI analysis")
    ai_meta.add_argument("input_file", help="Document file to analyze")
    ai_meta.add_argument(
        "--interactive", action="store_true", help="Interactive metadata suggestions"
    )
    ai_meta.add_argument("--output", help="Output enhanced metadata to file")

    # AI genre detection
    ai_genre = ai_sub.add_parser("genre", help="Detect genres and keywords using AI")
    ai_genre.add_argument("input_file", help="Document file to analyze")
    ai_genre.add_argument("--json", action="store_true", help="Output results as JSON")

    # AI alt text generation
    ai_alt = ai_sub.add_parser("alt-text", help="Generate alt text for images using AI")
    ai_alt.add_argument("input_path", help="Image file or document with images")
    ai_alt.add_argument(
        "--interactive", action="store_true", help="Interactive alt text suggestions"
    )
    ai_alt.add_argument("--output", help="Output alt text suggestions to file")

    # AI configuration
    ai_config = ai_sub.add_parser("config", help="Configure AI settings")
    ai_config.add_argument("--list", action="store_true", help="List current AI configuration")
    ai_config.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value"
    )
    ai_config.add_argument("--reset", action="store_true", help="Reset to default configuration")
