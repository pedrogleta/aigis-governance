from typing import cast
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langgraph.graph.state import RunnableConfig
from langchain_core.messages import ToolMessage, HumanMessage

from app.helpers.langgraph import stream_langgraph_events
from llm.agent import graph
from app.helpers.user_connections import get_db_schema
from core.types import AigisState
from app.state import active_threads
from core.database import get_postgres_db
from auth.dependencies import get_current_user
from models.user import User
from crud.thread import thread_crud


router = APIRouter(prefix="/chat")


@router.post("/thread")
async def create_thread(db: Session = Depends(get_postgres_db)):
    """Create a new chat thread and persist to Postgres"""
    thread_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    # Persist thread
    db_thread = thread_crud.create_thread(
        db, thread_id=thread_id, created_at=created_at
    )

    # Keep lightweight in-memory entry for active streaming coordination
    active_threads[thread_id] = {
        "created_at": created_at.isoformat(),
        "messages": [],
    }

    return {"thread_id": db_thread.thread_id}


@router.post("/{thread_id}/message")
async def send_message(
    thread_id: str,
    message: dict,
    db: Session = Depends(get_postgres_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the AI agent, persist user message, and stream the agent response"""
    db_thread = thread_crud.get_thread_by_thread_id(db, thread_id)
    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Persist user message
    timestamp = datetime.now(timezone.utc)
    user_text = message.get("text", "")
    # Optional user-selected connection from frontend
    user_connection_id = message.get("user_connection_id")
    thread_crud.add_message(
        db, db_thread, sender="user", text=user_text, timestamp=timestamp
    )

    # Update in-memory history for quick access/streaming
    if thread_id not in active_threads:
        active_threads[thread_id] = {
            "created_at": db_thread.created_at.isoformat(),
            "messages": [],
        }

    active_threads[thread_id]["messages"].append(
        {
            "sender": "user",
            "text": user_text,
            "timestamp": timestamp.isoformat(),
        }
    )

    # Prepare the input for the agent
    thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

    # Pass only minimal reference. Helper will resolve details with password.
    graph_input = cast(
        AigisState,
        {
            "messages": [user_text],
            "connection": {
                "user_id": current_user.id,
                "connection_id": user_connection_id,
            }
            if user_connection_id is not None
            else None,
        },
    )

    # Stream the AI response
    return StreamingResponse(
        stream_langgraph_events(graph_input, thread_config, active_threads, db),
        media_type="text/event-stream",
    )


@router.get("/{thread_id}")
async def get_thread_messages(thread_id: str, db: Session = Depends(get_postgres_db)):
    """Get all messages for a specific thread (from Postgres)"""
    db_thread = thread_crud.get_thread_by_thread_id(db, thread_id)
    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Return thread with messages
    thread = thread_crud.get_thread_with_messages(db, db_thread)

    # Convert to a simple dict structure
    messages = [
        {"sender": m.sender, "text": m.text, "timestamp": m.timestamp.isoformat()}
        for m in thread.messages
    ]

    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "messages": messages,
    }


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get the current graph state for a specific thread"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        # Get the current state from the graph's checkpointer
        thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

        state = graph.get_state(thread_config)
        db_schema = state.values.get("db_schema", "")
        connection = state.values.get("connection")

        return {
            "thread_id": thread_id,
            "thread_info": active_threads[thread_id],
            "graph_state": {"db_schema": db_schema, "connection": connection},
            "status": "active",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving graph state: {str(e)}"
        )


@router.post("/{thread_id}/connection")
async def update_thread_connection(
    thread_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    """Update the graph state for a thread with a new connection, and precompute db_schema."""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    user_connection_id = payload.get("user_connection_id")
    if user_connection_id is None:
        raise HTTPException(status_code=400, detail="user_connection_id is required")

    thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

    # Build minimal connection reference
    connection_ref = {"user_id": current_user.id, "connection_id": user_connection_id}

    # Compute db_schema for the new connection and update graph state
    db_schema = get_db_schema(connection=connection_ref)

    try:
        # Update the checkpointer state with both connection and db_schema
        graph.update_state(
            thread_config,
            {
                "connection": connection_ref,
                "db_schema": db_schema,
                "messages": [
                    HumanMessage(
                        content=f"Your connection has been changed to:\n\n{db_schema}"
                    )
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update state: {str(e)}")
    current_state = graph.get_state(thread_config)
    return {"graph_state": current_state}
