"""US3 wiki pages

Revision ID: 0004_us3_wiki_pages
Revises: 0003_retrieval_chat_citations
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_us3_wiki_pages"
down_revision = "0003_retrieval_chat_citations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wiki_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("wiki_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=True),
        sa.Column("generation_prompt_version", sa.String(length=64), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_file_id"], ["knowledge_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wiki_pages_source_file_id", "wiki_pages", ["source_file_id"])
    op.create_index("idx_wiki_pages_status", "wiki_pages", ["status"])
    op.create_index("idx_wiki_pages_type", "wiki_pages", ["wiki_type"])


def downgrade() -> None:
    op.drop_index("idx_wiki_pages_type", table_name="wiki_pages")
    op.drop_index("idx_wiki_pages_status", table_name="wiki_pages")
    op.drop_index("idx_wiki_pages_source_file_id", table_name="wiki_pages")
    op.drop_table("wiki_pages")
