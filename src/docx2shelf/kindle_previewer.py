"""
Kindle Previewer integration for EPUB preflight checking.

Automatically runs Kindle Previewer (if installed) to generate conversion
reports and identify potential issues with EPUB files on Kindle devices.
"""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class KindlePreviewerConfig:
    """Configuration for Kindle Previewer integration."""

    auto_detect_installation: bool = True
    custom_previewer_path: Optional[Path] = None
    generate_conversion_log: bool = True
    generate_screenshots: bool = False
    timeout_seconds: int = 300
    output_format: str = "KFX"  # KFX, AZW3, or MOBI
    device_type: str = "Kindle Oasis"  # Target device for preview


@dataclass
class PreviewerIssue:
    """Issue found by Kindle Previewer."""

    severity: str  # error, warning, info
    code: str
    message: str
    location: str = ""
    chapter: str = ""
    line_number: Optional[int] = None


@dataclass
class ConversionReport:
    """Kindle Previewer conversion report."""

    success: bool
    output_file: Optional[Path]
    log_file: Optional[Path]
    issues: List[PreviewerIssue]
    conversion_time: float
    file_size_original: int
    file_size_converted: Optional[int]
    metadata: Dict[str, Any]


class KindlePreviewerIntegration:
    """Integrates with Amazon Kindle Previewer for EPUB validation."""

    def __init__(self, config: Optional[KindlePreviewerConfig] = None):
        self.config = config or KindlePreviewerConfig()
        self.previewer_path: Optional[Path] = None
        self._detect_installation()

    def _detect_installation(self) -> None:
        """Detect Kindle Previewer installation."""
        if self.config.custom_previewer_path:
            if self.config.custom_previewer_path.exists():
                self.previewer_path = self.config.custom_previewer_path
                logger.info(f"Using custom Kindle Previewer: {self.previewer_path}")
                return
            else:
                logger.warning(
                    f"Custom Kindle Previewer path not found: {self.config.custom_previewer_path}"
                )

        if not self.config.auto_detect_installation:
            return

        # Common installation paths by platform
        system = platform.system().lower()

        if system == "windows":
            possible_paths = [
                Path(
                    r"C:\Program Files (x86)\Amazon\Kindle Previewer 3\lib\fc\bin\kindlepreviewer.exe"
                ),
                Path(r"C:\Program Files\Amazon\Kindle Previewer 3\lib\fc\bin\kindlepreviewer.exe"),
                Path.home()
                / "AppData"
                / "Local"
                / "Amazon"
                / "Kindle Previewer 3"
                / "lib"
                / "fc"
                / "bin"
                / "kindlepreviewer.exe",
            ]
        elif system == "darwin":  # macOS
            possible_paths = [
                Path("/Applications/Kindle Previewer 3.app/Contents/MacOS/Kindle Previewer 3"),
                Path.home()
                / "Applications"
                / "Kindle Previewer 3.app"
                / "Contents"
                / "MacOS"
                / "Kindle Previewer 3",
            ]
        else:  # Linux and others
            possible_paths = [
                Path.home()
                / ".local"
                / "share"
                / "Amazon"
                / "Kindle Previewer 3"
                / "lib"
                / "fc"
                / "bin"
                / "kindlepreviewer",
                Path("/opt/amazon/kindle-previewer-3/lib/fc/bin/kindlepreviewer"),
            ]

        # Try to find in PATH first
        try:
            result = shutil.which("kindlepreviewer")
            if result:
                self.previewer_path = Path(result)
                logger.info(f"Found Kindle Previewer in PATH: {self.previewer_path}")
                return
        except Exception:
            pass

        # Check common installation paths
        for path in possible_paths:
            if path.exists():
                self.previewer_path = path
                logger.info(f"Found Kindle Previewer: {self.previewer_path}")
                return

        logger.info(
            "Kindle Previewer not found. Install from https://kdp.amazon.com/en_US/help/topic/G202131170"
        )

    def is_available(self) -> bool:
        """Check if Kindle Previewer is available."""
        return self.previewer_path is not None and self.previewer_path.exists()

    def convert_epub(self, epub_path: Path, output_dir: Optional[Path] = None) -> ConversionReport:
        """
        Convert EPUB using Kindle Previewer and generate report.

        Args:
            epub_path: Path to EPUB file
            output_dir: Directory for output files (default: temp dir)

        Returns:
            ConversionReport with conversion results and issues
        """
        if not self.is_available():
            return ConversionReport(
                success=False,
                output_file=None,
                log_file=None,
                issues=[
                    PreviewerIssue(
                        severity="error",
                        code="KP_NOT_FOUND",
                        message="Kindle Previewer not found. Please install from Amazon KDP.",
                    )
                ],
                conversion_time=0.0,
                file_size_original=0,
                file_size_converted=None,
                metadata={},
            )

        if not epub_path.exists():
            return ConversionReport(
                success=False,
                output_file=None,
                log_file=None,
                issues=[
                    PreviewerIssue(
                        severity="error",
                        code="FILE_NOT_FOUND",
                        message=f"EPUB file not found: {epub_path}",
                    )
                ],
                conversion_time=0.0,
                file_size_original=0,
                file_size_converted=None,
                metadata={},
            )

        import time

        start_time = time.time()
        file_size_original = epub_path.stat().st_size

        # Setup output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="kindle_preview_"))
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Run Kindle Previewer conversion
            result = self._run_conversion(epub_path, output_dir)

            conversion_time = time.time() - start_time

            # Parse results
            issues = self._parse_conversion_log(result.get("log_file"))

            output_file = result.get("output_file")
            file_size_converted = (
                output_file.stat().st_size if output_file and output_file.exists() else None
            )

            return ConversionReport(
                success=result.get("success", False),
                output_file=output_file,
                log_file=result.get("log_file"),
                issues=issues,
                conversion_time=conversion_time,
                file_size_original=file_size_original,
                file_size_converted=file_size_converted,
                metadata=result.get("metadata", {}),
            )

        except Exception as e:
            logger.error(f"Kindle Previewer conversion failed: {e}")
            return ConversionReport(
                success=False,
                output_file=None,
                log_file=None,
                issues=[
                    PreviewerIssue(
                        severity="error",
                        code="CONVERSION_FAILED",
                        message=f"Conversion failed: {str(e)}",
                    )
                ],
                conversion_time=time.time() - start_time,
                file_size_original=file_size_original,
                file_size_converted=None,
                metadata={},
            )

    def _run_conversion(self, epub_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Run the actual Kindle Previewer conversion."""

        # Build command
        cmd = [
            str(self.previewer_path),
            str(epub_path),
            "-o",
            str(output_dir),
            "-f",
            self.config.output_format,
        ]

        if self.config.device_type:
            cmd.extend(["-d", self.config.device_type])

        if self.config.generate_conversion_log:
            cmd.append("-v")  # Verbose output

        logger.info(f"Running Kindle Previewer: {' '.join(cmd)}")

        try:
            # Run conversion
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=output_dir,
            )

            # Find output files
            output_file = self._find_converted_file(output_dir, epub_path.stem)
            log_file = self._find_log_file(output_dir, epub_path.stem)

            # Save stdout/stderr to log file if no log file found
            if not log_file and (process.stdout or process.stderr):
                log_file = output_dir / f"{epub_path.stem}_conversion.log"
                with open(log_file, "w", encoding="utf-8") as f:
                    if process.stdout:
                        f.write("=== STDOUT ===\n")
                        f.write(process.stdout)
                        f.write("\n")
                    if process.stderr:
                        f.write("=== STDERR ===\n")
                        f.write(process.stderr)
                        f.write("\n")

            success = process.returncode == 0 and output_file and output_file.exists()

            return {
                "success": success,
                "output_file": output_file,
                "log_file": log_file,
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "metadata": {
                    "command": " ".join(cmd),
                    "returncode": process.returncode,
                    "output_format": self.config.output_format,
                    "device_type": self.config.device_type,
                },
            }

        except subprocess.TimeoutExpired:
            raise Exception(f"Conversion timed out after {self.config.timeout_seconds} seconds")
        except FileNotFoundError:
            raise Exception(f"Kindle Previewer executable not found: {self.previewer_path}")

    def _find_converted_file(self, output_dir: Path, base_name: str) -> Optional[Path]:
        """Find the converted file in output directory."""

        # Common output file patterns
        extensions = {"KFX": [".kfx"], "AZW3": [".azw3"], "MOBI": [".mobi", ".azw"]}

        format_extensions = extensions.get(self.config.output_format, [".kfx", ".azw3", ".mobi"])

        for ext in format_extensions:
            candidate = output_dir / f"{base_name}{ext}"
            if candidate.exists():
                return candidate

        # Search recursively for any supported format
        for ext in [".kfx", ".azw3", ".mobi", ".azw"]:
            candidates = list(output_dir.rglob(f"*{ext}"))
            if candidates:
                return candidates[0]

        return None

    def _find_log_file(self, output_dir: Path, base_name: str) -> Optional[Path]:
        """Find the conversion log file."""

        log_patterns = [
            f"{base_name}.log",
            f"{base_name}_conversion.log",
            "conversion.log",
            "previewer.log",
        ]

        for pattern in log_patterns:
            candidate = output_dir / pattern
            if candidate.exists():
                return candidate

        # Search for any .log files
        log_files = list(output_dir.rglob("*.log"))
        if log_files:
            return log_files[0]

        return None

    def _parse_conversion_log(self, log_file: Optional[Path]) -> List[PreviewerIssue]:
        """Parse Kindle Previewer log file for issues."""
        issues = []

        if not log_file or not log_file.exists():
            return issues

        try:
            log_content = log_file.read_text(encoding="utf-8", errors="ignore")

            # Parse different types of log messages
            issues.extend(self._parse_error_messages(log_content))
            issues.extend(self._parse_warning_messages(log_content))
            issues.extend(self._parse_info_messages(log_content))

        except Exception as e:
            logger.warning(f"Failed to parse log file {log_file}: {e}")
            issues.append(
                PreviewerIssue(
                    severity="warning",
                    code="LOG_PARSE_ERROR",
                    message=f"Could not parse log file: {e}",
                )
            )

        return issues

    def _parse_error_messages(self, log_content: str) -> List[PreviewerIssue]:
        """Parse error messages from log content."""
        issues = []

        # Common Kindle Previewer error patterns
        error_patterns = [
            (r"ERROR:\s*(.+)", "CONVERSION_ERROR"),
            (r"FATAL:\s*(.+)", "FATAL_ERROR"),
            (r"Failed to convert:\s*(.+)", "CONVERSION_FAILED"),
            (r"Invalid EPUB:\s*(.+)", "INVALID_EPUB"),
            (r"CSS Error:\s*(.+)", "CSS_ERROR"),
            (r"Image Error:\s*(.+)", "IMAGE_ERROR"),
        ]

        import re

        for pattern, code in error_patterns:
            for match in re.finditer(pattern, log_content, re.IGNORECASE | re.MULTILINE):
                issues.append(
                    PreviewerIssue(
                        severity="error",
                        code=code,
                        message=match.group(1).strip(),
                        location=self._extract_location(match.group(0)),
                    )
                )

        return issues

    def _parse_warning_messages(self, log_content: str) -> List[PreviewerIssue]:
        """Parse warning messages from log content."""
        issues = []

        warning_patterns = [
            (r"WARNING:\s*(.+)", "CONVERSION_WARNING"),
            (r"WARN:\s*(.+)", "CONVERSION_WARNING"),
            (r"Unsupported:\s*(.+)", "UNSUPPORTED_FEATURE"),
            (r"Deprecated:\s*(.+)", "DEPRECATED_FEATURE"),
            (r"Font Warning:\s*(.+)", "FONT_WARNING"),
            (r"CSS Warning:\s*(.+)", "CSS_WARNING"),
        ]

        import re

        for pattern, code in warning_patterns:
            for match in re.finditer(pattern, log_content, re.IGNORECASE | re.MULTILINE):
                issues.append(
                    PreviewerIssue(
                        severity="warning",
                        code=code,
                        message=match.group(1).strip(),
                        location=self._extract_location(match.group(0)),
                    )
                )

        return issues

    def _parse_info_messages(self, log_content: str) -> List[PreviewerIssue]:
        """Parse informational messages from log content."""
        issues = []

        info_patterns = [
            (r"INFO:\s*(.+)", "INFO"),
            (r"Note:\s*(.+)", "NOTE"),
            (r"Converted:\s*(.+)", "CONVERSION_SUCCESS"),
        ]

        import re

        for pattern, code in info_patterns:
            for match in re.finditer(pattern, log_content, re.IGNORECASE | re.MULTILINE):
                issues.append(
                    PreviewerIssue(
                        severity="info",
                        code=code,
                        message=match.group(1).strip(),
                        location=self._extract_location(match.group(0)),
                    )
                )

        return issues

    def _extract_location(self, log_line: str) -> str:
        """Extract file location from log line."""
        import re

        # Common location patterns
        location_patterns = [
            r"in file (.+\.x?html?)",
            r"at (.+\.x?html?):\d+",
            r"(.+\.x?html?):\d+:\d+",
            r"chapter (\d+)",
            r"page (\d+)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, log_line, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def generate_preflight_report(self, epub_path: Path, output_path: Path) -> None:
        """Generate a comprehensive preflight report."""

        logger.info(f"Generating Kindle Previewer preflight report for {epub_path}")

        # Run conversion
        report = self.convert_epub(epub_path)

        # Generate HTML report
        html_report = self._generate_html_report(epub_path, report)

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_report, encoding="utf-8")

        logger.info(f"Preflight report saved to {output_path}")

    def _generate_html_report(self, epub_path: Path, report: ConversionReport) -> str:
        """Generate HTML preflight report."""

        # Count issues by severity
        error_count = len([i for i in report.issues if i.severity == "error"])
        warning_count = len([i for i in report.issues if i.severity == "warning"])
        info_count = len([i for i in report.issues if i.severity == "info"])

        # Determine overall status
        status = (
            "success"
            if report.success and error_count == 0
            else "warning" if error_count == 0 else "error"
        )
        status_text = (
            "✅ Passed"
            if status == "success"
            else "⚠️ Passed with warnings" if status == "warning" else "❌ Failed"
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kindle Previewer Preflight Report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #ddd; padding-bottom: 1rem; margin-bottom: 2rem; }}
        .status {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem; }}
        .status.success {{ color: #28a745; }}
        .status.warning {{ color: #ffc107; }}
        .status.error {{ color: #dc3545; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .metric {{ background: #f8f9fa; padding: 1rem; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; color: #495057; }}
        .metric-label {{ color: #6c757d; }}
        .issues {{ margin-top: 2rem; }}
        .issue {{ border: 1px solid #dee2e6; border-radius: 6px; margin-bottom: 1rem; }}
        .issue-header {{ padding: 0.75rem 1rem; font-weight: bold; }}
        .issue-body {{ padding: 0 1rem 1rem; }}
        .issue.error .issue-header {{ background-color: #f8d7da; color: #721c24; }}
        .issue.warning .issue-header {{ background-color: #fff3cd; color: #856404; }}
        .issue.info .issue-header {{ background-color: #d1ecf1; color: #0c5460; }}
        .metadata {{ background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-top: 2rem; }}
        .no-issues {{ text-align: center; color: #6c757d; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Kindle Previewer Preflight Report</h1>
        <div class="status {status}">{status_text}</div>
        <div><strong>File:</strong> {epub_path.name}</div>
        <div><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">{error_count}</div>
            <div class="metric-label">Errors</div>
        </div>
        <div class="metric">
            <div class="metric-value">{warning_count}</div>
            <div class="metric-label">Warnings</div>
        </div>
        <div class="metric">
            <div class="metric-value">{info_count}</div>
            <div class="metric-label">Info</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.conversion_time:.1f}s</div>
            <div class="metric-label">Conversion Time</div>
        </div>
    </div>

    <div class="issues">
        <h2>Issues ({len(report.issues)})</h2>
"""

        if report.issues:
            for issue in report.issues:
                html += f"""
        <div class="issue {issue.severity}">
            <div class="issue-header">
                {issue.severity.upper()}: {issue.code}
            </div>
            <div class="issue-body">
                <div>{issue.message}</div>
                {f'<div><strong>Location:</strong> {issue.location}</div>' if issue.location else ''}
            </div>
        </div>
"""
        else:
            html += '<div class="no-issues">No issues found! 🎉</div>'

        html += f"""
    </div>

    <div class="metadata">
        <h3>Conversion Details</h3>
        <div><strong>Original Size:</strong> {report.file_size_original:,} bytes</div>
        {f'<div><strong>Converted Size:</strong> {report.file_size_converted:,} bytes</div>' if report.file_size_converted else ''}
        <div><strong>Success:</strong> {'Yes' if report.success else 'No'}</div>
        {f'<div><strong>Output File:</strong> {report.output_file.name}</div>' if report.output_file else ''}
        {f'<div><strong>Log File:</strong> {report.log_file.name}</div>' if report.log_file else ''}
    </div>
</body>
</html>"""

        return html


def run_kindle_preflight(
    epub_path: Path,
    output_dir: Optional[Path] = None,
    config: Optional[KindlePreviewerConfig] = None,
) -> ConversionReport:
    """
    Run Kindle Previewer preflight check on EPUB file.

    Args:
        epub_path: Path to EPUB file
        output_dir: Directory for output files
        config: Kindle Previewer configuration

    Returns:
        ConversionReport with results
    """
    integration = KindlePreviewerIntegration(config)
    return integration.convert_epub(epub_path, output_dir)
