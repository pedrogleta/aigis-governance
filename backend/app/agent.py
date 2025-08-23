from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
)
from langgraph.prebuilt import tools_condition, ToolNode
from typing import cast
from core.types import AigisState
from tools.aigis import tools
from core.model import qwen_llm_with_tools
from prompts.aigis import aigis_prompt
from dotenv import load_dotenv

load_dotenv(override=True)


def check_db_schema(state: AigisState):
    if "db_schema" not in state:
        print("get db schema")
        db_schema = "example"
        return {"db_schema": db_schema}

    return {}


def assistant(state: AigisState):
    db_schema = state["db_schema"]

    sys_message = SystemMessage(content=aigis_prompt.format(db_schema=db_schema))

    assistant_response = cast(
        AIMessage, qwen_llm_with_tools.invoke([sys_message] + state["messages"])
    )

    return {"messages": [assistant_response]}


builder = StateGraph(AigisState)

builder.add_node("check_db_schema", check_db_schema)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "check_db_schema")
builder.add_edge("check_db_schema", "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
builder.add_edge("assistant", END)


checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
