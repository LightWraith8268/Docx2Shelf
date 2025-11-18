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
    run_batch_mode,
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
    run_tools,
    run_update,
    run_validate,
    run_wizard,
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













if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
