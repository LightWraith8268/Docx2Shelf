from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional

# Basic theme metadata for built-in themes (fallback)
BASIC_THEME_METADATA = {
    "serif": {
        "name": "Classic Serif",
        "description": "Traditional serif fonts for classic literature",
        "genre": "general",
        "features": ["serif", "traditional", "readable"]
    },
    "sans": {
        "name": "Modern Sans",
        "description": "Clean sans-serif fonts for contemporary works",
        "genre": "general",
        "features": ["sans-serif", "modern", "clean"]
    },
    "printlike": {
        "name": "Print-like",
        "description": "Mimics traditional print book formatting",
        "genre": "general",
        "features": ["print-style", "traditional", "formal"]
    }
}


def _get_assets_css_dir() -> Path:
    """Get the path to the assets/css directory."""
    return Path(__file__).parent / "assets" / "css"


def _parse_theme_metadata(css_content: str) -> Dict[str, str]:
    """
    Parse theme metadata from CSS comments.

    Expected format:
    /*
     * Theme Name: Theme Display Name
     * Description: Theme description
     * Genre: Fiction - Romance, Contemporary
     * Features: Feature list
     */
    """
    metadata = {}

    # Find the first comment block
    comment_match = re.search(r'/\*\s*(.*?)\s*\*/', css_content, re.DOTALL)
    if not comment_match:
        return metadata

    comment_content = comment_match.group(1)

    # Parse key-value pairs
    for line in comment_content.split('\n'):
        line = line.strip()
        if line.startswith('*'):
            line = line[1:].strip()

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_').replace('-', '_')
            value = value.strip()
            if key and value:
                metadata[key] = value

    return metadata


def _discover_themes() -> Dict[str, Dict]:
    """
    Discover all available themes by scanning the assets/css directory.

    Returns:
        Dict mapping theme name to theme metadata
    """
    themes = {}
    css_dir = _get_assets_css_dir()

    if not css_dir.exists():
        return BASIC_THEME_METADATA.copy()

    for css_file in css_dir.glob("*.css"):
        theme_name = css_file.stem

        try:
            css_content = css_file.read_text(encoding='utf-8')
            metadata = _parse_theme_metadata(css_content)

            # Convert to the expected format
            theme_info = {
                "name": metadata.get('theme_name', theme_name.replace('_', ' ').title()),
                "description": metadata.get('description', f"CSS theme for {theme_name}"),
                "genre": metadata.get('genre', 'general').lower(),
                "features": [
                    f.strip() for f in metadata.get('features', 'standard styling').split(',')
                ]
            }

            # Add file path for reference
            theme_info['file_path'] = str(css_file)
            theme_info['file_name'] = css_file.name

            themes[theme_name] = theme_info

        except Exception:
            # If we can't read the file, skip it but don't fail
            continue

    # Always include basic themes as fallback
    for theme_name, theme_info in BASIC_THEME_METADATA.items():
        if theme_name not in themes:
            themes[theme_name] = theme_info.copy()

    return themes


# Cache for discovered themes (avoid re-scanning on every call)
_theme_cache: Optional[Dict[str, Dict]] = None


def _get_theme_metadata_dict() -> Dict[str, Dict]:
    """Get the complete theme metadata dictionary with caching."""
    global _theme_cache
    if _theme_cache is None:
        _theme_cache = _discover_themes()
    return _theme_cache


def clear_theme_cache() -> None:
    """Clear the theme cache to force re-discovery."""
    global _theme_cache
    _theme_cache = None


def get_available_themes() -> List[str]:
    """Get list of all available theme names."""
    themes = _get_theme_metadata_dict()
    return sorted(themes.keys())


def get_theme_metadata(theme_name: str) -> Optional[Dict]:
    """Get metadata for a specific theme."""
    themes = _get_theme_metadata_dict()
    return themes.get(theme_name)


def get_themes_by_genre(genre: str) -> List[str]:
    """Get themes filtered by genre."""
    themes = _get_theme_metadata_dict()
    return [
        theme for theme, meta in themes.items()
        if meta["genre"] == genre.lower() or genre.lower() == "all"
    ]


