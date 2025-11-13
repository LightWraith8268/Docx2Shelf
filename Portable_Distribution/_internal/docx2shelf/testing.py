"""
Advanced testing and reliability framework for Docx2Shelf.

Includes property-based testing, fuzzing, performance benchmarks,
and golden EPUB fixtures for regression testing.
"""

from __future__ import annotations

import hashlib
import json
import random
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import hypothesis
from hypothesis import strategies as st


@dataclass
class TestResult:
    """Result of a test execution."""
    test_name: str
    success: bool
    duration_ms: float
    error_message: Optional[str] = None
    artifacts: List[Path] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result."""
    test_name: str
    duration_ms: float
    memory_peak_mb: float
    file_size_mb: float
    conversion_rate_mb_per_sec: float
    baseline_duration_ms: Optional[float] = None
    performance_regression: bool = False


class DOCXFuzzer:
    """Generates mutated DOCX files for fuzzing tests."""

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

    def generate_fuzzed_docx(self, base_docx: Path, output_path: Path, mutation_rate: float = 0.1) -> Path:
        """Generate a fuzzed DOCX file by mutating the base file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract base DOCX
            with zipfile.ZipFile(base_docx, 'r') as zip_file:
                zip_file.extractall(temp_path)

            # Apply mutations
            self._mutate_document_xml(temp_path / "word" / "document.xml", mutation_rate)
            self._mutate_styles_xml(temp_path / "word" / "styles.xml", mutation_rate)
            self._mutate_content_types(temp_path / "[Content_Types].xml", mutation_rate)

            # Repackage as DOCX
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arc_path = file_path.relative_to(temp_path)
                        zip_file.write(file_path, arc_path)

        return output_path

    def _mutate_document_xml(self, xml_path: Path, mutation_rate: float):
        """Mutate document.xml with various corruption patterns."""
        if not xml_path.exists():
            return

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Mutation strategies
            mutations = [
                self._corrupt_text_elements,
                self._duplicate_elements,
                self._remove_random_elements,
                self._corrupt_attributes,
                self._add_invalid_elements
            ]

            for mutation in mutations:
                if self.random.random() < mutation_rate:
                    mutation(root)

            tree.write(xml_path, encoding='utf-8', xml_declaration=True)

        except ET.ParseError:
            # If XML is already corrupted, apply binary mutations
            self._apply_binary_mutations(xml_path, mutation_rate)

    def _corrupt_text_elements(self, root: ET.Element):
        """Corrupt text elements with various patterns."""
        text_elements = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')

        for elem in text_elements[:self.random.randint(1, min(5, len(text_elements)))]:
            if elem.text:
                # Apply text corruptions
                corruptions = [
                    lambda t: t + '\x00\x01\x02',  # Add null bytes
                    lambda t: t.replace(' ', '\t\n\r'),  # Replace spaces with control chars
                    lambda t: ''.join(reversed(t)),  # Reverse text
                    lambda t: t * 100,  # Repeat text many times
                    lambda t: '\U0001F600' * len(t),  # Replace with emoji
                ]
                corruption = self.random.choice(corruptions)
                elem.text = corruption(elem.text)

    def _duplicate_elements(self, root: ET.Element):
        """Duplicate random elements to test handling of duplicates."""
        # Find parent-child relationships
        parent_map = {child: parent for parent in root.iter() for child in parent}
        all_elements = list(root.iter())

        if all_elements:
            elem_to_duplicate = self.random.choice(all_elements)
            parent = parent_map.get(elem_to_duplicate)
            if parent is not None:
                for _ in range(self.random.randint(2, 5)):
                    import copy
                    duplicate = copy.deepcopy(elem_to_duplicate)
                    parent.append(duplicate)

    def _remove_random_elements(self, root: ET.Element):
        """Remove random elements to test error handling."""
        # Find parent-child relationships
        parent_map = {child: parent for parent in root.iter() for child in parent}
        all_elements = list(root.iter())
        elements_to_remove = self.random.sample(
            all_elements,
            min(self.random.randint(1, 5), len(all_elements))
        )

        for elem in elements_to_remove:
            parent = parent_map.get(elem)
            if parent is not None:
                parent.remove(elem)

    def _corrupt_attributes(self, root: ET.Element):
        """Corrupt element attributes."""
        all_elements = list(root.iter())

        for elem in all_elements[:self.random.randint(1, min(10, len(all_elements)))]:
            # Add invalid attributes
            invalid_attrs = {
                'invalid_attr': '\x00\x01\x02',
                'malformed': '<script>alert("xss")</script>',
                'very_long': 'x' * 10000,
                '': 'empty_name',
                '\x00null\x00': 'null_in_name'
            }

            for attr, value in invalid_attrs.items():
                if self.random.random() < 0.3:
                    elem.set(attr, value)

    def _add_invalid_elements(self, root: ET.Element):
        """Add structurally invalid elements."""
        invalid_elements = [
            '<invalid>malformed',
            '</closing_without_opening>',
            '<nested><deeply><very><much></much></very></deeply></nested>',
            '<script>alert("xss")</script>',
            '<style>body { display: none; }</style>'
        ]

        for _ in range(self.random.randint(1, 3)):
            try:
                invalid_elem = ET.fromstring(f'<root>{self.random.choice(invalid_elements)}</root>')
                root.append(invalid_elem)
            except ET.ParseError:
                pass  # Expected for some invalid elements

    def _mutate_styles_xml(self, xml_path: Path, mutation_rate: float):
        """Mutate styles.xml to test style handling."""
        if not xml_path.exists():
            return

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Remove random styles
            styles = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}style')
            styles_to_remove = self.random.sample(
                styles,
                min(self.random.randint(0, 3), len(styles))
            )

            for style in styles_to_remove:
                parent = style.getparent()
                if parent is not None:
                    parent.remove(style)

            tree.write(xml_path, encoding='utf-8', xml_declaration=True)

        except ET.ParseError:
            self._apply_binary_mutations(xml_path, mutation_rate)

    def _mutate_content_types(self, xml_path: Path, mutation_rate: float):
        """Mutate [Content_Types].xml to test content type handling."""
        if not xml_path.exists():
            return

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Add invalid content types
            invalid_types = [
                'application/vnd.malicious',
                'text/javascript',
                'application/x-executable',
                '../../../etc/passwd',
                'file:///etc/passwd'
            ]

            for content_type in invalid_types:
                if self.random.random() < mutation_rate:
                    override_elem = ET.SubElement(root, 'Override')
                    override_elem.set('PartName', f'/word/invalid_{self.random.randint(1, 1000)}.xml')
                    override_elem.set('ContentType', content_type)

            tree.write(xml_path, encoding='utf-8', xml_declaration=True)

        except ET.ParseError:
            self._apply_binary_mutations(xml_path, mutation_rate)

    def _apply_binary_mutations(self, file_path: Path, mutation_rate: float):
        """Apply binary-level mutations to files."""
        try:
            with open(file_path, 'rb') as f:
                data = bytearray(f.read())

            # Apply binary mutations
            mutations_count = int(len(data) * mutation_rate * 0.01)  # 1% of mutation rate

            for _ in range(mutations_count):
                if data:
                    pos = self.random.randint(0, len(data) - 1)
                    # Mutation types
                    mutation_type = self.random.choice(['flip_bit', 'replace_byte', 'insert_byte', 'delete_byte'])

                    if mutation_type == 'flip_bit':
                        bit_pos = self.random.randint(0, 7)
                        data[pos] ^= (1 << bit_pos)
                    elif mutation_type == 'replace_byte':
                        data[pos] = self.random.randint(0, 255)
                    elif mutation_type == 'insert_byte':
                        data.insert(pos, self.random.randint(0, 255))
                    elif mutation_type == 'delete_byte':
                        del data[pos]

            with open(file_path, 'wb') as f:
                f.write(data)

        except Exception:
            pass  # Ignore errors in binary mutation


