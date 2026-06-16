from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter()


class UpdateConfigRequest(BaseModel):
    qwen_chat_model: str | None = None
    qwen_generation_model: str | None = None
    qwen_embedding_model: str | None = None
    qwen_rerank_model: str | None = None
    qwen_base_url: str | None = None


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/system/config")
def system_config() -> dict:
    settings = get_settings()
    return _build_config_response(settings)


@router.patch("/system/config")
def update_system_config(request: UpdateConfigRequest) -> dict:
    settings = get_settings()
    overrides = {k: v for k, v in request.model_dump().items() if v is not None}
    changed = settings.apply_runtime_overrides(**overrides)
    return {
        "updated": list(changed.keys()),
        "changed": changed,
        "config": _build_config_response(settings),
    }


def _build_config_response(settings) -> dict:
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "provider": {
            "type": "qwen" if settings.qwen_enabled else "fake",
            "qwen_enabled": settings.qwen_enabled,
            "base_url": settings.qwen_base_url,
            "timeout_seconds": settings.qwen_timeout_seconds,
        },
        "models": {
            "chat": settings.qwen_chat_model,
            "generation": settings.qwen_generation_model,
            "embedding": settings.qwen_embedding_model,
            "rerank": settings.qwen_rerank_model,
        },
    }

