from frontend.utils import pdf_renderer, styles


def test_display_pdf_valid_page_calls_st_image(monkeypatch, mocker):
    fake_doc = mocker.Mock()
    fake_doc.__len__ = lambda self=None: 1

    fake_page = mocker.Mock()
    fake_pix = mocker.Mock()
    fake_pix.tobytes.return_value = b"png"
    fake_page.get_pixmap.return_value = fake_pix
    fake_doc.load_page.return_value = fake_page

    fake_fitz = mocker.Mock()
    fake_fitz.open.return_value = fake_doc
    fake_fitz.Matrix.return_value = object()

    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    image_mock = mocker.patch.object(pdf_renderer.st, "image")
    error_mock = mocker.patch.object(pdf_renderer.st, "error")

    pdf_renderer.display_pdf(b"%PDF", 0)

    image_mock.assert_called_once()
    error_mock.assert_not_called()


def test_display_pdf_out_of_bounds_calls_error(monkeypatch, mocker):
    fake_doc = mocker.Mock()
    fake_doc.__len__ = lambda self=None: 1

    fake_fitz = mocker.Mock()
    fake_fitz.open.return_value = fake_doc
    fake_fitz.Matrix.return_value = object()

    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    error_mock = mocker.patch.object(pdf_renderer.st, "error")

    pdf_renderer.display_pdf(b"%PDF", 3)
    error_mock.assert_called_once()


def test_display_pdf_exception_calls_error(monkeypatch, mocker):
    fake_fitz = mocker.Mock()
    fake_fitz.open.side_effect = RuntimeError("boom")
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    error_mock = mocker.patch.object(pdf_renderer.st, "error")

    pdf_renderer.display_pdf(b"%PDF", 0)
    error_mock.assert_called_once()


def test_inject_css_calls_markdown(mocker):
    md = mocker.patch.object(styles.st, "markdown")
    styles.inject_css()
    md.assert_called_once()
    assert md.call_args.kwargs["unsafe_allow_html"] is True


def test_display_logo_main_sidebar_and_missing(monkeypatch, mocker):
    image_main = mocker.patch.object(styles.st, "image")
    image_side = mocker.patch.object(styles.st.sidebar, "image")

    class DummyCol:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    mocker.patch.object(styles.st, "columns", return_value=[DummyCol(), DummyCol(), DummyCol()])

    monkeypatch.setattr("os.path.exists", lambda p: True)
    styles.display_logo(sidebar=False)
    image_main.assert_called_once()

    styles.display_logo(sidebar=True)
    image_side.assert_called_once()

    image_main.reset_mock()
    image_side.reset_mock()
    monkeypatch.setattr("os.path.exists", lambda p: False)
    styles.display_logo(sidebar=False)
    styles.display_logo(sidebar=True)
    image_main.assert_not_called()
    image_side.assert_not_called()
