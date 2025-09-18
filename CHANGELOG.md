# Changelog

## [1.0.4]

### Added
- **Genre-specific theme system**: Added 6 new CSS themes (fantasy, romance, mystery, scifi, academic, night) with metadata-driven discovery.
- **Font subsetting**: Intelligent font optimization using fontTools to reduce EPUB file sizes by including only used characters.
- **Advanced image pipeline**: Auto-resize, compression, and WebP/AVIF conversion with configurable quality and dimensions.
- **Theme discovery API**: Comprehensive theme management with custom theme support and genre filtering.
- **Image processing options**: New CLI flags for image quality, dimensions, and format conversion control.

### Improved
- Font embedding now includes automatic subsetting to reduce file sizes and licensing warnings.
- Image processing with modern format conversion (WebP/AVIF) for better compression.
- Theme selection enhanced with `--list-themes` command and genre-based filtering.
- Graceful fallbacks when optional dependencies (fontTools, Pillow) are unavailable.

### Technical
- Created `fonts.py` module with character analysis and font subsetting capabilities.
- Created `images.py` module with comprehensive image optimization pipeline.
- Enhanced `themes.py` with metadata system and theme discovery functions.
- Added CLI options: `--image-quality`, `--image-max-width`, `--image-max-height`, `--image-format`.
- Updated `BuildOptions` dataclass with image processing configuration fields.

## [1.0.3]

### Added
- **Arbitrary ToC depth support**: Table of contents now supports heading depths from 1-6 levels (h1 through h6), extending beyond the previous h1/h2 limitation.
- **Mixed split strategy**: New `--split-at mixed` option with `--mixed-split-pattern` allows flexible content splitting (e.g., "h1,pagebreak" or "h1:main,pagebreak:appendix").
- **Enhanced heading level splitting**: Added support for splitting content at h3, h4, h5, and h6 heading levels.
- **Per-section start markers**: New `--reader-start-chapter` option allows specifying which chapter should be the reader's starting point in EPUB landmarks.

### Improved
- ToC generation now properly handles hierarchical heading structures with configurable depth limits.
- EPUB navigation supports deeper nesting for complex document structures.
- Heading ID generation creates proper hierarchical identifiers for multi-level documents.
- Reader start point can be customized instead of defaulting to first chapter.

### Technical
- Enhanced `_inject_heading_ids` function to process arbitrary heading depths.
- Added `split_html_by_heading_level` and `split_html_mixed` functions for flexible content splitting.
- Updated `BuildOptions` dataclass with new fields for mixed splitting and reader start configuration.
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
