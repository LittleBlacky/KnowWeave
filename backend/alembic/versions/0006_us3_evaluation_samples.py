"""US3 evaluation samples

Revision ID: 0006_us3_evaluation_samples
Revises: 0005_us3_feedback
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_us3_evaluation_samples"
down_revision = "0005_us3_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("expected_source_files", sa.JSON(), nullable=False),
        sa.Column("expected_source_chunks", sa.JSON(), nullable=False),
        sa.Column("created_from", sa.String(length=64), nullable=False),
        sa.Column("source_chat_message_id", sa.Uuid(), nullable=True),
        sa.Column("source_feedback_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("difficulty", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_evaluation_samples_created_from", "evaluation_samples", ["created_from"])
    op.create_index("idx_evaluation_samples_source_chat", "evaluation_samples", ["source_chat_message_id"])
    op.create_index("idx_evaluation_samples_source_feedback", "evaluation_samples", ["source_feedback_id"])
    op.create_index("idx_evaluation_samples_status", "evaluation_samples", ["status"])


def downgrade() -> None:
    op.drop_index("idx_evaluation_samples_status", table_name="evaluation_samples")
    op.drop_index("idx_evaluation_samples_source_feedback", table_name="evaluation_samples")
    op.drop_index("idx_evaluation_samples_source_chat", table_name="evaluation_samples")
    op.drop_index("idx_evaluation_samples_created_from", table_name="evaluation_samples")
    op.drop_table("evaluation_samples")
