"""CLI command handlers - extracted from cli.py for modularity."""

from .ai import run_ai_alt_text, run_ai_command, run_ai_config, run_ai_genre, run_ai_metadata
from .batch import run_batch_mode, run_wizard
from .build import run_build
from .conversion import run_convert, run_init_metadata
from .enterprise import (
    run_enterprise,
    run_enterprise_api,
    run_enterprise_batch,
    run_enterprise_config,
    run_enterprise_jobs,
    run_enterprise_reports,
    run_enterprise_users,
    run_enterprise_webhooks,
)
from .plugins import run_connectors, run_plugins
from .prompts import _prompt_missing
from .quality import run_checklist, run_doctor, run_quality_assessment
from .themes import run_list_themes, run_preview_themes, run_theme_editor
from .tools import run_tools, run_update, run_validate
from .utils import (
    apply_metadata_dict,
    print_checklist,
    print_metadata_summary,
    read_document_content,
    run_preview_mode,
    save_metadata_to_file,
)

__all__ = [
    "run_batch_mode",
    "run_build",
    "run_convert",
    "run_enterprise",
    "run_enterprise_api",
    "run_enterprise_batch",
    "run_enterprise_config",
    "run_enterprise_jobs",
    "run_enterprise_reports",
    "run_enterprise_users",
    "run_enterprise_webhooks",
    "_prompt_missing",
    "run_ai_alt_text",
    "run_ai_command",
    "run_ai_config",
    "run_ai_genre",
    "run_ai_metadata",
    "run_checklist",
    "run_init_metadata",
    "run_list_themes",
    "run_connectors",
    "run_doctor",
    "run_plugins",
    "run_preview_themes",
    "run_quality_assessment",
    "run_theme_editor",
    "run_tools",
    "run_update",
    "run_validate",
    "run_wizard",
    "apply_metadata_dict",
    "print_checklist",
    "print_metadata_summary",
    "read_document_content",
    "run_preview_mode",
    "save_metadata_to_file",
]