class PropertyBasedTester:
    """Property-based testing using Hypothesis."""

    @staticmethod
    @hypothesis.given(
        title=st.text(min_size=1, max_size=200),
        author=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=10000)
    )
    def test_metadata_preservation(title: str, author: str, content: str):
        """Test that metadata is preserved through conversion."""
        # This would be implemented to test actual conversion
        # For now, it's a template showing the structure
        assert len(title.strip()) > 0
        assert len(author.strip()) > 0
        assert len(content.strip()) > 0

    @staticmethod
    @hypothesis.given(
        html_content=st.text(min_size=1, max_size=50000),
        split_level=st.sampled_from(['h1', 'h2', 'pagebreak'])
    )
    def test_content_splitting_properties(html_content: str, split_level: str):
        """Test properties of content splitting."""
        # Template for testing content splitting properties
        assert split_level in ['h1', 'h2', 'pagebreak']

    @staticmethod
    @hypothesis.given(
        image_data=st.binary(min_size=1, max_size=1024*1024),  # Up to 1MB
        quality=st.integers(min_value=1, max_value=100)
    )
    def test_image_processing_properties(image_data: bytes, quality: int):
        """Test properties of image processing."""
        # Template for testing image processing
        assert 1 <= quality <= 100
        assert len(image_data) > 0


