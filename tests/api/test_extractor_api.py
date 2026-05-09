from fastapi.testclient import TestClient

from components.extractor import api as extractor_api


client = TestClient(extractor_api.app)


def test_extract_api_success(monkeypatch):
    class FakeParser:
        def parse(self, text):
            return {"format": "Switch Invoice", "header": {}, "pages": [], "all_line_items": []}

    monkeypatch.setattr(extractor_api, "parser", FakeParser())

    res = client.post("/extract", json={"ocr_text": "some text"})
    assert res.status_code == 200
    assert res.json()["format"] == "Switch Invoice"


def test_extract_api_returns_400_on_parser_error(monkeypatch):
    class FakeParser:
        def parse(self, text):
            return {"error": "unknown format"}

    monkeypatch.setattr(extractor_api, "parser", FakeParser())

    res = client.post("/extract", json={"ocr_text": "some text"})
    assert res.status_code == 400


def test_extract_api_returns_500_on_unexpected_exception(monkeypatch):
    class FakeParser:
        def parse(self, text):
            raise RuntimeError("boom")

    monkeypatch.setattr(extractor_api, "parser", FakeParser())

    res = client.post("/extract", json={"ocr_text": "some text"})
    assert res.status_code == 500
