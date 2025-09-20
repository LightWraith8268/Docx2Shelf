# Changelog

## [1.3.0] - 2025-01-19
### Performance & Optimization - Epic 24

#### Major Performance Enhancements
- **Parallel Processing**: Advanced conversion speed optimization with parallel image processing
- **Memory Optimization**: Streaming DOCX reader for large document processing with reduced memory footprint
- **Build Cache**: Intelligent dependency tracking and incremental updates for faster rebuilds
- **Performance Monitoring**: Comprehensive performance analytics with phase timing and memory tracking

#### Advanced Conversion System
- **Streaming Architecture**: Process large DOCX files in chunks to minimize memory usage
- **Smart Caching**: File modification-based cache invalidation with SQLite storage
- **Image Pipeline**: Parallel image extraction and processing with compression optimization
- **Legacy Compatibility**: Maintained backward compatibility with existing conversion functions

#### Developer Experience
- **Performance Profiling**: Built-in performance monitoring with detailed timing breakdowns
- **Cache Analytics**: Detailed cache hit/miss tracking and cleanup automation
- **Memory Management**: Automatic garbage collection triggers for large document processing
- **Build Optimization**: Reduced assembly time through performance-aware EPUB generation

#### Technical Improvements
- **Context Managers**: Phase timing with automatic cleanup and error handling
- **Database Integration**: SQLite-based caching with automatic migration and cleanup
- **Error Recovery**: Graceful fallback from optimized to standard conversion methods
- **Resource Management**: Proper cleanup of temporary files and memory allocations

## [1.2.9] - 2025-01-19
### Community Features Cleanup & Marketplace Focus

#### Major Changes
- **Removed community features**: Eliminated all community platform functionality including forums, user profiles, and achievement systems
- **Streamlined codebase**: Focused exclusively on plugin marketplace and ecosystem integration features
- **Simplified architecture**: Reduced complexity by removing community-related modules and dependencies

#### Plugin Marketplace (Retained)
- **Plugin discovery**: Search, filter, and browse plugins with ratings and reviews
- **Installation management**: Secure plugin installation with dependency resolution
- **Quality validation**: Automated security scanning and code quality checks
- **Marketplace API**: RESTful interface for plugin distribution and management

#### Ecosystem Integration (Retained)
- **Writing tool integration**: Import from Scrivener, Notion, and Google Docs
- **Publishing platform connectors**: Automated sync with KDP, Apple Books, and Kobo
- **Template gallery**: Pre-made themes and configuration templates

#### Technical Improvements
- **Cleaner test suite**: Removed community-related tests, focused on marketplace and ecosystem
- **Simplified imports**: Eliminated unused community module dependencies
- **Performance optimization**: Reduced memory footprint by removing community features
- **Code cleanup**: Removed all community references from marketplace and ecosystem modules

## [1.2.8] - 2025-01-19
### Community & Ecosystem

#### Plugin Marketplace & Distribution
- **Comprehensive marketplace system**: Plugin discovery with community ratings, reviews, and installation management
- **Plugin certification program**: Quality standards with automated security validation and code analysis
- **Dependency management**: Automatic resolution and compatibility checking with version conflict detection
- **Installation automation**: Secure download, validation, and installation with automatic dependency resolution
- **Plugin statistics**: Download counts, ratings, reviews, and usage analytics with trending algorithms

#### Community Platform & Collaboration
- **Community forums**: Discussion platform with categories, threading, and moderation capabilities
- **Knowledge base**: Community-driven documentation with article creation, review, and maintenance
- **User profiles**: Comprehensive profiles with reputation scoring, activity tracking, and contribution history
- **Achievement system**: Badges and recognition for contributions with gamification elements
- **Contributor recognition**: Points system with leaderboards and special recognition for active community members

#### Enhanced Ecosystem Integration
- **Writing tool integration**: Import capabilities for Scrivener projects, Notion pages, and Google Docs
- **Publishing platform connectors**: Automated metadata synchronization for KDP, Apple Books, and Kobo
- **Template gallery**: Community-contributed themes and configuration templates with download management
- **Document import pipeline**: Seamless import from external writing tools with format conversion
- **Publishing workflow**: Streamlined publishing with platform-specific validation and metadata mapping

