from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class ExampleModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "example_models"

    name: Mapped[str] = mapped_column()


def _default_value(column_name: str):
    default = ExampleModel.__table__.c[column_name].default
    assert default is not None
    try:
        return default.arg()
    except TypeError:
        return default.arg(None)


def test_utcnow_returns_timezone_aware_datetime() -> None:
    value = utcnow()

    assert isinstance(value, datetime)
    assert value.tzinfo is timezone.utc


def test_uuid_primary_key_mixin_provides_uuid_default() -> None:
    column = ExampleModel.__table__.c.id

    assert column.primary_key is True
    assert isinstance(_default_value("id"), UUID)


def test_timestamp_mixin_uses_timezone_aware_defaults() -> None:
    created_at = _default_value("created_at")
    updated_at = _default_value("updated_at")

    assert created_at.tzinfo is timezone.utc
    assert updated_at.tzinfo is timezone.utc
