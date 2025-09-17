from __future__ import annotations

import re
import uuid as _uuid
from importlib import resources
from pathlib import Path

from .metadata import BuildOptions, EpubMetadata


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_css(theme: str, extra_css: Path | None, opts: BuildOptions, styles_css: str = "") -> bytes:
    # Load packaged CSS: docx2shelf/assets/css/<theme>.css
    try:
        css_path = resources.files("docx2shelf.assets.css").joinpath(f"{theme}.css")
        with css_path.open("r", encoding="utf-8") as fh:
            css = fh.read()
    except Exception:
        css = ""
    if opts.font_size:
        css += f"\nhtml {{ font-size: {opts.font_size}; }}\n"
    if opts.line_height:
        css += f"\nhtml {{ line-height: {opts.line_height}; }}\n"
    if opts.justify:
        css += "\n" + "p { text-align: justify; }\n"
    if not opts.hyphenate:
        css += "\n" + "html { hyphens: manual; }\n"
    # Ensure images fit viewport and preserve aspect ratio
    css += "\nimg { max-width: 100%; height: auto; }\n"
    if opts.cover_scale == "contain":
        css += "\nimg[alt='Cover'] { max-width: 100%; height: auto; }\n"
    elif opts.cover_scale == "cover":
        css += (
            "\n/* 'cover' scaling hint; support varies across readers */\n"
            "img[alt='Cover'] { width: 100%; height: auto; }\n"
        )
    if opts.page_numbers:
        css += (
            "\n/* page number counters on h1/h2 (informational) */\n"
            "h1::before, h2::before { counter-increment: page; content: counter(page) '\\a0'; }\n"
        )
    # Add styles from styles.json
    if styles_css:
        css += "\n/* styles from styles.json */\n" + styles_css
    if extra_css and extra_css.exists():
        css += "\n/* user css */\n" + extra_css.read_text(encoding="utf-8")
    return css.encode("utf-8")


def _html_item(title: str, file_name: str, content: str, lang: str):
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e
    item = epub.EpubHtml(title=title, file_name=file_name, lang=lang)
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content
    item.set_content(content_bytes)
    return item


def _inject_heading_ids(html: str, chap_idx: int) -> tuple[str, str, list[tuple[str, str]]]:
    """Ensure first h1 has an id and collect h2 headings with ids.

    Returns: (html, h1_id, [(h2_title, h2_id), ...])
    """
    h1_id = f"ch{chap_idx:03d}"

    # Add id to first h1 if missing
    def h1_repl(match):
        tag_open = match.group(1)
        inside = match.group(2)
        if re.search(r"\bid=\"[^\"]+\"", tag_open):
            # keep existing attributes and id
            return f"<h1{tag_open}>{inside}</h1>"
        # inject id preserving other attributes
        return f'<h1{tag_open} id="{h1_id}">{inside}</h1>'

    pattern_h1 = r"<h1([^>]*)>(.*?)</h1>"
    html2 = re.sub(pattern_h1, h1_repl, html, count=1, flags=re.IGNORECASE | re.DOTALL)

    # Ensure h2 have ids; then collect titles + ids
    sec_idx = 0

    def h2_repl(match):
        nonlocal sec_idx
        sec_idx += 1
        tag_open = match.group(1)
        inside = match.group(2)
        if re.search(r"\bid=\"[^\"]+\"", tag_open):
            return f"<h2{tag_open}>{inside}</h2>"
        hid = f"{h1_id}-s{sec_idx:02d}"
        return f'<h2{tag_open} id="{hid}">{inside}</h2>'

    html3 = re.sub(r"<h2([^>]*)>(.*?)</h2>", h2_repl, html2, flags=re.IGNORECASE | re.DOTALL)

    titles = re.findall(r"<h2[^>]*>(.*?)</h2>", html3, flags=re.IGNORECASE | re.DOTALL)
    ids = re.findall(r"<h2[^>]*id=\"([^\"]+)\"[^>]*>", html3, flags=re.IGNORECASE)
    h2_items = [(re.sub(r"<[^>]+>", "", t), ids[i]) for i, t in enumerate(titles) if i < len(ids)]

    # Determine h1 id actually present
    m = re.search(r"<h1[^>]*id=\"([^\"]+)\"[^>]*>", html3, flags=re.IGNORECASE)
    if m:
        h1_id = m.group(1)
    return html3, h1_id, h2_items


