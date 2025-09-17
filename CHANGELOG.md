# Changelog

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
