# CLI Refactoring Plan - Modular Argument Parser Architecture

**Status**: 📋 PLANNED (Not Started)
**Version**: 2.1.10 (Proposed)
**Created**: 2025-11-17
**Priority**: HIGH - Critical maintainability improvement

---

## Executive Summary

Refactor `cli.py` (4,595 lines) by extracting three monolithic functions into focused modules:

1. **`_arg_parser()`** - 721 lines → Extract into `cli_args.py` (~800 lines)
2. **`run_build()`** - 492 lines → Extract into `cli_build.py` (~600 lines)
3. **`_prompt_missing()`** - 243 lines → Extract into `cli_prompts.py` (~300 lines)

**Expected Outcome**: Reduce cli.py from 4,595 lines to ~500 lines orchestration code, with average function size from 104 lines to <100 lines.

---

## Problem Analysis

### Current State Issues

| File | Lines | Functions | Largest Function | Complexity |
|------|-------|-----------|------------------|------------|
| cli.py | 4,595 | 44 | 721 lines (_arg_parser) | Very High |

**Critical Issues**:
1. **`_arg_parser()` (lines 48-768)**: Creates all argparse subcommands in single 721-line function
2. **`run_build()` (lines 1321-1812)**: Handles entire build workflow (validation + prompts + conversion + assembly) in 492 lines
3. **`_prompt_missing()` (lines 978-1220)**: Interactive metadata prompts in 243 lines

**Consequences**:
- Difficult to test individual argument groups
- Hard to maintain and extend with new subcommands
- Violates Single Responsibility Principle
- Confusing navigation and understanding

### Subcommand Analysis

From analysis, cli.py contains these major subcommand groups:

**Primary Commands** (10):
- `build` - Main EPUB build workflow
- `tools` - Tool management (install/uninstall Pandoc, EPUBCheck)
- `wizard` - Interactive book creation
- `theme-editor` - CSS theme customization
- `list-themes` - Show available themes
- `preview-themes` - Preview themes in browser
- `list-profiles` - Show publishing profiles
- `batch` - Batch processing
- `plugins` - Plugin management
- `connectors` - Document connector management

**AI Commands** (6):
- `ai metadata` - AI metadata enhancement
- `ai genre` - Genre detection
- `ai alt-text` - Image alt text generation
- `ai chapters` - Chapter detection
- `ai config` - AI configuration
- `ai quality` - Quality assessment

**Enterprise Commands** (7):
- `enterprise batch` - Enterprise batch processing
- `enterprise jobs` - Job management
- `enterprise config` - Configuration
- `enterprise users` - User management
- `enterprise api` - API management
- `enterprise webhooks` - Webhook management
- `enterprise reports` - Reporting

**Other Commands** (5):
- `checklist` - Publishing checklists
- `validate` - EPUB validation
- `convert` - Format conversion
- `doctor` - Health checks
- `preview` - Preview mode

---

## Proposed Architecture

### New Module Structure

```
src/docx2shelf/
├── cli.py                  (~500 lines) - Main orchestrator
├── cli_args/               (New directory)
│   ├── __init__.py         - Exports _arg_parser()
│   ├── build.py            (~150 lines) - Build command args
│   ├── tools.py            (~80 lines)  - Tools command args
│   ├── ai.py               (~100 lines) - AI command args
│   ├── enterprise.py       (~120 lines) - Enterprise command args
│   ├── plugins.py          (~100 lines) - Plugin command args
│   ├── connectors.py       (~60 lines)  - Connector command args
│   ├── themes.py           (~80 lines)  - Theme command args
│   └── misc.py             (~110 lines) - Misc commands (batch, wizard, etc.)
├── cli_build.py            (~600 lines) - Build workflow implementation
└── cli_prompts.py          (~300 lines) - Interactive metadata prompts
```

### Interface Design

#### cli_args/__init__.py
```python
"""Modular argument parser for docx2shelf CLI."""
from __future__ import annotations

import argparse
from .build import add_build_parser
from .tools import add_tools_parser
from .ai import add_ai_parser
from .enterprise import add_enterprise_parser
from .plugins import add_plugins_parser
from .connectors import add_connectors_parser
from .themes import add_themes_parser
from .misc import add_misc_parsers

def _arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    from ..version import get_version_string

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

    # Add all subcommand parsers
    add_build_parser(sub)
    add_tools_parser(sub)
    add_ai_parser(sub)
    add_enterprise_parser(sub)
    add_plugins_parser(sub)
    add_connectors_parser(sub)
    add_themes_parser(sub)
    add_misc_parsers(sub)

    return p
```

