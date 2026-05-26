from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db, make_engine
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'tags-api.db'}")
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


def _seed_file(client: TestClient) -> str:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
    )
    return upload_response.json()["data"]["id"]


def test_tag_api_creates_updates_binds_lists_and_removes_tag(client: TestClient) -> None:
    file_id = _seed_file(client)

    create_response = client.post(
        "/api/v1/tags",
        json={"name": "HR", "description": "People policy", "color": "#2563eb"},
    )
    assert create_response.status_code == 201
    tag_id = create_response.json()["data"]["id"]

    duplicate_response = client.post("/api/v1/tags", json={"name": "HR"})
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "TAG_NAME_ALREADY_EXISTS"

    update_response = client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "People Ops", "description": "Updated", "color": "#16a34a"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "People Ops"

    bind_response = client.post(
        "/api/v1/tag-bindings",
        json={"tag_id": tag_id, "target_type": "file", "target_id": file_id},
    )
    assert bind_response.status_code == 201
    assert bind_response.json()["data"]["target_id"] == file_id

    list_response = client.get("/api/v1/tags")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["binding_count"] == 1

    remove_response = client.request(
        "DELETE",
        "/api/v1/tag-bindings",
        json={"tag_id": tag_id, "target_type": "file", "target_id": file_id},
    )
    assert remove_response.status_code == 204

    delete_response = client.delete(f"/api/v1/tags/{tag_id}")
    assert delete_response.status_code == 204


def test_tag_binding_api_rejects_missing_target(client: TestClient) -> None:
    tag_id = client.post("/api/v1/tags", json={"name": "HR"}).json()["data"]["id"]

    response = client.post(
        "/api/v1/tag-bindings",
        json={"tag_id": tag_id, "target_type": "file", "target_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TAG_TARGET_NOT_FOUND"
