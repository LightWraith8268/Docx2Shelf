from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, AttributeError):
    HAS_PIL = False

from .bisac import validate_bisac_code, validate_isbn_format
from .metadata import EpubMetadata


@dataclass
class ChecklistIssue:
    """Represents an issue found during checklist validation."""

    severity: str  # "error", "warning", "info"
    category: str  # "cover", "metadata", "content", "format"
    message: str
    fix_suggestion: Optional[str] = None
    store: Optional[str] = None  # Which store this applies to


@dataclass
class ChecklistResult:
    """Results of running a publishing checklist."""

    store: str
    issues: List[ChecklistIssue]
    passed: bool

    @property
    def errors(self) -> List[ChecklistIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ChecklistIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> List[ChecklistIssue]:
        return [i for i in self.issues if i.severity == "info"]


class PublishingChecker:
    """Base class for store-specific publishing checklist validation."""

    def __init__(self, store_name: str):
        self.store_name = store_name
        self.issues: List[ChecklistIssue] = []

    def add_issue(self, severity: str, category: str, message: str,
                  fix_suggestion: Optional[str] = None):
        """Add an issue to the checklist results."""
        issue = ChecklistIssue(
            severity=severity,
            category=category,
            message=message,
            fix_suggestion=fix_suggestion,
            store=self.store_name
        )
        self.issues.append(issue)

    def check_cover_image(self, cover_path: Path) -> None:
        """Check cover image requirements."""
        if not cover_path or not cover_path.exists():
            self.add_issue("error", "cover", "Cover image file not found",
                          "Provide a cover image file")
            return

        if not HAS_PIL:
            self.add_issue("info", "cover",
                          "Image analysis skipped (PIL/Pillow not installed)",
                          "Install Pillow for detailed cover validation: pip install Pillow")
            return

        try:
            with Image.open(cover_path) as img:
                width, height = img.size
                self._check_cover_dimensions(width, height)
                self._check_cover_format(img.format, cover_path.suffix)
                self._check_cover_file_size(cover_path)
        except Exception as e:
            self.add_issue("error", "cover", f"Cannot read cover image: {e}",
                          "Ensure cover image is a valid image file")

    def check_metadata(self, metadata: EpubMetadata) -> None:
        """Check metadata requirements."""
        # Basic required fields
        if not metadata.title:
            self.add_issue("error", "metadata", "Title is required")

        if not metadata.author:
            self.add_issue("error", "metadata", "Author is required")

        if not metadata.language:
            self.add_issue("error", "metadata", "Language is required")

        # ISBN validation
        if metadata.isbn:
            is_valid, error = validate_isbn_format(metadata.isbn)
            if not is_valid:
                self.add_issue("warning", "metadata", f"ISBN issue: {error}")

        # BISAC code validation
        if metadata.bisac_codes:
            for code in metadata.bisac_codes:
                is_valid, error = validate_bisac_code(code)
                if not is_valid:
                    self.add_issue("warning", "metadata", f"BISAC code issue: {error}")

    def _check_cover_dimensions(self, width: int, height: int) -> None:
        """Override in subclasses for store-specific dimension requirements."""
        pass

    def _check_cover_format(self, format_name: str, file_ext: str) -> None:
        """Override in subclasses for store-specific format requirements."""
        pass

    def _check_cover_file_size(self, cover_path: Path) -> None:
        """Override in subclasses for store-specific file size requirements."""
        pass

    def run_checks(self, metadata: EpubMetadata, cover_path: Optional[Path] = None) -> ChecklistResult:
        """Run all checks and return results."""
        self.issues = []  # Reset issues

        self.check_metadata(metadata)

        if cover_path:
            self.check_cover_image(cover_path)

        # Additional store-specific checks
        self._run_store_specific_checks(metadata)

        # Determine if all checks passed (no errors)
        has_errors = any(issue.severity == "error" for issue in self.issues)

        return ChecklistResult(
            store=self.store_name,
            issues=self.issues.copy(),
            passed=not has_errors
        )

    def _run_store_specific_checks(self, metadata: EpubMetadata) -> None:
        """Override in subclasses for additional store-specific validation."""
        pass


class KDPChecker(PublishingChecker):
    """Amazon Kindle Direct Publishing checklist validator."""

    def __init__(self):
        super().__init__("KDP")

    def _check_cover_dimensions(self, width: int, height: int) -> None:
        # KDP cover requirements
        aspect_ratio = width / height

        if width < 1000 or height < 1600:
            self.add_issue("error", "cover",
                          f"Cover too small ({width}x{height}). KDP requires minimum 1000x1600px",
                          "Resize cover to at least 1000x1600 pixels")

        if aspect_ratio < 1.4 or aspect_ratio > 1.8:
            self.add_issue("warning", "cover",
                          f"Cover aspect ratio {aspect_ratio:.2f} outside recommended 1.4-1.8 range",
                          "Adjust cover dimensions for better KDP compatibility")

        # Ideal dimensions check
        if width < 1600 or height < 2560:
            self.add_issue("info", "cover",
                          "For best quality, KDP recommends 1600x2560px or higher")

    def _check_cover_format(self, format_name: str, file_ext: str) -> None:
        allowed_formats = ["JPEG", "JPG", "PNG", "TIFF", "TIF"]
        if format_name not in allowed_formats:
            self.add_issue("error", "cover",
                          f"Cover format '{format_name}' not supported by KDP",
                          "Use JPEG, PNG, or TIFF format")

    def _check_cover_file_size(self, cover_path: Path) -> None:
        file_size_mb = cover_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            self.add_issue("error", "cover",
                          f"Cover file too large ({file_size_mb:.1f}MB). KDP limit is 50MB",
                          "Compress cover image to under 50MB")

    def _run_store_specific_checks(self, metadata: EpubMetadata) -> None:
        # Description length check
        if metadata.description:
            if len(metadata.description) > 4000:
                self.add_issue("warning", "metadata",
                              f"Description too long ({len(metadata.description)} chars). KDP limit is 4000",
                              "Shorten description to under 4000 characters")

        # Title length check
        if metadata.title and len(metadata.title) > 200:
            self.add_issue("warning", "metadata",
                          f"Title too long ({len(metadata.title)} chars). KDP recommends under 200",
                          "Consider shortening title")

        # Series validation
        if metadata.series:
            if len(metadata.series) > 100:
                self.add_issue("warning", "metadata",
                              "Series name longer than 100 characters",
                              "Shorten series name for better display")

        # Age range validation for KDP
        if metadata.target_audience == "children" and not metadata.age_range:
            self.add_issue("warning", "metadata",
                          "Children's books should specify age range for better categorization")


class AppleChecker(PublishingChecker):
    """Apple Books checklist validator."""

    def __init__(self):
        super().__init__("Apple Books")

    def _check_cover_dimensions(self, width: int, height: int) -> None:
        # Apple Books cover requirements
        aspect_ratio = width / height

        if width < 1400 or height < 1400:
            self.add_issue("error", "cover",
                          f"Cover too small ({width}x{height}). Apple requires minimum 1400x1400px",
                          "Resize cover to at least 1400px on shortest side")

        if aspect_ratio < 1.0 or aspect_ratio > 2.0:
            self.add_issue("warning", "cover",
                          f"Cover aspect ratio {aspect_ratio:.2f} outside recommended 1.0-2.0 range",
                          "Apple Books works best with square to 2:1 ratio covers")

        # High-res recommendation
        if width < 2048 or height < 2048:
            self.add_issue("info", "cover",
                          "Apple recommends 2048px minimum on shortest side for Retina displays")

    def _check_cover_format(self, format_name: str, file_ext: str) -> None:
        # Apple prefers RGB JPEG or PNG
        allowed_formats = ["JPEG", "JPG", "PNG"]
        if format_name not in allowed_formats:
            self.add_issue("warning", "cover",
                          f"Cover format '{format_name}' may not be optimal for Apple Books",
                          "Use JPEG or PNG format for best compatibility")

    def _check_cover_file_size(self, cover_path: Path) -> None:
        file_size_mb = cover_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 2:
            self.add_issue("info", "cover",
                          f"Large cover file ({file_size_mb:.1f}MB). Consider optimizing for faster downloads")

    def _run_store_specific_checks(self, metadata: EpubMetadata) -> None:
        # Apple requires proper language codes
        if metadata.language:
            # Apple is stricter about language codes
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', metadata.language):
                self.add_issue("warning", "metadata",
                              f"Language code '{metadata.language}' may not be recognized by Apple",
                              "Use ISO 639-1 codes (e.g., 'en', 'en-US')")

        # Copyright information strongly recommended
        if not metadata.copyright_holder and not metadata.rights:
            self.add_issue("info", "metadata",
                          "Copyright information recommended for Apple Books")

        # Publisher information recommended
        if not metadata.publisher:
            self.add_issue("info", "metadata",
                          "Publisher information recommended for professional appearance")


class KoboChecker(PublishingChecker):
    """Kobo checklist validator."""

    def __init__(self):
        super().__init__("Kobo")

    def _check_cover_dimensions(self, width: int, height: int) -> None:
        # Kobo cover requirements
        aspect_ratio = width / height

        if width < 1200 or height < 1800:
            self.add_issue("error", "cover",
                          f"Cover too small ({width}x{height}). Kobo requires minimum 1200x1800px",
                          "Resize cover to at least 1200x1800 pixels")

        if aspect_ratio < 1.33 or aspect_ratio > 1.67:
            self.add_issue("warning", "cover",
                          f"Cover aspect ratio {aspect_ratio:.2f} outside recommended 1.33-1.67 range (4:3 to 3:2)",
                          "Adjust cover for optimal Kobo display")

        # Ideal size check
        if width < 1600 or height < 2400:
            self.add_issue("info", "cover",
                          "Kobo recommends 1600x2400px or higher for best quality")

    def _check_cover_format(self, format_name: str, file_ext: str) -> None:
        allowed_formats = ["JPEG", "JPG", "PNG"]
        if format_name not in allowed_formats:
            self.add_issue("warning", "cover",
                          f"Cover format '{format_name}' may cause issues with Kobo",
                          "Use JPEG or PNG format")

    def _check_cover_file_size(self, cover_path: Path) -> None:
        file_size_mb = cover_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10:
            self.add_issue("warning", "cover",
                          f"Cover file large ({file_size_mb:.1f}MB). Kobo recommends under 10MB",
                          "Compress cover image for better performance")

    def _run_store_specific_checks(self, metadata: EpubMetadata) -> None:
        # Kobo-specific metadata checks
        if metadata.description:
            if len(metadata.description) < 50:
                self.add_issue("warning", "metadata",
                              "Description very short. Kobo recommends detailed descriptions for discoverability")

        # Category/genre information important for Kobo
        if not metadata.bisac_codes and not metadata.subjects:
            self.add_issue("warning", "metadata",
                          "No category information found. Add BISAC codes or subjects for better discoverability")

        # Price information check
        if metadata.price and metadata.currency:
            # Basic price format validation
            try:
                price_val = float(metadata.price)
                if price_val < 0:
                    self.add_issue("error", "metadata", "Price cannot be negative")
            except ValueError:
                self.add_issue("error", "metadata", f"Invalid price format: '{metadata.price}'")


def get_checker(store: str) -> PublishingChecker:
    """Get the appropriate checker for a publishing store."""
    store_lower = store.lower()

    if store_lower in ["kdp", "amazon", "kindle"]:
        return KDPChecker()
    elif store_lower in ["apple", "ibooks", "apple books"]:
        return AppleChecker()
    elif store_lower in ["kobo"]:
        return KoboChecker()
    else:
        # Generic checker for unknown stores
        return PublishingChecker(store)


def run_all_checklists(metadata: EpubMetadata,
                      cover_path: Optional[Path] = None) -> Dict[str, ChecklistResult]:
    """Run checklists for all major publishing stores."""
    stores = ["KDP", "Apple Books", "Kobo"]
    results = {}

    for store in stores:
        checker = get_checker(store)
        result = checker.run_checks(metadata, cover_path)
        results[store] = result

    return results


def format_checklist_report(results: Dict[str, ChecklistResult]) -> str:
    """Format checklist results into a readable report."""
    lines = ["Publishing Store Compatibility Report", "=" * 40, ""]

    for store, result in results.items():
        lines.append(f"[{store}]")
        lines.append("-" * len(f"[{store}]"))

        if result.passed:
            lines.append("PASS: All critical checks passed")
        else:
            lines.append(f"FAIL: {len(result.errors)} critical issue(s) found")

        # Show errors first
        for issue in result.errors:
            lines.append(f"   ERROR: {issue.message}")
            if issue.fix_suggestion:
                lines.append(f"          Fix: {issue.fix_suggestion}")

        # Then warnings
        for issue in result.warnings:
            lines.append(f"   WARNING: {issue.message}")
            if issue.fix_suggestion:
                lines.append(f"            Fix: {issue.fix_suggestion}")

        # Finally info
        for issue in result.infos:
            lines.append(f"   INFO: {issue.message}")

        lines.append("")

    # Summary
    total_errors = sum(len(r.errors) for r in results.values())
    total_warnings = sum(len(r.warnings) for r in results.values())
    stores_passed = sum(1 for r in results.values() if r.passed)

    lines.append("Summary")
    lines.append("-" * 7)
    lines.append(f"Stores ready for publishing: {stores_passed}/{len(results)}")
    lines.append(f"Total errors: {total_errors}")
    lines.append(f"Total warnings: {total_warnings}")

    return "\n".join(lines)