#### cli_args/build.py
```python
"""Build command argument parser."""
from __future__ import annotations

import argparse

def add_build_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add build subcommand and its arguments."""
    b = subparsers.add_parser("build", help="Build an EPUB from inputs")

    # Input/output arguments
    b.add_argument(
        "--input",
        type=str,
        help="Path to manuscript file or directory of files (.docx, .md, .txt, .html)",
    )
    b.add_argument("--cover", type=str, help="Path to cover image (jpg/png)")

    # Metadata arguments
    b.add_argument("--title", type=str, help="Book title")
    b.add_argument("--author", type=str, help="Author name")
    # ... (all other build arguments)

    # Processing options
    b.add_argument(
        "--split-at",
        choices=["h1", "h2", "h3", "pagebreak", "mixed"],
        default="h1",
        help="How to split content into XHTML files",
    )
    # ... (all other processing options)
```

#### cli_build.py
```python
"""Build workflow implementation - extracted from cli.py run_build()."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .metadata import EpubMetadata, BuildOptions
from .cli_prompts import prompt_missing_metadata

def validate_build_args(args: argparse.Namespace) -> None:
    """Validate build arguments before processing."""
    # Extract validation logic from run_build()
    pass

def prepare_metadata(args: argparse.Namespace) -> tuple[EpubMetadata, BuildOptions]:
    """Prepare metadata and build options from arguments."""
    # Extract metadata preparation logic from run_build()
    pass

def execute_build_workflow(
    meta: EpubMetadata,
    opts: BuildOptions,
    output_path: Path,
) -> None:
    """Execute the main build workflow: convert + assemble."""
    # Extract build execution logic from run_build()
    pass

def run_build(args: argparse.Namespace) -> int:
    """Main build command handler - orchestrates workflow phases."""
    # Phase 1: Validate
    validate_build_args(args)

    # Phase 2: Prepare metadata
    meta, opts = prepare_metadata(args)

    # Phase 3: Execute build
    output_path = Path(args.output) if args.output else Path("output.epub")
    execute_build_workflow(meta, opts, output_path)

    return 0
```

#### cli_prompts.py
```python
"""Interactive metadata prompts - extracted from cli.py _prompt_missing()."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

def prompt_title(current_value: Optional[str]) -> str:
    """Prompt for book title."""
    # Extract title prompting logic
    pass

def prompt_author(current_value: Optional[str]) -> str:
    """Prompt for author name."""
    # Extract author prompting logic
    pass

def prompt_metadata_field(
    field_name: str,
    current_value: Optional[str],
    required: bool = True,
) -> Optional[str]:
    """Generic metadata field prompt."""
    # Extract generic prompting logic
    pass

def prompt_missing_metadata(args: argparse.Namespace) -> argparse.Namespace:
    """Interactively prompt for missing required metadata.

    Extracted from cli.py _prompt_missing() (243 lines).
    """
    # Extract all prompting logic, organized by metadata type:
    # - Basic metadata (title, author)
    # - Series metadata (series name, index)
    # - Publication metadata (publisher, pubdate)
    # - Classification metadata (subjects, keywords)
    # - Advanced metadata (ISBN, language)
    pass
```

---

## Implementation Plan

### Phase 1: Prepare Module Structure (30 minutes)

**Tasks**:
1. Create `src/docx2shelf/cli_args/` directory
2. Create `cli_args/__init__.py` with base structure
3. Create empty module files:
   - `cli_args/build.py`
   - `cli_args/tools.py`
   - `cli_args/ai.py`
   - `cli_args/enterprise.py`
   - `cli_args/plugins.py`
   - `cli_args/connectors.py`
   - `cli_args/themes.py`
   - `cli_args/misc.py`
4. Create `cli_build.py` and `cli_prompts.py` files

**Validation**:
- [ ] Directory structure created
- [ ] All module files exist with proper imports
- [ ] No syntax errors in new files

### Phase 2: Extract Argument Parsers (2-3 hours)

**Priority Order** (start with largest/most important):

1. **Build Command** (`cli_args/build.py`) - Lines 64-259 (~196 lines)
   - Extract all `b.add_argument()` calls
   - Preserve theme discovery logic
   - Maintain argument order and defaults

2. **Tools Command** (`cli_args/tools.py`) - Lines 357-385 (~28 lines)
   - Extract tools subparser and sub-subparsers
   - Simple extraction, good warm-up

3. **Plugins Command** (`cli_args/plugins.py`) - Lines 386-499 (~113 lines)
   - Extract complex nested subparsers (marketplace, bundles)
   - Preserve all plugin management subcommands

4. **AI Command** (`cli_args/ai.py`) - Lines 519-602 (~83 lines)
   - Extract AI subparser and sub-subparsers
   - Preserve all AI analysis subcommands

