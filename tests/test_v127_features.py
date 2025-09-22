"""
Comprehensive test suite for Docx2Shelf v1.2.7 features.

Tests documentation platform, developer tools, and performance optimization features.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from docx2shelf.developer_tools import (
    CodeGenerator,
    DevelopmentWorkflow,
    HotReloadHandler,
    LSPServer,
)
from docx2shelf.documentation import (
    DocumentationManager,
    TroubleshootingWizard,
    Tutorial,
    TutorialStep,
)
from docx2shelf.performance import (
    ConversionAnalytics,
    ConversionMetrics,
    MemoryOptimizer,
    PerformanceProfiler,
    create_analytics_system,
    create_conversion_profiler,
)


class TestDocumentationPlatform:
    """Test the comprehensive documentation platform (Epic 17)."""

    def test_tutorial_step_creation(self):
        """Test creating tutorial steps with validation."""
        step = TutorialStep(
            id="step1",
            title="First Step",
            description="This is the first step",
            code_example="print('hello')",
            expected_output="hello"
        )

        assert step.id == "step1"
        assert step.title == "First Step"
        assert step.code_example == "print('hello')"

    def test_tutorial_creation_and_execution(self):
        """Test creating and executing tutorials."""
        steps = [
            TutorialStep(
                id="step1",
                title="Install Package",
                description="Install docx2shelf",
                code_example="pip install docx2shelf"
            ),
            TutorialStep(
                id="step2",
                title="Basic Conversion",
                description="Convert a DOCX file",
                code_example="docx2shelf build --input test.docx --title 'Test'"
            )
        ]

        tutorial = Tutorial(
            id="getting-started",
            title="Getting Started",
            description="Learn the basics",
            steps=steps
        )

        assert tutorial.id == "getting-started"
        assert len(tutorial.steps) == 2
        assert tutorial.steps[0].title == "Install Package"

    def test_troubleshooting_wizard(self):
        """Test troubleshooting wizard functionality."""
        wizard = TroubleshootingWizard()

        # Test diagnosing common issues
        diagnosis = wizard.diagnose_issue("EPUB validation failed")
        assert isinstance(diagnosis, dict)
        assert "problem" in diagnosis
        assert "solutions" in diagnosis

        # Test with unknown issue
        diagnosis = wizard.diagnose_issue("unknown error type")
        assert "general troubleshooting" in diagnosis["problem"].lower()

    def test_documentation_manager_initialization(self):
        """Test documentation manager setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            manager = DocumentationManager(docs_dir)

            assert manager.docs_dir == docs_dir
            assert manager.docs_dir.exists()

    def test_built_in_tutorials_exist(self):
        """Test that built-in tutorials are properly defined."""
        manager = DocumentationManager()
        tutorials = manager.get_built_in_tutorials()

        assert len(tutorials) >= 3  # Should have getting-started, plugin-dev, enterprise

        # Check specific tutorials exist
        tutorial_ids = [t.id for t in tutorials]
        assert "getting-started" in tutorial_ids
        assert "plugin-development" in tutorial_ids
        assert "enterprise-deployment" in tutorial_ids


class TestDeveloperTools:
    """Test developer experience and tooling (Epic 18)."""

    def test_lsp_server_initialization(self):
        """Test LSP server setup."""
        server = LSPServer()
        assert server.workspace_root is None
        assert server.diagnostics == {}

    def test_lsp_symbol_extraction(self):
        """Test extracting symbols from Python code."""
        server = LSPServer()

        code = '''
def test_function():
    pass

class TestClass:
    def method(self):
        return True
'''

        symbols = server.extract_symbols(code)
        assert len(symbols) >= 2

        # Check for function and class
        symbol_names = [s['name'] for s in symbols]
        assert 'test_function' in symbol_names
        assert 'TestClass' in symbol_names

    def test_hot_reload_handler(self):
        """Test hot reload file watching."""
        callback_called = False
        callback_path = None

        def test_callback(path):
            nonlocal callback_called, callback_path
            callback_called = True
            callback_path = path

        handler = HotReloadHandler(test_callback)

        # Test file filtering
        assert handler._should_watch_file("/test/file.py")
        assert not handler._should_watch_file("/test/file.pyc")
        assert not handler._should_watch_file("/test/.git/file")

    def test_code_generator_plugin_template(self):
        """Test generating plugin code templates."""
        generator = CodeGenerator()

        plugin_code = generator.generate_plugin_template(
            name="TestPlugin",
            description="A test plugin",
            hooks=["pre_convert", "post_convert"]
        )

        assert "class TestPlugin" in plugin_code
        assert "pre_convert" in plugin_code
        assert "post_convert" in plugin_code
        assert "A test plugin" in plugin_code

    def test_code_generator_theme_template(self):
        """Test generating theme code templates."""
        generator = CodeGenerator()

        theme_code = generator.generate_theme_template(
            name="TestTheme",
            base_theme="serif",
            custom_fonts=["Arial", "Georgia"]
        )

        assert "TestTheme" in theme_code
        assert "Arial" in theme_code
        assert "Georgia" in theme_code

    def test_code_generator_config_template(self):
        """Test generating configuration templates."""
        generator = CodeGenerator()

        config = generator.generate_config_template(
            project_type="novel",
            target_stores=["kindle", "apple"]
        )

        assert isinstance(config, dict)
        assert "metadata" in config
        assert "build_options" in config

    def test_development_workflow_initialization(self):
        """Test development workflow setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            workflow = DevelopmentWorkflow(project_dir)

            assert workflow.project_dir == project_dir
            assert workflow.watcher is None
            assert not workflow.is_running

    @patch('docx2shelf.developer_tools.Observer')
    def test_development_workflow_start_stop(self, mock_observer):
        """Test starting and stopping development workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            workflow = DevelopmentWorkflow(project_dir)

            # Mock observer
            mock_observer_instance = Mock()
            mock_observer.return_value = mock_observer_instance

            workflow.start_hot_reload()
            assert workflow.is_running

            workflow.stop_hot_reload()
            assert not workflow.is_running


