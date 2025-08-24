from typing import Any, Dict, List, Optional, Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage


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
    def ask_database(query: str, state: Annotated[dict, InjectedState]):
        """Consults database based on natural language query"""

        if "db_schema" not in state:
            return "Error: ask_database tool not implemented. Warn the user"

        db_schema = state["db_schema"]

        if "connection" not in state:
            return "Error: ask_database tool not implemented. Warn the user"

        connection = state["connection"]

        if not model:
            return "Error: ask_database tool not implemented. Warn the user"

        sql_query = model.invoke(
            [
                SystemMessage(
                    content=ask_database_prompt.format(db_schema=db_schema, query=query)
                )
            ]
        )

        # @@TODO: use db_schema from state when the tool is executed (available via LangGraph state)
        # Optionally use `model` if provided, e.g. model.with_structured_output(...)
        _ = model  # placeholder to avoid unused var warnings if not used yet
        return {"status": "not-implemented", "query": query}

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