5. **Enterprise Command** (`cli_args/enterprise.py`) - Lines 603-702 (~99 lines)
   - Extract enterprise subparser and sub-subparsers
   - Preserve all enterprise management subcommands

6. **Connectors Command** (`cli_args/connectors.py`) - Lines 500-518 (~18 lines)
   - Extract connector subparser
   - Simple extraction

7. **Themes Command** (`cli_args/themes.py`) - Lines 287-320 (~33 lines)
   - Extract theme-related parsers (theme-editor, list-themes, preview-themes)

8. **Misc Commands** (`cli_args/misc.py`) - Remaining commands
   - wizard, batch, list-profiles, checklist, validate, convert, doctor, preview

**Validation After Each Extraction**:
```bash
# Test import
python -c "from src.docx2shelf.cli_args import _arg_parser; _arg_parser()"

# Test actual CLI
python -m docx2shelf --help
python -m docx2shelf build --help
python -m docx2shelf tools --help
# ... (test each subcommand)
```

### Phase 3: Extract Build Workflow (2-3 hours)

**Tasks**:
1. Analyze `run_build()` function (lines 1321-1812)
2. Identify logical phases:
   - Argument validation
   - Metadata preparation (loading from file, applying defaults)
   - Interactive prompting (if needed)
   - Document conversion
   - EPUB assembly
   - Post-processing (validation, quality checks)
3. Extract each phase into separate function in `cli_build.py`
4. Update `cli.py` to import and call new functions

**Validation**:
```bash
# Test build workflow
python -m docx2shelf build --input test.docx --title "Test" --author "Author"

# Test batch mode (uses same logic)
python -m docx2shelf batch --input docs/ --output output/
```

### Phase 4: Extract Prompting Logic (1-2 hours)

**Tasks**:
1. Analyze `_prompt_missing()` function (lines 978-1220)
2. Group prompts by metadata type
3. Extract into focused functions in `cli_prompts.py`:
   - `prompt_title()`
   - `prompt_author()`
   - `prompt_series()`
   - `prompt_publication_info()`
   - `prompt_classification()`
   - `prompt_advanced()`
4. Create generic `prompt_metadata_field()` helper
5. Update `cli_build.py` to import and use new prompting functions

**Validation**:
```bash
# Test interactive prompts (leave fields empty to trigger prompts)
python -m docx2shelf build --input test.docx
# Should prompt for title, author, etc.
```

### Phase 5: Update Main cli.py (30 minutes)

**Tasks**:
1. Update imports in `cli.py`:
   ```python
   from .cli_args import _arg_parser
   from .cli_build import run_build
   ```
2. Remove extracted functions from `cli.py`:
   - Delete lines 48-768 (_arg_parser)
   - Delete lines 1321-1812 (run_build)
   - Delete lines 978-1220 (_prompt_missing)
3. Keep all other command handlers (run_tools, run_wizard, etc.)
4. Verify imports and function calls still work

**Validation**:
```bash
# Test all major commands
python -m docx2shelf --version
python -m docx2shelf build --help
python -m docx2shelf tools --help
python -m docx2shelf wizard
```

### Phase 6: Testing & Validation (1-2 hours)

**Comprehensive Testing**:
1. **Unit Tests** (if time permits):
   - Test individual argument parsers
   - Test build workflow phases
   - Test prompting functions

2. **Integration Tests**:
   ```bash
   # Test build workflow
   pytest tests/test_cli.py -v

   # Test argument parsing
   python -m docx2shelf build --help
   python -m docx2shelf tools install --help
   python -m docx2shelf ai metadata --help

   # Test actual functionality
   python -m docx2shelf build --input tests/fixtures/sample.docx \
       --title "Test Book" --author "Test Author" --output test.epub
   ```

3. **Smoke Tests**:
   - [ ] All subcommands show help text
   - [ ] Build workflow completes successfully
   - [ ] Interactive prompts work
   - [ ] Error messages are clear

**Validation Checklist**:
- [ ] All imports resolve correctly
- [ ] No circular dependencies
- [ ] All CLI commands work as before
- [ ] Build workflow completes successfully
- [ ] Interactive prompts function correctly
- [ ] Error handling preserved
- [ ] No functionality lost

### Phase 7: Documentation & Cleanup (30 minutes)

**Tasks**:
1. Update `CHANGELOG.md`:
   ```markdown
   ## [2.1.10] - 2025-11-17
   ### Major Code Refactoring - Modular CLI Architecture

   #### Refactored
   - **cli.py**: Reduced from 4,595 lines to ~500 lines by extracting into focused modules:
     - `cli_args/` package: Argument parser split into 8 focused modules (~800 lines total)
     - `cli_build.py`: Build workflow extracted and organized into phases (~600 lines)
     - `cli_prompts.py`: Interactive metadata prompts modularized (~300 lines)
   - Improved maintainability and testability
   - No breaking changes - all functionality preserved
   ```

