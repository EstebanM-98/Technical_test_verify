from fastapi.testclient import TestClient

from components.validator import main as validator_main


client = TestClient(validator_main.app)


def test_validate_returns_validation_object(monkeypatch):
    class FakeEngine:
        def validate(self, data):
            return {"is_valid": True, "message": "ok", "errors": [], "details": [{"check": "x", "status": True, "message": "ok"}]}

    monkeypatch.setattr(validator_main, "engine", FakeEngine())

    payload = {"extracted_data": {"format": "Switch Invoice", "header": {}, "pages": []}}
    res = client.post("/validate", json=payload)

    assert res.status_code == 200
    body = res.json()
    assert body["is_valid"] is True
    assert "message" in body
    assert "errors" in body
    assert "details" in body


def test_validate_invalid_payload(monkeypatch):
    class FakeEngine:
        def validate(self, data):
            return {"is_valid": False, "message": "fail", "errors": ["e"], "details": [{"check": "x", "status": False, "message": "e"}]}

    monkeypatch.setattr(validator_main, "engine", FakeEngine())

    payload = {"extracted_data": {"format": "Switch Invoice", "header": {}, "pages": []}}
    res = client.post("/validate", json=payload)

    assert res.status_code == 200
    body = res.json()
    assert body["is_valid"] is False
    assert body["errors"]
