"""
Cross-references and Anchor Management for EPUB Generation

This module handles Word cross-references and generates stable intra-EPUB links
that work across split files. It ensures all headings, figures, tables, and
other referenceable elements have permanent, collision-safe IDs.

Features:
- Parse Word cross-reference fields from DOCX
- Generate stable, collision-safe anchor IDs
- Map cross-references to target elements across EPUB files
- Maintain link integrity after content splitting
- Support for heading, figure, table, and bookmark references
- Automatic back-link generation
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from xml.etree import ElementTree as ET


class CrossRefType(Enum):
    """Types of cross-references supported."""
    HEADING = "heading"
    FIGURE = "figure"
    TABLE = "table"
    BOOKMARK = "bookmark"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    EQUATION = "equation"
    PAGE = "page"
    SECTION = "section"


@dataclass
class AnchorTarget:
    """Represents a target that can be referenced."""

    # Identity
    id: str  # Collision-safe ID
    original_id: Optional[str] = None  # Original Word ID if available

    # Content
    title: str = ""
    text_content: str = ""

    # Type and location
    ref_type: CrossRefType = CrossRefType.HEADING
    chapter_file: str = ""  # Which EPUB file contains this target
    position: int = 0  # Position within the document

    # Hierarchy
    level: int = 1  # For headings: h1=1, h2=2, etc.
    parent_id: Optional[str] = None

    # Numbering
    number: Optional[str] = None  # Figure 1, Table 2, etc.

    # Metadata
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class CrossReference:
    """Represents a cross-reference from source to target."""

    # Source information
    source_id: str
    source_file: str
    source_position: int

    # Target information
    target_id: str
    target_type: CrossRefType

    # Reference properties
    ref_text: str = ""  # Text displayed for the reference
    ref_format: str = "default"  # How to format the reference

    # Link properties
    href: str = ""  # Final EPUB-relative href
    is_broken: bool = False

    # Original Word field info
    word_field_code: str = ""
    word_field_result: str = ""


@dataclass
class CrossRefConfig:
    """Configuration for cross-reference processing."""

    # ID generation
    id_prefix: str = "ref"
    max_id_length: int = 50
    collision_suffix_length: int = 6

    # Cross-reference text generation
    include_numbers: bool = True
    include_titles: bool = True
    max_title_length: int = 50

    # Link formatting
    generate_back_refs: bool = True
    back_ref_text: str = "↩"

    # Scope and filtering
    process_broken_refs: bool = True
    skip_external_refs: bool = False


class CrossRefProcessor:
    """Processes cross-references and generates stable anchors."""

    def __init__(self, config: CrossRefConfig):
        self.config = config
        self.targets: Dict[str, AnchorTarget] = {}
        self.references: List[CrossReference] = []
        self.id_registry: Set[str] = set()
        self._stats = {
            "targets_found": 0,
            "references_found": 0,
            "broken_references": 0,
            "id_collisions_resolved": 0
        }

    def process_content(self, html_chunks: List[str], chunk_files: List[str]) -> Tuple[List[str], Dict[str, str]]:
        """
        Process HTML content to extract targets and resolve cross-references.

        Returns:
            Updated HTML chunks and mapping of target IDs to files
        """

        # Step 1: Extract all potential targets
        self._extract_targets(html_chunks, chunk_files)

        # Step 2: Extract cross-references
        self._extract_cross_references(html_chunks, chunk_files)

        # Step 3: Resolve references to targets
        self._resolve_references()

        # Step 4: Update HTML with stable IDs and resolved links
        updated_chunks = self._update_html_with_anchors_and_links(html_chunks)

        # Step 5: Generate target mapping for external use
        target_mapping = {
            target.id: target.chapter_file
            for target in self.targets.values()
        }

        return updated_chunks, target_mapping

    def _extract_targets(self, html_chunks: List[str], chunk_files: List[str]) -> None:
        """Extract all elements that can be referenced."""

        for chunk_idx, (chunk, filename) in enumerate(zip(html_chunks, chunk_files)):
            # Extract headings
            self._extract_heading_targets(chunk, filename, chunk_idx)

            # Extract figures
            self._extract_figure_targets(chunk, filename, chunk_idx)

            # Extract tables
            self._extract_table_targets(chunk, filename, chunk_idx)

            # Extract bookmarks (if any)
            self._extract_bookmark_targets(chunk, filename, chunk_idx)

        self._stats["targets_found"] = len(self.targets)

    def _extract_heading_targets(self, chunk: str, filename: str, chunk_idx: int) -> None:
        """Extract heading elements as targets."""

        heading_pattern = r'<(h[1-6])([^>]*?)>(.*?)</\1>'

        for match in re.finditer(heading_pattern, chunk, re.IGNORECASE | re.DOTALL):
            tag = match.group(1).lower()
            attrs = match.group(2)
            content = match.group(3)

            # Clean content for title
            clean_title = re.sub(r'<[^>]+>', '', content).strip()

            if not clean_title:
                continue

            # Extract existing ID if present
            id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attrs)
            original_id = id_match.group(1) if id_match else None

            # Generate stable ID
            stable_id = self._generate_stable_id(clean_title, CrossRefType.HEADING, original_id)

            # Create target
            target = AnchorTarget(
                id=stable_id,
                original_id=original_id,
                title=clean_title,
                text_content=clean_title,
                ref_type=CrossRefType.HEADING,
                chapter_file=filename,
                position=match.start(),
                level=int(tag[1])
            )

            self.targets[stable_id] = target

    def _extract_figure_targets(self, chunk: str, filename: str, chunk_idx: int) -> None:
        """Extract figure elements as targets."""

        # Look for images with captions or figure elements
        patterns = [
            r'<figure[^>]*?>(.*?)</figure>',
            r'<img[^>]*?alt\s*=\s*["\']([^"\']+)["\'][^>]*?>',
            r'<div[^>]*?class\s*=\s*["\'][^"\']*figure[^"\']*["\'][^>]*?>(.*?)</div>'
        ]

        figure_number = 1

        for pattern in patterns:
            for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                content = match.group(1) if match.lastindex >= 1 else ""

                # Extract caption or alt text
                caption = self._extract_caption(content) or f"Figure {figure_number}"

                # Generate stable ID
                stable_id = self._generate_stable_id(caption, CrossRefType.FIGURE)

                target = AnchorTarget(
                    id=stable_id,
                    title=caption,
                    text_content=caption,
                    ref_type=CrossRefType.FIGURE,
                    chapter_file=filename,
                    position=match.start(),
                    number=str(figure_number)
                )

                self.targets[stable_id] = target
                figure_number += 1

    def _extract_table_targets(self, chunk: str, filename: str, chunk_idx: int) -> None:
        """Extract table elements as targets."""

        table_pattern = r'<table[^>]*?>(.*?)</table>'
        table_number = 1

        for match in re.finditer(table_pattern, chunk, re.IGNORECASE | re.DOTALL):
            table_content = match.group(1)

            # Look for caption
            caption_match = re.search(r'<caption[^>]*?>(.*?)</caption>', table_content, re.IGNORECASE | re.DOTALL)
            caption = caption_match.group(1) if caption_match else f"Table {table_number}"
            caption = re.sub(r'<[^>]+>', '', caption).strip()

            # Generate stable ID
            stable_id = self._generate_stable_id(caption, CrossRefType.TABLE)

            target = AnchorTarget(
                id=stable_id,
                title=caption,
                text_content=caption,
                ref_type=CrossRefType.TABLE,
                chapter_file=filename,
                position=match.start(),
                number=str(table_number)
            )

            self.targets[stable_id] = target
            table_number += 1

    def _extract_bookmark_targets(self, chunk: str, filename: str, chunk_idx: int) -> None:
        """Extract bookmark elements as targets."""

        # Look for Word bookmarks or anchor tags
        bookmark_patterns = [
            r'<a[^>]*?name\s*=\s*["\']([^"\']+)["\'][^>]*?>(.*?)</a>',
            r'<span[^>]*?id\s*=\s*["\']([^"\']+)["\'][^>]*?data-bookmark[^>]*?>(.*?)</span>'
        ]

        for pattern in bookmark_patterns:
            for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                bookmark_name = match.group(1)
                content = match.group(2)

                # Clean content
                clean_content = re.sub(r'<[^>]+>', '', content).strip()
                title = clean_content or bookmark_name

                # Generate stable ID
                stable_id = self._generate_stable_id(title, CrossRefType.BOOKMARK, bookmark_name)

                target = AnchorTarget(
                    id=stable_id,
                    original_id=bookmark_name,
                    title=title,
                    text_content=clean_content,
                    ref_type=CrossRefType.BOOKMARK,
                    chapter_file=filename,
                    position=match.start()
                )

                self.targets[stable_id] = target

    def _extract_cross_references(self, html_chunks: List[str], chunk_files: List[str]) -> None:
        """Extract cross-reference fields from HTML."""

        # Look for Word field codes or hyperlinks that might be cross-references
        ref_patterns = [
            r'<a[^>]*?href\s*=\s*["\']#([^"\']+)["\'][^>]*?>(.*?)</a>',
            r'<span[^>]*?class\s*=\s*["\'][^"\']*cross-?ref[^"\']*["\'][^>]*?>(.*?)</span>',
            r'<!--\s*REF\s+([^>]+)\s*-->(.*?)<!--\s*/REF\s*-->'
        ]

        ref_number = 1

        for chunk_idx, (chunk, filename) in enumerate(zip(html_chunks, chunk_files)):
            for pattern in ref_patterns:
                for match in re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL):
                    if pattern.startswith(r'<a'):  # Hyperlink pattern
                        target_anchor = match.group(1)
                        ref_text = match.group(2)
                    else:  # Other patterns
                        target_anchor = match.group(1) if match.lastindex >= 1 else ""
                        ref_text = match.group(2) if match.lastindex >= 2 else match.group(1)

                    # Clean reference text
                    clean_ref_text = re.sub(r'<[^>]+>', '', ref_text).strip()

                    # Create cross-reference
                    ref = CrossReference(
                        source_id=f"crossref_{ref_number}",
                        source_file=filename,
                        source_position=match.start(),
                        target_id=target_anchor,
                        target_type=self._guess_target_type(clean_ref_text),
                        ref_text=clean_ref_text,
                        word_field_result=clean_ref_text
                    )

                    self.references.append(ref)
                    ref_number += 1

        self._stats["references_found"] = len(self.references)

    def _resolve_references(self) -> None:
        """Resolve cross-references to their targets."""

        broken_refs = 0

        for ref in self.references:
            # Try to find target by various methods
            target = self._find_target_for_reference(ref)

            if target:
                # Generate href
                if target.chapter_file == ref.source_file:
                    # Same file reference
                    ref.href = f"#{target.id}"
                else:
                    # Cross-file reference
                    ref.href = f"{target.chapter_file}#{target.id}"

                ref.is_broken = False
            else:
                ref.is_broken = True
                broken_refs += 1

        self._stats["broken_references"] = broken_refs

    def _find_target_for_reference(self, ref: CrossReference) -> Optional[AnchorTarget]:
        """Find the target for a cross-reference."""

        # Direct ID match
        if ref.target_id in self.targets:
            return self.targets[ref.target_id]

        # Try to match by original ID
        for target in self.targets.values():
            if target.original_id == ref.target_id:
                return target

        # Try to match by content
        ref_text_lower = ref.ref_text.lower()
        for target in self.targets.values():
            if target.title.lower() in ref_text_lower or ref_text_lower in target.title.lower():
                return target

        return None

    def _update_html_with_anchors_and_links(self, html_chunks: List[str]) -> List[str]:
        """Update HTML with stable anchor IDs and resolved cross-reference links."""

        updated_chunks = []

        for chunk_idx, chunk in enumerate(html_chunks):
            updated_chunk = chunk

            # Add IDs to target elements
            updated_chunk = self._add_target_ids(updated_chunk)

            # Update cross-reference links
            updated_chunk = self._update_reference_links(updated_chunk)

            updated_chunks.append(updated_chunk)

        return updated_chunks

    def _add_target_ids(self, chunk: str) -> str:
        """Add stable IDs to target elements."""

        # Find targets in this chunk and add IDs
        for target in self.targets.values():
            if target.ref_type == CrossRefType.HEADING:
                # Update heading tags
                pattern = rf'<(h{target.level})([^>]*?)>({re.escape(target.title)})</\1>'

                def add_id(match):
                    tag = match.group(1)
                    attrs = match.group(2)
                    content = match.group(3)

                    # Add or update ID
                    if 'id=' in attrs:
                        attrs = re.sub(r'id\s*=\s*["\'][^"\']*["\']', f'id="{target.id}"', attrs)
                    else:
                        attrs += f' id="{target.id}"'

                    return f'<{tag}{attrs}>{content}</{tag}>'

                chunk = re.sub(pattern, add_id, chunk, flags=re.IGNORECASE)

        return chunk

    def _update_reference_links(self, chunk: str) -> str:
        """Update cross-reference links with resolved hrefs."""

        for ref in self.references:
            if not ref.is_broken and ref.href:
                # Find and update the reference link
                pattern = rf'<a[^>]*?href\s*=\s*["\']#?{re.escape(ref.target_id)}["\'][^>]*?>(.*?)</a>'
                replacement = f'<a href="{ref.href}" class="cross-ref">\\1</a>'
                chunk = re.sub(pattern, replacement, chunk, flags=re.IGNORECASE)

        return chunk

    def _generate_stable_id(self, content: str, ref_type: CrossRefType, original_id: Optional[str] = None) -> str:
        """Generate a stable, collision-safe ID."""

        # Start with original ID if available and safe
        if original_id and self._is_safe_id(original_id):
            base_id = original_id
        else:
            # Generate from content
            # Clean content for ID
            clean_content = re.sub(r'[^\w\s-]', '', content)
            clean_content = re.sub(r'\s+', '-', clean_content).lower()
            clean_content = clean_content[:self.config.max_id_length - len(self.config.id_prefix) - 10]

            base_id = f"{self.config.id_prefix}-{ref_type.value}-{clean_content}"

        # Ensure uniqueness
        final_id = base_id
        counter = 1

        while final_id in self.id_registry:
            # Generate collision suffix
            suffix = hashlib.md5(f"{base_id}-{counter}".encode()).hexdigest()[:self.config.collision_suffix_length]
            final_id = f"{base_id}-{suffix}"
            counter += 1

            if counter > 1000:  # Prevent infinite loops
                break

        if final_id != base_id:
            self._stats["id_collisions_resolved"] += 1

        self.id_registry.add(final_id)
        return final_id

    def _is_safe_id(self, id_str: str) -> bool:
        """Check if an ID is safe to use."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', id_str))

    def _extract_caption(self, content: str) -> Optional[str]:
        """Extract caption text from figure content."""
        caption_patterns = [
            r'<figcaption[^>]*?>(.*?)</figcaption>',
            r'<p[^>]*?class\s*=\s*["\'][^"\']*caption[^"\']*["\'][^>]*?>(.*?)</p>',
            r'<div[^>]*?class\s*=\s*["\'][^"\']*caption[^"\']*["\'][^>]*?>(.*?)</div>'
        ]

        for pattern in caption_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                caption = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if caption:
                    return caption

        return None

    def _guess_target_type(self, ref_text: str) -> CrossRefType:
        """Guess the target type from reference text."""
        ref_lower = ref_text.lower()

        if 'figure' in ref_lower or 'fig' in ref_lower:
            return CrossRefType.FIGURE
        elif 'table' in ref_lower:
            return CrossRefType.TABLE
        elif 'chapter' in ref_lower or 'section' in ref_lower:
            return CrossRefType.HEADING
        elif 'equation' in ref_lower or 'eq' in ref_lower:
            return CrossRefType.EQUATION
        else:
            return CrossRefType.HEADING  # Default

    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics."""
        return self._stats.copy()

    def get_targets_by_type(self, ref_type: CrossRefType) -> List[AnchorTarget]:
        """Get all targets of a specific type."""
        return [target for target in self.targets.values() if target.ref_type == ref_type]

    def generate_anchor_manifest(self) -> Dict[str, Dict[str, str]]:
        """Generate a manifest of all anchors for external use."""
        manifest = {}

        for target in self.targets.values():
            manifest[target.id] = {
                "title": target.title,
                "type": target.ref_type.value,
                "file": target.chapter_file,
                "number": target.number or "",
                "level": str(target.level)
            }

        return manifest


def create_default_crossref_config() -> CrossRefConfig:
    """Create default cross-reference configuration."""
    return CrossRefConfig()


def create_scholarly_crossref_config() -> CrossRefConfig:
    """Create cross-reference configuration optimized for scholarly documents."""
    return CrossRefConfig(
        include_numbers=True,
        include_titles=True,
        generate_back_refs=True,
        process_broken_refs=True,
        max_title_length=100
    )