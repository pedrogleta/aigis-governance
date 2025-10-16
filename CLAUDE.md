# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aigis Governance is an AI data assistant that connects to databases and answers questions in natural language. It writes SQL queries, executes them against user-selected connections, and returns answers with optional Vega-Lite visualizations. The system uses a React frontend with a FastAPI backend powered by LangGraph.

## Architecture

### Backend (Python/FastAPI)
- **Main entry**: `backend/app/main.py` - FastAPI app setup, CORS, routers
- **Authentication**: `backend/app/routes/auth.py` - JWT-based auth, user management
- **Chat system**: `backend/app/routes/chat.py` - Thread management, SSE streaming
- **Database connections**: `backend/app/routes/connections.py` - User DB connection CRUD
- **LangGraph integration**: `backend/app/helpers/langgraph.py` - SSE streaming adapter
- **Agent logic**: `backend/llm/agent.py` - LangGraph state graph with tools
- **LLM models**: `backend/llm/model.py` - Model initialization and tool binding
- **Tools**: `backend/llm/tools.py` - `ask_database`, `ask_analyst` implementations
- **Database utilities**: `backend/app/helpers/user_connections.py` - Schema markdown generation, SQL execution
- **Core modules**: `backend/core/` - Configuration, database engines, encryption (AES-GCM)

### Frontend (React + Vite + Tailwind)
- **API layer**: `frontend/src/services/api.ts` - HTTP client and SSE handling
- **Chat interface**: `frontend/src/components/ChatUI.tsx` - Main chat flow and streaming
- **Model selection**: `frontend/src/components/ModelSidebar.tsx` - Per-thread model management
- **Message rendering**: `frontend/src/components/MessageComponents.tsx` - Text, tool results, and Vega-Lite charts
- **Pages**: `frontend/src/pages/` - Login, Register, Chat views

## Development Commands

### Docker Compose (Recommended)
```bash
# Start all services (includes Postgres, backend, frontend)
docker compose up --build

# Stop services
docker compose down
```

### Backend Development
```bash
cd backend
uv venv && uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest

# Lint and format
uv run ruff check
uv run ruff format
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Key Concepts

### Agent Flow
1. **ask_database** tool: Converts natural language to SQL, executes against user's selected connection
2. **ask_analyst** tool: Converts tabular results to Vega-Lite chart specifications
3. Tools are executed in sequence, with streaming responses via Server-Sent Events

### Database Connections
- Users can connect to Postgres or SQLite databases
- Connection passwords are encrypted using AES-GCM with `MASTER_ENCRYPTION_KEY`
- Schema information is dynamically fetched and provided to the LLM as markdown

### Model Management
- Per-thread model selection (each chat can use a different LLM)
- Supports LM Studio (OpenAI-compatible), DeepSeek, Google Gemini, OpenAI
- Model availability determined by environment variables

## Environment Setup

### Required Variables
- `SECRET_KEY` - JWT signing secret
- `MASTER_ENCRYPTION_KEY` - AES encryption key for connection passwords
- `POSTGRES_*` variables for app database

### Optional LLM Providers
- `LM_STUDIO_ENDPOINT` - Local OpenAI-compatible endpoint
- `DEEPSEEK_API_KEY` - DeepSeek API access
- `GOOGLE_API_KEY` - Google Gemini access
- `OPENAI_API_KEY` - OpenAI API access

## Testing

- Backend tests located in `backend/tests/`
- Run with `uv run pytest` from backend directory
- Includes tests for auth and chat routers

## Database Migrations

- Uses Alembic for schema migrations
- Migration files in `backend/alembic/versions/`
- Apply migrations: `uv run alembic upgrade head`
- Auto-applied in Docker containers at startup