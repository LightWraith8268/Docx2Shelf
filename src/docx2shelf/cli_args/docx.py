"""DOCX generation subcommand argument parser.

Generates a .docx file from supported manuscript inputs (.md, .html, .htm, .txt, .docx).
Pandoc-backed; uses the bundled Pandoc binary managed by `docx2shelf tools install pandoc`.
"""

from __future__ import annotations

import argparse


def add_docx_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add `docx` subcommand for generating DOCX files."""
    p = subparsers.add_parser(
        "docx",
        help="Generate a .docx file from a manuscript (.md/.html/.txt/.docx)",
    )
    p.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to source manuscript (.md, .html, .htm, .txt, .docx)",
    )
    p.add_argument(
        "--output",
        type=str,
        help="Path to write .docx (default: <input stem>.docx next to input)",
    )
    p.add_argument(
        "--reference-doc",
        dest="reference_doc",
        type=str,
        help="Optional Pandoc --reference-doc styled DOCX template",
    )
    p.add_argument(
        "--metadata",
        type=str,
        help="Optional metadata.txt/metadata.md to inject title/author into DOCX core props",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )
