import os
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

load_dotenv(override=True)

# Initialize available model clients (not bound to tools here)
qwen_llm = init_chat_model(
    "qwen/qwen3-8b",
    temperature=0,
    model_provider="openai",
    base_url=os.getenv("LM_STUDIO_ENDPOINT", "http://0.0.0.0:1234/v1"),
    api_key="not-needed",
    stream_usage=True,
)

gpt_oss_llm = init_chat_model(
    "openai/gpt-oss-20b",
    temperature=0,
    model_provider="openai",
    base_url=os.getenv("LM_STUDIO_ENDPOINT", "http://0.0.0.0:1234/v1"),
    api_key="not-needed",
    stream_usage=True,
)

deepseek_llm = init_chat_model(
    "deepseek-chat", model_provider="deepseek", stream_usage=True, temperature=0
)

# Canonical registry of available models
_MODEL_REGISTRY: Dict[str, BaseChatModel] = {
    "qwen3-8b": qwen_llm,
    "gpt-oss-20b": gpt_oss_llm,
    "deepseek-chat": deepseek_llm,
}

# Aliases for convenience
_ALIASES: Dict[str, str] = {
    "qwen": "qwen3-8b",
    "gpt_oss": "gpt-oss-20b",
    "gpt-oss": "gpt-oss-20b",
    "deepseek": "deepseek-chat",
}

# Current model selection (starts unset)
_current_model_name: Optional[str] = None


def _availability_flags() -> Dict[str, bool]:
    lm = bool(os.getenv("LM_STUDIO_ENDPOINT"))
    deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
    return {
        "qwen3-8b": lm,
        "gpt-oss-20b": lm,
        "deepseek-chat": deepseek,
    }


def get_available_models() -> Dict[str, Dict[str, object]]:
    """Return metadata for each supported model, including availability."""
    desc = {
        "qwen3-8b": "Qwen 3 8B (via LM Studio/OpenAI-compatible)",
        "gpt-oss-20b": "OpenAI GPT-OSS 20B (via LM Studio/OpenAI-compatible)",
        "deepseek-chat": "DeepSeek Chat (provider=deepseek)",
    }
    flags = _availability_flags()
    return {
        k: {"description": v, "available": flags.get(k, False)} for k, v in desc.items()
    }


def resolve_model_name(name: str) -> Optional[str]:
    """Resolve input name or alias to canonical model name."""
    if name in _MODEL_REGISTRY:
        return name
    return _ALIASES.get(name)


def set_current_model(name: str) -> None:
    """Set the globally active model by canonical name or alias."""
    global _current_model_name
    canonical = resolve_model_name(name)
    if not canonical or canonical not in _MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{name}'. Available: {list(_MODEL_REGISTRY.keys())}"
        )
    _current_model_name = canonical


def get_current_model_name() -> Optional[str]:
    return _current_model_name


def get_current_llm() -> Optional[BaseChatModel]:
    """Return the currently selected model client (unbound), or None if unset."""
    if not _current_model_name:
        return None
    return _MODEL_REGISTRY.get(_current_model_name)
