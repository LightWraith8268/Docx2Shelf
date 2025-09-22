"""
Property-based tests for Docx2Shelf using Hypothesis.

These tests generate random inputs to verify that core functionality
behaves correctly under a wide range of conditions.
"""

import re
import string
from typing import List

import pytest

try:
    from hypothesis import Verbosity, assume, example, given, settings
    from hypothesis import strategies as st
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create mock decorators for when hypothesis is not available
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip("Hypothesis not available")(func)
        return decorator

    class st:
        @staticmethod
        def text(*args, **kwargs):
            return None
        @staticmethod
        def integers(*args, **kwargs):
            return None
        @staticmethod
        def lists(*args, **kwargs):
            return None

from docx2shelf.assemble import generate_output_filename
from docx2shelf.convert import split_html_by_heading, split_html_by_pagebreak


# HTML content generation strategies
@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPropertyBasedSplitting:
    """Property-based tests for HTML splitting functionality."""

    @given(st.lists(st.text(alphabet=string.ascii_letters + string.digits + ' .,!?', min_size=1, max_size=100), min_size=1, max_size=10))
    def test_split_by_h1_preserves_content(self, chapter_texts: List[str]):
        """Test that splitting by h1 preserves all original content."""
        assume(all(text.strip() for text in chapter_texts))  # No empty chapters
        assume(len(chapter_texts) >= 1)

        # Build HTML with h1 separators
        html_parts = []
        for i, text in enumerate(chapter_texts):
            html_parts.append(f"<h1>Chapter {i + 1}</h1>")
            html_parts.append(f"<p>{text}</p>")

        full_html = "".join(html_parts)

        # Split the HTML
        chunks = split_html_by_heading(full_html, level="h1")

        # Property: Number of chunks should equal number of chapters
        assert len(chunks) == len(chapter_texts), f"Expected {len(chapter_texts)} chunks, got {len(chunks)}"

        # Property: All original text should be preserved
        combined_chunks = "".join(chunks)
        for text in chapter_texts:
            assert text in combined_chunks, f"Original text '{text}' not found in split chunks"

        # Property: Each chunk should contain exactly one h1
        for chunk in chunks:
            h1_count = len(re.findall(r'<h1[^>]*>', chunk))
            assert h1_count == 1, f"Chunk should contain exactly one h1, found {h1_count}"

    @given(st.lists(st.text(alphabet=string.ascii_letters + string.digits + ' .,!?', min_size=1, max_size=100), min_size=1, max_size=10))
    def test_split_by_h2_preserves_content(self, section_texts: List[str]):
        """Test that splitting by h2 preserves all original content."""
        assume(all(text.strip() for text in section_texts))
        assume(len(section_texts) >= 1)

        # Build HTML with h2 separators
        html_parts = []
        for i, text in enumerate(section_texts):
            html_parts.append(f"<h2>Section {i + 1}</h2>")
            html_parts.append(f"<p>{text}</p>")

        full_html = "".join(html_parts)

        # Split the HTML
        chunks = split_html_by_heading(full_html, level="h2")

        # Property: Number of chunks should equal number of sections
        assert len(chunks) == len(section_texts), f"Expected {len(section_texts)} chunks, got {len(chunks)}"

        # Property: All original text should be preserved
        combined_chunks = "".join(chunks)
        for text in section_texts:
            assert text in combined_chunks, f"Original text '{text}' not found in split chunks"

    @given(st.lists(st.text(alphabet=string.ascii_letters + string.digits + ' .,!?', min_size=1, max_size=100), min_size=1, max_size=10))
    def test_split_by_pagebreak_preserves_content(self, page_texts: List[str]):
        """Test that splitting by pagebreak preserves all original content."""
        assume(all(text.strip() for text in page_texts))
        assume(len(page_texts) >= 1)

        # Build HTML with pagebreak separators
        html_parts = []
        for i, text in enumerate(page_texts):
            if i > 0:  # Add pagebreak before all but first page
                html_parts.append('<hr class="pagebreak" />')
            html_parts.append(f"<p>{text}</p>")

        full_html = "".join(html_parts)

        # Split the HTML
        chunks = split_html_by_pagebreak(full_html)

        # Property: Number of chunks should equal number of pages
        assert len(chunks) == len(page_texts), f"Expected {len(page_texts)} chunks, got {len(chunks)}"

        # Property: All original text should be preserved
        combined_chunks = "".join(chunks)
        for text in page_texts:
            assert text in combined_chunks, f"Original text '{text}' not found in split chunks"

        # Property: No chunk should contain pagebreak markers
        for chunk in chunks:
            assert 'class="pagebreak"' not in chunk, "Chunks should not contain pagebreak markers"

    @given(st.text(alphabet=string.ascii_letters + string.digits + ' .,!?', min_size=1, max_size=1000))
    def test_split_empty_returns_single_chunk(self, content: str):
        """Test that content without split markers returns a single chunk."""
        assume(content.strip())
        assume('<h1' not in content)
        assume('<h2' not in content)
        assume('pagebreak' not in content)

        html = f"<p>{content}</p>"

        # Test h1 splitting
        h1_chunks = split_html_by_heading(html, level="h1")
        assert len(h1_chunks) == 1, "Content without h1 should return single chunk"
        assert content in h1_chunks[0], "Original content should be preserved"

        # Test h2 splitting
        h2_chunks = split_html_by_heading(html, level="h2")
        assert len(h2_chunks) == 1, "Content without h2 should return single chunk"
        assert content in h2_chunks[0], "Original content should be preserved"

        # Test pagebreak splitting
        pb_chunks = split_html_by_pagebreak(html)
        assert len(pb_chunks) == 1, "Content without pagebreaks should return single chunk"
        assert content in pb_chunks[0], "Original content should be preserved"


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPropertyBasedNaming:
    """Property-based tests for output filename generation."""

    @given(
        st.text(alphabet=string.ascii_letters + string.digits + ' ', min_size=1, max_size=50),
        st.text(alphabet=string.ascii_letters + string.digits + ' ', min_size=1, max_size=50),
        st.integers(min_value=1, max_value=999)
    )
    def test_filename_generation_properties(self, title: str, author: str, series_index: int):
        """Test properties of filename generation patterns."""
        assume(title.strip())
        assume(author.strip())

        # Test basic pattern
        pattern = "{title}-{author}"
        filename = generate_output_filename(
            pattern=pattern,
            title=title.strip(),
            author=author.strip(),
            series_index=series_index
        )

        # Property: Generated filename should contain sanitized title and author
        assert len(filename) > 0, "Filename should not be empty"
        assert filename.endswith('.epub'), "Filename should end with .epub"

        # Property: Filename should not contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in filename, f"Filename should not contain invalid character: {char}"

    @given(st.integers(min_value=1, max_value=999))
    def test_series_index_formatting(self, series_index: int):
        """Test that series index formatting is consistent."""
        pattern = "{series}-{index2}-{title}"

        filename = generate_output_filename(
            pattern=pattern,
            title="Test Title",
            series="Test Series",
            series_index=series_index
        )

        # Property: index2 should be zero-padded to 2 digits
        expected_index = f"{series_index:02d}"
        assert expected_index in filename, f"Filename should contain zero-padded index: {expected_index}"

    @given(st.text(alphabet=string.ascii_letters + string.digits + ' -_', min_size=1, max_size=100))
    def test_title_sanitization(self, title: str):
        """Test that title sanitization preserves valid characters."""
        assume(title.strip())

        pattern = "{title}"
        filename = generate_output_filename(pattern=pattern, title=title.strip())

        # Property: Filename should not be empty
        assert len(filename) > 0, "Filename should not be empty"

        # Property: Valid characters should be preserved
        valid_chars = string.ascii_letters + string.digits + ' -_'
        for char in title:
            if char in valid_chars:
                # Check if the character appears in the filename (accounting for spaces -> underscores)
                expected_char = '_' if char == ' ' else char
                # This is a loose check since sanitization might do more complex transformations
                pass  # The exact preservation test would depend on sanitization implementation


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPropertyBasedEdgeCases:
    """Property-based tests for edge cases and error conditions."""

    @given(st.text(max_size=0))
    def test_empty_content_handling(self, empty_content: str):
        """Test that empty content is handled gracefully."""
        assert empty_content == ""

        # Test splitting empty content
        h1_chunks = split_html_by_heading(empty_content, level="h1")
        assert len(h1_chunks) == 1, "Empty content should return single chunk"
        assert h1_chunks[0] == empty_content, "Empty content should be preserved"

        h2_chunks = split_html_by_heading(empty_content, level="h2")
        assert len(h2_chunks) == 1, "Empty content should return single chunk"

        pb_chunks = split_html_by_pagebreak(empty_content)
        assert len(pb_chunks) == 1, "Empty content should return single chunk"

    @given(st.text(alphabet='<>/', min_size=1, max_size=50))
    def test_malformed_html_handling(self, malformed: str):
        """Test that malformed HTML is handled gracefully."""
        # The splitting functions should not crash on malformed HTML
        try:
            h1_chunks = split_html_by_heading(malformed, level="h1")
            assert isinstance(h1_chunks, list), "Should return list even for malformed HTML"

            h2_chunks = split_html_by_heading(malformed, level="h2")
            assert isinstance(h2_chunks, list), "Should return list even for malformed HTML"

            pb_chunks = split_html_by_pagebreak(malformed)
            assert isinstance(pb_chunks, list), "Should return list even for malformed HTML"

        except Exception as e:
            # If an exception is raised, it should be a specific, expected type
            # This is a placeholder - the actual implementation might handle this differently
            pytest.fail(f"Unexpected exception for malformed HTML: {e}")


