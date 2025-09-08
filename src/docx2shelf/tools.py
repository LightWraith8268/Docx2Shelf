from __future__ import annotations

import os
import platform
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Optional
from urllib.request import urlopen
import hashlib
import time


DEFAULT_PANDOC_VERSION = "3.1.12"
DEFAULT_EPUBCHECK_VERSION = "5.1.0"


def tools_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        p = base / "Docx2Shelf" / "bin"
    else:
        p = Path.home() / ".docx2shelf" / "bin"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path, *, attempts: int = 3, expect_sha256: str | None = None) -> None:
    last_err: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            with urlopen(url) as resp, open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
            if expect_sha256:
                got = _sha256(dest)
                if got.lower() != expect_sha256.lower():
                    raise RuntimeError(
                        f"Checksum mismatch for {dest.name}: expected {expect_sha256}, got {got}"
                    )
            if dest.stat().st_size <= 0:
                raise RuntimeError("Downloaded file is empty")
            return
        except Exception as e:
            last_err = e
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            time.sleep(0.8 * i)
    assert last_err is not None
    raise last_err


def _platform_tag() -> tuple[str, str]:
    sysname = platform.system().lower()
    mach = platform.machine().lower()
    return sysname, mach


def pandoc_path() -> Optional[Path]:
    # Prefer managed binary, else PATH
    td = tools_dir()
    exe = "pandoc.exe" if os.name == "nt" else "pandoc"
    cand = td / exe
    if cand.exists():
        return cand
    found = shutil.which("pandoc")
    return Path(found) if found else None


def epubcheck_cmd() -> Optional[list[str]]:
    # Prefer epubcheck wrapper in tools dir, else locate jar, else PATH
    td = tools_dir()
    wrapper = td / ("epubcheck.bat" if os.name == "nt" else "epubcheck")
    if wrapper.exists():
        return [str(wrapper)]
    jar = td / "epubcheck.jar"
    if jar.exists():
        java = shutil.which("java")
        if java:
            return [java, "-jar", str(jar)]
    which_cmd = shutil.which("epubcheck")
    if which_cmd:
        return [which_cmd]
    return None


def uninstall_pandoc() -> None:
    td = tools_dir()
    exe = "pandoc.exe" if os.name == "nt" else "pandoc"
    try:
        (td / exe).unlink(missing_ok=True)
    except Exception:
        pass


def uninstall_epubcheck() -> None:
    td = tools_dir()
    try:
        (td / "epubcheck.jar").unlink(missing_ok=True)
    except Exception:
        pass
    wrapper = td / ("epubcheck.bat" if os.name == "nt" else "epubcheck")
    try:
        wrapper.unlink(missing_ok=True)
    except Exception:
        pass


def uninstall_all_tools() -> None:
    uninstall_pandoc()
    uninstall_epubcheck()


def _fetch_pandoc_checksum(version: str, archive_name: str) -> str | None:
    # Try to fetch checksum list from release and parse for the archive
    base = f"https://github.com/jgm/pandoc/releases/download/{version}"
    for name in ("SHA256SUMS.txt", "sha256sum.txt", "SHA256SUMS"):  # various conventions
        url = f"{base}/{name}"
        try:
            with urlopen(url) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            for line in text.splitlines():
                if archive_name in line:
                    parts = line.strip().split()
                    if parts and all(c in "0123456789abcdefABCDEF" for c in parts[0]):
                        return parts[0]
        except Exception:
            continue
    return None


