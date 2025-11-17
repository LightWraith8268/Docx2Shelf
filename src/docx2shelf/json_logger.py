from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONLogger:
    """Machine-readable JSON logger for CI/CD pipelines."""

    def __init__(self, output_file: Optional[Path] = None):
        self.output_file = output_file
        self.start_time = time.time()
        self.log_entries: List[Dict[str, Any]] = []
        self.build_info: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "version": self._get_version(),
            "status": "running",
            "input_file": None,
            "output_file": None,
            "metadata": {},
            "build_options": {},
            "warnings": [],
            "errors": [],
            "validation_results": {},
            "processing_time": None,
        }

    def _get_version(self) -> str:
        """Get current docx2shelf version."""
        try:
            import importlib.metadata

            return importlib.metadata.version("docx2shelf")
        except Exception:
            return "unknown"

    def log_build_start(
        self, input_file: Path, output_file: Path, metadata: Any, options: Any
    ) -> None:
        """Log build start information."""
        self.build_info.update(
            {
                "input_file": str(input_file),
                "output_file": str(output_file),
                "metadata": self._serialize_metadata(metadata),
                "build_options": self._serialize_options(options),
            }
        )

        self.log_event("build_start", {"input": str(input_file), "output": str(output_file)})

    def log_conversion_phase(self, phase: str, details: Optional[Dict] = None) -> None:
        """Log conversion phase information."""
        self.log_event("conversion_phase", {"phase": phase, "details": details or {}})

    def log_warning(
        self, message: str, category: str = "general", details: Optional[Dict] = None
    ) -> None:
        """Log a warning message."""
        warning = {
            "message": message,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.build_info["warnings"].append(warning)
        self.log_event("warning", warning)

    def log_error(
        self, message: str, category: str = "general", details: Optional[Dict] = None
    ) -> None:
        """Log an error message."""
        error = {
            "message": message,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.build_info["errors"].append(error)
        self.log_event("error", error)

    def log_validation_result(self, validator: str, result: Dict[str, Any]) -> None:
        """Log validation results (e.g., EPUBCheck)."""
        self.build_info["validation_results"][validator] = result
        self.log_event("validation", {"validator": validator, "result": result})

    def log_accessibility_check(self, results: Dict[str, Any]) -> None:
        """Log accessibility check results."""
        self.log_event("accessibility_check", results)

    def log_font_processing(self, results: Dict[str, Any]) -> None:
        """Log font processing results."""
        self.log_event("font_processing", results)

    def log_image_processing(self, results: Dict[str, Any]) -> None:
        """Log image processing results."""
        self.log_event("image_processing", results)

    def log_build_complete(self, success: bool, output_size: Optional[int] = None) -> None:
        """Log build completion."""
        end_time = time.time()
        processing_time = end_time - self.start_time

        self.build_info.update(
            {
                "status": "success" if success else "failed",
                "processing_time": processing_time,
                "end_time": datetime.now().isoformat(),
                "output_size_bytes": output_size,
            }
        )

        self.log_event(
            "build_complete",
            {
                "success": success,
                "processing_time": processing_time,
                "output_size_bytes": output_size,
            },
        )

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a generic event."""
        entry = {"timestamp": datetime.now().isoformat(), "event": event_type, "data": data}
        self.log_entries.append(entry)

    def get_summary(self) -> Dict[str, Any]:
        """Get build summary for JSON output."""
        return {
            "build_info": self.build_info,
            "events": self.log_entries,
            "summary": {
                "total_warnings": len(self.build_info["warnings"]),
                "total_errors": len(self.build_info["errors"]),
                "success": self.build_info["status"] == "success",
                "processing_time": self.build_info.get("processing_time", 0),
            },
        }

    def write_json_log(self, output_path: Optional[Path] = None) -> None:
        """Write JSON log to file."""
        target_path = output_path or self.output_file

        if not target_path:
            return

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(self.get_summary(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not write JSON log to {target_path}: {e}", file=sys.stderr)

    def _serialize_metadata(self, metadata) -> Dict[str, Any]:
        """Serialize metadata object to JSON-compatible dict."""
        if not metadata:
            return {}

        result = {}
        for attr in [
            "title",
            "author",
            "language",
            "publisher",
            "description",
            "isbn",
            "series",
            "series_index",
        ]:
            value = getattr(metadata, attr, None)
            if value is not None:
                result[attr] = (
                    str(value) if not isinstance(value, (str, int, float, bool)) else value
                )

        return result

    def _serialize_options(self, options) -> Dict[str, Any]:
        """Serialize build options to JSON-compatible dict."""
        if not options:
            return {}

        result = {}
        for attr in [
            "theme",
            "split_at",
            "epub_version",
            "image_format",
            "hyphenate",
            "justify",
            "toc_depth",
        ]:
            value = getattr(options, attr, None)
            if value is not None:
                result[attr] = (
                    str(value) if not isinstance(value, (str, int, float, bool)) else value
                )

        return result


# Global logger instance
_global_logger: Optional[JSONLogger] = None


def init_json_logger(output_file: Optional[Path] = None) -> JSONLogger:
    """Initialize global JSON logger."""
    global _global_logger
    _global_logger = JSONLogger(output_file)
    return _global_logger


def get_json_logger() -> Optional[JSONLogger]:
    """Get the global JSON logger instance."""
    return _global_logger


def finalize_json_logger() -> None:
    """Finalize and write JSON log."""
    if _global_logger:
        _global_logger.write_json_log()
