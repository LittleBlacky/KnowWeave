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
    engine = make_engine(f"sqlite:///{tmp_path / 'evaluation-api.db'}")
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


def test_evaluation_candidates_api_creates_and_lists_manual_candidate(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evaluation-samples",
        json={
            "question": "Who approves short leave requests?",
            "expected_answer": "The direct manager approves short leave requests.",
            "expected_source_files": [],
            "expected_source_chunks": [],
            "created_from": "manual",
            "status": "draft",
            "difficulty": "easy",
            "metadata": {"dataset_key": "mvp_smoke"},
        },
    )

    assert response.status_code == 201
    created = response.json()["data"]
    assert created["id"]
    assert created["status"] == "draft"
    assert created["created_from"] == "manual"
    assert created["metadata_"]["dataset_key"] == "mvp_smoke"

    list_response = client.get("/api/v1/evaluation-samples?status=draft")

    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == created["id"]


def test_evaluation_candidates_api_creates_candidate_from_feedback(client: TestClient) -> None:
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
    chunk_id = build_response.json()["data"]["items"][0]["id"]
    feedback_id = client.post(
        "/api/v1/feedback",
        json={
            "target_type": "chunk",
            "target_id": chunk_id,
            "feedback_type": "chunk_low_quality",
            "comment": "Chunk should preserve the approver line.",
            "metadata": {"expected_source_hint": "Manager approval section"},
        },
    ).json()["data"]["id"]

    response = client.post(f"/api/v1/feedback/{feedback_id}/to-evaluation-sample")

    assert response.status_code == 201
    sample = response.json()["data"]
    assert sample["created_from"] == "feedback"
    assert sample["source_feedback_id"] == feedback_id
    assert sample["expected_source_chunks"] == [chunk_id]
    assert sample["metadata_"]["feedback_snapshot"]["comment"] == "Chunk should preserve the approver line."
