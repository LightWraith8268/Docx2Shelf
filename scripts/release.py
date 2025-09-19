#!/usr/bin/env python3
"""
Automated release script for Docx2Shelf.

This script ensures the complete release process is followed:
1. Update version in pyproject.toml
2. Update ROADMAP.md marking current version as completed
3. Update CHANGELOG.md with release notes
4. Update README.md with new user-facing features
5. Commit changes
6. Push to GitHub
7. Create GitHub release

Usage:
    python scripts/release.py --version 1.2.8 --type minor
    python scripts/release.py --version 1.2.8 --type minor --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding='utf-8')

    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def update_version(new_version: str, dry_run: bool = False) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding='utf-8')

    updated_content = re.sub(
        r'version = "([^"]+)"',
        f'version = "{new_version}"',
        content
    )

    if not dry_run:
        pyproject_path.write_text(updated_content, encoding='utf-8')

    print(f"Updated version to {new_version} in pyproject.toml")


def update_roadmap(version: str, milestone_name: str, dry_run: bool = False) -> None:
    """Update ROADMAP.md to mark current version as completed."""
    roadmap_path = Path("ROADMAP.md")
    content = roadmap_path.read_text(encoding='utf-8')

    # Find the current "Next" section and mark it as completed
    pattern = r'### 🟦 \*\*Next — v' + re.escape(version) + r': ([^*]+)\*\*'

    def replace_func(match):
        milestone_title = match.group(1).strip()
        return f'### ✅ **Completed — v{version}: {milestone_title}**'

    updated_content = re.sub(pattern, replace_func, content)

    if not dry_run:
        roadmap_path.write_text(updated_content, encoding='utf-8')

    print(f"Updated ROADMAP.md marking v{version} as completed")


def update_changelog(version: str, milestone_name: str, features: List[str], dry_run: bool = False) -> None:
    """Update CHANGELOG.md with new release entry."""
    changelog_path = Path("CHANGELOG.md")
    content = changelog_path.read_text(encoding='utf-8')

    today = datetime.now().strftime("%Y-%m-%d")

    # Create new changelog entry
    new_entry = f"""## [{version}] - {today}
### {milestone_name}

"""

    for feature in features:
        new_entry += f"- {feature}\n"

    new_entry += "\n"

    # Insert after the "# Changelog" header
    updated_content = content.replace(
        "# Changelog\n\n",
        f"# Changelog\n\n{new_entry}"
    )

    if not dry_run:
        changelog_path.write_text(updated_content, encoding='utf-8')

    print(f"Updated CHANGELOG.md with v{version} entry")


def update_readme_features(version: str, new_features: List[str], dry_run: bool = False) -> None:
    """Update README.md with new user-facing features."""
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding='utf-8')

    # Add version note to new features section if it exists
    if f"(New in v{version})" not in content and new_features:
        # Find existing version notes and update them
        pattern = r'### Developer Experience \(New in v[\d.]+\)'
        if re.search(pattern, content):
            updated_content = re.sub(
                pattern,
                f'### Developer Experience (New in v{version})',
                content
            )
        else:
            # Add new section for this version's features
            feature_section = f"""
### New in v{version}
"""
            for feature in new_features:
                feature_section += f"-   **{feature}**\n"

            # Insert after Advanced Workflows section
            updated_content = content.replace(
                "-   **No Internet Required**: Works completely offline - your manuscripts never leave your computer\n",
                f"-   **No Internet Required**: Works completely offline - your manuscripts never leave your computer\n{feature_section}"
            )

        if not dry_run:
            readme_path.write_text(updated_content, encoding='utf-8')

        print(f"Updated README.md with v{version} features")


def commit_and_push(version: str, milestone_name: str, dry_run: bool = False) -> None:
    """Commit changes and push to GitHub."""
    if dry_run:
        print("Would commit and push changes")
        return

    # Stage all changes
    run_command(["git", "add", "."])

    # Create commit message
    commit_msg = f"""feat: Release v{version} - {milestone_name}

- Updated version to {version} in pyproject.toml
- Updated ROADMAP.md marking v{version} as completed
- Updated CHANGELOG.md with {milestone_name} features
- Updated README.md with new user-facing features

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    # Commit
    run_command(["git", "commit", "-m", commit_msg])

    # Push
    run_command(["git", "push"])

    print(f"Committed and pushed v{version} changes")


def create_github_release(version: str, milestone_name: str, features: List[str], dry_run: bool = False) -> None:
    """Create GitHub release."""
    if dry_run:
        print("Would create GitHub release")
        return

    release_notes = f"""# 🚀 v{version} - {milestone_name}

## What's New

"""

    for feature in features:
        release_notes += f"- {feature}\n"

    release_notes += f"""

## 📖 Documentation Updates

- Updated ROADMAP.md with v{version} completion
- Enhanced CHANGELOG.md with detailed feature breakdown
- Updated README.md with new user-facing capabilities

## 💡 Installation

```bash
pipx install docx2shelf
```

See [installation guide](https://github.com/LightWraith8268/Docx2Shelf#installation) for more options.

---

**Full Changelog**: See [CHANGELOG.md](https://github.com/LightWraith8268/Docx2Shelf/blob/main/CHANGELOG.md)
"""

    # Create release
    run_command([
        "gh", "release", "create", f"v{version}",
        "--title", f"v{version} - {milestone_name}",
        "--notes", release_notes
    ])

    print(f"Created GitHub release v{version}")


def main():
    parser = argparse.ArgumentParser(description="Automated release script for Docx2Shelf")
    parser.add_argument("--version", required=True, help="New version number (e.g., 1.2.8)")
    parser.add_argument("--milestone", required=True, help="Milestone name (e.g., 'Community & Ecosystem')")
    parser.add_argument("--features", nargs="*", default=[], help="List of new features")
    parser.add_argument("--readme-features", nargs="*", default=[], help="List of README features")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    print(f"Starting release process for v{args.version}")

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")

    try:
        current_version = get_current_version()
        print(f"Current version: {current_version}")

        # Step 1: Update version
        update_version(args.version, args.dry_run)

        # Step 2: Update roadmap
        update_roadmap(args.version, args.milestone, args.dry_run)

        # Step 3: Update changelog
        update_changelog(args.version, args.milestone, args.features, args.dry_run)

        # Step 4: Update README
        if args.readme_features:
            update_readme_features(args.version, args.readme_features, args.dry_run)

        # Step 5: Commit and push
        commit_and_push(args.version, args.milestone, args.dry_run)

        # Step 6: Create GitHub release
        create_github_release(args.version, args.milestone, args.features, args.dry_run)

        print(f"✅ Release v{args.version} completed successfully!")

    except Exception as e:
        print(f"❌ Release failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()