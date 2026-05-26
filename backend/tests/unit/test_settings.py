from app.core.config import get_settings


def test_default_settings_load_without_qwen_api_key(monkeypatch) -> None:
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.app_name == "KnowWeave API"
    assert settings.service_name == "knowweave-backend"
    assert settings.version == "0.1.0"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.max_upload_mb == 50
    assert settings.qwen_api_key is None
    assert settings.qwen_enabled is False


def test_settings_can_read_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("KNOWWEAVE_SERVICE_NAME", "knowweave-test")
    monkeypatch.setenv("KNOWWEAVE_VERSION", "0.1.1-test")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.service_name == "knowweave-test"
    assert settings.version == "0.1.1-test"
