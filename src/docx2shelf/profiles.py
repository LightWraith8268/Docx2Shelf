from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


# Built-in publishing profiles
BUILTIN_PROFILES = {
    "kdp": {
        "name": "Amazon KDP",
        "description": "Optimized for Amazon Kindle Direct Publishing",
        "epub_version": "3",
        "cover_scale": "contain",
        "image_format": "original",  # KDP doesn't support WebP
        "image_max_width": 1600,
        "image_max_height": 2560,
        "image_quality": 90,
        "theme": "serif",
        "hyphenate": True,
        "justify": True,
        "epub2_compat": False,
        "epubcheck": True,
        "metadata_requirements": {
            "language": "required",
            "publisher": "recommended",
            "description": "required",
            "isbn": "optional"
        },
        "validations": [
            "cover_size_check",
            "language_required",
            "description_length_check"
        ]
    },
    "kobo": {
        "name": "Kobo Writing Life",
        "description": "Optimized for Kobo ebook publishing",
        "epub_version": "3",
        "cover_scale": "contain",
        "image_format": "webp",
        "image_max_width": 1200,
        "image_max_height": 1600,
        "image_quality": 85,
        "theme": "serif",
        "hyphenate": True,
        "justify": True,
        "epub2_compat": False,
        "epubcheck": True,
        "metadata_requirements": {
            "language": "required",
            "publisher": "optional",
            "description": "required",
            "series": "supported"
        },
        "validations": [
            "cover_size_check",
            "language_required"
        ]
    },
    "apple": {
        "name": "Apple Books",
        "description": "Optimized for Apple Books publishing",
        "epub_version": "3",
        "cover_scale": "contain",
        "image_format": "original",
        "image_max_width": 1400,
        "image_max_height": 1800,
        "image_quality": 92,
        "theme": "serif",
        "hyphenate": True,
        "justify": True,
        "epub2_compat": False,
        "epubcheck": True,
        "metadata_requirements": {
            "language": "required",
            "publisher": "recommended",
            "description": "required",
            "isbn": "recommended"
        },
        "validations": [
            "cover_size_check",
            "language_required",
            "apple_specific_checks"
        ]
    },
    "generic": {
        "name": "Generic EPUB",
        "description": "Standard EPUB 3 with broad compatibility",
        "epub_version": "3",
        "cover_scale": "contain",
        "image_format": "webp",
        "image_max_width": 1200,
        "image_max_height": 1600,
        "image_quality": 85,
        "theme": "serif",
        "hyphenate": True,
        "justify": True,
        "epub2_compat": False,
        "epubcheck": True,
        "metadata_requirements": {
            "language": "required",
            "description": "recommended"
        },
        "validations": [
            "basic_epub_checks"
        ]
    },
    "legacy": {
        "name": "Legacy Readers",
        "description": "Maximum compatibility with older EPUB readers",
        "epub_version": "2",
        "cover_scale": "contain",
        "image_format": "original",
        "image_max_width": 1000,
        "image_max_height": 1500,
        "image_quality": 80,
        "theme": "printlike",
        "hyphenate": False,
        "justify": True,
        "epub2_compat": True,
        "epubcheck": True,
        "metadata_requirements": {
            "language": "required"
        },
        "validations": [
            "epub2_compatibility_checks"
        ]
    }
}


def get_available_profiles() -> List[str]:
    """Get list of all available profile names."""
    return list(BUILTIN_PROFILES.keys())


def get_profile_info(profile_name: str) -> Optional[Dict]:
    """Get information about a specific profile."""
    return BUILTIN_PROFILES.get(profile_name)


def list_all_profiles() -> str:
    """Get formatted list of all profiles with descriptions."""
    lines = ["Available profiles:"]

    for profile_id, profile in BUILTIN_PROFILES.items():
        lines.append(f"  {profile_id}: {profile['name']} - {profile['description']}")

    return "\n".join(lines)


def apply_profile_to_args(args, profile_name: str) -> None:
    """Apply profile settings to argument namespace."""
    profile = get_profile_info(profile_name)
    if not profile:
        raise ValueError(f"Unknown profile: {profile_name}")

    # Apply profile settings to args, but don't override explicitly set values
    for key, value in profile.items():
        if key in ["name", "description", "metadata_requirements", "validations"]:
            continue

        arg_name = key.replace("-", "_")

        # Only set if not already explicitly provided
        if not hasattr(args, arg_name) or getattr(args, arg_name) is None:
            setattr(args, arg_name, value)

    # Handle special boolean conversions
    if hasattr(args, 'hyphenate') and isinstance(args.hyphenate, bool):
        args.hyphenate = "on" if args.hyphenate else "off"

    if hasattr(args, 'justify') and isinstance(args.justify, bool):
        args.justify = "on" if args.justify else "off"

    if hasattr(args, 'epubcheck') and isinstance(args.epubcheck, bool):
        args.epubcheck = "on" if args.epubcheck else "off"


