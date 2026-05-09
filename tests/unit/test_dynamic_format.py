from components.extractor.formats.dynamic_format import DynamicFormat


def _base_config():
    return {
        "format_name": "Test",
        "signature_regex": r"InvoiceX",
        "header_fields": {
            "vendor": {"type": "static", "value": "ACME"},
            "invoice_number": {
                "type": "regex",
                "pattern": r"INV-(\d+)",
                "group": 1,
            },
            "optional": {"type": "regex", "pattern": r"NO_MATCH:(\d+)", "group": 1},
        },
        "line_items": {
            "start_anchor": r"Description\s+Quantity\s+Rate\s+Amount",
            "stop_anchor": r"^Total",
            "row_pattern": r"^(.*?)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)$",
            "columns": ["description", "quantity", "rate", "amount"],
            "sku": {
                "source_field": "description",
                "pattern": r"SKU:(\w+)",
                "group": 1,
            },
        },
    }


def test_is_match_true_false_and_no_signature():
    cfg = _base_config()
    fmt = DynamicFormat(cfg)
    assert fmt.is_match("InvoiceX hello") is True
    assert fmt.is_match("nope") is False

    cfg["signature_regex"] = ""
    fmt2 = DynamicFormat(cfg)
    assert fmt2.is_match("InvoiceX hello") is False


def test_extract_header_fields_static_regex_missing():
    fmt = DynamicFormat(_base_config())
    result = fmt.extract_header_fields("INV-123 some text")

    assert result["vendor"] == "ACME"
    assert result["invoice_number"] == "123"
    assert result["optional"] is None


def test_extract_line_items_empty_when_no_rules():
    fmt = DynamicFormat({"format_name": "X", "line_items": {}})
    assert fmt.extract_line_items("anything") == []


def test_extract_line_items_parsing_flow_and_continuation_and_sku():
    fmt = DynamicFormat(_base_config())
    text = """
Header block
Description Quantity Rate Amount
Transport SKU:ABC123 base row 2.00 50.00 100.00
extra continuation line
Cloud SKU:DEF999 1,000.00 2.50 2,500.00
Total 2600.00
ignored tail
"""
    items = fmt.extract_line_items(text)

    assert len(items) == 2
    assert list(items[0].keys())[0] == "sku"
    assert items[0]["description"].endswith("extra continuation line")
    assert items[0]["sku"] == "ABC123"
    assert items[0]["quantity"] == 2.0
    assert items[0]["rate"] == 50.0
    assert items[0]["amount"] == 100.0
    assert items[1]["quantity"] == 1000.0
    assert items[1]["amount"] == 2500.0


def test_extract_line_items_supports_negative_values():
    cfg = _base_config()
    cfg["line_items"]["row_pattern"] = (
        r"^(.*?)\s+(-?[\d,]+\.\d+)\s+(-?[\d,]+\.\d+)\s+(-?[\d,]+\.\d+)$"
    )
    fmt = DynamicFormat(cfg)
    text = """
Description Quantity Rate Amount
Discount SKU:DISC -1.00 10.00 -10.00
Total
"""
    items = fmt.extract_line_items(text)
    assert len(items) == 1
    assert items[0]["quantity"] == -1.0
    assert items[0]["amount"] == -10.0


def test_extract_sku_direct_cases():
    cfg = _base_config()
    fmt = DynamicFormat(cfg)
    assert fmt._extract_sku({"description": "sku missing"}) is None
    assert fmt._extract_sku({"description": "hello SKU:ZX9 world"}) == "ZX9"

    cfg_no = _base_config()
    cfg_no["line_items"].pop("sku")
    fmt_no = DynamicFormat(cfg_no)
    assert fmt_no._extract_sku({"description": "SKU:A"}) is None

    cfg_empty = _base_config()
    cfg_empty["line_items"]["sku"]["pattern"] = ""
    fmt_empty = DynamicFormat(cfg_empty)
    assert fmt_empty._extract_sku({"description": "SKU:A"}) is None


def test_switch_like_config_shape_supports_sku_extraction(read_fixture_text):
    from pathlib import Path
    import json

    cfg_path = Path(__file__).resolve().parents[2] / "components" / "extractor" / "configs" / "switch.json"
    switch_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    fmt = DynamicFormat(switch_cfg)

    text = read_fixture_text("switch_ocr_text_valid.txt")
    items = fmt.extract_line_items(text)

    assert len(items) >= 1
    assert "sku" in items[0]
    assert items[0]["sku"] == "12345"
