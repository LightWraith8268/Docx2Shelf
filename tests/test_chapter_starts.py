
from docx2shelf.assemble import _find_chapter_starts, _inject_manual_chapter_ids
from docx2shelf.metadata import BuildOptions


def test_find_chapter_starts_exact_match():
    """Test finding chapters with exact text matching."""
    html_chunks = [
        "<p>Prologue content here</p>",
        "<p>Chapter 1: The Beginning starts here</p>",
        "<p>Some middle content</p>",
        "<p>Epilogue content here</p>",
    ]
    chapter_starts = ["Prologue", "Chapter 1", "Epilogue"]
    result = _find_chapter_starts(html_chunks, chapter_starts)

    expected = [("Prologue", 0), ("Chapter 1", 1), ("Epilogue", 3)]
    assert result == expected


def test_find_chapter_starts_regex_match():
    """Test finding chapters with regex patterns."""
    html_chunks = [
        "<h1>Chapter 1: Introduction</h1><p>Content</p>",
        "<h1>Chapter 2: Development</h1><p>More content</p>",
        "<h1>Chapter 3: Conclusion</h1><p>Final content</p>",
    ]
    chapter_starts = [r"Chapter \d+: Introduction", r"Chapter \d+: Development"]
    result = _find_chapter_starts(html_chunks, chapter_starts)

    expected = [("Chapter 1: Introduction", 0), ("Chapter 2: Development", 1)]
    assert result == expected


def test_find_chapter_starts_case_insensitive():
    """Test case insensitive matching."""
    html_chunks = ["<p>PROLOGUE section</p>", "<p>chapter one begins</p>"]
    chapter_starts = ["prologue", "Chapter One"]
    result = _find_chapter_starts(html_chunks, chapter_starts)

    expected = [("prologue", 0), ("Chapter One", 1)]
    assert result == expected


def test_find_chapter_starts_fallback():
    """Test fallback behavior when patterns don't match."""
    html_chunks = ["<p>Some content</p>", "<p>More content</p>"]
    chapter_starts = ["Nonexistent Pattern", "Another Missing Pattern"]
    result = _find_chapter_starts(html_chunks, chapter_starts)

    # Should create generic chapter names
    expected = [("Chapter 1", 0), ("Chapter 2", 1)]
    assert result == expected


def test_find_chapter_starts_empty_chunks():
    """Test behavior with empty chunks list."""
    html_chunks = []
    chapter_starts = ["Chapter 1"]
    result = _find_chapter_starts(html_chunks, chapter_starts)

    # Should handle gracefully with no crashes
    assert result == []


def test_find_chapter_starts_invalid_regex():
    """Test handling of invalid regex patterns."""
    html_chunks = ["<p>Valid chapter content</p>", "<p>Another section</p>"]
    chapter_starts = [
        "*[invalid regex",
        "Valid chapter",
    ]  # First pattern is invalid regex, won't match text
    result = _find_chapter_starts(html_chunks, chapter_starts)

    # Should create fallback for first pattern and find match for second
    expected = [("Chapter 1", 0), ("Valid chapter", 0)]
    assert result == expected


def test_inject_manual_chapter_ids():
    """Test manual chapter ID injection."""
    html = "<h1>My Chapter</h1><h2>Section 1</h2><p>Content</p><h2>Section 2</h2>"
    chunk_idx = 1
    chapter_title = "Custom Chapter Title"

    result_html, h1_id, h2_items = _inject_manual_chapter_ids(html, chunk_idx, chapter_title)

    # Should have proper chapter ID
    assert h1_id == "ch001"

    # Should have h2 subsections with IDs
    assert len(h2_items) == 2
    assert h2_items[0][0] == "Section 1"
    assert h2_items[1][0] == "Section 2"

    # HTML should contain the IDs
    assert 'id="ch001"' in result_html
    assert 'id="ch001-s01"' in result_html
    assert 'id="ch001-s02"' in result_html


def test_build_options_new_fields():
    """Test BuildOptions with new chapter start fields."""
    opts = BuildOptions(
        split_at="h1",
        theme="serif",
        embed_fonts_dir=None,
        hyphenate=True,
        justify=True,
        toc_depth=2,
        chapter_start_mode="manual",
        chapter_starts=["Prologue", "Chapter 1", "Epilogue"],
    )

    assert opts.chapter_start_mode == "manual"
    assert opts.chapter_starts == ["Prologue", "Chapter 1", "Epilogue"]


def test_build_options_defaults():
    """Test BuildOptions default values for new fields."""
    opts = BuildOptions(
        split_at="h1",
        theme="serif",
        embed_fonts_dir=None,
        hyphenate=True,
        justify=True,
        toc_depth=2,
    )

    assert opts.chapter_start_mode == "auto"
    assert opts.chapter_starts is None
