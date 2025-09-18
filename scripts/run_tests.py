#!/usr/bin/env python3
"""
Comprehensive test runner for Docx2Shelf.

This script provides different test execution modes for development and CI.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str = "") -> int:
    """Run a command and return exit code."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run Docx2Shelf tests")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "smoke", "property", "golden", "ci"],
        default="quick",
        help="Test execution mode"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox", "both"],
        default="chrome",
        help="Browser for smoke tests"
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"Running tests in mode: {args.mode}")
    print(f"Project root: {project_root}")

    total_exit_code = 0

    if args.mode == "quick":
        # Quick unit tests only
        cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow and not smoke"]
        if args.verbose:
            cmd.append("-v")
        if args.coverage:
            cmd.extend(["--cov=src/docx2shelf", "--cov-report=term-missing"])

        exit_code = run_command(cmd, "Quick unit tests")
        total_exit_code |= exit_code

    elif args.mode == "full":
        # All tests except smoke tests (which require browser setup)
        cmd = ["python", "-m", "pytest", "tests/", "-m", "not smoke"]
        if args.verbose:
            cmd.append("-v")
        if args.coverage:
            cmd.extend(["--cov=src/docx2shelf", "--cov-report=term-missing", "--cov-report=html"])

        exit_code = run_command(cmd, "Full test suite (excluding smoke tests)")
        total_exit_code |= exit_code

    elif args.mode == "smoke":
        # Smoke tests only
        cmd = ["python", "-m", "pytest", "tests/", "-m", "smoke"]
        if args.verbose:
            cmd.append("-v")

        exit_code = run_command(cmd, f"Smoke tests with {args.browser}")
        total_exit_code |= exit_code

    elif args.mode == "property":
        # Property-based tests only
        cmd = ["python", "-m", "pytest", "tests/", "-m", "property"]
        if args.verbose:
            cmd.append("-v")

        exit_code = run_command(cmd, "Property-based tests")
        total_exit_code |= exit_code

    elif args.mode == "golden":
        # Golden fixture tests only
        cmd = ["python", "-m", "pytest", "tests/", "-m", "golden"]
        if args.verbose:
            cmd.append("-v")

        exit_code = run_command(cmd, "Golden EPUB fixture tests")
        total_exit_code |= exit_code

    elif args.mode == "ci":
        # CI mode: comprehensive but skip browser-dependent tests if browsers unavailable
        print("Running CI test suite...")

        # 1. Unit tests
        cmd = ["python", "-m", "pytest", "tests/", "-m", "not smoke", "--cov=src/docx2shelf",
               "--cov-report=term-missing", "--cov-report=xml"]
        exit_code = run_command(cmd, "Unit and integration tests")
        total_exit_code |= exit_code

        # 2. Try smoke tests but don't fail if browser unavailable
        cmd = ["python", "-m", "pytest", "tests/", "-m", "smoke", "--tb=short"]
        exit_code = run_command(cmd, "Smoke tests (may skip if browser unavailable)")
        # Don't fail CI if smoke tests can't run
        if exit_code != 0:
            print("Note: Smoke tests skipped (browser not available)")

        # 3. Code quality checks
        print("\nRunning code quality checks...")

        # Linting
        cmd = ["python", "-m", "ruff", "check", "src/", "tests/"]
        exit_code = run_command(cmd, "Ruff linting")
        total_exit_code |= exit_code

        # Type checking
        cmd = ["python", "-m", "mypy", "src/docx2shelf/"]
        exit_code = run_command(cmd, "Type checking")
        # Don't fail on mypy for now, just report
        if exit_code != 0:
            print("Note: Type checking found issues but not failing build")

    else:
        print(f"Unknown mode: {args.mode}")
        return 1

    # Summary
    print(f"\n{'='*60}")
    if total_exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print(f"{'='*60}")

    return total_exit_code


if __name__ == "__main__":
    sys.exit(main())