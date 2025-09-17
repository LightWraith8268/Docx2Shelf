# Changelog

## [1.0.0] - 2025-09-17

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