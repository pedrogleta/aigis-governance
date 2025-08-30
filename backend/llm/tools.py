from typing import Any, List, Optional, Annotated
import json
from sqlalchemy import text
from app.helpers.user_connections import execute_query
from core.database import db_manager
from crud.connection import user_connection_crud
from core.crypto import decrypt_secret
from core.config import settings
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from llm.prompts import ask_analyst_prompt, json_fixer_prompt, ask_database_prompt
from llm.model import get_current_llm


def make_ask_database(model: Optional[BaseChatModel] = None):
    """Factory that returns the ask_database tool bound to an optional model."""

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

        (sql_execution_result, error) = execute_query(connection, sql_query)

        if error is not None:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            f"Query failed to execute. Error: {str(error)}",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )
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

    return ask_database


def make_ask_analyst(model: Optional[BaseChatModel] = None):
    """Factory that returns the ask_analyst tool bound to an optional model."""

    @tool
    def ask_analyst(query: str):
        """Asks for Data Analyst to build a plot with data you provide"""

        if not model:
            return "Error: app configuration error. Tell the user it's an internal server error."

        vega_lite_spec_message = model.invoke(
            [SystemMessage(content=ask_analyst_prompt.format(query_with_data=query))]
        )

        vega_lite_spec = str(vega_lite_spec_message.content)

        max_retries = 3
        for attempt_num in range(max_retries):
            try:
                json.loads(vega_lite_spec)
                break
            except Exception:
                if attempt_num == max_retries - 1:
                    break
                fix_response = model.invoke(
                    [
                        SystemMessage(
                            content=json_fixer_prompt.format(json=vega_lite_spec)
                        )
                    ]
                )
                new_spec = str(fix_response.content)
                if new_spec.strip() == vega_lite_spec.strip():
                    break
                vega_lite_spec = new_spec

        return {"type": "vega_lite_spec", "spec": vega_lite_spec}

    return ask_analyst


def create_tools(model: Optional[BaseChatModel] = None) -> List[Any]:
    """Create tool instances bound to the provided or current global LLM.

    If no model is provided, the globally selected model will be used. If none is
    selected, the tools will gracefully report an internal configuration error
    when called.
    """
    bound_model = model or get_current_llm()
    return [
        make_ask_database(bound_model),
        make_ask_analyst(bound_model),
    ]
