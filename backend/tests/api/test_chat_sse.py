from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db, make_engine
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'chat-sse-api.db'}")
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


def _seed_chunk(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
    )
    file_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/files/{file_id}/parse")
    client.post(f"/api/v1/files/{file_id}/chunks/build")


def _events(response_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for raw_event in response_text.strip().split("\n\n"):
        event_name = ""
        data = {}
        for line in raw_event.splitlines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ")
            if line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        events.append((event_name, data))
    return events


def test_chat_message_streams_normalized_sse_and_persists_citations(client: TestClient) -> None:
    _seed_chunk(client)
    session_response = client.post("/api/v1/chat/sessions", json={"title": "Policy Q&A"})
    session_id = session_response.json()["data"]["id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"question": "approval", "top_k": 1},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(response.text)
    assert [event_name for event_name, _ in events] == [
        "start",
        "retrieval",
        "delta",
        "delta",
        "delta",
        "delta",
        "citations",
        "done",
    ]
    assert events[0][1]["message_id"]
    assert events[0][1]["retrieval_run_id"] == events[1][1]["retrieval_run_id"]
    assert events[1][1]["results"][0]["result_type"] == "chunk"
    assert "".join(data["delta"] for name, data in events if name == "delta").startswith(
        "Fake answer: approval"
    )
    assert events[-2][1]["citations"][0]["key"] == "S1"
    assert events[-1][1]["status"] == "completed"

    citations_response = client.get(f"/api/v1/chat/messages/{events[0][1]['message_id']}/citations")
    assert citations_response.status_code == 200
    assert citations_response.json()["data"]["items"][0]["label"] == "S1"


def test_chat_message_without_retrieval_results_returns_done_without_citations(client: TestClient) -> None:
    session_response = client.post("/api/v1/chat/sessions", json={"title": "Empty Q&A"})
    session_id = session_response.json()["data"]["id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"question": "missing policy", "top_k": 1},
    )

    assert response.status_code == 200
    events = _events(response.text)
    assert [name for name, _ in events if name in {"citations", "done"}] == ["citations", "done"]
    assert events[-2][1]["citations"] == []
    assert events[-1][1]["status"] == "completed"
