from langgraph.graph import MessagesState
from typing import Optional, Dict, Any


class AigisState(MessagesState):
    db_schema: Optional[str]
    connection: Optional[Dict[str, Any]]
