from typing import Any, Dict, List, Optional, Annotated
import json
from sqlalchemy import text
from core.database import db_manager
from crud.connection import user_connection_crud
from core.crypto import decrypt_secret
from core.config import settings
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command


def make_ask_database(model: Optional[BaseChatModel] = None):
    """Factory that returns the ask_database tool bound to an optional model."""

    ask_database_prompt = """
You are a SQL writing agent that ONLY responds with raw SQL code.
You will be provided with a database schema and a natural language query. Using the schema and the query, build SQL to respond to that query.
DO NOT respond with anything else besides just the raw SQL code.

<db_schema>
    {db_schema}
</db_schema>

<query>
    {query}
</query>
"""

    @tool
    def ask_database(
        query: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[dict, InjectedState],
    ):
        """Consults database based on natural language query"""

        if "db_schema" not in state or "connection" not in state:
            return "Error: connection not found. Warn the user."

        db_schema = state["db_schema"]
        connection = state["connection"]

        if not model:
            return "Error: app configuration error. Tell the user it's an internal server error."

        sql_query_message = model.invoke(
            [
                SystemMessage(
                    content=ask_database_prompt.format(db_schema=db_schema, query=query)
                )
            ]
        )

        sql_query = str(sql_query_message.content)

        # Execute SQL against the user's selected connection
        sql_execution_result = ""

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
                    sql_execution_result = json.dumps(
                        {"columns": columns, "rows": data}
                    )
                else:
                    rowcount = getattr(result, "rowcount", None)
                    sql_execution_result = json.dumps({"rowcount": rowcount})

            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            "Executed query successfully!", tool_call_id=tool_call_id
                        )
                    ],
                    "sql_result": sql_execution_result,
                }
            )
        except Exception as e:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            f"Query failed to execute. Error: {str(e)}",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

    return ask_database


def make_ask_analyst(model: Optional[Any] = None):
    """Factory that returns the ask_analyst tool bound to an optional model."""

    @tool
    def ask_analyst(query: str):
        """Asks for Data Analyst to build a plot with data you provide"""
        _ = model
        return {"status": "not-implemented", "query": query}

    return ask_analyst


def create_tools(models: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Create the list of tools using the provided models registry.

    Pass in whatever models you want tools to use, e.g. {"qwen": qwen_llm}.
    This avoids importing models here and prevents circular imports.
    """
    models = models or {}
    qwen = models.get("qwen")
    # You can choose which model powers which tool; adjust as needed.
    return [
        make_ask_database(qwen),
        make_ask_analyst(qwen),
    ]
