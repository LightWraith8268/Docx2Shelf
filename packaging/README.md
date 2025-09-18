# Package Distribution Files

This directory contains configuration files for various package managers and distribution methods.

## Directory Structure

- `homebrew/` - Homebrew formula for macOS/Linux
- `winget/` - Windows Package Manager manifest
- `scoop/` - Scoop manifest for Windows
- `docker/` - Docker-related files (Dockerfile is in project root)

## Maintaining Package Definitions

### Homebrew

The Homebrew formula (`homebrew/docx2shelf.rb`) needs to be:
1. Updated with correct SHA256 checksums when new versions are released
2. Submitted to the homebrew-core repository via pull request

### Windows Package Manager (winget)

The winget manifest (`winget/docx2shelf.yaml`) should be:
1. Updated with new version information
2. SHA256 checksums updated for install.bat
3. Submitted to the winget-pkgs repository

### Scoop

The Scoop manifest (`scoop/docx2shelf.json`) includes:
1. Auto-update configuration that pulls from GitHub releases
2. Dependency on Python
3. Optional suggestion for Pandoc

## Publishing Process

1. **PyPI**: Automated via GitHub Actions when a release is published
2. **Docker**: Automated via GitHub Actions, images pushed to GitHub Container Registry
3. **Package Managers**: Manual submission to respective repositories with updated checksums

## Security

- All downloads include SHA-256 verification
- GPG verification is available for supported tools
- Docker images are built from source in CI/CD pipeline