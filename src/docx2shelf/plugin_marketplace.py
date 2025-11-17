"""
Plugin marketplace for Docx2Shelf.

Provides plugin discovery, installation, versioning, and marketplace functionality
for extending Docx2Shelf capabilities through a rich ecosystem.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.request import urlretrieve

import requests


@dataclass
class PluginInfo:
    """Information about a plugin."""

    name: str
    version: str
    description: str
    author: str
    homepage: str = ""
    license: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    docx2shelf_version: str = ""
    entry_point: str = ""
    install_url: str = ""
    checksum: str = ""
    installed: bool = False
    enabled: bool = True
    install_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "license": self.license,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "docx2shelf_version": self.docx2shelf_version,
            "entry_point": self.entry_point,
            "install_url": self.install_url,
            "checksum": self.checksum,
            "installed": self.installed,
            "enabled": self.enabled,
            "install_path": str(self.install_path) if self.install_path else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginInfo":
        """Create from dictionary."""
        install_path = Path(data["install_path"]) if data.get("install_path") else None
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            homepage=data.get("homepage", ""),
            license=data.get("license", ""),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            docx2shelf_version=data.get("docx2shelf_version", ""),
            entry_point=data.get("entry_point", ""),
            install_url=data.get("install_url", ""),
            checksum=data.get("checksum", ""),
            installed=data.get("installed", False),
            enabled=data.get("enabled", True),
            install_path=install_path,
        )


@dataclass
class MarketplaceConfig:
    """Configuration for plugin marketplace."""

    marketplace_url: str = "https://plugins.docx2shelf.org/api/v1"
    cache_duration: int = 3600  # 1 hour
    verify_checksums: bool = True
    allow_prerelease: bool = False
    trusted_publishers: Set[str] = field(default_factory=set)
    blocked_plugins: Set[str] = field(default_factory=set)


class PluginMarketplace:
    """Plugin marketplace for discovering and installing plugins."""

    def __init__(self, config: Optional[MarketplaceConfig] = None):
        """Initialize plugin marketplace.

        Args:
            config: Marketplace configuration
        """
        self.config = config or MarketplaceConfig()
        self.plugins_dir = Path.home() / ".docx2shelf" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.plugins_dir / "marketplace_cache.json"
        self.installed_file = self.plugins_dir / "installed.json"

        self._marketplace_cache: Dict[str, PluginInfo] = {}
        self._installed_plugins: Dict[str, PluginInfo] = {}

        self.load_installed_plugins()

    def load_installed_plugins(self):
        """Load information about installed plugins."""
        if self.installed_file.exists():
            try:
                with open(self.installed_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._installed_plugins = {
                        name: PluginInfo.from_dict(info) for name, info in data.items()
                    }
            except (json.JSONDecodeError, KeyError):
                self._installed_plugins = {}

    def save_installed_plugins(self):
        """Save information about installed plugins."""
        data = {name: plugin.to_dict() for name, plugin in self._installed_plugins.items()}

        with open(self.installed_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def refresh_marketplace(self) -> bool:
        """Refresh plugin information from marketplace.

        Returns:
            True if refresh was successful
        """
        try:
            # Check if cache is still valid
            if self._is_cache_valid():
                self._load_cache()
                return True

            # Fetch from marketplace
            response = requests.get(f"{self.config.marketplace_url}/plugins", timeout=30)
            response.raise_for_status()

            plugins_data = response.json()

            # Parse plugin information
            self._marketplace_cache = {}
            for plugin_data in plugins_data.get("plugins", []):
                try:
                    plugin = PluginInfo.from_dict(plugin_data)

                    # Skip blocked plugins
                    if plugin.name in self.config.blocked_plugins:
                        continue

                    # Skip prerelease if not allowed
                    if not self.config.allow_prerelease and "prerelease" in plugin.tags:
                        continue

                    self._marketplace_cache[plugin.name] = plugin

                except (KeyError, ValueError) as e:
                    print(
                        f"Warning: Invalid plugin data for {plugin_data.get('name', 'unknown')}: {e}"
                    )

            # Save cache
            self._save_cache()
            return True

        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to refresh marketplace: {e}")
            # Try to load existing cache
            if self.cache_file.exists():
                self._load_cache()
            return False

    def _is_cache_valid(self) -> bool:
        """Check if marketplace cache is still valid."""
        if not self.cache_file.exists():
            return False

        import time

        cache_age = time.time() - self.cache_file.stat().st_mtime
        return cache_age < self.config.cache_duration

    def _load_cache(self):
        """Load marketplace cache from file."""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._marketplace_cache = {
                    name: PluginInfo.from_dict(info) for name, info in data.items()
                }
        except (json.JSONDecodeError, KeyError):
            self._marketplace_cache = {}

    def _save_cache(self):
        """Save marketplace cache to file."""
        data = {name: plugin.to_dict() for name, plugin in self._marketplace_cache.items()}

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def search_plugins(self, query: str = "", tags: List[str] | None = None) -> List[PluginInfo]:
        """Search for plugins in marketplace.

        Args:
            query: Search query for name/description
            tags: List of tags to filter by

        Returns:
            List of matching plugins
        """
        if not self._marketplace_cache:
            self.refresh_marketplace()

        results = []
        query_lower = query.lower()

        for plugin in self._marketplace_cache.values():
            # Text search
            if query and not (
                query_lower in plugin.name.lower()
                or query_lower in plugin.description.lower()
                or query_lower in plugin.author.lower()
            ):
                continue

            # Tag filter
            if tags and not any(tag in plugin.tags for tag in tags):
                continue

            # Mark as installed if applicable
            if plugin.name in self._installed_plugins:
                plugin.installed = True

            results.append(plugin)

        # Sort by name
        return sorted(results, key=lambda p: p.name)

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get detailed information about a plugin.

        Args:
            name: Plugin name

        Returns:
            Plugin information or None if not found
        """
        # Check installed first
        if name in self._installed_plugins:
            return self._installed_plugins[name]

        # Check marketplace
        if not self._marketplace_cache:
            self.refresh_marketplace()

        return self._marketplace_cache.get(name)

    def install_plugin(self, name: str, version: Optional[str] = None) -> bool:
        """Install a plugin from marketplace.

        Args:
            name: Plugin name
            version: Specific version to install (default: latest)

        Returns:
            True if installation was successful
        """
        # Get plugin info
        plugin = self.get_plugin_info(name)
        if not plugin:
            print(f"Plugin '{name}' not found in marketplace")
            return False

        # Check if already installed
        if plugin.name in self._installed_plugins:
            installed = self._installed_plugins[plugin.name]
            if version and installed.version == version:
                print(f"Plugin '{name}' version {version} already installed")
                return True
            elif not version:
                print(f"Plugin '{name}' already installed (version {installed.version})")
                return True

        try:
            # Create install directory
            install_dir = self.plugins_dir / plugin.name
            if install_dir.exists():
                shutil.rmtree(install_dir)

            install_dir.mkdir(parents=True)

            # Download plugin
            print(f"Downloading {plugin.name}...")
            temp_file, _ = urlretrieve(plugin.install_url)

            # Verify checksum if available
            if self.config.verify_checksums and plugin.checksum:
                if not self._verify_checksum(temp_file, plugin.checksum):
                    print(f"Checksum verification failed for {plugin.name}")
                    return False

            # Extract plugin
            print(f"Installing {plugin.name}...")
            if plugin.install_url.endswith(".zip"):
                with zipfile.ZipFile(temp_file, "r") as zip_file:
                    zip_file.extractall(install_dir)
            else:
                # Single file plugin
                shutil.copy2(temp_file, install_dir / f"{plugin.name}.py")

            # Install dependencies
            if plugin.dependencies:
                print(f"Installing dependencies for {plugin.name}...")
                for dep in plugin.dependencies:
                    if not self._install_dependency(dep):
                        print(f"Failed to install dependency: {dep}")
                        return False

            # Update plugin info
            plugin.installed = True
            plugin.install_path = install_dir
            self._installed_plugins[plugin.name] = plugin

            # Save installed plugins
            self.save_installed_plugins()

            print(f"Successfully installed {plugin.name}")
            return True

        except Exception as e:
            print(f"Failed to install plugin {name}: {e}")
            # Clean up on failure
            if "install_dir" in locals() and install_dir.exists():
                shutil.rmtree(install_dir)
            return False

        finally:
            # Clean up temp file
            if "temp_file" in locals():
                try:
                    Path(temp_file).unlink()
                except OSError as e:
                    print(f"Warning: Failed to delete temporary file {temp_file}: {e}")

    def _verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file checksum."""
        import hashlib

        hash_algo, expected_hash = expected_checksum.split(":", 1)

        hasher = getattr(hashlib, hash_algo.lower(), None)
        if not hasher:
            print(f"Unknown hash algorithm: {hash_algo}")
            return False

        with open(file_path, "rb") as f:
            file_hash = hasher(f.read()).hexdigest()

        return file_hash == expected_hash

    def _install_dependency(self, dependency: str) -> bool:
        """Install a plugin dependency."""
        try:
            # Try to install as PyPI package first
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dependency], capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            # Try to install as plugin
            return self.install_plugin(dependency)

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin.

        Args:
            name: Plugin name

        Returns:
            True if uninstallation was successful
        """
        if name not in self._installed_plugins:
            print(f"Plugin '{name}' is not installed")
            return False

        try:
            plugin = self._installed_plugins[name]

            # Remove plugin directory
            if plugin.install_path and plugin.install_path.exists():
                shutil.rmtree(plugin.install_path)

            # Remove from installed plugins
            del self._installed_plugins[name]

            # Save installed plugins
            self.save_installed_plugins()

            print(f"Successfully uninstalled {name}")
            return True

        except Exception as e:
            print(f"Failed to uninstall plugin {name}: {e}")
            return False

    def update_plugin(self, name: str) -> bool:
        """Update an installed plugin to latest version.

        Args:
            name: Plugin name

        Returns:
            True if update was successful
        """
        if name not in self._installed_plugins:
            print(f"Plugin '{name}' is not installed")
            return False

        # Get latest version from marketplace
        if not self._marketplace_cache:
            self.refresh_marketplace()

        latest_plugin = self._marketplace_cache.get(name)
        if not latest_plugin:
            print(f"Plugin '{name}' not found in marketplace")
            return False

        installed_plugin = self._installed_plugins[name]

        # Check if update is needed
        if installed_plugin.version == latest_plugin.version:
            print(f"Plugin '{name}' is already up to date (version {installed_plugin.version})")
            return True

        print(f"Updating {name} from {installed_plugin.version} to {latest_plugin.version}")

        # Uninstall old version and install new
        if self.uninstall_plugin(name):
            return self.install_plugin(name)

        return False

    def list_installed_plugins(self) -> List[PluginInfo]:
        """List all installed plugins.

        Returns:
            List of installed plugins
        """
        return list(self._installed_plugins.values())

    def enable_plugin(self, name: str) -> bool:
        """Enable an installed plugin.

        Args:
            name: Plugin name

        Returns:
            True if successful
        """
        if name not in self._installed_plugins:
            print(f"Plugin '{name}' is not installed")
            return False

        self._installed_plugins[name].enabled = True
        self.save_installed_plugins()
        print(f"Enabled plugin '{name}'")
        return True

    def disable_plugin(self, name: str) -> bool:
        """Disable an installed plugin.

        Args:
            name: Plugin name

        Returns:
            True if successful
        """
        if name not in self._installed_plugins:
            print(f"Plugin '{name}' is not installed")
            return False

        self._installed_plugins[name].enabled = False
        self.save_installed_plugins()
        print(f"Disabled plugin '{name}'")
        return True

    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get statistics about plugin usage.

        Returns:
            Dictionary with plugin statistics
        """
        total_marketplace = len(self._marketplace_cache)
        total_installed = len(self._installed_plugins)
        enabled_count = sum(1 for p in self._installed_plugins.values() if p.enabled)

        # Tag statistics
        tag_counts = {}
        for plugin in self._marketplace_cache.values():
            for tag in plugin.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Popular tags (top 10)
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "marketplace_plugins": total_marketplace,
            "installed_plugins": total_installed,
            "enabled_plugins": enabled_count,
            "disabled_plugins": total_installed - enabled_count,
            "popular_tags": popular_tags,
            "cache_age_hours": (
                (Path(self.cache_file).stat().st_mtime - Path.stat().st_mtime) / 3600
                if self.cache_file.exists()
                else 0
            ),
        }

    def create_plugin_template(self, name: str, output_dir: Path) -> bool:
        """Create a template for developing a new plugin.

        Args:
            name: Plugin name
            output_dir: Directory to create template in

        Returns:
            True if template was created successfully
        """
        plugin_dir = output_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create main plugin file
        plugin_file = plugin_dir / f"{name}.py"
        plugin_template = f'''"""
{name} plugin for Docx2Shelf.

