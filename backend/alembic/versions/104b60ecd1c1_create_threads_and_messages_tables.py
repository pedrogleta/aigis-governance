"""Create Threads and Messages tables

Revision ID: 104b60ecd1c1
Revises: 54c53cc7d5b7
Create Date: 2025-08-23 19:31:32.725325

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "104b60ecd1c1"
down_revision: Union[str, Sequence[str], None] = "54c53cc7d5b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create threads and messages tables."""
    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("thread_id", sa.String(36), unique=True, index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "thread_id",
            sa.Integer(),
            sa.ForeignKey("threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender", sa.String(32), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop messages and threads tables."""
    op.drop_table("messages")
    op.drop_table("threads")
