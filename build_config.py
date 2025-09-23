"""
Build configuration for cross-platform Docx2Shelf distribution.

This script handles PyInstaller builds for Windows, macOS, and Linux
with proper bundling of assets, dependencies, and platform-specific optimizations.
"""

import os
import sys
import platform
from pathlib import Path

# Build configuration
BUILD_CONFIG = {
    "app_name": "Docx2Shelf",
    "version": "1.6.2",
    "author": "Docx2Shelf Contributors",
    "description": "Document to EPUB Converter",

    # Entry points
    "gui_entry": "src/docx2shelf/gui/app.py",
    "cli_entry": "src/docx2shelf/cli.py",

    # Assets to include
    "data_files": [
        ("src/docx2shelf/assets", "assets"),
        ("src/docx2shelf/templates", "templates"),
        ("README.md", "."),
        ("LICENSE", "."),
    ],

    # Hidden imports (for AI features)
    "hidden_imports": [
        "tiktoken",
        "requests",
        "platformdirs",
        "ebooklib",
        "python-docx",
        "pypandoc",
        "docx2shelf.ai_chapter_detection",
        "docx2shelf.free_ai_service",
        "docx2shelf.settings",
    ],

    # Platform-specific settings
    "windows": {
        "icon": "assets/icons/docx2shelf.ico",
        "console": False,  # GUI app
        "admin": False,    # No admin required
    },
    "macos": {
        "icon": "assets/icons/docx2shelf.icns",
        "bundle_identifier": "com.docx2shelf.app",
        "codesign": False,  # Set to True for app store
    },
    "linux": {
        "icon": "assets/icons/docx2shelf.png",
        "categories": ["Office", "Publishing"],
    }
}

def get_platform_config():
    """Get platform-specific build configuration."""
    system = platform.system().lower()
    if system == "windows":
        return BUILD_CONFIG["windows"]
    elif system == "darwin":
        return BUILD_CONFIG["macos"]
    else:
        return BUILD_CONFIG["linux"]

def generate_pyinstaller_spec():
    """Generate PyInstaller spec file for current platform."""
    platform_config = get_platform_config()

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Build configuration
app_name = "{BUILD_CONFIG['app_name']}"
version = "{BUILD_CONFIG['version']}"

# Analysis
a = Analysis(
    ['{BUILD_CONFIG["gui_entry"]}'],
    pathex=[],
    binaries=[],
    datas=[
        {BUILD_CONFIG["data_files"]},
    ],
    hiddenimports={BUILD_CONFIG["hidden_imports"]},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter.test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Bundle
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={'console' if 'console' in platform_config and platform_config['console'] else 'False'},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{platform_config.get("icon", "")}',
)

# Collection (directory distribution)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Platform-specific additions
'''

    # Add platform-specific configurations
    if platform.system() == "Darwin":  # macOS
        spec_content += f'''
# macOS App Bundle
app = BUNDLE(
    coll,
    name='{BUILD_CONFIG["app_name"]}.app',
    icon='{platform_config.get("icon", "")}',
    bundle_identifier='{platform_config.get("bundle_identifier", "com.docx2shelf.app")}',
    version='{BUILD_CONFIG["version"]}',
    info_plist={{
        'CFBundleName': '{BUILD_CONFIG["app_name"]}',
        'CFBundleDisplayName': '{BUILD_CONFIG["app_name"]}',
        'CFBundleVersion': '{BUILD_CONFIG["version"]}',
        'CFBundleShortVersionString': '{BUILD_CONFIG["version"]}',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }},
)
'''

    return spec_content

if __name__ == "__main__":
    spec_content = generate_pyinstaller_spec()
    with open("docx2shelf.spec", "w") as f:
        f.write(spec_content)
    print(f"Generated PyInstaller spec for {platform.system()}")