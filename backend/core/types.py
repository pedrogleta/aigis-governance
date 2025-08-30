from langgraph.graph import MessagesState
from typing import Optional, Dict, Any


class AigisState(MessagesState):
    model_name: Optional[str]
    db_schema: Optional[str]
    connection: Optional[Dict[str, Any]]
    sql_result: Optional[str]
