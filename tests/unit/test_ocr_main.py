from components.ocr.main import process_single_file


def test_process_single_file_missing_path_returns_none(tmp_path):
    missing = tmp_path / "no.pdf"
    ocr = object()
    assert process_single_file(str(missing), ocr) is None


def test_process_single_file_cache_hit_skips_ocr(monkeypatch, tmp_path, mocker):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"x")

    monkeypatch.setattr("components.ocr.main.check_if_processed", lambda _: "cached.txt")
    mock_ocr = mocker.Mock()

    out = process_single_file(str(pdf), mock_ocr)
    assert out == "cached.txt"
    mock_ocr.extract_ocr_text.assert_not_called()


def test_process_single_file_success_saves_result(monkeypatch, tmp_path, mocker):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"x")

    monkeypatch.setattr("components.ocr.main.check_if_processed", lambda _: False)
    monkeypatch.setattr("components.ocr.main.save_ocr_result", lambda text, path: "saved.txt")

    mock_ocr = mocker.Mock()
    mock_ocr.extract_ocr_text.return_value = "hello"

    out = process_single_file(str(pdf), mock_ocr)
    assert out == "saved.txt"


def test_process_single_file_empty_ocr_returns_none(monkeypatch, tmp_path, mocker):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"x")

    monkeypatch.setattr("components.ocr.main.check_if_processed", lambda _: False)
    mock_ocr = mocker.Mock()
    mock_ocr.extract_ocr_text.return_value = ""

    assert process_single_file(str(pdf), mock_ocr) is None


def test_process_single_file_exception_returns_none(monkeypatch, tmp_path, mocker):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"x")

    monkeypatch.setattr("components.ocr.main.check_if_processed", lambda _: False)
    mock_ocr = mocker.Mock()
    mock_ocr.extract_ocr_text.side_effect = RuntimeError("boom")

    assert process_single_file(str(pdf), mock_ocr) is None
