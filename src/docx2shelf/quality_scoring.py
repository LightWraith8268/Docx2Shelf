"""
EPUB Quality Scoring System for Docx2Shelf.

Provides comprehensive quality analysis with detailed scoring and actionable
improvement recommendations for EPUB files.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET
from zipfile import ZipFile

logger = logging.getLogger(__name__)


class QualityCategory(Enum):
    """Quality assessment categories."""
    STRUCTURE = "structure"           # Document structure and navigation
    CONTENT = "content"              # Text quality and formatting
    METADATA = "metadata"            # EPUB metadata completeness
    ACCESSIBILITY = "accessibility"  # A11y compliance
    TECHNICAL = "technical"          # Technical correctness
    PRESENTATION = "presentation"    # Visual design and typography


class QualityLevel(Enum):
    """Overall quality levels."""
    EXCELLENT = "excellent"    # 90-100 points
    GOOD = "good"             # 75-89 points
    FAIR = "fair"             # 60-74 points
    POOR = "poor"             # 40-59 points
    CRITICAL = "critical"     # 0-39 points


@dataclass
class QualityIssue:
    """Individual quality issue."""
    category: QualityCategory
    severity: str  # "critical", "major", "minor", "info"
    title: str
    description: str
    recommendation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    points_deducted: int = 0
    auto_fixable: bool = False


@dataclass
class CategoryScore:
    """Score for a quality category."""
    category: QualityCategory
    score: float  # 0-100
    max_score: float
    issues: List[QualityIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete quality assessment report."""
    overall_score: float  # 0-100
    quality_level: QualityLevel
    category_scores: Dict[QualityCategory, CategoryScore] = field(default_factory=dict)
    total_issues: int = 0
    critical_issues: int = 0
    auto_fixable_issues: int = 0
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = ""


