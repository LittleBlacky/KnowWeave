"""US2 retrieval, chat and citations

Revision ID: 0003_retrieval_chat_citations
Revises: 0002_us1_files_parsing_chunks
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_retrieval_chat_citations"
down_revision = "0002_us1_files_parsing_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_sessions_created_at", "chat_sessions", ["created_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("model_provider", sa.String(length=128), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("idx_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "retrieved_contexts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("retrieval_run_id", sa.Uuid(), nullable=False),
        sa.Column("chat_message_id", sa.Uuid(), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("result_type", sa.String(length=64), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(8, 4), nullable=True),
        sa.Column("retrieval_strategy", sa.String(length=64), nullable=False),
        sa.Column("retrieval_params", sa.JSON(), nullable=False),
        sa.Column("used_in_answer", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chat_message_id"], ["chat_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_retrieved_contexts_result_id", "retrieved_contexts", ["result_id"])
    op.create_index("idx_retrieved_contexts_result_type", "retrieved_contexts", ["result_type"])
    op.create_index("idx_retrieved_contexts_run_id", "retrieved_contexts", ["retrieval_run_id"])

    op.create_table(
        "citations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=True),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("knowledge_unit_id", sa.Uuid(), nullable=True),
        sa.Column("source_span_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("preview_text", sa.Text(), nullable=False),
        sa.Column("source_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"]),
        sa.ForeignKeyConstraint(["file_id"], ["knowledge_files.id"]),
        sa.ForeignKeyConstraint(["source_span_id"], ["source_spans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_citations_chunk_id", "citations", ["chunk_id"])
    op.create_index("idx_citations_file_id", "citations", ["file_id"])
    op.create_index("idx_citations_target", "citations", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_index("idx_citations_target", table_name="citations")
    op.drop_index("idx_citations_file_id", table_name="citations")
    op.drop_index("idx_citations_chunk_id", table_name="citations")
    op.drop_table("citations")

    op.drop_index("idx_retrieved_contexts_run_id", table_name="retrieved_contexts")
    op.drop_index("idx_retrieved_contexts_result_type", table_name="retrieved_contexts")
    op.drop_index("idx_retrieved_contexts_result_id", table_name="retrieved_contexts")
    op.drop_table("retrieved_contexts")

    op.drop_index("idx_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("idx_chat_messages_created_at", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("idx_chat_sessions_created_at", table_name="chat_sessions")
    op.drop_table("chat_sessions")
