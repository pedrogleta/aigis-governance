import os
from langchain.chat_models import init_chat_model
from llm.tools import create_tools

from dotenv import load_dotenv

load_dotenv(override=True)

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

# Create a simple registry of models to pass into tool factories
models = {
    "qwen": qwen_llm,
    "gpt_oss": gpt_oss_llm,
    "deepseek": deepseek_llm,
}

# Create tools at runtime (no circular imports) and expose them
tools = create_tools(models)

qwen_llm_with_tools = qwen_llm.bind_tools(tools)
gpt_oss_llm_with_tools = gpt_oss_llm.bind_tools(tools)
