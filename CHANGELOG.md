# Changelog

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
