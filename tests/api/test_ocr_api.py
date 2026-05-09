from fastapi.testclient import TestClient

from components.ocr import api as ocr_api


client = TestClient(ocr_api.app)


def test_process_cache_hit_returns_cached_and_skips_ocr(monkeypatch, mocker):
    monkeypatch.setattr(ocr_api, "ocr_service", mocker.Mock())
    monkeypatch.setattr(ocr_api, "compute_content_hash", lambda content: "h1")
    monkeypatch.setattr(
        ocr_api,
        "check_cache_by_hash",
        lambda h: {"ocr_text": "cached text", "character_count": 11},
    )

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})

    assert res.status_code == 200
    assert res.json()["ocr_text"] == "cached text"
    assert res.json()["cached"] is True
    ocr_api.ocr_service.extract_ocr_text.assert_not_called()


def test_process_cache_miss_success_calls_save_cache(monkeypatch, mocker):
    svc = mocker.Mock()
    svc.extract_ocr_text.return_value = "ocr result"

    monkeypatch.setattr(ocr_api, "ocr_service", svc)
    monkeypatch.setattr(ocr_api, "compute_content_hash", lambda content: "h2")
    monkeypatch.setattr(ocr_api, "check_cache_by_hash", lambda h: None)
    save_mock = mocker.patch.object(ocr_api, "save_cache_by_hash")

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})

    assert res.status_code == 200
    assert res.json()["cached"] is False
    assert res.json()["ocr_text"] == "ocr result"
    save_mock.assert_called_once()


def test_process_returns_500_when_service_not_initialized(monkeypatch):
    monkeypatch.setattr(ocr_api, "ocr_service", None)

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 500


def test_process_returns_400_when_empty_ocr(monkeypatch, mocker):
    svc = mocker.Mock()
    svc.extract_ocr_text.return_value = ""

    monkeypatch.setattr(ocr_api, "ocr_service", svc)
    monkeypatch.setattr(ocr_api, "compute_content_hash", lambda content: "h3")
    monkeypatch.setattr(ocr_api, "check_cache_by_hash", lambda h: None)

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 400


def test_process_returns_500_on_unexpected_error(monkeypatch, mocker):
    svc = mocker.Mock()
    svc.extract_ocr_text.side_effect = RuntimeError("boom")

    monkeypatch.setattr(ocr_api, "ocr_service", svc)
    monkeypatch.setattr(ocr_api, "compute_content_hash", lambda content: "h4")
    monkeypatch.setattr(ocr_api, "check_cache_by_hash", lambda h: None)

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 500


def test_process_temp_file_is_cleaned_up(monkeypatch, mocker):
    svc = mocker.Mock()
    svc.extract_ocr_text.return_value = "ok"

    monkeypatch.setattr(ocr_api, "ocr_service", svc)
    monkeypatch.setattr(ocr_api, "compute_content_hash", lambda content: "h5")
    monkeypatch.setattr(ocr_api, "check_cache_by_hash", lambda h: None)
    monkeypatch.setattr(ocr_api, "save_cache_by_hash", lambda *args, **kwargs: None)

    removed_paths = []

    def fake_remove(path):
        removed_paths.append(path)

    monkeypatch.setattr(ocr_api.os, "remove", fake_remove)

    res = client.post("/process", files={"file": ("a.pdf", b"%PDF", "application/pdf")})

    assert res.status_code == 200
    assert removed_paths
