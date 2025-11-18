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
    run_doctor,
    run_enterprise,
    run_plugins,
    run_quality_assessment,
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


def run_theme_editor(args: argparse.Namespace) -> int:
    """Run the interactive theme editor."""
    from .theme_editor import ThemeEditor

    # Parse arguments
    base_theme = args.base_theme or "serif"
    themes_dir = None
    if args.themes_dir:
        themes_dir = Path(args.themes_dir)

    try:
        editor = ThemeEditor(themes_dir=themes_dir)
        return editor.start_editor(base_theme)
    except KeyboardInterrupt:
        print("\n\nTheme editor cancelled by user.")
        return 1
    except Exception as e:
        print(f"Theme editor error: {e}")
        return 1


def run_list_themes(args: argparse.Namespace) -> int:
    """List available CSS themes."""
    try:
        from .themes import get_theme_info, get_themes_by_genre, list_all_themes

        if args.genre:
            themes = get_themes_by_genre(args.genre)
            if not themes:
                print(f"No themes found for genre: {args.genre}")
                return 1

            print(f"Themes for {args.genre}:")
            for theme in themes:
                print(f"  {get_theme_info(theme)}")
        else:
            print(list_all_themes())

        return 0
    except ImportError:
        print("Theme discovery not available. Available themes: serif, sans, printlike")
        return 1


def run_preview_themes(args: argparse.Namespace) -> int:
    """Generate and display theme previews in browser."""
    import webbrowser
    from pathlib import Path

    try:
        from .path_utils import get_safe_temp_path, write_text_safe
        from .themes import get_all_theme_names, get_theme_css_content
    except ImportError:
        print("Theme preview functionality not available")
        return 1

    # Get list of themes to preview
    if args.themes:
        themes_to_preview = args.themes
    else:
        themes_to_preview = get_all_theme_names()

    if not themes_to_preview:
        print("No themes found to preview")
        return 1

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = get_safe_temp_path("theme_preview")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load sample text
    if args.sample_text:
        try:
            sample_text = Path(args.sample_text).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading sample text file: {e}")
            sample_text = get_default_sample_text()
    else:
        sample_text = get_default_sample_text()

    # Generate preview files
    preview_files = []
    print(f"Generating theme previews in: {output_dir}")

    for theme_name in themes_to_preview:
        try:
            # Get theme CSS
            theme_css = get_theme_css_content(theme_name)

            # Generate preview HTML
            preview_html = generate_theme_preview_html(theme_name, theme_css, sample_text)

            # Write preview file
            preview_file = output_dir / f"{theme_name}_preview.html"
            write_text_safe(preview_file, preview_html)
            preview_files.append(preview_file)

            print(f"  [OK] Generated preview for {theme_name}")

        except Exception as e:
            print(f"  [ERROR] Error generating preview for {theme_name}: {e}")

    if not preview_files:
        print("No preview files were generated")
        return 1

    # Generate index file
    index_html = generate_theme_index_html(preview_files, themes_to_preview)
    index_file = output_dir / "index.html"
    write_text_safe(index_file, index_html)

    print("\n[THEMES] Theme previews generated!")
    print(f"Location: {output_dir}")
    print(f"Index file: {index_file}")

    # Open in browser if requested
    if not args.no_browser:
        try:
            webbrowser.open(f"file://{index_file.resolve()}")
            print("🚀 Opening preview in browser...")
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"Manually open: file://{index_file.resolve()}")

    return 0


