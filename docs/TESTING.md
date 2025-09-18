# Testing Guide for Docx2Shelf

This document describes the comprehensive testing framework for Docx2Shelf, covering unit tests, integration tests, property-based tests, golden EPUB fixtures, and reader smoke tests.

## Overview

Docx2Shelf uses a multi-layered testing approach to ensure reliability and catch regressions:

1. **Unit Tests** - Fast tests for individual functions and components
2. **Integration Tests** - Tests for component interaction and workflows
3. **Property-Based Tests** - Hypothesis-driven tests for edge cases
4. **Golden EPUB Fixtures** - Snapshot tests for known-good outputs
5. **Reader Smoke Tests** - Headless browser tests for rendering verification

## Quick Start

### Running Tests

```bash
# Quick unit tests (fast, no external dependencies)
python scripts/run_tests.py --mode quick

# Full test suite (excludes browser tests)
python scripts/run_tests.py --mode full --coverage

# All tests including smoke tests
python scripts/run_tests.py --mode ci

# Specific test categories
python scripts/run_tests.py --mode property  # Property-based tests
python scripts/run_tests.py --mode golden    # Golden fixture tests
python scripts/run_tests.py --mode smoke     # Reader smoke tests
```

### Using pytest directly

```bash
# Install test dependencies
pip install -e .[dev]

# Run all tests
pytest

# Run with coverage
pytest --cov=src/docx2shelf --cov-report=html

# Run specific test categories
pytest -m "unit"          # Unit tests only
pytest -m "integration"   # Integration tests only
pytest -m "property"      # Property-based tests only
pytest -m "smoke"         # Smoke tests only (requires browser)
```

## Test Categories

### Unit Tests

Fast, focused tests for individual functions and classes.

**Location**: `tests/test_*.py` (existing files)
**Markers**: `@pytest.mark.unit`
**Dependencies**: None (pure Python)

```python
# Example unit test
def test_split_html_by_heading_h1():
    html = "<h1>A</h1><p>1</p><h1>B</h1><p>2</p>"
    chunks = split_html_by_heading(html, level="h1")
    assert len(chunks) == 2
    assert "A" in chunks[0] and "1" in chunks[0]
```

### Integration Tests

Tests that verify component interaction and end-to-end workflows.

**Location**: `tests/test_integration_*.py`
**Markers**: `@pytest.mark.integration`
**Dependencies**: May require Pandoc, EPUBCheck

### Property-Based Tests

Hypothesis-driven tests that generate random inputs to verify properties.

**Location**: `tests/test_property_based.py`
**Markers**: `@pytest.mark.property`
**Dependencies**: `hypothesis`

```python
from hypothesis import given, strategies as st

@given(st.lists(st.text(min_size=1), min_size=1))
def test_split_preserves_content(chapter_texts):
    # Test that splitting preserves all content
    pass
```

**Key Properties Tested**:
- Content preservation during splitting
- Filename generation consistency
- Split logic correctness
- Edge case handling

### Golden EPUB Fixtures

Snapshot tests that maintain known-good EPUB outputs for regression detection.

**Location**: `tests/test_golden_epubs.py`
**Fixtures**: `tests/fixtures/golden_epubs/`
**Markers**: `@pytest.mark.golden`

**Test Patterns**:
- Simple documents
- Documents with footnotes
- Documents with tables
- Poetry formatting
- Images and media
- RTL text support

```python
def test_simple_document_structure():
    test = GoldenEPUBTest("simple")
    # Verify EPUB structure matches expected
    assert test.verify_epub_structure(epub_path)
```

### Reader Smoke Tests

Headless browser tests that verify EPUB content renders correctly.

**Location**: `tests/test_reader_smoke.py`
**Markers**: `@pytest.mark.smoke`
**Dependencies**: `selenium`, Chrome/Firefox browser

**Test Areas**:
- Basic XHTML rendering
- Typography and formatting
- Table rendering
- Image handling
- RTL text support
- Accessibility compliance

```python
def test_basic_epub_rendering(self):
    metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)
    assert metrics["headings_count"] >= 2
    assert len(metrics["css_errors"]) == 0
```

## Test Configuration

### pytest.ini

The project uses `pytest.ini` for test configuration:

```ini
[tool:pytest]
testpaths = tests
addopts = --strict-markers --cov=src/docx2shelf --cov-fail-under=70
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (may require external tools)
    smoke: Smoke tests (require browser/rendering)
    property: Property-based tests (using Hypothesis)
    golden: Golden fixture tests (snapshot testing)
```

### Hypothesis Configuration

Property-based tests use Hypothesis with different profiles:

