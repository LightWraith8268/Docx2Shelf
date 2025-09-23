# Docx2Shelf Distribution Guide

This guide covers building and distributing Docx2Shelf across multiple platforms.

## 🎯 Quick Start

### Local Development Build
```bash
# Install dependencies
pip install -e .[all]
pip install pyinstaller>=6.0

# Build for current platform
python scripts/build_local.py
```

### Automated CI/CD Builds
Push a git tag to trigger automated builds for all platforms:
```bash
git tag v1.6.3
git push origin v1.6.3
```

## 🏗️ Build Methods

### 1. PyInstaller (Recommended)
**Best for**: Cross-platform GUI applications with complex dependencies

**Pros:**
- Excellent Tkinter support
- Handles AI dependencies (requests, tiktoken, etc.)
- Single executable output
- Good local LLM library support
- Platform-specific optimizations

**Build Process:**
```bash
# Generate spec file
python build_config.py

# Build application
pyinstaller docx2shelf.spec --clean --noconfirm
```

**Output:**
- Windows: `Docx2Shelf.exe` (+ dependencies in folder)
- macOS: `Docx2Shelf.app` bundle
- Linux: `Docx2Shelf` executable (+ dependencies in folder)

### 2. Alternative: cx_Freeze
For comparison, here's a cx_Freeze setup:

```python
# setup_freeze.py
from cx_Freeze import setup, Executable
import sys

# Platform-specific settings
if sys.platform == "win32":
    base = "Win32GUI"  # No console window
else:
    base = None

setup(
    name="Docx2Shelf",
    version="1.6.2",
    description="Document to EPUB Converter",
    executables=[
        Executable(
            script="src/docx2shelf/gui/app.py",
            base=base,
            icon="assets/icons/docx2shelf.ico",
            target_name="Docx2Shelf"
        )
    ],
    options={
        "build_exe": {
            "packages": ["tkinter", "docx2shelf"],
            "include_files": [
                ("src/docx2shelf/assets", "assets"),
                ("src/docx2shelf/templates", "templates"),
            ],
            "excludes": ["matplotlib", "numpy", "scipy"]
        }
    }
)
```

### 3. Alternative: Nuitka
For maximum performance:

```bash
# Install Nuitka
pip install nuitka

# Build with Nuitka
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=tk-inter \
    --include-data-dir=src/docx2shelf/assets=assets \
    --include-data-dir=src/docx2shelf/templates=templates \
    --windows-disable-console \
    --windows-icon-from-ico=assets/icons/docx2shelf.ico \
    src/docx2shelf/gui/app.py
```

## 📦 Distribution Formats

### Windows
1. **Portable ZIP** - Extract and run anywhere
2. **NSIS Installer** - Professional Windows installer with registry entries
3. **MSI Package** - Enterprise deployment via Group Policy
4. **Windows Store** - UWP packaging (future consideration)

### macOS
1. **Portable ZIP** - Simple distribution
2. **DMG Image** - Standard macOS installer format
3. **PKG Installer** - System-level installation
4. **App Store** - Sandboxed distribution (requires changes)

### Linux
1. **Portable TAR.GZ** - Universal Linux distribution
2. **AppImage** - Self-contained portable application
3. **Snap Package** - Universal Linux package
4. **Flatpak** - Sandboxed distribution
5. **Distribution Packages** - DEB/RPM for specific distros

## 🤖 CI/CD Pipeline

### GitHub Actions Workflow
Our automated pipeline builds for all platforms:

```yaml
# Triggered by git tags or manual dispatch
on:
  push:
    tags: ['v*']
  workflow_dispatch:

# Matrix build for Windows, macOS, Linux
strategy:
  matrix:
    os: [windows-latest, macos-latest, ubuntu-latest]

# Steps:
# 1. Setup Python 3.11
# 2. Install dependencies
# 3. Generate platform-specific build
# 4. Create installers
# 5. Upload artifacts
# 6. Create GitHub release
```

### Build Outputs
Each release includes:
- **Portable versions** for all platforms
- **Native installers** (EXE, DMG, AppImage)
- **Source code** archives
- **Checksums** for verification

## 🔧 Platform-Specific Considerations

### Windows
- **No console window** for GUI builds
- **Icon embedding** in executable
- **DPI awareness** for high-resolution displays
- **Windows Defender** exclusions may be needed
- **Code signing** recommended for distribution

