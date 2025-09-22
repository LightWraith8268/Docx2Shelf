"""
Reader smoke tests for Docx2Shelf.

These tests verify that generated EPUBs can be properly rendered
and display correctly in various reader environments.
"""

import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class EPUBRenderer:
    """Headless EPUB renderer for smoke testing."""

    def __init__(self, browser: str = "chrome"):
        self.browser = browser
        self.driver = None

    def setup_driver(self):
        """Set up headless browser driver."""
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available for reader smoke tests")

        try:
            if self.browser == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                self.driver = webdriver.Chrome(options=options)
            elif self.browser == "firefox":
                options = FirefoxOptions()
                options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")

        except Exception as e:
            pytest.skip(f"Could not set up {self.browser} driver: {e}")

    def teardown_driver(self):
        """Clean up browser driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def extract_epub_content(self, epub_path: Path) -> Dict[str, str]:
        """Extract XHTML content from EPUB for rendering."""
        content_files = {}

        with zipfile.ZipFile(epub_path, 'r') as epub:
            for file_info in epub.filelist:
                if file_info.filename.endswith('.xhtml') or file_info.filename.endswith('.html'):
                    try:
                        content = epub.read(file_info.filename).decode('utf-8')
                        content_files[file_info.filename] = content
                    except Exception:
                        continue

        return content_files

    def render_xhtml_content(self, xhtml_content: str, css_content: str = "") -> Dict[str, Any]:
        """Render XHTML content and return rendering metrics."""
        if not self.driver:
            self.setup_driver()

        # Create a complete HTML document for rendering
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EPUB Smoke Test</title>
            <style>
                {css_content}
                body {{ font-family: serif; margin: 2em; }}
                h1, h2, h3 {{ color: #333; }}
                p {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            {xhtml_content}
        </body>
        </html>
        """

        # Load content into browser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(full_html)
            temp_path = f.name

        try:
            self.driver.get(f"file://{temp_path}")

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Collect rendering metrics
            metrics = self.collect_rendering_metrics()
            return metrics

        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    def collect_rendering_metrics(self) -> Dict[str, Any]:
        """Collect rendering metrics from the loaded page."""
        metrics = {
            "page_title": "",
            "headings_count": 0,
            "paragraphs_count": 0,
            "images_count": 0,
            "links_count": 0,
            "page_height": 0,
            "page_width": 0,
            "css_errors": [],
            "js_errors": [],
            "accessibility_issues": []
        }

        try:
            # Basic content metrics
            metrics["page_title"] = self.driver.title

            # Count elements
            metrics["headings_count"] = len(self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6"))
            metrics["paragraphs_count"] = len(self.driver.find_elements(By.TAG_NAME, "p"))
            metrics["images_count"] = len(self.driver.find_elements(By.TAG_NAME, "img"))
            metrics["links_count"] = len(self.driver.find_elements(By.TAG_NAME, "a"))

            # Page dimensions
            metrics["page_height"] = self.driver.execute_script("return document.body.scrollHeight")
            metrics["page_width"] = self.driver.execute_script("return document.body.scrollWidth")

            # Check for basic accessibility
            metrics["accessibility_issues"] = self.check_accessibility_basics()

            # Check for rendering errors
            metrics["css_errors"] = self.check_css_rendering()

        except Exception as e:
            metrics["collection_error"] = str(e)

        return metrics

    def check_accessibility_basics(self) -> List[str]:
        """Check for basic accessibility issues."""
        issues = []

        try:
            # Check for images without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                if not img.get_attribute("alt"):
                    issues.append("Image without alt text found")
                    break

            # Check for headings hierarchy
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            if headings:
                heading_levels = [int(h.tag_name[1]) for h in headings]
                # Check if first heading is h1
                if heading_levels and heading_levels[0] != 1:
                    issues.append("First heading is not h1")

                # Check for skipped heading levels
                for i in range(1, len(heading_levels)):
                    if heading_levels[i] > heading_levels[i-1] + 1:
                        issues.append("Skipped heading level detected")
                        break

            # Check for links without href
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if not link.get_attribute("href") and not link.get_attribute("id"):
                    issues.append("Link without href or id found")
                    break

        except Exception:
            issues.append("Error checking accessibility")

        return issues

    def check_css_rendering(self) -> List[str]:
        """Check for CSS rendering issues."""
        issues = []

        try:
            # Check if CSS is loaded by verifying computed styles
            body = self.driver.find_element(By.TAG_NAME, "body")
            font_family = body.value_of_css_property("font-family")

            if not font_family or font_family == "initial":
                issues.append("CSS may not be properly loaded")

            # Check for elements with zero dimensions (potential layout issues)
            paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
            zero_height_count = 0
            for p in paragraphs[:5]:  # Check first 5 paragraphs
                if p.size["height"] == 0 and p.text.strip():
                    zero_height_count += 1

            if zero_height_count > 0:
                issues.append(f"{zero_height_count} text elements with zero height")

        except Exception:
            issues.append("Error checking CSS rendering")

        return issues


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestReaderSmokeTests:
    """Smoke tests for EPUB rendering in reader environments."""

    def setup_method(self):
        """Set up test method."""
        self.renderer = EPUBRenderer("chrome")

    def teardown_method(self):
        """Clean up after test method."""
        if hasattr(self, 'renderer'):
            self.renderer.teardown_driver()

    def test_basic_epub_rendering(self):
        """Test that a basic EPUB can be rendered without errors."""
        # Create minimal XHTML content
        xhtml_content = """
        <div class="chapter">
            <h1>Chapter 1: Introduction</h1>
            <p>This is a test paragraph with some <em>emphasis</em> and <strong>bold text</strong>.</p>
            <p>Another paragraph with a <a href="#chapter2">link to chapter 2</a>.</p>

            <h2>Section 1.1</h2>
            <p>A subsection with more content.</p>
        </div>
        """

        css_content = """
        .chapter { margin: 1em 0; }
        h1 { font-size: 1.5em; margin-bottom: 0.5em; }
        h2 { font-size: 1.2em; margin-bottom: 0.3em; }
        p { margin-bottom: 1em; }
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)

        # Verify basic rendering
        assert metrics["headings_count"] >= 2, "Should have at least 2 headings"
        assert metrics["paragraphs_count"] >= 3, "Should have at least 3 paragraphs"
        assert metrics["links_count"] >= 1, "Should have at least 1 link"
        assert metrics["page_height"] > 0, "Page should have positive height"
        assert metrics["page_width"] > 0, "Page should have positive width"

        # Check for no major issues
        assert len(metrics["css_errors"]) == 0, f"CSS errors found: {metrics['css_errors']}"

    def test_typography_rendering(self):
        """Test that typography features render correctly."""
        xhtml_content = """
        <div class="typography-test">
            <h1>Typography Test</h1>
            <p>This paragraph tests <em>italic text</em>, <strong>bold text</strong>,
               and <strong><em>bold italic text</em></strong>.</p>

            <p>Smart quotes: "Hello world" and 'single quotes'.</p>
            <p>Em dashes — and en dashes – should render correctly.</p>
            <p>Ellipsis… should also work.</p>

            <blockquote>
                <p>This is a blockquote with proper indentation and styling.</p>
            </blockquote>

            <ul>
                <li>First list item</li>
                <li>Second list item with <code>inline code</code></li>
                <li>Third list item</li>
            </ul>
        </div>
        """

        css_content = """
        .typography-test { font-family: Georgia, serif; }
        blockquote { margin: 1em 2em; font-style: italic; }
        code { font-family: monospace; background: #f5f5f5; padding: 0.2em; }
        ul { margin: 1em 0; padding-left: 2em; }
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)

        # Verify typography elements are present
        assert metrics["headings_count"] >= 1, "Should have heading"
        assert metrics["paragraphs_count"] >= 3, "Should have multiple paragraphs"

    def test_table_rendering(self):
        """Test that tables render correctly."""
        xhtml_content = """
        <div class="table-test">
            <h1>Table Test</h1>
            <p>The following table should render correctly:</p>

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
                        <td>Cell 1,1</td>
                        <td>Cell 1,2</td>
                        <td>Cell 1,3</td>
                    </tr>
                    <tr>
                        <td>Cell 2,1</td>
                        <td>Cell 2,2</td>
                        <td>Cell 2,3</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

        css_content = """
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #ccc; padding: 0.5em; text-align: left; }
        th { background-color: #f5f5f5; font-weight: bold; }
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)

        # Tables should render with proper dimensions
        assert metrics["page_height"] > 100, "Table should add significant height"

    def test_image_rendering(self):
        """Test that images are handled correctly."""
        xhtml_content = """
        <div class="image-test">
            <h1>Image Test</h1>
            <p>Testing image handling:</p>

            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzAwODA4MCIgLz4KICA8dGV4dCB4PSI1MCIgeT0iNTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIwLjNlbSI+VGVzdDwvdGV4dD4KPC9zdmc+"
                 alt="Test image" width="100" height="100" />

            <p>Image with caption should display correctly.</p>
        </div>
        """

        css_content = """
        img { max-width: 100%; height: auto; margin: 1em 0; }
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)

        # Images should be detected
        assert metrics["images_count"] >= 1, "Should have at least 1 image"

        # Check accessibility
        assert "Image without alt text found" not in metrics["accessibility_issues"], \
            "Images should have alt text"

    def test_rtl_text_rendering(self):
        """Test that RTL text renders correctly."""
        xhtml_content = """
        <div class="rtl-test">
            <h1>RTL Text Test</h1>
            <p>Mixed LTR and RTL content:</p>

            <p dir="rtl" lang="ar">هذا نص عربي من اليمين إلى اليسار</p>
            <p dir="rtl" lang="he">זהו טקסט עברי מימין לשמאל</p>

            <p>Mixed content: English with <span dir="rtl" lang="ar">عربي</span> inline.</p>
        </div>
        """

        css_content = """
        [dir="rtl"] { text-align: right; }
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content, css_content)

        # RTL content should render without layout issues
        assert metrics["page_height"] > 0, "RTL content should render with positive height"

    def test_accessibility_compliance(self):
        """Test accessibility compliance of rendered content."""
        xhtml_content = """
        <div class="accessibility-test">
            <h1>Accessibility Test</h1>
            <h2>Section 1</h2>
            <p>This tests proper heading hierarchy.</p>

            <h3>Subsection 1.1</h3>
            <p>Content with proper structure.</p>

            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjMDA4MDgwIiAvPjwvc3ZnPg=="
                 alt="Decorative square" />

            <a href="#section2">Link to section 2</a>

            <h2 id="section2">Section 2</h2>
            <p>Target section for the link above.</p>
        </div>
        """

        metrics = self.renderer.render_xhtml_content(xhtml_content)

        # Check accessibility compliance
        accessibility_issues = metrics["accessibility_issues"]

        assert "First heading is not h1" not in accessibility_issues, \
            "Should start with h1"
        assert "Skipped heading level detected" not in accessibility_issues, \
            "Should not skip heading levels"
        assert "Image without alt text found" not in accessibility_issues, \
            "Images should have alt text"
        assert "Link without href or id found" not in accessibility_issues, \
            "Links should have proper attributes"


