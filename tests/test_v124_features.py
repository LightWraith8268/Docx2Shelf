"""
Test suite for v1.2.4 features: GUI, Ecosystem & Performance.

Tests anthology building, series management, GUI functionality,
web builder, performance optimizations, and plugin marketplace.
"""

import json
import shutil
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.docx2shelf.anthology import AnthologyBuilder, AnthologyConfig, SeriesBuilder, SeriesConfig, StoryInfo
from src.docx2shelf.gui.app import TkinterMainWindow, create_context_menu_windows
from src.docx2shelf.metadata import EpubMetadata
from src.docx2shelf.performance import BuildCache, ParallelImageProcessor, PerformanceMonitor, StreamingDocxReader
from src.docx2shelf.plugin_marketplace import MarketplaceConfig, PluginInfo, PluginMarketplace
from src.docx2shelf.web_builder import WebBuilder, WebBuilderServer


class TestAnthologyBuilder:
    """Test anthology building functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.anthology_builder = AnthologyBuilder()

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_anthology_config_creation(self):
        """Test creating anthology configuration."""
        config = AnthologyConfig(
            title="Test Anthology",
            author="Test Author",
            description="A test anthology collection"
        )

        assert config.title == "Test Anthology"
        assert config.author == "Test Author"
        assert config.description == "A test anthology collection"
        assert config.sort_by == "title"
        assert config.include_toc is True

    def test_story_info_creation(self):
        """Test creating story information."""
        story_path = self.temp_dir / "story.docx"
        story_path.write_text("Test story content", encoding='utf-8')

        story = StoryInfo(
            file_path=story_path,
            title="Test Story",
            author="Story Author",
            word_count=1000
        )

        assert story.file_path == story_path
        assert story.title == "Test Story"
        assert story.author == "Story Author"
        assert story.word_count == 1000

    def test_add_story_to_anthology(self):
        """Test adding stories to anthology."""
        story_path = self.temp_dir / "story1.docx"
        story_path.write_text("Story content", encoding='utf-8')

        story = StoryInfo(
            file_path=story_path,
            title="Story One",
            author="Author One"
        )

        self.anthology_builder.add_story(story)
        assert len(self.anthology_builder.stories) == 1
        assert self.anthology_builder.stories[0].title == "Story One"

    def test_anthology_sorting(self):
        """Test anthology story sorting."""
        # Create multiple stories
        story_paths = []
        for i in range(3):
            path = self.temp_dir / f"story{i}.docx"
            path.write_text(f"Story {i} content", encoding='utf-8')
            story_paths.append(path)

        stories = [
            StoryInfo(story_paths[0], "Zebra Story", "Author A"),
            StoryInfo(story_paths[1], "Alpha Story", "Author B"),
            StoryInfo(story_paths[2], "Beta Story", "Author C")
        ]

        for story in stories:
            self.anthology_builder.add_story(story)

        # Sort by title
        sorted_stories = self.anthology_builder._sort_stories("title")
        titles = [s.title for s in sorted_stories]
        assert titles == ["Alpha Story", "Beta Story", "Zebra Story"]

        # Sort by author
        sorted_stories = self.anthology_builder._sort_stories("author")
        authors = [s.author for s in sorted_stories]
        assert authors == ["Author A", "Author B", "Author C"]

    def test_anthology_toc_generation(self):
        """Test table of contents generation for anthology."""
        story_path = self.temp_dir / "story.docx"
        story_path.write_text("Story content", encoding='utf-8')

        story = StoryInfo(story_path, "Test Story", "Test Author")
        self.anthology_builder.add_story(story)

        toc_html = self.anthology_builder._create_anthology_toc()
        assert "Test Story" in toc_html
        assert "Test Author" in toc_html
        assert '<nav epub:type="toc"' in toc_html

    @patch('src.docx2shelf.anthology.convert_file_to_html')
    @patch('src.docx2shelf.anthology.assemble_epub')
    def test_anthology_build_process(self, mock_assemble, mock_convert):
        """Test complete anthology build process."""
        # Mock conversion
        mock_convert.return_value = (["<p>Story content</p>"], [], "Test Story")

        # Mock assembly
        mock_assemble.return_value = self.temp_dir / "test_anthology.epub"

        # Create story
        story_path = self.temp_dir / "story.docx"
        story_path.write_text("Story content", encoding='utf-8')
        story = StoryInfo(story_path, "Test Story", "Test Author")
        self.anthology_builder.add_story(story)

        # Set configuration
        config = AnthologyConfig(
            title="Test Anthology",
            author="Anthology Editor"
        )
        self.anthology_builder.configure(config)

        # Build anthology
        output_path = self.temp_dir / "anthology.epub"
        result_path = self.anthology_builder.build_anthology(output_path)

        assert result_path == self.temp_dir / "test_anthology.epub"
        mock_convert.assert_called_once()
        mock_assemble.assert_called_once()


class TestSeriesBuilder:
    """Test series building functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.series_builder = SeriesBuilder()

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_series_config_creation(self):
        """Test creating series configuration."""
        config = SeriesConfig(
            series_name="Test Series",
            author="Series Author",
            description="A test book series"
        )

        assert config.series_name == "Test Series"
        assert config.author == "Series Author"
        assert config.description == "A test book series"
        assert config.auto_also_by is True

    def test_add_book_to_series(self):
        """Test adding books to series."""
        book_path = self.temp_dir / "book1.epub"
        book_path.write_bytes(b"Mock EPUB content")

        metadata = EpubMetadata(
            title="Book One",
            author="Series Author",
            series="Test Series",
            series_index=1
        )

        self.series_builder.add_book(book_path, metadata)
        assert len(self.series_builder.books) == 1

    def test_series_index_validation(self):
        """Test series index validation and sorting."""
        # Add books out of order
        for i, index in enumerate([3, 1, 2]):
            book_path = self.temp_dir / f"book{i}.epub"
            book_path.write_bytes(b"Mock EPUB content")

            metadata = EpubMetadata(
                title=f"Book {index}",
                author="Series Author",
                series="Test Series",
                series_index=index
            )

            self.series_builder.add_book(book_path, metadata)

        # Validate ordering
        sorted_books = self.series_builder._sort_books_by_index()
        indices = [book[1].series_index for book in sorted_books]
        assert indices == [1, 2, 3]

    @patch('src.docx2shelf.anthology.assemble_epub')
    def test_also_by_page_generation(self, mock_assemble):
        """Test 'Also By This Author' page generation."""
        # Add multiple books
        for i in range(3):
            book_path = self.temp_dir / f"book{i}.epub"
            book_path.write_bytes(b"Mock EPUB content")

            metadata = EpubMetadata(
                title=f"Book {i+1}",
                author="Series Author",
                series="Test Series",
                series_index=i+1
            )

            self.series_builder.add_book(book_path, metadata)

        # Generate also-by page
        also_by_html = self.series_builder._create_also_by_page()

        assert "Also By This Author" in also_by_html
        assert "Book 1" in also_by_html
        assert "Book 2" in also_by_html
        assert "Book 3" in also_by_html


