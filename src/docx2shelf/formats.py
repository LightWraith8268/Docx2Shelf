"""
Advanced output format support for Docx2Shelf.

This module provides support for converting EPUB to various formats:
- PDF (via weasyprint or prince)
- MOBI (via kindlegen or calibre)
- AZW3 (via calibre)
- Web/HTML (standalone website)
- Plain text
- Word DOCX (reverse conversion)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

try:
    import weasyprint
except ImportError:
    weasyprint = None

try:
    from ebooklib import epub
except ImportError:
    epub = None


@dataclass
class FormatOptions:
    """Options for format conversion."""
    format_type: str
    output_path: Path
    quality: str = "standard"  # standard, high, web
    compression: bool = True
    metadata: Optional[Dict[str, Any]] = None
    custom_css: Optional[str] = None
    page_size: str = "A4"  # For PDF: A4, Letter, Custom
    margin: str = "1in"  # For PDF margins
    font_size: str = "12pt"  # Base font size
    font_family: str = "serif"  # serif, sans-serif, monospace
    include_toc: bool = True
    include_cover: bool = True


class FormatConverter:
    """Base class for format converters."""

    def __init__(self, epub_path: Path):
        self.epub_path = epub_path
        self.temp_dir: Optional[Path] = None
        self.extracted_epub: Optional[Path] = None

    def __enter__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.extracted_epub = self.temp_dir / "epub_content"
        self.extracted_epub.mkdir()

        # Extract EPUB
        with zipfile.ZipFile(self.epub_path, 'r') as zip_ref:
            zip_ref.extractall(self.extracted_epub)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def convert(self, options: FormatOptions) -> bool:
        """Convert to the target format. Subclasses should implement this."""
        raise NotImplementedError


class PDFConverter(FormatConverter):
    """Convert EPUB to PDF."""

    def convert(self, options: FormatOptions) -> bool:
        """Convert EPUB to PDF using weasyprint or prince."""
        try:
            if weasyprint:
                return self._convert_with_weasyprint(options)
            else:
                return self._convert_with_prince(options)
        except Exception as e:
            print(f"PDF conversion failed: {e}")
            return False

    def _convert_with_weasyprint(self, options: FormatOptions) -> bool:
        """Convert using weasyprint."""
        try:
            # Read EPUB content
            content_html = self._generate_single_html(options)

            # Create CSS for PDF
            pdf_css = self._generate_pdf_css(options)

            # Convert to PDF
            html_doc = weasyprint.HTML(string=content_html, base_url=str(self.extracted_epub))
            css_doc = weasyprint.CSS(string=pdf_css)

            pdf_doc = html_doc.render(stylesheets=[css_doc])
            pdf_doc.write_pdf(str(options.output_path))

            print(f"PDF created successfully: {options.output_path}")
            return True

        except Exception as e:
            print(f"Weasyprint conversion failed: {e}")
            return False

    def _convert_with_prince(self, options: FormatOptions) -> bool:
        """Convert using Prince XML (if available)."""
        try:
            # Check if prince is available
            result = subprocess.run(["prince", "--version"],
                                 capture_output=True, text=True)
            if result.returncode != 0:
                print("Prince XML not found")
                return False

            # Generate single HTML file
            html_file = self.temp_dir / "book.html"
            content_html = self._generate_single_html(options)
            html_file.write_text(content_html, encoding="utf-8")

            # Generate CSS
            css_file = self.temp_dir / "book.css"
            pdf_css = self._generate_pdf_css(options)
            css_file.write_text(pdf_css, encoding="utf-8")

            # Convert with Prince
            cmd = [
                "prince",
                "--style", str(css_file),
                "--output", str(options.output_path),
                str(html_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"PDF created successfully: {options.output_path}")
                return True
            else:
                print(f"Prince conversion failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"Prince conversion failed: {e}")
            return False

    def _generate_single_html(self, options: FormatOptions) -> str:
        """Generate a single HTML file from EPUB content."""
        # Read OPF file to get content order
        opf_files = list(self.extracted_epub.glob("**/*.opf"))
        if not opf_files:
            raise ValueError("No OPF file found in EPUB")

        opf_content = opf_files[0].read_text(encoding="utf-8")

        # Parse content files from OPF (simplified)
        content_files = []
        content_dir = opf_files[0].parent

        # Find XHTML files
        for xhtml_file in content_dir.glob("**/*.xhtml"):
            if "nav" not in xhtml_file.name.lower():
                content_files.append(xhtml_file)

        content_files.sort(key=lambda x: x.name)

        # Build combined HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            '<meta charset="utf-8"/>',
            f'<title>{options.metadata.get("title", "Book") if options.metadata else "Book"}</title>',
        ]

        # Add custom CSS if provided
        if options.custom_css:
            html_parts.append(f'<style>{options.custom_css}</style>')

        html_parts.extend([
            '</head>',
            '<body>'
        ])

        # Add cover if requested
        if options.include_cover:
            cover_files = list(content_dir.glob("**/cover.*"))
            if cover_files:
                html_parts.append(f'<div class="cover-page"><img src="{cover_files[0].name}" alt="Cover"/></div>')

        # Add content
        for content_file in content_files:
            try:
                file_content = content_file.read_text(encoding="utf-8")
                # Extract body content (simplified)
                if "<body>" in file_content and "</body>" in file_content:
                    body_start = file_content.find("<body>") + 6
                    body_end = file_content.find("</body>")
                    body_content = file_content[body_start:body_end]
                    html_parts.append(f'<div class="chapter">{body_content}</div>')
            except Exception as e:
                print(f"Error reading {content_file}: {e}")

        html_parts.extend([
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    def _generate_pdf_css(self, options: FormatOptions) -> str:
        """Generate CSS optimized for PDF output."""
        return f"""