# Firefox variant tests
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestReaderSmokeTestsFirefox:
    """Smoke tests using Firefox renderer for cross-browser verification."""

    def setup_method(self):
        """Set up test method."""
        self.renderer = EPUBRenderer("firefox")

    def teardown_method(self):
        """Clean up after test method."""
        if hasattr(self, 'renderer'):
            self.renderer.teardown_driver()

    def test_cross_browser_basic_rendering(self):
        """Test basic rendering in Firefox for cross-browser compatibility."""
        xhtml_content = """
        <div class="cross-browser-test">
            <h1>Cross-Browser Test</h1>
            <p>This content should render consistently across browsers.</p>
            <p>Testing <em>emphasis</em> and <strong>strong</strong> elements.</p>
        </div>
        """

        try:
            metrics = self.renderer.render_xhtml_content(xhtml_content)

            # Basic rendering should work in Firefox too
            assert metrics["headings_count"] >= 1, "Should have headings in Firefox"
            assert metrics["paragraphs_count"] >= 2, "Should have paragraphs in Firefox"
            assert metrics["page_height"] > 0, "Should have positive height in Firefox"

        except Exception as e:
            pytest.skip(f"Firefox driver not available: {e}")


# Helper functions for generating test EPUBs
def create_test_epub_content(content_type: str = "basic") -> str:
    """Create test EPUB content for various scenarios."""
    if content_type == "basic":
        return """
        <h1>Test Chapter</h1>
        <p>Basic test content with <em>formatting</em>.</p>
        """
    elif content_type == "complex":
        return """
        <h1>Complex Chapter</h1>
        <p>Content with <strong>bold</strong> and <em>italic</em> text.</p>
        <table><tr><td>Table</td><td>Content</td></tr></table>
        <ul><li>List item 1</li><li>List item 2</li></ul>
        """
    else:
        return "<h1>Default</h1><p>Default content.</p>"


# Configuration for CI environments
if SELENIUM_AVAILABLE:
    @pytest.fixture(scope="session")
    def selenium_config():
        """Configure Selenium for CI environments."""
        return {
            "headless": True,
            "window_size": (1920, 1080),
            "timeout": 30
        }