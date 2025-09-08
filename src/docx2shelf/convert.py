from __future__ import annotations

from pathlib import Path
import re
import tempfile

IMG_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def split_html_by_heading(html: str, level: str) -> list[str]:
    """Split a single HTML string into chunks at <h1> or <h2> boundaries.

    Uses a simple regex; good enough for initial implementation and Pandoc output.
    """
    tag = level.lower()
    # Normalize newlines to avoid regex surprises
    s = html.replace("\r\n", "\n")
    # Split but keep the heading with the following content
    pattern = re.compile(rf"(<{tag}[^>]*>.*?</{tag}>)", re.IGNORECASE | re.DOTALL)
    parts = pattern.split(s)
    if len(parts) <= 1:
        return [s]
    chunks: list[str] = []
    current: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # this is a heading
            if current:
                chunks.append("".join(current))
                current = []
            current.append(part)
        else:
            current.append(part)
    if current:
        chunks.append("".join(current))
    # Wrap chunks into section tags for cleanliness
    return [f"<section>{c}</section>" for c in chunks if c.strip()]


def split_html_by_pagebreak(html: str) -> list[str]:
    """Split HTML at common pagebreak markers.

    Looks for <hr class="pagebreak">, elements with style containing
    page-break-(before|after): always, or explicit <!-- PAGEBREAK --> comments.
    """
    s = html.replace("\r\n", "\n")
    # Insert a sentinel at break points
    patterns = [
        r"<hr[^>]*class=\"[^\"]*pagebreak[^\"]*\"[^>]*/?>",
        r"<[^>]*style=\"[^\"]*page-break-(before|after)\s*:\s*always[^\"]*\"[^>]*>",
        r"<!--\s*PAGEBREAK\s*-->",
    ]
    sentinel = "\n<!--__SPLIT__-->\n"
    for pat in patterns:
        s = re.sub(pat, sentinel, s, flags=re.IGNORECASE)
    parts = s.split(sentinel)
    chunks = [p for p in parts if p.strip()]
    return [f"<section>{c}</section>" for c in chunks]


