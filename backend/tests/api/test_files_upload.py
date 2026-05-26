from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'files-api.db'}")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path / "files"))
    get_settings.cache_clear()

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_upload_markdown_file_returns_file_contract(client: TestClient) -> None:

    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
        data={"directory_path": "/policies"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"] == {
        "id": payload["data"]["id"],
        "name": "policy.md",
        "original_filename": "policy.md",
        "file_type": "md",
        "mime_type": "text/markdown",
        "size_bytes": 39,
        "sha256": payload["data"]["sha256"],
        "directory_path": "/policies",
        "status": "uploaded",
    }
    assert len(payload["data"]["sha256"]) == 64
    assert payload["error"] is None
    assert payload["request_id"]


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("payload.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "FILE_TYPE_NOT_SUPPORTED"
    assert payload["error"]["message"] == "Only txt, md, pdf and docx files are supported in MVP."
    assert payload["request_id"]


def test_list_detail_and_soft_delete_file_contract(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("notes.txt", b"Plain notes", "text/plain")},
    )
    file_id = upload_response.json()["data"]["id"]

    list_response = client.get("/api/v1/files")
    detail_response = client.get(f"/api/v1/files/{file_id}")
    delete_response = client.delete(f"/api/v1/files/{file_id}")
    list_after_delete_response = client.get("/api/v1/files")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["id"] == file_id
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == file_id
    assert delete_response.status_code == 204
    assert list_after_delete_response.status_code == 200
    assert list_after_delete_response.json()["data"]["items"] == []
