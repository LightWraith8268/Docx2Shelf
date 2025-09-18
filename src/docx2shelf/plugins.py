"""
Plugin system for Docx2Shelf with hooks for pre-convert, post-convert, and metadata resolvers.
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

logger = logging.getLogger(__name__)


class PluginHook(Protocol):
    """Protocol defining the interface for plugin hooks."""

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the hook with the given context."""
        ...


class BasePlugin(ABC):
    """Base class for all Docx2Shelf plugins."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True

    @abstractmethod
    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        """Return a dictionary of hook types to hook implementations."""
        pass

    def disable(self) -> None:
        """Disable this plugin."""
        self.enabled = False

    def enable(self) -> None:
        """Enable this plugin."""
        self.enabled = True


class PreConvertHook(ABC):
    """Hook for sanitizing/preprocessing DOCX files before conversion."""

    @abstractmethod
    def process_docx(self, docx_path: Path, context: Dict[str, Any]) -> Path:
        """
        Process the DOCX file before conversion.

        Args:
            docx_path: Path to the input DOCX file
            context: Build context with metadata and options

        Returns:
            Path to the processed DOCX file (may be the same or a new file)
        """
        pass


class PostConvertHook(ABC):
    """Hook for transforming HTML content after conversion."""

    @abstractmethod
    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """
        Transform HTML content after conversion.

        Args:
            html_content: The HTML content to transform
            context: Build context with metadata and options

        Returns:
            Transformed HTML content
        """
        pass


class MetadataResolverHook(ABC):
    """Hook for resolving additional metadata."""

    @abstractmethod
    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve additional metadata.

        Args:
            metadata: Current metadata dictionary
            context: Build context

        Returns:
            Updated metadata dictionary
        """
        pass


class PluginManager:
    """Manages plugin loading, registration, and hook execution."""

    def __init__(self):
        self.plugins: List[BasePlugin] = []
        self.hooks: Dict[str, List[PluginHook]] = {
            'pre_convert': [],
            'post_convert': [],
            'metadata_resolver': []
        }

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Register a plugin with the manager."""
        if plugin in self.plugins:
            logger.warning(f"Plugin {plugin.name} is already registered")
            return

        self.plugins.append(plugin)

        # Register hooks from the plugin
        plugin_hooks = plugin.get_hooks()
        for hook_type, hooks in plugin_hooks.items():
            if hook_type in self.hooks:
                self.hooks[hook_type].extend(hooks)
            else:
                logger.warning(f"Unknown hook type: {hook_type}")

        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")

    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin by name."""
        plugin_to_remove = None
        for plugin in self.plugins:
            if plugin.name == plugin_name:
                plugin_to_remove = plugin
                break

        if plugin_to_remove:
            self.plugins.remove(plugin_to_remove)

            # Remove hooks from this plugin
            plugin_hooks = plugin_to_remove.get_hooks()
            for hook_type, hooks in plugin_hooks.items():
                if hook_type in self.hooks:
                    for hook in hooks:
                        if hook in self.hooks[hook_type]:
                            self.hooks[hook_type].remove(hook)

            logger.info(f"Unregistered plugin: {plugin_name}")
        else:
            logger.warning(f"Plugin not found: {plugin_name}")

    def load_plugin_from_file(self, plugin_path: Path) -> None:
        """Load a plugin from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load plugin spec from {plugin_path}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for plugin classes that inherit from BasePlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr != BasePlugin):

                    plugin_instance = attr()
                    self.register_plugin(plugin_instance)
                    break
            else:
                logger.warning(f"No plugin class found in {plugin_path}")

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}")

    def load_plugins_from_directory(self, plugins_dir: Path) -> None:
        """Load all plugins from a directory."""
        if not plugins_dir.exists() or not plugins_dir.is_dir():
            logger.debug(f"Plugins directory does not exist: {plugins_dir}")
            return

        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files
            self.load_plugin_from_file(plugin_file)

    def execute_pre_convert_hooks(self, docx_path: Path, context: Dict[str, Any]) -> Path:
        """Execute all pre-convert hooks."""
        current_path = docx_path

        for hook in self.hooks['pre_convert']:
            if isinstance(hook, PreConvertHook):
                try:
                    current_path = hook.process_docx(current_path, context)
                    logger.debug(f"Pre-convert hook processed: {current_path}")
                except Exception as e:
                    logger.error(f"Pre-convert hook failed: {e}")

        return current_path

    def execute_post_convert_hooks(self, html_content: str, context: Dict[str, Any]) -> str:
        """Execute all post-convert hooks."""
        current_html = html_content

        for hook in self.hooks['post_convert']:
            if isinstance(hook, PostConvertHook):
                try:
                    current_html = hook.transform_html(current_html, context)
                    logger.debug("Post-convert hook executed successfully")
                except Exception as e:
                    logger.error(f"Post-convert hook failed: {e}")

        return current_html

    def execute_metadata_resolver_hooks(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all metadata resolver hooks."""
        current_metadata = metadata.copy()

        for hook in self.hooks['metadata_resolver']:
            if isinstance(hook, MetadataResolverHook):
                try:
                    current_metadata = hook.resolve_metadata(current_metadata, context)
                    logger.debug("Metadata resolver hook executed successfully")
                except Exception as e:
                    logger.error(f"Metadata resolver hook failed: {e}")

        return current_metadata

    def list_plugins(self) -> List[Dict[str, str]]:
        """List all registered plugins."""
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'enabled': str(plugin.enabled)
            }
            for plugin in self.plugins
        ]

    def get_plugin_by_name(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None


# Global plugin manager instance
plugin_manager = PluginManager()


def load_default_plugins() -> None:
    """Load default plugins from the plugins directory."""
    from docx2shelf.utils import get_user_data_dir

    # Load from user plugins directory
    user_plugins_dir = get_user_data_dir() / "plugins"
    plugin_manager.load_plugins_from_directory(user_plugins_dir)

    # Load from package plugins directory if it exists
    package_plugins_dir = Path(__file__).parent / "plugins"
    plugin_manager.load_plugins_from_directory(package_plugins_dir)


# Example plugin implementation for demonstration
class ExampleCleanupPlugin(BasePlugin):
    """Example plugin that demonstrates the plugin system."""

    def __init__(self):
        super().__init__("example_cleanup", "1.0.0")

    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        return {
            'post_convert': [ExampleHTMLCleanupHook()]
        }


class ExampleHTMLCleanupHook(PostConvertHook):
    """Example hook that cleans up HTML content."""

    def transform_html(self, html_content: str, context: Dict[str, Any]) -> str:
        """Remove excessive whitespace and normalize line endings."""
        import re

        # Remove excessive whitespace
        html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)

        # Normalize line endings
        html_content = html_content.replace('\r\n', '\n').replace('\r', '\n')

        return html_content