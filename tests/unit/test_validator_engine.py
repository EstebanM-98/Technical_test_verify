import json
from pathlib import Path

from components.validator.core.rule_engine import ValidatorEngine


def test_load_configs_creates_dir_when_missing(tmp_path, monkeypatch):
    from components.validator.core import rule_engine

    fake_file = tmp_path / "components" / "validator" / "core" / "rule_engine.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# dummy", encoding="utf-8")
    monkeypatch.setattr(rule_engine, "__file__", str(fake_file))

    expected_dir = fake_file.parent.parent / "configs"
    assert not expected_dir.exists()

    engine = ValidatorEngine()

    assert isinstance(engine.configs, dict)
    assert expected_dir.exists()


def test_load_configs_from_temp_dir_skips_invalid(monkeypatch, tmp_path):
    config_root = tmp_path / "components" / "validator" / "configs"
    config_root.mkdir(parents=True)

    (config_root / "valid.json").write_text(
        json.dumps({"format_name": "A", "rules": []}), encoding="utf-8"
    )
    (config_root / "missing_format.json").write_text(json.dumps({"rules": []}), encoding="utf-8")
    (config_root / "broken.json").write_text("{oops", encoding="utf-8")

    from components.validator.core import rule_engine

    fake_file = config_root.parent / "core" / "rule_engine.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# dummy", encoding="utf-8")
    monkeypatch.setattr(rule_engine, "__file__", str(fake_file))

    engine = ValidatorEngine()
    assert "A" in engine.configs
    assert len(engine.configs) == 1


def test_validate_missing_format_returns_invalid():
    engine = ValidatorEngine()
    engine.configs = {"Switch Invoice": {"rules": []}}

    result = engine.validate({"header": {}, "pages": []})

    assert result["is_valid"] is False
    assert "No validation config found" in result["message"]
    assert result["errors"] == []


def test_validate_unknown_format_returns_invalid(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {"Switch Invoice": {"rules": []}}

    payload = read_fixture_json("switch_extracted_unknown_format.json")
    result = engine.validate(payload)

    assert result["is_valid"] is False
    assert "Unknown Invoice" in result["message"]


def test_validate_without_rules_returns_validated(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {"Switch Invoice": {"rules": []}}

    payload = read_fixture_json("switch_extracted_valid.json")
    result = engine.validate(payload)

    assert result["is_valid"] is True
    assert result["message"] == "Validated ✅"
    assert result["errors"] == []


def test_validate_valid_document_passes_with_details(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [
                {"type": "row_math", "tolerance": 0.1},
                {
                    "type": "document_sum",
                    "sum_column": "amount",
                    "equals_header": "total_amount",
                    "tolerance": 0.1,
                },
            ]
        }
    }

    payload = read_fixture_json("switch_extracted_valid.json")
    result = engine.validate(payload)

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert any(d["check"].startswith("Row") for d in result["details"])
    assert any(d["check"] == "Document Sum" and d["status"] for d in result["details"])


def test_validate_row_math_failure(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [{"type": "row_math", "tolerance": 0.1}],
        }
    }

    payload = read_fixture_json("switch_extracted_invalid_row_math.json")
    result = engine.validate(payload)

    assert result["is_valid"] is False
    assert any("Math Error" in e for e in result["errors"])
    assert any(d["check"].startswith("Row") and not d["status"] for d in result["details"])


def test_validate_document_sum_failure(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [
                {
                    "type": "document_sum",
                    "sum_column": "amount",
                    "equals_header": "total_amount",
                    "tolerance": 0.1,
                }
            ]
        }
    }

    payload = read_fixture_json("switch_extracted_invalid_document_sum.json")
    result = engine.validate(payload)

    assert result["is_valid"] is False
    assert any("Sum Error" in e for e in result["errors"])


def test_validate_missing_total_amount_returns_error(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [
                {
                    "type": "document_sum",
                    "sum_column": "amount",
                    "equals_header": "total_amount",
                    "tolerance": 0.1,
                }
            ]
        }
    }

    payload = read_fixture_json("switch_extracted_missing_total.json")
    result = engine.validate(payload)

    assert result["is_valid"] is False
    assert any("Header field 'total_amount' not found" in e for e in result["errors"])


def test_validate_numeric_strings_with_commas_are_supported():
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [
                {"type": "row_math", "tolerance": 0.1},
                {
                    "type": "document_sum",
                    "sum_column": "amount",
                    "equals_header": "total_amount",
                    "tolerance": 0.1,
                },
            ]
        }
    }

    payload = {
        "format": "Switch Invoice",
        "header": {"total_amount": "1,000.00"},
        "pages": [
            {
                "line_items": [
                    {"quantity": "10", "rate": "100", "amount": "1,000.00"}
                ]
            }
        ],
    }

    result = engine.validate(payload)
    assert result["is_valid"] is True


def test_validate_invalid_numeric_values_do_not_crash():
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [
                {"type": "row_math", "tolerance": 0.1},
                {
                    "type": "document_sum",
                    "sum_column": "amount",
                    "equals_header": "total_amount",
                    "tolerance": 0.1,
                },
            ]
        }
    }

    payload = {
        "format": "Switch Invoice",
        "header": {"total_amount": "abc"},
        "pages": [{"line_items": [{"quantity": "x", "rate": "1", "amount": "2"}]}],
    }

    result = engine.validate(payload)
    assert result["is_valid"] is False
    assert any("Evaluation Error" in e for e in result["errors"])


def test_validate_unknown_rule_type_is_skipped(read_fixture_json):
    engine = ValidatorEngine()
    engine.configs = {
        "Switch Invoice": {
            "rules": [{"type": "made_up_rule"}],
        }
    }

    payload = read_fixture_json("switch_extracted_valid.json")
    result = engine.validate(payload)

    assert result["is_valid"] is True
    assert result["errors"] == []
