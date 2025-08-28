import json
import os
from typing import Literal, Tuple, cast, Dict, Any, Optional
from langchain_core.messages import AIMessageChunk, ToolMessage
from langgraph.graph.state import RunnableConfig
from pydantic import BaseModel

from llm.agent import graph
from core.types import AigisState
from sqlalchemy.orm import Session
from crud.thread import thread_crud
from datetime import datetime, timezone
from dotenv import load_dotenv
from opik.integrations.langchain import OpikTracer

load_dotenv()

tracer = None
# if os.getenv("ENABLE_OPIK_TRACER") != 0:
#     tracer = OpikTracer(graph=graph.get_graph(xray=True))
# else:
#     tracer = None


class Chunk(BaseModel):
    type: Literal["AIMessageChunk"]


async def stream_langgraph_events(
    graph_input: AigisState,
    thread: RunnableConfig,
    active_threads: Dict[str, Any],
    db: Optional[Session] = None,
):
    """
    Asynchronous generator to stream LangGraph events.
    """

    thread_id = cast(dict, thread)["configurable"]["thread_id"]
    full_response = ""

    # Attach tracer callback only when enabled and tracer exists.
    if tracer is not None:
        thread["callbacks"] = [tracer]

    async for event in graph.astream(graph_input, thread, stream_mode="messages"):
        event_tuple = cast(Tuple, event)
        chunk = event_tuple[0]

        if isinstance(chunk, AIMessageChunk):
            if event_tuple[1]["langgraph_node"] == "tools":
                continue
            content = chunk.content
            full_response += str(content)
            data_to_send = {"content": content, "type": "chunk"}
            yield f"data: {json.dumps(data_to_send)}\n\n"
        elif isinstance(chunk, ToolMessage):
            content = chunk.content
            data_to_send = {"content": content, "type": "tool_result"}
            yield f"data: {json.dumps(data_to_send)}\n\n"
        else:
            error_msg = {"error": "chunk not found", "type": "error"}
            print("Error chunk:")
            print(chunk)
            print("Chunk type:")
            print(chunk.type)
            yield f"data: {json.dumps(error_msg)}\n\n"

    # Store the complete AI response in thread history (in-memory)
    ai_timestamp = datetime.now(timezone.utc)
    if thread_id in active_threads:
        active_threads[thread_id]["messages"].append(
            {
                "sender": "ai",
                "text": full_response,
                "timestamp": ai_timestamp.isoformat(),
            }
        )

    # Persist AI response to DB if session provided
    if db is not None:
        db_thread = thread_crud.get_thread_by_thread_id(db, thread_id)
        if db_thread:
            thread_crud.add_message(
                db, db_thread, sender="ai", text=full_response, timestamp=ai_timestamp
            )

    # Send end signal
    end_msg = {"type": "end", "full_response": full_response}
    yield f"data: {json.dumps(end_msg)}\n\n"
