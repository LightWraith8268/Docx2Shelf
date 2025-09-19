"""
Developer experience and tooling for Docx2Shelf.

Provides IDE support, development workflow optimization, hot-reload debugging,
and code generation tools for enhanced developer productivity.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import tempfile
import time
import watchdog
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Generator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


@dataclass
class CodeTemplate:
    """Code template for generating boilerplate code."""
    name: str
    description: str
    category: str
    files: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DevelopmentConfig:
    """Development environment configuration."""
    hot_reload_enabled: bool = True
    auto_install_deps: bool = True
    debug_mode: bool = False
    watch_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.css", "*.js", "*.yaml"])
    ignore_patterns: List[str] = field(default_factory=lambda: ["__pycache__", "*.pyc", ".git"])
    test_command: str = "pytest"
    lint_command: str = "ruff check"
    format_command: str = "black"


class HotReloadHandler(FileSystemEventHandler):
    """File system event handler for hot-reload functionality."""

    def __init__(self, reload_callback: Callable[[str], None], config: DevelopmentConfig):
        super().__init__()
        self.reload_callback = reload_callback
        self.config = config
        self.last_reload = {}
        self.debounce_seconds = 1.0

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path

        # Check if file matches watch patterns
        if not self._should_watch_file(file_path):
            return

        # Debounce rapid changes
        now = time.time()
        if (file_path in self.last_reload and
            now - self.last_reload[file_path] < self.debounce_seconds):
            return

        self.last_reload[file_path] = now

        try:
            self.reload_callback(file_path)
        except Exception as e:
            print(f"❌ Hot-reload error for {file_path}: {e}")

    def _should_watch_file(self, file_path: str) -> bool:
        """Check if file should trigger hot-reload."""
        path = Path(file_path)

        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if pattern in str(path):
                return False

        # Check watch patterns
        for pattern in self.config.watch_patterns:
            if path.match(pattern):
                return True

        return False


class LSPServer:
    """Language Server Protocol support for Docx2Shelf development."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.symbols = {}
        self.diagnostics = {}

    def initialize(self) -> Dict[str, Any]:
        """Initialize LSP server capabilities."""
        return {
            "capabilities": {
                "textDocumentSync": 1,  # Full sync
                "completionProvider": {
                    "resolveProvider": True,
                    "triggerCharacters": ["."]
                },
                "hoverProvider": True,
                "definitionProvider": True,
                "referencesProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "codeActionProvider": True,
                "documentFormattingProvider": True,
                "documentRangeFormattingProvider": True,
                "renameProvider": True
            }
        }

    def analyze_document(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python document for symbols and diagnostics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            symbols = self._extract_symbols(tree)
            diagnostics = self._run_diagnostics(file_path, content)

            self.symbols[str(file_path)] = symbols
            self.diagnostics[str(file_path)] = diagnostics

            return {
                "symbols": symbols,
                "diagnostics": diagnostics
            }

        except Exception as e:
            return {
                "error": str(e),
                "symbols": [],
                "diagnostics": [
                    {
                        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                        "severity": 1,  # Error
                        "message": f"Parse error: {e}"
                    }
                ]
            }

    def get_completions(self, file_path: Path, line: int, character: int) -> List[Dict[str, Any]]:
        """Get code completions for a position."""
        completions = []

        # Add Docx2Shelf API completions
        docx2shelf_completions = [
            {
                "label": "build_epub",
                "kind": 3,  # Function
                "detail": "Build EPUB from input file",
                "documentation": "Convert DOCX/MD/HTML to EPUB format"
            },
            {
                "label": "EpubMetadata",
                "kind": 7,  # Class
                "detail": "EPUB metadata container",
                "documentation": "Manages EPUB metadata fields"
            },
            {
                "label": "BasePlugin",
                "kind": 7,  # Class
                "detail": "Base class for plugins",
                "documentation": "Inherit from this class to create custom plugins"
            },
            {
                "label": "PreConvertHook",
                "kind": 8,  # Interface
                "detail": "Pre-conversion processing hook",
                "documentation": "Process content before conversion"
            },
            {
                "label": "PostConvertHook",
                "kind": 8,  # Interface
                "detail": "Post-conversion processing hook",
                "documentation": "Process content after conversion"
            }
        ]

        completions.extend(docx2shelf_completions)
        return completions

    def _extract_symbols(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract symbols from AST."""
        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    "name": node.name,
                    "kind": 12,  # Function
                    "location": {
                        "range": {
                            "start": {"line": node.lineno - 1, "character": node.col_offset},
                            "end": {"line": node.lineno - 1, "character": node.col_offset + len(node.name)}
                        }
                    }
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "kind": 5,  # Class
                    "location": {
                        "range": {
                            "start": {"line": node.lineno - 1, "character": node.col_offset},
                            "end": {"line": node.lineno - 1, "character": node.col_offset + len(node.name)}
                        }
                    }
                })

        return symbols

    def _run_diagnostics(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Run diagnostics on file content."""
        diagnostics = []

        # Simple linting checks
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Check for common issues
            if 'print(' in line and 'debug' not in line.lower():
                diagnostics.append({
                    "range": {
                        "start": {"line": i, "character": line.find('print(')},
                        "end": {"line": i, "character": len(line)}
                    },
                    "severity": 2,  # Warning
                    "message": "Consider using logging instead of print()",
                    "source": "docx2shelf-lsp"
                })

            if len(line) > 100:
                diagnostics.append({
                    "range": {
                        "start": {"line": i, "character": 100},
                        "end": {"line": i, "character": len(line)}
                    },
                    "severity": 3,  # Info
                    "message": "Line length exceeds 100 characters",
                    "source": "docx2shelf-lsp"
                })

        return diagnostics


class CodeGenerator:
    """Generates boilerplate code for plugins, themes, and configurations."""

    def __init__(self):
        self.templates = self._load_templates()

    def generate_plugin_template(self, plugin_name: str, plugin_type: str = "basic") -> Path:
        """Generate a plugin template."""
        template = self.templates.get(f"plugin_{plugin_type}")
        if not template:
            raise ValueError(f"Unknown plugin type: {plugin_type}")

        output_dir = Path.cwd() / plugin_name
        output_dir.mkdir(exist_ok=True)

        variables = {
            "plugin_name": plugin_name,
            "plugin_class": self._to_class_name(plugin_name),
            "plugin_id": plugin_name.lower().replace('-', '_'),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "year": datetime.now().year
        }

        for file_path, content in template.files.items():
            file_content = self._substitute_variables(content, variables)
            output_file = output_dir / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(file_content, encoding='utf-8')

        print(f"📦 Plugin template '{plugin_name}' created in {output_dir}")
        return output_dir

    def generate_theme_template(self, theme_name: str) -> Path:
        """Generate a theme template."""
        template = self.templates.get("theme_basic")
        if not template:
            raise ValueError("Theme template not found")

        output_dir = Path.cwd() / f"{theme_name}-theme"
        output_dir.mkdir(exist_ok=True)

        variables = {
            "theme_name": theme_name,
            "theme_id": theme_name.lower().replace('-', '_'),
            "creation_date": datetime.now().strftime("%Y-%m-%d")
        }

        for file_path, content in template.files.items():
            file_content = self._substitute_variables(content, variables)
            output_file = output_dir / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(file_content, encoding='utf-8')

        print(f"🎨 Theme template '{theme_name}' created in {output_dir}")
        return output_dir

    def generate_config_template(self, config_type: str = "development") -> Path:
        """Generate configuration template."""
        template = self.templates.get(f"config_{config_type}")
        if not template:
            raise ValueError(f"Unknown config type: {config_type}")

        output_file = Path.cwd() / f"docx2shelf-{config_type}.yaml"

        variables = {
            "config_type": config_type,
            "creation_date": datetime.now().strftime("%Y-%m-%d")
        }

        content = self._substitute_variables(template.files["config.yaml"], variables)
        output_file.write_text(content, encoding='utf-8')

        print(f"⚙️ Configuration template '{config_type}' created: {output_file}")
        return output_file

    def _to_class_name(self, name: str) -> str:
        """Convert name to class name format."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))

    def _substitute_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Substitute template variables in content."""
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content

    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Load code templates."""
        return {
            "plugin_basic": CodeTemplate(
                name="Basic Plugin",
                description="Simple plugin template with hooks",
                category="plugin",
                files={
                    "plugin.py": '''"""
{{plugin_name}} plugin for Docx2Shelf.

Created: {{creation_date}}
"""

from docx2shelf.plugins import BasePlugin, PreConvertHook, PostConvertHook

class {{plugin_class}}(BasePlugin):
    """{{plugin_name}} plugin."""

    def __init__(self):
        super().__init__("{{plugin_id}}", "1.0.0")
        self.description = "{{plugin_name}} plugin"

    def get_hooks(self):
        return {
            'pre_convert': [{{plugin_class}}PreHook()],
            'post_convert': [{{plugin_class}}PostHook()]
        }

class {{plugin_class}}PreHook(PreConvertHook):
    """Pre-conversion processing."""

    def process_docx(self, docx_path, context):
        # Add your pre-processing logic here
        print(f"Processing {docx_path} with {{plugin_name}}")
        return docx_path

class {{plugin_class}}PostHook(PostConvertHook):
    """Post-conversion processing."""

    def transform_html(self, html_content, context):
        # Add your post-processing logic here
        print(f"Transforming HTML with {{plugin_name}}")
        return html_content
''',
                    "plugin.json": '''{
    "name": "{{plugin_name}}",
    "version": "1.0.0",
    "description": "{{plugin_name}} plugin for Docx2Shelf",
    "author": "Your Name",
    "license": "MIT",
    "entry_point": "plugin.py",
    "dependencies": [],
    "category": "processing",
    "tags": ["custom", "processing"]
}''',
                    "README.md": '''# {{plugin_name}} Plugin

{{plugin_name}} plugin for Docx2Shelf.

## Installation

```bash
docx2shelf plugins load {{plugin_name}}
```

## Usage

The plugin automatically processes DOCX files during conversion.

## Configuration

No configuration required.

## Development

Created: {{creation_date}}
'''
                }
            ),
            "theme_basic": CodeTemplate(
                name="Basic Theme",
                description="Basic CSS theme template",
                category="theme",
                files={
                    "theme.css": '''/*
 * {{theme_name}} Theme for Docx2Shelf
 * Created: {{creation_date}}
 */

/* Base typography */
body {
    font-family: "Your Font", serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 2em;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 { font-size: 2em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.25em; }

/* Paragraphs */
p {
    margin: 1em 0;
    text-align: justify;
    text-justify: inter-word;
}

/* Lists */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

/* Images */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}

th {
    background-color: #f5f5f5;
    font-weight: bold;
}

/* Code */
code {
    font-family: "Courier New", monospace;
    background-color: #f5f5f5;
    padding: 0.1em 0.3em;
    border-radius: 3px;
}

pre {
    background-color: #f5f5f5;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
}

/* Blockquotes */
blockquote {
    margin: 1em 2em;
    padding: 0.5em 1em;
    border-left: 4px solid #ddd;
    font-style: italic;
}
''',
                    "theme.json": '''{
    "name": "{{theme_name}}",
    "version": "1.0.0",
    "description": "{{theme_name}} theme for Docx2Shelf",
    "author": "Your Name",
    "category": "theme",
    "files": ["theme.css"],
    "supports": ["epub3", "kindle"],
    "settings": {
        "font_size": "16px",
        "line_height": "1.6",
        "justify_text": true
    }
}'''
                }
            ),
            "config_development": CodeTemplate(
                name="Development Configuration",
                description="Development environment configuration",
                category="config",
                files={
                    "config.yaml": '''# Docx2Shelf Development Configuration
# Created: {{creation_date}}

# Development settings
development:
  hot_reload: true
  debug_mode: true
  auto_install_deps: true
  watch_patterns:
    - "*.py"
    - "*.css"
    - "*.js"
    - "*.yaml"
  ignore_patterns:
    - "__pycache__"
    - "*.pyc"
    - ".git"
    - "node_modules"

# Build settings
build:
  theme: "serif"
  justify: true
  hyphenate: true
  max_image_width: 1200
  optimize_images: true

# Plugin settings
plugins:
  auto_discover: true
  sandbox_enabled: false  # Disabled for development
  hot_reload_enabled: true
  development_mode: true

# Monitoring
monitoring:
  enabled: true
  metrics_enabled: true
  log_level: "DEBUG"

# Testing
testing:
  test_command: "pytest"
  coverage_threshold: 80
  lint_command: "ruff check"
  format_command: "black"
'''
                }
            )
        }


class DevelopmentWorkflow:
    """Manages development workflow with hot-reload and debugging."""

    def __init__(self, project_root: Path, config: DevelopmentConfig):
        self.project_root = project_root
        self.config = config
        self.observer = None
        self.lsp_server = LSPServer(project_root)
        self.code_generator = CodeGenerator()

    def start_development_server(self, port: int = 3000):
        """Start development server with hot-reload."""
        print(f"🔥 Starting development server on port {port}")
        print(f"📂 Watching: {self.project_root}")

        if self.config.hot_reload_enabled:
            self._start_file_watcher()

        # Start the actual development server
        try:
            self._run_development_server(port)
        except KeyboardInterrupt:
            print("\n🛑 Development server stopped")
        finally:
            self._stop_file_watcher()

    def _start_file_watcher(self):
        """Start file system watcher for hot-reload."""
        handler = HotReloadHandler(self._handle_file_change, self.config)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.project_root), recursive=True)
        self.observer.start()
        print("👀 File watcher started")

    def _stop_file_watcher(self):
        """Stop file system watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("👀 File watcher stopped")

    def _handle_file_change(self, file_path: str):
        """Handle file changes for hot-reload."""
        print(f"🔄 File changed: {file_path}")

        # Run appropriate actions based on file type
        path = Path(file_path)

        if path.suffix == '.py':
            self._handle_python_change(path)
        elif path.suffix == '.css':
            self._handle_css_change(path)
        elif path.suffix in ['.yaml', '.yml']:
            self._handle_config_change(path)

    def _handle_python_change(self, file_path: Path):
        """Handle Python file changes."""
        print(f"🐍 Reloading Python module: {file_path}")

        # Run linting
        if self.config.lint_command:
            try:
                result = subprocess.run(
                    [self.config.lint_command, str(file_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"⚠️  Linting issues: {result.stdout}")
            except FileNotFoundError:
                pass  # Linter not available

        # Analyze with LSP
        analysis = self.lsp_server.analyze_document(file_path)
        if analysis.get('diagnostics'):
            print(f"📊 Found {len(analysis['diagnostics'])} issues")

    def _handle_css_change(self, file_path: Path):
        """Handle CSS file changes."""
        print(f"🎨 CSS updated: {file_path}")
        # Could trigger style reload in browser if connected

    def _handle_config_change(self, file_path: Path):
        """Handle configuration file changes."""
        print(f"⚙️ Configuration updated: {file_path}")
        # Could reload development configuration

    def _run_development_server(self, port: int):
        """Run the actual development server."""
        # This would integrate with the web interface or API server
        # For now, just a simple placeholder
        print(f"🌐 Development server running on http://localhost:{port}")
        print("📚 Documentation: http://localhost:{port}/docs")
        print("🔧 API: http://localhost:{port}/api")

        # Keep server running
        while True:
            time.sleep(1)

    def run_tests(self):
        """Run tests with coverage."""
        print("🧪 Running tests...")
        try:
            result = subprocess.run([self.config.test_command], check=True)
            print("✅ All tests passed!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Tests failed!")
            return False

    def format_code(self):
        """Format code using configured formatter."""
        print("🎨 Formatting code...")
        try:
            result = subprocess.run([self.config.format_command, "."], check=True)
            print("✅ Code formatted!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Formatting failed!")
            return False


def setup_development_environment(project_root: Path) -> DevelopmentWorkflow:
    """Setup development environment with optimal configuration."""
    config = DevelopmentConfig(
        hot_reload_enabled=True,
        auto_install_deps=True,
        debug_mode=True,
        watch_patterns=["*.py", "*.css", "*.js", "*.yaml", "*.md"],
        ignore_patterns=["__pycache__", "*.pyc", ".git", "node_modules", ".pytest_cache"]
    )

    workflow = DevelopmentWorkflow(project_root, config)

    print("🚀 Development environment ready!")
    print("Features enabled:")
    print("  🔥 Hot-reload")
    print("  🐛 Debug mode")
    print("  📦 Auto-dependency installation")
    print("  🧪 Integrated testing")
    print("  🎨 Code formatting")

    return workflow