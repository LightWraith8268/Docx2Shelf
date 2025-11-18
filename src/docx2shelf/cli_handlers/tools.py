"""Tools, validation, and update command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_tools(args: argparse.Namespace) -> int:
    from ..tools import (
        epubcheck_cmd,
        install_epubcheck,
        install_pandoc,
        pandoc_path,
        tools_dir,
        uninstall_all_tools,
        uninstall_epubcheck,
        uninstall_pandoc,
    )

    if args.tool_cmd == "install":
        # Use version preset if no specific version provided
        version = args.version
        if not version and hasattr(args, "preset"):
            from ..tools import get_pinned_version

            version = get_pinned_version(args.name)

        if args.name == "pandoc":
            p = install_pandoc(version) if version else install_pandoc()
            print(f"Installed pandoc at: {p}")
            return 0
        if args.name == "epubcheck":
            p = install_epubcheck(version) if version else install_epubcheck()
            print(f"Installed epubcheck at: {p}")
            return 0

    elif args.tool_cmd == "where":
        td = tools_dir()
        print(f"Tools dir: {td}")
        print(f"Pandoc: {pandoc_path()}")
        print(f"EPUBCheck: {epubcheck_cmd()}")
        return 0

    elif args.tool_cmd == "uninstall":
        if args.name == "pandoc":
            uninstall_pandoc()
            print("Removed Pandoc from tools cache (if present).")
            return 0
        if args.name == "epubcheck":
            uninstall_epubcheck()
            print("Removed EPUBCheck from tools cache (if present).")
            return 0
        if args.name == "all":
            uninstall_all_tools()
            print("Removed all managed tools from tools cache (if present).")
            return 0

    elif args.tool_cmd == "doctor":
        from ..tools import tools_doctor

        return tools_doctor()

    elif args.tool_cmd == "bundle":
        from pathlib import Path

        from ..tools import get_offline_bundle_dir, setup_offline_bundle

        bundle_dir = Path(args.output) if args.output else get_offline_bundle_dir()
        try:
            setup_offline_bundle(bundle_dir)
            return 0
        except Exception as e:
            print(f"Error creating offline bundle: {e}")
            return 1

    return 1


def run_validate(args: argparse.Namespace) -> int:
    """Run EPUB validation using EPUBCheck and custom rules."""
    from ..validation import print_validation_report, validate_epub

    epub_path = Path(args.epub_path)
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_path}", file=sys.stderr)
        return 1

    if not epub_path.suffix.lower() == ".epub":
        print(f"Error: File must be an EPUB (.epub extension): {epub_path}", file=sys.stderr)
        return 1

    print(f"[VALIDATION] Validating EPUB: {epub_path}")
    print("=" * 50)

    try:
        # Run validation
        custom_checks = not args.skip_custom
        validation_result = validate_epub(
            epub_path, custom_checks=custom_checks, timeout=args.timeout
        )

        # Override EPUBCheck if skipped
        if args.skip_epubcheck:
            validation_result.epubcheck_available = False

        # Print detailed report
        print_validation_report(validation_result, verbose=args.verbose)

        # Return appropriate exit code
        if validation_result.has_errors:
            return 1  # Validation failed with errors
        else:
            return 0  # Validation passed

    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        return 1


def run_update(args: argparse.Namespace) -> int:
    """Update docx2shelf to the latest version."""
    try:
        from ..update import perform_update

        result = perform_update()

        if result:
            return 0
        else:
            return 1

    except ImportError:
        print("Update functionality not available.")
        print("Please download the latest installer from:")
        print("  https://github.com/LightWraith8268/Docx2Shelf/releases/latest")
        return 1
    except Exception as e:
        print(f"Update failed: {e}")
        return 1
