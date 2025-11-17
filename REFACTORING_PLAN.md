# Assemble.py Refactoring Plan

**Status:** ✅ COMPLETED
**Goal:** Break down the 1153-line assemble.py (complexity 238) into 7 focused modules
**Result:** Successfully reduced assemble.py from 1153 lines to 300 lines (74% reduction)

## Current State Analysis

### Main Issues
- `assemble_epub()` function: **625 lines** with **21 distinct responsibilities**
- High complexity score: **238**
- Violates Single Responsibility Principle
- Difficult to test, maintain, and extend

### Function Breakdown
The `assemble_epub()` function currently handles:
1. Metadata setup (identifier, title, language, author, publisher, dates, subjects, series)
2. Cover processing
3. CSS processing
4. Title page creation
5. Copyright page creation
6. Front/back matter (dedication, acknowledgements)
7. Resource validation (path security)
8. Image processing (optimization, format conversion)
9. Figure processor initialization
10. Accessibility features processing
11. Content security sanitization
12. Language attributes
13. Chapter processing (manual vs auto modes)
14. Heading ID injection
15. ToC building (nested structure)
16. Spine setup
17. Navigation document generation
18. List of figures/tables
19. Landmarks generation
20. Font embedding (with subsetting)
21. EPUB writing and validation

## Proposed Module Structure

### Module 1: `epub_metadata.py`
**Purpose:** Handle all EPUB metadata and cover setup
**Functions:**
- `setup_book_metadata(book, meta: EpubMetadata) -> None`
  - Set identifier, title, language, author
  - Set publisher, pubdate, description
  - Set title_sort, author_sort
  - Add subjects and keywords
  - Add Calibre series metadata
- `add_cover_to_book(book, meta: EpubMetadata) -> None`
  - Read cover image bytes
  - Set cover with ebooklib

**Dependencies:**
- `EpubMetadata` from metadata.py
- ebooklib

### Module 2: `epub_css.py`
**Purpose:** CSS and theme processing
**Functions:**
- `setup_book_css(book, opts: BuildOptions, styles_css: str, language: str) -> EpubItem`
  - Load CSS via `_load_css()` (move from assemble.py)
  - Create CSS EpubItem
  - Add to book
  - Return style_item for chapter linkage
- `_load_css()` - **Move from assemble.py**
- `_generate_epub2_compat_css()` - **Move from assemble.py**
- `generate_language_css()` - Use from language.py

**Dependencies:**
- `BuildOptions` from metadata.py
- `generate_language_css()` from language.py
- ebooklib

### Module 3: `epub_pages.py`
**Purpose:** Static page generation (title, copyright, matter, landmarks)
**Functions:**
- `create_title_page(meta: EpubMetadata) -> EpubHtml`
  - Load title.xhtml template
  - Replace placeholders
  - Create _html_item
- `create_copyright_page(meta: EpubMetadata) -> EpubHtml`
  - Generate copyright HTML
  - Create _html_item
- `create_front_back_matter(opts: BuildOptions, meta: EpubMetadata) -> list[EpubHtml]`
  - Process dedication.txt if exists
  - Process acknowledgements.txt if exists
  - Return list of matter items
- `create_landmarks_page(book, meta: EpubMetadata, opts: BuildOptions) -> EpubHtml | None`
  - Extract landmarks from book structure
  - Generate landmarks HTML
  - Return landmarks item or None on error
- `_html_item()` - **Move from assemble.py**

**Dependencies:**
- `EpubMetadata`, `BuildOptions` from metadata.py
- `_read_text()` from assemble.py (move to utils or keep local)
- ebooklib

### Module 4: `epub_resources.py`
**Purpose:** Resource processing (images, fonts)
**Functions:**
- `process_and_add_images(book, resources: list[Path], opts: BuildOptions) -> None`
  - Validate resource paths (security)
  - Filter image files
  - Process images with optimization
  - Add processed images to book
  - Handle non-image resources
- `process_and_add_fonts(book, opts: BuildOptions, html_chunks: list[str]) -> None`
  - Check if embed_fonts_dir exists
  - Display font licensing warning
  - Process fonts with subsetting
  - Add processed fonts to book

**Dependencies:**
- `BuildOptions` from metadata.py
- `validate_resource_path()` from content_security.py
- `process_images()` from images.py
- `get_media_type_for_image()` from images.py
- `process_embedded_fonts()`, `warn_about_font_licensing()` from fonts.py
- `safe_filename()`, `write_text_safe()` from path_utils.py
- ebooklib

### Module 5: `epub_chapters.py`
**Purpose:** Chapter processing and content preparation
**Functions:**
- `process_chapters(book, html_chunks: list[str], meta: EpubMetadata, opts: BuildOptions, style_item, figure_processor) -> tuple[list[EpubHtml], list[Link], list[list[Link]]]`
  - Handle manual vs auto chapter modes
  - Process figures in each chapter
  - Inject heading IDs
  - Create chapter EpubHtml items
  - Build chapter links and sub-links
  - Return (chapters, chapter_links, chapter_sub_links)