def _find_chapter_starts(
    html_chunks: list[str], chapter_starts: list[str]
) -> list[tuple[str, int]]:
    """Find user-defined chapter starts in HTML chunks.

    Returns list of (chapter_title, chunk_index) tuples.
    Falls back to generic titles if patterns not found.
    """
    import re

    found_chapters = []

    # Pre-process HTML chunks to text-only content (performance optimization)
    text_chunks = [re.sub(r"<[^>]+>", "", chunk) for chunk in html_chunks]

    for pattern in chapter_starts:
        pattern_found = False
        # Try to find this pattern in any chunk
        for i, text_content in enumerate(text_chunks):
            # Try both exact match and regex-style matching
            if pattern.lower() in text_content.lower():
                found_chapters.append((pattern.strip(), i))
                pattern_found = True
                break

            # Try as a regex pattern (single execution with better validation)
            try:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match and match.group(0).strip():  # Ensure meaningful match
                    title = match.group(0).strip()
                    found_chapters.append((title, i))
                    pattern_found = True
                    break
            except re.error:
                pass  # Invalid regex, skip

        # If pattern not found, create a generic chapter name
        if not pattern_found:
            # Ensure we don't exceed available chunks or create invalid indices
            chunk_idx = min(len(found_chapters), len(html_chunks) - 1)
            if chunk_idx >= 0 and chunk_idx < len(html_chunks):  # Ensure valid index
                found_chapters.append((f"Chapter {len(found_chapters) + 1}", chunk_idx))

    return found_chapters


