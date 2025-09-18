from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional


@dataclass
class EpubMetadata:
    title: str
    author: str
    language: str
    description: Optional[str]
    isbn: Optional[str]
    publisher: Optional[str]
    pubdate: Optional[date]
    uuid: Optional[str]
    series: Optional[str]
    series_index: Optional[str]
    title_sort: Optional[str]
    author_sort: Optional[str]
    subjects: List[str]
    keywords: List[str]
    cover_path: Path


@dataclass
class BuildOptions:
    split_at: str  # h1|h2|h3|pagebreak|mixed
    theme: str  # serif|sans|printlike
    embed_fonts_dir: Optional[Path]
    image_quality: int = 85
    image_max_width: int = 1200
    image_max_height: int = 1600
    image_format: str = "webp"
    vertical_writing: bool = False
    epub2_compat: bool = False
    hyphenate: bool
    justify: bool
    toc_depth: int
    chapter_start_mode: str = "auto"  # auto|manual|mixed
    chapter_starts: Optional[List[str]] = None
    mixed_split_pattern: Optional[str] = None
    reader_start_chapter: Optional[str] = None
    page_list: bool = False
    extra_css: Optional[Path] = None
    page_numbers: bool = False
    epub_version: str = "3"
    cover_scale: str = "contain"  # contain|cover
    dedication_txt: Optional[Path] = None
    ack_txt: Optional[Path] = None
    inspect: bool = False
    dry_run: bool = False
    epubcheck: bool = True
    font_size: Optional[str] = None
    line_height: Optional[str] = None
    quiet: bool = False
    verbose: bool = False


def build_output_filename(title: str, series: Optional[str], series_index: Optional[str]) -> str:
    base = title
    if series:
        idx = series_index or "01"
        base = f"{series}-{idx}-{title}"
    safe = base.replace("/", "-").replace("\\", "-").replace(":", "-").replace("\0", "").strip()
    return safe + ".epub"


def render_output_pattern(
    pattern: str,
    *,
    title: str,
    series: Optional[str],
    series_index: Optional[str],
) -> str:
    """Render an output filename from a pattern.

    Supported placeholders:
    - {title}
    - {series}
    - {index}  (series index as-is)
    - {index2} (series index zero-padded to 2 digits when numeric)
    """
    idx_raw = (series_index or "").strip()
    idx2 = idx_raw
    try:
        if idx_raw:
            idx2 = f"{int(idx_raw):02d}"
    except Exception:
        pass
    values = {
        "title": title,
        "series": series or "",
        "index": idx_raw,
        "index2": idx2 or idx_raw,
    }
    out = pattern.format(**values)
    # Cleanup common doubled separators if series/index were blank
    for sep in ["--", "__", "  "]:
        while sep in out:
            out = out.replace(sep, sep[0])
    return out.strip()


def parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    parts = value.split("-")
    if len(parts) != 3:
        raise ValueError("pubdate must be YYYY-MM-DD")
    y, m, d = map(int, parts)
    return date(y, m, d)


def validate_isbn13(isbn: str) -> bool:
    s = isbn.replace("-", "").replace(" ", "")
    if len(s) != 13 or not s.isdigit():
        return False
    nums = [int(c) for c in s]
    checksum = sum((3 if i % 2 else 1) * n for i, n in enumerate(nums[:12]))
    check = (10 - (checksum % 10)) % 10
    return check == nums[12]


_LANG_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")


def normalize_lang(code: str) -> str:
    return (code or "").strip().lower()


def validate_lang_code(code: str) -> bool:
    if not code:
        return False
    return bool(_LANG_RE.match(code))
