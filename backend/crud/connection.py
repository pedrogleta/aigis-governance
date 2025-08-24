from typing import List, Optional
from sqlalchemy.orm import Session

from models.user_connection import UserConnection
from schemas.connection import UserConnectionCreate
from core.config import settings
from core.crypto import encrypt_secret


class UserConnectionCRUD:
    @staticmethod
    def list_user_connections(db: Session, user_id: int) -> List[UserConnection]:
        return (
            db.query(UserConnection)
            .filter(UserConnection.user_id == user_id)
            .order_by(UserConnection.created_at.desc())
            .all()
        )

    @staticmethod
    def get_user_connection(
        db: Session, user_id: int, connection_id: int
    ) -> Optional[UserConnection]:
        return (
            db.query(UserConnection)
            .filter(
                UserConnection.user_id == user_id, UserConnection.id == connection_id
            )
            .first()
        )

    @staticmethod
    def create_user_connection(
        db: Session, user_id: int, payload: UserConnectionCreate
    ) -> UserConnection:
        iv = None
        encrypted_password = None
        if payload.password:
            iv, encrypted_password = encrypt_secret(
                payload.password, settings.master_encryption_key
            )

        record = UserConnection(
            user_id=user_id,
            name=payload.name,
            db_type=payload.db_type,
            host=payload.host,
            port=payload.port,
            username=payload.username,
            database_name=payload.database_name,
            encrypted_password=encrypted_password,
            iv=iv,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


user_connection_crud = UserConnectionCRUD()
