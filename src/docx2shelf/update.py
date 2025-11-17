from __future__ import annotations

import json
import platform
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from importlib import metadata
from pathlib import Path

REPO_URL = "https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest"


def perform_update():
    """Perform the actual update of docx2shelf to the latest version."""
    try:
        current_version = metadata.version("docx2shelf")
        print(f"Current version: {current_version}")
    except metadata.PackageNotFoundError:
        print("docx2shelf is not installed via pip. Cannot update automatically.")
        return False

    try:
        with urllib.request.urlopen(REPO_URL) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                latest_version = data.get("tag_name", "").lstrip("v")

                if latest_version and latest_version > current_version:
                    print(f"Updating from {current_version} to {latest_version}...")

                    # Try different update methods based on how it was installed
                    update_commands = [
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "git+https://github.com/LightWraith8268/Docx2Shelf.git",
                        ],
                        ["pipx", "upgrade", "docx2shelf"],
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--user",
                            "--upgrade",
                            "git+https://github.com/LightWraith8268/Docx2Shelf.git",
                        ],
                    ]

                    for cmd in update_commands:
                        try:
                            print(f"Trying: {' '.join(cmd)}")
                            result = subprocess.run(
                                cmd, capture_output=True, text=True, timeout=300
                            )
                            if result.returncode == 0:
                                print("Update successful!")
                                return True
                            else:
                                print(f"Command failed: {result.stderr}")
                        except (subprocess.TimeoutExpired, FileNotFoundError):
                            continue

                    print("All update methods failed.")
                    print("Please update manually using the installation script:")
                    print("  Windows: install.bat")
                    print("  macOS/Linux: install.sh")
                    return False

                else:
                    print(f"Already up to date (version {current_version})")
                    return True

            else:
                print("Failed to check for updates")
                return False

    except Exception as e:
        print(f"Update failed: {e}")
        return False


def check_for_updates():
    """Check for updates and return structured data for GUI/CLI use."""
    try:
        from .version import get_version

        current_version = get_version()
    except Exception:
        try:
            current_version = metadata.version("docx2shelf")
        except metadata.PackageNotFoundError:
            current_version = "unknown"

    try:
        with urllib.request.urlopen(REPO_URL, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                latest_version = data.get("tag_name", "").lstrip("v")

                if latest_version and _version_compare(latest_version, current_version) > 0:
                    # Get the appropriate download asset for this platform
                    download_url, installer_name = _get_platform_download_url(
                        data.get("assets", [])
                    )

                    return {
                        "update_available": True,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "download_url": download_url,
                        "installer_name": installer_name,
                        "changelog": data.get("body", "No changelog available."),
                        "release_url": data.get("html_url", ""),
                    }
                else:
                    return {
                        "update_available": False,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "message": "You are running the latest version.",
                    }
            else:
                return {
                    "update_available": False,
                    "error": f"Failed to check for updates (HTTP {response.status})",
                }
    except Exception as e:
        return {"update_available": False, "error": f"Failed to check for updates: {str(e)}"}


def _version_compare(version1: str, version2: str) -> int:
    """Compare two version strings. Returns 1 if version1 > version2, -1 if version1 < version2, 0 if equal."""
    try:
        # Split versions into parts and convert to integers for comparison
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]

        # Pad shorter version with zeros
        max_length = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_length - len(v1_parts)))
        v2_parts.extend([0] * (max_length - len(v2_parts)))

        # Compare each part
        for v1_part, v2_part in zip(v1_parts, v2_parts):
            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1

        return 0
    except (ValueError, AttributeError):
        # Fallback to string comparison
        return 1 if version1 > version2 else (-1 if version1 < version2 else 0)


