"""
Accessibility audit system for EPUB content.

Performs comprehensive accessibility checks and generates detailed reports
with actionable recommendations for improving EPUB accessibility compliance.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class A11yLevel(Enum):
    """Accessibility conformance levels."""
    A = "A"        # WCAG Level A
    AA = "AA"      # WCAG Level AA
    AAA = "AAA"    # WCAG Level AAA


class IssueType(Enum):
    """Types of accessibility issues."""
    MISSING_ALT_TEXT = "missing_alt_text"
    HEADING_STRUCTURE = "heading_structure"
    COLOR_CONTRAST = "color_contrast"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    SEMANTIC_MARKUP = "semantic_markup"
    READING_ORDER = "reading_order"
    LANGUAGE_ATTRIBUTES = "language_attributes"
    LINK_ACCESSIBILITY = "link_accessibility"
    TABLE_ACCESSIBILITY = "table_accessibility"
    FORM_ACCESSIBILITY = "form_accessibility"
    MEDIA_ACCESSIBILITY = "media_accessibility"
    FOCUS_MANAGEMENT = "focus_management"


class IssueSeverity(Enum):
    """Severity levels for accessibility issues."""
    CRITICAL = "critical"  # WCAG failure, blocks access
    MAJOR = "major"        # Significant barrier
    MINOR = "minor"        # Minor improvement
    INFO = "info"          # Best practice recommendation


@dataclass
class A11yIssue:
    """Accessibility issue found during audit."""
    id: str
    issue_type: IssueType
    severity: IssueSeverity
    wcag_level: A11yLevel
    title: str
    description: str
    location: str = ""
    line_number: Optional[int] = None
    element: str = ""
    recommendation: str = ""
    auto_fixable: bool = False
    wcag_criteria: List[str] = field(default_factory=list)


@dataclass
class A11yConfig:
    """Configuration for accessibility audit."""
    target_level: A11yLevel = A11yLevel.AA
    check_color_contrast: bool = True
    check_heading_structure: bool = True
    check_alt_text: bool = True
    check_semantic_markup: bool = True
    check_keyboard_navigation: bool = True
    check_language_attributes: bool = True
    generate_detailed_report: bool = True
    auto_fix_issues: bool = False


@dataclass
class A11yAuditResult:
    """Results of accessibility audit."""
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    info_issues: int
    issues_by_type: Dict[IssueType, int]
    conformance_level: Optional[A11yLevel]
    overall_score: float  # 0-100 percentage
    issues: List[A11yIssue]
    recommendations: List[str]
    auto_fixes_applied: int = 0


class AccessibilityAuditor:
    """Performs comprehensive accessibility audits on EPUB content."""

    def __init__(self, config: Optional[A11yConfig] = None):
        self.config = config or A11yConfig()
        self.issues: List[A11yIssue] = []
        self.image_alt_texts: Set[str] = set()
        self.heading_structure: List[Tuple[int, str]] = []

    def audit_epub(self, epub_path: Path) -> A11yAuditResult:
        """
        Perform comprehensive accessibility audit on EPUB.

        Args:
            epub_path: Path to EPUB file

        Returns:
            A11yAuditResult with detailed findings
        """
        logger.info(f"Starting accessibility audit of {epub_path}")

        self.issues.clear()
        self.image_alt_texts.clear()
        self.heading_structure.clear()

        # Extract and audit EPUB content
        try:
            content_files = self._extract_epub_content(epub_path)

            for file_path, content in content_files.items():
                self._audit_html_content(content, str(file_path))

            # Perform cross-file checks
            self._audit_heading_structure()
            self._audit_language_consistency()

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            self.issues.append(A11yIssue(
                id="audit_error",
                issue_type=IssueType.SEMANTIC_MARKUP,
                severity=IssueSeverity.CRITICAL,
                wcag_level=A11yLevel.A,
                title="Audit Error",
                description=f"Failed to audit EPUB: {e}",
                recommendation="Check EPUB file integrity"
            ))

        # Generate audit result
        return self._generate_audit_result()

    def _extract_epub_content(self, epub_path: Path) -> Dict[Path, str]:
        """Extract HTML content files from EPUB."""
        content_files = {}

        try:
            import zipfile

            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                # Find content files (XHTML/HTML)
                file_list = epub_zip.namelist()
                html_files = [f for f in file_list if f.endswith(('.html', '.xhtml', '.htm'))]

                for html_file in html_files:
                    try:
                        content = epub_zip.read(html_file).decode('utf-8')
                        content_files[Path(html_file)] = content
                    except Exception as e:
                        logger.warning(f"Could not read {html_file}: {e}")

        except Exception as e:
            logger.error(f"Could not extract EPUB content: {e}")

        return content_files

    def _audit_html_content(self, content: str, file_path: str) -> None:
        """Audit HTML content for accessibility issues."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
        except ImportError:
            logger.warning("BeautifulSoup not available, using basic parsing")
            self._basic_audit_html(content, file_path)
            return

        # Check various accessibility aspects
        self._check_alt_text(soup, file_path)
        self._check_heading_structure_file(soup, file_path)
        self._check_semantic_markup(soup, file_path)
        self._check_language_attributes(soup, file_path)
        self._check_link_accessibility(soup, file_path)
        self._check_table_accessibility(soup, file_path)
        self._check_form_accessibility(soup, file_path)
        self._check_keyboard_navigation(soup, file_path)
        self._check_reading_order(soup, file_path)

    def _basic_audit_html(self, content: str, file_path: str) -> None:
        """Basic HTML audit without BeautifulSoup."""
        # Check for images without alt text
        img_pattern = r'<img(?![^>]*alt\s*=)[^>]*>'
        missing_alt = re.findall(img_pattern, content, re.IGNORECASE)

        for match in missing_alt:
            self.issues.append(A11yIssue(
                id=f"missing_alt_{len(self.issues)}",
                issue_type=IssueType.MISSING_ALT_TEXT,
                severity=IssueSeverity.CRITICAL,
                wcag_level=A11yLevel.A,
                title="Missing Alt Text",
                description="Image found without alt attribute",
                location=file_path,
                element=match[:100],
                recommendation="Add descriptive alt text for all images",
                wcag_criteria=["1.1.1"]
            ))

    def _check_alt_text(self, soup, file_path: str) -> None:
        """Check image alt text accessibility."""
        if not self.config.check_alt_text:
            return

        images = soup.find_all('img')

        for img in images:
            alt_text = img.get('alt', '').strip()
            src = img.get('src', '')

            if not alt_text:
                # Check if image is decorative (should have empty alt)
                is_decorative = self._is_decorative_image(img)

                severity = IssueSeverity.MINOR if is_decorative else IssueSeverity.CRITICAL

                self.issues.append(A11yIssue(
                    id=f"missing_alt_{len(self.issues)}",
                    issue_type=IssueType.MISSING_ALT_TEXT,
                    severity=severity,
                    wcag_level=A11yLevel.A,
                    title="Missing Alt Text",
                    description=f"Image '{src}' missing alt attribute",
                    location=file_path,
                    element=str(img)[:100],
                    recommendation="Add descriptive alt text or empty alt='' for decorative images",
                    auto_fixable=is_decorative,
                    wcag_criteria=["1.1.1"]
                ))
            else:
                # Check alt text quality
                self._check_alt_text_quality(alt_text, src, file_path)
                self.image_alt_texts.add(alt_text)

    def _is_decorative_image(self, img_element) -> bool:
        """Determine if an image is likely decorative."""
        # Check for common decorative image indicators
        src = img_element.get('src', '').lower()
        decorative_patterns = [
            'decoration', 'ornament', 'divider', 'spacer',
            'bullet', 'arrow', 'icon', 'border'
        ]

        return any(pattern in src for pattern in decorative_patterns)

    def _check_alt_text_quality(self, alt_text: str, src: str, file_path: str) -> None:
        """Check quality of alt text."""
        # Check for common alt text issues
        issues = []

        if len(alt_text) > 125:
            issues.append("Alt text too long (>125 characters)")

        if alt_text.lower().startswith(('image of', 'picture of', 'photo of')):
            issues.append("Redundant alt text prefix")

        if alt_text.lower() in ['image', 'picture', 'photo', 'graphic']:
            issues.append("Generic alt text")

        if src.lower().replace('-', ' ').replace('_', ' ') in alt_text.lower():
            issues.append("Alt text appears to be filename")

        for issue in issues:
            self.issues.append(A11yIssue(
                id=f"alt_quality_{len(self.issues)}",
                issue_type=IssueType.MISSING_ALT_TEXT,
                severity=IssueSeverity.MINOR,
                wcag_level=A11yLevel.A,
                title="Alt Text Quality Issue",
                description=f"{issue}: '{alt_text}'",
                location=file_path,
                recommendation="Improve alt text to be concise and descriptive",
                wcag_criteria=["1.1.1"]
            ))

    def _check_heading_structure_file(self, soup, file_path: str) -> None:
        """Check heading structure in a single file."""
        if not self.config.check_heading_structure:
            return

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text().strip()

            # Store for global structure check
            self.heading_structure.append((level, text))

            # Check for skipped heading levels
            if level > prev_level + 1:
                self.issues.append(A11yIssue(
                    id=f"heading_skip_{len(self.issues)}",
                    issue_type=IssueType.HEADING_STRUCTURE,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.A,
                    title="Skipped Heading Level",
                    description=f"Heading jumps from h{prev_level} to h{level}",
                    location=file_path,
                    element=str(heading)[:100],
                    recommendation="Use sequential heading levels (h1, h2, h3, etc.)",
                    wcag_criteria=["1.3.1", "2.4.6"]
                ))

            # Check for empty headings
            if not text:
                self.issues.append(A11yIssue(
                    id=f"empty_heading_{len(self.issues)}",
                    issue_type=IssueType.HEADING_STRUCTURE,
                    severity=IssueSeverity.CRITICAL,
                    wcag_level=A11yLevel.A,
                    title="Empty Heading",
                    description=f"Heading {heading.name} has no text content",
                    location=file_path,
                    element=str(heading),
                    recommendation="Add descriptive text to all headings",
                    wcag_criteria=["1.3.1", "2.4.6"]
                ))

            prev_level = level

    def _audit_heading_structure(self) -> None:
        """Audit global heading structure across all files."""
        if not self.heading_structure:
            return

        # Check for missing h1
        has_h1 = any(level == 1 for level, _ in self.heading_structure)
        if not has_h1:
            self.issues.append(A11yIssue(
                id="missing_h1",
                issue_type=IssueType.HEADING_STRUCTURE,
                severity=IssueSeverity.CRITICAL,
                wcag_level=A11yLevel.A,
                title="Missing H1",
                description="Document structure missing main heading (h1)",
                recommendation="Add h1 element as main document title",
                wcag_criteria=["1.3.1", "2.4.6"]
            ))

        # Check for multiple h1s (may be valid in EPUB but worth noting)
        h1_count = sum(1 for level, _ in self.heading_structure if level == 1)
        if h1_count > 1:
            self.issues.append(A11yIssue(
                id="multiple_h1",
                issue_type=IssueType.HEADING_STRUCTURE,
                severity=IssueSeverity.MINOR,
                wcag_level=A11yLevel.AA,
                title="Multiple H1 Elements",
                description=f"Found {h1_count} h1 elements across documents",
                recommendation="Consider using one h1 per chapter/section",
                wcag_criteria=["2.4.6"]
            ))

    def _check_semantic_markup(self, soup, file_path: str) -> None:
        """Check for proper semantic markup usage."""
        if not self.config.check_semantic_markup:
            return

        # Check for semantic HTML5 elements
        semantic_elements = ['article', 'section', 'nav', 'aside', 'header', 'footer', 'main']
        has_semantic = any(soup.find(elem) for elem in semantic_elements)

        if not has_semantic:
            self.issues.append(A11yIssue(
                id=f"no_semantic_{len(self.issues)}",
                issue_type=IssueType.SEMANTIC_MARKUP,
                severity=IssueSeverity.MINOR,
                wcag_level=A11yLevel.AA,
                title="Limited Semantic Markup",
                description="Document lacks semantic HTML5 elements",
                location=file_path,
                recommendation="Use semantic elements like <article>, <section>, <nav>",
                wcag_criteria=["1.3.1"]
            ))

        # Check for proper list markup
        self._check_list_markup(soup, file_path)

        # Check for ARIA usage
        self._check_aria_usage(soup, file_path)

    def _check_list_markup(self, soup, file_path: str) -> None:
        """Check for proper list markup."""
        # Find potential lists marked up incorrectly
        paragraphs = soup.find_all('p')

        for p in paragraphs:
            text = p.get_text().strip()
            # Check for bullet-like characters that should be lists
            if re.match(r'^[•·▪▫‣⁃*-]\s+', text):
                self.issues.append(A11yIssue(
                    id=f"fake_list_{len(self.issues)}",
                    issue_type=IssueType.SEMANTIC_MARKUP,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.A,
                    title="Improper List Markup",
                    description="List items marked as paragraphs instead of <ul>/<li>",
                    location=file_path,
                    element=str(p)[:100],
                    recommendation="Use proper <ul>/<ol> and <li> elements for lists",
                    auto_fixable=True,
                    wcag_criteria=["1.3.1"]
                ))

    def _check_aria_usage(self, soup, file_path: str) -> None:
        """Check for ARIA attribute usage and validity."""
        aria_elements = soup.find_all(attrs=lambda x: x and any(k.startswith('aria-') for k in x.keys()))

        for element in aria_elements:
            aria_attrs = {k: v for k, v in element.attrs.items() if k.startswith('aria-')}

            # Check for redundant ARIA
            if 'aria-label' in aria_attrs and element.get_text().strip():
                self.issues.append(A11yIssue(
                    id=f"redundant_aria_{len(self.issues)}",
                    issue_type=IssueType.SEMANTIC_MARKUP,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.A,
                    title="Redundant ARIA Label",
                    description="Element has both aria-label and visible text",
                    location=file_path,
                    element=str(element)[:100],
                    recommendation="Remove aria-label if visible text is sufficient",
                    wcag_criteria=["4.1.2"]
                ))

    def _check_language_attributes(self, soup, file_path: str) -> None:
        """Check for proper language attributes."""
        if not self.config.check_language_attributes:
            return

        # Check for lang attribute on html element
        html_elem = soup.find('html')
        if html_elem and not html_elem.get('lang'):
            self.issues.append(A11yIssue(
                id=f"missing_lang_{len(self.issues)}",
                issue_type=IssueType.LANGUAGE_ATTRIBUTES,
                severity=IssueSeverity.CRITICAL,
                wcag_level=A11yLevel.A,
                title="Missing Language Declaration",
                description="HTML element missing lang attribute",
                location=file_path,
                recommendation="Add lang attribute to <html> element (e.g., lang='en')",
                auto_fixable=True,
                wcag_criteria=["3.1.1"]
            ))

    def _check_link_accessibility(self, soup, file_path: str) -> None:
        """Check link accessibility."""
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')
            text = link.get_text().strip()

            # Check for empty links
            if not text and not link.get('aria-label'):
                self.issues.append(A11yIssue(
                    id=f"empty_link_{len(self.issues)}",
                    issue_type=IssueType.LINK_ACCESSIBILITY,
                    severity=IssueSeverity.CRITICAL,
                    wcag_level=A11yLevel.A,
                    title="Empty Link",
                    description="Link has no accessible text",
                    location=file_path,
                    element=str(link)[:100],
                    recommendation="Add descriptive text or aria-label to links",
                    wcag_criteria=["2.4.4"]
                ))

            # Check for generic link text
            if text.lower() in ['click here', 'read more', 'more', 'here', 'link']:
                self.issues.append(A11yIssue(
                    id=f"generic_link_{len(self.issues)}",
                    issue_type=IssueType.LINK_ACCESSIBILITY,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.A,
                    title="Generic Link Text",
                    description=f"Link text '{text}' is not descriptive",
                    location=file_path,
                    element=str(link)[:100],
                    recommendation="Use descriptive link text that explains the destination",
                    wcag_criteria=["2.4.4"]
                ))

    def _check_table_accessibility(self, soup, file_path: str) -> None:
        """Check table accessibility."""
        tables = soup.find_all('table')

        for table in tables:
            # Check for table headers
            headers = table.find_all('th')
            if not headers:
                self.issues.append(A11yIssue(
                    id=f"table_no_headers_{len(self.issues)}",
                    issue_type=IssueType.TABLE_ACCESSIBILITY,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.A,
                    title="Table Missing Headers",
                    description="Data table without proper header cells",
                    location=file_path,
                    element=str(table)[:100],
                    recommendation="Use <th> elements for table headers",
                    wcag_criteria=["1.3.1"]
                ))

            # Check for table caption
            caption = table.find('caption')
            if not caption:
                self.issues.append(A11yIssue(
                    id=f"table_no_caption_{len(self.issues)}",
                    issue_type=IssueType.TABLE_ACCESSIBILITY,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.A,
                    title="Table Missing Caption",
                    description="Table without descriptive caption",
                    location=file_path,
                    recommendation="Add <caption> element to describe table content",
                    wcag_criteria=["1.3.1"]
                ))

    def _check_form_accessibility(self, soup, file_path: str) -> None:
        """Check form accessibility."""
        inputs = soup.find_all(['input', 'textarea', 'select'])

        for input_elem in inputs:
            input_id = input_elem.get('id')
            input_type = input_elem.get('type', 'text')

            # Check for associated labels
            label = soup.find('label', {'for': input_id}) if input_id else None
            aria_label = input_elem.get('aria-label')

            if not label and not aria_label:
                self.issues.append(A11yIssue(
                    id=f"input_no_label_{len(self.issues)}",
                    issue_type=IssueType.FORM_ACCESSIBILITY,
                    severity=IssueSeverity.CRITICAL,
                    wcag_level=A11yLevel.A,
                    title="Form Input Missing Label",
                    description=f"Input field ({input_type}) lacks accessible label",
                    location=file_path,
                    element=str(input_elem)[:100],
                    recommendation="Add <label> element or aria-label attribute",
                    wcag_criteria=["1.3.1", "3.3.2"]
                ))

    def _check_keyboard_navigation(self, soup, file_path: str) -> None:
        """Check keyboard navigation accessibility."""
        if not self.config.check_keyboard_navigation:
            return

        # Check for tabindex usage
        tabindex_elements = soup.find_all(attrs={'tabindex': True})

        for elem in tabindex_elements:
            tabindex = elem.get('tabindex')
            try:
                tabindex_val = int(tabindex)
                if tabindex_val > 0:
                    self.issues.append(A11yIssue(
                        id=f"positive_tabindex_{len(self.issues)}",
                        issue_type=IssueType.KEYBOARD_NAVIGATION,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.A,
                        title="Positive Tabindex",
                        description=f"Element uses positive tabindex ({tabindex})",
                        location=file_path,
                        element=str(elem)[:100],
                        recommendation="Avoid positive tabindex values; use 0 or -1",
                        wcag_criteria=["2.4.3"]
                    ))
            except ValueError:
                pass

    def _check_reading_order(self, soup, file_path: str) -> None:
        """Check logical reading order."""
        # Check for CSS that might affect reading order
        style_elements = soup.find_all('style')

        for style in style_elements:
            css_content = style.get_text()
            if 'position:' in css_content and ('absolute' in css_content or 'fixed' in css_content):
                self.issues.append(A11yIssue(
                    id=f"position_absolute_{len(self.issues)}",
                    issue_type=IssueType.READING_ORDER,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.A,
                    title="Absolute Positioning May Affect Reading Order",
                    description="CSS absolute/fixed positioning detected",
                    location=file_path,
                    recommendation="Ensure positioned elements don't disrupt logical reading order",
                    wcag_criteria=["1.3.2"]
                ))

    def _audit_language_consistency(self) -> None:
        """Check for consistent language usage across files."""
        # This would check for language consistency
        # Implementation depends on specific requirements
        pass

    def _generate_audit_result(self) -> A11yAuditResult:
        """Generate comprehensive audit result."""
        # Count issues by severity
        critical_count = len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL])
        major_count = len([i for i in self.issues if i.severity == IssueSeverity.MAJOR])
        minor_count = len([i for i in self.issues if i.severity == IssueSeverity.MINOR])
        info_count = len([i for i in self.issues if i.severity == IssueSeverity.INFO])

        # Count issues by type
        issues_by_type = {}
        for issue_type in IssueType:
            issues_by_type[issue_type] = len([i for i in self.issues if i.issue_type == issue_type])

        # Determine conformance level
        conformance_level = self._determine_conformance_level()

        # Calculate overall score
        overall_score = self._calculate_score(critical_count, major_count, minor_count)

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return A11yAuditResult(
            total_issues=len(self.issues),
            critical_issues=critical_count,
            major_issues=major_count,
            minor_issues=minor_count,
            info_issues=info_count,
            issues_by_type=issues_by_type,
            conformance_level=conformance_level,
            overall_score=overall_score,
            issues=self.issues,
            recommendations=recommendations
        )

    def _determine_conformance_level(self) -> Optional[A11yLevel]:
        """Determine WCAG conformance level based on issues."""
        critical_issues = [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

        if critical_issues:
            return None  # No conformance if critical issues exist

        # Check for Level A compliance
        level_a_issues = [i for i in self.issues if i.wcag_level == A11yLevel.A and i.severity in [IssueSeverity.MAJOR, IssueSeverity.CRITICAL]]
        if level_a_issues:
            return None

        # Check for Level AA compliance
        level_aa_issues = [i for i in self.issues if i.wcag_level == A11yLevel.AA and i.severity in [IssueSeverity.MAJOR, IssueSeverity.CRITICAL]]
        if level_aa_issues:
            return A11yLevel.A

        return A11yLevel.AA  # Assuming AAA is rare and not automatically determined

    def _calculate_score(self, critical: int, major: int, minor: int) -> float:
        """Calculate overall accessibility score (0-100)."""
        if critical > 0:
            return max(0, 50 - (critical * 10))

        score = 100
        score -= major * 5    # -5 points per major issue
        score -= minor * 1    # -1 point per minor issue

        return max(0, score)

    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Critical issues first
        critical_types = set(i.issue_type for i in self.issues if i.severity == IssueSeverity.CRITICAL)

        if IssueType.MISSING_ALT_TEXT in critical_types:
            recommendations.append("Add alt text to all images - this is essential for screen reader users")

        if IssueType.HEADING_STRUCTURE in critical_types:
            recommendations.append("Fix heading structure - use sequential heading levels (h1, h2, h3)")

        if IssueType.LANGUAGE_ATTRIBUTES in critical_types:
            recommendations.append("Add language attributes to HTML elements")

        # Major issues
        major_types = set(i.issue_type for i in self.issues if i.severity == IssueSeverity.MAJOR)

        if IssueType.TABLE_ACCESSIBILITY in major_types:
            recommendations.append("Improve table accessibility with proper headers and captions")

        if IssueType.SEMANTIC_MARKUP in major_types:
            recommendations.append("Use semantic HTML5 elements for better structure")

        # General recommendations
        if len(self.issues) > 10:
            recommendations.append("Consider accessibility review in development process")

        return recommendations

    def generate_html_report(self, result: A11yAuditResult, output_path: Path) -> None:
        """Generate comprehensive HTML accessibility report."""

        # Determine status and color scheme
        if result.conformance_level is None:
            status = "❌ Non-Conformant"
            status_class = "fail"
        elif result.conformance_level == A11yLevel.A:
            status = "⚠️ WCAG A Conformant"
            status_class = "warning"
        else:
            status = "✅ WCAG AA Conformant"
            status_class = "pass"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit Report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #ddd; padding-bottom: 1rem; margin-bottom: 2rem; }}
        .status {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem; }}
        .status.pass {{ color: #28a745; }}
        .status.warning {{ color: #ffc107; }}
        .status.fail {{ color: #dc3545; }}
        .score {{ font-size: 3rem; font-weight: bold; text-align: center; margin: 2rem 0; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .metric {{ background: #f8f9fa; padding: 1rem; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; }}
        .metric.critical {{ border-left: 4px solid #dc3545; }}
        .metric.major {{ border-left: 4px solid #ffc107; }}
        .metric.minor {{ border-left: 4px solid #17a2b8; }}
        .recommendations {{ background: #e8f4fd; padding: 1.5rem; border-radius: 6px; margin: 2rem 0; }}
        .issues {{ margin-top: 2rem; }}
        .issue {{ border: 1px solid #dee2e6; border-radius: 6px; margin-bottom: 1rem; }}
        .issue-header {{ padding: 0.75rem 1rem; font-weight: bold; }}
        .issue-body {{ padding: 0 1rem 1rem; }}
        .issue.critical .issue-header {{ background-color: #f8d7da; color: #721c24; }}
        .issue.major .issue-header {{ background-color: #fff3cd; color: #856404; }}
        .issue.minor .issue-header {{ background-color: #d1ecf1; color: #0c5460; }}
        .issue.info .issue-header {{ background-color: #d4edda; color: #155724; }}
        .issue-meta {{ font-size: 0.9em; color: #6c757d; margin-top: 0.5rem; }}
        .wcag-criteria {{ background: #f8f9fa; padding: 0.3rem 0.6rem; border-radius: 3px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EPUB Accessibility Audit Report</h1>
        <div class="status {status_class}">{status}</div>
        <div class="score {status_class}">{result.overall_score:.0f}/100</div>
    </div>

    <div class="summary">
        <div class="metric critical">
            <div class="metric-value">{result.critical_issues}</div>
            <div>Critical Issues</div>
        </div>
        <div class="metric major">
            <div class="metric-value">{result.major_issues}</div>
            <div>Major Issues</div>
        </div>
        <div class="metric minor">
            <div class="metric-value">{result.minor_issues}</div>
            <div>Minor Issues</div>
        </div>
        <div class="metric">
            <div class="metric-value">{result.info_issues}</div>
            <div>Info Items</div>
        </div>
    </div>
"""

        if result.recommendations:
            html_content += f"""
    <div class="recommendations">
        <h2>🎯 Priority Recommendations</h2>
        <ol>
"""
            for rec in result.recommendations:
                html_content += f"            <li>{rec}</li>\n"

            html_content += """        </ol>
    </div>
"""

        html_content += f"""
    <div class="issues">
        <h2>Issues Found ({len(result.issues)})</h2>
"""

        # Group issues by severity
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.MAJOR, IssueSeverity.MINOR, IssueSeverity.INFO]:
            severity_issues = [i for i in result.issues if i.severity == severity]

            if severity_issues:
                html_content += f"""
        <h3>{severity.value.title()} Issues ({len(severity_issues)})</h3>
"""

                for issue in severity_issues:
                    wcag_badges = " ".join([f'<span class="wcag-criteria">WCAG {criteria}</span>' for criteria in issue.wcag_criteria])

                    html_content += f"""
        <div class="issue {issue.severity.value}">
            <div class="issue-header">
                {issue.title}
            </div>
            <div class="issue-body">
                <div>{issue.description}</div>
                {f'<div><strong>Location:</strong> {issue.location}</div>' if issue.location else ''}
                {f'<div><strong>Element:</strong> <code>{issue.element}</code></div>' if issue.element else ''}
                <div><strong>Recommendation:</strong> {issue.recommendation}</div>
                <div class="issue-meta">
                    {wcag_badges}
                    {' • <strong>Auto-fixable</strong>' if issue.auto_fixable else ''}
                </div>
            </div>
        </div>
"""

        html_content += """
    </div>
</body>
</html>"""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')

        logger.info(f"Accessibility report generated: {output_path}")


def audit_epub_accessibility(
    epub_path: Path,
    config: Optional[A11yConfig] = None
) -> A11yAuditResult:
    """
    Perform comprehensive accessibility audit on EPUB file.

    Args:
        epub_path: Path to EPUB file
        config: Audit configuration

    Returns:
        A11yAuditResult with detailed findings
    """
    auditor = AccessibilityAuditor(config)
    return auditor.audit_epub(epub_path)