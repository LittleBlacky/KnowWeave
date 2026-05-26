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
    engine = make_engine(f"sqlite:///{tmp_path / 'wiki-api.db'}")
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
        files={
            "file": (
                "policy.md",
                b"# Policy\n\nLeave requests require manager approval.",
                "text/markdown",
            )
        },
    )
    file_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/files/{file_id}/parse")
    client.post(f"/api/v1/files/{file_id}/chunks/build")
    return file_id


def test_wiki_api_creates_lists_reads_and_edits_document_wiki(client: TestClient) -> None:
    file_id = _seed_file(client)

    create_response = client.post(f"/api/v1/files/{file_id}/wiki")

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["wiki_type"] == "document_wiki"
    assert created["status"] == "draft"
    assert "Leave requests require manager approval." in created["content_markdown"]

    list_response = client.get("/api/v1/wiki")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["id"] == created["id"]

    contract_list_response = client.get("/api/v1/wiki/pages")
    assert contract_list_response.status_code == 200
    assert contract_list_response.json()["data"]["items"][0]["id"] == created["id"]

    detail_response = client.get(f"/api/v1/wiki/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == created["id"]

    contract_detail_response = client.get(f"/api/v1/wiki/pages/{created['id']}")
    assert contract_detail_response.status_code == 200
    assert contract_detail_response.json()["data"]["id"] == created["id"]

    rejected = client.patch(
        f"/api/v1/wiki/{created['id']}",
        json={"content_markdown": "Updated policy content.", "change_summary": ""},
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "WIKI_CHANGE_SUMMARY_REQUIRED"

    update_response = client.patch(
        f"/api/v1/wiki/{created['id']}",
        json={
            "content_markdown": "Updated policy content.",
            "change_summary": "Clarified manager approval policy.",
            "status": "verified",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["content_markdown"] == "Updated policy content."
    assert update_response.json()["data"]["status"] == "verified"

    contract_update_response = client.patch(
        f"/api/v1/wiki/pages/{created['id']}",
        json={
            "content_markdown": "Updated again.",
            "change_summary": "Verified contract alias.",
            "status": "verified",
        },
    )
    assert contract_update_response.status_code == 200
    assert contract_update_response.json()["data"]["content_markdown"] == "Updated again."


def test_wiki_api_returns_citations_with_source_span(client: TestClient) -> None:
    file_id = _seed_file(client)
    wiki_id = client.post(f"/api/v1/files/{file_id}/wiki").json()["data"]["id"]

    response = client.get(f"/api/v1/wiki/{wiki_id}/citations")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["target_type"] == "wiki_page"
    assert payload["items"][0]["source_span_id"]
    assert payload["items"][0]["preview_text"] == "# Policy\n\nLeave requests require manager approval."
    assert payload["items"][0]["source_available"] is True

    contract_response = client.get(f"/api/v1/wiki/pages/{wiki_id}/citations")
    assert contract_response.status_code == 200
    assert contract_response.json()["data"]["total"] == 1
