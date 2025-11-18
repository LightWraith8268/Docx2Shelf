"""Batch processing and wizard command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_batch_mode(args: argparse.Namespace) -> int:
    """Run batch processing mode."""
    try:
        from ..batch import create_batch_report, run_batch_mode, validate_batch_args

        # Validate batch arguments
        errors = validate_batch_args(args)
        if errors:
            for error in errors:
                print(f"Error: {error}", file=sys.stderr)
            return 1

        # Run batch processing
        summary = run_batch_mode(
            directory=Path(args.batch_dir),
            pattern=args.batch_pattern,
            output_dir=Path(args.batch_output_dir) if args.batch_output_dir else None,
            parallel=args.parallel,
            max_workers=args.max_workers,
            base_args=args,
            quiet=getattr(args, "quiet", False),
        )

        # Generate report if requested
        if args.report:
            report_path = Path(args.report)
            create_batch_report(summary, report_path)
            print(f"[BATCH] Batch report written to: {report_path}")

        # Return non-zero if any files failed
        return 0 if summary["failed"] == 0 else 1

    except ImportError:
        print("Batch processing not available.")
        return 1
    except Exception as e:
        print(f"Batch processing error: {e}", file=sys.stderr)
        return 1


def run_wizard(args: argparse.Namespace) -> int:
    """Run the interactive conversion wizard."""
    from ..wizard import run_wizard_mode

    # Parse arguments
    input_file = None
    if args.input:
        input_file = Path(args.input)
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return 1

    session_dir = None
    if args.session_dir:
        session_dir = Path(args.session_dir)

    # Configure wizard settings
    if args.no_preview:
        print("Real-time preview disabled")

    try:
        return run_wizard_mode(input_file)
    except KeyboardInterrupt:
        print("\n\nWizard cancelled by user.")
        return 1
    except Exception as e:
        print(f"Wizard error: {e}")
        return 1
