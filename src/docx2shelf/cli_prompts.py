"""Interactive metadata prompts - extracted from cli.py _prompt_missing().

This module will contain the refactored prompting logic, organized by metadata type:
- prompt_title(): Title prompting
- prompt_author(): Author prompting
- prompt_series(): Series metadata prompting
- prompt_publication_info(): Publisher, pubdate prompting
- prompt_classification(): Subjects, keywords prompting
- prompt_advanced(): ISBN, language, UUID prompting
"""
from __future__ import annotations

import argparse
from typing import Optional


def prompt_missing_metadata(args: argparse.Namespace) -> argparse.Namespace:
    """Interactively prompt for missing required metadata.

    TODO Phase 4: Extract prompting logic from cli.py lines 978-1220
    This is a placeholder that will be replaced with the full implementation.
    """
    print("Prompting placeholder - to be implemented in Phase 4")
    return args