def _get_platform_download_url(assets: list) -> tuple[str, str]:
    """Get the appropriate download URL and installer name for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Define platform-specific asset patterns with preference order
    # Prefer installers over portable versions - updated to match actual asset names
    platform_patterns = {
        "windows": [
            ("installer", ["docx2shelf-setup.exe", "setup.exe"]),  # Windows installer (preferred)
            (
                "portable",
                ["docx2shelf-windows-portable.zip", "windows-portable.zip"],
            ),  # Windows portable
        ],
        "darwin": [
            (
                "installer",
                ["docx2shelf-installer.dmg", "installer.dmg"],
            ),  # macOS DMG installer (preferred)
            ("portable", ["docx2shelf-macos-portable.zip", "macos-portable.zip"]),  # macOS portable
        ],
        "linux": [
            (
                "installer",
                ["docx2shelf-x86_64.appimage", "x86_64.appimage"],
            ),  # Linux AppImage (preferred)
            (
                "portable",
                ["docx2shelf-linux-portable.tar.gz", "linux-portable.tar.gz"],
            ),  # Linux portable
        ],
    }

    # Find the best matching asset for current platform
    if system in platform_patterns:
        for asset_type, patterns in platform_patterns[system]:
            for asset in assets:
                asset_name = asset.get("name", "").lower()
                download_url = asset.get("browser_download_url", "")

                # Check if any pattern matches this asset
                for pattern in patterns:
                    if pattern in asset_name:
                        return download_url, asset.get("name", "installer")

    # Fallback: look for any platform-specific file
    fallback_patterns = {
        "windows": [".exe", "windows", "win"],
        "darwin": [".dmg", "macos", "darwin"],
        "linux": [".appimage", "linux"],
    }

    if system in fallback_patterns:
        for asset in assets:
            asset_name = asset.get("name", "").lower()
            download_url = asset.get("browser_download_url", "")

            if any(pattern in asset_name for pattern in fallback_patterns[system]):
                return download_url, asset.get("name", "installer")

    # Generic fallback: any zip or executable file
    for asset in assets:
        asset_name = asset.get("name", "").lower()
        download_url = asset.get("browser_download_url", "")

        if any(ext in asset_name for ext in [".zip", ".exe", ".dmg", ".appimage"]):
            return download_url, asset.get("name", "installer")

    # Last resort: return first asset
    if assets:
        first_asset = assets[0]
        return first_asset.get("browser_download_url", ""), first_asset.get("name", "installer")

    return "", "No installer available"


def download_and_install_update(download_url: str, installer_name: str) -> bool:
    """Download and install the update."""
    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            installer_path = temp_path / installer_name

            # Download the installer
            print(f"Downloading {installer_name}...")
            with urllib.request.urlopen(download_url) as response:
                if response.status == 200:
                    with open(installer_path, "wb") as f:
                        f.write(response.read())
                else:
                    print(f"Failed to download installer (HTTP {response.status})")
                    return False

            # Install based on file type and platform
            system = platform.system().lower()

            if installer_name.lower().endswith(".exe"):
                # Windows installer - run silently if possible
                try:
                    # Try silent installation first
                    result = subprocess.run(
                        [str(installer_path), "/S"], capture_output=True, timeout=300
                    )
                    if result.returncode == 0:
                        return True

                    # Fall back to interactive installation
                    subprocess.run([str(installer_path)], check=True)
                    return True
                except subprocess.TimeoutExpired:
                    print("Installation timed out")
                    return False

            elif installer_name.lower().endswith(".dmg"):
                # macOS DMG - mount and install
                try:
                    # Mount the DMG
                    mount_result = subprocess.run(
                        ["hdiutil", "attach", str(installer_path)], capture_output=True, text=True
                    )
                    if mount_result.returncode != 0:
                        # Fall back to opening DMG
                        subprocess.run(["open", str(installer_path)], check=True)
                        return True

                    # Parse mount point
                    mount_point = None
                    for line in mount_result.stdout.splitlines():
                        if "/Volumes/" in line:
                            mount_point = line.split("\t")[-1].strip()
                            break

                    if mount_point:
                        # Look for app bundle to copy
                        for item in Path(mount_point).iterdir():
                            if item.suffix == ".app":
                                # Copy to Applications
                                apps_dir = Path("/Applications")
                                if apps_dir.exists():
                                    subprocess.run(["cp", "-R", str(item), str(apps_dir)])
                                    # Unmount DMG
                                    subprocess.run(["hdiutil", "detach", mount_point])
                                    return True

                        # Unmount if no app found
                        subprocess.run(["hdiutil", "detach", mount_point])

                    # Fall back to opening DMG
                    subprocess.run(["open", str(installer_path)], check=True)
                    return True

                except Exception:
                    # Fall back to opening DMG
                    subprocess.run(["open", str(installer_path)], check=True)
                    return True

            elif installer_name.lower().endswith(".appimage"):
                # Linux AppImage - make executable and run
                try:
                    # Make executable
                    subprocess.run(["chmod", "+x", str(installer_path)], check=True)

                    # Move to a persistent location
                    home_bin = Path.home() / "bin"
                    home_bin.mkdir(exist_ok=True)

                    final_path = home_bin / "Docx2Shelf"
                    subprocess.run(["cp", str(installer_path), str(final_path)], check=True)
                    subprocess.run(["chmod", "+x", str(final_path)], check=True)

                    print(f"AppImage installed to {final_path}")
                    return True

                except Exception:
                    # Fall back to making executable in temp location
                    subprocess.run(["chmod", "+x", str(installer_path)], check=True)
                    print(f"AppImage ready at {installer_path}")
                    return True

            elif installer_name.lower().endswith((".zip", ".tar.gz")):
                # Portable versions - extract and handle
                extract_path = temp_path / "extracted"

                if installer_name.lower().endswith(".zip"):
                    with zipfile.ZipFile(installer_path, "r") as zip_file:
                        zip_file.extractall(extract_path)
                elif installer_name.lower().endswith(".tar.gz"):
                    import tarfile

                    with tarfile.open(installer_path, "r:gz") as tar_file:
                        tar_file.extractall(extract_path)

                # For portable versions, just inform user about extraction
                print(f"Portable version extracted to {extract_path}")
                print("Please copy the extracted files to your preferred location.")

                # Try to open the extraction folder
                try:
                    if system == "windows":
                        subprocess.run(["explorer", str(extract_path)])
                    elif system == "darwin":
                        subprocess.run(["open", str(extract_path)])
                    else:
                        subprocess.run(["xdg-open", str(extract_path)])
                except Exception:
                    pass

                return True

            else:
                # Unknown file type - try platform-specific opener
                try:
                    if system == "windows":
                        subprocess.run([str(installer_path)], check=True)
                    elif system == "darwin":
                        subprocess.run(["open", str(installer_path)], check=True)
                    else:
                        subprocess.run(["xdg-open", str(installer_path)], check=True)
                    return True
                except Exception:
                    print(f"Downloaded to {installer_path}. Please install manually.")
                    return False

    except Exception as e:
        print(f"Failed to install update: {e}")
        return False


def check_for_updates_cli():
    """CLI version of update checking with print output."""
    result = check_for_updates()

    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        return

    if result.get("update_available"):
        print(
            f"\n---\nUpdate available: {result['current_version']} -> {result['latest_version']}\n"
            f"Run 'docx2shelf update' to upgrade.\n---",
            file=sys.stderr,
        )
    else:
        print(f"Already up to date (version {result.get('current_version', 'unknown')})")


# Legacy function name for backwards compatibility
def check_for_updates_legacy():
    """Legacy function for backwards compatibility."""
    check_for_updates_cli()
