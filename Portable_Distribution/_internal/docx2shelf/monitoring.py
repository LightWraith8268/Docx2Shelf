"""
Production monitoring and observability for Docx2Shelf.

Provides health checks, metrics collection, and observability
for production deployments with Prometheus integration.
"""

from __future__ import annotations

import gc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class HealthStatus:
    """Health check status information."""
    healthy: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetricPoint:
    """Single metric measurement."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    help_text: str = ""


class MetricsCollector:
    """Collects and manages application metrics."""

    def __init__(self):
        self._metrics: Dict[str, MetricPoint] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = Lock()

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._counters[key] = self._counters.get(key, 0) + value
            self._metrics[key] = MetricPoint(
                name=name,
                value=self._counters[key],
                labels=labels or {},
                help_text=f"Counter: {name}"
            )

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            self._gauges[key] = value
            self._metrics[key] = MetricPoint(
                name=name,
                value=value,
                labels=labels or {},
                help_text=f"Gauge: {name}"
            )

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add observation to histogram metric."""
        with self._lock:
            key = self._get_metric_key(name, labels or {})
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)

            # Calculate statistics
            values = self._histograms[key]
            avg = sum(values) / len(values)

            # Update metric with average (simplified histogram)
            self._metrics[key] = MetricPoint(
                name=name,
                value=avg,
                labels=labels or {},
                help_text=f"Histogram average: {name}"
            )

    def get_metrics(self) -> List[MetricPoint]:
        """Get all current metrics."""
        with self._lock:
            return list(self._metrics.values())

    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        for metric in self.get_metrics():
            # Help text
            lines.append(f"# HELP {metric.name} {metric.help_text}")
            lines.append(f"# TYPE {metric.name} gauge")

            # Metric line
            labels_str = ""
            if metric.labels:
                label_pairs = [f'{k}="{v}"' for k, v in metric.labels.items()]
                labels_str = "{" + ",".join(label_pairs) + "}"

            lines.append(f"{metric.name}{labels_str} {metric.value}")

        return "\n".join(lines) + "\n"

    def _get_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate unique key for metric with labels."""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}#{label_str}"


class HealthChecker:
    """Manages health checks for the application."""

    def __init__(self):
        self._checks: Dict[str, Callable[[], HealthStatus]] = {}
        self._cache: Dict[str, HealthStatus] = {}
        self._cache_ttl = 30  # Cache health check results for 30 seconds

    def register_check(self, name: str, check_func: Callable[[], HealthStatus]):
        """Register a health check function."""
        self._checks[name] = check_func

    def run_check(self, name: str) -> HealthStatus:
        """Run a specific health check."""
        if name not in self._checks:
            return HealthStatus(
                healthy=False,
                message=f"Health check '{name}' not found"
            )

        # Check cache
        if name in self._cache:
            cached = self._cache[name]
            age = (datetime.now(timezone.utc) - cached.timestamp).total_seconds()
            if age < self._cache_ttl:
                return cached

        # Run check
        try:
            result = self._checks[name]()
            self._cache[name] = result
            return result
        except Exception as e:
            result = HealthStatus(
                healthy=False,
                message=f"Health check failed: {e}",
                details={"error": str(e)}
            )
            self._cache[name] = result
            return result

    def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all registered health checks."""
        return {name: self.run_check(name) for name in self._checks}

    def get_overall_health(self) -> HealthStatus:
        """Get overall application health status."""
        all_checks = self.run_all_checks()

        if not all_checks:
            return HealthStatus(
                healthy=True,
                message="No health checks registered",
                details={"check_count": 0}
            )

        failed_checks = [name for name, status in all_checks.items() if not status.healthy]

        if failed_checks:
            return HealthStatus(
                healthy=False,
                message=f"Health checks failed: {', '.join(failed_checks)}",
                details={
                    "failed_checks": failed_checks,
                    "total_checks": len(all_checks)
                }
            )

        return HealthStatus(
            healthy=True,
            message="All health checks passed",
            details={"total_checks": len(all_checks)}
        )


class SystemMonitor:
    """Monitors system resources and application performance."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.process = psutil.Process()

    def collect_system_metrics(self):
        """Collect system resource metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.set_gauge("system_cpu_usage_percent", cpu_percent)

        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics.set_gauge("system_memory_usage_percent", memory.percent)
        self.metrics.set_gauge("system_memory_available_bytes", memory.available)
        self.metrics.set_gauge("system_memory_total_bytes", memory.total)

        # Disk metrics
        disk = psutil.disk_usage('/')
        self.metrics.set_gauge("system_disk_usage_percent",
                              (disk.used / disk.total) * 100)
        self.metrics.set_gauge("system_disk_free_bytes", disk.free)
        self.metrics.set_gauge("system_disk_total_bytes", disk.total)

        # Process metrics
        self.metrics.set_gauge("process_memory_rss_bytes",
                              self.process.memory_info().rss)
        self.metrics.set_gauge("process_memory_vms_bytes",
                              self.process.memory_info().vms)
        self.metrics.set_gauge("process_cpu_percent",
                              self.process.cpu_percent())

        # Python garbage collection
        gc_stats = gc.get_stats()
        for i, stats in enumerate(gc_stats):
            self.metrics.set_gauge(f"python_gc_generation_{i}_collections",
                                  stats['collections'])
            self.metrics.set_gauge(f"python_gc_generation_{i}_collected",
                                  stats['collected'])
            self.metrics.set_gauge(f"python_gc_generation_{i}_uncollectable",
                                  stats['uncollectable'])


