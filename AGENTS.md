# Agents, tools, and streaming (current implementation)

This document explains how the agent, tools, and streaming pipeline work today. It reflects the FastAPI + LangGraph implementation found under `backend/`.

## Overview

- Conversation is thread‑based. The frontend creates a thread and then streams responses for each message.
- A single LangGraph state machine orchestrates the assistant and its tools.
- Two tools are implemented:
  - ask_database – write SQL from NL + schema; execute against the user‑selected DB
  - ask_analyst – produce a Vega‑Lite JSON spec from data for charting
- Streaming uses Server‑Sent Events (SSE) with small, structured payloads.

## Key files

- Graph and tools
  - `backend/llm/agent.py` – builds a LangGraph StateGraph over `AigisState`
  - `backend/llm/model.py` – initializes chat models, maintains a model registry and availability, resolves models per thread
  - `backend/llm/tools.py` – tool factories `make_ask_database`, `make_ask_analyst`, and `create_tools()` that resolve the model at call time
  - `backend/llm/prompts.py` – system and tool prompts
- State and helpers
  - `backend/core/types.py` – `AigisState` extends `MessagesState` with `model_name`, `db_schema`, `connection`, `sql_result`
  - `backend/app/helpers/user_connections.py` – resolves user connection, introspects schema, executes SQL
  - `backend/app/helpers/langgraph.py` – `stream_langgraph_events` converts LangGraph stream to SSE
- API
  - `backend/app/routes/chat.py` – thread creation, message send (SSE), state view, set connection
  - Per‑thread model APIs: `GET /chat/{thread_id}/model`, `POST /chat/{thread_id}/model`

## State shape

`AigisState` includes:
- `messages`: LangChain message list (managed by LangGraph)
- `model_name`: the effective model name for this thread (may be unset)
- `db_schema`: markdown snapshot of the connected DB (tables, columns, sample rows)
- `connection`: minimal reference `{ user_id, connection_id }`
- `sql_result`: last SQL execution result (JSON string: `{ columns: [], rows: [] }`)

## Agent graph

Defined in `backend/llm/agent.py`:
- Nodes: `assistant`, `tools`
- Edges: START → assistant → tools? → assistant → END (conditional via `tools_condition`)
- Checkpointer: in‑memory (`MemorySaver`)

The `assistant` function:
- Builds a `SystemMessage` from `aigis_prompt` with `db_schema` and `sql_result`
- Resolves the effective model for the current thread from `state.model_name` (or a global fallback) and binds tools on the fly
- Invokes the model with tools; if the model calls a tool, control moves to the tools node

## Tools

`llm/tools.py` defines factories that resolve the LLM per‑thread at call time:

- ask_database(query)
  - Uses the thread’s effective model to generate raw SQL (prompt: `ask_database_prompt`)
  - Executes SQL via `execute_query(connection, sql)` using SQLAlchemy and the dynamic engine for that user/connection
  - On success: returns a `Command(update={ messages: [ToolMessage(...)] , sql_result: <json> })`
  - On failure: returns a `Command(update={ messages: [ToolMessage("Query failed...")] })`

- ask_analyst(query)
  - Uses the thread’s effective model to return a Vega‑Lite JSON spec string
  - Attempts up to 3 automatic JSON fixes (`json_fixer_prompt`) if invalid
  - Returns `{ type: "vega_lite_spec", spec: <json string> }`

Tools must not capture a specific model at import time. Instead, they read `state.model_name` (set when sending a message) and look up the LLM via the registry in `llm/model.py`. This guarantees the assistant and tools use the same model for a thread.

## Streaming

`app/helpers/langgraph.py` exposes `stream_langgraph_events` used by `POST /chat/{thread_id}/message`.

Event format (SSE lines start with `data: `):
- `{ type: "chunk", content: string }` – token/text chunks from the assistant
- `{ type: "tool_result", content: any }` – tool outputs (including charts)
- `{ type: "end", full_response: string }` – final aggregation for convenience
- `{ type: "error", error: string }` – rare error case

Frontend maps these to components in `MessageComponents.tsx`:
- Text: markdown with GFM; shows streaming cursor and progress during generation
- Tool output: detects `{ type: "vega_lite_spec", spec }` and renders via `react‑vega`

## Connections and schema

`/connections` endpoints manage per‑user connections stored in Postgres. Secrets are encrypted with AES‑GCM using `MASTER_ENCRYPTION_KEY`.

On thread connection update (`POST /chat/{thread_id}/connection`):
- Server fetches the full record, decrypts password, builds an engine, introspects tables/columns, fetches up to 3 sample rows per table.
- The resulting markdown is stored in `db_schema` in the graph state for prompt grounding.

## Models and providers

`llm/model.py` uses LangChain `init_chat_model` and exposes a model registry:
- OSS via LM Studio: `openai/gpt-oss-20b`, `qwen/qwen3-8b` (enable with `LM_STUDIO_ENDPOINT`)
- Optional: `deepseek-chat` (enable with `DEEPSEEK_API_KEY`)

Selection is per‑thread and persisted on the thread record. Use the APIs:
- `GET /chat/{thread_id}/model` → `{ thread_id, model, models: { name: available } }`
- `POST /chat/{thread_id}/model` with `{ name }` to set. Aliases supported: `qwen` → `qwen3-8b`, `gpt_oss`/`gpt-oss` → `gpt-oss-20b`, `deepseek` → `deepseek-chat`.

If no model is set for a thread and no global fallback exists, the assistant will return a clear error prompting model selection.

## Extending

- Add a new tool: implement a `@tool` in `llm/tools.py` (or a factory), return `Command(update=...)` when you need to update state/messages.
- Add DB types: extend `DatabaseManager.get_user_connection_engine` to support new drivers.
- Persist state: swap `MemorySaver` for a persistent checkpointer.

## Testing

Basic route tests live in `backend/tests/`. Add unit tests for tools and DB helpers when changing behavior.

## Notes

- MinIO appears in compose but charts render from Vega‑Lite in the client; MinIO is not required for charts.
- CORS is `*` in dev; adjust `core/config.py` and FastAPI CORS settings for production.

