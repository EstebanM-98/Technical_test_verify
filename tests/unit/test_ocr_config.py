import pytest

from components.ocr.config import load_configuration


REQUIRED_ENV = {
    "VERYFI_CLIENT_ID": "cid",
    "VERYFI_CLIENT_SECRET": "csecret",
    "VERYFI_USERNAME": "user",
    "VERYFI_API_KEY": "akey",
}


def test_load_configuration_reads_env_without_real_dotenv(monkeypatch):
    monkeypatch.setattr("components.ocr.config.os.path.exists", lambda _: False)
    monkeypatch.setattr("components.ocr.config.load_dotenv", lambda *args, **kwargs: None)

    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)

    cfg = load_configuration()
    assert cfg == {
        "client_id": "cid",
        "client_secret": "csecret",
        "username": "user",
        "api_key": "akey",
    }


def test_load_configuration_raises_when_missing_credentials(monkeypatch):
    monkeypatch.setattr("components.ocr.config.os.path.exists", lambda _: False)
    monkeypatch.setattr("components.ocr.config.load_dotenv", lambda *args, **kwargs: None)

    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("VERYFI_CLIENT_ID", "cid")

    with pytest.raises(ValueError, match="Missing Veryfi credentials"):
        load_configuration()