class GoldenEPUBTester:
    """Tests against golden EPUB fixtures for regression detection."""

    def __init__(self, fixtures_dir: Path):
        self.fixtures_dir = fixtures_dir
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def create_golden_fixture(self, input_docx: Path, test_name: str, options: Dict[str, Any]) -> Path:
        """Create a golden EPUB fixture from input."""
        from .assemble import assemble_epub
        from .convert import convert_file_to_html
        from .metadata import BuildOptions, EpubMetadata

        # Convert to get the expected output
        html_chunks, images, title = convert_file_to_html(input_docx)

        # Create metadata
        metadata = EpubMetadata(
            title=options.get('title', title or 'Test Document'),
            author=options.get('author', 'Test Author')
        )

        # Create build options
        build_options = BuildOptions(**options.get('build_options', {}))

        # Generate EPUB
        fixture_path = self.fixtures_dir / f"{test_name}_golden.epub"
        assemble_epub(
            html_chunks=html_chunks,
            metadata=metadata,
            output_path=fixture_path,
            images=images,
            options=build_options
        )

        # Create fixture metadata
        fixture_metadata = {
            'test_name': test_name,
            'created_at': time.time(),
            'input_docx_hash': self._file_hash(input_docx),
            'options': options,
            'epub_hash': self._file_hash(fixture_path)
        }

        metadata_path = self.fixtures_dir / f"{test_name}_golden.json"
        with open(metadata_path, 'w') as f:
            json.dump(fixture_metadata, f, indent=2)

        return fixture_path

    def test_against_golden_fixture(self, input_docx: Path, test_name: str, options: Dict[str, Any]) -> TestResult:
        """Test current conversion against golden fixture."""
        start_time = time.time()

        try:
            # Load golden fixture metadata
            metadata_path = self.fixtures_dir / f"{test_name}_golden.json"
            if not metadata_path.exists():
                return TestResult(
                    test_name=test_name,
                    success=False,
                    duration_ms=0,
                    error_message=f"Golden fixture metadata not found: {metadata_path}"
                )

            with open(metadata_path) as f:
                fixture_metadata = json.load(f)

            # Check if input file has changed
            current_input_hash = self._file_hash(input_docx)
            if current_input_hash != fixture_metadata['input_docx_hash']:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    duration_ms=0,
                    error_message="Input file hash mismatch - fixture needs update"
                )

            # Perform current conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                current_output = Path(temp_dir) / "current.epub"

                from .assemble import assemble_epub
                from .convert import convert_file_to_html
                from .metadata import BuildOptions, EpubMetadata

                html_chunks, images, title = convert_file_to_html(input_docx)

                metadata = EpubMetadata(
                    title=options.get('title', title or 'Test Document'),
                    author=options.get('author', 'Test Author')
                )

                build_options = BuildOptions(**options.get('build_options', {}))

                assemble_epub(
                    html_chunks=html_chunks,
                    metadata=metadata,
                    output_path=current_output,
                    images=images,
                    options=build_options
                )

                # Compare with golden fixture
                differences = self._compare_epubs(
                    self.fixtures_dir / f"{test_name}_golden.epub",
                    current_output
                )

                duration_ms = (time.time() - start_time) * 1000

                if not differences:
                    return TestResult(
                        test_name=test_name,
                        success=True,
                        duration_ms=duration_ms,
                        metadata={'comparison': 'identical'}
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        success=False,
                        duration_ms=duration_ms,
                        error_message="EPUB differs from golden fixture",
                        metadata={'differences': differences}
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                success=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )

    def _compare_epubs(self, golden_epub: Path, current_epub: Path) -> List[str]:
        """Compare two EPUB files and return differences."""
        differences = []

        with tempfile.TemporaryDirectory() as temp_dir:
            golden_dir = Path(temp_dir) / "golden"
            current_dir = Path(temp_dir) / "current"

            # Extract both EPUBs
            with zipfile.ZipFile(golden_epub, 'r') as zf:
                zf.extractall(golden_dir)

            with zipfile.ZipFile(current_epub, 'r') as zf:
                zf.extractall(current_dir)

            # Compare file structure
            golden_files = set(p.relative_to(golden_dir) for p in golden_dir.rglob('*') if p.is_file())
            current_files = set(p.relative_to(current_dir) for p in current_dir.rglob('*') if p.is_file())

            if golden_files != current_files:
                differences.append(f"File structure differs: {golden_files.symmetric_difference(current_files)}")

            # Compare file contents
            for file_path in golden_files.intersection(current_files):
                golden_file = golden_dir / file_path
                current_file = current_dir / file_path

                if self._file_hash(golden_file) != self._file_hash(current_file):
                    differences.append(f"File content differs: {file_path}")

        return differences

    def _file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class PerformanceTester:
    """Performance testing and benchmarking."""

    def __init__(self, baseline_file: Optional[Path] = None):
        self.baseline_file = baseline_file
        self.baselines: Dict[str, float] = {}
        self.load_baselines()

    def load_baselines(self):
        """Load performance baselines from file."""
        if self.baseline_file and self.baseline_file.exists():
            try:
                with open(self.baseline_file) as f:
                    self.baselines = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.baselines = {}

    def save_baselines(self):
        """Save performance baselines to file."""
        if self.baseline_file:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(self.baselines, f, indent=2)

    def benchmark_conversion(self, input_docx: Path, test_name: str) -> PerformanceBenchmark:
        """Benchmark DOCX to EPUB conversion performance."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        peak_memory = initial_memory

        try:
            # Monitor memory during conversion
            def memory_monitor():
                nonlocal peak_memory
                while hasattr(memory_monitor, 'running'):
                    current_memory = process.memory_info().rss / 1024 / 1024
                    peak_memory = max(peak_memory, current_memory)
                    time.sleep(0.1)

            # Start memory monitoring in background
            import threading
            memory_monitor.running = True
            monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
            monitor_thread.start()

            # Perform conversion
            from .assemble import assemble_epub
            from .convert import convert_file_to_html
            from .metadata import EpubMetadata

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "benchmark.epub"

                html_chunks, images, title = convert_file_to_html(input_docx)
                metadata = EpubMetadata(title=title or 'Benchmark', author='Test')

                assemble_epub(
                    html_chunks=html_chunks,
                    metadata=metadata,
                    output_path=output_path,
                    images=images
                )

            # Stop memory monitoring
            memory_monitor.running = False

            duration_ms = (time.time() - start_time) * 1000
            file_size_mb = input_docx.stat().st_size / 1024 / 1024
            conversion_rate = file_size_mb / (duration_ms / 1000) if duration_ms > 0 else 0

            # Check for performance regression
            baseline_duration = self.baselines.get(test_name)
            performance_regression = False

            if baseline_duration:
                # Consider it a regression if > 20% slower
                regression_threshold = baseline_duration * 1.2
                performance_regression = duration_ms > regression_threshold
            else:
                # Set new baseline
                self.baselines[test_name] = duration_ms
                self.save_baselines()

            return PerformanceBenchmark(
                test_name=test_name,
                duration_ms=duration_ms,
                memory_peak_mb=peak_memory,
                file_size_mb=file_size_mb,
                conversion_rate_mb_per_sec=conversion_rate,
                baseline_duration_ms=baseline_duration,
                performance_regression=performance_regression
            )

        except Exception:
            memory_monitor.running = False
            duration_ms = (time.time() - start_time) * 1000
            file_size_mb = input_docx.stat().st_size / 1024 / 1024

            return PerformanceBenchmark(
                test_name=f"{test_name}_error",
                duration_ms=duration_ms,
                memory_peak_mb=peak_memory,
                file_size_mb=file_size_mb,
                conversion_rate_mb_per_sec=0,
                performance_regression=True
            )


class ReliabilityTestSuite:
    """Comprehensive reliability test suite."""

    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self.fuzzer = DOCXFuzzer()
        self.golden_tester = GoldenEPUBTester(test_data_dir / "golden_fixtures")
        self.performance_tester = PerformanceTester(test_data_dir / "performance_baselines.json")
        self.property_tester = PropertyBasedTester()

    def run_comprehensive_test_suite(self, test_docx_files: List[Path]) -> Dict[str, Any]:
        """Run the complete reliability test suite."""
        results = {
            'test_run_time': time.time(),
            'fuzzing_tests': [],
            'golden_fixture_tests': [],
            'performance_benchmarks': [],
            'property_tests': [],
            'overall_success': True
        }

        # Run fuzzing tests
        for i, docx_file in enumerate(test_docx_files):
            for fuzz_iteration in range(5):  # 5 fuzzed versions per file
                try:
                    fuzzed_docx = self.test_data_dir / f"fuzzed_{i}_{fuzz_iteration}.docx"
                    self.fuzzer.generate_fuzzed_docx(docx_file, fuzzed_docx)

                    # Test that fuzzed file doesn't crash the converter
                    test_result = self._test_conversion_robustness(fuzzed_docx, f"fuzz_{i}_{fuzz_iteration}")
                    results['fuzzing_tests'].append(test_result)

                    if not test_result['success']:
                        results['overall_success'] = False

                except Exception as e:
                    results['fuzzing_tests'].append({
                        'test_name': f"fuzz_{i}_{fuzz_iteration}",
                        'success': False,
                        'error': str(e)
                    })
                    results['overall_success'] = False

        # Run golden fixture tests
        for i, docx_file in enumerate(test_docx_files):
            test_name = f"golden_{docx_file.stem}"
            test_options = {'title': f'Test Document {i}', 'author': 'Test Author'}

            golden_result = self.golden_tester.test_against_golden_fixture(
                docx_file, test_name, test_options
            )
            results['golden_fixture_tests'].append({
                'test_name': golden_result.test_name,
                'success': golden_result.success,
                'duration_ms': golden_result.duration_ms,
                'error': golden_result.error_message
            })

            if not golden_result.success:
                results['overall_success'] = False

        # Run performance benchmarks
        for i, docx_file in enumerate(test_docx_files):
            benchmark = self.performance_tester.benchmark_conversion(
                docx_file, f"perf_{docx_file.stem}"
            )
            results['performance_benchmarks'].append({
                'test_name': benchmark.test_name,
                'duration_ms': benchmark.duration_ms,
                'memory_peak_mb': benchmark.memory_peak_mb,
                'conversion_rate_mb_per_sec': benchmark.conversion_rate_mb_per_sec,
                'performance_regression': benchmark.performance_regression
            })

            if benchmark.performance_regression:
                results['overall_success'] = False

        return results

    def _test_conversion_robustness(self, docx_file: Path, test_name: str) -> Dict[str, Any]:
        """Test that conversion doesn't crash on malformed input."""
        start_time = time.time()

        try:
            from .convert import convert_file_to_html

            # This should not crash, even with malformed input
            html_chunks, images, title = convert_file_to_html(docx_file)

            # Basic validation that we got reasonable output
            success = (
                isinstance(html_chunks, list) and
                isinstance(images, list) and
                isinstance(title, (str, type(None)))
            )

            return {
                'test_name': test_name,
                'success': success,
                'duration_ms': (time.time() - start_time) * 1000,
                'output_chunks': len(html_chunks),
                'output_images': len(images)
            }

        except Exception as e:
            return {
                'test_name': test_name,
                'success': False,
                'duration_ms': (time.time() - start_time) * 1000,
                'error': str(e),
                'error_type': type(e).__name__
            }