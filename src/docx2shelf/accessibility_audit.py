"""
Accessibility audit system for EPUB content.

Performs comprehensive accessibility checks and generates detailed reports
with actionable recommendations for improving EPUB accessibility compliance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class A11yLevel(Enum):
    """Accessibility conformance levels."""

    A = "A"  # WCAG Level A
    AA = "AA"  # WCAG Level AA
    AAA = "AAA"  # WCAG Level AAA


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
    MAJOR = "major"  # Significant barrier
    MINOR = "minor"  # Minor improvement
    INFO = "info"  # Best practice recommendation


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
        self.wcag_criteria = self._load_wcag_criteria()

    def audit_epub(self, epub_path: Path) -> A11yAuditResult:
        """Perform comprehensive accessibility audit on EPUB."""
        logger.info(f"Starting accessibility audit of {epub_path}")

        issues = []

        try:
            from zipfile import ZipFile

            with ZipFile(epub_path, "r") as epub_zip:
                # Get all content files
                content_files = [f for f in epub_zip.namelist() if f.endswith(".xhtml")]

                for file_path in content_files:
                    content = epub_zip.read(file_path).decode("utf-8")
                    file_issues = self._audit_content_file(content, file_path)
                    issues.extend(file_issues)

                # Check EPUB-specific accessibility features
                epub_issues = self._audit_epub_structure(epub_zip)
                issues.extend(epub_issues)

        except Exception as e:
            logger.error(f"Accessibility audit failed: {e}")
            issues.append(
                A11yIssue(
                    id="audit_error",
                    issue_type=IssueType.SEMANTIC_MARKUP,
                    severity=IssueSeverity.CRITICAL,
                    wcag_level=A11yLevel.A,
                    title="Audit Error",
                    description=f"Failed to perform accessibility audit: {str(e)}",
                    recommendation="Fix file structure and try again",
                )
            )

        return self._compile_audit_result(issues)

    def _audit_content_file(self, content: str, file_path: str) -> List[A11yIssue]:
        """Audit individual content file for accessibility issues."""
        issues = []

        # Parse HTML content
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            # Try to parse as HTML fragment
            content_wrapped = f"<div>{content}</div>"
            try:
                root = ET.fromstring(content_wrapped)
            except ET.ParseError:
                issues.append(
                    A11yIssue(
                        id="invalid_html",
                        issue_type=IssueType.SEMANTIC_MARKUP,
                        severity=IssueSeverity.CRITICAL,
                        wcag_level=A11yLevel.A,
                        title="Invalid HTML Structure",
                        description="Content file contains invalid HTML/XHTML",
                        location=file_path,
                        recommendation="Fix HTML syntax errors",
                        wcag_criteria=["4.1.1"],
                    )
                )
                return issues

        # Run specific checks
        if self.config.check_alt_text:
            issues.extend(self._check_alt_text(root, file_path))

        if self.config.check_heading_structure:
            issues.extend(self._check_heading_structure(root, file_path))

        if self.config.check_semantic_markup:
            issues.extend(self._check_semantic_markup(root, file_path))

        if self.config.check_language_attributes:
            issues.extend(self._check_language_attributes(root, file_path))

        if self.config.check_keyboard_navigation:
            issues.extend(self._check_keyboard_navigation(root, file_path))

        issues.extend(self._check_links(root, file_path))
        issues.extend(self._check_tables(root, file_path))
        issues.extend(self._check_forms(root, file_path))
        issues.extend(self._check_media(root, file_path))
        issues.extend(self._check_reading_order(root, file_path))

        return issues

    def _check_alt_text(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check for missing or inadequate alt text on images."""
        issues = []

        # Find all image elements
        images = root.findall(".//img") + root.findall(".//{http://www.w3.org/1999/xhtml}img")

        for img in images:
            alt_text = img.get("alt", "")
            src = img.get("src", "")

            if alt_text is None:
                issues.append(
                    A11yIssue(
                        id=f"missing_alt_{hash(src)}",
                        issue_type=IssueType.MISSING_ALT_TEXT,
                        severity=IssueSeverity.CRITICAL,
                        wcag_level=A11yLevel.A,
                        title="Missing Alt Text",
                        description=f"Image '{src}' missing alt attribute",
                        location=file_path,
                        element=ET.tostring(img, encoding="unicode"),
                        recommendation="Add descriptive alt text for all images",
                        auto_fixable=False,
                        wcag_criteria=["1.1.1"],
                    )
                )
            elif alt_text.strip() == "":
                # Empty alt text is acceptable for decorative images
                # Check if this might be meaningful content
                if any(
                    keyword in src.lower() for keyword in ["chart", "graph", "diagram", "figure"]
                ):
                    issues.append(
                        A11yIssue(
                            id=f"empty_alt_{hash(src)}",
                            issue_type=IssueType.MISSING_ALT_TEXT,
                            severity=IssueSeverity.MAJOR,
                            wcag_level=A11yLevel.A,
                            title="Empty Alt Text on Informative Image",
                            description=f"Image '{src}' appears informative but has empty alt text",
                            location=file_path,
                            element=ET.tostring(img, encoding="unicode"),
                            recommendation="Add descriptive alt text or confirm image is decorative",
                            wcag_criteria=["1.1.1"],
                        )
                    )
            elif len(alt_text) < 5:
                issues.append(
                    A11yIssue(
                        id=f"short_alt_{hash(src)}",
                        issue_type=IssueType.MISSING_ALT_TEXT,
                        severity=IssueSeverity.MINOR,
                        wcag_level=A11yLevel.A,
                        title="Very Short Alt Text",
                        description=f"Alt text '{alt_text}' may be too brief",
                        location=file_path,
                        element=ET.tostring(img, encoding="unicode"),
                        recommendation="Consider more descriptive alt text",
                        wcag_criteria=["1.1.1"],
                    )
                )

        return issues

    def _check_heading_structure(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check heading structure and hierarchy."""
        issues = []

        # Find all heading elements in document order
        headings = []
        # Find all elements and filter for headings to preserve document order
        for elem in root.iter():
            tag = elem.tag.lower()
            if tag.startswith("h") and len(tag) == 2 and tag[1:].isdigit():
                headings.append(elem)
            elif (
                tag.endswith("}h1")
                or tag.endswith("}h2")
                or tag.endswith("}h3")
                or tag.endswith("}h4")
                or tag.endswith("}h5")
                or tag.endswith("}h6")
            ):
                headings.append(elem)

        if not headings:
            issues.append(
                A11yIssue(
                    id="no_headings",
                    issue_type=IssueType.HEADING_STRUCTURE,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.AA,
                    title="No Headings Found",
                    description="Document lacks heading structure",
                    location=file_path,
                    recommendation="Add headings to create logical document structure",
                    wcag_criteria=["2.4.6", "1.3.1"],
                )
            )
            return issues

        # Extract heading levels
        heading_levels = []
        for heading in headings:
            tag = heading.tag.lower()
            if tag.startswith("h") and tag[1:].isdigit():
                level = int(tag[1:])
            elif "}h" in tag:
                level = int(tag.split("}h")[1])
            else:
                continue
            heading_levels.append((level, heading))

        # Check for proper hierarchy
        prev_level = 0
        for level, heading in heading_levels:
            if level - prev_level > 1:
                issues.append(
                    A11yIssue(
                        id=f"skipped_heading_{hash(ET.tostring(heading))}",
                        issue_type=IssueType.HEADING_STRUCTURE,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.AA,
                        title="Skipped Heading Level",
                        description=f"Heading jumps from h{prev_level} to h{level}",
                        location=file_path,
                        element=ET.tostring(heading, encoding="unicode"),
                        recommendation="Use sequential heading levels",
                        wcag_criteria=["1.3.1", "2.4.6"],
                    )
                )

            # Check for empty headings
            text_content = heading.text or ""
            if len(text_content.strip()) == 0:
                issues.append(
                    A11yIssue(
                        id=f"empty_heading_{hash(ET.tostring(heading))}",
                        issue_type=IssueType.HEADING_STRUCTURE,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.A,
                        title="Empty Heading",
                        description=f"Heading h{level} is empty",
                        location=file_path,
                        element=ET.tostring(heading, encoding="unicode"),
                        recommendation="Add descriptive text to heading or remove if unnecessary",
                        wcag_criteria=["2.4.6"],
                    )
                )

            prev_level = level

        return issues

    def _check_semantic_markup(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check for proper semantic markup usage."""
        issues = []

        # Check for proper use of semantic elements
        semantic_elements = ["main", "nav", "article", "section", "aside", "header", "footer"]
        found_semantic = False

        for element in semantic_elements:
            ns = "{http://www.w3.org/1999/xhtml}"
            if root.findall(f".//{element}") or root.findall(f".//{ns}{element}"):
                found_semantic = True
                break

        if not found_semantic:
            # Check if content is substantial enough to warrant semantic markup
            text_content = self._extract_text_content(root)
            if len(text_content.split()) > 100:  # Substantial content
                issues.append(
                    A11yIssue(
                        id="no_semantic_markup",
                        issue_type=IssueType.SEMANTIC_MARKUP,
                        severity=IssueSeverity.MINOR,
                        wcag_level=A11yLevel.AA,
                        title="No Semantic Markup",
                        description="Document lacks semantic HTML5 elements",
                        location=file_path,
                        recommendation="Use semantic elements like <main>, <nav>, <article> for better structure",
                        wcag_criteria=["1.3.1"],
                    )
                )

        # Check for improper use of formatting tags for semantic meaning
        bold_tags = root.findall(".//b") + root.findall(".//{http://www.w3.org/1999/xhtml}b")
        italic_tags = root.findall(".//i") + root.findall(".//{http://www.w3.org/1999/xhtml}i")

        for tag in bold_tags + italic_tags:
            text = tag.text or ""
            if len(text.split()) > 5:  # Likely semantic, not just formatting
                tag_name = tag.tag.split("}")[-1] if "}" in tag.tag else tag.tag
                issues.append(
                    A11yIssue(
                        id=f"semantic_formatting_{hash(ET.tostring(tag))}",
                        issue_type=IssueType.SEMANTIC_MARKUP,
                        severity=IssueSeverity.MINOR,
                        wcag_level=A11yLevel.AA,
                        title="Formatting Tag Used for Semantic Meaning",
                        description=f"<{tag_name}> tag used for what appears to be semantic emphasis",
                        location=file_path,
                        element=ET.tostring(tag, encoding="unicode"),
                        recommendation=f"Consider using <strong> or <em> instead of <{tag_name}> for semantic emphasis",
                        wcag_criteria=["1.3.1"],
                    )
                )

        return issues

    def _check_language_attributes(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check for proper language attributes."""
        issues = []

        # Check for lang attribute on root element
        lang_attr = root.get("lang") or root.get("{http://www.w3.org/XML/1998/namespace}lang")

        if not lang_attr:
            issues.append(
                A11yIssue(
                    id="missing_lang",
                    issue_type=IssueType.LANGUAGE_ATTRIBUTES,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.A,
                    title="Missing Language Attribute",
                    description="Document lacks lang attribute",
                    location=file_path,
                    recommendation="Add lang attribute to identify document language",
                    auto_fixable=True,
                    wcag_criteria=["3.1.1"],
                )
            )
        elif len(lang_attr) < 2:
            issues.append(
                A11yIssue(
                    id="invalid_lang",
                    issue_type=IssueType.LANGUAGE_ATTRIBUTES,
                    severity=IssueSeverity.MAJOR,
                    wcag_level=A11yLevel.A,
                    title="Invalid Language Code",
                    description=f"Language attribute '{lang_attr}' is invalid",
                    location=file_path,
                    recommendation="Use valid ISO 639-1 language code",
                    wcag_criteria=["3.1.1"],
                )
            )

        return issues

    def _check_keyboard_navigation(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check for keyboard navigation accessibility."""
        issues = []

        # Check for interactive elements with tabindex
        interactive_elements = (
            root.findall(".//a")
            + root.findall(".//button")
            + root.findall(".//input")
            + root.findall(".//select")
            + root.findall(".//{http://www.w3.org/1999/xhtml}a")
            + root.findall(".//{http://www.w3.org/1999/xhtml}button")
        )

        for element in interactive_elements:
            tabindex = element.get("tabindex")
            if tabindex and int(tabindex) > 0:
                issues.append(
                    A11yIssue(
                        id=f"positive_tabindex_{hash(ET.tostring(element))}",
                        issue_type=IssueType.KEYBOARD_NAVIGATION,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.A,
                        title="Positive Tabindex",
                        description=f"Element has positive tabindex ({tabindex})",
                        location=file_path,
                        element=ET.tostring(element, encoding="unicode"),
                        recommendation="Avoid positive tabindex values; use 0 or -1",
                        wcag_criteria=["2.4.3"],
                    )
                )

        return issues

    def _check_links(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check link accessibility."""
        issues = []

        links = root.findall(".//a") + root.findall(".//{http://www.w3.org/1999/xhtml}a")

        for link in links:
            href = link.get("href", "")
            text_content = self._extract_text_content(link).strip()

            if not text_content:
                issues.append(
                    A11yIssue(
                        id=f"empty_link_{hash(ET.tostring(link))}",
                        issue_type=IssueType.LINK_ACCESSIBILITY,
                        severity=IssueSeverity.CRITICAL,
                        wcag_level=A11yLevel.A,
                        title="Empty Link",
                        description="Link has no accessible text",
                        location=file_path,
                        element=ET.tostring(link, encoding="unicode"),
                        recommendation="Add descriptive link text or aria-label",
                        wcag_criteria=["2.4.4", "4.1.2"],
                    )
                )
            elif len(text_content) < 3:
                issues.append(
                    A11yIssue(
                        id=f"short_link_{hash(ET.tostring(link))}",
                        issue_type=IssueType.LINK_ACCESSIBILITY,
                        severity=IssueSeverity.MINOR,
                        wcag_level=A11yLevel.AA,
                        title="Very Short Link Text",
                        description=f"Link text '{text_content}' may be too brief",
                        location=file_path,
                        element=ET.tostring(link, encoding="unicode"),
                        recommendation="Use more descriptive link text",
                        wcag_criteria=["2.4.4"],
                    )
                )
            elif text_content.lower() in ["click here", "read more", "more", "here", "link"]:
                issues.append(
                    A11yIssue(
                        id=f"generic_link_{hash(ET.tostring(link))}",
                        issue_type=IssueType.LINK_ACCESSIBILITY,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.AA,
                        title="Generic Link Text",
                        description=f"Link text '{text_content}' is not descriptive",
                        location=file_path,
                        element=ET.tostring(link, encoding="unicode"),
                        recommendation="Use descriptive link text that explains the destination",
                        wcag_criteria=["2.4.4"],
                    )
                )

        return issues

    def _check_tables(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check table accessibility."""
        issues = []

        tables = root.findall(".//table") + root.findall(".//{http://www.w3.org/1999/xhtml}table")

        for table in tables:
            # Check for table headers
            headers = table.findall(".//th") + table.findall(".//{http://www.w3.org/1999/xhtml}th")
            if not headers:
                issues.append(
                    A11yIssue(
                        id=f"table_no_headers_{hash(ET.tostring(table))}",
                        issue_type=IssueType.TABLE_ACCESSIBILITY,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.A,
                        title="Table Missing Headers",
                        description="Data table lacks header cells",
                        location=file_path,
                        element=ET.tostring(table, encoding="unicode")[:200],
                        recommendation="Add <th> elements for table headers",
                        wcag_criteria=["1.3.1"],
                    )
                )

            # Check for table caption
            caption = table.find(".//caption") or table.find(
                ".//{http://www.w3.org/1999/xhtml}caption"
            )
            if not caption:
                # Check if table is complex (more than simple 2x2)
                rows = table.findall(".//tr") + table.findall(".//{http://www.w3.org/1999/xhtml}tr")
                if len(rows) > 2:
                    issues.append(
                        A11yIssue(
                            id=f"table_no_caption_{hash(ET.tostring(table))}",
                            issue_type=IssueType.TABLE_ACCESSIBILITY,
                            severity=IssueSeverity.MINOR,
                            wcag_level=A11yLevel.AA,
                            title="Table Missing Caption",
                            description="Complex table lacks descriptive caption",
                            location=file_path,
                            element=ET.tostring(table, encoding="unicode")[:200],
                            recommendation="Add <caption> to describe table purpose",
                            wcag_criteria=["1.3.1"],
                        )
                    )

        return issues

    def _check_forms(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check form accessibility."""
        issues = []

        # Find form inputs
        inputs = (
            root.findall(".//input")
            + root.findall(".//select")
            + root.findall(".//textarea")
            + root.findall(".//{http://www.w3.org/1999/xhtml}input")
            + root.findall(".//{http://www.w3.org/1999/xhtml}select")
            + root.findall(".//{http://www.w3.org/1999/xhtml}textarea")
        )

        for input_elem in inputs:
            input_id = input_elem.get("id", "")
            input_type = input_elem.get("type", "text")

            # Skip submit buttons and hidden inputs
            if input_type in ["submit", "button", "hidden"]:
                continue

            # Check for associated label
            has_label = False

            # Look for label by for attribute
            if input_id:
                ns = "{http://www.w3.org/1999/xhtml}"
                labels = root.findall(f'.//label[@for="{input_id}"]') + root.findall(
                    f'.//{ns}label[@for="{input_id}"]'
                )
                if labels:
                    has_label = True

            # Check for aria-label or aria-labelledby
            if not has_label:
                if input_elem.get("aria-label") or input_elem.get("aria-labelledby"):
                    has_label = True

            if not has_label:
                issues.append(
                    A11yIssue(
                        id=f"input_no_label_{hash(ET.tostring(input_elem))}",
                        issue_type=IssueType.FORM_ACCESSIBILITY,
                        severity=IssueSeverity.CRITICAL,
                        wcag_level=A11yLevel.A,
                        title="Form Input Missing Label",
                        description=f"Input of type '{input_type}' lacks accessible label",
                        location=file_path,
                        element=ET.tostring(input_elem, encoding="unicode"),
                        recommendation="Add <label>, aria-label, or aria-labelledby",
                        wcag_criteria=["1.3.1", "4.1.2"],
                    )
                )

        return issues

    def _check_media(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check multimedia accessibility."""
        issues = []

        # Check for audio/video elements
        media_elements = (
            root.findall(".//audio")
            + root.findall(".//video")
            + root.findall(".//{http://www.w3.org/1999/xhtml}audio")
            + root.findall(".//{http://www.w3.org/1999/xhtml}video")
        )

        for media in media_elements:
            media_type = media.tag.split("}")[-1] if "}" in media.tag else media.tag

            # Check for controls
            if not media.get("controls"):
                issues.append(
                    A11yIssue(
                        id=f"media_no_controls_{hash(ET.tostring(media))}",
                        issue_type=IssueType.MEDIA_ACCESSIBILITY,
                        severity=IssueSeverity.MAJOR,
                        wcag_level=A11yLevel.A,
                        title="Media Missing Controls",
                        description=f"{media_type} element lacks user controls",
                        location=file_path,
                        element=ET.tostring(media, encoding="unicode"),
                        recommendation="Add controls attribute to media elements",
                        wcag_criteria=["2.1.1"],
                    )
                )

            # Check for captions/transcripts (video)
            if media_type == "video":
                tracks = media.findall(".//track") + media.findall(
                    ".//{http://www.w3.org/1999/xhtml}track"
                )
                has_captions = any(track.get("kind") == "captions" for track in tracks)

                if not has_captions:
                    issues.append(
                        A11yIssue(
                            id=f"video_no_captions_{hash(ET.tostring(media))}",
                            issue_type=IssueType.MEDIA_ACCESSIBILITY,
                            severity=IssueSeverity.CRITICAL,
                            wcag_level=A11yLevel.A,
                            title="Video Missing Captions",
                            description="Video content lacks captions",
                            location=file_path,
                            element=ET.tostring(media, encoding="unicode"),
                            recommendation="Add caption track or provide transcript",
                            wcag_criteria=["1.2.2"],
                        )
                    )

        return issues

    def _check_reading_order(self, root: ET.Element, file_path: str) -> List[A11yIssue]:
        """Check logical reading order."""
        issues = []

        # Check for CSS that might affect reading order
        # This is a simplified check - full CSS analysis would require parsing CSS files
        elements_with_float = []
        elements_with_position = []

        for elem in root.iter():
            style = elem.get("style", "")
            if "float:" in style or "position:" in style:
                if "float:" in style:
                    elements_with_float.append(elem)
                if "position:" in style:
                    elements_with_position.append(elem)

        if elements_with_float:
            issues.append(
                A11yIssue(
                    id="float_elements",
                    issue_type=IssueType.READING_ORDER,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.AA,
                    title="Floated Elements May Affect Reading Order",
                    description=f"Found {len(elements_with_float)} elements with float positioning",
                    location=file_path,
                    recommendation="Ensure floated elements don't disrupt logical reading order",
                    wcag_criteria=["1.3.2"],
                )
            )

        if elements_with_position:
            issues.append(
                A11yIssue(
                    id="positioned_elements",
                    issue_type=IssueType.READING_ORDER,
                    severity=IssueSeverity.MINOR,
                    wcag_level=A11yLevel.AA,
                    title="Positioned Elements May Affect Reading Order",
                    description=f"Found {len(elements_with_position)} elements with absolute/relative positioning",
                    location=file_path,
                    recommendation="Ensure positioned elements maintain logical reading order",
                    wcag_criteria=["1.3.2"],
                )
            )

        return issues

    def _audit_epub_structure(self, epub_zip) -> List[A11yIssue]:
        """Audit EPUB-specific accessibility features."""
        issues = []

        # Check for accessibility metadata in OPF
        opf_files = [f for f in epub_zip.namelist() if f.endswith(".opf")]
        if opf_files:
            try:
                opf_content = epub_zip.read(opf_files[0]).decode("utf-8")
                root = ET.fromstring(opf_content)

                # Check for accessibility metadata
                metadata = root.find(".//{http://www.idpf.org/2007/opf}metadata")
                if metadata is not None:
                    # Look for a11y metadata
                    a11y_meta = metadata.findall(
                        './/{http://www.idpf.org/2007/opf}meta[@property="schema:accessibilityFeature"]'
                    )
                    if not a11y_meta:
                        issues.append(
                            A11yIssue(
                                id="missing_a11y_metadata",
                                issue_type=IssueType.SEMANTIC_MARKUP,
                                severity=IssueSeverity.MINOR,
                                wcag_level=A11yLevel.AA,
                                title="Missing Accessibility Metadata",
                                description="EPUB lacks accessibility metadata",
                                location=opf_files[0],
                                recommendation="Add accessibility metadata to OPF file",
                                wcag_criteria=["4.1.2"],
                            )
                        )
            except Exception:
                pass

        return issues

    def _extract_text_content(self, element: ET.Element) -> str:
        """Extract text content from XML element."""
        text = element.text or ""
        for child in element:
            text += self._extract_text_content(child)
            if child.tail:
                text += child.tail
        return text

    def _compile_audit_result(self, issues: List[A11yIssue]) -> A11yAuditResult:
        """Compile audit results into final report."""
        # Count issues by severity
        critical_count = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        major_count = len([i for i in issues if i.severity == IssueSeverity.MAJOR])
        minor_count = len([i for i in issues if i.severity == IssueSeverity.MINOR])
        info_count = len([i for i in issues if i.severity == IssueSeverity.INFO])

        # Count issues by type
        issues_by_type = {}
        for issue_type in IssueType:
            issues_by_type[issue_type] = len([i for i in issues if i.issue_type == issue_type])

        # Determine conformance level
        conformance_level = None
        if critical_count == 0:
            if major_count == 0:
                if minor_count == 0:
                    conformance_level = A11yLevel.AAA
                else:
                    conformance_level = A11yLevel.AA
            else:
                # Check if major issues are AA level
                aa_major_issues = [
                    i
                    for i in issues
                    if i.severity == IssueSeverity.MAJOR and i.wcag_level == A11yLevel.AA
                ]
                if len(aa_major_issues) == 0:
                    conformance_level = A11yLevel.A

        # Calculate overall score (0-100)
        total_issues = len(issues)
        if total_issues == 0:
            overall_score = 100.0
        else:
            # Weight by severity: Critical=20, Major=10, Minor=5, Info=1
            weighted_score = (
                (critical_count * 20) + (major_count * 10) + (minor_count * 5) + (info_count * 1)
            )
            max_possible_score = total_issues * 20  # If all were critical
            overall_score = max(0, 100 - (weighted_score / max_possible_score * 100))

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, conformance_level)

        return A11yAuditResult(
            total_issues=total_issues,
            critical_issues=critical_count,
            major_issues=major_count,
            minor_issues=minor_count,
            info_issues=info_count,
            issues_by_type=issues_by_type,
            conformance_level=conformance_level,
            overall_score=overall_score,
            issues=issues,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, issues: List[A11yIssue], conformance_level: Optional[A11yLevel]
    ) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        if conformance_level is None:
            recommendations.append(
                "🚨 Critical accessibility issues found. Address immediately for basic compliance."
            )
        elif conformance_level == A11yLevel.A:
            recommendations.append("✅ Meets WCAG Level A. Work on major issues for AA compliance.")
        elif conformance_level == A11yLevel.AA:
            recommendations.append(
                "✅ Meets WCAG Level AA. Consider minor improvements for excellence."
            )
        elif conformance_level == A11yLevel.AAA:
            recommendations.append("🌟 Excellent accessibility! Meets WCAG Level AAA.")

        # Issue-specific recommendations
        issue_types = set(issue.issue_type for issue in issues)

        if IssueType.MISSING_ALT_TEXT in issue_types:
            recommendations.append("🖼️ Add descriptive alt text to all images")

        if IssueType.HEADING_STRUCTURE in issue_types:
            recommendations.append("📝 Fix heading hierarchy and structure")

        if IssueType.LINK_ACCESSIBILITY in issue_types:
            recommendations.append("🔗 Improve link accessibility with descriptive text")

        if IssueType.TABLE_ACCESSIBILITY in issue_types:
            recommendations.append("📊 Add proper headers and captions to tables")

        auto_fixable = len([i for i in issues if i.auto_fixable])
        if auto_fixable > 0:
            recommendations.append(f"🔧 {auto_fixable} issues can be automatically fixed")

        return recommendations

    def _load_wcag_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Load WCAG 2.1 criteria definitions."""
        # This would typically load from a comprehensive WCAG database
        # For now, return a simplified mapping
        return {
            "1.1.1": {"title": "Non-text Content", "level": "A"},
            "1.3.1": {"title": "Info and Relationships", "level": "A"},
            "1.3.2": {"title": "Meaningful Sequence", "level": "A"},
            "2.1.1": {"title": "Keyboard", "level": "A"},
            "2.4.3": {"title": "Focus Order", "level": "A"},
            "2.4.4": {"title": "Link Purpose (In Context)", "level": "A"},
            "2.4.6": {"title": "Headings and Labels", "level": "AA"},
            "3.1.1": {"title": "Language of Page", "level": "A"},
            "4.1.1": {"title": "Parsing", "level": "A"},
            "4.1.2": {"title": "Name, Role, Value", "level": "A"},
            "1.2.2": {"title": "Captions (Prerecorded)", "level": "A"},
        }


def audit_epub_accessibility(
    epub_path: Path, config: Optional[A11yConfig] = None
) -> A11yAuditResult:
    """Convenience function to audit EPUB accessibility."""
    auditor = AccessibilityAuditor(config)
    return auditor.audit_epub(epub_path)
