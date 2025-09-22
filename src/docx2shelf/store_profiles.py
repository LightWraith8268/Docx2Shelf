"""
Store-specific profiles and validation for major EPUB retailers.

Provides CSS profiles, validation rules, and metadata requirements
for Amazon KDP, Apple Books, Kobo, and other major platforms.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .metadata import EpubMetadata

logger = logging.getLogger(__name__)


class StoreProfile(Enum):
    """Supported store profiles."""
    KDP = "kdp"              # Amazon Kindle Direct Publishing
    APPLE = "apple"          # Apple Books
    KOBO = "kobo"            # Kobo
    GOOGLE = "google"        # Google Play Books
    BARNES_NOBLE = "bn"      # Barnes & Noble
    GENERIC = "generic"      # Generic EPUB 3 standard


@dataclass
class ValidationRule:
    """Store-specific validation rule."""
    rule_id: str
    severity: str  # error, warning, info
    title: str
    description: str
    check_function: str  # Name of function to call
    applies_to: List[str] = field(default_factory=list)  # css, metadata, content, structure


@dataclass
class CSSRestriction:
    """CSS property restriction."""
    property: str
    allowed_values: Optional[List[str]] = None
    forbidden_values: Optional[List[str]] = None
    max_value: Optional[str] = None
    min_value: Optional[str] = None
    replacement_suggestion: Optional[str] = None


@dataclass
class StoreRequirements:
    """Requirements for a specific store."""
    profile: StoreProfile
    name: str
    description: str

    # EPUB format requirements
    supported_epub_versions: List[str] = field(default_factory=lambda: ["3.0", "3.1", "3.2"])
    max_file_size_mb: Optional[int] = None
    max_chapter_count: Optional[int] = None

    # Image requirements
    max_image_width: Optional[int] = None
    max_image_height: Optional[int] = None
    supported_image_formats: List[str] = field(default_factory=lambda: ["jpeg", "png", "gif", "svg"])
    cover_required_width: Optional[int] = None
    cover_required_height: Optional[int] = None
    cover_aspect_ratio: Optional[str] = None  # "1.6:1" format

    # CSS restrictions
    css_restrictions: List[CSSRestriction] = field(default_factory=list)
    forbidden_css_properties: List[str] = field(default_factory=list)

    # Font requirements
    max_embedded_fonts: Optional[int] = None
    supported_font_formats: List[str] = field(default_factory=lambda: ["woff", "woff2", "ttf", "otf"])

    # Metadata requirements
    required_metadata_fields: List[str] = field(default_factory=list)
    max_title_length: Optional[int] = None
    max_description_length: Optional[int] = None

    # Content restrictions
    max_toc_depth: Optional[int] = None
    requires_page_list: bool = False

    # Validation rules
    validation_rules: List[ValidationRule] = field(default_factory=list)


class StoreProfileManager:
    """Manages store-specific profiles and validation."""

    def __init__(self):
        self.profiles: Dict[StoreProfile, StoreRequirements] = {}
        self._initialize_profiles()

    def _initialize_profiles(self):
        """Initialize built-in store profiles."""
        self.profiles[StoreProfile.KDP] = self._create_kdp_profile()
        self.profiles[StoreProfile.APPLE] = self._create_apple_profile()
        self.profiles[StoreProfile.KOBO] = self._create_kobo_profile()
        self.profiles[StoreProfile.GOOGLE] = self._create_google_profile()
        self.profiles[StoreProfile.BARNES_NOBLE] = self._create_bn_profile()
        self.profiles[StoreProfile.GENERIC] = self._create_generic_profile()

    def _create_kdp_profile(self) -> StoreRequirements:
        """Create Amazon KDP profile."""
        return StoreRequirements(
            profile=StoreProfile.KDP,
            name="Amazon Kindle Direct Publishing",
            description="Requirements for Amazon KDP and Kindle devices",

            supported_epub_versions=["3.0", "3.1"],
            max_file_size_mb=650,  # 650MB limit

            # Image requirements
            max_image_width=4000,
            max_image_height=4000,
            supported_image_formats=["jpeg", "png", "gif"],
            cover_required_width=1600,
            cover_required_height=2560,
            cover_aspect_ratio="1.6:1",

            # CSS restrictions for Kindle
            css_restrictions=[
                CSSRestriction("position", forbidden_values=["fixed", "absolute"]),
                CSSRestriction("float", forbidden_values=["left", "right"]),
                CSSRestriction("display", forbidden_values=["flex", "grid"]),
                CSSRestriction("page-break-before", allowed_values=["auto", "always", "avoid"]),
                CSSRestriction("page-break-after", allowed_values=["auto", "always", "avoid"]),
                CSSRestriction("text-align", allowed_values=["left", "right", "center", "justify"]),
            ],

            forbidden_css_properties=[
                "transform", "transition", "animation", "filter", "backdrop-filter",
                "clip-path", "mask", "mix-blend-mode", "@supports", "@media (prefers-color-scheme)"
            ],

            # Font restrictions
            max_embedded_fonts=5,
            supported_font_formats=["ttf", "otf"],

            # Metadata requirements
            required_metadata_fields=["title", "author", "language", "isbn"],
            max_title_length=255,
            max_description_length=4000,

            max_toc_depth=3,

            validation_rules=[
                ValidationRule(
                    "kdp_cover_dimensions",
                    "error",
                    "Cover image dimensions",
                    "Cover must be at least 1600x2560 pixels with 1.6:1 aspect ratio",
                    "check_kdp_cover_dimensions",
                    ["metadata"]
                ),
                ValidationRule(
                    "kdp_css_positioning",
                    "warning",
                    "CSS positioning not supported",
                    "Absolute and fixed positioning may not work on Kindle devices",
                    "check_kdp_css_positioning",
                    ["css"]
                ),
                ValidationRule(
                    "kdp_file_size",
                    "error",
                    "File size limit",
                    "EPUB file must be under 650MB",
                    "check_file_size",
                    ["structure"]
                ),
            ]
        )

    def _create_apple_profile(self) -> StoreRequirements:
        """Create Apple Books profile."""
        return StoreRequirements(
            profile=StoreProfile.APPLE,
            name="Apple Books",
            description="Requirements for Apple Books Store",

            supported_epub_versions=["3.0", "3.1", "3.2"],
            max_file_size_mb=2000,  # 2GB limit

            # Image requirements
            max_image_width=3840,  # 4K support
            max_image_height=2160,
            supported_image_formats=["jpeg", "png", "gif", "svg"],
            cover_required_width=1400,
            cover_required_height=1800,

            # CSS - Apple Books has excellent CSS support
            css_restrictions=[
                CSSRestriction("position", allowed_values=["static", "relative", "absolute", "fixed"]),
                CSSRestriction("display", allowed_values=["block", "inline", "inline-block", "flex", "grid", "table", "table-cell"]),
            ],

            max_embedded_fonts=10,
            supported_font_formats=["woff", "woff2", "ttf", "otf"],

            required_metadata_fields=["title", "author", "language"],
            max_title_length=255,
            max_description_length=5000,

            max_toc_depth=6,

            validation_rules=[
                ValidationRule(
                    "apple_epub_version",
                    "warning",
                    "EPUB version support",
                    "Apple Books supports EPUB 3.2 features",
                    "check_epub_version",
                    ["structure"]
                ),
                ValidationRule(
                    "apple_css_support",
                    "info",
                    "Advanced CSS features",
                    "Apple Books supports modern CSS including flexbox and grid",
                    "check_css_features",
                    ["css"]
                ),
            ]
        )

    def _create_kobo_profile(self) -> StoreRequirements:
        """Create Kobo profile."""
        return StoreRequirements(
            profile=StoreProfile.KOBO,
            name="Kobo",
            description="Requirements for Kobo Store and devices",

            supported_epub_versions=["3.0", "3.1"],
            max_file_size_mb=100,  # Conservative limit

            max_image_width=2048,
            max_image_height=2048,
            supported_image_formats=["jpeg", "png", "gif", "svg"],
            cover_required_width=1200,
            cover_required_height=1600,

            css_restrictions=[
                CSSRestriction("position", forbidden_values=["fixed"]),
                CSSRestriction("display", forbidden_values=["grid"]),  # Limited grid support
            ],

            max_embedded_fonts=8,
            supported_font_formats=["ttf", "otf", "woff"],

            required_metadata_fields=["title", "author", "language"],
            max_title_length=255,
            max_description_length=3000,

            max_toc_depth=4,

            validation_rules=[
                ValidationRule(
                    "kobo_font_formats",
                    "warning",
                    "Font format support",
                    "Kobo has best support for TTF and OTF fonts",
                    "check_font_formats",
                    ["content"]
                ),
            ]
        )

    def _create_google_profile(self) -> StoreRequirements:
        """Create Google Play Books profile."""
        return StoreRequirements(
            profile=StoreProfile.GOOGLE,
            name="Google Play Books",
            description="Requirements for Google Play Books",

            supported_epub_versions=["3.0", "3.1", "3.2"],
            max_file_size_mb=100,

            max_image_width=2048,
            max_image_height=2048,
            supported_image_formats=["jpeg", "png", "gif", "svg"],
            cover_required_width=1200,
            cover_required_height=1600,

            max_embedded_fonts=10,
            supported_font_formats=["woff", "woff2", "ttf", "otf"],

            required_metadata_fields=["title", "author", "language", "isbn"],
            max_title_length=255,
            max_description_length=4000,

            max_toc_depth=5,

            validation_rules=[
                ValidationRule(
                    "google_isbn_required",
                    "error",
                    "ISBN required",
                    "Google Play Books requires ISBN for submission",
                    "check_isbn_present",
                    ["metadata"]
                ),
            ]
        )

    def _create_bn_profile(self) -> StoreRequirements:
        """Create Barnes & Noble profile."""
        return StoreRequirements(
            profile=StoreProfile.BARNES_NOBLE,
            name="Barnes & Noble",
            description="Requirements for Barnes & Noble NOOK",

            supported_epub_versions=["3.0", "3.1"],
            max_file_size_mb=20,  # Conservative limit for NOOK

            max_image_width=1600,
            max_image_height=2400,
            supported_image_formats=["jpeg", "png", "gif"],
            cover_required_width=1200,
            cover_required_height=1600,

            css_restrictions=[
                CSSRestriction("position", forbidden_values=["fixed", "absolute"]),
                CSSRestriction("display", forbidden_values=["flex", "grid"]),
            ],

            max_embedded_fonts=5,
            supported_font_formats=["ttf", "otf"],

            required_metadata_fields=["title", "author", "language"],
            max_title_length=255,
            max_description_length=2000,

            max_toc_depth=3,

            validation_rules=[
                ValidationRule(
                    "bn_file_size",
                    "warning",
                    "File size recommendation",
                    "Keep file size under 20MB for optimal NOOK performance",
                    "check_file_size",
                    ["structure"]
                ),
            ]
        )

    def _create_generic_profile(self) -> StoreRequirements:
        """Create generic EPUB 3 profile."""
        return StoreRequirements(
            profile=StoreProfile.GENERIC,
            name="Generic EPUB 3",
            description="Standard EPUB 3 specification requirements",

            supported_epub_versions=["3.0", "3.1", "3.2"],

            supported_image_formats=["jpeg", "png", "gif", "svg"],
            supported_font_formats=["woff", "woff2", "ttf", "otf"],

            required_metadata_fields=["title", "author", "language"],

            validation_rules=[
                ValidationRule(
                    "epub_validation",
                    "error",
                    "EPUB validation",
                    "EPUB must pass EPUBCheck validation",
                    "check_epubcheck",
                    ["structure"]
                ),
            ]
        )

    def get_profile(self, profile_name: StoreProfile) -> StoreRequirements:
        """Get requirements for a specific store profile."""
        return self.profiles.get(profile_name, self.profiles[StoreProfile.GENERIC])

    def validate_epub(self, profile_name: StoreProfile, epub_path: Path, metadata: EpubMetadata) -> List[Dict[str, Any]]:
        """
        Validate EPUB against store profile requirements.

        Returns:
            List of validation issues
        """
        profile = self.get_profile(profile_name)
        issues = []

        # Run validation rules
        for rule in profile.validation_rules:
            try:
                rule_issues = self._run_validation_rule(rule, profile, epub_path, metadata)
                issues.extend(rule_issues)
            except Exception as e:
                logger.warning(f"Validation rule {rule.rule_id} failed: {e}")

        return issues

    def _run_validation_rule(self, rule: ValidationRule, profile: StoreRequirements, epub_path: Path, metadata: EpubMetadata) -> List[Dict[str, Any]]:
        """Run a specific validation rule."""
        issues = []

        # Dispatch to specific check functions
        if rule.check_function == "check_kdp_cover_dimensions":
            issues.extend(self._check_kdp_cover_dimensions(metadata, profile))
        elif rule.check_function == "check_file_size":
            issues.extend(self._check_file_size(epub_path, profile))
        elif rule.check_function == "check_isbn_present":
            issues.extend(self._check_isbn_present(metadata))
        elif rule.check_function == "check_epub_version":
            issues.extend(self._check_epub_version(profile))
        elif rule.check_function == "check_css_features":
            issues.extend(self._check_css_features(epub_path, profile))
        elif rule.check_function == "check_font_formats":
            issues.extend(self._check_font_formats(epub_path, profile))
        elif rule.check_function == "check_kdp_css_positioning":
            issues.extend(self._check_kdp_css_positioning(epub_path))
        elif rule.check_function == "check_epubcheck":
            issues.extend(self._check_epubcheck(epub_path))

        return issues

    def _check_kdp_cover_dimensions(self, metadata: EpubMetadata, profile: StoreRequirements) -> List[Dict[str, Any]]:
        """Check KDP cover image dimensions."""
        issues = []

        if not metadata.cover_path or not metadata.cover_path.exists():
            issues.append({
                "rule_id": "kdp_cover_dimensions",
                "severity": "error",
                "message": "Cover image file not found",
                "location": "metadata.cover_path"
            })
            return issues

        try:
            from PIL import Image
            with Image.open(metadata.cover_path) as img:
                width, height = img.size

                if width < profile.cover_required_width or height < profile.cover_required_height:
                    issues.append({
                        "rule_id": "kdp_cover_dimensions",
                        "severity": "error",
                        "message": f"Cover image too small: {width}x{height}. Minimum: {profile.cover_required_width}x{profile.cover_required_height}",
                        "location": str(metadata.cover_path)
                    })

                # Check aspect ratio
                aspect_ratio = width / height
                expected_ratio = 1600 / 2560  # 0.625
                if abs(aspect_ratio - expected_ratio) > 0.1:
                    issues.append({
                        "rule_id": "kdp_cover_dimensions",
                        "severity": "warning",
                        "message": f"Cover aspect ratio {aspect_ratio:.2f} differs from recommended 1.6:1 ({expected_ratio:.2f})",
                        "location": str(metadata.cover_path)
                    })

        except Exception as e:
            issues.append({
                "rule_id": "kdp_cover_dimensions",
                "severity": "error",
                "message": f"Could not read cover image: {e}",
                "location": str(metadata.cover_path)
            })

        return issues

    def _check_file_size(self, epub_path: Path, profile: StoreRequirements) -> List[Dict[str, Any]]:
        """Check EPUB file size."""
        issues = []

        if not epub_path.exists():
            return issues

        file_size_mb = epub_path.stat().st_size / (1024 * 1024)

        if profile.max_file_size_mb and file_size_mb > profile.max_file_size_mb:
            issues.append({
                "rule_id": "file_size_limit",
                "severity": "error",
                "message": f"File size {file_size_mb:.1f}MB exceeds limit of {profile.max_file_size_mb}MB",
                "location": str(epub_path)
            })

        return issues

    def _check_isbn_present(self, metadata: EpubMetadata) -> List[Dict[str, Any]]:
        """Check if ISBN is present."""
        issues = []

        if not metadata.isbn:
            issues.append({
                "rule_id": "isbn_required",
                "severity": "error",
                "message": "ISBN is required for this store",
                "location": "metadata.isbn"
            })

        return issues

    def _check_epub_version(self, profile: StoreRequirements) -> List[Dict[str, Any]]:
        """Check EPUB version compatibility."""
        # This would typically parse the EPUB's container.xml and package.opf
        # For now, return empty (would need actual EPUB parsing)
        return []

    def _check_css_features(self, epub_path: Path, profile: StoreRequirements) -> List[Dict[str, Any]]:
        """Check CSS feature usage."""
        # This would parse CSS files in the EPUB
        # For now, return empty (would need CSS parsing)
        return []

    def _check_font_formats(self, epub_path: Path, profile: StoreRequirements) -> List[Dict[str, Any]]:
        """Check embedded font formats."""
        # This would check fonts in the EPUB
        # For now, return empty (would need EPUB parsing)
        return []

    def _check_kdp_css_positioning(self, epub_path: Path) -> List[Dict[str, Any]]:
        """Check for problematic CSS positioning for KDP."""
        # This would parse CSS files and check for forbidden properties
        # For now, return empty (would need CSS parsing)
        return []

    def _check_epubcheck(self, epub_path: Path) -> List[Dict[str, Any]]:
        """Run EPUBCheck validation."""
        # This would integrate with the existing EPUBCheck functionality
        # For now, return empty
        return []

    def generate_store_css(self, profile_name: StoreProfile) -> str:
        """Generate store-optimized CSS."""
        profile = self.get_profile(profile_name)

        css_parts = [
            f"/* CSS optimized for {profile.name} */",
            f"/* Profile: {profile.description} */",
            "",
        ]

        # Add base styles safe for all stores
        css_parts.extend([
            "/* Base typography */",
            "body {",
            "    font-family: Georgia, 'Times New Roman', Times, serif;",
            "    line-height: 1.6;",
            "    margin: 1.5em;",
            "    text-align: left;",
            "}",
            "",
            "h1, h2, h3, h4, h5, h6 {",
            "    page-break-after: avoid;",
            "    margin-top: 1.5em;",
            "    margin-bottom: 0.75em;",
            "}",
            "",
            "p {",
            "    orphans: 2;",
            "    widows: 2;",
            "    margin: 0 0 1em 0;",
            "}",
            "",
        ])

        # Add store-specific optimizations
        if profile_name == StoreProfile.KDP:
            css_parts.extend([
                "/* Kindle-optimized styles */",
                "/* Avoid problematic properties for Kindle */",
                ".float-left, .float-right { /* Remove float */ }",
                ".position-absolute, .position-fixed { /* Remove positioning */ }",
                "",
                "/* Kindle-safe text alignment */",
                ".text-center { text-align: center; }",
                ".text-left { text-align: left; }",
                ".text-right { text-align: right; }",
                "",
            ])

        elif profile_name == StoreProfile.APPLE:
            css_parts.extend([
                "/* Apple Books enhanced styles */",
                "/* Take advantage of modern CSS support */",
                "@media (prefers-color-scheme: dark) {",
                "    body { background: #1a1a1a; color: #e6e6e6; }",
                "}",
                "",
                "/* Flexbox support for Apple Books */",
                ".flex-container {",
                "    display: flex;",
                "    align-items: center;",
                "    justify-content: space-between;",
                "}",
                "",
            ])

        elif profile_name == StoreProfile.KOBO:
            css_parts.extend([
                "/* Kobo-optimized styles */",
                "/* Conservative CSS for wide device compatibility */",
                ".kobo-safe {",
                "    display: block;",
                "    position: relative;",
                "}",
                "",
            ])

        return "\n".join(css_parts)

    def get_validation_summary(self, profile_name: StoreProfile, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate validation summary for a profile."""
        profile = self.get_profile(profile_name)

        error_count = len([i for i in issues if i["severity"] == "error"])
        warning_count = len([i for i in issues if i["severity"] == "warning"])
        info_count = len([i for i in issues if i["severity"] == "info"])

        status = "pass" if error_count == 0 else "fail"
        if error_count == 0 and warning_count > 0:
            status = "pass_with_warnings"

        return {
            "profile": profile_name.value,
            "profile_name": profile.name,
            "status": status,
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "issues": issues
        }


def validate_for_store(
    profile_name: StoreProfile,
    epub_path: Path,
    metadata: EpubMetadata
) -> Dict[str, Any]:
    """
    Validate EPUB for specific store requirements.

    Args:
        profile_name: Target store profile
        epub_path: Path to EPUB file
        metadata: EPUB metadata

    Returns:
        Validation summary with issues
    """
    manager = StoreProfileManager()
    issues = manager.validate_epub(profile_name, epub_path, metadata)
    return manager.get_validation_summary(profile_name, issues)


def get_store_css(profile_name: StoreProfile) -> str:
    """
    Get store-optimized CSS for a profile.

    Args:
        profile_name: Target store profile

    Returns:
        CSS optimized for the store
    """
    manager = StoreProfileManager()
    return manager.generate_store_css(profile_name)