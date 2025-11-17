#!/usr/bin/env python3
"""
Nuitka build configuration for Docx2Shelf GUI application.
Replaces PyInstaller with native compilation for better AV compatibility.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_with_nuitka():
    """Build Docx2Shelf using Nuitka for better antivirus compatibility."""

    # Ultra-conservative Nuitka command to prevent hangs
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # Create standalone executable

        # Entry point
        "src/docx2shelf/gui_main.py",

        # Output control
        "--output-filename=Docx2Shelf.exe" if sys.platform == "win32" else "--output-filename=Docx2Shelf",
        "--output-dir=dist",

        # Conservative import handling
        "--follow-imports",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=distutils",

        # Explicitly include standard library modules that might be missed
        "--include-module=concurrent.futures",
        "--include-module=concurrent",
        "--include-module=threading",
        "--include-module=multiprocessing",

        # Core Python standard library modules used throughout the codebase
        "--include-module=json",
        "--include-module=re",
        "--include-module=sys",
        "--include-module=os",
        "--include-module=tempfile",
        "--include-module=uuid",
        "--include-module=hashlib",
        "--include-module=subprocess",
        "--include-module=time",
        "--include-module=logging",
        "--include-module=sqlite3",
        "--include-module=shutil",
        "--include-module=platform",
        "--include-module=zipfile",
        "--include-module=webbrowser",
        "--include-module=io",
        "--include-module=pathlib",

        # XML and web-related modules
        "--include-module=xml",
        "--include-module=xml.etree",
        "--include-module=xml.etree.ElementTree",
        "--include-module=xml.dom",
        "--include-module=xml.dom.minidom",
        "--include-module=urllib",
        "--include-module=urllib.request",
        "--include-module=urllib.parse",
        "--include-module=http",
        "--include-module=http.server",
        "--include-module=socketserver",

        # Date/time and collections
        "--include-module=datetime",
        "--include-module=collections",

        # Math and random
        "--include-module=math",
        "--include-module=random",

        # Essential plugins only
        "--enable-plugin=tk-inter",

        # Windows-specific options
        "--disable-console" if sys.platform == "win32" else "",
        "--windows-icon-from-ico=src/docx2shelf/gui/assets/icon.ico" if sys.platform == "win32" and Path("src/docx2shelf/gui/assets/icon.ico").exists() else "",

        # Conservative settings to prevent hangs
        "--assume-yes-for-downloads",
        "--jobs=1",  # Single job
        "--low-memory",  # Reduce memory usage
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

            # Reorganize output to match expected structure for installers
            # Nuitka creates: dist/gui_main.dist/
            # Expected by installers: dist/Docx2Shelf/
            nuitka_output = Path("dist/gui_main.dist")
            expected_output = Path("dist/Docx2Shelf")

            if nuitka_output.exists():
                print(f"Reorganizing output from {nuitka_output} to {expected_output}")

                # Remove old expected output if it exists
                if expected_output.exists():
                    shutil.rmtree(expected_output)

                # Copy Nuitka output to expected location
                shutil.copytree(nuitka_output, expected_output)
                print(f"Output reorganized successfully")

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