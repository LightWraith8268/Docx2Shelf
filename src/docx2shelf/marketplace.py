"""
Marketplace for Docx2Shelf tools, themes, and resources.

This module provides access to:
- Curated themes and templates
- Useful conversion tools and utilities
- Format-specific resources
- Quality enhancement tools

Note: This is a read-only marketplace focused on official resources.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None


@dataclass
class MarketplaceTheme:
    """A theme available in the marketplace."""

    name: str
    description: str
    category: str  # serif, sans-serif, specialty, academic, fiction
    author: str
    version: str
    download_url: str
    checksum: str
    preview_image: Optional[str]
    tags: List[str]
    file_size: int
    compatibility: str  # "3.0+", "all"
    rating: float
    downloads: int
    featured: bool = False


@dataclass
class MarketplaceTool:
    """A tool available in the marketplace."""

    name: str
    description: str
    category: str  # conversion, quality, accessibility, publishing
    executable: str
    version: str
    download_url: str
    checksum: str
    platforms: List[str]  # ["windows", "macos", "linux"]
    file_size: int
    install_instructions: str
    dependencies: List[str]
    homepage: str
    rating: float
    downloads: int
    featured: bool = False


@dataclass
class MarketplaceResource:
    """A resource available in the marketplace."""

    name: str
    description: str
    category: str  # template, font, image, reference
    resource_type: str  # css, font, image, pdf, epub
    download_url: str
    checksum: str
    tags: List[str]
    file_size: int
    license: str
    author: str
    rating: float
    downloads: int
    featured: bool = False


class MarketplaceManager:
    """Manages marketplace content discovery and installation."""

    def __init__(self):
        self.cache_dir = self._get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.themes_dir = self._get_themes_dir()
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir = self._get_tools_dir()
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.resources_dir = self._get_resources_dir()
        self.resources_dir.mkdir(parents=True, exist_ok=True)

        # Use offline catalog for now (could be updated via download later)
        self.catalog_data = self._get_offline_catalog()

    def _get_cache_dir(self) -> Path:
        """Get the marketplace cache directory."""
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:
            base = Path.home()
        return base / ".docx2shelf" / "marketplace"

    def _get_themes_dir(self) -> Path:
        """Get the themes directory."""
        return self.cache_dir / "themes"

    def _get_tools_dir(self) -> Path:
        """Get the tools directory."""
        return self.cache_dir / "tools"

    def _get_resources_dir(self) -> Path:
        """Get the resources directory."""
        return self.cache_dir / "resources"

    def _get_offline_catalog(self) -> Dict[str, Any]:
        """Get the offline catalog of marketplace items."""
        return {
            "themes": [
                {
                    "name": "Academic Paper",
                    "description": "Clean, professional theme for academic papers and theses",
                    "category": "academic",
                    "author": "Docx2Shelf",
                    "version": "1.0.0",
                    "download_url": "https://releases.docx2shelf.com/themes/academic-paper-v1.zip",
                    "checksum": "sha256:abc123...",
                    "preview_image": "https://releases.docx2shelf.com/previews/academic-paper.png",
                    "tags": ["academic", "clean", "minimal", "citations"],
                    "file_size": 25600,
                    "compatibility": "3.0+",
                    "rating": 4.8,
                    "downloads": 15420,
                    "featured": True,
                },
                {
                    "name": "Fiction Novel",
                    "description": "Elegant theme optimized for fiction with beautiful typography",
                    "category": "fiction",
                    "author": "Docx2Shelf",
                    "version": "1.2.0",
                    "download_url": "https://releases.docx2shelf.com/themes/fiction-novel-v1.2.zip",
                    "checksum": "sha256:def456...",
                    "preview_image": "https://releases.docx2shelf.com/previews/fiction-novel.png",
                    "tags": ["fiction", "elegant", "readable", "drop-caps"],
                    "file_size": 34200,
                    "compatibility": "3.0+",
                    "rating": 4.9,
                    "downloads": 28350,
                    "featured": True,
                },
                {
                    "name": "Technical Manual",
                    "description": "Comprehensive theme for technical documentation with code highlighting",
                    "category": "technical",
                    "author": "Docx2Shelf",
                    "version": "1.1.0",
                    "download_url": "https://releases.docx2shelf.com/themes/technical-manual-v1.1.zip",
                    "checksum": "sha256:ghi789...",
                    "preview_image": "https://releases.docx2shelf.com/previews/technical-manual.png",
                    "tags": ["technical", "code", "documentation", "syntax-highlighting"],
                    "file_size": 41800,
                    "compatibility": "3.0+",
                    "rating": 4.7,
                    "downloads": 9850,
                    "featured": False,
                },
                {
                    "name": "Children's Book",
                    "description": "Playful theme with large fonts and colorful design for children's books",
                    "category": "specialty",
                    "author": "Docx2Shelf",
                    "version": "1.0.0",
                    "download_url": "https://releases.docx2shelf.com/themes/childrens-book-v1.zip",
                    "checksum": "sha256:jkl012...",
                    "preview_image": "https://releases.docx2shelf.com/previews/childrens-book.png",
                    "tags": ["children", "colorful", "large-text", "illustrations"],
                    "file_size": 28900,
                    "compatibility": "3.0+",
                    "rating": 4.6,
                    "downloads": 6240,
                    "featured": False,
                },
            ],
            "tools": [
                {
                    "name": "EPUB Optimizer",
                    "description": "Advanced EPUB compression and optimization tool",
                    "category": "quality",
                    "executable": "epub-optimizer",
                    "version": "2.1.0",
                    "download_url": "https://releases.docx2shelf.com/tools/epub-optimizer-v2.1.zip",
                    "checksum": "sha256:mno345...",
                    "platforms": ["windows", "macos", "linux"],
                    "file_size": 5242880,
                    "install_instructions": "Extract and add to PATH",
                    "dependencies": [],
                    "homepage": "https://tools.docx2shelf.com/epub-optimizer",
                    "rating": 4.8,
                    "downloads": 12400,
                    "featured": True,
                },
                {
                    "name": "Image Processor",
                    "description": "Batch image compression and format conversion for EPUBs",
                    "category": "conversion",
                    "executable": "image-processor",
                    "version": "1.5.0",
                    "download_url": "https://releases.docx2shelf.com/tools/image-processor-v1.5.zip",
                    "checksum": "sha256:pqr678...",
                    "platforms": ["windows", "macos", "linux"],
                    "file_size": 3145728,
                    "install_instructions": "Extract and add to PATH",
                    "dependencies": ["libwebp", "libjpeg"],
                    "homepage": "https://tools.docx2shelf.com/image-processor",
                    "rating": 4.5,
                    "downloads": 8750,
                    "featured": False,
                },
                {
                    "name": "Accessibility Checker",
                    "description": "Comprehensive accessibility validation for EPUB files",
                    "category": "accessibility",
                    "executable": "a11y-checker",
                    "version": "3.0.0",
                    "download_url": "https://releases.docx2shelf.com/tools/a11y-checker-v3.zip",
                    "checksum": "sha256:stu901...",
                    "platforms": ["windows", "macos", "linux"],
                    "file_size": 2097152,
                    "install_instructions": "Extract and add to PATH",
                    "dependencies": [],
                    "homepage": "https://tools.docx2shelf.com/a11y-checker",
                    "rating": 4.9,
                    "downloads": 5320,
                    "featured": True,
                },
            ],
            "resources": [
                {
                    "name": "Professional Fonts Pack",
                    "description": "Collection of high-quality fonts optimized for digital reading",
                    "category": "font",
                    "resource_type": "font",
                    "download_url": "https://releases.docx2shelf.com/resources/pro-fonts-pack.zip",
                    "checksum": "sha256:vwx234...",
                    "tags": ["fonts", "professional", "reading", "typography"],
                    "file_size": 10485760,
                    "license": "OFL",
                    "author": "Various",
                    "rating": 4.7,
                    "downloads": 18650,
                    "featured": True,
                },
                {
                    "name": "EPUB Templates",
                    "description": "Ready-to-use EPUB templates for various book types",
                    "category": "template",
                    "resource_type": "epub",
                    "download_url": "https://releases.docx2shelf.com/resources/epub-templates.zip",
                    "checksum": "sha256:yz567...",
                    "tags": ["templates", "starter", "examples", "structure"],
                    "file_size": 1048576,
                    "license": "MIT",
                    "author": "Docx2Shelf",
                    "rating": 4.8,
                    "downloads": 22100,
                    "featured": True,
                },
                {
                    "name": "Publishing Reference Guide",
                    "description": "Comprehensive guide to digital publishing standards and best practices",
                    "category": "reference",
                    "resource_type": "pdf",
                    "download_url": "https://releases.docx2shelf.com/resources/publishing-guide.pdf",
                    "checksum": "sha256:abc890...",
                    "tags": ["guide", "reference", "publishing", "standards"],
                    "file_size": 5242880,
                    "license": "CC BY-SA",
                    "author": "Docx2Shelf Team",
                    "rating": 4.9,
                    "downloads": 31200,
                    "featured": False,
                },
            ],
            "version": "1.0.0",
            "last_updated": "2025-09-20",
        }

    def get_themes(
        self, category: Optional[str] = None, featured_only: bool = False
    ) -> List[MarketplaceTheme]:
        """Get available themes from the marketplace."""
        themes_data = self.catalog_data.get("themes", [])
        themes = [MarketplaceTheme(**theme) for theme in themes_data]

        if category:
            themes = [t for t in themes if t.category == category]

        if featured_only:
            themes = [t for t in themes if t.featured]

        # Sort by downloads (popularity)
        themes.sort(key=lambda x: x.downloads, reverse=True)
        return themes

    def get_tools(
        self, category: Optional[str] = None, platform: Optional[str] = None
    ) -> List[MarketplaceTool]:
        """Get available tools from the marketplace."""
        tools_data = self.catalog_data.get("tools", [])
        tools = [MarketplaceTool(**tool) for tool in tools_data]

        if category:
            tools = [t for t in tools if t.category == category]

        if platform:
            tools = [t for t in tools if platform in t.platforms]

        # Sort by rating and downloads
        tools.sort(key=lambda x: (x.rating, x.downloads), reverse=True)
        return tools

    def get_resources(
        self, category: Optional[str] = None, resource_type: Optional[str] = None
    ) -> List[MarketplaceResource]:
        """Get available resources from the marketplace."""
        resources_data = self.catalog_data.get("resources", [])
        resources = [MarketplaceResource(**resource) for resource in resources_data]

        if category:
            resources = [r for r in resources if r.category == category]

        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]

        # Sort by downloads
        resources.sort(key=lambda x: x.downloads, reverse=True)
        return resources

    def search(self, query: str, item_type: Optional[str] = None) -> Dict[str, List]:
        """Search marketplace items."""
        query_lower = query.lower()
        results = {"themes": [], "tools": [], "resources": []}

        if not item_type or item_type == "themes":
            themes = self.get_themes()
            for theme in themes:
                if (
                    query_lower in theme.name.lower()
                    or query_lower in theme.description.lower()
                    or any(query_lower in tag.lower() for tag in theme.tags)
                ):
                    results["themes"].append(theme)

        if not item_type or item_type == "tools":
            tools = self.get_tools()
            for tool in tools:
                if query_lower in tool.name.lower() or query_lower in tool.description.lower():
                    results["tools"].append(tool)

        if not item_type or item_type == "resources":
            resources = self.get_resources()
            for resource in resources:
                if (
                    query_lower in resource.name.lower()
                    or query_lower in resource.description.lower()
                    or any(query_lower in tag.lower() for tag in resource.tags)
                ):
                    results["resources"].append(resource)

        return results

    def install_theme(self, theme: MarketplaceTheme) -> bool:
        """Install a theme from the marketplace."""
        try:
            print(f"Installing theme: {theme.name}")

            if not requests:
                print("Error: requests library required for downloads")
                return False

            # Download theme
            response = requests.get(theme.download_url, timeout=30)
            if response.status_code != 200:
                print(f"Download failed: HTTP {response.status_code}")
                return False

            # Verify checksum (simplified for demo)
            # In real implementation, would verify against theme.checksum

            # Extract theme
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            try:
                theme_dir = self.themes_dir / theme.name.replace(" ", "_").lower()
                theme_dir.mkdir(exist_ok=True)

                with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                    zip_ref.extractall(theme_dir)

                # Save metadata
                metadata = asdict(theme)
                (theme_dir / "metadata.json").write_text(
                    json.dumps(metadata, indent=2), encoding="utf-8"
                )

                print(f"✓ Theme '{theme.name}' installed successfully")
                return True

            finally:
                os.unlink(temp_file_path)

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def install_tool(self, tool: MarketplaceTool) -> bool:
        """Install a tool from the marketplace."""
        try:
            print(f"Installing tool: {tool.name}")

            if not requests:
                print("Error: requests library required for downloads")
                return False

            # Check platform compatibility
            current_platform = sys.platform
            platform_map = {"win32": "windows", "darwin": "macos", "linux": "linux"}
            platform_name = platform_map.get(current_platform, current_platform)

            if platform_name not in tool.platforms:
                print(f"Tool not available for {platform_name}")
                return False

            # Download tool
            response = requests.get(tool.download_url, timeout=60)
            if response.status_code != 200:
                print(f"Download failed: HTTP {response.status_code}")
                return False

            # Extract tool
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            try:
                tool_dir = self.tools_dir / tool.name.replace(" ", "_").lower()
                tool_dir.mkdir(exist_ok=True)

                with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                    zip_ref.extractall(tool_dir)

                # Save metadata and installation info
                metadata = asdict(tool)
                (tool_dir / "metadata.json").write_text(
                    json.dumps(metadata, indent=2), encoding="utf-8"
                )

                print(f"✓ Tool '{tool.name}' installed successfully")
                print(f"Installation instructions: {tool.install_instructions}")

                if tool.dependencies:
                    print(f"Dependencies required: {', '.join(tool.dependencies)}")

                return True

            finally:
                os.unlink(temp_file_path)

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def install_resource(self, resource: MarketplaceResource) -> bool:
        """Install a resource from the marketplace."""
        try:
            print(f"Installing resource: {resource.name}")

            if not requests:
                print("Error: requests library required for downloads")
                return False

            # Download resource
            response = requests.get(resource.download_url, timeout=60)
            if response.status_code != 200:
                print(f"Download failed: HTTP {response.status_code}")
                return False

            # Save resource
            resource_dir = self.resources_dir / resource.name.replace(" ", "_").lower()
            resource_dir.mkdir(exist_ok=True)

            if resource.resource_type == "pdf":
                # Save PDF directly
                (resource_dir / f"{resource.name}.pdf").write_bytes(response.content)
            else:
                # Extract archive
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name

                try:
                    with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                        zip_ref.extractall(resource_dir)
                finally:
                    os.unlink(temp_file_path)

            # Save metadata
            metadata = asdict(resource)
            (resource_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=2), encoding="utf-8"
            )

            print(f"✓ Resource '{resource.name}' installed successfully")
            print(f"License: {resource.license}")
            return True

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def list_installed_themes(self) -> List[str]:
        """List installed themes."""
        installed = []
        for item in self.themes_dir.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                installed.append(item.name.replace("_", " ").title())
        return sorted(installed)

    def list_installed_tools(self) -> List[str]:
        """List installed tools."""
        installed = []
        for item in self.tools_dir.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                installed.append(item.name.replace("_", " ").title())
        return sorted(installed)

    def list_installed_resources(self) -> List[str]:
        """List installed resources."""
        installed = []
        for item in self.resources_dir.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                installed.append(item.name.replace("_", " ").title())
        return sorted(installed)

    def get_featured_items(self) -> Dict[str, List]:
        """Get featured items from all categories."""
        return {
            "themes": self.get_themes(featured_only=True),
            "tools": [t for t in self.get_tools() if t.featured],
            "resources": [r for r in self.get_resources() if r.featured],
        }

    def get_categories(self) -> Dict[str, List[str]]:
        """Get available categories for each item type."""
        themes = self.get_themes()
        tools = self.get_tools()
        resources = self.get_resources()

        return {
            "themes": sorted(list(set(t.category for t in themes))),
            "tools": sorted(list(set(t.category for t in tools))),
            "resources": sorted(list(set(r.category for r in resources))),
        }


# Global instance
marketplace = MarketplaceManager()
