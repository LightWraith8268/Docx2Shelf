# Docx2Shelf Roadmap

> **Vision**  
> Make Docx2Shelf the most *reliable, standards‑compliant, and author‑friendly* DOCX→EPUB tool—equally comfortable in a one‑click GUI flow and in large automated pipelines.

---

## Guiding principles
- **Quality first:** clean XHTML, predictable structure, strong accessibility and validation by default.
- **Offline by default:** zero network calls unless explicitly enabled (e.g., optional connectors).
- **Composable:** core + plugins + themes—small pieces, loosely coupled.
- **Reproducible:** same input → same output across OSes and versions.
- **Secure supply chain:** verified downloads, signed releases, SBOM, reproducible builds.

---

## Completed (v1.1.x)
The following large items are **done** and form the new baseline:
- Robust DOCX fallback parser: tracked changes, comments, complex tables, text boxes/shapes, equations, headers/footers, footnotes/endnotes.
- Style mapping via user‑overridable `styles.json`.
- “Rasterize‑on‑escape” for untranslatable layout elements.
- ToC & splitting: arbitrary ToC depth (≥3), mixed split strategies, per‑section start markers.
- Theme packs & theme API (beyond serif/sans/printlike). Night‑mode friendly base themes.
- Font subsetting via fontTools with licensing warnings.
- Image pipeline: resize/compress, long‑edge caps, WebP/AVIF with fallback, per‑image DPI rules.
- Accessibility pass: alt‑text prompts, ARIA landmarks, accessibility metadata.
- **EPUBCheck runs by default** (opt‑out); friendly summary with actionable hints.
- Language/script support: RTL, CJK/vertical options, hyphenation dictionaries; language‑aware defaults.
- EPUB 2 compatibility mode (stricter CSS, dual nav/NCX).
- UX & workflow: `--preview` (pre‑zip local viewer), `--inspect`, profiles `--profile kdp|kobo|apple|generic`.
- Batch mode and machine‑readable logs (`--json`) for CI.
- Richer `metadata.txt` schema (roles, BISAC/keywords normalization, series anchors) + retailer lints.
- First‑party GitHub Action (matrix builds, artifacts, EPUBCheck reports).
- Plugin hooks (pre‑convert, transforms, metadata resolvers).
- Optional offline‑first connectors (local MD→EPUB; gated cloud imports as opt‑in packages).
- Distribution: PyPI (`pipx`), Homebrew, winget, Scoop, Docker image.
- Signed tool downloads with SHA‑256 verification; GPG available.
- Tools Manager polish: version pin sets, `tools doctor`, offline bundles.
- Tests & QA: golden EPUB fixtures, property‑based tests, reader smoke tests.
- Docs: screenshots/GIFs, “quality cookbook,” theme gallery, starter metadata templates.
- Governance: LICENSE, CONTRIBUTING, Code of Conduct, issue templates & “good first issue” board.

---

## Milestones (Now → Next → Later)

### ✅ **Completed — v1.2.2: Semantics & Scholarly polish**
**Epics**
1. **Cross‑references & anchors**
   - [x] Map Word cross‑refs (headings/figures/tables) to stable intra‑EPUB links after splitting.
   - [x] Generate permanent anchors for all headings/figures/tables with collision‑safe IDs.
   - **Acceptance**: ✅ Given a DOCX with cross‑refs, produced EPUB preserves link targets across split files.

2. **Indexing**
   - [x] Parse Word XE fields (and/or a plaintext index spec).
   - [x] Build `/text/index.xhtml` with alphabetical sections and back‑links to occurrences.
   - **Acceptance**: ✅ Index page is generated, alphabetized, and all entries resolve.

3. **Notes flow**
   - [x] Footnote/endnote **back‑refs** to note calls.
   - [x] Optional consolidated "Notes" page style with per‑chapter anchors.
   - **Acceptance**: ✅ From a note, user can return to the exact call site.

4. **Figures, tables & lists**
   - [x] Wrap captions as semantic `<figure><figcaption>` and `<table>` with proper `scope`/headers.
   - [x] Auto "List of Figures/Tables" pages (opt‑in) from caption inventory.
   - **Acceptance**: ✅ Captions render semantically; lists link correctly.

**DX & Tests**
- [x] Golden fixtures for cross‑refs, index, captions, and back‑refs.
- [x] Enhanced placeholder completion across codebase.

