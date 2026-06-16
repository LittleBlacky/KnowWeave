from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.config import ConfigOverride
from app.schemas.common import ApiResponse

router = APIRouter()  # system config + health


class UpdateConfigRequest(BaseModel):
    qwen_api_key: str | None = None
    qwen_chat_model: str | None = None
    qwen_generation_model: str | None = None
    qwen_embedding_model: str | None = None
    qwen_rerank_model: str | None = None
    qwen_base_url: str | None = None


def _load_db_overrides(db: Session) -> dict[str, str]:
    """Load config overrides from database."""
    rows = db.query(ConfigOverride).all()
    return {row.key: row.value for row in rows if row.value is not None}


def _save_db_override(db: Session, key: str, value: str) -> None:
    """Upsert a config override into the database."""
    from sqlalchemy import select

    existing = db.scalar(select(ConfigOverride).where(ConfigOverride.key == key))
    if existing:
        existing.value = value
    else:
        db.add(ConfigOverride(key=key, value=value))
    db.commit()


def _remove_db_override(db: Session, key: str) -> None:
    """Remove a config override from the database."""
    from sqlalchemy import select

    existing = db.scalar(select(ConfigOverride).where(ConfigOverride.key == key))
    if existing:
        db.delete(existing)
        db.commit()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/system/config")
def system_config(db: Session = Depends(get_db)) -> ApiResponse[dict]:
    settings = get_settings()
    overrides = _load_db_overrides(db)
    return ApiResponse(
        data=_build_config_response(settings, overrides),
        error=None,
        request_id="req_system_config",
    )


@router.patch("/system/config")
def update_system_config(
    request: UpdateConfigRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    settings = get_settings()
    overrides = {k: v for k, v in request.model_dump().items() if v is not None}
    changed = settings.apply_runtime_overrides(**overrides)

    # Persist to DB
    for key, value in overrides.items():
        if value is not None:
            _save_db_override(db, key, value)
        else:
            _remove_db_override(db, key)

    db_overrides = _load_db_overrides(db)
    return ApiResponse(
        data={
            "updated": list(changed.keys()),
            "changed": changed,
            "config": _build_config_response(settings, db_overrides),
        },
        error=None,
        request_id="req_system_config_update",
    )


def _build_config_response(settings, db_overrides: dict | None = None) -> dict:
    ov = db_overrides or {}
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "provider": {
            "type": "qwen" if settings.qwen_enabled else "fake",
            "qwen_enabled": settings.qwen_enabled,
            "base_url": ov.get("qwen_base_url", settings.qwen_base_url),
            "timeout_seconds": settings.qwen_timeout_seconds,
        },
        "models": {
            "chat": ov.get("qwen_chat_model", settings.qwen_chat_model),
            "generation": ov.get("qwen_generation_model", settings.qwen_generation_model),
            "embedding": ov.get("qwen_embedding_model", settings.qwen_embedding_model),
            "rerank": ov.get("qwen_rerank_model", settings.qwen_rerank_model),
        },
    }

