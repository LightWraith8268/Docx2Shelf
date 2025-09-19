"""
Performance optimization and analytics module for Docx2Shelf.

Provides streaming DOCX reading, incremental build cache, parallel processing,
advanced performance profiling, memory optimization, and conversion analytics
to reduce memory usage and improve conversion speed for large documents.
"""

from __future__ import annotations

import cProfile
import hashlib
import io
import json
import multiprocessing
import pickle
import pstats
import sqlite3
import threading
import time
import tracemalloc
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union
from zipfile import ZipFile

import psutil
from PIL import Image

from .metadata import BuildOptions


@dataclass
class ConversionMetrics:
    """Metrics for a single conversion operation."""

    input_file: str
    input_size_mb: float
    output_size_mb: float
    conversion_time_seconds: float
    memory_peak_mb: float
    cpu_percent: float
    chapter_count: int
    image_count: int
    processing_stages: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass
class PerformanceProfile:
    """Detailed performance profiling data."""

    function_stats: Dict[str, Dict[str, Any]]
    memory_timeline: List[Dict[str, Any]]
    hot_paths: List[str]
    optimization_suggestions: List[str]


class StreamingDocxReader:
    """Streaming DOCX reader to minimize memory usage for large documents."""

    def __init__(self, docx_path: Path, chunk_size: int = 1024 * 1024):
        """Initialize streaming reader.

        Args:
            docx_path: Path to DOCX file
            chunk_size: Size of chunks to read in bytes (default 1MB)
        """
        self.docx_path = docx_path
        self.chunk_size = chunk_size
        self._zip_file: Optional[ZipFile] = None

    def __enter__(self):
        self._zip_file = ZipFile(self.docx_path, 'r')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._zip_file:
            self._zip_file.close()

    def stream_document_xml(self) -> Generator[str, None, None]:
        """Stream the main document XML in chunks."""
        if not self._zip_file:
            raise RuntimeError("StreamingDocxReader not opened")

        try:
            with self._zip_file.open('word/document.xml') as doc_file:
                while True:
                    chunk = doc_file.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk.decode('utf-8', errors='replace')
        except KeyError:
            raise ValueError("Invalid DOCX file: missing document.xml")

    def get_embedded_images(self) -> List[Tuple[str, bytes]]:
        """Extract embedded images without loading full document into memory."""
        if not self._zip_file:
            raise RuntimeError("StreamingDocxReader not opened")

        images = []
        for file_path in self._zip_file.namelist():
            if file_path.startswith('word/media/'):
                with self._zip_file.open(file_path) as img_file:
                    images.append((file_path, img_file.read()))

        return images

    def get_document_metadata(self) -> Dict[str, Any]:
        """Extract document metadata efficiently."""
        if not self._zip_file:
            raise RuntimeError("StreamingDocxReader not opened")

        metadata = {}

        # Core properties
        try:
            with self._zip_file.open('docProps/core.xml') as core_file:
                core_xml = core_file.read().decode('utf-8')
                # Parse basic metadata without full XML parsing
                metadata['core'] = self._extract_simple_metadata(core_xml)
        except KeyError:
            pass

        # App properties
        try:
            with self._zip_file.open('docProps/app.xml') as app_file:
                app_xml = app_file.read().decode('utf-8')
                metadata['app'] = self._extract_simple_metadata(app_xml)
        except KeyError:
            pass

        return metadata

    def _extract_simple_metadata(self, xml_content: str) -> Dict[str, str]:
        """Extract simple metadata using string operations instead of XML parsing."""
        metadata = {}

        # Simple regex-like extraction for common properties
        properties = ['dc:title', 'dc:creator', 'dc:subject', 'dc:description']

        for prop in properties:
            start_tag = f'<{prop}>'
            end_tag = f'</{prop}>'
            start_idx = xml_content.find(start_tag)
            if start_idx != -1:
                start_idx += len(start_tag)
                end_idx = xml_content.find(end_tag, start_idx)
                if end_idx != -1:
                    metadata[prop.replace('dc:', '')] = xml_content[start_idx:end_idx]

        return metadata


