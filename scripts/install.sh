#!/usr/bin/env bash
set -euo pipefail

# Docx2Shelf installer for Linux/macOS
# Default: install via pipx with [docx] extra

METHOD="pipx"           # pipx | pip-user | pip-system
EXTRAS="docx"           # none | docx | pandoc | all
WITH_TOOLS="none"       # none | pandoc | epubcheck | all

usage() {
  echo "Usage: $0 [--method pipx|pip-user|pip-system] [--extras none|docx|pandoc|all] [--with-tools none|pandoc|epubcheck|all]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method) METHOD="${2:-}"; shift 2;;
    --extras) EXTRAS="${2:-}"; shift 2;;
    --with-tools) WITH_TOOLS="${2:-}"; shift 2;;
    -h|--help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi
}

ensure_pipx() {
  if command -v pipx >/dev/null 2>&1; then return 0; fi
  echo "pipx not found; installing to user site..."
  local py; py=$(python_cmd)
  $py -m pip install --user pipx
  $py -m pipx ensurepath || true
  echo "Re-open your terminal if 'pipx' is not immediately found on PATH."
}

pkg_spec="."
case "$EXTRAS" in
  none) pkg_spec=".";;
  docx) pkg_spec=".[docx]";;
  pandoc) pkg_spec=".[pandoc]";;
  all) pkg_spec=".[docx,pandoc]";;
  *) echo "Invalid --extras: $EXTRAS"; exit 2;;
esac

echo "Installing Docx2Shelf using method=$METHOD extras=$EXTRAS"

if [[ "$METHOD" == "pipx" ]]; then
  ensure_pipx
  if pipx list 2>/dev/null | grep -qi '^package docx2shelf '; then
    echo "Upgrading existing pipx package..."
    pipx upgrade "$pkg_spec"
  else
    pipx install "$pkg_spec"
  fi
elif [[ "$METHOD" == "pip-user" ]]; then
  $(python_cmd) -m pip install --user "$pkg_spec"
elif [[ "$METHOD" == "pip-system" ]]; then
  $(python_cmd) -m pip install "$pkg_spec"
else
  echo "Unknown method: $METHOD"; exit 2
fi

echo "Verifying CLI on PATH..."
if ! command -v docx2shelf >/dev/null 2>&1; then
  echo "docx2shelf is not on PATH yet. Ensure your user scripts directory is in PATH (e.g., ~/.local/bin)." >&2
  exit 0
fi

docx2shelf --help >/dev/null || {
  echo "docx2shelf installed but failed to run. Check Python/pipx environment." >&2
  exit 1
}

# Optional tools installation
case "$WITH_TOOLS" in
  none) ;;
  pandoc)
    echo "Installing Pandoc via tools manager..."
    docx2shelf tools install pandoc || true ;;
  epubcheck)
    echo "Installing EPUBCheck via tools manager..."
    docx2shelf tools install epubcheck || true ;;
  all)
    echo "Installing Pandoc + EPUBCheck via tools manager..."
    docx2shelf tools install pandoc || true
    docx2shelf tools install epubcheck || true ;;
  *) echo "Invalid --with-tools: $WITH_TOOLS" ;;
esac

echo "Done. Try: docx2shelf --help"
