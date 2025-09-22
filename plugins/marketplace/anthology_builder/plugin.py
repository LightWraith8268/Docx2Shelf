"""
Anthology Builder Plugin.

Provides anthology and collection building functionality.
"""

from __future__ import annotations

from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, MetadataResolverHook


class AnthologyBuilderPlugin(BasePlugin):
    """Plugin for building anthologies and collections."""

    def __init__(self):
        super().__init__("anthology_builder", "1.0.0")

    def get_hooks(self) -> Dict[str, List]:
        """Return plugin hooks."""
        return {
            'metadata_resolver': [AnthologyMetadataHook()]
        }


class AnthologyMetadataHook(MetadataResolverHook):
    """Hook for anthology-specific metadata enhancement."""

    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for anthology projects."""
        project_type = context.get('project_type')

        if project_type == 'anthology':
            # Add anthology-specific metadata
            metadata['anthology'] = {
                'story_count': context.get('story_count', 0),
                'editors': context.get('editors', []),
                'theme': context.get('anthology_theme', ''),
                'publication_order': context.get('publication_order', 'title')
            }

            # Adjust title format for anthology
            if not metadata.get('subtitle') and context.get('anthology_theme'):
                metadata['subtitle'] = f"A {context['anthology_theme']} Collection"

        return metadata