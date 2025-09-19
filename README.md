# Docx2Shelf

Offline Python CLI for converting manuscripts into valid EPUB 3 ebooks.

Docx2Shelf is designed to be a comprehensive and easy-to-use tool for authors and publishers. It handles various aspects of ebook creation, including cover embedding, metadata management, content splitting, and CSS theming. It prefers Pandoc for high-fidelity conversions but includes a fallback for DOCX when Pandoc isn't available.

## Features

### Core Conversion
-   **Multiple Input Formats**: Convert from DOCX, Markdown, TXT, and HTML files
-   **Professional EPUB Output**: Creates valid EPUB 3 files with proper metadata and structure
-   **Smart Content Organization**: Automatically splits content into chapters based on headings or page breaks
-   **Beautiful Typography**: Choose from built-in themes (serif, sans, printlike) or add custom CSS
-   **Cross-References & Indexing**: Preserves Word cross-references and generates searchable indexes
-   **Math Support**: MathML, SVG, and PNG fallbacks for equations with accessibility features

### Publishing & Metadata
-   **Comprehensive Metadata**: Full support for title, author, ISBN, series info, and publishing details
-   **Publishing-Ready**: Built-in validation and compatibility checks for major ebook stores
-   **ONIX 3.0 Export**: Generate industry-standard metadata for retailers
-   **Store Profiles**: KDP, Apple Books, Kobo, Google Play, and B&N compatibility validation
-   **Accessibility Features**: WCAG compliance, screen reader support, and dyslexic-friendly themes

### Advanced Workflows
-   **Anthology & Series Builder**: Merge multiple manuscripts into collections or series
-   **GUI Applications**: Cross-platform desktop app and web-based interface
-   **Performance Optimizations**: Streaming processing, build cache, and parallel image processing
-   **Plugin Marketplace**: Discover, install, and manage community plugins
-   **Plugin Support**: Extend functionality with custom plugins for specialized workflows
-   **No Internet Required**: Works completely offline - your manuscripts never leave your computer

## Installation

Docx2Shelf requires **Python 3.11 or newer**.

### Quick Install Options

Choose the method that works best for your system:

#### PyPI (Recommended for Python users)
```bash
pipx install docx2shelf
# or with pip:
pip install docx2shelf
```

#### Package Managers

**Homebrew (macOS/Linux):**
```bash
brew install docx2shelf
```

**Windows Package Manager:**
```bash
winget install LightWraith8268.Docx2Shelf
```

**Scoop (Windows):**
```bash
scoop install docx2shelf
```

#### Docker (Advanced Users)
```bash
docker run -v $(pwd):/workspace ghcr.io/lightwraith8268/docx2shelf build --input manuscript.docx --title "My Book" --author "Author"
```

#### Quick Install Scripts

**Windows**: The `install.bat` script automatically installs Docx2Shelf and adds it to your system PATH for global usage:
```cmd
curl -L -o install.bat https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.bat && install.bat
```
```powershell
Invoke-WebRequest -Uri "https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.bat" -OutFile "install.bat"; .\install.bat
```

Features:
- Automatically detects and installs Python dependencies
- Installs pipx if not present
- Adds docx2shelf to system PATH permanently
- Verifies installation and provides troubleshooting
- Works with both `python` and `py` commands

**macOS/Linux**: The `install.sh` script provides flexible installation options:
```bash
curl -sSL https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.sh | bash
```

Options:
```bash
# Install with specific method and extras
./install.sh --method pipx --extras docx --with-tools pandoc

# Available methods: pipx (default), pip-user, pip-system
# Available extras: none, docx (default), pandoc, all
# Available tools: none (default), pandoc, epubcheck, all
```

### Updating Docx2Shelf

To update your installed Docx2Shelf to the latest version, simply run:

```bash
docx2shelf update
```

## Quickstart

To convert a manuscript, navigate to its directory and run `docx2shelf`. The tool will guide you through the process interactively.

```bash
# Interactive mode (simplest - just follow the prompts)
docx2shelf

# Or specify options directly
docx2shelf build \
  --input manuscript.docx \
  --cover cover.jpg \
  --title "Book Title" \
  --author "Author Name" \
  --language en \
  --theme serif \
  --split-at h1 \
  --justify on --hyphenate on
```

-   **Dry run**: Add `--dry-run` to print the planned manifest/spine without creating the EPUB.
-   **Inspect sources**: Add `--inspect` to emit a `.src/` folder next to the EPUB for debugging.

## CLI Commands & Options

