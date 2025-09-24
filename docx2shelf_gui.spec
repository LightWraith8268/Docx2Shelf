# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the source directory
source_dir = Path(".") / "src"

# Analysis
a = Analysis(
    ['src/docx2shelf/gui_main.py'],
    pathex=[str(source_dir), str(Path(".").absolute()), str(Path("src").absolute())],
    binaries=[],
    datas=[
        # Include all data files needed by the application
        ('src/docx2shelf', 'docx2shelf'),  # Include entire docx2shelf package with proper structure
    ],
    hiddenimports=[
        # GUI framework
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
        'tkinter.scrolledtext',

        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',

        # EPUB handling
        'ebooklib',
        'ebooklib.epub',

        # HTML processing
        'bs4',
        'bs4.BeautifulSoup',
        'beautifulsoup4',

        # System utilities
        'platformdirs',
        'darkdetect',
        'packaging',

        # All docx2shelf modules
        'docx2shelf',
        'docx2shelf.gui',
        'docx2shelf.gui.modern_app',
        'docx2shelf.update',
        'docx2shelf.convert',
        'docx2shelf.assemble',
        'docx2shelf.metadata',
        'docx2shelf.settings',
        'docx2shelf.version',
        'docx2shelf.utils',
        'docx2shelf.figures',
        'docx2shelf.media_overlays',
        'docx2shelf.math_handler',
        'docx2shelf.cli',
        'docx2shelf.tools',
        'docx2shelf.themes',
        'docx2shelf.fonts',
        'docx2shelf.ai_integration',
        'docx2shelf.ai_genre_detection',
        'docx2shelf.ai_metadata',
        'docx2shelf.plugins',
        'docx2shelf.plugin_types',
        'docx2shelf.accessibility',
        'docx2shelf.validation',
        'docx2shelf.error_handler',
        'docx2shelf.path_utils',

        # Python standard library modules
        'zipfile',
        'tempfile',
        'json',
        'urllib.request',
        'urllib.parse',
        'subprocess',
        'threading',
        'datetime',
        'pathlib',
        'os',
        'sys',
        'webbrowser',
        'importlib',
        'importlib.metadata',
        'logging',
        're',
        'collections',
        'dataclasses',
        'typing',
        'functools',
        'itertools',
        'io',
        'shutil',
        'hashlib',
        'base64',
        'uuid',
        'time',
        'math',
        'random',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'jupyter',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Platform-specific executable configuration
if sys.platform == "win32":
    exe_name = "Docx2Shelf.exe"
    console = False
    icon = "src/docx2shelf/gui/assets/icon.ico"
elif sys.platform == "darwin":
    exe_name = "Docx2Shelf"
    console = False
    icon = "src/docx2shelf/gui/assets/icon.icns"
else:
    exe_name = "Docx2Shelf"
    console = False
    icon = "src/docx2shelf/gui/assets/icon.png"

# Create executable with metadata to reduce false positives
version_info = None  # PyInstaller version parameter expects file path, not dict

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to reduce antivirus false positives
    console=console,
    disable_windowed_traceback=False,
    # Add runtime options to reduce false positives
    noupx=True,
    onefile=False,  # Keep as onedir to reduce packing suspicion
    argv_emulation=False,
    target_arch=None,  # Use default architecture (64-bit on GitHub Actions)
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Disable icon until we have proper icon files
    version=version_info,  # Add version metadata
)

# Create distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX to reduce antivirus false positives
    upx_exclude=[],
    name="Docx2Shelf",
)

# macOS App Bundle
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Docx2Shelf.app",
        icon=None,  # Disable icon until we have proper icon files
        bundle_identifier="com.docx2shelf.app",
        version="1.9.2",
        info_plist={
            'CFBundleName': 'Docx2Shelf',
            'CFBundleDisplayName': 'Docx2Shelf',
            'CFBundleIdentifier': 'com.docx2shelf.app',
            'CFBundleVersion': '1.9.2',
            'CFBundleShortVersionString': '1.9.2',
            'CFBundleExecutable': 'Docx2Shelf',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'D2S!',
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Microsoft Word Document',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeExtensions': ['docx'],
                    'CFBundleTypeMIMETypes': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                },
                {
                    'CFBundleTypeName': 'Markdown Document',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeExtensions': ['md', 'markdown'],
                    'CFBundleTypeMIMETypes': ['text/markdown'],
                },
                {
                    'CFBundleTypeName': 'HTML Document',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeExtensions': ['html', 'htm'],
                    'CFBundleTypeMIMETypes': ['text/html'],
                },
                {
                    'CFBundleTypeName': 'Text Document',
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeExtensions': ['txt'],
                    'CFBundleTypeMIMETypes': ['text/plain'],
                },
            ]
        },
    )