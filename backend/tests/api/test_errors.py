from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.main import create_app


def test_app_error_returns_standard_error_envelope() -> None:
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    def boom() -> None:
        raise AppError(
            code="FILE_TYPE_NOT_SUPPORTED",
            message="Only txt, md, pdf and docx files are supported in MVP.",
            status_code=415,
            details={"allowed": ["txt", "md", "pdf", "docx"]},
        )

    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/boom")

    assert response.status_code == 415
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"] == {
        "code": "FILE_TYPE_NOT_SUPPORTED",
        "message": "Only txt, md, pdf and docx files are supported in MVP.",
        "details": {"allowed": ["txt", "md", "pdf", "docx"]},
    }
    assert payload["request_id"]


def test_http_error_returns_standard_error_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["message"] == "Not Found"
    assert payload["error"]["details"] == {}
    assert payload["request_id"]