### Core Commands
```bash
# Build EPUB from manuscript
docx2shelf build --input manuscript.docx --title "Book Title" --author "Author"

# Anthology and series building
docx2shelf anthology create --name "My Collection" --output anthology.epub
docx2shelf series build --series "Fantasy Series" --auto-also-by

# GUI applications
docx2shelf gui              # Launch desktop GUI
docx2shelf web              # Start web interface

# Plugin management
docx2shelf plugins list     # List installed plugins
docx2shelf plugins install plugin-name
docx2shelf plugins marketplace search "keyword"

# Tools and validation
docx2shelf tools install pandoc
docx2shelf checklist --epub book.epub --store kdp
```

### Build Options
-   **Required**: `--input` (path to manuscript file or directory), `--title`, `--cover` (author defaults are configurable).
-   **Metadata**: `--author`, `--language`, `--isbn`, `--publisher`, `--pubdate YYYY-MM-DD`, `--uuid`, `--seriesName`, `--seriesIndex`, `--title-sort`, `--author-sort`, `--subjects`, `--keywords`.
-   **Conversion**: `--split-at h1|h2|pagebreak`, `--toc-depth N`, `--theme serif|sans|printlike`, `--css EXTRA.css`.
-   **Layout**: `--justify on|off`, `--hyphenate on|off`, `--page-numbers on|off`, `--page-list on|off`, `--embed-fonts DIR`, `--cover-scale contain|cover`, `--font-size`, `--line-height`.
-   **Output**: `--output out.epub`, `--output-pattern "{series}-{index2}-{title}"`, `--inspect`, `--dry-run`.
-   **Non-interactive**: `--no-prompt` (use metadata.txt + flags only), `--auto-install-tools`, `--no-install-tools`, `--prompt-all`, `--quiet`, `--verbose`.

## Advanced Features

### Tools Manager
Install optional tools locally (no admin privileges required):

```bash
# Install Pandoc for better DOCX conversion
docx2shelf tools install pandoc

# Install EPUBCheck for validation
docx2shelf tools install epubcheck
```

### Anthology & Series Building

Create professional multi-book collections and series with automatic cross-referencing:

```bash
# Create an anthology from multiple manuscripts
docx2shelf anthology create \
  --name "Science Fiction Collection" \
  --editor "Editor Name" \
  --add story1.docx --add story2.docx --add story3.docx \
  --output anthology.epub

# Build a book series with auto-generated "Also By" pages
docx2shelf series build \
  --series "Fantasy Chronicles" \
  --author "Series Author" \
  --auto-also-by \
  --add book1.epub --add book2.epub --add book3.epub
```

**Features:**
- Automatic table of contents with grouped stories
- Story sorting by title, author, or custom order
- Cross-references between books in series
- Auto-generated "Also By This Author" pages
- Series metadata and navigation
- Professional anthology formatting

### GUI Applications

#### Desktop GUI
Cross-platform desktop application with drag-and-drop support:

```bash
docx2shelf gui
```

**Features:**
- Drag-and-drop file conversion
- Visual metadata editor
- Live preview of EPUB structure
- Progress tracking and status updates
- Theme selection and customization
- Batch processing support
- Works on Windows, macOS, and Linux

#### Web Interface
Modern web-based builder for teams and remote access:

```bash
# Start local web server
docx2shelf web --port 8080

# Access at http://localhost:8080
```

**Features:**
- Modern responsive web interface
- Project management and organization
- Collaborative editing capabilities
- REST API for automation
- File upload and cloud storage integration
- Mobile-friendly design
- Real-time conversion status

### Plugin Ecosystem & Marketplace

Docx2Shelf features a comprehensive plugin system with marketplace integration:

#### Plugin Management
```bash
# Browse marketplace
docx2shelf plugins marketplace search "keyword"
docx2shelf plugins marketplace list --popular

# Install plugin bundles (recommended)
docx2shelf plugins bundles install publishing    # Store validation tools
docx2shelf plugins bundles install workflow      # Multi-book tools
docx2shelf plugins bundles install accessibility # A11y tools
docx2shelf plugins bundles install cloud         # Cloud connectors
docx2shelf plugins bundles install premium       # Everything

# Install individual plugins
docx2shelf plugins marketplace install store_profiles
docx2shelf plugins marketplace install anthology_builder

# Manage installed plugins
docx2shelf plugins list --core-only              # Show core plugins only
docx2shelf plugins list --marketplace-only       # Show marketplace plugins
docx2shelf plugins enable plugin-name
docx2shelf plugins disable plugin-name           # (Core essentials cannot be disabled)
docx2shelf plugins marketplace update plugin-name

# Create new plugins
docx2shelf plugins create-template my-plugin
```

#### Installation with Plugin Bundles

Install Docx2Shelf with plugin bundles for your use case:

```bash
# Windows - with publishing bundle
.\install.bat --with-plugins publishing

# macOS/Linux - with workflow bundle
./install.sh --with-plugins workflow

# Premium installation (all plugins)
./install.sh --with-plugins premium --with-tools all
```

