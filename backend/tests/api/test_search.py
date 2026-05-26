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
    engine = make_engine(f"sqlite:///{tmp_path / 'search-api.db'}")
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


def _seed_chunk(client: TestClient) -> tuple[str, str]:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
    )
    file_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/files/{file_id}/parse")
    chunks_response = client.post(f"/api/v1/files/{file_id}/chunks/build")
    return file_id, chunks_response.json()["data"]["items"][0]["id"]


def test_search_api_returns_retrieval_run_and_chunk_results(client: TestClient) -> None:
    _seed_chunk(client)

    response = client.post("/api/v1/search", json={"query": "approval", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["query"] == "approval"
    assert payload["data"]["strategy"] == "keyword"
    assert payload["data"]["retrieval_run_id"]
    assert payload["data"]["results"][0]["result_type"] == "chunk"
    assert payload["data"]["results"][0]["rank"] == 1
    assert payload["data"]["results"][0]["source"]["source_available"] is True


def test_search_api_returns_requested_target_types(client: TestClient) -> None:
    file_id, chunk_id = _seed_chunk(client)
    unit_response = client.post(
        "/api/v1/knowledge-units",
        json={
            "title": "Leave approval rule",
            "unit_type": "rule",
            "content": "Leave requests need approval.",
            "summary": "Approval rule for leave.",
            "status": "pending_review",
            "source_chunk_ids": [chunk_id],
        },
    )
    wiki_response = client.post(f"/api/v1/files/{file_id}/wiki")

    response = client.post(
        "/api/v1/search",
        json={
            "query": "approval",
            "target_types": ["file", "chunk", "knowledge_unit", "wiki_page"],
            "top_k": 10,
        },
    )

    assert response.status_code == 200
    results = response.json()["data"]["results"]
    assert {item["result_type"] for item in results} == {
        "file",
        "chunk",
        "knowledge_unit",
        "wiki_page",
    }
    result_ids = {item["result_id"] for item in results}
    assert file_id in result_ids
    assert chunk_id in result_ids
    assert unit_response.json()["data"]["id"] in result_ids
    assert wiki_response.json()["data"]["id"] in result_ids


def test_search_run_inspection_returns_persisted_contexts(client: TestClient) -> None:
    _seed_chunk(client)
    search_response = client.post("/api/v1/search", json={"query": "approval"})
    run_id = search_response.json()["data"]["retrieval_run_id"]

    response = client.get(f"/api/v1/search/runs/{run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["retrieval_run_id"] == run_id
    assert payload["data"]["query"] == "approval"
    assert payload["data"]["results"][0]["result_type"] == "chunk"
