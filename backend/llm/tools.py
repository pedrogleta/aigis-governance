from typing import Any, Dict, List, Optional
from langchain_core.tools import tool


def make_ask_database(model: Optional[Any] = None):
    """Factory that returns the ask_database tool bound to an optional model.

    The model can be any callable/LLM-like object you want to use internally
    (e.g., a structured-output wrapper). Keeping this as a factory avoids
    circular imports by injecting dependencies from the outside at runtime.
    """

    @tool
    def ask_database(query: str):
        """Consults database based on natural language query"""
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
