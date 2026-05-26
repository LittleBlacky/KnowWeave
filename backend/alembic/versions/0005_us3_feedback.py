"""US3 feedback

Revision ID: 0005_us3_feedback
Revises: 0004_us3_wiki_pages
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_us3_feedback"
down_revision = "0004_us3_wiki_pages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_feedback_target", "feedback", ["target_type", "target_id"])
    op.create_index("idx_feedback_type", "feedback", ["feedback_type"])
    op.create_index("idx_feedback_status", "feedback", ["status"])


def downgrade() -> None:
    op.drop_index("idx_feedback_status", table_name="feedback")
    op.drop_index("idx_feedback_type", table_name="feedback")
    op.drop_index("idx_feedback_target", table_name="feedback")
    op.drop_table("feedback")
