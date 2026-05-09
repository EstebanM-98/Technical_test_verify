import json

from components.extractor.core.document_parser import DocumentParser
from components.extractor.formats.dynamic_format import DynamicFormat


def test_split_pages_strips_and_removes_empty():
    parser = DocumentParser()
    text = "  page1  \f\n\n  \f page2 \f  "
    pages = parser._split_pages(text)
    assert pages == ["page1", "page2"]


def test_load_configs_handles_invalid_and_loads_valid(monkeypatch, tmp_path):
    from components.extractor.core import document_parser

    fake_root = tmp_path / "components" / "extractor"
    cfg_dir = fake_root / "configs"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "ok.json").write_text(json.dumps({"format_name": "X"}), encoding="utf-8")
    (cfg_dir / "broken.json").write_text("{bad", encoding="utf-8")

    fake_file = fake_root / "core" / "document_parser.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# dummy", encoding="utf-8")
    monkeypatch.setattr(document_parser, "__file__", str(fake_file))

    parser = DocumentParser()
    assert len(parser.formats) == 1
    assert parser.formats[0].format_name == "X"


def test_load_configs_creates_dir_if_missing(monkeypatch, tmp_path):
    from components.extractor.core import document_parser

    fake_file = tmp_path / "components" / "extractor" / "core" / "document_parser.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# dummy", encoding="utf-8")
    monkeypatch.setattr(document_parser, "__file__", str(fake_file))

    parser = DocumentParser()
    expected_dir = fake_file.parent.parent / "configs"
    assert expected_dir.exists()
    assert parser.formats == []


def test_parse_empty_text_returns_error():
    parser = DocumentParser()
    parser.formats = []

    result = parser.parse(" \n \f  ")
    assert result == {"error": "Empty document"}


def test_parse_unknown_format_returns_clear_error():
    parser = DocumentParser()
    parser.formats = []

    result = parser.parse("something not matching")
    assert "error" in result
    assert "configurado" in result["error"]


def test_parse_valid_document_uses_full_text_header_and_pages(read_fixture_text):
    cfg = {
        "format_name": "Controlled",
        "signature_regex": r"Switch",
        "header_fields": {
            "from_full_text": {"type": "regex", "pattern": r"Total USD \$([\d.]+)", "group": 1},
        },
        "line_items": {
            "start_anchor": r"Description\s+Quantity\s+Rate\s+Amount",
            "stop_anchor": r"^Total",
            "row_pattern": r"^(.*?)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)$",
            "columns": ["description", "quantity", "rate", "amount"],
        },
    }
    parser = DocumentParser()
    parser.formats = [DynamicFormat(cfg)]

    text = read_fixture_text("switch_ocr_text_multipage.txt")
    result = parser.parse(text)

    assert result["format"] == "Controlled"
    assert result["header"]["from_full_text"] == "125.00"
    assert len(result["pages"]) == 2
    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][0]["line_items_count"] == len(result["pages"][0]["line_items"])
    assert result["pages"][1]["line_items_count"] == len(result["pages"][1]["line_items"])
    assert len(result["all_line_items"]) == (
        result["pages"][0]["line_items_count"] + result["pages"][1]["line_items_count"]
    )
