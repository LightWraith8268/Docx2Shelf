"""
Advanced typography controls for EPUB generation.

This module provides fine-grained control over typography, including:
- Custom font stacks and web font loading
- Advanced spacing and layout controls
- OpenType feature support
- Responsive typography for different screen sizes
- Professional typographic best practices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class FontWeight(Enum):
    """Standard font weight values."""

    THIN = "100"
    EXTRA_LIGHT = "200"
    LIGHT = "300"
    NORMAL = "400"
    MEDIUM = "500"
    SEMI_BOLD = "600"
    BOLD = "700"
    EXTRA_BOLD = "800"
    BLACK = "900"


class FontStyle(Enum):
    """Font style options."""

    NORMAL = "normal"
    ITALIC = "italic"
    OBLIQUE = "oblique"


class TextAlign(Enum):
    """Text alignment options."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    JUSTIFY = "justify"
    START = "start"
    END = "end"


class OpenTypeFeature(Enum):
    """Common OpenType features."""

    LIGATURES = "liga"
    DISCRETIONARY_LIGATURES = "dlig"
    CONTEXTUAL_ALTERNATES = "calt"
    SWASH = "swsh"
    STYLISTIC_ALTERNATES = "salt"
    SMALL_CAPS = "smcp"
    ALL_SMALL_CAPS = "c2sc"
    PETITE_CAPS = "pcap"
    ALL_PETITE_CAPS = "c2pc"
    LINING_NUMS = "lnum"
    OLDSTYLE_NUMS = "onum"
    PROPORTIONAL_NUMS = "pnum"
    TABULAR_NUMS = "tnum"
    SLASHED_ZERO = "zero"
    ORDINALS = "ordn"
    SUPERSCRIPT = "sups"
    SUBSCRIPT = "subs"


@dataclass
class FontFace:
    """Represents a font face with all its properties."""

    family: str
    weight: FontWeight = FontWeight.NORMAL
    style: FontStyle = FontStyle.NORMAL
    file_path: Optional[Path] = None
    format: Optional[str] = None  # woff2, woff, truetype, etc.
    unicode_range: Optional[str] = None
    display: str = "swap"  # font-display property


@dataclass
class TypographyScale:
    """Typographic scale for consistent sizing."""

    base_size: str = "1rem"
    scale_ratio: float = 1.25  # Major third
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None
    h4: Optional[str] = None
    h5: Optional[str] = None
    h6: Optional[str] = None
    body: Optional[str] = None
    small: Optional[str] = None
    caption: Optional[str] = None

    def __post_init__(self):
        """Calculate scale sizes if not explicitly set."""
        if not self.h1:
            self.h1 = f"{self.scale_ratio ** 3:.3f}rem"
        if not self.h2:
            self.h2 = f"{self.scale_ratio ** 2:.3f}rem"
        if not self.h3:
            self.h3 = f"{self.scale_ratio ** 1:.3f}rem"
        if not self.h4:
            self.h4 = self.base_size
        if not self.h5:
            self.h5 = f"{1 / self.scale_ratio:.3f}rem"
        if not self.h6:
            self.h6 = f"{1 / (self.scale_ratio ** 2):.3f}rem"
        if not self.body:
            self.body = self.base_size
        if not self.small:
            self.small = f"{1 / self.scale_ratio:.3f}rem"
        if not self.caption:
            self.caption = f"{1 / (self.scale_ratio ** 2):.3f}rem"


@dataclass
class SpacingScale:
    """Spacing scale for consistent margins and padding."""

    base_unit: str = "1rem"
    xs: str = "0.25rem"
    sm: str = "0.5rem"
    md: str = "1rem"
    lg: str = "1.5rem"
    xl: str = "2rem"
    xxl: str = "3rem"
    xxxl: str = "4rem"