**Implementation Notes**
- Added `crossrefs.py` with collision-safe ID generation using MD5 hashing
- Added `indexing.py` with XE field parsing and hierarchical index generation
- Added `notes.py` with back-reference generation and consolidated notes pages
- Added `figures.py` with semantic figure/table wrapping and auto-generated lists
- Enhanced `convert.py` with improved text box/shape handling and run style mapping
- Completed Google Docs and OneDrive connector implementations
- Added comprehensive test suite in `test_v12_features.py` with golden fixtures
- Updated CSS themes (serif, sans, printlike) with complete implementations

---

### ✅ **Completed — v1.2.3: Retail Ops & Accessibility+**
**Epics**
5. **Math handling**
   - [x] Toggleable **MathML** with **SVG** fallback; per‑book policy (`math: mathml|svg|images`).
   - [x] Equation alt‑text prompts or plugin hook.
   - **Acceptance**: ✅ Same equation renders on Apple Books (MathML) and Kindle (SVG/png).

6. **Retailer preflight**
   - [x] **ONIX 3.0** export generated from `metadata.txt` (title, contributors, IDs, prices, BISAC).
   - [x] **Kindle Previewer** integration (if installed): capture preflight logs as artifacts.
   - [x] Store‑profiled CSS/lints for KDP/Apple/Kobo (beyond base presets).
   - **Acceptance**: ✅ Build emits `.epub`, `.onix.xml`, and (if KP installed) KP report; fails on critical lints.

7. **Accessibility Level‑Up**
   - [x] **Media Overlays (SMIL)** when audio is provided (read‑aloud EPUB).
   - [x] Dyslexic‑friendly theme + automatic dual theme via `prefers-color-scheme`.
   - [x] **A11y audit report** (missing alts, heading order, landmarks coverage).
   - **Acceptance**: ✅ EPUBCheck + A11y audit pass; overlays sync highlights.

**DX & Tests**
- [x] Enhanced retailer profile validation system.
- [x] Comprehensive accessibility audit framework.

**Implementation Notes**
- Added `math_handler.py` with MathML/SVG/PNG conversion pipeline and auto alt-text generation
- Added `onix_export.py` with full ONIX 3.0 XML generation from EPUB metadata
- Added `kindle_previewer.py` with automatic conversion and issue detection
- Added `store_profiles.py` with validation rules for KDP, Apple Books, Kobo, Google Play, and B&N
- Added `media_overlays.py` with SMIL generation for synchronized audio narration
- Added `dyslexic.css` theme with enhanced accessibility features and dual theme support
- Added `accessibility_audit.py` with comprehensive WCAG compliance checking and HTML reporting
- Enhanced placeholder completion across all connector implementations

---

### ✅ **Completed — v1.2.4: GUI, Ecosystem & Performance**
**Epics**
8. **Anthology & series builder**
   - [x] Merge multiple manuscripts into one EPUB (grouped ToC, per‑story front‑matter).
   - [x] "Series packer": batch build series, auto "Also By This Author" from previous outputs.
   - **Acceptance**: ✅ N inputs → one EPUB with grouped ToC; also‑by page updates automatically.

9. **GUI & integrations**
   - [x] Cross‑platform GUI (Tkinter/PyQt) with drag‑drop; Windows context‑menu: "Convert to EPUB".
   - [x] Web-based builder with HTTP server and REST API for team workflows.
   - **Acceptance**: ✅ Non‑CLI users can convert with defaults and preview locally.

10. **Performance & reliability**
    - [x] Streaming DOCX read to lower peak RAM.
    - [x] Incremental build cache keyed by DOCX hash; parallel image pipeline.
    - [x] Performance monitoring and optimization reporting.
    - **Acceptance**: ✅ Defined perf targets achieved with streaming processing and caching.

11. **Plugin ecosystem hardening**
    - [x] Hybrid plugin architecture with core built-ins vs marketplace downloads.
    - [x] Plugin marketplace with bundles, search, install, and version management.
    - [x] Plugin classification system and dependency management.
    - **Acceptance**: ✅ Plugins install via marketplace; core vs optional distinction implemented.

**Implementation Notes**
- Added complete plugin marketplace system with hybrid architecture
- Implemented cross-platform GUI applications (desktop + web)
- Added anthology/series building with automatic cross-referencing
- Performance optimizations: streaming, caching, parallel processing
- Enhanced installation scripts with plugin bundle support

---

### ✅ **Completed — v1.2.5: Security & Supply Chain**
**Epics**
12. **Supply‑chain & releases**
    - [x] Sigstore signing for wheels and GHCR images; SLSA provenance; SBOM (CycloneDX).
    - [x] Verified Publisher for winget/Homebrew; reproducible build notes.
    - [x] Dependency vulnerability scanning and automated security updates.
    - **Acceptance**: ✅ Release page includes signatures, provenance, SBOM; automated verification job is green.

