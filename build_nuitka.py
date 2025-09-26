#!/usr/bin/env python3
"""
Nuitka build configuration for Docx2Shelf GUI application.
Replaces PyInstaller with native compilation for better AV compatibility.
"""

import os
import sys
import subprocess
from pathlib import Path

def build_with_nuitka():
    """Build Docx2Shelf using Nuitka for better antivirus compatibility."""

    # Base Nuitka command
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # Create standalone executable
        "--onefile",     # Single executable file

        # Entry point
        "src/docx2shelf/gui_main.py",

        # Output control
        "--output-filename=Docx2Shelf.exe" if sys.platform == "win32" else "--output-filename=Docx2Shelf",
        "--output-dir=dist",

        # Include data files and modules
        "--include-package=docx2shelf",
        "--include-package=customtkinter",
        "--include-package=tkinter",
        "--include-package=PIL",
        "--include-package=ebooklib",
        "--include-package=bs4",
        "--include-package=platformdirs",
        "--include-package=darkdetect",
        "--include-package=packaging",

        # Include data directories
        "--include-data-dir=src/docx2shelf=docx2shelf",

        # Windows-specific options
        "--disable-console" if sys.platform == "win32" else "",
        "--windows-icon=src/docx2shelf/gui/assets/icon.ico" if sys.platform == "win32" and Path("src/docx2shelf/gui/assets/icon.ico").exists() else "",

        # Anti-malware optimizations
        "--assume-yes-for-downloads",
        "--warn-unusual-code=no",
        "--warn-implicit-exceptions=no",

        # Performance optimizations
        "--enable-plugin=tk-inter",
        "--enable-plugin=multiprocessing" if sys.platform != "win32" else "",

        # Version information for Windows
        f"--windows-company-name=Docx2Shelf Open Source Project" if sys.platform == "win32" else "",
        f"--windows-product-name=Docx2Shelf Document Converter" if sys.platform == "win32" else "",
        f"--windows-file-version=2.0.9.0" if sys.platform == "win32" else "",
        f"--windows-product-version=2.0.9" if sys.platform == "win32" else "",
        f"--windows-file-description=Legitimate Document to EPUB Converter - Native Compilation" if sys.platform == "win32" else "",
    ]

    # Remove empty strings from command
    nuitka_cmd = [arg for arg in nuitka_cmd if arg]

    print("🚀 Building with Nuitka for better antivirus compatibility...")
    print(f"Command: {' '.join(nuitka_cmd)}")

    try:
        # Run Nuitka build
        result = subprocess.run(nuitka_cmd, check=True, capture_output=True, text=True)
        print("✅ Nuitka build successful!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Nuitka build failed!")
        print(f"Error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

if __name__ == "__main__":
    success = build_with_nuitka()
    sys.exit(0 if success else 1)