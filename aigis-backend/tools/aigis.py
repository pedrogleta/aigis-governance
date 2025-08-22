from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing import Annotated, List, TypedDict, cast
from langchain_core.tools import InjectedToolCallId, tool

from prompts.aigis import aigis_prompt
from core.model import deepseek_llm, gpt_oss_llm, qwen_llm


@tool
def ask_database(query: str):
    """Consults database based on natural language query"""

    # @@TODO get db_schema from state


@tool
def ask_analyst(query: str):
    """Asks for Data Analyst to build a plot with data you provide"""


tools = [ask_database, ask_analyst]