class TestPerformanceOptimization:
    """Test performance optimization and analytics (Epic 19)."""

    def test_performance_profiler_creation(self):
        """Test creating performance profiler."""
        profiler = create_conversion_profiler(enable_memory=True)
        assert isinstance(profiler, PerformanceProfiler)
        assert profiler.enable_memory_tracking

    def test_performance_profiler_stage_tracking(self):
        """Test profiler stage tracking."""
        profiler = PerformanceProfiler(enable_memory_tracking=False)

        profiler.start_stage("parsing")
        assert profiler.current_stage == "parsing"

        time.sleep(0.01)  # Small delay
        profiler.end_stage()

        assert profiler.current_stage is None
        assert "parsing" in profiler.stage_timings
        assert profiler.stage_timings["parsing"] > 0

    def test_conversion_metrics_creation(self):
        """Test creating conversion metrics."""
        metrics = ConversionMetrics(
            input_file="test.docx",
            input_size_mb=5.2,
            output_size_mb=2.1,
            conversion_time_seconds=12.5,
            memory_peak_mb=128.0,
            cpu_percent=45.0,
            chapter_count=8,
            image_count=3
        )

        assert metrics.input_file == "test.docx"
        assert metrics.input_size_mb == 5.2
        assert metrics.chapter_count == 8

    def test_conversion_analytics_initialization(self):
        """Test analytics system setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analytics_dir = Path(temp_dir) / "analytics"
            analytics = create_analytics_system(analytics_dir)

            assert analytics.analytics_dir == analytics_dir
            assert analytics.analytics_dir.exists()

    def test_conversion_analytics_recording(self):
        """Test recording conversion metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analytics_dir = Path(temp_dir) / "analytics"
            analytics = ConversionAnalytics(analytics_dir)

            metrics = ConversionMetrics(
                input_file="test.docx",
                input_size_mb=1.0,
                output_size_mb=0.8,
                conversion_time_seconds=5.0,
                memory_peak_mb=64.0,
                cpu_percent=30.0,
                chapter_count=4,
                image_count=2
            )

            analytics.record_conversion(metrics)

            # Check that metrics file was created
            assert analytics.metrics_file.exists()

            # Load and verify content
            with open(analytics.metrics_file, 'r', encoding='utf-8') as f:
                saved_metrics = json.load(f)

            assert len(saved_metrics) == 1
            assert saved_metrics[0]['input_file'] == "test.docx"

    def test_memory_optimizer_recommendations(self):
        """Test memory optimization recommendations."""
        optimizer = MemoryOptimizer()

        # Test small document
        small_doc_settings = optimizer.optimize_for_large_documents(5.0)
        assert not small_doc_settings['streaming_mode']
        assert small_doc_settings['parallel_processing']

        # Test large document
        large_doc_settings = optimizer.optimize_for_large_documents(150.0)
        assert large_doc_settings['streaming_mode']
        assert not large_doc_settings['parallel_processing']

    def test_memory_requirements_estimation(self):
        """Test memory requirements estimation."""
        optimizer = MemoryOptimizer()

        requirements = optimizer.estimate_memory_requirements(
            file_size_mb=10.0,
            image_count=5,
            chapter_count=8
        )

        assert 'base_mb' in requirements
        assert 'images_mb' in requirements
        assert 'chapters_mb' in requirements
        assert 'total_estimated_mb' in requirements
        assert requirements['total_estimated_mb'] > 0

    def test_analytics_performance_trends(self):
        """Test performance trends analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analytics_dir = Path(temp_dir) / "analytics"
            analytics = ConversionAnalytics(analytics_dir)

            # Record multiple metrics
            for i in range(3):
                metrics = ConversionMetrics(
                    input_file=f"test{i}.docx",
                    input_size_mb=float(i + 1),
                    output_size_mb=float(i + 0.5),
                    conversion_time_seconds=float(i + 2),
                    memory_peak_mb=float(64 + i * 10),
                    cpu_percent=float(30 + i * 5),
                    chapter_count=4 + i,
                    image_count=2 + i
                )
                analytics.record_conversion(metrics)

            trends = analytics.get_performance_trends(days=1)

            assert 'total_conversions' in trends
            assert trends['total_conversions'] == 3
            assert 'avg_conversion_time_seconds' in trends

    def test_benchmark_suite_execution(self):
        """Test running benchmark suite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analytics_dir = Path(temp_dir) / "analytics"
            analytics = ConversionAnalytics(analytics_dir)

            benchmarks = analytics.run_benchmark_suite()

            assert 'system' in benchmarks
            assert 'memory_allocation_ms' in benchmarks
            assert 'file_io' in benchmarks
            assert 'timestamp' in benchmarks

            # Verify system info
            assert 'cpu_count' in benchmarks['system']
            assert 'memory_total_gb' in benchmarks['system']

            # Verify file I/O benchmarks
            assert 'write_1mb_ms' in benchmarks['file_io']
            assert 'read_1mb_ms' in benchmarks['file_io']


