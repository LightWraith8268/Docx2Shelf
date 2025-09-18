from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .metadata import BuildOptions, EpubMetadata, build_output_filename, parse_date
from .tools import (
    epubcheck_cmd,
    install_epubcheck,
    install_pandoc,
    pandoc_path,
    tools_dir,
    uninstall_all_tools,
    uninstall_epubcheck,
    uninstall_pandoc,
)
from .update import check_for_updates
from .utils import (
    parse_kv_file,
    prompt,
    prompt_bool,
    prompt_select,
    sanitize_filename,
)


def _arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="docx2shelf",
        description="Convert a DOCX manuscript into a valid EPUB 3 (offline)",
    )
    sub = p.add_subparsers(dest="command", required=False)

    b = sub.add_parser("build", help="Build an EPUB from inputs")
    b.add_argument(
        "--input",
        type=str,
        help="Path to manuscript file or directory of files (.docx, .md, .txt, .html)",
    )
    b.add_argument("--cover", type=str, help="Path to cover image (jpg/png)")
    b.add_argument("--title", type=str, help="Book title")
    b.add_argument("--author", type=str, help="Author name")
    b.add_argument("--seriesName", type=str, help="Series name (optional)")
    b.add_argument("--seriesIndex", type=str, help="Series index/number (optional)")
    b.add_argument(
        "--title-sort", dest="title_sort", type=str, help="Calibre title sort (optional)"
    )
    b.add_argument(
        "--author-sort", dest="author_sort", type=str, help="Calibre author sort (optional)"
    )
    b.add_argument("--description", type=str, help="Long description (optional)")
    b.add_argument("--isbn", type=str, help="ISBN-13 digits only (optional)")
    b.add_argument("--language", type=str, default="en", help="Language code, e.g., en")
    b.add_argument("--publisher", type=str, help="Publisher (optional)")
    b.add_argument("--pubdate", type=str, help="Publication date ISO YYYY-MM-DD (optional)")
    b.add_argument("--uuid", type=str, help="UUID to use when no ISBN (optional)")
    b.add_argument("--subjects", type=str, help="Comma-separated subjects")
    b.add_argument("--keywords", type=str, help="Comma-separated keywords")

    b.add_argument(
        "--split-at",
        choices=["h1", "h2", "h3", "pagebreak", "mixed"],
        default="h1",
        help="How to split content into XHTML files",
    )
    b.add_argument(
        "--mixed-split-pattern",
        type=str,
        help="Mixed split pattern: 'h1,pagebreak' or 'h1:main,pagebreak:appendix' etc.",
    )
    # Import themes dynamically to get available themes
    try:
        from .themes import get_available_themes
        available_themes = get_available_themes()
    except ImportError:
        available_themes = ["serif", "sans", "printlike"]  # Fallback

    b.add_argument(
        "--theme",
        choices=available_themes,
        default="serif",
        help="Base CSS theme (use --list-themes to see all options)",
    )
    b.add_argument("--embed-fonts", type=str, help="Directory of TTF/OTF to embed")
    b.add_argument("--image-quality", type=int, default=85, help="JPEG/WebP quality for image compression (1-100)")
    b.add_argument("--image-max-width", type=int, default=1200, help="Maximum image width in pixels")
    b.add_argument("--image-max-height", type=int, default=1600, help="Maximum image height in pixels")
    b.add_argument("--image-format", choices=["original", "webp", "avif"], default="webp", help="Convert images to modern format")
    b.add_argument("--hyphenate", choices=["on", "off"], default="on")
    b.add_argument("--justify", choices=["on", "off"], default="on")
    b.add_argument("--toc-depth", type=int, default=2, help="Table of contents depth (1-6)")
    b.add_argument(
        "--chapter-start-mode",
        choices=["auto", "manual", "mixed"],
        default="auto",
        help="TOC chapter detection: auto (scan headings), manual (user-defined), mixed (both)",
    )
    b.add_argument(
        "--chapter-starts",
        type=str,
        help="Comma-separated list of chapter start text patterns for manual TOC mode",
    )
    b.add_argument(
        "--reader-start-chapter",
        type=str,
        help="Chapter title or pattern where reader should start (e.g., 'Chapter 1', 'Prologue')",
    )
    b.add_argument("--page-list", choices=["on", "off"], default="off")
    b.add_argument("--css", type=str, help="Path to extra CSS to merge (optional)")
    b.add_argument("--page-numbers", choices=["on", "off"], default="off")
    b.add_argument("--epub-version", type=str, default="3")
    b.add_argument("--cover-scale", choices=["contain", "cover"], default="contain")
    b.add_argument(
        "--font-size", dest="font_size", type=str, help="Base font size (e.g., 1rem, 12pt)"
    )
    b.add_argument(
        "--line-height", dest="line_height", type=str, help="Base line height (e.g., 1.5)"
    )

    b.add_argument("--dedication", type=str, help="Path to plain-text dedication (optional)")
    b.add_argument("--ack", type=str, help="Path to plain-text acknowledgements (optional)")

    b.add_argument("--output", type=str, help="Output .epub path (optional)")
    b.add_argument(
        "--output-pattern",
        dest="output_pattern",
        type=str,
        help="Filename pattern with placeholders {title}, {series}, {index}, {index2}",
    )
    b.add_argument("--inspect", action="store_true", help="Emit inspect folder with sources")
    b.add_argument("--dry-run", action="store_true", help="Print planned manifest/spine only")
    b.add_argument(
        "--epubcheck",
        choices=["on", "off"],
        default="on",
        help="Validate with EPUBCheck if available",
    )
    b.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt; use provided defaults and flags only",
    )
    b.add_argument(
        "--auto-install-tools",
        action="store_true",
        help="Automatically install Pandoc/EPUBCheck when missing (no prompts)",
    )
    b.add_argument(
        "--no-install-tools", action="store_true", help="Do not install tools even if missing"
    )
    b.add_argument(
        "--prompt-all", action="store_true", help="Prompt for every field even if prefilled"
    )
    b.add_argument("--quiet", action="store_true", help="Reduce output (errors only)")
    b.add_argument("--verbose", action="store_true", help="Increase output (extra diagnostics)")

    t = sub.add_parser(
        "init-metadata", help="Generate a metadata.txt template next to the input file"
    )
    t.add_argument(
        "--input", type=str, required=True, help="Path to manuscript file (.docx, .md, .txt)"
    )
    t.add_argument("--cover", type=str, help="Optional default cover path")
    t.add_argument(
        "--output",
        type=str,
        help="Optional path to write template (defaults to input folder/metadata.txt)",
    )
    t.add_argument("--force", action="store_true", help="Overwrite existing file if present")

    # --- List themes subcommand ---
    list_themes = sub.add_parser("list-themes", help="List available CSS themes")
    list_themes.add_argument(
        "--genre",
        help="Filter themes by genre (fantasy, romance, mystery, scifi, academic, general)",
    )

    m = sub.add_parser("tools", help="Manage optional tools (Pandoc, EPUBCheck)")
    m_sub = m.add_subparsers(dest="tool_cmd", required=True)
    mi = m_sub.add_parser("install", help="Install a tool")
    mi.add_argument("name", choices=["pandoc", "epubcheck"], help="Tool name")
    mi.add_argument("--version", dest="version", help="Tool version (optional)")
    mu = m_sub.add_parser("uninstall", help="Uninstall a tool")
    mu.add_argument("name", choices=["pandoc", "epubcheck", "all"], help="Tool name")
    m_sub.add_parser("where", help="Show tool locations")

    sub.add_parser("update", help="Update docx2shelf to the latest version")

    return p