@page {{
    size: {options.page_size};
    margin: {options.margin};
    @top-center {{
        content: string(doctitle);
        font-size: 10pt;
        color: #666;
    }}
    @bottom-center {{
        content: counter(page);
        font-size: 10pt;
        color: #666;
    }}
}}

body {{
    font-family: {options.font_family};
    font-size: {options.font_size};
    line-height: 1.6;
    color: #000;
    background: white;
}}

h1, h2, h3, h4, h5, h6 {{
    page-break-after: avoid;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}}

h1 {{
    string-set: doctitle content();
    page-break-before: always;
    font-size: 1.8em;
}}

h2 {{ font-size: 1.5em; }}
h3 {{ font-size: 1.3em; }}

p {{
    margin: 0 0 1em 0;
    text-align: justify;
    orphans: 3;
    widows: 3;
}}

.cover-page {{
    page-break-after: always;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
}}

.cover-page img {{
    max-width: 100%;
    max-height: 100%;
}}

.chapter {{
    page-break-before: avoid;
}}

img {{
    max-width: 100%;
    height: auto;
    page-break-inside: avoid;
}}

table {{
    page-break-inside: avoid;
    width: 100%;
    border-collapse: collapse;
}}

pre, code {{
    font-family: monospace;
    background: #f5f5f5;
    padding: 0.5em;
    page-break-inside: avoid;
}}

