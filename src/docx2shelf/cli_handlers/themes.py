"""Theme management command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
from pathlib import Path


def run_theme_editor(args: argparse.Namespace) -> int:
    """Run the interactive theme editor."""
    from ..theme_editor import ThemeEditor

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
        from ..themes import get_theme_info, get_themes_by_genre, list_all_themes

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
        from ..path_utils import get_safe_temp_path, write_text_safe
        from ..themes import get_all_theme_names, get_theme_css_content
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

        .theme-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e1e4e8;
        }}

        .theme-title {{
            color: #2c3e50;
            font-size: 2em;
            margin: 0 0 10px 0;
        }}

        .theme-subtitle {{
            color: #666;
            font-size: 1em;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="theme-header">
            <h1 class="theme-title">{theme_name.title()} Theme</h1>
            <p class="theme-subtitle">Sample EPUB Content Preview</p>
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
