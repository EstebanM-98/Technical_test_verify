import json

from components.extractor.utils.file_handler import read_text, write_json


def test_read_text_reads_utf8(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hola ñ", encoding="utf-8")

    assert read_text(str(path)) == "hola ñ"


def test_write_json_pretty_and_unicode(tmp_path):
    path = tmp_path / "out.json"
    data = {"mensaje": "áéí", "n": 1}

    write_json(data, str(path))

    raw = path.read_text(encoding="utf-8")
    assert "\n    \"n\": 1" in raw
    assert "áéí" in raw

    loaded = json.loads(raw)
    assert loaded == data