def docx_to_html(docx_path: Path) -> tuple[list[str], list[Path]]:
    """Convert DOCX to HTML chunks and gather any extracted resources.

    Strategy:
    1) Try Pandoc via pypandoc for rich conversion.
    2) Fallback to a lightweight python-docx paragraph/headings extraction.
    """
    # 1) Pandoc path
    try:
        import pypandoc  # type: ignore

        html = pypandoc.convert_file(str(docx_path), to="html", extra_args=["--wrap=none"])
        # Split at h1 by default; caller can later decide via CLI how to split
        chunks = split_html_by_heading(html, level="h1")
        return chunks, []
    except Exception:
        pass

    # 2) python-docx fallback
    try:
        from docx import Document  # type: ignore
        from docx.oxml.ns import qn  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "No converter found. Install pypandoc (Pandoc recommended) or python-docx."
        ) from e

    document = Document(str(docx_path))
    parts: list[str] = []

    # Temp dir for extracted images
    tempdir = Path(tempfile.mkdtemp(prefix="docx2shelf_"))
    images: dict[str, Path] = {}

    def flush_section(buf: list[str], footnotes: list[str] | None = None):
        if not buf:
            return
        body = "".join(buf)
        if footnotes:
            notes_html = "<hr/><section class=\"footnotes\"><ol>" + "".join(footnotes) + "</ol></section>"
            body += notes_html
        parts.append("<section>" + body + "</section>")
        buf.clear()

    buf: list[str] = []
    note_idx = 0
    current_notes: list[str] = []
    # List handling state
    current_list_type: str | None = None  # 'ul' | 'ol'
    list_items: list[str] = []

    def flush_list():
        nonlocal current_list_type, list_items
        if current_list_type and list_items:
            buf.append(f"<{current_list_type}>" + "".join(list_items) + f"</{current_list_type}>")
        current_list_type = None
        list_items = []
    pending_img: str | None = None
    for p in document.paragraphs:
        style = (p.style.name or "").lower()
        # Detect list paragraphs
        is_num = False
        is_list = False
        try:
            pPr = p._p.pPr  # type: ignore[attr-defined]
            is_list = pPr is not None and pPr.numPr is not None  # type: ignore[attr-defined]
        except Exception:
            is_list = False
        if 'list' in style or 'bullet' in style or 'number' in style:
            is_list = True
            is_num = 'number' in style

        # Build paragraph content with basic runs formatting and images, merging hyperlinks
        run_html: list[str] = []
        current_link_href: str | None = None
        current_link_buf: list[str] = []
        for run in p.runs:
            txt = run.text or ""
            # Images in this run?
            try:
                blips = run.element.xpath('.//a:blip', namespaces=IMG_NS)
            except Exception:
                blips = []
            for blip in blips:
                rid = blip.get(qn('r:embed'))
                if rid and rid in document.part.related_parts:
                    part = document.part.related_parts[rid]
                    filename = Path(part.partname).name
                    # Try to get alt text via docPr
                    alt = ""
                    try:
                        docprs = run.element.xpath('.//wp:docPr', namespaces=IMG_NS)
                        if docprs:
                            alt = docprs[0].get('descr') or docprs[0].get('title') or ""
                    except Exception:
                        alt = ""
                    if filename not in images:
                        out = tempdir / filename
                        out.write_bytes(part.blob)
                        images[filename] = out
                    alt_attr = f" alt=\"{alt}\"" if alt else " alt=\"\""
                    run_html.append(f"<img src=\"images/{filename}\"{alt_attr} />")
            # Footnote/endnote references
            try:
                fns = run.element.xpath('.//w:footnoteReference', namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"})
            except Exception:
                fns = []
            try:
                ens = run.element.xpath('.//w:endnoteReference', namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"})
            except Exception:
                ens = []
            # Manual page breaks
            try:
                brs = run.element.xpath('.//w:br[@w:type="page"]', namespaces=IMG_NS)
            except Exception:
                brs = []
            if brs:
                # Insert a pagebreak sentinel to be split later
                run_html.append("<!-- PAGEBREAK -->")
            for ref in fns + ens:
                note_idx += 1
                ref_id = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                sup = f"<sup id=\"fnref{note_idx}\"><a href=\"#fn{note_idx}\">{note_idx}</a></sup>"
                run_html.append(sup)
                # Retrieve note text if possible
                note_text = None
                try:
                    if 'footnote' in ref.tag and hasattr(document.part, 'footnotes_part') and document.part.footnotes_part is not None:
                        # type: ignore[attr-defined]
                        nodes = document.part.footnotes_part._element.xpath(
                            f'.//w:footnote[@w:id="{ref_id}"]//w:t',
                            namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"},
                        )
                        note_text = "".join(n.text or "" for n in nodes).strip()
                    elif 'endnote' in ref.tag and hasattr(document.part, 'endnotes_part') and document.part.endnotes_part is not None:
                        nodes = document.part.endnotes_part._element.xpath(
                            f'.//w:endnote[@w:id="{ref_id}"]//w:t',
                            namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"},
                        )
                        note_text = "".join(n.text or "" for n in nodes).strip()
                except Exception:
                    note_text = None
                if not note_text:
                    note_text = "(note)"
                current_notes.append(f"<li id=\"fn{note_idx}\"><p>{note_text} <a href=\"#fnref{note_idx}\">↩</a></p></li>")

            if txt:
                # Basic inline formatting
                if getattr(run, 'bold', False):
                    txt = f"<strong>{txt}</strong>"
                if getattr(run, 'italic', False):
                    txt = f"<em>{txt}</em>"
                # Hyperlinks: wrap if run is inside a hyperlink element
                try:
                    parent = run._r.getparent()
                    if parent is not None and parent.tag.endswith('}hyperlink'):
                        from docx.oxml.ns import qn  # type: ignore
                        rid = parent.get(qn('r:id')) if parent is not None else None
                        anchor = parent.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}anchor') if parent is not None else None
                        href = None
                        if rid and rid in p.part.rels:
                            href = p.part.rels[rid].target_ref  # type: ignore[attr-defined]
                        elif anchor:
                            href = f"#{anchor}"
                        if href:
                            if current_link_href == href:
                                current_link_buf.append(txt)
                                txt = ""
                            else:
                                # flush previous
                                if current_link_href is not None:
                                    run_html.append(f"<a href=\"{current_link_href}\">{''.join(current_link_buf)}</a>")
                                    current_link_buf = []
                                current_link_href = href
                                current_link_buf.append(txt)
                                txt = ""
                except Exception:
                    pass
                if txt:
                    # flush any open link first when standalone text encountered
                    if current_link_href is not None and current_link_buf:
                        run_html.append(f"<a href=\"{current_link_href}\">{''.join(current_link_buf)}</a>")
                        current_link_href = None
                        current_link_buf = []
                    run_html.append(txt)

        # Flush open hyperlink group
        if current_link_href is not None and current_link_buf:
            run_html.append(f"<a href=\"{current_link_href}\">{''.join(current_link_buf)}</a>")

        content = "".join(run_html).strip()
        if not content and not pending_img:
            continue
        # If previous paragraph was image-only and this is a caption, wrap in figure
        if 'caption' in style and pending_img:
            flush_list()
            buf.append(f"<figure>{pending_img}<figcaption>{content}</figcaption></figure>")
            pending_img = None
            continue

        # If content is an image-only paragraph, hold to see if next is a caption
        if re.fullmatch(r"\s*<img[^>]+>\s*", content):
            pending_img = content
            continue

        # If we have a pending image and the current paragraph is not a caption, flush it first
        if pending_img and ('caption' not in style):
            flush_list()
            buf.append(f"<p>{pending_img}</p>")
            pending_img = None

        if "heading 1" in style:
            flush_list()
            flush_section(buf, current_notes)
            current_notes = []
            buf.append(f"<h1>{content}</h1>")
        elif "heading 2" in style:
            flush_list()
            buf.append(f"<h2>{content}</h2>")
        elif is_list:
            list_type = 'ol' if is_num else 'ul'
            if current_list_type and current_list_type != list_type:
                flush_list()
            current_list_type = list_type if current_list_type is None else current_list_type
            list_items.append(f"<li>{content}</li>")
        elif 'quote' in style:
            flush_list()
            buf.append(f"<blockquote><p>{content}</p></blockquote>")
        else:
            flush_list()
            buf.append(f"<p>{content}</p>")

    flush_list()
    flush_section(buf, current_notes)
    if not parts:
        parts = ["<section><p>(Empty document)</p></section>"]
    # Return extracted images as resources
    return parts, list(images.values())
