"""
Indexing System for EPUB Generation

This module handles index generation from Word XE (Index Entry) fields and
creates alphabetical index pages with back-links to occurrences throughout
the document.

Features:
- Parse Word XE (Index Entry) fields from DOCX
- Generate alphabetical index with proper sorting
- Create back-links to all occurrences
- Support for sub-entries and cross-references
- Multi-level index hierarchies
- Customizable index formatting and styling
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class IndexEntryType(Enum):
    """Types of index entries."""

    MAIN = "main"
    SUB = "sub"
    SUB_SUB = "subsub"
    CROSS_REF = "crossref"
    SEE_ALSO = "seealso"


@dataclass
class IndexEntry:
    """Represents a single index entry."""

    # Content
    text: str
    sort_key: str
    entry_type: IndexEntryType = IndexEntryType.MAIN

    # Hierarchy
    parent: Optional["IndexEntry"] = None
    children: List["IndexEntry"] = field(default_factory=list)

    # Occurrences
    occurrences: List["IndexOccurrence"] = field(default_factory=list)

    # Cross-references
    see_refs: List[str] = field(default_factory=list)
    see_also_refs: List[str] = field(default_factory=list)

    # Formatting
    emphasis: bool = False  # Bold or italic
    page_range: bool = False  # Entry spans multiple pages


@dataclass
class IndexOccurrence:
    """Represents an occurrence of an index entry in the document."""

    # Location
    file_path: str
    anchor_id: str
    position: int

    # Context
    surrounding_text: str = ""
    chapter_title: str = ""
    section_title: str = ""

    # Formatting
    emphasis: bool = False
    is_primary: bool = False  # Main discussion of this topic


@dataclass
class IndexConfig:
    """Configuration for index generation."""

    # Processing
    case_sensitive: bool = False
    merge_similar_entries: bool = True
    max_surrounding_context: int = 100

    # Sorting
    ignore_articles: List[str] = field(default_factory=lambda: ["a", "an", "the"])
    locale: str = "en_US"

    # Formatting
    max_entries_per_letter: int = 1000
    show_letter_headers: bool = True
    show_occurrence_count: bool = False

    # Cross-references
    process_see_refs: bool = True
    process_see_also_refs: bool = True

    # Output
    index_file_name: str = "index.xhtml"
    index_title: str = "Index"


@dataclass
class IndexSection:
    """Represents a section of the index (e.g., all entries starting with 'A')."""

    letter: str
    entries: List[IndexEntry] = field(default_factory=list)
    entry_count: int = 0


class IndexGenerator:
    """Generates index from Word XE fields and document content."""

    def __init__(self, config: IndexConfig):
        self.config = config
        self.entries: Dict[str, IndexEntry] = {}
        self.raw_entries: List[Dict] = []
        self._stats = {
            "xe_fields_found": 0,
            "entries_created": 0,
            "occurrences_found": 0,
            "cross_refs_resolved": 0,
        }

    def process_content(
        self, html_chunks: List[str], chunk_files: List[str]
    ) -> Tuple[str, Dict[str, List[str]]]:
        """
        Process HTML content to extract index entries and generate index page.

        Returns:
            Index HTML content and mapping of entries to their occurrence files
        """

        # Step 1: Extract XE fields and index markers
        self._extract_index_markers(html_chunks, chunk_files)

        # Step 2: Parse index entries from markers
        self._parse_index_entries()

        # Step 3: Build index hierarchy
        self._build_index_hierarchy()

        # Step 4: Sort and organize entries
        self._sort_and_organize()

        # Step 5: Resolve cross-references
        self._resolve_cross_references()

        # Step 6: Generate index HTML
        index_html = self._generate_index_html()

        # Step 7: Create occurrence mapping
        occurrence_mapping = self._create_occurrence_mapping()

        return index_html, occurrence_mapping

    def _extract_index_markers(self, html_chunks: List[str], chunk_files: List[str]) -> None:
        """Extract index markers from HTML content."""

        # Patterns for various index marker formats
        xe_patterns = [
            # Word XE field format
            r'<!--\s*XE\s+"([^"]+)"\s*(?:;([^>]*))?\s*-->',
            # HTML data attributes
            r'<span[^>]*data-index-entry\s*=\s*"([^"]+)"[^>]*>(.*?)</span>',
            # Custom index markers
            r'<index-entry[^>]*entry\s*=\s*"([^"]+)"[^>]*(?:\s*/\s*>|>(.*?)</index-entry>)',
            # Hidden index spans
            r'<span[^>]*class\s*=\s*"[^"]*index-marker[^"]*"[^>]*data-entry\s*=\s*"([^"]+)"[^>]*>',
        ]

        entry_id = 1

        for chunk_idx, (chunk, filename) in enumerate(zip(html_chunks, chunk_files)):
            for pattern in xe_patterns:
                for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                    entry_text = match.group(1)
                    context = match.group(2) if match.lastindex and match.lastindex >= 2 else ""

                    # Extract surrounding text for context
                    start_pos = max(0, match.start() - self.config.max_surrounding_context)
                    end_pos = min(len(chunk), match.end() + self.config.max_surrounding_context)
                    surrounding = chunk[start_pos:end_pos]
                    surrounding = re.sub(r"<[^>]+>", " ", surrounding)
                    surrounding = " ".join(surrounding.split())

                    # Create raw entry
                    raw_entry = {
                        "id": f"idx_{entry_id}",
                        "text": entry_text,
                        "file": filename,
                        "position": match.start(),
                        "context": context,
                        "surrounding": surrounding,
                        "anchor_id": f"idx_occurrence_{entry_id}",
                    }

                    self.raw_entries.append(raw_entry)
                    entry_id += 1

        self._stats["xe_fields_found"] = len(self.raw_entries)

    def _parse_index_entries(self) -> None:
        """Parse raw entries into structured index entries."""

        for raw_entry in self.raw_entries:
            # Parse entry text for hierarchy and cross-references
            parsed = self._parse_entry_text(raw_entry["text"])

            # Create or update index entry
            entry_key = self._normalize_entry_key(parsed["main_text"])

            if entry_key not in self.entries:
                self.entries[entry_key] = IndexEntry(
                    text=parsed["main_text"],
                    sort_key=self._generate_sort_key(parsed["main_text"]),
                    entry_type=IndexEntryType.MAIN,
                    emphasis=parsed.get("emphasis", False),
                )

            # Create occurrence
            occurrence = IndexOccurrence(
                file_path=raw_entry["file"],
                anchor_id=raw_entry["anchor_id"],
                position=raw_entry["position"],
                surrounding_text=raw_entry["surrounding"],
                is_primary=parsed.get("primary", False),
            )

            self.entries[entry_key].occurrences.append(occurrence)

            # Handle sub-entries
            if parsed.get("sub_entries"):
                for sub_text in parsed["sub_entries"]:
                    self._add_sub_entry(self.entries[entry_key], sub_text, occurrence)

            # Handle cross-references
            if parsed.get("see_refs"):
                self.entries[entry_key].see_refs.extend(parsed["see_refs"])

            if parsed.get("see_also_refs"):
                self.entries[entry_key].see_also_refs.extend(parsed["see_also_refs"])

        self._stats["entries_created"] = len(self.entries)
        self._stats["occurrences_found"] = sum(
            len(entry.occurrences) for entry in self.entries.values()
        )

    def _parse_entry_text(self, entry_text: str) -> Dict:
        """Parse index entry text for hierarchy and formatting."""

        result = {
            "main_text": entry_text,
            "sub_entries": [],
            "see_refs": [],
            "see_also_refs": [],
            "emphasis": False,
            "primary": False,
        }

        # Handle sub-entries (separated by colons or semicolons)
        if ":" in entry_text:
            parts = entry_text.split(":")
            result["main_text"] = parts[0].strip()
            result["sub_entries"] = [part.strip() for part in parts[1:] if part.strip()]

        # Handle see references
        see_pattern = r"\bsee\s+([^;,]+)"
        see_matches = re.findall(see_pattern, entry_text, re.IGNORECASE)
        if see_matches:
            result["see_refs"] = [ref.strip() for ref in see_matches]
            # Remove see references from main text
            result["main_text"] = re.sub(
                see_pattern, "", result["main_text"], count=0, flags=re.IGNORECASE
            ).strip()

        # Handle see also references
        see_also_pattern = r"\bsee\s+also\s+([^;,]+)"
        see_also_matches = re.findall(see_also_pattern, entry_text, re.IGNORECASE)
        if see_also_matches:
            result["see_also_refs"] = [ref.strip() for ref in see_also_matches]
            # Remove see also references from main text
            result["main_text"] = re.sub(
                see_also_pattern, "", result["main_text"], count=0, flags=re.IGNORECASE
            ).strip()

        # Check for emphasis markers
        if entry_text.startswith("*") or entry_text.endswith("*"):
            result["emphasis"] = True
            result["main_text"] = result["main_text"].strip("*")

        # Check for primary occurrence marker
        if "**" in entry_text:
            result["primary"] = True
            result["main_text"] = result["main_text"].replace("**", "")

        return result

    def _add_sub_entry(
        self, parent_entry: IndexEntry, sub_text: str, occurrence: IndexOccurrence
    ) -> None:
        """Add a sub-entry to a parent entry."""

        # Find or create sub-entry
        sub_entry = None
        for child in parent_entry.children:
            if child.text == sub_text:
                sub_entry = child
                break

        if not sub_entry:
            sub_entry = IndexEntry(
                text=sub_text,
                sort_key=self._generate_sort_key(sub_text),
                entry_type=IndexEntryType.SUB,
                parent=parent_entry,
            )
            parent_entry.children.append(sub_entry)

        sub_entry.occurrences.append(occurrence)

    def _normalize_entry_key(self, text: str) -> str:
        """Normalize entry text for grouping."""
        if not self.config.case_sensitive:
            text = text.lower()

        # Remove leading articles if configured
        for article in self.config.ignore_articles:
            if text.lower().startswith(article.lower() + " "):
                text = text[len(article) :].strip()
                break

        return text

    def _generate_sort_key(self, text: str) -> str:
        """Generate sort key for alphabetical ordering."""

        # Normalize Unicode characters
        normalized = unicodedata.normalize("NFD", text)

        # Remove diacritics
        ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

        # Convert to lowercase for sorting
        sort_key = ascii_text.lower()

        # Remove leading articles
        for article in self.config.ignore_articles:
            if sort_key.startswith(article.lower() + " "):
                sort_key = sort_key[len(article) :].strip()
                break

        return sort_key

    def _build_index_hierarchy(self) -> None:
        """Build hierarchical structure of index entries."""

        # Sort children within each entry
        for entry in self.entries.values():
            entry.children.sort(key=lambda x: x.sort_key)

            # Sort grandchildren if any
            for child in entry.children:
                child.children.sort(key=lambda x: x.sort_key)

    def _sort_and_organize(self) -> None:
        """Sort entries and organize into alphabetical sections."""

        # Sort main entries
        sorted_entries = sorted(self.entries.values(), key=lambda x: x.sort_key)

        # Re-organize into dictionary for easier access
        self.entries = {entry.text: entry for entry in sorted_entries}

    def _resolve_cross_references(self) -> None:
        """Resolve see and see-also cross-references."""

        cross_refs_resolved = 0

        for entry in self.entries.values():
            # Resolve see references
            resolved_see = []
            for see_ref in entry.see_refs:
                target_key = self._normalize_entry_key(see_ref)
                if target_key in self.entries:
                    resolved_see.append(see_ref)
                    cross_refs_resolved += 1

            entry.see_refs = resolved_see

            # Resolve see also references
            resolved_see_also = []
            for see_also_ref in entry.see_also_refs:
                target_key = self._normalize_entry_key(see_also_ref)
                if target_key in self.entries:
                    resolved_see_also.append(see_also_ref)
                    cross_refs_resolved += 1

            entry.see_also_refs = resolved_see_also

        self._stats["cross_refs_resolved"] = cross_refs_resolved

    def _generate_index_html(self) -> str:
        """Generate HTML for the index page."""

        # Group entries by first letter
        sections = self._group_entries_by_letter()

        html_parts = []

        # HTML header
        html_parts.append(
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" href="styles.css"/>
</head>
<body>
    <div class="index-page">
        <h1 class="index-title">{title}</h1>""".format(
                title=self.config.index_title
            )
        )

        # Generate index sections
        for section in sections:
            if section.entries:
                html_parts.append(
                    f'\n        <div class="index-section" id="index-{section.letter.lower()}">'
                )

                if self.config.show_letter_headers:
                    html_parts.append(
                        f'            <h2 class="index-letter-header">{section.letter}</h2>'
                    )

                html_parts.append('            <dl class="index-entries">')

                for entry in section.entries:
                    html_parts.append(self._render_entry_html(entry))

                html_parts.append("            </dl>")
                html_parts.append("        </div>")

        # HTML footer
        html_parts.append(
            """
    </div>
</body>
</html>"""
        )

        return "\n".join(html_parts)

    def _group_entries_by_letter(self) -> List[IndexSection]:
        """Group index entries by first letter."""

        sections = {}

        for entry in self.entries.values():
            first_char = entry.sort_key[0].upper() if entry.sort_key else "A"

            # Handle numbers and symbols
            if not first_char.isalpha():
                first_char = "#"

            if first_char not in sections:
                sections[first_char] = IndexSection(letter=first_char)

            sections[first_char].entries.append(entry)
            sections[first_char].entry_count += 1

        # Sort sections alphabetically
        sorted_sections = []
        for letter in sorted(sections.keys()):
            if letter == "#":
                continue  # Add symbols section at the end
            sorted_sections.append(sections[letter])

        # Add symbols section if it exists
        if "#" in sections:
            sorted_sections.append(sections["#"])

        return sorted_sections

    def _render_entry_html(self, entry: IndexEntry, level: int = 0) -> str:
        """Render a single index entry as HTML."""

        indent = "    " * level
        html_parts = []

        # Main entry
        html_parts.append(f'{indent}                <dt class="index-entry level-{level}">')

        if entry.emphasis:
            html_parts.append(f"<strong>{entry.text}</strong>")
        else:
            html_parts.append(entry.text)

        html_parts.append("</dt>")

        # Entry content (occurrences and cross-references)
        html_parts.append(f'{indent}                <dd class="index-content">')

        # Render occurrences
        if entry.occurrences:
            occurrence_links = []
            for i, occurrence in enumerate(entry.occurrences):
                link_class = "primary" if occurrence.is_primary else "occurrence"
                href = f"{occurrence.file_path}#{occurrence.anchor_id}"
                occurrence_links.append(f'<a href="{href}" class="index-{link_class}">{i + 1}</a>')

            html_parts.append(f'{indent}                    {", ".join(occurrence_links)}')

        # Render see references
        if entry.see_refs:
            see_links = [
                f'<a href="#index-{self._normalize_entry_key(ref)}" class="index-see">{ref}</a>'
                for ref in entry.see_refs
            ]
            html_parts.append(
                f'{indent}                    <span class="see-refs">See {", ".join(see_links)}</span>'
            )

        # Render see also references
        if entry.see_also_refs:
            see_also_links = [
                f'<a href="#index-{self._normalize_entry_key(ref)}" class="index-see-also">{ref}</a>'
                for ref in entry.see_also_refs
            ]
            html_parts.append(
                f'{indent}                    <span class="see-also-refs">See also {", ".join(see_also_links)}</span>'
            )

        html_parts.append(f"{indent}                </dd>")

        # Render sub-entries
        for child in entry.children:
            html_parts.append(self._render_entry_html(child, level + 1))

        return "\n".join(html_parts)

    def _create_occurrence_mapping(self) -> Dict[str, List[str]]:
        """Create mapping of index entries to their occurrence files."""

        mapping = {}

        for entry in self.entries.values():
            files = list(set(occ.file_path for occ in entry.occurrences))
            mapping[entry.text] = files

            # Include sub-entries
            for child in entry.children:
                child_files = list(set(occ.file_path for occ in child.occurrences))
                mapping[f"{entry.text}:{child.text}"] = child_files

        return mapping

    def get_statistics(self) -> Dict[str, int]:
        """Get indexing statistics."""
        return self._stats.copy()

    def get_index_summary(self) -> str:
        """Generate a summary of the index."""

        total_entries = len(self.entries)
        total_occurrences = sum(len(entry.occurrences) for entry in self.entries.values())
        total_sub_entries = sum(len(entry.children) for entry in self.entries.values())

        sections = self._group_entries_by_letter()
        section_count = len(sections)

        return f"""
Index Generation Summary
=======================

Entries: {total_entries}
Sub-entries: {total_sub_entries}
Total occurrences: {total_occurrences}
Alphabetical sections: {section_count}

XE fields processed: {self._stats['xe_fields_found']}
Cross-references resolved: {self._stats['cross_refs_resolved']}
"""


def create_default_index_config() -> IndexConfig:
    """Create default index configuration."""
    return IndexConfig()


def create_scholarly_index_config() -> IndexConfig:
    """Create index configuration optimized for scholarly documents."""
    return IndexConfig(
        process_see_refs=True,
        process_see_also_refs=True,
        show_occurrence_count=True,
        max_entries_per_letter=2000,
        case_sensitive=False,
    )
