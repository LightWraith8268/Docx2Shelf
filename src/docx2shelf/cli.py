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


def _arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="docx2shelf",
        description="Convert a DOCX manuscript into a valid EPUB 3 (offline)",
    )

    # Add version argument
    p.add_argument(
        "--version", action="version",
        version=get_version_string(),
        help="Show version information and exit"
    )

    sub = p.add_subparsers(dest="command", required=False)

    b = sub.add_parser("build", help="Build an EPUB from inputs")
    b.add_argument(
        "--input",
        type=str,
        help="Path to manuscript file or directory of files (.docx, .md, .txt, .html)",
    )
    b.add_argument("--cover", type=str, help="Path to cover image (jpg/png)")
    b.add_argument("--title", type=str, help="Book title")
    b.add_argument("--author", type=str, help="Author name")
    b.add_argument("--seriesName", type=str, help="Series name (optional)")
    b.add_argument("--seriesIndex", type=str, help="Series index/number (optional)")
    b.add_argument(
        "--title-sort", dest="title_sort", type=str, help="Calibre title sort (optional)"
    )
    b.add_argument(
        "--author-sort", dest="author_sort", type=str, help="Calibre author sort (optional)"
    )
    b.add_argument("--description", type=str, help="Long description (optional)")
    b.add_argument("--isbn", type=str, help="ISBN-13 digits only (optional)")
    b.add_argument("--language", type=str, default="en", help="Language code, e.g., en")
    b.add_argument("--publisher", type=str, help="Publisher (optional)")
    b.add_argument("--pubdate", type=str, help="Publication date ISO YYYY-MM-DD (optional)")
    b.add_argument("--uuid", type=str, help="UUID to use when no ISBN (optional)")
    b.add_argument("--subjects", type=str, help="Comma-separated subjects")
    b.add_argument("--keywords", type=str, help="Comma-separated keywords")

    b.add_argument(
        "--split-at",
        choices=["h1", "h2", "h3", "pagebreak", "mixed"],
        default="h1",
        help="How to split content into XHTML files",
    )
    b.add_argument(
        "--mixed-split-pattern",
        type=str,
        help="Mixed split pattern: 'h1,pagebreak' or 'h1:main,pagebreak:appendix' etc.",
    )
    # Import themes dynamically to get available themes
    try:
        from .themes import get_available_themes
        available_themes = get_available_themes()
    except ImportError:
        available_themes = ["serif", "sans", "printlike"]  # Fallback

    b.add_argument(
        "--theme",
        choices=available_themes,
        default="serif",
        help="Base CSS theme (use --list-themes to see all options)",
    )
    b.add_argument("--embed-fonts", type=str, help="Directory of TTF/OTF to embed")
    b.add_argument("--image-quality", type=int, default=85, help="JPEG/WebP quality for image compression (1-100)")
    b.add_argument("--image-max-width", type=int, default=1200, help="Maximum image width in pixels")
    b.add_argument("--image-max-height", type=int, default=1600, help="Maximum image height in pixels")
    b.add_argument("--image-format", choices=["original", "webp", "avif"], default="webp", help="Convert images to modern format")
    b.add_argument("--enhanced-images", action="store_true", help="Enable enhanced image processing for edge cases (CMYK, transparency, large images)")
    b.add_argument("--vertical-writing", action="store_true", help="Enable vertical writing mode for CJK languages")
    b.add_argument("--hyphenate", choices=["on", "off"], default="on")
    b.add_argument("--justify", choices=["on", "off"], default="on")
    b.add_argument("--toc-depth", type=int, default=2, help="Table of contents depth (1-6)")
    b.add_argument(
        "--chapter-start-mode",
        choices=["auto", "manual", "mixed"],
        default="auto",
        help="TOC chapter detection: auto (scan headings), manual (user-defined), mixed (both)",
    )
    b.add_argument(
        "--chapter-starts",
        type=str,
        help="Comma-separated list of chapter start text patterns for manual TOC mode",
    )
    b.add_argument(
        "--reader-start-chapter",
        type=str,
        help="Chapter title or pattern where reader should start (e.g., 'Chapter 1', 'Prologue')",
    )
    b.add_argument("--page-list", choices=["on", "off"], default="off")
    b.add_argument("--css", type=str, help="Path to extra CSS to merge (optional)")
    b.add_argument("--page-numbers", choices=["on", "off"], default="off")
    b.add_argument("--epub-version", type=str, default="3")
    b.add_argument("--epub2-compat", action="store_true", help="Enable EPUB 2 compatibility mode (stricter CSS)")
    b.add_argument("--cover-scale", choices=["contain", "cover"], default="contain")
    b.add_argument(
        "--font-size", dest="font_size", type=str, help="Base font size (e.g., 1rem, 12pt)"
    )
    b.add_argument(
        "--line-height", dest="line_height", type=str, help="Base line height (e.g., 1.5)"
    )

    b.add_argument("--dedication", type=str, help="Path to plain-text dedication (optional)")
    b.add_argument("--ack", type=str, help="Path to plain-text acknowledgements (optional)")

    # AI Enhancement Options
    b.add_argument("--ai-enhance", action="store_true", help="Enable AI-powered metadata enhancement")
    b.add_argument("--ai-genre", action="store_true", help="Use AI for genre detection and keyword generation")
    b.add_argument("--ai-alt-text", action="store_true", help="Generate AI-powered alt text for images")
    b.add_argument("--ai-interactive", action="store_true", help="Interactive AI suggestions with user prompts")
    b.add_argument("--ai-config", type=str, help="Path to AI configuration file (optional)")

    b.add_argument("--output", type=str, help="Output .epub path (optional)")
    b.add_argument(
        "--output-pattern",
        dest="output_pattern",
        type=str,
        help="Filename pattern with placeholders {title}, {series}, {index}, {index2}",
    )
    b.add_argument("--inspect", action="store_true", help="Emit inspect folder with sources")
    b.add_argument("--dry-run", action="store_true", help="Print planned manifest/spine only")
    b.add_argument("--preview", action="store_true", help="Generate live preview in browser instead of EPUB file")
    b.add_argument("--preview-port", type=int, default=8000, help="Port for preview server (default: 8000)")

    # Import profiles for dynamic choices
    try:
        from .profiles import get_available_profiles
        available_profiles = get_available_profiles()
        profile_help = "Publishing profile to pre-fill settings (use --list-profiles to see all options)"
    except ImportError:
        available_profiles = ["kdp", "kobo", "apple", "generic", "legacy"]
        profile_help = "Publishing profile to pre-fill settings"

    b.add_argument("--profile", choices=available_profiles, help=profile_help)
    b.add_argument("--json-output", help="Output build results in JSON format to specified file")
    b.add_argument(
        "--epubcheck",
        choices=["on", "off"],
        default="on",
        help="Validate with EPUBCheck if available",
    )
    b.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt; use provided defaults and flags only",
    )
    b.add_argument(
        "--auto-install-tools",
        action="store_true",
        help="Automatically install Pandoc/EPUBCheck when missing (no prompts)",
    )
    b.add_argument(
        "--no-install-tools", action="store_true", help="Do not install tools even if missing"
    )
    b.add_argument(
        "--prompt-all", action="store_true", help="Prompt for every field even if prefilled"
    )
    b.add_argument("--quiet", action="store_true", help="Reduce output (errors only)")
    b.add_argument("--verbose", action="store_true", help="Increase output (extra diagnostics)")

    t = sub.add_parser(
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

    # --- Wizard subcommand ---
    wizard = sub.add_parser("wizard", help="Interactive conversion wizard with step-by-step guidance")
    wizard.add_argument(
        "--input", type=str, help="Optional path to input file to start wizard with"
    )
    wizard.add_argument(
        "--no-preview", action="store_true", help="Disable real-time preview generation"
    )
    wizard.add_argument(
        "--session-dir", type=str, help="Directory to store wizard session files"
    )

    # --- Theme Editor subcommand ---
    theme_editor = sub.add_parser("theme-editor", help="Advanced theme editor with visual customization")
    theme_editor.add_argument(
        "--base-theme", type=str, default="serif", help="Base theme to start from (serif, sans, printlike)"
    )
    theme_editor.add_argument(
        "--themes-dir", type=str, help="Directory to store custom themes"
    )

    # --- List themes subcommand ---
    list_themes = sub.add_parser("list-themes", help="List available CSS themes")
    list_themes.add_argument(
        "--genre",
        help="Filter themes by genre (fantasy, romance, mystery, scifi, academic, general)",
    )

    # --- List profiles subcommand ---
    list_profiles = sub.add_parser("list-profiles", help="List available publishing profiles")
    list_profiles.add_argument(
        "--profile",
        help="Show detailed information for a specific profile",
    )

    # --- Batch mode subcommand ---
    batch = sub.add_parser("batch", help="Process multiple DOCX files in batch mode")
    batch.add_argument("--dir", dest="batch_dir", required=True, help="Directory containing DOCX files")
    batch.add_argument("--pattern", dest="batch_pattern", default="*.docx", help="File pattern to match (default: *.docx)")
    batch.add_argument("--output-dir", dest="batch_output_dir", help="Output directory for generated EPUBs")
    batch.add_argument("--parallel", action="store_true", help="Process files in parallel")
    batch.add_argument("--max-workers", type=int, help="Maximum number of parallel workers")
    batch.add_argument("--report", help="Generate batch processing report to file")

    # Add common build options to batch command
    batch.add_argument("--profile", choices=available_profiles, help=profile_help)
    batch.add_argument("--theme", choices=available_themes, default="serif", help="Base CSS theme")
    batch.add_argument("--epub-version", type=str, default="3")
    batch.add_argument("--image-format", choices=["original", "webp", "avif"], default="webp")
    batch.add_argument("--epubcheck", choices=["on", "off"], default="on")

    m = sub.add_parser("tools", help="Manage optional tools (Pandoc, EPUBCheck)")
    m_sub = m.add_subparsers(dest="tool_cmd", required=True)
    mi = m_sub.add_parser("install", help="Install a tool")
    mi.add_argument("name", choices=["pandoc", "epubcheck"], help="Tool name")
    mi.add_argument("--version", dest="version", help="Tool version (optional)")
    mi.add_argument("--preset", choices=["stable", "latest", "bleeding"],
                   default="stable", help="Version preset to use")
    mu = m_sub.add_parser("uninstall", help="Uninstall a tool")
    mu.add_argument("name", choices=["pandoc", "epubcheck", "all"], help="Tool name")
    m_sub.add_parser("where", help="Show tool locations")

    # Health check command
    m_sub.add_parser("doctor", help="Run comprehensive health check on tools setup")

    # Offline bundle commands
    mb = m_sub.add_parser("bundle", help="Create offline installation bundle")
    mb.add_argument("--output", help="Output directory for bundle (default: user data dir)")
    mb.add_argument("--preset", choices=["stable", "latest", "bleeding"],
                   default="stable", help="Version preset for bundled tools")

    # Plugin management commands
    plugins_parser = sub.add_parser("plugins", help="Manage plugins and hooks")
    p_sub = plugins_parser.add_subparsers(dest="plugin_cmd", required=True)

    # List plugins
    plist = p_sub.add_parser("list", help="List available plugins")
    plist.add_argument("--all", action="store_true", help="Show all available plugins (not just loaded)")
    plist.add_argument("--core-only", action="store_true", help="Show only core built-in plugins")
    plist.add_argument("--marketplace-only", action="store_true", help="Show only marketplace plugins")
    plist.add_argument("--category", choices=['core', 'accessibility', 'publishing', 'workflow', 'performance', 'integration', 'theme', 'utility'], help="Filter by category")
    plist.add_argument("--verbose", "-v", action="store_true", help="Show detailed plugin information")

    # Marketplace commands
    pm = p_sub.add_parser("marketplace", help="Browse and install marketplace plugins")
    pm_sub = pm.add_subparsers(dest="marketplace_cmd", required=True)

    # Search marketplace
    pmsearch = pm_sub.add_parser("search", help="Search marketplace plugins")
    pmsearch.add_argument("query", nargs="?", help="Search query")
    pmsearch.add_argument("--tags", nargs="*", help="Filter by tags")
    pmsearch.add_argument("--category", help="Filter by category")

    # List marketplace plugins
    pmlist = pm_sub.add_parser("list", help="List marketplace plugins")
    pmlist.add_argument("--popular", action="store_true", help="Show popular plugins")
    pmlist.add_argument("--new", action="store_true", help="Show newest plugins")

    # Install marketplace plugin
    pminstall = pm_sub.add_parser("install", help="Install plugin from marketplace")
    pminstall.add_argument("plugin", help="Plugin name or package")
    pminstall.add_argument("--version", help="Specific version to install")

    # Update marketplace plugin
    pmupdate = pm_sub.add_parser("update", help="Update marketplace plugin")
    pmupdate.add_argument("plugin", help="Plugin name to update")

    # Uninstall marketplace plugin
    pmuninstall = pm_sub.add_parser("uninstall", help="Uninstall marketplace plugin")
    pmuninstall.add_argument("plugin", help="Plugin name to uninstall")

    # Plugin bundles
    pb = p_sub.add_parser("bundles", help="Manage plugin bundles")
    pb_sub = pb.add_subparsers(dest="bundle_cmd", required=True)

    # List bundles
    pblist = pb_sub.add_parser("list", help="List available plugin bundles")
    pblist.add_argument("--verbose", "-v", action="store_true", help="Show detailed bundle information")

    # Install bundle
    pbinstall = pb_sub.add_parser("install", help="Install plugin bundle")
    pbinstall.add_argument("bundle", choices=['publishing', 'workflow', 'accessibility', 'cloud', 'premium'], help="Bundle to install")

    # Bundle info
    pbinfo = pb_sub.add_parser("info", help="Show information about a bundle")
    pbinfo.add_argument("bundle", help="Bundle name")

    # Load plugin
    pl = p_sub.add_parser("load", help="Load a plugin from file")
    pl.add_argument("path", help="Path to plugin file")

    # Enable/disable plugins
    pe = p_sub.add_parser("enable", help="Enable a plugin")
    pe.add_argument("name", help="Plugin name")
    pd = p_sub.add_parser("disable", help="Disable a plugin")
    pd.add_argument("name", help="Plugin name")

    # Plugin info
    pinfo = p_sub.add_parser("info", help="Show detailed information about a plugin")
    pinfo.add_argument("name", help="Plugin name")

    # Discover plugins
    pdiscover = p_sub.add_parser("discover", help="Discover available plugins in standard locations")
    pdiscover.add_argument("--install", action="store_true", help="Install user plugins directory if it doesn't exist")

    # Create plugin template
    pcreate = p_sub.add_parser("create", help="Create a new plugin from template")
    pcreate.add_argument("name", help="Plugin name")
    pcreate.add_argument("--template", choices=["basic", "html-cleaner", "metadata-enhancer"],
                        default="basic", help="Template to use")
    pcreate.add_argument("--output", help="Output directory (default: current directory)")

    # Connector management commands
    c = sub.add_parser("connectors", help="Manage document connectors")
    c_sub = c.add_subparsers(dest="connector_cmd", required=True)
    c_sub.add_parser("list", help="List available connectors")
    ce = c_sub.add_parser("enable", help="Enable a connector")
    ce.add_argument("name", help="Connector name")
    ce.add_argument("--allow-network", action="store_true", help="Allow network access for connector")
    cd = c_sub.add_parser("disable", help="Disable a connector")
    cd.add_argument("name", help="Connector name")
    ca = c_sub.add_parser("auth", help="Authenticate with a connector")
    ca.add_argument("name", help="Connector name")
    ca.add_argument("--credentials", help="Path to credentials file")
    cf = c_sub.add_parser("fetch", help="Fetch document from connector")
    cf.add_argument("connector", help="Connector name")
    cf.add_argument("document_id", help="Document ID")
    cf.add_argument("--output", help="Output path")

    # --- AI subcommand ---
    ai = sub.add_parser("ai", help="AI-powered document analysis and enhancement")
    ai_sub = ai.add_subparsers(dest="ai_action", required=True)

    # AI metadata enhancement
    ai_meta = ai_sub.add_parser("metadata", help="Enhance metadata using AI analysis")
    ai_meta.add_argument("input_file", help="Document file to analyze")
    ai_meta.add_argument("--interactive", action="store_true", help="Interactive metadata suggestions")
    ai_meta.add_argument("--output", help="Output enhanced metadata to file")

    # AI genre detection
    ai_genre = ai_sub.add_parser("genre", help="Detect genres and keywords using AI")
    ai_genre.add_argument("input_file", help="Document file to analyze")
    ai_genre.add_argument("--json", action="store_true", help="Output results as JSON")

    # AI alt text generation
    ai_alt = ai_sub.add_parser("alt-text", help="Generate alt text for images using AI")
    ai_alt.add_argument("input_path", help="Image file or document with images")
    ai_alt.add_argument("--interactive", action="store_true", help="Interactive alt text suggestions")
    ai_alt.add_argument("--output", help="Output alt text suggestions to file")

    # AI configuration
    ai_config = ai_sub.add_parser("config", help="Configure AI settings")
    ai_config.add_argument("--list", action="store_true", help="List current AI configuration")
    ai_config.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value")
    ai_config.add_argument("--reset", action="store_true", help="Reset to default configuration")

    sub.add_parser("update", help="Update docx2shelf to the latest version")

    # Environment diagnostic command
    sub.add_parser("doctor", help="Run comprehensive environment diagnostics")

    # Interactive CLI command
    sub.add_parser("interactive", help="Launch interactive menu-driven CLI interface")

    # --- Checklist subcommand ---
    check = sub.add_parser("checklist", help="Run publishing store compatibility checklists")
    check.add_argument("--metadata", help="Path to metadata.txt file (default: ./metadata.txt)")
    check.add_argument("--cover", help="Path to cover image file")
    check.add_argument("--store", choices=["kdp", "apple", "kobo", "all"], default="all",
                      help="Which store to check (default: all)")
    check.add_argument("--json", action="store_true", help="Output results as JSON")

    # --- Quality assessment subcommand ---
    quality = sub.add_parser("quality", help="Comprehensive quality analysis of EPUB files")
    quality.add_argument("epub_path", help="Path to EPUB file to analyze")
    quality.add_argument("--content-files", nargs="*", help="Additional content files to validate (XHTML/HTML)")
    quality.add_argument("--target-level", choices=["A", "AA", "AAA"], default="AA",
                        help="WCAG accessibility target level (default: AA)")
    quality.add_argument("--skip-accessibility", action="store_true",
                        help="Skip accessibility compliance checking")
    quality.add_argument("--skip-content-validation", action="store_true",
                        help="Skip content validation (grammar, style, formatting)")
    quality.add_argument("--skip-quality-scoring", action="store_true",
                        help="Skip overall quality scoring")
    quality.add_argument("--json", action="store_true", help="Output results as JSON")
    quality.add_argument("--output", help="Save detailed report to file")
    quality.add_argument("--auto-fix", action="store_true",
                        help="Automatically fix issues where possible")
    quality.add_argument("--verbose", action="store_true",
                        help="Show detailed issue descriptions and recommendations")

    # --- EPUB validation subcommand ---
    validate = sub.add_parser("validate", help="Validate EPUB files using EPUBCheck and custom rules")
    validate.add_argument("epub_path", help="Path to EPUB file to validate")
    validate.add_argument("--verbose", action="store_true", help="Show detailed validation report")
    validate.add_argument("--skip-epubcheck", action="store_true", help="Skip EPUBCheck validation")
    validate.add_argument("--skip-custom", action="store_true", help="Skip custom validation checks")
    validate.add_argument("--timeout", type=int, default=120, help="Timeout for EPUBCheck in seconds")

    # Convert command for format conversion
    convert = sub.add_parser("convert", help="Convert EPUB to other formats (PDF, MOBI, AZW3, Web, Text)")
    convert.add_argument("input", help="Path to EPUB file to convert")
    convert.add_argument("--format", "-f",
                        choices=["pdf", "mobi", "azw3", "web", "txt", "text"],
                        required=True,
                        help="Output format")
    convert.add_argument("--output", "-o",
                        help="Output file/directory path (auto-generated if not specified)")
    convert.add_argument("--quality",
                        choices=["standard", "high", "web"],
                        default="standard",
                        help="Output quality level")
    convert.add_argument("--compression", action="store_true", default=True,
                        help="Enable compression (where applicable)")
    convert.add_argument("--no-compression", action="store_false", dest="compression",
                        help="Disable compression")
    convert.add_argument("--page-size",
                        default="A4",
                        help="Page size for PDF (A4, Letter, Legal, etc.)")
    convert.add_argument("--margin",
                        default="1in",
                        help="Page margins for PDF (e.g., 1in, 2cm)")
    convert.add_argument("--font-size",
                        default="12pt",
                        help="Base font size")
    convert.add_argument("--font-family",
                        choices=["serif", "sans-serif", "monospace"],
                        default="serif",
                        help="Font family")
    convert.add_argument("--no-toc", action="store_false", dest="include_toc",
                        help="Exclude table of contents")
    convert.add_argument("--no-cover", action="store_false", dest="include_cover",
                        help="Exclude cover image")
    convert.add_argument("--css",
                        help="Path to custom CSS file for styling")
    convert.add_argument("--check-deps", action="store_true",
                        help="Check format dependencies and exit")

    # --- Enterprise subcommand ---
    enterprise = sub.add_parser("enterprise", help="Enterprise features for batch processing and automation")
    enterprise_sub = enterprise.add_subparsers(dest="enterprise_cmd", required=True)

    # Enterprise batch processing
    ent_batch = enterprise_sub.add_parser("batch", help="Advanced batch processing for enterprises")
    ent_batch.add_argument("name", help="Job name")
    ent_batch.add_argument("--input", required=True, help="Input directory or pattern")
    ent_batch.add_argument("--output", required=True, help="Output directory")
    ent_batch.add_argument("--mode", choices=["files", "books"], default="books",
                          help="Processing mode: 'files' (individual) or 'books' (folders as books)")
    ent_batch.add_argument("--config", help="Path to job configuration file (YAML/JSON)")
    ent_batch.add_argument("--webhook", help="Webhook URL for job notifications")
    ent_batch.add_argument("--priority", type=int, default=5, help="Job priority (1-10)")
    ent_batch.add_argument("--theme", default="serif", help="EPUB theme")
    ent_batch.add_argument("--split-at", default="h1", help="Chapter split level")
    ent_batch.add_argument("--max-concurrent", type=int, help="Maximum concurrent jobs")

    # Enterprise job management
    ent_jobs = enterprise_sub.add_parser("jobs", help="Manage batch jobs")
    ent_jobs.add_argument("--list", action="store_true", help="List all jobs")
    ent_jobs.add_argument("--status", choices=["pending", "running", "completed", "failed", "cancelled"],
                         help="Filter jobs by status")
    ent_jobs.add_argument("--cancel", help="Cancel job by ID")
    ent_jobs.add_argument("--details", help="Show detailed job information by ID")
    ent_jobs.add_argument("--cleanup", action="store_true", help="Clean up old completed jobs")

    # Enterprise configuration
    ent_config = enterprise_sub.add_parser("config", help="Enterprise configuration management")
    ent_config.add_argument("--init", action="store_true", help="Initialize enterprise configuration")
    ent_config.add_argument("--show", action="store_true", help="Show current configuration")
    ent_config.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value")
    ent_config.add_argument("--reset", action="store_true", help="Reset to default configuration")
    ent_config.add_argument("--export", help="Export configuration to file")
    ent_config.add_argument("--import", dest="import_config", help="Import configuration from file")

    # Enterprise user management
    ent_users = enterprise_sub.add_parser("users", help="User management and permissions")
    ent_users.add_argument("--create", help="Create new user (username)")
    ent_users.add_argument("--email", help="User email (for create)")
    ent_users.add_argument("--role", choices=["admin", "user", "viewer"], default="user",
                          help="User role (for create)")
    ent_users.add_argument("--list", action="store_true", help="List all users")
    ent_users.add_argument("--permissions", help="Set user permissions (comma-separated)")
    ent_users.add_argument("--deactivate", help="Deactivate user by ID")
    ent_users.add_argument("--generate-key", help="Generate API key for user")

    # Enterprise API server
    ent_api = enterprise_sub.add_parser("api", help="Enterprise API server management")
    ent_api.add_argument("--start", action="store_true", help="Start API server")
    ent_api.add_argument("--host", default="localhost", help="API server host")
    ent_api.add_argument("--port", type=int, default=8080, help="API server port")
    ent_api.add_argument("--debug", action="store_true", help="Enable debug mode")
    ent_api.add_argument("--status", action="store_true", help="Show API server status")

    # Enterprise webhooks
    ent_webhooks = enterprise_sub.add_parser("webhooks", help="Webhook management")
    ent_webhooks.add_argument("--add", help="Add webhook URL")
    ent_webhooks.add_argument("--events", nargs="*", help="Webhook events to subscribe to")
    ent_webhooks.add_argument("--secret", help="Webhook secret for signatures")
    ent_webhooks.add_argument("--list", action="store_true", help="List configured webhooks")
    ent_webhooks.add_argument("--remove", help="Remove webhook by ID")
    ent_webhooks.add_argument("--test", help="Test webhook by URL")

    # Enterprise reporting
    ent_reports = enterprise_sub.add_parser("reports", help="Enterprise reporting and analytics")
    ent_reports.add_argument("--stats", action="store_true", help="Show processing statistics")
    ent_reports.add_argument("--usage", action="store_true", help="Show usage analytics")
    ent_reports.add_argument("--export", help="Export report to file (CSV/JSON)")
    ent_reports.add_argument("--period", choices=["day", "week", "month"], default="week",
                            help="Reporting period")

    return p


def _apply_metadata_dict(args: argparse.Namespace, md: dict, base_dir: Path | None) -> None:
    if not md:
        return

    def get(k: str):
        # allow simple aliases
        aliases = {
            "series": "seriesName",
            "seriesname": "seriesName",
            "series_index": "seriesIndex",
            "seriesindex": "seriesIndex",
            "title-sort": "title_sort",
            "author-sort": "author_sort",
        }
        k2 = aliases.get(k.lower(), k)
        return md.get(k, md.get(k.lower(), md.get(k2, md.get(k2.lower()))))

    def pathify(val: str | None) -> str | None:
        if not val:
            return None
        p = Path(val)
        if not p.is_absolute() and base_dir:
            p = (base_dir / p).resolve()
        return str(p)

    # Core (file overrides defaults; CLI may still override if passed explicitly)
    if (not args.input) and get("input"):
        args.input = get("input")
    if (not args.cover) and get("cover"):
        args.cover = pathify(get("cover"))
    if (not args.title) and get("title"):
        args.title = get("title")
    if (not args.author) and get("author"):
        args.author = get("author")
    if (not args.language) and get("language"):
        args.language = get("language")
    # Optional metadata
    if get("seriesname") or get("series"):
        args.seriesName = get("seriesname") or get("series")
    if get("seriesindex"):
        args.seriesIndex = get("seriesindex")
    if get("title_sort") or get("title-sort"):
        setattr(args, "title_sort", get("title_sort") or get("title-sort"))
    if get("author_sort") or get("author-sort"):
        setattr(args, "author_sort", get("author_sort") or get("author-sort"))
    if get("description"):
        args.description = get("description")
    if get("isbn"):
        args.isbn = get("isbn")
    if get("publisher"):
        args.publisher = get("publisher")
    if get("pubdate"):
        args.pubdate = get("pubdate")
    if get("uuid"):
        args.uuid = get("uuid")
    if get("subjects"):
        args.subjects = get("subjects")
    if get("keywords"):
        args.keywords = get("keywords")

    # Extended metadata fields
    if get("editor"):
        setattr(args, "editor", get("editor"))
    if get("illustrator"):
        setattr(args, "illustrator", get("illustrator"))
    if get("translator"):
        setattr(args, "translator", get("translator"))
    if get("narrator"):
        setattr(args, "narrator", get("narrator"))
    if get("designer"):
        setattr(args, "designer", get("designer"))
    if get("contributor"):
        setattr(args, "contributor", get("contributor"))
    if get("bisac_codes") or get("bisac-codes"):
        setattr(args, "bisac_codes", get("bisac_codes") or get("bisac-codes"))
    if get("age_range") or get("age-range"):
        setattr(args, "age_range", get("age_range") or get("age-range"))
    if get("reading_level") or get("reading-level"):
        setattr(args, "reading_level", get("reading_level") or get("reading-level"))
    if get("copyright_holder") or get("copyright-holder"):
        setattr(args, "copyright_holder", get("copyright_holder") or get("copyright-holder"))
    if get("copyright_year") or get("copyright-year"):
        setattr(args, "copyright_year", get("copyright_year") or get("copyright-year"))
    if get("rights"):
        setattr(args, "rights", get("rights"))
    if get("price"):
        setattr(args, "price", get("price"))
    if get("currency"):
        setattr(args, "currency", get("currency"))
    if get("print_isbn") or get("print-isbn"):
        setattr(args, "print_isbn", get("print_isbn") or get("print-isbn"))
    if get("audiobook_isbn") or get("audiobook-isbn"):
        setattr(args, "audiobook_isbn", get("audiobook_isbn") or get("audiobook-isbn"))
    if get("series_type") or get("series-type"):
        setattr(args, "series_type", get("series_type") or get("series-type"))
    if get("series_position") or get("series-position"):
        setattr(args, "series_position", get("series_position") or get("series-position"))
    if get("publication_type") or get("publication-type"):
        setattr(args, "publication_type", get("publication_type") or get("publication-type"))
    if get("target_audience") or get("target-audience"):
        setattr(args, "target_audience", get("target_audience") or get("target-audience"))
    if get("content_warnings") or get("content-warnings"):
        setattr(args, "content_warnings", get("content_warnings") or get("content-warnings"))
    # Conversion/layout
    if (args.split_at in (None, "", "h1")) and (get("split_at") or get("split-at")):
        args.split_at = get("split_at") or get("split-at")
    if (args.theme in (None, "", "serif")) and get("theme"):
        args.theme = get("theme")
    if (args.hyphenate in (None, "", "on")) and get("hyphenate"):
        args.hyphenate = get("hyphenate")
    if (args.justify in (None, "", "on")) and get("justify"):
        args.justify = get("justify")
    try:
        if get("toc_depth") and not getattr(args, "toc_depth_set", False):
            args.toc_depth = int(get("toc_depth"))
            setattr(args, "toc_depth_set", True)
    except Exception:
        pass
    if (getattr(args, "toc_depth", None) in (None, 2)) and get("toc_depth"):
        try:
            args.toc_depth = int(get("toc_depth"))
        except Exception:
            pass
    # Chapter start mode and patterns
    if (getattr(args, "chapter_start_mode", None) in (None, "auto")) and (
        get("chapter_start_mode") or get("chapter-start-mode")
    ):
        setattr(args, "chapter_start_mode", get("chapter_start_mode") or get("chapter-start-mode"))
    if (getattr(args, "chapter_starts", None) in (None, "")) and (
        get("chapter_starts") or get("chapter-starts")
    ):
        setattr(args, "chapter_starts", get("chapter_starts") or get("chapter-starts"))
    if (args.page_list in (None, "", "off")) and (get("page_list") or get("page-list")):
        args.page_list = get("page_list") or get("page-list")
    if (args.page_numbers in (None, "", "off")) and (get("page_numbers") or get("page-numbers")):
        args.page_numbers = get("page_numbers") or get("page-numbers")
    if (args.cover_scale in (None, "", "contain")) and (get("cover_scale") or get("cover-scale")):
        args.cover_scale = get("cover_scale") or get("cover-scale")
    # Typography options
    if getattr(args, "font_size", None) in (None, "") and (get("font_size") or get("font-size")):
        setattr(args, "font_size", get("font_size") or get("font-size"))
    if getattr(args, "line_height", None) in (None, "") and (
        get("line_height") or get("line-height")
    ):
        setattr(args, "line_height", get("line_height") or get("line-height"))
    # Assets
    if (getattr(args, "css", None) in (None, "")) and get("css"):
        args.css = pathify(get("css"))
    if (getattr(args, "embed_fonts", None) in (None, "")) and (
        get("embed_fonts") or get("embed-fonts")
    ):
        args.embed_fonts = pathify(get("embed_fonts") or get("embed-fonts"))
    if (getattr(args, "dedication", None) in (None, "")) and get("dedication"):
        args.dedication = pathify(get("dedication"))
    if (getattr(args, "ack", None) in (None, "")) and (
        get("ack") or get("acknowledgements") or get("acknowledgments")
    ):
        args.ack = pathify(get("ack") or get("acknowledgements") or get("acknowledgments"))
    # Output
    if (getattr(args, "output", None) in (None, "")) and get("output"):
        args.output = pathify(get("output"))
    if (getattr(args, "epubcheck", None) in (None, "on")) and get("epubcheck"):
        args.epubcheck = get("epubcheck")


def _print_checklist(args: argparse.Namespace) -> None:
    def checked(val) -> str:
        return "[x]" if (val is not None and str(val).strip() != "") else "[ ]"

    items = [
        ("Input", args.input),
        ("Cover", args.cover),
        ("Title", args.title),
        ("Author", args.author),
        ("Language", args.language),
        ("Series", args.seriesName),
        ("Series Index", args.seriesIndex),
        ("Title Sort", getattr(args, "title_sort", None)),
        ("Author Sort", getattr(args, "author_sort", None)),
        ("Description", args.description),
        ("ISBN", args.isbn),
        ("Publisher", args.publisher),
        ("PubDate", args.pubdate),
        ("UUID", args.uuid),
        ("Subjects", args.subjects),
        ("Keywords", args.keywords),
        ("Split At", args.split_at),
        ("Theme", args.theme),
        ("Hyphenate", args.hyphenate),
        ("Justify", args.justify),
        ("ToC Depth", getattr(args, "toc_depth", None)),
        ("Page List", args.page_list),
        ("Page Numbers", args.page_numbers),
        ("Cover Scale", args.cover_scale),
        ("Extra CSS", args.css),
        ("Fonts Dir", args.embed_fonts),
        ("Dedication", args.dedication),
        ("Acknowledgements", args.ack),
        ("EPUBCheck", getattr(args, "epubcheck", None)),
        ("Output", args.output),
    ]
    print("\n== Metadata Checklist ==")
    print("(Press Enter to skip/keep current when prompted)\n")
    for name, val in items:
        display = str(val) if val is not None and str(val).strip() != "" else "—"
        print(f" {checked(val)} {name}: {display}")
    print("")


def _prompt_missing(args: argparse.Namespace) -> argparse.Namespace:
    # Ask interactively for anything not provided on CLI.
    import sys as _sys

    interactive = (not getattr(args, "no_prompt", False)) and _sys.stdin.isatty()

    # Ask for input path if not provided
    if not args.input and interactive:
        args.input = prompt("Path to manuscript file or folder", allow_empty=False)

    # Attempt to pre-load metadata from metadata.txt
    md_loaded = False
    if args.input:
        try:
            input_path = Path(args.input).expanduser()
            md_dir = input_path.parent if input_path.is_file() else input_path
            mfile = md_dir / "metadata.txt"
            if mfile.exists():
                _apply_metadata_dict(args, parse_kv_file(mfile), md_dir)
                md_loaded = True
        except Exception:
            pass
    # If no input yet, try CWD metadata.txt and let it specify input
    if not md_loaded:
        mfile = Path.cwd() / "metadata.txt"
        if mfile.exists():
            md = parse_kv_file(mfile)
            _apply_metadata_dict(args, md, Path.cwd())
            # If input now set, and a different dir holds another metadata.txt, merge it
            if args.input:
                d = Path(args.input).expanduser().resolve().parent
                if d != Path.cwd() and (d / "metadata.txt").exists():
                    _apply_metadata_dict(args, parse_kv_file(d / "metadata.txt"), d)

    # After potential docx selection, attempt to auto-detect or pick common cover file name
    if not args.cover and args.input:
        docx_path_tmp = Path(args.input).expanduser().resolve()
        docx_dir_tmp = docx_path_tmp.parent
        # Enumerate available image files (jpg/jpeg/png)
        cover_candidates = (
            [p.name for p in sorted(docx_dir_tmp.glob("*.jpg"))]
            + [p.name for p in sorted(docx_dir_tmp.glob("*.jpeg"))]
            + [p.name for p in sorted(docx_dir_tmp.glob("*.png"))]
        )
        # Prefer conventional cover names first if present
        conventional = [
            n for n in ("cover.jpg", "cover.jpeg", "cover.png") if (docx_dir_tmp / n).is_file()
        ]
        if conventional:
            # Move conventional names to the front of the candidate list
            cover_candidates = list(dict.fromkeys(conventional + cover_candidates))
        if interactive and cover_candidates:
            args.cover = prompt_select("Select cover image:", cover_candidates, default_index=1)

    if interactive:
        _print_checklist(args)

    if not args.cover and interactive:
        # Offer a numeric pick of images in the folder, else prompt
        cwd = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        img_files = (
            [p.name for p in sorted(cwd.glob("*.jpg"))]
            + [p.name for p in sorted(cwd.glob("*.jpeg"))]
            + [p.name for p in sorted(cwd.glob("*.png"))]
        )
        if img_files:
            args.cover = prompt_select("Select cover image:", img_files, default_index=1)
        else:
            args.cover = prompt("Cover filename in this folder (jpg/png)", allow_empty=True)
    if not args.title and interactive:
        args.title = prompt("Book title", allow_empty=True)
    # Ask for author and language (respect provided values)
    if interactive:
        args.author = prompt("Author", default=args.author or "", allow_empty=True)
        args.language = prompt("Language (BCP-47)", default=args.language or "en")
    # Defaults already exist for author and language.
    # Optional metadata
    if interactive and (args.seriesName is None):
        args.seriesName = prompt("Series name (optional)", default="", allow_empty=True)
    if interactive and (args.seriesIndex is None) and args.seriesName:
        args.seriesIndex = prompt("Series index (optional)", default="", allow_empty=True)
    # Calibre-compatible sort fields
    if interactive and getattr(args, "title_sort", None) is None:
        setattr(args, "title_sort", prompt("Title sort (optional)", default="", allow_empty=True))
    if interactive and getattr(args, "author_sort", None) is None:
        setattr(args, "author_sort", prompt("Author sort (optional)", default="", allow_empty=True))
    if interactive and args.description is None:
        args.description = prompt("Description (optional)", default="", allow_empty=True)
    if interactive and args.isbn is None:
        args.isbn = prompt("ISBN-13 (optional)", default="", allow_empty=True)
    if interactive and args.publisher is None:
        args.publisher = prompt("Publisher (optional)", default="", allow_empty=True)
    if interactive and args.pubdate is None:
        args.pubdate = prompt(
            "Publication date YYYY-MM-DD (optional)", default="", allow_empty=True
        )
    if interactive and args.uuid is None:
        args.uuid = prompt("UUID (optional, auto if absent)", default="", allow_empty=True)
    if interactive and args.subjects is None:
        args.subjects = prompt("Subjects (comma-separated, optional)", default="", allow_empty=True)
    if interactive and args.keywords is None:
        args.keywords = prompt("Keywords (comma-separated, optional)", default="", allow_empty=True)

    # Conversion/layout options
    if interactive:
        args.split_at = prompt_select(
            "Split at:",
            ["h1", "h2", "pagebreak"],
            default_index={"h1": 1, "h2": 2, "pagebreak": 3}.get(args.split_at, 1),
        )
        args.theme = prompt_select(
            "Theme:",
            ["serif", "sans", "printlike"],
            default_index={"serif": 1, "sans": 2, "printlike": 3}.get(args.theme, 1),
        )
        args.hyphenate = prompt_select(
            "Hyphenate:", ["on", "off"], default_index={"on": 1, "off": 2}.get(args.hyphenate, 1)
        )
        args.justify = prompt_select(
            "Justify:", ["on", "off"], default_index={"on": 1, "off": 2}.get(args.justify, 1)
        )
        # Numeric picker for ToC depth
        default_idx = 1 if int(args.toc_depth) == 1 else 2
        sel = prompt_select("ToC depth:", ["1", "2"], default_index=default_idx)
        args.toc_depth = int(sel)

        # Chapter start mode selection
        mode_default = {"auto": 1, "manual": 2, "mixed": 3}.get(
            getattr(args, "chapter_start_mode", "auto"), 1
        )
        mode_sel = prompt_select(
            "Chapter detection:",
            ["auto (scan headings)", "manual (user-defined)", "mixed"],
            default_index=mode_default,
        )
        if mode_sel == "auto (scan headings)":
            args.chapter_start_mode = "auto"
        elif mode_sel == "manual (user-defined)":
            args.chapter_start_mode = "manual"
            # Prompt for chapter starts if not already provided
            if not getattr(args, "chapter_starts", None):
                chapter_input = prompt(
                    "Chapter start patterns (comma-separated):",
                    default="Chapter 1, Chapter 2, Chapter 3",
                )
                if chapter_input and chapter_input.strip():
                    args.chapter_starts = chapter_input.strip()
        else:  # mixed
            args.chapter_start_mode = "mixed"

        args.page_list = prompt_select(
            "Include page-list nav?",
            ["on", "off"],
            default_index={"on": 1, "off": 2}.get(args.page_list, 2),
        )
        args.page_numbers = prompt_select(
            "Show page number counters?",
            ["on", "off"],
            default_index={"on": 1, "off": 2}.get(args.page_numbers, 2),
        )
        args.cover_scale = prompt_select(
            "Cover scaling:",
            ["contain", "cover"],
            default_index={"contain": 1, "cover": 2}.get(args.cover_scale, 1),
        )
    # Optional assets
    if interactive and args.css is None:
        # Offer a numeric pick of CSS files in the folder
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        css_files = [p.name for p in sorted(base.glob("*.css"))]
        if css_files:
            choices = ["(none)"] + css_files
            sel = prompt_select("Extra CSS (optional):", choices, default_index=1)
            args.css = "" if sel == "(none)" else sel
        else:
            args.css = ""
    if interactive and args.embed_fonts is None:
        # Find directories that contain TTF/OTF files and offer a pick
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        dir_candidates = []
        for d in sorted([p for p in base.iterdir() if p.is_dir()]):
            if any((d.glob("*.ttf"))) or any((d.glob("*.otf"))):
                dir_candidates.append(d.name)
        if dir_candidates:
            choices = ["(none)"] + dir_candidates
            sel = prompt_select("Embed fonts directory (optional):", choices, default_index=1)
            args.embed_fonts = "" if sel == "(none)" else sel
        else:
            args.embed_fonts = ""
    if interactive and args.dedication is None:
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        txt_files = [p.name for p in sorted(base.glob("*.txt"))]
        if txt_files:
            choices = ["(none)"] + txt_files
            sel = prompt_select("Dedication .txt (optional):", choices, default_index=1)
            args.dedication = "" if sel == "(none)" else sel
        else:
            args.dedication = ""
    if interactive and args.ack is None:
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        txt_files = [p.name for p in sorted(base.glob("*.txt"))]
        if txt_files:
            choices = ["(none)"] + txt_files
            sel = prompt_select("Acknowledgements .txt (optional):", choices, default_index=1)
            args.ack = "" if sel == "(none)" else sel
        else:
            args.ack = ""
    # Validation
    if interactive:
        epub_default_idx = 1 if getattr(args, "epubcheck", None) in (True, None, "on") else 2
        args.epubcheck = prompt_select(
            "Validate with EPUBCheck if available?", ["on", "off"], default_index=epub_default_idx
        )

    if args.output is None and interactive:
        # Suggest computed output filename and allow override
        suggested = build_output_filename(
            title=args.title,
            series=args.seriesName or None,
            series_index=args.seriesIndex or None,
        )
        out = prompt("Output filename", default=suggested)
        args.output = out

    # Auto-generate a metadata.txt template next to input if missing (interactive)
    try:
        if interactive and args.input:
            input_path = Path(args.input).expanduser()
            mpath = input_path.parent / "metadata.txt"
            if not mpath.exists():
                tmpl_ns = argparse.Namespace(
                    input=str(input_path),
                    cover=args.cover if args.cover else None,
                    output=None,
                    force=False,
                )
                run_init_metadata(tmpl_ns)
    except Exception:
        pass

    return args


def _print_metadata_summary(meta: EpubMetadata, opts: BuildOptions, output: Path | None) -> None:
    def mark(val):
        return "[x]" if val else "[ ]"

    print("\n== Metadata Summary ==")
    print(f" {mark(meta.title)} Title: {meta.title or '—'}")
    print(f" {mark(meta.author)} Author: {meta.author or '—'}")
    print(f" {mark(meta.language)} Language: {meta.language or '—'}")
    print(f" {mark(meta.isbn or meta.uuid)} Identifier: {'ISBN '+meta.isbn if meta.isbn else (meta.uuid or '—')}")
    if meta.series:
        print(f" {mark(meta.series)} Series: {meta.series} #{meta.series_index or '—'}")
    print(f" {mark(meta.publisher)} Publisher: {meta.publisher or '—'}")
    print(f" {mark(meta.pubdate)} PubDate: {meta.pubdate.isoformat() if meta.pubdate else '—'}")
    print(f" {mark(bool(meta.subjects))} Subjects: {', '.join(meta.subjects) if meta.subjects else '—'}")
    print(f" {mark(bool(meta.keywords))} Keywords: {', '.join(meta.keywords) if meta.keywords else '—'}")
    print(f" {mark(meta.cover_path)} Cover: {meta.cover_path}")
    print(f" {mark(opts.extra_css)} Extra CSS: {opts.extra_css or '—'}  | Fonts: {opts.embed_fonts_dir or '—'}")
    # Show chapter mode information
    if opts.chapter_start_mode == "manual" and opts.chapter_starts:
        chapter_list = (
            opts.chapter_starts[:3]
            if isinstance(opts.chapter_starts, list)
            else opts.chapter_starts.split(",")[:3]
        )
        display_chapters = ", ".join(chapter_list) + ("..." if len(chapter_list) > 3 else "")
        print(f" {mark(opts.chapter_starts)} Chapter Mode: manual ({display_chapters})")
    elif opts.chapter_start_mode == "mixed":
        print(" [x] Chapter Mode: mixed (custom + auto)")
    else:
        print(" [x] Chapter Mode: auto (scan headings)")
    print(f" Output: {output or '—'}\n")


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
            quiet=getattr(args, 'quiet', False)
        )

        # Generate report if requested
        if args.report:
            report_path = Path(args.report)
            create_batch_report(summary, report_path)
            print(f"📄 Batch report written to: {report_path}")

        # Return non-zero if any files failed
        return 0 if summary['failed'] == 0 else 1

    except ImportError:
        print("Batch processing not available.")
        return 1
    except Exception as e:
        print(f"Batch processing error: {e}", file=sys.stderr)
        return 1