@dataclass
class AdvancedTypography:
    """Advanced typography configuration."""

    # Font settings
    font_faces: List[FontFace] = field(default_factory=list)
    primary_font_stack: List[str] = field(default_factory=lambda: ["Georgia", "serif"])
    heading_font_stack: List[str] = field(default_factory=lambda: ["system-ui", "sans-serif"])
    code_font_stack: List[str] = field(default_factory=lambda: ["'SF Mono'", "Monaco", "monospace"])

    # Typography scales
    typography_scale: TypographyScale = field(default_factory=TypographyScale)
    spacing_scale: SpacingScale = field(default_factory=SpacingScale)

    # Line height settings
    base_line_height: float = 1.6
    heading_line_height: float = 1.2
    code_line_height: float = 1.4

    # Letter spacing
    base_letter_spacing: str = "normal"
    heading_letter_spacing: str = "-0.02em"
    small_caps_letter_spacing: str = "0.1em"

    # Paragraph settings
    paragraph_spacing: str = "1.25em"
    paragraph_indent: str = "0"
    first_line_indent: str = "1.5em"

    # OpenType features
    opentype_features: List[OpenTypeFeature] = field(
        default_factory=lambda: [
            OpenTypeFeature.LIGATURES,
            OpenTypeFeature.CONTEXTUAL_ALTERNATES,
            OpenTypeFeature.LINING_NUMS,
        ]
    )

    # Hyphenation and justification
    hyphenation: bool = True
    hyphenate_limit_chars: str = "6 3 2"  # word chars, before, after
    hyphenate_limit_lines: int = 2
    hyphenate_limit_zone: str = "8%"

    # Text rendering optimizations
    text_rendering: str = "optimizeLegibility"
    font_smoothing: str = "antialiased"
    font_variant_ligatures: str = "common-ligatures"

    # Reading experience
    optimal_line_length: str = "65ch"  # characters per line
    reading_margin: str = "auto"

    # Responsive settings
    mobile_scale_factor: float = 0.9
    tablet_scale_factor: float = 0.95

    # Accessibility
    focus_outline_width: str = "2px"
    focus_outline_style: str = "solid"
    focus_outline_color: str = "#0066cc"
    high_contrast_ratio: float = 7.0  # WCAG AAA standard


def generate_font_face_css(font_face: FontFace) -> str:
    """Generate CSS @font-face declaration."""
    css_parts = ["@font-face {"]
    css_parts.append(f"  font-family: '{font_face.family}';")

    if font_face.file_path:
        format_hint = f" format('{font_face.format}')" if font_face.format else ""
        css_parts.append(f"  src: url('{font_face.file_path}'){format_hint};")

    css_parts.append(f"  font-weight: {font_face.weight.value};")
    css_parts.append(f"  font-style: {font_face.style.value};")
    css_parts.append(f"  font-display: {font_face.display};")

    if font_face.unicode_range:
        css_parts.append(f"  unicode-range: {font_face.unicode_range};")

    css_parts.append("}")
    return "\n".join(css_parts)


def generate_opentype_features_css(features: List[OpenTypeFeature]) -> str:
    """Generate CSS for OpenType features."""
    if not features:
        return ""

    feature_strings = [f'"{feature.value}"' for feature in features]
    return f"font-feature-settings: {', '.join(feature_strings)};"