def _apply_metadata_dict(args: argparse.Namespace, md: dict, base_dir: Path | None) -> None:
    if not md:
        return

    def get(k: str):
        # allow simple aliases
        aliases = {
            "series": "seriesName",
            "seriesname": "seriesName",
            "series_index": "seriesIndex",
            "seriesindex": "seriesIndex",
            "title-sort": "title_sort",
            "author-sort": "author_sort",
        }
        k2 = aliases.get(k.lower(), k)
        return md.get(k, md.get(k.lower(), md.get(k2, md.get(k2.lower()))))

    def pathify(val: str | None) -> str | None:
        if not val:
            return None
        p = Path(val)
        if not p.is_absolute() and base_dir:
            p = (base_dir / p).resolve()
        return str(p)

    # Core (file overrides defaults; CLI may still override if passed explicitly)
    if (not args.input) and get("input"):
        args.input = get("input")
    if (not args.cover) and get("cover"):
        args.cover = pathify(get("cover"))
    if (not args.title) and get("title"):
        args.title = get("title")
    if (not args.author) and get("author"):
        args.author = get("author")
    if (not args.language) and get("language"):
        args.language = get("language")
    # Optional metadata
    if get("seriesname") or get("series"):
        args.seriesName = get("seriesname") or get("series")
    if get("seriesindex"):
        args.seriesIndex = get("seriesindex")
    if get("title_sort") or get("title-sort"):
        setattr(args, "title_sort", get("title_sort") or get("title-sort"))
    if get("author_sort") or get("author-sort"):
        setattr(args, "author_sort", get("author_sort") or get("author-sort"))
    if get("description"):
        args.description = get("description")
    if get("isbn"):
        args.isbn = get("isbn")
    if get("publisher"):
        args.publisher = get("publisher")
    if get("pubdate"):
        args.pubdate = get("pubdate")
    if get("uuid"):
        args.uuid = get("uuid")
    if get("subjects"):
        args.subjects = get("subjects")
    if get("keywords"):
        args.keywords = get("keywords")
    # Conversion/layout
    if (args.split_at in (None, "", "h1")) and (get("split_at") or get("split-at")):
        args.split_at = get("split_at") or get("split-at")
    if (args.theme in (None, "", "serif")) and get("theme"):
        args.theme = get("theme")
    if (args.hyphenate in (None, "", "on")) and get("hyphenate"):
        args.hyphenate = get("hyphenate")
    if (args.justify in (None, "", "on")) and get("justify"):
        args.justify = get("justify")
    try:
        if get("toc_depth") and not getattr(args, "toc_depth_set", False):
            args.toc_depth = int(get("toc_depth"))
            setattr(args, "toc_depth_set", True)
    except Exception:
        pass
    if (getattr(args, "toc_depth", None) in (None, 2)) and get("toc_depth"):
        try:
            args.toc_depth = int(get("toc_depth"))
        except Exception:
            pass
    # Chapter start mode and patterns
    if (getattr(args, "chapter_start_mode", None) in (None, "auto")) and (
        get("chapter_start_mode") or get("chapter-start-mode")
    ):
        setattr(args, "chapter_start_mode", get("chapter_start_mode") or get("chapter-start-mode"))
    if (getattr(args, "chapter_starts", None) in (None, "")) and (
        get("chapter_starts") or get("chapter-starts")
    ):
        setattr(args, "chapter_starts", get("chapter_starts") or get("chapter-starts"))
    if (args.page_list in (None, "", "off")) and (get("page_list") or get("page-list")):
        args.page_list = get("page_list") or get("page-list")
    if (args.page_numbers in (None, "", "off")) and (get("page_numbers") or get("page-numbers")):
        args.page_numbers = get("page_numbers") or get("page-numbers")
    if (args.cover_scale in (None, "", "contain")) and (get("cover_scale") or get("cover-scale")):
        args.cover_scale = get("cover_scale") or get("cover-scale")
    # Typography options
    if getattr(args, "font_size", None) in (None, "") and (get("font_size") or get("font-size")):
        setattr(args, "font_size", get("font_size") or get("font-size"))
    if getattr(args, "line_height", None) in (None, "") and (
        get("line_height") or get("line-height")
    ):
        setattr(args, "line_height", get("line_height") or get("line-height"))
    # Assets
    if (getattr(args, "css", None) in (None, "")) and get("css"):
        args.css = pathify(get("css"))
    if (getattr(args, "embed_fonts", None) in (None, "")) and (
        get("embed_fonts") or get("embed-fonts")
    ):
        args.embed_fonts = pathify(get("embed_fonts") or get("embed-fonts"))
    if (getattr(args, "dedication", None) in (None, "")) and get("dedication"):
        args.dedication = pathify(get("dedication"))
    if (getattr(args, "ack", None) in (None, "")) and (
        get("ack") or get("acknowledgements") or get("acknowledgments")
    ):
        args.ack = pathify(get("ack") or get("acknowledgements") or get("acknowledgments"))
    # Output
    if (getattr(args, "output", None) in (None, "")) and get("output"):
        args.output = pathify(get("output"))
    if (getattr(args, "epubcheck", None) in (None, "on")) and get("epubcheck"):
        args.epubcheck = get("epubcheck")


