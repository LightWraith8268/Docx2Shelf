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

    # Simplified Nuitka command - let Nuitka auto-discover dependencies
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # Create standalone executable
        "--onefile",     # Single executable file

        # Entry point
        "src/docx2shelf/gui_main.py",

        # Output control
        "--output-filename=Docx2Shelf.exe" if sys.platform == "win32" else "--output-filename=Docx2Shelf",
        "--output-dir=dist",

        # Follow imports automatically
        "--follow-imports",

        # Essential plugins
        "--enable-plugin=tk-inter",

        # Windows-specific options
        "--disable-console" if sys.platform == "win32" else "",
        "--windows-icon-from-ico=src/docx2shelf/gui/assets/icon.ico" if sys.platform == "win32" and Path("src/docx2shelf/gui/assets/icon.ico").exists() else "",

        # Basic optimizations
        "--assume-yes-for-downloads",
        "--jobs=1",  # Use single job to reduce memory usage
    ]

    # Remove empty strings from command
    nuitka_cmd = [arg for arg in nuitka_cmd if arg]

    print("Building with Nuitka for better antivirus compatibility...")
    print(f"Command: {' '.join(nuitka_cmd)}")

    try:
        # Run Nuitka build with streaming output
        process = subprocess.Popen(
            nuitka_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        rc = process.poll()
        if rc == 0:
            print("Nuitka build successful!")
            return True
        else:
            print(f"Nuitka build failed with exit code {rc}")
            return False

    except Exception as e:
        print(f"Nuitka build failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = build_with_nuitka()
    sys.exit(0 if success else 1)