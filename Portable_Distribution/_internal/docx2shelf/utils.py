from __future__ import annotations

from pathlib import Path
from typing import Dict
import platformdirs


def prompt(question: str, default: str | None = None, allow_empty: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{question}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if val or allow_empty:
            return val
        print("Please enter a value.")


def prompt_choice(question: str, choices: list[str], default: str | None = None) -> str:
    while True:
        val = prompt(f"{question} ({'/'.join(choices)})", default=default)
        if val in choices:
            return val
        print(f"Choose one of: {', '.join(choices)}")


def prompt_bool(question: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        val = input(f"{question} [{d}]: ").strip().lower()
        if not val:
            return default
        if val in {"y", "yes"}:
            return True
        if val in {"n", "no"}:
            return False
        print("Enter y or n.")


def prompt_select(question: str, options: list[str], default_index: int = 1) -> str:
    """Numeric picker for a list of options. Returns selected option string.

    - Shows options as 1..N with their labels.
    - default_index is 1-based; clamped to valid range.
    """
    if not options:
        raise ValueError("prompt_select requires at least one option")
    di = max(1, min(default_index, len(options)))
    print(question)
    for i, label in enumerate(options, start=1):
        print(f"  {i}) {label}")
    while True:
        raw = input(f"Select [{di}]: ").strip()
        if not raw:
            return options[di - 1]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1]
        print(f"Enter a number 1..{len(options)} or press Enter for default.")


def sanitize_filename(name: str) -> str:
    return name.replace("/", "-").replace("\\", "-").replace(":", "-").replace("\0", "").strip()


def parse_kv_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path or not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        sep = ":" if ":" in line else ("=" if "=" in line else None)
        if not sep:
            continue
        k, v = line.split(sep, 1)
        k = k.strip().lower()
        v = v.strip().strip('"').strip("'")
        data[k] = v
    return data


def get_user_data_dir() -> Path:
    """Get the user data directory for docx2shelf."""
    return Path(platformdirs.user_data_dir("docx2shelf", "Docx2Shelf"))
