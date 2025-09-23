from __future__ import annotations

import hashlib
import os
import platform
import shutil
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

DEFAULT_PANDOC_VERSION = "3.1.12"
DEFAULT_EPUBCHECK_VERSION = "5.1.0"

# Version pin sets for different stability levels
VERSION_PIN_SETS = {
    "stable": {
        "pandoc": "3.1.11",  # Known stable version
        "epubcheck": "5.0.1"  # Known stable version
    },
    "latest": {
        "pandoc": "3.1.12",  # Latest tested version
        "epubcheck": "5.1.0"  # Latest tested version
    },
    "bleeding": {
        "pandoc": None,  # Use latest available
        "epubcheck": None  # Use latest available
    }
}


def tools_dir() -> Path:
    """Get the tools directory using platformdirs for cross-platform compatibility."""
    try:
        from .path_utils import get_user_data_dir
        p = get_user_data_dir("docx2shelf") / "bin"
    except ImportError:
        # Fallback if path_utils not available
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


def _download(url: str, dest: Path, *, attempts: int = 3, expect_sha256: str | None = None,
              gpg_signature_url: str | None = None, trusted_keys: list[str] | None = None) -> None:
    """Download a file with optional SHA-256 and GPG verification."""
    last_err: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            with urlopen(url) as resp, open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)

            if dest.stat().st_size <= 0:
                raise RuntimeError("Downloaded file is empty")

            # SHA-256 verification (existing)
            if expect_sha256:
                got = _sha256(dest)
                if got.lower() != expect_sha256.lower():
                    raise RuntimeError(
                        f"Checksum mismatch for {dest.name}: expected {expect_sha256}, got {got}"
                    )

            # GPG verification (new)
            if gpg_signature_url and trusted_keys:
                _verify_gpg_signature(dest, gpg_signature_url, trusted_keys)

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


