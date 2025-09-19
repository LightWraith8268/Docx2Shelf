"""
Notes Flow Management for EPUB Generation

This module handles footnotes and endnotes with proper back-references,
allowing readers to navigate from notes back to their call sites. Supports
both inline notes and consolidated notes pages.

Features:
- Footnote and endnote back-reference generation
- Consolidated "Notes" page with per-chapter organization
- Proper EPUB 3 semantic markup for notes
- Cross-file note linking for split documents
- Customizable note numbering and formatting
- Reading flow optimization
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


class NoteType(Enum):
    """Types of notes supported."""
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    SIDENOTE = "sidenote"
    MARGINAL = "marginal"


class NoteStyle(Enum):
    """Note presentation styles."""
    INLINE = "inline"          # Notes appear at bottom of page/chapter
    CONSOLIDATED = "consolidated"  # All notes on separate pages
    POPUP = "popup"           # Notes appear in popups (EPUB 3)
    LINKED = "linked"         # Simple hyperlinks to notes


@dataclass
class NoteCall:
    """Represents a note call site in the text."""

    # Identity
    id: str
    note_id: str

    # Location
    file_path: str
    position: int
    chapter_title: str = ""

    # Content
    call_text: str = ""  # The superscript number or symbol
    surrounding_context: str = ""

    # Formatting
    call_format: str = "numeric"  # numeric, alpha, symbols
    is_custom_marker: bool = False


@dataclass
class Note:
    """Represents a footnote or endnote."""

    # Identity
    id: str
    type: NoteType
    number: int

    # Content
    content: str
    plain_text: str = ""

    # Location
    original_file: str = ""
    target_file: str = ""  # Where the note will appear in EPUB

    # Calls
    calls: List[NoteCall] = field(default_factory=list)

    # Formatting
    number_format: str = "1"  # 1, i, a, *, etc.
    is_continuation: bool = False  # Note continues from previous


@dataclass
class NotesConfig:
    """Configuration for notes processing."""

    # Style and placement
    note_style: NoteStyle = NoteStyle.INLINE
    consolidate_endnotes: bool = True
    footnotes_per_chapter: bool = True

    # Numbering
    restart_numbering_per_chapter: bool = True
    footnote_numbering: str = "numeric"  # numeric, roman, alpha, symbols
    endnote_numbering: str = "roman"

    # Back-references
    generate_back_refs: bool = True
    back_ref_symbol: str = "↩"
    back_ref_title: str = "Return to text"

    # Consolidated notes page
    notes_page_title: str = "Notes"
    group_by_chapter: bool = True
    include_chapter_headings: bool = True

    # Content processing
    preserve_note_formatting: bool = True
    max_note_preview_length: int = 100

    # File organization
    notes_file_name: str = "notes.xhtml"
    notes_css_class: str = "notes"


@dataclass
class ChapterNotes:
    """Notes organized by chapter."""

    chapter_title: str
    chapter_file: str
    footnotes: List[Note] = field(default_factory=list)
    endnotes: List[Note] = field(default_factory=list)


class NotesProcessor:
    """Processes notes and generates proper back-references."""

    def __init__(self, config: NotesConfig):
        self.config = config
        self.notes: Dict[str, Note] = {}
        self.calls: Dict[str, NoteCall] = {}
        self.chapters: List[ChapterNotes] = []
        self._stats = {
            "footnotes_found": 0,
            "endnotes_found": 0,
            "calls_found": 0,
            "back_refs_generated": 0
        }

    def process_content(self, html_chunks: List[str], chunk_files: List[str], chapter_titles: List[str] = None) -> Tuple[List[str], Optional[str]]:
        """
        Process HTML content to handle notes and generate back-references.

        Returns:
            Updated HTML chunks and optional consolidated notes page HTML
        """

        # Ensure we have chapter titles
        if not chapter_titles:
            chapter_titles = [f"Chapter {i+1}" for i in range(len(html_chunks))]

        # Step 1: Extract notes and calls from content
        self._extract_notes_and_calls(html_chunks, chunk_files, chapter_titles)

        # Step 2: Generate unique IDs and organize
        self._organize_notes_by_chapter(chunk_files, chapter_titles)

        # Step 3: Generate back-references
        self._generate_back_references()

        # Step 4: Update HTML with proper note markup
        updated_chunks = self._update_html_with_note_markup(html_chunks)

        # Step 5: Generate consolidated notes page if needed
        consolidated_notes = None
        if self.config.note_style == NoteStyle.CONSOLIDATED:
            consolidated_notes = self._generate_consolidated_notes_page()

        return updated_chunks, consolidated_notes

    def _extract_notes_and_calls(self, html_chunks: List[str], chunk_files: List[str], chapter_titles: List[str]) -> None:
        """Extract footnotes, endnotes, and their call sites."""

        # Patterns for note calls
        call_patterns = [
            r'<a[^>]*href\s*=\s*["\']#(footnote|endnote)[-_]?(\d+)["\'][^>]*class\s*=\s*["\'][^"\']*note-?call[^"\']*["\'][^>]*>(.*?)</a>',
            r'<sup[^>]*class\s*=\s*["\'][^"\']*note-?call[^"\']*["\'][^>]*><a[^>]*href\s*=\s*["\']#([^"\']+)["\'][^>]*>(.*?)</a></sup>',
            r'<span[^>]*class\s*=\s*["\'][^"\']*footnote-?ref[^"\']*["\'][^>]*><a[^>]*href\s*=\s*["\']#([^"\']+)["\'][^>]*>(.*?)</a></span>'
        ]

        # Patterns for notes themselves
        note_patterns = [
            r'<div[^>]*class\s*=\s*["\'][^"\']*footnote[^"\']*["\'][^>]*id\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</div>',
            r'<li[^>]*id\s*=\s*["\'](footnote|endnote)[-_]?(\d+)["\'][^>]*>(.*?)</li>',
            r'<aside[^>]*epub:type\s*=\s*["\']footnote["\'][^>]*id\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</aside>'
        ]

        note_id_counter = 1
        call_id_counter = 1

        for chunk_idx, (chunk, filename, chapter_title) in enumerate(zip(html_chunks, chunk_files, chapter_titles)):
            # Extract note calls
            for pattern in call_patterns:
                for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                    if len(match.groups()) >= 3:
                        note_ref = match.group(1)
                        if match.group(2).isdigit():
                            note_ref += f"_{match.group(2)}"
                        call_text = match.group(3)
                    else:
                        note_ref = match.group(1)
                        call_text = match.group(2)

                    call_text = re.sub(r'<[^>]+>', '', call_text).strip()

                    # Extract surrounding context
                    start_pos = max(0, match.start() - 100)
                    end_pos = min(len(chunk), match.end() + 100)
                    context = chunk[start_pos:end_pos]
                    context = re.sub(r'<[^>]+>', ' ', context)
                    context = ' '.join(context.split())

                    call = NoteCall(
                        id=f"call_{call_id_counter}",
                        note_id=note_ref,
                        file_path=filename,
                        position=match.start(),
                        chapter_title=chapter_title,
                        call_text=call_text,
                        surrounding_context=context
                    )

                    self.calls[call.id] = call
                    call_id_counter += 1

            # Extract notes
            for pattern in note_patterns:
                for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                    if 'footnote' in pattern or 'footnote' in match.group(0).lower():
                        note_type = NoteType.FOOTNOTE
                    else:
                        note_type = NoteType.ENDNOTE

                    if len(match.groups()) >= 3:
                        note_id = f"{match.group(1)}_{match.group(2)}"
                        content = match.group(3)
                    else:
                        note_id = match.group(1)
                        content = match.group(2) if len(match.groups()) >= 2 else match.group(1)

                    # Clean content
                    plain_text = re.sub(r'<[^>]+>', ' ', content)
                    plain_text = ' '.join(plain_text.split())

                    note = Note(
                        id=note_id,
                        type=note_type,
                        number=note_id_counter,
                        content=content,
                        plain_text=plain_text,
                        original_file=filename
                    )

                    self.notes[note_id] = note
                    note_id_counter += 1

        # Link calls to notes
        for call in self.calls.values():
            if call.note_id in self.notes:
                self.notes[call.note_id].calls.append(call)

        self._stats["footnotes_found"] = len([n for n in self.notes.values() if n.type == NoteType.FOOTNOTE])
        self._stats["endnotes_found"] = len([n for n in self.notes.values() if n.type == NoteType.ENDNOTE])
        self._stats["calls_found"] = len(self.calls)

    def _organize_notes_by_chapter(self, chunk_files: List[str], chapter_titles: List[str]) -> None:
        """Organize notes by chapter."""

        # Create chapter structures
        for filename, title in zip(chunk_files, chapter_titles):
            chapter_notes = ChapterNotes(
                chapter_title=title,
                chapter_file=filename
            )

            # Assign notes to chapters based on their calls
            for note in self.notes.values():
                if any(call.file_path == filename for call in note.calls):
                    if note.type == NoteType.FOOTNOTE:
                        chapter_notes.footnotes.append(note)
                    elif note.type == NoteType.ENDNOTE:
                        chapter_notes.endnotes.append(note)

            # Sort notes by number
            chapter_notes.footnotes.sort(key=lambda x: x.number)
            chapter_notes.endnotes.sort(key=lambda x: x.number)

            self.chapters.append(chapter_notes)

    def _generate_back_references(self) -> None:
        """Generate back-reference links from notes to their call sites."""

        if not self.config.generate_back_refs:
            return

        back_refs_generated = 0

        for note in self.notes.values():
            back_ref_links = []

            for call in note.calls:
                # Generate back-reference link
                if call.file_path == note.original_file:
                    # Same file reference
                    href = f"#{call.id}"
                else:
                    # Cross-file reference
                    href = f"{call.file_path}#{call.id}"

                back_ref_html = f'<a href="{href}" class="note-back-ref" title="{self.config.back_ref_title}">{self.config.back_ref_symbol}</a>'
                back_ref_links.append(back_ref_html)

            # Add back-references to note content
            if back_ref_links:
                back_ref_section = f' <span class="note-back-refs">{" ".join(back_ref_links)}</span>'
                note.content = note.content.rstrip() + back_ref_section
                back_refs_generated += 1

        self._stats["back_refs_generated"] = back_refs_generated

    def _update_html_with_note_markup(self, html_chunks: List[str]) -> List[str]:
        """Update HTML with proper note markup and IDs."""

        updated_chunks = []

        for chunk_idx, chunk in enumerate(html_chunks):
            updated_chunk = chunk

            # Add IDs to note calls if missing
            updated_chunk = self._add_call_ids(updated_chunk)

            # Update note markup with proper semantic elements
            updated_chunk = self._enhance_note_markup(updated_chunk)

            # Handle note placement based on style
            if self.config.note_style == NoteStyle.INLINE:
                updated_chunk = self._position_inline_notes(updated_chunk)
            elif self.config.note_style == NoteStyle.CONSOLIDATED:
                updated_chunk = self._remove_inline_notes(updated_chunk)

            updated_chunks.append(updated_chunk)

        return updated_chunks

    def _add_call_ids(self, chunk: str) -> str:
        """Add IDs to note calls for back-referencing."""

        for call in self.calls.values():
            # Find the call in this chunk and add ID if missing
            pattern = rf'<(a|sup|span)[^>]*class\s*=\s*["\'][^"\']*note-?call[^"\']*["\'][^>]*>([^<]*{re.escape(call.call_text)}[^<]*)</\1>'

            def add_call_id(match):
                tag = match.group(1)
                content = match.group(2)
                attrs = match.group(0)[len(f'<{tag}'):match.group(0).find('>')]

                if 'id=' not in attrs:
                    attrs += f' id="{call.id}"'

                return f'<{tag}{attrs}>{content}</{tag}>'

            chunk = re.sub(pattern, add_call_id, chunk, flags=re.IGNORECASE)

        return chunk

    def _enhance_note_markup(self, chunk: str) -> str:
        """Enhance note markup with proper semantic elements."""

        # Convert footnotes to proper aside elements
        footnote_pattern = r'<div([^>]*class\s*=\s*["\'][^"\']*footnote[^"\']*["\'][^>]*?)>(.*?)</div>'

        def enhance_footnote(match):
            attrs = match.group(1)
            content = match.group(2)

            # Add EPUB type if not present
            if 'epub:type=' not in attrs:
                attrs += ' epub:type="footnote"'

            # Add role if not present
            if 'role=' not in attrs:
                attrs += ' role="doc-footnote"'

            return f'<aside{attrs}>{content}</aside>'

        chunk = re.sub(footnote_pattern, enhance_footnote, chunk, flags=re.IGNORECASE | re.DOTALL)

        return chunk

    def _position_inline_notes(self, chunk: str) -> str:
        """Position notes inline at appropriate locations."""

        if self.config.footnotes_per_chapter:
            # Move footnotes to end of chapter
            footnotes = []

            # Extract footnotes
            footnote_pattern = r'<aside[^>]*epub:type\s*=\s*["\']footnote["\'][^>]*>(.*?)</aside>'

            def extract_footnote(match):
                footnotes.append(match.group(0))
                return ''  # Remove from original position

            chunk = re.sub(footnote_pattern, extract_footnote, chunk, flags=re.IGNORECASE | re.DOTALL)

            # Add footnotes section at end if any found
            if footnotes:
                footnotes_section = '''
        <section class="footnotes" epub:type="footnotes">
            <h2>Notes</h2>
            <div class="footnotes-list">
                ''' + '\n                '.join(footnotes) + '''
            </div>
        </section>'''

                # Insert before closing body tag
                chunk = chunk.replace('</body>', footnotes_section + '\n</body>')

        return chunk

    def _remove_inline_notes(self, chunk: str) -> str:
        """Remove inline notes when using consolidated style."""

        # Remove footnote and endnote elements
        note_patterns = [
            r'<aside[^>]*epub:type\s*=\s*["\']footnote["\'][^>]*>.*?</aside>',
            r'<div[^>]*class\s*=\s*["\'][^"\']*footnote[^"\']*["\'][^>]*>.*?</div>',
            r'<section[^>]*class\s*=\s*["\'][^"\']*footnotes[^"\']*["\'][^>]*>.*?</section>'
        ]

        for pattern in note_patterns:
            chunk = re.sub(pattern, '', chunk, flags=re.IGNORECASE | re.DOTALL)

        return chunk

    def _generate_consolidated_notes_page(self) -> str:
        """Generate consolidated notes page HTML."""

        html_parts = []

        # HTML header
        html_parts.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{self.config.notes_page_title}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" href="styles.css"/>
</head>
<body>
    <div class="{self.config.notes_css_class}">
        <h1 class="notes-title">{self.config.notes_page_title}</h1>''')

        # Generate notes by chapter
        for chapter in self.chapters:
            if chapter.footnotes or chapter.endnotes:
                html_parts.append(f'''
        <section class="chapter-notes" id="notes-{self._slugify(chapter.chapter_title)}">''')

                if self.config.include_chapter_headings:
                    html_parts.append(f'            <h2 class="chapter-notes-title">{chapter.chapter_title}</h2>')

                # Footnotes
                if chapter.footnotes:
                    html_parts.append('            <div class="footnotes-section">')
                    html_parts.append('                <h3>Footnotes</h3>')
                    html_parts.append('                <ol class="footnotes-list">')

                    for note in chapter.footnotes:
                        html_parts.append(f'                    <li id="{note.id}" class="footnote">')
                        html_parts.append(f'                        {note.content}')
                        html_parts.append('                    </li>')

                    html_parts.append('                </ol>')
                    html_parts.append('            </div>')

                # Endnotes
                if chapter.endnotes:
                    html_parts.append('            <div class="endnotes-section">')
                    html_parts.append('                <h3>Endnotes</h3>')
                    html_parts.append('                <ol class="endnotes-list">')

                    for note in chapter.endnotes:
                        html_parts.append(f'                    <li id="{note.id}" class="endnote">')
                        html_parts.append(f'                        {note.content}')
                        html_parts.append('                    </li>')

                    html_parts.append('                </ol>')
                    html_parts.append('            </div>')

                html_parts.append('        </section>')

        # HTML footer
        html_parts.append('''
    </div>
</body>
</html>''')

        return '\n'.join(html_parts)

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        slug = re.sub(r'[^\w\s-]', '', text)
        slug = re.sub(r'\s+', '-', slug)
        return slug.lower()

    def get_statistics(self) -> Dict[str, int]:
        """Get notes processing statistics."""
        return self._stats.copy()

    def get_notes_summary(self) -> str:
        """Generate a summary of notes processing."""

        total_notes = self._stats["footnotes_found"] + self._stats["endnotes_found"]

        return f"""
Notes Processing Summary
=======================

Total notes: {total_notes}
  • Footnotes: {self._stats["footnotes_found"]}
  • Endnotes: {self._stats["endnotes_found"]}

Note calls found: {self._stats["calls_found"]}
Back-references generated: {self._stats["back_refs_generated"]}

Chapters with notes: {len([c for c in self.chapters if c.footnotes or c.endnotes])}
Note style: {self.config.note_style.value}
"""


def create_default_notes_config() -> NotesConfig:
    """Create default notes configuration."""
    return NotesConfig()


def create_scholarly_notes_config() -> NotesConfig:
    """Create notes configuration optimized for scholarly documents."""
    return NotesConfig(
        note_style=NoteStyle.CONSOLIDATED,
        generate_back_refs=True,
        group_by_chapter=True,
        include_chapter_headings=True,
        preserve_note_formatting=True
    )