#### Technical Infrastructure
- **Marketplace system**: PluginMarketplace, PluginCertificationChecker, and DependencyResolver for plugin management
- **Community platform**: CommunityPlatform, CommunityForums, KnowledgeBase, and achievement tracking systems
- **Ecosystem integration**: EcosystemIntegrationManager with writing tool connectors and publishing platform integration
- **Security framework**: Plugin validation, sandboxing, and security scanning with automated threat detection
- **API integration**: RESTful API integration with external services and marketplace backend

#### Testing & Quality Assurance
- **Comprehensive test suite**: 20+ test classes covering marketplace, community, and ecosystem integration features
- **Integration testing**: End-to-end validation of plugin installation, community interaction, and ecosystem workflows
- **Security testing**: Plugin validation, authentication testing, and integration security verification
- **Performance testing**: Marketplace search, community platform scalability, and integration response time validation
- **User experience testing**: Workflow validation for plugin discovery, community participation, and tool integration

## [1.2.7] - 2025-01-19
### Documentation & Developer Experience

#### Comprehensive Documentation Platform
- **MkDocs integration**: Complete documentation site with Material theme, comprehensive navigation, and responsive design
- **Interactive tutorials**: Built-in step-by-step tutorials for getting started, plugin development, and enterprise deployment
- **Troubleshooting wizard**: Intelligent problem diagnosis with guided solutions and common issue resolution
- **Documentation management**: Automated doc building, serving, and content organization with markdown extensions
- **Tutorial validation**: Interactive tutorial system with code execution, validation, and progress tracking

#### Developer Experience & Tooling
- **Language Server Protocol (LSP)**: IDE integration with symbol extraction, diagnostics, and intelligent code completion
- **Hot-reload development**: Real-time file watching with automatic reloading for efficient development workflows
- **Code generation**: Template-based generators for plugins, themes, and configurations with AST analysis
- **Development workflow**: Integrated debugging tools with file monitoring and automated restart capabilities
- **IDE support**: Enhanced development experience with syntax highlighting and intelligent code assistance

#### Performance Optimization & Analytics
- **Advanced profiling**: Comprehensive performance analysis with function statistics, execution timings, and memory tracking
- **Conversion analytics**: Historical performance tracking with trend analysis and benchmarking capabilities
- **Memory optimization**: Document-size-based optimization recommendations with streaming processing support
- **Regression detection**: Automated performance regression analysis with baseline comparisons and alerting
- **Optimization suggestions**: AI-powered recommendations for improving conversion speed and memory usage

#### Technical Infrastructure
- **Documentation system**: DocumentationManager with tutorial execution, troubleshooting wizard, and content validation
- **Developer tools**: LSPServer, HotReloadHandler, CodeGenerator, and DevelopmentWorkflow for enhanced productivity
- **Performance framework**: PerformanceProfiler, ConversionAnalytics, MemoryOptimizer with comprehensive monitoring
- **Analytics persistence**: SQLite-based analytics storage with trend analysis and historical comparison
- **Template generation**: AST-based code generation with intelligent boilerplate creation

#### Testing & Quality Assurance
- **Comprehensive test suite**: 15+ test classes covering documentation, developer tools, and performance features
- **Integration testing**: End-to-end validation of cross-module functionality and workflow compatibility
- **Developer workflow testing**: Hot-reload, LSP, and code generation validation with mock frameworks
- **Performance testing**: Analytics recording, benchmark execution, and optimization recommendation validation
- **Documentation testing**: Tutorial execution, troubleshooting wizard, and content generation verification

## [1.2.6] - 2025-01-19
### Operational Excellence & Enterprise Deployment

#### Production Deployment & Monitoring
- **Kubernetes orchestration**: Complete production-ready manifests including deployment, service, configmap, HPA, and ServiceMonitor configurations
- **Helm chart**: Comprehensive Helm chart with configurable values, dependency management, and production defaults
- **Observability framework**: Integrated Prometheus metrics collection, health checks, and system resource monitoring
- **Auto-scaling**: Horizontal Pod Autoscaler with CPU, memory, and custom metrics scaling policies
- **Container security**: Security contexts, read-only root filesystem, non-root user execution, and capability dropping