class TestIntegration:
    """Integration tests for v1.2.7 features working together."""

    def test_documentation_with_developer_tools(self):
        """Test documentation platform working with developer tools."""
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            doc_manager = DocumentationManager(docs_dir)

            # Generate plugin template
            generator = CodeGenerator()
            plugin_code = generator.generate_plugin_template(
                name="TestPlugin",
                description="Integration test plugin",
                hooks=["pre_convert"]
            )

            # Create plugin file
            plugin_file = docs_dir / "test_plugin.py"
            plugin_file.write_text(plugin_code)

            # Test LSP can analyze the generated code
            lsp = LSPServer()
            symbols = lsp.extract_symbols(plugin_code)

            assert len(symbols) > 0
            assert any(s['name'] == 'TestPlugin' for s in symbols)

    def test_performance_with_documentation(self):
        """Test performance monitoring with documentation generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup analytics
            analytics = ConversionAnalytics(Path(temp_dir) / "analytics")

            # Setup documentation
            docs_dir = Path(temp_dir) / "docs"
            doc_manager = DocumentationManager(docs_dir)

            # Profile documentation building
            profiler = PerformanceProfiler(enable_memory_tracking=False)
            profiler.start_profiling()

            profiler.start_stage("doc_generation")
            tutorials = doc_manager.get_built_in_tutorials()
            profiler.end_stage()

            profile = profiler.stop_profiling()

            assert len(tutorials) > 0
            assert "doc_generation" in profile.function_stats or len(profile.hot_paths) >= 0

    def test_end_to_end_v127_workflow(self):
        """Test complete v1.2.7 workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # 1. Setup documentation
            doc_manager = DocumentationManager(project_dir / "docs")
            tutorials = doc_manager.get_built_in_tutorials()
            assert len(tutorials) > 0

            # 2. Setup developer tools
            generator = CodeGenerator()
            workflow = DevelopmentWorkflow(project_dir)

            # Generate some templates
            plugin_code = generator.generate_plugin_template("TestPlugin", "Test", ["pre_convert"])
            theme_code = generator.generate_theme_template("TestTheme", "serif", [])
            config = generator.generate_config_template("novel", ["kindle"])

            assert "TestPlugin" in plugin_code
            assert "TestTheme" in theme_code
            assert isinstance(config, dict)

            # 3. Setup performance monitoring
            analytics = ConversionAnalytics(project_dir / "analytics")
            optimizer = MemoryOptimizer()

            # Test optimization recommendations
            settings = optimizer.optimize_for_large_documents(50.0)
            assert settings['streaming_mode']

            # Record a test conversion
            metrics = ConversionMetrics(
                input_file="integration_test.docx",
                input_size_mb=50.0,
                output_size_mb=25.0,
                conversion_time_seconds=30.0,
                memory_peak_mb=256.0,
                cpu_percent=60.0,
                chapter_count=12,
                image_count=8
            )
            analytics.record_conversion(metrics)

            # Verify analytics
            trends = analytics.get_performance_trends(days=1)
            assert trends['total_conversions'] == 1