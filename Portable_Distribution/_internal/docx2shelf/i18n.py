"""
Internationalization and Multi-language Support for EPUB Generation

This module provides comprehensive support for multiple languages and writing systems,
including RTL (Right-to-Left) text, CJK (Chinese, Japanese, Korean) languages,
and proper language detection and handling.

Features:
- Language detection and validation
- RTL text support (Arabic, Hebrew, Persian, etc.)
- CJK language support with proper typography
- Font selection for different writing systems
- Text direction handling
- Language-specific formatting rules
- Unicode normalization
- Hyphenation support for multiple languages
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


class WritingDirection(Enum):
    """Text writing direction."""
    LTR = "ltr"  # Left-to-right
    RTL = "rtl"  # Right-to-left
    TTB = "ttb"  # Top-to-bottom (for vertical writing)


class ScriptType(Enum):
    """Script/writing system types."""
    LATIN = "latin"
    ARABIC = "arabic"
    HEBREW = "hebrew"
    CJK = "cjk"
    CYRILLIC = "cyrillic"
    DEVANAGARI = "devanagari"
    THAI = "thai"
    HANGUL = "hangul"
    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    HAN = "han"  # Chinese characters


@dataclass
class LanguageConfig:
    """Configuration for a specific language."""

    # Basic language info
    code: str  # ISO 639-1 code (e.g., "en", "ar", "zh")
    name: str  # Human-readable name
    native_name: str  # Name in the language itself

    # Writing system
    direction: WritingDirection = WritingDirection.LTR
    script: ScriptType = ScriptType.LATIN

    # Typography
    primary_fonts: List[str] = field(default_factory=list)
    fallback_fonts: List[str] = field(default_factory=list)

    # Formatting preferences
    hyphenation_enabled: bool = True
    justification_enabled: bool = True
    line_break_rules: str = "normal"  # normal, strict, loose
    word_spacing: str = "normal"

    # Character handling
    normalize_unicode: bool = True
    normalization_form: str = "NFC"  # NFC, NFD, NFKC, NFKD

    # Quotation marks
    primary_quotes: Tuple[str, str] = (""", """)
    secondary_quotes: Tuple[str, str] = ("'", "'")

    # Number formatting
    decimal_separator: str = "."
    thousands_separator: str = ","

    # Date/time formatting patterns (strftime-compatible)
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"


# Predefined language configurations
LANGUAGE_CONFIGS = {
    "en": LanguageConfig(
        code="en",
        name="English",
        native_name="English",
        direction=WritingDirection.LTR,
        script=ScriptType.LATIN,
        primary_fonts=["Georgia", "Times New Roman", "serif"],
        primary_quotes=(""", """),
        secondary_quotes=("'", "'")
    ),
    "ar": LanguageConfig(
        code="ar",
        name="Arabic",
        native_name="العربية",
        direction=WritingDirection.RTL,
        script=ScriptType.ARABIC,
        primary_fonts=["Amiri", "Noto Naskh Arabic", "Arabic Typesetting", "serif"],
        fallback_fonts=["Tahoma", "Arial Unicode MS"],
        justification_enabled=True,
        primary_quotes=("«", "»"),
        secondary_quotes=("‹", "›"),
        decimal_separator="٫",
        thousands_separator="٬"
    ),
    "he": LanguageConfig(
        code="he",
        name="Hebrew",
        native_name="עברית",
        direction=WritingDirection.RTL,
        script=ScriptType.HEBREW,
        primary_fonts=["SBL Hebrew", "Noto Serif Hebrew", "David", "serif"],
        fallback_fonts=["Arial Unicode MS", "Tahoma"],
        primary_quotes=("״", "״"),
        secondary_quotes=("׳", "׳")
    ),
    "zh": LanguageConfig(
        code="zh",
        name="Chinese",
        native_name="中文",
        direction=WritingDirection.LTR,
        script=ScriptType.CJK,
        primary_fonts=["Noto Serif CJK SC", "SimSun", "serif"],
        fallback_fonts=["Arial Unicode MS", "sans-serif"],
        hyphenation_enabled=False,
        line_break_rules="strict",
        primary_quotes=("「", "」"),
        secondary_quotes=("『", "』")
    ),
    "ja": LanguageConfig(
        code="ja",
        name="Japanese",
        native_name="日本語",
        direction=WritingDirection.LTR,
        script=ScriptType.CJK,
        primary_fonts=["Noto Serif CJK JP", "Yu Mincho", "serif"],
        fallback_fonts=["Hiragino Mincho Pro", "MS Mincho"],
        hyphenation_enabled=False,
        line_break_rules="strict",
        primary_quotes=("「", "」"),
        secondary_quotes=("『", "』")
    ),
    "ko": LanguageConfig(
        code="ko",
        name="Korean",
        native_name="한국어",
        direction=WritingDirection.LTR,
        script=ScriptType.HANGUL,
        primary_fonts=["Noto Serif CJK KR", "Batang", "serif"],
        fallback_fonts=["Dotum", "Arial Unicode MS"],
        hyphenation_enabled=False,
        line_break_rules="strict",
        primary_quotes=("「", "」"),
        secondary_quotes=("『", "』")
    ),
    "fa": LanguageConfig(
        code="fa",
        name="Persian",
        native_name="فارسی",
        direction=WritingDirection.RTL,
        script=ScriptType.ARABIC,
        primary_fonts=["Noto Naskh Arabic", "Persian", "Tahoma"],
        primary_quotes=("«", "»"),
        secondary_quotes=("‹", "›")
    ),
    "ru": LanguageConfig(
        code="ru",
        name="Russian",
        native_name="Русский",
        direction=WritingDirection.LTR,
        script=ScriptType.CYRILLIC,
        primary_fonts=["Times New Roman", "serif"],
        primary_quotes=("«", "»"),
        secondary_quotes=("„", """)
    ),
    "de": LanguageConfig(
        code="de",
        name="German",
        native_name="Deutsch",
        direction=WritingDirection.LTR,
        script=ScriptType.LATIN,
        primary_fonts=["Georgia", "Times New Roman", "serif"],
        primary_quotes=("„", """),
        secondary_quotes=("‚", "'")
    ),
    "fr": LanguageConfig(
        code="fr",
        name="French",
        native_name="Français",
        direction=WritingDirection.LTR,
        script=ScriptType.LATIN,
        primary_fonts=["Georgia", "Times New Roman", "serif"],
        primary_quotes=("«", "»"),
        secondary_quotes=("‹", "›")
    ),
    "es": LanguageConfig(
        code="es",
        name="Spanish",
        native_name="Español",
        direction=WritingDirection.LTR,
        script=ScriptType.LATIN,
        primary_fonts=["Georgia", "Times New Roman", "serif"],
        primary_quotes=("«", "»"),
        secondary_quotes=("‹", "›")
    ),
    "th": LanguageConfig(
        code="th",
        name="Thai",
        native_name="ไทย",
        direction=WritingDirection.LTR,
        script=ScriptType.THAI,
        primary_fonts=["Noto Serif Thai", "Cordia New", "serif"],
        hyphenation_enabled=False,
        word_spacing="0.25em"
    )
}


def detect_language_from_content(content: str) -> Optional[str]:
    """Detect language from text content using character frequency analysis."""
    if not content or len(content.strip()) < 50:
        return None

    # Remove HTML tags for analysis
    text = re.sub(r'<[^>]+>', '', content)
    text = text.strip()[:1000]  # Analyze first 1000 chars

    if not text:
        return None

    # Count character frequencies by script
    script_counts = {
        ScriptType.LATIN: 0,
        ScriptType.ARABIC: 0,
        ScriptType.HEBREW: 0,
        ScriptType.CJK: 0,
        ScriptType.CYRILLIC: 0,
        ScriptType.THAI: 0,
        ScriptType.HANGUL: 0
    }

    for char in text:
        if char.isspace() or char.isdigit():
            continue

        # Get Unicode category and script
        category = unicodedata.category(char)
        if category.startswith('L'):  # Letter categories
            name = unicodedata.name(char, '')

            if 'ARABIC' in name:
                script_counts[ScriptType.ARABIC] += 1
            elif 'HEBREW' in name:
                script_counts[ScriptType.HEBREW] += 1
            elif 'CJK' in name or 'IDEOGRAPHIC' in name:
                script_counts[ScriptType.CJK] += 1
            elif 'CYRILLIC' in name:
                script_counts[ScriptType.CYRILLIC] += 1
            elif 'THAI' in name:
                script_counts[ScriptType.THAI] += 1
            elif 'HANGUL' in name:
                script_counts[ScriptType.HANGUL] += 1
            elif ord(char) < 128:  # Basic Latin
                script_counts[ScriptType.LATIN] += 1

    # Find dominant script
    dominant_script = max(script_counts, key=script_counts.get)

    # Map script to likely language
    script_to_language = {
        ScriptType.ARABIC: "ar",
        ScriptType.HEBREW: "he",
        ScriptType.CJK: "zh",  # Could be zh, ja, or ko
        ScriptType.CYRILLIC: "ru",
        ScriptType.THAI: "th",
        ScriptType.HANGUL: "ko",
        ScriptType.LATIN: "en"  # Default to English for Latin script
    }

    return script_to_language.get(dominant_script)


def normalize_text(text: str, config: LanguageConfig) -> str:
    """Normalize text according to language configuration."""
    if not config.normalize_unicode:
        return text

    return unicodedata.normalize(config.normalization_form, text)


def apply_language_specific_formatting(content: str, config: LanguageConfig) -> str:
    """Apply language-specific formatting rules to HTML content."""
    # Add language and direction attributes to HTML elements
    content = add_language_attributes(content, config)

    # Apply text direction
    content = apply_text_direction(content, config)

    # Normalize Unicode if needed
    if config.normalize_unicode:
        content = normalize_text(content, config)

    # Apply quotation mark corrections
    content = fix_quotation_marks(content, config)

    return content


def add_language_attributes(content: str, config: LanguageConfig) -> str:
    """Add lang and dir attributes to HTML elements."""
    # Add to html element
    html_pattern = r'<html([^>]*?)>'
    def add_html_attrs(match):
        attrs = match.group(1)

        # Add lang if not present
        if 'lang=' not in attrs:
            attrs += f' lang="{config.code}"'

        # Add dir if RTL and not present
        if config.direction == WritingDirection.RTL and 'dir=' not in attrs:
            attrs += ' dir="rtl"'

        return f'<html{attrs}>'

    content = re.sub(html_pattern, add_html_attrs, content, flags=re.IGNORECASE)

    # Add to body element for RTL languages
    if config.direction == WritingDirection.RTL:
        body_pattern = r'<body([^>]*?)>'
        def add_body_dir(match):
            attrs = match.group(1)
            if 'dir=' not in attrs:
                attrs += ' dir="rtl"'
            return f'<body{attrs}>'

        content = re.sub(body_pattern, add_body_dir, content, flags=re.IGNORECASE)

    return content


def apply_text_direction(content: str, config: LanguageConfig) -> str:
    """Apply text direction styling and attributes."""
    if config.direction == WritingDirection.RTL:
        # Add RTL class to paragraphs and text elements
        replacements = [
            (r'<p([^>]*?)>', r'<p\1 dir="rtl">'),
            (r'<div([^>]*?)>', r'<div\1 dir="rtl">'),
            (r'<span([^>]*?)>', r'<span\1 dir="rtl">'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    return content


def fix_quotation_marks(content: str, config: LanguageConfig) -> str:
    """Replace ASCII quotes with language-appropriate quotation marks."""
    # Replace double quotes
    content = content.replace('"', config.primary_quotes[0])
    content = content.replace('"', config.primary_quotes[1])

    # Replace single quotes
    content = content.replace("'", config.secondary_quotes[0])
    content = content.replace("'", config.secondary_quotes[1])

    return content


def generate_language_css(config: LanguageConfig) -> str:
    """Generate CSS for language-specific typography and layout."""
    css_parts = []

    # Font stack
    font_stack = ", ".join([
        f'"{font}"' if ' ' in font else font
        for font in config.primary_fonts + config.fallback_fonts
    ])

    css_parts.append(f"""
/* Language-specific typography for {config.name} ({config.code}) */
:lang({config.code}) {{
    font-family: {font_stack};
""")

    # Text direction
    if config.direction == WritingDirection.RTL:
        css_parts.append("    direction: rtl;")
        css_parts.append("    text-align: right;")

    # Line breaking rules for CJK
    if config.script == ScriptType.CJK:
        css_parts.append(f"    line-break: {config.line_break_rules};")
        css_parts.append("    word-break: keep-all;")
        css_parts.append("    overflow-wrap: break-word;")

    # Word spacing for Thai
    if config.script == ScriptType.THAI:
        css_parts.append(f"    word-spacing: {config.word_spacing};")

    # Hyphenation
    if config.hyphenation_enabled:
        css_parts.append("    hyphens: auto;")
        css_parts.append(f"    -webkit-hyphens: auto;")
        css_parts.append(f"    -ms-hyphens: auto;")
    else:
        css_parts.append("    hyphens: none;")

    # Text justification
    if not config.justification_enabled:
        css_parts.append("    text-align: left;")

    css_parts.append("}")

    # RTL-specific adjustments
    if config.direction == WritingDirection.RTL:
        css_parts.append(f"""

/* RTL-specific adjustments for {config.name} */
:lang({config.code}) .toc {{
    direction: rtl;
    text-align: right;
}}

:lang({config.code}) blockquote {{
    border-right: 3px solid #ccc;
    border-left: none;
    padding-right: 1em;
    padding-left: 0;
    margin-right: 1em;
    margin-left: 0;
}}

:lang({config.code}) ul, :lang({config.code}) ol {{
    padding-right: 2em;
    padding-left: 0;
}}""")

    # CJK-specific adjustments
    if config.script == ScriptType.CJK:
        css_parts.append(f"""

/* CJK-specific adjustments for {config.name} */
:lang({config.code}) {{
    text-indent: 2em;
}}

:lang({config.code}) h1, :lang({config.code}) h2, :lang({config.code}) h3,
:lang({config.code}) h4, :lang({config.code}) h5, :lang({config.code}) h6 {{
    text-align: center;
}}

:lang({config.code}) .punctuation {{
    font-feature-settings: "halt" 1;
}}""")

    return "\n".join(css_parts)


def get_language_config(language_code: str) -> LanguageConfig:
    """Get language configuration for a given language code."""
    # Normalize language code
    lang_code = language_code.lower().split('-')[0]  # Remove region codes

    return LANGUAGE_CONFIGS.get(lang_code, LANGUAGE_CONFIGS["en"])


def validate_language_code(language_code: str) -> bool:
    """Validate if a language code is supported."""
    lang_code = language_code.lower().split('-')[0]
    return lang_code in LANGUAGE_CONFIGS


def get_supported_languages() -> List[Tuple[str, str, str]]:
    """Get list of supported languages as (code, name, native_name) tuples."""
    return [
        (config.code, config.name, config.native_name)
        for config in LANGUAGE_CONFIGS.values()
    ]


def detect_mixed_languages(content: str) -> List[str]:
    """Detect multiple languages in content."""
    # This is a simplified implementation
    # A real implementation would use more sophisticated NLP techniques
    detected = []

    # Look for common language patterns
    patterns = {
        "ar": r'[\u0600-\u06FF\u0750-\u077F]+',  # Arabic
        "he": r'[\u0590-\u05FF]+',               # Hebrew
        "zh": r'[\u4E00-\u9FFF]+',               # CJK Unified Ideographs
        "ja": r'[\u3040-\u309F\u30A0-\u30FF]+', # Hiragana + Katakana
        "ko": r'[\uAC00-\uD7AF]+',               # Hangul
        "th": r'[\u0E00-\u0E7F]+',               # Thai
        "ru": r'[\u0400-\u04FF]+',               # Cyrillic
    }

    for lang, pattern in patterns.items():
        if re.search(pattern, content):
            detected.append(lang)

    return detected


def create_polyglot_css(languages: List[str]) -> str:
    """Create CSS for documents with multiple languages."""
    css_parts = []

    css_parts.append("/* Multi-language document styles */")

    for lang_code in languages:
        config = get_language_config(lang_code)
        css_parts.append(generate_language_css(config))

    # Add general polyglot styles
    css_parts.append("""
/* General polyglot support */
.lang-switch {
    font-size: 0.9em;
    color: #666;
    margin: 0.5em 0;
}

.mixed-direction {
    unicode-bidi: embed;
}

.rtl-embed {
    direction: rtl;
    unicode-bidi: embed;
}

.ltr-embed {
    direction: ltr;
    unicode-bidi: embed;
}""")

    return "\n".join(css_parts)