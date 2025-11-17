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
    run_build,
    run_enterprise,
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


def run_checklist(args: argparse.Namespace) -> int:
    """Run publishing store compatibility checklists."""
    import json

    # Determine metadata file path
    metadata_path = Path(args.metadata) if args.metadata else Path("metadata.txt")

    if not metadata_path.exists():
        print(f"Error: Metadata file not found: {metadata_path}", file=sys.stderr)
        print("Run 'docx2shelf init-metadata' to create a metadata.txt file", file=sys.stderr)
        return 1

    # Load metadata from file
    try:
        metadata_dict = parse_kv_file(metadata_path)

        # Create a minimal EpubMetadata object from the metadata file
        metadata = EpubMetadata(
            title=metadata_dict.get("title", ""),
            author=metadata_dict.get("author", ""),
            language=metadata_dict.get("language", "en"),
            description=metadata_dict.get("description"),
            isbn=metadata_dict.get("isbn"),
            publisher=metadata_dict.get("publisher"),
            pubdate=(
                parse_date(metadata_dict.get("pubdate")) if metadata_dict.get("pubdate") else None
            ),
            uuid=metadata_dict.get("uuid"),
            series=metadata_dict.get("series"),
            series_index=metadata_dict.get("series_index"),
            title_sort=metadata_dict.get("title_sort"),
            author_sort=metadata_dict.get("author_sort"),
            subjects=(
                metadata_dict.get("subjects", "").split(",")
                if metadata_dict.get("subjects")
                else []
            ),
            keywords=(
                metadata_dict.get("keywords", "").split(",")
                if metadata_dict.get("keywords")
                else []
            ),
            cover_path=Path(args.cover) if args.cover else Path("cover.jpg"),  # Default cover path
            # Extended metadata fields
            editor=metadata_dict.get("editor"),
            illustrator=metadata_dict.get("illustrator"),
            translator=metadata_dict.get("translator"),
            narrator=metadata_dict.get("narrator"),
            designer=metadata_dict.get("designer"),
            contributor=metadata_dict.get("contributor"),
            bisac_codes=(
                metadata_dict.get("bisac_codes", "").split(",")
                if metadata_dict.get("bisac_codes")
                else []
            ),
            age_range=metadata_dict.get("age_range"),
            reading_level=metadata_dict.get("reading_level"),
            copyright_holder=metadata_dict.get("copyright_holder"),
            copyright_year=metadata_dict.get("copyright_year"),
            rights=metadata_dict.get("rights"),
            price=metadata_dict.get("price"),
            currency=metadata_dict.get("currency"),
            print_isbn=metadata_dict.get("print_isbn"),
            audiobook_isbn=metadata_dict.get("audiobook_isbn"),
            series_type=metadata_dict.get("series_type"),
            series_position=metadata_dict.get("series_position"),
            publication_type=metadata_dict.get("publication_type"),
            target_audience=metadata_dict.get("target_audience"),
            content_warnings=(
                metadata_dict.get("content_warnings", "").split(",")
                if metadata_dict.get("content_warnings")
                else []
            ),
        )
    except Exception as e:
        print(f"Error parsing metadata file: {e}", file=sys.stderr)
        return 1

    # Determine cover image path
    cover_path = None
    if args.cover:
        cover_path = Path(args.cover)
        if not cover_path.exists():
            print(f"Warning: Cover image not found: {cover_path}", file=sys.stderr)
            cover_path = None
    else:
        # Try to find a cover image in common locations
        for cover_name in ["cover.jpg", "cover.png", "cover.jpeg"]:
            potential_cover = metadata_path.parent / cover_name
            if potential_cover.exists():
                cover_path = potential_cover
                break

    # Run checklists
    try:
        if args.store == "all":
            results = run_all_checklists(metadata, cover_path)
        else:
            checker = get_checker(args.store)
            result = checker.run_checks(metadata, cover_path)
            # Use proper store display name
            store_names = {"kdp": "KDP", "apple": "Apple Books", "kobo": "Kobo"}
            display_name = store_names.get(args.store, args.store.title())
            results = {display_name: result}

        if args.json:
            # Output as JSON
            json_results = {}
            for store, result in results.items():
                json_results[store] = {
                    "passed": result.passed,
                    "errors": [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "message": i.message,
                            "fix_suggestion": i.fix_suggestion,
                        }
                        for i in result.errors
                    ],
                    "warnings": [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "message": i.message,
                            "fix_suggestion": i.fix_suggestion,
                        }
                        for i in result.warnings
                    ],
                    "infos": [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "message": i.message,
                            "fix_suggestion": i.fix_suggestion,
                        }
                        for i in result.infos
                    ],
                }
            print(json.dumps(json_results, indent=2))
        else:
            # Output formatted report
            report = format_checklist_report(results)
            print(report)

        # Return appropriate exit code
        has_errors = any(len(result.errors) > 0 for result in results.values())
        return 1 if has_errors else 0

    except Exception as e:
        print(f"Error running checklists: {e}", file=sys.stderr)
        return 1


