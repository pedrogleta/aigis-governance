"""Create User Connections table

Revision ID: 6b4606763e8e
Revises: 104b60ecd1c1
Create Date: 2025-08-23 21:17:04.070489

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6b4606763e8e"
down_revision: Union[str, Sequence[str], None] = "104b60ecd1c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create user_connections table."""
    op.create_table(
        "user_connections",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("db_type", sa.String(length=32), nullable=False),
        sa.Column("encrypted_password", sa.LargeBinary(), nullable=True),
        sa.Column("iv", sa.LargeBinary(), nullable=True),
        sa.Column("host", sa.String(length=512), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("database_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_user_connection_name_per_user"),
    )


def downgrade() -> None:
    """Downgrade schema: drop user_connections table."""
    op.drop_table("user_connections")
