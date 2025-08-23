from langgraph.graph import MessagesState
from typing import Optional


class AigisState(MessagesState):
    db_schema: Optional[str]
    connection: Optional[str]
