from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
)
from langgraph.prebuilt import tools_condition, ToolNode
from typing import cast
from core.types import AigisState
from llm.model import qwen_llm_with_tools, tools, gpt_oss_llm_with_tools
from llm.prompts import aigis_prompt
from dotenv import load_dotenv


load_dotenv(override=True)


def assistant(state: AigisState):
    db_schema = state.get("db_schema", "No connection selected by the user.")
    sql_result = state.get("sql_result", "")

    sys_message = SystemMessage(
        content=aigis_prompt.format(db_schema=db_schema, sql_result=sql_result)
    )

    assistant_response = cast(
        AIMessage, gpt_oss_llm_with_tools.invoke([sys_message] + state["messages"])
    )

    return {"messages": [assistant_response]}


builder = StateGraph(AigisState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
builder.add_edge("assistant", END)


checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