class ConversionMonitor:
    """Monitors EPUB conversion operations."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def record_conversion_start(self, input_format: str, input_size_bytes: int):
        """Record the start of a conversion operation."""
        self.metrics.increment_counter(
            "conversions_started_total",
            labels={"input_format": input_format}
        )
        self.metrics.set_gauge(
            "conversion_input_size_bytes",
            input_size_bytes,
            labels={"input_format": input_format}
        )

    def record_conversion_complete(self, input_format: str, duration_seconds: float,
                                  output_size_bytes: int, success: bool = True):
        """Record the completion of a conversion operation."""
        status = "success" if success else "failure"

        self.metrics.increment_counter(
            "conversions_completed_total",
            labels={"input_format": input_format, "status": status}
        )

        self.metrics.observe_histogram(
            "conversion_duration_seconds",
            duration_seconds,
            labels={"input_format": input_format}
        )

        if success:
            self.metrics.set_gauge(
                "conversion_output_size_bytes",
                output_size_bytes,
                labels={"input_format": input_format}
            )

    def record_conversion_error(self, input_format: str, error_type: str):
        """Record a conversion error."""
        self.metrics.increment_counter(
            "conversion_errors_total",
            labels={"input_format": input_format, "error_type": error_type}
        )


class ObservabilityManager:
    """Central manager for application observability."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self.system_monitor = SystemMonitor(self.metrics)
        self.conversion_monitor = ConversionMonitor(self.metrics)

        # Register default health checks
        self._register_default_health_checks()

    def _register_default_health_checks(self):
        """Register default health checks."""
        self.health_checker.register_check("system_resources", self._check_system_resources)
        self.health_checker.register_check("disk_space", self._check_disk_space)
        self.health_checker.register_check("memory_usage", self._check_memory_usage)

    def _check_system_resources(self) -> HealthStatus:
        """Check overall system resource availability."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            if cpu_percent > 90:
                return HealthStatus(
                    healthy=False,
                    message=f"High CPU usage: {cpu_percent:.1f}%",
                    details={"cpu_percent": cpu_percent}
                )

            if memory.percent > 90:
                return HealthStatus(
                    healthy=False,
                    message=f"High memory usage: {memory.percent:.1f}%",
                    details={"memory_percent": memory.percent}
                )

            return HealthStatus(
                healthy=True,
                message="System resources healthy",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent
                }
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"Failed to check system resources: {e}"
            )

    def _check_disk_space(self) -> HealthStatus:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100

            if usage_percent > 90:
                return HealthStatus(
                    healthy=False,
                    message=f"Low disk space: {usage_percent:.1f}% used",
                    details={"disk_usage_percent": usage_percent}
                )

            return HealthStatus(
                healthy=True,
                message=f"Disk space healthy: {usage_percent:.1f}% used",
                details={"disk_usage_percent": usage_percent}
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"Failed to check disk space: {e}"
            )

    def _check_memory_usage(self) -> HealthStatus:
        """Check memory usage of current process."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            if memory_percent > 80:
                return HealthStatus(
                    healthy=False,
                    message=f"High process memory usage: {memory_percent:.1f}%",
                    details={
                        "memory_percent": memory_percent,
                        "rss_bytes": memory_info.rss
                    }
                )

            return HealthStatus(
                healthy=True,
                message=f"Process memory healthy: {memory_percent:.1f}%",
                details={
                    "memory_percent": memory_percent,
                    "rss_bytes": memory_info.rss
                }
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                message=f"Failed to check memory usage: {e}"
            )

    def start_monitoring(self):
        """Start background monitoring tasks."""
        # Collect initial system metrics
        self.system_monitor.collect_system_metrics()

    def get_health_endpoint_data(self) -> Dict[str, Any]:
        """Get data for health check endpoint."""
        overall_health = self.health_checker.get_overall_health()
        all_checks = self.health_checker.run_all_checks()

        return {
            "status": "healthy" if overall_health.healthy else "unhealthy",
            "message": overall_health.message,
            "timestamp": overall_health.timestamp.isoformat(),
            "checks": {
                name: {
                    "healthy": status.healthy,
                    "message": status.message,
                    "details": status.details
                }
                for name, status in all_checks.items()
            }
        }

    def get_metrics_endpoint_data(self) -> str:
        """Get metrics data in Prometheus format."""
        # Update system metrics before returning
        self.system_monitor.collect_system_metrics()
        return self.metrics.get_prometheus_format()


# Global observability instance
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """Get the global observability manager instance."""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager()
        _observability_manager.start_monitoring()
    return _observability_manager


def record_conversion_metrics(input_format: str, input_size: int,
                            duration: float, output_size: int, success: bool = True):
    """Convenience function to record conversion metrics."""
    monitor = get_observability_manager().conversion_monitor
    monitor.record_conversion_start(input_format, input_size)
    monitor.record_conversion_complete(input_format, duration, output_size, success)


def record_conversion_error(input_format: str, error_type: str):
    """Convenience function to record conversion errors."""
    monitor = get_observability_manager().conversion_monitor
    monitor.record_conversion_error(input_format, error_type)