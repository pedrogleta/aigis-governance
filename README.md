# Aigis Governance

An AI Agent system that allows users to connect to datasets and ask natural language questions about data, including creating plots for data visualization.

## Features

- 🤖 **AI Agents** - Multi-agent system for data analysis and visualization
- 🔍 **Natural Language Queries** - Ask questions about your data in plain English
- 📊 **Data Visualization** - Generate plots and charts automatically
- 🗄️ **BigQuery Integration** - Direct connection to Google BigQuery datasets
- 💻 **Modern Web Interface** - React-based chat interface with dark/green theme

## Architecture

The system consists of:
- **Backend**: Python-based FastAPI backend
- **Frontend**: React + Vite chat interface for user interaction
- **Database**: BigQuery integration for data access and analysis

## Setup and Run

### Prerequisites

### Running the application (locally)

The backend is a FastAPI app and the frontend uses Vite. During development run them separately from the project root:

Backend (from `backend/`):
```bash
# create and activate a uv-managed virtual environment and sync dependencies
cd backend
uv venv
uv sync
# run the server inside the uv venv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (from `frontend/`):
```bash
cd frontend
npm install
npm run dev
```

### Running with Docker Compose

A docker-compose setup is provided to run the full stack (Postgres, MinIO, backend, frontend). From the project root:

```bash
docker compose up --build
```

This will expose:
- Backend: http://localhost:8000
- Frontend (Vite dev server): http://localhost:3000



## Backend Development

The project uses a custom FastAPI backend. The backend provides authentication, chat endpoints (SSE streaming), and connections to both PostgreSQL (primary) and user-created SQLite databases.

Key backend locations:

- `backend/app/main.py` - FastAPI application entrypoint
- `backend/app/routes/auth.py` - Authentication endpoints (register, login, user management)
- `backend/app/routes/chat.py` - Chat/thread endpoints and SSE streaming
- `backend/core/database.py` - Database manager and FastAPI DB dependencies (Postgres + SQLite)

### Backend Commands (development)

Use one of the following from the `backend/` directory to run the server for development:

```bash
# Run with uvicorn (module path)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run via python (calls uvicorn inside main)
python -m backend.app.main
```

Note: The backend runs with Uvicorn and the frontend uses Vite during development. Docker Compose will run both services so you can open the frontend at the address above.
```

## Backend Development

The Python backend includes:

- **AI Agents**: Multi-agent system for data analysis
- **BigQuery Tools**: Database connection and query tools
- **Data Science Tools**: Analysis and visualization capabilities

### Backend Commands

Use Uvicorn for local development:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

The backend exposes REST and SSE endpoints for chat and agent orchestration. Refer to `backend/app/routes` for details.

## Configuration

### Environment Variables

- `ROOT_AGENT_MODEL` - AI model to use (default: gemini-2.5-pro)
- `CODE_INTERPRETER_EXTENSION_NAME` - Extension for code execution

### Frontend Configuration

Edit `frontend/config.ts` to customize:
- API base URL
- Feature flags
- UI settings

## Troubleshooting

### Common Issues

1. **BigQuery Connection Errors**
   - Ensure your Google Cloud credentials (service account or ADC) are available to the backend when using BigQuery
   - Check your project permissions

2. **Frontend Build Errors**
   - Make sure all dependencies are installed: `npm install`
   - Check Tailwind CSS configuration

3. **API Connection Issues**
   - Verify backend is running on correct port
   - Check CORS configuration

### Getting Help

- Check the console for error messages
- Verify your backend is running and accessible
- Ensure all environment variables are set correctly

## Hint

If your setup uses BigQuery or other cloud services, place any service account JSON credentials in `backend/credentials.json` (do not commit this file). Use environment variables or a `.env` file for secrets and configuration.

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. 