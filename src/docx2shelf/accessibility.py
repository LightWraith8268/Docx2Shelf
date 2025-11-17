from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class AccessibilityFeature(Enum):
    """EPUB 3 accessibility features."""

    ARIA_LANDMARKS = "aria-landmarks"
    HEADING_STRUCTURE = "heading-structure"
    PAGE_NAVIGATION = "page-navigation"
    TABLE_OF_CONTENTS = "table-of-contents"
    ALT_TEXT = "alt-text"
    LONG_DESCRIPTIONS = "long-descriptions"
    SEMANTIC_MARKUP = "semantic-markup"
    READING_ORDER = "reading-order"
    HIGH_CONTRAST = "high-contrast"
    LARGE_TEXT = "large-text"
    KEYBOARD_NAV = "keyboard-navigation"
    SCREEN_READER = "screen-reader-optimized"


@dataclass
class AccessibilityConfiguration:
    """Configuration for accessibility features."""

    # WCAG compliance level
    wcag_level: str = "AA"  # A, AA, AAA

    # Enabled features
    enabled_features: List[AccessibilityFeature] = field(
        default_factory=lambda: [
            AccessibilityFeature.ARIA_LANDMARKS,
            AccessibilityFeature.HEADING_STRUCTURE,
            AccessibilityFeature.TABLE_OF_CONTENTS,
            AccessibilityFeature.SEMANTIC_MARKUP,
            AccessibilityFeature.READING_ORDER,
            AccessibilityFeature.SCREEN_READER,
        ]
    )

    # Language and localization
    primary_language: str = "en"
    language_direction: str = "ltr"  # ltr, rtl

    # Visual accessibility
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    minimum_font_size: str = "12pt"
    minimum_contrast_ratio: float = 4.5  # WCAG AA standard

    # Navigation aids
    skip_links: bool = True
    page_list: bool = False
    landmark_navigation: bool = True
    heading_navigation: bool = True

    # Screen reader optimization
    reading_order_hints: bool = True
    aria_descriptions: bool = True
    semantic_roles: bool = True

    # Alternative content
    alt_text_required: bool = True
    long_descriptions: bool = False

    # Metadata
    accessibility_summary: str = "This publication conforms to WCAG 2.1 Level AA."
    accessibility_features: List[str] = field(default_factory=list)
    accessibility_hazards: List[str] = field(default_factory=lambda: ["none"])
    accessibility_api: str = "ARIA"


def check_image_alt_text(html_chunks: List[str]) -> List[Tuple[str, str]]:
    """Check for images missing alt text.

    Returns list of (chunk_index, img_tag) for images without alt text.
    """
    missing_alt = []

    for i, chunk in enumerate(html_chunks):
        # Find all img tags
        img_pattern = r"<img[^>]*>"
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
                alt_text = input("   Enter alt text (or 'skip' to leave empty): ").strip()
                if alt_text.lower() == "skip":
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
                if "alt=" in img_tag.lower():
                    # Replace existing empty alt
                    new_img_tag = re.sub(
                        r'alt\s*=\s*["\'][^"\']*["\']',
                        f'alt="{alt_text}"',
                        img_tag,
                        flags=re.IGNORECASE,
                    )
                else:
                    # Add alt attribute before the closing >
                    new_img_tag = img_tag.replace(">", f' alt="{alt_text}">')

                updated_chunk = updated_chunk.replace(img_tag, new_img_tag)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def generate_accessibility_metadata() -> Dict[str, str]:
    """Generate EPUB accessibility metadata."""
    return {
        "schema:accessMode": "textual,visual",
        "schema:accessModeSufficient": "textual",
        "schema:accessibilityFeature": "structuralNavigation,readingOrder,alternativeText",
        "schema:accessibilityHazard": "none",
        "schema:accessibilitySummary": "This publication conforms to EPUB Accessibility standards with structured navigation, reading order, and alternative text for images.",
    }


def add_aria_landmarks(html_chunks: List[str], metadata) -> List[str]:
    """Add ARIA landmarks to HTML content."""
    if not html_chunks:
        return html_chunks

    updated_chunks = []

    for i, chunk in enumerate(html_chunks):
        updated_chunk = chunk

        # Add main landmark to first content chapter
        if i == 0 and "<body" in chunk:
            # Find body tag and add role="main"
            body_pattern = r"<body([^>]*)>"

            def add_main_role(match):
                attrs = match.group(1)
                if "role=" not in attrs.lower():
                    attrs += ' role="main"'
                return f"<body{attrs}>"

            updated_chunk = re.sub(body_pattern, add_main_role, updated_chunk, flags=re.IGNORECASE)

        # Add navigation landmarks to heading elements
        heading_pattern = r"<(h[1-6])([^>]*)>(.*?)</\1>"

        def add_heading_nav(match):
            tag, attrs, content = match.groups()
            # Add aria-level if not present
            if "aria-level=" not in attrs.lower():
                level = tag[1]  # Extract number from h1, h2, etc.
                attrs += f' aria-level="{level}"'
            return f"<{tag}{attrs}>{content}</{tag}>"

        updated_chunk = re.sub(
            heading_pattern, add_heading_nav, updated_chunk, flags=re.IGNORECASE | re.DOTALL
        )

        updated_chunks.append(updated_chunk)

    return updated_chunks


def detect_document_language(html_chunks: List[str], metadata) -> str:
    """Detect document language from content or metadata."""
    # Try to get language from metadata first
    if hasattr(metadata, "language") and metadata.language:
        return metadata.language

    # Look for lang attributes in HTML
    for chunk in html_chunks:
        lang_match = re.search(r'<html[^>]*lang\s*=\s*["\']([^"\']+)["\']', chunk, re.IGNORECASE)
        if lang_match:
            return lang_match.group(1)

    # Default to English
    return "en"


