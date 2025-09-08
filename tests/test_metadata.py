from docx2shelf.metadata import build_output_filename, validate_isbn13, validate_lang_code, normalize_lang


def test_build_output_filename_simple():
    assert build_output_filename("My Book", None, None).endswith("My Book.epub")


def test_build_output_filename_series():
    name = build_output_filename("My Book", "Saga", "02")
    assert name.startswith("Saga-02-My Book")
    assert name.endswith(".epub")


def test_validate_isbn13():
    assert validate_isbn13("9780306406157")
    assert validate_isbn13("978-0-306-40615-7")
    assert not validate_isbn13("9780306406158")


def test_validate_lang_code():
    assert validate_lang_code("en")
    assert validate_lang_code("en-US")
    assert validate_lang_code("zh-Hant-TW")
    assert not validate_lang_code("")
    assert not validate_lang_code("english")
    assert normalize_lang("EN-us") == "en-us"
