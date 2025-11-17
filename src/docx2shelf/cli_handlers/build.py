"""Build command handler - extracted from cli.py run_build().

This module implements the complete build workflow for converting documents to EPUB format.
It handles validation, metadata preparation, document conversion, EPUB assembly, and validation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_build(args: argparse.Namespace) -> int:
    """Execute the complete EPUB build workflow.

    This function orchestrates the entire build process including:
    - Path validation and normalization
    - Document conversion (DOCX, MD, TXT, HTML to HTML chunks)
    - Metadata validation and enhancement (including AI features)
    - EPUB assembly
    - Post-build validation with EPUBCheck
    - Performance monitoring

    Args:
        args: Parsed command-line arguments containing build options

    Returns:
        Exit code: 0 for success, 1 for user cancellation, 2 for validation errors, 3 for EPUB validation failures
    """
    from ..assemble import assemble_epub, plan_build
    from ..convert import (
        convert_file_to_html,
        split_html_by_heading,
        split_html_by_heading_level,
        split_html_by_pagebreak,
        split_html_mixed,
    )
    from ..performance import PerformanceMonitor
    from ..metadata import (
        EpubMetadata,
        BuildOptions,
        parse_date,
        validate_isbn13,
        normalize_lang,
        validate_lang_code,
        build_output_filename,
    )
    from ..security import (
        normalize_path,
        is_safe_path,
        safe_filename,
        sanitize_filename,
        ensure_unicode_path,
    )
    from ..error_handling import handle_error
    from ..tools import pandoc_path, install_pandoc, epubcheck_cmd, install_epubcheck
    from ..prompts import prompt_bool
    from ..ai_features import get_ai_manager, enhance_metadata_with_ai, detect_genre_with_ai
    from ..cli import (
        _apply_metadata_dict,
        _print_checklist,
        _print_metadata_summary,
        _run_preview_mode,
        _read_document_content,
    )

    # Initialize performance monitoring for the entire build process
    build_monitor = PerformanceMonitor()
    build_monitor.start_monitoring()

    # Initialize JSON logger if requested
    json_logger = None
    if getattr(args, "json_output", None):
        from ..json_logger import init_json_logger

        json_logger = init_json_logger(Path(args.json_output))

    # Apply profile settings if specified
    if getattr(args, "profile", None):
        try:
            from ..profiles import apply_profile_to_args

            apply_profile_to_args(args, args.profile)
            if not getattr(args, "quiet", False):
                print(f"[PROFILE] Applied profile: {args.profile}")
        except ImportError:
            print("Warning: Profile system not available", file=sys.stderr)
        except Exception as e:
            print(f"Error applying profile: {e}", file=sys.stderr)
            return 1

    # Validate paths with enhanced error handling
    try:
        # Normalize and validate input path
        input_path = normalize_path(Path(args.input).expanduser())
        if not is_safe_path(input_path):
            print(
                f"Error: Input path contains invalid characters or directory traversal: {input_path}"
            )
            return 1

        input_path = input_path.resolve()
        if not input_path.exists():
            # Use enhanced error handling for missing input files
            handled = handle_error(
                error=FileNotFoundError(f"Input file not found: {input_path}"),
                operation="input file validation",
                file_path=input_path,
                interactive=True,
            )
            if not handled:
                print(f"Error: Input path not found: {input_path}", file=sys.stderr)
                return 2

        input_dir = input_path.parent if input_path.is_file() else input_path

        # Normalize cover path with safety checks
        cover_path_candidate = normalize_path(Path(args.cover).expanduser())
        if not is_safe_path(cover_path_candidate, input_dir):
            # Try relative to input directory
            safe_cover_name = safe_filename(args.cover)
            cover_path_candidate = input_dir / safe_cover_name

        if not cover_path_candidate.is_absolute():
            cover_path_candidate = input_dir / cover_path_candidate
        cover_path = cover_path_candidate.resolve()

        if not cover_path.is_file():
            # Use enhanced error handling for missing cover files
            handled = handle_error(
                error=FileNotFoundError(f"Cover file not found: {cover_path}"),
                operation="cover file validation",
                file_path=cover_path,
                interactive=True,
            )
            if not handled:
                print(f"Error: cover not found: {cover_path}", file=sys.stderr)
                return 2

    except Exception as e:
        # Handle unexpected validation errors
        handled = handle_error(error=e, operation="file path validation", interactive=True)
        if not handled:
            print(f"Error validating paths: {e}", file=sys.stderr)
            return 2

    # --- Input file handling ---
    html_chunks = []
    resources = []
    all_styles_css = []

    supported_extensions = {".docx", ".md", ".txt", ".html", ".htm"}

    if input_path.is_dir():
        print("Input is a directory, processing supported files in alphabetical order...")
        files_to_process = sorted(
            [
                p
                for p in input_path.iterdir()
                if p.is_file() and p.suffix.lower() in supported_extensions
            ]
        )
        if not files_to_process:
            print(f"Error: No supported files found in directory: {input_path}", file=sys.stderr)
            return 2

        with build_monitor.phase_timer("batch_conversion"):
            for file in files_to_process:
                print(f" - Processing {file.name}...")
                try:
                    with build_monitor.phase_timer(f"convert_{file.name}"):
                        chunks, res, styles_css = convert_file_to_html(file)
                    html_chunks.extend(chunks)
                    resources.extend(res)
                    # Collect styles CSS from all files
                    if styles_css and styles_css not in all_styles_css:
                        all_styles_css.append(styles_css)
                except (RuntimeError, ValueError) as e:
                    print(f"Error converting {file.name}: {e}", file=sys.stderr)
                    return 2
    elif input_path.is_file():
        if input_path.suffix.lower() not in supported_extensions:
            print(f"Error: Unsupported file type: {input_path.suffix}", file=sys.stderr)
            return 2
        try:
            with build_monitor.phase_timer("file_conversion"):
                html_chunks, resources, styles_css = convert_file_to_html(input_path)
            all_styles_css = [styles_css] if styles_css else []
        except (RuntimeError, ValueError) as e:
            print(f"Error converting {input_path.name}: {e}", file=sys.stderr)
            return 2
    else:
        print(f"Error: Input path is not a file or directory: {input_path}", file=sys.stderr)
        return 2

    # Basic validations
    if args.isbn:
        from .metadata import validate_isbn13

        if not validate_isbn13(args.isbn):
            print(
                "Error: Invalid ISBN-13. Provide 13 digits with a valid checksum.",
                file=sys.stderr,
            )
            return 2
    if cover_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        print("Error: Cover must be a .jpg, .jpeg, or .png image.", file=sys.stderr)
        return 2

    # Language normalization/validation
    args.language = normalize_lang(args.language)
    if not validate_lang_code(args.language):
        print("Error: Language must be a BCP-47 code like 'en' or 'en-us'.", file=sys.stderr)
        return 2

    if not args.title or str(args.title).strip() == "":
        print("Error: Title is required.", file=sys.stderr)
        return 2

    meta = EpubMetadata(
        title=args.title,
        author=args.author or "Unknown Author",
        language=args.language or "en",
        description=(args.description or None),
        isbn=(args.isbn or None),
        publisher=(args.publisher or None),
        pubdate=parse_date(args.pubdate) if args.pubdate else None,
        uuid=(args.uuid or None),
        series=(args.seriesName or None),
        series_index=(args.seriesIndex or None),
        title_sort=(getattr(args, "title_sort", "") or None),
        author_sort=(getattr(args, "author_sort", "") or None),
        subjects=[s.strip() for s in (args.subjects or "").split(",") if s.strip()],
        keywords=[s.strip() for s in (args.keywords or "").split(",") if s.strip()],
        cover_path=cover_path,
    )

    # AI Enhancement Integration
    if getattr(args, "ai_enhance", False) or getattr(args, "ai_genre", False):
        ai_manager = get_ai_manager()
        if ai_manager.is_available():
            try:
                # Read document content for AI analysis
                content = _read_document_content(input_path)
                if content:
                    # AI metadata enhancement
                    if getattr(args, "ai_enhance", False):
                        if not getattr(args, "quiet", False):
                            print("[AI] Enhancing metadata with AI...")
                        enhanced = enhance_metadata_with_ai(
                            content, meta, interactive=getattr(args, "ai_interactive", False)
                        )
                        meta = enhanced.original
                        if not getattr(args, "quiet", False) and enhanced.applied_suggestions:
                            print(
                                f"[AI] Applied {len(enhanced.applied_suggestions)} AI metadata suggestions"
                            )

                    # AI genre detection
                    if getattr(args, "ai_genre", False):
                        if not getattr(args, "quiet", False):
                            print("[AI] Detecting genres with AI...")
                        genre_result = detect_genre_with_ai(
                            content,
                            {
                                "title": meta.title,
                                "author": meta.author,
                                "description": meta.description or "",
                            },
                        )
                        if genre_result.genres and not hasattr(meta, "genre"):
                            meta.genre = genre_result.genres[0].genre
                        if genre_result.keywords and not meta.keywords:
                            meta.keywords = genre_result.keywords[:10]
                        if not getattr(args, "quiet", False):
                            print(f"[AI] AI detected genre: {getattr(meta, 'genre', 'None')}")

            except Exception as e:
                if not getattr(args, "quiet", False):
                    print(f"[WARNING] AI enhancement failed: {e}")
        else:
            if not getattr(args, "quiet", False):
                print("[WARNING] AI features requested but not available")

    # Apply store profile optimizations if specified
    if getattr(args, "store_profile", None):
        try:
            from .store_profiles import StoreProfile, StoreProfileManager

            profile = StoreProfile(args.store_profile)
            manager = StoreProfileManager()

            # Apply store-specific CSS optimizations
            store_css = manager.generate_store_css(profile)
            if not getattr(args, "quiet", False):
                print(f"[STORE] Applied {profile.value} optimization profile")

            # Store the store profile for later use in BuildOptions
            args._store_profile_css = store_css
            args._store_profile_enum = profile

        except ImportError:
            print("Warning: Store profile system not available", file=sys.stderr)
        except Exception as e:
            print(f"Error applying store profile: {e}", file=sys.stderr)

    # Resolve optional resource paths relative to input dir
    def _resolve_rel_to_input(path_str: str | None) -> Path | None:
        if not path_str:
            return None
        p = Path(path_str).expanduser()
        if not p.is_absolute():
            p = input_dir / p
        return p.resolve()

    css_path = _resolve_rel_to_input(args.css) if getattr(args, "css", None) else None
    fonts_dir = (
        _resolve_rel_to_input(args.embed_fonts) if getattr(args, "embed_fonts", None) else None
    )
    dedication_path = (
        _resolve_rel_to_input(args.dedication) if getattr(args, "dedication", None) else None
    )
    ack_path = _resolve_rel_to_input(args.ack) if getattr(args, "ack", None) else None

    # Parse chapter starts if provided
    chapter_starts = None
    if getattr(args, "chapter_starts", None):
        chapter_starts = [s.strip() for s in args.chapter_starts.split(",") if s.strip()]

    # Validate ToC depth
    toc_depth = max(1, min(6, int(args.toc_depth)))

    opts = BuildOptions(
        split_at=args.split_at,
        theme=args.theme,
        embed_fonts_dir=fonts_dir,
        image_quality=args.image_quality,
        image_max_width=args.image_max_width,
        image_max_height=args.image_max_height,
        image_format=args.image_format,
        enhanced_images=getattr(args, "enhanced_images", False),
        vertical_writing=args.vertical_writing,
        epub2_compat=args.epub2_compat,
        hyphenate=args.hyphenate == "on",
        justify=args.justify == "on",
        toc_depth=toc_depth,
        chapter_start_mode=getattr(args, "chapter_start_mode", "auto"),
        chapter_starts=chapter_starts,
        mixed_split_pattern=getattr(args, "mixed_split_pattern", None),
        reader_start_chapter=getattr(args, "reader_start_chapter", None),
        page_list=args.page_list == "on",
        extra_css=css_path,
        page_numbers=args.page_numbers == "on",
        epub_version=str(args.epub_version),
        cover_scale=args.cover_scale,
        dedication_txt=dedication_path,
        ack_txt=ack_path,
        inspect=args.inspect,
        dry_run=args.dry_run,
        preview=args.preview,
        preview_port=args.preview_port,
        epubcheck=(
            (args.epubcheck == "on")
            if isinstance(args.epubcheck, str)
            else bool(getattr(args, "epubcheck", True))
        ),
        font_size=(getattr(args, "font_size", None) or None),
        line_height=(getattr(args, "line_height", None) or None),
        quiet=bool(getattr(args, "quiet", False)),
        verbose=bool(getattr(args, "verbose", False)),
        store_profile_css=getattr(args, "_store_profile_css", None),
    )

    # Prefill from DOCX core properties if missing
    if (
        input_path.is_file()
        and input_path.suffix.lower() == ".docx"
        and (not args.title or not args.author)
    ):
        try:
            from docx import Document  # type: ignore

            d = Document(str(input_path))
            core = getattr(d, "core_properties", None)
            if core:
                if not args.title and getattr(core, "title", None):
                    args.title = core.title
                if (not args.author) and getattr(core, "author", None):
                    args.author = core.author
        except Exception:
            pass

    # Offer to install Pandoc/EPUBCheck if missing (interactive only)
    interactive_build = (not getattr(args, "no_prompt", False)) and sys.stdin.isatty()
    allow_install = not bool(getattr(args, "no_install_tools", False))
    if allow_install:
        # Pandoc
        try:
            if pandoc_path() is None:
                if getattr(args, "auto_install_tools", False):
                    p = install_pandoc()
                    if not getattr(args, "quiet", False):
                        print(f"Installed Pandoc at: {p}")
                elif interactive_build:
                    if prompt_bool("Pandoc not found. Install now?", default=True):
                        p = install_pandoc()
                        if not getattr(args, "quiet", False):
                            print(f"Installed Pandoc at: {p}")
        except Exception as e:
            print(f"Pandoc install failed: {e}", file=sys.stderr)
        # EPUBCheck
        try:
            ep_on = (
                (args.epubcheck == "on")
                if isinstance(args.epubcheck, str)
                else bool(getattr(args, "epubcheck", True))
            )
            if ep_on and epubcheck_cmd() is None:
                if getattr(args, "auto_install_tools", False):
                    j = install_epubcheck()
                    if not getattr(args, "quiet", False):
                        print(f"Installed EPUBCheck jar: {j}")
                elif interactive_build:
                    if prompt_bool("EPUBCheck not found. Install now?", default=True):
                        j = install_epubcheck()
                        if not getattr(args, "quiet", False):
                            print(f"Installed EPUBCheck jar: {j}")
        except Exception as e:
            print(f"EPUBCheck install failed: {e}", file=sys.stderr)

    # Apply split strategy if needed
    if args.split_at in {"h1", "h2"}:
        combined = "".join(html_chunks)
        html_chunks = split_html_by_heading(combined, level=args.split_at)
    elif args.split_at in {"h3", "h4", "h5", "h6"}:
        combined = "".join(html_chunks)
        html_chunks = split_html_by_heading_level(combined, level=args.split_at)
    elif args.split_at == "pagebreak":
        combined = "".join(html_chunks)
        html_chunks = split_html_by_pagebreak(combined)
    elif args.split_at == "mixed":
        combined = "".join(html_chunks)
        mixed_pattern = getattr(args, "mixed_split_pattern", None)
        html_chunks = split_html_mixed(combined, mixed_pattern)

    plan = plan_build(meta, opts, html_chunks, resources)
    _print_metadata_summary(meta, opts, None if not args.output else Path(args.output))

    if args.dry_run:
        print("-- Dry Run: Planned manifest/spine --")
        for line in plan:
            print(line)
        return 0

    # Handle preview mode
    if args.preview:
        return _run_preview_mode(meta, opts, html_chunks, resources, args)

    # Confirm to proceed if interactive
    interactive = (not getattr(args, "no_prompt", False)) and sys.stdin.isatty()
    if interactive:
        proceed = prompt_bool("Proceed to build now?", default=True)
        if not proceed:
            print("Cancelled.")
            return 1

    # Compute default output name if missing
    if not args.output:
        if getattr(args, "output_pattern", None):
            from .metadata import render_output_pattern

            stem = render_output_pattern(
                args.output_pattern,
                title=args.title,
                series=args.seriesName or None,
                series_index=args.seriesIndex or None,
            )
            args.output = stem if stem.lower().endswith(".epub") else f"{stem}.epub"
        else:
            args.output = build_output_filename(
                title=args.title,
                series=args.seriesName or None,
                series_index=args.seriesIndex or None,
            )

    # Resolve output relative to input dir if relative with safety checks
    out_path = normalize_path(Path(args.output))
    if not is_safe_path(out_path):
        # Sanitize the output filename
        safe_output_name = safe_filename(args.output)
        out_path = Path(safe_output_name)

    if not out_path.is_absolute():
        out_path = input_dir / out_path

    out_path = ensure_unicode_path(out_path)

    # Sanitize name and ensure .epub extension
    name = out_path.name
    if not name.lower().endswith(".epub"):
        name = sanitize_filename(name) + ".epub"
    out_path = out_path.with_name(name)

    output = out_path.resolve()
    # Combine all styles CSS
    combined_styles_css = "\n".join(all_styles_css)

    # Final assembly phase with performance monitoring
    with build_monitor.phase_timer("epub_assembly"):
        assemble_epub(
            meta, opts, html_chunks, resources, output, combined_styles_css, build_monitor
        )

    # EPUB validation phase
    if getattr(args, "epubcheck", "on") == "on" and output.exists():
        from .validation import print_validation_report, validate_epub

        if not getattr(args, "quiet", False):
            print("\n[VALIDATION] Validating EPUB quality...")

        with build_monitor.phase_timer("epub_validation"):
            validation_result = validate_epub(output, custom_checks=True, timeout=120)

        if not getattr(args, "quiet", False):
            print_validation_report(validation_result, verbose=getattr(args, "verbose", False))

        # Exit with error code if validation failed with errors
        if validation_result.has_errors:
            print(
                f"\n[ERROR] EPUB validation failed with {len(validation_result.errors)} critical error(s)."
            )
            print("Please fix the errors above before distributing your EPUB.")
            return 3  # Different exit code for validation failures

    # Stop monitoring and display performance summary
    build_monitor.stop_monitoring()
    if not getattr(args, "quiet", False):
        print(f"\n📊 Performance Summary:\n{build_monitor.get_summary()}")

    print(f"Wrote: {output}")
    if opts.inspect:
        print("Inspect folder emitted for debugging.")
    return 0

