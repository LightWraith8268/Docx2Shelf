"""
HTML Cleaner Plugin for Docx2Shelf

This plugin demonstrates HTML post-processing capabilities.
It cleans up common HTML formatting issues and applies consistent styling.

Author: Docx2Shelf Team
Version: 1.0.0
License: MIT
"""

import re
from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, PostConvertHook


class HTMLCleanerPlugin(BasePlugin):
    """Plugin for cleaning and standardizing HTML output."""

    def __init__(self):
        super().__init__(
            name="html_cleaner",
            version="1.0.0"
        )

    def get_hooks(self) -> Dict[str, List]:
        return {
            'post_convert': [HTMLCleanupHook()]
        }


class HTMLCleanupHook(PostConvertHook):
    """Cleans up HTML content after conversion."""

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """
        Apply comprehensive HTML cleanup.

        Transformations applied:
        - Normalize whitespace
        - Fix smart quotes and special characters
        - Remove empty paragraphs
        - Add semantic CSS classes
        - Clean up line breaks
        """
        try:
            html = html_content

            # 1. Normalize smart quotes and special characters
            html = self._normalize_quotes(html)

            # 2. Clean up whitespace
            html = self._normalize_whitespace(html)

            # 3. Remove empty or nearly empty paragraphs
            html = self._remove_empty_paragraphs(html)

            # 4. Add semantic CSS classes
            html = self._add_semantic_classes(html)

            # 5. Fix common formatting issues
            html = self._fix_formatting_issues(html)

            # 6. Handle special content blocks
            html = self._format_special_blocks(html)

            return html

        except Exception as e:
            print(f"HTML Cleaner warning: {e}")
            return html_content  # Return original on error

    def _normalize_quotes(self, html: str) -> str:
        """Convert smart quotes to proper HTML entities."""
        replacements = {
            '"': '&ldquo;',  # Left double quote
            '"': '&rdquo;',  # Right double quote
            ''': '&lsquo;',  # Left single quote
            ''': '&rsquo;',  # Right single quote
            '–': '&ndash;',  # En dash
            '—': '&mdash;',  # Em dash
            '…': '&hellip;', # Ellipsis
        }

        for char, entity in replacements.items():
            html = html.replace(char, entity)

        return html

    def _normalize_whitespace(self, html: str) -> str:
        """Clean up excessive whitespace."""
        # Remove excessive line breaks
        html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)

        # Clean up spaces around tags
        html = re.sub(r'>\s+<', '><', html)

        # Normalize spaces within text
        html = re.sub(r'[ \t]+', ' ', html)

        return html.strip()

    def _remove_empty_paragraphs(self, html: str) -> str:
        """Remove empty or whitespace-only paragraphs."""
        # Remove completely empty paragraphs
        html = re.sub(r'<p>\s*</p>', '', html)

        # Remove paragraphs with only non-breaking spaces
        html = re.sub(r'<p>(\s|&nbsp;)*</p>', '', html)

        # Remove paragraphs with only whitespace and basic formatting
        html = re.sub(r'<p>(\s|</?(?:em|strong|i|b)>)*</p>', '', html)

        return html

    def _add_semantic_classes(self, html: str) -> str:
        """Add CSS classes for semantic meaning."""
        # Add classes to different paragraph types
        html = re.sub(
            r'<p>([A-Z][^<]*[.!?])\s*</p>',
            r'<p class="first-sentence">\1</p>',
            html
        )

        # Mark paragraphs that start with quotes
        html = re.sub(
            r'<p>(&ldquo;|")',
            r'<p class="dialogue">\\1',
            html
        )

        # Mark emphasis patterns
        html = re.sub(
            r'<p>(<em>Note:</em>|<strong>Note:</strong>)',
            r'<p class="note">\\1',
            html
        )

        html = re.sub(
            r'<p>(<em>Warning:</em>|<strong>Warning:</strong>)',
            r'<p class="warning">\\1',
            html
        )

        return html

    def _fix_formatting_issues(self, html: str) -> str:
        """Fix common formatting problems."""
        # Fix spacing around emphasis
        html = re.sub(r'\s+</(em|strong)>', r'</\1>', html)
        html = re.sub(r'<(em|strong)>\s+', r'<\1>', html)

        # Fix nested emphasis tags
        html = re.sub(r'<em><strong>(.*?)</strong></em>', r'<strong><em>\1</em></strong>', html)

        # Clean up multiple spaces
        html = re.sub(r'  +', ' ', html)

        # Fix punctuation spacing
        html = re.sub(r'\s+([.!?,:;])', r'\1', html)

        return html

    def _format_special_blocks(self, html: str) -> str:
        """Format special content blocks."""
        # Format chapter titles (all caps paragraphs)
        html = re.sub(
            r'<p>([A-Z\s]{10,})</p>',
            r'<p class="chapter-title">\1</p>',
            html
        )

        # Format scene breaks (lines with just symbols)
        html = re.sub(
            r'<p>(\s*[*#\-~]{3,}\s*)</p>',
            r'<p class="scene-break">\1</p>',
            html
        )

        # Format dates and timestamps
        html = re.sub(
            r'<p>(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}.*?)</p>',
            r'<p class="dateline">\1</p>',
            html
        )

        # Format letter signatures (right-aligned short lines)
        html = re.sub(
            r'<p>(\s*[A-Z][a-z]+ [A-Z][a-z]+\s*)</p>',
            r'<p class="signature">\1</p>',
            html
        )

        return html


