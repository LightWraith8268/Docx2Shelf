"""Version information for docx2shelf."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path


def get_version() -> str:
    """Get the version of docx2shelf."""
    # When running from source, prioritize pyproject.toml
    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding='utf-8')
            for line in content.splitlines():
                if line.strip().startswith('version = '):
                    # Extract version from 'version = "1.6.3"'
                    version = line.split('=')[1].strip().strip('"\'')
                    return version
    except Exception:
        pass

    try:
        # Fallback to installed package metadata
        return importlib.metadata.version("docx2shelf")
    except importlib.metadata.PackageNotFoundError:
        pass

    # Ultimate fallback
    return "unknown"


def get_version_info() -> dict[str, str]:
    """Get comprehensive version information."""
    version = get_version()

    # Try to get additional info
    info = {
        "version": version,
        "package": "docx2shelf"
    }

    try:
        # Get package metadata if available
        metadata = importlib.metadata.metadata("docx2shelf")
        info.update({
            "description": metadata.get("Summary", ""),
            "author": metadata.get("Author", ""),
            "license": metadata.get("License", ""),
            "python_requires": metadata.get("Requires-Python", ""),
        })
    except (importlib.metadata.PackageNotFoundError, Exception):
        # Running from source
        info.update({
            "description": "Offline CLI to convert DOCX manuscripts into valid EPUB 3",
            "author": "Docx2Shelf Contributors",
            "license": "MIT",
            "python_requires": ">=3.11",
        })

    return info


# Module constants
__version__ = get_version()
VERSION = __version__