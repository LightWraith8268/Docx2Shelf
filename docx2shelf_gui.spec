# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the source directory
source_dir = Path(".") / "src"

# Analysis
a = Analysis(
    ['src/docx2shelf/gui_main.py'],
    pathex=[str(source_dir)],
    binaries=[],
    datas=[
        ('src/docx2shelf/assets', 'docx2shelf/assets'),
        ('src/docx2shelf/templates', 'docx2shelf/templates'),
        ('src/docx2shelf/gui/assets', 'docx2shelf/gui/assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'ebooklib',
        'ebooklib.epub',
        'platformdirs',
        'docx2shelf.gui.modern_app',
        'docx2shelf.update',
        'docx2shelf.convert',
        'docx2shelf.assemble',
        'docx2shelf.metadata',
        'docx2shelf.settings',
        'docx2shelf.version',
        'docx2shelf.utils',
        'zipfile',
        'tempfile',
        'json',
        'urllib.request',
        'subprocess',
        'threading',
        'datetime',
        'pathlib',
        'os',
        'sys',
        'webbrowser',
        'darkdetect',
        'packaging',
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,  # Use platform-specific icon
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
        icon=icon,  # Use platform-specific icon
        bundle_identifier="com.docx2shelf.app",
        version="1.8.4",
        info_plist={
            'CFBundleName': 'Docx2Shelf',
            'CFBundleDisplayName': 'Docx2Shelf',
            'CFBundleIdentifier': 'com.docx2shelf.app',
            'CFBundleVersion': '1.8.4',
            'CFBundleShortVersionString': '1.8.4',
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