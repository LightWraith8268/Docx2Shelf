"""
Basic Plugin Template for Docx2Shelf

This template provides a starting point for creating custom plugins.
Copy this file and modify it to create your own plugin.

Author: Your Name
Version: 1.0.0
License: MIT
"""

from docx2shelf.plugins import (
    BasePlugin,
    PreConvertHook,
    PostConvertHook,
    MetadataResolverHook
)
from typing import Dict, Any, List
from pathlib import Path


class BasicTemplatePlugin(BasePlugin):
    """
    Basic template plugin demonstrating all hook types.

    This plugin serves as a starting point for developing custom plugins.
    Rename the class and implement the hooks you need.
    """

    def __init__(self):
        super().__init__(
            name="basic_template",  # Change this to your plugin name
            version="1.0.0"
        )

    def get_hooks(self) -> Dict[str, List]:
        """
        Return the hooks this plugin provides.
        Remove hook types you don't need.
        """
        return {
            'pre_convert': [BasicPreProcessor()],
            'post_convert': [BasicPostProcessor()],
            'metadata_resolver': [BasicMetadataResolver()]
        }


class BasicPreProcessor(PreConvertHook):
    """
    Processes DOCX files before conversion.

    Use this to:
    - Clean up DOCX content
    - Add custom formatting
    - Extract additional information
    """

    def process_docx(self, docx_path: Path, context: Dict[str, Any]) -> Path:
        """
        Process the DOCX file before conversion.

        Args:
            docx_path: Path to the input DOCX file
            context: Build context with metadata and options

        Returns:
            Path to the processed DOCX file (may be same or new file)
        """
        try:
            # Your pre-processing logic here
            print(f"Processing DOCX: {docx_path}")

            # Example: Log information about the document
            print(f"Document size: {docx_path.stat().st_size} bytes")

            # Return the original path (no changes)
            # Or create a new file and return its path
            return docx_path

        except Exception as e:
            print(f"Error in pre-processing: {e}")
            return docx_path  # Return original on error


class BasicPostProcessor(PostConvertHook):
    """
    Transforms HTML content after conversion.

    Use this to:
    - Clean up HTML formatting
    - Add CSS classes
    - Replace text patterns
    - Add custom elements
    """

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """
        Transform HTML content after conversion.

        Args:
            html_content: The HTML content to transform
            context: Build context with metadata and options

        Returns:
            Transformed HTML content
        """
        try:
            # Your HTML transformation logic here
            print("Transforming HTML content...")

            # Example transformations (remove these and add your own):

            # 1. Replace smart quotes
            html_content = html_content.replace('"', '"').replace('"', '"')
            html_content = html_content.replace(''', "'").replace(''', "'")

            # 2. Add CSS classes to paragraphs
            import re
            html_content = re.sub(
                r'<p>([^<]+)</p>',
                r'<p class="custom-paragraph">\1</p>',
                html_content
            )

            # 3. Format special content
            html_content = html_content.replace(
                'NOTE:',
                '<span class="note-indicator">NOTE:</span>'
            )

            return html_content

        except Exception as e:
            print(f"Error in post-processing: {e}")
            return html_content  # Return original on error


class BasicMetadataResolver(MetadataResolverHook):
    """
    Adds or modifies metadata dynamically.

    Use this to:
    - Auto-generate metadata from content
    - Validate metadata values
    - Apply business rules
    - Fetch metadata from external sources
    """

    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve additional metadata.

        Args:
            metadata: Current metadata dictionary
            context: Build context

        Returns:
            Updated metadata dictionary
        """
        try:
            print("Resolving metadata...")

            # Example metadata enhancements (remove these and add your own):

            # 1. Set default language if not specified
            if 'language' not in metadata:
                metadata['language'] = 'en'
                print("Set default language to 'en'")

            # 2. Auto-generate description from title
            if 'description' not in metadata and 'title' in metadata:
                metadata['description'] = f"An EPUB book: {metadata['title']}"
                print("Generated description from title")

            # 3. Add creation timestamp
            import datetime
            metadata['plugin_processed_at'] = datetime.datetime.now().isoformat()

            # 4. Add plugin signature
            metadata['processed_by_plugins'] = metadata.get('processed_by_plugins', [])
            metadata['processed_by_plugins'].append(self.__class__.__name__)

            return metadata

        except Exception as e:
            print(f"Error in metadata resolution: {e}")
            return metadata  # Return original on error


# Optional: Add configuration loading
class ConfigurablePlugin(BasePlugin):
    """
    Example of a plugin with configuration support.
    """

    def __init__(self, config_path: Path = None):
        super().__init__("configurable_plugin", "1.0.0")
        self.config = self.load_config(config_path)

    def load_config(self, config_path: Path = None) -> Dict[str, Any]:
        """Load plugin configuration from file or use defaults."""
        default_config = {
            'enabled_features': ['smart_quotes', 'css_classes'],
            'replacement_patterns': {},
            'debug_mode': False
        }

        if config_path and config_path.exists():
            try:
                import json
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    print(f"Loaded configuration from {config_path}")
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")

        return default_config

    def get_hooks(self) -> Dict[str, List]:
        return {
            'post_convert': [ConfigurablePostProcessor(self.config)]
        }


class ConfigurablePostProcessor(PostConvertHook):
    """Post processor that uses configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        if self.config.get('debug_mode'):
            print("Running in debug mode")

        if 'smart_quotes' in self.config.get('enabled_features', []):
            html_content = html_content.replace('"', '"').replace('"', '"')

        for pattern, replacement in self.config.get('replacement_patterns', {}).items():
            html_content = html_content.replace(pattern, replacement)

        return html_content


# Instructions for users:
"""
To use this template:

1. Copy this file to your desired location
2. Rename the classes (BasicTemplatePlugin, etc.)
3. Modify the plugin name in __init__()
4. Implement only the hooks you need (remove unused ones)
5. Add your custom logic to the hook methods
6. Test your plugin thoroughly

To load your plugin:
    docx2shelf plugins load /path/to/your_plugin.py

To enable your plugin:
    docx2shelf plugins enable your_plugin_name
"""