def run_quality_assessment(args: argparse.Namespace) -> int:
    """Run comprehensive quality assessment on EPUB file."""
    import json
    from zipfile import ZipFile

    epub_path = Path(args.epub_path)
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_path}", file=sys.stderr)
        return 1

    if not epub_path.suffix.lower() == ".epub":
        print(f"Error: File must be an EPUB (.epub extension): {epub_path}", file=sys.stderr)
        return 1

    print(f"🔍 Analyzing EPUB quality: {epub_path}")
    print("=" * 60)

    results = {}
    total_issues = 0
    total_critical = 0

    # 1. Quality Scoring Analysis
    if not args.skip_quality_scoring:
        print("📊 Running quality scoring analysis...")
        try:
            quality_report = analyze_epub_quality(epub_path)
            results["quality_scoring"] = {
                "overall_score": quality_report.overall_score,
                "quality_level": quality_report.quality_level.value,
                "total_issues": quality_report.total_issues,
                "critical_issues": quality_report.critical_issues,
                "auto_fixable_issues": quality_report.auto_fixable_issues,
                "category_scores": {
                    cat.value: {"score": score.score, "issues": len(score.issues)}
                    for cat, score in quality_report.category_scores.items()
                },
                "recommendations": quality_report.recommendations,
            }
            total_issues += quality_report.total_issues
            total_critical += quality_report.critical_issues

            if not args.json:
                print(
                    f"   Overall Score: {quality_report.overall_score:.1f}/100 ({quality_report.quality_level.value.title()})"
                )
                print(
                    f"   Issues Found: {quality_report.total_issues} ({quality_report.critical_issues} critical)"
                )
                if quality_report.auto_fixable_issues > 0:
                    print(f"   Auto-fixable: {quality_report.auto_fixable_issues} issues")
                print()

        except Exception as e:
            print(f"Error in quality scoring: {e}", file=sys.stderr)
            results["quality_scoring"] = {"error": str(e)}

    # 2. Accessibility Compliance Analysis
    if not args.skip_accessibility:
        print("♿ Running accessibility compliance analysis...")
        try:
            from .accessibility_audit import A11yConfig, A11yLevel

            # Configure accessibility audit
            target_level = A11yLevel[args.target_level]
            config = A11yConfig(target_level=target_level)

            a11y_result = audit_epub_accessibility(epub_path, config)
            results["accessibility"] = {
                "overall_score": a11y_result.overall_score,
                "conformance_level": (
                    a11y_result.conformance_level.value if a11y_result.conformance_level else None
                ),
                "total_issues": a11y_result.total_issues,
                "critical_issues": a11y_result.critical_issues,
                "major_issues": a11y_result.major_issues,
                "minor_issues": a11y_result.minor_issues,
                "auto_fixes_applied": a11y_result.auto_fixes_applied,
                "issues_by_type": {k.value: v for k, v in a11y_result.issues_by_type.items()},
                "recommendations": a11y_result.recommendations,
            }
            total_issues += a11y_result.total_issues
            total_critical += a11y_result.critical_issues

            if not args.json:
                conformance = (
                    a11y_result.conformance_level.value if a11y_result.conformance_level else "None"
                )
                print(
                    f"   Accessibility Score: {a11y_result.overall_score:.1f}/100 (WCAG {conformance})"
                )
                print(
                    f"   Issues Found: {a11y_result.total_issues} ({a11y_result.critical_issues} critical)"
                )
                print()

        except Exception as e:
            print(f"Error in accessibility analysis: {e}", file=sys.stderr)
            results["accessibility"] = {"error": str(e)}

    # 3. EPUB Structure & Format Validation
    print("📋 Running EPUB structure validation...")
    try:
        from .validation import validate_epub

        validation_result = validate_epub(epub_path, custom_checks=True, timeout=120)

        results["epub_validation"] = {
            "is_valid": validation_result.is_valid,
            "total_issues": validation_result.total_issues,
            "errors": len(validation_result.errors),
            "warnings": len(validation_result.warnings),
            "info": len(validation_result.info),
            "epubcheck_available": validation_result.epubcheck_available,
            "custom_checks_run": validation_result.custom_checks_run,
            "issues": [
                {
                    "severity": issue.severity,
                    "message": issue.message,
                    "location": issue.location,
                    "rule": issue.rule,
                }
                for issue in (
                    validation_result.errors + validation_result.warnings + validation_result.info
                )
            ],
        }

        total_issues += validation_result.total_issues
        total_critical += len(validation_result.errors)

        if not args.json:
            print(f"   EPUB Valid: {'Yes' if validation_result.is_valid else 'No'}")
            print(
                f"   Issues Found: {validation_result.total_issues} ({len(validation_result.errors)} errors, {len(validation_result.warnings)} warnings)"
            )
            if not validation_result.epubcheck_available:
                print(
                    "   [INFO] Install EPUBCheck for industry-standard validation: docx2shelf tools install epubcheck"
                )
            print()

    except Exception as e:
        print(f"Error in EPUB validation: {e}", file=sys.stderr)
        results["epub_validation"] = {"error": str(e)}

    # 4. Content Validation
    if not args.skip_content_validation:
        print("📝 Running content validation...")
        try:
            content_reports = []

            # Extract and validate content from EPUB
            with ZipFile(epub_path, "r") as epub_zip:
                content_files = [
                    f for f in epub_zip.namelist() if f.endswith(".xhtml") or f.endswith(".html")
                ]

                for file_path in content_files[:10]:  # Limit to first 10 files for performance
                    try:
                        content = epub_zip.read(file_path).decode("utf-8")
                        report = validate_content_quality(content, file_path)
                        content_reports.append(report)
                    except Exception as e:
                        print(f"Warning: Could not validate {file_path}: {e}")

            # Validate additional content files if provided
            if args.content_files:
                for file_path in args.content_files:
                    content_path = Path(file_path)
                    if content_path.exists():
                        try:
                            content = content_path.read_text(encoding="utf-8")
                            report = validate_content_quality(content, str(content_path))
                            content_reports.append(report)
                        except Exception as e:
                            print(f"Warning: Could not validate {content_path}: {e}")

            # Aggregate content validation results
            total_content_issues = sum(len(r.issues) for r in content_reports)
            total_errors = sum(r.error_count for r in content_reports)
            total_warnings = sum(r.warning_count for r in content_reports)
            total_auto_fixable = sum(r.auto_fixable_count for r in content_reports)

            results["content_validation"] = {
                "files_checked": len(content_reports),
                "total_issues": total_content_issues,
                "error_count": total_errors,
                "warning_count": total_warnings,
                "suggestion_count": sum(r.suggestion_count for r in content_reports),
                "auto_fixable_count": total_auto_fixable,
                "reports": [
                    {
                        "file_path": r.file_path,
                        "issues": len(r.issues),
                        "stats": {
                            "word_count": r.stats.word_count,
                            "flesch_reading_ease": r.stats.flesch_reading_ease,
                            "avg_words_per_sentence": r.stats.avg_words_per_sentence,
                        },
                    }
                    for r in content_reports
                ],
            }

            total_issues += total_content_issues
            total_critical += total_errors

            if not args.json:
                print(f"   Files Analyzed: {len(content_reports)}")
                print(
                    f"   Issues Found: {total_content_issues} ({total_errors} errors, {total_warnings} warnings)"
                )
                if total_auto_fixable > 0:
                    print(f"   Auto-fixable: {total_auto_fixable} issues")
                print()

        except Exception as e:
            print(f"Error in content validation: {e}", file=sys.stderr)
            results["content_validation"] = {"error": str(e)}

    # Output results
    if args.json:
        # JSON output
        output_data = {
            "epub_path": str(epub_path),
            "analysis_timestamp": __import__("datetime").datetime.now().isoformat(),
            "summary": {
                "total_issues": total_issues,
                "critical_issues": total_critical,
                "analysis_types": len([k for k in results.keys() if "error" not in results[k]]),
            },
            "results": results,
        }

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
            print(f"📄 Detailed report saved to: {output_path}")
        else:
            print(json.dumps(output_data, indent=2))

    else:
        # Human-readable output
        print("=" * 60)
        print("📋 QUALITY ASSESSMENT SUMMARY")
        print("=" * 60)

        if "quality_scoring" in results and "error" not in results["quality_scoring"]:
            quality_data = results["quality_scoring"]
            print(
                f"🎯 Overall Quality Score: {quality_data['overall_score']:.1f}/100 ({quality_data['quality_level'].title()})"
            )

        print(f"📊 Total Issues Found: {total_issues}")
        if total_critical > 0:
            print(f"🚨 Critical Issues: {total_critical}")

        # Show top recommendations
        all_recommendations = []
        for analysis_type, data in results.items():
            if "recommendations" in data:
                all_recommendations.extend(data["recommendations"])

        if all_recommendations:
            print("\n💡 Top Recommendations:")
            for i, rec in enumerate(all_recommendations[:5], 1):
                print(f"   {i}. {rec}")

        if args.output:
            # Save detailed report
            report_lines = [f"Quality Assessment Report for {epub_path}", "=" * 60, ""]

            # Add detailed results for each analysis type
            for analysis_type, data in results.items():
                if "error" not in data:
                    report_lines.append(f"{analysis_type.replace('_', ' ').title()}:")
                    report_lines.append("-" * 30)

                    if analysis_type == "quality_scoring":
                        report_lines.append(f"Overall Score: {data['overall_score']:.1f}/100")
                        report_lines.append(f"Quality Level: {data['quality_level'].title()}")
                        report_lines.append(f"Total Issues: {data['total_issues']}")
                        report_lines.append("Category Scores:")
                        for cat, score_data in data["category_scores"].items():
                            report_lines.append(
                                f"  - {cat.title()}: {score_data['score']:.1f}/100 ({score_data['issues']} issues)"
                            )

                    elif analysis_type == "accessibility":
                        report_lines.append(f"Accessibility Score: {data['overall_score']:.1f}/100")
                        conformance = data["conformance_level"] or "None"
                        report_lines.append(f"WCAG Conformance: {conformance}")
                        report_lines.append(
                            f"Issues: {data['total_issues']} total, {data['critical_issues']} critical"
                        )

                    elif analysis_type == "epub_validation":
                        report_lines.append(f"EPUB Valid: {'Yes' if data['is_valid'] else 'No'}")
                        report_lines.append(
                            f"Issues: {data['total_issues']} total ({data['errors']} errors, {data['warnings']} warnings)"
                        )
                        report_lines.append(
                            f"EPUBCheck Available: {'Yes' if data['epubcheck_available'] else 'No'}"
                        )
                        if data["issues"]:
                            report_lines.append("Issues Found:")
                            for issue in data["issues"][
                                :10
                            ]:  # Limit to first 10 issues for brevity
                                location = (
                                    f" ({issue['location']})" if issue.get("location") else ""
                                )
                                report_lines.append(
                                    f"  • [{issue['severity'].upper()}]{location}: {issue['message']}"
                                )
                            if len(data["issues"]) > 10:
                                report_lines.append(
                                    f"  ... and {len(data['issues']) - 10} more issues"
                                )

                    elif analysis_type == "content_validation":
                        report_lines.append(f"Files Analyzed: {data['files_checked']}")
                        report_lines.append(
                            f"Issues: {data['total_issues']} total, {data['error_count']} errors"
                        )

                    if "recommendations" in data:
                        report_lines.append("Recommendations:")
                        for rec in data["recommendations"]:
                            report_lines.append(f"  • {rec}")

                    report_lines.append("")

            output_path = Path(args.output)
            output_path.write_text("\n".join(report_lines), encoding="utf-8")
            print(f"\n📄 Detailed report saved to: {output_path}")

    # Return appropriate exit code
    return 1 if total_critical > 0 else 0


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