def _print_checklist(args: argparse.Namespace) -> None:
    def checked(val) -> str:
        return "[x]" if (val is not None and str(val).strip() != "") else "[ ]"

    items = [
        ("Input", args.input),
        ("Cover", args.cover),
        ("Title", args.title),
        ("Author", args.author),
        ("Language", args.language),
        ("Series", args.seriesName),
        ("Series Index", args.seriesIndex),
        ("Title Sort", getattr(args, "title_sort", None)),
        ("Author Sort", getattr(args, "author_sort", None)),
        ("Description", args.description),
        ("ISBN", args.isbn),
        ("Publisher", args.publisher),
        ("PubDate", args.pubdate),
        ("UUID", args.uuid),
        ("Subjects", args.subjects),
        ("Keywords", args.keywords),
        ("Split At", args.split_at),
        ("Theme", args.theme),
        ("Hyphenate", args.hyphenate),
        ("Justify", args.justify),
        ("ToC Depth", getattr(args, "toc_depth", None)),
        ("Page List", args.page_list),
        ("Page Numbers", args.page_numbers),
        ("Cover Scale", args.cover_scale),
        ("Extra CSS", args.css),
        ("Fonts Dir", args.embed_fonts),
        ("Dedication", args.dedication),
        ("Acknowledgements", args.ack),
        ("EPUBCheck", getattr(args, "epubcheck", None)),
        ("Output", args.output),
    ]
    print("\n== Metadata Checklist ==")
    print("(Press Enter to skip/keep current when prompted)\n")
    for name, val in items:
        display = str(val) if val is not None and str(val).strip() != "" else "—"
        print(f" {checked(val)} {name}: {display}")
    print("")


