# Docx2Shelf Plugin Development Guide

This guide will help you create custom plugins to extend Docx2Shelf's functionality.

## Overview

Docx2Shelf supports three types of plugins through a hook-based system:

1. **PreConvertHook** - Process DOCX files before conversion
2. **PostConvertHook** - Transform HTML content after conversion
3. **MetadataResolverHook** - Add or modify metadata dynamically

## Quick Start

### 1. Create Your Plugin File

Create a Python file anywhere on your system (e.g., `my_plugin.py`):

```python
from docx2shelf.plugins import BasePlugin, PostConvertHook
from typing import Dict, Any, List
from pathlib import Path

class MyCustomPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_custom_plugin", "1.0.0")

    def get_hooks(self) -> Dict[str, List]:
        return {
            'post_convert': [MyHTMLProcessor()]
        }

class MyHTMLProcessor(PostConvertHook):
    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        # Your custom HTML transformation
        return html_content.replace("old_text", "new_text")
```

### 2. Load Your Plugin

```bash
# Load your plugin
docx2shelf plugins load /path/to/my_plugin.py

# List loaded plugins
docx2shelf plugins list

# Enable/disable plugins
docx2shelf plugins enable my_custom_plugin
docx2shelf plugins disable my_custom_plugin
```

### 3. Use Your Plugin

Your plugin will automatically run during the conversion process when enabled.

## Plugin Types Explained

### PreConvertHook

Processes DOCX files before they're converted to HTML. Use this to:
- Clean up or sanitize DOCX content
- Add custom styles or formatting
- Extract additional metadata
- Modify document structure

```python
from docx2shelf.plugins import PreConvertHook
from pathlib import Path
from typing import Dict, Any

class DocxCleanupHook(PreConvertHook):
    def process_docx(self, docx_path: Path, context: Dict[str, Any]) -> Path:
        # Option 1: Modify the original file and return same path
        self.cleanup_docx_file(docx_path)
        return docx_path

        # Option 2: Create a new file and return new path
        # new_path = docx_path.parent / f"cleaned_{docx_path.name}"
        # self.create_cleaned_docx(docx_path, new_path)
        # return new_path

    def cleanup_docx_file(self, docx_path: Path):
        # Your DOCX cleanup logic here
        pass
```

### PostConvertHook

Transforms HTML content after conversion. Use this to:
- Clean up HTML formatting
- Add custom CSS classes
- Replace text patterns
- Inject custom elements

```python
from docx2shelf.plugins import PostConvertHook
from typing import Dict, Any
import re

class HTMLFormatterHook(PostConvertHook):
    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        # Add custom CSS classes to paragraphs
        html_content = re.sub(
            r'<p>([^<]+)</p>',
            r'<p class="custom-paragraph">\1</p>',
            html_content
        )

        # Replace smart quotes
        html_content = html_content.replace('"', '"').replace('"', '"')

        # Add custom formatting
        html_content = html_content.replace(
            '<em>Note:</em>',
            '<div class="note-box"><em>Note:</em>'
        )

        return html_content
```

### MetadataResolverHook

Adds or modifies metadata dynamically. Use this to:
- Auto-generate metadata from content
- Fetch metadata from external sources
- Apply business rules to metadata
- Validate metadata values

```python
from docx2shelf.plugins import MetadataResolverHook
from typing import Dict, Any
import re

class MetadataEnhancerHook(MetadataResolverHook):
    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Auto-generate description from content
        if 'description' not in metadata and 'content_preview' in context:
            content = context['content_preview']
            # Extract first paragraph as description
            first_para = re.search(r'<p>([^<]+)</p>', content)
            if first_para:
                metadata['description'] = first_para.group(1)[:200] + "..."

        # Set default language if not specified
        if 'language' not in metadata:
            metadata['language'] = 'en'

        # Auto-generate tags based on content
        if 'tags' not in metadata:
            metadata['tags'] = self.generate_tags(context.get('content', ''))

        return metadata

    def generate_tags(self, content: str) -> List[str]:
        # Simple tag generation based on content
        tags = []
        if 'romance' in content.lower():
            tags.append('romance')
        if 'mystery' in content.lower():
            tags.append('mystery')
        return tags
```

## Context Information

The `context` dictionary passed to hooks contains useful information:

```python
context = {
    'input_path': Path,          # Original input file path
    'output_path': Path,         # Target output path
    'metadata': Dict,            # Current metadata
    'build_options': BuildOptions, # Build configuration
    'content_preview': str,      # Preview of HTML content (post-convert only)
    'chapter_count': int,        # Number of chapters detected
    'resources': List[Path],     # Extracted resources (images, etc.)
}
```

## Plugin Installation Locations

Plugins can be loaded from several locations:

1. **User plugins directory**: `~/.local/share/docx2shelf/plugins/` (Linux/macOS) or `%APPDATA%/Docx2Shelf/plugins/` (Windows)
2. **Project-specific**: Place plugins in your project directory
3. **Manual loading**: Use `docx2shelf plugins load <path>` for any location

### Auto-loading Plugins

Place your plugin files in the user plugins directory to have them automatically discovered:

```bash
# Linux/macOS
mkdir -p ~/.local/share/docx2shelf/plugins/
cp my_plugin.py ~/.local/share/docx2shelf/plugins/

# Windows
mkdir "%APPDATA%\Docx2Shelf\plugins\"
copy my_plugin.py "%APPDATA%\Docx2Shelf\plugins\"
```