def generate_typography_css(typography: AdvancedTypography) -> str:
    """Generate complete typography CSS."""
    css_parts = []

    # CSS Custom Properties (Variables)
    css_parts.append(":root {")
    css_parts.append("  /* Typography Scale */")
    css_parts.append(f"  --font-size-h1: {typography.typography_scale.h1};")
    css_parts.append(f"  --font-size-h2: {typography.typography_scale.h2};")
    css_parts.append(f"  --font-size-h3: {typography.typography_scale.h3};")
    css_parts.append(f"  --font-size-h4: {typography.typography_scale.h4};")
    css_parts.append(f"  --font-size-h5: {typography.typography_scale.h5};")
    css_parts.append(f"  --font-size-h6: {typography.typography_scale.h6};")
    css_parts.append(f"  --font-size-body: {typography.typography_scale.body};")
    css_parts.append(f"  --font-size-small: {typography.typography_scale.small};")
    css_parts.append("")
    css_parts.append("  /* Spacing Scale */")
    css_parts.append(f"  --space-xs: {typography.spacing_scale.xs};")
    css_parts.append(f"  --space-sm: {typography.spacing_scale.sm};")
    css_parts.append(f"  --space-md: {typography.spacing_scale.md};")
    css_parts.append(f"  --space-lg: {typography.spacing_scale.lg};")
    css_parts.append(f"  --space-xl: {typography.spacing_scale.xl};")
    css_parts.append(f"  --space-xxl: {typography.spacing_scale.xxl};")
    css_parts.append("")
    css_parts.append("  /* Font Stacks */")
    primary_stack = ", ".join(
        f"'{font}'" if " " in font else font for font in typography.primary_font_stack
    )
    heading_stack = ", ".join(
        f"'{font}'" if " " in font else font for font in typography.heading_font_stack
    )
    code_stack = ", ".join(
        f"'{font}'" if " " in font else font for font in typography.code_font_stack
    )
    css_parts.append(f"  --font-primary: {primary_stack};")
    css_parts.append(f"  --font-heading: {heading_stack};")
    css_parts.append(f"  --font-code: {code_stack};")
    css_parts.append("")
    css_parts.append("  /* Line Heights */")
    css_parts.append(f"  --line-height-base: {typography.base_line_height};")
    css_parts.append(f"  --line-height-heading: {typography.heading_line_height};")
    css_parts.append(f"  --line-height-code: {typography.code_line_height};")
    css_parts.append("}")
    css_parts.append("")

    # Font face declarations
    if typography.font_faces:
        css_parts.append("/* Custom Font Faces */")
        for font_face in typography.font_faces:
            css_parts.append(generate_font_face_css(font_face))
            css_parts.append("")

    # Base typography
    css_parts.append("/* Base Typography */")
    css_parts.append("html {")
    css_parts.append(f"  font-size: {typography.typography_scale.base_size};")
    css_parts.append("}")
    css_parts.append("")

    css_parts.append("body {")
    css_parts.append("  font-family: var(--font-primary);")
    css_parts.append("  font-size: var(--font-size-body);")
    css_parts.append("  line-height: var(--line-height-base);")
    css_parts.append(f"  letter-spacing: {typography.base_letter_spacing};")
    css_parts.append(f"  text-rendering: {typography.text_rendering};")
    css_parts.append(f"  -webkit-font-smoothing: {typography.font_smoothing};")
    css_parts.append("  -moz-osx-font-smoothing: grayscale;")

    if typography.opentype_features:
        css_parts.append(f"  {generate_opentype_features_css(typography.opentype_features)}")

    if typography.hyphenation:
        css_parts.append("  hyphens: auto;")
        css_parts.append("  hyphenate-limit-chars: var(--hyphenate-limit-chars, 6 3 2);")

    css_parts.append("}")
    css_parts.append("")

    # Headings
    css_parts.append("/* Headings */")
    css_parts.append("h1, h2, h3, h4, h5, h6 {")
    css_parts.append("  font-family: var(--font-heading);")
    css_parts.append("  line-height: var(--line-height-heading);")
    css_parts.append(f"  letter-spacing: {typography.heading_letter_spacing};")
    css_parts.append("  margin-bottom: var(--space-md);")
    css_parts.append("}")
    css_parts.append("")

    for i, tag in enumerate(["h1", "h2", "h3", "h4", "h5", "h6"], 1):
        css_parts.append(f"{tag} {{ font-size: var(--font-size-{tag}); }}")
    css_parts.append("")

    # Paragraphs
    css_parts.append("/* Paragraphs */")
    css_parts.append("p {")
    css_parts.append(f"  margin-bottom: {typography.paragraph_spacing};")
    css_parts.append(f"  text-indent: {typography.paragraph_indent};")
    css_parts.append(f"  max-width: {typography.optimal_line_length};")
    css_parts.append("}")
    css_parts.append("")

    css_parts.append("p:first-child,")
    css_parts.append("h1 + p, h2 + p, h3 + p, h4 + p, h5 + p, h6 + p {")
    css_parts.append("  text-indent: 0;")
    css_parts.append("}")
    css_parts.append("")

    if typography.first_line_indent != "0":
        css_parts.append("p + p {")
        css_parts.append(f"  text-indent: {typography.first_line_indent};")
        css_parts.append("}")
        css_parts.append("")

    # Code and preformatted text
    css_parts.append("/* Code */")
    css_parts.append("code, pre, kbd, samp {")
    css_parts.append("  font-family: var(--font-code);")
    css_parts.append("  line-height: var(--line-height-code);")
    css_parts.append("}")
    css_parts.append("")

    # Responsive adjustments
    css_parts.append("/* Responsive Typography */")
    css_parts.append("@media screen and (max-width: 768px) {")
    css_parts.append("  html {")
    css_parts.append(
        f"    font-size: calc({typography.typography_scale.base_size} * {typography.mobile_scale_factor});"
    )
    css_parts.append("  }")
    css_parts.append("}")
    css_parts.append("")

    css_parts.append("@media screen and (min-width: 769px) and (max-width: 1024px) {")
    css_parts.append("  html {")
    css_parts.append(
        f"    font-size: calc({typography.typography_scale.base_size} * {typography.tablet_scale_factor});"
    )
    css_parts.append("  }")
    css_parts.append("}")
    css_parts.append("")

    # Accessibility
    css_parts.append("/* Accessibility */")
    css_parts.append("*:focus {")
    css_parts.append(
        f"  outline: {typography.focus_outline_width} {typography.focus_outline_style} {typography.focus_outline_color};"
    )
    css_parts.append("  outline-offset: 2px;")
    css_parts.append("}")
    css_parts.append("")

    css_parts.append("@media (prefers-reduced-motion: reduce) {")
    css_parts.append("  * {")
    css_parts.append("    animation-duration: 0.01ms !important;")
    css_parts.append("    animation-iteration-count: 1 !important;")
    css_parts.append("    transition-duration: 0.01ms !important;")
    css_parts.append("  }")
    css_parts.append("}")
    css_parts.append("")

    css_parts.append("@media (prefers-contrast: high) {")
    css_parts.append("  body {")
    css_parts.append("    background: white;")
    css_parts.append("    color: black;")
    css_parts.append("  }")
    css_parts.append("}")

    return "\n".join(css_parts)


