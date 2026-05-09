import json
from pathlib import Path

from components.ocr import file_utils


def test_compute_content_hash_properties():
    a = b"abc"
    b = b"abcd"
    h1 = file_utils.compute_content_hash(a)
    h2 = file_utils.compute_content_hash(a)
    h3 = file_utils.compute_content_hash(b)

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


def test_check_cache_by_hash_miss(monkeypatch, tmp_path):
    monkeypatch.setattr(file_utils, "_CACHE_DIR", str(tmp_path))
    assert file_utils.check_cache_by_hash("deadbeef") is None


def test_check_cache_by_hash_hit(monkeypatch, tmp_path):
    monkeypatch.setattr(file_utils, "_CACHE_DIR", str(tmp_path))
    payload = {"ocr_text": "x", "character_count": 1}
    (tmp_path / "abc.json").write_text(json.dumps(payload), encoding="utf-8")

    data = file_utils.check_cache_by_hash("abc")
    assert data == payload


def test_check_cache_by_hash_bad_json_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(file_utils, "_CACHE_DIR", str(tmp_path))
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    assert file_utils.check_cache_by_hash("bad") is None


def test_save_cache_by_hash_writes_expected_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(file_utils, "_CACHE_DIR", str(tmp_path))

    saved_path = file_utils.save_cache_by_hash("hello", "hash123", "invoice.pdf")
    assert Path(saved_path).exists()

    data = json.loads(Path(saved_path).read_text(encoding="utf-8"))
    assert data["file_hash"] == "hash123"
    assert data["original_filename"] == "invoice.pdf"
    assert "processed_at" in data
    assert data["character_count"] == 5
    assert data["ocr_text"] == "hello"


def test_get_output_dir_creates_dir(monkeypatch, tmp_path):
    fake_file = tmp_path / "module" / "file_utils.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# dummy", encoding="utf-8")

    monkeypatch.setattr(file_utils, "__file__", str(fake_file))
    out = file_utils.get_output_dir()

    assert Path(out).exists()
    assert Path(out).name == "output"


def test_check_if_processed_hit_and_miss(monkeypatch, tmp_path):
    out = tmp_path / "output"
    monkeypatch.setattr(file_utils, "get_output_dir", lambda: str(out))

    missing = file_utils.check_if_processed("/tmp/mydoc.pdf")
    assert missing is False

    doc_dir = out / "mydoc"
    doc_dir.mkdir(parents=True)
    txt = doc_dir / "mydoc.txt"
    txt.write_text("ok", encoding="utf-8")

    found = file_utils.check_if_processed("/tmp/mydoc.pdf")
    assert found == str(txt)


def test_save_ocr_result_creates_expected_file(monkeypatch, tmp_path):
    out = tmp_path / "output"
    monkeypatch.setattr(file_utils, "get_output_dir", lambda: str(out))

    path = file_utils.save_ocr_result("content", "/x/a_file.pdf")
    p = Path(path)

    assert p.exists()
    assert p.name == "a_file.txt"
    assert p.parent.name == "a_file"
    assert p.read_text(encoding="utf-8") == "content"