blockquote {{
    margin: 1em 2em;
    font-style: italic;
    border-left: 3px solid #ccc;
    padding-left: 1em;
}}
"""


class MOBIConverter(FormatConverter):
    """Convert EPUB to MOBI using Calibre or kindlegen."""

    def convert(self, options: FormatOptions) -> bool:
        """Convert EPUB to MOBI."""
        try:
            # Try Calibre first, then kindlegen
            if self._convert_with_calibre(options):
                return True
            else:
                return self._convert_with_kindlegen(options)
        except Exception as e:
            print(f"MOBI conversion failed: {e}")
            return False

    def _convert_with_calibre(self, options: FormatOptions) -> bool:
        """Convert using Calibre's ebook-convert."""
        try:
            cmd = [
                "ebook-convert",
                str(self.epub_path),
                str(options.output_path),
                "--output-profile", "kindle",
            ]

            if options.compression:
                cmd.extend(["--mobi-file-type", "new"])

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"MOBI created successfully: {options.output_path}")
                return True
            else:
                print(f"Calibre conversion failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("Calibre not found")
            return False
        except Exception as e:
            print(f"Calibre conversion error: {e}")
            return False

    def _convert_with_kindlegen(self, options: FormatOptions) -> bool:
        """Convert using Amazon's kindlegen (legacy)."""
        try:
            cmd = ["kindlegen", str(self.epub_path), "-o", options.output_path.name]

            result = subprocess.run(cmd, capture_output=True, text=True,
                                 cwd=str(options.output_path.parent))

            # kindlegen returns 1 for warnings, 0 for success
            if result.returncode in [0, 1]:
                print(f"MOBI created successfully: {options.output_path}")
                return True
            else:
                print(f"kindlegen conversion failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("kindlegen not found")
            return False
        except Exception as e:
            print(f"kindlegen conversion error: {e}")
            return False


class AZW3Converter(FormatConverter):
    """Convert EPUB to AZW3 using Calibre."""

    def convert(self, options: FormatOptions) -> bool:
        """Convert EPUB to AZW3."""
        try:
            cmd = [
                "ebook-convert",
                str(self.epub_path),
                str(options.output_path),
                "--output-profile", "kindle_dx",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"AZW3 created successfully: {options.output_path}")
                return True
            else:
                print(f"AZW3 conversion failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("Calibre not found for AZW3 conversion")
            return False
        except Exception as e:
            print(f"AZW3 conversion error: {e}")
            return False


class WebConverter(FormatConverter):
    """Convert EPUB to standalone website."""

    def convert(self, options: FormatOptions) -> bool:
        """Convert EPUB to web format."""
        try:
            web_dir = options.output_path
            web_dir.mkdir(parents=True, exist_ok=True)

            # Copy EPUB content
            content_dir = web_dir / "content"
            shutil.copytree(self.extracted_epub, content_dir, dirs_exist_ok=True)

            # Generate navigation
            self._generate_web_navigation(web_dir, options)

            # Generate index.html
            self._generate_web_index(web_dir, options)

            # Copy/generate web assets
            self._generate_web_assets(web_dir, options)

            print(f"Website created successfully: {options.output_path}")
            return True

        except Exception as e:
            print(f"Web conversion failed: {e}")
            return False

    def _generate_web_navigation(self, web_dir: Path, options: FormatOptions) -> None:
        """Generate navigation menu for the website."""
        # Find content files
        content_files = []
        content_dir = web_dir / "content"

        for xhtml_file in content_dir.glob("**/*.xhtml"):
            if "nav" not in xhtml_file.name.lower():
                content_files.append(xhtml_file.relative_to(content_dir))

        content_files.sort(key=lambda x: x.name)

        nav_html = ['<nav class="book-nav">']
        nav_html.append('<h3>Contents</h3>')
        nav_html.append('<ul>')

        for i, content_file in enumerate(content_files):
            title = f"Chapter {i + 1}"
            # Try to extract title from file
            try:
                file_content = (content_dir / content_file).read_text(encoding="utf-8")
                if "<h1>" in file_content:
                    start = file_content.find("<h1>") + 4
                    end = file_content.find("</h1>", start)
                    if end > start:
                        title = file_content[start:end].strip()
            except Exception:
                pass

            nav_html.append(f'<li><a href="content/{content_file}">{title}</a></li>')

        nav_html.append('</ul>')
        nav_html.append('</nav>')

        # Save navigation
        (web_dir / "navigation.html").write_text('\n'.join(nav_html), encoding="utf-8")

    def _generate_web_index(self, web_dir: Path, options: FormatOptions) -> None:
        """Generate the main index.html file."""
        title = options.metadata.get("title", "Book") if options.metadata else "Book"
        author = options.metadata.get("author", "Unknown") if options.metadata else "Unknown"

        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="styles/web.css">
</head>
<body>
    <header class="book-header">
        <h1>{title}</h1>
        <p class="author">by {author}</p>
    </header>

    <main class="book-container">
        <aside class="sidebar">
            <div id="navigation"></div>
        </aside>

        <section class="content-area">
            <div id="reader">
                <h2>Welcome</h2>
                <p>Select a chapter from the navigation menu to start reading.</p>
            </div>
        </section>
    </main>

    <script src="scripts/reader.js"></script>
</body>
</html>"""

        (web_dir / "index.html").write_text(index_html, encoding="utf-8")

    def _generate_web_assets(self, web_dir: Path, options: FormatOptions) -> None:
        """Generate CSS and JavaScript for the web version."""
        # Create directories
        (web_dir / "styles").mkdir(exist_ok=True)
        (web_dir / "scripts").mkdir(exist_ok=True)

        # Generate CSS
        web_css = """
/* Web Reader Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f8f9fa;
}

.book-header {
    background: #fff;
    padding: 1rem 2rem;
    border-bottom: 1px solid #e9ecef;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.book-header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.author {
    color: #666;
    font-style: italic;
}

.book-container {
    display: flex;
    height: calc(100vh - 120px);
}

.sidebar {
    width: 300px;
    background: #fff;
    border-right: 1px solid #e9ecef;
    overflow-y: auto;
    padding: 1rem;
}

.book-nav h3 {
    margin-bottom: 1rem;
    color: #495057;
}

.book-nav ul {
    list-style: none;
}

.book-nav li {
    margin-bottom: 0.5rem;
}

.book-nav a {
    color: #007bff;
    text-decoration: none;
    padding: 0.5rem;
    display: block;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.book-nav a:hover {
    background: #f8f9fa;
}

.content-area {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
}

#reader {
    max-width: 800px;
    margin: 0 auto;
    background: #fff;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

#reader h1, #reader h2, #reader h3 {
    margin-bottom: 1rem;
    color: #343a40;
}

#reader p {
    margin-bottom: 1rem;
    text-align: justify;
}

#reader img {
    max-width: 100%;
    height: auto;
    margin: 1rem 0;
    border-radius: 4px;
}

@media (max-width: 768px) {
    .book-container {
        flex-direction: column;
    }

    .sidebar {
        width: 100%;
        height: auto;
        max-height: 200px;
    }

    .content-area {
        padding: 1rem;
    }

    #reader {
        padding: 1rem;
    }
}
"""

        (web_dir / "styles" / "web.css").write_text(web_css, encoding="utf-8")

        # Generate JavaScript
        web_js = """
// Web Reader JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Load navigation
    fetch('navigation.html')
        .then(response => response.text())
        .then(html => {
            document.getElementById('navigation').innerHTML = html;

            // Add click handlers
            document.querySelectorAll('.book-nav a').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    loadChapter(this.href);
                });
            });
        })
        .catch(error => {
            console.error('Error loading navigation:', error);
        });
});

function loadChapter(url) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            // Extract body content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const body = doc.querySelector('body');

            if (body) {
                document.getElementById('reader').innerHTML = body.innerHTML;
            } else {
                document.getElementById('reader').innerHTML = html;
            }

            // Scroll to top
            document.querySelector('.content-area').scrollTo(0, 0);
        })
        .catch(error => {
            console.error('Error loading chapter:', error);
            document.getElementById('reader').innerHTML = '<p>Error loading chapter.</p>';
        });
}
"""

        (web_dir / "scripts" / "reader.js").write_text(web_js, encoding="utf-8")


class TextConverter(FormatConverter):
    """Convert EPUB to plain text."""

    def convert(self, options: FormatOptions) -> bool:
        """Convert EPUB to plain text."""
        try:
            # Find content files
            content_files = []
            for xhtml_file in self.extracted_epub.glob("**/*.xhtml"):
                if "nav" not in xhtml_file.name.lower():
                    content_files.append(xhtml_file)

            content_files.sort(key=lambda x: x.name)

            # Extract text content
            text_content = []

            for content_file in content_files:
                try:
                    file_content = content_file.read_text(encoding="utf-8")
                    # Simple HTML tag removal (basic)
                    import re
                    text = re.sub(r'<[^>]+>', '', file_content)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text:
                        text_content.append(text)
                        text_content.append('\n\n' + '='*50 + '\n\n')
                except Exception as e:
                    print(f"Error processing {content_file}: {e}")

            # Save as text file
            options.output_path.write_text('\n'.join(text_content), encoding="utf-8")

            print(f"Text file created successfully: {options.output_path}")
            return True

        except Exception as e:
            print(f"Text conversion failed: {e}")
            return False


def convert_epub(epub_path: Path, format_type: str, output_path: Path, **kwargs) -> bool:
    """
    Convert EPUB to various formats.

    Args:
        epub_path: Path to the source EPUB file
        format_type: Target format ('pdf', 'mobi', 'azw3', 'web', 'txt')
        output_path: Path for the output file/directory
        **kwargs: Additional options for FormatOptions

    Returns:
        bool: True if conversion was successful
    """
    if not epub_path.exists():
        print(f"EPUB file not found: {epub_path}")
        return False

    # Create format options
    options = FormatOptions(
        format_type=format_type,
        output_path=output_path,
        **kwargs
    )

    # Select converter
    converter_class = {
        'pdf': PDFConverter,
        'mobi': MOBIConverter,
        'azw3': AZW3Converter,
        'web': WebConverter,
        'txt': TextConverter,
        'text': TextConverter,
    }.get(format_type.lower())

    if not converter_class:
        print(f"Unsupported format: {format_type}")
        return False

    # Convert
    with converter_class(epub_path) as converter:
        return converter.convert(options)


def get_supported_formats() -> List[str]:
    """Get list of supported output formats."""
    return ['pdf', 'mobi', 'azw3', 'web', 'txt']


def check_format_dependencies(format_type: str) -> Dict[str, bool]:
    """Check if dependencies for a format are available."""
    deps = {}

    if format_type == 'pdf':
        deps['weasyprint'] = weasyprint is not None
        try:
            subprocess.run(["prince", "--version"], capture_output=True)
            deps['prince'] = True
        except FileNotFoundError:
            deps['prince'] = False

    elif format_type in ['mobi', 'azw3']:
        try:
            subprocess.run(["ebook-convert", "--version"], capture_output=True)
            deps['calibre'] = True
        except FileNotFoundError:
            deps['calibre'] = False

        if format_type == 'mobi':
            try:
                subprocess.run(["kindlegen"], capture_output=True)
                deps['kindlegen'] = True
            except FileNotFoundError:
                deps['kindlegen'] = False

    elif format_type == 'web':
        deps['builtin'] = True  # No external dependencies

    elif format_type == 'txt':
        deps['builtin'] = True  # No external dependencies

    return deps