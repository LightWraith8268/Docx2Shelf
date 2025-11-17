"""
Math equation handling for EPUB generation.

Supports multiple output formats:
- MathML for readers that support it (Apple Books, etc.)
- SVG fallback for broader compatibility
- PNG/image fallback for maximum compatibility

Handles equation extraction from DOCX and conversion to appropriate formats.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class MathFormat(Enum):
    """Supported math output formats."""

    MATHML = "mathml"
    SVG = "svg"
    PNG = "png"
    AUTO = "auto"  # Choose best format based on equation complexity


@dataclass
class MathConfig:
    """Configuration for math equation processing."""

    primary_format: MathFormat = MathFormat.AUTO
    fallback_format: MathFormat = MathFormat.SVG
    include_alt_text: bool = True
    prompt_for_alt_text: bool = True
    svg_font_size: int = 16
    png_dpi: int = 150
    max_equation_width: int = 600
    max_equation_height: int = 200
    cache_equations: bool = True


@dataclass
class EquationInfo:
    """Information about a processed equation."""

    id: str
    source_latex: str
    source_mathml: str
    alt_text: str
    primary_format: MathFormat
    primary_content: str
    fallback_format: Optional[MathFormat]
    fallback_content: Optional[str]
    width: Optional[int] = None
    height: Optional[int] = None


class MathProcessor:
    """Processes mathematical equations in EPUB content."""

    def __init__(self, config: Optional[MathConfig] = None):
        self.config = config or MathConfig()
        self.equations: List[EquationInfo] = []
        self.equation_cache: Dict[str, EquationInfo] = {}

    def process_content(self, html_content: str, interactive: bool = False) -> str:
        """Process HTML content to handle mathematical equations."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available for math processing")
            return html_content

        soup = BeautifulSoup(html_content, "html.parser")

        # Find and process equations
        self._process_mathml_equations(soup, interactive)
        self._process_latex_equations(soup, interactive)
        self._process_omml_equations(soup, interactive)

        return str(soup)

    def _process_mathml_equations(self, soup, interactive: bool = False) -> None:
        """Process existing MathML equations."""
        mathml_elements = soup.find_all("math", namespace="http://www.w3.org/1998/Math/MathML")

        for math_elem in mathml_elements:
            try:
                # Extract MathML content
                mathml_content = str(math_elem)
                equation_id = self._generate_equation_id(mathml_content)

                # Get or prompt for alt text
                alt_text = self._get_equation_alt_text(
                    mathml_content, interactive, math_elem.get("alt", "")
                )

                # Determine output format
                primary_format = self._determine_format(mathml_content)

                if primary_format == MathFormat.MATHML:
                    # Keep MathML, ensure proper attributes
                    math_elem["xmlns"] = "http://www.w3.org/1998/Math/MathML"
                    if alt_text:
                        math_elem["alt"] = alt_text

                    # Create fallback if needed
                    fallback_content = None
                    fallback_format = None
                    if self.config.fallback_format != MathFormat.MATHML:
                        fallback_content, fallback_format = self._create_fallback(
                            mathml_content, self.config.fallback_format
                        )

                else:
                    # Convert to different format
                    primary_content, _ = self._create_fallback(mathml_content, primary_format)
                    self._replace_math_element(
                        soup, math_elem, primary_content, primary_format, alt_text
                    )

                # Store equation info
                equation = EquationInfo(
                    id=equation_id,
                    source_latex="",
                    source_mathml=mathml_content,
                    alt_text=alt_text,
                    primary_format=primary_format,
                    primary_content=(
                        mathml_content if primary_format == MathFormat.MATHML else primary_content
                    ),
                    fallback_format=fallback_format,
                    fallback_content=fallback_content,
                )
                self.equations.append(equation)

            except Exception as e:
                logger.warning(f"Failed to process MathML equation: {e}")

    def _process_latex_equations(self, soup, interactive: bool = False) -> None:
        """Process LaTeX equations (inline and display)."""
        # Look for LaTeX patterns
        latex_patterns = [
            (r"\$\$([^$]+)\$\$", "display"),  # Display math
            (r"\$([^$]+)\$", "inline"),  # Inline math
            (r"\\begin\{equation\}(.*?)\\end\{equation\}", "display"),
            (r"\\begin\{align\}(.*?)\\end\{align\}", "display"),
        ]

        text_content = soup.get_text()

        for pattern, math_type in latex_patterns:
            matches = re.finditer(pattern, text_content, re.DOTALL)

            for match in matches:
                latex_content = match.group(1).strip()
                equation_id = self._generate_equation_id(latex_content)

                # Get alt text
                alt_text = self._get_equation_alt_text(latex_content, interactive)

                # Convert LaTeX to target format
                primary_format = self._determine_format(latex_content)
                primary_content = self._convert_latex(latex_content, primary_format)

                # Create replacement element
                if primary_format == MathFormat.MATHML:
                    replacement = soup.new_tag("math", xmlns="http://www.w3.org/1998/Math/MathML")
                    replacement.string = primary_content
                    if alt_text:
                        replacement["alt"] = alt_text
                else:
                    replacement = self._create_non_mathml_element(
                        soup, primary_content, primary_format, alt_text
                    )

                # Find and replace in DOM (simplified - would need more robust text replacement)
                # This is a basic implementation
                self._replace_text_with_element(soup, match.group(0), replacement)

                # Store equation info
                equation = EquationInfo(
                    id=equation_id,
                    source_latex=latex_content,
                    source_mathml="",
                    alt_text=alt_text,
                    primary_format=primary_format,
                    primary_content=primary_content,
                    fallback_format=self.config.fallback_format,
                    fallback_content=None,
                )
                self.equations.append(equation)

    def _process_omml_equations(self, soup, interactive: bool = False) -> None:
        """Process Office Math Markup Language (OMML) from Word."""
        # Look for OMML elements (usually in Word-generated HTML)
        omml_elements = soup.find_all(["m:oMath", "oMath"])

        for omml_elem in omml_elements:
            try:
                omml_content = str(omml_elem)
                equation_id = self._generate_equation_id(omml_content)

                # Convert OMML to MathML (simplified conversion)
                mathml_content = self._convert_omml_to_mathml(omml_content)

                # Get alt text
                alt_text = self._get_equation_alt_text(omml_content, interactive)

                # Determine output format
                primary_format = self._determine_format(mathml_content)

                if primary_format == MathFormat.MATHML:
                    # Replace with MathML
                    math_elem = soup.new_tag("math", xmlns="http://www.w3.org/1998/Math/MathML")
                    math_elem.string = mathml_content
                    if alt_text:
                        math_elem["alt"] = alt_text
                    omml_elem.replace_with(math_elem)
                else:
                    # Convert to other format
                    primary_content, _ = self._create_fallback(mathml_content, primary_format)
                    replacement = self._create_non_mathml_element(
                        soup, primary_content, primary_format, alt_text
                    )
                    omml_elem.replace_with(replacement)

                # Store equation info
                equation = EquationInfo(
                    id=equation_id,
                    source_latex="",
                    source_mathml=mathml_content,
                    alt_text=alt_text,
                    primary_format=primary_format,
                    primary_content=(
                        mathml_content if primary_format == MathFormat.MATHML else primary_content
                    ),
                    fallback_format=None,
                    fallback_content=None,
                )
                self.equations.append(equation)

            except Exception as e:
                logger.warning(f"Failed to process OMML equation: {e}")

    def _generate_equation_id(self, content: str) -> str:
        """Generate a unique ID for an equation."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"equation-{content_hash}"

    def _determine_format(self, content: str) -> MathFormat:
        """Determine the best output format for an equation."""
        if self.config.primary_format != MathFormat.AUTO:
            return self.config.primary_format

        # Simple heuristics for format selection
        if len(content) < 50 and not any(op in content for op in ["\\frac", "\\sum", "\\int"]):
            return MathFormat.MATHML  # Simple equations work well in MathML
        elif len(content) > 200:
            return MathFormat.PNG  # Complex equations better as images
        else:
            return MathFormat.SVG  # Medium complexity as SVG

    def _get_equation_alt_text(
        self, content: str, interactive: bool, existing_alt: str = ""
    ) -> str:
        """Get alt text for an equation."""
        if existing_alt:
            return existing_alt

        if not self.config.include_alt_text:
            return ""

        if interactive and self.config.prompt_for_alt_text:
            # In a real implementation, this would prompt the user
            logger.info(f"Alt text needed for equation: {content[:50]}...")
            return f"[Mathematical equation: {content[:30]}...]"
        else:
            # Generate basic alt text
            return self._generate_alt_text(content)

    def _generate_alt_text(self, content: str) -> str:
        """Generate basic alt text from equation content."""
        # Simple LaTeX to text conversion
        replacements = {
            r"\\frac\{([^}]+)\}\{([^}]+)\}": r"\1 over \2",
            r"\\sqrt\{([^}]+)\}": r"square root of \1",
            r"\\sum": "sum",
            r"\\int": "integral",
            r"\\alpha": "alpha",
            r"\\beta": "beta",
            r"\\gamma": "gamma",
            r"\\pi": "pi",
            r"\^(\w)": r" to the power of \1",
            r"_(\w)": r" subscript \1",
        }

        alt_text = content
        for pattern, replacement in replacements.items():
            alt_text = re.sub(pattern, replacement, alt_text)

        # Clean up
        alt_text = re.sub(r"[{}\\]", "", alt_text)
        alt_text = re.sub(r"\s+", " ", alt_text).strip()

        return f"Mathematical equation: {alt_text}"

    def _convert_latex(self, latex: str, target_format: MathFormat) -> str:
        """Convert LaTeX to target format."""
        if target_format == MathFormat.MATHML:
            return self._latex_to_mathml(latex)
        elif target_format == MathFormat.SVG:
            return self._latex_to_svg(latex)
        elif target_format == MathFormat.PNG:
            return self._latex_to_png(latex)
        else:
            return latex

    def _latex_to_mathml(self, latex: str) -> str:
        """Convert LaTeX to MathML (basic implementation)."""
        # This is a simplified conversion - a real implementation would use
        # a library like latex2mathml or similar

        # Basic conversion patterns
        mathml = latex

        # Simple replacements
        replacements = {
            r"\\frac\{([^}]+)\}\{([^}]+)\}": r"<mfrac><mi>\1</mi><mi>\2</mi></mfrac>",
            r"\\sqrt\{([^}]+)\}": r"<msqrt><mi>\1</mi></msqrt>",
            r"\^([a-zA-Z0-9])": r"<msup><mi>x</mi><mi>\1</mi></msup>",
            r"_([a-zA-Z0-9])": r"<msub><mi>x</mi><mi>\1</mi></msub>",
        }

        for pattern, replacement in replacements.items():
            mathml = re.sub(pattern, replacement, mathml)

        return f'<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>{mathml}</mi></math>'

    def _latex_to_svg(self, latex: str) -> str:
        """Convert LaTeX to SVG using matplotlib."""
        try:
            import xml.etree.ElementTree as ET
            from io import StringIO

            import matplotlib.mathtext as mathtext
            import matplotlib.pyplot as plt

            # Configure matplotlib for LaTeX rendering
            plt.rcParams["mathtext.fontset"] = "cm"
            plt.rcParams["font.size"] = self.config.svg_font_size

            # Create figure with tight layout
            fig, ax = plt.subplots(figsize=(6, 2))
            ax.axis("off")

            # Render LaTeX as mathematical text
            try:
                # Try to render as math mode
                if not latex.startswith("$"):
                    latex = f"${latex}$"

                text = ax.text(
                    0.5,
                    0.5,
                    latex,
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=self.config.svg_font_size,
                )

                # Get tight bounding box
                fig.canvas.draw()
                bbox = text.get_window_extent(fig.canvas.get_renderer())
                bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())

                # Save as SVG
                svg_buffer = StringIO()
                fig.savefig(
                    svg_buffer, format="svg", bbox_inches="tight", transparent=True, pad_inches=0.1
                )
                plt.close(fig)

                svg_content = svg_buffer.getvalue()
                svg_buffer.close()

                # Clean up SVG and optimize
                root = ET.fromstring(svg_content)
                # Remove unnecessary attributes
                for elem in root.iter():
                    if "id" in elem.attrib:
                        del elem.attrib["id"]

                return ET.tostring(root, encoding="unicode")

            except Exception:
                plt.close(fig)
                # Fallback to simple text rendering
                return self._create_fallback_svg(latex)

        except ImportError:
            # Matplotlib not available, use fallback
            return self._create_fallback_svg(latex)

    def _create_fallback_svg(self, text: str) -> str:
        """Create a simple SVG fallback for math expressions."""
        # Estimate dimensions based on text length
        width = max(100, len(text) * 8)
        height = 30

        # Clean text for XML
        clean_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
            <text x="{width//2}" y="{height//2}" font-family="serif, Times, 'Times New Roman'"
                  font-size="{self.config.svg_font_size}" text-anchor="middle"
                  dominant-baseline="central">{clean_text}</text>
        </svg>"""

    def _latex_to_png(self, latex: str) -> str:
        """Convert LaTeX to PNG and return base64 data URL."""
        try:
            import base64
            from io import BytesIO

            import matplotlib.pyplot as plt

            # Configure matplotlib for LaTeX rendering
            plt.rcParams["mathtext.fontset"] = "cm"
            plt.rcParams["font.size"] = self.config.svg_font_size

            # Create figure with white background
            fig, ax = plt.subplots(figsize=(6, 2), facecolor="white")
            ax.axis("off")
            ax.set_facecolor("white")

            try:
                # Try to render as math mode
                if not latex.startswith("$"):
                    latex = f"${latex}$"

                text = ax.text(
                    0.5,
                    0.5,
                    latex,
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=self.config.svg_font_size,
                    color="black",
                )

                # Get tight bounding box
                fig.canvas.draw()
                bbox = text.get_window_extent(fig.canvas.get_renderer())
                bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())

                # Save as PNG with high DPI
                png_buffer = BytesIO()
                fig.savefig(
                    png_buffer,
                    format="png",
                    bbox_inches="tight",
                    facecolor="white",
                    edgecolor="none",
                    dpi=150,
                    pad_inches=0.1,
                )
                plt.close(fig)

                png_buffer.seek(0)
                png_data = png_buffer.getvalue()
                png_buffer.close()

                # Convert to base64 data URL
                base64_png = base64.b64encode(png_data).decode()
                return f"data:image/png;base64,{base64_png}"

            except Exception:
                plt.close(fig)
                # Return fallback
                return self._create_fallback_png(latex)

        except ImportError:
            # Matplotlib not available, use fallback
            return self._create_fallback_png(latex)

    def _create_fallback_png(self, text: str) -> str:
        """Create a fallback PNG data URL for math expressions."""
        try:
            import base64
            from io import BytesIO

            from PIL import Image, ImageDraw, ImageFont

            # Estimate image size
            width = max(200, len(text) * 12)
            height = 40

            # Create image with white background
            img = Image.new("RGB", (width, height), color="white")
            draw = ImageDraw.Draw(img)

            # Try to use a decent font
            try:
                font = ImageFont.truetype("times.ttf", self.config.svg_font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("Times New Roman.ttf", self.config.svg_font_size)
                except (OSError, IOError):
                    font = ImageFont.load_default()

            # Draw text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2

            draw.text((x, y), text, fill="black", font=font)

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            png_data = buffer.getvalue()
            buffer.close()

            base64_png = base64.b64encode(png_data).decode()
            return f"data:image/png;base64,{base64_png}"

        except ImportError:
            # PIL not available, return minimal placeholder
            placeholder_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
            base64_png = base64.b64encode(placeholder_png).decode()
            return f"data:image/png;base64,{base64_png}"

    def _convert_omml_to_mathml(self, omml: str) -> str:
        """Convert OMML (Office Math Markup Language) to MathML."""
        try:
            import xml.etree.ElementTree as ET

            # Parse OMML XML
            root = ET.fromstring(omml)

            # OMML namespace
            ns = {"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}

            # Create MathML root
            mathml_parts = ['<math xmlns="http://www.w3.org/1998/Math/MathML">']

            # Process OMML elements
            for elem in root.iter():
                local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

                # Map common OMML elements to MathML
                if local_name == "oMath":
                    continue  # Root element
                elif local_name == "f":  # Fraction
                    mathml_parts.append("<mfrac>")
                elif local_name == "num":  # Numerator
                    mathml_parts.append("<mn>")
                    if elem.text:
                        mathml_parts.append(self._escape_xml(elem.text))
                    mathml_parts.append("</mn>")
                elif local_name == "den":  # Denominator
                    mathml_parts.append("<mn>")
                    if elem.text:
                        mathml_parts.append(self._escape_xml(elem.text))
                    mathml_parts.append("</mn>")
                elif local_name == "sup":  # Superscript
                    mathml_parts.append("<msup>")
                elif local_name == "sub":  # Subscript
                    mathml_parts.append("<msub>")
                elif local_name == "r":  # Run (text)
                    # Extract text from run
                    text_content = "".join(elem.itertext())
                    if text_content.strip():
                        # Determine if it's a number, identifier, or operator
                        if text_content.strip().isdigit():
                            mathml_parts.append(f"<mn>{self._escape_xml(text_content)}</mn>")
                        elif text_content.strip() in "+-*/=<>()[]{}":
                            mathml_parts.append(f"<mo>{self._escape_xml(text_content)}</mo>")
                        else:
                            mathml_parts.append(f"<mi>{self._escape_xml(text_content)}</mi>")

            # Close fraction, superscript, subscript elements
            if "</mfrac>" in "".join(mathml_parts[-10:]):
                mathml_parts.append("</mfrac>")
            if "<msup>" in "".join(mathml_parts[-10:]):
                mathml_parts.append("</msup>")
            if "<msub>" in "".join(mathml_parts[-10:]):
                mathml_parts.append("</msub>")

            mathml_parts.append("</math>")

            mathml = "".join(mathml_parts)

            # Clean up malformed MathML
            mathml = self._clean_mathml(mathml)

            return mathml

        except Exception:
            # Fallback: extract text and convert as simple expression
            try:
                root = ET.fromstring(omml)
                text_content = "".join(root.itertext()).strip()
                return (
                    self._latex_to_mathml(text_content)
                    if text_content
                    else '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>?</mi></math>'
                )
            except ET.ParseError:
                return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>?</mi></math>'

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _clean_mathml(self, mathml: str) -> str:
        """Clean up malformed MathML."""
        try:
            # Parse and reformat to ensure well-formed XML
            root = ET.fromstring(mathml)
            return ET.tostring(root, encoding="unicode")
        except ET.ParseError:
            # If parsing fails, return a basic fallback
            return '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>?</mi></math>'

    def _create_fallback(
        self, mathml_content: str, fallback_format: MathFormat
    ) -> Tuple[str, MathFormat]:
        """Create fallback content in specified format."""
        if fallback_format == MathFormat.SVG:
            return self._mathml_to_svg(mathml_content), MathFormat.SVG
        elif fallback_format == MathFormat.PNG:
            return self._mathml_to_png(mathml_content), MathFormat.PNG
        else:
            return mathml_content, MathFormat.MATHML

    def _mathml_to_svg(self, mathml: str) -> str:
        """Convert MathML to SVG."""
        # Extract text for basic SVG rendering
        try:
            root = ET.fromstring(mathml)
            text_content = "".join(root.itertext())
            return self._latex_to_svg(text_content)
        except ET.ParseError:
            return self._latex_to_svg(mathml)

    def _mathml_to_png(self, mathml: str) -> str:
        """Convert MathML to PNG data URL."""
        try:
            root = ET.fromstring(mathml)
            text_content = "".join(root.itertext())
            return self._latex_to_png(text_content)
        except ET.ParseError:
            return self._latex_to_png(mathml)

    def _create_non_mathml_element(
        self, soup, content: str, format_type: MathFormat, alt_text: str
    ):
        """Create HTML element for non-MathML formats."""
        if format_type == MathFormat.SVG:
            # Parse SVG content and insert
            try:
                svg_soup = BeautifulSoup(content, "xml")
                svg_elem = svg_soup.find("svg")
                if alt_text:
                    svg_elem["aria-label"] = alt_text
                return svg_elem
            except (ValueError, TypeError, AttributeError):
                # Fallback to text
                span = soup.new_tag("span", **{"class": "math-svg"})
                span.string = content
                return span

        elif format_type == MathFormat.PNG:
            img = soup.new_tag("img", src=content, **{"class": "math-image"})
            if alt_text:
                img["alt"] = alt_text
            return img

        else:
            # Generic span
            span = soup.new_tag("span", **{"class": "math-equation"})
            span.string = content
            if alt_text:
                span["title"] = alt_text
            return span

    def _replace_math_element(
        self, soup, old_elem, new_content: str, format_type: MathFormat, alt_text: str
    ) -> None:
        """Replace a math element with new content."""
        new_elem = self._create_non_mathml_element(soup, new_content, format_type, alt_text)
        old_elem.replace_with(new_elem)

    def _replace_text_with_element(self, soup, text: str, element) -> None:
        """Replace text content with an element."""
        # Find and replace text in the soup
        for text_node in soup.find_all(string=True):
            if text in text_node:
                # Split the text node and insert the element
                parts = text_node.split(text)
                if len(parts) > 1:
                    # Replace the text node with parts and the element
                    parent = text_node.parent
                    if parent:
                        # Insert the first part
                        if parts[0]:
                            parent.insert_before(soup.new_string(parts[0]), text_node)

                        # Insert the element
                        parent.insert_before(element, text_node)

                        # Insert the remaining parts
                        remaining_text = text.join(parts[1:])
                        if remaining_text:
                            parent.insert_before(soup.new_string(remaining_text), text_node)

                        # Remove the original text node
                        text_node.extract()
                        break

    def get_equation_count(self) -> int:
        """Get the total number of equations processed."""
        return len(self.equations)

    def get_equations_by_format(self, format_type: MathFormat) -> List[EquationInfo]:
        """Get equations using a specific format."""
        return [eq for eq in self.equations if eq.primary_format == format_type]

    def generate_math_css(self) -> str:
        """Generate CSS for math rendering."""
        css = """
/* Math equation styling */
.math-equation {
    font-family: "Times New Roman", Times, serif;
    font-style: italic;
    display: inline;
}

.math-image {
    vertical-align: middle;
    max-width: 100%;
    height: auto;
}

.math-svg {
    vertical-align: middle;
    display: inline-block;
}

/* MathML fallback styling */
math {
    font-family: "Times New Roman", Times, serif;
    font-size: 1em;
    display: inline;
}

math[display="block"] {
    display: block;
    text-align: center;
    margin: 1em 0;
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
    .math-svg {
        animation: none;
    }
}
"""
        return css


def process_math_equations(
    html_content: str, config: Optional[MathConfig] = None, interactive: bool = False
) -> Tuple[str, MathProcessor]:
    """
    Process mathematical equations in HTML content.

    Args:
        html_content: HTML content containing equations
        config: Math processing configuration
        interactive: Whether to prompt for alt text

    Returns:
        Tuple of (processed_html, math_processor)
    """
    processor = MathProcessor(config)
    processed_html = processor.process_content(html_content, interactive)
    return processed_html, processor