13. **Advanced reliability & testing**
    - [x] Fuzzing corpus (Hypothesis) of mutated DOCX; long‑doc benchmarks in CI.
    - [x] Property-based testing for conversion reliability across document types.
    - [x] Automated regression testing with golden EPUB fixtures.
    - **Acceptance**: ✅ CI includes comprehensive reliability tests; perf regressions caught automatically.

**Implementation Notes**
- Added complete security framework with SecurityManager, Sigstore integration, SLSA provenance, SBOM generation
- Implemented comprehensive testing infrastructure: DOCXFuzzer, PropertyBasedTester, GoldenEPUBTester, PerformanceTester
- Enhanced GitHub Actions workflow with secure release pipeline and attestation generation
- Created ReliabilityTestSuite integrating all testing frameworks with robustness validation

---

### 🟦 **Next — v1.2.6: Operational Excellence & Deployment**
**Epics**
14. **Production deployment & monitoring**
    - [ ] Container orchestration with Kubernetes manifests and Helm charts.
    - [ ] Health checks, metrics collection, and observability (Prometheus/Grafana).
    - [ ] Auto-scaling and load balancing for high-volume conversion workloads.
    - **Acceptance**: Production-ready deployment with monitoring, scaling, and health checks.

15. **Advanced plugin system**
    - [ ] Plugin sandboxing and security isolation for untrusted plugins.
    - [ ] Hot-reload plugin architecture with zero-downtime updates.
    - [ ] Plugin performance profiling and resource usage monitoring.
    - **Acceptance**: Plugins can be safely loaded/unloaded without service restart; resource usage tracked.

16. **Enterprise integration & APIs**
    - [ ] Webhook integration for external system notifications and triggers.
    - [ ] Advanced REST API with OpenAPI specification and rate limiting.
    - [ ] Database integration for conversion history and audit trails.
    - **Acceptance**: External systems can integrate seamlessly; full audit trail maintained.

**Implementation Notes**
- Focus on production-grade deployment and operational excellence
- Enhance plugin system with security and performance monitoring
- Build enterprise integration capabilities for workflow automation
- Maintain compatibility with existing v1.2.5 security framework

---

### 🟦 **Later — v1.3.0: Enterprise & AI**
**Epics**
17. **Enterprise & team features**
    - [ ] Role-based access control for web interface and shared projects.
    - [ ] Audit logging and conversion tracking for enterprise workflows.
    - [ ] Batch processing API with queue management and job status.
    - **Acceptance**: Enterprise teams can manage large-scale conversion workflows with proper access controls.

18. **Documentation & learning platform**
    - [ ] MkDocs site with cookbook, theme gallery, plugin API, retailer guides.
    - [ ] Interactive tutorials and troubleshooting wizard.
    - [ ] Video tutorials and community learning resources.
    - **Acceptance**: Site deploys on tag; examples build as part of CI to ensure they don't rot.

19. **AI & automation features**
    - [ ] AI-powered metadata suggestion and enhancement.
    - [ ] Automated genre detection and keyword generation.
    - [ ] Smart image alt-text generation and accessibility improvements.
    - **Acceptance**: AI features improve metadata quality and accessibility without manual intervention.

---

## Tracking & labels
- **Labels**: `epic`, `a11y`, `retail`, `math`, `performance`, `plugin`, `docs`, `good-first-issue`, `help-wanted`, `security`.
- **Issue naming**: `[v1.2.2][epic] Cross‑refs & anchors` ; `[v1.2.2][task] Back‑refs from footnotes`.
- **Projects**: 3 columns per milestone: *Backlog → In progress → Done*; automated via GH Actions.
- **Definition of Done**: tests + docs + examples updated; changelog entry; release notes drafted; CI green on Linux/macOS/Windows.

---

## Risks & mitigations
- **Reader CSS quirks** → maintain compatibility matrix & snapshot tests.
- **Large‑doc performance** → streaming & caching; perf guardrails in CI.
- **Dependency drift** → Tools Manager pin sets; nightly canary builds with alerts.
- **A11y regressions** → automated a11y audit with minimum thresholds.

---

## Contributing
See **CONTRIBUTING.md**. New to the codebase? Start with `good-first-issue` on docs, fixtures, or theme samples.  
Have a niche workflow? Consider authoring a plugin—check the Plugin API section in the docs site.

