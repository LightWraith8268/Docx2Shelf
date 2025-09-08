#!/usr/bin/env bash
set -euo pipefail

# Docx2Shelf uninstaller for Linux/macOS
# Default: uninstall pipx package if present, else fallback to pip user/system.

METHOD="auto"   # auto | pipx | pip-user | pip-system

usage() {
  echo "Usage: $0 [--method auto|pipx|pip-user|pip-system]"; exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method) METHOD="${2:-}"; shift 2;;
    -h|--help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

python_cmd() { if command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi; }

echo "Uninstalling Docx2Shelf using method=$METHOD"

if [[ "$METHOD" == "auto" ]]; then
  if command -v pipx >/dev/null 2>&1 && pipx list 2>/dev/null | grep -qi '^package docx2shelf ' ; then
    METHOD="pipx"
  else
    METHOD="pip-user"
  fi
fi

case "$METHOD" in
  pipx)
    if command -v pipx >/dev/null 2>&1; then
      pipx uninstall docx2shelf || true
    else
      echo "pipx not found; nothing to remove via pipx"
    fi
    ;;
  pip-user)
    $(python_cmd) -m pip uninstall -y docx2shelf || true
    ;;
  pip-system)
    $(python_cmd) -m pip uninstall -y docx2shelf || true
    ;;
  *) echo "Unknown method: $METHOD"; exit 2;;
esac

echo "Done. If 'docx2shelf' still appears on PATH, restart your terminal or remove leftover binaries from your scripts directory."

