"""Watch + offline preflight helpers for the build subcommand.

Pure stdlib polling watcher (no `watchdog` dep) so the tool stays offline-friendly.
Designed for unattended/idle automation: run once, detect file changes, rebuild,
emit exit codes, repeat.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path


def offline_preflight(args: argparse.Namespace) -> int:
    """Return 0 if offline build can proceed, non-zero error code otherwise.

    Verifies bundled Pandoc + EPUBCheck are already installed locally so no
    network fetch is triggered mid-build.
    """
    from ..tools import epubcheck_cmd, pandoc_path

    missing: list[str] = []
    if pandoc_path() is None:
        missing.append("pandoc (run: docx2shelf tools install pandoc)")
    if epubcheck_cmd() is None:
        missing.append("epubcheck (run: docx2shelf tools install epubcheck)")
    if missing:
        print("Offline preflight failed. Missing local tools:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 5
    return 0


def _collect_watch_targets(args: argparse.Namespace) -> list[Path]:
    """Collect files/dirs whose mtimes trigger a rebuild."""
    targets: list[Path] = []
    if getattr(args, "input", None):
        targets.append(Path(args.input).expanduser())
    if getattr(args, "cover", None):
        targets.append(Path(args.cover).expanduser())
    if getattr(args, "metadata", None):
        targets.append(Path(args.metadata).expanduser())
    # Auto-discovered metadata next to input
    if getattr(args, "input", None):
        ip = Path(args.input).expanduser()
        d = ip.parent if ip.is_file() else ip
        for name in ("metadata.txt", "metadata.md"):
            p = d / name
            if p.exists():
                targets.append(p)
    return targets


def _snapshot(targets: list[Path]) -> dict[str, float]:
    """Map path → max mtime. For dirs, walk recursively (cap depth implicit via FS)."""
    snap: dict[str, float] = {}
    for t in targets:
        if not t.exists():
            continue
        if t.is_file():
            snap[str(t)] = t.stat().st_mtime
        elif t.is_dir():
            for sub in t.rglob("*"):
                if sub.is_file():
                    snap[str(sub)] = sub.stat().st_mtime
    return snap


def run_build_watch(args: argparse.Namespace, run_build_fn) -> int:
    """Run an initial build, then poll for changes and rebuild.

    Returns the last build's exit code on Ctrl-C / SIGTERM.
    """
    interval = max(0.25, float(getattr(args, "watch_interval", 2.0) or 2.0))
    targets = _collect_watch_targets(args)
    if not targets:
        print("watch: no input/cover/metadata to watch", file=sys.stderr)
        return 2

    print(
        f"watch: monitoring {len(targets)} target(s) every {interval}s. Ctrl-C to stop.",
        flush=True,
    )

    stopped = False

    def _stop(_signum, _frame):
        nonlocal stopped
        stopped = True
        print("\nwatch: stopping...")

    signal.signal(signal.SIGINT, _stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)

    last_snap = _snapshot(targets)
    last_rc = run_build_fn(args)
    print(f"watch: initial build rc={last_rc}", flush=True)

    while not stopped:
        time.sleep(interval)
        if stopped:
            break
        snap = _snapshot(targets)
        if snap != last_snap:
            changed = sorted(set(snap) ^ set(last_snap)) or [
                p for p in snap if last_snap.get(p) != snap[p]
            ]
            print(
                f"watch: change detected ({len(changed)} file(s)); rebuilding...",
                flush=True,
            )
            last_snap = snap
            try:
                last_rc = run_build_fn(args)
            except Exception as exc:
                print(
                    f"watch: build raised {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                last_rc = 1
            print(f"watch: rebuild rc={last_rc}", flush=True)

    return last_rc
