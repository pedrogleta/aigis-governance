"""
Utilities for multi-tenant behavior, such as creating per-user schemas in Postgres.
"""

import re
from sqlalchemy.orm import Session
from sqlalchemy import text


MAX_IDENTIFIER_LEN = 63  # PostgreSQL identifier max length


def _slugify_email(email: str) -> str:
    """Convert an email into a safe PostgreSQL identifier fragment.

    - lowercase
    - replace non [a-z0-9_] with '_'
    - collapse multiple underscores
    - ensure starts with a letter by prefixing 'u_'
    """
    base = email.strip().lower()
    base = re.sub(r"[^a-z0-9_]", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base or not base[0].isalpha():
        base = f"u_{base}" if base else "u"
    return base


def make_user_schema_name(email: str, user_id: int) -> str:
    """Create a deterministic, unique, and valid schema name from email + user id.

    Schema name format: <slug(email)>__u<id>, truncated to 63 chars.
    We reserve space for the suffix to keep uniqueness.
    """
    suffix = f"__u{user_id}"
    slug = _slugify_email(email)
    allowed = MAX_IDENTIFIER_LEN - len(suffix)
    if allowed < 1:
        # extremely large id; fallback to 'u<id>'
        return f"u{user_id}"[-MAX_IDENTIFIER_LEN:]
    base = slug[:allowed]
    return f"{base}{suffix}"


def ensure_user_schema(db: Session, schema_name: str) -> None:
    """Create the schema in Postgres if it does not already exist."""
    # Safe since schema_name is strictly sanitized to [a-z0-9_]
    db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    db.commit()