- **dev**: 10 examples (fast for development)
- **ci**: 100 examples (thorough for CI)
- **thorough**: 1000 examples (comprehensive testing)

## Dependencies

### Required for Basic Testing
- `pytest>=7.0`
- `pytest-cov>=4.0`

### Optional for Advanced Testing
- `hypothesis>=6.0` - Property-based testing
- `selenium>=4.0` - Browser automation for smoke tests
- `ruff>=0.5.0` - Code linting
- `mypy>=1.8` - Type checking

Install all test dependencies:
```bash
pip install -e .[dev]
```

## CI Integration

### GitHub Actions

The test suite integrates with GitHub Actions for automated testing:

```yaml
- name: Run test suite
  run: python scripts/run_tests.py --mode ci --coverage

- name: Upload coverage
  uses: codecov/codecov-action@v3
  if: matrix.python-version == '3.11'
```

### Test Matrix

CI tests run across:
- Python versions: 3.11, 3.12
- Operating systems: Ubuntu, Windows, macOS
- With and without optional dependencies (Pandoc, EPUBCheck)

## Writing Tests

### Guidelines

1. **Use appropriate markers** to categorize tests
2. **Write descriptive test names** that explain what is being tested
3. **Include docstrings** for complex test scenarios
4. **Use fixtures** for shared test data
5. **Mock external dependencies** when possible
6. **Test edge cases** and error conditions

### Test Structure

```python
import pytest
from docx2shelf.module import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""

    @pytest.mark.unit
    def test_normal_case(self):
        """Test normal operation with valid inputs."""
        result = function_to_test("valid_input")
        assert result == "expected_output"

    @pytest.mark.unit
    def test_edge_case(self):
        """Test edge case handling."""
        result = function_to_test("")
        assert result is None

    @pytest.mark.integration
    def test_with_external_dependency(self):
        """Test integration with external component."""
        # May require external tools or files
        pass
```

### Fixtures

Use pytest fixtures for shared test data:

```python
@pytest.fixture
def sample_epub_content():
    """Provide sample EPUB content for testing."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "chapters": ["Chapter 1 content", "Chapter 2 content"]
    }

def test_epub_generation(sample_epub_content):
    epub = generate_epub(sample_epub_content)
    assert epub.title == "Test Book"
```

## Coverage Requirements

- **Minimum coverage**: 70% (enforced by CI)
- **Target coverage**: 85%
- **Critical paths**: 95%+ coverage for core conversion logic

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src/docx2shelf --cov-report=html

# View report
open htmlcov/index.html
```

## Performance Testing

While not part of the core test suite, performance benchmarks are available:

```bash
# Run with profiling
pytest --profile

# Memory usage analysis
pytest --memory-profile
```

## Troubleshooting

### Common Issues

**Selenium tests failing**:
- Install Chrome/Firefox browser
- Install appropriate WebDriver
- Check headless mode configuration

**Hypothesis tests taking too long**:
- Reduce example count in profile
- Use `@settings(max_examples=10)` for slow tests

**Coverage too low**:
- Add tests for uncovered code paths
- Remove dead code
- Add integration tests for complex workflows

### Debug Mode

Run tests with debugging enabled:

```bash
# Verbose output
pytest -v

# Debug on failure
pytest --pdb

# Capture output
pytest -s
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Add appropriate markers** for test categorization
3. **Update golden fixtures** if output format changes
4. **Add property-based tests** for complex logic
5. **Include smoke tests** for UI/rendering changes

### Test Review Checklist

- [ ] Tests cover new functionality
- [ ] Tests include edge cases
- [ ] Tests are properly marked
- [ ] Documentation updated
- [ ] Coverage requirements met
- [ ] CI tests pass

## Examples

### Testing a New Converter

```python
class TestNewConverter:
    @pytest.mark.unit
    def test_basic_conversion(self):
        converter = NewConverter()
        result = converter.convert("input")
        assert result == "expected_output"

    @pytest.mark.property
    @given(st.text())
    def test_conversion_properties(self, input_text):
        converter = NewConverter()
        result = converter.convert(input_text)
        # Test that conversion preserves certain properties
        assert len(result) >= 0
        assert isinstance(result, str)

    @pytest.mark.integration
    def test_end_to_end_conversion(self):
        # Test complete conversion workflow
        pass
```

### Adding Golden Fixtures

```python
def test_new_document_type():
    test = GoldenEPUBTest("new_type")
    if not test.input_docx.exists():
        test.create_test_docx(create_new_type_content())

    # Run conversion and verify structure
    assert test.verify_epub_structure(output_epub)
```

For more examples, see the existing test files in the `tests/` directory.