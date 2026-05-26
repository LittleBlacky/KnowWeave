from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db, make_engine
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'chunk-curation-api.db'}")
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


def _build_single_chunk(client: TestClient) -> dict:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
    )
    file_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/files/{file_id}/parse")
    return client.post(f"/api/v1/files/{file_id}/chunks/build").json()["data"]["items"][0]


def test_patch_chunk_saves_edited_content_without_overwriting_raw_or_source_span(
    client: TestClient,
) -> None:
    chunk = _build_single_chunk(client)
    original_span = chunk["source_spans"][0]

    response = client.patch(
        f"/api/v1/chunks/{chunk['id']}",
        json={"edited_content": "Leave requests require manager approval."},
    )

    assert response.status_code == 200
    payload = response.json()
    updated = payload["data"]
    assert updated["raw_content"] == "# Policy\n\nLeave requests need approval."
    assert updated["edited_content"] == "Leave requests require manager approval."
    assert updated["is_manually_edited"] is True
    assert updated["search_text"] == "Leave requests require manager approval."
    assert updated["source_spans"] == [original_span]
    assert payload["error"] is None


def test_ignore_and_verify_chunk_update_status_and_searchability(client: TestClient) -> None:
    chunk = _build_single_chunk(client)

    ignored_response = client.post(f"/api/v1/chunks/{chunk['id']}/ignore")
    verified_response = client.post(f"/api/v1/chunks/{chunk['id']}/verify")

    assert ignored_response.status_code == 200
    ignored = ignored_response.json()["data"]
    assert ignored["status"] == "ignored"
    assert ignored["is_searchable"] is False

    assert verified_response.status_code == 200
    verified = verified_response.json()["data"]
    assert verified["status"] == "verified"
    assert verified["is_searchable"] is True


def test_get_missing_chunk_returns_standard_error(client: TestClient) -> None:
    response = client.get("/api/v1/chunks/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "CHUNK_NOT_FOUND"
