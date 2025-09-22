"""
Comprehensive test suite for v1.2.6 features.

Tests operational excellence, deployment monitoring, advanced plugin system,
and enterprise integration capabilities.
"""

import shutil
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.docx2shelf.enterprise_api import (
    APIKey,
    ConversionJob,
    DatabaseManager,
    EnterpriseAPIManager,
    RateLimiter,
    WebhookManager,
)
from src.docx2shelf.monitoring import (
    ConversionMonitor,
    HealthChecker,
    HealthStatus,
    MetricsCollector,
    ObservabilityManager,
    SystemMonitor,
)
from src.docx2shelf.plugin_sandbox import (
    AdvancedPluginManager,
    HotReloadablePlugin,
    PluginExecutionContext,
    PluginResourceMonitor,
    ResourceLimits,
)


class TestProductionMonitoring:
    """Test production deployment and monitoring features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_metrics_collector(self):
        """Test metrics collection functionality."""
        collector = MetricsCollector()

        # Test counter
        collector.increment_counter("test_counter", 1.0, {"type": "unit_test"})
        collector.increment_counter("test_counter", 2.0, {"type": "unit_test"})

        # Test gauge
        collector.set_gauge("test_gauge", 42.0, {"type": "unit_test"})

        # Test histogram
        collector.observe_histogram("test_histogram", 1.5, {"type": "unit_test"})
        collector.observe_histogram("test_histogram", 2.5, {"type": "unit_test"})

        # Verify metrics
        metrics = collector.get_metrics()
        assert len(metrics) == 3

        # Test Prometheus format
        prometheus_output = collector.get_prometheus_format()
        assert "test_counter" in prometheus_output
        assert "test_gauge" in prometheus_output
        assert "test_histogram" in prometheus_output

    def test_health_checker(self):
        """Test health check system."""
        checker = HealthChecker()

        # Register test health check
        def test_check():
            return HealthStatus(healthy=True, message="Test check passed")

        checker.register_check("test_check", test_check)

        # Run individual check
        result = checker.run_check("test_check")
        assert result.healthy is True
        assert "Test check passed" in result.message

        # Run all checks
        all_results = checker.run_all_checks()
        assert "test_check" in all_results

        # Test overall health
        overall = checker.get_overall_health()
        assert overall.healthy is True

    def test_health_checker_failure(self):
        """Test health check failure scenarios."""
        checker = HealthChecker()

        # Register failing check
        def failing_check():
            return HealthStatus(healthy=False, message="Test failure")

        checker.register_check("failing_check", failing_check)

        # Test overall health with failure
        overall = checker.get_overall_health()
        assert overall.healthy is False
        assert "failing_check" in overall.message

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_system_monitor(self, mock_process, mock_disk, mock_memory, mock_cpu):
        """Test system resource monitoring."""
        # Mock system metrics
        mock_cpu.return_value = 25.0
        mock_memory.return_value = Mock(percent=50.0, available=8000000000, total=16000000000)
        mock_disk.return_value = Mock(used=500000000000, total=1000000000000, free=500000000000)
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=500000000, vms=1000000000)
        mock_process_instance.cpu_percent.return_value = 15.0
        mock_process.return_value = mock_process_instance

        collector = MetricsCollector()
        monitor = SystemMonitor(collector)

        # Collect metrics
        monitor.collect_system_metrics()

        # Verify metrics were collected
        metrics = collector.get_metrics()
        metric_names = [m.name for m in metrics]

        assert "system_cpu_usage_percent" in metric_names
        assert "system_memory_usage_percent" in metric_names
        assert "process_memory_rss_bytes" in metric_names

    def test_conversion_monitor(self):
        """Test conversion operation monitoring."""
        collector = MetricsCollector()
        monitor = ConversionMonitor(collector)

        # Record conversion start
        monitor.record_conversion_start("docx", 1024000)

        # Record conversion completion
        monitor.record_conversion_complete("docx", 15.5, 2048000, True)

        # Record conversion error
        monitor.record_conversion_error("docx", "invalid_format")

        # Verify metrics
        metrics = collector.get_metrics()
        metric_names = [m.name for m in metrics]

        assert "conversions_started_total" in metric_names
        assert "conversions_completed_total" in metric_names
        assert "conversion_errors_total" in metric_names

    def test_observability_manager_integration(self):
        """Test complete observability manager integration."""
        manager = ObservabilityManager()

        # Test health endpoint data
        health_data = manager.get_health_endpoint_data()
        assert "status" in health_data
        assert "checks" in health_data

        # Test metrics endpoint data
        metrics_data = manager.get_metrics_endpoint_data()
        assert isinstance(metrics_data, str)
        assert len(metrics_data) > 0


class TestAdvancedPluginSystem:
    """Test advanced plugin system with sandboxing and hot-reload."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / "plugins"
        self.plugin_dir.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_resource_limits(self):
        """Test plugin resource limit configuration."""
        limits = ResourceLimits(
            max_memory_mb=128,
            max_cpu_percent=25.0,
            max_execution_time_seconds=10
        )

        context = PluginExecutionContext(
            plugin_id="test_plugin",
            temp_dir=self.temp_dir / "test_plugin",
            resource_limits=limits
        )

        assert context.resource_limits.max_memory_mb == 128
        assert context.resource_limits.max_cpu_percent == 25.0

    def test_plugin_execution_context(self):
        """Test plugin execution context setup."""
        context = PluginExecutionContext(
            plugin_id="test_plugin",
            temp_dir=self.temp_dir / "test_plugin",
            resource_limits=ResourceLimits(),
            sandbox_enabled=True
        )

        # Add forbidden modules
        context.forbidden_modules.add("os")
        context.forbidden_modules.add("subprocess")

        assert "os" in context.forbidden_modules
        assert context.sandbox_enabled is True

    def test_hot_reloadable_plugin(self):
        """Test hot-reload plugin functionality."""
        # Create test plugin file
        plugin_file = self.plugin_dir / "test_plugin.py"
        plugin_content = '''
def test_function():
    return "Hello from plugin v1"
'''
        plugin_file.write_text(plugin_content)

        # Create hot-reloadable plugin
        plugin = HotReloadablePlugin(plugin_file, "test_plugin")

        # Test initial load
        assert plugin.load() is True
        func = plugin.get_plugin_function("test_function")
        assert func is not None
        assert func() == "Hello from plugin v1"

        # Simulate file modification
        time.sleep(0.1)  # Ensure modification time difference
        updated_content = '''
def test_function():
    return "Hello from plugin v2"
'''
        plugin_file.write_text(updated_content)

        # Test hot reload
        assert plugin.is_outdated() is True
        assert plugin.load() is True
        func = plugin.get_plugin_function("test_function")
        assert func() == "Hello from plugin v2"

    def test_plugin_manager_discovery(self):
        """Test plugin discovery and management."""
        # Create test plugins
        plugin1_file = self.plugin_dir / "plugin1.py"
        plugin1_file.write_text('''
def process_data(data):
    return f"Processed: {data}"
''')

        plugin2_file = self.plugin_dir / "plugin2.py"
        plugin2_file.write_text('''
def transform_text(text):
    return text.upper()
''')

        # Create plugin manager
        manager = AdvancedPluginManager(self.plugin_dir)
        manager.start()

        # Test plugin discovery
        assert "plugin1" in manager.plugins
        assert "plugin2" in manager.plugins

        # Test plugin execution
        result1 = manager.execute_plugin_function("plugin1", "process_data", "test_data")
        assert result1 == "Processed: test_data"

        result2 = manager.execute_plugin_function("plugin2", "transform_text", "hello")
        assert result2 == "HELLO"

        manager.stop()

    @patch('psutil.Process')
    def test_plugin_resource_monitoring(self, mock_process):
        """Test plugin resource monitoring."""
        # Mock process metrics
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=100*1024*1024)  # 100MB
        mock_process.return_value = mock_process_instance

        context = PluginExecutionContext(
            plugin_id="test_plugin",
            temp_dir=self.temp_dir / "test_plugin",
            resource_limits=ResourceLimits(max_memory_mb=256),
            sandbox_enabled=False  # Disable sandbox for testing
        )

        monitor = PluginResourceMonitor(context)
        monitor.start_monitoring()

        # Let monitor run briefly
        time.sleep(0.2)

        results = monitor.stop_monitoring()

        assert "execution_time_seconds" in results
        assert "peak_memory_mb" in results
        assert results["execution_time_seconds"] > 0

    def test_plugin_metrics_collection(self):
        """Test plugin performance metrics collection."""
        # Create simple plugin
        plugin_file = self.plugin_dir / "metrics_test.py"
        plugin_file.write_text('''
import time

def slow_function():
    time.sleep(0.1)
    return "completed"
''')

        manager = AdvancedPluginManager(self.plugin_dir)
        manager.sandbox_enabled = False  # Disable sandbox for testing
        manager.start()

        # Execute plugin multiple times
        for _ in range(3):
            manager.execute_plugin_function("metrics_test", "slow_function")

        # Check metrics
        metrics = manager.get_plugin_metrics("metrics_test")
        assert metrics is not None
        assert metrics.execution_count == 3
        assert metrics.total_execution_time > 0
        assert metrics.average_execution_time > 0

        manager.stop()


