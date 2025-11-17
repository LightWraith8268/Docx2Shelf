"""
Path utilities for cross-platform file handling and Unicode support.

This module provides utilities for:
- Normalizing Windows paths and handling drive letters
- Supporting non-ASCII characters in filenames
- Cross-platform path resolution
- Safe path operations with proper encoding
"""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path
from typing import Union

try:
    import platformdirs

    PLATFORMDIRS_AVAILABLE = True
except ImportError:
    PLATFORMDIRS_AVAILABLE = False


def normalize_path(path: Union[str, Path], target_platform: str = None) -> Path:
    """
    Normalize a path for the target platform, handling Unicode and drive letters.

    Args:
        path: Path to normalize (string or Path object)
        target_platform: Target platform ('windows', 'posix', or None for current)

    Returns:
        Normalized Path object
    """
    if isinstance(path, str):
        path = Path(path)

    # Determine target platform
    if target_platform is None:
        target_platform = "windows" if os.name == "nt" else "posix"

    # Convert to string for normalization
    path_str = str(path)

    # Normalize Unicode characters (NFC normalization)
    path_str = unicodedata.normalize("NFC", path_str)

    # Handle Windows-specific normalization
    if target_platform == "windows":
        # Convert forward slashes to backslashes
        path_str = path_str.replace("/", "\\")

        # Handle UNC paths (\\server\share)
        if path_str.startswith("\\\\"):
            return Path(path_str)

        # Handle drive letters - ensure they're uppercase
        if len(path_str) >= 2 and path_str[1] == ":":
            path_str = path_str[0].upper() + path_str[1:]

        # Remove redundant separators
        while "\\\\" in path_str:
            path_str = path_str.replace("\\\\", "\\")
    else:
        # POSIX normalization
        path_str = path_str.replace("\\", "/")

        # Remove redundant separators
        while "//" in path_str:
            path_str = path_str.replace("//", "/")

    # Convert back to Path
    return Path(path_str).resolve() if path.is_absolute() else Path(path_str)


def safe_filename(filename: str, replacement_char: str = "_") -> str:
    """
    Create a safe filename by replacing invalid characters.

    Args:
        filename: Original filename
        replacement_char: Character to replace invalid chars with

    Returns:
        Safe filename string
    """
    # Normalize Unicode
    filename = unicodedata.normalize("NFC", filename)

    # Define invalid characters for Windows (most restrictive)
    invalid_chars = r'<>:"/\|?*'

    # Replace invalid characters
    for char in invalid_chars:
        filename = filename.replace(char, replacement_char)

    # Remove control characters (0-31)
    filename = "".join(char for char in filename if ord(char) >= 32)

    # Trim whitespace and dots from ends
    filename = filename.strip(" .")

    # Handle reserved names on Windows
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    base_name = filename.upper()
    if "." in base_name:
        base_name = base_name.split(".")[0]

    if base_name in reserved_names:
        filename = f"{replacement_char}{filename}"

    # Ensure filename isn't empty
    if not filename:
        filename = "unnamed"

    return filename


def safe_path_join(*parts: Union[str, Path]) -> Path:
    """
    Safely join path parts with proper Unicode handling.

    Args:
        *parts: Path parts to join

    Returns:
        Joined Path object
    """
    # Convert all parts to normalized strings
    str_parts = []
    for part in parts:
        if isinstance(part, Path):
            part_str = str(part)
        else:
            part_str = str(part)

        # Normalize Unicode
        part_str = unicodedata.normalize("NFC", part_str)
        str_parts.append(part_str)

    # Join using pathlib
    result = Path(*str_parts)

    # Normalize the final path
    return normalize_path(result)


def ensure_unicode_path(path: Union[str, Path]) -> Path:
    """
    Ensure a path can handle Unicode characters properly.

    Args:
        path: Path to check and normalize

    Returns:
        Unicode-safe Path object
    """
    if isinstance(path, str):
        # Decode if it's bytes-like
        if isinstance(path, bytes):
            path = path.decode("utf-8", errors="replace")
        path = Path(path)

    # Normalize Unicode representation
    path_str = unicodedata.normalize("NFC", str(path))

    return Path(path_str)


def get_safe_temp_path(base_name: str = "docx2shelf") -> Path:
    """
    Get a safe temporary directory path with Unicode support.

    Args:
        base_name: Base name for the temp directory

    Returns:
        Path to safe temporary directory
    """
    import tempfile

    # Use platformdirs if available for better cross-platform support
    if PLATFORMDIRS_AVAILABLE:
        temp_dir = Path(platformdirs.user_cache_dir("docx2shelf", "temp"))
    else:
        # Fallback to system temp directory
        temp_dir = Path(tempfile.gettempdir())

    # Ensure the temp directory supports Unicode
    temp_dir = ensure_unicode_path(temp_dir)

    # Create safe base name
    safe_base = safe_filename(base_name)

    return temp_dir / safe_base


