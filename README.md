# Aigis Governance

An AI data assistant you can connect to your own databases. Ask questions in natural language; the system writes SQL, executes it against your selected connection, and returns answers with optional Vega‑Lite visualizations. A modern React chat UI streams responses from a FastAPI backend powered by LangGraph.

## Highlights

- Chat with your data using natural language
- Tool-using agent: generates SQL then optional charts (Vega‑Lite)
- Streaming responses over SSE
- Authentication and per‑user database connections (Postgres/SQLite now; extensible)
- Postgres for app data (users, threads, user connections)
- Simple local OSS model setup via LM Studio or bring your own provider
 - Per‑thread LLM model selection (each chat thread can choose its own model)

## Architecture at a glance

- Backend (Python/FastAPI):
   - Auth (JWT), connections CRUD and testing
   - Chat threads + Server‑Sent Events streaming
   - LangGraph agent with tools defined in code
   - Postgres as the primary database; dynamic engines to user‑provided DBs
   - Per‑thread model selection APIs
- Frontend (React + Vite + Tailwind):
   - Chat UI with live streaming
   - Manage and select your DB connections
   - Renders Vega‑Lite specs client‑side (no image service required)
- Docker Compose: spins up Postgres, backend, frontend (MinIO is included but optional and not required for charts which render client‑side)

Code map (selected):

- Backend
   - `backend/app/main.py` – FastAPI app, CORS, routers, `/health`
   - `backend/app/routes/auth.py` – register/login/me, profile, admin users
   - `backend/app/routes/chat.py` – create thread, send message (SSE), thread state
   - Per‑thread model APIs: `GET /chat/{thread_id}/model`, `POST /chat/{thread_id}/model`
   - `backend/app/routes/connections.py` – per‑user DB connections CRUD + `/test`
   - `backend/app/helpers/langgraph.py` – SSE streaming adapter
   - `backend/app/helpers/user_connections.py` – build db schema markdown, run SQL
   - `backend/llm/agent.py` – LangGraph state graph + tools node
   - `backend/llm/model.py` – model initialization and tool binding
   - `backend/llm/tools.py` – `ask_database`, `ask_analyst` tool implementations
   - `backend/llm/prompts.py` – system, SQL, and Vega‑Lite prompts
   - `backend/core/{config,database,types,crypto}.py` – settings, engines, state, AES‑GCM
   - `backend/models/*`, `backend/crud/*`, `backend/schemas/*` – users, threads, connections
- Frontend
   - `frontend/src/services/api.ts` – threads, SSE, auth, connections API
   - `frontend/src/components/ChatUI.tsx` – chat flow and streaming rendering
   - `frontend/src/components/ModelSidebar.tsx` – per‑thread model selection UI
   - `frontend/src/components/MessageComponents.tsx` – text/tool/plot renderers
   - `frontend/src/pages/*` – Login, Register, Chat

## How it works

1) Connect a database
- Create a connection under Connections: Postgres or SQLite (file path)
- Passwords are stored encrypted (AES‑GCM) using a `MASTER_ENCRYPTION_KEY`

2) Ask a question
- Frontend sends your message to `POST /chat/{thread_id}/message` and opens an SSE stream
- The agent prompt includes a markdown snapshot of your DB schema (fetched live)

3) Agent flow (LangGraph)
- Tool order: `ask_database` → optional `ask_analyst`
- `ask_database` uses an LLM to write raw SQL from your request and schema, then executes it against your selected connection
- `ask_analyst` turns tabular results into a Vega‑Lite JSON spec for charting
- Backend streams tokens as `chunk` events and tool outputs as `tool_result`
- Frontend renders markdown and charts (via react‑vega)

## Quickstart

### Option A: Docker Compose

Prereqs: Docker + Docker Compose

1) From repo root:
```bash
docker compose up --build
```

2) Open:
- Backend API: http://localhost:8000
- Frontend (Vite dev server): http://localhost:3000

Environment used by Compose (defaults shown in `docker-compose.yml`):
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `LM_STUDIO_ENDPOINT` (default `http://0.0.0.0:1234`)
 - `DEEPSEEK_API_KEY` (optional; enables DeepSeek provider)
 - `GOOGLE_API_KEY` (optional; enables Gemini models)
 - `OPENAI_API_KEY` (optional; enables OpenAI models)
- `ENABLE_OPIK_TRACER` (0/1)
- For secure password storage in connections, set in backend container env or `.env` in `backend/`: `MASTER_ENCRYPTION_KEY` and `SECRET_KEY`

The backend container runs Alembic migrations automatically at startup.

