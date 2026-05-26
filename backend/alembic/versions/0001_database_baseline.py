"""database baseline

Revision ID: 0001_database_baseline
Revises:
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op

revision = "0001_database_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    pass
