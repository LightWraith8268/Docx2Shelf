"""
Web-based EPUB builder with local server interface.

Provides a modern web interface for EPUB conversion that runs locally,
offering advanced features and live preview capabilities.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import tempfile
import threading
import uuid
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebBuilderHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the web builder interface."""

    def __init__(self, request, client_address, server):
        self.web_builder = server.web_builder
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/" or path == "/index.html":
            self.serve_main_page()
        elif path == "/api/status":
            self.serve_api_status()
        elif path == "/api/themes":
            self.serve_api_themes()
        elif path == "/api/projects":
            self.serve_api_projects()
        elif path.startswith("/static/"):
            self.serve_static_file(path[8:])  # Remove /static/ prefix
        elif path.startswith("/preview/"):
            self.serve_preview_file(path[9:])  # Remove /preview/ prefix
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        if path == "/api/upload":
            self.handle_upload(post_data)
        elif path == "/api/convert":
            self.handle_convert(post_data)
        elif path == "/api/metadata":
            self.handle_metadata_update(post_data)
        elif path == "/api/anthology/create":
            self.handle_anthology_create(post_data)
        elif path == "/api/anthology/add-story":
            self.handle_anthology_add_story(post_data)
        else:
            self.send_error(404, "API endpoint not found")

    def serve_main_page(self):
        """Serve the main web interface."""
        html_content = self.web_builder.get_main_page_html()

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html_content.encode('utf-8')))
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def serve_api_status(self):
        """Serve API status information."""
        status = {
            "version": "1.2.4",
            "status": "ready",
            "active_projects": len(self.web_builder.projects),
            "available_themes": list(self.web_builder.get_available_themes().keys())
        }

        self.send_json_response(status)

    def serve_api_themes(self):
        """Serve available themes information."""
        themes = self.web_builder.get_available_themes()
        self.send_json_response(themes)

    def serve_api_projects(self):
        """Serve projects list."""
        projects = [
            {
                "id": project_id,
                "name": project.get("name", "Untitled"),
                "type": project.get("type", "single"),
                "created": project.get("created"),
                "status": project.get("status", "draft")
            }
            for project_id, project in self.web_builder.projects.items()
        ]

        self.send_json_response(projects)

    def serve_static_file(self, file_path: str):
        """Serve static files (CSS, JS, images)."""
        static_dir = Path(__file__).parent / "static"
        full_path = static_dir / file_path

        if not full_path.exists() or not full_path.is_file():
            self.send_error(404, "Static file not found")
            return

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'

        try:
            with open(full_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            logger.error(f"Error serving static file {file_path}: {e}")
            self.send_error(500, "Internal server error")

    def serve_preview_file(self, file_path: str):
        """Serve preview files."""
        # Implementation for serving preview files
        self.send_error(501, "Preview not yet implemented")

    def handle_upload(self, post_data: bytes):
        """Handle file upload."""
        try:
            # Parse multipart form data (simplified)
            # In a production implementation, use a proper multipart parser
            boundary = self.headers.get('Content-Type', '').split('boundary=')[-1]

            if not boundary:
                self.send_error(400, "Invalid multipart data")
                return

            # For now, create a dummy project
            project_id = str(uuid.uuid4())
            project = {
                "id": project_id,
                "name": "Uploaded Document",
                "type": "single",
                "created": datetime.now().isoformat(),
                "status": "uploaded",
                "files": []
            }

            self.web_builder.projects[project_id] = project

            self.send_json_response({"project_id": project_id, "status": "uploaded"})

        except Exception as e:
            logger.error(f"Upload error: {e}")
            self.send_error(500, f"Upload failed: {e}")

    def handle_convert(self, post_data: bytes):
        """Handle conversion request."""
        try:
            data = json.loads(post_data.decode('utf-8'))
            project_id = data.get('project_id')
            options = data.get('options', {})

            if project_id not in self.web_builder.projects:
                self.send_error(404, "Project not found")
                return

            # Start conversion in background
            self.web_builder.start_conversion(project_id, options)

            self.send_json_response({"status": "conversion_started"})

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            self.send_error(500, f"Conversion failed: {e}")

    def handle_metadata_update(self, post_data: bytes):
        """Handle metadata update."""
        try:
            data = json.loads(post_data.decode('utf-8'))
            project_id = data.get('project_id')
            metadata = data.get('metadata', {})

            if project_id not in self.web_builder.projects:
                self.send_error(404, "Project not found")
                return

            # Update project metadata
            self.web_builder.projects[project_id]['metadata'] = metadata

            self.send_json_response({"status": "metadata_updated"})

        except Exception as e:
            logger.error(f"Metadata update error: {e}")
            self.send_error(500, f"Metadata update failed: {e}")

    def handle_anthology_create(self, post_data: bytes):
        """Handle anthology creation."""
        try:
            data = json.loads(post_data.decode('utf-8'))

            project_id = str(uuid.uuid4())
            project = {
                "id": project_id,
                "name": data.get('title', 'New Anthology'),
                "type": "anthology",
                "created": datetime.now().isoformat(),
                "status": "draft",
                "config": data.get('config', {}),
                "stories": []
            }

            self.web_builder.projects[project_id] = project

            self.send_json_response({"project_id": project_id, "status": "created"})

        except Exception as e:
            logger.error(f"Anthology creation error: {e}")
            self.send_error(500, f"Anthology creation failed: {e}")

    def handle_anthology_add_story(self, post_data: bytes):
        """Handle adding story to anthology."""
        try:
            data = json.loads(post_data.decode('utf-8'))
            project_id = data.get('project_id')

            if project_id not in self.web_builder.projects:
                self.send_error(404, "Project not found")
                return

            project = self.web_builder.projects[project_id]
            if project.get('type') != 'anthology':
                self.send_error(400, "Project is not an anthology")
                return

            # Add story to anthology
            story_info = data.get('story', {})
            project['stories'].append(story_info)

            self.send_json_response({"status": "story_added"})

        except Exception as e:
            logger.error(f"Add story error: {e}")
            self.send_error(500, f"Add story failed: {e}")

    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response."""
        json_data = json.dumps(data, indent=2).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(json_data))
        self.end_headers()
        self.wfile.write(json_data)


class WebBuilderServer:
    """Web builder server with project management."""

    def __init__(self, host="localhost", port=0):
        self.host = host
        self.port = port
        self.server = None
        self.web_builder = None
        self.running = False

    def start(self, open_browser=True):
        """Start the web server."""
        self.web_builder = WebBuilder()

        # Create server
        handler = lambda *args: WebBuilderHandler(*args)
        self.server = HTTPServer((self.host, self.port), handler)
        self.server.web_builder = self.web_builder

        # Get actual port if port was 0 (auto-assign)
        if self.port == 0:
            self.port = self.server.server_address[1]

        self.running = True

        logger.info(f"Starting web builder server on http://{self.host}:{self.port}")

        if open_browser:
            # Open browser in a separate thread to avoid blocking
            def open_browser_delayed():
                import time
                time.sleep(1)  # Give server time to start
                webbrowser.open(f"http://{self.host}:{self.port}")

            threading.Thread(target=open_browser_delayed, daemon=True).start()

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the web server."""
        if self.server:
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            logger.info("Web builder server stopped")


class WebBuilder:
    """Main web builder application logic."""

    def __init__(self):
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.temp_dir = Path(tempfile.mkdtemp(prefix="docx2shelf_web_"))

    def get_main_page_html(self) -> str:
        """Generate the main page HTML."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docx2Shelf Web Builder</title>
    <link rel="stylesheet" href="/static/app.css">
</head>
<body>
    <div id="app">
        <header class="header">
            <h1>📚 Docx2Shelf Web Builder</h1>
            <nav>
                <button id="new-project-btn" class="btn btn-primary">New Project</button>
                <button id="new-anthology-btn" class="btn btn-secondary">New Anthology</button>
            </nav>
        </header>

        <main class="main">
            <div class="sidebar">
                <h2>Projects</h2>
                <div id="projects-list">
                    <div class="empty-state">
                        <p>No projects yet</p>
                        <p>Upload a DOCX file to get started</p>
                    </div>
                </div>
            </div>

            <div class="content">
                <div id="upload-area" class="upload-area">
                    <div class="upload-content">
                        <div class="upload-icon">📄</div>
                        <h3>Drop DOCX files here</h3>
                        <p>or click to browse</p>
                        <input type="file" id="file-input" accept=".docx" multiple style="display: none;">
                        <button id="browse-btn" class="btn btn-outline">Browse Files</button>
                    </div>
                </div>

                <div id="project-editor" class="project-editor" style="display: none;">
                    <div class="editor-header">
                        <h2 id="project-title">Project Title</h2>
                        <div class="editor-actions">
                            <button id="preview-btn" class="btn btn-outline">Preview</button>
                            <button id="convert-btn" class="btn btn-primary">Convert to EPUB</button>
                        </div>
                    </div>

                    <div class="editor-tabs">
                        <button class="tab-btn active" data-tab="metadata">Metadata</button>
                        <button class="tab-btn" data-tab="settings">Settings</button>
                        <button class="tab-btn" data-tab="preview">Preview</button>
                    </div>

                    <div class="tab-content">
                        <div id="tab-metadata" class="tab-panel active">
                            <form id="metadata-form" class="form">
                                <div class="form-group">
                                    <label for="title">Title</label>
                                    <input type="text" id="title" name="title" required>
                                </div>
                                <div class="form-group">
                                    <label for="author">Author</label>
                                    <input type="text" id="author" name="author" required>
                                </div>
                                <div class="form-group">
                                    <label for="language">Language</label>
                                    <select id="language" name="language">
                                        <option value="en">English</option>
                                        <option value="es">Spanish</option>
                                        <option value="fr">French</option>
                                        <option value="de">German</option>
                                        <option value="it">Italian</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="description">Description</label>
                                    <textarea id="description" name="description" rows="4"></textarea>
                                </div>
                            </form>
                        </div>

                        <div id="tab-settings" class="tab-panel">
                            <form id="settings-form" class="form">
                                <div class="form-group">
                                    <label for="theme">CSS Theme</label>
                                    <select id="theme" name="theme">
                                        <option value="serif">Serif</option>
                                        <option value="sans">Sans-serif</option>
                                        <option value="printlike">Print-like</option>
                                        <option value="dyslexic">Dyslexic-friendly</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>
                                        <input type="checkbox" id="validate" name="validate" checked>
                                        Validate EPUB
                                    </label>
                                </div>
                                <div class="form-group">
                                    <label>
                                        <input type="checkbox" id="accessibility" name="accessibility" checked>
                                        Include accessibility features
                                    </label>
                                </div>
                                <div class="form-group">
                                    <label for="image-width">Max image width (px)</label>
                                    <input type="number" id="image-width" name="image-width" value="1200" min="400" max="4000">
                                </div>
                            </form>
                        </div>

                        <div id="tab-preview" class="tab-panel">
                            <div class="preview-area">
                                <div class="preview-placeholder">
                                    <p>Preview will appear here after conversion</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <div id="progress-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Converting to EPUB</h3>
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill"></div>
                </div>
                <p id="progress-text">Starting conversion...</p>
                <button id="cancel-btn" class="btn btn-outline">Cancel</button>
            </div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>"""

    def get_available_themes(self) -> Dict[str, Dict[str, str]]:
        """Get available CSS themes."""
        return {
            "serif": {
                "name": "Classic Serif",
                "description": "Traditional serif fonts for classic literature",
                "preview": "Traditional serif typography with elegant spacing"
            },
            "sans": {
                "name": "Modern Sans",
                "description": "Clean sans-serif fonts for contemporary content",
                "preview": "Clean, modern sans-serif design"
            },
            "printlike": {
                "name": "Print-like",
                "description": "Traditional book layout mimicking printed pages",
                "preview": "Traditional print book appearance"
            },
            "dyslexic": {
                "name": "Dyslexic-friendly",
                "description": "Optimized for readers with dyslexia",
                "preview": "Enhanced readability with dyslexic-friendly fonts"
            }
        }

    def start_conversion(self, project_id: str, options: Dict[str, Any]):
        """Start EPUB conversion for a project."""
        def convert_worker():
            try:
                project = self.projects[project_id]
                project['status'] = 'converting'

                # Simulate conversion process
                import time
                time.sleep(2)  # Simulate work

                project['status'] = 'completed'
                project['output_path'] = str(self.temp_dir / f"{project_id}.epub")

                logger.info(f"Conversion completed for project {project_id}")

            except Exception as e:
                logger.error(f"Conversion failed for project {project_id}: {e}")
                project['status'] = 'error'
                project['error'] = str(e)

        # Start conversion in background thread
        threading.Thread(target=convert_worker, daemon=True).start()


def create_static_files():
    """Create static CSS and JS files for the web interface."""
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    # Create CSS file
    css_content = """
/* Docx2Shelf Web Builder Styles */
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --border-color: #dee2e6;
    --border-radius: 6px;
    --spacing: 1rem;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--dark-color);
    background: var(--light-color);
}

.header {
    background: white;
    border-bottom: 1px solid var(--border-color);
    padding: var(--spacing);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header h1 {
    margin: 0;
    color: var(--primary-color);
}

.main {
    display: flex;
    height: calc(100vh - 80px);
}

.sidebar {
    width: 300px;
    background: white;
    border-right: 1px solid var(--border-color);
    padding: var(--spacing);
    overflow-y: auto;
}

.content {
    flex: 1;
    padding: var(--spacing);
    overflow-y: auto;
}

.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    margin: 0.25rem;
    border: 1px solid transparent;
    border-radius: var(--border-radius);
    text-decoration: none;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background: #0056b3;
    border-color: #0056b3;
}

.btn-secondary {
    background: var(--secondary-color);
    color: white;
    border-color: var(--secondary-color);
}

.btn-outline {
    background: transparent;
    color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-outline:hover {
    background: var(--primary-color);
    color: white;
}

.upload-area {
    border: 2px dashed var(--border-color);
    border-radius: var(--border-radius);
    padding: 3rem;
    text-align: center;
    background: white;
    transition: all 0.2s;
}

.upload-area:hover {
    border-color: var(--primary-color);
    background: #f0f8ff;
}

.upload-area.dragover {
    border-color: var(--primary-color);
    background: #e3f2fd;
}

.upload-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.project-editor {
    background: white;
    border-radius: var(--border-radius);
    padding: var(--spacing);
}

.editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing);
    padding-bottom: var(--spacing);
    border-bottom: 1px solid var(--border-color);
}

.editor-tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: var(--spacing);
}

.tab-btn {
    background: none;
    border: none;
    padding: 0.75rem 1.5rem;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}

.tab-btn:hover {
    background: var(--light-color);
}

.tab-btn.active {
    border-bottom-color: var(--primary-color);
    color: var(--primary-color);
}

.tab-panel {
    display: none;
}

.tab-panel.active {
    display: block;
}

.form {
    max-width: 600px;
}

.form-group {
    margin-bottom: var(--spacing);
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 2rem;
    border-radius: var(--border-radius);
    max-width: 500px;
    width: 90%;
}

.progress-bar {
    width: 100%;
    height: 20px;
    background: var(--light-color);
    border-radius: 10px;
    overflow: hidden;
    margin: var(--spacing) 0;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    width: 0%;
    transition: width 0.3s;
}

.empty-state {
    text-align: center;
    color: var(--secondary-color);
    padding: 2rem;
}

@media (max-width: 768px) {
    .main {
        flex-direction: column;
    }

    .sidebar {
        width: 100%;
        height: 200px;
    }

    .header {
        flex-direction: column;
        gap: 1rem;
    }
}
"""

    (static_dir / "app.css").write_text(css_content, encoding='utf-8')

    # Create JavaScript file
    js_content = """
// Docx2Shelf Web Builder JavaScript
class WebBuilder {
    constructor() {
        this.currentProject = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProjects();
    }

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-btn');
        const uploadArea = document.getElementById('upload-area');

        browseBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Convert button
        document.getElementById('convert-btn').addEventListener('click', () => this.startConversion());

        // New project buttons
        document.getElementById('new-project-btn').addEventListener('click', () => this.newProject());
        document.getElementById('new-anthology-btn').addEventListener('click', () => this.newAnthology());
    }

    async handleFiles(files) {
        for (const file of files) {
            if (file.name.endsWith('.docx')) {
                await this.uploadFile(file);
            }
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.loadProject(result.project_id);
                this.loadProjects();
            } else {
                alert('Upload failed: ' + result.error);
            }
        } catch (error) {
            alert('Upload error: ' + error.message);
        }
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const projects = await response.json();

            const projectsList = document.getElementById('projects-list');

            if (projects.length === 0) {
                projectsList.innerHTML = `
                    <div class="empty-state">
                        <p>No projects yet</p>
                        <p>Upload a DOCX file to get started</p>
                    </div>
                `;
            } else {
                projectsList.innerHTML = projects.map(project => `
                    <div class="project-item" data-project-id="${project.id}">
                        <h4>${project.name}</h4>
                        <p>${project.type} - ${project.status}</p>
                        <small>${new Date(project.created).toLocaleDateString()}</small>
                    </div>
                `).join('');

                // Add click handlers
                projectsList.querySelectorAll('.project-item').forEach(item => {
                    item.addEventListener('click', () => {
                        this.loadProject(item.dataset.projectId);
                    });
                });
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    loadProject(projectId) {
        this.currentProject = projectId;

        // Show project editor
        document.getElementById('upload-area').style.display = 'none';
        document.getElementById('project-editor').style.display = 'block';

        // Load project data
        // This would fetch actual project data in a real implementation
        document.getElementById('project-title').textContent = `Project ${projectId.slice(0, 8)}`;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`tab-${tabName}`).classList.add('active');
    }

    async startConversion() {
        if (!this.currentProject) return;

        const options = {
            theme: document.getElementById('theme').value,
            validate: document.getElementById('validate').checked,
            accessibility: document.getElementById('accessibility').checked,
            imageWidth: parseInt(document.getElementById('image-width').value)
        };

        const metadata = {
            title: document.getElementById('title').value,
            author: document.getElementById('author').value,
            language: document.getElementById('language').value,
            description: document.getElementById('description').value
        };

        try {
            // Update metadata first
            await fetch('/api/metadata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: this.currentProject,
                    metadata: metadata
                })
            });

            // Start conversion
            const response = await fetch('/api/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: this.currentProject,
                    options: options
                })
            });

            if (response.ok) {
                this.showProgressModal();
            } else {
                alert('Conversion failed to start');
            }
        } catch (error) {
            alert('Conversion error: ' + error.message);
        }
    }

    showProgressModal() {
        document.getElementById('progress-modal').style.display = 'flex';

        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                setTimeout(() => {
                    document.getElementById('progress-modal').style.display = 'none';
                    alert('Conversion completed!');
                }, 1000);
            }

            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-text').textContent =
                progress < 100 ? `Converting... ${Math.round(progress)}%` : 'Conversion complete!';
        }, 500);
    }

    newProject() {
        document.getElementById('file-input').click();
    }

    newAnthology() {
        alert('Anthology creation coming soon!');
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new WebBuilder();
});
"""

    (static_dir / "app.js").write_text(js_content, encoding='utf-8')

    logger.info(f"Created static files in {static_dir}")


def start_web_builder(host="localhost", port=8080, open_browser=True):
    """
    Start the web builder server.

    Args:
        host: Server host (default: localhost)
        port: Server port (default: 8080, 0 for auto-assign)
        open_browser: Whether to open browser automatically

    Returns:
        WebBuilderServer instance
    """
    # Create static files if they don't exist
    create_static_files()

    server = WebBuilderServer(host, port)

    # Start server in background thread
    server_thread = threading.Thread(target=server.start, args=(open_browser,), daemon=True)
    server_thread.start()

    return server


def main():
    """Main entry point for web builder."""
    import argparse

    parser = argparse.ArgumentParser(description="Docx2Shelf Web Builder")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port (0 for auto-assign)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")

    args = parser.parse_args()

    print(f"Starting Docx2Shelf Web Builder on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        server = WebBuilderServer(args.host, args.port)
        server.start(open_browser=not args.no_browser)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()