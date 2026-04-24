"""Compute the next release version for the Release workflow.

Reads current version from pyproject.toml, finds the latest `v*.*.*` git tag,
and determines the next version based on either a forced bump (FORCE_BUMP env
var: "major"/"minor"/"patch") or conventional commits since the last tag.

Emits three outputs to $GITHUB_OUTPUT:
  version  - bare version string, e.g. "2.2.1"
  tag      - tag string, e.g. "v2.2.1"
  released - "true" if a release should happen, "false" otherwise
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def try_git(*args: str) -> str | None:
    try:
        return git(*args)
    except subprocess.CalledProcessError:
        return None


def parse_version(raw: str) -> tuple[int, int, int]:
    clean = raw.lstrip("v").split("-", 1)[0].split("+", 1)[0]
    parts = clean.split(".")
    if len(parts) < 3:
        parts += ["0"] * (3 - len(parts))
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as exc:
        raise SystemExit(f"Cannot parse version '{raw}': {exc}")


def read_pyproject_version() -> str:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit("Could not find version in pyproject.toml")
    return match.group(1)


def detect_bump_from_commits(rev_range: str) -> str | None:
    log = try_git("log", rev_range, "--format=%B%x00", "--no-merges") or ""
    commits = [c.strip() for c in log.split("\x00") if c.strip()]
    if not commits:
        return None

    first_line_re = re.compile(r"^(?P<type>[a-zA-Z]+)(\([^)]+\))?(?P<bang>!)?:")
    breaking = False
    has_feat = False
    has_fix = False
    for commit in commits:
        first = commit.splitlines()[0] if commit else ""
        match = first_line_re.match(first)
        if match:
            if match.group("bang"):
                breaking = True
            ctype = match.group("type").lower()
            if ctype == "feat":
                has_feat = True
            elif ctype in ("fix", "perf"):
                has_fix = True
        if re.search(r"(?m)^BREAKING CHANGE:", commit):
            breaking = True

    if breaking:
        return "major"
    if has_feat:
        return "minor"
    if has_fix:
        return "patch"
    return None


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        print(f"{name}={value}")
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    current_pyproject = read_pyproject_version()
    last_tag = try_git("describe", "--tags", "--abbrev=0", "--match", "v*.*.*")

    pyproject_tuple = parse_version(current_pyproject)
    tag_tuple = parse_version(last_tag) if last_tag else (0, 0, 0)
    base = max(pyproject_tuple, tag_tuple)

    force = os.environ.get("FORCE_BUMP", "").strip().lower()
    if force in ("major", "minor", "patch"):
        bump_type: str | None = force
    elif force:
        raise SystemExit(f"Invalid FORCE_BUMP value: '{force}' (expected major|minor|patch|'')")
    else:
        rev_range = f"{last_tag}..HEAD" if last_tag else "HEAD"
        bump_type = detect_bump_from_commits(rev_range)

    if not bump_type:
        print("No bumpable commits (feat/fix/perf/BREAKING CHANGE) since last tag;")
        print("no manual bump requested. Skipping release.")
        write_output("version", current_pyproject)
        write_output("tag", last_tag or f"v{current_pyproject}")
        write_output("released", "false")
        return 0

    major, minor, patch = base
    if bump_type == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump_type == "minor":
        minor, patch = minor + 1, 0
    elif bump_type == "patch":
        patch += 1

    existing_tags = set((try_git("tag", "--list") or "").split())
    while f"v{major}.{minor}.{patch}" in existing_tags:
        patch += 1

    next_version = f"{major}.{minor}.{patch}"
    next_tag = f"v{next_version}"

    print(f"pyproject current: {current_pyproject}")
    print(f"last tag:          {last_tag or '(none)'}")
    print(f"bump type:         {bump_type}")
    print(f"next version:      {next_version}")
    print(f"next tag:          {next_tag}")

    write_output("version", next_version)
    write_output("tag", next_tag)
    write_output("released", "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
