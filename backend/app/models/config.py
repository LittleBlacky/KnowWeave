"""Runtime configuration overrides persisted to database."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ConfigOverride(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "config_overrides"

    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("key", name="uq_config_overrides_key"),
    )
