"""
Anthology Builder Plugin for Docx2Shelf.

Merges multiple manuscripts into professional collections.
"""

from .plugin import AnthologyBuilderPlugin

__version__ = "1.0.0"
__all__ = ["AnthologyBuilderPlugin"]


def create_plugin():
    """Plugin entry point."""
    return AnthologyBuilderPlugin()