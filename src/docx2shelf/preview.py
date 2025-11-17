from __future__ import annotations

import http.server
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional


class EPUBPreviewHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for EPUB preview."""

    def __init__(self, *args, preview_dir: Path, **kwargs):
        self.preview_dir = preview_dir
        super().__init__(*args, directory=str(preview_dir), **kwargs)

    def end_headers(self):
        # Add CORS headers for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress access logs unless in verbose mode
        pass


def create_preview_index(preview_dir: Path, title: str = "EPUB Preview") -> Path:
    """Create an index.html file for EPUB preview."""

    # Find all XHTML files
    xhtml_files = sorted(preview_dir.glob("**/*.xhtml"))
    css_files = sorted(preview_dir.glob("**/*.css"))

    # Create a simple index page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        .file-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .file-group {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        .file-group h2 {{
            margin-top: 0;
            color: #495057;
            font-size: 1.2em;
        }}
        .file-link {{
            display: block;
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            text-decoration: none;
            color: #007acc;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            transition: background-color 0.2s;
        }}
        .file-link:hover {{
            background-color: #e3f2fd;
            text-decoration: none;
        }}
        .preview-frame {{
            width: 100%;
            height: 600px;
            border: 1px solid #ccc;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .btn {{
            padding: 8px 16px;
            margin: 5px;
            background: #007acc;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
        .btn:hover {{
            background: #005fa3;
        }}
        .status {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
    </style>
</head>
<body>
    <h1>📚 {title}</h1>

    <div class="status">
        ✅ Preview generated successfully. Use this page to review your EPUB content before final export.
    </div>

    <div class="controls">
        <h2>Quick Actions</h2>
        <button class="btn" onclick="location.reload()">🔄 Refresh</button>
        <a href="#" class="btn" onclick="toggleFrame()">👁️ Toggle Preview Frame</a>
    </div>

    <div class="file-list">
        <div class="file-group">
            <h2>📄 Content Files</h2>
"""

    # Add links to XHTML files
    for xhtml_file in xhtml_files:
        rel_path = xhtml_file.relative_to(preview_dir)
        file_name = xhtml_file.stem.replace("_", " ").title()
        html_content += f'            <a href="{rel_path}" class="file-link" target="preview-frame">{file_name}</a>\n'

    html_content += """        </div>

        <div class="file-group">
            <h2>🎨 Style Files</h2>
"""

    # Add links to CSS files
    for css_file in css_files:
        rel_path = css_file.relative_to(preview_dir)
        file_name = css_file.stem.replace("_", " ").title()
        html_content += (
            f'            <a href="{rel_path}" class="file-link" target="_blank">{file_name}</a>\n'
        )

    html_content += """        </div>
    </div>

    <iframe id="preview-frame" name="preview-frame" class="preview-frame"
            src="about:blank" title="Content Preview">
    </iframe>

    <script>
        function toggleFrame() {
            const frame = document.getElementById('preview-frame');
            if (frame.style.display === 'none') {
                frame.style.display = 'block';
            } else {
                frame.style.display = 'none';
            }
        }

        // Auto-load first content file
        window.addEventListener('load', function() {
            const firstLink = document.querySelector('.file-link[target="preview-frame"]');
            if (firstLink) {
                document.getElementById('preview-frame').src = firstLink.href;
            }
        });
    </script>
</body>
</html>"""

    index_path = preview_dir / "index.html"
    index_path.write_text(html_content, encoding="utf-8")
    return index_path


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    import socket

    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue

    raise RuntimeError(
        f"Could not find available port in range {start_port}-{start_port + max_attempts}"
    )


def start_preview_server(
    preview_dir: Path, port: int = 8000, quiet: bool = False
) -> tuple[threading.Thread, int]:
    """Start a local HTTP server for EPUB preview.

    Returns tuple of (server_thread, actual_port)
    """
    actual_port = find_available_port(port)

    def serve():
        handler = lambda *args, **kwargs: EPUBPreviewHandler(
            *args, preview_dir=preview_dir, **kwargs
        )

        with socketserver.TCPServer(("localhost", actual_port), handler) as httpd:
            if not quiet:
                print(f"🌐 Preview server started at http://localhost:{actual_port}")
            httpd.serve_forever()

    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()

    # Give server time to start
    time.sleep(0.5)

    return server_thread, actual_port


def open_preview_in_browser(port: int, quiet: bool = False) -> bool:
    """Open the preview in the default web browser."""
    url = f"http://localhost:{port}"

    try:
        if not quiet:
            print(f"🚀 Opening preview in browser: {url}")

        webbrowser.open(url)
        return True
    except Exception as e:
        if not quiet:
            print(f"Could not open browser: {e}", file=sys.stderr)
            print(f"Manual URL: {url}", file=sys.stderr)
        return False


def create_epub_preview(
    epub_content_dir: Path, output_dir: Path, title: str = "EPUB Preview", quiet: bool = False
) -> Path:
    """Create a preview directory structure from EPUB content.

    Returns path to the preview directory.
    """
    if not epub_content_dir.exists():
        raise FileNotFoundError(f"EPUB content directory not found: {epub_content_dir}")

    # Create preview directory
    preview_dir = output_dir / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    if not quiet:
        print(f"📁 Creating preview in: {preview_dir}")

    # Copy all EPUB content to preview directory
    import shutil

    for item in epub_content_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, preview_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, preview_dir / item.name, dirs_exist_ok=True)

    # Create index page
    index_path = create_preview_index(preview_dir, title)

    if not quiet:
        print(f"📄 Created preview index: {index_path}")

    return preview_dir


def run_live_preview(
    epub_content_dir: Path,
    output_dir: Path,
    title: str = "EPUB Preview",
    port: int = 8000,
    auto_open: bool = True,
    quiet: bool = False,
) -> Optional[int]:
    """Run complete live preview workflow.

    Returns the port number if successful, None if failed.
    """
    try:
        # Create preview directory
        preview_dir = create_epub_preview(epub_content_dir, output_dir, title, quiet)

        # Start server
        server_thread, actual_port = start_preview_server(preview_dir, port, quiet)

        # Open in browser
        if auto_open:
            open_preview_in_browser(actual_port, quiet)

        if not quiet:
            print("\n" + "=" * 50)
            print("📚 EPUB Preview Ready!")
            print(f"🌐 URL: http://localhost:{actual_port}")
            print("📁 Preview files:", preview_dir)
            print("\nPress Ctrl+C to stop the preview server")
            print("=" * 50)

        return actual_port

    except Exception as e:
        if not quiet:
            print(f"Error creating preview: {e}", file=sys.stderr)
        return None


def cleanup_preview(preview_dir: Path, quiet: bool = False) -> None:
    """Clean up preview directory."""
    import shutil

    try:
        if preview_dir.exists():
            shutil.rmtree(preview_dir)
            if not quiet:
                print(f"🧹 Cleaned up preview directory: {preview_dir}")
    except Exception as e:
        if not quiet:
            print(f"Warning: Could not clean up preview directory: {e}", file=sys.stderr)