#### Core Built-in Plugins

**Always included with Docx2Shelf installation:**

**Essential Processing (Cannot be disabled):**
1. **Math Handler** - Converts OMML/MathML equations to multiple formats (SVG, PNG)
2. **Cross-Reference Handler** - Preserves Word cross-references with stable anchor IDs
3. **Index Generator** - Creates searchable indexes from Word XE fields
4. **Notes Manager** - Handles footnotes/endnotes with back-references
5. **Figures & Tables Handler** - Semantic HTML conversion for accessibility

**Core Features (Can be disabled):**
6. **HTML Cleanup** - Basic HTML optimization and whitespace removal
7. **Accessibility Auditor** - WCAG compliance checking and validation
8. **Performance Monitor** - Conversion performance tracking and optimization

#### Marketplace Plugins

**Available for download via plugin marketplace:**

**Publishing Bundle:**
- **Store Profile Manager** - KDP, Apple Books, Kobo validation
- **ONIX Export Handler** - Industry-standard metadata for retailers
- **Kindle Previewer Integration** - Amazon compatibility testing

**Workflow Bundle:**
- **Anthology Builder** - Merge multiple manuscripts into collections
- **Series Builder** - Book series with automatic cross-referencing
- **Web Builder** - Browser-based conversion interface

**Accessibility Bundle:**
- **Media Overlays Handler** - SMIL audio synchronization for read-aloud
- **Dyslexic-Friendly Themes** - Enhanced readability themes

**Cloud Integration Bundle:**
- **Google Docs Connector** - Import directly from Google Docs
- **OneDrive Connector** - Import from Microsoft OneDrive

**Theme & Styling:**
- **Advanced Theme Pack** - Premium themes and styling options
- **Custom CSS Builder** - Visual theme editor and generator

#### Plugin Development

Create custom plugins with three hook types:

```python
from docx2shelf.plugins import BasePlugin, PreConvertHook, PostConvertHook, MetadataResolverHook

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_plugin", "1.0.0")

    def get_hooks(self):
        return {
            'pre_convert': [MyPreProcessor()],
            'post_convert': [MyPostProcessor()],
            'metadata_resolver': [MyMetadataEnhancer()]
        }

class MyPreProcessor(PreConvertHook):
    def process_docx(self, docx_path, context):
        # Modify DOCX before conversion
        return docx_path

class MyPostProcessor(PostConvertHook):
    def transform_html(self, html_content, context):
        # Transform HTML after conversion
        return html_content

class MyMetadataEnhancer(MetadataResolverHook):
    def resolve_metadata(self, metadata, context):
        # Enhance or modify metadata
        return metadata
```

#### Plugin Marketplace

The marketplace provides:
- **Plugin Discovery**: Search and browse community plugins
- **Version Management**: Automatic updates and dependency resolution
- **Security**: Checksum verification and trusted publishers
- **Templates**: Starter templates for common plugin types
- **Documentation**: Comprehensive plugin development guides

**Popular Plugin Categories:**
- Document hygiene and cleanup
- Advanced typography and formatting
- Metadata enhancement and validation
- Store-specific optimizations
- Accessibility improvements
- Custom output formats

### Document Connectors
Import from various sources (requires explicit opt-in):

```bash
# List available connectors
docx2shelf connectors list

# Convert local Markdown files
docx2shelf connectors fetch local_markdown document.md
```

### Publishing Compatibility
Check your EPUB against store requirements:

```bash
# Run compatibility checks for major stores
docx2shelf checklist --epub my-book.epub --store kdp
```

## Enterprise & Production Deployment (v1.2.6+)

### Enterprise API & Integration

Docx2Shelf v1.2.6 introduces enterprise-grade features for production environments and large-scale workflows:

#### REST API Server
Start the enterprise API server for programmatic access:

```bash
# Install with enterprise features
pip install docx2shelf[enterprise]

# Start API server
docx2shelf api start --port 8080 --workers 4

# Generate API key for authentication
docx2shelf api create-key --name "Production" --permissions read,write
```

**API Features:**
- **OpenAPI 3.0 specification** at `/api/docs`
- **Authentication** via API keys with permissions
- **Rate limiting** with configurable thresholds
- **Job queue management** for conversion operations
- **Webhook notifications** for real-time status updates
- **Audit logging** for enterprise compliance

#### Webhook Integration
Configure webhooks for real-time notifications:

```bash
# Add webhook endpoint
docx2shelf api webhooks add \
  --url https://your-app.com/webhooks/docx2shelf \
  --secret your-webhook-secret \
  --events job.created,job.completed,job.failed

# Test webhook delivery
docx2shelf api webhooks test --endpoint-id 123
```

**Webhook Events:**
- `job.created` - New conversion job submitted
- `job.running` - Job processing started
- `job.completed` - Conversion completed successfully
- `job.failed` - Conversion failed with error details

