"""
Store Profile Manager Plugin.

Validates EPUBs against major retailer requirements.
"""

from __future__ import annotations

from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, PostConvertHook
from docx2shelf.store_profiles import StoreProfileManager


class StoreProfilePlugin(BasePlugin):
    """Plugin for store-specific validation and optimization."""

    def __init__(self):
        super().__init__("store_profiles", "1.0.0")
        self.store_manager = StoreProfileManager()

    def get_hooks(self) -> Dict[str, List]:
        """Return plugin hooks."""
        return {
            'post_convert': [StoreValidationHook(self.store_manager)]
        }


class StoreValidationHook(PostConvertHook):
    """Hook for store-specific validation."""

    def __init__(self, store_manager: StoreProfileManager):
        self.store_manager = store_manager

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """Apply store-specific transformations and validations."""
        # Get target store from context
        target_store = context.get('target_store', 'generic')

        if target_store != 'generic':
            # Apply store-specific optimizations
            profile = self.store_manager.get_profile(target_store)
            if profile:
                # Apply transformations based on store requirements
                html_content = self._apply_store_optimizations(html_content, profile)

        return html_content

    def _apply_store_optimizations(self, html: str, profile: Dict[str, Any]) -> str:
        """Apply store-specific HTML optimizations."""
        # Example optimizations based on store profile
        css_limits = profile.get('css_limits', {})

        # KDP-specific optimizations
        if profile.get('name') == 'kdp':
            # Remove unsupported CSS properties
            html = self._remove_unsupported_css(html, css_limits.get('unsupported_properties', []))

        # Apple Books optimizations
        elif profile.get('name') == 'apple':
            # Optimize for Apple Books reader
            html = self._optimize_for_apple_books(html)

        return html

    def _remove_unsupported_css(self, html: str, unsupported: List[str]) -> str:
        """Remove CSS properties not supported by the store."""
        # Implementation would parse and clean CSS
        return html

    def _optimize_for_apple_books(self, html: str) -> str:
        """Apply Apple Books specific optimizations."""
        # Implementation would apply Apple Books optimizations
        return html