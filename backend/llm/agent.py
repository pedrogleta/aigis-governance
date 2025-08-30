from typing import cast

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from core.types import AigisState
from llm.model import get_current_llm
from llm.prompts import aigis_prompt
from llm.tools import create_tools


load_dotenv(override=True)


def _build_assistant_node(model_with_tools):
    def assistant(state: AigisState):
        db_schema = state.get("db_schema", "No connection selected by the user.")
        sql_result = state.get("sql_result", "")

        sys_message = SystemMessage(
            content=aigis_prompt.format(db_schema=db_schema, sql_result=sql_result)
        )

        assistant_response = cast(
            AIMessage, model_with_tools.invoke([sys_message] + state["messages"])
        )

        return {"messages": [assistant_response]}

    return assistant


_checkpointer = MemorySaver()
_graph = None
_bound_model = None


def rebuild_graph() -> None:
    """Rebuild the LangGraph using the currently selected model and tools.

    If no model is selected, tools will return configuration errors until a model
    is set, and the assistant node will also raise if invoked. This encourages
    clients to set a model via API before chatting.
    """
    global _graph, _bound_model
    base_model = get_current_llm()
    tools = create_tools(base_model)
    model_with_tools = base_model.bind_tools(tools) if base_model else None
    _bound_model = model_with_tools

    builder = StateGraph(AigisState)
    # Assistant node requires a model_with_tools. Provide a guard that emits a helpful error.
    if model_with_tools is None:

        def assistant_error(state: AigisState):
            raise RuntimeError(
                "No model selected. Use the /models/select endpoint to set a model before chatting."
            )

        builder.add_node("assistant", assistant_error)
    else:
        builder.add_node("assistant", _build_assistant_node(model_with_tools))

    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    builder.add_edge("assistant", END)

    _graph = builder.compile(checkpointer=_checkpointer)


def get_graph():
    """Get the compiled graph, building it lazily if needed."""
    global _graph
    if _graph is None:
        rebuild_graph()
    return _graph
