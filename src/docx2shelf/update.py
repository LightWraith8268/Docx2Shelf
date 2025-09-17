from __future__ import annotations

import json
import sys
import urllib.request
from importlib import metadata

REPO_URL = "https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest"


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