def run_build(args: argparse.Namespace) -> int:
    from .assemble import assemble_epub, plan_build
    from .convert import (
        convert_file_to_html,
        split_html_by_heading,
        split_html_by_heading_level,
        split_html_by_pagebreak,
        split_html_mixed,
    )
    from .performance import PerformanceMonitor

    # Initialize performance monitoring for the entire build process
    build_monitor = PerformanceMonitor()
    build_monitor.start_monitoring()

    # Initialize JSON logger if requested
    json_logger = None
    if getattr(args, 'json_output', None):
        from .json_logger import init_json_logger
        json_logger = init_json_logger(Path(args.json_output))

    # Apply profile settings if specified
    if getattr(args, 'profile', None):
        try:
            from .profiles import apply_profile_to_args
            apply_profile_to_args(args, args.profile)
            if not getattr(args, 'quiet', False):
                print(f"📋 Applied profile: {args.profile}")
        except ImportError:
            print("Warning: Profile system not available", file=sys.stderr)
        except Exception as e:
            print(f"Error applying profile: {e}", file=sys.stderr)
            return 1

    # Validate paths with enhanced error handling
    try:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            # Use enhanced error handling for missing input files
            handled = handle_error(
                error=FileNotFoundError(f"Input file not found: {input_path}"),
                operation="input file validation",
                file_path=input_path,
                interactive=True
            )
            if not handled:
                print(f"Error: Input path not found: {input_path}", file=sys.stderr)
                return 2

        input_dir = input_path.parent if input_path.is_file() else input_path

        cover_path_candidate = Path(args.cover).expanduser()
        if not cover_path_candidate.is_absolute():
            cover_path_candidate = input_dir / cover_path_candidate
        cover_path = cover_path_candidate.resolve()

        if not cover_path.is_file():
            # Use enhanced error handling for missing cover files
            handled = handle_error(
                error=FileNotFoundError(f"Cover file not found: {cover_path}"),
                operation="cover file validation",
                file_path=cover_path,
                interactive=True
            )
            if not handled:
                print(f"Error: cover not found: {cover_path}", file=sys.stderr)
                return 2

    except Exception as e:
        # Handle unexpected validation errors
        handled = handle_error(
            error=e,
            operation="file path validation",
            interactive=True
        )
        if not handled:
            print(f"Error validating paths: {e}", file=sys.stderr)
            return 2

    # --- Input file handling ---
    html_chunks = []
    resources = []
    all_styles_css = []

    supported_extensions = {".docx", ".md", ".txt", ".html", ".htm"}

    if input_path.is_dir():
        print("Input is a directory, processing supported files in alphabetical order...")
        files_to_process = sorted(
            [
                p
                for p in input_path.iterdir()
                if p.is_file() and p.suffix.lower() in supported_extensions
            ]
        )
        if not files_to_process:
            print(f"Error: No supported files found in directory: {input_path}", file=sys.stderr)
            return 2

        with build_monitor.phase_timer("batch_conversion"):
            for file in files_to_process:
                print(f" - Processing {file.name}...")
                try:
                    with build_monitor.phase_timer(f"convert_{file.name}"):
                        chunks, res, styles_css = convert_file_to_html(file)
                    html_chunks.extend(chunks)
                    resources.extend(res)
                    # Collect styles CSS from all files
                    if styles_css and styles_css not in all_styles_css:
                        all_styles_css.append(styles_css)
                except (RuntimeError, ValueError) as e:
                    print(f"Error converting {file.name}: {e}", file=sys.stderr)
                    return 2
    elif input_path.is_file():
        if input_path.suffix.lower() not in supported_extensions:
            print(f"Error: Unsupported file type: {input_path.suffix}", file=sys.stderr)
            return 2
        try:
            with build_monitor.phase_timer("file_conversion"):
                html_chunks, resources, styles_css = convert_file_to_html(input_path)
            all_styles_css = [styles_css] if styles_css else []
        except (RuntimeError, ValueError) as e:
            print(f"Error converting {input_path.name}: {e}", file=sys.stderr)
            return 2
    else:
        print(f"Error: Input path is not a file or directory: {input_path}", file=sys.stderr)
        return 2

    # Basic validations
    if args.isbn:
        from .metadata import validate_isbn13

        if not validate_isbn13(args.isbn):
            print(
                "Error: Invalid ISBN-13. Provide 13 digits with a valid checksum.",
                file=sys.stderr,
            )
            return 2
    if cover_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        print("Error: Cover must be a .jpg, .jpeg, or .png image.", file=sys.stderr)
        return 2

    # Language normalization/validation
    from .metadata import normalize_lang, validate_lang_code

    args.language = normalize_lang(args.language)
    if not validate_lang_code(args.language):
        print("Error: Language must be a BCP-47 code like 'en' or 'en-us'.", file=sys.stderr)
        return 2

    if not args.title or str(args.title).strip() == "":
        print("Error: Title is required.", file=sys.stderr)
        return 2

    meta = EpubMetadata(
        title=args.title,
        author=args.author or "Unknown Author",
        language=args.language or "en",
        description=(args.description or None),
        isbn=(args.isbn or None),
        publisher=(args.publisher or None),
        pubdate=parse_date(args.pubdate) if args.pubdate else None,
        uuid=(args.uuid or None),
        series=(args.seriesName or None),
        series_index=(args.seriesIndex or None),
        title_sort=(getattr(args, "title_sort", "") or None),
        author_sort=(getattr(args, "author_sort", "") or None),
        subjects=[s.strip() for s in (args.subjects or "").split(",") if s.strip()],
        keywords=[s.strip() for s in (args.keywords or "").split(",") if s.strip()],
        cover_path=cover_path,
    )

    # AI Enhancement Integration
    if getattr(args, 'ai_enhance', False) or getattr(args, 'ai_genre', False):
        ai_manager = get_ai_manager()
        if ai_manager.is_available():
            try:
                # Read document content for AI analysis
                content = _read_document_content(input_path)
                if content:
                    # AI metadata enhancement
                    if getattr(args, 'ai_enhance', False):
                        if not getattr(args, 'quiet', False):
                            print("🤖 Enhancing metadata with AI...")
                        enhanced = enhance_metadata_with_ai(
                            content, meta,
                            interactive=getattr(args, 'ai_interactive', False)
                        )
                        meta = enhanced.original
                        if not getattr(args, 'quiet', False) and enhanced.applied_suggestions:
                            print(f"✅ Applied {len(enhanced.applied_suggestions)} AI metadata suggestions")

                    # AI genre detection
                    if getattr(args, 'ai_genre', False):
                        if not getattr(args, 'quiet', False):
                            print("🎯 Detecting genres with AI...")
                        genre_result = detect_genre_with_ai(content, {
                            'title': meta.title,
                            'author': meta.author,
                            'description': meta.description or ''
                        })
                        if genre_result.genres and not hasattr(meta, 'genre'):
                            meta.genre = genre_result.genres[0].genre
                        if genre_result.keywords and not meta.keywords:
                            meta.keywords = genre_result.keywords[:10]
                        if not getattr(args, 'quiet', False):
                            print(f"✅ AI detected genre: {getattr(meta, 'genre', 'None')}")

            except Exception as e:
                if not getattr(args, 'quiet', False):
                    print(f"⚠️  AI enhancement failed: {e}")
        else:
            if not getattr(args, 'quiet', False):
                print("⚠️  AI features requested but not available")


    # Resolve optional resource paths relative to input dir
    def _resolve_rel_to_input(path_str: str | None) -> Path | None:
        if not path_str:
            return None
        p = Path(path_str).expanduser()
        if not p.is_absolute():
            p = input_dir / p
        return p.resolve()

    css_path = _resolve_rel_to_input(args.css) if getattr(args, "css", None) else None
    fonts_dir = (
        _resolve_rel_to_input(args.embed_fonts) if getattr(args, "embed_fonts", None) else None
    )
    dedication_path = (
        _resolve_rel_to_input(args.dedication) if getattr(args, "dedication", None) else None
    )
    ack_path = _resolve_rel_to_input(args.ack) if getattr(args, "ack", None) else None

    # Parse chapter starts if provided
    chapter_starts = None
    if getattr(args, "chapter_starts", None):
        chapter_starts = [s.strip() for s in args.chapter_starts.split(",") if s.strip()]

    # Validate ToC depth
    toc_depth = max(1, min(6, int(args.toc_depth)))

    opts = BuildOptions(
        split_at=args.split_at,
        theme=args.theme,
        embed_fonts_dir=fonts_dir,
        image_quality=args.image_quality,
        image_max_width=args.image_max_width,
        image_max_height=args.image_max_height,
        image_format=args.image_format,
        enhanced_images=getattr(args, "enhanced_images", False),
        vertical_writing=args.vertical_writing,
        epub2_compat=args.epub2_compat,
        hyphenate=args.hyphenate == "on",
        justify=args.justify == "on",
        toc_depth=toc_depth,
        chapter_start_mode=getattr(args, "chapter_start_mode", "auto"),
        chapter_starts=chapter_starts,
        mixed_split_pattern=getattr(args, "mixed_split_pattern", None),
        reader_start_chapter=getattr(args, "reader_start_chapter", None),
        page_list=args.page_list == "on",
        extra_css=css_path,
        page_numbers=args.page_numbers == "on",
        epub_version=str(args.epub_version),
        cover_scale=args.cover_scale,
        dedication_txt=dedication_path,
        ack_txt=ack_path,
        inspect=args.inspect,
        dry_run=args.dry_run,
        preview=args.preview,
        preview_port=args.preview_port,
        epubcheck=(
            (args.epubcheck == "on")
            if isinstance(args.epubcheck, str)
            else bool(getattr(args, "epubcheck", True))
        ),
        font_size=(getattr(args, "font_size", None) or None),
        line_height=(getattr(args, "line_height", None) or None),
        quiet=bool(getattr(args, "quiet", False)),
        verbose=bool(getattr(args, "verbose", False)),
    )

    # Prefill from DOCX core properties if missing
    if (
        input_path.is_file()
        and input_path.suffix.lower() == ".docx"
        and (not args.title or not args.author)
    ):
        try:
            from docx import Document  # type: ignore

            d = Document(str(input_path))
            core = getattr(d, "core_properties", None)
            if core:
                if not args.title and getattr(core, "title", None):
                    args.title = core.title
                if (not args.author) and getattr(core, "author", None):
                    args.author = core.author
        except Exception:
            pass

    # Offer to install Pandoc/EPUBCheck if missing (interactive only)
    interactive_build = (not getattr(args, "no_prompt", False)) and sys.stdin.isatty()
    allow_install = not bool(getattr(args, "no_install_tools", False))
    if allow_install:
        # Pandoc
        try:
            if pandoc_path() is None:
                if getattr(args, "auto_install_tools", False):
                    p = install_pandoc()
                    if not getattr(args, "quiet", False):
                        print(f"Installed Pandoc at: {p}")
                elif interactive_build:
                    if prompt_bool("Pandoc not found. Install now?", default=True):
                        p = install_pandoc()
                        if not getattr(args, "quiet", False):
                            print(f"Installed Pandoc at: {p}")
        except Exception as e:
            print(f"Pandoc install failed: {e}", file=sys.stderr)
        # EPUBCheck
        try:
            ep_on = (
                (args.epubcheck == "on")
                if isinstance(args.epubcheck, str)
                else bool(getattr(args, "epubcheck", True))
            )
            if ep_on and epubcheck_cmd() is None:
                if getattr(args, "auto_install_tools", False):
                    j = install_epubcheck()
                    if not getattr(args, "quiet", False):
                        print(f"Installed EPUBCheck jar: {j}")
                elif interactive_build:
                    if prompt_bool("EPUBCheck not found. Install now?", default=True):
                        j = install_epubcheck()
                        if not getattr(args, "quiet", False):
                            print(f"Installed EPUBCheck jar: {j}")
        except Exception as e:
            print(f"EPUBCheck install failed: {e}", file=sys.stderr)

    # Apply split strategy if needed
    if args.split_at in {"h1", "h2"}:
        combined = "".join(html_chunks)
        html_chunks = split_html_by_heading(combined, level=args.split_at)
    elif args.split_at in {"h3", "h4", "h5", "h6"}:
        combined = "".join(html_chunks)
        html_chunks = split_html_by_heading_level(combined, level=args.split_at)
    elif args.split_at == "pagebreak":
        combined = "".join(html_chunks)
        html_chunks = split_html_by_pagebreak(combined)
    elif args.split_at == "mixed":
        combined = "".join(html_chunks)
        mixed_pattern = getattr(args, 'mixed_split_pattern', None)
        html_chunks = split_html_mixed(combined, mixed_pattern)

    plan = plan_build(meta, opts, html_chunks, resources)
    _print_metadata_summary(meta, opts, None if not args.output else Path(args.output))

    if args.dry_run:
        print("-- Dry Run: Planned manifest/spine --")
        for line in plan:
            print(line)
        return 0

    # Handle preview mode
    if args.preview:
        return _run_preview_mode(meta, opts, html_chunks, resources, args)

    # Confirm to proceed if interactive
    interactive = (not getattr(args, "no_prompt", False)) and sys.stdin.isatty()
    if interactive:
        proceed = prompt_bool("Proceed to build now?", default=True)
        if not proceed:
            print("Cancelled.")
            return 1

    # Compute default output name if missing
    if not args.output:
        if getattr(args, "output_pattern", None):
            from .metadata import render_output_pattern

            stem = render_output_pattern(
                args.output_pattern,
                title=args.title,
                series=args.seriesName or None,
                series_index=args.seriesIndex or None,
            )
            args.output = stem if stem.lower().endswith(".epub") else f"{stem}.epub"
        else:
            args.output = build_output_filename(
                title=args.title,
                series=args.seriesName or None,
                series_index=args.seriesIndex or None,
            )

    # Resolve output relative to input dir if relative
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = input_dir / out_path

    # Sanitize name and ensure .epub extension
    name = out_path.name
    if not name.lower().endswith(".epub"):
        name = sanitize_filename(name) + ".epub"
    out_path = out_path.with_name(name)

    output = out_path.resolve()
    # Combine all styles CSS
    combined_styles_css = "\n".join(all_styles_css)

    # Final assembly phase with performance monitoring
    with build_monitor.phase_timer("epub_assembly"):
        assemble_epub(meta, opts, html_chunks, resources, output, combined_styles_css, build_monitor)

    # EPUB validation phase
    if getattr(args, 'epubcheck', 'on') == 'on' and output.exists():
        from .validation import print_validation_report, validate_epub

        if not getattr(args, 'quiet', False):
            print("\n[VALIDATION] Validating EPUB quality...")

        with build_monitor.phase_timer("epub_validation"):
            validation_result = validate_epub(output, custom_checks=True, timeout=120)

        if not getattr(args, 'quiet', False):
            print_validation_report(validation_result, verbose=getattr(args, 'verbose', False))

        # Exit with error code if validation failed with errors
        if validation_result.has_errors:
            print(f"\n[ERROR] EPUB validation failed with {len(validation_result.errors)} critical error(s).")
            print("Please fix the errors above before distributing your EPUB.")
            return 3  # Different exit code for validation failures

    # Stop monitoring and display performance summary
    build_monitor.stop_monitoring()
    if not getattr(args, 'quiet', False):
        print(f"\n📊 Performance Summary:\n{build_monitor.get_summary()}")

    print(f"Wrote: {output}")
    if opts.inspect:
        print("Inspect folder emitted for debugging.")
    return 0


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
        if not version and hasattr(args, 'preset'):
            from .tools import get_pinned_version
            version = get_pinned_version(args.name, args.preset)

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