## Plugin Template

Use this template to start developing your plugin:

```python
"""
My Custom Docx2Shelf Plugin
Description: [What your plugin does]
Author: [Your name]
Version: 1.0.0
"""

from docx2shelf.plugins import (
    BasePlugin,
    PreConvertHook,
    PostConvertHook,
    MetadataResolverHook
)
from typing import Dict, Any, List
from pathlib import Path

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            name="my_plugin",
            version="1.0.0"
        )

    def get_hooks(self) -> Dict[str, List]:
        return {
            'pre_convert': [MyPreProcessor()],
            'post_convert': [MyPostProcessor()],
            'metadata_resolver': [MyMetadataResolver()]
        }

class MyPreProcessor(PreConvertHook):
    def process_docx(self, docx_path: Path, context: Dict[str, Any]) -> Path:
        # Your pre-processing logic
        return docx_path

class MyPostProcessor(PostConvertHook):
    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        # Your HTML transformation logic
        return html_content

class MyMetadataResolver(MetadataResolverHook):
    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Your metadata enhancement logic
        return metadata
```

## Best Practices

### 1. Error Handling

Always include proper error handling:

```python
def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
    try:
        # Your transformation logic
        return self.my_transformation(html_content)
    except Exception as e:
        # Log the error but don't break the build
        print(f"Warning: Plugin transformation failed: {e}")
        return html_content  # Return original content
```

### 2. Configuration

Make your plugins configurable:

```python
class ConfigurablePlugin(BasePlugin):
    def __init__(self, config_file: Optional[Path] = None):
        super().__init__("configurable_plugin", "1.0.0")
        self.config = self.load_config(config_file)

    def load_config(self, config_file: Optional[Path]) -> Dict:
        if config_file and config_file.exists():
            import json
            with open(config_file, 'r') as f:
                return json.load(f)
        return {
            'replace_patterns': [],
            'add_css_classes': True,
            'generate_toc': False
        }
```

### 3. Testing

Test your plugins thoroughly:

```python
def test_my_hook():
    hook = MyHTMLProcessor()
    test_html = "<p>old_text</p>"
    result = hook.transform_html(test_html, {})
    assert result == "<p>new_text</p>"
```

### 4. Documentation

Document your plugin's purpose and usage:

```python
class WellDocumentedHook(PostConvertHook):
    """
    Transforms HTML content by applying custom formatting rules.

    This hook:
    - Adds CSS classes to specific elements
    - Replaces text patterns
    - Formats special content blocks

    Configuration:
    - Set patterns in context['plugin_config']['patterns']
    - Enable/disable features via context['plugin_config']['features']
    """

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        # Implementation...
        pass
```

## Plugin Management Commands

```bash
# List all plugins
docx2shelf plugins list

# Load a plugin file
docx2shelf plugins load /path/to/plugin.py

# Enable a plugin
docx2shelf plugins enable plugin_name

# Disable a plugin
docx2shelf plugins disable plugin_name

# Show plugin details
docx2shelf plugins info plugin_name
```

## Example Use Cases

### Academic Papers
- Add citation formatting
- Generate bibliography
- Format equations and figures
- Add cross-references

### Fiction Books
- Smart quote replacement
- Scene break formatting
- Character name consistency
- Chapter numbering

### Technical Documentation
- Code syntax highlighting
- API reference generation
- Cross-linking
- Glossary generation

### Multi-language Content
- Character encoding normalization
- Language-specific formatting
- RTL text handling
- Font substitution

## Troubleshooting

### Plugin Not Loading
1. Check file syntax with `python -m py_compile plugin.py`
2. Verify plugin class inherits from `BasePlugin`
3. Ensure `get_hooks()` method returns correct structure

### Plugin Not Running
1. Check if plugin is enabled: `docx2shelf plugins list`
2. Verify hook type matches your needs
3. Add debug prints to your hook methods

### Import Errors
1. Ensure `docx2shelf` package is importable
2. Check Python path and virtual environment
3. Install any additional dependencies your plugin needs

## Contributing Plugin Examples

If you create useful plugins, consider contributing them to the community:

1. Create a GitHub repository for your plugin
2. Include documentation and examples
3. Add tests for your plugin functionality
4. Share on the Docx2Shelf discussions page

## Advanced Topics

### Plugin Dependencies

If your plugin needs additional packages:

```python
class AdvancedPlugin(BasePlugin):
    def __init__(self):
        super().__init__("advanced_plugin", "1.0.0")
        self.check_dependencies()

    def check_dependencies(self):
        try:
            import required_package
        except ImportError:
            raise ImportError(
                "This plugin requires 'required_package'. "
                "Install with: pip install required_package"
            )
```

### Plugin Communication

Plugins can share data through the context:

```python
# Plugin A stores data
def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    context['plugin_data'] = {'processed_by': 'plugin_a'}
    return metadata

# Plugin B reads data
def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
    if 'plugin_data' in context:
        # Use data from Plugin A
        pass
    return html_content
```

### Performance Considerations

- Minimize file I/O operations
- Cache expensive computations
- Use lazy loading for heavy dependencies
- Consider memory usage for large documents

---

For more examples and community plugins, visit the [Docx2Shelf plugins repository](https://github.com/LightWraith8268/Docx2Shelf/discussions).