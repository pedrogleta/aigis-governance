"""Create table_name column in user_connections

Revision ID: 8386b225d990
Revises: 6b4606763e8e
Create Date: 2025-08-28 19:13:00.909183

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8386b225d990"
down_revision: Union[str, Sequence[str], None] = "6b4606763e8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user_connections",
        sa.Column("table_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_connections", "table_name")