def get_theme_info(theme_name: str) -> str:
    """Get formatted theme information."""
    meta = get_theme_metadata(theme_name)
    if not meta:
        return f"Unknown theme: {theme_name}"

    features = (
        ", ".join(meta["features"]) if isinstance(meta["features"], list) else meta["features"]
    )
    return f"{meta['name']}: {meta['description']} (Features: {features})"


def list_all_themes() -> str:
    """Get formatted list of all themes with descriptions."""
    themes = _get_theme_metadata_dict()
    lines = ["Available themes:"]

    # Group by genre
    genres = {}
    for theme, meta in themes.items():
        genre = meta["genre"]
        if genre not in genres:
            genres[genre] = []
        genres[genre].append((theme, meta))

    for genre, theme_list in sorted(genres.items()):
        lines.append(f"\n{genre.title()}:")
        for theme, meta in sorted(theme_list):
            lines.append(f"  {theme}: {meta['name']} - {meta['description']}")

    return "\n".join(lines)


def validate_theme(theme_name: str) -> bool:
    """Check if a theme exists and is valid."""
    themes = _get_theme_metadata_dict()
    if theme_name not in themes:
        return False

    # Check if CSS file exists
    theme_meta = themes[theme_name]

    # If it has a file_path, check that
    if 'file_path' in theme_meta:
        return Path(theme_meta['file_path']).exists()

    # Otherwise check the assets directory
    try:
        css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme_name}.css")
        return css_path.exists()
    except Exception:
        return False


def discover_custom_themes(search_path: Path) -> Dict[str, Path]:
    """Discover custom theme CSS files in a directory."""
    custom_themes = {}
    if not search_path.exists() or not search_path.is_dir():
        return custom_themes

    for css_file in search_path.glob("*.css"):
        theme_name = css_file.stem
        # Avoid conflicts with built-in themes
        if theme_name not in BASIC_THEME_METADATA:
            custom_themes[theme_name] = css_file

    return custom_themes


def get_theme_css_path(theme_name: str, custom_theme_dir: Optional[Path] = None) -> Optional[Path]:
    """Get the path to a theme's CSS file, checking custom themes first."""
    # Check for custom theme first
    if custom_theme_dir:
        custom_themes = discover_custom_themes(custom_theme_dir)
        if theme_name in custom_themes:
            return custom_themes[theme_name]

    # Check discovered themes
    themes = _get_theme_metadata_dict()
    if theme_name in themes:
        theme_meta = themes[theme_name]

        # If it has a file_path, use that
        if 'file_path' in theme_meta:
            theme_path = Path(theme_meta['file_path'])
            if theme_path.exists():
                return theme_path

    # Check built-in themes in assets directory
    try:
        css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme_name}.css")
        if css_path.exists():
            return css_path
    except Exception:
        pass

    return None


def create_theme_manifest(output_path: Path) -> None:
    """Create a JSON manifest of all available themes."""
    themes = _get_theme_metadata_dict()

    # Remove file_path from the manifest (internal use only)
    clean_themes = {}
    for theme_name, theme_meta in themes.items():
        clean_meta = theme_meta.copy()
        clean_meta.pop('file_path', None)
        clean_meta.pop('file_name', None)
        clean_themes[theme_name] = clean_meta

    manifest = {
        "themes": clean_themes,
        "version": "1.0",
        "generated_by": "docx2shelf"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def refresh_themes() -> None:
    """Force refresh of theme discovery (useful for development)."""
    clear_theme_cache()
    _get_theme_metadata_dict()  # Rebuild cache


def get_all_theme_names() -> List[str]:
    """Get list of all available theme names."""
    return get_available_themes()


def get_theme_css_content(theme_name: str, custom_theme_dir: Optional[Path] = None) -> str:
    """
    Get the CSS content for a theme.

    Args:
        theme_name: Name of the theme
        custom_theme_dir: Optional directory to search for custom themes

    Returns:
        CSS content as string

    Raises:
        FileNotFoundError: If theme file is not found
        ValueError: If theme name is invalid
    """
    if not validate_theme(theme_name):
        raise ValueError(f"Invalid theme name: {theme_name}")

    theme_path = get_theme_css_path(theme_name, custom_theme_dir)
    if not theme_path or not theme_path.exists():
        raise FileNotFoundError(f"Theme file not found for: {theme_name}")

    try:
        return theme_path.read_text(encoding='utf-8')
    except Exception as e:
        raise ValueError(f"Error reading theme file {theme_path}: {e}")