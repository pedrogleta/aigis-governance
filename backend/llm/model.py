import os
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

load_dotenv(override=True)

# Initialize available model clients (not bound to tools here) only when env allows
_lm_studio_endpoint = os.getenv("LM_STUDIO_ENDPOINT")
_deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

qwen_llm: Optional[BaseChatModel] = None
gpt_oss_llm: Optional[BaseChatModel] = None
deepseek_llm: Optional[BaseChatModel] = None

if _lm_studio_endpoint:
    qwen_llm = init_chat_model(
        "qwen/qwen3-8b",
        temperature=0,
        model_provider="openai",
        base_url=_lm_studio_endpoint,
        api_key="not-needed",
        stream_usage=True,
    )

    gpt_oss_llm = init_chat_model(
        "openai/gpt-oss-20b",
        temperature=0,
        model_provider="openai",
        base_url=_lm_studio_endpoint,
        api_key="not-needed",
        stream_usage=True,
    )

if _deepseek_api_key:
    deepseek_llm = init_chat_model(
        "deepseek-chat",
        model_provider="deepseek",
        stream_usage=True,
        temperature=0,
    )

# Canonical registry of available models
_MODEL_REGISTRY: Dict[str, BaseChatModel] = {}
if qwen_llm is not None:
    _MODEL_REGISTRY["qwen3-8b"] = qwen_llm
if gpt_oss_llm is not None:
    _MODEL_REGISTRY["gpt-oss-20b"] = gpt_oss_llm
if deepseek_llm is not None:
    _MODEL_REGISTRY["deepseek-chat"] = deepseek_llm

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
            f"Unknown or unavailable model '{name}'. Available now: {list(_MODEL_REGISTRY.keys())}"
        )
    _current_model_name = canonical


def get_current_model_name() -> Optional[str]:
    return _current_model_name


def get_current_llm() -> Optional[BaseChatModel]:
    """Return the currently selected model client (unbound), or None if unset."""
    if not _current_model_name:
        return None
    return _MODEL_REGISTRY.get(_current_model_name)


# --- Per-thread utilities ---
def get_llm_by_name(name: str) -> Optional[BaseChatModel]:
    """Return an initialized LLM by canonical name. Returns None if unavailable."""
    return _MODEL_REGISTRY.get(name)


def is_model_available(name: str) -> bool:
    """Check if canonical model name is currently available (env configured)."""
    return name in _MODEL_REGISTRY


def canonicalize_model_name(name: str) -> Optional[str]:
    """Resolve input name or alias to canonical model name, only if available."""
    canonical = resolve_model_name(name)
    if canonical and canonical in _MODEL_REGISTRY:
        return canonical
    return None
