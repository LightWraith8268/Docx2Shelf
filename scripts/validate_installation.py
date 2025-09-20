#!/usr/bin/env python3
"""
Docx2Shelf Installation Validator

This script validates that docx2shelf is properly installed and configured,
providing detailed diagnostics and recommendations for fixing issues.
"""

import sys
import subprocess
import os
import importlib
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import platform
import shutil


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, name: str, success: bool, message: str, details: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.message = message
        self.details = details or {}

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.name}: {self.message}"


class InstallationValidator:
    """Comprehensive installation validator for docx2shelf."""

    def __init__(self, verbose: bool = False):
        """Initialize the validator.

        Args:
            verbose: Whether to show detailed output
        """
        self.verbose = verbose
        self.results: List[ValidationResult] = []
        self.system_info = self._gather_system_info()

    def run_all_validations(self) -> bool:
        """Run all validation checks.

        Returns:
            True if all critical checks pass, False otherwise
        """
        print("🔍 Running comprehensive installation validation...")
        print("=" * 60)

        # System checks
        self._validate_python_environment()
        self._validate_package_management()

        # Installation checks
        self._validate_docx2shelf_installation()
        self._validate_dependencies()
        self._validate_command_availability()

        # Functionality checks
        self._validate_core_functionality()
        self._validate_optional_features()

        # Configuration checks
        self._validate_paths_and_permissions()

        # Generate report
        return self._generate_report()

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for diagnostics."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "python_prefix": sys.prefix,
            "working_directory": os.getcwd(),
            "user_home": str(Path.home()),
            "environment_variables": {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "USER": os.environ.get("USER", os.environ.get("USERNAME", "")),
            }
        }

    def _validate_python_environment(self):
        """Validate Python environment."""
        print("\n🐍 Python Environment")
        print("-" * 20)

        # Python version check
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            self.results.append(ValidationResult(
                "Python Version",
                True,
                f"Python {version.major}.{version.minor}.{version.micro} (compatible)",
                {"version": f"{version.major}.{version.minor}.{version.micro}"}
            ))
        else:
            self.results.append(ValidationResult(
                "Python Version",
                False,
                f"Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)",
                {"version": f"{version.major}.{version.minor}.{version.micro}"}
            ))

        print(self.results[-1])

        # Python executable accessibility
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    "Python Executable",
                    True,
                    f"Accessible at {sys.executable}"
                ))
            else:
                self.results.append(ValidationResult(
                    "Python Executable",
                    False,
                    f"Not accessible: {result.stderr}"
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Python Executable",
                False,
                f"Error running Python: {e}"
            ))

        print(self.results[-1])

    def _validate_package_management(self):
        """Validate package management tools."""
        print("\n📦 Package Management")
        print("-" * 20)

        # pip check
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    "pip",
                    True,
                    f"Available: {result.stdout.strip()}"
                ))
            else:
                self.results.append(ValidationResult(
                    "pip",
                    False,
                    "Not available or not working"
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                "pip",
                False,
                f"Error checking pip: {e}"
            ))

        print(self.results[-1])

        # pipx check (optional)
        try:
            result = subprocess.run(["pipx", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    "pipx",
                    True,
                    f"Available: {result.stdout.strip()}"
                ))
            else:
                self.results.append(ValidationResult(
                    "pipx",
                    True,  # Not critical
                    "Not available (optional)"
                ))
        except FileNotFoundError:
            self.results.append(ValidationResult(
                "pipx",
                True,  # Not critical
                "Not available (optional)"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "pipx",
                True,  # Not critical
                f"Error checking pipx: {e}"
            ))

        print(self.results[-1])

    def _validate_docx2shelf_installation(self):
        """Validate docx2shelf installation."""
        print("\n📚 Docx2Shelf Installation")
        print("-" * 30)

        # Check if docx2shelf module can be imported
        try:
            import docx2shelf
            version = getattr(docx2shelf, "__version__", "unknown")
            self.results.append(ValidationResult(
                "Module Import",
                True,
                f"Successfully imported docx2shelf v{version}",
                {"version": version, "location": docx2shelf.__file__}
            ))
        except ImportError as e:
            self.results.append(ValidationResult(
                "Module Import",
                False,
                f"Cannot import docx2shelf: {e}"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Module Import",
                False,
                f"Error importing docx2shelf: {e}"
            ))

        print(self.results[-1])

        # Check installation via pip
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", "docx2shelf"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse pip show output
                info = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()

                self.results.append(ValidationResult(
                    "pip Installation",
                    True,
                    f"Installed via pip: {info.get('Version', 'unknown')}",
                    {"pip_info": info}
                ))
            else:
                self.results.append(ValidationResult(
                    "pip Installation",
                    False,
                    "Not installed via pip"
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                "pip Installation",
                False,
                f"Error checking pip installation: {e}"
            ))

        print(self.results[-1])

    def _validate_dependencies(self):
        """Validate required dependencies."""
        print("\n🔗 Dependencies")
        print("-" * 15)

        dependencies = [
            ("ebooklib", "EPUB processing"),
            ("docx", "DOCX processing (python-docx)"),
        ]

        for dep_name, description in dependencies:
            try:
                module = importlib.import_module(dep_name)
                version = getattr(module, "__version__", "unknown")
                self.results.append(ValidationResult(
                    f"Dependency: {dep_name}",
                    True,
                    f"{description} available (v{version})",
                    {"version": version}
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    f"Dependency: {dep_name}",
                    False,
                    f"{description} not available"
                ))
            except Exception as e:
                self.results.append(ValidationResult(
                    f"Dependency: {dep_name}",
                    False,
                    f"Error checking {description}: {e}"
                ))

            print(self.results[-1])

    def _validate_command_availability(self):
        """Validate command-line availability."""
        print("\n⚡ Command Availability")
        print("-" * 22)

        # Check if docx2shelf command is available
        try:
            result = subprocess.run(["docx2shelf", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    "Command Line",
                    True,
                    f"docx2shelf command available: {result.stdout.strip()}"
                ))
            else:
                self.results.append(ValidationResult(
                    "Command Line",
                    False,
                    f"docx2shelf command failed: {result.stderr}"
                ))
        except FileNotFoundError:
            self.results.append(ValidationResult(
                "Command Line",
                False,
                "docx2shelf command not found on PATH"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Command Line",
                False,
                f"Error running docx2shelf command: {e}"
            ))

        print(self.results[-1])

        # Try to find the executable
        executable_path = shutil.which("docx2shelf")
        if executable_path:
            self.results.append(ValidationResult(
                "Executable Location",
                True,
                f"Found at: {executable_path}"
            ))
        else:
            self.results.append(ValidationResult(
                "Executable Location",
                False,
                "Executable not found on PATH"
            ))

        print(self.results[-1])

    def _validate_core_functionality(self):
        """Validate core functionality."""
        print("\n🎯 Core Functionality")
        print("-" * 20)

        # Test basic import and functionality
        try:
            from docx2shelf.metadata import EpubMetadata
            metadata = EpubMetadata(title="Test", author="Test Author", language="en")

            self.results.append(ValidationResult(
                "Metadata Creation",
                True,
                "Can create EPUB metadata objects"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Metadata Creation",
                False,
                f"Cannot create metadata: {e}"
            ))

        print(self.results[-1])

        # Test CLI module
        try:
            from docx2shelf.cli import main
            self.results.append(ValidationResult(
                "CLI Module",
                True,
                "CLI module can be imported"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "CLI Module",
                False,
                f"Cannot import CLI module: {e}"
            ))

        print(self.results[-1])

    def _validate_optional_features(self):
        """Validate optional features."""
        print("\n🎨 Optional Features")
        print("-" * 19)

        # Test wizard availability
        try:
            from docx2shelf.wizard import ConversionWizard
            self.results.append(ValidationResult(
                "Conversion Wizard",
                True,
                "Interactive wizard available"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Conversion Wizard",
                False,
                f"Wizard not available: {e}"
            ))

        print(self.results[-1])

        # Test theme editor availability
        try:
            from docx2shelf.theme_editor import ThemeEditor
            self.results.append(ValidationResult(
                "Theme Editor",
                True,
                "Advanced theme editor available"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Theme Editor",
                False,
                f"Theme editor not available: {e}"
            ))

        print(self.results[-1])

        # Test error handling system
        try:
            from docx2shelf.error_handler import EnhancedErrorHandler
            self.results.append(ValidationResult(
                "Error Handling",
                True,
                "Enhanced error handling available"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Error Handling",
                False,
                f"Error handling not available: {e}"
            ))

        print(self.results[-1])

    def _validate_paths_and_permissions(self):
        """Validate paths and permissions."""
        print("\n📁 Paths & Permissions")
        print("-" * 22)

        # Check write permissions for user directory
        user_dir = Path.home() / ".docx2shelf"
        try:
            user_dir.mkdir(exist_ok=True)
            test_file = user_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()

            self.results.append(ValidationResult(
                "User Directory",
                True,
                f"Can write to {user_dir}"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "User Directory",
                False,
                f"Cannot write to {user_dir}: {e}"
            ))

        print(self.results[-1])

        # Check temp directory access
        import tempfile
        try:
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(b"test")

            self.results.append(ValidationResult(
                "Temp Directory",
                True,
                "Can create temporary files"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Temp Directory",
                False,
                f"Cannot create temporary files: {e}"
            ))

        print(self.results[-1])

    def _generate_report(self) -> bool:
        """Generate validation report.

        Returns:
            True if all critical checks pass
        """
        print("\n" + "=" * 60)
        print("📋 VALIDATION REPORT")
        print("=" * 60)

        # Count results
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.success)
        failed_checks = total_checks - passed_checks

        print(f"Total checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {failed_checks}")
        print()

        # Show failed checks
        if failed_checks > 0:
            print("❌ FAILED CHECKS:")
            print("-" * 15)
            for result in self.results:
                if not result.success:
                    print(f"  • {result.name}: {result.message}")
            print()

        # Determine overall status
        critical_failures = [
            r for r in self.results
            if not r.success and r.name in [
                "Python Version", "Module Import", "Dependencies: ebooklib"
            ]
        ]

        success = len(critical_failures) == 0

        if success:
            print("✅ OVERALL STATUS: PASSED")
            print("   Docx2Shelf is properly installed and functional!")
        else:
            print("❌ OVERALL STATUS: FAILED")
            print("   Critical issues prevent proper functionality.")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 17)

        if failed_checks == 0:
            print("  • No issues found! Docx2Shelf is ready to use.")
            print("  • Try: docx2shelf wizard")
            print("  • Or: docx2shelf --help")
        else:
            self._generate_recommendations()

        # Save detailed report
        if self.verbose:
            self._save_detailed_report()

        return success

    def _generate_recommendations(self):
        """Generate specific recommendations based on failed checks."""
        for result in self.results:
            if not result.success:
                if result.name == "Python Version":
                    print("  • Upgrade Python to 3.11 or higher from https://python.org")

                elif result.name == "Module Import":
                    print("  • Reinstall docx2shelf: pip install --user docx2shelf[docx]")

                elif result.name == "Command Line":
                    print("  • Add Python Scripts directory to PATH")
                    print("  • Or restart your terminal/command prompt")

                elif "Dependency" in result.name:
                    dep_name = result.name.split(": ")[1]
                    if dep_name == "docx":
                        print("  • Install python-docx: pip install --user python-docx")
                    else:
                        print(f"  • Install {dep_name}: pip install --user {dep_name}")

                elif result.name == "User Directory":
                    print("  • Check file permissions in your home directory")
                    print("  • Or run as administrator/with sudo")

        print("  • Run this validator again after making changes")
        print("  • Contact support if issues persist")

    def _save_detailed_report(self):
        """Save detailed report to file."""
        report_data = {
            "timestamp": "2025-01-19",
            "system_info": self.system_info,
            "validation_results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }

        report_file = Path.home() / ".docx2shelf" / "validation_report.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate docx2shelf installation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show summary")

    args = parser.parse_args()

    if args.quiet and args.verbose:
        print("Error: Cannot use both --quiet and --verbose")
        return 1

    validator = InstallationValidator(verbose=args.verbose)

    try:
        success = validator.run_all_validations()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())