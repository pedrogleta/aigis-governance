"""add selected_model to threads

Revision ID: 7f0a9b2c1e3a
Revises: 8386b225d990
Create Date: 2025-08-29
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f0a9b2c1e3a"
down_revision = "8386b225d990"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "threads", sa.Column("selected_model", sa.String(length=64), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("threads", "selected_model")
