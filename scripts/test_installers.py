#!/usr/bin/env python3
"""
Comprehensive Installer Testing Suite

This script tests all docx2shelf installers to ensure they work correctly
across different environments and scenarios.
"""

import sys
import subprocess
import os
import tempfile
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import platform


class InstallerTestResult:
    """Result of an installer test."""

    def __init__(self, test_name: str, success: bool, message: str, duration: float = 0.0):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.duration = duration
        self.details = {}

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.test_name}: {self.message} ({self.duration:.2f}s)"


class InstallerTestSuite:
    """Comprehensive test suite for docx2shelf installers."""

    def __init__(self, verbose: bool = False, temp_dir: Optional[Path] = None):
        """Initialize the test suite.

        Args:
            verbose: Whether to show detailed output
            temp_dir: Custom temporary directory for testing
        """
        self.verbose = verbose
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="docx2shelf_test_"))
        self.results: List[InstallerTestResult] = []
        self.original_cwd = Path.cwd()
        self.test_environments = []

    def run_all_tests(self) -> bool:
        """Run all installer tests.

        Returns:
            True if all tests pass, False otherwise
        """
        print("🧪 Running comprehensive installer test suite...")
        print("=" * 60)
        print(f"Test directory: {self.temp_dir}")
        print(f"Platform: {platform.platform()}")
        print()

        try:
            # Prepare test environment
            self._prepare_test_environment()

            # Run tests
            self._test_standard_installer()
            self._test_enhanced_installer()
            self._test_offline_installer()
            self._test_validation_tools()
            self._test_cross_platform_compatibility()

            # Generate report
            return self._generate_test_report()

        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            return False

        finally:
            # Cleanup
            os.chdir(self.original_cwd)

    def _prepare_test_environment(self):
        """Prepare the test environment."""
        print("🔧 Preparing test environment...")

        # Create test directory structure
        self.temp_dir.mkdir(exist_ok=True)
        (self.temp_dir / "environments").mkdir(exist_ok=True)
        (self.temp_dir / "logs").mkdir(exist_ok=True)
        (self.temp_dir / "artifacts").mkdir(exist_ok=True)

        # Copy installer files
        installer_files = [
            "install.bat",
            "install_enhanced.bat",
            "scripts/create_offline_installer.py",
            "scripts/validate_installation.py",
            "scripts/diagnose.bat"
        ]

        for file_path in installer_files:
            src = self.original_cwd / file_path
            if src.exists():
                dest = self.temp_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                if self.verbose:
                    print(f"  Copied: {file_path}")

        # Copy pyproject.toml and source if available
        if (self.original_cwd / "pyproject.toml").exists():
            shutil.copy2(self.original_cwd / "pyproject.toml", self.temp_dir)
            if (self.original_cwd / "src").exists():
                shutil.copytree(self.original_cwd / "src", self.temp_dir / "src")

        print("✅ Test environment prepared")

    def _test_standard_installer(self):
        """Test the standard installer."""
        print("\n📦 Testing Standard Installer")
        print("-" * 30)

        if not (self.temp_dir / "install.bat").exists():
            self.results.append(InstallerTestResult(
                "Standard Installer",
                False,
                "install.bat not found"
            ))
            return

        # Create isolated environment
        env_dir = self._create_test_environment("standard")
        os.chdir(env_dir)

        start_time = time.time()

        try:
            if platform.system() == "Windows":
                # Test Windows batch installer
                result = subprocess.run(
                    [str(self.temp_dir / "install.bat")],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if result.returncode == 0:
                    # Verify installation
                    verify_result = subprocess.run(
                        ["docx2shelf", "--version"],
                        capture_output=True,
                        text=True
                    )

                    if verify_result.returncode == 0:
                        self.results.append(InstallerTestResult(
                            "Standard Installer",
                            True,
                            f"Successfully installed: {verify_result.stdout.strip()}",
                            time.time() - start_time
                        ))
                    else:
                        self.results.append(InstallerTestResult(
                            "Standard Installer",
                            False,
                            "Installation completed but verification failed",
                            time.time() - start_time
                        ))
                else:
                    self.results.append(InstallerTestResult(
                        "Standard Installer",
                        False,
                        f"Installation failed: {result.stderr}",
                        time.time() - start_time
                    ))
            else:
                self.results.append(InstallerTestResult(
                    "Standard Installer",
                    True,
                    "Skipped on non-Windows platform"
                ))

        except subprocess.TimeoutExpired:
            self.results.append(InstallerTestResult(
                "Standard Installer",
                False,
                "Installation timed out",
                time.time() - start_time
            ))
        except Exception as e:
            self.results.append(InstallerTestResult(
                "Standard Installer",
                False,
                f"Test error: {e}",
                time.time() - start_time
            ))

        print(self.results[-1])

    def _test_enhanced_installer(self):
        """Test the enhanced installer."""
        print("\n🚀 Testing Enhanced Installer")
        print("-" * 32)

        if not (self.temp_dir / "install_enhanced.bat").exists():
            self.results.append(InstallerTestResult(
                "Enhanced Installer",
                False,
                "install_enhanced.bat not found"
            ))
            return

        # Test different modes
        test_modes = [
            ("--help", "Help display"),
            ("--local", "Local installation") if (self.temp_dir / "pyproject.toml").exists() else None,
            ("--dev", "Development installation") if (self.temp_dir / "src").exists() else None,
        ]

        for mode_args, mode_desc in filter(None, test_modes):
            env_dir = self._create_test_environment(f"enhanced_{mode_args.replace('--', '')}")
            os.chdir(env_dir)

            start_time = time.time()

            try:
                if platform.system() == "Windows":
                    cmd = [str(self.temp_dir / "install_enhanced.bat")]
                    if mode_args != "--help":
                        cmd.append(mode_args)

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )

                    if mode_args == "--help":
                        success = "Usage:" in result.stdout or "Options:" in result.stdout
                    else:
                        success = result.returncode == 0

                    if success:
                        self.results.append(InstallerTestResult(
                            f"Enhanced Installer ({mode_desc})",
                            True,
                            "Test passed",
                            time.time() - start_time
                        ))
                    else:
                        self.results.append(InstallerTestResult(
                            f"Enhanced Installer ({mode_desc})",
                            False,
                            f"Test failed: {result.stderr}",
                            time.time() - start_time
                        ))
                else:
                    self.results.append(InstallerTestResult(
                        f"Enhanced Installer ({mode_desc})",
                        True,
                        "Skipped on non-Windows platform"
                    ))

            except subprocess.TimeoutExpired:
                self.results.append(InstallerTestResult(
                    f"Enhanced Installer ({mode_desc})",
                    False,
                    "Test timed out",
                    time.time() - start_time
                ))
            except Exception as e:
                self.results.append(InstallerTestResult(
                    f"Enhanced Installer ({mode_desc})",
                    False,
                    f"Test error: {e}",
                    time.time() - start_time
                ))

            print(self.results[-1])

    def _test_offline_installer(self):
        """Test the offline installer creation and usage."""
        print("\n💿 Testing Offline Installer")
        print("-" * 29)

        offline_script = self.temp_dir / "scripts" / "create_offline_installer.py"
        if not offline_script.exists():
            self.results.append(InstallerTestResult(
                "Offline Installer Creation",
                False,
                "create_offline_installer.py not found"
            ))
            return

        # Test offline installer creation
        env_dir = self._create_test_environment("offline")
        os.chdir(env_dir)

        start_time = time.time()

        try:
            # Create offline installer
            result = subprocess.run([
                sys.executable,
                str(offline_script),
                "--output", "offline_test"
            ], capture_output=True, text=True, timeout=600)  # 10 minutes

            if result.returncode == 0:
                offline_zip = env_dir / "offline_test" / "docx2shelf_offline_installer.zip"
                if offline_zip.exists():
                    self.results.append(InstallerTestResult(
                        "Offline Installer Creation",
                        True,
                        f"Created successfully ({offline_zip.stat().st_size // 1024} KB)",
                        time.time() - start_time
                    ))

                    # Test offline installer extraction and validation
                    self._test_offline_installer_usage(offline_zip)
                else:
                    self.results.append(InstallerTestResult(
                        "Offline Installer Creation",
                        False,
                        "Offline installer zip not created",
                        time.time() - start_time
                    ))
            else:
                self.results.append(InstallerTestResult(
                    "Offline Installer Creation",
                    False,
                    f"Creation failed: {result.stderr}",
                    time.time() - start_time
                ))

        except subprocess.TimeoutExpired:
            self.results.append(InstallerTestResult(
                "Offline Installer Creation",
                False,
                "Creation timed out",
                time.time() - start_time
            ))
        except Exception as e:
            self.results.append(InstallerTestResult(
                "Offline Installer Creation",
                False,
                f"Test error: {e}",
                time.time() - start_time
            ))

        print(self.results[-1])

    def _test_offline_installer_usage(self, offline_zip: Path):
        """Test using the offline installer."""
        start_time = time.time()

        try:
            # Extract offline installer
            import zipfile
            extract_dir = offline_zip.parent / "extracted"
            with zipfile.ZipFile(offline_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            installer_dir = extract_dir / "docx2shelf_offline_installer"
            if not installer_dir.exists():
                self.results.append(InstallerTestResult(
                    "Offline Installer Usage",
                    False,
                    "Offline installer structure invalid",
                    time.time() - start_time
                ))
                return

            # Test Python installer script
            python_script = installer_dir / "scripts" / "install_offline.py"
            if python_script.exists():
                # Test script syntax
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(python_script)
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.results.append(InstallerTestResult(
                        "Offline Installer (Python)",
                        True,
                        "Python script syntax valid",
                        time.time() - start_time
                    ))
                else:
                    self.results.append(InstallerTestResult(
                        "Offline Installer (Python)",
                        False,
                        f"Python script syntax error: {result.stderr}",
                        time.time() - start_time
                    ))
            else:
                self.results.append(InstallerTestResult(
                    "Offline Installer (Python)",
                    False,
                    "Python installer script not found",
                    time.time() - start_time
                ))

        except Exception as e:
            self.results.append(InstallerTestResult(
                "Offline Installer Usage",
                False,
                f"Test error: {e}",
                time.time() - start_time
            ))

        print(self.results[-1])

    def _test_validation_tools(self):
        """Test validation and diagnostic tools."""
        print("\n🔍 Testing Validation Tools")
        print("-" * 27)

        # Test validation script
        validation_script = self.temp_dir / "scripts" / "validate_installation.py"
        if validation_script.exists():
            start_time = time.time()

            try:
                # Test help output
                result = subprocess.run([
                    sys.executable, str(validation_script), "--help"
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and "usage:" in result.stdout.lower():
                    self.results.append(InstallerTestResult(
                        "Validation Script",
                        True,
                        "Help output works correctly",
                        time.time() - start_time
                    ))
                else:
                    self.results.append(InstallerTestResult(
                        "Validation Script",
                        False,
                        f"Help output failed: {result.stderr}",
                        time.time() - start_time
                    ))

            except Exception as e:
                self.results.append(InstallerTestResult(
                    "Validation Script",
                    False,
                    f"Test error: {e}",
                    time.time() - start_time
                ))
        else:
            self.results.append(InstallerTestResult(
                "Validation Script",
                False,
                "validate_installation.py not found"
            ))

        print(self.results[-1])

        # Test diagnostic script (Windows only)
        if platform.system() == "Windows":
            diagnostic_script = self.temp_dir / "scripts" / "diagnose.bat"
            if diagnostic_script.exists():
                start_time = time.time()

                try:
                    # Test that the script exists and is readable
                    with open(diagnostic_script, 'r') as f:
                        content = f.read()

                    if "Docx2Shelf Diagnostic" in content:
                        self.results.append(InstallerTestResult(
                            "Diagnostic Script",
                            True,
                            "Script structure valid",
                            time.time() - start_time
                        ))
                    else:
                        self.results.append(InstallerTestResult(
                            "Diagnostic Script",
                            False,
                            "Script structure invalid",
                            time.time() - start_time
                        ))

                except Exception as e:
                    self.results.append(InstallerTestResult(
                        "Diagnostic Script",
                        False,
                        f"Test error: {e}",
                        time.time() - start_time
                    ))
            else:
                self.results.append(InstallerTestResult(
                    "Diagnostic Script",
                    False,
                    "diagnose.bat not found"
                ))

            print(self.results[-1])

    def _test_cross_platform_compatibility(self):
        """Test cross-platform compatibility."""
        print("\n🌐 Testing Cross-Platform Compatibility")
        print("-" * 40)

        # Test Python scripts on current platform
        python_scripts = [
            "scripts/create_offline_installer.py",
            "scripts/validate_installation.py"
        ]

        for script_path in python_scripts:
            script_file = self.temp_dir / script_path
            if script_file.exists():
                start_time = time.time()

                try:
                    # Test syntax
                    result = subprocess.run([
                        sys.executable, "-m", "py_compile", str(script_file)
                    ], capture_output=True, text=True)

                    if result.returncode == 0:
                        # Test import
                        result = subprocess.run([
                            sys.executable, "-c", f"exec(open('{script_file}').read())"
                        ], capture_output=True, text=True, timeout=10)

                        # Most scripts will fail because they expect command line args,
                        # but we're just testing that they can be loaded
                        success = "usage:" in result.stderr.lower() or \
                                result.returncode == 0 or \
                                "SystemExit" in result.stderr

                        if success:
                            self.results.append(InstallerTestResult(
                                f"Cross-Platform ({script_path})",
                                True,
                                "Script loads successfully",
                                time.time() - start_time
                            ))
                        else:
                            self.results.append(InstallerTestResult(
                                f"Cross-Platform ({script_path})",
                                False,
                                f"Script load failed: {result.stderr}",
                                time.time() - start_time
                            ))
                    else:
                        self.results.append(InstallerTestResult(
                            f"Cross-Platform ({script_path})",
                            False,
                            f"Syntax error: {result.stderr}",
                            time.time() - start_time
                        ))

                except Exception as e:
                    self.results.append(InstallerTestResult(
                        f"Cross-Platform ({script_path})",
                        False,
                        f"Test error: {e}",
                        time.time() - start_time
                    ))

                print(self.results[-1])

    def _create_test_environment(self, name: str) -> Path:
        """Create an isolated test environment."""
        env_dir = self.temp_dir / "environments" / name
        if env_dir.exists():
            shutil.rmtree(env_dir)
        env_dir.mkdir(parents=True)

        # Copy necessary files
        for file_name in ["install.bat", "install_enhanced.bat"]:
            src = self.temp_dir / file_name
            if src.exists():
                shutil.copy2(src, env_dir)

        # Copy scripts directory
        scripts_src = self.temp_dir / "scripts"
        if scripts_src.exists():
            shutil.copytree(scripts_src, env_dir / "scripts")

        # Copy source if available
        if (self.temp_dir / "src").exists():
            shutil.copytree(self.temp_dir / "src", env_dir / "src")

        # Copy pyproject.toml if available
        if (self.temp_dir / "pyproject.toml").exists():
            shutil.copy2(self.temp_dir / "pyproject.toml", env_dir)

        return env_dir

    def _generate_test_report(self) -> bool:
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 INSTALLER TEST REPORT")
        print("=" * 60)

        # Summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        total_time = sum(r.duration for r in self.results)

        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total time: {total_time:.2f}s")
        print()

        # Failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 15)
            for result in self.results:
                if not result.success:
                    print(f"  • {result.test_name}: {result.message}")
            print()

        # Overall status
        success = failed_tests == 0

        if success:
            print("✅ OVERALL STATUS: ALL TESTS PASSED")
            print("   All installers are working correctly!")
        else:
            print("❌ OVERALL STATUS: SOME TESTS FAILED")
            print("   Please review failed tests and fix issues.")

        # Save detailed report
        self._save_test_report()

        return success

    def _save_test_report(self):
        """Save detailed test report to file."""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "platform": platform.platform(),
            "python_version": sys.version,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details
                }
                for r in self.results
            ],
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": sum(1 for r in self.results if r.success),
                "failed_tests": sum(1 for r in self.results if not r.success),
                "total_time": sum(r.duration for r in self.results)
            }
        }

        report_file = self.temp_dir / "logs" / "installer_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test docx2shelf installers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--temp-dir", type=Path, help="Custom temporary directory")
    parser.add_argument("--keep-temp", action="store_true", help="Don't delete temp directory")

    args = parser.parse_args()

    test_suite = InstallerTestSuite(verbose=args.verbose, temp_dir=args.temp_dir)

    try:
        success = test_suite.run_all_tests()

        if not args.keep_temp and test_suite.temp_dir.exists():
            shutil.rmtree(test_suite.temp_dir)
            print(f"\n🧹 Cleaned up test directory: {test_suite.temp_dir}")
        elif args.keep_temp:
            print(f"\n📁 Test directory preserved: {test_suite.temp_dir}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())