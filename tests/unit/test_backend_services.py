import pytest
import respx
from httpx import Response

from backend.services import run_pipeline


@pytest.mark.asyncio
async def test_run_pipeline_raises_if_env_missing(monkeypatch):
    monkeypatch.delenv("OCR_URL", raising=False)
    monkeypatch.delenv("EXTRACTOR_URL", raising=False)
    monkeypatch.delenv("VALIDATOR_URL", raising=False)

    with pytest.raises(RuntimeError, match="Required environment variables not set"):
        await run_pipeline("a.pdf", b"pdf")


@pytest.mark.asyncio
@respx.mock
async def test_run_pipeline_success(monkeypatch):
    monkeypatch.setenv("OCR_URL", "http://ocr/process")
    monkeypatch.setenv("EXTRACTOR_URL", "http://extractor/extract")
    monkeypatch.setenv("VALIDATOR_URL", "http://validator/validate")

    ocr_route = respx.post("http://ocr/process").mock(
        return_value=Response(200, json={"ocr_text": "OCR TEXT"})
    )
    ext_route = respx.post("http://extractor/extract").mock(
        return_value=Response(200, json={"format": "Switch Invoice", "pages": []})
    )
    val_route = respx.post("http://validator/validate").mock(
        return_value=Response(200, json={"is_valid": True, "message": "ok", "errors": [], "details": []})
    )

    result = await run_pipeline("a.pdf", b"%PDF")

    assert result["format"] == "Switch Invoice"
    assert "validation" in result
    assert result["validation"]["is_valid"] is True

    assert ocr_route.called and ext_route.called and val_route.called

    sent_files = ocr_route.calls[0].request
    assert b"multipart/form-data" in sent_files.headers.get("content-type", "").encode()

    ext_payload = ext_route.calls[0].request.content.decode()
    assert '"ocr_text":"OCR TEXT"' in ext_payload

    val_payload = val_route.calls[0].request.content.decode()
    assert '"extracted_data"' in val_payload


@pytest.mark.asyncio
@respx.mock
async def test_run_pipeline_ocr_failure_raises(monkeypatch):
    monkeypatch.setenv("OCR_URL", "http://ocr/process")
    monkeypatch.setenv("EXTRACTOR_URL", "http://extractor/extract")
    monkeypatch.setenv("VALIDATOR_URL", "http://validator/validate")

    respx.post("http://ocr/process").mock(return_value=Response(500, text="ocr fail"))

    with pytest.raises(RuntimeError, match="OCR Service failed"):
        await run_pipeline("a.pdf", b"x")


@pytest.mark.asyncio
@respx.mock
async def test_run_pipeline_extractor_failure_raises(monkeypatch):
    monkeypatch.setenv("OCR_URL", "http://ocr/process")
    monkeypatch.setenv("EXTRACTOR_URL", "http://extractor/extract")
    monkeypatch.setenv("VALIDATOR_URL", "http://validator/validate")

    respx.post("http://ocr/process").mock(return_value=Response(200, json={"ocr_text": ""}))
    respx.post("http://extractor/extract").mock(return_value=Response(500, text="extractor fail"))

    with pytest.raises(RuntimeError, match="Extractor Service failed"):
        await run_pipeline("a.pdf", b"x")


@pytest.mark.asyncio
@respx.mock
async def test_run_pipeline_validator_failure_adds_fallback(monkeypatch):
    monkeypatch.setenv("OCR_URL", "http://ocr/process")
    monkeypatch.setenv("EXTRACTOR_URL", "http://extractor/extract")
    monkeypatch.setenv("VALIDATOR_URL", "http://validator/validate")

    respx.post("http://ocr/process").mock(return_value=Response(200, json={"ocr_text": ""}))
    respx.post("http://extractor/extract").mock(
        return_value=Response(200, json={"format": "Switch Invoice", "pages": []})
    )
    respx.post("http://validator/validate").mock(return_value=Response(503, text="down"))

    result = await run_pipeline("a.pdf", b"x")

    assert result["validation"]["is_valid"] is False
    assert result["validation"]["message"].startswith("Validator failed:")
    assert result["validation"]["errors"] == []
    assert result["validation"]["details"] == []


@pytest.mark.asyncio
@respx.mock
async def test_run_pipeline_empty_ocr_text_still_calls_extractor(monkeypatch):
    monkeypatch.setenv("OCR_URL", "http://ocr/process")
    monkeypatch.setenv("EXTRACTOR_URL", "http://extractor/extract")
    monkeypatch.setenv("VALIDATOR_URL", "http://validator/validate")

    respx.post("http://ocr/process").mock(return_value=Response(200, json={"ocr_text": ""}))
    ext_route = respx.post("http://extractor/extract").mock(
        return_value=Response(200, json={"format": "Switch Invoice", "pages": []})
    )
    respx.post("http://validator/validate").mock(
        return_value=Response(200, json={"is_valid": True, "message": "ok", "errors": [], "details": []})
    )

    await run_pipeline("a.pdf", b"x")
    assert ext_route.called
    assert '"ocr_text":""' in ext_route.calls[0].request.content.decode()
