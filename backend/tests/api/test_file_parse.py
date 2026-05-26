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
    engine = make_engine(f"sqlite:///{tmp_path / 'file-parse-api.db'}")
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


def test_parse_markdown_file_and_list_document_blocks(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/files/upload",
        files={"file": ("policy.md", b"# Policy\n\nParagraph body", "text/markdown")},
    )
    file_id = upload_response.json()["data"]["id"]

    parse_response = client.post(f"/api/v1/files/{file_id}/parse")
    blocks_response = client.get(f"/api/v1/files/{file_id}/blocks")

    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["data"]["status"] == "parse_succeeded"
    assert parse_payload["data"]["parser_name"] == "markdown_parser"
    assert parse_payload["data"]["block_count"] == 2
    assert parse_payload["error"] is None
    assert parse_payload["request_id"]

    assert blocks_response.status_code == 200
    blocks_payload = blocks_response.json()
    assert [block["block_type"] for block in blocks_payload["data"]["items"]] == [
        "heading",
        "paragraph",
    ]
    assert blocks_payload["data"]["items"][0]["raw_content"] == "# Policy"
    assert blocks_payload["data"]["items"][0]["line_start"] == 1
    assert blocks_payload["data"]["items"][1]["raw_content"] == "Paragraph body"


def test_parse_missing_file_returns_standard_error(client: TestClient) -> None:
    response = client.post("/api/v1/files/00000000-0000-0000-0000-000000000000/parse")

    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "FILE_NOT_FOUND"
    assert payload["request_id"]