#### Enterprise CLI Commands
```bash
# Job management
docx2shelf api jobs list --status running
docx2shelf api jobs status --job-id abc123
docx2shelf api jobs cancel --job-id abc123

# Queue management
docx2shelf api queue status
docx2shelf api queue pause
docx2shelf api queue resume

# Monitoring and health
docx2shelf api health
docx2shelf api metrics
```

### Production Deployment

#### Kubernetes Deployment
Deploy Docx2Shelf in production Kubernetes environments:

```bash
# Install with Helm (recommended)
helm repo add docx2shelf https://charts.docx2shelf.io
helm install docx2shelf docx2shelf/docx2shelf --values production-values.yaml

# Or use Kubernetes manifests directly
kubectl apply -f k8s/
```

**Production Features:**
- **Auto-scaling** with HPA based on CPU, memory, and queue size
- **Prometheus monitoring** with comprehensive metrics
- **Health checks** for liveness, readiness, and startup probes
- **Security hardening** with non-root containers and capability restrictions
- **High availability** with pod anti-affinity and rolling updates

#### Docker Deployment
```bash
# Production container
docker run -d \
  --name docx2shelf-api \
  -p 8080:8080 \
  -e DOCX2SHELF_WORKERS=4 \
  -e DOCX2SHELF_DB_PATH=/data/docx2shelf.db \
  -v /data:/data \
  ghcr.io/lightwraith8268/docx2shelf:v1.2.6

# With monitoring
docker-compose up -f docker-compose.prod.yml
```

### Advanced Plugin Management

#### Plugin Sandboxing & Security
v1.2.6 introduces advanced plugin security features:

```bash
# Enable plugin sandboxing (production environments)
docx2shelf plugins config --sandbox-enabled true --resource-limits strict

# Monitor plugin resource usage
docx2shelf plugins monitor --plugin-id my-plugin --duration 300s

# Performance profiling
docx2shelf plugins profile --top-consumers 5
```

**Security Features:**
- **Sandbox isolation** with import restrictions and resource limits
- **Hot-reload capability** for zero-downtime plugin updates
- **Resource monitoring** for memory, CPU, and execution time
- **Cross-platform compatibility** with graceful feature degradation

#### Plugin Performance Management
```bash
# Resource limits configuration
docx2shelf plugins config set resource-limits \
  --max-memory 256MB \
  --max-cpu 50% \
  --max-execution-time 30s

# Hot-reload settings
docx2shelf plugins config set hot-reload \
  --enabled true \
  --check-interval 5s

# Performance metrics
docx2shelf plugins metrics --format prometheus
```

### Monitoring & Observability

#### System Monitoring
Built-in monitoring with Prometheus integration:

```bash
# Start with monitoring enabled
docx2shelf api start --monitoring-enabled --metrics-port 9090

# Health check endpoints
curl http://localhost:8080/health          # Overall health
curl http://localhost:8080/health/live     # Liveness probe
curl http://localhost:8080/health/ready    # Readiness probe

# Prometheus metrics
curl http://localhost:8080/metrics
```

**Monitoring Features:**
- **System metrics**: CPU, memory, disk usage
- **Conversion metrics**: Job counts, durations, success rates
- **Plugin metrics**: Resource usage, execution times, error rates
- **API metrics**: Request rates, response times, error counts

#### Production Configuration
```yaml
# production-config.yaml
server:
  workers: 8
  max_request_size: 100MB
  request_timeout: 300s

conversion:
  max_concurrent_jobs: 20
  temp_cleanup_interval: 60s

monitoring:
  enabled: true
  prometheus_metrics: true
  health_checks_enabled: true

plugins:
  sandbox_enabled: true
  hot_reload_enabled: true
  resource_limits:
    max_memory_mb: 512
    max_cpu_percent: 75

security:
  rate_limiting:
    enabled: true
    requests_per_minute: 120
    burst_size: 20
```

## What Gets Produced

Inside the `.epub` (ZIP) you’ll find:

-   `EPUB/content.opf` — metadata, manifest, spine
-   `EPUB/nav.xhtml` + `EPUB/toc.ncx` — modern + legacy Table of Contents
-   `EPUB/text/landmarks.xhtml` — EPUB 3 landmarks (cover, title page, ToC, start)
-   `EPUB/style/base.css` — theme CSS (+ merged user CSS)
-   `EPUB/text/` — title, copyright, optional dedication/acknowledgements, and `chap_###.xhtml` files
-   `EPUB/images/` — cover + extracted images (if any)
-   `EPUB/fonts/` — embedded fonts when provided

## License

MIT

## Changelog

For a detailed list of changes, please refer to the [CHANGELOG.md](CHANGELOG.md) file.