### Option B: Local development

Backend
```bash
cd backend
uv venv && uv sync
# create .env with at least:
#   SECRET_KEY=change-me
#   MASTER_ENCRYPTION_KEY=change-me
#   POSTGRES_HOST=localhost
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD=postgres
#   POSTGRES_DB=aigis_governance
# optional model providers:
#   LM_STUDIO_ENDPOINT=http://0.0.0.0:1234/v1
#   DEEPSEEK_API_KEY=your-deepseek-key
#   GOOGLE_API_KEY=your-google-key
#   OPENAI_API_KEY=your-openai-key
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd frontend
npm install
npm run dev
```

## API overview

Auth (`/auth`)
- `POST /register` – email, username, password
- `POST /login` – returns JWT; use `Authorization: Bearer <token>`
- `GET /me` – current user; `PUT /me` – update profile; `POST /change-password`
- Admin: `GET /users`, `GET /users/{id}`, `DELETE /users/{id}`

Connections (`/connections`)
- `GET /` list, `POST /` create, `GET/PUT/DELETE /{id}`, `POST /{id}/test`
- Supports db_type: `postgres` or `sqlite` (for SQLite, set host to file path)

Chat (`/chat`)
- `POST /thread` – create a thread → `{ "thread_id": "uuid" }`
- `POST /{thread_id}/message` – body `{ text, user_connection_id? }` streams SSE
   - Events: `{type:"chunk",content:string}`, `{type:"tool_result",content:any}`, `{type:"end",full_response:string}`
- `GET /{thread_id}` – persisted messages
- `GET /{thread_id}/state` – graph state snapshot (e.g., `db_schema`)
- `POST /{thread_id}/connection` – set active user_connection for this thread
- `GET /{thread_id}/model` – get the current model for this thread and availability map
- `POST /{thread_id}/model` – set the model for this thread; body `{ name: "qwen3-8b" | "gpt-oss-20b" | "deepseek-chat" }` (aliases like `qwen`, `gpt_oss`, `deepseek` accepted)

Health
- `GET /health` – server and Postgres connectivity

## Models and providers

Supported models are initialized in `backend/llm/model.py` using LangChain’s `init_chat_model`:
- OSS via LM Studio: `openai/gpt-oss-20b`, `qwen/qwen3-8b` (enable by setting `LM_STUDIO_ENDPOINT`)
- DeepSeek: `deepseek-chat` (enable by setting `DEEPSEEK_API_KEY`)
- Google: `gemini-2.5-pro` (enable by setting `GOOGLE_API_KEY`)
- OpenAI: `gpt-5` (enable by setting `OPENAI_API_KEY`)

Selection is per‑thread: each chat thread can choose its own model via the UI (Model button near the header) or APIs listed above. Availability is derived from environment variables and returned in the `GET /chat/{thread_id}/model` response.

Notes:
- A thread starts with no model selected; the UI shows a red “No model selected” indicator until you pick one.
- Tools and the assistant resolve the model per‑thread at runtime. If no model is set, the assistant will return an error prompting you to select one.
- Aliases are accepted for convenience: `qwen` → `qwen3-8b`, `gpt_oss`/`gpt-oss` → `gpt-oss-20b`, `deepseek` → `deepseek-chat`, `gemini`/`gemini-pro` → `gemini-2.5-pro`, `gpt5` → `gpt-5`.

## Agent and tools

- Graph: `backend/llm/agent.py` (LangGraph with in‑memory checkpointer)
- State: `AigisState` includes `messages`, `model_name`, `db_schema`, `connection`, `sql_result`
- Tools:
   - `ask_database(query)` – LLM→SQL, executes via SQLAlchemy, returns rows/count
   - `ask_analyst(query)` – returns `{ type: "vega_lite_spec", spec: <JSON> }`
- Prompts in `backend/llm/prompts.py` enforce tool ordering and output formats

## Security notes

- JWT `SECRET_KEY` and AES‑GCM `MASTER_ENCRYPTION_KEY` must be set
- Connection passwords are stored encrypted (iv + ciphertext) in Postgres

## Troubleshooting

- 401/403 from API: ensure you’re sending `Authorization: Bearer <token>`
- Chat SSE doesn’t stream: check browser devtools network tab and backend logs
- “connection not found” in responses: select a connection in the UI first
- SQL errors come back as tool results; the agent will surface a friendly message
- Frontend 3000 → Backend 8000: CORS is enabled to `*` by default in dev

## License

No explicit license file has been provided in this repository. Consult the repository owner if you need usage terms.