# Example configuration-based version
class ConfigurableHTMLCleanerPlugin(BasePlugin):
    """Configurable version of the HTML cleaner."""

    def __init__(self, config_path: str = None):
        super().__init__("configurable_html_cleaner", "1.0.0")
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "normalize_quotes": True,
            "remove_empty_paragraphs": True,
            "add_semantic_classes": True,
            "custom_replacements": {},
            "preserve_patterns": [],
            "css_class_rules": {
                "dialogue": r'<p>(&ldquo;|")',
                "note": r'<p>(<em>Note:</em>|<strong>Note:</strong>)',
                "warning": r'<p>(<em>Warning:</em>|<strong>Warning:</strong>)'
            }
        }

        if config_path:
            try:
                import json
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Could not load config from {config_path}: {e}")

        return default_config

    def get_hooks(self) -> Dict[str, List]:
        return {
            'post_convert': [ConfigurableHTMLCleanupHook(self.config)]
        }


class ConfigurableHTMLCleanupHook(PostConvertHook):
    """Configurable HTML cleanup hook."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """Apply cleanup based on configuration."""
        html = html_content

        try:
            # Apply custom replacements first
            for pattern, replacement in self.config.get("custom_replacements", {}).items():
                html = html.replace(pattern, replacement)

            # Apply standard cleanup if enabled
            if self.config.get("normalize_quotes", True):
                html = self._normalize_quotes(html)

            if self.config.get("remove_empty_paragraphs", True):
                html = self._remove_empty_paragraphs(html)

            if self.config.get("add_semantic_classes", True):
                html = self._add_css_classes(html)

            return html

        except Exception as e:
            print(f"Configurable HTML Cleaner warning: {e}")
            return html_content

    def _normalize_quotes(self, html: str) -> str:
        """Normalize quotes to HTML entities."""
        replacements = {
            '"': '&ldquo;',
            '"': '&rdquo;',
            ''': '&lsquo;',
            ''': '&rsquo;',
        }
        for char, entity in replacements.items():
            html = html.replace(char, entity)
        return html

    def _remove_empty_paragraphs(self, html: str) -> str:
        """Remove empty paragraphs."""
        return re.sub(r'<p>\s*</p>', '', html)

    def _add_css_classes(self, html: str) -> str:
        """Add CSS classes based on configuration rules."""
        for class_name, pattern in self.config.get("css_class_rules", {}).items():
            html = re.sub(
                pattern,
                f'<p class="{class_name}">\\1',
                html
            )
        return html


"""
Usage Examples:

1. Basic usage:
   docx2shelf plugins load html_cleaner.py
   docx2shelf plugins enable html_cleaner

2. With configuration file (create config.json):
   {
     "normalize_quotes": true,
     "custom_replacements": {
       "Mr.": "Mr.",
       "Mrs.": "Mrs."
     },
     "css_class_rules": {
       "important": "<p>(<strong>Important:</strong>)"
     }
   }

   Then modify the plugin initialization:
   plugin = ConfigurableHTMLCleanerPlugin("config.json")
"""