### macOS
- **App bundle structure** required
- **Gatekeeper compatibility** (notarization)
- **Retina display support**
- **Dark mode compatibility**
- **Apple Silicon** (M1/M2) support

### Linux
- **Desktop integration** (.desktop files)
- **Icon theme integration**
- **Multiple distribution support**
- **Dependency management** (system vs bundled)
- **AppStream metadata** for software centers

## 🚀 Advanced Distribution

### App Stores

#### Microsoft Store (Windows)
```bash
# Convert to UWP package
pip install msix-packaging-tool

# Package for Store
msix-packaging-tool create-package \
    --source dist/Docx2Shelf \
    --destination Docx2Shelf.msix \
    --package-editor
```

#### Mac App Store
Requires sandboxing and entitlements:
```xml
<!-- entitlements.plist -->
<key>com.apple.security.app-sandbox</key>
<true/>
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
```

#### Linux Software Centers
```bash
# Create Flatpak
flatpak-builder build-dir org.docx2shelf.Docx2Shelf.yml

# Create Snap
snapcraft
```

### Enterprise Deployment

#### Silent Installation
```bash
# Windows
Docx2Shelf-Setup.exe /S

# macOS
installer -pkg Docx2Shelf.pkg -target /

# Linux
sudo dpkg -i docx2shelf.deb
```

#### Group Policy (Windows)
MSI packages can be deployed via Active Directory Group Policy for enterprise environments.

## 🧪 Testing Strategy

### Automated Testing
```bash
# Test builds in CI
python -m pytest tests/
python scripts/test_build.py

# Smoke tests for executables
./dist/Docx2Shelf --version
./dist/Docx2Shelf --help
```

### Manual Testing Checklist
- [ ] Application launches without errors
- [ ] GUI renders correctly on each platform
- [ ] File dialogs work (open/save)
- [ ] Conversion process completes
- [ ] AI features function (local LLM, remote API)
- [ ] Settings persistence works
- [ ] No console windows on Windows GUI build

### Virtual Environment Testing
Test on clean systems using:
- **Windows**: Windows Sandbox, VirtualBox VMs
- **macOS**: macOS virtual machines, clean user accounts
- **Linux**: Docker containers, various distributions

## 📋 Release Process

### 1. Pre-Release
```bash
# Update version numbers
vim pyproject.toml  # Update version
vim src/docx2shelf/__init__.py  # Update __version__

# Test locally
python scripts/build_local.py
python -m pytest

# Update changelog
vim CHANGELOG.md
```

### 2. Release
```bash
# Create and push tag
git tag v1.6.3
git push origin v1.6.3

# GitHub Actions automatically:
# - Builds for all platforms
# - Creates installers
# - Uploads to GitHub Releases
```

### 3. Post-Release
```bash
# Update documentation
# Notify users via appropriate channels
# Monitor for issues
```

## 🔍 Troubleshooting

### Common Issues

#### PyInstaller Import Errors
```bash
# Add missing imports to spec file
hiddenimports=['missing_module', 'another_module']

# Or use hook files
echo "hiddenimports = ['missing_module']" > hook-my_package.py
```

#### Large Executable Size
```bash
# Exclude unnecessary packages
excludes=['matplotlib', 'numpy', 'unused_package']

# Use UPX compression
upx=True  # In spec file
```

#### Tkinter Issues
```bash
# Ensure tk-inter plugin is enabled
--enable-plugin=tk-inter  # For Nuitka

# Include tkinter explicitly
--hidden-import=tkinter  # For PyInstaller
```

#### macOS Gatekeeper
```bash
# Sign the application
codesign --force --deep --sign "Developer ID" Docx2Shelf.app

# Notarize for Gatekeeper
xcrun notarytool submit Docx2Shelf.dmg --keychain-profile "notary"
```

### Debug Builds
For troubleshooting, create debug builds:
```bash
# PyInstaller debug build
pyinstaller --debug=all docx2shelf.spec

# Enable console on Windows
# Set console=True in spec file
```

## 📊 Performance Optimization

### Size Optimization
- Exclude unused dependencies
- Use UPX compression
- Remove debug symbols
- Optimize asset inclusion

### Startup Speed
- Lazy import heavy modules
- Precompile Python bytecode
- Use --onefile sparingly (slower startup)

### Runtime Performance
- Bundle native libraries
- Use platform-specific optimizations
- Profile and optimize hot paths

This distribution setup provides professional-grade deployment for Docx2Shelf across all major platforms while maintaining the flexibility to support local LLM integrations and AI features.