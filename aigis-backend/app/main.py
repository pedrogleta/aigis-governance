from typing import cast
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import RunnableConfig
import uvicorn
import uuid
from datetime import datetime

from app.utils import stream_langgraph_events
from app.agent import graph
from core.types import AigisState

load_dotenv(override=True)

app = FastAPI()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active threads (in production, use a proper database)
active_threads = {}


@app.post("/chat/thread")
async def create_thread():
    """Create a new chat thread"""
    thread_id = str(uuid.uuid4())
    active_threads[thread_id] = {
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
    }
    return {"thread_id": thread_id}


@app.post("/chat/{thread_id}/message")
async def send_message(thread_id: str, message: dict):
    """Send a message to the AI agent and stream the response"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Add user message to thread history
    active_threads[thread_id]["messages"].append(
        {
            "sender": "user",
            "text": message.get("text", ""),
            "timestamp": datetime.utcnow().isoformat(),
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


@app.get("/chat/{thread_id}")
async def get_thread_messages(thread_id: str):
    """Get all messages for a specific thread"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    return active_threads[thread_id]


@app.get("/chat/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get the current graph state for a specific thread"""
    if thread_id not in active_threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        # Get the current state from the graph's checkpointer
        thread_config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})

        state = graph.get_state(thread_config)

        print(state)

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
