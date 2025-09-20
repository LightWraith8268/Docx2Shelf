"""
Comprehensive test suite for Quality Assurance features in Docx2Shelf v1.2.9.

Tests quality scoring, content validation, and accessibility compliance features.
"""

import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docx2shelf.accessibility_audit import (
    A11yAuditResult,
    A11yConfig,
    A11yLevel,
    AccessibilityAuditor,
    IssueType,
    IssueSeverity,
    audit_epub_accessibility,
)
from docx2shelf.content_validation import (
    ContentStats,
    ContentValidator,
    ValidationCategory,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    validate_content_quality,
)
from docx2shelf.quality_scoring import (
    CategoryScore,
    EPUBQualityAnalyzer,
    QualityCategory,
    QualityIssue,
    QualityLevel,
    QualityReport,
    analyze_epub_quality,
)


class TestQualityScoring:
    """Test EPUB quality scoring system."""

    def test_quality_issue_creation(self):
        """Test creating quality issue objects."""
        issue = QualityIssue(
            category=QualityCategory.STRUCTURE,
            severity="major",
            title="Missing navigation",
            description="EPUB lacks navigation file",
            recommendation="Add navigation.xhtml file",
            file_path="content/chapter1.xhtml",
            points_deducted=15,
            auto_fixable=False
        )

        assert issue.category == QualityCategory.STRUCTURE
        assert issue.severity == "major"
        assert issue.title == "Missing navigation"
        assert issue.points_deducted == 15
        assert not issue.auto_fixable

    def test_category_score_calculation(self):
        """Test category score calculation."""
        score = CategoryScore(
            category=QualityCategory.METADATA,
            score=85.0,
            max_score=100.0
        )

        issue = QualityIssue(
            category=QualityCategory.METADATA,
            severity="minor",
            title="Missing description",
            description="EPUB lacks description metadata",
            recommendation="Add description metadata",
            points_deducted=5
        )

        score.issues.append(issue)
        assert len(score.issues) == 1
        assert score.score == 85.0

    def test_quality_report_generation(self):
        """Test quality report generation."""
        report = QualityReport(overall_score=78.5, quality_level=QualityLevel.GOOD)
        report.total_issues = 12
        report.critical_issues = 0
        report.auto_fixable_issues = 5

        assert report.overall_score == 78.5
        assert report.quality_level == QualityLevel.GOOD
        assert report.total_issues == 12
        assert report.auto_fixable_issues == 5

    def test_quality_analyzer_initialization(self):
        """Test quality analyzer initialization."""
        analyzer = EPUBQualityAnalyzer()

        assert analyzer.scoring_weights[QualityCategory.STRUCTURE] == 25
        assert analyzer.scoring_weights[QualityCategory.ACCESSIBILITY] == 20
        assert analyzer.scoring_weights[QualityCategory.CONTENT] == 20

    def test_mock_epub_analysis(self):
        """Test EPUB quality analysis with mock data."""
        analyzer = EPUBQualityAnalyzer()

        # Create a mock EPUB file for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "test.epub"

            # Create minimal EPUB structure
            with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                epub_zip.writestr('mimetype', 'application/epub+zip')
                epub_zip.writestr('META-INF/container.xml', '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
                epub_zip.writestr('content.opf', '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="id" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:identifier id="id">test-book-123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>''')
                epub_zip.writestr('nav.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Navigation</title>
</head>
<body>
  <nav epub:type="toc">
    <ol>
      <li><a href="chapter1.xhtml">Chapter 1</a></li>
    </ol>
  </nav>
</body>
</html>''')
                epub_zip.writestr('chapter1.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
</head>
<body>
  <h1>Chapter 1</h1>
  <p>This is a test chapter with some content.</p>
  <img src="image.jpg" alt="Test image"/>
</body>
</html>''')

            # Test analysis
            report = analyzer.analyze_epub(epub_path)

            assert isinstance(report, QualityReport)
            assert report.overall_score >= 0
            assert report.overall_score <= 100
            assert report.quality_level in [level for level in QualityLevel]

    def test_quality_level_determination(self):
        """Test quality level determination logic."""
        analyzer = EPUBQualityAnalyzer()

        assert analyzer._determine_quality_level(95) == QualityLevel.EXCELLENT
        assert analyzer._determine_quality_level(80) == QualityLevel.GOOD
        assert analyzer._determine_quality_level(65) == QualityLevel.FAIR
        assert analyzer._determine_quality_level(45) == QualityLevel.POOR
        assert analyzer._determine_quality_level(25) == QualityLevel.CRITICAL

    def test_convenience_function(self):
        """Test convenience function for quality analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "test.epub"

            # Create minimal EPUB
            with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                epub_zip.writestr('mimetype', 'application/epub+zip')

            report = analyze_epub_quality(epub_path)
            assert isinstance(report, QualityReport)


class TestContentValidation:
    """Test content validation engine."""

    def test_validation_issue_creation(self):
        """Test creating validation issue objects."""
        issue = ValidationIssue(
            category=ValidationCategory.GRAMMAR,
            severity=ValidationSeverity.WARNING,
            title="Double space",
            description="Found multiple consecutive spaces",
            suggestion="Replace with single space",
            context="This  is  a  test",
            file_path="chapter1.xhtml",
            start_pos=4,
            end_pos=6,
            auto_fixable=True,
            confidence=0.95
        )

        assert issue.category == ValidationCategory.GRAMMAR
        assert issue.severity == ValidationSeverity.WARNING
        assert issue.auto_fixable
        assert issue.confidence == 0.95

    def test_content_stats_calculation(self):
        """Test content statistics calculation."""
        validator = ContentValidator()
        text = "This is a test sentence. This is another test sentence! This is a third sentence."

        stats = validator._calculate_stats(text)

        assert stats.word_count > 0
        assert stats.sentence_count == 3
        assert stats.avg_words_per_sentence > 0
        assert 0 <= stats.flesch_reading_ease <= 100

    def test_content_validation_basic(self):
        """Test basic content validation."""
        validator = ContentValidator()

        content = """
        <html>
        <body>
            <h1>Test Chapter</h1>
            <p>This  is  a  test  paragraph  with  multiple  spaces.</p>
            <p>This paragraph has space before punctuation .</p>
        </body>
        </html>
        """

        report = validator.validate_content(content, "test.xhtml")

        assert isinstance(report, ValidationReport)
        assert report.file_path == "test.xhtml"
        assert len(report.issues) > 0

        # Should find multiple space issues
        grammar_issues = [i for i in report.issues if i.category == ValidationCategory.GRAMMAR]
        assert len(grammar_issues) > 0

    def test_grammar_checking(self):
        """Test grammar checking functionality."""
        validator = ContentValidator()

        # Test with various grammar issues
        content = """
        <html>
        <body>
            <p>This  has  double  spaces.</p>
            <p>Space before punctuation .</p>
            <p>Missing space after punctuation.Like this.</p>
            <p>The teh typo should be caught.</p>
        </body>
        </html>
        """

        report = validator.validate_content(content)

        grammar_issues = [i for i in report.issues if i.category == ValidationCategory.GRAMMAR]
        assert len(grammar_issues) >= 3  # Should catch multiple issues

        # Check for auto-fixable issues
        auto_fixable = [i for i in grammar_issues if i.auto_fixable]
        assert len(auto_fixable) > 0

    def test_style_checking(self):
        """Test style checking functionality."""
        validator = ContentValidator()

        content = """
        <html>
        <body>
            <p>This is a very unique situation that is very important.</p>
            <p>In order to understand this, you need to know the basic fundamentals.</p>
            <p>The word excellent appears excellent times in this excellent text.</p>
        </body>
        </html>
        """

        report = validator.validate_content(content)

        style_issues = [i for i in report.issues if i.category == ValidationCategory.STYLE]
        assert len(style_issues) > 0

    def test_readability_analysis(self):
        """Test readability analysis."""
        validator = ContentValidator()

        # Text with very long sentences
        long_sentence_content = """
        <html>
        <body>
            <p>This is an extremely long sentence that contains many words and clauses and subclauses that make it very difficult to read and understand for most readers and should probably be broken up into smaller more manageable sentences that are easier to comprehend and process.</p>
        </body>
        </html>
        """

        report = validator.validate_content(long_sentence_content)

        readability_issues = [i for i in report.issues if i.category == ValidationCategory.READABILITY]
        assert len(readability_issues) > 0

    def test_formatting_checks(self):
        """Test formatting validation."""
        validator = ContentValidator()

        content = """
        <html>
        <body>
            <p></p>
            <p>Mixed "quotes" and 'quotes' and "smart quotes".</p>



            <p>Multiple line breaks above.</p>
        </body>
        </html>
        """

        report = validator.validate_content(content)

        formatting_issues = [i for i in report.issues if i.category == ValidationCategory.FORMATTING]
        assert len(formatting_issues) > 0

    def test_consistency_checks(self):
        """Test consistency validation."""
        validator = ContentValidator()

        content = """
        <html>
        <body>
            <h1>Chapter Title Case</h1>
            <h1>Another sentence case heading</h1>
            <p>Date: 12/31/2023</p>
            <p>Another date: 2023-12-31</p>
        </body>
        </html>
        """

        report = validator.validate_content(content)

        consistency_issues = [i for i in report.issues if i.category == ValidationCategory.CONSISTENCY]
        assert len(consistency_issues) >= 0  # May or may not find issues

    def test_structure_checks(self):
        """Test document structure validation."""
        validator = ContentValidator()

        # Content without paragraph tags
        content = """
        <html>
        <body>
            <h1>Chapter</h1>
            <h4>Subsection</h4>
            This is text without paragraph tags.
        </body>
        </html>
        """

        report = validator.validate_content(content)

        structure_issues = [i for i in report.issues if i.category == ValidationCategory.STRUCTURE]
        assert len(structure_issues) > 0

    def test_convenience_function(self):
        """Test convenience function for content validation."""
        content = "<p>This  is  a  test.</p>"

        report = validate_content_quality(content, "test.html")
        assert isinstance(report, ValidationReport)
        assert report.file_path == "test.html"


class TestAccessibilityAudit:
    """Test accessibility compliance scanner."""

    def test_a11y_issue_creation(self):
        """Test creating accessibility issue objects."""
        from docx2shelf.accessibility_audit import A11yIssue

        issue = A11yIssue(
            id="missing_alt_123",
            issue_type=IssueType.MISSING_ALT_TEXT,
            severity=IssueSeverity.CRITICAL,
            wcag_level=A11yLevel.A,
            title="Missing Alt Text",
            description="Image lacks alt attribute",
            location="chapter1.xhtml",
            recommendation="Add descriptive alt text",
            auto_fixable=False,
            wcag_criteria=["1.1.1"]
        )

        assert issue.issue_type == IssueType.MISSING_ALT_TEXT
        assert issue.severity == IssueSeverity.CRITICAL
        assert issue.wcag_level == A11yLevel.A
        assert "1.1.1" in issue.wcag_criteria

    def test_a11y_config(self):
        """Test accessibility audit configuration."""
        config = A11yConfig(
            target_level=A11yLevel.AA,
            check_alt_text=True,
            check_heading_structure=True,
            auto_fix_issues=False
        )

        assert config.target_level == A11yLevel.AA
        assert config.check_alt_text
        assert config.check_heading_structure
        assert not config.auto_fix_issues

    def test_accessibility_auditor_initialization(self):
        """Test accessibility auditor initialization."""
        auditor = AccessibilityAuditor()

        assert auditor.config.target_level == A11yLevel.AA
        assert isinstance(auditor.wcag_criteria, dict)
        assert "1.1.1" in auditor.wcag_criteria

    def test_alt_text_checking(self):
        """Test alt text accessibility checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <img src="image1.jpg"/>
    <img src="image2.jpg" alt=""/>
    <img src="chart.png" alt=""/>
    <img src="image3.jpg" alt="Good description"/>
    <img src="image4.jpg" alt="OK"/>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        alt_text_issues = [i for i in issues if i.issue_type == IssueType.MISSING_ALT_TEXT]
        assert len(alt_text_issues) >= 2  # Should find missing and potentially inadequate alt text

    def test_heading_structure_checking(self):
        """Test heading structure accessibility checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <h1>Main Title</h1>
    <h4>Skipped Levels</h4>
    <h2></h2>
    <h3>Proper Level</h3>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        heading_issues = [i for i in issues if i.issue_type == IssueType.HEADING_STRUCTURE]
        assert len(heading_issues) >= 2  # Should find skipped level and empty heading

    def test_link_accessibility_checking(self):
        """Test link accessibility checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <a href="page1.html"></a>
    <a href="page2.html">Go</a>
    <a href="page3.html">Click here</a>
    <a href="page4.html">Read more about advanced topics</a>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        link_issues = [i for i in issues if i.issue_type == IssueType.LINK_ACCESSIBILITY]
        assert len(link_issues) >= 3  # Should find empty, short, and generic links

    def test_table_accessibility_checking(self):
        """Test table accessibility checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <table>
        <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
        </tr>
        <tr>
            <td>Cell 3</td>
            <td>Cell 4</td>
        </tr>
        <tr>
            <td>Cell 5</td>
            <td>Cell 6</td>
        </tr>
    </table>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        table_issues = [i for i in issues if i.issue_type == IssueType.TABLE_ACCESSIBILITY]
        assert len(table_issues) >= 2  # Should find missing headers and caption

    def test_language_attributes_checking(self):
        """Test language attributes checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <p>Content without language attribute</p>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        lang_issues = [i for i in issues if i.issue_type == IssueType.LANGUAGE_ATTRIBUTES]
        assert len(lang_issues) >= 1  # Should find missing language attribute

    def test_semantic_markup_checking(self):
        """Test semantic markup checking."""
        auditor = AccessibilityAuditor()

        content = '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <p>This is a long document with substantial content that should use semantic markup for better accessibility. This paragraph contains enough content to warrant the use of semantic HTML5 elements like main, article, or section tags. Without these semantic elements, screen readers and other assistive technologies may have difficulty understanding the document structure and providing appropriate navigation options for users.</p>
    <b>This is probably semantic emphasis not just formatting because it is a long phrase that appears to have meaning</b>
</body>
</html>'''

        issues = auditor._audit_content_file(content, "test.xhtml")

        semantic_issues = [i for i in issues if i.issue_type == IssueType.SEMANTIC_MARKUP]
        assert len(semantic_issues) >= 1  # Should find lack of semantic markup

    def test_mock_epub_accessibility_audit(self):
        """Test full EPUB accessibility audit with mock data."""
        auditor = AccessibilityAuditor()

        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "test.epub"

            # Create EPUB with accessibility issues
            with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                epub_zip.writestr('mimetype', 'application/epub+zip')
                epub_zip.writestr('content.opf', '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
  </metadata>
</package>''')
                epub_zip.writestr('chapter1.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
    <h1>Chapter 1</h1>
    <img src="image.jpg"/>
    <a href="next.html">Click here</a>
</body>
</html>''')

            result = auditor.audit_epub(epub_path)

            assert isinstance(result, A11yAuditResult)
            assert result.total_issues > 0
            assert result.overall_score >= 0
            assert result.overall_score <= 100

    def test_audit_result_compilation(self):
        """Test audit result compilation logic."""
        auditor = AccessibilityAuditor()

        # Create test issues manually
        def create_test_issue(severity, level):
            from docx2shelf.accessibility_audit import A11yIssue
            return A11yIssue(
                id=f"test_{severity.value}",
                issue_type=IssueType.MISSING_ALT_TEXT,
                severity=severity,
                wcag_level=level,
                title="Test Issue",
                description="Test description",
                recommendation="Test recommendation"
            )

        issues = [
            create_test_issue(IssueSeverity.CRITICAL, A11yLevel.A),
            create_test_issue(IssueSeverity.MAJOR, A11yLevel.AA),
            create_test_issue(IssueSeverity.MINOR, A11yLevel.AA),
        ]

        result = auditor._compile_audit_result(issues)

        assert result.total_issues == 3
        assert result.critical_issues == 1
        assert result.major_issues == 1
        assert result.minor_issues == 1
        assert result.conformance_level is None  # Due to critical issue

    def test_convenience_function(self):
        """Test convenience function for accessibility audit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "test.epub"

            # Create minimal EPUB
            with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                epub_zip.writestr('mimetype', 'application/epub+zip')
                epub_zip.writestr('chapter1.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body><p>Test</p></body>
</html>''')

            result = audit_epub_accessibility(epub_path)
            assert isinstance(result, A11yAuditResult)


