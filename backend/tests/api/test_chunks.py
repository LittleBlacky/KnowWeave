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
    engine = make_engine(f"sqlite:///{tmp_path / 'chunks-api.db'}")
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


def test_build_and_list_file_chunks(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nLeave requests need approval.", "text/markdown")},
    )
    file_id = upload_response.json()["data"]["id"]
    client.post(f"/api/v1/files/{file_id}/parse")

    build_response = client.post(f"/api/v1/files/{file_id}/chunks/build")
    list_response = client.get(f"/api/v1/files/{file_id}/chunks")

    assert build_response.status_code == 200
    build_payload = build_response.json()
    assert build_payload["data"]["total"] == 1
    assert build_payload["data"]["items"][0]["raw_content"] == "# Policy\n\nLeave requests need approval."
    assert build_payload["data"]["items"][0]["source_spans"][0]["line_start"] == 1
    assert build_payload["data"]["items"][0]["source_spans"][0]["line_end"] == 3

    assert list_response.status_code == 200
    assert list_response.json()["data"] == build_payload["data"]


def test_build_chunks_requires_parsed_file(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("notes.txt", b"Unparsed notes", "text/plain")},
    )
    file_id = upload_response.json()["data"]["id"]

    response = client.post(f"/api/v1/files/{file_id}/chunks/build")

    assert response.status_code == 400
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "CHUNKING_REQUIRES_PARSE"