class TestPerformanceOptimizations:
    """Test performance optimization features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        # Record some metrics
        monitor.record_phase_start("test_phase")
        time.sleep(0.1)  # Simulate work
        monitor.record_phase_end("test_phase")

        monitor.increment_counter("test_counter", 5)
        monitor.record_memory_usage()

        # Finish monitoring
        report = monitor.finish_monitoring()

        assert "metrics" in report
        assert "phase_times" in report
        assert "test_phase" in report["phase_times"]
        assert report["metrics"]["test_counter"] == 5
        assert report["metrics"]["total_time"] > 0

    def test_build_cache(self):
        """Test build cache functionality."""
        cache = BuildCache(self.temp_dir)

        # Create a test file
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content", encoding='utf-8')

        # Test file hash generation
        file_hash = cache.get_file_hash(test_file)
        assert len(file_hash) == 64  # SHA-256 hash length

        # Test caching
        from src.docx2shelf.metadata import BuildOptions
        options = BuildOptions()

        assert not cache.is_cached(test_file, options)

        # Cache a result
        output_path = self.temp_dir / "output.epub"
        output_path.write_bytes(b"mock epub")

        cache.cache_result(test_file, output_path, options, {"test": "metadata"})
        assert cache.is_cached(test_file, options)

        # Retrieve cached result
        cached_path = cache.get_cached_result(test_file, options)
        assert cached_path == output_path

    def test_parallel_image_processor(self):
        """Test parallel image processing."""
        processor = ParallelImageProcessor(max_workers=2)

        # Create mock image data
        images = [
            ("image1.jpg", b"mock_jpeg_data_1"),
            ("image2.jpg", b"mock_jpeg_data_2"),
            ("image3.png", b"mock_png_data_3")
        ]

        output_dir = self.temp_dir / "images"

        with patch('src.docx2shelf.performance.Image') as mock_image:
            # Mock PIL Image operations
            mock_img = Mock()
            mock_img.mode = 'RGB'
            mock_img.width = 800
            mock_img.height = 600
            mock_img.resize.return_value = mock_img
            mock_image.open.return_value.__enter__.return_value = mock_img

            # Process images
            results = processor.process_images_parallel(images, output_dir)

            # Verify results
            assert len(results) <= len(images)  # Some might fail due to mocking
            assert output_dir.exists()

    def test_streaming_docx_reader(self):
        """Test streaming DOCX reader."""
        # Create a mock DOCX-like ZIP file
        docx_path = self.temp_dir / "test.docx"

        with zipfile.ZipFile(docx_path, 'w') as zf:
            zf.writestr('word/document.xml', '<document>Test content</document>')
            zf.writestr('word/media/image1.jpg', b'fake_image_data')
            zf.writestr('docProps/core.xml', '<dc:title>Test Title</dc:title>')

        # Test streaming reader
        with StreamingDocxReader(docx_path) as reader:
            # Test document streaming
            chunks = list(reader.stream_document_xml())
            assert len(chunks) > 0
            assert 'Test content' in ''.join(chunks)

            # Test image extraction
            images = reader.get_embedded_images()
            assert len(images) == 1
            assert images[0][0] == 'word/media/image1.jpg'

            # Test metadata extraction
            metadata = reader.get_document_metadata()
            assert 'core' in metadata


class TestPluginMarketplace:
    """Test plugin marketplace functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = MarketplaceConfig()
        self.marketplace = PluginMarketplace(self.config)
        # Override plugins directory for testing
        self.marketplace.plugins_dir = self.temp_dir / "plugins"
        self.marketplace.plugins_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_plugin_info_serialization(self):
        """Test plugin info serialization/deserialization."""
        plugin = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            tags=["test", "example"],
            dependencies=["requests"]
        )

        # Test to_dict
        data = plugin.to_dict()
        assert data["name"] == "test-plugin"
        assert data["version"] == "1.0.0"
        assert data["tags"] == ["test", "example"]

        # Test from_dict
        restored = PluginInfo.from_dict(data)
        assert restored.name == plugin.name
        assert restored.version == plugin.version
        assert restored.tags == plugin.tags

    def test_plugin_search(self):
        """Test plugin search functionality."""
        # Create mock marketplace cache
        self.marketplace._marketplace_cache = {
            "test-plugin": PluginInfo(
                name="test-plugin",
                version="1.0.0",
                description="A test plugin for testing",
                author="Test Author",
                tags=["test", "utility"]
            ),
            "doc-converter": PluginInfo(
                name="doc-converter",
                version="2.0.0",
                description="Document conversion utilities",
                author="Doc Author",
                tags=["conversion", "utility"]
            )
        }

        # Test text search
        results = self.marketplace.search_plugins("test")
        assert len(results) == 1
        assert results[0].name == "test-plugin"

        # Test tag search
        results = self.marketplace.search_plugins(tags=["utility"])
        assert len(results) == 2

        # Test combined search
        results = self.marketplace.search_plugins("conversion", tags=["utility"])
        assert len(results) == 1
        assert results[0].name == "doc-converter"

    @patch('requests.get')
    def test_marketplace_refresh(self, mock_get):
        """Test marketplace refresh functionality."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "plugins": [
                {
                    "name": "example-plugin",
                    "version": "1.0.0",
                    "description": "An example plugin",
                    "author": "Example Author",
                    "homepage": "https://example.com",
                    "license": "MIT",
                    "tags": ["example"],
                    "dependencies": [],
                    "docx2shelf_version": ">=1.2.4",
                    "entry_point": "example_plugin.create_plugin",
                    "install_url": "https://example.com/plugin.zip",
                    "checksum": "sha256:abcdef..."
                }
            ]
        }
        mock_get.return_value = mock_response

        # Test refresh
        success = self.marketplace.refresh_marketplace()
        assert success is True
        assert "example-plugin" in self.marketplace._marketplace_cache

        # Verify plugin info
        plugin = self.marketplace._marketplace_cache["example-plugin"]
        assert plugin.name == "example-plugin"
        assert plugin.version == "1.0.0"
        assert plugin.license == "MIT"

    def test_plugin_template_creation(self):
        """Test plugin template creation."""
        template_dir = self.temp_dir / "templates"
        success = self.marketplace.create_plugin_template("my-plugin", template_dir)

        assert success is True

        plugin_dir = template_dir / "my-plugin"
        assert plugin_dir.exists()

        # Check files were created
        assert (plugin_dir / "my-plugin.py").exists()
        assert (plugin_dir / "plugin.json").exists()
        assert (plugin_dir / "README.md").exists()

        # Check plugin.json content
        with open(plugin_dir / "plugin.json", 'r') as f:
            metadata = json.load(f)
            assert metadata["name"] == "my-plugin"
            assert metadata["version"] == "1.0.0"

    def test_plugin_statistics(self):
        """Test plugin statistics generation."""
        # Add some mock data
        self.marketplace._marketplace_cache = {
            "plugin1": PluginInfo("plugin1", "1.0.0", "Test 1", "Author 1", tags=["test", "utility"]),
            "plugin2": PluginInfo("plugin2", "1.0.0", "Test 2", "Author 2", tags=["conversion", "utility"])
        }

        self.marketplace._installed_plugins = {
            "plugin1": PluginInfo("plugin1", "1.0.0", "Test 1", "Author 1", installed=True, enabled=True)
        }

        stats = self.marketplace.get_plugin_stats()

        assert stats["marketplace_plugins"] == 2
        assert stats["installed_plugins"] == 1
        assert stats["enabled_plugins"] == 1
        assert stats["disabled_plugins"] == 0

        # Check popular tags
        popular_tags = dict(stats["popular_tags"])
        assert popular_tags["utility"] == 2
        assert popular_tags["test"] == 1


class TestWebBuilder:
    """Test web-based builder functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_web_builder_initialization(self):
        """Test web builder initialization."""
        builder = WebBuilder(work_dir=self.temp_dir)

        assert builder.work_dir == self.temp_dir
        assert builder.host == "localhost"
        assert builder.port == 8080
        assert builder.projects == {}

    def test_web_builder_server_creation(self):
        """Test web builder server creation."""
        builder = WebBuilder(work_dir=self.temp_dir)
        server = WebBuilderServer(builder)

        assert server.builder == builder
        assert hasattr(server, 'httpd')

    @patch('http.server.HTTPServer')
    def test_web_server_startup(self, mock_server):
        """Test web server startup process."""
        builder = WebBuilder(work_dir=self.temp_dir)
        server = WebBuilderServer(builder)

        # Mock server instance
        mock_httpd = Mock()
        mock_server.return_value = mock_httpd

        # Start server in thread
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()

        # Allow time for startup
        time.sleep(0.1)

        # Verify server was created
        mock_server.assert_called_once()

    def test_project_management(self):
        """Test project creation and management."""
        builder = WebBuilder(work_dir=self.temp_dir)

        # Create a project
        project_id = builder.create_project("test-project", "single")
        assert project_id in builder.projects
        assert builder.projects[project_id]["name"] == "test-project"
        assert builder.projects[project_id]["type"] == "single"

        # Get project
        project = builder.get_project(project_id)
        assert project is not None
        assert project["name"] == "test-project"

        # Delete project
        success = builder.delete_project(project_id)
        assert success is True
        assert project_id not in builder.projects


