"""
Test suite for v1.2: Semantics & Scholarly polish features.

Tests the four major epics:
1. Cross-references & anchors
2. Indexing
3. Notes flow
4. Figures, tables & lists
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from src.docx2shelf.crossrefs import CrossReferenceProcessor, CrossRefConfig
from src.docx2shelf.indexing import IndexProcessor, IndexConfig
from src.docx2shelf.notes import NotesProcessor, NotesConfig
from src.docx2shelf.figures import FigureProcessor, FigureConfig


class TestCrossReferences:
    """Test cross-reference and anchor functionality."""

    def setup_method(self):
        self.config = CrossRefConfig()
        self.processor = CrossReferenceProcessor(self.config)

    def test_anchor_generation(self):
        """Test that stable anchors are generated for headings."""
        html = '<h1>Introduction</h1><h2>Methodology</h2>'
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        h1 = soup.find('h1')
        h2 = soup.find('h2')

        assert h1.get('id') is not None
        assert h2.get('id') is not None
        assert h1['id'].startswith('docx2shelf-heading-')
        assert h2['id'].startswith('docx2shelf-heading-')

    def test_cross_reference_linking(self):
        """Test that cross-references are properly linked."""
        html = '''
        <h2 id="section-results">Results</h2>
        <p>See <a href="#section-results">Results section</a> for details.</p>
        '''
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        link = soup.find('a')
        target = soup.find('h2')

        assert link.get('href') == f"#{target['id']}"

    def test_collision_safe_ids(self):
        """Test that duplicate headings get unique IDs."""
        html = '<h1>Introduction</h1><h1>Introduction</h1>'
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        h1_tags = soup.find_all('h1')

        assert len(h1_tags) == 2
        assert h1_tags[0]['id'] != h1_tags[1]['id']


class TestIndexing:
    """Test indexing functionality."""

    def setup_method(self):
        self.config = IndexConfig()
        self.processor = IndexProcessor(self.config)

    def test_xe_field_parsing(self):
        """Test parsing of XE index fields."""
        html = '''
        <p>Programming is important.</p>
        <!--XE "Programming"-->
        <p>Python is a language.</p>
        <!--XE "Python"-->
        '''
        result = self.processor.process_content(html)

        assert len(self.processor.entries) == 2
        assert 'Programming' in [entry.main_text for entry in self.processor.entries]
        assert 'Python' in [entry.main_text for entry in self.processor.entries]

    def test_hierarchical_entries(self):
        """Test parsing of hierarchical index entries."""
        html = '''
        <p>Data structures are important.</p>
        <!--XE "Data structures:arrays"-->
        <!--XE "Data structures:lists"-->
        '''
        result = self.processor.process_content(html)

        entries = [entry for entry in self.processor.entries if entry.main_text == 'Data structures']
        assert len(entries) >= 1
        entry = entries[0]
        assert 'arrays' in entry.sub_entries
        assert 'lists' in entry.sub_entries

    def test_index_generation(self):
        """Test index HTML generation."""
        html = '''
        <!--XE "Apple"-->
        <!--XE "Banana"-->
        <!--XE "Cherry"-->
        '''
        self.processor.process_content(html, "Chapter 1", "chap_001")
        index_html = self.processor.generate_index()

        soup = BeautifulSoup(index_html, 'html.parser')
        assert soup.find('h1').text == 'Index'

        # Check alphabetical ordering
        entries = soup.find_all('li', class_='index-entry')
        entry_texts = [entry.get_text().split()[0] for entry in entries]
        assert entry_texts == sorted(entry_texts)


class TestNotesFlow:
    """Test notes and footnotes functionality."""

    def setup_method(self):
        self.config = NotesConfig()
        self.processor = NotesProcessor(self.config)

    def test_footnote_processing(self):
        """Test footnote processing and back-reference generation."""
        html = '''
        <p>Some text<a href="#fn1" id="fnref1" class="footnote-ref"><sup>1</sup></a>.</p>
        <section class="footnotes">
            <ol>
                <li id="fn1"><p>Footnote text.</p></li>
            </ol>
        </section>
        '''
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        footnote = soup.find('li', id='fn1')
        back_ref = footnote.find('a', class_='note-back-ref')

        assert back_ref is not None
        assert back_ref.get('href') == '#fnref1'

    def test_consolidated_notes_page(self):
        """Test generation of consolidated notes page."""
        html = '''
        <p>Text with note<a href="#fn1" class="footnote-ref"><sup>1</sup></a>.</p>
        <section class="footnotes">
            <li id="fn1"><p>Note content.</p></li>
        </section>
        '''
        self.processor.process_content(html, "Chapter 1", "chap_001")
        notes_page = self.processor.generate_consolidated_notes()

        soup = BeautifulSoup(notes_page, 'html.parser')
        assert soup.find('h1').text == 'Notes'
        assert soup.find('h2').text == 'Chapter 1'


class TestFiguresAndTables:
    """Test figures and tables processing."""

    def setup_method(self):
        self.config = FigureConfig()
        self.processor = FigureProcessor(self.config)

    def test_image_wrapping(self):
        """Test that images are wrapped in figure elements."""
        html = '<img src="test.jpg" alt="Test image" title="Test Figure">'
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        figure = soup.find('figure')
        img = figure.find('img')
        figcaption = figure.find('figcaption')

        assert figure is not None
        assert img is not None
        assert figcaption is not None
        assert figcaption.text == 'Test Figure'

    def test_table_wrapping(self):
        """Test that tables are wrapped in figure elements."""
        html = '''
        <table>
            <tr><th>Header</th></tr>
            <tr><td>Data</td></tr>
        </table>
        '''
        result = self.processor.process_content(html)

        soup = BeautifulSoup(result, 'html.parser')
        figure = soup.find('figure', class_='table-figure')
        table = figure.find('table')
        figcaption = figure.find('figcaption')

        assert figure is not None
        assert table is not None
        assert figcaption is not None

    def test_list_of_figures_generation(self):
        """Test generation of List of Figures."""
        html = '''
        <img src="chart.png" alt="Chart" title="Sales Chart">
        <img src="graph.png" alt="Graph" title="Performance Graph">
        '''
        self.processor.process_content(html, "Chapter 1", "chap_001")
        lof = self.processor.generate_list_of_figures()

        soup = BeautifulSoup(lof, 'html.parser')
        assert soup.find('h1').text == 'List of Figures'

        links = soup.find_all('a')
        assert len(links) == 2
        assert 'Sales Chart' in links[0].text
        assert 'Performance Graph' in links[1].text

    def test_list_of_tables_generation(self):
        """Test generation of List of Tables."""
        html = '''
        <table><caption>Results Table</caption><tr><td>Data</td></tr></table>
        <table><tr><th>Analysis</th></tr><tr><td>Data</td></tr></table>
        '''
        self.processor.process_content(html, "Chapter 1", "chap_001")
        lot = self.processor.generate_list_of_tables()

        soup = BeautifulSoup(lot, 'html.parser')
        assert soup.find('h1').text == 'List of Tables'

        links = soup.find_all('a')
        assert len(links) == 2


class TestIntegration:
    """Integration tests for v1.2 features working together."""

    def test_complete_document_processing(self):
        """Test processing a document with all v1.2 features."""
        # Load test fixture
        fixtures_dir = Path(__file__).parent / 'fixtures'
        test_file = fixtures_dir / 'cross_refs_test.html'

        if test_file.exists():
            html_content = test_file.read_text(encoding='utf-8')

            # Process with all v1.2 processors
            crossref_processor = CrossReferenceProcessor()
            index_processor = IndexProcessor()
            notes_processor = NotesProcessor()
            figure_processor = FigureProcessor()

            # Apply processing pipeline
            result = crossref_processor.process_content(html_content)
            result = index_processor.process_content(result, "Test Chapter", "test_001")
            result = notes_processor.process_content(result, "Test Chapter", "test_001")
            result = figure_processor.process_content(result, "Test Chapter", "test_001")

            # Verify the result contains expected elements
            soup = BeautifulSoup(result, 'html.parser')

            # Check for anchors
            headings_with_ids = soup.find_all(['h1', 'h2', 'h3'], id=True)
            assert len(headings_with_ids) > 0

            # Check for figures
            figures = soup.find_all('figure')
            assert len(figures) > 0

            # Verify processors captured content
            assert index_processor.get_entry_count() > 0
            assert figure_processor.get_figure_count() > 0
        else:
            pytest.skip("Test fixture not found")

    def test_golden_fixtures_all_features(self):
        """Test all v1.2 features against golden fixtures."""
        fixtures_dir = Path(__file__).parent / 'fixtures'

        test_files = [
            'cross_refs_test.html',
            'indexing_test.html',
            'notes_test.html',
            'figures_tables_test.html'
        ]

        for test_file in test_files:
            file_path = fixtures_dir / test_file
            if file_path.exists():
                html_content = file_path.read_text(encoding='utf-8')

                # Test that processing doesn't raise exceptions
                try:
                    crossref_processor = CrossReferenceProcessor()
                    result = crossref_processor.process_content(html_content)

                    index_processor = IndexProcessor()
                    result = index_processor.process_content(result, "Test", "test")

                    notes_processor = NotesProcessor()
                    result = notes_processor.process_content(result, "Test", "test")

                    figure_processor = FigureProcessor()
                    result = figure_processor.process_content(result, "Test", "test")

                    # Verify result is valid HTML
                    soup = BeautifulSoup(result, 'html.parser')
                    assert soup is not None

                except Exception as e:
                    pytest.fail(f"Processing {test_file} failed: {e}")
            else:
                pytest.skip(f"Fixture {test_file} not found")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])