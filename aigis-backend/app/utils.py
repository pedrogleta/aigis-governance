import os
import json
from typing import Literal, Tuple, cast, Dict, Any
from langchain_core.messages import AIMessageChunk, ToolMessage
from langgraph.graph.state import RunnableConfig
from pydantic import BaseModel
from opik.integrations.langchain import OpikTracer

from app.agent import graph
from core.types import AigisState

os.environ["OPIK_URL_OVERRIDE"] = "http://localhost:5173/api"
tracer = OpikTracer(graph=graph.get_graph(xray=True))


class Chunk(BaseModel):
    type: Literal["AIMessageChunk"]


async def stream_langgraph_events(
    graph_input: AigisState,
    thread: RunnableConfig,
    active_threads: Dict[str, Any],
):
    """
    Asynchronous generator to stream LangGraph events.
    """

    thread_id = cast(dict, thread)["configurable"]["thread_id"]
    full_response = ""

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

    # Store the complete AI response in thread history
    if thread_id in active_threads:
        active_threads[thread_id]["messages"].append(
            {
                "sender": "ai",
                "text": full_response,
                "timestamp": "now",  # You might want to use proper datetime here
            }
        )

    # Send end signal
    end_msg = {"type": "end", "full_response": full_response}
    yield f"data: {json.dumps(end_msg)}\n\n"
