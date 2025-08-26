# Aigis Backend (FastAPI)

FastAPI application providing authentication, chat threads with SSE streaming, and per‑user database connections. Agent orchestration is implemented with LangGraph and simple tools for SQL and Vega‑Lite.

## Key entry points

- App: `app/main.py` (imports routers for auth, chat, connections)
- Health: `GET /health` (also checks Postgres connectivity)
- Routers: `app/routes/{auth,chat,connections}.py`
- Config: `core/config.py` (Pydantic settings from `.env`)
- DB: `core/database.py` (Postgres engine + dynamic user connection engines)
- Alembic: `alembic/` (migrations configured to use `settings.postgres_url`)

## Setup (local)

```bash
uv venv && uv sync

# Create .env in backend/ (example)
cat > .env << 'EOF'
SECRET_KEY=change-me
MASTER_ENCRYPTION_KEY=change-me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=aigis_governance
LM_STUDIO_ENDPOINT=http://0.0.0.0:1234/v1
ENABLE_OPIK_TRACER=0
EOF

# Run migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running with Docker

The root `docker-compose.yml` builds this service and runs Alembic migrations on startup via `entrypoint.sh`.

## Endpoints (summary)

- Auth: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/change-password`, admin user management
- Connections: `/connections/` (CRUD), `/connections/{id}/test`
- Chat: `/chat/thread`, `/chat/{thread_id}/message` (SSE), `/chat/{thread_id}`, `/chat/{thread_id}/state`, `/chat/{thread_id}/connection`
- Health: `/health`

## Notes

- JWT signing uses `SECRET_KEY` and algorithm from settings (`HS256` by default)
- User connection passwords are encrypted with AES‑GCM using `MASTER_ENCRYPTION_KEY`
- Models and tools are configured in `llm/` and can be adjusted to your provider