def add_language_attributes(html_chunks: List[str], language: str) -> List[str]:
    """Add language attributes to HTML elements."""
    if not language:
        return html_chunks

    updated_chunks = []

    for chunk in html_chunks:
        updated_chunk = chunk

        # Add lang attribute to html element if not present
        if "<html" in chunk and "lang=" not in chunk.lower():
            html_pattern = r"<html([^>]*)>"

            def add_lang(match):
                attrs = match.group(1)
                attrs += f' lang="{language}"'
                return f"<html{attrs}>"

            updated_chunk = re.sub(html_pattern, add_lang, updated_chunk, flags=re.IGNORECASE)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def validate_reading_order(html_chunks: List[str]) -> List[str]:
    """Validate and report on reading order issues."""
    issues = []

    for i, chunk in enumerate(html_chunks):
        # Check for heading hierarchy skips
        headings = re.findall(r"<h([1-6])", chunk, re.IGNORECASE)

        if headings:
            heading_levels = [int(h) for h in headings]

            for j in range(1, len(heading_levels)):
                current = heading_levels[j]
                previous = heading_levels[j - 1]

                # Check if we skip heading levels (e.g., h1 -> h3)
                if current > previous + 1:
                    issues.append(
                        f"Chunk {i}: Heading hierarchy skip from h{previous} to h{current}"
                    )

    return issues


def process_accessibility_features(
    html_chunks: List[str], metadata, interactive: bool = True, quiet: bool = False
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
    html_chunks: List[str], accessibility_meta: Dict[str, str], language: str = "en"
) -> str:
    """Create human-readable accessibility summary."""

    # Count accessibility features
    image_count = sum(len(re.findall(r"<img[^>]*>", chunk, re.IGNORECASE)) for chunk in html_chunks)
    alt_text_count = sum(
        len(re.findall(r'<img[^>]*alt\s*=\s*["\'][^"\']+["\']', chunk, re.IGNORECASE))
        for chunk in html_chunks
    )
    heading_count = sum(len(re.findall(r"<h[1-6]", chunk, re.IGNORECASE)) for chunk in html_chunks)

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

    summary.extend(
        [
            "",
            "Standards Compliance:",
            "• EPUB Accessibility 1.1",
            "• WCAG 2.1 AA (partial)",
            "• Schema.org accessibility metadata",
        ]
    )

    return "\n".join(summary)


def generate_accessibility_css(config: AccessibilityConfiguration) -> str:
    """Generate CSS for accessibility features."""
    css_parts = []

    # Skip links styling
    if config.skip_links:
        css_parts.append(
            """
/* Skip Navigation Links */
.skip-links {
    position: absolute;
    top: -40px;
    left: 6px;
    background: #000;
    color: #fff;
    padding: 8px;
    text-decoration: none;
    border-radius: 0 0 4px 4px;
    list-style: none;
    margin: 0;
    z-index: 1000;
}

.skip-links a {
    color: #fff;
    text-decoration: none;
    padding: 4px 8px;
    display: block;
}

.skip-links a:focus {
    position: relative;
    top: 40px;
    left: 0;
}"""
        )

    # High contrast mode
    if config.high_contrast_mode:
        css_parts.append(
            """
/* High Contrast Mode */
@media (prefers-contrast: high) {
    body {
        background: #000 !important;
        color: #fff !important;
    }

    a {
        color: #00ff00 !important;
    }

    a:visited {
        color: #ff00ff !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #ffff00 !important;
    }
}"""
        )

    # Large text support
    if config.large_text_mode:
        css_parts.append(
            f"""
/* Large Text Support */
@media (min-resolution: 192dpi) and (prefers-reduced-motion: no-preference) {{
    body {{
        font-size: {config.minimum_font_size};
    }}
}}

.large-text body {{
    font-size: calc({config.minimum_font_size} * 1.2);
    line-height: 1.8;
}}"""
        )

    # Focus indicators
    css_parts.append(
        """
/* Enhanced Focus Indicators */
*:focus {
    outline: 2px solid #0066cc;
    outline-offset: 2px;
}

*:focus:not(:focus-visible) {
    outline: none;
}

*:focus-visible {
    outline: 2px solid #0066cc;
    outline-offset: 2px;
}"""
    )

    # Screen reader optimizations
    css_parts.append(
        """
/* Screen Reader Optimizations */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.sr-only:focus {
    position: static;
    width: auto;
    height: auto;
    padding: inherit;
    margin: inherit;
    overflow: visible;
    clip: auto;
    white-space: inherit;
}"""
    )

    # Motion preferences
    css_parts.append(
        """
/* Respect Motion Preferences */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}"""
    )

    return "\n".join(css_parts)


def create_default_accessibility_config() -> AccessibilityConfiguration:
    """Create a default accessibility configuration."""
    return AccessibilityConfiguration(
        accessibility_features=[
            "structuralNavigation",
            "alternativeText",
            "tableOfContents",
            "readingOrder",
        ]
    )


def create_enhanced_accessibility_config() -> AccessibilityConfiguration:
    """Create an enhanced accessibility configuration for maximum compliance."""
    return AccessibilityConfiguration(
        wcag_level="AAA",
        enabled_features=list(AccessibilityFeature),
        minimum_contrast_ratio=7.0,
        large_text_mode=True,
        long_descriptions=True,
        accessibility_features=[
            "structuralNavigation",
            "alternativeText",
            "tableOfContents",
            "readingOrder",
            "highContrast",
            "largeText",
            "keyboardNavigation",
            "screenReaderOptimized",
        ],
        accessibility_summary="This publication conforms to WCAG 2.1 Level AAA and includes enhanced accessibility features for users with disabilities.",
    )
