from types import SimpleNamespace

from frontend.views import dashboard


def test_open_project_loads_project_and_pdf_success(mocker):
    session_state = SimpleNamespace()
    mocker.patch.object(dashboard.st, "session_state", session_state)
    rerun = mocker.patch.object(dashboard.st, "rerun")

    project_resp = mocker.Mock(status_code=200)
    project_resp.json.return_value = {"extracted_data": {"x": 1}}

    pdf_resp = mocker.Mock(status_code=200, content=b"%PDF")

    get_mock = mocker.patch.object(dashboard.httpx, "get", side_effect=[project_resp, pdf_resp])

    dashboard._open_project(10, "http://backend")

    assert session_state.current_project == 10
    assert session_state.pdf_page == 0
    assert session_state.extracted_data == {"x": 1}
    assert session_state.pdf_bytes == b"%PDF"
    assert get_mock.call_count == 2
    rerun.assert_called_once()


def test_open_project_handles_project_load_error(mocker):
    session_state = SimpleNamespace()
    mocker.patch.object(dashboard.st, "session_state", session_state)
    mocker.patch.object(dashboard.st, "rerun")
    mocker.patch.object(dashboard.st, "warning")

    pdf_resp = mocker.Mock(status_code=200, content=b"%PDF")
    mocker.patch.object(dashboard.httpx, "get", side_effect=[RuntimeError("boom"), pdf_resp])

    dashboard._open_project(10, "http://backend")

    assert session_state.extracted_data is None
    assert session_state.pdf_bytes == b"%PDF"


def test_open_project_handles_pdf_load_error(mocker):
    session_state = SimpleNamespace()
    mocker.patch.object(dashboard.st, "session_state", session_state)
    mocker.patch.object(dashboard.st, "rerun")
    mocker.patch.object(dashboard.st, "warning")

    project_resp = mocker.Mock(status_code=200)
    project_resp.json.return_value = {"extracted_data": {"x": 1}}

    mocker.patch.object(dashboard.httpx, "get", side_effect=[project_resp, RuntimeError("boom")])

    dashboard._open_project(10, "http://backend")

    assert session_state.extracted_data == {"x": 1}
    assert session_state.pdf_bytes is None