def get_default_sample_text() -> str:
    """Get default sample text for theme preview."""
    return """
    <h1>Chapter 1: The Beginning</h1>
    <p>This is a sample paragraph to demonstrate how text appears in this theme.
    The quick brown fox jumps over the lazy dog, showcasing various letters and spacing.</p>

    <h2>Section Title</h2>
    <p><em>Italic text</em> and <strong>bold text</strong> are used for emphasis.
    This helps you see how different text formatting appears with the theme.</p>

    <h3>Subsection</h3>
    <p>Quotations appear like this: "The only way to do great work is to love what you do."
    This demonstrates how quoted text is styled in the theme.</p>

    <blockquote>
    <p>This is a blockquote element that shows how longer quoted passages are formatted.
    It typically has different styling from regular paragraphs.</p>
    </blockquote>

    <p>Lists are formatted as follows:</p>
    <ul>
        <li>First item in an unordered list</li>
        <li>Second item with <strong>bold text</strong></li>
        <li>Third item with <em>italic text</em></li>
    </ul>

    <ol>
        <li>First item in an ordered list</li>
        <li>Second numbered item</li>
        <li>Third numbered item</li>
    </ol>
    """


def generate_theme_preview_html(theme_name: str, theme_css: str, sample_text: str) -> str:
    """Generate HTML preview for a theme."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theme Preview: {theme_name.title()}</title>
    <style>
        /* Theme CSS */
        {theme_css}

        /* Preview-specific styles */
        body {{
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}

        .preview-container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .preview-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}

        .theme-name {{
            font-size: 1.5em;
            color: #666;
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="preview-header">
            <h1 class="theme-name">Theme: {theme_name.title()}</h1>
        </div>
        {sample_text}
    </div>
</body>
</html>"""


def generate_theme_index_html(preview_files: list, theme_names: list) -> str:
    """Generate index HTML with links to all theme previews."""
    theme_links = []
    for i, theme_name in enumerate(theme_names):
        if i < len(preview_files):
            filename = preview_files[i].name
            theme_links.append(f'<li><a href="{filename}">{theme_name.title()}</a></li>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docx2Shelf Theme Previews</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}

        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}

        .theme-list {{
            list-style: none;
            padding: 0;
        }}

        .theme-list li {{
            margin: 10px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            transition: background-color 0.2s;
        }}

        .theme-list li:hover {{
            background: #e9ecef;
        }}

        .theme-list a {{
            text-decoration: none;
            color: #3498db;
            font-weight: 500;
            font-size: 1.1em;
        }}

        .theme-list a:hover {{
            color: #2980b9;
        }}

        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Docx2Shelf Theme Previews</h1>
        <p>Click on any theme name below to see how it will style your EPUB content:</p>

        <ul class="theme-list">
            {''.join(theme_links)}
        </ul>

        <div class="footer">
            <p>Generated by Docx2Shelf Theme Previewer</p>
        </div>
    </div>
