from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional

# Theme metadata definitions
THEME_METADATA = {
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
    },
    "fantasy": {
        "name": "Fantasy Epic",
        "description": "Ornate styling perfect for fantasy and historical fiction",
        "genre": "fantasy",
        "features": ["ornate", "decorative", "medieval", "serif"]
    },
    "romance": {
        "name": "Romance",
        "description": "Elegant fonts with romantic flourishes",
        "genre": "romance",
        "features": ["elegant", "script", "decorative", "serif"]
    },
    "mystery": {
        "name": "Mystery & Thriller",
        "description": "Bold, stark typography for suspenseful works",
        "genre": "mystery",
        "features": ["bold", "stark", "uppercase", "thriller"]
    },
    "scifi": {
        "name": "Science Fiction",
        "description": "Modern, tech-inspired design for sci-fi works",
        "genre": "scifi",
        "features": ["futuristic", "tech", "clean", "sans-serif"]
    },
    "academic": {
        "name": "Academic",
        "description": "Professional formatting for non-fiction and academic works",
        "genre": "academic",
        "features": ["professional", "footnotes", "tables", "serif"]
    },
    "night": {
        "name": "Night Mode",
        "description": "Dark theme optimized for night reading",
        "genre": "general",
        "features": ["dark", "night-mode", "eye-friendly", "accessibility"]
    }
}


def get_available_themes() -> List[str]:
    """Get list of all available theme names."""
    return list(THEME_METADATA.keys())


def get_theme_metadata(theme_name: str) -> Optional[Dict]:
    """Get metadata for a specific theme."""
    return THEME_METADATA.get(theme_name)


def get_themes_by_genre(genre: str) -> List[str]:
    """Get themes filtered by genre."""
    return [
        theme for theme, meta in THEME_METADATA.items()
        if meta["genre"] == genre or genre == "all"
    ]


def get_theme_info(theme_name: str) -> str:
    """Get formatted theme information."""
    meta = get_theme_metadata(theme_name)
    if not meta:
        return f"Unknown theme: {theme_name}"

    features = ", ".join(meta["features"])
    return f"{meta['name']}: {meta['description']} (Features: {features})"


def list_all_themes() -> str:
    """Get formatted list of all themes with descriptions."""
    lines = ["Available themes:"]

    # Group by genre
    genres = {}
    for theme, meta in THEME_METADATA.items():
        genre = meta["genre"]
        if genre not in genres:
            genres[genre] = []
        genres[genre].append((theme, meta))

    for genre, themes in sorted(genres.items()):
        lines.append(f"\n{genre.title()}:")
        for theme, meta in themes:
            lines.append(f"  {theme}: {meta['name']} - {meta['description']}")

    return "\n".join(lines)


def validate_theme(theme_name: str) -> bool:
    """Check if a theme exists and is valid."""
    if theme_name not in THEME_METADATA:
        return False

    # Check if CSS file exists
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
        if theme_name not in THEME_METADATA:
            custom_themes[theme_name] = css_file

    return custom_themes


def get_theme_css_path(theme_name: str, custom_theme_dir: Optional[Path] = None) -> Optional[Path]:
    """Get the path to a theme's CSS file, checking custom themes first."""
    # Check for custom theme first
    if custom_theme_dir:
        custom_themes = discover_custom_themes(custom_theme_dir)
        if theme_name in custom_themes:
            return custom_themes[theme_name]

    # Check built-in themes
    if theme_name in THEME_METADATA:
        try:
            css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme_name}.css")
            if css_path.exists():
                return css_path
        except Exception:
            pass

    return None


def create_theme_manifest(output_path: Path) -> None:
    """Create a JSON manifest of all available themes."""
    manifest = {
        "themes": THEME_METADATA,
        "version": "1.0",
        "generated_by": "docx2shelf"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)