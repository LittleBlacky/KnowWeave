from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel

# Fields that can be updated at runtime without restart
_RUNTIME_MUTABLE_FIELDS = frozenset({
    "qwen_api_key",
    "qwen_chat_model",
    "qwen_generation_model",
    "qwen_embedding_model",
    "qwen_rerank_model",
    "qwen_base_url",
})


class Settings(BaseModel):
    app_name: str = "KnowWeave API"
    service_name: str = "knowweave-backend"
    version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://knowweave:knowweave@localhost:5432/knowweave"
    file_storage_root: str = "./data/files"
    max_upload_mb: int = 50
    qwen_api_key: str | None = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_chat_model: str = "qwen-plus"
    qwen_generation_model: str = "qwen-plus"
    qwen_embedding_model: str = "text-embedding-v3"
    qwen_rerank_model: str = "gte-rerank"
    qwen_timeout_seconds: float = 60.0
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4317",
        "http://127.0.0.1:4317",
    )

    @property
    def qwen_enabled(self) -> bool:
        return bool(self.qwen_api_key)

    def apply_runtime_overrides(self, **overrides: str | int) -> dict[str, object]:
        """Apply runtime-configurable overrides. Returns which fields changed."""
        changed: dict[str, object] = {}
        for key, value in overrides.items():
            if key not in _RUNTIME_MUTABLE_FIELDS:
                continue
            current = getattr(self, key, None)
            if value is not None and str(current) != str(value):
                # coerce types — max_upload_mb is int, model names are str
                if key == "max_upload_mb":
                    setattr(self, key, int(value))
                else:
                    setattr(self, key, str(value))
                changed[key] = getattr(self, key)
        return changed


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("KNOWWEAVE_APP_NAME", Settings.model_fields["app_name"].default),
        service_name=os.getenv(
            "KNOWWEAVE_SERVICE_NAME",
            Settings.model_fields["service_name"].default,
        ),
        version=os.getenv("KNOWWEAVE_VERSION", Settings.model_fields["version"].default),
        environment=os.getenv(
            "KNOWWEAVE_ENVIRONMENT",
            os.getenv("APP_ENV", Settings.model_fields["environment"].default),
        ),
        database_url=os.getenv(
            "DATABASE_URL",
            Settings.model_fields["database_url"].default,
        ),
        file_storage_root=os.getenv(
            "FILE_STORAGE_ROOT",
            Settings.model_fields["file_storage_root"].default,
        ),
        max_upload_mb=int(
            os.getenv("MAX_UPLOAD_MB", str(Settings.model_fields["max_upload_mb"].default))
        ),
        qwen_api_key=os.getenv("QWEN_API_KEY"),
        qwen_base_url=os.getenv(
            "QWEN_BASE_URL",
            Settings.model_fields["qwen_base_url"].default,
        ),
        qwen_chat_model=os.getenv(
            "QWEN_CHAT_MODEL",
            Settings.model_fields["qwen_chat_model"].default,
        ),
        qwen_generation_model=os.getenv(
            "QWEN_GENERATION_MODEL",
            Settings.model_fields["qwen_generation_model"].default,
        ),
        qwen_embedding_model=os.getenv(
            "QWEN_EMBEDDING_MODEL",
            Settings.model_fields["qwen_embedding_model"].default,
        ),
        qwen_rerank_model=os.getenv(
            "QWEN_RERANK_MODEL",
            Settings.model_fields["qwen_rerank_model"].default,
        ),
        qwen_timeout_seconds=float(
            os.getenv(
                "QWEN_TIMEOUT_SECONDS",
                str(Settings.model_fields["qwen_timeout_seconds"].default),
            )
        ),
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                ",".join(Settings.model_fields["cors_origins"].default),
            ).split(",")
            if origin.strip()
        ),
    )
