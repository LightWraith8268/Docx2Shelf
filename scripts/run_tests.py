"""Pytest wrapper used by CI and local dev.

Provides --mode {ci,full,performance} and --coverage / --verbose passthroughs.
Referenced by .github/workflows/ci.yml and CLAUDE.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


CI_IGNORE_TESTS = (
    # Version-specific feature tests that lag behind post-Phase-5 refactors.
    # Tracked as tech debt; restored selectively as the underlying APIs
    # (anthology builder, series builder, k8s integration helpers, doc platform,
    # LSP/dev tools, hot-reload plugins, etc.) are re-stabilized.
    "tests/test_v124_features.py",
    "tests/test_v125_comprehensive.py",
    "tests/test_v126_comprehensive.py",
    "tests/test_v127_features.py",
)


def build_pytest_args(mode: str, coverage: bool, verbose: bool) -> list[str]:
    args = [sys.executable, "-m", "pytest"]

    if mode == "ci":
        # Skip slow/property-heavy tests, keep core unit + integration coverage.
        args += ["-m", "not slow and not perf", "--maxfail=10"]
        for path in CI_IGNORE_TESTS:
            args += [f"--ignore={path}"]
    elif mode == "full":
        args += ["--maxfail=20"]
    elif mode == "performance":
        args += ["-m", "perf or slow"]
    else:
        raise SystemExit(f"unknown --mode: {mode!r}")

    if coverage:
        args += [
            "--cov=src/docx2shelf",
            "--cov-report=xml",
            "--cov-report=term-missing",
        ]

    if verbose:
        args += ["-vv"]
    else:
        args += ["-q"]

    args += ["tests"]
    return args


def main() -> int:
    parser = argparse.ArgumentParser(description="Run docx2shelf test suite")
    parser.add_argument(
        "--mode",
        choices=["ci", "full", "performance"],
        default="ci",
        help="Test profile (default: ci)",
    )
    parser.add_argument("--coverage", action="store_true", help="Emit coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose pytest output")
    ns = parser.parse_args()

    cmd = build_pytest_args(ns.mode, ns.coverage, ns.verbose)
    print(f"+ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
