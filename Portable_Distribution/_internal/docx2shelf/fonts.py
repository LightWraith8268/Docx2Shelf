from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Set


def extract_text_from_html_chunks(html_chunks: List[str]) -> str:
    """Extract all text content from HTML chunks for character analysis."""
    all_text = []

    for chunk in html_chunks:
        # Remove HTML tags but preserve text content
        text = re.sub(r'<[^>]+>', ' ', chunk)
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')

        all_text.append(text)

    return ' '.join(all_text)


def get_unique_characters(text: str) -> Set[str]:
    """Get set of unique characters used in the text."""
    # Remove excessive whitespace but preserve one space
    text = re.sub(r'\s+', ' ', text)
    return set(text)


def subset_font(font_path: Path, characters: Set[str], output_path: Path, quiet: bool = False) -> bool:
    """Subset a font file to include only the specified characters.

    Uses fontTools library for font subsetting.
    Returns True if successful, False otherwise.
    """
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        if not quiet:
            print("Warning: fontTools not available. Font subsetting disabled.", file=sys.stderr)
            print("Install with: pip install fonttools", file=sys.stderr)
        return False

    try:
        # Create character list for subsetting
        char_list = list(characters)

        # Add some essential characters if not present
        essential_chars = {' ', '\n', '\t', '.', ',', '!', '?', '-'}
        for char in essential_chars:
            if char not in characters:
                char_list.append(char)

        # Create subsetter options
        options = subset.Options()
        options.layout_features = ['*']  # Keep layout features
        options.name_IDs = ['*']  # Keep name table
        options.notdef_outline = True  # Keep .notdef glyph
        options.glyph_names = False  # Remove glyph names to save space

        # Create subsetter
        subsetter = subset.Subsetter(options=options)

        # Load font
        font = TTFont(str(font_path))

        # Populate subsetter with characters
        subsetter.populate(text=''.join(char_list))

        # Subset the font
        subsetter.subset(font)

        # Save subsetted font
        font.save(str(output_path))

        if not quiet:
            original_size = font_path.stat().st_size
            new_size = output_path.stat().st_size
            reduction = ((original_size - new_size) / original_size) * 100
            print(f"Font subsetted: {font_path.name} ({original_size:,} → {new_size:,} bytes, {reduction:.1f}% reduction)")

        return True

    except Exception as e:
        if not quiet:
            print(f"Error subsetting font {font_path.name}: {e}", file=sys.stderr)
        return False


def process_embedded_fonts(fonts_dir: Path, html_chunks: List[str], output_dir: Path, quiet: bool = False) -> List[Path]:
    """Process and subset fonts based on actual text usage.

    Returns list of processed font files.
    """
    if not fonts_dir.exists() or not fonts_dir.is_dir():
        return []

    # Extract all text content
    all_text = extract_text_from_html_chunks(html_chunks)
    unique_chars = get_unique_characters(all_text)

    if not quiet:
        print(f"Found {len(unique_chars)} unique characters in document")

    # Find font files
    font_extensions = {'.ttf', '.otf', '.woff', '.woff2'}
    font_files = []

    for ext in font_extensions:
        font_files.extend(fonts_dir.glob(f"*{ext}"))

    if not font_files:
        if not quiet:
            print("No font files found in embed-fonts directory")
        return []

    # Check for fontTools availability
    try:
        import fontTools
    except ImportError:
        # Copy fonts without subsetting if fontTools is not available
        if not quiet:
            print("fontTools not available. Copying fonts without subsetting.")
            print("Install fontTools for font subsetting: pip install fonttools")

        processed_fonts = []
        for font_file in font_files:
            # Only process TTF and OTF files
            if font_file.suffix.lower() in {'.ttf', '.otf'}:
                output_path = output_dir / font_file.name
                output_path.write_bytes(font_file.read_bytes())
                processed_fonts.append(output_path)
                if not quiet:
                    print(f"Copied font: {font_file.name}")

        return processed_fonts

    # Process fonts with subsetting
    processed_fonts = []

    for font_file in font_files:
        # Only subset TTF and OTF files
        if font_file.suffix.lower() not in {'.ttf', '.otf'}:
            # Copy other formats as-is
            output_path = output_dir / font_file.name
            output_path.write_bytes(font_file.read_bytes())
            processed_fonts.append(output_path)
            if not quiet:
                print(f"Copied font (no subsetting): {font_file.name}")
            continue

        # Create output filename
        stem = font_file.stem
        suffix = font_file.suffix
        output_path = output_dir / f"{stem}_subset{suffix}"

        # Subset the font
        if subset_font(font_file, unique_chars, output_path, quiet):
            processed_fonts.append(output_path)
        else:
            # Fall back to copying original if subsetting fails
            fallback_path = output_dir / font_file.name
            fallback_path.write_bytes(font_file.read_bytes())
            processed_fonts.append(fallback_path)
            if not quiet:
                print(f"Copied font (subsetting failed): {font_file.name}")

    return processed_fonts


def warn_about_font_licensing(fonts_dir: Path, quiet: bool = False) -> None:
    """Display warnings about font licensing for embedded fonts."""
    if quiet:
        return

    font_files = []
    font_extensions = {'.ttf', '.otf', '.woff', '.woff2'}

    for ext in font_extensions:
        font_files.extend(fonts_dir.glob(f"*{ext}"))

    if font_files:
        print("\n⚠️  Font Licensing Warning:", file=sys.stderr)
        print("Please ensure you have the right to embed and distribute the following fonts:", file=sys.stderr)
        for font_file in font_files:
            print(f"  - {font_file.name}", file=sys.stderr)
        print("Some fonts may require additional licensing for ebook distribution.", file=sys.stderr)
        print("Check the font's license agreement before distribution.\n", file=sys.stderr)