"""Quality, diagnostics, and validation command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse


def run_checklist(args: argparse.Namespace) -> int:
    """Run publishing store compatibility checklists."""
    import json
    from pathlib import Path

    from ..metadata import EpubMetadata, parse_kv_file
    from ..quality import format_checklist_report, get_checker, run_all_checklists

    # Load metadata
    metadata = None
    if args.epub_path:
        epub_path = Path(args.epub_path)
        if not epub_path.exists():
            print(f"Error: EPUB file not found: {epub_path}")
            return 1

        # Try to load metadata from EPUB
        try:
            from ..metadata import load_metadata_from_epub

            metadata = load_metadata_from_epub(epub_path)
        except Exception as e:
            print(f"Warning: Could not load metadata from EPUB: {e}")
    elif args.metadata_file:
        metadata_file = Path(args.metadata_file)
        if not metadata_file.exists():
            print(f"Error: Metadata file not found: {metadata_file}")
            return 1

        try:
            kv_dict = parse_kv_file(metadata_file)
            metadata = EpubMetadata.from_dict(kv_dict)
        except Exception as e:
            print(f"Error parsing metadata: {e}")
            return 1

    if not metadata:
        print("Error: No metadata provided. Use --epub-path or --metadata-file")
        return 1

    # Run checklists
    try:
        if args.store:
            # Run specific store checklist
            checker = get_checker(args.store)
            if not checker:
                print(f"Error: Unknown store '{args.store}'")
                print("Available: kdp, apple, kobo, googleplay, all")
                return 1

            results = checker.check(metadata)

            if args.json:
                print(json.dumps(results.to_dict(), indent=2))
            else:
                print(format_checklist_report(results))

            return 0 if results.passed else 1
        else:
            # Run all checklists
            all_results = run_all_checklists(metadata)

            if args.json:
                output = {store: result.to_dict() for store, result in all_results.items()}
                print(json.dumps(output, indent=2))
            else:
                for store_name, result in all_results.items():
                    print(f"\n{'=' * 60}")
                    print(f"{store_name.upper()} CHECKLIST")
                    print("=" * 60)
                    print(format_checklist_report(result))

            # Return error if any failed
            any_failed = any(not result.passed for result in all_results.values())
            return 1 if any_failed else 0

    except Exception as e:
        print(f"Error running checklist: {e}")
        return 1


def run_quality_assessment(args: argparse.Namespace) -> int:
    """Run comprehensive quality assessment on EPUB."""
    import json
    from pathlib import Path

    epub_path = Path(args.epub_path)

    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_path}")
        return 1

    print(f"Running quality assessment on: {epub_path.name}\n")

    all_results = {}
    has_errors = False

    # Quality scoring (if not skipped)
    if not getattr(args, "skip_quality_scoring", False):
        try:
            print("[1/4] Quality Scoring...")
            from ..quality import analyze_epub_quality

            quality_results = analyze_epub_quality(epub_path)
            all_results["quality"] = quality_results

            if not args.json:
                print(f"  Overall Score: {quality_results['overall_score']}/100")
                print(
                    f"  Grade: {quality_results['grade']} ({quality_results['grade_description']})"
                )

                # Show category scores
                print("\n  Category Scores:")
                for category, data in quality_results["categories"].items():
                    score = data["score"]
                    status = "✓" if score >= 70 else "⚠" if score >= 50 else "✗"
                    print(f"    {status} {category.title()}: {score}/100")

                # Show issues if any
                if quality_results.get("issues"):
                    print("\n  Issues Found:")
                    for issue in quality_results["issues"][:5]:  # Show first 5
                        severity = issue["severity"].upper()
                        print(f"    [{severity}] {issue['category']}: {issue['message']}")
                    if len(quality_results["issues"]) > 5:
                        remaining = len(quality_results["issues"]) - 5
                        print(f"    ... and {remaining} more issue(s)")

            if quality_results["overall_score"] < 70:
                has_errors = True

        except Exception as e:
            print(f"  Error during quality scoring: {e}")
            has_errors = True

    # Accessibility audit (if not skipped)
    if not getattr(args, "skip_accessibility", False):
        try:
            print("\n[2/4] Accessibility Audit...")
            from ..quality import audit_epub_accessibility

            accessibility_results = audit_epub_accessibility(epub_path)
            all_results["accessibility"] = accessibility_results

            if not args.json:
                wcag_level = accessibility_results.get("wcag_level", "N/A")
                compliance = accessibility_results.get("compliance_percentage", 0)

                print(f"  WCAG Level: {wcag_level}")
                print(f"  Compliance: {compliance}%")

                # Show critical issues
                critical = [
                    i for i in accessibility_results.get("issues", []) if i["severity"] == "error"
                ]
                if critical:
                    print(f"\n  Critical Issues ({len(critical)}):")
                    for issue in critical[:3]:
                        print(f"    ✗ {issue['criterion']}: {issue['message']}")
                    if len(critical) > 3:
                        print(f"    ... and {len(critical) - 3} more")

            if compliance < 80:
                has_errors = True

        except Exception as e:
            print(f"  Error during accessibility audit: {e}")
            has_errors = True

    # EPUB validation (if not skipped)
    if not getattr(args, "skip_epub_validation", False):
        try:
            print("\n[3/4] EPUB Validation...")
            from ..quality import validate_epub

            validation_results = validate_epub(epub_path)
            all_results["epub_validation"] = validation_results

            if not args.json:
                is_valid = validation_results.get("valid", False)
                status = "✓ Valid" if is_valid else "✗ Invalid"
                print(f"  Status: {status}")

                errors = validation_results.get("errors", [])
                warnings = validation_results.get("warnings", [])

                if errors:
                    print(f"\n  Errors ({len(errors)}):")
                    for error in errors[:3]:
                        print(f"    ✗ {error}")
                    if len(errors) > 3:
                        print(f"    ... and {len(errors) - 3} more")

                if warnings:
                    print(f"\n  Warnings ({len(warnings)}):")
                    for warning in warnings[:3]:
                        print(f"    ⚠ {warning}")
                    if len(warnings) > 3:
                        print(f"    ... and {len(warnings) - 3} more")

            if not is_valid:
                has_errors = True

        except Exception as e:
            print(f"  Error during EPUB validation: {e}")
            has_errors = True

    # Content validation (if not skipped)
    if not getattr(args, "skip_content_validation", False):
        try:
            print("\n[4/4] Content Validation...")
            from ..quality import validate_content_quality

            content_results = validate_content_quality(epub_path)
            all_results["content"] = content_results

            if not args.json:
                issues = content_results.get("issues", [])
                suggestions = content_results.get("suggestions", [])

                if issues:
                    print(f"\n  Issues ({len(issues)}):")
                    for issue in issues[:3]:
                        print(f"    ⚠ {issue}")
                    if len(issues) > 3:
                        print(f"    ... and {len(issues) - 3} more")

                if suggestions:
                    print(f"\n  Suggestions ({len(suggestions)}):")
                    for suggestion in suggestions[:3]:
                        print(f"    💡 {suggestion}")
                    if len(suggestions) > 3:
                        print(f"    ... and {len(suggestions) - 3} more")

                if not issues:
                    print("  ✓ No content issues found")

        except Exception as e:
            print(f"  Error during content validation: {e}")
            has_errors = True

    # Output results
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        print("\n" + "=" * 60)
        if has_errors:
            print("⚠ Quality assessment completed with issues")
            print("\nRecommendations:")
            print("  • Review and fix critical issues")
            print("  • Improve accessibility compliance")
            print("  • Validate EPUB structure")
            print("  • Run 'docx2shelf validate' for detailed checks")
        else:
            print("✓ Quality assessment passed!")
            print("\nYour EPUB meets professional publishing standards.")

    return 1 if has_errors else 0


def run_doctor(args: argparse.Namespace) -> int:
    """Run comprehensive environment diagnostics."""
    import platform
    import sys
    from pathlib import Path

    print("[DOCTOR] Docx2Shelf Environment Diagnostics")
    print("=" * 50)

    issues_found = 0
    warnings_found = 0

    # System Information
    print("\n[SYSTEM] System Information:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]} ({sys.executable})")

    # Python version check
    if sys.version_info >= (3, 11):
        print("  [OK] Python version is compatible")
    else:
        print(
            f"  [ERROR] Python {sys.version_info.major}.{sys.version_info.minor} is too old (requires 3.11+)"
        )
        issues_found += 1

    # Package installation check
    print("\n[PACKAGE] Docx2Shelf Installation:")
    try:
        from importlib import metadata

        version = metadata.version("docx2shelf")
        print(f"  [OK] Docx2Shelf {version} installed")
    except Exception as e:
        print(f"  [ERROR] Could not determine docx2shelf version: {e}")
        issues_found += 1

    # Dependencies check
    print("\n[DEPS] Core Dependencies:")
    core_deps = ["ebooklib", "lxml"]
    for dep in core_deps:
        try:
            __import__(dep)
            print(f"  [OK] {dep} available")
        except ImportError:
            print(f"  [ERROR] {dep} not available")
            issues_found += 1

    # Optional dependencies
    optional_deps = {
        "python-docx": "DOCX fallback support",
        "pypandoc": "Pandoc Python integration",
        "requests": "Update and marketplace features",
        "fastapi": "Enterprise API features",
        "sqlalchemy": "Enterprise database features",
    }

    print("\n[OPTIONAL] Optional Dependencies:")
    for dep, description in optional_deps.items():
        try:
            __import__(dep.replace("-", "_"))
            print(f"  [OK] {dep} - {description}")
        except ImportError:
            print(f"  [INFO] {dep} not installed - {description}")

    # Tools check (reuse existing tools_doctor)
    print("\n[TOOLS] External Tools:")
    from ..tools import tools_doctor

    tools_result = tools_doctor()
    if tools_result != 0:
        issues_found += tools_result

    # File system checks
    print("\n[FILESYSTEM] File System Access:")

    # Check write access to current directory
    try:
        test_file = Path("docx2shelf_test_write.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("  [OK] Current directory is writable")
    except Exception as e:
        print(f"  [WARNING] Current directory write test failed: {e}")
        warnings_found += 1

    # Check temp directory
    import tempfile

    try:
        temp_dir = Path(tempfile.gettempdir())
        print(f"  [OK] Temp directory: {temp_dir}")
        if temp_dir.exists() and temp_dir.is_dir():
            print("  [OK] Temp directory accessible")
        else:
            print("  [ERROR] Temp directory not accessible")
            issues_found += 1
    except Exception as e:
        print(f"  [ERROR] Temp directory check failed: {e}")
        issues_found += 1

    # Memory check
    print("\n[MEMORY] Memory Information:")
    try:
        import psutil

        memory = psutil.virtual_memory()
        print(f"  [OK] Available RAM: {memory.available // (1024**3)} GB")
        if memory.available < 1024**3:  # Less than 1GB
            print("  [WARNING] Low available memory may affect large document processing")
            warnings_found += 1
    except ImportError:
        print("  [INFO] psutil not available - cannot check memory")

    # Summary
    print("\n" + "=" * 50)
    total_issues = issues_found + warnings_found

    if issues_found == 0 and warnings_found == 0:
        print("[SUCCESS] All diagnostics passed! Environment is ready.")
        return 0
    elif issues_found == 0:
        print(f"[OK] Environment functional with {warnings_found} warning(s)")
        print("\nWarnings found but system should work normally.")
        return 0
    else:
        print(f"[ERROR] Found {issues_found} critical issue(s) and {warnings_found} warning(s)")
        print("\nRecommended actions:")
        if sys.version_info < (3, 11):
            print("- Update Python to version 3.11 or higher")
        print("- Install missing dependencies: pip install docx2shelf[all]")
        print("- Run 'docx2shelf tools install pandoc' for document conversion")
        print("- Run 'docx2shelf tools install epubcheck' for validation")
        return 1
