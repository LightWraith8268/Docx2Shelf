from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from importlib import metadata

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
                        [sys.executable, "-m", "pip", "install", "--upgrade", "git+https://github.com/LightWraith8268/Docx2Shelf.git"],
                        ["pipx", "upgrade", "docx2shelf"],
                        [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "git+https://github.com/LightWraith8268/Docx2Shelf.git"],
                    ]

                    for cmd in update_commands:
                        try:
                            print(f"Trying: {' '.join(cmd)}")
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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
    """Check for updates and notify the user if a new version is available."""
    try:
        current_version = metadata.version("docx2shelf")
    except metadata.PackageNotFoundError:
        # Package not installed, maybe running from source
        return

    try:
        with urllib.request.urlopen(REPO_URL) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                latest_version = data.get("tag_name", "").lstrip("v")

                if latest_version and latest_version > current_version:
                    print(
                        f"\n---\nUpdate available: {current_version} -> {latest_version}\n"
                        f"Run 'docx2shelf update' to upgrade.\n---",
                        file=sys.stderr,
                    )
    except Exception:
        # Silently fail on network errors or other issues
        pass
