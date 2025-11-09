"""
Smart Table of Contents Generation for EPUB

This module provides intelligent table of contents generation with:
- AI-powered chapter detection and structuring
- Automatic section numbering and hierarchy
- Smart title extraction and cleanup
- Multi-level navigation support
- Reading progress estimation
- Bookmark and navigation aids
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union


class TocLevel(Enum):
    """Table of contents hierarchy levels."""
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    SUBSUBSECTION = "subsubsection"


class NumberingStyle(Enum):
    """Chapter/section numbering styles."""
    NONE = "none"
    NUMERIC = "numeric"  # 1, 2, 3
    ROMAN = "roman"      # I, II, III
    ROMAN_LOWER = "roman_lower"  # i, ii, iii
    ALPHA = "alpha"      # A, B, C
    ALPHA_LOWER = "alpha_lower"  # a, b, c
    WORDS = "words"      # One, Two, Three


@dataclass
class TocEntry:
    """Represents a single table of contents entry."""

    # Content
    title: str
    level: TocLevel
    href: str

    # Hierarchy
    parent: Optional['TocEntry'] = None
    children: List['TocEntry'] = field(default_factory=list)

    # Numbering
    number: Optional[Union[int, str]] = None
    display_number: str = ""

    # Metadata
    word_count: int = 0
    estimated_reading_time: int = 0  # minutes
    page_breaks: int = 0

    # Content analysis
    content_type: str = "chapter"  # chapter, preface, appendix, etc.
    importance_score: float = 1.0

    # Navigation aids
    anchor_id: str = ""
    epub_type: str = ""


@dataclass
class SmartTocConfig:
    """Configuration for smart TOC generation."""

    # Detection settings
    min_chapter_words: int = 100
    max_toc_depth: int = 3
    auto_detect_parts: bool = True
    auto_detect_preface: bool = True
    auto_detect_appendix: bool = True

    # Numbering
    chapter_numbering: NumberingStyle = NumberingStyle.NUMERIC
    section_numbering: NumberingStyle = NumberingStyle.NUMERIC
    include_unnumbered: bool = True

    # Title processing
    clean_titles: bool = True
    max_title_length: int = 100
    capitalize_titles: bool = False

    # Reading time estimation
    words_per_minute: int = 250
    include_reading_time: bool = False

    # Special sections
    frontmatter_patterns: List[str] = field(default_factory=lambda: [
        r"preface", r"foreword", r"introduction", r"prologue", r"acknowledgments"
    ])
    backmatter_patterns: List[str] = field(default_factory=lambda: [
        r"epilogue", r"afterword", r"appendix", r"bibliography", r"index", r"glossary"
    ])

    # Content filtering
    exclude_patterns: List[str] = field(default_factory=lambda: [
        r"table of contents", r"copyright", r"about the author"
    ])


class SmartTocGenerator:
    """Smart table of contents generator."""

    def __init__(self, config: SmartTocConfig):
        self.config = config
        self.entries: List[TocEntry] = []
        self._statistics = {
            "total_entries": 0,
            "chapters": 0,
            "sections": 0,
            "total_words": 0,
            "estimated_reading_time": 0
        }

    def generate_toc(self, html_chunks: List[str], titles: List[str] | None = None) -> List[TocEntry]:
        """Generate smart table of contents from HTML content."""

        # Extract headings from content
        all_headings = self._extract_headings(html_chunks)

        # Analyze and classify headings
        classified_headings = self._classify_headings(all_headings)

        # Build hierarchy
        toc_entries = self._build_hierarchy(classified_headings)

        # Apply numbering
        toc_entries = self._apply_numbering(toc_entries)

        # Calculate reading metrics
        toc_entries = self._calculate_reading_metrics(toc_entries, html_chunks)

        # Generate navigation aids
        toc_entries = self._generate_navigation_aids(toc_entries)

        self.entries = toc_entries
        self._update_statistics()

        return toc_entries

    def _extract_headings(self, html_chunks: List[str]) -> List[Dict]:
        """Extract all headings from HTML content."""
        headings = []

        heading_pattern = r'<(h[1-6])([^>]*)>(.*?)</\1>'

        for chunk_idx, chunk in enumerate(html_chunks):
            matches = re.finditer(heading_pattern, chunk, re.IGNORECASE | re.DOTALL)

            for match in matches:
                tag = match.group(1).lower()
                attrs = match.group(2)
                content = match.group(3)

                # Clean up content
                clean_content = re.sub(r'<[^>]+>', '', content).strip()

                if clean_content and len(clean_content) > 0:
                    # Extract level from tag
                    level = int(tag[1])

                    # Extract any existing id
                    id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attrs)
                    existing_id = id_match.group(1) if id_match else ""

                    headings.append({
                        'title': clean_content,
                        'level': level,
                        'chunk_index': chunk_idx,
                        'raw_html': match.group(0),
                        'id': existing_id,
                        'position': match.start()
                    })

        return headings

    def _classify_headings(self, headings: List[Dict]) -> List[Dict]:
        """Classify headings into content types."""

        for heading in headings:
            title_lower = heading['title'].lower()

            # Check for frontmatter
            if any(re.search(pattern, title_lower) for pattern in self.config.frontmatter_patterns):
                heading['content_type'] = 'frontmatter'
                heading['toc_level'] = TocLevel.CHAPTER

            # Check for backmatter
            elif any(re.search(pattern, title_lower) for pattern in self.config.backmatter_patterns):
                heading['content_type'] = 'backmatter'
                heading['toc_level'] = TocLevel.CHAPTER

            # Check for parts (usually h1 with specific patterns)
            elif heading['level'] == 1 and self.config.auto_detect_parts:
                if re.search(r'\bpart\b|\bbook\b|\bvolume\b', title_lower):
                    heading['content_type'] = 'part'
                    heading['toc_level'] = TocLevel.PART
                else:
                    heading['content_type'] = 'chapter'
                    heading['toc_level'] = TocLevel.CHAPTER

            # Regular chapters (h1 and h2)
            elif heading['level'] in [1, 2]:
                heading['content_type'] = 'chapter'
                heading['toc_level'] = TocLevel.CHAPTER

            # Sections (h3)
            elif heading['level'] == 3:
                heading['content_type'] = 'section'
                heading['toc_level'] = TocLevel.SECTION

            # Subsections (h4)
            elif heading['level'] == 4:
                heading['content_type'] = 'subsection'
                heading['toc_level'] = TocLevel.SUBSECTION

            # Sub-subsections (h5, h6)
            else:
                heading['content_type'] = 'subsubsection'
                heading['toc_level'] = TocLevel.SUBSUBSECTION

            # Check if should be excluded
            if any(re.search(pattern, title_lower) for pattern in self.config.exclude_patterns):
                heading['exclude'] = True
            else:
                heading['exclude'] = False

        return [h for h in headings if not h.get('exclude', False)]

    def _build_hierarchy(self, headings: List[Dict]) -> List[TocEntry]:
        """Build hierarchical structure from classified headings."""
        entries = []
        stack = []  # Stack to track parent entries

        for heading in headings:
            # Clean title if configured
            title = self._clean_title(heading['title']) if self.config.clean_titles else heading['title']

            # Generate href
            href = f"chapter_{heading['chunk_index']}.xhtml"
            if heading['id']:
                href += f"#{heading['id']}"

            # Create entry
            entry = TocEntry(
                title=title,
                level=heading['toc_level'],
                href=href,
                content_type=heading['content_type'],
                anchor_id=heading['id'] or f"heading_{len(entries)}",
                epub_type=self._get_epub_type(heading['content_type'])
            )

            # Determine parent based on hierarchy
            while stack and self._should_pop_stack(stack[-1].level, entry.level):
                stack.pop()

            if stack:
                parent = stack[-1]
                entry.parent = parent
                parent.children.append(entry)
            else:
                entries.append(entry)

            stack.append(entry)

        return entries

    def _should_pop_stack(self, parent_level: TocLevel, current_level: TocLevel) -> bool:
        """Determine if we should pop from the parent stack."""
        level_order = [TocLevel.PART, TocLevel.CHAPTER, TocLevel.SECTION,
                      TocLevel.SUBSECTION, TocLevel.SUBSUBSECTION]

        try:
            parent_idx = level_order.index(parent_level)
            current_idx = level_order.index(current_level)
            return current_idx <= parent_idx
        except ValueError:
            return False

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title text."""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()

        # Remove numbering if it's redundant
        title = re.sub(r'^(chapter|section|part)\s*\d+:?\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^\d+\.?\s*', '', title)

        # Capitalize if configured
        if self.config.capitalize_titles:
            title = title.title()

        # Truncate if too long
        if len(title) > self.config.max_title_length:
            title = title[:self.config.max_title_length - 3] + "..."

        return title

    def _get_epub_type(self, content_type: str) -> str:
        """Get EPUB type for content type."""
        type_mapping = {
            'part': 'part',
            'chapter': 'chapter',
            'section': 'section',
            'frontmatter': 'frontmatter',
            'backmatter': 'backmatter'
        }
        return type_mapping.get(content_type, 'chapter')

    def _apply_numbering(self, entries: List[TocEntry]) -> List[TocEntry]:
        """Apply numbering to TOC entries."""

        def number_entries(entry_list: List[TocEntry], level: TocLevel, counter: int = 1):
            for entry in entry_list:
                if entry.level == level:
                    if level == TocLevel.CHAPTER:
                        entry.number = counter
                        entry.display_number = self._format_number(counter, self.config.chapter_numbering)
                        counter += 1
                    elif level == TocLevel.SECTION:
                        entry.number = counter
                        entry.display_number = self._format_number(counter, self.config.section_numbering)
                        counter += 1

                # Recursively number children
                if entry.children:
                    number_entries(entry.children, level, 1)

        # Number chapters
        chapter_counter = 1
        for entry in self._get_all_entries(entries):
            if entry.level == TocLevel.CHAPTER and entry.content_type == 'chapter':
                entry.number = chapter_counter
                entry.display_number = self._format_number(chapter_counter, self.config.chapter_numbering)
                chapter_counter += 1

        # Number sections within each chapter
        for entry in self._get_all_entries(entries):
            if entry.level == TocLevel.CHAPTER:
                section_counter = 1
                for child in entry.children:
                    if child.level == TocLevel.SECTION:
                        child.number = section_counter
                        child.display_number = self._format_number(section_counter, self.config.section_numbering)
                        section_counter += 1

        return entries

    def _format_number(self, number: int, style: NumberingStyle) -> str:
        """Format number according to numbering style."""
        if style == NumberingStyle.NONE:
            return ""
        elif style == NumberingStyle.NUMERIC:
            return str(number)
        elif style == NumberingStyle.ROMAN:
            return self._int_to_roman(number).upper()
        elif style == NumberingStyle.ROMAN_LOWER:
            return self._int_to_roman(number).lower()
        elif style == NumberingStyle.ALPHA:
            return chr(ord('A') + number - 1) if number <= 26 else f"A{number-26}"
        elif style == NumberingStyle.ALPHA_LOWER:
            return chr(ord('a') + number - 1) if number <= 26 else f"a{number-26}"
        elif style == NumberingStyle.WORDS:
            word_map = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
                       6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}
            return word_map.get(number, str(number))
        return str(number)

    def _int_to_roman(self, num: int) -> str:
        """Convert integer to Roman numeral."""
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        literals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']

        result = ""
        for i in range(len(values)):
            while num >= values[i]:
                result += literals[i]
                num -= values[i]
        return result

    def _calculate_reading_metrics(self, entries: List[TocEntry], html_chunks: List[str]) -> List[TocEntry]:
        """Calculate word counts and reading time estimates."""

        def count_words_in_chunk(chunk: str) -> int:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', chunk)
            # Count words
            words = re.findall(r'\b\w+\b', text)
            return len(words)

        for entry in self._get_all_entries(entries):
            # Extract chunk index from href
            chunk_match = re.search(r'chapter_(\d+)', entry.href)
            if chunk_match:
                chunk_idx = int(chunk_match.group(1))
                if chunk_idx < len(html_chunks):
                    entry.word_count = count_words_in_chunk(html_chunks[chunk_idx])
                    entry.estimated_reading_time = max(1, entry.word_count // self.config.words_per_minute)

        return entries

    def _generate_navigation_aids(self, entries: List[TocEntry]) -> List[TocEntry]:
        """Generate navigation aids and anchors."""

        for entry in self._get_all_entries(entries):
            # Generate anchor ID if not present
            if not entry.anchor_id:
                safe_title = re.sub(r'[^\w\s-]', '', entry.title)
                safe_title = re.sub(r'\s+', '-', safe_title).lower()
                entry.anchor_id = f"toc-{safe_title}"

            # Set importance score based on level and content
            if entry.level == TocLevel.PART:
                entry.importance_score = 1.0
            elif entry.level == TocLevel.CHAPTER:
                entry.importance_score = 0.8
            elif entry.content_type in ['frontmatter', 'backmatter']:
                entry.importance_score = 0.6
            else:
                entry.importance_score = 0.4

        return entries

    def _get_all_entries(self, entries: List[TocEntry]) -> List[TocEntry]:
        """Get all entries in flat list (depth-first)."""
        result = []
        for entry in entries:
            result.append(entry)
            result.extend(self._get_all_entries(entry.children))
        return result

    def _update_statistics(self) -> None:
        """Update generation statistics."""
        all_entries = self._get_all_entries(self.entries)

        self._statistics = {
            "total_entries": len(all_entries),
            "chapters": len([e for e in all_entries if e.level == TocLevel.CHAPTER]),
            "sections": len([e for e in all_entries if e.level == TocLevel.SECTION]),
            "total_words": sum(e.word_count for e in all_entries),
            "estimated_reading_time": sum(e.estimated_reading_time for e in all_entries)
        }

    def generate_nav_xhtml(self) -> str:
        """Generate EPUB 3 navigation XHTML."""
        nav_html = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Navigation</title>
    <meta charset="UTF-8"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
'''

        def render_entry(entry: TocEntry, depth: int = 0) -> str:
            if depth > self.config.max_toc_depth:
                return ""

            html = f'<li><a href="{entry.href}">'

            if entry.display_number:
                html += f'<span class="chapter-number">{entry.display_number}. </span>'

            html += f'{entry.title}</a>'

            if self.config.include_reading_time and entry.estimated_reading_time > 0:
                html += f' <span class="reading-time">({entry.estimated_reading_time} min)</span>'

            if entry.children:
                html += '<ol>'
                for child in entry.children:
                    html += render_entry(child, depth + 1)
                html += '</ol>'

            html += '</li>\n'
            return html

        for entry in self.entries:
            nav_html += render_entry(entry)

        nav_html += '''        </ol>
    </nav>
</body>
</html>'''

        return nav_html

    def get_statistics_report(self) -> str:
        """Generate a statistics report."""
        stats = self._statistics

        return f"""
Smart TOC Generation Report
==========================

Entries Generated: {stats['total_entries']}
  • Chapters: {stats['chapters']}
  • Sections: {stats['sections']}

Content Analysis:
  • Total Words: {stats['total_words']:,}
  • Estimated Reading Time: {stats['estimated_reading_time']} minutes

Configuration:
  • Max Depth: {self.config.max_toc_depth}
  • Chapter Numbering: {self.config.chapter_numbering.value}
  • Section Numbering: {self.config.section_numbering.value}
"""


def create_default_toc_config() -> SmartTocConfig:
    """Create default TOC configuration."""
    return SmartTocConfig()


def create_academic_toc_config() -> SmartTocConfig:
    """Create TOC configuration for academic documents."""
    return SmartTocConfig(
        max_toc_depth=4,
        chapter_numbering=NumberingStyle.NUMERIC,
        section_numbering=NumberingStyle.NUMERIC,
        include_reading_time=True,
        auto_detect_parts=True,
        frontmatter_patterns=[
            r"abstract", r"preface", r"acknowledgments", r"introduction"
        ],
        backmatter_patterns=[
            r"conclusion", r"bibliography", r"references", r"appendix", r"index"
        ]
    )


def create_fiction_toc_config() -> SmartTocConfig:
    """Create TOC configuration for fiction books."""
    return SmartTocConfig(
        max_toc_depth=2,
        chapter_numbering=NumberingStyle.NUMERIC,
        section_numbering=NumberingStyle.NONE,
        clean_titles=True,
        auto_detect_parts=True,
        frontmatter_patterns=[
            r"prologue", r"preface", r"foreword"
        ],
        backmatter_patterns=[
            r"epilogue", r"afterword", r"about the author"
        ]
    )