"""US1 files, parsing, chunks and source spans

Revision ID: 0002_us1_files_parsing_chunks
Revises: 0001_database_baseline
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_us1_files_parsing_chunks"
down_revision = "0001_database_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("directory_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_files_created_at", "knowledge_files", ["created_at"])
    op.create_index("idx_files_file_type", "knowledge_files", ["file_type"])
    op.create_index("idx_files_sha256", "knowledge_files", ["sha256"])
    op.create_index("idx_files_status", "knowledge_files", ["status"])

    op.create_table(
        "parse_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("parse_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_parse_results_created_at", "parse_results", ["created_at"])
    op.create_index("idx_parse_results_file_id", "parse_results", ["file_id"])
    op.create_index("idx_parse_results_status", "parse_results", ["status"])

    op.create_table(
        "document_blocks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("parse_result_id", sa.Uuid(), nullable=False),
        sa.Column("parent_block_id", sa.Uuid(), nullable=True),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("normalized_content", sa.Text(), nullable=True),
        sa.Column("is_ignored", sa.Boolean(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("asset_ref", sa.Text(), nullable=True),
        sa.Column("context_before", sa.Text(), nullable=True),
        sa.Column("context_after", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.ForeignKeyConstraint(["parent_block_id"], ["document_blocks.id"]),
        sa.ForeignKeyConstraint(["parse_result_id"], ["parse_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_document_blocks_file_id", "document_blocks", ["file_id"])
    op.create_index("idx_document_blocks_order", "document_blocks", ["parse_result_id", "block_index"])
    op.create_index("idx_document_blocks_parse_result_id", "document_blocks", ["parse_result_id"])
    op.create_index("idx_document_blocks_type", "document_blocks", ["block_type"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("parse_result_id", sa.Uuid(), nullable=False),
        sa.Column("document_block_id", sa.Uuid(), nullable=True),
        sa.Column("parent_chunk_id", sa.Uuid(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_type", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("edited_content", sa.Text(), nullable=True),
        sa.Column("is_manually_edited", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("quality_signals", sa.JSON(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("is_searchable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_block_id"], ["document_blocks.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.ForeignKeyConstraint(["parent_chunk_id"], ["chunks.id"]),
        sa.ForeignKeyConstraint(["parse_result_id"], ["parse_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chunks_file_id", "chunks", ["file_id"])
    op.create_index("idx_chunks_is_searchable", "chunks", ["is_searchable"])
    op.create_index("idx_chunks_parent_id", "chunks", ["parent_chunk_id"])
    op.create_index("idx_chunks_status", "chunks", ["status"])
    op.create_index("idx_chunks_type", "chunks", ["chunk_type"])

    op.create_table(
        "source_spans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("document_block_id", sa.Uuid(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("column_start", sa.Integer(), nullable=True),
        sa.Column("column_end", sa.Integer(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("selector", sa.JSON(), nullable=True),
        sa.Column("preview_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"]),
        sa.ForeignKeyConstraint(["document_block_id"], ["document_blocks.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_source_spans_chunk_id", "source_spans", ["chunk_id"])
    op.create_index("idx_source_spans_document_block_id", "source_spans", ["document_block_id"])
    op.create_index("idx_source_spans_file_id", "source_spans", ["file_id"])


def downgrade() -> None:
    op.drop_index("idx_source_spans_file_id", table_name="source_spans")
    op.drop_index("idx_source_spans_document_block_id", table_name="source_spans")
    op.drop_index("idx_source_spans_chunk_id", table_name="source_spans")
    op.drop_table("source_spans")

    op.drop_index("idx_chunks_type", table_name="chunks")
    op.drop_index("idx_chunks_status", table_name="chunks")
    op.drop_index("idx_chunks_parent_id", table_name="chunks")
    op.drop_index("idx_chunks_is_searchable", table_name="chunks")
    op.drop_index("idx_chunks_file_id", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("idx_document_blocks_type", table_name="document_blocks")
    op.drop_index("idx_document_blocks_parse_result_id", table_name="document_blocks")
    op.drop_index("idx_document_blocks_order", table_name="document_blocks")
    op.drop_index("idx_document_blocks_file_id", table_name="document_blocks")
    op.drop_table("document_blocks")

    op.drop_index("idx_parse_results_status", table_name="parse_results")
    op.drop_index("idx_parse_results_file_id", table_name="parse_results")
    op.drop_index("idx_parse_results_created_at", table_name="parse_results")
    op.drop_table("parse_results")

    op.drop_index("idx_files_status", table_name="knowledge_files")
    op.drop_index("idx_files_sha256", table_name="knowledge_files")
    op.drop_index("idx_files_file_type", table_name="knowledge_files")
    op.drop_index("idx_files_created_at", table_name="knowledge_files")
    op.drop_table("knowledge_files")