A template plugin demonstrating the plugin API.
"""

from docx2shelf.plugins import Plugin, PluginHook, PluginMetadata


class {name.title()}Plugin(Plugin):
    """Example plugin for Docx2Shelf."""

    metadata = PluginMetadata(
        name="{name}",
        version="1.0.0",
        description="A template plugin for Docx2Shelf",
        author="Your Name",
        license="MIT"
    )

    @PluginHook.pre_convert
    def before_conversion(self, input_path, context):
        """Called before document conversion."""
        print(f"{{self.metadata.name}}: Processing {{input_path}}")
        return input_path, context

    @PluginHook.post_convert
    def after_conversion(self, html_chunks, images, context):
        """Called after document conversion."""
        print(f"{{self.metadata.name}}: Converted {{len(html_chunks)}} chunks")
        return html_chunks, images, context

    @PluginHook.metadata_resolver
    def resolve_metadata(self, metadata, context):
        """Called to resolve or enhance metadata."""
        # Example: Add plugin-specific metadata
        metadata.extra_metadata["processed_by"] = self.metadata.name
        return metadata

    def configure(self, config):
        """Configure the plugin with user settings."""
        # Handle plugin configuration
        pass


# Plugin entry point
def create_plugin():
    """Create and return the plugin instance."""
    return {name.title()}Plugin()
'''

        plugin_file.write_text(plugin_template, encoding="utf-8")

        # Create plugin metadata file
        metadata_file = plugin_dir / "plugin.json"
        metadata = {
            {
                "name": name,
                "version": "1.0.0",
                "description": "A template plugin for Docx2Shelf",
                "author": "Your Name",
                "license": "MIT",
                "homepage": "",
                "tags": ["template", "example"],
                "dependencies": [],
                "docx2shelf_version": ">=1.2.4",
                "entry_point": f"{name}.create_plugin",
            }
        }

        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Create README
        readme_file = plugin_dir / "README.md"
        readme_content = f"""# {name.title()} Plugin

A template plugin for Docx2Shelf.

## Installation

1. Copy this directory to your Docx2Shelf plugins folder
2. Enable the plugin using: `docx2shelf plugins enable {name}`

## Configuration

This plugin doesn't require any configuration.

## Development

To modify this plugin:

1. Edit `{name}.py` to implement your functionality
2. Update `plugin.json` with your plugin metadata
3. Test your plugin with Docx2Shelf

## License

MIT License
"""

        readme_file.write_text(readme_content, encoding="utf-8")

        print(f"Plugin template created in {plugin_dir}")
        return True


# Global marketplace instance
_marketplace_instance: Optional[PluginMarketplace] = None


def get_marketplace() -> PluginMarketplace:
    """Get the global plugin marketplace instance."""
    global _marketplace_instance
    if _marketplace_instance is None:
        _marketplace_instance = PluginMarketplace()
    return _marketplace_instance