</body>
</html>"""


def run_init_metadata(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file() or input_path.suffix.lower() not in {
        ".docx",
        ".md",
        ".txt",
        ".html",
        ".htm",
    }:
        print(f"Error: Input file not found or not a supported type: {input_path}", file=sys.stderr)
        return 2
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.parent / "metadata.txt"
    )
    if out_path.exists() and not args.force:
        print(
            f"Refusing to overwrite existing file: {out_path}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 2

    title_guess = input_path.stem.replace("_", " ").replace("-", " ").strip().title()
    from .metadata import build_output_filename

    output_guess = build_output_filename(title_guess, None, None)

    lines = [
        "# Docx2Shelf metadata template",
        "# Lines starting with # are ignored. Keys are case-insensitive.",
        "# Use key: value or key=value. Paths can be relative to this DOCX folder.",
        "# Output naming (optional): you can pass --output-pattern on the CLI",
        '# Example: --output-pattern "{series}-{index2}-{title}"',
        "",
        f"Title: {title_guess}",
        "Author:",
        "Language: en",
        "",
        "# Basic metadata",
        "SeriesName:",
        "SeriesIndex:",
        "Title-Sort:",
        "Author-Sort:",
        "Description:",
        "ISBN:",
        "Publisher:",
        "PubDate: 2024-01-01",
        "UUID:",
        "Subjects: ",
        "Keywords: ",
        "",
        "# Extended metadata (roles, classifications, etc.)",
        "Editor:",
        "Illustrator:",
        "Translator:",
        "Narrator:",
        "Designer:",
        "Contributor:",
        "BISAC-Codes: ",
        "Age-Range:",
        "Reading-Level:",
        "Copyright-Holder:",
        "Copyright-Year:",
        "Rights:",
        "Price:",
        "Currency:",
        "Print-ISBN:",
        "Audiobook-ISBN:",
        "Series-Type:",
        "Series-Position:",
        "Publication-Type:",
        "Target-Audience:",
        "Content-Warnings: ",
        "",
        "# Assets",
        f"Cover: {args.cover or ''}",
        "CSS:",
        "Embed-Fonts:",
        "",
        "# Conversion & layout",
        "Theme: serif",
        "Split-At: h1",
        "ToC_Depth: 2",
        "Chapter-Start-Mode: auto",
        "Chapter-Starts:",
        "Hyphenate: on",
        "Justify: on",
        "Page-List: off",
        "Page-Numbers: off",
        "Cover-Scale: contain",
        "",
        "# Output & validation",
        f"Output: {output_guess}",
        "EPUBCheck: on",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote template: {out_path}")
    return 0


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







def run_convert(args) -> int:
    """Handle EPUB format conversion."""
    from pathlib import Path

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    if not input_path.suffix.lower() == ".epub":
        print(f"Error: Input file must be an EPUB file, got: {input_path.suffix}")
        return 1

    # Check format dependencies if requested
    if args.check_deps:
        print(f"Checking dependencies for {args.format} format...")
        deps = check_format_dependencies(args.format)

        if not deps:
            print(f"No external dependencies required for {args.format}")
            return 0

        print("Dependencies:")
        for dep, available in deps.items():
            status = "✓ Available" if available else "✗ Not found"
            print(f"  {dep}: {status}")

        # Check if any required dependencies are missing
        if args.format == "pdf" and not any(deps.values()):
            print("\nError: PDF conversion requires either weasyprint or prince")
            print("Install with: pip install weasyprint")
            return 1
        elif args.format in ["mobi", "azw3"] and not deps.get("calibre"):
            print(f"\nError: {args.format.upper()} conversion requires Calibre")
            print("Install from: https://calibre-ebook.com/download")
            return 1

        return 0

    # Generate output path if not specified
    if args.output:
        output_path = Path(args.output)
    else:
        # Auto-generate based on format
        if args.format == "web":
            output_path = input_path.parent / f"{input_path.stem}_web"
        else:
            ext_map = {
                "pdf": ".pdf",
                "mobi": ".mobi",
                "azw3": ".azw3",
                "txt": ".txt",
                "text": ".txt",
            }
            ext = ext_map.get(args.format, f".{args.format}")
            output_path = input_path.parent / f"{input_path.stem}{ext}"

    # Read custom CSS if provided
    custom_css = None
    if args.css:
        css_path = Path(args.css)
        if css_path.exists():
            custom_css = css_path.read_text(encoding="utf-8")
        else:
            print(f"Warning: CSS file not found: {css_path}")

    # Extract metadata from args for conversion
    metadata = {
        "title": getattr(args, "title", None),
        "author": getattr(args, "author", None),
    }

    print(f"Converting {input_path} to {args.format.upper()}...")
    print(f"Output: {output_path}")

    # Perform conversion
    success = convert_epub(
        epub_path=input_path,
        format_type=args.format,
        output_path=output_path,
        quality=args.quality,
        compression=args.compression,
        metadata=metadata,
        custom_css=custom_css,
        page_size=args.page_size,
        margin=args.margin,
        font_size=getattr(args, "font_size", "12pt"),
        font_family=args.font_family,
        include_toc=args.include_toc,
        include_cover=args.include_cover,
    )

    if success:
        print("✓ Conversion completed successfully!")
        if args.format == "web":
            print(f"Open {output_path / 'index.html'} in your browser to view")
        return 0
    else:
        print("✗ Conversion failed")
        return 1




if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
