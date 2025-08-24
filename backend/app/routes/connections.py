from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_active_user
from core.database import get_postgres_db
from crud.connection import user_connection_crud
from models.user import User
from models.user_connection import UserConnection
from schemas.connection import (
    UserConnectionCreate,
    UserConnectionResponse,
    UserConnectionUpdate,
)
from core.crypto import decrypt_secret
from core.config import settings
from core.database import db_manager


router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("/", response_model=List[UserConnectionResponse])
async def list_connections(
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    return [c for c in user_connection_crud.list_user_connections(db, current_user.id)]


@router.post(
    "/", response_model=UserConnectionResponse, status_code=status.HTTP_201_CREATED
)
async def create_connection(
    payload: UserConnectionCreate,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    record = user_connection_crud.create_user_connection(db, current_user.id, payload)
    return record


@router.get("/{connection_id}", response_model=UserConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    record = user_connection_crud.get_user_connection(
        db, current_user.id, connection_id
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )
    return record


@router.put("/{connection_id}", response_model=UserConnectionResponse)
async def update_connection(
    connection_id: int,
    payload: UserConnectionUpdate,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    record = user_connection_crud.update_user_connection(
        db, current_user.id, connection_id, payload
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )
    return record


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    ok = user_connection_crud.delete_user_connection(db, current_user.id, connection_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )
    return None


@router.post("/{connection_id}/test", status_code=status.HTTP_200_OK)
async def test_connection(
    connection_id: int,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    record: UserConnection | None = user_connection_crud.get_user_connection(
        db, current_user.id, connection_id
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )

    password = None
    if record.encrypted_password and record.iv:
        try:
            password = decrypt_secret(
                record.encrypted_password, record.iv, settings.master_encryption_key
            )
        except Exception:
            raise HTTPException(
                status_code=400, detail="Failed to decrypt stored password"
            )

    try:
        engine = db_manager.get_user_connection_engine(
            user_id=current_user.id,
            connection_id=record.id,
            db_type=record.db_type,
            host=record.host or "",
            port=record.port,
            username=record.username,
            password=password,
            database_name=record.database_name,
        )
        with engine.connect() as conn:
            list(conn.execute("SELECT 1"))
        return {"detail": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
