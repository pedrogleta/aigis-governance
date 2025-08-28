"""
UserConnection model to store user-provided database connection details.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    LargeBinary,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship  # type: ignore
from sqlalchemy.sql import func

from core.database import Base


class UserConnection(Base):
    __tablename__ = "user_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_connection_name_per_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    db_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Secret storage
    encrypted_password: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    iv: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    # Connection params (for SQLite, host can be a file path)
    host: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    database_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # When this connection represents a user-imported CSV table in their schema,
    # this stores the table name created for that CSV.
    table_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User")

    def to_safe_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "database_name": self.database_name,
            "table_name": self.table_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
