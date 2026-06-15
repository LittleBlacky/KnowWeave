"""P1: wiki_revisions table for version history.

Revision ID: 0009_p1_wiki_revisions
Revises: 0008_p1_chunk_embedding
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_p1_wiki_revisions"
down_revision: str | None = "0008_p1_chunk_embedding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("wiki_page_id", sa.Uuid(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("change_summary", sa.String(1024), nullable=False),
        sa.Column("edit_source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["wiki_page_id"], ["wiki_pages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wiki_revisions_page", "wiki_revisions", ["wiki_page_id", "revision_number"])


def downgrade() -> None:
    op.drop_index("idx_wiki_revisions_page", table_name="wiki_revisions")
    op.drop_table("wiki_revisions")
