"""
Content Validation Engine for Docx2Shelf.

Provides comprehensive content quality checks including grammar, style,
formatting, and readability analysis with actionable recommendations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationCategory(Enum):
    """Content validation categories."""

    GRAMMAR = "grammar"
    STYLE = "style"
    FORMATTING = "formatting"
    READABILITY = "readability"
    CONSISTENCY = "consistency"
    STRUCTURE = "structure"


class ValidationSeverity(Enum):
    """Validation issue severity levels."""

    ERROR = "error"  # Must fix
    WARNING = "warning"  # Should fix
    SUGGESTION = "suggestion"  # Consider fixing
    INFO = "info"  # For information only


@dataclass
class ValidationIssue:
    """Individual content validation issue."""

    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    suggestion: str
    context: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    auto_fixable: bool = False
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class ContentStats:
    """Content statistics for analysis."""

    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    avg_words_per_sentence: float = 0.0
    avg_sentences_per_paragraph: float = 0.0
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    unique_words: int = 0
    vocabulary_diversity: float = 0.0


@dataclass
class ValidationReport:
    """Content validation report."""

    file_path: str
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: ContentStats = field(default_factory=ContentStats)
    error_count: int = 0
    warning_count: int = 0
    suggestion_count: int = 0
    auto_fixable_count: int = 0


class ContentValidator:
    """Comprehensive content validation engine."""

    def __init__(self):
        self.common_words = {
            "the",
            "be",
            "to",
            "of",
            "and",
            "a",
            "in",
            "that",
            "have",
            "i",
            "it",
            "for",
            "not",
            "on",
            "with",
            "he",
            "as",
            "you",
            "do",
            "at",
            "this",
            "but",
            "his",
            "by",
            "from",
        }

        # Common style patterns
        self.style_patterns = self._initialize_style_patterns()
        self.formatting_patterns = self._initialize_formatting_patterns()

    def validate_content(self, content: str, file_path: str = "") -> ValidationReport:
        """Validate content and return comprehensive report."""
        report = ValidationReport(file_path=file_path)

        # Extract text content from HTML/XHTML
        text_content = self._extract_text(content)

        # Extract raw text preserving original spacing for grammar checks
        raw_text = self._extract_text_raw(content)

        # Calculate content statistics
        report.stats = self._calculate_stats(text_content)

        # Run validation checks
        self._check_grammar(content, raw_text, report)
        self._check_style(content, text_content, report)
        self._check_formatting(content, report)
        self._check_readability(text_content, report)
        self._check_consistency(content, text_content, report)
        self._check_structure(content, report)

        # Count issues by severity
        report.error_count = len(
            [i for i in report.issues if i.severity == ValidationSeverity.ERROR]
        )
        report.warning_count = len(
            [i for i in report.issues if i.severity == ValidationSeverity.WARNING]
        )
        report.suggestion_count = len(
            [i for i in report.issues if i.severity == ValidationSeverity.SUGGESTION]
        )
        report.auto_fixable_count = len([i for i in report.issues if i.auto_fixable])

        return report

    def _extract_text(self, content: str) -> str:
        """Extract plain text from HTML/XHTML content."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", content)

        # Decode HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_text_raw(self, content: str) -> str:
        """Extract plain text from HTML/XHTML content preserving original spacing."""
        # Remove HTML tags but preserve whitespace
        text = re.sub(r"<[^>]+>", "", content)

        # Decode HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")

        return text.strip()

    def _calculate_stats(self, text: str) -> ContentStats:
        """Calculate comprehensive content statistics."""
        stats = ContentStats()

        if not text:
            return stats

        # Basic counts
        words = text.split()
        stats.word_count = len(words)

        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        stats.sentence_count = len(sentences)

        paragraphs = text.split("\n\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        stats.paragraph_count = len(paragraphs)

        # Average calculations
        if stats.sentence_count > 0:
            stats.avg_words_per_sentence = stats.word_count / stats.sentence_count

        if stats.paragraph_count > 0:
            stats.avg_sentences_per_paragraph = stats.sentence_count / stats.paragraph_count

        # Readability scores
        stats.flesch_reading_ease = self._calculate_flesch_reading_ease(text, stats)
        stats.flesch_kincaid_grade = self._calculate_flesch_kincaid_grade(text, stats)

        # Vocabulary analysis
        unique_words = set(word.lower().strip('.,!?;:"()[]{}') for word in words)
        stats.unique_words = len(unique_words)

        if stats.word_count > 0:
            stats.vocabulary_diversity = stats.unique_words / stats.word_count

        return stats

    def _check_grammar(self, content: str, text: str, report: ValidationReport):
        """Check for common grammar issues."""

        # Double spaces
        if "  " in text:
            matches = [(m.start(), m.end()) for m in re.finditer(r"  +", text)]
            for start, end in matches:
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.GRAMMAR,
                        ValidationSeverity.WARNING,
                        "Multiple consecutive spaces",
                        "Found multiple spaces in a row",
                        "Replace with single space",
                        context=text[max(0, start - 20) : min(len(text), end + 20)],
                        file_path=report.file_path,
                        start_pos=start,
                        end_pos=end,
                        auto_fixable=True,
                        confidence=0.95,
                    )
                )

        # Space before punctuation
        pattern = r"\s+([.!?,:;])"
        matches = list(re.finditer(pattern, text))
        for match in matches:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.GRAMMAR,
                    ValidationSeverity.WARNING,
                    "Space before punctuation",
                    f"Unnecessary space before '{match.group(1)}'",
                    "Remove space before punctuation",
                    context=text[max(0, match.start() - 15) : min(len(text), match.end() + 15)],
                    file_path=report.file_path,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    auto_fixable=True,
                    confidence=0.9,
                )
            )

        # Missing space after punctuation
        pattern = r"([.!?,:;])([A-Za-z])"
        matches = list(re.finditer(pattern, text))
        for match in matches:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.GRAMMAR,
                    ValidationSeverity.WARNING,
                    "Missing space after punctuation",
                    f"No space after '{match.group(1)}'",
                    "Add space after punctuation",
                    context=text[max(0, match.start() - 10) : min(len(text), match.end() + 20)],
                    file_path=report.file_path,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    auto_fixable=True,
                    confidence=0.85,
                )
            )

        # Common typos and errors
        common_errors = {
            r"\bteh\b": "the",
            r"\band\sand\b": "and",
            r"\byou\syou\b": "you",
            r"\bwith\swith\b": "with",
            r"\bform\b(?=\s+the)": "from",  # "form the" -> "from the"
        }

        for pattern, correction in common_errors.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.GRAMMAR,
                        ValidationSeverity.ERROR,
                        "Possible typo",
                        f"'{match.group()}' might be a typo",
                        f"Consider changing to '{correction}'",
                        context=text[max(0, match.start() - 15) : min(len(text), match.end() + 15)],
                        file_path=report.file_path,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        auto_fixable=True,
                        confidence=0.8,
                    )
                )

    def _check_style(self, content: str, text: str, report: ValidationReport):
        """Check for style issues."""

        # Passive voice detection (simplified)
        passive_patterns = [
            r"\b(was|were|is|are|been|being)\s+\w+ed\b",
            r"\b(was|were|is|are|been|being)\s+\w+en\b",
        ]

        for pattern in passive_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.STYLE,
                        ValidationSeverity.SUGGESTION,
                        "Possible passive voice",
                        f"'{match.group()}' may be passive voice",
                        "Consider using active voice for more engaging writing",
                        context=text[max(0, match.start() - 20) : min(len(text), match.end() + 20)],
                        file_path=report.file_path,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.6,
                    )
                )

        # Redundant phrases
        redundant_phrases = {
            r"\bvery\s+unique\b": "unique",
            r"\bfree\s+gift\b": "gift",
            r"\bfuture\s+plans\b": "plans",
            r"\bpast\s+history\b": "history",
            r"\bin\s+order\s+to\b": "to",
            r"\bdue\s+to\s+the\s+fact\s+that\b": "because",
        }

        for pattern, suggestion in redundant_phrases.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.STYLE,
                        ValidationSeverity.SUGGESTION,
                        "Redundant phrase",
                        f"'{match.group()}' is redundant",
                        f"Consider using '{suggestion}' instead",
                        context=text[max(0, match.start() - 15) : min(len(text), match.end() + 15)],
                        file_path=report.file_path,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        auto_fixable=True,
                        confidence=0.75,
                    )
                )

        # Overused words
        words = text.lower().split()
        word_counts = {}
        for word in words:
            clean_word = word.strip('.,!?;:"()[]{}')
            if len(clean_word) > 4 and clean_word not in self.common_words:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1

        for word, count in word_counts.items():
            if count > len(words) / 100:  # More than 1% of total words
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.STYLE,
                        ValidationSeverity.SUGGESTION,
                        "Overused word",
                        f"The word '{word}' appears {count} times",
                        "Consider using synonyms for variety",
                        file_path=report.file_path,
                        confidence=0.7,
                    )
                )

    def _check_formatting(self, content: str, report: ValidationReport):
        """Check for formatting issues."""

        # Multiple consecutive line breaks
        pattern = r"\n\s*\n\s*\n+"
        matches = list(re.finditer(pattern, content))
        for match in matches:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.FORMATTING,
                    ValidationSeverity.WARNING,
                    "Multiple line breaks",
                    "Found multiple consecutive line breaks",
                    "Use consistent paragraph spacing",
                    file_path=report.file_path,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    auto_fixable=True,
                    confidence=0.9,
                )
            )

        # Inconsistent quotation marks
        straight_quotes = content.count('"') + content.count("'")
        smart_quotes = (
            content.count('"') + content.count('"') + content.count(""") + content.count(""")
        )

        if straight_quotes > 0 and smart_quotes > 0:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.FORMATTING,
                    ValidationSeverity.WARNING,
                    "Inconsistent quotation marks",
                    "Mix of straight and smart quotes detected",
                    "Use consistent quotation mark style throughout",
                    file_path=report.file_path,
                    auto_fixable=True,
                    confidence=0.85,
                )
            )

        # Empty paragraphs
        empty_p_pattern = r"<p>\s*</p>"
        matches = list(re.finditer(empty_p_pattern, content))
        for match in matches:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.FORMATTING,
                    ValidationSeverity.WARNING,
                    "Empty paragraph",
                    "Found empty paragraph tag",
                    "Remove empty paragraph or add content",
                    file_path=report.file_path,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    auto_fixable=True,
                    confidence=0.95,
                )
            )

    def _check_readability(self, text: str, report: ValidationReport):
        """Check readability metrics and provide suggestions."""

        if report.stats.avg_words_per_sentence > 25:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.READABILITY,
                    ValidationSeverity.SUGGESTION,
                    "Long sentences",
                    f"Average sentence length is {report.stats.avg_words_per_sentence:.1f} words",
                    "Consider breaking up long sentences for better readability",
                    file_path=report.file_path,
                    confidence=0.8,
                )
            )

        if report.stats.flesch_reading_ease < 30:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.READABILITY,
                    ValidationSeverity.WARNING,
                    "Very difficult to read",
                    f"Flesch Reading Ease score is {report.stats.flesch_reading_ease:.1f} (very difficult)",
                    "Simplify language and sentence structure",
                    file_path=report.file_path,
                    confidence=0.75,
                )
            )
        elif report.stats.flesch_reading_ease < 50:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.READABILITY,
                    ValidationSeverity.SUGGESTION,
                    "Difficult to read",
                    f"Flesch Reading Ease score is {report.stats.flesch_reading_ease:.1f} (difficult)",
                    "Consider simplifying language for broader accessibility",
                    file_path=report.file_path,
                    confidence=0.65,
                )
            )

        if report.stats.flesch_kincaid_grade > 16:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.READABILITY,
                    ValidationSeverity.SUGGESTION,
                    "High grade level",
                    f"Flesch-Kincaid grade level is {report.stats.flesch_kincaid_grade:.1f}",
                    "Consider lowering complexity for wider audience",
                    file_path=report.file_path,
                    confidence=0.7,
                )
            )

    def _check_consistency(self, content: str, text: str, report: ValidationReport):
        """Check for consistency issues."""

        # Inconsistent capitalization in headings
        headings = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", content, re.IGNORECASE | re.DOTALL)
        if len(headings) > 1:
            title_case_count = 0
            sentence_case_count = 0

            for heading in headings:
                heading_text = re.sub(r"<[^>]+>", "", heading).strip()
                if heading_text:
                    words = heading_text.split()
                    if len(words) > 1:
                        # Check if it's title case (most words capitalized)
                        capitalized_words = sum(1 for word in words if word[0].isupper())
                        if capitalized_words > len(words) / 2:
                            title_case_count += 1
                        else:
                            sentence_case_count += 1

            if title_case_count > 0 and sentence_case_count > 0:
                report.issues.append(
                    ValidationIssue(
                        ValidationCategory.CONSISTENCY,
                        ValidationSeverity.WARNING,
                        "Inconsistent heading capitalization",
                        "Mix of title case and sentence case in headings",
                        "Use consistent capitalization style for all headings",
                        file_path=report.file_path,
                        confidence=0.8,
                    )
                )

        # Date format consistency
        date_patterns = [
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}-\d{1,2}-\d{4}\b",  # MM-DD-YYYY
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",  # YYYY-MM-DD
        ]

        found_patterns = set()
        for pattern in date_patterns:
            if re.search(pattern, text):
                found_patterns.add(pattern)

        if len(found_patterns) > 1:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.CONSISTENCY,
                    ValidationSeverity.SUGGESTION,
                    "Inconsistent date formats",
                    "Multiple date formats found in text",
                    "Use consistent date format throughout document",
                    file_path=report.file_path,
                    confidence=0.75,
                )
            )

    def _check_structure(self, content: str, report: ValidationReport):
        """Check document structure issues."""

        # Check for proper paragraph structure
        p_tags = content.count("<p>")
        if p_tags == 0 and len(content) > 1000:
            report.issues.append(
                ValidationIssue(
                    ValidationCategory.STRUCTURE,
                    ValidationSeverity.ERROR,
                    "No paragraph structure",
                    "Content lacks proper paragraph tags",
                    "Wrap text content in <p> tags",
                    file_path=report.file_path,
                    confidence=0.95,
                )
            )

        # Check heading hierarchy
        headings = re.findall(r"<h([1-6])", content)
        if headings:
            heading_levels = [int(h) for h in headings]

            # Check for skipped levels
            for i in range(1, len(heading_levels)):
                if heading_levels[i] - heading_levels[i - 1] > 1:
                    report.issues.append(
                        ValidationIssue(
                            ValidationCategory.STRUCTURE,
                            ValidationSeverity.WARNING,
                            "Skipped heading level",
                            f"Heading jumps from h{heading_levels[i-1]} to h{heading_levels[i]}",
                            "Use sequential heading levels (h1, h2, h3...)",
                            file_path=report.file_path,
                            confidence=0.85,
                        )
                    )
                    break

    def _calculate_flesch_reading_ease(self, text: str, stats: ContentStats) -> float:
        """Calculate Flesch Reading Ease score."""
        if stats.sentence_count == 0 or stats.word_count == 0:
            return 0.0

        # Count syllables (simplified approximation)
        syllable_count = 0
        words = text.split()
        for word in words:
            clean_word = re.sub(r"[^a-zA-Z]", "", word.lower())
            if clean_word:
                # Simple syllable counting heuristic
                vowel_groups = re.findall(r"[aeiouy]+", clean_word)
                syllables = len(vowel_groups)
                if clean_word.endswith("e") and syllables > 1:
                    syllables -= 1
                syllable_count += max(1, syllables)

        avg_sentence_length = stats.word_count / stats.sentence_count
        avg_syllables_per_word = syllable_count / stats.word_count

        return 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

    def _calculate_flesch_kincaid_grade(self, text: str, stats: ContentStats) -> float:
        """Calculate Flesch-Kincaid Grade Level."""
        if stats.sentence_count == 0 or stats.word_count == 0:
            return 0.0

        # Count syllables (same as above)
        syllable_count = 0
        words = text.split()
        for word in words:
            clean_word = re.sub(r"[^a-zA-Z]", "", word.lower())
            if clean_word:
                vowel_groups = re.findall(r"[aeiouy]+", clean_word)
                syllables = len(vowel_groups)
                if clean_word.endswith("e") and syllables > 1:
                    syllables -= 1
                syllable_count += max(1, syllables)

        avg_sentence_length = stats.word_count / stats.sentence_count
        avg_syllables_per_word = syllable_count / stats.word_count

        return (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59

    def _initialize_style_patterns(self) -> Dict[str, str]:
        """Initialize style checking patterns."""
        return {
            "weak_words": r"\b(very|really|quite|rather|somewhat|pretty|fairly)\b",
            "hedge_words": r"\b(maybe|perhaps|possibly|probably|might|could)\b",
            "filler_words": r"\b(just|actually|basically|literally|obviously)\b",
        }

    def _initialize_formatting_patterns(self) -> Dict[str, str]:
        """Initialize formatting checking patterns."""
        return {
            "multiple_spaces": r"  +",
            "tabs_mixed_spaces": r"[\t ]+[\t ]+",
            "trailing_whitespace": r"[ \t]+$",
        }


def validate_content_quality(content: str, file_path: str = "") -> ValidationReport:
    """Convenience function to validate content quality."""
    validator = ContentValidator()
    return validator.validate_content(content, file_path)
