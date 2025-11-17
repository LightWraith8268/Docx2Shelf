"""
Content security utilities for sanitizing HTML, SVG, and other content.

This module provides utilities for:
- Stripping dangerous JavaScript and event handlers from HTML
- Sanitizing SVG content to remove scripts and unsafe elements
- Path traversal protection for file operations
- Content validation and safety checks
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from .path_utils import is_safe_path, normalize_path

# Dangerous HTML tags that should be removed
DANGEROUS_HTML_TAGS = {
    "script",
    "object",
    "embed",
    "applet",
    "iframe",
    "frame",
    "frameset",
    "meta",
    "link",
    "style",
    "base",
    "form",
    "input",
    "button",
    "textarea",
    "select",
    "option",
    "video",
    "audio",
    "source",
    "track",
}

# Dangerous HTML attributes that should be removed
DANGEROUS_HTML_ATTRS = {
    "onload",
    "onunload",
    "onclick",
    "ondblclick",
    "onmousedown",
    "onmouseup",
    "onmouseover",
    "onmousemove",
    "onmouseout",
    "onfocus",
    "onblur",
    "onkeypress",
    "onkeydown",
    "onkeyup",
    "onsubmit",
    "onreset",
    "onselect",
    "onchange",
    "onabort",
    "onerror",
    "onresize",
    "onscroll",
    "onbeforeunload",
    "oncontextmenu",
    "ondrag",
    "ondragend",
    "ondragenter",
    "ondragleave",
    "ondragover",
    "ondragstart",
    "ondrop",
    "oninput",
    "oninvalid",
    "onpointerdown",
    "onpointerup",
    "onpointercancel",
    "onpointermove",
    "onpointerover",
    "onpointerout",
    "onpointerenter",
    "onpointerleave",
    "ongotpointercapture",
    "onlostpointercapture",
    "onwheel",
    "ontouchstart",
    "ontouchend",
    "ontouchmove",
    "ontouchcancel",
    "onanimationstart",
    "onanimationend",
    "onanimationiteration",
    "ontransitionend",
    "javascript:",
    "data:",
    "vbscript:",
    "livescript:",
    "mocha:",
}

# Dangerous SVG elements that should be removed
DANGEROUS_SVG_ELEMENTS = {
    "script",
    "foreignObject",
    "animation",
    "animateTransform",
    "animate",
    "set",
    "animateMotion",
    "animateColor",
    "feColorMatrix",
    "feComponentTransfer",
    "feComposite",
    "feConvolveMatrix",
    "feDiffuseLighting",
    "feDisplacementMap",
    "feDistantLight",
    "feFlood",
    "feFuncA",
    "feFuncB",
    "feFuncG",
    "feFuncR",
    "feGaussianBlur",
    "feImage",
    "feMerge",
    "feMergeNode",
    "feMorphology",
    "feOffset",
    "fePointLight",
    "feSpecularLighting",
    "feSpotLight",
    "feTile",
    "feTurbulence",
}

# Safe SVG elements that are allowed
SAFE_SVG_ELEMENTS = {
    "svg",
    "g",
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "text",
    "tspan",
    "textPath",
    "defs",
    "clipPath",
    "mask",
    "marker",
    "symbol",
    "use",
    "image",
    "switch",
    "metadata",
    "title",
    "desc",
}

# Safe SVG attributes
SAFE_SVG_ATTRS = {
    "id",
    "class",
    "style",
    "x",
    "y",
    "width",
    "height",
    "viewBox",
    "preserveAspectRatio",
    "d",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-dasharray",
    "stroke-dashoffset",
    "opacity",
    "fill-opacity",
    "stroke-opacity",
    "transform",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "x1",
    "y1",
    "x2",
    "y2",
    "points",
    "font-family",
    "font-size",
    "font-weight",
    "text-anchor",
    "dominant-baseline",
    "alignment-baseline",
    "clip-path",
    "mask",
    "marker-start",
    "marker-mid",
    "marker-end",
    "href",
    "xlink:href",
    "xmlns",
    "xmlns:xlink",
    "version",
}


class ContentSanitizer:
    """Sanitizes HTML and SVG content to remove dangerous elements."""

    def __init__(self, strict_mode: bool = True):
        """
        Initialize content sanitizer.

        Args:
            strict_mode: If True, removes more potentially dangerous content
        """
        self.strict_mode = strict_mode
        self.removed_elements: List[str] = []
        self.modified_attributes: List[str] = []

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content by removing dangerous elements and attributes.

        Args:
            html_content: Raw HTML content to sanitize

        Returns:
            Sanitized HTML content
        """
        if not html_content or not html_content.strip():
            return html_content

        # Reset tracking
        self.removed_elements.clear()
        self.modified_attributes.clear()

        # Remove dangerous script content first
        html_content = self._remove_script_content(html_content)

        # Remove dangerous attributes using regex
        html_content = self._remove_dangerous_attributes(html_content)

        # Remove dangerous tags
        html_content = self._remove_dangerous_tags(html_content)

        # Sanitize URLs in remaining attributes
        html_content = self._sanitize_urls(html_content)

        # Clean up malformed HTML
        html_content = self._clean_malformed_html(html_content)

        return html_content

    def sanitize_svg(self, svg_content: str) -> str:
        """
        Sanitize SVG content by removing dangerous elements and scripts.

        Args:
            svg_content: Raw SVG content to sanitize

        Returns:
            Sanitized SVG content
        """
        if not svg_content or not svg_content.strip():
            return svg_content

        try:
            # Parse SVG as XML
            root = ET.fromstring(svg_content)
            self._sanitize_svg_element(root)

            # Convert back to string
            return ET.tostring(root, encoding="unicode")
        except ET.ParseError:
            # If parsing fails, fall back to regex-based cleaning
            return self._sanitize_svg_fallback(svg_content)

    def _remove_script_content(self, content: str) -> str:
        """Remove script tags and their content."""
        # Remove script tags (case insensitive)
        script_pattern = r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>"
        content = re.sub(script_pattern, "", content, flags=re.IGNORECASE | re.DOTALL)

        # Remove javascript: URLs
        content = re.sub(r'javascript\s*:[^"\'\s>]*', "", content, flags=re.IGNORECASE)

        # Remove vbscript: URLs
        content = re.sub(r'vbscript\s*:[^"\'\s>]*', "", content, flags=re.IGNORECASE)

        # Remove data: URLs with javascript
        content = re.sub(r'data\s*:[^,]*javascript[^"\'\s>]*', "", content, flags=re.IGNORECASE)

        return content

    def _remove_dangerous_attributes(self, content: str) -> str:
        """Remove dangerous HTML attributes."""
        for attr in DANGEROUS_HTML_ATTRS:
            if attr.endswith(":"):
                # Handle URL schemes
                pattern = rf'{re.escape(attr)}[^"\'\s>]*'
            else:
                # Handle event attributes
                pattern = rf'\s{re.escape(attr)}\s*=\s*["\'][^"\']*["\']'

            old_content = content
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

            if old_content != content:
                self.modified_attributes.append(attr)

        return content

    def _remove_dangerous_tags(self, content: str) -> str:
        """Remove dangerous HTML tags."""
        for tag in DANGEROUS_HTML_TAGS:
            # Remove opening and closing tags
            pattern_open = rf"<{re.escape(tag)}\b[^>]*>"
            pattern_close = rf"</{re.escape(tag)}>"
            pattern_self_close = rf"<{re.escape(tag)}\b[^>]*/>"

            old_content = content
            content = re.sub(pattern_open, "", content, flags=re.IGNORECASE)
            content = re.sub(pattern_close, "", content, flags=re.IGNORECASE)
            content = re.sub(pattern_self_close, "", content, flags=re.IGNORECASE)

            if old_content != content:
                self.removed_elements.append(tag)

        return content

    def _sanitize_urls(self, content: str) -> str:
        """Sanitize URLs in href and src attributes."""

        def sanitize_url_match(match):
            attr_name = match.group(1)
            quote_char = match.group(2)
            url = match.group(3)

            # Parse URL
            try:
                parsed = urlparse(url)
                scheme = parsed.scheme.lower()

                # Allow only safe schemes
                safe_schemes = {"http", "https", "mailto", "ftp", "ftps", "#", ""}
                if scheme not in safe_schemes:
                    self.modified_attributes.append(f"{attr_name}={url}")
                    return f"{attr_name}={quote_char}{quote_char}"

                return match.group(0)
            except Exception:
                # If URL parsing fails, remove it
                self.modified_attributes.append(f"{attr_name}={url}")
                return f"{attr_name}={quote_char}{quote_char}"

        # Match href and src attributes
        url_pattern = r"(href|src)\s*=\s*([\"\'])([^\"\']*)\2"
        content = re.sub(url_pattern, sanitize_url_match, content, flags=re.IGNORECASE)

        return content

    def _clean_malformed_html(self, content: str) -> str:
        """Clean up malformed HTML."""
        # Remove comments that might contain scripts
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # Remove CDATA sections that might contain scripts
        content = re.sub(r"<!\[CDATA\[.*?\]\]>", "", content, flags=re.DOTALL)

        # Escape any remaining < or > that aren't part of valid tags
        # This is a simple approach - more sophisticated parsing might be needed
        content = re.sub(r"<(?!/?\w+[^>]*>)", "&lt;", content)

        return content

    def _sanitize_svg_element(self, element: ET.Element) -> None:
        """Recursively sanitize an SVG element."""
        # Remove dangerous elements
        if element.tag.split("}")[-1] in DANGEROUS_SVG_ELEMENTS:
            # Mark for removal by clearing it
            element.clear()
            element.tag = "removed"
            return

        # Clean attributes
        attrs_to_remove = []
        for attr_name, attr_value in element.attrib.items():
            # Remove event handlers
            if attr_name.lower().startswith("on"):
                attrs_to_remove.append(attr_name)
                continue

            # Check for script content in attributes
            if isinstance(attr_value, str):
                attr_lower = attr_value.lower()
                if (
                    "javascript:" in attr_lower
                    or "vbscript:" in attr_lower
                    or "data:" in attr_lower
                    and "javascript" in attr_lower
                ):
                    attrs_to_remove.append(attr_name)
                    continue

        # Remove dangerous attributes
        for attr in attrs_to_remove:
            del element.attrib[attr]
            self.modified_attributes.append(attr)

        # Recursively process children
        children_to_remove = []
        for child in element:
            if child.tag == "removed":
                children_to_remove.append(child)
            else:
                self._sanitize_svg_element(child)

        # Remove marked children
        for child in children_to_remove:
            element.remove(child)
            self.removed_elements.append(child.tag)

    def _sanitize_svg_fallback(self, svg_content: str) -> str:
        """Fallback SVG sanitization using regex."""
        # Remove script elements
        script_pattern = r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>"
        svg_content = re.sub(script_pattern, "", svg_content, flags=re.IGNORECASE | re.DOTALL)

        # Remove dangerous elements
        for element in DANGEROUS_SVG_ELEMENTS:
            pattern = rf"<{re.escape(element)}\b[^>]*(?:/>|>.*?</{re.escape(element)}>)"
            svg_content = re.sub(pattern, "", svg_content, flags=re.IGNORECASE | re.DOTALL)

        # Remove event handlers
        for attr in DANGEROUS_HTML_ATTRS:
            if not attr.endswith(":"):
                pattern = rf'\s{re.escape(attr)}\s*=\s*["\'][^"\']*["\']'
                svg_content = re.sub(pattern, "", svg_content, flags=re.IGNORECASE)

        return svg_content

    def get_sanitization_report(self) -> Dict[str, List[str]]:
        """Get a report of what was sanitized."""
        return {
            "removed_elements": list(set(self.removed_elements)),
            "modified_attributes": list(set(self.modified_attributes)),
        }


