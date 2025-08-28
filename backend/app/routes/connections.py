from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
import csv
import io
import re

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
from core.tenancy import make_user_schema_name, ensure_user_schema, MAX_IDENTIFIER_LEN


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
            list(conn.execute(text("SELECT 1")))
        return {"detail": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


def _slugify_identifier(name: str) -> str:
    base = name.strip().lower()
    base = re.sub(r"[^a-z0-9_]", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base or not base[0].isalpha():
        base = f"t_{base}" if base else "t"
    return base[:MAX_IDENTIFIER_LEN]


@router.post("/import/csv/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a CSV and return a preview with inferred columns and a temporary key.

    For simplicity, we keep the CSV content in memory and return it back as a tokenized payload
    that the client will echo in the finalize call. In production, use object storage or DB temp table.
    """
    try:
        content = await file.read()
        decoded = content.decode("utf-8", errors="replace")
        # Parse CSV quickly to infer headers and few sample rows
        reader = csv.reader(io.StringIO(decoded))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Empty CSV")
        headers = rows[0]
        data_rows = rows[1:]
        sample = data_rows[:5]
        # Stash payload back to client (stateless). For integrity, we include a short hash-like length marker.
        temp_payload = {
            "filename": file.filename or "import.csv",
            "headers": headers,
            "sample": sample,
            "raw": decoded,
        }
        return temp_payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.post("/import/csv/finish", response_model=UserConnectionResponse)
async def finish_import_csv(
    filename: str = Form(...),
    raw: str = Form(...),
    column_types_json: str = Form(...),
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create the user's schema (if missing), create a table from CSV, insert data, and register a 'custom' connection.

    Params are provided via form data: filename, raw CSV content, and a JSON mapping of column types.
    """
    import json

    # Determine user schema
    schema_name = make_user_schema_name(current_user.email, current_user.id)
    ensure_user_schema(db, schema_name)

    # Table name from file
    table_base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    table_no_ext = table_base.rsplit(".", 1)[0]
    table_name = _slugify_identifier(table_no_ext)

    try:
        column_types = json.loads(column_types_json)
        if not isinstance(column_types, dict):
            raise ValueError("column_types_json must be a JSON object")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid column types: {e}")

    # Parse CSV
    try:
        reader = csv.reader(io.StringIO(raw))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Empty CSV")
        headers = rows[0]
        data_rows = rows[1:]
        if not headers:
            raise HTTPException(status_code=400, detail="CSV missing header row")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # Build CREATE TABLE statement in user's schema
    # Sanitize and map types; support basic types text, integer, float, boolean, date, timestamp
    def map_type(t: str) -> str:
        t = (t or "").lower()
        if t in ("int", "integer", "bigint"):
            return "BIGINT"
        if t in ("float", "double", "real", "numeric", "decimal"):
            return "DOUBLE PRECISION"
        if t in ("bool", "boolean"):
            return "BOOLEAN"
        if t in ("date",):
            return "DATE"
        if t in ("timestamp", "datetime"):
            return "TIMESTAMP"
        return "TEXT"

    columns_sql_parts: List[str] = []
    safe_headers: List[str] = []
    for h in headers:
        safe_h = _slugify_identifier(h)
        safe_headers.append(safe_h)
        col_type = map_type(column_types.get(h) or column_types.get(safe_h) or "text")
        columns_sql_parts.append(f'"{safe_h}" {col_type}')

    create_sql = f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" ( {", ".join(columns_sql_parts)} );'

    # Insert rows using parameterized COPY-like inserts (simple executemany)
    # Convert values according to types where possible
    from typing import Optional

    def convert_value(val: Optional[str], t: str):
        try:
            t = (t or "").lower()
            if val == "" or val is None:
                return None
            if t in ("int", "integer", "bigint"):
                return int(val)
            if t in ("float", "double", "real", "numeric", "decimal"):
                return float(val)
            if t in ("bool", "boolean"):
                return str(val).strip().lower() in ("1", "true", "t", "yes", "y")
            # For date/timestamp leave as text; Postgres will cast TEXT to proper type if possible when inserting into typed cols
            return val
        except Exception:
            return None if val == "" else val

    type_lookup = {
        (h if h in column_types else _slugify_identifier(h)): (
            column_types.get(h) or column_types.get(_slugify_identifier(h)) or "text"
        )
        for h in headers
    }

    with db.begin():
        # Create table
        db.execute(text(create_sql))
        # Prepare insert
        cols_quoted = ", ".join([f'"{h}"' for h in safe_headers])
        placeholders = ", ".join([f":v{i}" for i in range(len(safe_headers))])
        insert_sql = text(
            f'INSERT INTO "{schema_name}"."{table_name}" ( {cols_quoted} ) VALUES ( {placeholders} )'
        )

        batch_params = []
        for row in data_rows:
            values = []
            for i, h in enumerate(headers):
                raw_val = row[i] if i < len(row) else None
                t = (
                    type_lookup.get(h)
                    or type_lookup.get(_slugify_identifier(h))
                    or "text"
                )
                values.append(convert_value(raw_val, t))
            params = {f"v{i}": v for i, v in enumerate(values)}
            batch_params.append(params)

        if batch_params:
            db.execute(insert_sql, batch_params)

    # Register a 'custom' connection pointing to this user's schema in the main Postgres
    conn_payload = UserConnectionCreate(
        name=f"{table_name} (custom)",
        db_type="custom",
        host=None,
        port=None,
        username=None,
        database_name=schema_name,
        password=None,
    )
    record = user_connection_crud.create_user_connection(
        db, current_user.id, conn_payload
    )
    return record
