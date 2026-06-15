"""P1: add chunk embedding column for semantic search.

Revision ID: 0008_p1_chunk_embedding
Revises: 0007_us3_knowledge_units_tags
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_p1_chunk_embedding"
down_revision: str | None = "0007_us3_knowledge_units_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chunks", sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("chunks", "embedding")