class TestEnterpriseIntegration:
    """Test enterprise integration and API features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_database_manager_initialization(self):
        """Test database manager initialization."""
        db_manager = DatabaseManager(self.db_path)
        assert self.db_path.exists()

        # Test table creation
        with db_manager._get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "conversion_jobs" in tables
            assert "api_keys" in tables
            assert "webhook_endpoints" in tables
            assert "audit_log" in tables

    def test_conversion_job_lifecycle(self):
        """Test complete conversion job lifecycle."""
        db_manager = DatabaseManager(self.db_path)

        # Create job
        job = ConversionJob(
            job_id=str(uuid.uuid4()),
            input_file_path="/test/input.docx",
            user_id="test_user",
            metadata={"title": "Test Document"},
            file_size_bytes=1024000
        )

        job_id = db_manager.create_conversion_job(job)
        assert job_id == job.job_id

        # Retrieve job
        retrieved_job = db_manager.get_conversion_job(job_id)
        assert retrieved_job is not None
        assert retrieved_job.input_file_path == "/test/input.docx"
        assert retrieved_job.metadata["title"] == "Test Document"

        # Update job
        retrieved_job.status = "running"
        retrieved_job.progress_percent = 50.0
        db_manager.update_conversion_job(retrieved_job)

        # Verify update
        updated_job = db_manager.get_conversion_job(job_id)
        assert updated_job.status == "running"
        assert updated_job.progress_percent == 50.0

        # List jobs
        jobs = db_manager.list_conversion_jobs(user_id="test_user")
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id

    def test_api_key_management(self):
        """Test API key creation and validation."""
        db_manager = DatabaseManager(self.db_path)

        # Create API key
        api_key = APIKey(
            key_id="test12345",
            key_hash="abcdef123456",
            name="Test API Key",
            user_id="test_user",
            permissions=["read", "write"]
        )

        db_manager.create_api_key(api_key)

        # Retrieve API key
        retrieved_key = db_manager.get_api_key("test12345")
        assert retrieved_key is not None
        assert retrieved_key.name == "Test API Key"
        assert "read" in retrieved_key.permissions

        # Update usage
        db_manager.update_api_key_usage("test12345")
        updated_key = db_manager.get_api_key("test12345")
        assert updated_key.last_used_at is not None

    def test_audit_logging(self):
        """Test audit event logging."""
        db_manager = DatabaseManager(self.db_path)

        # Log audit event
        db_manager.log_audit_event(
            user_id="test_user",
            action="job.created",
            resource_type="conversion_job",
            resource_id="test_job_123",
            details={"file": "test.docx"},
            ip_address="192.168.1.100"
        )

        # Verify audit log
        with db_manager._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM audit_log WHERE user_id = ?", ("test_user",))
            log_entry = cursor.fetchone()
            assert log_entry is not None
            assert log_entry[2] == "test_user"  # user_id
            assert log_entry[3] == "job.created"  # action

    @patch('requests.post')
    def test_webhook_manager(self, mock_post):
        """Test webhook notification system."""
        mock_post.return_value.status_code = 200

        db_manager = DatabaseManager(self.db_path)
        webhook_manager = WebhookManager(db_manager)

        # Add webhook endpoint
        from src.docx2shelf.enterprise_api import WebhookEndpoint
        endpoint = WebhookEndpoint(
            url="https://example.com/webhook",
            secret="test_secret",
            events=["job.completed"],
            enabled=True
        )
        webhook_manager.add_endpoint(endpoint)

        # Send webhook
        test_data = {"job_id": "123", "status": "completed"}
        webhook_manager.send_webhook("job.completed", test_data)

        # Verify webhook was called
        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[1]["json"]["event"] == "job.completed"
        assert call_args[1]["json"]["data"] == test_data

    def test_rate_limiter(self):
        """Test API rate limiting."""
        rate_limiter = RateLimiter()

        # Test normal usage
        assert rate_limiter.is_allowed("client1", requests_per_minute=5) is True
        assert rate_limiter.is_allowed("client1", requests_per_minute=5) is True

        # Test rate limit exceeded
        for _ in range(10):
            rate_limiter.is_allowed("client2", requests_per_minute=5)

        # Should be rate limited now
        assert rate_limiter.is_allowed("client2", requests_per_minute=5) is False

        # Different client should not be affected
        assert rate_limiter.is_allowed("client3", requests_per_minute=5) is True

    def test_enterprise_api_manager_integration(self):
        """Test complete enterprise API manager integration."""
        api_manager = EnterpriseAPIManager(self.db_path)

        # Generate API key
        api_key = api_manager.generate_api_key("test_key", "test_user", ["read", "write"])
        assert len(api_key) > 20

        # Authenticate API key
        authenticated_key = api_manager.authenticate_api_key(api_key)
        assert authenticated_key is not None
        assert authenticated_key.user_id == "test_user"

        # Create conversion job
        job = api_manager.create_conversion_job(
            input_file_path="/test/input.docx",
            user_id="test_user",
            metadata={"title": "Test Document"}
        )
        assert job.job_id is not None
        assert job.user_id == "test_user"

        # Update job status
        api_manager.update_job_status(job.job_id, "running", progress_percent=25.0)

        # Get queue status
        queue_status = api_manager.get_job_queue_status()
        assert "pending_jobs" in queue_status
        assert "running_jobs" in queue_status


class TestKubernetesIntegration:
    """Test Kubernetes deployment integration."""

    def test_kubernetes_manifests_existence(self):
        """Test that Kubernetes manifests exist and are valid."""
        k8s_dir = Path("S:/coding/Docx2Shelf/k8s")
        assert k8s_dir.exists()

        # Check required manifest files
        required_files = [
            "deployment.yaml",
            "service.yaml",
            "configmap.yaml",
            "hpa.yaml",
            "servicemonitor.yaml"
        ]

        for file_name in required_files:
            manifest_file = k8s_dir / file_name
            assert manifest_file.exists(), f"Missing Kubernetes manifest: {file_name}"

    def test_helm_chart_structure(self):
        """Test Helm chart structure and files."""
        helm_dir = Path("S:/coding/Docx2Shelf/helm/docx2shelf")
        assert helm_dir.exists()

        # Check Chart.yaml
        chart_file = helm_dir / "Chart.yaml"
        assert chart_file.exists()

        # Check values.yaml
        values_file = helm_dir / "values.yaml"
        assert values_file.exists()

        # Check templates directory
        templates_dir = helm_dir / "templates"
        assert templates_dir.exists()

        # Check helper templates
        helpers_file = templates_dir / "_helpers.tpl"
        assert helpers_file.exists()

    def test_openapi_specification(self):
        """Test OpenAPI specification exists and is valid."""
        api_spec_file = Path("S:/coding/Docx2Shelf/api-spec.yaml")
        assert api_spec_file.exists()

        # Basic validation of YAML structure
        import yaml
        with open(api_spec_file) as f:
            spec = yaml.safe_load(f)

        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec

        # Check version matches
        assert spec["info"]["version"] == "1.2.6"


class TestIntegrationV126:
    """Integration tests for v1.2.6 features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_monitoring_and_plugin_integration(self):
        """Test integration between monitoring and plugin systems."""
        # Create observability manager
        observability = ObservabilityManager()

        # Create plugin manager
        plugin_dir = self.temp_dir / "plugins"
        plugin_dir.mkdir()
        plugin_manager = AdvancedPluginManager(plugin_dir)

        # Create test plugin
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_file.write_text('''
def process_data(data):
    return f"Processed: {data}"
''')

        plugin_manager.sandbox_enabled = False  # Disable for testing
        plugin_manager.start()

        # Execute plugin with monitoring
        observability.conversion_monitor.record_conversion_start("plugin", 1024)

        result = plugin_manager.execute_plugin_function("test_plugin", "process_data", "test")
        assert result == "Processed: test"

        observability.conversion_monitor.record_conversion_complete("plugin", 1.0, 2048, True)

        # Verify metrics were recorded
        metrics = observability.metrics.get_metrics()
        metric_names = [m.name for m in metrics]
        assert "conversions_started_total" in metric_names

        plugin_manager.stop()

    def test_enterprise_api_with_monitoring(self):
        """Test enterprise API integration with monitoring."""
        # Create enterprise API manager
        db_path = self.temp_dir / "enterprise.db"
        api_manager = EnterpriseAPIManager(db_path)

        # Create observability manager
        observability = ObservabilityManager()

        # Create conversion job with monitoring
        observability.conversion_monitor.record_conversion_start("docx", 1024000)

        job = api_manager.create_conversion_job(
            input_file_path="/test/input.docx",
            user_id="test_user"
        )

        # Simulate job processing with monitoring
        api_manager.update_job_status(job.job_id, "running", progress_percent=50.0)
        observability.conversion_monitor.record_conversion_complete("docx", 15.0, 2048000, True)
        api_manager.update_job_status(job.job_id, "completed", progress_percent=100.0)

        # Verify job was tracked
        completed_job = api_manager.db_manager.get_conversion_job(job.job_id)
        assert completed_job.status == "completed"
        assert completed_job.progress_percent == 100.0

        # Verify metrics were collected
        metrics = observability.metrics.get_metrics()
        assert len(metrics) > 0

    def test_end_to_end_v126_workflow(self):
        """Test complete v1.2.6 workflow integration."""
        # Initialize all components
        db_path = self.temp_dir / "v126_test.db"
        api_manager = EnterpriseAPIManager(db_path)
        observability = ObservabilityManager()

        plugin_dir = self.temp_dir / "plugins"
        plugin_dir.mkdir()
        plugin_manager = AdvancedPluginManager(plugin_dir)

        # Create processing plugin
        plugin_file = plugin_dir / "processor.py"
        plugin_file.write_text('''
def convert_document(input_path, output_path):
    # Simulate document conversion
    import time
    time.sleep(0.1)
    return {"status": "success", "pages": 42}
''')

        plugin_manager.sandbox_enabled = False
        plugin_manager.start()

        # Generate API key
        api_key = api_manager.generate_api_key("integration_test", "test_user")
        authenticated_key = api_manager.authenticate_api_key(api_key)
        assert authenticated_key is not None

        # Create conversion job
        job = api_manager.create_conversion_job(
            input_file_path="/test/document.docx",
            user_id="test_user",
            metadata={"title": "Integration Test"}
        )

        # Process job with plugin and monitoring
        observability.conversion_monitor.record_conversion_start("docx", 1024000)
        api_manager.update_job_status(job.job_id, "running")

        # Execute conversion plugin
        result = plugin_manager.execute_plugin_function(
            "processor", "convert_document",
            "/test/document.docx", "/test/output.epub"
        )

        # Complete job
        observability.conversion_monitor.record_conversion_complete("docx", 2.5, 2048000, True)
        api_manager.update_job_status(job.job_id, "completed", progress_percent=100.0)

        # Verify complete workflow
        final_job = api_manager.db_manager.get_conversion_job(job.job_id)
        assert final_job.status == "completed"
        assert final_job.progress_percent == 100.0

        plugin_metrics = plugin_manager.get_plugin_metrics("processor")
        assert plugin_metrics.execution_count == 1

        system_metrics = observability.metrics.get_metrics()
        assert len(system_metrics) > 0

        # Verify health checks pass
        health_data = observability.get_health_endpoint_data()
        assert health_data["status"] == "healthy"

        plugin_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])