#### Advanced Plugin System
- **Plugin sandboxing**: Security isolation with import restrictions, resource limits, and execution context isolation
- **Hot-reload architecture**: Zero-downtime plugin updates with automatic file monitoring and module reloading
- **Resource monitoring**: Real-time tracking of plugin memory usage, CPU consumption, and execution time
- **Performance profiling**: Comprehensive metrics collection with top resource consumer analysis and execution statistics
- **Cross-platform compatibility**: Windows and Unix resource handling with graceful platform-specific feature degradation

#### Enterprise Integration & APIs
- **REST API**: Complete OpenAPI 3.0 specification with authentication, rate limiting, and comprehensive endpoints
- **Webhook integration**: Event-driven notifications with HMAC signature verification, retry logic, and event filtering
- **Database persistence**: SQLite backend with conversion job tracking, audit trails, and API key management
- **Rate limiting**: Token bucket algorithm with per-client tracking and configurable burst sizes
- **Enterprise authentication**: API key-based authentication with permissions and usage tracking

#### Technical Infrastructure
- **Monitoring stack**: MetricsCollector, HealthChecker, SystemMonitor, and ConversionMonitor with Prometheus export
- **Plugin management**: AdvancedPluginManager with sandbox execution, hot-reload, and performance profiling
- **Enterprise API manager**: Job queue management, webhook notifications, and audit logging
- **Container deployment**: Production-ready Docker configuration with multi-stage builds and security hardening

#### Testing & Quality Assurance
- **Comprehensive test suite**: 25 test cases covering monitoring, plugin system, enterprise features, and Kubernetes integration
- **Integration testing**: End-to-end workflow validation with all v1.2.6 components working together
- **Cross-platform testing**: Windows and Unix compatibility validation with platform-specific feature handling
- **Performance testing**: Plugin resource usage validation and monitoring system verification

## [1.1.1]
### Added
- Comprehensive test suite with golden EPUB fixtures for regression detection
- Property-based testing using Hypothesis for edge case verification
- Reader smoke tests with headless browser rendering validation
- Multi-layered testing framework: unit, integration, property-based, golden fixtures, and smoke tests
- Advanced CI/CD testing pipeline with coverage reporting and multi-platform validation
- Test runner script with multiple execution modes (quick, full, smoke, property, golden, ci)
- Comprehensive testing documentation with guidelines and examples

### Testing Infrastructure
- Golden EPUB fixtures covering simple documents, footnotes, tables, poetry, images, and RTL text
- Property-based tests for content preservation, filename generation, and split logic correctness
- Headless browser smoke tests for typography, accessibility, and rendering verification
- pytest configuration with test markers and coverage requirements (70% minimum)
- Hypothesis integration with configurable test profiles for development and CI
- Selenium-based reader testing with Chrome/Firefox support

### CI/CD Enhancements
- Enhanced GitHub Actions workflow with comprehensive test matrix
- Multi-platform testing across Ubuntu, macOS, Windows with Python 3.11 and 3.12
- Separate test jobs for external tools integration and plugin system validation
- Coverage reporting with Codecov integration
- Code quality checks with ruff linting and mypy type checking

### Developer Experience
- Test runner script supporting different execution modes and coverage reporting
- Detailed testing documentation with guidelines, examples, and troubleshooting
- Test categorization with markers for efficient test execution
- Development and CI test profiles for optimal performance

## [1.1.0]
### Added
- Comprehensive plugin system with development documentation and example templates
- Plugin discovery mechanism scanning multiple standard locations
- Enhanced plugin CLI commands: `list`, `load`, `enable`, `disable`, `info`, `discover`, `create`
- Plugin template creation with `docx2shelf plugins create` supporting basic, HTML cleaner, and metadata enhancer templates
- Tools manager health check with `docx2shelf tools doctor` command providing PATH diagnostics
- Version pin sets for tools (stable, latest, bleeding) with `--preset` option
- Offline bundle mode for air-gapped machines with `docx2shelf tools bundle`
- Auto-discovery of plugins from user directory, package directory, and project directory
- Plugin information extraction using AST parsing for safe metadata reading
- Template-based plugin creation with automatic class name customization

