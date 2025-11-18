from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .accessibility_audit import audit_epub_accessibility
from .ai_accessibility import generate_image_alt_texts
from .ai_genre_detection import detect_genre_with_ai
from .ai_integration import AIConfig, get_ai_manager
from .ai_metadata import enhance_metadata_with_ai
from .content_validation import validate_content_quality
from .error_handler import handle_error
from .formats import check_format_dependencies, convert_epub
from .metadata import BuildOptions, EpubMetadata, build_output_filename, parse_date
from .path_utils import ensure_unicode_path, is_safe_path, normalize_path, safe_filename
from .preview import run_live_preview
from .publishing_checklists import format_checklist_report, get_checker, run_all_checklists
from .quality_scoring import analyze_epub_quality
from .tools import (
    epubcheck_cmd,
    install_epubcheck,
    install_pandoc,
    pandoc_path,
    tools_dir,
    uninstall_all_tools,
    uninstall_epubcheck,
    uninstall_pandoc,
)
from .update import check_for_updates
from .utils import (
    parse_kv_file,
    prompt,
    prompt_bool,
    prompt_select,
    sanitize_filename,
)
from .version import get_version_info


def get_version_string() -> str:
    """Get formatted version string for CLI."""
    info = get_version_info()
    return f"docx2shelf {info['version']} - {info['description']}"


# Import modular argument parser
from .cli_args import _arg_parser

# Import modular command handlers
from .cli_handlers import (
    _prompt_missing,
    read_document_content,
    run_ai_command,
    run_build,
    run_checklist,
    run_connectors,
    run_convert,
    run_doctor,
    run_enterprise,
    run_init_metadata,
    run_list_themes,
    run_plugins,
    run_preview_themes,
    run_quality_assessment,
    run_theme_editor,
    save_metadata_to_file,
)

def run_list_profiles(args: argparse.Namespace) -> int:
    """List available publishing profiles."""
    try:
        from .profiles import get_profile_summary, list_all_profiles

        if args.profile:
            # Show detailed info for specific profile
            summary = get_profile_summary(args.profile)
            print(summary)
        else:
            # Show all profiles
            print(list_all_profiles())

        return 0
    except ImportError:
        print("Profile system not available.")
        return 1


def run_batch_mode(args: argparse.Namespace) -> int:
    """Run batch processing mode."""
    try:
        from .batch import create_batch_report, run_batch_mode, validate_batch_args

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
    from .wizard import run_wizard_mode

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






def run_tools(args: argparse.Namespace) -> int:
    if args.tool_cmd == "install":
        # Use version preset if no specific version provided
        version = args.version
        if not version and hasattr(args, "preset"):
            from .tools import get_pinned_version

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
        from .tools import tools_doctor

        return tools_doctor()

    elif args.tool_cmd == "bundle":
        from pathlib import Path

        from .tools import get_offline_bundle_dir, setup_offline_bundle

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
    from .validation import print_validation_report, validate_epub

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




def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Perform a quick update check in a background thread if not running update command
    if not (argv and "update" in argv[0]):
        import threading

        update_thread = threading.Thread(target=check_for_updates)
        update_thread.start()

    if not argv:
        # Launch interactive CLI when no args are provided
        from .interactive_cli import run_interactive_cli

        run_interactive_cli()
        return 0
    parser = _arg_parser()
    args = parser.parse_args(argv)

    if args.command == "build":
        args = _prompt_missing(args)
        return run_build(args)
    if args.command == "init-metadata":
        return run_init_metadata(args)
    if args.command == "wizard":
        return run_wizard(args)
    if args.command == "theme-editor":
        return run_theme_editor(args)
    if args.command == "list-themes":
        return run_list_themes(args)
    if args.command == "preview-themes":
        return run_preview_themes(args)
    if args.command == "list-profiles":
        return run_list_profiles(args)
    if args.command == "batch":
        return run_batch_mode(args)
    if args.command == "tools":
        return run_tools(args)
    if args.command == "plugins":
        return run_plugins(args)
    if args.command == "connectors":
        return run_connectors(args)
    if args.command == "ai":
        return run_ai_command(args)
    if args.command == "update":
        return run_update(args)
    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "interactive":
        from .interactive_cli import run_interactive_cli

        run_interactive_cli()
        return 0
    if args.command == "gui":
        from .gui.modern_app import main as run_modern_gui

        return run_modern_gui()
    if args.command == "checklist":
        return run_checklist(args)
    if args.command == "quality":
        return run_quality_assessment(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "convert":
        return run_convert(args)
    if args.command == "enterprise":
        return run_enterprise(args)

    parser.print_help()
    return 1


def run_update(args: argparse.Namespace) -> int:
    """Update docx2shelf to the latest version."""
    try:
        from .update import perform_update

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











if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
