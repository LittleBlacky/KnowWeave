"""US3 knowledge units and tags

Revision ID: 0007_us3_knowledge_units_tags
Revises: 0006_us3_evaluation_samples
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_us3_knowledge_units_tags"
down_revision = "0006_us3_evaluation_samples"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_units",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("unit_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("trust_level", sa.Integer(), nullable=True),
        sa.Column("applicable_scope", sa.Text(), nullable=True),
        sa.Column("created_from", sa.String(length=64), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_knowledge_units_created_from", "knowledge_units", ["created_from"])
    op.create_index("idx_knowledge_units_status", "knowledge_units", ["status"])
    op.create_index("idx_knowledge_units_type", "knowledge_units", ["unit_type"])

    op.create_table(
        "knowledge_unit_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_unit_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=True),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("source_span_id", sa.Uuid(), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("source_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.ForeignKeyConstraint(["knowledge_unit_id"], ["knowledge_units.id"]),
        sa.ForeignKeyConstraint(["source_span_id"], ["source_spans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ku_sources_chunk_id", "knowledge_unit_sources", ["chunk_id"])
    op.create_index("idx_ku_sources_file_id", "knowledge_unit_sources", ["file_id"])
    op.create_index("idx_ku_sources_unit_id", "knowledge_unit_sources", ["knowledge_unit_id"])

    op.create_table(
        "wiki_page_units",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("wiki_page_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_unit_id", sa.Uuid(), nullable=False),
        sa.Column("section_anchor", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_unit_id"], ["knowledge_units.id"]),
        sa.ForeignKeyConstraint(["wiki_page_id"], ["wiki_pages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wiki_page_units_unit_id", "wiki_page_units", ["knowledge_unit_id"])
    op.create_index("idx_wiki_page_units_wiki_id", "wiki_page_units", ["wiki_page_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )
    op.create_index("idx_tags_name", "tags", ["name"])

    op.create_table(
        "tag_bindings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tag_id", "target_type", "target_id", name="uq_tag_bindings_target"),
    )
    op.create_index("idx_tag_bindings_tag_id", "tag_bindings", ["tag_id"])
    op.create_index("idx_tag_bindings_target", "tag_bindings", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_index("idx_tag_bindings_target", table_name="tag_bindings")
    op.drop_index("idx_tag_bindings_tag_id", table_name="tag_bindings")
    op.drop_table("tag_bindings")
    op.drop_index("idx_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_index("idx_wiki_page_units_wiki_id", table_name="wiki_page_units")
    op.drop_index("idx_wiki_page_units_unit_id", table_name="wiki_page_units")
    op.drop_table("wiki_page_units")
    op.drop_index("idx_ku_sources_unit_id", table_name="knowledge_unit_sources")
    op.drop_index("idx_ku_sources_file_id", table_name="knowledge_unit_sources")
    op.drop_index("idx_ku_sources_chunk_id", table_name="knowledge_unit_sources")
    op.drop_table("knowledge_unit_sources")
    op.drop_index("idx_knowledge_units_type", table_name="knowledge_units")
    op.drop_index("idx_knowledge_units_status", table_name="knowledge_units")
    op.drop_index("idx_knowledge_units_created_from", table_name="knowledge_units")
    op.drop_table("knowledge_units")
