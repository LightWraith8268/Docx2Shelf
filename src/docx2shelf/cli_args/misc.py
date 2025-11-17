"""Miscellaneous command argument parsers.

This module defines the argument parsers for miscellaneous subcommands that don't
fit into specific categories: init-metadata, wizard, batch, list-profiles, update,
doctor, interactive, gui, checklist, quality, validate, and convert.
"""

from __future__ import annotations

import argparse


def add_misc_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add miscellaneous subcommands and their arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    # Init metadata template subcommand
    t = subparsers.add_parser(
        "init-metadata", help="Generate a metadata.txt template next to the input file"
    )
    t.add_argument(
        "--input", type=str, required=True, help="Path to manuscript file (.docx, .md, .txt)"
    )
    t.add_argument("--cover", type=str, help="Optional default cover path")
    t.add_argument(
        "--output",
        type=str,
        help="Optional path to write template (defaults to input folder/metadata.txt)",
    )
    t.add_argument("--force", action="store_true", help="Overwrite existing file if present")

    # Wizard subcommand
    wizard = subparsers.add_parser(
        "wizard", help="Interactive conversion wizard with step-by-step guidance"
    )
    wizard.add_argument(
        "--input", type=str, help="Optional path to input file to start wizard with"
    )
    wizard.add_argument(
        "--no-preview", action="store_true", help="Disable real-time preview generation"
    )
    wizard.add_argument("--session-dir", type=str, help="Directory to store wizard session files")

    # List profiles subcommand
    list_profiles = subparsers.add_parser("list-profiles", help="List available publishing profiles")
    list_profiles.add_argument(
        "--profile",
        help="Show detailed information for a specific profile",
    )

    # Batch mode subcommand - needs available_profiles and available_themes from build.py
    # For now, we'll accept strings and validate later in the handler
    batch = subparsers.add_parser("batch", help="Process multiple DOCX files in batch mode")
    batch.add_argument(
        "--dir", dest="batch_dir", required=True, help="Directory containing DOCX files"
    )
    batch.add_argument(
        "--pattern",
        dest="batch_pattern",
        default="*.docx",
        help="File pattern to match (default: *.docx)",
    )
    batch.add_argument(
        "--output-dir", dest="batch_output_dir", help="Output directory for generated EPUBs"
    )
    batch.add_argument("--parallel", action="store_true", help="Process files in parallel")
    batch.add_argument("--max-workers", type=int, help="Maximum number of parallel workers")
    batch.add_argument("--report", help="Generate batch processing report to file")

    # Add common build options to batch command
    batch.add_argument("--profile", help="Publishing profile to use")
    batch.add_argument("--theme", default="serif", help="Base CSS theme")
    batch.add_argument(
        "--store-profile",
        choices=["kdp", "apple", "kobo", "google", "bn", "generic"],
        help="Optimize EPUB for specific store",
    )
    batch.add_argument("--epub-version", type=str, default="3")
    batch.add_argument("--image-format", choices=["original", "webp", "avif"], default="webp")
    batch.add_argument("--epubcheck", choices=["on", "off"], default="on")

    # Update subcommand
    subparsers.add_parser("update", help="Update docx2shelf to the latest version")

    # Environment diagnostic command
    subparsers.add_parser("doctor", help="Run comprehensive environment diagnostics")

    # Interactive CLI command
    subparsers.add_parser("interactive", help="Launch interactive menu-driven CLI interface")

    # GUI command
    subparsers.add_parser("gui", help="Launch graphical user interface")

    # Checklist subcommand
    check = subparsers.add_parser("checklist", help="Run publishing store compatibility checklists")
    check.add_argument("--metadata", help="Path to metadata.txt file (default: ./metadata.txt)")
    check.add_argument("--cover", help="Path to cover image file")
    check.add_argument(
        "--store",
        choices=["kdp", "apple", "kobo", "all"],
        default="all",
        help="Which store to check (default: all)",
    )
    check.add_argument("--json", action="store_true", help="Output results as JSON")

    # Quality assessment subcommand
    quality = subparsers.add_parser("quality", help="Comprehensive quality analysis of EPUB files")
    quality.add_argument("epub_path", help="Path to EPUB file to analyze")
    quality.add_argument(
        "--content-files", nargs="*", help="Additional content files to validate (XHTML/HTML)"
    )
    quality.add_argument(
        "--target-level",
        choices=["A", "AA", "AAA"],
        default="AA",
        help="WCAG accessibility target level (default: AA)",
    )
    quality.add_argument(
        "--skip-accessibility", action="store_true", help="Skip accessibility compliance checking"
    )
    quality.add_argument(
        "--skip-content-validation",
        action="store_true",
        help="Skip content validation (grammar, style, formatting)",
    )
    quality.add_argument(
        "--skip-quality-scoring", action="store_true", help="Skip overall quality scoring"
    )
    quality.add_argument("--json", action="store_true", help="Output results as JSON")
    quality.add_argument("--output", help="Save detailed report to file")
    quality.add_argument(
        "--auto-fix", action="store_true", help="Automatically fix issues where possible"
    )
    quality.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed issue descriptions and recommendations",
    )

    # EPUB validation subcommand
    validate = subparsers.add_parser(
        "validate", help="Validate EPUB files using EPUBCheck and custom rules"
    )
    validate.add_argument("epub_path", help="Path to EPUB file to validate")
    validate.add_argument("--verbose", action="store_true", help="Show detailed validation report")
    validate.add_argument("--skip-epubcheck", action="store_true", help="Skip EPUBCheck validation")
    validate.add_argument(
        "--skip-custom", action="store_true", help="Skip custom validation checks"
    )
    validate.add_argument(
        "--timeout", type=int, default=120, help="Timeout for EPUBCheck in seconds"
    )

    # Convert command for format conversion
    convert = subparsers.add_parser(
        "convert", help="Convert EPUB to other formats (PDF, MOBI, AZW3, Web, Text)"
    )
    convert.add_argument("input", help="Path to EPUB file to convert")
    convert.add_argument(
        "--format",
        "-f",
        choices=["pdf", "mobi", "azw3", "web", "txt", "text"],
        required=True,
        help="Output format",
    )
    convert.add_argument(
        "--output", "-o", help="Output file/directory path (auto-generated if not specified)"
    )
    convert.add_argument(
        "--quality",
        choices=["standard", "high", "web"],
        default="standard",
        help="Output quality level",
    )
    convert.add_argument(
        "--compression",
        action="store_true",
        default=True,
        help="Enable compression (where applicable)",
    )
