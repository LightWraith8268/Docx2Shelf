#!/usr/bin/env python3
"""
Test runner for golden-file regression tests.

This script helps run and manage golden-file tests for DOCX conversion validation.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_golden_tests(test_type="all", verbose=False):
    """Run golden-file tests."""
    print("[TEST] Running Golden-File Tests")
    print("=" * 50)

    test_files = []

    if test_type == "all":
        test_files = ["tests/test_golden_epubs.py"]
    elif test_type == "structure":
        test_files = ["tests/test_golden_epubs.py::TestGoldenEPUBFixtures"]
    elif test_type == "regression":
        test_files = ["tests/test_golden_epubs.py::TestGoldenRegressionTesting"]
    else:
        test_files = [f"tests/test_golden_epubs.py::TestGoldenEPUBFixtures::test_{test_type}_document_structure"]

    cmd = ["python", "-m", "pytest"] + test_files

    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.extend(["-v"])

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def generate_fixtures():
    """Generate golden fixtures."""
    print("[BUILD] Generating Golden Fixtures")
    print("=" * 50)

    try:
        result = subprocess.run([
            "python", "scripts/generate_golden_fixtures.py"
        ], check=False)
        return result.returncode
    except Exception as e:
        print(f"Error generating fixtures: {e}")
        return 1


def validate_fixtures():
    """Validate existing golden fixtures."""
    print("[VALIDATE] Validating Golden Fixtures")
    print("=" * 50)

    fixtures_dir = Path("tests/fixtures/golden_epubs")

    if not fixtures_dir.exists():
        print("[ERROR] Fixtures directory not found")
        return 1

    golden_epubs = list(fixtures_dir.rglob("*_golden.epub"))

    if not golden_epubs:
        print("[ERROR] No golden EPUB fixtures found")
        print("[TIP] Run: python scripts/test_golden_files.py --generate")
        return 1

    print(f"[INFO] Found {len(golden_epubs)} golden EPUB fixtures:")
    for epub in golden_epubs:
        try:
            rel_path = epub.relative_to(Path.cwd())
            print(f"  - {rel_path} ({epub.stat().st_size // 1024} KB)")
        except ValueError:
            print(f"  - {epub} ({epub.stat().st_size // 1024} KB)")

    # Check for corresponding structure files
    missing_structures = []
    for epub in golden_epubs:
        structure_file = epub.parent / "expected_structure.json"
        if not structure_file.exists():
            missing_structures.append(structure_file)

    if missing_structures:
        print(f"\n[WARN] Missing {len(missing_structures)} structure files:")
        for structure in missing_structures:
            print(f"  - {structure.relative_to(Path.cwd())}")
        print("[TIP] Regenerate fixtures to create structure files")

    return 0


def cleanup_fixtures():
    """Clean up generated fixtures."""
    print("[CLEAN] Cleaning Up Golden Fixtures")
    print("=" * 50)

    fixtures_dir = Path("tests/fixtures/golden_epubs")

    if not fixtures_dir.exists():
        print("[INFO] No fixtures directory found")
        return 0

    # Find all generated files
    generated_files = []
    for pattern in ["*_golden.epub", "expected_structure.json", "*.html"]:
        generated_files.extend(fixtures_dir.rglob(pattern))

    if not generated_files:
        print("[INFO] No generated fixtures found")
        return 0

    print(f"[CLEAN] Found {len(generated_files)} generated files:")
    for file in generated_files:
        rel_path = file.relative_to(Path.cwd())
        print(f"  - {rel_path}")

    response = input("\nDelete these files? [y/N]: ").strip().lower()
    if response in ['y', 'yes']:
        for file in generated_files:
            try:
                file.unlink()
                print(f"[PASS] Deleted {file.name}")
            except Exception as e:
                print(f"[FAIL] Failed to delete {file.name}: {e}")

        # Remove empty directories
        for test_dir in fixtures_dir.iterdir():
            if test_dir.is_dir() and not any(test_dir.iterdir()):
                test_dir.rmdir()
                print(f"[PASS] Removed empty directory {test_dir.name}")

        print("[SUCCESS] Cleanup complete")
    else:
        print("[CANCEL] Cleanup cancelled")

    return 0


def status_report():
    """Generate status report for golden-file testing."""
    print("[STATUS] Golden-File Testing Status Report")
    print("=" * 50)

    fixtures_dir = Path("tests/fixtures/golden_epubs")

    # Check test categories
    test_categories = ["simple", "footnotes", "tables", "poetry", "images"]

    print("\n[CATEGORIES] Test Categories:")
    for category in test_categories:
        category_dir = fixtures_dir / category
        source_files = []
        golden_epub = None
        structure_file = None

        if category_dir.exists():
            # Check for source files
            for ext in [".docx", ".html"]:
                source_file = category_dir / f"{category}{ext}"
                if source_file.exists():
                    source_files.append(source_file)

            # Check for golden EPUB
            golden_epub = category_dir / f"{category}_golden.epub"
            if not golden_epub.exists():
                golden_epub = None

            # Check for structure file
            structure_file = category_dir / "expected_structure.json"
            if not structure_file.exists():
                structure_file = None

        # Status indicators
        source_status = "[PASS]" if source_files else "[FAIL]"
        golden_status = "[PASS]" if golden_epub else "[FAIL]"
        structure_status = "[PASS]" if structure_file else "[FAIL]"

        print(f"  {category:>10}: Source {source_status} | Golden {golden_status} | Structure {structure_status}")

    # Test file status
    test_file = Path("tests/test_golden_epubs.py")
    if test_file.exists():
        print(f"\n[TEST] Test file: [PASS] {test_file}")
    else:
        print(f"\n[TEST] Test file: [FAIL] {test_file}")

    # Generator script status
    generator_script = Path("scripts/generate_golden_fixtures.py")
    if generator_script.exists():
        print(f"[BUILD] Generator: [PASS] {generator_script}")
    else:
        print(f"[BUILD] Generator: [FAIL] {generator_script}")

    print("\n[NEXT] Next steps:")
    if not any((fixtures_dir / cat / f"{cat}_golden.epub").exists() for cat in test_categories):
        print("  1. Generate fixtures: python scripts/test_golden_files.py --generate")
    print("  2. Run structure tests: python scripts/test_golden_files.py --test structure")
    print("  3. Run regression tests: python scripts/test_golden_files.py --test regression")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Golden-file test runner for docx2shelf")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", choices=["all", "structure", "regression", "simple", "footnotes", "tables", "poetry", "images"],
                      help="Run golden-file tests")
    group.add_argument("--generate", action="store_true", help="Generate golden fixtures")
    group.add_argument("--validate", action="store_true", help="Validate existing fixtures")
    group.add_argument("--cleanup", action="store_true", help="Clean up generated fixtures")
    group.add_argument("--status", action="store_true", help="Show status report")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Check if we're in the right directory
    if not Path("tests/test_golden_epubs.py").exists():
        print("[ERROR] Must be run from docx2shelf root directory")
        return 1

    if args.test:
        return run_golden_tests(args.test, args.verbose)
    elif args.generate:
        return generate_fixtures()
    elif args.validate:
        return validate_fixtures()
    elif args.cleanup:
        return cleanup_fixtures()
    elif args.status:
        return status_report()

    return 0


if __name__ == "__main__":
    sys.exit(main())