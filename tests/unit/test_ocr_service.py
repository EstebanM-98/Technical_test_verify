import pytest

from components.ocr.ocr import VeryfiOCR


def test_veryfi_ocr_initializes_client_with_expected_args(mocker):
    client_cls = mocker.patch("components.ocr.ocr.Client")

    cfg = {
        "client_id": "id",
        "client_secret": "secret",
        "username": "user",
        "api_key": "key",
    }
    VeryfiOCR(cfg)

    client_cls.assert_called_once_with("id", "secret", "user", "key")


def test_process_document_delegates_and_returns_dict(mocker):
    client_cls = mocker.patch("components.ocr.ocr.Client")
    client_cls.return_value.process_document.return_value = {"ocr_text": "abc", "x": 1}

    svc = VeryfiOCR(
        {
            "client_id": "id",
            "client_secret": "secret",
            "username": "user",
            "api_key": "key",
        }
    )

    res = svc.process_document("/tmp/a.pdf")
    assert res == {"ocr_text": "abc", "x": 1}
    client_cls.return_value.process_document.assert_called_once_with("/tmp/a.pdf")


def test_process_document_wraps_exception_as_runtime_error(mocker):
    client_cls = mocker.patch("components.ocr.ocr.Client")
    client_cls.return_value.process_document.side_effect = Exception("boom")

    svc = VeryfiOCR(
        {
            "client_id": "id",
            "client_secret": "secret",
            "username": "user",
            "api_key": "key",
        }
    )

    with pytest.raises(RuntimeError, match="Error communicating with Veryfi API"):
        svc.process_document("/tmp/a.pdf")


def test_extract_ocr_text_returns_field_or_empty(mocker):
    svc = VeryfiOCR.__new__(VeryfiOCR)
    mocker.patch.object(svc, "process_document", return_value={"ocr_text": "hello"})
    assert svc.extract_ocr_text("x.pdf") == "hello"

    svc2 = VeryfiOCR.__new__(VeryfiOCR)
    mocker.patch.object(svc2, "process_document", return_value={"nope": "x"})
    assert svc2.extract_ocr_text("x.pdf") == ""