def create_professional_typography() -> AdvancedTypography:
    """Create a professional typography configuration."""
    return AdvancedTypography(
        primary_font_stack=["Charter", "Georgia", "Cambria", "serif"],
        heading_font_stack=["Avenir Next", "Helvetica Neue", "Arial", "sans-serif"],
        typography_scale=TypographyScale(base_size="18px", scale_ratio=1.25),
        base_line_height=1.7,
        paragraph_spacing="1.5em",
        first_line_indent="1.5em",
        opentype_features=[
            OpenTypeFeature.LIGATURES,
            OpenTypeFeature.CONTEXTUAL_ALTERNATES,
            OpenTypeFeature.OLDSTYLE_NUMS,
        ],
    )


def create_modern_typography() -> AdvancedTypography:
    """Create a modern typography configuration."""
    return AdvancedTypography(
        primary_font_stack=["Inter", "system-ui", "sans-serif"],
        heading_font_stack=["Inter", "system-ui", "sans-serif"],
        typography_scale=TypographyScale(base_size="16px", scale_ratio=1.2),
        base_line_height=1.6,
        paragraph_spacing="1.25em",
        paragraph_indent="0",
        heading_letter_spacing="-0.01em",
        opentype_features=[
            OpenTypeFeature.LIGATURES,
            OpenTypeFeature.CONTEXTUAL_ALTERNATES,
            OpenTypeFeature.LINING_NUMS,
            OpenTypeFeature.TABULAR_NUMS,
        ],
    )


def create_academic_typography() -> AdvancedTypography:
    """Create an academic typography configuration."""
    return AdvancedTypography(
        primary_font_stack=["Minion Pro", "Adobe Garamond Pro", "Garamond", "serif"],
        heading_font_stack=["Minion Pro", "Adobe Garamond Pro", "Garamond", "serif"],
        code_font_stack=["Source Code Pro", "Consolas", "Monaco", "monospace"],
        typography_scale=TypographyScale(base_size="12pt", scale_ratio=1.2),
        base_line_height=1.5,
        paragraph_spacing="1em",
        first_line_indent="1.5em",
        opentype_features=[
            OpenTypeFeature.LIGATURES,
            OpenTypeFeature.CONTEXTUAL_ALTERNATES,
            OpenTypeFeature.OLDSTYLE_NUMS,
            OpenTypeFeature.SMALL_CAPS,
        ],
    )
