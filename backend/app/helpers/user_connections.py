from core.database import db_manager
from sqlalchemy import inspect


def get_db_schema(connection: dict | None = None) -> str:
    # Determine engine based on provided connection; fallback to default sqlite engine
    engine = None
    if connection:
        try:
            user_id = connection.get("user_id")
            connection_id = connection.get("id")
            db_type = (connection.get("db_type") or "").lower()
            host = connection.get("host")
            port = connection.get("port")
            username = connection.get("username")
            # Password is not sent from frontend; attempt without it. If required, this will fail gracefully below.
            password = None
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
                    result = conn.execute(f'SELECT * FROM "{table}" LIMIT 3;')
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