### Changed
- Enhanced README with comprehensive plugin development section and examples
- Improved plugin management with verbose output options and detailed information display
- Extended tools CLI with preset support and offline bundle capabilities
- Enhanced plugin system documentation with best practices and troubleshooting

### Plugin Examples Added
- Basic Template: Complete starter showing all hook types with detailed comments
- HTML Cleaner: Advanced post-processing with smart quotes, CSS classes, and configurable cleanup
- Metadata Enhancer: Auto-generates descriptions, detects genres, estimates reading time with fiction-specific analysis

## [1.0.9]
### Added
- Automated PyPI publishing via GitHub Actions with trusted publishing
- Docker container support with pre-installed Pandoc and EPUBCheck
- Package manager distribution support for Homebrew, winget, and Scoop
- GPG signature verification for tool downloads (optional, with graceful fallback)
- Multi-platform Docker image builds (linux/amd64, linux/arm64)
- Comprehensive package distribution documentation and manifests

### Changed
- Enhanced tool download system with dual SHA-256 and GPG verification
- Updated README with multiple installation methods including package managers
- Improved Docker workflow with automated publishing to GitHub Container Registry

### Infrastructure
- Added PyPI publishing workflow triggered on releases
- Added Docker build and publish workflow with multi-platform support
- Created package manager configuration files for Homebrew, winget, and Scoop

## [1.0.8]
### Added
- First-party GitHub Action for automated EPUB building in CI/CD pipelines
- Matrix testing support across Windows/macOS/Linux with optional Pandoc and EPUBCheck
- Plugin system with hooks for pre-convert, post-convert, and metadata resolution
- Optional connectors framework for local Markdown and cloud document sources
- Plugin management CLI commands: `docx2shelf plugins list/load/enable/disable`
- Connector management CLI commands: `docx2shelf connectors list/enable/disable/auth/fetch`
- Network consent system for cloud connectors maintaining offline-first principle
- Pre-convert hooks for DOCX sanitization and preprocessing
- Post-convert hooks for HTML content transformation
- Metadata resolver hooks for dynamic metadata enrichment
- Local Markdown connector for seamless Markdown-to-EPUB workflow
- Google Docs and OneDrive connector framework (requires explicit opt-in)

### Changed
- Enhanced build pipeline with plugin hook integration
- Improved conversion workflow with configurable preprocessing and postprocessing
- Updated CLI interface with new plugin and connector management commands

## [1.0.7]
### Changed
- Extended metadata system with comprehensive role-based contributors (editor, illustrator, translator, narrator, designer, contributor)
- BISAC subject heading code validation and suggestion system with industry-standard categorization
- Age range and reading level validation for children's and educational books
- Copyright and rights management fields with pricing information support
- Content warnings and target audience specification
- Enhanced metadata.txt template with 20+ new optional fields for professional publishing
- Publishing store compatibility checklist system with docx2shelf checklist command
- Store-specific validation for KDP, Apple Books, and Kobo with detailed requirements checking
- Cover image validation including dimensions, format, and file size requirements
- JSON output support for CI/CD integration and automated publishing workflows
- Comprehensive metadata validation reporting with actionable fix suggestions

## [1.0.6]
### Changed
- Live preview mode with --preview flag that generates interactive browser-based preview instead of EPUB file
- Publishing profiles system with --profile flag supporting kdp, kobo, apple, generic, and legacy presets
- Batch processing mode with --batch command for processing multiple DOCX files with --parallel support
- Machine-readable JSON logging with --json-output flag for CI/CD pipeline integration
- Interactive preview server with automatic browser opening and content navigation
- Profile validation with platform-specific requirements and recommendations
- Parallel processing support with configurable worker limits for batch operations
- Comprehensive JSON output including build metadata, warnings, errors, and validation results
- Custom profile discovery and creation support for organization-specific presets
- Batch processing reports with detailed success/failure tracking

