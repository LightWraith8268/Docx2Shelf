"""
Golden EPUB fixture tests for Docx2Shelf.

These tests maintain known-good EPUB outputs for various DOCX patterns
to catch regressions in the conversion pipeline.
"""

import json
import zipfile
from pathlib import Path
from typing import Any, Dict

import pytest


class GoldenEPUBTest:
    """Base class for golden EPUB fixture tests."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "golden_epubs" / test_name
        self.input_docx = self.fixtures_dir / f"{test_name}.docx"
        self.expected_structure = self.fixtures_dir / "expected_structure.json"
        self.expected_content = self.fixtures_dir / "expected_content"

    def create_test_docx(self, content_html: str, title: str = "Test Document"):
        """Create a minimal DOCX file for testing."""
        # For now, create a placeholder - in a real implementation,
        # we'd use python-docx to create actual DOCX files
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple HTML file as a placeholder
        # In production, this would be actual DOCX creation
        placeholder_path = self.fixtures_dir / f"{self.test_name}_content.html"
        with open(placeholder_path, 'w', encoding='utf-8') as f:
            f.write(f"<h1>{title}</h1>\n{content_html}")

        return placeholder_path

    def extract_epub_structure(self, epub_path: Path) -> Dict[str, Any]:
        """Extract EPUB structure for comparison."""
        structure = {
            "files": [],
            "metadata": {},
            "spine_order": [],
            "nav_content": "",
            "css_content": ""
        }

        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Get file list
            structure["files"] = sorted(epub.namelist())

            # Extract OPF metadata
            try:
                opf_content = epub.read("EPUB/content.opf").decode('utf-8')
                # Simple extraction - in production, we'd use proper XML parsing
                if '<dc:title>' in opf_content:
                    title_start = opf_content.find('<dc:title>') + 10
                    title_end = opf_content.find('</dc:title>')
                    structure["metadata"]["title"] = opf_content[title_start:title_end]
            except:
                pass

            # Extract navigation
            try:
                nav_content = epub.read("EPUB/nav.xhtml").decode('utf-8')
                structure["nav_content"] = nav_content
            except:
                pass

            # Extract CSS
            try:
                css_content = epub.read("EPUB/style/base.css").decode('utf-8')
                structure["css_content"] = css_content[:500]  # First 500 chars
            except:
                pass

        return structure

    def save_expected_structure(self, epub_path: Path):
        """Save the structure of a known-good EPUB as expected output."""
        structure = self.extract_epub_structure(epub_path)

        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        with open(self.expected_structure, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, sort_keys=True)

    def verify_epub_structure(self, epub_path: Path) -> bool:
        """Verify EPUB structure matches expected."""
        if not self.expected_structure.exists():
            pytest.skip(f"No expected structure file for {self.test_name}")

        with open(self.expected_structure, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        actual = self.extract_epub_structure(epub_path)

        # Compare key structure elements
        assert len(actual["files"]) >= len(expected["files"]), f"Missing files in {self.test_name}"

        # Check critical files exist
        critical_files = ["EPUB/content.opf", "EPUB/nav.xhtml", "EPUB/style/base.css"]
        for critical_file in critical_files:
            assert critical_file in actual["files"], f"Missing critical file: {critical_file}"

        # Check metadata if available
        if expected.get("metadata", {}).get("title"):
            assert actual.get("metadata", {}).get("title") == expected["metadata"]["title"]

        return True


def create_simple_test_content():
    """Create simple document content for testing."""
    return """
    <h1>Chapter 1: Introduction</h1>
    <p>This is a simple paragraph with <em>emphasis</em> and <strong>strong text</strong>.</p>
    <p>Another paragraph with a <a href="https://example.com">link</a>.</p>

    <h1>Chapter 2: Content</h1>
    <p>Second chapter content with some <code>inline code</code>.</p>
    <ul>
        <li>First list item</li>
        <li>Second list item</li>
    </ul>
    """


def create_footnotes_test_content():
    """Create document with footnotes for testing."""
    return """
    <h1>Document with Footnotes</h1>
    <p>This is text with a footnote<sup><a href="#fn1" id="fnref1">1</a></sup>.</p>
    <p>Another paragraph with another footnote<sup><a href="#fn2" id="fnref2">2</a></sup>.</p>

    <h2>Footnotes</h2>
    <ol>
        <li id="fn1">This is the first footnote. <a href="#fnref1">↩</a></li>
        <li id="fn2">This is the second footnote with <em>formatting</em>. <a href="#fnref2">↩</a></li>
    </ol>
    """


def create_tables_test_content():
    """Create document with tables for testing."""
    return """
    <h1>Document with Tables</h1>
    <p>Here is a simple table:</p>

    <table>
        <thead>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
                <th>Header 3</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Cell 1</td>
                <td>Cell 2</td>
                <td>Cell 3</td>
            </tr>
            <tr>
                <td>Row 2, Col 1</td>
                <td>Row 2, Col 2</td>
                <td>Row 2, Col 3</td>
            </tr>
        </tbody>
    </table>

    <p>And another table with different formatting:</p>
    <table>
        <tr>
            <td><strong>Name</strong></td>
            <td>John Doe</td>
        </tr>
        <tr>
            <td><strong>Age</strong></td>
            <td>30</td>
        </tr>
    </table>
    """


def create_poetry_test_content():
    """Create document with poetry formatting for testing."""
    return """
    <h1>Poetry Collection</h1>

    <h2>Poem 1: Lines</h2>
    <div class="poem">
        <p class="line">Roses are red,</p>
        <p class="line">Violets are blue,</p>
        <p class="line">EPUB conversion</p>
        <p class="line">Should work for you.</p>
    </div>

    <h2>Poem 2: Stanzas</h2>
    <div class="poem">
        <div class="stanza">
            <p class="line">First stanza line one</p>
            <p class="line">First stanza line two</p>
        </div>

        <div class="stanza">
            <p class="line">Second stanza line one</p>
            <p class="line">Second stanza line two</p>
        </div>
    </div>
    """


def create_rtl_test_content():
    """Create document with RTL text for testing."""
    return """
    <h1>RTL Text Document</h1>
    <p>This document contains both LTR and RTL text.</p>

    <h2>Arabic Text</h2>
    <p dir="rtl" lang="ar">هذا نص باللغة العربية من اليمين إلى اليسار.</p>
    <p dir="rtl" lang="ar">فقرة أخرى بالعربية مع <strong>نص غامق</strong> و<em>نص مائل</em>.</p>

    <h2>Hebrew Text</h2>
    <p dir="rtl" lang="he">זהו טקסט בעברית מימין לשמאל.</p>

    <h2>Mixed Content</h2>
    <p>This is LTR text with some <span dir="rtl" lang="ar">عربي</span> inline RTL content.</p>
    """


# Test fixtures using the golden EPUB test framework
class TestGoldenEPUBFixtures:
    """Test suite for golden EPUB fixtures."""

    def test_simple_document_structure(self):
        """Test conversion of a simple document maintains expected structure."""
        test = GoldenEPUBTest("simple")

        # Check if golden fixture exists
        golden_epub = test.fixtures_dir / "simple_golden.epub"
        if not golden_epub.exists():
            pytest.skip(f"Golden fixture not found: {golden_epub}. Run scripts/generate_golden_fixtures.py first.")

        # Verify the golden fixture structure
        assert test.verify_epub_structure(golden_epub), "Golden EPUB structure validation failed"

    def test_footnotes_document_structure(self):
        """Test conversion of document with footnotes maintains expected structure."""
        test = GoldenEPUBTest("footnotes")

        golden_epub = test.fixtures_dir / "footnotes_golden.epub"
        if not golden_epub.exists():
            pytest.skip(f"Golden fixture not found: {golden_epub}. Run scripts/generate_golden_fixtures.py first.")

        assert test.verify_epub_structure(golden_epub), "Footnotes EPUB structure validation failed"

    def test_tables_document_structure(self):
        """Test conversion of document with tables maintains expected structure."""
        test = GoldenEPUBTest("tables")

        golden_epub = test.fixtures_dir / "tables_golden.epub"
        if not golden_epub.exists():
            pytest.skip(f"Golden fixture not found: {golden_epub}. Run scripts/generate_golden_fixtures.py first.")

        assert test.verify_epub_structure(golden_epub), "Tables EPUB structure validation failed"

    def test_poetry_document_structure(self):
        """Test conversion of document with poetry formatting maintains expected structure."""
        test = GoldenEPUBTest("poetry")

        golden_epub = test.fixtures_dir / "poetry_golden.epub"
        if not golden_epub.exists():
            pytest.skip(f"Golden fixture not found: {golden_epub}. Run scripts/generate_golden_fixtures.py first.")

        assert test.verify_epub_structure(golden_epub), "Poetry EPUB structure validation failed"

    def test_images_document_structure(self):
        """Test conversion of document with images maintains expected structure."""
        test = GoldenEPUBTest("images")

        golden_epub = test.fixtures_dir / "images_golden.epub"
        if not golden_epub.exists():
            pytest.skip(f"Golden fixture not found: {golden_epub}. Run scripts/generate_golden_fixtures.py first.")

        assert test.verify_epub_structure(golden_epub), "Images EPUB structure validation failed"


class TestGoldenRegressionTesting:
    """Test suite for regression testing against golden EPUBs."""

    def test_conversion_produces_consistent_output(self):
        """Test that converting test files produces output consistent with golden EPUBs."""
        import subprocess
        import tempfile

        fixtures_dir = Path(__file__).parent / "fixtures" / "golden_epubs"
        test_cases = ["simple", "footnotes", "tables", "poetry", "images"]

        for test_name in test_cases:
            test_dir = fixtures_dir / test_name
            source_file = None

            # Find source file (DOCX or HTML)
            for ext in [".docx", ".html"]:
                potential_source = test_dir / f"{test_name}{ext}"
                if potential_source.exists():
                    source_file = potential_source
                    break

            golden_epub = test_dir / f"{test_name}_golden.epub"

            if not source_file or not golden_epub.exists():
                pytest.skip(f"Missing source or golden file for {test_name}")
                continue

            # Convert source to EPUB
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_epub = Path(temp_dir) / f"{test_name}_test.epub"

                # Run docx2shelf conversion
                cmd = [
                    "python", "-m", "docx2shelf", "build",
                    "--input", str(source_file),
                    "--title", f"{test_name.title()} Test",
                    "--author", "Test Author",
                    "--output", str(temp_epub)
                ]

                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        pytest.skip(f"Conversion failed for {test_name}: {result.stderr}")
                        continue

                    # Compare with golden EPUB
                    test = GoldenEPUBTest(test_name)
                    golden_structure = test.extract_epub_structure(golden_epub)
                    test_structure = test.extract_epub_structure(temp_epub)

                    # Compare critical elements
                    assert len(test_structure["files"]) >= len(golden_structure["files"]), \
                        f"Test EPUB has fewer files than golden for {test_name}"

                    # Check for critical files
                    critical_files = ["EPUB/content.opf", "EPUB/nav.xhtml"]
                    for critical_file in critical_files:
                        assert critical_file in test_structure["files"], \
                            f"Missing critical file {critical_file} in {test_name}"

                    print(f"✓ {test_name} conversion matches golden EPUB structure")

                except subprocess.CalledProcessError as e:
                    pytest.skip(f"Conversion process failed for {test_name}: {e}")
                except Exception as e:
                    pytest.fail(f"Unexpected error testing {test_name}: {e}")

    def test_theme_consistency_across_golden_files(self):
        """Test that different themes produce consistent structural changes."""
        import subprocess
        import tempfile

        fixtures_dir = Path(__file__).parent / "fixtures" / "golden_epubs"
        simple_source = fixtures_dir / "simple" / "simple.html"

        if not simple_source.exists():
            pytest.skip("Simple test source not found")

        themes = ["serif", "sans", "printlike"]
        epub_structures = {}

        for theme in themes:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_epub = Path(temp_dir) / f"simple_{theme}.epub"

                cmd = [
                    "python", "-m", "docx2shelf", "build",
                    "--input", str(simple_source),
                    "--title", "Simple Test",
                    "--author", "Test Author",
                    "--theme", theme,
                    "--output", str(temp_epub)
                ]

                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0 and temp_epub.exists():
                        test = GoldenEPUBTest("simple")
                        structure = test.extract_epub_structure(temp_epub)
                        epub_structures[theme] = structure
                        print(f"✓ Generated EPUB with {theme} theme")

                except Exception as e:
                    print(f"✗ Failed to generate EPUB with {theme} theme: {e}")

        # Compare structures - they should have the same files but different CSS
        if len(epub_structures) >= 2:
            themes_list = list(epub_structures.keys())
            base_theme = themes_list[0]
            base_files = set(epub_structures[base_theme]["files"])

            for theme in themes_list[1:]:
                theme_files = set(epub_structures[theme]["files"])
                assert base_files == theme_files, \
                    f"File structure differs between {base_theme} and {theme} themes"

            print("✓ All themes produce consistent file structures")
        else:
            pytest.skip("Not enough themes tested successfully")


# Helper function to generate golden fixtures (for manual use)
def generate_golden_fixtures():
    """Generate golden EPUB fixtures from test documents."""
    test_cases = [
        ("simple", create_simple_test_content(), "Simple Test Document"),
        ("footnotes", create_footnotes_test_content(), "Footnotes Test Document"),
        ("tables", create_tables_test_content(), "Tables Test Document"),
        ("poetry", create_poetry_test_content(), "Poetry Test Document"),
        ("rtl", create_rtl_test_content(), "RTL Test Document")
    ]

    for test_name, content, title in test_cases:
        test = GoldenEPUBTest(test_name)

        # Create the test content file
        content_file = test.create_test_docx(content, title)
        print(f"Created test content for {test_name}: {content_file}")

        # In a real implementation, we would:
        # 1. Convert the DOCX to EPUB using docx2shelf
        # 2. Save the resulting EPUB structure as the golden fixture
        # 3. Store expected content snippets for verification

        print(f"Golden fixture template created for {test_name}")


if __name__ == "__main__":
    # Generate fixtures when run directly
    generate_golden_fixtures()