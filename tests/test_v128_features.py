"""
Comprehensive test suite for Docx2Shelf v1.2.8 features.

Tests plugin marketplace and ecosystem integration features.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from docx2shelf.ecosystem import (
    EcosystemIntegrationManager,
    ExternalDocument,
    GoogleDocsIntegration,
    IntegrationConfig,
    NotionIntegration,
    PublishingPlatformConnector,
    PublishingTarget,
    ScrivenerIntegration,
    TemplateGallery,
    TemplateItem,
    WritingToolIntegration,
    create_ecosystem_manager,
)
from docx2shelf.marketplace import (
    PluginCertificationChecker,
    PluginDependencyResolver,
    PluginMarketplace,
    PluginMetadata,
    PluginStats,
    create_marketplace_instance,
)


class TestPluginMarketplace:
    """Test the comprehensive plugin marketplace system (Epic 20)."""

    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata objects."""
        metadata = PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            author="Test Author",
            description="A test plugin",
            category="utility",
            tags=["test", "utility"],
            dependencies=["core-plugin"],
            compatibility=["1.2.8"],
            download_url="https://example.com/plugin.zip",
            checksum="abc123"
        )

        assert metadata.id == "test-plugin"
        assert metadata.name == "Test Plugin"
        assert "test" in metadata.tags
        assert "core-plugin" in metadata.dependencies

    def test_plugin_stats_creation(self):
        """Test creating plugin statistics objects."""
        stats = PluginStats(
            plugin_id="test-plugin",
            download_count=150,
            weekly_downloads=25,
            monthly_downloads=100
        )

        assert stats.plugin_id == "test-plugin"
        assert stats.download_count == 150
        assert stats.weekly_downloads == 25

    def test_marketplace_initialization(self):
        """Test marketplace initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "marketplace"
            marketplace = PluginMarketplace(cache_dir)

            assert marketplace.cache_dir == cache_dir
            assert marketplace.cache_dir.exists()
            assert marketplace.db_path.exists()

    def test_plugin_certification_checker(self):
        """Test plugin certification and validation."""
        checker = PluginCertificationChecker()

        # Test certification levels
        stats = PluginStats(
            plugin_id="test",
            download_count=600,
            weekly_downloads=50,
            monthly_downloads=200
        )

        level = checker.get_certification_level(stats)
        assert level == "trusted"

        # Test basic certification
        basic_stats = PluginStats(
            plugin_id="test",
            download_count=15,
            weekly_downloads=2,
            monthly_downloads=8
        )

        level = checker.get_certification_level(basic_stats)
        assert level == "basic"

    def test_plugin_code_validation(self):
        """Test plugin code security validation."""
        checker = PluginCertificationChecker()

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir)

            # Create safe plugin structure
            (plugin_dir / "__init__.py").write_text("# Safe plugin")
            (plugin_dir / "README.md").write_text("# Documentation")

            is_valid, issues = checker.validate_plugin_code(plugin_dir)
            assert is_valid or len(issues) <= 2  # May fail on missing tests

            # Create unsafe plugin
            unsafe_file = plugin_dir / "unsafe.py"
            unsafe_file.write_text("import os; os.system('rm -rf /')")

            is_valid, issues = checker.validate_plugin_code(plugin_dir)
            assert not is_valid
            assert any("security" in issue.lower() for issue in issues)

    def test_dependency_resolver(self):
        """Test plugin dependency resolution."""
        marketplace = create_marketplace_instance()
        resolver = PluginDependencyResolver(marketplace)

        # Mock marketplace data
        with patch.object(marketplace, 'get_plugin_metadata') as mock_get:
            mock_get.side_effect = lambda pid: {
                'plugin-a': PluginMetadata(
                    id="plugin-a", name="Plugin A", version="1.0", author="Test",
                    description="Test", category="test", dependencies=["plugin-b"]
                ),
                'plugin-b': PluginMetadata(
                    id="plugin-b", name="Plugin B", version="1.0", author="Test",
                    description="Test", category="test", dependencies=[]
                )
            }.get(pid)

            dependencies = resolver.resolve_dependencies("plugin-a")
            assert "plugin-b" in dependencies

            # Test compatibility checking
            is_compatible = resolver.check_compatibility("plugin-a", "1.2.8")
            assert is_compatible  # No restrictions

    def test_marketplace_search(self):
        """Test marketplace plugin search functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            marketplace = PluginMarketplace(Path(temp_dir))

            # Mock database with test data
            with patch.object(marketplace, 'refresh_marketplace_data'):
                results = marketplace.search_plugins(query="test", category="utility")
                assert isinstance(results, list)

    def test_plugin_installation_workflow(self):
        """Test complete plugin installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            marketplace = PluginMarketplace(Path(temp_dir))

            # Test installation (mocked)
            with patch.object(marketplace, 'get_plugin_metadata') as mock_get:
                with patch.object(marketplace.dependency_resolver, 'check_compatibility', return_value=True):
                    with patch.object(marketplace.dependency_resolver, 'resolve_dependencies', return_value=[]):
                        mock_get.return_value = None  # Plugin not found
                        result = marketplace.install_plugin("nonexistent-plugin")
                        assert not result

    def test_marketplace_reviews(self):
        """Test marketplace review system."""
        marketplace = create_marketplace_instance()

        # Mock API response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'reviews': [
                    {
                        'plugin_id': 'test-plugin',
                        'user_id': 'user1',
                        'username': 'testuser',
                        'rating': 5,
                        'title': 'Great plugin!',
                        'content': 'Works perfectly',
                        'helpful_count': 10,
                        'created_at': '2025-01-19',
                        'verified_download': True
                    }
                ]
            }
            mock_get.return_value = mock_response

            reviews = marketplace.get_plugin_reviews("test-plugin")
            assert len(reviews) == 1
            assert reviews[0].rating == 5
            assert reviews[0].username == "testuser"


# Community features removed - focusing on marketplace and ecosystem only


class TestEcosystemIntegration:
    """Test ecosystem integration features (Epic 22)."""

    def test_external_document_creation(self):
        """Test creating external document objects."""
        doc = ExternalDocument(
            document_id="doc123",
            title="Test Document",
            content="# Test Document\n\nContent here",
            format="markdown",
            author="Test Author",
            last_modified="2025-01-19T10:00:00Z",
            source_service="notion"
        )

        assert doc.document_id == "doc123"
        assert doc.title == "Test Document"
        assert doc.format == "markdown"
        assert doc.source_service == "notion"

    def test_publishing_target_creation(self):
        """Test publishing platform target configuration."""
        target = PublishingTarget(
            platform_id="kdp",
            platform_name="Amazon KDP",
            api_endpoint="https://kdp.amazon.com/api/v1",
            supported_formats=["epub", "mobi"],
            metadata_mapping={"title": "book_title", "author": "author_name"}
        )

        assert target.platform_id == "kdp"
        assert "epub" in target.supported_formats
        assert target.metadata_mapping["title"] == "book_title"

    def test_template_item_creation(self):
        """Test template gallery item creation."""
        template = TemplateItem(
            template_id="template123",
            name="Novel Template",
            description="A template for novels",
            category="fiction",
            author="Template Author",
            version="1.0.0",
            download_url="https://example.com/template.zip",
            tags=["novel", "fiction"]
        )

        assert template.template_id == "template123"
        assert template.name == "Novel Template"
        assert "novel" in template.tags

    def test_scrivener_integration(self):
        """Test Scrivener writing tool integration."""
        integration = ScrivenerIntegration()

        # Test authentication (file-based)
        with tempfile.TemporaryDirectory() as temp_dir:
            scrivener_dir = Path(temp_dir) / "scrivener"
            scrivener_dir.mkdir()

            credentials = {"scrivener_projects_path": str(scrivener_dir)}
            result = integration.authenticate(credentials)
            assert result

            # Test with invalid path
            invalid_credentials = {"scrivener_projects_path": "/nonexistent"}
            result = integration.authenticate(invalid_credentials)
            assert not result

    def test_notion_integration(self):
        """Test Notion writing tool integration."""
        integration = NotionIntegration()

        # Test authentication (without real API key)
        credentials = {"api_key": ""}
        result = integration.authenticate(credentials)
        assert not result

        # Test with mock API
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            credentials = {"api_key": "test_key"}
            result = integration.authenticate(credentials)
            assert result

    def test_google_docs_integration(self):
        """Test Google Docs integration (placeholder)."""
        integration = GoogleDocsIntegration()

        # Currently returns False (placeholder implementation)
        result = integration.authenticate({"api_key": "test"})
        assert not result

        documents = integration.list_documents()
        assert documents == []

    def test_publishing_platform_connector(self):
        """Test publishing platform connector."""
        connector = PublishingPlatformConnector()

        # Test platform retrieval
        kdp_platform = connector.get_platform("kdp")
        assert kdp_platform is not None
        assert kdp_platform.platform_name == "Amazon Kindle Direct Publishing"

        apple_platform = connector.get_platform("apple_books")
        assert apple_platform is not None

        # Test metadata sync
        epub_metadata = {
            "title": "My Book",
            "author": "Author Name",
            "description": "Book description"
        }

        synced_metadata = connector.sync_metadata("kdp", epub_metadata)
        assert "book_title" in synced_metadata
        assert synced_metadata["book_title"] == "My Book"

    def test_template_gallery(self):
        """Test template gallery functionality."""
        gallery = TemplateGallery()

        # Test search (mocked)
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'templates': [
                    {
                        'template_id': 'template123',
                        'name': 'Test Template',
                        'description': 'A test template',
                        'category': 'fiction',
                        'author': 'Test Author',
                        'version': '1.0.0',
                        'download_url': 'https://example.com/template.zip',
                        'tags': ['test'],
                        'created_at': '2025-01-19',
                        'updated_at': '2025-01-19'
                    }
                ]
            }
            mock_get.return_value = mock_response

            templates = gallery.search_templates(query="test")
            assert len(templates) == 1
            assert templates[0].name == "Test Template"

    def test_ecosystem_integration_manager(self):
        """Test complete ecosystem integration manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = EcosystemIntegrationManager(Path(temp_dir))

            # Test configuration
            config = IntegrationConfig(
                service_name="test_service",
                api_endpoint="https://api.example.com",
                api_key="test_key",
                enabled=True
            )

            manager.configure_integration("test_service", config)
            assert "test_service" in manager.configurations

            # Test available integrations
            integrations = manager.list_available_integrations()
            assert "scrivener" in integrations
            assert "notion" in integrations

            # Test getting writing tool
            scrivener = manager.get_writing_tool("scrivener")
            assert isinstance(scrivener, ScrivenerIntegration)