class EPUBQualityAnalyzer:
    """Comprehensive EPUB quality analyzer."""

    def __init__(self):
        self.scoring_weights = {
            QualityCategory.STRUCTURE: 25,      # Navigation, chapters, ToC
            QualityCategory.CONTENT: 20,        # Text quality, formatting
            QualityCategory.METADATA: 15,       # Title, author, description
            QualityCategory.ACCESSIBILITY: 20,  # A11y compliance
            QualityCategory.TECHNICAL: 15,      # Validation, standards
            QualityCategory.PRESENTATION: 5     # Typography, design
        }

    def analyze_epub(self, epub_path: Path) -> QualityReport:
        """Perform comprehensive quality analysis of EPUB file."""
        logger.info(f"Starting quality analysis of {epub_path}")

        # Initialize with placeholder values - will be calculated later
        report = QualityReport(overall_score=0.0, quality_level=QualityLevel.POOR)

        try:
            with ZipFile(epub_path, 'r') as epub_zip:
                # Analyze each category
                report.category_scores[QualityCategory.STRUCTURE] = self._analyze_structure(epub_zip)
                report.category_scores[QualityCategory.CONTENT] = self._analyze_content(epub_zip)
                report.category_scores[QualityCategory.METADATA] = self._analyze_metadata(epub_zip)
                report.category_scores[QualityCategory.ACCESSIBILITY] = self._analyze_accessibility(epub_zip)
                report.category_scores[QualityCategory.TECHNICAL] = self._analyze_technical(epub_zip)
                report.category_scores[QualityCategory.PRESENTATION] = self._analyze_presentation(epub_zip)

                # Calculate overall score
                report.overall_score = self._calculate_overall_score(report.category_scores)
                report.quality_level = self._determine_quality_level(report.overall_score)

                # Aggregate statistics
                report.total_issues = sum(len(cat.issues) for cat in report.category_scores.values())
                report.critical_issues = sum(
                    len([i for i in cat.issues if i.severity == "critical"])
                    for cat in report.category_scores.values()
                )
                report.auto_fixable_issues = sum(
                    len([i for i in cat.issues if i.auto_fixable])
                    for cat in report.category_scores.values()
                )

                # Generate overall recommendations
                report.recommendations = self._generate_overall_recommendations(report)

        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            report = self._create_error_report(str(e))

        return report

    def _analyze_structure(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze document structure and navigation."""
        score = CategoryScore(QualityCategory.STRUCTURE, 100, 100)

        try:
            # Check for proper navigation
            nav_files = [f for f in epub_zip.namelist() if 'nav' in f.lower()]
            if not nav_files:
                score.issues.append(QualityIssue(
                    QualityCategory.STRUCTURE,
                    "major",
                    "Missing navigation file",
                    "EPUB lacks proper navigation structure",
                    "Add navigation.xhtml with proper table of contents",
                    points_deducted=15
                ))

            # Check content file structure
            content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml')]
            if len(content_files) < 2:
                score.issues.append(QualityIssue(
                    QualityCategory.STRUCTURE,
                    "minor",
                    "Limited chapter structure",
                    "Book has very few content files - consider splitting into chapters",
                    "Split content into logical chapters for better navigation",
                    points_deducted=5
                ))

            # Check for proper heading hierarchy
            for content_file in content_files[:5]:  # Sample first 5 files
                try:
                    content = epub_zip.read(content_file).decode('utf-8')
                    headings = re.findall(r'<h([1-6])', content)
                    if headings:
                        heading_levels = [int(h) for h in headings]
                        if not self._is_proper_heading_hierarchy(heading_levels):
                            score.issues.append(QualityIssue(
                                QualityCategory.STRUCTURE,
                                "minor",
                                "Improper heading hierarchy",
                                f"Heading levels skip or jump improperly in {content_file}",
                                "Use proper heading hierarchy (h1 → h2 → h3...)",
                                file_path=content_file,
                                points_deducted=3
                            ))
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Structure analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _analyze_content(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze content quality and formatting."""
        score = CategoryScore(QualityCategory.CONTENT, 100, 100)

        try:
            content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml')]
            total_word_count = 0
            formatting_issues = 0

            for content_file in content_files:
                try:
                    content = epub_zip.read(content_file).decode('utf-8')

                    # Check word count
                    text_content = re.sub(r'<[^>]+>', '', content)
                    words = len(text_content.split())
                    total_word_count += words

                    # Check for common formatting issues
                    if '  ' in text_content:  # Double spaces
                        formatting_issues += 1

                    if re.search(r'\s+[.!?]', text_content):  # Space before punctuation
                        formatting_issues += 1

                    # Check for proper paragraph structure
                    if content.count('<p>') < words / 100:  # Very long paragraphs
                        score.issues.append(QualityIssue(
                            QualityCategory.CONTENT,
                            "minor",
                            "Long paragraphs detected",
                            f"File {content_file} may have overly long paragraphs",
                            "Break up long paragraphs for better readability",
                            file_path=content_file,
                            points_deducted=2
                        ))

                except Exception:
                    continue

            # Evaluate overall content metrics
            if total_word_count < 1000:
                score.issues.append(QualityIssue(
                    QualityCategory.CONTENT,
                    "info",
                    "Short content length",
                    f"Total content is only {total_word_count} words",
                    "Consider adding more content for a complete reading experience",
                    points_deducted=5
                ))

            if formatting_issues > len(content_files) * 2:
                score.issues.append(QualityIssue(
                    QualityCategory.CONTENT,
                    "minor",
                    "Formatting inconsistencies",
                    f"Found {formatting_issues} formatting issues across content",
                    "Review and clean up text formatting",
                    points_deducted=8,
                    auto_fixable=True
                ))

        except Exception as e:
            logger.warning(f"Content analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _analyze_metadata(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze EPUB metadata completeness and quality."""
        score = CategoryScore(QualityCategory.METADATA, 100, 100)

        try:
            # Read OPF file
            opf_files = [f for f in epub_zip.namelist() if f.endswith('.opf')]
            if not opf_files:
                score.issues.append(QualityIssue(
                    QualityCategory.METADATA,
                    "critical",
                    "Missing OPF file",
                    "EPUB package document not found",
                    "Ensure proper EPUB structure with package.opf",
                    points_deducted=50
                ))
                return score

            opf_content = epub_zip.read(opf_files[0]).decode('utf-8')

            # Parse metadata
            try:
                root = ET.fromstring(opf_content)
                metadata = root.find('.//{http://www.idpf.org/2007/opf}metadata')

                if metadata is None:
                    score.issues.append(QualityIssue(
                        QualityCategory.METADATA,
                        "critical",
                        "Missing metadata section",
                        "OPF file lacks metadata section",
                        "Add proper metadata section to OPF file",
                        points_deducted=40
                    ))
                    return score

                # Check required metadata elements
                required_elements = {
                    'title': './/{http://purl.org/dc/elements/1.1/}title',
                    'creator': './/{http://purl.org/dc/elements/1.1/}creator',
                    'identifier': './/{http://purl.org/dc/elements/1.1/}identifier',
                    'language': './/{http://purl.org/dc/elements/1.1/}language'
                }

                for element_name, xpath in required_elements.items():
                    element = root.find(xpath)
                    if element is None or not element.text.strip():
                        score.issues.append(QualityIssue(
                            QualityCategory.METADATA,
                            "major" if element_name in ['title', 'creator'] else "minor",
                            f"Missing {element_name}",
                            f"Required metadata element '{element_name}' is missing or empty",
                            f"Add proper {element_name} metadata",
                            points_deducted=15 if element_name in ['title', 'creator'] else 8
                        ))

                # Check optional but recommended metadata
                optional_elements = {
                    'description': './/{http://purl.org/dc/elements/1.1/}description',
                    'publisher': './/{http://purl.org/dc/elements/1.1/}publisher',
                    'date': './/{http://purl.org/dc/elements/1.1/}date'
                }

                missing_optional = 0
                for element_name, xpath in optional_elements.items():
                    element = root.find(xpath)
                    if element is None or not element.text.strip():
                        missing_optional += 1

                if missing_optional > 1:
                    score.issues.append(QualityIssue(
                        QualityCategory.METADATA,
                        "info",
                        "Incomplete optional metadata",
                        f"Missing {missing_optional} recommended metadata elements",
                        "Add description, publisher, and publication date for better discoverability",
                        points_deducted=5
                    ))

            except ET.ParseError:
                score.issues.append(QualityIssue(
                    QualityCategory.METADATA,
                    "critical",
                    "Invalid OPF XML",
                    "OPF file contains invalid XML",
                    "Fix XML syntax errors in package.opf",
                    points_deducted=30
                ))

        except Exception as e:
            logger.warning(f"Metadata analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _analyze_accessibility(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze accessibility compliance."""
        score = CategoryScore(QualityCategory.ACCESSIBILITY, 100, 100)

        try:
            content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml')]

            for content_file in content_files[:10]:  # Sample first 10 files
                try:
                    content = epub_zip.read(content_file).decode('utf-8')

                    # Check for images without alt text
                    img_tags = re.findall(r'<img[^>]*>', content)
                    for img_tag in img_tags:
                        if 'alt=' not in img_tag:
                            score.issues.append(QualityIssue(
                                QualityCategory.ACCESSIBILITY,
                                "major",
                                "Image missing alt text",
                                f"Image in {content_file} lacks alt text",
                                "Add descriptive alt text to all images",
                                file_path=content_file,
                                points_deducted=5
                            ))

                    # Check for proper language attributes
                    if 'lang=' not in content and 'xml:lang=' not in content:
                        score.issues.append(QualityIssue(
                            QualityCategory.ACCESSIBILITY,
                            "minor",
                            "Missing language attributes",
                            f"Content file {content_file} lacks language attributes",
                            "Add lang and xml:lang attributes to content",
                            file_path=content_file,
                            points_deducted=3
                        ))

                    # Check for proper table structure
                    table_tags = re.findall(r'<table[^>]*>.*?</table>', content, re.DOTALL)
                    for table in table_tags:
                        if '<th' not in table and '<caption' not in table:
                            score.issues.append(QualityIssue(
                                QualityCategory.ACCESSIBILITY,
                                "minor",
                                "Table lacks headers or caption",
                                f"Table in {content_file} lacks proper headers or caption",
                                "Add table headers (th) and/or caption for accessibility",
                                file_path=content_file,
                                points_deducted=4
                            ))

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Accessibility analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _analyze_technical(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze technical correctness and standards compliance."""
        score = CategoryScore(QualityCategory.TECHNICAL, 100, 100)

        try:
            # Check for required EPUB files
            required_files = ['META-INF/container.xml', 'mimetype']
            for req_file in required_files:
                if req_file not in epub_zip.namelist():
                    score.issues.append(QualityIssue(
                        QualityCategory.TECHNICAL,
                        "critical",
                        f"Missing required file: {req_file}",
                        f"EPUB standard requires {req_file}",
                        f"Add missing {req_file} file",
                        points_deducted=25
                    ))

            # Check mimetype content
            if 'mimetype' in epub_zip.namelist():
                mimetype_content = epub_zip.read('mimetype').decode('utf-8').strip()
                if mimetype_content != 'application/epub+zip':
                    score.issues.append(QualityIssue(
                        QualityCategory.TECHNICAL,
                        "major",
                        "Incorrect mimetype",
                        f"Mimetype is '{mimetype_content}' instead of 'application/epub+zip'",
                        "Set mimetype to 'application/epub+zip'",
                        points_deducted=15
                    ))

            # Check for valid XHTML
            content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml')]
            invalid_xhtml_count = 0

            for content_file in content_files[:5]:  # Sample first 5 files
                try:
                    content = epub_zip.read(content_file).decode('utf-8')
                    ET.fromstring(content)  # Basic XML validation
                except ET.ParseError:
                    invalid_xhtml_count += 1

            if invalid_xhtml_count > 0:
                score.issues.append(QualityIssue(
                    QualityCategory.TECHNICAL,
                    "major",
                    "Invalid XHTML files",
                    f"{invalid_xhtml_count} content files contain invalid XHTML",
                    "Fix XML syntax errors in content files",
                    points_deducted=10 * invalid_xhtml_count
                ))

        except Exception as e:
            logger.warning(f"Technical analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _analyze_presentation(self, epub_zip: ZipFile) -> CategoryScore:
        """Analyze visual presentation and typography."""
        score = CategoryScore(QualityCategory.PRESENTATION, 100, 100)

        try:
            # Check for CSS files
            css_files = [f for f in epub_zip.namelist() if f.endswith('.css')]
            if not css_files:
                score.issues.append(QualityIssue(
                    QualityCategory.PRESENTATION,
                    "minor",
                    "No custom styling",
                    "EPUB lacks custom CSS styling",
                    "Add CSS files for improved typography and presentation",
                    points_deducted=10
                ))
            else:
                # Check CSS quality
                for css_file in css_files:
                    try:
                        css_content = epub_zip.read(css_file).decode('utf-8')

                        # Check for responsive design
                        if '@media' not in css_content:
                            score.issues.append(QualityIssue(
                                QualityCategory.PRESENTATION,
                                "info",
                                "No responsive design",
                                f"CSS file {css_file} lacks media queries",
                                "Add responsive design with media queries",
                                file_path=css_file,
                                points_deducted=3
                            ))

                        # Check for proper font stack
                        if 'font-family' in css_content:
                            if 'serif' not in css_content and 'sans-serif' not in css_content:
                                score.issues.append(QualityIssue(
                                    QualityCategory.PRESENTATION,
                                    "minor",
                                    "No fallback fonts",
                                    f"CSS file {css_file} lacks generic font fallbacks",
                                    "Add generic font families (serif, sans-serif) as fallbacks",
                                    file_path=css_file,
                                    points_deducted=2
                                ))

                    except Exception:
                        continue

            # Check for cover image
            cover_images = [f for f in epub_zip.namelist()
                          if any(keyword in f.lower() for keyword in ['cover', 'title'])]
            if not cover_images:
                score.issues.append(QualityIssue(
                    QualityCategory.PRESENTATION,
                    "minor",
                    "No cover image",
                    "EPUB lacks a cover image",
                    "Add a professional cover image",
                    points_deducted=5
                ))

        except Exception as e:
            logger.warning(f"Presentation analysis error: {e}")

        # Calculate final score
        total_deducted = sum(issue.points_deducted for issue in score.issues)
        score.score = max(0, 100 - total_deducted)

        return score

    def _calculate_overall_score(self, category_scores: Dict[QualityCategory, CategoryScore]) -> float:
        """Calculate weighted overall quality score."""
        total_weighted_score = 0
        total_weight = 0

        for category, score_data in category_scores.items():
            weight = self.scoring_weights.get(category, 0)
            weighted_score = (score_data.score / 100) * weight
            total_weighted_score += weighted_score
            total_weight += weight

        return (total_weighted_score / total_weight) * 100 if total_weight > 0 else 0

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from numeric score."""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.FAIR
        elif score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _generate_overall_recommendations(self, report: QualityReport) -> List[str]:
        """Generate overall improvement recommendations."""
        recommendations = []

        # Priority recommendations based on quality level
        if report.quality_level == QualityLevel.CRITICAL:
            recommendations.append("🚨 Critical issues detected. Address technical and metadata problems first.")

        if report.critical_issues > 0:
            recommendations.append(f"⚠️ Fix {report.critical_issues} critical issues immediately.")

        # Category-specific recommendations
        if report.category_scores:
            lowest_category = min(report.category_scores.items(), key=lambda x: x[1].score)
            if lowest_category[1].score < 70:
                recommendations.append(f"🎯 Focus on improving {lowest_category[0].value} (lowest score: {lowest_category[1].score:.1f}%).")

        if report.auto_fixable_issues > 0:
            recommendations.append(f"🔧 {report.auto_fixable_issues} issues can be automatically fixed.")

        # General recommendations
        if report.overall_score < 80:
            recommendations.append("📚 Review the Quality Cookbook for best practices.")

        if not recommendations:
            recommendations.append("✅ Excellent quality! Consider minor optimizations for perfect score.")

        return recommendations

    def _is_proper_heading_hierarchy(self, heading_levels: List[int]) -> bool:
        """Check if heading levels follow proper hierarchy."""
        if not heading_levels:
            return True

        for i in range(1, len(heading_levels)):
            # Check if jump is too large (e.g., h1 to h4)
            if heading_levels[i] - heading_levels[i-1] > 1:
                return False

        return True

    def _create_error_report(self, error_message: str) -> QualityReport:
        """Create error report when analysis fails."""
        # Initialize with placeholder values - will be calculated later
        report = QualityReport(overall_score=0.0, quality_level=QualityLevel.POOR)
        report.overall_score = 0
        report.quality_level = QualityLevel.CRITICAL
        report.recommendations = [f"Analysis failed: {error_message}"]
        return report


def analyze_epub_quality(epub_path: Path) -> QualityReport:
    """Convenience function to analyze EPUB quality."""
    analyzer = EPUBQualityAnalyzer()
    return analyzer.analyze_epub(epub_path)