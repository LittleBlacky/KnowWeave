from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_service_status() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "knowweave-backend",
        "version": "0.1.0",
    }


def test_local_frontend_origin_is_allowed_by_cors() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/files",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