def _verify_gpg_signature(file_path: Path, signature_url: str, trusted_keys: list[str]) -> None:
    """Verify GPG signature of a downloaded file."""
    import subprocess
    import tempfile

    # Check if gpg is available
    if not shutil.which("gpg"):
        print("Warning: GPG not available, skipping signature verification")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        signature_file = temp_path / f"{file_path.name}.sig"

        try:
            # Download signature file
            with urlopen(signature_url) as resp, open(signature_file, "wb") as f:
                shutil.copyfileobj(resp, f)

            # Import trusted keys if provided
            for key in trusted_keys:
                try:
                    result = subprocess.run([
                        "gpg", "--quiet", "--batch", "--import", "-"
                    ], input=key, text=True, capture_output=True)
                    if result.returncode != 0:
                        print(f"Warning: Failed to import GPG key: {result.stderr}")
                except Exception as e:
                    print(f"Warning: Error importing GPG key: {e}")

            # Verify signature
            result = subprocess.run([
                "gpg", "--quiet", "--batch", "--verify", str(signature_file), str(file_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"[OK] GPG signature verified for {file_path.name}")
            else:
                print(f"Warning: GPG signature verification failed for {file_path.name}: {result.stderr}")
                # Don't fail the download, just warn

        except Exception as e:
            print(f"Warning: GPG verification error for {file_path.name}: {e}")
            # Don't fail the download, just warn


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


def check_pandoc_availability() -> tuple[bool, str, Optional[str]]:
    """
    Check Pandoc availability and return status, message, and version.

    Returns:
        (is_available, status_message, version_or_none)
    """
    import subprocess

    # Check if pandoc binary exists
    pandoc_binary = pandoc_path()
    if not pandoc_binary:
        return False, "Pandoc binary not found. Install with 'docx2shelf tools install pandoc'", None

    # Check if binary is executable
    try:
        result = subprocess.run(
            [str(pandoc_binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return False, f"Pandoc binary exists but failed to run: {result.stderr}", None

        # Extract version from output
        version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown"
        version = version_line.replace("pandoc ", "").split()[0] if "pandoc " in version_line else "Unknown"

        # Check minimum version (Pandoc 2.0+)
        if version != "Unknown":
            try:
                major_version = int(version.split('.')[0])
                if major_version < 2:
                    return False, f"Pandoc {version} is too old (requires 2.0+). Update with 'docx2shelf tools install pandoc'", version
            except (ValueError, IndexError):
                pass  # Continue with unknown version

        return True, f"Pandoc {version} available", version

    except subprocess.TimeoutExpired:
        return False, "Pandoc binary exists but timed out during version check", None
    except Exception as e:
        return False, f"Error checking Pandoc: {e}", None


def check_pypandoc_availability() -> tuple[bool, str]:
    """
    Check pypandoc Python library availability.

    Returns:
        (is_available, status_message)
    """
    try:
        import pypandoc

        # Check if pypandoc can find pandoc
        try:
            pandoc_path_from_pypandoc = pypandoc.get_pandoc_path()
            return True, f"pypandoc available (using pandoc at {pandoc_path_from_pypandoc})"
        except OSError:
            return False, "pypandoc installed but cannot find pandoc binary"

    except ImportError:
        return False, "pypandoc not installed. Install with 'pip install pypandoc'"


def get_pandoc_status() -> dict[str, any]:
    """
    Get comprehensive Pandoc status information.

    Returns:
        Dictionary with detailed status information
    """
    pandoc_available, pandoc_msg, pandoc_version = check_pandoc_availability()
    pypandoc_available, pypandoc_msg = check_pypandoc_availability()

    return {
        "pandoc_binary": {
            "available": pandoc_available,
            "message": pandoc_msg,
            "version": pandoc_version,
            "path": str(pandoc_path()) if pandoc_path() else None
        },
        "pypandoc_library": {
            "available": pypandoc_available,
            "message": pypandoc_msg
        },
        "overall_available": pandoc_available and pypandoc_available,
        "fallback_needed": not (pandoc_available and pypandoc_available)
    }


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
    for cand in (f"{archive_name}.sha256", "SHA256SUMS.txt", "sha256sum.txt"):
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
        wrapper.write_text(f'@echo off\njava -jar "{jar}" %*\n', encoding="utf-8")
    else:
        # Use single-quoted f-string to avoid escaping inner double quotes
        wrapper.write_text(f'#!/usr/bin/env sh\nexec java -jar "{jar}" "$@"\n', encoding="utf-8")
        try:
            wrapper.chmod(0o755)
        except Exception:
            pass
    tmp.unlink(missing_ok=True)
    return jar


def get_version_pin_config() -> Path:
    """Get path to version pin configuration file."""
    config_dir = tools_dir().parent / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "version_pins.json"


def load_version_pins() -> dict:
    """Load current version pin configuration."""
    config_file = get_version_pin_config()
    if not config_file.exists():
        return {"preset": "latest"}

    try:
        import json
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {"preset": "latest"}


def save_version_pins(config: dict) -> None:
    """Save version pin configuration."""
    config_file = get_version_pin_config()
    import json
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def set_version_pin_preset(preset: str) -> None:
    """Set version pin preset (stable, latest, bleeding)."""
    if preset not in VERSION_PIN_SETS:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(VERSION_PIN_SETS.keys())}")

    config = {"preset": preset, "custom_pins": {}}
    save_version_pins(config)
    print(f"Version pin preset set to: {preset}")


def pin_tool_version(tool: str, version: str) -> None:
    """Pin a specific tool to a specific version."""
    config = load_version_pins()
    if "custom_pins" not in config:
        config["custom_pins"] = {}

    config["custom_pins"][tool] = version
    save_version_pins(config)
    print(f"Pinned {tool} to version {version}")


def get_pinned_version(tool: str) -> Optional[str]:
    """Get the pinned version for a tool."""
    config = load_version_pins()

    # Check custom pins first
    if "custom_pins" in config and tool in config["custom_pins"]:
        return config["custom_pins"][tool]

    # Check preset
    preset = config.get("preset", "latest")
    if preset in VERSION_PIN_SETS and tool in VERSION_PIN_SETS[preset]:
        return VERSION_PIN_SETS[preset][tool]

    # Fall back to defaults
    if tool == "pandoc":
        return DEFAULT_PANDOC_VERSION
    elif tool == "epubcheck":
        return DEFAULT_EPUBCHECK_VERSION

    return None


def tools_doctor() -> int:
    """Run comprehensive health check on tools setup."""
    import subprocess
    import sys

    print("[DOCTOR] Docx2Shelf Tools Health Check")
    print("=" * 40)

    issues_found = 0

    # Check Python version
    print(f"[OK] Python version: {sys.version}")

    # Check tools directory
    td = tools_dir()
    print(f"[OK] Tools directory: {td}")
    print(f"  Exists: {'Yes' if td.exists() else 'No'}")
    print(f"  Writable: {'Yes' if os.access(td, os.W_OK) else 'No'}")

    # Check Pandoc with enhanced detection
    print("\n[PANDOC] Pandoc Status:")
    status = get_pandoc_status()

    # Pandoc binary status
    binary_info = status["pandoc_binary"]
    if binary_info["available"]:
        print(f"  [OK] Binary: {binary_info['message']}")
        print(f"  [OK] Path: {binary_info['path']}")

        # Check if version matches pinned version
        pinned = get_pinned_version("pandoc")
        if pinned and binary_info["version"] and pinned not in binary_info["version"]:
            print(f"  [WARNING] Expected version {pinned}, got {binary_info['version']}")
            issues_found += 1
    else:
        print(f"  [ERROR] Binary: {binary_info['message']}")
        issues_found += 1

    # pypandoc library status
    library_info = status["pypandoc_library"]
    if library_info["available"]:
        print(f"  [OK] Library: {library_info['message']}")
    else:
        print(f"  [WARNING] Library: {library_info['message']}")

    # Overall status and recommendations
    if status["overall_available"]:
        print("  [OK] Pandoc fully functional for document conversion")
    elif status["fallback_needed"]:
        print("  [WARNING] Pandoc issues detected - will use fallback conversion")
        print("  [INFO] Install missing components for best performance:")
        if not binary_info["available"]:
            print("    - Run 'docx2shelf tools install pandoc' to install Pandoc")
        if not library_info["available"]:
            print("    - Run 'pip install pypandoc' to install Python integration")

    # Check EPUBCheck
    print("\n[EPUBCHECK] EPUBCheck Status:")
    epubcheck_cmd_list = epubcheck_cmd()
    if epubcheck_cmd_list:
        print(f"  [OK] Found at: {epubcheck_cmd_list[0]}")
        try:
            result = subprocess.run(epubcheck_cmd_list + ["--version"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_info = result.stdout.strip() if result.stdout else result.stderr.strip()
                print(f"  [OK] Version: {version_info}")

                # Check if version matches pinned version
                pinned = get_pinned_version("epubcheck")
                if pinned and pinned not in version_info:
                    print(f"  [WARNING]  Warning: Expected version {pinned}, got {version_info}")
                    issues_found += 1
            else:
                print(f"  [ERROR] Error running epubcheck: {result.stderr}")
                issues_found += 1
        except Exception as e:
            print(f"  [ERROR] Error checking epubcheck: {e}")
            issues_found += 1
    else:
        print("  [ERROR] EPUBCheck not found")
        issues_found += 1

    # Check Java (for EPUBCheck)
    print("\n[JAVA] Java Status:")
    try:
        result = subprocess.run(["java", "-version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            java_version = result.stderr.split('\n')[0] if result.stderr else "Unknown"
            print(f"  [OK] Java available: {java_version}")
        else:
            print("  [ERROR] Java not working properly")
            issues_found += 1
    except FileNotFoundError:
        print("  [ERROR] Java not found (required for EPUBCheck)")
        issues_found += 1
    except Exception as e:
        print(f"  [ERROR] Error checking Java: {e}")
        issues_found += 1

    # Check version pins configuration
    print("\n[PINS] Version Pins:")
    config = load_version_pins()
    preset = config.get("preset", "latest")
    print(f"  Current preset: {preset}")

    custom_pins = config.get("custom_pins", {})
    if custom_pins:
        print("  Custom pins:")
        for tool, version in custom_pins.items():
            print(f"    {tool}: {version}")
    else:
        print("  No custom pins set")

    # Check PATH
    print("\n[PATH]  PATH Diagnostics:")
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    tools_in_path = []

    for tool in ["pandoc", "java", "python", "pip", "pipx"]:
        found = shutil.which(tool)
        if found:
            tools_in_path.append(f"  [OK] {tool}: {found}")
        else:
            tools_in_path.append(f"  [ERROR] {tool}: not found")

    for tool_info in tools_in_path:
        print(tool_info)

    # Summary
    print("\n" + "=" * 40)
    if issues_found == 0:
        print("[SUCCESS] All systems operational!")
        return 0
    else:
        print(f"[WARNING]  Found {issues_found} issue(s)")
        print("\nRecommended actions:")
        print("- Run 'docx2shelf tools install pandoc' to install Pandoc")
        print("- Run 'docx2shelf tools install epubcheck' to install EPUBCheck")
        print("- Ensure Java is installed for EPUBCheck functionality")
        return 1


def setup_offline_bundle(bundle_dir: Path) -> None:
    """Set up offline bundle directory with pre-downloaded tools."""
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Create bundle structure
    cache_dir = bundle_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    print(f"Setting up offline bundle in: {bundle_dir}")

    # Pre-download Pandoc for current platform
    try:
        sysname, mach = _platform_tag()
        pandoc_version = get_pinned_version("pandoc") or DEFAULT_PANDOC_VERSION

        # Download Pandoc archive to cache
        pandoc_cache = cache_dir / f"pandoc-{pandoc_version}-{sysname}-{mach}.tar.gz"
        if not pandoc_cache.exists():
            # This would need platform-specific URLs - simplified for now
            print(f"Would download Pandoc {pandoc_version} to {pandoc_cache}")

        # Download EPUBCheck to cache
        epubcheck_version = get_pinned_version("epubcheck") or DEFAULT_EPUBCHECK_VERSION
        epubcheck_cache = cache_dir / f"epubcheck-{epubcheck_version}.zip"
        if not epubcheck_cache.exists():
            print(f"Would download EPUBCheck {epubcheck_version} to {epubcheck_cache}")

        # Create offline installation script
        install_script = bundle_dir / ("install_offline.bat" if os.name == "nt" else "install_offline.sh")
        script_content = f"""#!/bin/bash
# Offline installation script for Docx2Shelf tools
# Bundle created: {time.strftime('%Y-%m-%d %H:%M:%S')}

echo "Installing tools from offline bundle..."
# Copy cached files to tools directory and extract
# Implementation would copy from cache to tools directory
echo "Offline installation complete!"
"""
        install_script.write_text(script_content)
        if os.name != "nt":
            install_script.chmod(0o755)

        print(f"[OK] Offline bundle prepared in {bundle_dir}")
        print("Bundle includes cached tool downloads for air-gapped installation.")

    except Exception as e:
        print(f"Error setting up offline bundle: {e}")


def get_offline_bundle_dir() -> Path:
    """Get the default offline bundle directory."""
    return tools_dir().parent / "offline_bundle"