def sanitize_file_content(
    file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None
) -> Dict[str, any]:
    """
    Sanitize content in a file.

    Args:
        file_path: Path to file to sanitize
        output_path: Optional output path (overwrites input if not provided)

    Returns:
        Dictionary with sanitization results and report
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate path safety
    if not is_safe_path(file_path):
        raise ValueError(f"Unsafe file path: {file_path}")

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise ValueError(f"Cannot read file {file_path}: {e}")

    # Determine file type and sanitize accordingly
    suffix = file_path.suffix.lower()
    sanitizer = ContentSanitizer()

    if suffix in {".html", ".htm", ".xhtml"}:
        sanitized_content = sanitizer.sanitize_html(content)
    elif suffix in {".svg"}:
        sanitized_content = sanitizer.sanitize_svg(content)
    else:
        # For other file types, do basic sanitization
        sanitized_content = sanitizer.sanitize_html(content)

    # Write sanitized content
    output_file = Path(output_path) if output_path else file_path
    if not is_safe_path(output_file):
        raise ValueError(f"Unsafe output path: {output_file}")

    try:
        output_file.write_text(sanitized_content, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Cannot write to {output_file}: {e}")

    return {
        "input_file": str(file_path),
        "output_file": str(output_file),
        "original_size": len(content),
        "sanitized_size": len(sanitized_content),
        "report": sanitizer.get_sanitization_report(),
    }


def validate_resource_path(resource_path: Union[str, Path], base_path: Union[str, Path]) -> bool:
    """
    Validate that a resource path is safe and within the allowed base directory.

    Args:
        resource_path: Path to validate
        base_path: Base directory that should contain the resource

    Returns:
        True if path is safe
    """
    try:
        resource_path = normalize_path(Path(resource_path))
        base_path = normalize_path(Path(base_path))

        # Check basic path safety
        if not is_safe_path(resource_path, base_path):
            return False

        # Additional checks for resource files
        # Don't allow hidden files
        if resource_path.name.startswith("."):
            return False

        # Don't allow executable extensions
        dangerous_extensions = {
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".scr",
            ".pif",
            ".js",
            ".vbs",
            ".jar",
        }
        if resource_path.suffix.lower() in dangerous_extensions:
            return False

        return True
    except Exception:
        return False


def scan_content_for_threats(content: str) -> List[Dict[str, str]]:
    """
    Scan content for potential security threats.

    Args:
        content: Content to scan

    Returns:
        List of threats found
    """
    threats = []

    # Check for script injections
    script_patterns = [
        (r"<script\b", "Script tag found"),
        (r"javascript\s*:", "JavaScript URL found"),
        (r"vbscript\s*:", "VBScript URL found"),
        (r"data\s*:[^,]*javascript", "JavaScript in data URL"),
        (r"on\w+\s*=", "Event handler attribute found"),
        (r"eval\s*\(", "eval() function call"),
        (r"setTimeout\s*\(", "setTimeout() function call"),
        (r"setInterval\s*\(", "setInterval() function call"),
    ]

    for pattern, description in script_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            threats.append(
                {
                    "type": "script_injection",
                    "description": description,
                    "position": match.start(),
                    "content": content[max(0, match.start() - 20) : match.end() + 20],
                }
            )

    # Check for suspicious URLs
    url_patterns = [
        (r'(?:src|href)\s*=\s*["\']?\s*(?:javascript|vbscript|data):', "Dangerous URL scheme"),
        (r'(?:src|href)\s*=\s*["\']?\s*[^"\']*\.(?:exe|bat|cmd|scr|pif)', "Executable file link"),
    ]

    for pattern, description in url_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            threats.append(
                {
                    "type": "suspicious_url",
                    "description": description,
                    "position": match.start(),
                    "content": content[max(0, match.start() - 10) : match.end() + 10],
                }
            )

    return threats