def install_pandoc(version: str = DEFAULT_PANDOC_VERSION) -> Path:
    sysname, mach = _platform_tag()
    td = tools_dir()
    exe = "pandoc.exe" if os.name == "nt" else "pandoc"
    out = td / exe
    if out.exists():
        return out
    base = f"https://github.com/jgm/pandoc/releases/download/{version}"
    # Map platform → archive name
    if sysname == "windows":
        arc = f"pandoc-{version}-windows-x86_64.zip"
    elif sysname == "darwin":
        # arm64 vs x86_64
        if "arm" in mach or "aarch" in mach:
            arc = f"pandoc-{version}-macOS-arm64.zip"
        else:
            arc = f"pandoc-{version}-macOS.zip"
    else:  # linux
        arc = f"pandoc-{version}-linux-amd64.tar.gz"
    url = f"{base}/{arc}"
    tmp = td / arc
    expect = _fetch_pandoc_checksum(version, arc)
    _download(url, tmp, attempts=3, expect_sha256=expect)
    # Extract binary
    if tmp.suffix == ".zip":
        with zipfile.ZipFile(tmp) as z:
            # find pandoc binary inside
            member = next((m for m in z.namelist() if m.endswith("/" + exe)), None)
            if not member:
                raise RuntimeError("pandoc binary not found in archive")
            td.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
    else:
        with tarfile.open(tmp, "r:gz") as t:
            member = next((m for m in t.getmembers() if m.name.endswith("/" + exe)), None)
            if not member:
                raise RuntimeError("pandoc binary not found in archive")
            td.mkdir(parents=True, exist_ok=True)
            f = t.extractfile(member)
            if not f:
                raise RuntimeError("failed to extract pandoc from archive")
            with open(out, "wb") as dst:
                shutil.copyfileobj(f, dst)
    try:
        out.chmod(0o755)
    except Exception:
        pass
    tmp.unlink(missing_ok=True)
    return out


def _fetch_epubcheck_checksum(version: str, archive_name: str) -> str | None:
    base = f"https://github.com/w3c/epubcheck/releases/download/v{version}"
    # Try common checksum filename variants
    for cand in (f"{archive_name}.sha256", f"SHA256SUMS.txt", f"sha256sum.txt"):
        url = f"{base}/{cand}"
        try:
            with urlopen(url) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            # If .sha256 single-line format
            if cand.endswith(".sha256"):
                s = text.strip().split()[0]
                return s if all(c in "0123456789abcdefABCDEF" for c in s) else None
            # Parse list format
            for line in text.splitlines():
                if archive_name in line:
                    parts = line.strip().split()
                    if parts and all(c in "0123456789abcdefABCDEF" for c in parts[0]):
                        return parts[0]
        except Exception:
            continue
    return None


def install_epubcheck(version: str = DEFAULT_EPUBCHECK_VERSION) -> Path:
    td = tools_dir()
    jar = td / "epubcheck.jar"
    if jar.exists():
        return jar
    base = f"https://github.com/w3c/epubcheck/releases/download/v{version}"
    arc = f"epubcheck-{version}.zip"
    url = f"{base}/{arc}"
    tmp = td / arc
    expect = _fetch_epubcheck_checksum(version, arc)
    _download(url, tmp, attempts=3, expect_sha256=expect)
    with zipfile.ZipFile(tmp) as z:
        member = next((m for m in z.namelist() if m.endswith("/epubcheck.jar")), None)
        if not member:
            # sometimes jar is at root
            member = next((m for m in z.namelist() if m.endswith("epubcheck.jar")), None)
        if not member:
            raise RuntimeError("epubcheck.jar not found in archive")
        with z.open(member) as src, open(jar, "wb") as dst:
            shutil.copyfileobj(src, dst)
    # Create a wrapper for convenience
    wrapper = td / ("epubcheck.bat" if os.name == "nt" else "epubcheck")
    if os.name == "nt":
        wrapper.write_text(f"@echo off\njava -jar \"{jar}\" %*\n", encoding="utf-8")
    else:
        # Use single-quoted f-string to avoid escaping inner double quotes
        wrapper.write_text(f'#!/usr/bin/env sh\nexec java -jar "{jar}" "$@"\n', encoding="utf-8")
        try:
            wrapper.chmod(0o755)
        except Exception:
            pass
    tmp.unlink(missing_ok=True)
    return jar