def _prompt_missing(args: argparse.Namespace) -> argparse.Namespace:
    # Ask interactively for anything not provided on CLI.
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
                _apply_metadata_dict(args, parse_kv_file(mfile), md_dir)
                md_loaded = True
        except Exception:
            pass
    # If no input yet, try CWD metadata.txt and let it specify input
    if not md_loaded:
        mfile = Path.cwd() / "metadata.txt"
        if mfile.exists():
            md = parse_kv_file(mfile)
            _apply_metadata_dict(args, md, Path.cwd())
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
        _print_checklist(args)

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


def _print_metadata_summary(meta: EpubMetadata, opts: BuildOptions, output: Path | None) -> None:
    def mark(val):
        return "[x]" if val else "[ ]"

    print("\n== Metadata Summary ==")
    print(f" {mark(meta.title)} Title: {meta.title or '—'}")
    print(f" {mark(meta.author)} Author: {meta.author or '—'}")
    print(f" {mark(meta.language)} Language: {meta.language or '—'}")
    print(f" {mark(meta.isbn or meta.uuid)} Identifier: {'ISBN '+meta.isbn if meta.isbn else (meta.uuid or '—')}")
    if meta.series:
        print(f" {mark(meta.series)} Series: {meta.series} #{meta.series_index or '—'}")
    print(f" {mark(meta.publisher)} Publisher: {meta.publisher or '—'}")
    print(f" {mark(meta.pubdate)} PubDate: {meta.pubdate.isoformat() if meta.pubdate else '—'}")
    print(f" {mark(bool(meta.subjects))} Subjects: {', '.join(meta.subjects) if meta.subjects else '—'}")
    print(f" {mark(bool(meta.keywords))} Keywords: {', '.join(meta.keywords) if meta.keywords else '—'}")
    print(f" {mark(meta.cover_path)} Cover: {meta.cover_path}")
    print(f" {mark(opts.extra_css)} Extra CSS: {opts.extra_css or '—'}  | Fonts: {opts.embed_fonts_dir or '—'}")
    # Show chapter mode information
    if opts.chapter_start_mode == "manual" and opts.chapter_starts:
        chapter_list = (
            opts.chapter_starts[:3]
            if isinstance(opts.chapter_starts, list)
            else opts.chapter_starts.split(",")[:3]
        )
        display_chapters = ", ".join(chapter_list) + ("..." if len(chapter_list) > 3 else "")
        print(f" {mark(opts.chapter_starts)} Chapter Mode: manual ({display_chapters})")
    elif opts.chapter_start_mode == "mixed":
        print(" [x] Chapter Mode: mixed (custom + auto)")
    else:
        print(" [x] Chapter Mode: auto (scan headings)")
    print(f" Output: {output or '—'}\n")


