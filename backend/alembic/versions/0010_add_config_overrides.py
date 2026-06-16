"""add config_overrides table

Revision ID: 0010
Revises: 0009_p1_wiki_revisions
Create Date: 2026-06-16 15:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009_p1_wiki_revisions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_overrides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(128), nullable=False, index=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_config_overrides_key"),
    )


def downgrade() -> None:
    op.drop_table("config_overrides")
