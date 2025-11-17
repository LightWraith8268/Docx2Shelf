"""
Advanced plugin system with security isolation and hot-reload capabilities.

Provides sandboxing, resource monitoring, and zero-downtime plugin updates
for enterprise-grade plugin management.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import signal
import sys
import tempfile
import threading
import time

try:
    import resource
except ImportError:
    # resource module is Unix-only
    resource = None
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import psutil


@dataclass
class ResourceLimits:
    """Resource limits for plugin execution."""

    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    max_execution_time_seconds: int = 30
    max_file_descriptors: int = 100
    max_network_connections: int = 10
    max_disk_write_mb: int = 100


@dataclass
class PluginExecutionContext:
    """Context information for plugin execution."""

    plugin_id: str
    temp_dir: Path
    resource_limits: ResourceLimits
    allowed_modules: Set[str] = field(default_factory=set)
    forbidden_modules: Set[str] = field(default_factory=set)
    sandbox_enabled: bool = True


@dataclass
class PluginMetrics:
    """Metrics collected during plugin execution."""

    plugin_id: str
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    peak_memory_usage_mb: float = 0.0
    error_count: int = 0
    last_execution: Optional[datetime] = None
    last_error: Optional[str] = None


class SecurityViolationError(Exception):
    """Raised when plugin violates security constraints."""

    pass


class ResourceExhaustedError(Exception):
    """Raised when plugin exceeds resource limits."""

    pass


class PluginSandbox:
    """Provides security isolation for plugin execution."""

    def __init__(self, context: PluginExecutionContext):
        self.context = context
        self.original_modules = set(sys.modules.keys())
        self.resource_monitor = None

    def __enter__(self):
        """Enter sandbox environment."""
        if self.context.sandbox_enabled:
            self._setup_resource_limits()
            self._setup_import_restrictions()
            self._setup_file_system_restrictions()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox environment."""
        if self.context.sandbox_enabled:
            self._cleanup_imported_modules()
            self._cleanup_resources()

    def _setup_resource_limits(self):
        """Set up resource limits for the process."""
        if resource is None:
            print("Warning: Resource limits not available on this platform")
            return

        try:
            # Memory limit
            memory_limit = self.context.resource_limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

            # CPU time limit
            cpu_limit = self.context.resource_limits.max_execution_time_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

            # File descriptor limit
            fd_limit = self.context.resource_limits.max_file_descriptors
            resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))

        except (ValueError, OSError) as e:
            # Resource limits may not be available on all platforms
            print(f"Warning: Could not set resource limits: {e}")

    def _setup_import_restrictions(self):
        """Set up import restrictions for security."""
        # Handle different __builtins__ types across Python implementations
        if isinstance(__builtins__, dict):
            self.original_import = __builtins__["__import__"]
        else:
            self.original_import = __builtins__.__import__

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Check forbidden modules
            if name in self.context.forbidden_modules:
                raise SecurityViolationError(f"Import of module '{name}' is forbidden")

            # Check allowed modules (if whitelist is specified)
            if (
                self.context.allowed_modules
                and name not in self.context.allowed_modules
                and not any(
                    name.startswith(allowed + ".") for allowed in self.context.allowed_modules
                )
            ):
                raise SecurityViolationError(f"Import of module '{name}' is not allowed")

            return self.original_import(name, globals, locals, fromlist, level)

        if isinstance(__builtins__, dict):
            __builtins__["__import__"] = restricted_import
        else:
            __builtins__.__import__ = restricted_import

    def _setup_file_system_restrictions(self):
        """Set up file system access restrictions."""
        # Create isolated temp directory for plugin
        self.context.temp_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(self.context.temp_dir)

    def _cleanup_imported_modules(self):
        """Clean up modules imported during plugin execution."""
        current_modules = set(sys.modules.keys())
        new_modules = current_modules - self.original_modules

        for module_name in new_modules:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def _cleanup_resources(self):
        """Clean up resources used during execution."""
        # Restore original import function
        if hasattr(self, "original_import"):
            if isinstance(__builtins__, dict):
                __builtins__["__import__"] = self.original_import
            else:
                __builtins__.__import__ = self.original_import

        # Force garbage collection
        import gc

        gc.collect()