def _inject_manual_chapter_ids(
    html: str, chap_idx: int, chapter_title: str
) -> tuple[str, str, list[tuple[str, str]]]:
    """Inject IDs for manually defined chapters, similar to _inject_heading_ids."""
    import re

    # Create a unique ID for this chapter
    h1_id = f"ch{chap_idx:03d}"

    # Look for existing h1/h2 headings to preserve them
    h2_items = []

    # Ensure h2 have ids; collect titles + ids
    sec_idx = 0

    def h2_repl(match):
        nonlocal sec_idx
        sec_idx += 1
        tag_open = match.group(1)
        inside = match.group(2)
        if re.search(r"\bid=\"[^\"]+\"", tag_open):
            return f"<h2{tag_open}>{inside}</h2>"
        hid = f"{h1_id}-s{sec_idx:02d}"
        return f'<h2{tag_open} id="{hid}">{inside}</h2>'

    html_with_h2_ids = re.sub(
        r"<h2([^>]*)>(.*?)</h2>", h2_repl, html, flags=re.IGNORECASE | re.DOTALL
    )

    # Extract h2 titles and IDs for TOC
    titles = re.findall(r"<h2[^>]*>(.*?)</h2>", html_with_h2_ids, flags=re.IGNORECASE | re.DOTALL)
    ids = re.findall(r"<h2[^>]*id=\"([^\"]+)\"[^>]*>", html_with_h2_ids, flags=re.IGNORECASE)
    h2_items = [(re.sub(r"<[^>]+>", "", t), ids[i]) for i, t in enumerate(titles) if i < len(ids)]

    # Add chapter anchor at the beginning if no h1 exists
    if not re.search(r"<h1[^>]*>", html_with_h2_ids, re.IGNORECASE):
        html_with_h2_ids = f'<div id="{h1_id}"></div>' + html_with_h2_ids
    else:
        # Add ID to existing h1
        def h1_repl(match):
            tag_open = match.group(1)
            inside = match.group(2)
            if re.search(r"\bid=\"[^\"]+\"", tag_open):
                return f"<h1{tag_open}>{inside}</h1>"
            return f'<h1{tag_open} id="{h1_id}">{inside}</h1>'

        html_with_h2_ids = re.sub(
            r"<h1([^>]*)>(.*?)</h1>",
            h1_repl,
            html_with_h2_ids,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    return html_with_h2_ids, h1_id, h2_items


def plan_build(
    meta: EpubMetadata,
    opts: BuildOptions,
    html_chunks: list[str],
    resources: list[Path],
) -> list[str]:
    plan: list[str] = []
    plan.append(f"Title: {meta.title}")
    plan.append(f"Author: {meta.author}")
    if meta.series:
        plan.append(f"Series: {meta.series} #{meta.series_index or '?'}")
    plan.append(f"Language: {meta.language}")
    if meta.isbn:
        plan.append(f"Identifier: ISBN {meta.isbn}")
    plan.append(f"Cover: {meta.cover_path}")
    plan.append(f"Theme: {opts.theme}, Split: {opts.split_at}, ToC depth: {opts.toc_depth}")
    plan.append(f"Chunks: {len(html_chunks)}, Resources: {len(resources)}")
    if opts.page_numbers:
        plan.append("Page numbers: CSS counters (informational)")
    if opts.page_list:
        plan.append("EPUB page-list: enabled (reader support varies)")
    return plan


def assemble_epub(
    meta: EpubMetadata,
    opts: BuildOptions,
    html_chunks: list[str],
    resources: list[Path],
    output_path: Path,
    styles_css: str = "",
) -> None:
    """Assemble the EPUB with ebooklib and write to output_path."""
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    book = epub.EpubBook()

    identifier = meta.isbn or meta.uuid or str(_uuid.uuid4())
    book.set_identifier(identifier)
    book.set_title(meta.title)
    book.set_language(meta.language or "en")
    book.add_author(meta.author)
    if meta.publisher:
        book.add_metadata("DC", "publisher", meta.publisher)
    if meta.pubdate:
        book.add_metadata("DC", "date", meta.pubdate.isoformat())
    if meta.description:
        book.add_metadata("DC", "description", meta.description)
    if meta.title_sort:
        book.add_metadata(None, "meta", meta.title_sort, {"name": "calibre:title_sort"})
    if meta.author_sort:
        book.add_metadata(None, "meta", meta.author_sort, {"name": "calibre:author_sort"})
    for subj in meta.subjects:
        book.add_metadata("DC", "subject", subj)
    for kw in meta.keywords:
        book.add_metadata("DC", "subject", kw)
    # Calibre series metadata
    if meta.series:
        book.add_metadata(None, "meta", meta.series, {"name": "calibre:series"})
        if meta.series_index:
            book.add_metadata(
                None,
                "meta",
                str(meta.series_index),
                {"name": "calibre:series_index"},
            )

    # Cover
    cover_bytes = meta.cover_path.read_bytes()
    # Let ebooklib create the cover page automatically
    book.set_cover(meta.cover_path.name, cover_bytes)

    # CSS
    css_bytes = _load_css(opts.theme, opts.extra_css, opts, styles_css)
    style_item = epub.EpubItem(
        uid="style_base",
        file_name="style/base.css",
        media_type="text/css",
        content=css_bytes,
    )
    book.add_item(style_item)

    # Title page
    # Load packaged title template
    try:
        title_path = resources.files("docx2shelf.templates").joinpath("title.xhtml")
        with title_path.open("r", encoding="utf-8") as fh:
            content = (
                fh.read().replace("{{ title }}", meta.title).replace("{{ author }}", meta.author)
            )
    except Exception:
        content = f"<html><body><h1>{meta.title}</h1><p>{meta.author}</p></body></html>"
    title_page = _html_item("Title Page", "text/title.xhtml", content, meta.language)
    book.add_item(title_page)

    # Copyright page (auto)
    import datetime as _dt

    year = str(_dt.date.today().year)
    copyright_html = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Copyright</title></head><body>"
        f"<section><h2>Copyright</h2><p>© {year} {meta.author}. All rights reserved.</p></section>"
        "</body></html>"
    )
    copyright_page = _html_item("Copyright", "text/copyright.xhtml", copyright_html, meta.language)
    book.add_item(copyright_page)

    # Optional front/back matter
    matter_items = []
    if opts.dedication_txt and opts.dedication_txt.exists():
        txt = _read_text(opts.dedication_txt)
        ded_html = f"<h2>Dedication</h2><p>{txt}</p>"
        matter_items.append(
            _html_item("Dedication", "text/dedication.xhtml", ded_html, meta.language)
        )
    if opts.ack_txt and opts.ack_txt.exists():
        txt = _read_text(opts.ack_txt)
        matter_items.append(
            _html_item(
                "Acknowledgements",
                "text/ack.xhtml",
                f"<h2>Acknowledgements</h2><p>{txt}</p>",
                meta.language,
            )
        )
    for it in matter_items:
        book.add_item(it)

    # Add extracted resources (images) under images/
    for res in resources:
        mt = (
            "image/jpeg"
            if res.suffix.lower() in {".jpg", ".jpeg"}
            else ("image/png" if res.suffix.lower() == ".png" else None)
        )
        if mt is None:
            continue
        item = epub.EpubItem(
            uid=f"img_{res.stem}",
            file_name=f"images/{res.name}",
            media_type=mt,
            content=res.read_bytes(),
        )
        book.add_item(item)

    # Chapters from html_chunks
    chapters = []
    chapter_links = []
    chapter_sub_links = []

    # Determine chapter processing mode
    if opts.chapter_start_mode in ("manual", "mixed") and opts.chapter_starts:
        # Manual mode: use user-defined chapter starts
        manual_chapters = _find_chapter_starts(html_chunks, opts.chapter_starts)

        for chap_num, (chapter_title, chunk_idx) in enumerate(manual_chapters, start=1):
            if chunk_idx < len(html_chunks):
                chunk = html_chunks[chunk_idx]
                chunk2, h1_id, subs = _inject_manual_chapter_ids(chunk, chap_num, chapter_title)
                chap_fn = f"text/chap_{chap_num:03d}.xhtml"
                chap = _html_item(chapter_title, chap_fn, chunk2, meta.language)
                chap.add_item(style_item)
                book.add_item(chap)
                chapters.append(chap)
                # Build links for TOC using custom title
                chap_link = epub.Link(chap_fn + f"#{h1_id}", chapter_title, f"chap{chap_num:03d}")
                chapter_links.append(chap_link)
                sub_links = []
                if opts.toc_depth > 1:  # Include subheadings in manual mode too
                    for idx, (title, hid) in enumerate(subs):
                        sub_links.append(
                            epub.Link(chap_fn + f"#{hid}", title, f"chap{chap_num:03d}-{idx+1:02d}")
                        )
                chapter_sub_links.append(sub_links)

        # Add remaining chunks as additional chapters if there are more chunks than defined chapters
        for i in range(len(manual_chapters), len(html_chunks)):
            chunk = html_chunks[i]
            chap_num = i + 1
            chunk2, h1_id, subs = _inject_heading_ids(chunk, chap_num)
            chap_fn = f"text/chap_{chap_num:03d}.xhtml"
            chap = _html_item(f"Chapter {chap_num}", chap_fn, chunk2, meta.language)
            chap.add_item(style_item)
            book.add_item(chap)
            chapters.append(chap)
            chap_link = epub.Link(
                chap_fn + f"#{h1_id}", f"Chapter {chap_num}", f"chap{chap_num:03d}"
            )
            chapter_links.append(chap_link)
            sub_links = []
            for idx, (title, hid) in enumerate(subs):
                sub_links.append(
                    epub.Link(chap_fn + f"#{hid}", title, f"chap{chap_num:03d}-{idx+1:02d}")
                )
            chapter_sub_links.append(sub_links)

    else:
        # Auto mode (default): scan headings as before
        for i, chunk in enumerate(html_chunks, start=1):
            chunk2, h1_id, subs = _inject_heading_ids(chunk, i)
            chap_fn = f"text/chap_{i:03d}.xhtml"
            chap = _html_item(f"Chapter {i}", chap_fn, chunk2, meta.language)
            chap.add_item(style_item)
            book.add_item(chap)
            chapters.append(chap)
            # Build links for TOC
            chap_link = epub.Link(chap_fn + f"#{h1_id}", f"Chapter {i}", f"chap{i:03d}")
            chapter_links.append(chap_link)
            sub_links = []
            for idx, (title, hid) in enumerate(subs):
                sub_links.append(epub.Link(chap_fn + f"#{hid}", title, f"chap{i:03d}-{idx+1:02d}"))
            chapter_sub_links.append(sub_links)

    # TOC and spine
    # TOC by depth
    toc_items = [title_page, copyright_page] + matter_items
    depth = max(1, min(2, opts.toc_depth))
    for i, chap_link in enumerate(chapter_links):
        if depth == 1 or not chapter_sub_links[i]:
            toc_items.append(chap_link)
        else:
            toc_items.append((chap_link, chapter_sub_links[i]))
    book.toc = tuple(toc_items)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", title_page, copyright_page] + matter_items + chapters

    # Optional page-list nav (informational; support varies)
    if opts.page_list:
        items = []
        for i, chap in enumerate(chapters, start=1):
            frag = f"#ch{i:03d}"
            items.append(f"<li><a href='{chap.file_name}{frag}'>Page {i}</a></li>")
        page_list_html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops'>"
            "<head><title>Page List</title></head><body>"
            "<nav epub:type='page-list'><h2>Pages</h2><ol>" + "".join(items) + "</ol></nav>"
            "</body></html>"
        )
        page_list_item = _html_item(
            "Page List",
            "text/page-list.xhtml",
            page_list_html,
            meta.language,
        )
        book.add_item(page_list_item)

    # Landmarks nav for better reader navigation
    try:
        landmarks_html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops'>"
            "<head><title>Landmarks</title></head><body>"
            "<nav epub:type='landmarks'><h2>Guide</h2><ol>"
            "<li><a epub:type='titlepage' href='text/title.xhtml'>Title Page</a></li>"
            "<li><a epub:type='toc' href='nav.xhtml'>Table of Contents</a></li>"
            "<li><a epub:type='cover' href='cover.xhtml'>Cover</a></li>"
            "<li><a epub:type='bodymatter' href='text/chap_001.xhtml#ch001'>Start Reading</a></li>"
            "</ol></nav>"
            "</body></html>"
        )
        landmarks_item = _html_item(
            "Landmarks", "text/landmarks.xhtml", landmarks_html, meta.language
        )
        book.add_item(landmarks_item)
    except Exception:
        pass

    # Embed fonts (optional)
    if opts.embed_fonts_dir and opts.embed_fonts_dir.exists():
        for font in sorted(opts.embed_fonts_dir.glob("**/*")):
            if font.suffix.lower() in {".ttf", ".otf"} and font.is_file():
                data = font.read_bytes()
                item = epub.EpubItem(
                    uid=f"font_{font.stem}",
                    file_name=f"fonts/{font.name}",
                    media_type="font/otf" if font.suffix.lower() == ".otf" else "font/ttf",
                    content=data,
                )
                book.add_item(item)

    # Write EPUB
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)

    # Inspect output (dump sources)
    if opts.inspect:
        folder = output_path.with_suffix("")
        folder = folder.parent / (folder.name + ".src")
        folder.mkdir(parents=True, exist_ok=True)
        # Save HTML chunks for debugging
        for i, chunk in enumerate(html_chunks, start=1):
            (folder / f"chap_{i:03d}.xhtml").write_text(chunk, encoding="utf-8")
        (folder / "meta.txt").write_text(
            "\n".join(
                [
                    f"title={meta.title}",
                    f"author={meta.author}",
                    f"language={meta.language}",
                    f"identifier={identifier}",
                ]
            ),
            encoding="utf-8",
        )

    # Optional EPUBCheck if available
    if opts.epubcheck:
        try:
            import shutil
            import subprocess

            cmd = shutil.which("epubcheck")
            if cmd:
                proc = subprocess.run([cmd, str(output_path)], capture_output=True, text=True)
                out = (proc.stdout or "") + "\n" + (proc.stderr or "")
                # Naive counts
                errors = len([1 for line in out.splitlines() if "ERROR" in line])
                warnings = len([1 for line in out.splitlines() if "WARNING" in line])
                summary = f"EPUBCheck: {errors} error(s), {warnings} warning(s)"
                if not opts.quiet:
                    print(summary)
                    if opts.verbose and (errors or warnings):
                        print("First issues:")
                        shown = 0
                        for line in out.splitlines():
                            if ("ERROR" in line) or ("WARNING" in line):
                                print("  " + line)
                                shown += 1
                                if shown >= 10:
                                    break
        except Exception:
            pass
