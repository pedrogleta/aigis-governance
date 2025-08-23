from typing import cast
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.graph.state import RunnableConfig

from app.utils import stream_langgraph_events
from app.agent import graph
from core.types import AigisState
from app.state import active_threads

router = APIRouter(prefix="/chat")


@router.post("/thread")
async def create_thread():
    """Create a new chat thread"""
    thread_id = str(uuid.uuid4())
    active_threads[thread_id] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
    }
    return {"thread_id": thread_id}


@router.post("/{thread_id}/message")
async def send_message(thread_id: str, message: dict):
    """Send a message to the AI agent and stream the response"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Add user message to thread history
    active_threads[thread_id]["messages"].append(
        {
            "sender": "user",
            "text": message.get("text", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Prepare the input for the agent
    thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

    graph_input = cast(
        AigisState,
        {"messages": [message.get("text", "")]},
    )

    # Stream the AI response
    return StreamingResponse(
        stream_langgraph_events(graph_input, thread_config, active_threads),
        media_type="text/event-stream",
    )


@router.get("/{thread_id}")
async def get_thread_messages(thread_id: str):
    """Get all messages for a specific thread"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    return active_threads[thread_id]


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get the current graph state for a specific thread"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        # Get the current state from the graph's checkpointer
        thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

        state = graph.get_state(thread_config)

        db_schema = state.values["db_schema"] if "db_schema" in state.values else ""

        return {
            "thread_id": thread_id,
            "thread_info": active_threads[thread_id],
            "graph_state": {"db_schema": db_schema},
            "status": "active",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving graph state: {str(e)}"
        )
