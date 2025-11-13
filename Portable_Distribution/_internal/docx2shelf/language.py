from __future__ import annotations

import re
from typing import Dict, List

# Language-specific configuration data
LANGUAGE_CONFIGS = {
    # Right-to-left languages
    'ar': {
        'name': 'Arabic',
        'script': 'Arab',
        'direction': 'rtl',
        'hyphenation': False,
        'justify': True,
        'font_stack': '"Noto Sans Arabic", "Arial Unicode MS", "Tahoma", sans-serif',
        'css_rules': [
            'body { direction: rtl; text-align: right; }',
            'h1, h2, h3, h4, h5, h6 { direction: rtl; text-align: right; }',
            'p { direction: rtl; text-align: right; }',
            'blockquote { direction: rtl; text-align: right; }',
        ]
    },
    'he': {
        'name': 'Hebrew',
        'script': 'Hebr',
        'direction': 'rtl',
        'hyphenation': False,
        'justify': True,
        'font_stack': '"Noto Sans Hebrew", "Arial Unicode MS", "Tahoma", sans-serif',
        'css_rules': [
            'body { direction: rtl; text-align: right; }',
            'h1, h2, h3, h4, h5, h6 { direction: rtl; text-align: right; }',
            'p { direction: rtl; text-align: right; }',
            'blockquote { direction: rtl; text-align: right; }',
        ]
    },
    'fa': {
        'name': 'Persian',
        'script': 'Arab',
        'direction': 'rtl',
        'hyphenation': False,
        'justify': True,
        'font_stack': '"Noto Sans Arabic", "Arial Unicode MS", "Tahoma", sans-serif',
        'css_rules': [
            'body { direction: rtl; text-align: right; }',
            'h1, h2, h3, h4, h5, h6 { direction: rtl; text-align: right; }',
            'p { direction: rtl; text-align: right; }',
            'blockquote { direction: rtl; text-align: right; }',
        ]
    },

    # CJK languages (vertical writing support)
    'zh': {
        'name': 'Chinese',
        'script': 'Hans',
        'direction': 'ltr',
        'hyphenation': False,
        'justify': False,
        'font_stack': '"Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", "SimHei", sans-serif',
        'css_rules': [
            'body { word-break: break-all; }',
            'p { text-align: justify; text-justify: inter-ideograph; }',
        ],
        'vertical_rules': [
            'body { writing-mode: vertical-rl; text-orientation: mixed; }',
            'h1, h2, h3, h4, h5, h6 { writing-mode: vertical-rl; }',
            'p { writing-mode: vertical-rl; text-orientation: mixed; }',
        ]
    },
    'zh-tw': {
        'name': 'Chinese (Traditional)',
        'script': 'Hant',
        'direction': 'ltr',
        'hyphenation': False,
        'justify': False,
        'font_stack': '"Noto Sans CJK TC", "Source Han Sans TC", "Microsoft JhengHei", "PMingLiU", sans-serif',
        'css_rules': [
            'body { word-break: break-all; }',
            'p { text-align: justify; text-justify: inter-ideograph; }',
        ],
        'vertical_rules': [
            'body { writing-mode: vertical-rl; text-orientation: mixed; }',
            'h1, h2, h3, h4, h5, h6 { writing-mode: vertical-rl; }',
            'p { writing-mode: vertical-rl; text-orientation: mixed; }',
        ]
    },
    'ja': {
        'name': 'Japanese',
        'script': 'Jpan',
        'direction': 'ltr',
        'hyphenation': False,
        'justify': False,
        'font_stack': '"Noto Sans CJK JP", "Source Han Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif',
        'css_rules': [
            'body { word-break: break-all; }',
            'p { text-align: justify; text-justify: inter-ideograph; }',
        ],
        'vertical_rules': [
            'body { writing-mode: vertical-rl; text-orientation: mixed; }',
            'h1, h2, h3, h4, h5, h6 { writing-mode: vertical-rl; }',
            'p { writing-mode: vertical-rl; text-orientation: mixed; }',
        ]
    },
    'ko': {
        'name': 'Korean',
        'script': 'Kore',
        'direction': 'ltr',
        'hyphenation': False,
        'justify': True,
        'font_stack': '"Noto Sans CJK KR", "Source Han Sans KR", "Malgun Gothic", "Dotum", sans-serif',
        'css_rules': [
            'body { word-break: keep-all; }',
            'p { text-align: justify; text-justify: inter-word; }',
        ]
    },

    # European languages with special requirements
    'de': {
        'name': 'German',
        'script': 'Latn',
        'direction': 'ltr',
        'hyphenation': True,
        'justify': True,
        'font_stack': None,  # Use default
        'css_rules': [
            'html { hyphens: auto; }',
            'p { text-align: justify; }',
        ]
    },
    'fr': {
        'name': 'French',
        'script': 'Latn',
        'direction': 'ltr',
        'hyphenation': True,
        'justify': True,
        'font_stack': None,
        'css_rules': [
            'html { hyphens: auto; }',
            'p { text-align: justify; }',
        ]
    },
    'ru': {
        'name': 'Russian',
        'script': 'Cyrl',
        'direction': 'ltr',
        'hyphenation': True,
        'justify': True,
        'font_stack': '"Noto Sans", "Times New Roman", serif',
        'css_rules': [
            'html { hyphens: auto; }',
            'p { text-align: justify; }',
        ]
    },
}