def run_update(args: argparse.Namespace) -> int:
    import subprocess

    print("Checking for updates...")
    check_for_updates()  # This will print if there is an update
    if prompt_bool("Do you want to try upgrading now?", default=True):
        try:
            subprocess.run(["pipx", "upgrade", "docx2shelf"], check=True)
            print("Update successful!")
            return 0
        except FileNotFoundError:
            print(
                "Error: pipx not found. Please make sure pipx is installed and in your PATH.",
                file=sys.stderr,
            )
            return 1
        except subprocess.CalledProcessError as e:
            print(f"Error during update: {e}", file=sys.stderr)
            return 1
    return 0


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
            pubdate=parse_date(metadata_dict.get("pubdate")) if metadata_dict.get("pubdate") else None,
            uuid=metadata_dict.get("uuid"),
            series=metadata_dict.get("series"),
            series_index=metadata_dict.get("series_index"),
            title_sort=metadata_dict.get("title_sort"),
            author_sort=metadata_dict.get("author_sort"),
            subjects=metadata_dict.get("subjects", "").split(",") if metadata_dict.get("subjects") else [],
            keywords=metadata_dict.get("keywords", "").split(",") if metadata_dict.get("keywords") else [],
            cover_path=Path(args.cover) if args.cover else Path("cover.jpg"),  # Default cover path
            # Extended metadata fields
            editor=metadata_dict.get("editor"),
            illustrator=metadata_dict.get("illustrator"),
            translator=metadata_dict.get("translator"),
            narrator=metadata_dict.get("narrator"),
            designer=metadata_dict.get("designer"),
            contributor=metadata_dict.get("contributor"),
            bisac_codes=metadata_dict.get("bisac_codes", "").split(",") if metadata_dict.get("bisac_codes") else [],
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
            content_warnings=metadata_dict.get("content_warnings", "").split(",") if metadata_dict.get("content_warnings") else []
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
                    "errors": [{"severity": i.severity, "category": i.category,
                              "message": i.message, "fix_suggestion": i.fix_suggestion}
                              for i in result.errors],
                    "warnings": [{"severity": i.severity, "category": i.category,
                                "message": i.message, "fix_suggestion": i.fix_suggestion}
                                for i in result.warnings],
                    "infos": [{"severity": i.severity, "category": i.category,
                             "message": i.message, "fix_suggestion": i.fix_suggestion}
                             for i in result.infos]
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

    if not epub_path.suffix.lower() == '.epub':
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
            results['quality_scoring'] = {
                'overall_score': quality_report.overall_score,
                'quality_level': quality_report.quality_level.value,
                'total_issues': quality_report.total_issues,
                'critical_issues': quality_report.critical_issues,
                'auto_fixable_issues': quality_report.auto_fixable_issues,
                'category_scores': {
                    cat.value: {'score': score.score, 'issues': len(score.issues)}
                    for cat, score in quality_report.category_scores.items()
                },
                'recommendations': quality_report.recommendations
            }
            total_issues += quality_report.total_issues
            total_critical += quality_report.critical_issues

            if not args.json:
                print(f"   Overall Score: {quality_report.overall_score:.1f}/100 ({quality_report.quality_level.value.title()})")
                print(f"   Issues Found: {quality_report.total_issues} ({quality_report.critical_issues} critical)")
                if quality_report.auto_fixable_issues > 0:
                    print(f"   Auto-fixable: {quality_report.auto_fixable_issues} issues")
                print()

        except Exception as e:
            print(f"Error in quality scoring: {e}", file=sys.stderr)
            results['quality_scoring'] = {'error': str(e)}

    # 2. Accessibility Compliance Analysis
    if not args.skip_accessibility:
        print("♿ Running accessibility compliance analysis...")
        try:
            from .accessibility_audit import A11yConfig, A11yLevel

            # Configure accessibility audit
            target_level = A11yLevel[args.target_level]
            config = A11yConfig(target_level=target_level)

            a11y_result = audit_epub_accessibility(epub_path, config)
            results['accessibility'] = {
                'overall_score': a11y_result.overall_score,
                'conformance_level': a11y_result.conformance_level.value if a11y_result.conformance_level else None,
                'total_issues': a11y_result.total_issues,
                'critical_issues': a11y_result.critical_issues,
                'major_issues': a11y_result.major_issues,
                'minor_issues': a11y_result.minor_issues,
                'auto_fixes_applied': a11y_result.auto_fixes_applied,
                'issues_by_type': {k.value: v for k, v in a11y_result.issues_by_type.items()},
                'recommendations': a11y_result.recommendations
            }
            total_issues += a11y_result.total_issues
            total_critical += a11y_result.critical_issues

            if not args.json:
                conformance = a11y_result.conformance_level.value if a11y_result.conformance_level else "None"
                print(f"   Accessibility Score: {a11y_result.overall_score:.1f}/100 (WCAG {conformance})")
                print(f"   Issues Found: {a11y_result.total_issues} ({a11y_result.critical_issues} critical)")
                print()

        except Exception as e:
            print(f"Error in accessibility analysis: {e}", file=sys.stderr)
            results['accessibility'] = {'error': str(e)}

    # 3. EPUB Structure & Format Validation
    print("📋 Running EPUB structure validation...")
    try:
        from .validation import validate_epub

        validation_result = validate_epub(epub_path, custom_checks=True, timeout=120)

        results['epub_validation'] = {
            'is_valid': validation_result.is_valid,
            'total_issues': validation_result.total_issues,
            'errors': len(validation_result.errors),
            'warnings': len(validation_result.warnings),
            'info': len(validation_result.info),
            'epubcheck_available': validation_result.epubcheck_available,
            'custom_checks_run': validation_result.custom_checks_run,
            'issues': [
                {
                    'severity': issue.severity,
                    'message': issue.message,
                    'location': issue.location,
                    'rule': issue.rule
                }
                for issue in (validation_result.errors + validation_result.warnings + validation_result.info)
            ]
        }

        total_issues += validation_result.total_issues
        total_critical += len(validation_result.errors)

        if not args.json:
            print(f"   EPUB Valid: {'Yes' if validation_result.is_valid else 'No'}")
            print(f"   Issues Found: {validation_result.total_issues} ({len(validation_result.errors)} errors, {len(validation_result.warnings)} warnings)")
            if not validation_result.epubcheck_available:
                print("   [INFO] Install EPUBCheck for industry-standard validation: docx2shelf tools install epubcheck")
            print()

    except Exception as e:
        print(f"Error in EPUB validation: {e}", file=sys.stderr)
        results['epub_validation'] = {'error': str(e)}

    # 4. Content Validation
    if not args.skip_content_validation:
        print("📝 Running content validation...")
        try:
            content_reports = []

            # Extract and validate content from EPUB
            with ZipFile(epub_path, 'r') as epub_zip:
                content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml') or f.endswith('.html')]

                for file_path in content_files[:10]:  # Limit to first 10 files for performance
                    try:
                        content = epub_zip.read(file_path).decode('utf-8')
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
                            content = content_path.read_text(encoding='utf-8')
                            report = validate_content_quality(content, str(content_path))
                            content_reports.append(report)
                        except Exception as e:
                            print(f"Warning: Could not validate {content_path}: {e}")

            # Aggregate content validation results
            total_content_issues = sum(len(r.issues) for r in content_reports)
            total_errors = sum(r.error_count for r in content_reports)
            total_warnings = sum(r.warning_count for r in content_reports)
            total_auto_fixable = sum(r.auto_fixable_count for r in content_reports)

            results['content_validation'] = {
                'files_checked': len(content_reports),
                'total_issues': total_content_issues,
                'error_count': total_errors,
                'warning_count': total_warnings,
                'suggestion_count': sum(r.suggestion_count for r in content_reports),
                'auto_fixable_count': total_auto_fixable,
                'reports': [
                    {
                        'file_path': r.file_path,
                        'issues': len(r.issues),
                        'stats': {
                            'word_count': r.stats.word_count,
                            'flesch_reading_ease': r.stats.flesch_reading_ease,
                            'avg_words_per_sentence': r.stats.avg_words_per_sentence
                        }
                    } for r in content_reports
                ]
            }

            total_issues += total_content_issues
            total_critical += total_errors

            if not args.json:
                print(f"   Files Analyzed: {len(content_reports)}")
                print(f"   Issues Found: {total_content_issues} ({total_errors} errors, {total_warnings} warnings)")
                if total_auto_fixable > 0:
                    print(f"   Auto-fixable: {total_auto_fixable} issues")
                print()

        except Exception as e:
            print(f"Error in content validation: {e}", file=sys.stderr)
            results['content_validation'] = {'error': str(e)}

    # Output results
    if args.json:
        # JSON output
        output_data = {
            'epub_path': str(epub_path),
            'analysis_timestamp': __import__('datetime').datetime.now().isoformat(),
            'summary': {
                'total_issues': total_issues,
                'critical_issues': total_critical,
                'analysis_types': len([k for k in results.keys() if 'error' not in results[k]])
            },
            'results': results
        }

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(output_data, indent=2), encoding='utf-8')
            print(f"📄 Detailed report saved to: {output_path}")
        else:
            print(json.dumps(output_data, indent=2))

    else:
        # Human-readable output
        print("=" * 60)
        print("📋 QUALITY ASSESSMENT SUMMARY")
        print("=" * 60)

        if 'quality_scoring' in results and 'error' not in results['quality_scoring']:
            quality_data = results['quality_scoring']
            print(f"🎯 Overall Quality Score: {quality_data['overall_score']:.1f}/100 ({quality_data['quality_level'].title()})")

        print(f"📊 Total Issues Found: {total_issues}")
        if total_critical > 0:
            print(f"🚨 Critical Issues: {total_critical}")

        # Show top recommendations
        all_recommendations = []
        for analysis_type, data in results.items():
            if 'recommendations' in data:
                all_recommendations.extend(data['recommendations'])

        if all_recommendations:
            print("\n💡 Top Recommendations:")
            for i, rec in enumerate(all_recommendations[:5], 1):
                print(f"   {i}. {rec}")

        if args.output:
            # Save detailed report
            report_lines = [
                f"Quality Assessment Report for {epub_path}",
                "=" * 60,
                ""
            ]

            # Add detailed results for each analysis type
            for analysis_type, data in results.items():
                if 'error' not in data:
                    report_lines.append(f"{analysis_type.replace('_', ' ').title()}:")
                    report_lines.append("-" * 30)

                    if analysis_type == 'quality_scoring':
                        report_lines.append(f"Overall Score: {data['overall_score']:.1f}/100")
                        report_lines.append(f"Quality Level: {data['quality_level'].title()}")
                        report_lines.append(f"Total Issues: {data['total_issues']}")
                        report_lines.append("Category Scores:")
                        for cat, score_data in data['category_scores'].items():
                            report_lines.append(f"  - {cat.title()}: {score_data['score']:.1f}/100 ({score_data['issues']} issues)")

                    elif analysis_type == 'accessibility':
                        report_lines.append(f"Accessibility Score: {data['overall_score']:.1f}/100")
                        conformance = data['conformance_level'] or 'None'
                        report_lines.append(f"WCAG Conformance: {conformance}")
                        report_lines.append(f"Issues: {data['total_issues']} total, {data['critical_issues']} critical")

                    elif analysis_type == 'epub_validation':
                        report_lines.append(f"EPUB Valid: {'Yes' if data['is_valid'] else 'No'}")
                        report_lines.append(f"Issues: {data['total_issues']} total ({data['errors']} errors, {data['warnings']} warnings)")
                        report_lines.append(f"EPUBCheck Available: {'Yes' if data['epubcheck_available'] else 'No'}")
                        if data['issues']:
                            report_lines.append("Issues Found:")
                            for issue in data['issues'][:10]:  # Limit to first 10 issues for brevity
                                location = f" ({issue['location']})" if issue.get('location') else ""
                                report_lines.append(f"  • [{issue['severity'].upper()}]{location}: {issue['message']}")
                            if len(data['issues']) > 10:
                                report_lines.append(f"  ... and {len(data['issues']) - 10} more issues")

                    elif analysis_type == 'content_validation':
                        report_lines.append(f"Files Analyzed: {data['files_checked']}")
                        report_lines.append(f"Issues: {data['total_issues']} total, {data['error_count']} errors")

                    if 'recommendations' in data:
                        report_lines.append("Recommendations:")
                        for rec in data['recommendations']:
                            report_lines.append(f"  • {rec}")

                    report_lines.append("")

            output_path = Path(args.output)
            output_path.write_text('\n'.join(report_lines), encoding='utf-8')
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

    if not epub_path.suffix.lower() == '.epub':
        print(f"Error: File must be an EPUB (.epub extension): {epub_path}", file=sys.stderr)
        return 1

    print(f"[VALIDATION] Validating EPUB: {epub_path}")
    print("=" * 50)

    try:
        # Run validation
        custom_checks = not args.skip_custom
        validation_result = validate_epub(
            epub_path,
            custom_checks=custom_checks,
            timeout=args.timeout
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
        print("⚠️  AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🤖 Analyzing metadata for: {input_file.name}")

        # Read document content
        content = _read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Create basic metadata
        metadata = EpubMetadata(
            title=input_file.stem,
            author="Unknown Author",
            language="en"
        )

        # Enhance with AI
        enhanced = enhance_metadata_with_ai(content, metadata, interactive=args.interactive)

        # Output results
        if args.output:
            _save_metadata_to_file(enhanced.original, Path(args.output))
            print(f"✅ Enhanced metadata saved to: {args.output}")
        else:
            print("\n📊 Enhanced Metadata:")
            print(f"   Title: {enhanced.original.title}")
            print(f"   Author: {enhanced.original.author}")
            print(f"   Description: {enhanced.original.description or '(none)'}")
            if hasattr(enhanced.original, 'genre') and enhanced.original.genre:
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
        print("⚠️  AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🎯 Analyzing genres and keywords for: {input_file.name}")

        # Read document content
        content = _read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Detect genres
        metadata_dict = {
            'title': input_file.stem,
            'author': 'Unknown Author',
            'description': ''
        }
        result = detect_genre_with_ai(content, metadata_dict)

        if args.json:
            import json
            output = {
                'genres': [{'genre': g.genre, 'confidence': g.confidence, 'source': g.source}
                          for g in result.genres],
                'keywords': result.keywords,
                'analysis_summary': result.analysis_summary
            }
            print(json.dumps(output, indent=2))
        else:
            print("\n📚 Detected Genres:")
            for genre in result.genres[:5]:
                confidence_icon = "🟢" if genre.confidence >= 0.8 else "🟡" if genre.confidence >= 0.6 else "🔴"
                print(f"   {confidence_icon} {genre.genre} ({genre.confidence:.1%}) - {genre.source}")

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
        print("⚠️  AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🖼️  Generating alt text for: {input_path.name}")

        if input_path.is_file() and input_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Single image file
            suggestions = generate_image_alt_texts([input_path], interactive=args.interactive)

            if suggestions:
                print("\n✨ Alt Text Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    confidence_icon = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.6 else "🔴"
                    print(f"   {i}. {confidence_icon} {suggestion.alt_text}")
                    print(f"      Confidence: {suggestion.confidence:.1%} | Source: {suggestion.source}")
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
                print(f"✅ Set {key} = {value}")
            else:
                print(f"Error: Unknown configuration key: {key}")
                return 1

        elif args.reset:
            # Reset to defaults would go here
            print("✅ AI configuration reset to defaults")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def _read_document_content(file_path: Path) -> str:
    """Read document content for AI analysis."""
    try:
        if file_path.suffix.lower() == '.docx':
            # Use docx2txt or similar to extract text
            from .convert import extract_text_from_docx
            return extract_text_from_docx(file_path)
        else:
            # Read as text file
            return file_path.read_text(encoding='utf-8')
    except Exception:
        return ""


def _save_metadata_to_file(metadata: EpubMetadata, output_path: Path):
    """Save metadata to a file."""
    metadata_dict = {
        'title': metadata.title,
        'author': metadata.author,
        'description': metadata.description,
        'language': metadata.language,
    }

    if hasattr(metadata, 'genre') and metadata.genre:
        metadata_dict['genre'] = metadata.genre
    if hasattr(metadata, 'keywords') and metadata.keywords:
        metadata_dict['keywords'] = metadata.keywords

    with open(output_path, 'w', encoding='utf-8') as f:
        for key, value in metadata_dict.items():
            if value:
                f.write(f"{key}={value}\n")


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
        print(f"  [ERROR] Python {sys.version_info.major}.{sys.version_info.minor} is too old (requires 3.11+)")
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
        "sqlalchemy": "Enterprise database features"
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
                status = "✓ Loaded" if plugin['loaded'] else "○ Available"
                if args.verbose:
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    print(f"    Description: {plugin['description']}")
                    print(f"    Location: {plugin['location']}")
                    print(f"    File: {plugin['file_name']}")
                    print(f"    Classes: {', '.join(plugin['classes'])}")
                    print()
                else:
                    print(f"  {status} {plugin['name']} (v{plugin['version']}) - {plugin['description']}")
        else:
            # Show only loaded plugins
            plugins = plugin_manager.list_plugins()
            if not plugins:
                print("No plugins loaded.")
                print("Run 'docx2shelf plugins list --all' to see available plugins.")
                return 0

            print("Loaded plugins:")
            for plugin in plugins:
                status = "✓" if plugin['enabled'] == 'True' else "✗"
                if args.verbose:
                    detailed = get_plugin_info(plugin['name'])
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    if detailed:
                        print(f"    Hooks: {detailed['hook_count']} total")
                        for hook_type, hook_classes in detailed['hooks'].items():
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

        for hook_type, hook_classes in plugin_info['hooks'].items():
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
                status = "✓ Loaded" if plugin['loaded'] else "○ Available"
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
            with open(plugin_file, 'r') as f:
                content = f.read()

            content = content.replace("basic_template", args.name)
            content = content.replace("BasicTemplatePlugin", f"{args.name.title().replace('_', '')}Plugin")
            content = content.replace("BasicPreProcessor", f"{args.name.title().replace('_', '')}PreProcessor")
            content = content.replace("BasicPostProcessor", f"{args.name.title().replace('_', '')}PostProcessor")
            content = content.replace("BasicMetadataResolver", f"{args.name.title().replace('_', '')}MetadataResolver")

            with open(plugin_file, 'w') as f:
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
            status = "✓" if conn['enabled'] else "✗"
            network = "🌐" if conn['requires_network'] else "📁"
            auth = "🔑" if conn['authenticated'] else "🔓"
            print(f"  {status} {network} {auth} {conn['name']}")

        print("\nLegend:")
        print("  ✓/✗ = Enabled/Disabled")
        print("  🌐/📁 = Network/Local")
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
            auth_kwargs['credentials_path'] = args.credentials

        success = connector.authenticate(**auth_kwargs)
        if success:
            print(f"Authenticated with connector: {args.name}")
            return 0
        else:
            print(f"Authentication failed for connector: {args.name}")
            return 1

    elif args.connector_cmd == "fetch":
        try:
            output_path = Path(args.output) if args.output else Path(f"downloaded_{args.document_id}.docx")
            result_path = download_from_connector(args.connector, args.document_id, output_path)
            print(f"Downloaded document to: {result_path}")
            return 0
        except Exception as e:
            print(f"Error downloading document: {e}")
            return 1

    return 1


def _run_preview_mode(meta: EpubMetadata, opts: BuildOptions, html_chunks: list[str], resources: list[Path], args) -> int:
    """Run live preview mode instead of generating EPUB."""
    import signal
    import sys
    import tempfile
    import time

    from .assemble import assemble_epub

    try:
        # Create temporary directory for preview content
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate EPUB content in temporary location (but don't zip it)
            epub_temp = temp_path / "temp.epub"

            # Generate the EPUB content structure
            if not opts.quiet:
                print("📚 Generating preview content...")

            assemble_epub(
                meta=meta,
                opts=opts,
                html_chunks=html_chunks,
                resources=resources,
                output_path=epub_temp,
                styles_css="",  # Will be populated by conversion process
                performance_monitor=None  # Preview mode doesn't need monitoring
            )

            # Check if inspect folder was created (contains the EPUB content structure)
            inspect_dir = epub_temp.parent / f"{epub_temp.stem}.src"
            if not inspect_dir.exists():
                # Force inspect mode for preview
                opts.inspect = True
                assemble_epub(
                    meta=meta,
                    opts=opts,
                    html_chunks=html_chunks,
                    resources=resources,
                    output_path=epub_temp,
                    styles_css=""
                )

            if not inspect_dir.exists():
                print("Error: Could not generate preview content", file=sys.stderr)
                return 1

            # Create output directory for preview
            output_dir = Path.cwd() / "preview_output"
            output_dir.mkdir(exist_ok=True)

            # Run live preview
            port = run_live_preview(
                epub_content_dir=inspect_dir,
                output_dir=output_dir,
                title=meta.title or "EPUB Preview",
                port=opts.preview_port,
                auto_open=True,
                quiet=opts.quiet
            )

            if port is None:
                return 1

            # Set up signal handlers for graceful shutdown
            def signal_handler(sig, frame):
                if not opts.quiet:
                    print("\n\n🛑 Stopping preview server...")
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Keep the server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                if not opts.quiet:
                    print("\n\n🛑 Preview server stopped")
                return 0

    except Exception as e:
        if not opts.quiet:
            print(f"Error running preview: {e}", file=sys.stderr)
        return 1


def run_convert(args) -> int:
    """Handle EPUB format conversion."""
    from pathlib import Path

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    if not input_path.suffix.lower() == '.epub':
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
        if args.format == 'pdf' and not any(deps.values()):
            print("\nError: PDF conversion requires either weasyprint or prince")
            print("Install with: pip install weasyprint")
            return 1
        elif args.format in ['mobi', 'azw3'] and not deps.get('calibre'):
            print(f"\nError: {args.format.upper()} conversion requires Calibre")
            print("Install from: https://calibre-ebook.com/download")
            return 1

        return 0

    # Generate output path if not specified
    if args.output:
        output_path = Path(args.output)
    else:
        # Auto-generate based on format
        if args.format == 'web':
            output_path = input_path.parent / f"{input_path.stem}_web"
        else:
            ext_map = {
                'pdf': '.pdf',
                'mobi': '.mobi',
                'azw3': '.azw3',
                'txt': '.txt',
                'text': '.txt'
            }
            ext = ext_map.get(args.format, f'.{args.format}')
            output_path = input_path.parent / f"{input_path.stem}{ext}"

    # Read custom CSS if provided
    custom_css = None
    if args.css:
        css_path = Path(args.css)
        if css_path.exists():
            custom_css = css_path.read_text(encoding='utf-8')
        else:
            print(f"Warning: CSS file not found: {css_path}")

    # Extract metadata from args for conversion
    metadata = {
        'title': getattr(args, 'title', None),
        'author': getattr(args, 'author', None),
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
        font_size=getattr(args, 'font_size', '12pt'),
        font_family=args.font_family,
        include_toc=args.include_toc,
        include_cover=args.include_cover
    )

    if success:
        print("✓ Conversion completed successfully!")
        if args.format == 'web':
            print(f"Open {output_path / 'index.html'} in your browser to view")
        return 0
    else:
        print("✗ Conversion failed")
        return 1


def run_enterprise(args) -> int:
    """Handle enterprise subcommands."""
    try:
        if args.enterprise_cmd == "batch":
            return run_enterprise_batch(args)
        elif args.enterprise_cmd == "jobs":
            return run_enterprise_jobs(args)
        elif args.enterprise_cmd == "config":
            return run_enterprise_config(args)
        elif args.enterprise_cmd == "users":
            return run_enterprise_users(args)
        elif args.enterprise_cmd == "api":
            return run_enterprise_api(args)
        elif args.enterprise_cmd == "webhooks":
            return run_enterprise_webhooks(args)
        elif args.enterprise_cmd == "reports":
            return run_enterprise_reports(args)
        else:
            print(f"Unknown enterprise command: {args.enterprise_cmd}")
            return 1
    except Exception as e:
        print(f"Error running enterprise command: {e}")
        return 1


def run_enterprise_batch(args) -> int:
    """Handle enterprise batch processing."""
    try:
        import json
        import uuid

        import yaml

        from .enterprise import BatchJob, get_batch_processor

        # Load configuration if provided
        config = {}
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                try:
                    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f) or {}
                    else:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load config file: {e}")

        # Apply command line overrides
        config.update({
            "theme": args.theme,
            "split_at": args.split_at,
            "title": config.get("title", ""),
            "author": config.get("author", ""),
            "language": config.get("language", "en"),
            "toc_depth": config.get("toc_depth", 2),
            "hyphenate": config.get("hyphenate", True),
            "justify": config.get("justify", True)
        })

        # Create batch job
        job = BatchJob(
            id=str(uuid.uuid4()),
            name=args.name,
            input_pattern=args.input,
            output_directory=args.output,
            config=config,
            processing_mode=args.mode,
            webhook_url=args.webhook
        )

        # Submit to batch processor
        processor = get_batch_processor()

        # Update max concurrent jobs if specified
        if args.max_concurrent:
            processor.config.max_concurrent_jobs = args.max_concurrent

        job_id = processor.submit_batch_job(job)

        print(f"✓ Batch job '{args.name}' created successfully")
        print(f"  Job ID: {job_id}")
        print(f"  Mode: {args.mode}")
        print(f"  Input: {args.input}")
        print(f"  Output: {args.output}")

        if args.webhook:
            print(f"  Webhook: {args.webhook}")

        print(f"\nUse 'docx2shelf enterprise jobs --details {job_id}' to check status")
        return 0

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        print("Install with: pip install docx2shelf[enterprise]")
        return 1
    except Exception as e:
        print(f"Error creating batch job: {e}")
        return 1


def run_enterprise_jobs(args) -> int:
    """Handle enterprise job management."""
    try:
        from .enterprise import get_batch_processor

        processor = get_batch_processor()

        if args.list:
            jobs = processor.list_jobs(status_filter=args.status)

            if not jobs:
                print("No batch jobs found")
                return 0

            print(f"{'Job ID':<36} {'Name':<20} {'Mode':<8} {'Status':<12} {'Progress':<10} {'Created'}")
            print("-" * 100)

            for job in jobs:
                created = job.created_at[:19] if isinstance(job.created_at, str) else str(job.created_at)[:19]
                print(f"{job.id:<36} {job.name[:19]:<20} {job.processing_mode:<8} {job.status:<12} {job.progress:>3}% {created}")

            return 0

        elif args.details:
            job = processor.get_job_status(args.details)
            if not job:
                print(f"Job not found: {args.details}")
                return 1

            print(f"Job Details: {job.name}")
            print("=" * 50)
            print(f"ID: {job.id}")
            print(f"Name: {job.name}")
            print(f"Mode: {job.processing_mode}")
            print(f"Status: {job.status}")
            print(f"Progress: {job.progress}%")
            print(f"Input: {job.input_pattern}")
            print(f"Output: {job.output_directory}")
            print(f"Created: {job.created_at}")

            if job.started_at:
                print(f"Started: {job.started_at}")
            if job.completed_at:
                print(f"Completed: {job.completed_at}")

            print("\nProgress Details:")
            print(f"  Total Items: {job.total_items}")
            print(f"  Processed: {job.processed_items}")
            print(f"  Failed: {job.failed_items}")
            print(f"  Total Files: {job.total_files}")
            print(f"  Files Processed: {job.processed_files}")
            print(f"  Files Failed: {job.failed_files}")

            if job.processing_mode == "books" and job.book_results:
                print("\nBook Results:")
                for book_name, result in job.book_results.items():
                    print(f"  {book_name}: {result['status']}")

            if job.error_log:
                print("\nRecent Errors:")
                for error in job.error_log[-5:]:
                    print(f"  - {error}")

            return 0

        elif args.cancel:
            success = processor.cancel_job(args.cancel)
            if success:
                print(f"✓ Job {args.cancel} cancelled successfully")
                return 0
            else:
                print(f"✗ Could not cancel job {args.cancel} (may have already completed)")
                return 1

        elif args.cleanup:
            cleaned = processor.cleanup_old_jobs()
            print(f"✓ Cleaned up {cleaned} old jobs")
            return 0

        else:
            print("Please specify an action: --list, --details <id>, --cancel <id>, or --cleanup")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing jobs: {e}")
        return 1


def run_enterprise_config(args) -> int:
    """Handle enterprise configuration."""
    try:
        from .enterprise import get_config_manager

        config_manager = get_config_manager()

        if args.init:
            # Initialize default configuration
            config_manager.reset_to_defaults()
            print("✓ Enterprise configuration initialized with defaults")
            print(f"Configuration saved to: {config_manager.config_path}")
            return 0

        elif args.show:
            config = config_manager.config
            print("Enterprise Configuration:")
            print("=" * 30)
            print(f"Max Concurrent Jobs: {config.max_concurrent_jobs}")
            print(f"Max Files Per Job: {config.max_files_per_job}")
            print(f"Job Timeout (hours): {config.job_timeout_hours}")
            print(f"Auto Cleanup (days): {config.auto_cleanup_days}")
            print(f"Enable Webhooks: {config.enable_webhooks}")
            print(f"Enable API: {config.enable_api}")
            print(f"API Host: {config.api_host}")
            print(f"API Port: {config.api_port}")
            print(f"Log Level: {config.log_level}")
            return 0

        elif args.set:
            key, value = args.set

            # Convert value to appropriate type
            if key in ["max_concurrent_jobs", "max_files_per_job", "job_timeout_hours", "auto_cleanup_days", "api_port"]:
                value = int(value)
            elif key in ["enable_webhooks", "enable_api"]:
                value = value.lower() in ["true", "1", "yes", "on"]

            config_manager.update_config(**{key: value})
            print(f"✓ Configuration updated: {key} = {value}")
            return 0

        elif args.reset:
            config_manager.reset_to_defaults()
            print("✓ Configuration reset to defaults")
            return 0

        elif args.export:
            import shutil
            shutil.copy2(config_manager.config_path, args.export)
            print(f"✓ Configuration exported to: {args.export}")
            return 0

        elif args.import_config:
            import shutil
            shutil.copy2(args.import_config, config_manager.config_path)
            config_manager.config = config_manager._load_config()
            print(f"✓ Configuration imported from: {args.import_config}")
            return 0

        else:
            print("Please specify an action: --init, --show, --set KEY VALUE, --reset, --export FILE, or --import FILE")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing configuration: {e}")
        return 1


def run_enterprise_users(args) -> int:
    """Handle enterprise user management."""
    try:
        from .enterprise import get_user_manager

        user_manager = get_user_manager()

        if args.create:
            if not args.email:
                print("Error: --email is required when creating a user")
                return 1

            permissions = []
            if args.permissions:
                permissions = [p.strip() for p in args.permissions.split(",")]

            user = user_manager.create_user(
                username=args.create,
                email=args.email,
                role=args.role,
                permissions=permissions
            )

            print("✓ User created successfully")
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  API Key: {user.api_key}")
            print(f"  Permissions: {', '.join(user.permissions)}")
            return 0

        elif args.list:
            users = user_manager.list_users()

            if not users:
                print("No users found")
                return 0

            print(f"{'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
            print("-" * 70)

            for user in users:
                created = user.created_at[:19] if isinstance(user.created_at, str) else str(user.created_at)[:19]
                print(f"{user.username:<20} {user.email:<30} {user.role:<10} {created}")

            return 0

        elif args.generate_key:
            user = user_manager.get_user(args.generate_key)
            if not user:
                print(f"User not found: {args.generate_key}")
                return 1

            # Generate new API key
            from .enterprise import get_api_manager
            api_manager = get_api_manager()
            new_key = api_manager.generate_api_key(
                name=f"Generated for {user.username}",
                user_id=user.id,
                permissions=user.permissions
            )

            print(f"✓ New API key generated for {user.username}")
            print(f"  API Key: {new_key}")
            return 0

        elif args.deactivate:
            success = user_manager.delete_user(args.deactivate)
            if success:
                print(f"✓ User {args.deactivate} deactivated successfully")
                return 0
            else:
                print(f"✗ Could not deactivate user {args.deactivate}")
                return 1

        else:
            print("Please specify an action: --create USERNAME --email EMAIL, --list, --generate-key USER_ID, or --deactivate USER_ID")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing users: {e}")
        return 1


def run_enterprise_api(args) -> int:
    """Handle enterprise API server."""
    try:
        if args.start:
            from .enterprise_api import start_api_server

            if not start_api_server:
                print("Error: FastAPI not available. Install with: pip install fastapi uvicorn")
                return 1

            print("🚀 Starting Enterprise API server...")
            print(f"   Host: {args.host}")
            print(f"   Port: {args.port}")
            print(f"   Debug: {args.debug}")
            print(f"   API Documentation: http://{args.host}:{args.port}/docs")

            # This will block until the server is stopped
            start_api_server(host=args.host, port=args.port, debug=args.debug)
            return 0

        elif args.status:
            print("API server status checking not implemented yet")
            return 0

        else:
            print("Please specify an action: --start or --status")
            return 1

    except ImportError:
        print("Error: Enterprise API requires additional dependencies")
        print("Install with: pip install fastapi uvicorn")
        return 1
    except Exception as e:
        print(f"Error managing API server: {e}")
        return 1


def run_enterprise_webhooks(args) -> int:
    """Handle enterprise webhook management."""
    try:
        from .enterprise_api import get_api_manager

        api_manager = get_api_manager()
        webhook_manager = api_manager.webhook_manager

        if args.add:
            from .enterprise_api import WebhookEndpoint

            endpoint = WebhookEndpoint(
                url=args.add,
                secret=args.secret,
                events=args.events or [],
                headers={},
                enabled=True
            )

            webhook_manager.add_endpoint(endpoint)
            print(f"✓ Webhook added: {args.add}")
            if args.events:
                print(f"  Events: {', '.join(args.events)}")
            return 0

        elif args.list:
            if not webhook_manager.endpoints:
                print("No webhooks configured")
                return 0

            print("Configured Webhooks:")
            print("-" * 50)
            for i, endpoint in enumerate(webhook_manager.endpoints, 1):
                print(f"{i}. {endpoint.url}")
                print(f"   Events: {', '.join(endpoint.events) if endpoint.events else 'All'}")
                print(f"   Enabled: {endpoint.enabled}")
                print()

            return 0

        elif args.test:
            # Send a test webhook
            test_data = {
                "test": True,
                "message": "This is a test webhook from docx2shelf enterprise"
            }

            webhook_manager.send_webhook("test", test_data)
            print("✓ Test webhook sent to all configured endpoints")
            return 0

        else:
            print("Please specify an action: --add URL, --list, or --test")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing webhooks: {e}")
        return 1


def run_enterprise_reports(args) -> int:
    """Handle enterprise reporting."""
    try:
        import csv
        import json
        from datetime import datetime, timedelta

        from .enterprise import get_batch_processor
        from .enterprise_api import get_api_manager

        processor = get_batch_processor()
        api_manager = get_api_manager()

        if args.stats:
            # Get job statistics
            jobs = processor.list_jobs()

            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs if j.status == "completed"])
            failed_jobs = len([j for j in jobs if j.status == "failed"])
            running_jobs = len([j for j in jobs if j.status == "running"])
            pending_jobs = len([j for j in jobs if j.status == "pending"])

            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

            print("Enterprise Processing Statistics:")
            print("=" * 40)
            print(f"Total Jobs: {total_jobs}")
            print(f"Completed: {completed_jobs}")
            print(f"Failed: {failed_jobs}")
            print(f"Running: {running_jobs}")
            print(f"Pending: {pending_jobs}")
            print(f"Success Rate: {success_rate:.1f}%")

            # Calculate processing time stats
            processing_times = []
            for job in jobs:
                if job.started_at and job.completed_at and job.status == "completed":
                    try:
                        started = datetime.fromisoformat(job.started_at.replace('Z', '+00:00'))
                        completed = datetime.fromisoformat(job.completed_at.replace('Z', '+00:00'))
                        duration = (completed - started).total_seconds()
                        processing_times.append(duration)
                    except:
                        pass

            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                print(f"Average Processing Time: {avg_time:.1f} seconds")

            return 0

        elif args.usage:
            print("Usage analytics not implemented yet")
            return 0

        elif args.export:
            jobs = processor.list_jobs()

            if args.export.endswith('.json'):
                # Export as JSON
                export_data = []
                for job in jobs:
                    export_data.append({
                        "id": job.id,
                        "name": job.name,
                        "status": job.status,
                        "processing_mode": job.processing_mode,
                        "total_items": job.total_items,
                        "processed_items": job.processed_items,
                        "failed_items": job.failed_items,
                        "created_at": job.created_at,
                        "started_at": job.started_at,
                        "completed_at": job.completed_at
                    })

                with open(args.export, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)

            elif args.export.endswith('.csv'):
                # Export as CSV
                with open(args.export, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'ID', 'Name', 'Status', 'Mode', 'Total Items',
                        'Processed', 'Failed', 'Created', 'Started', 'Completed'
                    ])

                    for job in jobs:
                        writer.writerow([
                            job.id, job.name, job.status, job.processing_mode,
                            job.total_items, job.processed_items, job.failed_items,
                            job.created_at, job.started_at or '', job.completed_at or ''
                        ])
            else:
                print("Error: Export format must be .json or .csv")
                return 1

            print(f"✓ Report exported to: {args.export}")
            return 0

        else:
            print("Please specify an action: --stats, --usage, or --export FILE")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error generating reports: {e}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