class BuildCache:
    """Incremental build cache to avoid rebuilding unchanged content."""

    def __init__(self, cache_dir: Path):
        """Initialize build cache.

        Args:
            cache_dir: Directory to store cache database
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "build_cache.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS build_cache (
                    input_hash TEXT PRIMARY KEY,
                    input_path TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    options_hash TEXT NOT NULL,
                    build_time REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_cache (
                    image_hash TEXT PRIMARY KEY,
                    original_path TEXT NOT NULL,
                    processed_path TEXT NOT NULL,
                    processing_options TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    last_accessed REAL NOT NULL
                )
            """)

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file efficiently."""
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def get_options_hash(self, options: BuildOptions) -> str:
        """Calculate hash of build options."""
        # Convert options to JSON for consistent hashing
        options_dict = {
            'theme': options.theme,
            'css_options': options.css_options,
            'split_on': options.split_on,
            'max_toc_depth': options.max_toc_depth,
            'include_pagebreaks': options.include_pagebreaks
        }

        options_json = json.dumps(options_dict, sort_keys=True)
        return hashlib.sha256(options_json.encode()).hexdigest()

    def is_cached(self, input_path: Path, options: BuildOptions) -> bool:
        """Check if build result is cached and valid."""
        input_hash = self.get_file_hash(input_path)
        options_hash = self.get_options_hash(options)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT output_path FROM build_cache WHERE input_hash = ? AND options_hash = ?",
                (input_hash, options_hash)
            )
            result = cursor.fetchone()

            if result:
                output_path = Path(result[0])
                if output_path.exists():
                    # Update last accessed time
                    conn.execute(
                        "UPDATE build_cache SET last_accessed = ? WHERE input_hash = ?",
                        (time.time(), input_hash)
                    )
                    return True

        return False

    def get_cached_result(self, input_path: Path, options: BuildOptions) -> Optional[Path]:
        """Get cached build result if available."""
        if not self.is_cached(input_path, options):
            return None

        input_hash = self.get_file_hash(input_path)
        options_hash = self.get_options_hash(options)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT output_path FROM build_cache WHERE input_hash = ? AND options_hash = ?",
                (input_hash, options_hash)
            )
            result = cursor.fetchone()

            if result:
                return Path(result[0])

        return None

    def cache_result(self, input_path: Path, output_path: Path, options: BuildOptions, metadata: Dict[str, Any]):
        """Cache build result."""
        input_hash = self.get_file_hash(input_path)
        options_hash = self.get_options_hash(options)
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO build_cache
                   (input_hash, input_path, output_path, options_hash, build_time, last_accessed, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (input_hash, str(input_path), str(output_path), options_hash,
                 current_time, current_time, json.dumps(metadata))
            )

    def cleanup_old_cache(self, max_age_days: int = 30):
        """Remove old cache entries."""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Get old entries to remove their files
            cursor = conn.execute(
                "SELECT output_path FROM build_cache WHERE last_accessed < ?",
                (cutoff_time,)
            )

            for (output_path,) in cursor.fetchall():
                try:
                    Path(output_path).unlink(missing_ok=True)
                except Exception:
                    pass

            # Remove from database
            conn.execute("DELETE FROM build_cache WHERE last_accessed < ?", (cutoff_time,))
            conn.execute("DELETE FROM image_cache WHERE last_accessed < ?", (cutoff_time,))


class ParallelImageProcessor:
    """Parallel image processing pipeline for faster conversion."""

    def __init__(self, max_workers: Optional[int] = None):
        """Initialize parallel processor.

        Args:
            max_workers: Maximum number of worker threads (default: CPU count)
        """
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 8)
        self.cache = None

    def set_cache(self, cache: BuildCache):
        """Set build cache for image processing."""
        self.cache = cache

    def process_images_parallel(self,
                              images: List[Tuple[str, bytes]],
                              output_dir: Path,
                              max_width: int = 1200,
                              quality: int = 85) -> List[Tuple[str, Path]]:
        """Process multiple images in parallel.

        Args:
            images: List of (filename, image_data) tuples
            output_dir: Directory to save processed images
            max_width: Maximum image width
            quality: JPEG quality (1-100)

        Returns:
            List of (original_filename, processed_path) tuples
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare tasks
        tasks = []
        for filename, image_data in images:
            tasks.append((filename, image_data, output_dir, max_width, quality))

        # Process in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._process_single_image, *task): task[0]
                for task in tasks
            }

            for future in as_completed(future_to_task):
                filename = future_to_task[future]
                try:
                    result = future.result()
                    if result:
                        results.append((filename, result))
                except Exception as e:
                    print(f"Error processing image {filename}: {e}")

        return results

    def _process_single_image(self,
                            filename: str,
                            image_data: bytes,
                            output_dir: Path,
                            max_width: int,
                            quality: int) -> Optional[Path]:
        """Process a single image."""
        try:
            # Calculate hash for caching
            image_hash = hashlib.sha256(image_data).hexdigest()

            # Check cache first
            if self.cache:
                with sqlite3.connect(self.cache.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT processed_path FROM image_cache WHERE image_hash = ?",
                        (image_hash,)
                    )
                    result = cursor.fetchone()

                    if result:
                        cached_path = Path(result[0])
                        if cached_path.exists():
                            # Update last accessed
                            conn.execute(
                                "UPDATE image_cache SET last_accessed = ? WHERE image_hash = ?",
                                (time.time(), image_hash)
                            )
                            return cached_path

            # Process image
            from io import BytesIO

            with Image.open(BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if necessary
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Generate output filename
                base_name = Path(filename).stem
                output_path = output_dir / f"{base_name}_{image_hash[:8]}.jpg"

                # Save optimized image
                img.save(output_path, 'JPEG', quality=quality, optimize=True)

                # Cache result
                if self.cache:
                    with sqlite3.connect(self.cache.db_path) as conn:
                        conn.execute(
                            """INSERT OR REPLACE INTO image_cache
                               (image_hash, original_path, processed_path, processing_options, file_size, last_accessed)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (image_hash, filename, str(output_path),
                             json.dumps({'max_width': max_width, 'quality': quality}),
                             output_path.stat().st_size, time.time())
                        )

                return output_path

        except Exception as e:
            print(f"Failed to process image {filename}: {e}")
            return None


class PerformanceProfiler:
    """Advanced performance profiler for conversion operations."""

    def __init__(self, enable_memory_tracking: bool = True):
        self.enable_memory_tracking = enable_memory_tracking
        self.profiler: Optional[cProfile.Profile] = None
        self.start_time: float = 0
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.stage_timings: Dict[str, float] = {}
        self.current_stage: Optional[str] = None

    def start_profiling(self) -> None:
        """Start performance profiling."""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        self.start_time = time.time()

        if self.enable_memory_tracking:
            tracemalloc.start()

    def stop_profiling(self) -> PerformanceProfile:
        """Stop profiling and return performance data."""
        if not self.profiler:
            raise RuntimeError("Profiler not started")

        self.profiler.disable()

        # Capture final memory snapshot
        if self.enable_memory_tracking:
            current, peak = tracemalloc.get_traced_memory()
            self.memory_snapshots.append({
                'timestamp': time.time() - self.start_time,
                'current_mb': current / 1024 / 1024,
                'peak_mb': peak / 1024 / 1024,
                'stage': 'final'
            })
            tracemalloc.stop()

        return self._analyze_profile()

    def start_stage(self, stage_name: str) -> None:
        """Mark the start of a processing stage."""
        if self.current_stage:
            self.end_stage()

        self.current_stage = stage_name
        self.stage_timings[stage_name] = time.time()

        # Memory snapshot
        if self.enable_memory_tracking and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            self.memory_snapshots.append({
                'timestamp': time.time() - self.start_time,
                'current_mb': current / 1024 / 1024,
                'peak_mb': peak / 1024 / 1024,
                'stage': stage_name
            })

    def end_stage(self) -> None:
        """Mark the end of the current processing stage."""
        if not self.current_stage:
            return

        elapsed = time.time() - self.stage_timings[self.current_stage]
        self.stage_timings[self.current_stage] = elapsed
        self.current_stage = None

    def _analyze_profile(self) -> PerformanceProfile:
        """Analyze profiling data and generate insights."""
        # Extract function statistics
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')

        function_stats = {}
        for func, (cc, nc, tt, ct, callers) in ps.stats.items():
            function_stats[f"{func[0]}:{func[1]}({func[2]})"] = {
                'call_count': cc,
                'total_time': tt,
                'cumulative_time': ct,
                'per_call': tt / cc if cc > 0 else 0
            }

        # Identify hot paths (functions taking >5% of total time)
        total_time = sum(stats['total_time'] for stats in function_stats.values())
        hot_paths = [
            func for func, stats in function_stats.items()
            if stats['total_time'] / total_time > 0.05
        ]

        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(function_stats, hot_paths)

        return PerformanceProfile(
            function_stats=function_stats,
            memory_timeline=self.memory_snapshots,
            hot_paths=hot_paths,
            optimization_suggestions=suggestions
        )

    def _generate_optimization_suggestions(
        self,
        function_stats: Dict[str, Dict[str, Any]],
        hot_paths: List[str]
    ) -> List[str]:
        """Generate performance optimization suggestions."""
        suggestions = []

        # Memory-related suggestions
        if self.memory_snapshots:
            peak_memory = max(snap['peak_mb'] for snap in self.memory_snapshots)
            if peak_memory > 500:  # > 500MB
                suggestions.append(
                    f"High memory usage detected ({peak_memory:.1f}MB). "
                    "Consider streaming processing for large documents."
                )

        # Function-specific suggestions
        for func in hot_paths:
            if 'image' in func.lower():
                suggestions.append(
                    "Image processing is a performance bottleneck. "
                    "Consider parallel image processing or caching."
                )
            elif 'parse' in func.lower() or 'xml' in func.lower():
                suggestions.append(
                    "Document parsing is slow. Consider using faster XML parsers "
                    "or streaming parsing for large documents."
                )

        return suggestions


class ConversionAnalytics:
    """Analytics system for tracking conversion performance over time."""

    def __init__(self, analytics_dir: Optional[Path] = None):
        self.analytics_dir = analytics_dir or Path.home() / ".docx2shelf" / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.analytics_dir / "conversion_metrics.json"
        self.benchmarks_file = self.analytics_dir / "benchmarks.json"

    def record_conversion(self, metrics: ConversionMetrics) -> None:
        """Record metrics for a conversion operation."""
        # Load existing metrics
        existing_metrics = []
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                existing_metrics = json.load(f)

        # Add new metrics
        metrics_dict = {
            'timestamp': time.time(),
            'input_file': metrics.input_file,
            'input_size_mb': metrics.input_size_mb,
            'output_size_mb': metrics.output_size_mb,
            'conversion_time_seconds': metrics.conversion_time_seconds,
            'memory_peak_mb': metrics.memory_peak_mb,
            'cpu_percent': metrics.cpu_percent,
            'chapter_count': metrics.chapter_count,
            'image_count': metrics.image_count,
            'processing_stages': metrics.processing_stages,
            'error_count': metrics.error_count,
            'warnings': metrics.warnings
        }

        existing_metrics.append(metrics_dict)

        # Keep only last 1000 entries
        if len(existing_metrics) > 1000:
            existing_metrics = existing_metrics[-1000:]

        # Save updated metrics
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(existing_metrics, f, indent=2)

    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over the specified number of days."""
        if not self.metrics_file.exists():
            return {}

        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            all_metrics = json.load(f)

        # Filter to recent metrics
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        recent_metrics = [m for m in all_metrics if m['timestamp'] > cutoff_time]

        if not recent_metrics:
            return {}

        # Calculate trends
        avg_conversion_time = sum(m['conversion_time_seconds'] for m in recent_metrics) / len(recent_metrics)
        avg_memory_usage = sum(m['memory_peak_mb'] for m in recent_metrics) / len(recent_metrics)
        total_conversions = len(recent_metrics)
        total_errors = sum(m['error_count'] for m in recent_metrics)

        # Performance by file size buckets
        size_buckets = defaultdict(list)
        for m in recent_metrics:
            if m['input_size_mb'] < 1:
                bucket = 'small'
            elif m['input_size_mb'] < 10:
                bucket = 'medium'
            else:
                bucket = 'large'
            size_buckets[bucket].append(m['conversion_time_seconds'])

        bucket_averages = {
            bucket: sum(times) / len(times)
            for bucket, times in size_buckets.items()
        }

        return {
            'period_days': days,
            'total_conversions': total_conversions,
            'avg_conversion_time_seconds': avg_conversion_time,
            'avg_memory_usage_mb': avg_memory_usage,
            'total_errors': total_errors,
            'error_rate': total_errors / total_conversions if total_conversions > 0 else 0,
            'performance_by_size': bucket_averages
        }

    def run_benchmark_suite(self) -> Dict[str, Any]:
        """Run comprehensive benchmark tests."""
        benchmarks = {}

        # System information
        benchmarks['system'] = {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_type': 'unknown'  # Would need platform-specific detection
        }

        # Memory allocation benchmark
        start_time = time.time()
        test_data = [i for i in range(1000000)]  # 1M integers
        allocation_time = time.time() - start_time
        del test_data

        benchmarks['memory_allocation_ms'] = allocation_time * 1000

        # File I/O benchmark
        test_file = self.analytics_dir / "benchmark_test.tmp"
        test_content = "x" * 1024 * 1024  # 1MB of data

        start_time = time.time()
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        write_time = time.time() - start_time

        start_time = time.time()
        with open(test_file, 'r', encoding='utf-8') as f:
            _ = f.read()
        read_time = time.time() - start_time

        test_file.unlink()  # Clean up

        benchmarks['file_io'] = {
            'write_1mb_ms': write_time * 1000,
            'read_1mb_ms': read_time * 1000
        }

        # Save benchmarks
        benchmarks['timestamp'] = time.time()

        existing_benchmarks = []
        if self.benchmarks_file.exists():
            with open(self.benchmarks_file, 'r', encoding='utf-8') as f:
                existing_benchmarks = json.load(f)

        existing_benchmarks.append(benchmarks)

        # Keep only last 50 benchmark runs
        if len(existing_benchmarks) > 50:
            existing_benchmarks = existing_benchmarks[-50:]

        with open(self.benchmarks_file, 'w', encoding='utf-8') as f:
            json.dump(existing_benchmarks, f, indent=2)

        return benchmarks

    def detect_performance_regressions(self) -> List[str]:
        """Detect performance regressions compared to historical data."""
        if not self.benchmarks_file.exists():
            return ["No historical benchmark data available"]

        with open(self.benchmarks_file, 'r', encoding='utf-8') as f:
            benchmarks = json.load(f)

        if len(benchmarks) < 2:
            return ["Insufficient benchmark data for regression analysis"]

        current = benchmarks[-1]
        baseline = benchmarks[-10] if len(benchmarks) >= 10 else benchmarks[0]

        regressions = []

        # Check memory allocation performance
        current_mem = current.get('memory_allocation_ms', 0)
        baseline_mem = baseline.get('memory_allocation_ms', 0)
        if baseline_mem > 0 and current_mem > baseline_mem * 1.2:  # 20% slower
            regressions.append(
                f"Memory allocation performance regression: "
                f"{current_mem:.1f}ms vs {baseline_mem:.1f}ms baseline"
            )

        # Check file I/O performance
        current_io = current.get('file_io', {})
        baseline_io = baseline.get('file_io', {})

        for operation in ['write_1mb_ms', 'read_1mb_ms']:
            current_val = current_io.get(operation, 0)
            baseline_val = baseline_io.get(operation, 0)
            if baseline_val > 0 and current_val > baseline_val * 1.3:  # 30% slower
                regressions.append(
                    f"File I/O regression ({operation}): "
                    f"{current_val:.1f}ms vs {baseline_val:.1f}ms baseline"
                )

        return regressions if regressions else ["No performance regressions detected"]


class MemoryOptimizer:
    """Memory optimization utilities for large document processing."""

    @staticmethod
    def optimize_for_large_documents(file_size_mb: float) -> Dict[str, Any]:
        """Return optimization settings based on document size."""
        if file_size_mb < 10:
            return {
                'streaming_mode': False,
                'chunk_size': None,
                'parallel_processing': True,
                'memory_limit_mb': None
            }
        elif file_size_mb < 100:
            return {
                'streaming_mode': True,
                'chunk_size': 1024 * 1024,  # 1MB chunks
                'parallel_processing': True,
                'memory_limit_mb': 512
            }
        else:
            return {
                'streaming_mode': True,
                'chunk_size': 512 * 1024,  # 512KB chunks
                'parallel_processing': False,  # Avoid memory pressure
                'memory_limit_mb': 256
            }

    @staticmethod
    def estimate_memory_requirements(
        file_size_mb: float,
        image_count: int,
        chapter_count: int
    ) -> Dict[str, float]:
        """Estimate memory requirements for conversion."""
        # Base memory for document structure
        base_memory = file_size_mb * 2  # 2x file size for parsing

        # Additional memory for images (estimate 1MB per image in memory)
        image_memory = image_count * 1.0

        # Memory for chapter processing (estimate 5MB per chapter)
        chapter_memory = chapter_count * 5.0

        # Safety margin
        total_estimated = (base_memory + image_memory + chapter_memory) * 1.5

        return {
            'base_mb': base_memory,
            'images_mb': image_memory,
            'chapters_mb': chapter_memory,
            'total_estimated_mb': total_estimated,
            'recommended_available_mb': total_estimated * 2
        }


class PerformanceMonitor:
    """Monitor and report performance metrics during conversion."""

    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = None
        self.metrics = {}
        self.phase_times = {}
        self.memory_snapshots = []

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.metrics = {
            'total_time': 0,
            'peak_memory': 0,
            'images_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def record_phase_start(self, phase_name: str):
        """Record start of a processing phase."""
        self.phase_times[phase_name] = {'start': time.time()}

    def record_phase_end(self, phase_name: str):
        """Record end of a processing phase."""
        if phase_name in self.phase_times and 'start' in self.phase_times[phase_name]:
            self.phase_times[phase_name]['duration'] = time.time() - self.phase_times[phase_name]['start']

    def record_memory_usage(self):
        """Record current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_snapshots.append({
                'time': time.time() - (self.start_time or time.time()),
                'memory_mb': memory_mb
            })
            self.metrics['peak_memory'] = max(self.metrics['peak_memory'], memory_mb)
        except ImportError:
            pass

    def increment_counter(self, counter_name: str, amount: int = 1):
        """Increment a performance counter."""
        if counter_name not in self.metrics:
            self.metrics[counter_name] = 0
        self.metrics[counter_name] += amount

    def finish_monitoring(self) -> Dict[str, Any]:
        """Finish monitoring and return performance report."""
        if self.start_time:
            self.metrics['total_time'] = time.time() - self.start_time

        return {
            'metrics': self.metrics,
            'phase_times': self.phase_times,
            'memory_snapshots': self.memory_snapshots
        }

    def get_performance_summary(self) -> str:
        """Get human-readable performance summary."""
        if not self.start_time:
            return "No performance data available"

        total_time = self.metrics.get('total_time', 0)
        peak_memory = self.metrics.get('peak_memory', 0)
        images_processed = self.metrics.get('images_processed', 0)
        cache_hits = self.metrics.get('cache_hits', 0)
        cache_misses = self.metrics.get('cache_misses', 0)

        cache_hit_rate = cache_hits / (cache_hits + cache_misses) * 100 if (cache_hits + cache_misses) > 0 else 0

        summary = f"""Performance Summary:
  Total Time: {total_time:.2f}s
  Peak Memory: {peak_memory:.1f}MB
  Images Processed: {images_processed}
  Cache Hit Rate: {cache_hit_rate:.1f}%
"""

        if self.phase_times:
            summary += "\nPhase Breakdown:\n"
            for phase, times in self.phase_times.items():
                if 'duration' in times:
                    percentage = (times['duration'] / total_time) * 100 if total_time > 0 else 0
                    summary += f"  {phase}: {times['duration']:.2f}s ({percentage:.1f}%)\n"

        return summary


def create_conversion_profiler(enable_memory: bool = True) -> PerformanceProfiler:
    """Create a configured performance profiler."""
    return PerformanceProfiler(enable_memory_tracking=enable_memory)


def create_analytics_system(analytics_dir: Optional[Path] = None) -> ConversionAnalytics:
    """Create a configured analytics system."""
    return ConversionAnalytics(analytics_dir)


def create_memory_optimizer() -> MemoryOptimizer:
    """Create a memory optimizer instance."""
    return MemoryOptimizer()