class PluginResourceMonitor:
    """Monitors resource usage during plugin execution."""

    def __init__(self, context: PluginExecutionContext):
        self.context = context
        self.process = psutil.Process()
        self.monitoring = False
        self.peak_memory = 0.0
        self.start_time = None
        self.monitor_thread = None

    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.start_time = time.time()
        self.peak_memory = 0.0
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        execution_time = time.time() - self.start_time if self.start_time else 0.0

        return {
            "execution_time_seconds": execution_time,
            "peak_memory_mb": self.peak_memory,
            "memory_limit_exceeded": self.peak_memory > self.context.resource_limits.max_memory_mb,
            "time_limit_exceeded": execution_time
            > self.context.resource_limits.max_execution_time_seconds,
        }

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Check memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                self.peak_memory = max(self.peak_memory, memory_mb)

                # Check limits
                if memory_mb > self.context.resource_limits.max_memory_mb:
                    raise ResourceExhaustedError(f"Memory limit exceeded: {memory_mb:.1f}MB")

                # Check execution time
                if self.start_time:
                    execution_time = time.time() - self.start_time
                    if execution_time > self.context.resource_limits.max_execution_time_seconds:
                        raise ResourceExhaustedError(
                            f"Execution time limit exceeded: {execution_time:.1f}s"
                        )

                time.sleep(0.1)  # Check every 100ms

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process might have ended
                break
            except ResourceExhaustedError:
                # Terminate the process
                self.monitoring = False
                os.kill(os.getpid(), signal.SIGTERM)
                break


class HotReloadablePlugin:
    """Plugin wrapper that supports hot reloading."""

    def __init__(self, plugin_path: Path, plugin_id: str):
        self.plugin_path = plugin_path
        self.plugin_id = plugin_id
        self.module = None
        self.last_modified = None
        self.load_error = None

    def load(self) -> bool:
        """Load or reload the plugin module."""
        try:
            current_modified = self.plugin_path.stat().st_mtime

            # Check if reload is needed
            if (
                self.module is None
                or self.last_modified is None
                or current_modified > self.last_modified
            ):

                # Unload existing module if it exists
                if self.module and hasattr(self.module, "__name__"):
                    module_name = self.module.__name__
                    if module_name in sys.modules:
                        del sys.modules[module_name]

                # Load the module
                spec = importlib.util.spec_from_file_location(
                    f"plugin_{self.plugin_id}", self.plugin_path
                )
                if spec and spec.loader:
                    self.module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.module)
                    self.last_modified = current_modified
                    self.load_error = None
                    return True

            return self.module is not None

        except Exception as e:
            self.load_error = str(e)
            return False

    def is_outdated(self) -> bool:
        """Check if plugin file has been modified since last load."""
        if not self.plugin_path.exists():
            return False

        current_modified = self.plugin_path.stat().st_mtime
        return self.last_modified is None or current_modified > self.last_modified

    def get_plugin_function(self, function_name: str) -> Optional[Callable]:
        """Get a function from the plugin module."""
        if self.module and hasattr(self.module, function_name):
            return getattr(self.module, function_name)
        return None


