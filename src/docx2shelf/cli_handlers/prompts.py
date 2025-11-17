"""Interactive metadata prompts for CLI - extracted from cli.py _prompt_missing()."""

from __future__ import annotations

import argparse
from pathlib import Path


def _prompt_missing(args: argparse.Namespace) -> argparse.Namespace:
    """Interactively prompt for missing required metadata.

    This function prompts the user for any metadata fields that are required
    but were not provided via command-line arguments. It also attempts to
    auto-detect cover images and load metadata from metadata.txt files.

    Args:
        args: The argument namespace from argparse

    Returns:
        The modified argument namespace with prompted values filled in
    """
    from ..prompts import (
        prompt,
        prompt_bool,
        prompt_select,
    )
    from ..metadata import parse_kv_file, build_output_filename
    import sys as _sys

    interactive = (not getattr(args, "no_prompt", False)) and _sys.stdin.isatty()

    # Ask for input path if not provided
    if not args.input and interactive:
        args.input = prompt("Path to manuscript file or folder", allow_empty=False)

    # Attempt to pre-load metadata from metadata.txt
    md_loaded = False
    if args.input:
        try:
            input_path = Path(args.input).expanduser()
            md_dir = input_path.parent if input_path.is_file() else input_path
            mfile = md_dir / "metadata.txt"
            if mfile.exists():
                from .utils import apply_metadata_dict
                apply_metadata_dict(args, parse_kv_file(mfile), md_dir)
                md_loaded = True
        except Exception:
            pass
    # If no input yet, try CWD metadata.txt and let it specify input
    if not md_loaded:
        mfile = Path.cwd() / "metadata.txt"
        if mfile.exists():
            md = parse_kv_file(mfile)
            from .utils import apply_metadata_dict
            apply_metadata_dict(args, md, Path.cwd())
            # If input now set, and a different dir holds another metadata.txt, merge it
            if args.input:
                d = Path(args.input).expanduser().resolve().parent
                if d != Path.cwd() and (d / "metadata.txt").exists():
                    _apply_metadata_dict(args, parse_kv_file(d / "metadata.txt"), d)

    # After potential docx selection, attempt to auto-detect or pick common cover file name
    if not args.cover and args.input:
        docx_path_tmp = Path(args.input).expanduser().resolve()
        docx_dir_tmp = docx_path_tmp.parent
        # Enumerate available image files (jpg/jpeg/png)
        cover_candidates = (
            [p.name for p in sorted(docx_dir_tmp.glob("*.jpg"))]
            + [p.name for p in sorted(docx_dir_tmp.glob("*.jpeg"))]
            + [p.name for p in sorted(docx_dir_tmp.glob("*.png"))]
        )
        # Prefer conventional cover names first if present
        conventional = [
            n for n in ("cover.jpg", "cover.jpeg", "cover.png") if (docx_dir_tmp / n).is_file()
        ]
        if conventional:
            # Move conventional names to the front of the candidate list
            cover_candidates = list(dict.fromkeys(conventional + cover_candidates))
        if interactive and cover_candidates:
            args.cover = prompt_select("Select cover image:", cover_candidates, default_index=1)

    if interactive:
        from .utils import print_checklist
        print_checklist(args)

    if not args.cover and interactive:
        # Offer a numeric pick of images in the folder, else prompt
        cwd = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        img_files = (
            [p.name for p in sorted(cwd.glob("*.jpg"))]
            + [p.name for p in sorted(cwd.glob("*.jpeg"))]
            + [p.name for p in sorted(cwd.glob("*.png"))]
        )
        if img_files:
            args.cover = prompt_select("Select cover image:", img_files, default_index=1)
        else:
            args.cover = prompt("Cover filename in this folder (jpg/png)", allow_empty=True)
    if not args.title and interactive:
        args.title = prompt("Book title", allow_empty=True)
    # Ask for author and language (respect provided values)
    if interactive:
        args.author = prompt("Author", default=args.author or "", allow_empty=True)
        args.language = prompt("Language (BCP-47)", default=args.language or "en")
    # Defaults already exist for author and language.
    # Optional metadata
    if interactive and (args.seriesName is None):
        args.seriesName = prompt("Series name (optional)", default="", allow_empty=True)
    if interactive and (args.seriesIndex is None) and args.seriesName:
        args.seriesIndex = prompt("Series index (optional)", default="", allow_empty=True)
    # Calibre-compatible sort fields
    if interactive and getattr(args, "title_sort", None) is None:
        setattr(args, "title_sort", prompt("Title sort (optional)", default="", allow_empty=True))
    if interactive and getattr(args, "author_sort", None) is None:
        setattr(args, "author_sort", prompt("Author sort (optional)", default="", allow_empty=True))
    if interactive and args.description is None:
        args.description = prompt("Description (optional)", default="", allow_empty=True)
    if interactive and args.isbn is None:
        args.isbn = prompt("ISBN-13 (optional)", default="", allow_empty=True)
    if interactive and args.publisher is None:
        args.publisher = prompt("Publisher (optional)", default="", allow_empty=True)
    if interactive and args.pubdate is None:
        args.pubdate = prompt(
            "Publication date YYYY-MM-DD (optional)", default="", allow_empty=True
        )
    if interactive and args.uuid is None:
        args.uuid = prompt("UUID (optional, auto if absent)", default="", allow_empty=True)
    if interactive and args.subjects is None:
        args.subjects = prompt("Subjects (comma-separated, optional)", default="", allow_empty=True)
    if interactive and args.keywords is None:
        args.keywords = prompt("Keywords (comma-separated, optional)", default="", allow_empty=True)

    # Conversion/layout options
    if interactive:
        args.split_at = prompt_select(
            "Split at:",
            ["h1", "h2", "pagebreak"],
            default_index={"h1": 1, "h2": 2, "pagebreak": 3}.get(args.split_at, 1),
        )
        args.theme = prompt_select(
            "Theme:",
            ["serif", "sans", "printlike"],
            default_index={"serif": 1, "sans": 2, "printlike": 3}.get(args.theme, 1),
        )
        args.hyphenate = prompt_select(
            "Hyphenate:", ["on", "off"], default_index={"on": 1, "off": 2}.get(args.hyphenate, 1)
        )
        args.justify = prompt_select(
            "Justify:", ["on", "off"], default_index={"on": 1, "off": 2}.get(args.justify, 1)
        )
        # Numeric picker for ToC depth
        default_idx = 1 if int(args.toc_depth) == 1 else 2
        sel = prompt_select("ToC depth:", ["1", "2"], default_index=default_idx)
        args.toc_depth = int(sel)

        # Chapter start mode selection
        mode_default = {"auto": 1, "manual": 2, "mixed": 3}.get(
            getattr(args, "chapter_start_mode", "auto"), 1
        )
        mode_sel = prompt_select(
            "Chapter detection:",
            ["auto (scan headings)", "manual (user-defined)", "mixed"],
            default_index=mode_default,
        )
        if mode_sel == "auto (scan headings)":
            args.chapter_start_mode = "auto"
        elif mode_sel == "manual (user-defined)":
            args.chapter_start_mode = "manual"
            # Prompt for chapter starts if not already provided
            if not getattr(args, "chapter_starts", None):
                chapter_input = prompt(
                    "Chapter start patterns (comma-separated):",
                    default="Chapter 1, Chapter 2, Chapter 3",
                )
                if chapter_input and chapter_input.strip():
                    args.chapter_starts = chapter_input.strip()
        else:  # mixed
            args.chapter_start_mode = "mixed"

        args.page_list = prompt_select(
            "Include page-list nav?",
            ["on", "off"],
            default_index={"on": 1, "off": 2}.get(args.page_list, 2),
        )
        args.page_numbers = prompt_select(
            "Show page number counters?",
            ["on", "off"],
            default_index={"on": 1, "off": 2}.get(args.page_numbers, 2),
        )
        args.cover_scale = prompt_select(
            "Cover scaling:",
            ["contain", "cover"],
            default_index={"contain": 1, "cover": 2}.get(args.cover_scale, 1),
        )
    # Optional assets
    if interactive and args.css is None:
        # Offer a numeric pick of CSS files in the folder
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        css_files = [p.name for p in sorted(base.glob("*.css"))]
        if css_files:
            choices = ["(none)"] + css_files
            sel = prompt_select("Extra CSS (optional):", choices, default_index=1)
            args.css = "" if sel == "(none)" else sel
        else:
            args.css = ""
    if interactive and args.embed_fonts is None:
        # Find directories that contain TTF/OTF files and offer a pick
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        dir_candidates = []
        for d in sorted([p for p in base.iterdir() if p.is_dir()]):
            if any((d.glob("*.ttf"))) or any((d.glob("*.otf"))):
                dir_candidates.append(d.name)
        if dir_candidates:
            choices = ["(none)"] + dir_candidates
            sel = prompt_select("Embed fonts directory (optional):", choices, default_index=1)
            args.embed_fonts = "" if sel == "(none)" else sel
        else:
            args.embed_fonts = ""
    if interactive and args.dedication is None:
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        txt_files = [p.name for p in sorted(base.glob("*.txt"))]
        if txt_files:
            choices = ["(none)"] + txt_files
            sel = prompt_select("Dedication .txt (optional):", choices, default_index=1)
            args.dedication = "" if sel == "(none)" else sel
        else:
            args.dedication = ""
    if interactive and args.ack is None:
        base = Path.cwd() if not args.input else Path(args.input).expanduser().resolve().parent
        txt_files = [p.name for p in sorted(base.glob("*.txt"))]
        if txt_files:
            choices = ["(none)"] + txt_files
            sel = prompt_select("Acknowledgements .txt (optional):", choices, default_index=1)
            args.ack = "" if sel == "(none)" else sel
        else:
            args.ack = ""
    # Validation
    if interactive:
        epub_default_idx = 1 if getattr(args, "epubcheck", None) in (True, None, "on") else 2
        args.epubcheck = prompt_select(
            "Validate with EPUBCheck if available?", ["on", "off"], default_index=epub_default_idx
        )

    if args.output is None and interactive:
        # Suggest computed output filename and allow override
        suggested = build_output_filename(
            title=args.title,
            series=args.seriesName or None,
            series_index=args.seriesIndex or None,
        )
        out = prompt("Output filename", default=suggested)
        args.output = out

    # Auto-generate a metadata.txt template next to input if missing (interactive)
    try:
        if interactive and args.input:
            from ..cli import run_init_metadata
            input_path = Path(args.input).expanduser()
            mpath = input_path.parent / "metadata.txt"
            if not mpath.exists():
                tmpl_ns = argparse.Namespace(
                    input=str(input_path),
                    cover=args.cover if args.cover else None,
                    output=None,
                    force=False,
                )
                run_init_metadata(tmpl_ns)
    except Exception:
        pass

    return args
