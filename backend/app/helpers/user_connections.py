import json
from typing import Optional, TypedDict, Any


from core.database import db_manager
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from crud.connection import user_connection_crud
from core.crypto import decrypt_secret
from core.config import settings


class ConnectionMinimalReference(TypedDict):
    user_id: str
    connection_id: str


def get_db_schema(connection: ConnectionMinimalReference) -> str:
    """Return a markdown summary of the connected database schema.

    Strategy
    - Resolve an SQLAlchemy Engine from either a minimal reference (user_id, connection_id)
      or a legacy full connection dict.
    - Use Inspector to list tables and columns.
    - For each table, render a small markdown with up to N sample rows using
      a cross-dialect compatible query for LIMIT/TOP.
    - Fail soft: on any unexpected error, return an empty string.
    """

    def _resolve_engine_from_connection(
        conn_ref: ConnectionMinimalReference,
    ) -> tuple[Optional[Any | Engine], Optional[str], Optional[str]]:
        try:
            # Preferred minimal reference
            ref_user_id = conn_ref.get("user_id")
            ref_connection_id = conn_ref.get("connection_id")
            with db_manager.get_postgres_session_context() as db:
                record = user_connection_crud.get_user_connection(
                    db,
                    user_id=int(ref_user_id),
                    connection_id=int(ref_connection_id),
                )
                if record is None:
                    return (None, None, None)

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
                    (record.db_type or "").lower(),
                    record.host,
                    int(record.port) if record.port is not None else None,
                    record.username,
                    password,
                    record.database_name,
                )
                return (engine, record.db_type, record.table_name)

        except Exception:
            return (None, None, None)
        return (None, None, None)

    def _db_type_label(engine) -> str:
        try:
            name = (engine.dialect.name or "").lower()
            if "postgres" in name:
                return "PostgreSQL"
            if "sqlite" in name:
                return "SQLite"
            if "mssql" in name or "sqlserver" in name:
                return "SQL Server"
            if "oracle" in name:
                return "Oracle"
            if "mysql" in name:
                return "MySQL"
            return name.capitalize() if name else "Unknown"
        except Exception:
            return "Unknown"

    def _quote_identifier(engine, identifier: str) -> str:
        try:
            return engine.dialect.identifier_preparer.quote(identifier)
        except Exception:
            # Fallback to safe double quotes if preparer unavailable
            return f'"{identifier}"'

    def _sample_query(engine, table_name: str, limit: int) -> str:
        dialect = (engine.dialect.name or "").lower()
        qtable = _quote_identifier(engine, table_name)
        if "mssql" in dialect or "sqlserver" in dialect:
            return f"SELECT TOP {limit} * FROM {qtable};"
        if "oracle" in dialect:
            return f"SELECT * FROM {qtable} FETCH FIRST {limit} ROWS ONLY"
        # Default LIMIT works for PostgreSQL, SQLite, MySQL, DuckDB, etc.
        return f"SELECT * FROM {qtable} LIMIT {limit};"

    def _get_table_columns(inspector, table_name: str) -> list[str]:
        try:
            return [c.get("name") for c in inspector.get_columns(table_name)]
        except Exception:
            return []

    def _render_markdown_table(
        col_names: list[str], rows: list[tuple | list]
    ) -> list[str]:
        if not col_names:
            return ["_No columns found._\n", "\n"]

        lines: list[str] = []
        header = "| " + " | ".join(col_names) + " |"
        separator = "| " + " | ".join(["---"] * len(col_names)) + " |"
        lines.append(header)
        lines.append(separator)

        if rows:
            for row in rows:
                cells = []
                for val in row:
                    s = "" if val is None else str(val)
                    s = s.replace("|", "\\|")
                    cells.append(s)
                lines.append("| " + " | ".join(cells) + " |")
        else:
            for _ in range(3):
                lines.append("| " + " | ".join([""] * len(col_names)) + " |")

        lines.append("\n")
        return lines

    # 1) Resolve engine
    engine, db_type, table_name = _resolve_engine_from_connection(connection)
    if engine is None:
        return ""

    # 2) Prepare inspector and metadata
    try:
        inspector = inspect(engine)
        db_label = _db_type_label(engine)
        try:
            tables = inspector.get_table_names()
        except Exception:
            tables = []

        # If this is a 'custom' connection, only include the specific table_name stored on the connection
        if db_type == "custom":
            if table_name is not None and table_name != "":
                tables = [table_name]

        md_parts = [f"Database Type: {db_label}\n", "\n"]

        SAMPLE_LIMIT = 3
        with engine.connect() as conn:
            for table in tables:
                md_parts.append(f"### {table}\n")
                col_names = _get_table_columns(inspector, table)

                rows: list = []
                if col_names:
                    try:
                        query = _sample_query(engine, table, SAMPLE_LIMIT)
                        result = conn.execute(text(query))
                        rows = result.fetchall()
                    except Exception:
                        rows = []

                md_parts.extend(_render_markdown_table(col_names, rows))
    except Exception:
        return ""

    return "\n".join(md_parts)


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
