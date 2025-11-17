# CLI Refactoring - Phase 1 Quick Start Guide

**Status**: Ready to Execute
**Time Required**: 30 minutes
**Risk Level**: Very Low (just creating structure)

---

## Overview

This guide provides step-by-step instructions for Phase 1 of the CLI refactoring: creating the module structure and verifying imports work correctly.

**No existing code is modified in Phase 1** - we only create new files with placeholder code.

---

## Step-by-Step Instructions

### Step 1: Create cli_args Package (5 minutes)

```bash
# Create the directory
mkdir -p src/docx2shelf/cli_args

# Create __init__.py with base structure
cat > src/docx2shelf/cli_args/__init__.py << 'EOF'
"""Modular argument parser for docx2shelf CLI.

This package splits the monolithic _arg_parser() function into focused modules:
- build.py: Build command arguments
- tools.py: Tools management arguments
- ai.py: AI command arguments
- enterprise.py: Enterprise command arguments
- plugins.py: Plugin management arguments
- connectors.py: Connector arguments
- themes.py: Theme-related arguments
- misc.py: Miscellaneous commands (wizard, batch, etc.)
"""
from __future__ import annotations

import argparse


def _arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands.

    This is a placeholder that will be populated in Phase 2.
    For now, it just creates the base parser.
    """
    from ..cli import get_version_string

    p = argparse.ArgumentParser(
        prog="docx2shelf",
        description="Convert a DOCX manuscript into a valid EPUB 3 (offline)",
    )

    p.add_argument(
        "--version",
        action="version",
        version=get_version_string(),
        help="Show version information and exit",
    )

    sub = p.add_subparsers(dest="command", required=False)

    # TODO Phase 2: Add all subcommand parsers here
    # add_build_parser(sub)
    # add_tools_parser(sub)
    # add_ai_parser(sub)
    # add_enterprise_parser(sub)
    # add_plugins_parser(sub)
    # add_connectors_parser(sub)
    # add_themes_parser(sub)
    # add_misc_parsers(sub)

    return p


__all__ = ["_arg_parser"]
EOF
```

### Step 2: Create Module Files (10 minutes)

```bash
# Create build.py
cat > src/docx2shelf/cli_args/build.py << 'EOF'
"""Build command argument parser."""
from __future__ import annotations

import argparse


def add_build_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add build subcommand and its arguments.

    TODO Phase 2: Extract all build arguments from cli.py lines 64-259
    """
    b = subparsers.add_parser("build", help="Build an EPUB from inputs")
    # TODO: Add all build arguments here
    pass
EOF

# Create tools.py
cat > src/docx2shelf/cli_args/tools.py << 'EOF'
"""Tools command argument parser."""
from __future__ import annotations

import argparse


def add_tools_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add tools subcommand and its arguments.

    TODO Phase 2: Extract all tools arguments from cli.py lines 357-385
    """
    t = subparsers.add_parser("tools", help="Manage optional tools")
    # TODO: Add all tools arguments here
    pass
EOF

# Create ai.py
cat > src/docx2shelf/cli_args/ai.py << 'EOF'
"""AI command argument parser."""
from __future__ import annotations

import argparse


def add_ai_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add AI subcommand and its arguments.

    TODO Phase 2: Extract all AI arguments from cli.py lines 519-602
    """
    ai = subparsers.add_parser("ai", help="AI-powered document analysis")
    # TODO: Add all AI arguments here
    pass
EOF

# Create enterprise.py
cat > src/docx2shelf/cli_args/enterprise.py << 'EOF'
"""Enterprise command argument parser."""
from __future__ import annotations

import argparse


def add_enterprise_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add enterprise subcommand and its arguments.

    TODO Phase 2: Extract all enterprise arguments from cli.py
    """
    ent = subparsers.add_parser("enterprise", help="Enterprise features")
    # TODO: Add all enterprise arguments here
    pass
EOF

# Create plugins.py
cat > src/docx2shelf/cli_args/plugins.py << 'EOF'
"""Plugins command argument parser."""
from __future__ import annotations

import argparse


def add_plugins_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add plugins subcommand and its arguments.

    TODO Phase 2: Extract all plugins arguments from cli.py lines 386-499
    """
    p = subparsers.add_parser("plugins", help="Manage plugins and hooks")
    # TODO: Add all plugins arguments here
    pass
EOF

# Create connectors.py
cat > src/docx2shelf/cli_args/connectors.py << 'EOF'
"""Connectors command argument parser."""
from __future__ import annotations

import argparse


def add_connectors_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add connectors subcommand and its arguments.

    TODO Phase 2: Extract all connectors arguments from cli.py lines 500-518
    """
    c = subparsers.add_parser("connectors", help="Manage document connectors")
    # TODO: Add all connectors arguments here
    pass
EOF

# Create themes.py
cat > src/docx2shelf/cli_args/themes.py << 'EOF'
"""Theme command argument parsers."""
from __future__ import annotations

import argparse


def add_themes_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add theme-related subcommands (theme-editor, list-themes, preview-themes).

    TODO Phase 2: Extract all theme arguments from cli.py lines 287-320
    """
    # TODO: Add theme-editor parser
    # TODO: Add list-themes parser
    # TODO: Add preview-themes parser
    pass
EOF

# Create misc.py
cat > src/docx2shelf/cli_args/misc.py << 'EOF'
"""Miscellaneous command argument parsers."""
from __future__ import annotations

import argparse


def add_misc_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add miscellaneous subcommands (wizard, batch, validate, etc.).

    TODO Phase 2: Extract all misc arguments from cli.py
    """
    # TODO: Add wizard parser
    # TODO: Add batch parser
    # TODO: Add list-profiles parser
    # TODO: Add checklist parser
    # TODO: Add validate parser
    # TODO: Add convert parser
    # TODO: Add doctor parser
    # TODO: Add preview parser
    pass
EOF
```

