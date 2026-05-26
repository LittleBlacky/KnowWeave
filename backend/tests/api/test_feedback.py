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
    engine = make_engine(f"sqlite:///{tmp_path / 'feedback-api.db'}")
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


def test_feedback_api_saves_unified_feedback_payload(client: TestClient) -> None:
    chunk_id = _seed_chunk(client)

    response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "chunk",
            "target_id": chunk_id,
            "feedback_type": "chunk_low_quality",
            "comment": "Chunk should be split by approval rule.",
            "metadata": {"source": "component-test"},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["id"]
    assert payload["data"]["target_type"] == "chunk"
    assert payload["data"]["target_id"] == chunk_id
    assert payload["data"]["feedback_type"] == "chunk_low_quality"
    assert payload["data"]["status"] == "open"
    assert payload["data"]["metadata_"]["source"] == "component-test"


def test_feedback_api_lists_feedback_and_accepts_knowledge_unit_target(client: TestClient) -> None:
    chunk_id = _seed_chunk(client)
    unit_response = client.post(
        "/api/v1/knowledge-units",
        json={
            "title": "Leave approval rule",
            "content": "Leave requests require manager approval.",
            "status": "pending_review",
            "source_chunk_ids": [chunk_id],
        },
    )
    unit_id = unit_response.json()["data"]["id"]

    create_response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "knowledge_unit",
            "target_id": unit_id,
            "feedback_type": "retrieval_helpful",
        },
    )
    list_response = client.get("/api/v1/feedback", params={"target_type": "knowledge_unit"})

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["target_id"] == unit_id


def test_feedback_api_returns_clear_error_for_missing_target(client: TestClient) -> None:
    response = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "chunk",
            "target_id": str(uuid4()),
            "feedback_type": "chunk_low_quality",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FEEDBACK_TARGET_NOT_FOUND"
