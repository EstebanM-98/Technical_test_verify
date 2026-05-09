from pathlib import Path

from components.extractor.main import extract_information


def test_extract_information_reads_from_file_and_writes_json(tmp_path, monkeypatch):
    src = tmp_path / "doc.txt"
    src.write_text("text", encoding="utf-8")

    class FakeParser:
        def parse(self, text):
            assert text == "text"
            return {"format": "X", "header": {}, "pages": [], "all_line_items": []}

    monkeypatch.setattr("components.extractor.main.DocumentParser", lambda: FakeParser())

    out_dir = tmp_path / "out"
    result = extract_information(str(src), str(out_dir))

    assert result["format"] == "X"
    out_file = out_dir / "doc" / "doc.json"
    assert out_file.exists()


def test_extract_information_uses_raw_text_when_not_file(tmp_path, monkeypatch):
    class FakeParser:
        def parse(self, text):
            assert text == "RAW OCR"
            return {"format": "X", "header": {}, "pages": [], "all_line_items": []}

    monkeypatch.setattr("components.extractor.main.DocumentParser", lambda: FakeParser())

    out_dir = tmp_path / "out"
    extract_information("RAW OCR", str(out_dir))

    out_file = out_dir / "extracted_document" / "extracted_document.json"
    assert out_file.exists()


def test_extract_information_default_output_dir(monkeypatch, tmp_path):
    fake_main = tmp_path / "components" / "extractor" / "main.py"
    fake_main.parent.mkdir(parents=True)
    fake_main.write_text("# dummy", encoding="utf-8")
    monkeypatch.setattr("components.extractor.main.__file__", str(fake_main))

    class FakeParser:
        def parse(self, text):
            return {"format": "X", "header": {}, "pages": [], "all_line_items": []}

    monkeypatch.setattr("components.extractor.main.DocumentParser", lambda: FakeParser())

    extract_information("RAW")

    out_file = fake_main.parent / "output" / "extracted_document" / "extracted_document.json"
    assert out_file.exists()


def test_extract_information_returns_error_without_writing(tmp_path, monkeypatch):
    class FakeParser:
        def parse(self, text):
            return {"error": "bad"}

    monkeypatch.setattr("components.extractor.main.DocumentParser", lambda: FakeParser())

    out_dir = tmp_path / "out"
    result = extract_information("RAW", str(out_dir))
    assert result == {"error": "bad"}
    assert not out_dir.exists()
