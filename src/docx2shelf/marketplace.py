"""
Plugin marketplace and distribution system for Docx2Shelf.

This module provides a plugin marketplace with discovery, installation management,
dependency resolution, and quality validation for extending Docx2Shelf functionality.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve

import requests


@dataclass
class PluginMetadata:
    """Metadata for a marketplace plugin."""

    id: str
    name: str
    version: str
    author: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    compatibility: List[str] = field(default_factory=list)  # Docx2Shelf versions
    download_url: str = ""
    file_size: int = 0
    checksum: str = ""
    created_at: str = ""
    updated_at: str = ""




@dataclass
class PluginStats:
    """Basic statistics for a plugin."""

    plugin_id: str
    download_count: int = 0
    weekly_downloads: int = 0
    monthly_downloads: int = 0
    last_updated: str = ""


class PluginCertificationChecker:
    """Plugin quality certification and validation system."""

    def __init__(self):
        self.certification_levels = {
            'basic': {'min_downloads': 10},
            'verified': {'min_downloads': 100},
            'trusted': {'min_downloads': 500}
        }

    def validate_plugin_code(self, plugin_path: Path) -> Tuple[bool, List[str]]:
        """Validate plugin code for security and quality."""
        issues = []

        # Check for security issues
        if not self._check_security(plugin_path):
            issues.append("Security: Potential security vulnerabilities detected")

        # Check code quality
        if not self._check_code_quality(plugin_path):
            issues.append("Quality: Code quality below standards")

        # Check documentation
        if not self._check_documentation(plugin_path):
            issues.append("Documentation: Insufficient documentation")

        # Check test coverage
        if not self._check_tests(plugin_path):
            issues.append("Testing: Missing or insufficient tests")

        return len(issues) == 0, issues

    def _check_security(self, plugin_path: Path) -> bool:
        """Check for common security issues."""
        dangerous_imports = ['os.system', 'subprocess.call', 'exec', 'eval']

        for py_file in plugin_path.glob("**/*.py"):
            content = py_file.read_text(encoding='utf-8')
            for dangerous in dangerous_imports:
                if dangerous in content:
                    return False

        return True

    def _check_code_quality(self, plugin_path: Path) -> bool:
        """Basic code quality checks."""
        # Check for __init__.py files
        has_init = (plugin_path / "__init__.py").exists()

        # Check for docstrings
        py_files = list(plugin_path.glob("**/*.py"))
        if not py_files:
            return False

        # Basic quality heuristics
        return has_init and len(py_files) > 0

    def _check_documentation(self, plugin_path: Path) -> bool:
        """Check for adequate documentation."""
        doc_files = ['README.md', 'README.txt', 'docs/']
        return any((plugin_path / doc).exists() for doc in doc_files)

    def _check_tests(self, plugin_path: Path) -> bool:
        """Check for test files."""
        test_patterns = ['test_*.py', 'tests/', '*_test.py']
        for pattern in test_patterns:
            if list(plugin_path.glob(pattern)):
                return True
        return False

    def get_certification_level(self, stats: PluginStats) -> Optional[str]:
        """Determine certification level based on statistics."""
        for level, requirements in reversed(self.certification_levels.items()):
            if stats.download_count >= requirements['min_downloads']:
                return level
        return None


class PluginDependencyResolver:
    """Resolves and manages plugin dependencies."""

    def __init__(self, marketplace: 'PluginMarketplace'):
        self.marketplace = marketplace

    def resolve_dependencies(self, plugin_id: str) -> List[str]:
        """Resolve all dependencies for a plugin."""
        resolved = []
        to_resolve = [plugin_id]
        visited = set()

        while to_resolve:
            current = to_resolve.pop(0)
            if current in visited:
                continue

            visited.add(current)
            plugin = self.marketplace.get_plugin_metadata(current)

            if plugin:
                resolved.append(current)
                for dep in plugin.dependencies:
                    if dep not in visited:
                        to_resolve.append(dep)

        return resolved[1:]  # Exclude the original plugin

    def check_compatibility(self, plugin_id: str, docx2shelf_version: str) -> bool:
        """Check if plugin is compatible with current Docx2Shelf version."""
        plugin = self.marketplace.get_plugin_metadata(plugin_id)
        if not plugin or not plugin.compatibility:
            return True  # Assume compatible if no restrictions

        return docx2shelf_version in plugin.compatibility

    def get_dependency_tree(self, plugin_id: str) -> Dict[str, List[str]]:
        """Get full dependency tree for visualization."""
        tree = {}

        def build_tree(pid: str, level: int = 0):
            if level > 10:  # Prevent infinite recursion
                return

            plugin = self.marketplace.get_plugin_metadata(pid)
            if plugin:
                tree[pid] = plugin.dependencies
                for dep in plugin.dependencies:
                    build_tree(dep, level + 1)

        build_tree(plugin_id)
        return tree


class PluginMarketplace:
    """Main plugin marketplace interface."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".docx2shelf" / "marketplace"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "marketplace.db"
        self.plugins_dir = self.cache_dir / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)

        self.api_base = "https://marketplace.docx2shelf.io/api/v1"
        self.cdn_base = "https://cdn.docx2shelf.io/plugins"

        self.certifier = PluginCertificationChecker()
        self.dependency_resolver = PluginDependencyResolver(self)

        self._init_database()

    def _init_database(self):
        """Initialize local marketplace database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    author TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    homepage TEXT,
                    repository TEXT,
                    license TEXT,
                    dependencies TEXT NOT NULL,
                    compatibility TEXT NOT NULL,
                    download_url TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    cached_at REAL NOT NULL
                )
            """)


            conn.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    plugin_id TEXT PRIMARY KEY,
                    download_count INTEGER DEFAULT 0,
                    weekly_downloads INTEGER DEFAULT 0,
                    monthly_downloads INTEGER DEFAULT 0,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS installed_plugins (
                    plugin_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    install_path TEXT NOT NULL,
                    installed_at REAL NOT NULL,
                    auto_update BOOLEAN DEFAULT TRUE
                )
            """)

    def refresh_marketplace_data(self, force: bool = False) -> bool:
        """Refresh marketplace data from remote API."""
        try:
            # Check if cache is still fresh (1 hour)
            if not force and self.db_path.exists():
                cache_age = time.time() - self.db_path.stat().st_mtime
                if cache_age < 3600:  # 1 hour
                    return True

            # Fetch plugins list
            response = requests.get(f"{self.api_base}/plugins", timeout=30)
            response.raise_for_status()
            plugins_data = response.json()

            # Update local database
            with sqlite3.connect(self.db_path) as conn:
                # Clear old data
                conn.execute("DELETE FROM plugins")
                conn.execute("DELETE FROM stats")

                # Insert new data
                for plugin_data in plugins_data.get('plugins', []):
                    metadata = PluginMetadata(**plugin_data['metadata'])
                    stats = PluginStats(**plugin_data.get('stats', {}))

                    # Insert plugin
                    conn.execute("""
                        INSERT INTO plugins VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metadata.id, metadata.name, metadata.version, metadata.author,
                        metadata.description, metadata.category, json.dumps(metadata.tags),
                        metadata.homepage, metadata.repository, metadata.license,
                        json.dumps(metadata.dependencies), json.dumps(metadata.compatibility),
                        metadata.download_url, metadata.file_size, metadata.checksum,
                        metadata.created_at, metadata.updated_at, time.time()
                    ))

                    # Insert stats
                    conn.execute("""
                        INSERT INTO stats VALUES (?, ?, ?, ?, ?)
                    """, (
                        stats.plugin_id, stats.download_count, stats.weekly_downloads,
                        stats.monthly_downloads, stats.last_updated
                    ))

            return True

        except Exception as e:
            print(f"Failed to refresh marketplace data: {e}")
            return False

    def search_plugins(self, query: str = "", category: str = "",
                      tags: List[str] = None, sort_by: str = "popularity") -> List[PluginMetadata]:
        """Search for plugins in the marketplace."""
        self.refresh_marketplace_data()

        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT p.*, s.download_count
                FROM plugins p
                LEFT JOIN stats s ON p.id = s.plugin_id
                WHERE 1=1
            """
            params = []

            if query:
                sql += " AND (p.name LIKE ? OR p.description LIKE ? OR p.tags LIKE ?)"
                query_param = f"%{query}%"
                params.extend([query_param, query_param, query_param])

            if category:
                sql += " AND p.category = ?"
                params.append(category)

            if tags:
                for tag in tags:
                    sql += " AND p.tags LIKE ?"
                    params.append(f"%{tag}%")

            # Sort order
            if sort_by == "popularity":
                sql += " ORDER BY s.download_count DESC"
            elif sort_by == "recent":
                sql += " ORDER BY p.updated_at DESC"
            elif sort_by == "name":
                sql += " ORDER BY p.name ASC"

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                metadata = PluginMetadata(
                    id=row[0], name=row[1], version=row[2], author=row[3],
                    description=row[4], category=row[5], tags=json.loads(row[6]),
                    homepage=row[7], repository=row[8], license=row[9],
                    dependencies=json.loads(row[10]), compatibility=json.loads(row[11]),
                    download_url=row[12], file_size=row[13], checksum=row[14],
                    created_at=row[15], updated_at=row[16]
                )
                results.append(metadata)

            return results

    def get_plugin_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get metadata for a specific plugin."""
        self.refresh_marketplace_data()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
            row = cursor.fetchone()

            if row:
                return PluginMetadata(
                    id=row[0], name=row[1], version=row[2], author=row[3],
                    description=row[4], category=row[5], tags=json.loads(row[6]),
                    homepage=row[7], repository=row[8], license=row[9],
                    dependencies=json.loads(row[10]), compatibility=json.loads(row[11]),
                    download_url=row[12], file_size=row[13], checksum=row[14],
                    created_at=row[15], updated_at=row[16]
                )

        return None

    def get_plugin_stats(self, plugin_id: str) -> Optional[PluginStats]:
        """Get statistics for a specific plugin."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM stats WHERE plugin_id = ?", (plugin_id,))
            row = cursor.fetchone()

            if row:
                return PluginStats(
                    plugin_id=row[0], download_count=row[1], weekly_downloads=row[2],
                    monthly_downloads=row[3], last_updated=row[4]
                )

        return None


    def install_plugin(self, plugin_id: str, auto_update: bool = True) -> bool:
        """Install a plugin from the marketplace."""
        plugin = self.get_plugin_metadata(plugin_id)
        if not plugin:
            print(f"Plugin {plugin_id} not found")
            return False

        # Check compatibility
        if not self.dependency_resolver.check_compatibility(plugin_id, "1.2.8"):
            print(f"Plugin {plugin_id} is not compatible with this version")
            return False

        # Resolve dependencies
        dependencies = self.dependency_resolver.resolve_dependencies(plugin_id)

        # Install dependencies first
        for dep_id in dependencies:
            if not self.is_plugin_installed(dep_id):
                print(f"Installing dependency: {dep_id}")
                if not self.install_plugin(dep_id, auto_update):
                    print(f"Failed to install dependency: {dep_id}")
                    return False

        # Download plugin
        try:
            temp_dir = Path(tempfile.mkdtemp())
            download_path = temp_dir / f"{plugin_id}.zip"

            print(f"Downloading {plugin.name}...")
            urlretrieve(plugin.download_url, download_path)

            # Verify checksum
            with open(download_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            if file_hash != plugin.checksum:
                print(f"Checksum verification failed for {plugin.name}")
                return False

            # Extract plugin
            install_path = self.plugins_dir / plugin_id
            install_path.mkdir(exist_ok=True)

            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(install_path)

            # Validate plugin
            is_valid, issues = self.certifier.validate_plugin_code(install_path)
            if not is_valid:
                print(f"Plugin validation failed: {'; '.join(issues)}")
                shutil.rmtree(install_path)
                return False

            # Record installation
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO installed_plugins VALUES (?, ?, ?, ?, ?)
                """, (plugin_id, plugin.version, str(install_path), time.time(), auto_update))

            print(f"Successfully installed {plugin.name} v{plugin.version}")
            return True

        except Exception as e:
            print(f"Failed to install {plugin.name}: {e}")
            return False

        finally:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        if not self.is_plugin_installed(plugin_id):
            print(f"Plugin {plugin_id} is not installed")
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT install_path FROM installed_plugins WHERE plugin_id = ?",
                (plugin_id,)
            )
            row = cursor.fetchone()

            if row:
                install_path = Path(row[0])
                if install_path.exists():
                    shutil.rmtree(install_path)

                conn.execute("DELETE FROM installed_plugins WHERE plugin_id = ?", (plugin_id,))
                print(f"Successfully uninstalled {plugin_id}")
                return True

        return False

    def is_plugin_installed(self, plugin_id: str) -> bool:
        """Check if a plugin is installed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM installed_plugins WHERE plugin_id = ?",
                (plugin_id,)
            )
            return cursor.fetchone() is not None

    def list_installed_plugins(self) -> List[Tuple[str, str, str]]:
        """List all installed plugins."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ip.plugin_id, ip.version, p.name
                FROM installed_plugins ip
                LEFT JOIN plugins p ON ip.plugin_id = p.id
            """)
            return cursor.fetchall()

    def update_plugin(self, plugin_id: str) -> bool:
        """Update an installed plugin to the latest version."""
        if not self.is_plugin_installed(plugin_id):
            return False

        # Get current and latest versions
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT version FROM installed_plugins WHERE plugin_id = ?",
                (plugin_id,)
            )
            current_version = cursor.fetchone()[0]

        latest_plugin = self.get_plugin_metadata(plugin_id)
        if not latest_plugin or latest_plugin.version == current_version:
            return True  # Already up to date

        # Uninstall old version and install new one
        self.uninstall_plugin(plugin_id)
        return self.install_plugin(plugin_id)

    def get_categories(self) -> List[str]:
        """Get list of all plugin categories."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT category FROM plugins ORDER BY category")
            return [row[0] for row in cursor.fetchall()]

    def get_featured_plugins(self, limit: int = 10) -> List[PluginMetadata]:
        """Get featured/popular plugins."""
        return self.search_plugins(sort_by="popularity")[:limit]


def create_marketplace_instance(cache_dir: Optional[Path] = None) -> PluginMarketplace:
    """Create a configured marketplace instance."""
    return PluginMarketplace(cache_dir)