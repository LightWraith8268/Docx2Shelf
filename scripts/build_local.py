#!/usr/bin/env python3
"""
Local build script for Docx2Shelf.

This script handles local builds for development and testing.
Run this before committing to test the build process.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            shell=(platform.system() == "Windows")
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_dependencies():
    """Check if all build dependencies are available."""
    print("Checking build dependencies...")

    # Check Python
    if sys.version_info < (3, 11):
        print("Error: Python 3.11+ required")
        sys.exit(1)

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    # Check main dependencies
    try:
        import tkinter
        print("✓ Tkinter available")
    except ImportError:
        print("Error: Tkinter not available")
        sys.exit(1)

    # Check project is installed
    try:
        import docx2shelf
        print(f"✓ Docx2Shelf package available")
    except ImportError:
        print("Installing Docx2Shelf in development mode...")
        run_command([sys.executable, "-m", "pip", "install", "-e", ".[all]"])

def create_icons():
    """Create placeholder icons if they don't exist."""
    icons_dir = Path("assets/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    icon_files = {
        "docx2shelf.ico": "Windows icon",
        "docx2shelf.icns": "macOS icon",
        "docx2shelf.png": "Linux icon"
    }

    for icon_file, description in icon_files.items():
        icon_path = icons_dir / icon_file
        if not icon_path.exists():
            print(f"Creating placeholder {icon_file}")
            icon_path.write_text(f"# {description} placeholder\n")

def build_app():
    """Build the application using PyInstaller."""
    print(f"Building Docx2Shelf for {platform.system()}...")

    # Clean previous builds
    build_dirs = ["build", "dist", "__pycache__"]
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            print(f"Cleaning {build_dir}/")
            shutil.rmtree(build_dir)

    # Generate spec file
    print("Generating PyInstaller spec...")
    run_command([sys.executable, "build_config.py"])

    # Run PyInstaller
    print("Running PyInstaller...")
    run_command(["pyinstaller", "docx2shelf.spec", "--clean", "--noconfirm"])

    # Test the build
    print("Testing the built application...")
    test_executable()

def test_executable():
    """Test the built executable."""
    system = platform.system()

    if system == "Windows":
        exe_path = Path("dist/Docx2Shelf/Docx2Shelf.exe")
    elif system == "Darwin":
        exe_path = Path("dist/Docx2Shelf.app/Contents/MacOS/Docx2Shelf")
    else:
        exe_path = Path("dist/Docx2Shelf/Docx2Shelf")

    if not exe_path.exists():
        print(f"Error: Executable not found at {exe_path}")
        sys.exit(1)

    print(f"✓ Executable built: {exe_path}")

    # Try to run version check (will fail in GUI mode, but that's expected)
    try:
        result = run_command([str(exe_path), "--version"], check=False)
        if result.returncode == 0:
            print("✓ Version check successful")
        else:
            print("Note: GUI mode detected (normal for GUI builds)")
    except Exception as e:
        print(f"Note: Could not test version check: {e}")

def create_portable_archive():
    """Create a portable archive of the application."""
    system = platform.system()

    if system == "Windows":
        archive_name = "docx2shelf-windows-portable.zip"
        import zipfile
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk("dist/Docx2Shelf"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, "dist")
                    zf.write(file_path, arc_path)

    elif system == "Darwin":
        archive_name = "docx2shelf-macos-portable.zip"
        run_command(["zip", "-r", archive_name, "Docx2Shelf.app"], cwd="dist")

    else:
        archive_name = "docx2shelf-linux-portable.tar.gz"
        run_command(["tar", "-czf", archive_name, "Docx2Shelf"], cwd="dist")

    print(f"✓ Created portable archive: {archive_name}")

def main():
    """Main build process."""
    print("Docx2Shelf Local Build Script")
    print("=" * 40)

    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    print(f"Building in: {os.getcwd()}")

    # Run build steps
    check_dependencies()
    create_icons()
    build_app()
    create_portable_archive()

    print("\n" + "=" * 40)
    print("✓ Build completed successfully!")
    print(f"✓ Executable: dist/Docx2Shelf/")
    print(f"✓ Archive: *-portable.*")
    print("\nTo test the application:")

    system = platform.system()
    if system == "Windows":
        print("  dist\\Docx2Shelf\\Docx2Shelf.exe")
    elif system == "Darwin":
        print("  open dist/Docx2Shelf.app")
    else:
        print("  ./dist/Docx2Shelf/Docx2Shelf")

if __name__ == "__main__":
    main()