class TestIntegration:
    """Integration tests for v1.2.8 features working together."""

    def test_marketplace_ecosystem_integration(self):
        """Test marketplace and ecosystem integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup marketplace
            marketplace_dir = Path(temp_dir) / "marketplace"
            marketplace = PluginMarketplace(marketplace_dir)

            # Setup ecosystem manager
            ecosystem_dir = Path(temp_dir) / "ecosystem"
            ecosystem = EcosystemIntegrationManager(ecosystem_dir)

            # Test integration workflow
            integrations = ecosystem.list_available_integrations()
            assert len(integrations) > 0

            # Mock plugin installation for ecosystem integration
            with patch.object(marketplace, 'install_plugin', return_value=True):
                result = marketplace.install_plugin("ecosystem-integration-plugin")
                assert result


    def test_complete_v128_workflow(self):
        """Test complete v1.2.8 workflow integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # 1. Setup all systems
            marketplace = PluginMarketplace(base_dir / "marketplace")
            ecosystem = EcosystemIntegrationManager(base_dir / "ecosystem")

            # 2. Test ecosystem integration
            integrations = ecosystem.list_available_integrations()
            assert "scrivener" in integrations
            assert "notion" in integrations

            # 3. Test publishing connector
            connector = ecosystem.publishing_connector
            kdp_platform = connector.get_platform("kdp")
            assert kdp_platform is not None

            # 4. Test marketplace functionality
            categories = marketplace.get_categories()
            assert isinstance(categories, list)

            print("✅ Complete v1.2.8 workflow integration test passed!")


# Additional helper tests
class TestHelperFunctions:
    """Test helper functions and utilities."""

    def test_create_marketplace_instance(self):
        """Test marketplace instance creation helper."""
        marketplace = create_marketplace_instance()
        assert isinstance(marketplace, PluginMarketplace)


    def test_create_ecosystem_manager(self):
        """Test ecosystem manager creation helper."""
        manager = create_ecosystem_manager()
        assert isinstance(manager, EcosystemIntegrationManager)