"""
Backfill per-user PostgreSQL schemas for all existing users.

Usage (from backend/ directory):
    uv run python -m scripts.create_user_schemas
"""

from core.database import db_manager
from models.user import User
from core.tenancy import make_user_schema_name, ensure_user_schema


def main() -> None:
    with db_manager.get_postgres_session_context() as db:
        users = db.query(User).all()
        count = 0
        for u in users:
            schema = make_user_schema_name(u.email, u.id)
            ensure_user_schema(db, schema)
            count += 1
        print(f"Ensured schemas for {count} users.")


if __name__ == "__main__":
    main()
