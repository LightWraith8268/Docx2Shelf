"""Rewrite the `version = "..."` line in pyproject.toml.

Reads target from env var NEW_VERSION.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def main() -> int:
    new_version = os.environ.get("NEW_VERSION", "").strip()
    if not new_version:
        raise SystemExit("NEW_VERSION env var is required")

    path = Path("pyproject.toml")
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(?m)^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        text,
        count=1,
    )
    if count == 0:
        raise SystemExit("No version line found in pyproject.toml")
    path.write_text(updated, encoding="utf-8")
    print(f"Set pyproject.toml version to {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