def run_build(args: argparse.Namespace) -> int:
    from .assemble import assemble_epub, plan_build
    from .convert import convert_file_to_html, split_html_by_heading, split_html_by_pagebreak, split_html_by_heading_level, split_html_mixed

    # Validate paths
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}", file=sys.stderr)
        return 2

    input_dir = input_path.parent if input_path.is_file() else input_path

    cover_path_candidate = Path(args.cover).expanduser()
    if not cover_path_candidate.is_absolute():
        cover_path_candidate = input_dir / cover_path_candidate
    cover_path = cover_path_candidate.resolve()

    if not cover_path.is_file():
        print(f"Error: cover not found: {cover_path}", file=sys.stderr)
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

        for file in files_to_process:
            print(f" - Processing {file.name}...")
            try:
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
    from .metadata import normalize_lang, validate_lang_code

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
        epubcheck=(
            (args.epubcheck == "on")
            if isinstance(args.epubcheck, str)
            else bool(getattr(args, "epubcheck", True))
        ),
        font_size=(getattr(args, "font_size", None) or None),
        line_height=(getattr(args, "line_height", None) or None),
        quiet=bool(getattr(args, "quiet", False)),
        verbose=bool(getattr(args, "verbose", False)),
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
        mixed_pattern = getattr(args, 'mixed_split_pattern', None)
        html_chunks = split_html_mixed(combined, mixed_pattern)

    plan = plan_build(meta, opts, html_chunks, resources)
    _print_metadata_summary(meta, opts, None if not args.output else Path(args.output))

    if args.dry_run:
        print("-- Dry Run: Planned manifest/spine --")
        for line in plan:
            print(line)
        return 0

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

    # Resolve output relative to input dir if relative
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = input_dir / out_path

    # Sanitize name and ensure .epub extension
    name = out_path.name
    if not name.lower().endswith(".epub"):
        name = sanitize_filename(name) + ".epub"
    out_path = out_path.with_name(name)

    output = out_path.resolve()
    # Combine all styles CSS
    combined_styles_css = "\n".join(all_styles_css)
    assemble_epub(meta, opts, html_chunks, resources, output, combined_styles_css)
    print(f"Wrote: {output}")
    if opts.inspect:
        print("Inspect folder emitted for debugging.")
    return 0


def run_list_themes(args: argparse.Namespace) -> int:
    """List available CSS themes."""
    try:
        from .themes import list_all_themes, get_themes_by_genre, get_theme_info

        if args.genre:
            themes = get_themes_by_genre(args.genre)
            if not themes:
                print(f"No themes found for genre: {args.genre}")
                return 1

            print(f"Themes for {args.genre}:")
            for theme in themes:
                print(f"  {get_theme_info(theme)}")
        else:
            print(list_all_themes())

        return 0
    except ImportError:
        print("Theme discovery not available. Available themes: serif, sans, printlike")
        return 1


