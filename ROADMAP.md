# Docx2Shelf Repository Review

## Repository Overview

* **Core directories:** `src/docx2shelf/`, `tests/`, `plugins/marketplace/`, `scripts/`, `packaging/`, `helm/`, `k8s/`
* **Install scripts:** `install.bat`, `install_fixed.bat`, `install.sh`
* **Configs & tooling:** `pyproject.toml`, `mkdocs.yml`, `action.yml`, `Dockerfile`
* **Docs:** README, ROADMAP with feature promises

Repo promises features like EPUB-3 output, Pandoc-preferred conversion, fallback DOCX parser, themes, ONIX 3.0 export, plugin marketplace, FastAPI server, batch processing, RBAC, webhooks, and Kubernetes support.

---

## Packaging & Install Concerns

* **Install scripts**:

  * May duplicate PATH entries or assume admin rights
  * Use `python -m pip` instead of `pip` to avoid mismatches
  * Paths with spaces may fail; quoting is required
  * Suggest: unify installers, add dry-run mode, ensure idempotence

* **pyproject.toml**:

  * Ensure `name`, `version`, `requires-python (>=3.11)`, dependencies, and extras are all defined
  * Use extras (`[project.optional-dependencies]`) for CLI, API, ONIX, plugins

* **Dockerfile**:

  * Should bundle Pandoc, ImageMagick, fonts, etc.
  * Use non-root user, pin base image, add healthcheck
  * Cache wheels to speed builds

* **Kubernetes/Helm**:

  * Add resource limits, probes, ConfigMaps/Secrets for API keys
  * Provide job chart for batch conversions

---

## Bug & Failure Hotspots

1. **Pandoc detection**: Must fail gracefully with clear warning if missing/outdated
2. **EPUB validation**: Use epubcheck in CI to catch cross-ref, image, MathML, or landmark issues
3. **Image handling**: Test large/CMYK/transparency edge cases, embedded header/footer images
4. **Chapter splitting**: Verify mixed split rules don’t produce empty or duplicate files
5. **TOC & landmarks**: Ensure nav.xhtml and spine order match; prevent duplicate start points
6. **ONIX exporter**: Validate against XSD; mark as experimental if incomplete
7. **CLI UX**: Fatal errors → non-zero exit codes, warnings → non-blocking messages
8. **Windows paths**: Normalize with pathlib, guard for non-ASCII
9. **Temp/cache dirs**: Prefer `platformdirs` locations over bundled `/tmp`
10. **Plugins**: Sandbox plugin imports; enforce version compatibility

---

## CI/CD & Quality Gates

* Pre-commit hooks: black, ruff, isort, mypy
* Golden-file tests: DOCX → XHTML/OPF/NCX with diffs
* CI matrix: Windows/macOS/Linux, Python 3.11/3.12, pip & pipx installers
* Release automation: semantic-release, attach wheels, Docker image, SBOM

---

## Security & Robustness

* Strip dangerous inline SVG/JS
* Warn on non-redistributable fonts
* Guard against path traversal in user assets
* API: enforce API keys, rate limits, async job queue, request size caps

---

## UX Enhancements

* `docx2shelf doctor` command: check environment (Pandoc, epubcheck, fonts)
* Theme previewer: output sample HTML + CSS pack
* `--store-profile kdp|kobo|apple` flags to auto-tune strictness

---

## Suggested Non-Community (Pro/Enterprise) Features

1. **QA Report**: HTML with linted issues and retailer-specific warnings
2. **Theme Designer GUI**: Live preview typography and export CSS
3. **Batch Studio & Watch Mode**: Queue multiple docs with recipe presets
4. **Retailer Connectors**: Push EPUB + metadata via KDP/Kobo/Apple APIs
5. **Watermarking/Fingerprinting**: Leak tracing without DRM
6. **Team & Compliance**: RBAC, SSO, audit logs, analytics
7. **Managed Cloud Queue**: Hosted job API with SLAs, S3/GCS storage

---

## Concrete Next Steps

* Add **Feature Matrix** to README (Available/Beta/Planned)
* Implement **CI/CD matrix** with epubcheck validation
* Harden **install scripts** for idempotence and quoting
* Ship a **`docx2shelf doctor`** environment diagnostic
