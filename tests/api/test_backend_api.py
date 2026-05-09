import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.database import get_db


def _build_client(tmp_path, monkeypatch):
    from backend import api as backend_api

    db_file = tmp_path / "test_backend.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    models.Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    backend_api.app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(backend_api, "UPLOADS_DIR", str(tmp_path / "uploads"))

    client = TestClient(backend_api.app)
    return client, backend_api


def _register_and_login(client, username="user1", password="pass1"):
    reg = client.post("/auth/register", json={"username": username, "password": password})
    assert reg.status_code == 200
    login = client.post("/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return login.json()["user_id"]


def test_auth_register_and_duplicate_and_login(tmp_path, monkeypatch):
    client, backend_api = _build_client(tmp_path, monkeypatch)

    r1 = client.post("/auth/register", json={"username": "alice", "password": "secret"})
    assert r1.status_code == 200

    r_dup = client.post("/auth/register", json={"username": "alice", "password": "secret"})
    assert r_dup.status_code == 400

    ok_login = client.post("/auth/login", json={"username": "alice", "password": "secret"})
    assert ok_login.status_code == 200
    assert "user_id" in ok_login.json()
    assert ok_login.json()["username"] == "alice"

    bad_login = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert bad_login.status_code == 400

    backend_api.app.dependency_overrides.clear()


def test_projects_crud_and_filters_and_pdf_delete(tmp_path, monkeypatch):
    client, backend_api = _build_client(tmp_path, monkeypatch)

    user1 = _register_and_login(client, "u1", "p1")
    user2 = _register_and_login(client, "u2", "p2")

    p1 = client.post(f"/projects?user_id={user1}", json={"name": "proj1"})
    p2 = client.post(f"/projects?user_id={user2}", json={"name": "proj2"})
    assert p1.status_code == 200
    assert p2.status_code == 200

    list_u1 = client.get(f"/projects?user_id={user1}")
    assert list_u1.status_code == 200
    assert len(list_u1.json()) == 1
    assert list_u1.json()[0]["name"] == "proj1"

    pid = p1.json()["id"]
    get_ok = client.get(f"/projects/{pid}")
    assert get_ok.status_code == 200
    assert get_ok.json()["id"] == pid
    assert get_ok.json()["extracted_data"] is None

    get_404 = client.get("/projects/99999")
    assert get_404.status_code == 404

    upd_ok = client.put(f"/projects/{pid}", json={"name": "renamed"})
    assert upd_ok.status_code == 200
    assert upd_ok.json()["name"] == "renamed"

    upd_404 = client.put("/projects/99999", json={"name": "x"})
    assert upd_404.status_code == 404

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    pdf_path = uploads / f"project_{pid}.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    del_ok = client.delete(f"/projects/{pid}")
    assert del_ok.status_code == 200
    assert not pdf_path.exists()

    del_404 = client.delete("/projects/99999")
    assert del_404.status_code == 404

    backend_api.app.dependency_overrides.clear()


def test_process_project_success_and_failure_and_not_found(tmp_path, monkeypatch):
    client, backend_api = _build_client(tmp_path, monkeypatch)
    user_id = _register_and_login(client, "proc", "procpass")

    created = client.post(f"/projects?user_id={user_id}", json={"name": "to-process"})
    pid = created.json()["id"]

    async def fake_pipeline(filename, content):
        assert filename == "file.pdf"
        assert content.startswith(b"%PDF")
        return {"format": "Switch Invoice", "header": {"total_amount": "1.00"}, "pages": []}

    monkeypatch.setattr(backend_api, "run_pipeline", fake_pipeline)

    resp = client.post(
        f"/projects/{pid}/process",
        files={"file": ("file.pdf", b"%PDF-sample", "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["format"] == "Switch Invoice"

    saved_pdf = tmp_path / "uploads" / f"project_{pid}.pdf"
    assert saved_pdf.exists()

    project = client.get(f"/projects/{pid}")
    assert project.status_code == 200
    assert project.json()["pdf_filename"] == "file.pdf"
    assert project.json()["extracted_data"]["format"] == "Switch Invoice"

    async def boom(*args, **kwargs):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(backend_api, "run_pipeline", boom)
    err = client.post(
        f"/projects/{pid}/process",
        files={"file": ("file.pdf", b"%PDF-sample", "application/pdf")},
    )
    assert err.status_code == 500

    missing = client.post(
        "/projects/99999/process",
        files={"file": ("file.pdf", b"%PDF-sample", "application/pdf")},
    )
    assert missing.status_code == 404

    backend_api.app.dependency_overrides.clear()


def test_get_project_pdf_endpoint(tmp_path, monkeypatch):
    client, backend_api = _build_client(tmp_path, monkeypatch)
    user_id = _register_and_login(client, "pdfu", "pdfp")
    created = client.post(f"/projects?user_id={user_id}", json={"name": "pdf"})
    pid = created.json()["id"]

    path = tmp_path / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"project_{pid}.pdf"
    file_path.write_bytes(b"%PDF-test")

    ok = client.get(f"/projects/{pid}/pdf")
    assert ok.status_code == 200
    assert ok.content.startswith(b"%PDF")

    missing = client.get("/projects/99999/pdf")
    assert missing.status_code == 404

    backend_api.app.dependency_overrides.clear()
