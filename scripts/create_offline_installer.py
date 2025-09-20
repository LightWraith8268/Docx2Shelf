#!/usr/bin/env python3
"""
Create Offline Installer for Docx2Shelf

This script creates a self-contained offline installer that bundles all dependencies
and can install docx2shelf without requiring internet access.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
from pathlib import Path
import json
import hashlib
from typing import List, Dict, Optional


class OfflineInstallerBuilder:
    """Builder for offline docx2shelf installer."""

    def __init__(self, output_dir: Path = None):
        """Initialize the builder.

        Args:
            output_dir: Directory to create the offline installer in
        """
        self.output_dir = output_dir or Path.cwd() / "offline_installer"
        self.temp_dir = None
        self.dependencies = []

    def create_installer(self, include_dev_deps: bool = False) -> Path:
        """Create the offline installer package.

        Args:
            include_dev_deps: Whether to include development dependencies

        Returns:
            Path to the created installer
        """
        print("🚀 Creating offline installer for docx2shelf...")

        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="docx2shelf_offline_"))
        print(f"📁 Working directory: {self.temp_dir}")

        try:
            # Step 1: Download all dependencies
            self._download_dependencies(include_dev_deps)

            # Step 2: Create installer structure
            installer_dir = self._create_installer_structure()

            # Step 3: Copy wheels and dependencies
            self._copy_wheels(installer_dir)

            # Step 4: Create installation scripts
            self._create_installation_scripts(installer_dir)

            # Step 5: Create verification data
            self._create_verification_data(installer_dir)

            # Step 6: Package everything
            installer_path = self._package_installer(installer_dir)

            print(f"✅ Offline installer created: {installer_path}")
            return installer_path

        finally:
            # Cleanup
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

    def _download_dependencies(self, include_dev_deps: bool):
        """Download all dependencies as wheels."""
        print("📦 Downloading dependencies...")

        wheels_dir = self.temp_dir / "wheels"
        wheels_dir.mkdir(parents=True)

        # Base dependencies
        packages = [
            "docx2shelf[docx]",
            "ebooklib",
            "python-docx",
        ]

        if include_dev_deps:
            packages.extend([
                "pytest",
                "pytest-cov",
                "ruff",
                "black",
                "mypy",
            ])

        # Download packages
        for package in packages:
            print(f"  📥 Downloading {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "download",
                "--dest", str(wheels_dir),
                "--prefer-binary",
                package
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"  ⚠️  Warning: Failed to download {package}")
                print(f"     Error: {result.stderr}")
            else:
                print(f"  ✅ Downloaded {package}")

        # Get list of downloaded files
        self.dependencies = list(wheels_dir.glob("*.whl")) + list(wheels_dir.glob("*.tar.gz"))
        print(f"📦 Downloaded {len(self.dependencies)} packages")

    def _create_installer_structure(self) -> Path:
        """Create the installer directory structure."""
        print("📁 Creating installer structure...")

        installer_dir = self.temp_dir / "docx2shelf_offline_installer"
        installer_dir.mkdir()

        # Create subdirectories
        (installer_dir / "wheels").mkdir()
        (installer_dir / "scripts").mkdir()
        (installer_dir / "docs").mkdir()

        return installer_dir

    def _copy_wheels(self, installer_dir: Path):
        """Copy downloaded wheels to installer."""
        print("📦 Copying packages...")

        wheels_dest = installer_dir / "wheels"
        wheels_src = self.temp_dir / "wheels"

        for wheel_file in self.dependencies:
            dest_file = wheels_dest / wheel_file.name
            shutil.copy2(wheel_file, dest_file)
            print(f"  ✅ Copied {wheel_file.name}")

    def _create_installation_scripts(self, installer_dir: Path):
        """Create installation scripts."""
        print("📝 Creating installation scripts...")

        scripts_dir = installer_dir / "scripts"

        # Windows batch installer
        batch_script = scripts_dir / "install_offline.bat"
        with open(batch_script, "w", encoding="utf-8") as f:
            f.write(self._get_windows_installer_script())

        # Python installer script
        python_script = scripts_dir / "install_offline.py"
        with open(python_script, "w", encoding="utf-8") as f:
            f.write(self._get_python_installer_script())

        # Shell script for Unix systems
        shell_script = scripts_dir / "install_offline.sh"
        with open(shell_script, "w", encoding="utf-8") as f:
            f.write(self._get_shell_installer_script())

        # Make shell script executable
        if sys.platform != "win32":
            os.chmod(shell_script, 0o755)

        print("  ✅ Created installation scripts")

    def _create_verification_data(self, installer_dir: Path):
        """Create verification data for integrity checks."""
        print("🔒 Creating verification data...")

        verification_data = {
            "version": "1.3.1",
            "created_by": "docx2shelf offline installer builder",
            "packages": {},
            "checksums": {}
        }

        wheels_dir = installer_dir / "wheels"
        for wheel_file in wheels_dir.iterdir():
            if wheel_file.is_file():
                # Calculate checksums
                with open(wheel_file, "rb") as f:
                    content = f.read()
                    md5_hash = hashlib.md5(content).hexdigest()
                    sha256_hash = hashlib.sha256(content).hexdigest()

                verification_data["checksums"][wheel_file.name] = {
                    "md5": md5_hash,
                    "sha256": sha256_hash,
                    "size": len(content)
                }

        # Save verification data
        verification_file = installer_dir / "verification.json"
        with open(verification_file, "w", encoding="utf-8") as f:
            json.dump(verification_data, f, indent=2)

        print("  ✅ Created verification data")

    def _package_installer(self, installer_dir: Path) -> Path:
        """Package the installer into a zip file."""
        print("📦 Packaging installer...")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create zip file
        zip_path = self.output_dir / "docx2shelf_offline_installer.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in installer_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(installer_dir.parent)
                    zipf.write(file_path, arcname)

        print(f"  ✅ Created package: {zip_path}")
        return zip_path

    def _get_windows_installer_script(self) -> str:
        """Get the Windows batch installer script."""
        return '''@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Offline Installer for Windows
echo ========================================
echo    Docx2Shelf Offline Installer
echo ========================================
echo.

:: Check for Python
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python not found. Please install Python 3.11+ from https://python.org
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)

echo ✓ Python found: %PYTHON_CMD%

:: Get script directory
set "SCRIPT_DIR=%~dp0"
set "WHEELS_DIR=%SCRIPT_DIR%..\\wheels"

:: Verify wheels directory exists
if not exist "%WHEELS_DIR%" (
    echo ERROR: Wheels directory not found: %WHEELS_DIR%
    echo Make sure you extracted the complete offline installer.
    pause
    exit /b 1
)

echo ✓ Found offline packages in: %WHEELS_DIR%

:: Install from offline wheels
echo Installing docx2shelf from offline packages...
%PYTHON_CMD% -m pip install --user --find-links "%WHEELS_DIR%" --no-index docx2shelf[docx]

if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    echo Trying individual package installation...

    :: Try installing dependencies individually
    %PYTHON_CMD% -m pip install --user --find-links "%WHEELS_DIR%" --no-index ebooklib
    %PYTHON_CMD% -m pip install --user --find-links "%WHEELS_DIR%" --no-index python-docx
    %PYTHON_CMD% -m pip install --user --find-links "%WHEELS_DIR%" --no-index docx2shelf

    if %errorlevel% neq 0 (
        echo ERROR: Individual installation also failed
        pause
        exit /b 1
    )
)

:: Verify installation
echo Verifying installation...
docx2shelf --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Installation successful!
    docx2shelf --version
) else (
    echo ⚠️  Installation completed but docx2shelf not found on PATH
    echo You may need to restart your terminal or add Python Scripts to PATH
)

echo.
echo Installation completed!
pause
'''

    def _get_python_installer_script(self) -> str:
        """Get the Python installer script."""
        return '''#!/usr/bin/env python3
"""
Docx2Shelf Offline Installer (Python)