## [1.0.5]
### Changed
- Auto-detection of missing alt text with interactive prompts for accessibility compliance
- Default-enabled EPUBCheck validation with friendly error reporting and actionable suggestions
- RTL language support for Arabic, Hebrew, Persian with automatic direction detection
- CJK vertical writing modes for Chinese, Japanese, Korean with --vertical-writing flag
- Language-aware hyphenation and justification defaults based on script requirements
- Font stack optimization for different writing systems
- EPUB 2 compatibility mode via --epub2-compat flag with stricter CSS constraints
- Schema.org accessibility metadata automatically generated and embedded
- ARIA landmarks added for structural navigation and screen reader support
- Reading order validation with automatic issue detection
- Enhanced EPUBCheck output with timeout handling and issue prioritization
- Language-specific CSS generation with RTL and CJK support
- Automatic language attributes injected into HTML content

## [1.0.4]
### Changed
- Added 6 genre-specific CSS themes: fantasy, romance, mystery, scifi, academic, night
- Intelligent font optimization using fontTools to reduce EPUB file sizes by including only used characters
- Auto-resize, compression, and WebP/AVIF conversion with configurable quality and dimensions
- Theme discovery API with custom theme support and genre filtering
- Font embedding now includes automatic subsetting to reduce file sizes and licensing warnings
- Image processing with modern format conversion for better compression
- Theme selection enhanced with --list-themes command and genre-based filtering
- Graceful fallbacks when optional dependencies (fontTools, Pillow) are unavailable
- CLI options added: --image-quality, --image-max-width, --image-max-height, --image-format

## [1.0.3]
### Changed
- Table of contents now supports heading depths from 1-6 levels (h1 through h6)
- Mixed split strategy with --split-at mixed option and --mixed-split-pattern for flexible content splitting
- Enhanced heading level splitting with support for h3, h4, h5, and h6 splitting
- Per-section start markers with --reader-start-chapter option for custom reader start points
- ToC generation properly handles hierarchical heading structures with configurable depth limits
- EPUB navigation supports deeper nesting for complex document structures
- Heading ID generation creates proper hierarchical identifiers for multi-level documents
- Reader start point can be customized instead of defaulting to first chapter
- Improved ToC assembly logic to handle variable-depth heading structures.

## [1.0.2]

### Added
- **Robust DOCX fallback parser**: Enhanced DOCX processing with improved support for tracked changes, comments, complex tables, text boxes, shapes, and equations when Pandoc is not available.
- **Advanced style mapping system**: Comprehensive styles.json configuration with user-override support. Users can now place custom styles.json files in their document directory or working directory to override default Word style → HTML mappings.
- **Rasterize-on-escape feature**: Optional image fallback system for complex layout elements that cannot be cleanly translated to HTML, preserving author intention through visual placeholders.
- **Enhanced CSS injection**: Automatic injection of CSS rules from styles.json into generated EPUBs, providing better styling for new element types.

### Improved
- DOCX fallback parser now handles insertions, deletions, and move operations from Word's track changes feature.
- Comment processing with visual indicators and tooltip text extraction.
- Table processing with better structure preservation and error handling.
- Extended paragraph and character style mappings covering more Word built-in styles.
- Better handling of figures, captions, equations, and code blocks.

## [1.0.1]

### Changed
- The `install.bat` script was updated to download necessary files directly from the GitHub repository, making the installation fully standalone.
- The `install.ps1` script now downloads the `.whl` file directly from GitHub releases for installation.
- The `install.ps1` script now adds the `pipx` script path to the current PowerShell session's PATH, making `docx2shelf` immediately available.
- The `install.bat` file now pauses at the end of its execution to allow the user to review the installation output.

## [1.0.0]

### Added
- Support for `.txt`, `.md`, `.html`, and `.htm` as input file formats.
- Support for providing a directory as input, treating each file as a chapter.
- Automatic update checker that notifies users of new releases.
- A new `update` command to upgrade the tool.
- An `install.bat` script for easier installation on Windows.

### Changed
- The `--docx` command-line argument is now `--input` to reflect the broader file support.
- The output directory now defaults to the input directory.

### Fixed
- Various code style and linting issues.

### Removed
- Unnecessary files and build artifacts from the repository.