def run_init_metadata(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file() or input_path.suffix.lower() not in {
        ".docx",
        ".md",
        ".txt",
        ".html",
        ".htm",
    }:
        print(f"Error: Input file not found or not a supported type: {input_path}", file=sys.stderr)
        return 2
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.parent / "metadata.txt"
    )
    if out_path.exists() and not args.force:
        print(
            f"Refusing to overwrite existing file: {out_path}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 2

    title_guess = input_path.stem.replace("_", " ").replace("-", " ").strip().title()
    from .metadata import build_output_filename

    output_guess = build_output_filename(title_guess, None, None)

    lines = [
        "# Docx2Shelf metadata template",
        "# Lines starting with # are ignored. Keys are case-insensitive.",
        "# Use key: value or key=value. Paths can be relative to this DOCX folder.",
        "# Output naming (optional): you can pass --output-pattern on the CLI",
                '# Example: --output-pattern "{series}-{index2}-{title}"',
        "",
        f"Title: {title_guess}",
        "Author:",
        "Language: en",
        "",
        "# Optional metadata",
        "SeriesName:",
        "SeriesIndex:",
        "Title-Sort:",
        "Author-Sort:",
        "Description:",
        "ISBN:",
        "Publisher:",
        "PubDate: 2024-01-01",
        "UUID:",
        "Subjects: ",
        "Keywords: ",
        "",
        "# Assets",
        f"Cover: {args.cover or ''}",
        "CSS:",
        "Embed-Fonts:",
        "",
        "# Conversion & layout",
        "Theme: serif",
        "Split-At: h1",
        "ToC_Depth: 2",
        "Chapter-Start-Mode: auto",
        "Chapter-Starts:",
        "Hyphenate: on",
        "Justify: on",
        "Page-List: off",
        "Page-Numbers: off",
        "Cover-Scale: contain",
        "",
        "# Output & validation",
        f"Output: {output_guess}",
        "EPUBCheck: on",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote template: {out_path}")
    return 0


def run_tools(args: argparse.Namespace) -> int:
    if args.tool_cmd == "install":
        if args.name == "pandoc":
            p = install_pandoc(args.version) if args.version else install_pandoc()
            print(f"Installed pandoc at: {p}")
            return 0
        if args.name == "epubcheck":
            p = install_epubcheck(args.version) if args.version else install_epubcheck()
            print(f"Installed epubcheck at: {p}")
            return 0
    if args.tool_cmd == "where":
        td = tools_dir()
        print(f"Tools dir: {td}")
        print(f"Pandoc: {pandoc_path()}")
        print(f"EPUBCheck: {epubcheck_cmd()}")
        return 0
    if args.tool_cmd == "uninstall":
        if args.name == "pandoc":
            uninstall_pandoc()
            print("Removed Pandoc from tools cache (if present).")
            return 0
        if args.name == "epubcheck":
            uninstall_epubcheck()
            print("Removed EPUBCheck from tools cache (if present).")
            return 0
        if args.name == "all":
            uninstall_all_tools()
            print("Removed all managed tools from tools cache (if present).")
            return 0
    return 1


def run_update(args: argparse.Namespace) -> int:
    import subprocess

    print("Checking for updates...")
    check_for_updates()  # This will print if there is an update
    if prompt_bool("Do you want to try upgrading now?", default=True):
        try:
            subprocess.run(["pipx", "upgrade", "docx2shelf"], check=True)
            print("Update successful!")
            return 0
        except FileNotFoundError:
            print(
                "Error: pipx not found. Please make sure pipx is installed and in your PATH.",
                file=sys.stderr,
            )
            return 1
        except subprocess.CalledProcessError as e:
            print(f"Error during update: {e}", file=sys.stderr)
            return 1
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Perform a quick update check in a background thread if not running update command
    if not (argv and "update" in argv[0]):
        import threading

        update_thread = threading.Thread(target=check_for_updates)
        update_thread.start()

    if not argv:
        # Default to interactive build when no args are provided
        argv = ["build"]
    parser = _arg_parser()
    args = parser.parse_args(argv)

    if args.command == "build":
        args = _prompt_missing(args)
        return run_build(args)
    if args.command == "init-metadata":
        return run_init_metadata(args)
    if args.command == "list-themes":
        return run_list_themes(args)
    if args.command == "tools":
        return run_tools(args)
    if args.command == "update":
        return run_update(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