### Step 3: Create cli_build.py (5 minutes)

```bash
cat > src/docx2shelf/cli_build.py << 'EOF'
"""Build workflow implementation - extracted from cli.py run_build().

This module will contain the refactored build workflow, split into phases:
- validate_build_args(): Argument validation
- prepare_metadata(): Metadata and options preparation
- execute_build_workflow(): Main build execution
"""
from __future__ import annotations

import argparse
from pathlib import Path

# These imports will be uncommented in Phase 3
# from .metadata import EpubMetadata, BuildOptions
# from .cli_prompts import prompt_missing_metadata


def run_build(args: argparse.Namespace) -> int:
    """Main build command handler - orchestrates workflow phases.

    TODO Phase 3: Extract build workflow from cli.py lines 1321-1812
    This is a placeholder that will be replaced with the full implementation.
    """
    print("Build workflow placeholder - to be implemented in Phase 3")
    return 1  # Return error code for now
EOF
```

### Step 4: Create cli_prompts.py (5 minutes)

```bash
cat > src/docx2shelf/cli_prompts.py << 'EOF'
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
EOF
```

### Step 5: Verify Structure (5 minutes)

```bash
# Check directory structure
tree src/docx2shelf/cli_args/

# Expected output:
# src/docx2shelf/cli_args/
# ├── __init__.py
# ├── ai.py
# ├── build.py
# ├── connectors.py
# ├── enterprise.py
# ├── misc.py
# ├── plugins.py
# ├── themes.py
# └── tools.py

# Verify no syntax errors
python -m py_compile src/docx2shelf/cli_args/__init__.py
python -m py_compile src/docx2shelf/cli_args/build.py
python -m py_compile src/docx2shelf/cli_args/tools.py
python -m py_compile src/docx2shelf/cli_args/ai.py
python -m py_compile src/docx2shelf/cli_args/enterprise.py
python -m py_compile src/docx2shelf/cli_args/plugins.py
python -m py_compile src/docx2shelf/cli_args/connectors.py
python -m py_compile src/docx2shelf/cli_args/themes.py
python -m py_compile src/docx2shelf/cli_args/misc.py
python -m py_compile src/docx2shelf/cli_build.py
python -m py_compile src/docx2shelf/cli_prompts.py

# Test imports work
python -c "from src.docx2shelf.cli_args import _arg_parser; print('✓ cli_args imports successfully')"
python -c "from src.docx2shelf import cli_build; print('✓ cli_build imports successfully')"
python -c "from src.docx2shelf import cli_prompts; print('✓ cli_prompts imports successfully')"
```

---

## Validation Checklist

After completing all steps, verify:

- [ ] Directory `src/docx2shelf/cli_args/` exists
- [ ] File `src/docx2shelf/cli_args/__init__.py` exists (275 lines)
- [ ] All 8 module files exist in `cli_args/`:
  - [ ] `build.py`
  - [ ] `tools.py`
  - [ ] `ai.py`
  - [ ] `enterprise.py`
  - [ ] `plugins.py`
  - [ ] `connectors.py`
  - [ ] `themes.py`
  - [ ] `misc.py`
- [ ] File `src/docx2shelf/cli_build.py` exists
- [ ] File `src/docx2shelf/cli_prompts.py` exists
- [ ] No syntax errors (all files compile successfully)
- [ ] All imports work (test imports pass)

---

## What Happens Next?

**Phase 1 Complete** ✅

You now have:
- Clean module structure ready for extraction
- Placeholder functions that define interfaces
- No changes to existing cli.py (still works as before)
- Foundation for Phase 2 (actual extraction)

**Next Steps**:
1. **Commit Phase 1**: Save the structure
   ```bash
   git add src/docx2shelf/cli_args/
   git add src/docx2shelf/cli_build.py
   git add src/docx2shelf/cli_prompts.py
   git commit -m "Phase 1: Create modular CLI structure (placeholder modules)"
   ```

2. **Proceed to Phase 2**: Start extracting actual argument parser code from cli.py into the new modules

**Or**:
- **Pause here** and wait for approval before proceeding to Phase 2
- **Review structure** and make adjustments if needed

---

## Rollback (If Needed)

If anything goes wrong, simply delete the new files:

```bash
rm -rf src/docx2shelf/cli_args/
rm src/docx2shelf/cli_build.py
rm src/docx2shelf/cli_prompts.py
```

The original cli.py is completely unchanged and will continue to work.

---

**Ready to Execute?** All commands are copy-paste ready. Estimated time: **30 minutes**.
