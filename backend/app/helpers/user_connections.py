import json
from typing import Optional


from core.database import db_manager
from sqlalchemy import inspect, text
from crud.connection import user_connection_crud
from core.crypto import decrypt_secret
from core.config import settings
from sqlalchemy import text


def get_db_schema(connection: dict | None = None) -> str:
    # Determine engine based on provided connection reference (user_id, connection_id)
    engine = None
    if connection:
        try:
            # Prefer minimal reference { user_id, connection_id }
            ref_user_id = connection.get("user_id")
            ref_connection_id = connection.get("connection_id") or connection.get("id")

            if ref_user_id is not None and ref_connection_id is not None:
                # Fetch full connection details from main DB and decrypt password if present
                with db_manager.get_postgres_session_context() as db:
                    record = user_connection_crud.get_user_connection(
                        db,
                        user_id=int(ref_user_id),
                        connection_id=int(ref_connection_id),
                    )

                    if record is not None:
                        db_type = (record.db_type or "").lower()
                        host = record.host
                        port = record.port
                        username = record.username
                        database_name = record.database_name
                        password = None
                        if record.encrypted_password and record.iv:
                            try:
                                password = decrypt_secret(
                                    record.encrypted_password,
                                    record.iv,
                                    settings.master_encryption_key,
                                )
                            except Exception:
                                password = None

                        engine = db_manager.get_user_connection_engine(
                            int(ref_user_id),
                            int(ref_connection_id),
                            db_type,
                            host,
                            int(port) if port is not None else None,
                            username,
                            password,
                            database_name,
                        )
            else:
                # Backward compatibility: full connection dict provided
                user_id = connection.get("user_id")
                connection_id = connection.get("id")
                db_type = (connection.get("db_type") or "").lower()
                host = connection.get("host")
                port = connection.get("port")
                username = connection.get("username")
                password = connection.get("password")
                database_name = connection.get("database_name")

                if user_id is not None and connection_id is not None and db_type:
                    engine = db_manager.get_user_connection_engine(
                        int(user_id),
                        int(connection_id),
                        db_type,
                        host,
                        int(port) if port is not None else None,
                        username,
                        password,
                        database_name,
                    )
        except Exception:
            engine = None

    if engine is None:
        return ""
    inspector = inspect(engine)
    try:
        tables = inspector.get_table_names()
    except Exception:
        # Fallback: query sqlite_master directly if inspector fails
        tables = []
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                )
                tables = [row[0] for row in result]
        except Exception:
            tables = []

    md_parts = []
    # Build markdown for each table: title + markdown table (columns) + up to 3 sample rows
    try:
        with engine.connect() as conn:
            for table in tables:
                md_parts.append(f"### {table}\n")

                # Get columns
                try:
                    cols = inspector.get_columns(table)
                    col_names = [c["name"] for c in cols]
                except Exception:
                    col_names = []

                if not col_names:
                    md_parts.append("_No columns found._\n\n")
                    continue

                # Header and separator
                header = "| " + " | ".join(col_names) + " |"
                separator = "| " + " | ".join(["---"] * len(col_names)) + " |"
                md_parts.append(header)
                md_parts.append(separator)

                # Fetch up to 3 sample rows
                try:
                    result = conn.execute(text(f'SELECT * FROM "{table}" LIMIT 3;'))
                    rows = result.fetchall()
                except Exception:
                    rows = []

                if rows:
                    for row in rows:
                        # Row can be a Row or tuple; convert each cell to string and escape pipes
                        cells = []
                        for val in row:
                            s = "" if val is None else str(val)
                            s = s.replace("|", "\\|")
                            cells.append(s)
                        md_parts.append("| " + " | ".join(cells) + " |")
                else:
                    # Add empty placeholder rows if no data
                    for _ in range(3):
                        md_parts.append("| " + " | ".join([""] * len(col_names)) + " |")

                md_parts.append("\n")
    except Exception:
        # If anything goes wrong assembling markdown, return an empty schema string
        db_schema = ""
        return db_schema

    db_schema = "\n".join(md_parts)
    return db_schema


def execute_query(connection: dict, sql_query: str):
    try:
        conn_ref = connection
        user_id = conn_ref.get("user_id")
        connection_id = conn_ref.get("connection_id") or conn_ref.get("id")
        if user_id is None or connection_id is None:
            raise ValueError("Missing connection reference in state")

        # Fetch full connection record from the main DB and decrypt password
        with db_manager.get_postgres_session_context() as db:
            record = user_connection_crud.get_user_connection(
                db, user_id=int(user_id), connection_id=int(connection_id)
            )
            if record is None:
                raise ValueError("User connection not found")

            password: Optional[str] = None
            if record.encrypted_password and record.iv:
                try:
                    password = decrypt_secret(
                        record.encrypted_password,
                        record.iv,
                        settings.master_encryption_key,
                    )
                except Exception:
                    password = None

            engine = db_manager.get_user_connection_engine(
                int(user_id),
                int(connection_id),
                (record.db_type or "").lower(),
                record.host,
                int(record.port) if record.port is not None else None,
                record.username,
                password,
                record.database_name,
            )

        # Execute the query and serialize results
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            if hasattr(result, "returns_rows") and result.returns_rows:
                rows = result.mappings().fetchmany(50)
                data = [dict(row) for row in rows]
                columns = list(rows[0].keys()) if rows else []
                sql_execution_result = json.dumps({"columns": columns, "rows": data})
            else:
                rowcount = getattr(result, "rowcount", None)
                sql_execution_result = json.dumps({"rowcount": rowcount})

        return (sql_execution_result, None)

    except Exception as e:
        return (None, e)
