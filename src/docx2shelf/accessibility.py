from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def check_image_alt_text(html_chunks: List[str]) -> List[Tuple[str, str]]:
    """Check for images missing alt text.

    Returns list of (chunk_index, img_tag) for images without alt text.
    """
    missing_alt = []

    for i, chunk in enumerate(html_chunks):
        # Find all img tags
        img_pattern = r'<img[^>]*>'
        img_tags = re.findall(img_pattern, chunk, re.IGNORECASE)

        for img_tag in img_tags:
            # Check if alt attribute exists and is not empty
            alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            if not alt_match or not alt_match.group(1).strip():
                missing_alt.append((str(i), img_tag))

    return missing_alt


def prompt_for_alt_text(missing_alt: List[Tuple[str, str]], quiet: bool = False) -> Dict[str, str]:
    """Prompt user for alt text for missing images.

    Returns dictionary mapping img_tag -> alt_text.
    """
    if quiet or not missing_alt:
        return {}

    alt_text_map = {}

    print("\n📖 EPUB Accessibility Check", file=sys.stderr)
    print("The following images are missing alt text:", file=sys.stderr)

    for i, (chunk_idx, img_tag) in enumerate(missing_alt, 1):
        print(f"\n{i}. Chunk {chunk_idx}: {img_tag}", file=sys.stderr)

        # Extract src if available for context
        src_match = re.search(r'src\s*=\s*["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
        if src_match:
            print(f"   Source: {src_match.group(1)}", file=sys.stderr)

        # Prompt for alt text
        while True:
            try:
                alt_text = input(f"   Enter alt text (or 'skip' to leave empty): ").strip()
                if alt_text.lower() == 'skip':
                    alt_text = ""
                    break
                elif alt_text:
                    break
                else:
                    print("   Please enter alt text or 'skip'", file=sys.stderr)
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping remaining alt text prompts...", file=sys.stderr)
                return alt_text_map

        if alt_text:
            alt_text_map[img_tag] = alt_text

    return alt_text_map


def add_alt_text_to_html(html_chunks: List[str], alt_text_map: Dict[str, str]) -> List[str]:
    """Add alt text to HTML chunks based on mapping."""
    if not alt_text_map:
        return html_chunks

    updated_chunks = []

    for chunk in html_chunks:
        updated_chunk = chunk

        for img_tag, alt_text in alt_text_map.items():
            if img_tag in updated_chunk:
                # Add alt attribute to the img tag
                if 'alt=' in img_tag.lower():
                    # Replace existing empty alt
                    new_img_tag = re.sub(
                        r'alt\s*=\s*["\'][^"\']*["\']',
                        f'alt="{alt_text}"',
                        img_tag,
                        flags=re.IGNORECASE
                    )
                else:
                    # Add alt attribute before the closing >
                    new_img_tag = img_tag.replace('>', f' alt="{alt_text}">')

                updated_chunk = updated_chunk.replace(img_tag, new_img_tag)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def generate_accessibility_metadata() -> Dict[str, str]:
    """Generate EPUB accessibility metadata."""
    return {
        'schema:accessMode': 'textual,visual',
        'schema:accessModeSufficient': 'textual',
        'schema:accessibilityFeature': 'structuralNavigation,readingOrder,alternativeText',
        'schema:accessibilityHazard': 'none',
        'schema:accessibilitySummary': 'This publication conforms to EPUB Accessibility standards with structured navigation, reading order, and alternative text for images.'
    }


def add_aria_landmarks(html_chunks: List[str], metadata) -> List[str]:
    """Add ARIA landmarks to HTML content."""
    if not html_chunks:
        return html_chunks

    updated_chunks = []

    for i, chunk in enumerate(html_chunks):
        updated_chunk = chunk

        # Add main landmark to first content chapter
        if i == 0 and '<body' in chunk:
            # Find body tag and add role="main"
            body_pattern = r'<body([^>]*)>'
            def add_main_role(match):
                attrs = match.group(1)
                if 'role=' not in attrs.lower():
                    attrs += ' role="main"'
                return f'<body{attrs}>'

            updated_chunk = re.sub(body_pattern, add_main_role, updated_chunk, flags=re.IGNORECASE)

        # Add navigation landmarks to heading elements
        heading_pattern = r'<(h[1-6])([^>]*)>(.*?)</\1>'
        def add_heading_nav(match):
            tag, attrs, content = match.groups()
            # Add aria-level if not present
            if 'aria-level=' not in attrs.lower():
                level = tag[1]  # Extract number from h1, h2, etc.
                attrs += f' aria-level="{level}"'
            return f'<{tag}{attrs}>{content}</{tag}>'

        updated_chunk = re.sub(heading_pattern, add_heading_nav, updated_chunk, flags=re.IGNORECASE | re.DOTALL)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def detect_document_language(html_chunks: List[str], metadata) -> str:
    """Detect document language from content or metadata."""
    # Try to get language from metadata first
    if hasattr(metadata, 'language') and metadata.language:
        return metadata.language

    # Look for lang attributes in HTML
    for chunk in html_chunks:
        lang_match = re.search(r'<html[^>]*lang\s*=\s*["\']([^"\']+)["\']', chunk, re.IGNORECASE)
        if lang_match:
            return lang_match.group(1)

    # Default to English
    return 'en'


def add_language_attributes(html_chunks: List[str], language: str) -> List[str]:
    """Add language attributes to HTML elements."""
    if not language:
        return html_chunks

    updated_chunks = []

    for chunk in html_chunks:
        updated_chunk = chunk

        # Add lang attribute to html element if not present
        if '<html' in chunk and 'lang=' not in chunk.lower():
            html_pattern = r'<html([^>]*)>'
            def add_lang(match):
                attrs = match.group(1)
                attrs += f' lang="{language}"'
                return f'<html{attrs}>'

            updated_chunk = re.sub(html_pattern, add_lang, updated_chunk, flags=re.IGNORECASE)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def validate_reading_order(html_chunks: List[str]) -> List[str]:
    """Validate and report on reading order issues."""
    issues = []

    for i, chunk in enumerate(html_chunks):
        # Check for heading hierarchy skips
        headings = re.findall(r'<h([1-6])', chunk, re.IGNORECASE)

        if headings:
            heading_levels = [int(h) for h in headings]

            for j in range(1, len(heading_levels)):
                current = heading_levels[j]
                previous = heading_levels[j-1]

                # Check if we skip heading levels (e.g., h1 -> h3)
                if current > previous + 1:
                    issues.append(f"Chunk {i}: Heading hierarchy skip from h{previous} to h{current}")

    return issues


def process_accessibility_features(
    html_chunks: List[str],
    metadata,
    interactive: bool = True,
    quiet: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    """Process all accessibility features for EPUB content.

    Returns updated HTML chunks and accessibility metadata.
    """
    if not quiet:
        print("🔍 Processing EPUB Accessibility features...", file=sys.stderr)

    # Step 1: Check for missing alt text
    missing_alt = check_image_alt_text(html_chunks)
    alt_text_map = {}

    if missing_alt:
        if interactive and not quiet:
            alt_text_map = prompt_for_alt_text(missing_alt, quiet)
        elif not quiet:
            print(f"⚠️  Found {len(missing_alt)} images without alt text", file=sys.stderr)
            print("Use interactive mode to add alt text for better accessibility", file=sys.stderr)

    # Step 2: Add alt text to HTML
    if alt_text_map:
        html_chunks = add_alt_text_to_html(html_chunks, alt_text_map)
        if not quiet:
            print(f"✅ Added alt text to {len(alt_text_map)} images", file=sys.stderr)

    # Step 3: Detect language
    language = detect_document_language(html_chunks, metadata)
    if not quiet:
        print(f"🌐 Document language: {language}", file=sys.stderr)

    # Step 4: Add language attributes
    html_chunks = add_language_attributes(html_chunks, language)

    # Step 5: Add ARIA landmarks
    html_chunks = add_aria_landmarks(html_chunks, metadata)
    if not quiet:
        print("🏷️  Added ARIA landmarks", file=sys.stderr)

    # Step 6: Validate reading order
    reading_issues = validate_reading_order(html_chunks)
    if reading_issues and not quiet:
        print("⚠️  Reading order issues found:", file=sys.stderr)
        for issue in reading_issues:
            print(f"   {issue}", file=sys.stderr)

    # Step 7: Generate accessibility metadata
    accessibility_meta = generate_accessibility_metadata()
    if not quiet:
        print("📋 Generated accessibility metadata", file=sys.stderr)

    return html_chunks, accessibility_meta


def create_accessibility_summary(
    html_chunks: List[str],
    accessibility_meta: Dict[str, str],
    language: str = 'en'
) -> str:
    """Create human-readable accessibility summary."""

    # Count accessibility features
    image_count = sum(len(re.findall(r'<img[^>]*>', chunk, re.IGNORECASE)) for chunk in html_chunks)
    alt_text_count = sum(len(re.findall(r'<img[^>]*alt\s*=\s*["\'][^"\']+["\']', chunk, re.IGNORECASE)) for chunk in html_chunks)
    heading_count = sum(len(re.findall(r'<h[1-6]', chunk, re.IGNORECASE)) for chunk in html_chunks)

    summary = [
        "EPUB Accessibility Summary",
        "=" * 28,
        f"Document Language: {language}",
        f"Total Images: {image_count}",
        f"Images with Alt Text: {alt_text_count}",
        f"Total Headings: {heading_count}",
        "",
        "Accessibility Features:",
        "• Structural navigation via headings",
        "• Logical reading order",
        "• ARIA landmarks",
        "• Language identification",
    ]

    if alt_text_count == image_count:
        summary.append("• Alternative text for all images ✅")
    elif alt_text_count > 0:
        summary.append(f"• Alternative text for {alt_text_count}/{image_count} images ⚠️")
    else:
        summary.append("• No alternative text provided ❌")

    summary.extend([
        "",
        "Standards Compliance:",
        "• EPUB Accessibility 1.1",
        "• WCAG 2.1 AA (partial)",
        "• Schema.org accessibility metadata"
    ])

    return "\n".join(summary)