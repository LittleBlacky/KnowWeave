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
    engine = make_engine(f"sqlite:///{tmp_path / 'knowledge-units-api.db'}")
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


def _seed_chunk(client: TestClient) -> str:
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
    build_response = client.post(f"/api/v1/files/{file_id}/chunks/build")
    return build_response.json()["data"]["items"][0]["id"]


def test_knowledge_unit_api_creates_lists_reads_and_updates_unit(client: TestClient) -> None:
    chunk_id = _seed_chunk(client)
    tag_id = client.post("/api/v1/tags", json={"name": "HR"}).json()["data"]["id"]

    create_response = client.post(
        "/api/v1/knowledge-units",
        json={
            "title": "Leave approval rule",
            "unit_type": "rule",
            "content": "Leave requests require manager approval.",
            "summary": "Manager approval is required.",
            "status": "pending_review",
            "applicable_scope": "HR policies",
            "source_chunk_ids": [chunk_id],
            "tag_ids": [tag_id],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["title"] == "Leave approval rule"
    assert created["created_from"] == "chunk"
    assert created["source_count"] == 1
    assert created["tags"][0]["name"] == "HR"

    list_response = client.get(
        "/api/v1/knowledge-units",
        params={"tag": "HR", "status": "pending_review"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["id"] == created["id"]

    detail_response = client.get(f"/api/v1/knowledge-units/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["sources"][0]["chunk_id"] == chunk_id

    update_response = client.patch(
        f"/api/v1/knowledge-units/{created['id']}",
        json={
            "title": "Verified leave approval rule",
            "content": "Leave requests require manager approval.",
            "status": "verified",
            "source_chunk_ids": [chunk_id],
            "tag_ids": [tag_id],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "verified"
    assert update_response.json()["data"]["verified_at"] is not None


def test_knowledge_unit_api_rejects_verified_unit_without_source(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge-units",
        json={
            "title": "Unbacked rule",
            "content": "Managers approve all leave.",
            "status": "verified",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "KNOWLEDGE_UNIT_VERIFIED_SOURCE_REQUIRED"
