from typing import Any, Dict, List, Optional, Annotated
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

    ask_analyst_prompt = """
You are a Vega-Lite writing agent that ONLY responds with raw Vega-Lite JSON spec.
You will be provided with a natural language query and relevant data. Using the data and the query, build a Vega-Lite JSON spec to build the requested visualization.
DO NOT respond with anything else besides just the raw JSON.

The $schema to use is: https://vega.github.io/schema/vega-lite/v5.json

Here are some examples:
<examples>
    <example>
    {{
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "A simple bar chart.",
    "data": {{
        "values": [
        {{"category": "A", "amount": 28}},
        {{"category": "B", "amount": 55}},
        {{"category": "C", "amount": 43}}
        ]
    }},
    "mark": "bar",
    "encoding": {{
        "x": {{"field": "category", "type": "ordinal"}},
        "y": {{"field": "amount", "type": "quantitative"}}
    }}
    }}
    </example>
    <example>
    {{
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "Stock price over time.",
    "data": {{
        "values": [
        {{"date": "2025-01-01", "price": 150}},
        {{"date": "2025-01-02", "price": 155}},
        {{"date": "2025-01-03", "price": 148}},
        {{"date": "2025-01-04", "price": 152}},
        {{"date": "2025-01-05", "price": 160}},
        {{"date": "2025-01-06", "price": 158}}
        ]
    }},
    "mark": {{"type": "line", "point": true}},
    "encoding": {{
        "x": {{"field": "date", "type": "temporal", "title": "Date"}},
        "y": {{"field": "price", "type": "quantitative", "title": "Price (USD)"}}
    }}
    }}
    </example>
</examples>

Here is the query with relevant data:
<query_with_data>
    {query_with_data}
</query_with_data>
"""

    json_fixer_prompt = """
You are a JSON fixing agent. Your job is to read a raw JSON, identify where it is broken and fix it.
You should then output the fixed JSON.
ONLY output the full fixed JSON.

<json>
    {json}
</json>
"""

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
