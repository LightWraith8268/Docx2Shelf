"""HTML cleanup plugin template.

Strips noisy attributes and empty elements from the converted HTML before
EPUB assembly. Customize the patterns below for your manuscript style.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, PluginHook, PostConvertHook


class HtmlCleanerPostProcessor(PostConvertHook):
    """Removes Word-specific cruft from Pandoc-generated HTML."""

    # Attributes Pandoc/Word leak into output that EPUB readers ignore.
    NOISE_ATTRS = ("class", "lang", "data-custom-style")

    # Empty inline tags Pandoc occasionally emits for stripped Word artifacts.
    EMPTY_TAGS = ("span", "em", "strong", "a")

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        cleaned = html_content

        for attr in self.NOISE_ATTRS:
            cleaned = re.sub(
                rf'\s+{attr}="[^"]*"',
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

        for tag in self.EMPTY_TAGS:
            cleaned = re.sub(
                rf"<{tag}\s*>\s*</{tag}>",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

        # Collapse consecutive whitespace runs that the strip can leave behind.
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        return cleaned


class HtmlCleanerPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="html_cleaner", version="0.1.0")

    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        return {"post_convert": [HtmlCleanerPostProcessor()]}
