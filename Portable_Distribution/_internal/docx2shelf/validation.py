"""
EPUB validation utilities for ensuring high-quality EPUB output.

This module provides comprehensive EPUB validation using EPUBCheck and custom
validation rules to catch common issues before publication.
"""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ValidationIssue:
    """Represents a validation issue found in an EPUB."""
    severity: str  # "error", "warning", "info"
    message: str
    location: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of EPUB validation."""
    is_valid: bool
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]
    info: List[ValidationIssue]
    epubcheck_available: bool
    custom_checks_run: bool

    @property
    def total_issues(self) -> int:
        """Total number of issues found."""
        return len(self.errors) + len(self.warnings) + len(self.info)

    @property
    def has_errors(self) -> bool:
        """Whether any errors were found."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Whether any warnings were found."""
        return len(self.warnings) > 0


class EPUBValidator:
    """Comprehensive EPUB validation using EPUBCheck and custom rules."""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        self.epubcheck_available = self._check_epubcheck_availability()

    def _check_epubcheck_availability(self) -> bool:
        """Check if EPUBCheck is available."""
        from .tools import epubcheck_cmd
        return epubcheck_cmd() is not None

    def validate(self, epub_path: Path, custom_checks: bool = True) -> ValidationResult:
        """
        Perform comprehensive EPUB validation.

        Args:
            epub_path: Path to the EPUB file to validate
            custom_checks: Whether to run custom validation checks

        Returns:
            ValidationResult with all found issues
        """
        errors = []
        warnings = []
        info = []

        # Run EPUBCheck validation
        if self.epubcheck_available:
            epubcheck_result = self._run_epubcheck(epub_path)
            errors.extend(epubcheck_result["errors"])
            warnings.extend(epubcheck_result["warnings"])
            info.extend(epubcheck_result["info"])

        # Run custom validation checks
        custom_checks_run = False
        if custom_checks:
            try:
                custom_result = self._run_custom_checks(epub_path)
                errors.extend(custom_result["errors"])
                warnings.extend(custom_result["warnings"])
                info.extend(custom_result["info"])
                custom_checks_run = True
            except Exception as e:
                warnings.append(ValidationIssue(
                    severity="warning",
                    message=f"Custom validation checks failed: {e}",
                    rule="custom_check_error"
                ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            epubcheck_available=self.epubcheck_available,
            custom_checks_run=custom_checks_run
        )

    def _run_epubcheck(self, epub_path: Path) -> Dict[str, List[ValidationIssue]]:
        """Run EPUBCheck validation."""
        from .tools import epubcheck_cmd

        errors = []
        warnings = []
        info = []

        try:
            cmd = epubcheck_cmd()
            if not cmd:
                return {"errors": errors, "warnings": warnings, "info": info}

            # Try to get JSON output first, fall back to text
            proc = subprocess.run(
                cmd + ["--json", str(epub_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if proc.returncode != 0:
                # Try text output if JSON failed
                proc = subprocess.run(
                    cmd + [str(epub_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

            # Parse output
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")

            # Try to parse as JSON first
            try:
                if proc.stdout and proc.stdout.strip().startswith('{'):
                    json_output = json.loads(proc.stdout)
                    return self._parse_epubcheck_json(json_output)
            except json.JSONDecodeError:
                pass

            # Fall back to text parsing
            return self._parse_epubcheck_text(output)

        except subprocess.TimeoutExpired:
            errors.append(ValidationIssue(
                severity="error",
                message="EPUBCheck validation timed out",
                rule="epubcheck_timeout"
            ))
        except Exception as e:
            errors.append(ValidationIssue(
                severity="error",
                message=f"EPUBCheck validation failed: {e}",
                rule="epubcheck_error"
            ))

        return {"errors": errors, "warnings": warnings, "info": info}

    def _parse_epubcheck_json(
        self, json_output: Dict[str, Any]
    ) -> Dict[str, List[ValidationIssue]]:
        """Parse EPUBCheck JSON output."""
        errors = []
        warnings = []
        info = []

        messages = json_output.get("messages", [])
        for msg in messages:
            severity = msg.get("severity", "").lower()

            issue = ValidationIssue(
                severity=severity,
                message=msg.get("message", ""),
                location=msg.get("location", {}).get("path"),
                line=msg.get("location", {}).get("line"),
                column=msg.get("location", {}).get("column"),
                rule=msg.get("id")
            )

            if severity == "error" or severity == "fatal":
                errors.append(issue)
            elif severity == "warning":
                warnings.append(issue)
            else:
                info.append(issue)

        return {"errors": errors, "warnings": warnings, "info": info}

    def _parse_epubcheck_text(self, output: str) -> Dict[str, List[ValidationIssue]]:
        """Parse EPUBCheck text output."""
        errors = []
        warnings = []
        info = []

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Parse line format: SEVERITY(location): message
            severity = None
            message = line
            location = None

            if "ERROR" in line.upper():
                severity = "error"
            elif "WARNING" in line.upper():
                severity = "warning"
            elif "INFO" in line.upper():
                severity = "info"
            else:
                continue

            # Try to extract location and message
            if "(" in line and "):" in line:
                parts = line.split("(", 1)
                if len(parts) == 2:
                    location_part = parts[1].split("):", 1)[0]
                    message_part = parts[1].split("):", 1)[1].strip()
                    location = location_part
                    message = message_part

            issue = ValidationIssue(
                severity=severity,
                message=message,
                location=location,
                rule="epubcheck_text_parse"
            )

            if severity == "error":
                errors.append(issue)
            elif severity == "warning":
                warnings.append(issue)
            else:
                info.append(issue)

        return {"errors": errors, "warnings": warnings, "info": info}

    def _run_custom_checks(self, epub_path: Path) -> Dict[str, List[ValidationIssue]]:
        """Run custom validation checks."""
        errors = []
        warnings = []
        info = []

        try:
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                # Check for required files
                required_files = ['META-INF/container.xml', 'mimetype']
                for required_file in required_files:
                    if required_file not in epub_zip.namelist():
                        errors.append(ValidationIssue(
                            severity="error",
                            message=f"Required file missing: {required_file}",
                            rule="missing_required_file"
                        ))

                # Check mimetype content
                if 'mimetype' in epub_zip.namelist():
                    mimetype_content = epub_zip.read('mimetype').decode('utf-8').strip()
                    if mimetype_content != 'application/epub+zip':
                        errors.append(ValidationIssue(
                            severity="error",
                            message=f"Invalid mimetype: {mimetype_content}",
                            rule="invalid_mimetype"
                        ))

                # Check for large images
                for file_info in epub_zip.filelist:
                    if file_info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        if file_info.file_size > 2 * 1024 * 1024:  # 2MB
                            warnings.append(ValidationIssue(
                                severity="warning",
                                message=(
                            f"Large image file: {file_info.filename} "
                            f"({file_info.file_size // 1024}KB)"
                        ),
                                location=file_info.filename,
                                rule="large_image_file"
                            ))

                # Check for proper OPF structure
                container_content = epub_zip.read('META-INF/container.xml').decode('utf-8')
                try:
                    container_xml = ET.fromstring(container_content)
                    opf_path = None
                    for rootfile in container_xml.findall(
                        './/{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'
                    ):
                        opf_path = rootfile.get('full-path')
                        break

                    if opf_path and opf_path in epub_zip.namelist():
                        opf_content = epub_zip.read(opf_path).decode('utf-8')
                        self._validate_opf_content(opf_content, opf_path, warnings, info)
                    else:
                        errors.append(ValidationIssue(
                            severity="error",
                            message="OPF file not found or not listed in container.xml",
                            rule="missing_opf_file"
                        ))

                except ET.ParseError as e:
                    errors.append(ValidationIssue(
                        severity="error",
                        message=f"XML parsing error in container.xml: {e}",
                        rule="xml_parse_error"
                    ))

        except zipfile.BadZipFile:
            errors.append(ValidationIssue(
                severity="error",
                message="EPUB file is corrupted or not a valid ZIP archive",
                rule="invalid_zip_file"
            ))

        return {"errors": errors, "warnings": warnings, "info": info}

    def _validate_opf_content(
        self,
        opf_content: str,
        opf_path: str,
        warnings: List[ValidationIssue],
        info: List[ValidationIssue]
    ):
        """Validate OPF file content."""
        try:
            opf_xml = ET.fromstring(opf_content)

            # Check for required metadata
            metadata_elem = opf_xml.find('.//{http://www.idpf.org/2007/opf}metadata')
            if metadata_elem is not None:
                # Check for title
                title_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}title')
                if title_elem is None or not title_elem.text:
                    warnings.append(ValidationIssue(
                        severity="warning",
                        message="No title found in metadata",
                        location=opf_path,
                        rule="missing_title"
                    ))

                # Check for author
                creator_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}creator')
                if creator_elem is None or not creator_elem.text:
                    warnings.append(ValidationIssue(
                        severity="warning",
                        message="No author found in metadata",
                        location=opf_path,
                        rule="missing_author"
                    ))

                # Check for language
                language_elem = metadata_elem.find('.//{http://purl.org/dc/elements/1.1/}language')
                if language_elem is None or not language_elem.text:
                    warnings.append(ValidationIssue(
                        severity="warning",
                        message="No language specified in metadata",
                        location=opf_path,
                        rule="missing_language"
                    ))

            # Check manifest and spine consistency
            manifest_items = {}
            manifest_elem = opf_xml.find('.//{http://www.idpf.org/2007/opf}manifest')
            if manifest_elem is not None:
                for item in manifest_elem.findall('.//{http://www.idpf.org/2007/opf}item'):
                    item_id = item.get('id')
                    if item_id:
                        manifest_items[item_id] = item.get('href')

            spine_elem = opf_xml.find('.//{http://www.idpf.org/2007/opf}spine')
            if spine_elem is not None:
                for itemref in spine_elem.findall('.//{http://www.idpf.org/2007/opf}itemref'):
                    idref = itemref.get('idref')
                    if idref and idref not in manifest_items:
                        warnings.append(ValidationIssue(
                            severity="warning",
                            message=f"Spine references missing manifest item: {idref}",
                            location=opf_path,
                            rule="spine_manifest_mismatch"
                        ))

        except ET.ParseError as e:
            warnings.append(ValidationIssue(
                severity="warning",
                message=f"XML parsing error in OPF file: {e}",
                location=opf_path,
                rule="opf_xml_parse_error"
            ))


def validate_epub(
    epub_path: Path, custom_checks: bool = True, timeout: int = 120
) -> ValidationResult:
    """
    Convenience function to validate an EPUB file.

    Args:
        epub_path: Path to the EPUB file
        custom_checks: Whether to run custom validation checks
        timeout: Timeout for EPUBCheck in seconds

    Returns:
        ValidationResult with all found issues
    """
    validator = EPUBValidator(timeout=timeout)
    return validator.validate(epub_path, custom_checks=custom_checks)


def print_validation_report(result: ValidationResult, verbose: bool = False) -> None:
    """
    Print a formatted validation report.

    Args:
        result: ValidationResult to format
        verbose: Whether to show detailed issue information
    """
    print("\n" + "=" * 50)
    print("[VALIDATION] EPUB Validation Report")
    print("=" * 50)

    # Overall status
    if result.is_valid:
        print("[SUCCESS] EPUB validation passed")
    else:
        print(f"[ERROR] EPUB validation failed with {len(result.errors)} error(s)")

    # Summary
    print("\nSummary:")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Info: {len(result.info)}")
    print(f"  EPUBCheck available: {'Yes' if result.epubcheck_available else 'No'}")
    print(f"  Custom checks run: {'Yes' if result.custom_checks_run else 'No'}")

    if not result.epubcheck_available:
        print("\n[INFO] Install EPUBCheck for industry-standard validation:")
        print("  docx2shelf tools install epubcheck")

    # Show issues
    if verbose and result.total_issues > 0:
        print("\nDetailed Issues:")

        for error in result.errors:
            location = f" ({error.location})" if error.location else ""
            print(f"  [ERROR]{location}: {error.message}")

        for warning in result.warnings:
            location = f" ({warning.location})" if warning.location else ""
            print(f"  [WARNING]{location}: {warning.message}")

        for info_item in result.info:
            location = f" ({info_item.location})" if info_item.location else ""
            print(f"  [INFO]{location}: {info_item.message}")

    elif result.total_issues > 0:
        print("\nTop Issues (use --verbose for full list):")

        # Show first few critical issues
        critical_issues = result.errors[:3] + result.warnings[:3]
        for issue in critical_issues:
            location = f" ({issue.location})" if issue.location else ""
            severity_tag = f"[{issue.severity.upper()}]"
            print(f"  {severity_tag}{location}: {issue.message}")

        if result.total_issues > 6:
            print(f"  ... and {result.total_issues - 6} more issues")

    print("")