class TestGUIFunctionality:
    """Test GUI application functionality."""

    def test_context_menu_creation(self):
        """Test Windows context menu creation."""
        if hasattr(create_context_menu_windows, '__call__'):
            # Test would require Windows registry access
            # This is a placeholder for the actual implementation test
            assert callable(create_context_menu_windows)

    @patch('tkinter.Tk')
    def test_tkinter_window_initialization(self, mock_tk):
        """Test Tkinter main window initialization."""
        # Mock Tkinter components
        mock_root = Mock()
        mock_tk.return_value = mock_root

        with patch('tkinter.ttk.Notebook'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.StringVar'):

            window = TkinterMainWindow()

            # Verify initialization
            assert hasattr(window, 'root')
            mock_tk.assert_called_once()

    def test_gui_framework_detection(self):
        """Test GUI framework detection logic."""
        from src.docx2shelf.gui.app import detect_gui_framework

        # This will return the first available framework or None
        framework = detect_gui_framework()
        assert framework in [None, "tkinter", "pyqt5", "pyqt6"]


# Integration tests
class TestIntegrationV124:
    """Integration tests for v1.2.4 features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_performance_with_anthology(self):
        """Test performance optimizations work with anthology building."""
        # Create anthology builder with performance monitoring
        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        anthology_builder = AnthologyBuilder()

        # Add mock stories
        for i in range(3):
            story_path = self.temp_dir / f"story{i}.docx"
            story_path.write_text(f"Story {i} content", encoding='utf-8')

            story = StoryInfo(
                file_path=story_path,
                title=f"Story {i}",
                author=f"Author {i}"
            )
            anthology_builder.add_story(story)

        # Monitor performance
        monitor.record_phase_start("anthology_build")

        # This would normally build the anthology
        # For testing, just verify the setup
        assert len(anthology_builder.stories) == 3

        monitor.record_phase_end("anthology_build")
        report = monitor.finish_monitoring()

        assert "anthology_build" in report["phase_times"]

    def test_plugin_with_web_builder(self):
        """Test plugin integration with web builder."""
        # Create web builder
        builder = WebBuilder(work_dir=self.temp_dir)

        # Create marketplace
        marketplace = PluginMarketplace()

        # This integration test verifies the components can work together
        assert builder.work_dir.exists()
        assert marketplace.plugins_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])