2. Update `CLAUDE.md` if needed (document new architecture)

3. Clean up any temporary files or comments

4. Final verification:
   ```bash
   # Linting
   ruff check src/docx2shelf/cli.py
   ruff check src/docx2shelf/cli_args/
   ruff check src/docx2shelf/cli_build.py
   ruff check src/docx2shelf/cli_prompts.py

   # Formatting
   black --check src/docx2shelf/cli.py
   black --check src/docx2shelf/cli_args/
   black --check src/docx2shelf/cli_build.py
   black --check src/docx2shelf/cli_prompts.py
   ```

---

## Success Metrics

### Before Refactoring
- **cli.py**: 4,595 lines, 44 functions
- **Largest function**: 721 lines (_arg_parser)
- **Average function size**: ~104 lines
- **Complexity**: Very High
- **Maintainability**: Low

### After Refactoring (Target)
- **cli.py**: ~500 lines (orchestration only)
- **cli_args/**: ~800 lines total (8 focused modules)
- **cli_build.py**: ~600 lines (organized phases)
- **cli_prompts.py**: ~300 lines (modular prompts)
- **Largest function**: <100 lines
- **Average function size**: ~30 lines
- **Complexity**: Low
- **Maintainability**: High

### Expected Improvements
- ✅ **74% reduction** in cli.py size (4,595 → 500 lines)
- ✅ **Testability**: Individual parsers and phases can be unit tested
- ✅ **Extensibility**: New subcommands add 50-100 line modules, not 100+ lines to monolith
- ✅ **Clarity**: Each module has single, clear responsibility
- ✅ **Navigation**: Easy to find and modify specific functionality

---

## Risk Mitigation

### Risks & Mitigations

1. **Risk**: Breaking CLI functionality
   - **Mitigation**: Comprehensive testing after each phase
   - **Rollback**: Git history preserves original

2. **Risk**: Circular dependencies
   - **Mitigation**: Clear separation of concerns (parsers → build → prompts)
   - **Testing**: Import checks after each module creation

3. **Risk**: Lost functionality
   - **Mitigation**: Line-by-line extraction, preserving all logic
   - **Validation**: Test all subcommands before and after

4. **Risk**: Import errors
   - **Mitigation**: Test imports immediately after creating modules
   - **Fix**: Adjust `__init__.py` exports as needed

---

## Time Estimate

| Phase | Estimated Time | Cumulative |
|-------|---------------|------------|
| 1. Prepare structure | 30 min | 30 min |
| 2. Extract parsers | 2-3 hours | 2.5-3.5 hours |
| 3. Extract build workflow | 2-3 hours | 4.5-6.5 hours |
| 4. Extract prompts | 1-2 hours | 5.5-8.5 hours |
| 5. Update main cli.py | 30 min | 6-9 hours |
| 6. Testing & validation | 1-2 hours | 7-11 hours |
| 7. Documentation | 30 min | **7.5-11.5 hours** |

**Recommended Approach**: Spread over 2-3 sessions to avoid fatigue and ensure thorough testing.

---

## Comparison to assemble.py Refactoring

### Similar Success Pattern

The v2.1.9 `assemble.py` refactoring provides a proven blueprint:

| Metric | assemble.py (v2.1.9) | cli.py (v2.1.10 target) |
|--------|----------------------|-------------------------|
| **Original size** | 1,153 lines | 4,595 lines |
| **Refactored size** | 300 lines | ~500 lines |
| **Reduction** | 74% | 89% |
| **New modules** | 6 focused modules | 10 focused modules |
| **Test impact** | Zero (all tests pass) | Target: Zero |
| **User impact** | None (internal) | None (internal) |

**Key Lessons Applied**:
- Incremental extraction with validation at each step
- Preserve all functionality (no breaking changes)
- Clear module boundaries and interfaces
- Comprehensive testing before declaring success
- Update CHANGELOG and documentation

---

## Next Steps

**Awaiting User Decision**:
1. **Proceed with refactoring now?** (7-12 hours estimated)
2. **Defer to future version?** (mark as v2.2.0 milestone)
3. **Start with Phase 1 only?** (structure preparation, 30 minutes)

**Recommendation**: Start with Phase 1 (structure preparation) to validate the approach, then proceed with full refactoring if structure looks good.

---

**Created by**: Code quality analysis (2025-11-17)
**References**:
- `/tmp/code_quality_analysis.md` - Original analysis identifying issues
- `REFACTORING_PLAN.md` - Successful pattern from v2.1.9
- `src/docx2shelf/cli.py` - Source file to refactor