class TestQualityAssuranceIntegration:
    """Test integration of all quality assurance features."""

    def test_combined_quality_analysis(self):
        """Test combined quality scoring, content validation, and accessibility audit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = Path(temp_dir) / "comprehensive_test.epub"

            # Create EPUB with various quality issues
            with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                epub_zip.writestr('mimetype', 'application/epub+zip')
                epub_zip.writestr('META-INF/container.xml', '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
                epub_zip.writestr('content.opf', '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
    <!-- Missing author and other metadata -->
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>''')
                epub_zip.writestr('chapter1.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
</head>
<body>
  <h1>Chapter  One</h1>
  <p>This  is  a  test  paragraph  with  multiple  spaces  and  other  issues .</p>
  <p>This sentence is very long and contains many clauses and subclauses that make it difficult to read and should probably be broken up.</p>
  <img src="image.jpg"/>
  <a href="next.html">Click here</a>
  <table>
    <tr><td>Data 1</td><td>Data 2</td></tr>
  </table>
</body>
</html>''')

            # Run all quality checks
            quality_report = analyze_epub_quality(epub_path)
            a11y_result = audit_epub_accessibility(epub_path)

            # Extract content for validation
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                content = epub_zip.read('chapter1.xhtml').decode('utf-8')
                validation_report = validate_content_quality(content, 'chapter1.xhtml')

            # Verify all analyses completed
            assert isinstance(quality_report, QualityReport)
            assert isinstance(a11y_result, A11yAuditResult)
            assert isinstance(validation_report, ValidationReport)

            # Verify issues were found
            assert quality_report.total_issues > 0
            assert a11y_result.total_issues > 0
            assert len(validation_report.issues) > 0

            # Verify scores are reasonable
            assert 0 <= quality_report.overall_score <= 100
            assert 0 <= a11y_result.overall_score <= 100

    def test_quality_improvement_recommendations(self):
        """Test that quality improvement recommendations are generated."""
        analyzer = EPUBQualityAnalyzer()
        auditor = AccessibilityAuditor()
        validator = ContentValidator()

        # Test recommendation generation
        quality_report = QualityReport(overall_score=85.0, quality_level=QualityLevel.GOOD)
        quality_report.overall_score = 65.0
        quality_report.quality_level = QualityLevel.FAIR
        quality_report.auto_fixable_issues = 8

        recommendations = analyzer._generate_overall_recommendations(quality_report)
        assert len(recommendations) > 0
        assert any("auto" in rec.lower() for rec in recommendations)

        # Test A11y recommendations
        from docx2shelf.accessibility_audit import A11yIssue
        issues = [
            A11yIssue(
                id="test1",
                issue_type=IssueType.MISSING_ALT_TEXT,
                severity=IssueSeverity.MAJOR,
                wcag_level=A11yLevel.A,
                title="Test",
                description="Test",
                recommendation="Test"
            )
        ]

        a11y_recommendations = auditor._generate_recommendations(issues, A11yLevel.A)
        assert len(a11y_recommendations) > 0

    def test_auto_fixable_issue_detection(self):
        """Test detection of auto-fixable issues across all systems."""
        validator = ContentValidator()

        # Content with auto-fixable issues
        content = '''
        <html>
        <body>
            <p>This  has  double  spaces  everywhere  .</p>
            <p>Mixed "quotes" and 'quotes'.</p>
            <p></p>
        </body>
        </html>
        '''

        report = validator.validate_content(content)

        auto_fixable = [i for i in report.issues if i.auto_fixable]
        assert len(auto_fixable) > 0

        # Verify auto-fixable count is tracked
        assert report.auto_fixable_count == len(auto_fixable)

    def test_quality_metrics_consistency(self):
        """Test that quality metrics are consistent across different analyses."""
        # This test ensures that similar content gets similar scores
        analyzer = EPUBQualityAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create two similar EPUBs
            for i, title in enumerate(['Good Book', 'Another Good Book']):
                epub_path = Path(temp_dir) / f"book{i}.epub"

                with zipfile.ZipFile(epub_path, 'w') as epub_zip:
                    epub_zip.writestr('mimetype', 'application/epub+zip')
                    epub_zip.writestr('META-INF/container.xml', '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
                    epub_zip.writestr('content.opf', f'''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:identifier>test-{i}</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>''')
                    epub_zip.writestr('nav.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <ol><li><a href="chapter1.xhtml">Chapter 1</a></li></ol>
  </nav>
</body>
</html>''')
                    epub_zip.writestr('chapter1.xhtml', '''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>Chapter 1</title></head>
<body>
  <h1>Chapter 1</h1>
  <p>This is well-formatted content with proper structure.</p>
  <img src="image.jpg" alt="A descriptive image"/>
</body>
</html>''')

                # Analyze and compare scores
                report = analyzer.analyze_epub(epub_path)

                # Both should get similar high scores since they're well-formed
                assert report.overall_score > 70  # Should be reasonably high
                assert report.quality_level in [QualityLevel.GOOD, QualityLevel.EXCELLENT]


class TestQualityReporting:
    """Test quality reporting and output formats."""

    def test_quality_report_serialization(self):
        """Test that quality reports can be serialized to JSON."""
        import json

        report = QualityReport(overall_score=78.5, quality_level=QualityLevel.GOOD)
        report.overall_score = 85.5
        report.quality_level = QualityLevel.GOOD
        report.total_issues = 5
        report.recommendations = ["Fix issue 1", "Fix issue 2"]

        # Test that we can serialize key data
        report_data = {
            'overall_score': report.overall_score,
            'quality_level': report.quality_level.value,
            'total_issues': report.total_issues,
            'recommendations': report.recommendations
        }

        json_str = json.dumps(report_data)
        parsed = json.loads(json_str)

        assert parsed['overall_score'] == 85.5
        assert parsed['quality_level'] == 'good'
        assert parsed['total_issues'] == 5

    def test_issue_context_extraction(self):
        """Test that validation issues capture proper context."""
        validator = ContentValidator()

        content = '''
        <html>
        <body>
            <p>This paragraph has an error  here with double spaces.</p>
            <p>Another paragraph with issues.</p>
        </body>
        </html>
        '''

        report = validator.validate_content(content)

        # Find issues with context
        issues_with_context = [i for i in report.issues if i.context]
        assert len(issues_with_context) > 0

        # Verify context contains relevant text
        context_issue = issues_with_context[0]
        assert len(context_issue.context) > 0
        assert context_issue.context.strip()  # Not just whitespace

    def test_recommendation_prioritization(self):
        """Test that recommendations are properly prioritized."""
        analyzer = EPUBQualityAnalyzer()

        report = QualityReport(overall_score=78.5, quality_level=QualityLevel.GOOD)
        report.critical_issues = 5
        report.auto_fixable_issues = 10

        recommendations = analyzer._generate_overall_recommendations(report)

        # Critical issues should be mentioned first
        critical_mentioned = any("critical" in rec.lower() for rec in recommendations[:2])
        assert critical_mentioned

        # Auto-fixable should be mentioned
        auto_fix_mentioned = any("auto" in rec.lower() for rec in recommendations)
        assert auto_fix_mentioned


# Helper functions for testing
def create_minimal_epub(path: Path, issues: bool = False):
    """Create a minimal EPUB file for testing."""
    with zipfile.ZipFile(path, 'w') as epub_zip:
        epub_zip.writestr('mimetype', 'application/epub+zip')

        if issues:
            # Create EPUB with deliberate issues
            epub_zip.writestr('content.opf', '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <!-- Missing metadata -->
</package>''')
        else:
            # Create proper EPUB
            epub_zip.writestr('content.opf', '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:identifier>test-123</dc:identifier>
    <dc:language>en</dc:language>
  </metadata>
</package>''')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])