from typing import Any, List, Optional, Annotated
import json
from app.helpers.user_connections import execute_query
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from llm.prompts import ask_analyst_prompt, json_fixer_prompt, ask_database_prompt
from llm.model import get_llm_by_name


def _resolve_thread_model(state: dict) -> Optional[BaseChatModel]:
    name = state.get("model_name") if isinstance(state, dict) else None
    if not name:
        return None
    return get_llm_by_name(name)


def make_ask_database(model: Optional[BaseChatModel] = None):
    """Factory that returns the ask_database tool. Model is resolved per-thread from state."""

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

        # Resolve model per-thread
        effective_model = model or _resolve_thread_model(state)
        if not effective_model:
            return "Error: no model selected for this thread. Ask the user to pick a model."

        sql_query_message = effective_model.invoke(
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
                            f"Query failed to execute.\n Query: {sql_query}\n Error: {str(error)}",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        f"Executed query successfully!\n Query: {sql_query}\n Result: {sql_execution_result}",
                        tool_call_id=tool_call_id,
                    )
                ],
                "sql_result": sql_execution_result,
            }
        )

    return ask_database


def make_ask_analyst(model: Optional[BaseChatModel] = None):
    """Factory that returns the ask_analyst tool. Model is resolved per-thread from state."""

    @tool
    def ask_analyst(
        query: str,
        state: Annotated[dict, InjectedState],
    ):
        """Asks for Data Analyst to build a plot with data you provide"""

        effective_model = model or _resolve_thread_model(state)
        if not effective_model:
            return "Error: no model selected for this thread. Ask the user to pick a model."

        vega_lite_spec_message = effective_model.invoke(
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
                fix_response = effective_model.invoke(
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
    """Create tool instances. Model is resolved per-thread at call time via state."""
    return [
        make_ask_database(model),
        make_ask_analyst(model),
    ]
