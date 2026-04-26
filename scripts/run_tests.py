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


CI_IGNORE_TESTS: tuple[str, ...] = ()
# All v12x version-specific feature tests are now collected. The previous
# generation of refactor-stale exclusions (v124-v127) has been restored by
# realigning anthology / series / web builder / docs / dev-tools APIs with
# their tests and tolerating Windows-only sqlite teardown locks.


def build_pytest_args(mode: str, coverage: bool, verbose: bool) -> list[str]:
    args = [sys.executable, "-m", "pytest"]

    # Hard cap each individual test at 120s so a hung browser/inotify call
    # cannot stall the whole suite (CI runners give no useful feedback when
    # a job hangs for 60+ minutes). Requires pytest-timeout (declared in
    # [project.optional-dependencies].dev).
    args += ["--timeout=120", "--timeout-method=thread"]

    if mode == "ci":
        # Skip slow/property-heavy tests, keep core unit + integration coverage.
        args += ["-m", "not slow and not perf", "--maxfail=10"]
    elif mode == "full":
        args += ["--maxfail=20"]
    elif mode == "performance":
        args += ["-m", "perf or slow"]
    else:
        raise SystemExit(f"unknown --mode: {mode!r}")

    # Phase-5-stale tests are unconditionally ignored; reintroduce when
    # underlying APIs are restored.
    for path in CI_IGNORE_TESTS:
        args += [f"--ignore={path}"]

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
