"""CLI command handlers - extracted from cli.py for modularity."""

from .build import run_build
from .prompts import _prompt_missing
from .utils import (
    apply_metadata_dict,
    print_checklist,
    print_metadata_summary,
    read_document_content,
    run_preview_mode,
    save_metadata_to_file,
)

__all__ = [
    "run_build",
    "_prompt_missing",
    "apply_metadata_dict",
    "print_checklist",
    "print_metadata_summary",
    "read_document_content",
    "run_preview_mode",
    "save_metadata_to_file",
]
