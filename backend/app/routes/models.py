from fastapi import APIRouter, HTTPException

from llm.agent import rebuild_graph
from llm.model import (
    get_available_models,
    get_current_model_name,
    set_current_model,
)


router = APIRouter(prefix="/models", tags=["models"])


@router.get("/")
def list_models():
    """List model options with availability flags."""
    return {
        "models": get_available_models(),
        "current": get_current_model_name(),
    }


@router.post("/select")
def select_model(payload: dict):
    """Select the active model for the assistant and tools.

    Body: {"name": "qwen3-8b" | "gpt-oss-20b" | "deepseek-chat" | "gemini-2.5-pro" | "gpt-5"}
    Aliases accepted: "qwen" → "qwen3-8b", "gpt_oss"/"gpt-oss" → "gpt-oss-20b",
    "deepseek" → "deepseek-chat", "gemini"/"gemini-pro" → "gemini-2.5-pro", "gpt5" → "gpt-5".
    """
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name' in body")
    try:
        set_current_model(name)
        rebuild_graph()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "current": get_current_model_name()}