def get_user_data_dir(app_name: str = "docx2shelf") -> Path:
    """
    Get the user data directory using platformdirs for cross-platform compatibility.

    Args:
        app_name: Application name for directory

    Returns:
        Path to user data directory
    """
    if PLATFORMDIRS_AVAILABLE:
        return ensure_unicode_path(Path(platformdirs.user_data_dir(app_name)))
    else:
        # Fallback based on platform
        if os.name == "nt":  # Windows
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:  # Unix-like
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return ensure_unicode_path(base / app_name)


def get_user_cache_dir(app_name: str = "docx2shelf") -> Path:
    """
    Get the user cache directory using platformdirs for cross-platform compatibility.

    Args:
        app_name: Application name for directory

    Returns:
        Path to user cache directory
    """
    if PLATFORMDIRS_AVAILABLE:
        return ensure_unicode_path(Path(platformdirs.user_cache_dir(app_name)))
    else:
        # Fallback based on platform
        if os.name == "nt":  # Windows
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:  # Unix-like
            base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        return ensure_unicode_path(base / app_name)


def get_user_config_dir(app_name: str = "docx2shelf") -> Path:
    """
    Get the user config directory using platformdirs for cross-platform compatibility.

    Args:
        app_name: Application name for directory

    Returns:
        Path to user config directory
    """
    if PLATFORMDIRS_AVAILABLE:
        return ensure_unicode_path(Path(platformdirs.user_config_dir(app_name)))
    else:
        # Fallback based on platform
        if os.name == "nt":  # Windows
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:  # Unix-like
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return ensure_unicode_path(base / app_name)


def validate_path_encoding(path: Union[str, Path]) -> bool:
    """
    Validate that a path can be properly encoded/decoded.

    Args:
        path: Path to validate

    Returns:
        True if path encoding is valid
    """
    try:
        path_str = str(path)

        # Test UTF-8 encoding/decoding
        encoded = path_str.encode("utf-8")
        decoded = encoded.decode("utf-8")

        # Test Unicode normalization
        normalized = unicodedata.normalize("NFC", decoded)

        return path_str == normalized
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False


def fix_path_encoding(path: Union[str, Path], fallback_encoding: str = "latin1") -> Path:
    """
    Attempt to fix path encoding issues.

    Args:
        path: Path with potential encoding issues
        fallback_encoding: Fallback encoding to try

    Returns:
        Fixed Path object
    """
    if isinstance(path, Path):
        path_str = str(path)
    else:
        path_str = path

    # If it's already valid, return it
    if validate_path_encoding(path_str):
        return Path(path_str)

    # Try to fix encoding issues
    try:
        # If it's bytes-like, decode it
        if isinstance(path_str, bytes):
            path_str = path_str.decode("utf-8", errors="replace")

        # Try fallback encoding
        try:
            # Encode with fallback, then decode as UTF-8
            if isinstance(path_str, str):
                encoded = path_str.encode(fallback_encoding, errors="ignore")
                path_str = encoded.decode("utf-8", errors="replace")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

        # Normalize Unicode
        path_str = unicodedata.normalize("NFC", path_str)

        return Path(path_str)
    except Exception:
        # Last resort: create a safe filename
        safe_name = safe_filename(str(path).replace("/", "_").replace("\\", "_"))
        return Path(safe_name)


def get_display_path(path: Union[str, Path], max_length: int = 50) -> str:
    """
    Get a user-friendly display version of a path.

    Args:
        path: Path to display
        max_length: Maximum display length

    Returns:
        User-friendly path string
    """
    path_str = str(normalize_path(path))

    if len(path_str) <= max_length:
        return path_str

    # Truncate with ellipsis
    if max_length <= 3:
        return "..."

    # Keep start and end of path
    start_len = (max_length - 3) // 2
    end_len = max_length - 3 - start_len

    return f"{path_str[:start_len]}...{path_str[-end_len:]}"


def is_safe_path(path: Union[str, Path], base_path: Union[str, Path] = None) -> bool:
    """
    Check if a path is safe (no directory traversal, valid encoding).

    Args:
        path: Path to check
        base_path: Base path for relative path validation

    Returns:
        True if path is safe
    """
    try:
        path = normalize_path(path)

        # Check encoding
        if not validate_path_encoding(path):
            return False

        # Check for directory traversal
        if ".." in path.parts:
            return False

        # If base_path is provided, ensure path is within it
        if base_path is not None:
            base_path = normalize_path(base_path)
            try:
                path.resolve().relative_to(base_path.resolve())
            except ValueError:
                return False

        return True
    except Exception:
        return False


# Convenience functions for common operations
def write_text_safe(path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """
    Safely write text to a file with proper encoding.

    Args:
        path: File path
        content: Text content to write
        encoding: Text encoding (default: utf-8)
    """
    path = ensure_unicode_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding, errors="replace") as f:
        f.write(content)


def read_text_safe(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    Safely read text from a file with proper encoding.

    Args:
        path: File path
        encoding: Text encoding (default: utf-8)

    Returns:
        File content as string
    """
    path = ensure_unicode_path(path)

    with open(path, "r", encoding=encoding, errors="replace") as f:
        return f.read()