# Default fallbacks for unknown languages
DEFAULT_CONFIG = {
    'name': 'Unknown',
    'script': 'Latn',
    'direction': 'ltr',
    'hyphenation': True,
    'justify': True,
    'font_stack': None,
    'css_rules': []
}


def get_language_config(language_code: str) -> Dict:
    """Get language configuration for a given BCP-47 language code."""
    # Normalize language code
    lang_code = language_code.lower().strip()

    # Try exact match first
    if lang_code in LANGUAGE_CONFIGS:
        return LANGUAGE_CONFIGS[lang_code]

    # Try base language (e.g., 'en-us' -> 'en')
    base_lang = lang_code.split('-')[0]
    if base_lang in LANGUAGE_CONFIGS:
        return LANGUAGE_CONFIGS[base_lang]

    # Return default configuration
    return DEFAULT_CONFIG


def is_rtl_language(language_code: str) -> bool:
    """Check if language is right-to-left."""
    config = get_language_config(language_code)
    return config['direction'] == 'rtl'


def is_cjk_language(language_code: str) -> bool:
    """Check if language is CJK (Chinese, Japanese, Korean)."""
    base_lang = language_code.lower().split('-')[0]
    return base_lang in ['zh', 'ja', 'ko']


def supports_vertical_writing(language_code: str) -> bool:
    """Check if language supports vertical writing mode."""
    config = get_language_config(language_code)
    return 'vertical_rules' in config


def generate_language_css(language_code: str, vertical_mode: bool = False) -> str:
    """Generate CSS rules for language-specific formatting."""
    config = get_language_config(language_code)
    css_rules = []

    # Add font stack if specified
    if config.get('font_stack'):
        css_rules.append(f'body {{ font-family: {config["font_stack"]}; }}')

    # Add base language rules
    css_rules.extend(config.get('css_rules', []))

    # Add vertical writing rules if requested and supported
    if vertical_mode and 'vertical_rules' in config:
        css_rules.extend(config['vertical_rules'])

    return '\n'.join(css_rules)


def apply_language_defaults(opts, language_code: str) -> None:
    """Apply language-aware defaults to build options."""
    config = get_language_config(language_code)

    # Override hyphenation default based on language
    if hasattr(opts, 'hyphenate') and opts.hyphenate is None:
        opts.hyphenate = config['hyphenation']

    # Override justification default based on language
    if hasattr(opts, 'justify') and opts.justify is None:
        opts.justify = config['justify']


def add_language_attributes_to_html(html_chunks: List[str], language_code: str) -> List[str]:
    """Add appropriate language and direction attributes to HTML."""
    config = get_language_config(language_code)
    updated_chunks = []

    for chunk in html_chunks:
        updated_chunk = chunk

        # Add lang and dir attributes to html element
        if '<html' in chunk:
            # Add lang attribute
            if 'lang=' not in chunk.lower():
                html_pattern = r'<html([^>]*?)>'
                def add_lang_attr(match):
                    attrs = match.group(1)
                    attrs += f' lang="{language_code}"'
                    if config['direction'] == 'rtl':
                        attrs += ' dir="rtl"'
                    return f'<html{attrs}>'

                updated_chunk = re.sub(html_pattern, add_lang_attr, updated_chunk, flags=re.IGNORECASE)

        # Add dir attribute to body if RTL
        if config['direction'] == 'rtl' and '<body' in chunk:
            if 'dir=' not in chunk.lower():
                body_pattern = r'<body([^>]*?)>'
                def add_dir_attr(match):
                    attrs = match.group(1)
                    attrs += ' dir="rtl"'
                    return f'<body{attrs}>'

                updated_chunk = re.sub(body_pattern, add_dir_attr, updated_chunk, flags=re.IGNORECASE)

        updated_chunks.append(updated_chunk)

    return updated_chunks


def detect_text_direction(text_sample: str) -> str:
    """Detect text direction from a sample of text content."""
    # Count RTL characters
    rtl_chars = 0
    total_chars = 0

    # Unicode ranges for RTL scripts
    rtl_ranges = [
        (0x0590, 0x05FF),  # Hebrew
        (0x0600, 0x06FF),  # Arabic
        (0x0700, 0x074F),  # Syriac
        (0x0750, 0x077F),  # Arabic Supplement
        (0x0780, 0x07BF),  # Thaana
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB1D, 0xFB4F),  # Hebrew Presentation Forms
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    ]

    for char in text_sample:
        char_code = ord(char)
        total_chars += 1

        for start, end in rtl_ranges:
            if start <= char_code <= end:
                rtl_chars += 1
                break

    if total_chars == 0:
        return 'ltr'

    # If more than 30% RTL characters, consider it RTL
    rtl_ratio = rtl_chars / total_chars
    return 'rtl' if rtl_ratio > 0.3 else 'ltr'


def create_language_summary(language_code: str, vertical_mode: bool = False) -> str:
    """Create human-readable language configuration summary."""
    config = get_language_config(language_code)

    summary = [
        f"Language: {config['name']} ({language_code})",
        f"Script: {config['script']}",
        f"Direction: {config['direction'].upper()}",
        f"Hyphenation: {'Enabled' if config['hyphenation'] else 'Disabled'}",
        f"Justification: {'Enabled' if config['justify'] else 'Disabled'}",
    ]

    if vertical_mode and supports_vertical_writing(language_code):
        summary.append("Writing Mode: Vertical")

    if config.get('font_stack'):
        summary.append(f"Font Stack: {config['font_stack']}")

    return '\n'.join(summary)