This script installs docx2shelf from offline packages without requiring internet access.
"""

import sys
import subprocess
import os
from pathlib import Path
import json


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("Please upgrade to Python 3.11 or higher")
        return False

    print(f"✓ Python {version.major}.{version.minor} is compatible")
    return True


def verify_packages(wheels_dir):
    """Verify package integrity."""
    print("🔒 Verifying package integrity...")

    verification_file = wheels_dir.parent / "verification.json"
    if not verification_file.exists():
        print("⚠️  Verification data not found, skipping integrity check")
        return True

    try:
        with open(verification_file) as f:
            verification_data = json.load(f)

        checksums = verification_data.get("checksums", {})

        for wheel_file in wheels_dir.iterdir():
            if wheel_file.is_file() and wheel_file.name in checksums:
                import hashlib
                with open(wheel_file, "rb") as f:
                    content = f.read()
                    actual_sha256 = hashlib.sha256(content).hexdigest()

                expected_sha256 = checksums[wheel_file.name]["sha256"]
                if actual_sha256 != expected_sha256:
                    print(f"❌ Integrity check failed for {wheel_file.name}")
                    return False

        print("✓ All packages verified")
        return True

    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
        return True  # Continue anyway


def install_offline():
    """Install docx2shelf from offline packages."""
    print("========================================")
    print("    Docx2Shelf Offline Installer")
    print("========================================")
    print()

    # Check Python version
    if not check_python_version():
        return 1

    # Get paths
    script_dir = Path(__file__).parent
    wheels_dir = script_dir.parent / "wheels"

    if not wheels_dir.exists():
        print(f"❌ Wheels directory not found: {wheels_dir}")
        print("Make sure you extracted the complete offline installer.")
        return 1

    print(f"✓ Found offline packages in: {wheels_dir}")

    # Verify packages
    if not verify_packages(wheels_dir):
        print("❌ Package verification failed")
        return 1

    # Install packages
    print("📦 Installing docx2shelf from offline packages...")

    cmd = [
        sys.executable, "-m", "pip", "install", "--user",
        "--find-links", str(wheels_dir),
        "--no-index",
        "docx2shelf[docx]"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Installation failed")
        print("Trying individual package installation...")

        # Try installing dependencies individually
        packages = ["ebooklib", "python-docx", "docx2shelf"]
        for package in packages:
            cmd = [
                sys.executable, "-m", "pip", "install", "--user",
                "--find-links", str(wheels_dir),
                "--no-index",
                package
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to install {package}")
                print(f"Error: {result.stderr}")
                return 1
            print(f"✓ Installed {package}")

    # Verify installation
    print("🔍 Verifying installation...")
    result = subprocess.run([sys.executable, "-c", "import docx2shelf; print('docx2shelf imported successfully')"],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Installation successful!")

        # Try to get version
        try:
            result = subprocess.run(["docx2shelf", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Version: {result.stdout.strip()}")
            else:
                print("⚠️  docx2shelf command not found on PATH")
                print("You may need to restart your terminal or add Python Scripts to PATH")
        except FileNotFoundError:
            print("⚠️  docx2shelf command not found on PATH")
            print("You may need to restart your terminal or add Python Scripts to PATH")
    else:
        print("❌ Installation verification failed")
        print(f"Error: {result.stderr}")
        return 1

    print()
    print("Installation completed!")
    return 0


if __name__ == "__main__":
    sys.exit(install_offline())
'''

    def _get_shell_installer_script(self) -> str:
        """Get the shell installer script for Unix systems."""
        return '''#!/bin/bash

# Docx2Shelf Offline Installer for Unix Systems

echo "========================================"
echo "    Docx2Shelf Offline Installer"
echo "========================================"
echo

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ ERROR: Python not found"
    echo "Please install Python 3.11+ from your package manager or https://python.org"
    exit 1
fi

echo "✓ Python found: $PYTHON_CMD"

# Check Python version
python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Python version: $python_version"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="$SCRIPT_DIR/../wheels"

# Verify wheels directory exists
if [ ! -d "$WHEELS_DIR" ]; then
    echo "❌ ERROR: Wheels directory not found: $WHEELS_DIR"
    echo "Make sure you extracted the complete offline installer."
    exit 1
fi

echo "✓ Found offline packages in: $WHEELS_DIR"

# Install from offline wheels
echo "📦 Installing docx2shelf from offline packages..."
$PYTHON_CMD -m pip install --user --find-links "$WHEELS_DIR" --no-index "docx2shelf[docx]"

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    echo "Trying individual package installation..."

    # Try installing dependencies individually
    $PYTHON_CMD -m pip install --user --find-links "$WHEELS_DIR" --no-index ebooklib
    $PYTHON_CMD -m pip install --user --find-links "$WHEELS_DIR" --no-index python-docx
    $PYTHON_CMD -m pip install --user --find-links "$WHEELS_DIR" --no-index docx2shelf

    if [ $? -ne 0 ]; then
        echo "❌ Individual installation also failed"
        exit 1
    fi
fi

# Verify installation
echo "🔍 Verifying installation..."
if command -v docx2shelf &> /dev/null; then
    echo "✅ Installation successful!"
    docx2shelf --version
else
    echo "⚠️  Installation completed but docx2shelf not found on PATH"
    echo "You may need to restart your terminal or add ~/.local/bin to PATH"
fi

echo
echo "Installation completed!"
'''


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Create offline installer for docx2shelf")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--dev", action="store_true", help="Include development dependencies")

    args = parser.parse_args()

    builder = OfflineInstallerBuilder(args.output)

    try:
        installer_path = builder.create_installer(include_dev_deps=args.dev)
        print(f"\n🎉 Offline installer created successfully!")
        print(f"📦 Package: {installer_path}")
        print(f"📁 Size: {installer_path.stat().st_size // 1024 // 1024} MB")
        print("\nTo use the offline installer:")
        print("1. Extract the zip file")
        print("2. Run install_offline.bat (Windows) or install_offline.sh (Unix)")
        print("3. Or run: python scripts/install_offline.py")

    except Exception as e:
        print(f"❌ Failed to create offline installer: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())