from docx2shelf.convert import split_html_by_heading, split_html_by_pagebreak


def test_split_html_by_heading_h1():
    html = "<h1>A</h1><p>1</p><h1>B</h1><p>2</p>"
    chunks = split_html_by_heading(html, level="h1")
    assert len(chunks) == 2
    assert "A" in chunks[0] and "1" in chunks[0]
    assert "B" in chunks[1] and "2" in chunks[1]


def test_split_html_by_pagebreak_hr():
    html = '<p>a</p><hr class="pagebreak" /><p>b</p>'
    parts = split_html_by_pagebreak(html)
    assert len(parts) == 2
    assert "a" in parts[0]
    assert "b" in parts[1]
