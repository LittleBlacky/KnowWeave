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
    assert settings.qwen_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.qwen_chat_model == "qwen-plus"
    assert settings.qwen_generation_model == "qwen-plus"
    assert settings.qwen_timeout_seconds == 60.0
    assert "http://localhost:3000" in settings.cors_origins


def test_settings_can_read_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("KNOWWEAVE_SERVICE_NAME", "knowweave-test")
    monkeypatch.setenv("KNOWWEAVE_VERSION", "0.1.1-test")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.service_name == "knowweave-test"
    assert settings.version == "0.1.1-test"


def test_settings_can_read_cors_origin_overrides(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, http://example.test")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.cors_origins == ("http://localhost:3000", "http://example.test")


def test_settings_can_read_qwen_environment(monkeypatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("QWEN_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("QWEN_CHAT_MODEL", "qwen-test")
    monkeypatch.setenv("QWEN_GENERATION_MODEL", "qwen-generation-test")
    monkeypatch.setenv("QWEN_TIMEOUT_SECONDS", "12.5")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.qwen_enabled is True
    assert settings.qwen_api_key == "test-key"
    assert settings.qwen_base_url == "https://example.test/v1"
    assert settings.qwen_chat_model == "qwen-test"
    assert settings.qwen_generation_model == "qwen-generation-test"
    assert settings.qwen_timeout_seconds == 12.5