- `_inject_heading_ids()` - **Move from assemble.py**
- `_inject_manual_chapter_ids()` - **Move from assemble.py**
- `_find_chapter_starts()` - **Move from assemble.py**

**Dependencies:**
- `EpubMetadata`, `BuildOptions` from metadata.py
- `FigureProcessor` from figures.py
- `_html_item()` from epub_pages.py
- ebooklib

### Module 6: `epub_navigation.py`
**Purpose:** ToC, spine, and navigation document generation
**Functions:**
- `setup_book_navigation(book, chapters: list[EpubHtml], chapter_links: list[Link], chapter_sub_links: list[list[Link]], opts: BuildOptions, title_page, copyright_page, matter_items: list[EpubHtml]) -> None`
  - Build nested ToC structure
  - Setup spine with proper order
  - Add navigation document
  - Add list of figures/tables if enabled
  - Validate ToC/spine consistency
- `build_nested_toc()` - Extract from assemble_epub
- `_validate_toc_spine_consistency()` - **Move from assemble.py**

**Dependencies:**
- `BuildOptions` from metadata.py
- ebooklib

### Module 7: Keep in `assemble.py`
**Purpose:** Main orchestration and validation
**Functions:**
- `assemble_epub()` - **Refactored to orchestrate the modules above**
  - Initialize performance monitoring
  - Call `setup_book_metadata()`
  - Call `add_cover_to_book()`
  - Call `setup_book_css()`
  - Call `create_title_page()`, `create_copyright_page()`
  - Call `create_front_back_matter()`
  - Call `process_and_add_images()`
  - Process accessibility features (keep here, tightly coupled)
  - Apply content security (keep here, tightly coupled)
  - Add language attributes (keep here, tightly coupled)
  - Call `process_chapters()`
  - Call `setup_book_navigation()`
  - Call `create_landmarks_page()`
  - Call `process_and_add_fonts()`
  - Write EPUB
  - Inspection output
  - Call `_run_epubcheck_validation()`
- `_run_epubcheck_validation()` - **Keep in assemble.py** (or move to validation module later)
- `plan_build()` - **Keep in assemble.py** (high-level coordination)

## Implementation Order

### Phase 1: Low-Risk Extractions
1. ✅ Create `epub_metadata.py` - Pure data setup, minimal dependencies
2. ✅ Create `epub_css.py` - Self-contained CSS handling
3. ✅ Create `epub_pages.py` - Static page generation

### Phase 2: Resource Processing
4. ✅ Create `epub_resources.py` - Image and font processing

### Phase 3: Complex Logic
5. ✅ Create `epub_chapters.py` - Chapter processing with heading detection
6. ✅ Create `epub_navigation.py` - ToC and navigation structure

### Phase 4: Integration
7. ✅ Refactor `assemble_epub()` to use new modules
8. ✅ Update all imports
9. ✅ Run full test suite
10. ✅ Fix any broken tests
11. ✅ Verify EPUB output matches original

## Testing Strategy

### Unit Tests
- Each new module should have focused unit tests
- Test edge cases (missing files, invalid data)
- Mock ebooklib interactions where possible

### Integration Tests
- Test full EPUB assembly with various input combinations
- Verify output EPUB structure matches original
- Run EPUBCheck validation on test outputs

### Regression Tests
- Compare generated EPUBs before/after refactoring
- Ensure file sizes, structure, and content are identical
- Verify no functionality is lost

## Success Metrics

### Code Quality
- **Line count reduction:** assemble.py should drop from 1153 → ~300 lines
- **Complexity reduction:** Target complexity < 50 per module
- **Function length:** No function > 100 lines
- **Test coverage:** Maintain or improve current coverage

### Maintainability
- Each module has a single, clear responsibility
- Easy to locate and modify specific functionality
- Reduced cognitive load for developers

### Performance
- No performance regression (measure EPUB assembly time)
- Maintain current optimization levels (image processing, font subsetting)

## Risk Mitigation

### High Risk Areas
1. **Chapter processing logic** - Complex manual vs auto mode handling
2. **ToC building** - Nested structure with arbitrary depth
3. **Resource path validation** - Security implications
4. **Figure numbering** - Cross-references and consistency

### Mitigation Strategies
- Create comprehensive tests before refactoring
- Refactor incrementally with frequent test runs
- Keep original code commented until verification complete
- Use git branches for each phase
- Manual verification of generated EPUBs

## Rollback Plan

If issues arise:
1. Each phase is a separate git commit
2. Can rollback to last stable state
3. Original assemble.py preserved in git history
4. Tests ensure functional equivalence

## Timeline Estimate

- Phase 1 (Low-Risk): 2-3 hours
- Phase 2 (Resources): 1-2 hours
- Phase 3 (Complex Logic): 3-4 hours
- Phase 4 (Integration): 2-3 hours
- **Total:** 8-12 hours of focused work

## Notes

- Preserve all existing functionality - no features removed
- Maintain backward compatibility with existing code
- Document all module interfaces
- Update CLAUDE.md with new architecture