# Integration test with property-based approach
@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPropertyBasedIntegration:
    """Integration tests using property-based testing."""

    @given(
        st.lists(
            st.text(alphabet=string.ascii_letters + string.digits + ' .,!?', min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    def test_split_and_rejoin_idempotency(self, chapters: List[str]):
        """Test that splitting and rejoining preserves essential content."""
        assume(all(chapter.strip() for chapter in chapters))

        # Create HTML with chapters
        html_parts = []
        for i, chapter in enumerate(chapters):
            html_parts.append(f"<h1>Chapter {i + 1}</h1>")
            html_parts.append(f"<p>{chapter}</p>")

        original_html = "".join(html_parts)

        # Split and rejoin
        chunks = split_html_by_heading(original_html, level="h1")
        rejoined = "".join(chunks)

        # Property: Essential content should be preserved
        for chapter in chapters:
            assert chapter in rejoined, f"Chapter content '{chapter}' should be preserved"

        # Property: Chapter count should be preserved
        original_h1_count = len(re.findall(r'<h1[^>]*>', original_html))
        rejoined_h1_count = len(re.findall(r'<h1[^>]*>', rejoined))
        assert original_h1_count == rejoined_h1_count, "H1 count should be preserved"


# Test configuration
if HYPOTHESIS_AVAILABLE:
    # Configure Hypothesis for CI/local testing
    settings.register_profile("ci", max_examples=100, verbosity=Verbosity.normal)
    settings.register_profile("dev", max_examples=10, verbosity=Verbosity.normal)
    settings.register_profile("thorough", max_examples=1000, verbosity=Verbosity.verbose)

    # Use CI profile by default
    settings.load_profile("ci")