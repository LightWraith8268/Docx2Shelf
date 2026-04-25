"""Benchmark a single HTML→chunks conversion. Used by CI performance scope."""

from __future__ import annotations

import time
from pathlib import Path

from docx2shelf.convert import convert_file_to_html


def main() -> None:
    from docx2shelf.tools import get_pandoc_status

    status = get_pandoc_status()
    if not status["overall_available"]:
        print("Skipping benchmark: Pandoc not available in this environment.")
        print(f"  pandoc_binary: {status['pandoc_binary']['message']}")
        print(f"  pypandoc_library: {status['pypandoc_library']['message']}")
        return

    test_content = "<h1>Chapter 1</h1>" + "<p>Test paragraph.</p>" * 1000
    test_file = Path("benchmark_test.html")
    test_file.write_text(test_content, encoding="utf-8")
    try:
        start = time.time()
        chunks, _resources, _title = convert_file_to_html(test_file)
        duration = max(1e-6, time.time() - start)
        print(f"Performance: Converted {len(test_content)} chars into {len(chunks)} chunks in {duration:.2f}s")
        print(f"Throughput: {len(test_content) / duration:.0f} chars/sec")
    finally:
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
