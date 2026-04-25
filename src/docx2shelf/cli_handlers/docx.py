"""DOCX generation handler.

Converts manuscript inputs to a .docx via Pandoc (using the bundled binary).
Optionally injects core properties (title/author) from a metadata file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SUPPORTED_INPUT_SUFFIXES = {".md", ".html", ".htm", ".txt", ".docx"}


def run_docx(args: argparse.Namespace) -> int:
    """Generate a .docx file from a manuscript source."""
    from ..tools import get_pandoc_status

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists() or not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 2

    suffix = input_path.suffix.lower()
    if suffix not in SUPPORTED_INPUT_SUFFIXES:
        print(
            f"Error: unsupported input type {suffix!r}. "
            f"Supported: {sorted(SUPPORTED_INPUT_SUFFIXES)}",
            file=sys.stderr,
        )
        return 2

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_suffix(".docx")
    )
    if output_path.suffix.lower() != ".docx":
        print(
            f"Error: --output must end in .docx (got {output_path.suffix!r})",
            file=sys.stderr,
        )
        return 2

    status = get_pandoc_status()
    if not status["overall_available"]:
        print("Error: Pandoc is required for DOCX generation.", file=sys.stderr)
        if not status["pandoc_binary"]["available"]:
            print(
                "  - Pandoc binary missing. Run 'docx2shelf tools install pandoc'.",
                file=sys.stderr,
            )
        if not status["pypandoc_library"]["available"]:
            print("  - pypandoc missing. Run 'pip install pypandoc'.", file=sys.stderr)
        return 3

    if suffix == ".md":
        source_format = "markdown"
    elif suffix in (".html", ".htm"):
        source_format = "html"
    elif suffix == ".txt":
        source_format = "plain"
    else:
        source_format = "docx"

    extra_args: list[str] = []
    if args.reference_doc:
        ref = Path(args.reference_doc).expanduser().resolve()
        if not ref.exists():
            print(f"Error: reference doc not found: {ref}", file=sys.stderr)
            return 2
        extra_args.append(f"--reference-doc={ref}")

    metadata_kv: dict[str, str] = {}
    if args.metadata:
        from ..utils import parse_kv_file

        meta_path = Path(args.metadata).expanduser().resolve()
        if not meta_path.exists():
            print(f"Error: metadata file not found: {meta_path}", file=sys.stderr)
            return 2
        metadata_kv = parse_kv_file(meta_path)
        # Pandoc DOCX writer reads `lang` (not `language`) for dc:language.
        # `author` maps to dc:creator via Pandoc's standard variable naming.
        pandoc_key_map = {
            "title": "title",
            "author": "author",
            "language": "lang",
            "publisher": "publisher",
            "description": "description",
            "subject": "subject",
            "keywords": "keywords",
        }
        for src_key, pandoc_key in pandoc_key_map.items():
            value = metadata_kv.get(src_key)
            if value:
                extra_args.append(f"--metadata={pandoc_key}={value}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import pypandoc
    except ImportError:
        print("Error: pypandoc not installed.", file=sys.stderr)
        return 3

    try:
        pypandoc.convert_file(
            str(input_path),
            to="docx",
            format=source_format,
            outputfile=str(output_path),
            extra_args=extra_args,
        )
    except Exception as exc:
        print(f"Error: Pandoc conversion failed: {exc}", file=sys.stderr)
        return 4

    if not output_path.exists():
        print(f"Error: Pandoc reported success but output missing: {output_path}", file=sys.stderr)
        return 4

    if not args.quiet:
        size_kb = output_path.stat().st_size / 1024
        print(f"Wrote: {output_path} ({size_kb:.1f} KB)")
    return 0