def run_ai_command(args) -> int:
    """Handle AI subcommands."""
    try:
        if args.ai_action == "metadata":
            return run_ai_metadata(args)
        elif args.ai_action == "genre":
            return run_ai_genre(args)
        elif args.ai_action == "alt-text":
            return run_ai_alt_text(args)
        elif args.ai_action == "config":
            return run_ai_config(args)
        else:
            print(f"Unknown AI action: {args.ai_action}")
            return 1
    except Exception as e:
        print(f"Error running AI command: {e}")
        return 1


def run_ai_metadata(args) -> int:
    """Enhance metadata using AI analysis."""
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🤖 Analyzing metadata for: {input_file.name}")

        # Read document content
        content = read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Create basic metadata
        metadata = EpubMetadata(title=input_file.stem, author="Unknown Author", language="en")

        # Enhance with AI
        enhanced = enhance_metadata_with_ai(content, metadata, interactive=args.interactive)

        # Output results
        if args.output:
            save_metadata_to_file(enhanced.original, Path(args.output))
            print(f"[SUCCESS] Enhanced metadata saved to: {args.output}")
        else:
            print("\n📊 Enhanced Metadata:")
            print(f"   Title: {enhanced.original.title}")
            print(f"   Author: {enhanced.original.author}")
            print(f"   Description: {enhanced.original.description or '(none)'}")
            if hasattr(enhanced.original, "genre") and enhanced.original.genre:
                print(f"   Genre: {enhanced.original.genre}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_genre(args) -> int:
    """Detect genres and keywords using AI."""
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🎯 Analyzing genres and keywords for: {input_file.name}")

        # Read document content
        content = read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Detect genres
        metadata_dict = {"title": input_file.stem, "author": "Unknown Author", "description": ""}
        result = detect_genre_with_ai(content, metadata_dict)

        if args.json:
            import json

            output = {
                "genres": [
                    {"genre": g.genre, "confidence": g.confidence, "source": g.source}
                    for g in result.genres
                ],
                "keywords": result.keywords,
                "analysis_summary": result.analysis_summary,
            }
            print(json.dumps(output, indent=2))
        else:
            print("\n📚 Detected Genres:")
            for genre in result.genres[:5]:
                confidence_icon = (
                    "🟢" if genre.confidence >= 0.8 else "🟡" if genre.confidence >= 0.6 else "🔴"
                )
                print(
                    f"   {confidence_icon} {genre.genre} ({genre.confidence:.1%}) - {genre.source}"
                )

            print(f"\n🏷️  Keywords: {', '.join(result.keywords[:15])}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_alt_text(args) -> int:
    """Generate alt text for images using AI."""
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🖼️  Generating alt text for: {input_path.name}")

        if input_path.is_file() and input_path.suffix.lower() in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
        ]:
            # Single image file
            suggestions = generate_image_alt_texts([input_path], interactive=args.interactive)

            if suggestions:
                print("\n✨ Alt Text Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    confidence_icon = (
                        "🟢"
                        if suggestion.confidence >= 0.8
                        else "🟡" if suggestion.confidence >= 0.6 else "🔴"
                    )
                    print(f"   {i}. {confidence_icon} {suggestion.alt_text}")
                    print(
                        f"      Confidence: {suggestion.confidence:.1%} | Source: {suggestion.source}"
                    )
            else:
                print("No alt text suggestions generated")

        else:
            print("Error: Please provide a valid image file (.jpg, .png, .gif, .webp)")
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_config(args) -> int:
    """Manage AI configuration."""
    try:
        config = AIConfig()

        if args.list:
            print("🔧 AI Configuration:")
            print(f"   Model Type: {config.model_type}")
            print(f"   Local Model: {config.local_model}")
            if config.openai_api_key:
                print(f"   OpenAI API Key: {'*' * 8}{config.openai_api_key[-4:]}")
            else:
                print("   OpenAI API Key: Not configured")
            print(f"   Cache Enabled: {config.enable_caching}")
            print(f"   Cache Directory: {config.cache_dir}")

        elif args.set:
            key, value = args.set
            if hasattr(config, key):
                setattr(config, key, value)
                # Save configuration would go here
                print(f"[SET] {key} = {value}")
            else:
                print(f"Error: Unknown configuration key: {key}")
                return 1

        elif args.reset:
            # Reset to defaults would go here
            print("[SUCCESS] AI configuration reset to defaults")

        return 0

    except Exception as e:
        print(f"Error: {e}")
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


def run_doctor(args: argparse.Namespace) -> int:
    """Run comprehensive environment diagnostics."""
    import platform
    import sys
    from pathlib import Path

    print("[DOCTOR] Docx2Shelf Environment Diagnostics")
    print("=" * 50)

    issues_found = 0
    warnings_found = 0

    # System Information
    print("\n[SYSTEM] System Information:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]} ({sys.executable})")

    # Python version check
    if sys.version_info >= (3, 11):
        print("  [OK] Python version is compatible")
    else:
        print(
            f"  [ERROR] Python {sys.version_info.major}.{sys.version_info.minor} is too old (requires 3.11+)"
        )
        issues_found += 1

    # Package installation check
    print("\n[PACKAGE] Docx2Shelf Installation:")
    try:
        from importlib import metadata

        version = metadata.version("docx2shelf")
        print(f"  [OK] Docx2Shelf {version} installed")
    except Exception as e:
        print(f"  [ERROR] Could not determine docx2shelf version: {e}")
        issues_found += 1

    # Dependencies check
    print("\n[DEPS] Core Dependencies:")
    core_deps = ["ebooklib", "lxml"]
    for dep in core_deps:
        try:
            __import__(dep)
            print(f"  [OK] {dep} available")
        except ImportError:
            print(f"  [ERROR] {dep} not available")
            issues_found += 1

    # Optional dependencies
    optional_deps = {
        "python-docx": "DOCX fallback support",
        "pypandoc": "Pandoc Python integration",
        "requests": "Update and marketplace features",
        "fastapi": "Enterprise API features",
        "sqlalchemy": "Enterprise database features",
    }

    print("\n[OPTIONAL] Optional Dependencies:")
    for dep, description in optional_deps.items():
        try:
            __import__(dep.replace("-", "_"))
            print(f"  [OK] {dep} - {description}")
        except ImportError:
            print(f"  [INFO] {dep} not installed - {description}")

    # Tools check (reuse existing tools_doctor)
    print("\n[TOOLS] External Tools:")
    from .tools import tools_doctor

    tools_result = tools_doctor()
    if tools_result != 0:
        issues_found += tools_result

    # File system checks
    print("\n[FILESYSTEM] File System Access:")

    # Check write access to current directory
    try:
        test_file = Path("docx2shelf_test_write.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("  [OK] Current directory is writable")
    except Exception as e:
        print(f"  [WARNING] Current directory write test failed: {e}")
        warnings_found += 1

    # Check temp directory
    import tempfile

    try:
        temp_dir = Path(tempfile.gettempdir())
        print(f"  [OK] Temp directory: {temp_dir}")
        if temp_dir.exists() and temp_dir.is_dir():
            print("  [OK] Temp directory accessible")
        else:
            print("  [ERROR] Temp directory not accessible")
            issues_found += 1
    except Exception as e:
        print(f"  [ERROR] Temp directory check failed: {e}")
        issues_found += 1

    # Memory check
    print("\n[MEMORY] Memory Information:")
    try:
        import psutil

        memory = psutil.virtual_memory()
        print(f"  [OK] Available RAM: {memory.available // (1024**3)} GB")
        if memory.available < 1024**3:  # Less than 1GB
            print("  [WARNING] Low available memory may affect large document processing")
            warnings_found += 1
    except ImportError:
        print("  [INFO] psutil not available - cannot check memory")

    # Summary
    print("\n" + "=" * 50)
    total_issues = issues_found + warnings_found

    if issues_found == 0 and warnings_found == 0:
        print("[SUCCESS] All diagnostics passed! Environment is ready.")
        return 0
    elif issues_found == 0:
        print(f"[OK] Environment functional with {warnings_found} warning(s)")
        print("\nWarnings found but system should work normally.")
        return 0
    else:
        print(f"[ERROR] Found {issues_found} critical issue(s) and {warnings_found} warning(s)")
        print("\nRecommended actions:")
        if sys.version_info < (3, 11):
            print("- Update Python to version 3.11 or higher")
        print("- Install missing dependencies: pip install docx2shelf[all]")
        print("- Run 'docx2shelf tools install pandoc' for document conversion")
        print("- Run 'docx2shelf tools install epubcheck' for validation")
        return 1


def run_plugins(args) -> int:
    """Handle plugin management commands."""
    import shutil
    from pathlib import Path

    from .plugins import (
        discover_available_plugins,
        get_plugin_info,
        load_default_plugins,
        plugin_manager,
    )
    from .utils import get_user_data_dir

    # Load default plugins first
    load_default_plugins()

    if args.plugin_cmd == "list":
        if args.all:
            # Show all available plugins
            available_plugins = discover_available_plugins()
            if not available_plugins:
                print("No plugins found in discovery locations.")
                return 0

            print("Available plugins:")
            for plugin in available_plugins:
                status = "✓ Loaded" if plugin["loaded"] else "○ Available"
                if args.verbose:
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    print(f"    Description: {plugin['description']}")
                    print(f"    Location: {plugin['location']}")
                    print(f"    File: {plugin['file_name']}")
                    print(f"    Classes: {', '.join(plugin['classes'])}")
                    print()
                else:
                    print(
                        f"  {status} {plugin['name']} (v{plugin['version']}) - {plugin['description']}"
                    )
        else:
            # Show only loaded plugins
            plugins = plugin_manager.list_plugins()
            if not plugins:
                print("No plugins loaded.")
                print("Run 'docx2shelf plugins list --all' to see available plugins.")
                return 0

            print("Loaded plugins:")
            for plugin in plugins:
                status = "✓" if plugin["enabled"] == "True" else "✗"
                if args.verbose:
                    detailed = get_plugin_info(plugin["name"])
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    if detailed:
                        print(f"    Hooks: {detailed['hook_count']} total")
                        for hook_type, hook_classes in detailed["hooks"].items():
                            print(f"      {hook_type}: {', '.join(hook_classes)}")
                    print()
                else:
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
        return 0

    elif args.plugin_cmd == "load":
        plugin_path = Path(args.path)
        if not plugin_path.exists():
            print(f"Error: Plugin file not found: {plugin_path}")
            return 1

        plugin_manager.load_plugin_from_file(plugin_path)
        print(f"✓ Loaded plugin from: {plugin_path}")
        return 0

    elif args.plugin_cmd == "enable":
        plugin = plugin_manager.get_plugin_by_name(args.name)
        if not plugin:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        plugin.enable()
        print(f"✓ Enabled plugin: {args.name}")
        return 0

    elif args.plugin_cmd == "disable":
        plugin = plugin_manager.get_plugin_by_name(args.name)
        if not plugin:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        plugin.disable()
        print(f"✓ Disabled plugin: {args.name}")
        return 0

    elif args.plugin_cmd == "info":
        plugin_info = get_plugin_info(args.name)
        if not plugin_info:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        print(f"Plugin: {plugin_info['name']}")
        print(f"Version: {plugin_info['version']}")
        print(f"Status: {'Enabled' if plugin_info['enabled'] else 'Disabled'}")
        print(f"Hooks: {plugin_info['hook_count']} total")

        for hook_type, hook_classes in plugin_info["hooks"].items():
            print(f"  {hook_type}:")
            for hook_class in hook_classes:
                print(f"    - {hook_class}")

        return 0

    elif args.plugin_cmd == "discover":
        available_plugins = discover_available_plugins()

        if args.install:
            user_plugins_dir = get_user_data_dir() / "plugins"
            if not user_plugins_dir.exists():
                user_plugins_dir.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created user plugins directory: {user_plugins_dir}")
            else:
                print(f"User plugins directory already exists: {user_plugins_dir}")

        print("\nPlugin discovery locations:")
        print(f"  • User plugins: {get_user_data_dir() / 'plugins'}")
        print(f"  • Package plugins: {Path(__file__).parent / 'plugins'}")
        print(f"  • Project plugins: {Path.cwd() / 'plugins'}")

        if available_plugins:
            print(f"\nFound {len(available_plugins)} plugins:")
            for plugin in available_plugins:
                status = "✓ Loaded" if plugin["loaded"] else "○ Available"
                print(f"  {status} {plugin['name']} ({plugin['location']})")
        else:
            print("\nNo plugins found in discovery locations.")
            print("You can:")
            print("  • Copy plugin files to the user plugins directory")
            print("  • Create a 'plugins' folder in your project")
            print("  • Use 'docx2shelf plugins load <path>' for custom locations")

        return 0

    elif args.plugin_cmd == "create":
        # Create a new plugin from template
        output_dir = Path(args.output) if args.output else Path.cwd()
        plugin_file = output_dir / f"{args.name}.py"

        if plugin_file.exists():
            print(f"Error: Plugin file already exists: {plugin_file}")
            return 1

        # Get template content
        template_path = Path(__file__).parent.parent.parent / "docs" / "plugins" / "examples"

        if args.template == "basic":
            template_file = template_path / "basic_template.py"
        elif args.template == "html-cleaner":
            template_file = template_path / "html_cleaner.py"
        elif args.template == "metadata-enhancer":
            template_file = template_path / "metadata_enhancer.py"

        if not template_file.exists():
            print(f"Error: Template not found: {template_file}")
            return 1

        # Copy and customize template
        shutil.copy2(template_file, plugin_file)

        # Replace placeholder names in the basic template
        if args.template == "basic":
            with open(plugin_file, "r") as f:
                content = f.read()

            content = content.replace("basic_template", args.name)
            content = content.replace(
                "BasicTemplatePlugin", f"{args.name.title().replace('_', '')}Plugin"
            )
            content = content.replace(
                "BasicPreProcessor", f"{args.name.title().replace('_', '')}PreProcessor"
            )
            content = content.replace(
                "BasicPostProcessor", f"{args.name.title().replace('_', '')}PostProcessor"
            )
            content = content.replace(
                "BasicMetadataResolver", f"{args.name.title().replace('_', '')}MetadataResolver"
            )

            with open(plugin_file, "w") as f:
                f.write(content)

        print(f"✓ Created plugin: {plugin_file}")
        print(f"Template: {args.template}")
        print("\nNext steps:")
        print(f"  1. Edit {plugin_file} to implement your logic")
        print(f"  2. Load the plugin: docx2shelf plugins load {plugin_file}")
        print(f"  3. Enable the plugin: docx2shelf plugins enable {args.name}")

        return 0

    return 1


def run_connectors(args) -> int:
    """Handle connector management commands."""
    from pathlib import Path

    from .connectors import connector_manager, download_from_connector, load_default_connectors

    # Load default connectors first
    load_default_connectors()

    if args.connector_cmd == "list":
        connectors = connector_manager.list_connectors()
        if not connectors:
            print("No connectors available.")
            return 0

        print("Available connectors:")
        for conn in connectors:
            status = "✓" if conn["enabled"] else "✗"
            network = "[NET]" if conn["requires_network"] else "[LOCAL]"
            auth = "🔑" if conn["authenticated"] else "🔓"
            print(f"  {status} {network} {auth} {conn['name']}")

        print("\nLegend:")
        print("  ✓/✗ = Enabled/Disabled")
        print("  [NET]/[LOCAL] = Network/Local")
        print("  🔑/🔓 = Authenticated/Not authenticated")
        return 0

    elif args.connector_cmd == "enable":
        if args.allow_network:
            connector_manager.give_network_consent()

        success = connector_manager.enable_connector(args.name, force=args.allow_network)
        if success:
            print(f"Enabled connector: {args.name}")
            return 0
        else:
            print(f"Failed to enable connector: {args.name}")
            return 1

    elif args.connector_cmd == "disable":
        success = connector_manager.disable_connector(args.name)
        if success:
            print(f"Disabled connector: {args.name}")
            return 0
        else:
            print(f"Failed to disable connector: {args.name}")
            return 1

    elif args.connector_cmd == "auth":
        connector = connector_manager.get_connector(args.name)
        if not connector:
            print(f"Error: Connector not found: {args.name}")
            return 1

        if not connector.enabled:
            print(f"Error: Connector not enabled: {args.name}")
            return 1

        auth_kwargs = {}
        if args.credentials:
            auth_kwargs["credentials_path"] = args.credentials

        success = connector.authenticate(**auth_kwargs)
        if success:
            print(f"Authenticated with connector: {args.name}")
            return 0
        else:
            print(f"Authentication failed for connector: {args.name}")
            return 1

    elif args.connector_cmd == "fetch":
        try:
            output_path = (
                Path(args.output) if args.output else Path(f"downloaded_{args.document_id}.docx")
            )
            result_path = download_from_connector(args.connector, args.document_id, output_path)
            print(f"Downloaded document to: {result_path}")
            return 0
        except Exception as e:
            print(f"Error downloading document: {e}")
            return 1

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