class AdvancedPluginManager:
    """Advanced plugin manager with sandboxing and hot-reload."""

    def __init__(self, plugin_dir: Path, default_limits: Optional[ResourceLimits] = None):
        self.plugin_dir = plugin_dir
        self.default_limits = default_limits or ResourceLimits()
        self.plugins: Dict[str, HotReloadablePlugin] = {}
        self.plugin_metrics: Dict[str, PluginMetrics] = {}
        self.hot_reload_enabled = True
        self.sandbox_enabled = True
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

    def start(self):
        """Start the plugin manager."""
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.discover_plugins()

        if self.hot_reload_enabled:
            self._start_hot_reload_monitoring()

    def stop(self):
        """Stop the plugin manager."""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join()

    def discover_plugins(self):
        """Discover and load plugins from the plugin directory."""
        for plugin_file in self.plugin_dir.glob("*.py"):
            if not plugin_file.name.startswith("_"):
                plugin_id = plugin_file.stem
                self.load_plugin(plugin_id, plugin_file)

    def load_plugin(self, plugin_id: str, plugin_path: Path) -> bool:
        """Load a specific plugin."""
        try:
            plugin = HotReloadablePlugin(plugin_path, plugin_id)
            if plugin.load():
                self.plugins[plugin_id] = plugin
                if plugin_id not in self.plugin_metrics:
                    self.plugin_metrics[plugin_id] = PluginMetrics(plugin_id=plugin_id)
                return True
            else:
                print(f"Failed to load plugin {plugin_id}: {plugin.load_error}")
                return False

        except Exception as e:
            print(f"Error loading plugin {plugin_id}: {e}")
            return False

    def unload_plugin(self, plugin_id: str):
        """Unload a specific plugin."""
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]

    def execute_plugin_function(self, plugin_id: str, function_name: str, *args, **kwargs) -> Any:
        """Execute a function from a plugin with sandboxing."""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        plugin = self.plugins[plugin_id]

        # Check for hot reload
        if self.hot_reload_enabled and plugin.is_outdated():
            plugin.load()

        # Get the function
        func = plugin.get_plugin_function(function_name)
        if not func:
            raise ValueError(f"Function '{function_name}' not found in plugin '{plugin_id}'")

        # Execute with monitoring and sandboxing
        return self._execute_with_sandbox(plugin_id, func, *args, **kwargs)

    def _execute_with_sandbox(self, plugin_id: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with sandbox and monitoring."""
        metrics = self.plugin_metrics[plugin_id]
        start_time = time.time()

        # Create execution context
        temp_dir = Path(tempfile.mkdtemp(prefix=f"plugin_{plugin_id}_"))
        context = PluginExecutionContext(
            plugin_id=plugin_id,
            temp_dir=temp_dir,
            resource_limits=self.default_limits,
            sandbox_enabled=self.sandbox_enabled,
        )

        # Set up forbidden modules for security
        context.forbidden_modules.update(
            {
                "os",
                "subprocess",
                "shutil",
                "sys",
                "importlib",
                "socket",
                "urllib",
                "requests",
                "ftplib",
                "smtplib",
            }
        )

        result = None
        error = None

        try:
            # Execute in sandbox
            with PluginSandbox(context):
                monitor = PluginResourceMonitor(context)
                monitor.start_monitoring()

                try:
                    result = func(*args, **kwargs)
                finally:
                    monitor_results = monitor.stop_monitoring()

                # Update metrics
                execution_time = time.time() - start_time
                metrics.execution_count += 1
                metrics.total_execution_time += execution_time
                metrics.average_execution_time = (
                    metrics.total_execution_time / metrics.execution_count
                )
                metrics.peak_memory_usage_mb = max(
                    metrics.peak_memory_usage_mb, monitor_results["peak_memory_mb"]
                )
                metrics.last_execution = datetime.now(timezone.utc)

        except Exception as e:
            error = str(e)
            metrics.error_count += 1
            metrics.last_error = error
            raise

        finally:
            # Cleanup temp directory
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e_cleanup:
                # Temp directory cleanup failed, but don't fail the entire operation
                print(f"Warning: Failed to cleanup temp directory {temp_dir}: {e_cleanup}")

        return result

    def get_plugin_metrics(self, plugin_id: str) -> Optional[PluginMetrics]:
        """Get metrics for a specific plugin."""
        return self.plugin_metrics.get(plugin_id)

    def get_all_plugin_metrics(self) -> Dict[str, PluginMetrics]:
        """Get metrics for all plugins."""
        return self.plugin_metrics.copy()

    def _start_hot_reload_monitoring(self):
        """Start monitoring for plugin file changes."""
        self._monitoring_thread = threading.Thread(
            target=self._hot_reload_monitor_loop, daemon=True
        )
        self._monitoring_thread.start()

    def _hot_reload_monitor_loop(self):
        """Monitor loop for hot reload."""
        while not self._stop_monitoring.wait(1.0):  # Check every second
            try:
                for plugin_id, plugin in list(self.plugins.items()):
                    if plugin.is_outdated():
                        print(f"Reloading plugin: {plugin_id}")
                        plugin.load()

                # Discover new plugins
                self.discover_plugins()

            except Exception as e:
                print(f"Error in hot reload monitoring: {e}")


class PluginPerformanceProfiler:
    """Profiles plugin performance and resource usage."""

    def __init__(self, plugin_manager: AdvancedPluginManager):
        self.plugin_manager = plugin_manager

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report for all plugins."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_plugins": len(self.plugin_manager.plugins),
            "plugins": {},
        }

        for plugin_id, metrics in self.plugin_manager.plugin_metrics.items():
            report["plugins"][plugin_id] = {
                "execution_count": metrics.execution_count,
                "total_execution_time": metrics.total_execution_time,
                "average_execution_time": metrics.average_execution_time,
                "peak_memory_usage_mb": metrics.peak_memory_usage_mb,
                "error_count": metrics.error_count,
                "error_rate": (metrics.error_count / max(metrics.execution_count, 1)) * 100,
                "last_execution": (
                    metrics.last_execution.isoformat() if metrics.last_execution else None
                ),
                "last_error": metrics.last_error,
            }

        return report

    def get_top_resource_consumers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get plugins that consume the most resources."""
        plugins_data = []

        for plugin_id, metrics in self.plugin_manager.plugin_metrics.items():
            plugins_data.append(
                {
                    "plugin_id": plugin_id,
                    "total_execution_time": metrics.total_execution_time,
                    "peak_memory_usage_mb": metrics.peak_memory_usage_mb,
                    "execution_count": metrics.execution_count,
                }
            )

        # Sort by total execution time
        return sorted(plugins_data, key=lambda x: x["total_execution_time"], reverse=True)[:limit]
