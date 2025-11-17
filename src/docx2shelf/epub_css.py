"""EPUB CSS and theme processing.

This module handles all CSS-related functionality for EPUB generation including:
- Theme CSS loading and discovery
- Font size, line height, and typography options
- Image and cover scaling CSS
- Page number counters
- Language-specific CSS
- EPUB 2 compatibility mode
- Store profile optimizations
- User custom CSS
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from .language import generate_language_css
from .metadata import BuildOptions


def _generate_epub2_compat_css() -> str:
    """Generate CSS rules for EPUB 2 compatibility mode.

    Returns:
        str: CSS rules that enforce EPUB 2 constraints by removing
             modern CSS features that may not be supported.
    """
    return """
/* EPUB 2 compatibility constraints */
/* Remove modern CSS features that may not be supported */
body {
    /* Avoid CSS Grid and Flexbox */
    display: block !important;
}

/* Simpler font stacks for better compatibility */
h1, h2, h3, h4, h5, h6 {
    font-family: serif !important;
}

/* Avoid advanced selectors and properties */
* {
    /* Remove CSS transforms and animations */
    transform: none !important;
    transition: none !important;
    animation: none !important;

    /* Remove modern layout properties */
    display: inline, block, inline-block, list-item, table, table-cell !important;
}

/* Conservative image sizing */
img {
    max-width: 100% !important;
    height: auto !important;
    /* Remove object-fit and other modern properties */
    object-fit: initial !important;
}

/* Simple table styling */
table {
    border-collapse: collapse !important;
    width: 100% !important;
}

/* Conservative text formatting */
p {
    /* Avoid advanced text properties */
    text-overflow: clip !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/* Remove advanced pseudo-elements and selectors */
::before, ::after {
    content: none !important;
}

/* Avoid CSS counters and generated content */
ol, ul {
    list-style-type: decimal !important;
}

ul {
    list-style-type: disc !important;
}
"""


def load_theme_css(
    theme: str,
    extra_css: Path | None,
    opts: BuildOptions,
    styles_css: str = "",
    language: str = "en",
) -> bytes:
    """Load and compile all CSS for the EPUB.

    This function loads the base theme CSS and applies various customizations
    including typography options, language-specific styles, EPUB 2 compatibility,
    store profile optimizations, and user custom CSS.

    Args:
        theme: Name of the theme to use (serif, sans, printlike, etc.)
        extra_css: Optional path to user's custom CSS file
        opts: BuildOptions with CSS customization settings
        styles_css: Additional CSS from styles.json
        language: Language code for language-specific CSS (default: "en")

    Returns:
        bytes: Complete compiled CSS as UTF-8 encoded bytes
    """
    # Load theme CSS using the theme discovery system
    css = ""
    try:
        from .themes import get_theme_css_path, validate_theme

        if validate_theme(theme):
            theme_path = get_theme_css_path(theme)
            if theme_path:
                with theme_path.open("r", encoding="utf-8") as fh:
                    css = fh.read()
        else:
            # Fallback to direct file loading for backwards compatibility
            css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme}.css")
            with css_path.open("r", encoding="utf-8") as fh:
                css = fh.read()
    except Exception:
        # Final fallback - try direct file access
        try:
            css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme}.css")
            with css_path.open("r", encoding="utf-8") as fh:
                css = fh.read()
        except Exception:
            css = ""

    # Apply typography customizations
    if opts.font_size:
        css += f"\nhtml {{ font-size: {opts.font_size}; }}\n"
    if opts.line_height:
        css += f"\nhtml {{ line-height: {opts.line_height}; }}\n"
    if opts.justify:
        css += "\n" + "p { text-align: justify; }\n"
    if not opts.hyphenate:
        css += "\n" + "html { hyphens: manual; }\n"

    # Ensure images fit viewport and preserve aspect ratio
    css += "\nimg { max-width: 100%; height: auto; }\n"

    # Cover image scaling options
    if opts.cover_scale == "contain":
        css += "\nimg[alt='Cover'] { max-width: 100%; height: auto; }\n"
    elif opts.cover_scale == "cover":
        css += (
            "\n/* 'cover' scaling hint; support varies across readers */\n"
            "img[alt='Cover'] { width: 100%; height: auto; }\n"
        )

    # Page number counters (informational)
    if opts.page_numbers:
        css += (
            "\n/* page number counters on h1/h2 (informational) */\n"
            "h1::before, h2::before { counter-increment: page; content: counter(page) '\\a0'; }\n"
        )

    # Add styles from styles.json
    if styles_css:
        css += "\n/* styles from styles.json */\n" + styles_css

    # Add language-specific CSS
    language_css = generate_language_css(language, opts.vertical_writing)
    if language_css:
        css += "\n/* language-specific styles */\n" + language_css

    # Add EPUB 2 compatibility CSS if enabled
    if opts.epub2_compat:
        epub2_css = _generate_epub2_compat_css()
        css += "\n/* EPUB 2 compatibility styles */\n" + epub2_css

    # Add store profile CSS if specified
    if opts.store_profile_css:
        css += "\n/* store profile optimizations */\n" + opts.store_profile_css

    # Add user custom CSS
    if extra_css and extra_css.exists():
        css += "\n/* user css */\n" + extra_css.read_text(encoding="utf-8")

    return css.encode("utf-8")


def setup_book_css(
    book, opts: BuildOptions, styles_css: str = "", language: str = "en"
) -> object:
    """Load CSS and create CSS item for the EPUB book.

    Args:
        book: EpubBook instance from ebooklib
        opts: BuildOptions with theme and CSS settings
        styles_css: Additional CSS from styles.json (default: "")
        language: Language code for language-specific CSS (default: "en")

    Returns:
        EpubItem: The CSS item that should be added to chapters
    """
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Load and compile CSS
    css_bytes = load_theme_css(opts.theme, opts.extra_css, opts, styles_css, language)

    # Create CSS item
    style_item = epub.EpubItem(
        uid="style_base",
        file_name="style/base.css",
        media_type="text/css",
        content=css_bytes,
    )

    # Add to book
    book.add_item(style_item)

    return style_item