def validate_profile_requirements(meta, profile_name: str) -> List[str]:
    """Validate that metadata meets profile requirements.

    Returns list of validation errors.
    """
    profile = get_profile_info(profile_name)
    if not profile:
        return [f"Unknown profile: {profile_name}"]

    errors = []
    requirements = profile.get("metadata_requirements", {})

    # Check required fields
    for field, requirement in requirements.items():
        if requirement == "required":
            value = getattr(meta, field, None)
            if not value:
                errors.append(f"{profile['name']} requires {field}")

    # Run profile-specific validations
    validations = profile.get("validations", [])
    for validation in validations:
        validation_errors = _run_validation(validation, meta, profile)
        errors.extend(validation_errors)

    return errors


def _run_validation(validation_name: str, meta, profile: Dict) -> List[str]:
    """Run a specific validation check."""
    errors = []

    if validation_name == "cover_size_check":
        # Check cover dimensions if available
        if hasattr(meta, 'cover_path') and meta.cover_path:
            try:
                from PIL import Image
                with Image.open(meta.cover_path) as img:
                    width, height = img.size
                    max_width = profile.get("image_max_width", 1600)
                    max_height = profile.get("image_max_height", 2560)

                    if width > max_width or height > max_height:
                        errors.append(f"Cover size {width}x{height} exceeds {profile['name']} limits ({max_width}x{max_height})")

                    # Check aspect ratio for some profiles
                    if profile_name := profile.get("name"):
                        if "KDP" in profile_name:
                            ratio = height / width
                            if ratio < 1.25 or ratio > 2.0:
                                errors.append(f"Cover aspect ratio {ratio:.2f} outside KDP recommendations (1.25-2.0)")

            except ImportError:
                pass  # PIL not available
            except Exception:
                pass  # Could not read image

    elif validation_name == "language_required":
        if not getattr(meta, 'language', None):
            errors.append(f"{profile['name']} requires language to be specified")

    elif validation_name == "description_length_check":
        description = getattr(meta, 'description', None)
        if description:
            if len(description) < 50:
                errors.append(f"{profile['name']} recommends description of at least 50 characters")
            elif len(description) > 4000:
                errors.append(f"{profile['name']} description should not exceed 4000 characters")

    elif validation_name == "apple_specific_checks":
        # Apple Books specific requirements
        if getattr(meta, 'publisher', None) == "":
            errors.append("Apple Books recommends setting a publisher name")

    elif validation_name == "epub2_compatibility_checks":
        # Check for EPUB 2 compatibility issues
        pass  # Could add specific EPUB 2 checks here

    elif validation_name == "basic_epub_checks":
        # Basic EPUB validation
        if not getattr(meta, 'title', None):
            errors.append("EPUB requires a title")
        if not getattr(meta, 'author', None):
            errors.append("EPUB requires an author")

    return errors


def create_custom_profile(profile_data: Dict, output_path: Path) -> None:
    """Create a custom profile file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)


def load_custom_profile(profile_path: Path) -> Dict:
    """Load a custom profile from a file."""
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Could not load profile from {profile_path}: {e}")


def discover_custom_profiles(search_dir: Path) -> Dict[str, Path]:
    """Discover custom profile files in a directory."""
    custom_profiles = {}

    if not search_dir.exists() or not search_dir.is_dir():
        return custom_profiles

    for profile_file in search_dir.glob("*.profile.json"):
        profile_name = profile_file.stem.replace(".profile", "")
        if profile_name not in BUILTIN_PROFILES:
            custom_profiles[profile_name] = profile_file

    return custom_profiles


def get_profile_summary(profile_name: str) -> str:
    """Get a detailed summary of profile settings."""
    profile = get_profile_info(profile_name)
    if not profile:
        return f"Profile '{profile_name}' not found"

    lines = [
        f"Profile: {profile['name']}",
        f"Description: {profile['description']}",
        "",
        "Settings:",
        f"  EPUB Version: {profile.get('epub_version', '3')}",
        f"  Theme: {profile.get('theme', 'serif')}",
        f"  Image Format: {profile.get('image_format', 'webp')}",
        f"  Max Image Size: {profile.get('image_max_width', 1200)}x{profile.get('image_max_height', 1600)}",
        f"  Image Quality: {profile.get('image_quality', 85)}%",
        f"  Hyphenation: {'On' if profile.get('hyphenate', True) else 'Off'}",
        f"  Justification: {'On' if profile.get('justify', True) else 'Off'}",
        f"  EPUB2 Compatibility: {'On' if profile.get('epub2_compat', False) else 'Off'}",
        "",
        "Metadata Requirements:"
    ]

    requirements = profile.get("metadata_requirements", {})
    for field, req_type in requirements.items():
        lines.append(f"  {field}: {req_type}")

    return "\n".join(lines)