# AIGIS Governance - Frontend to Backend Connection

This guide explains how to connect the React frontend to the Google ADK API server.

## Quick Start

### 1. Start the Backend (ADK API Server)

```bash
cd backend
./start_server.sh
```

This will:
- Activate the Python virtual environment
- Install dependencies if needed
- Start the ADK API server on port 8000
- The server will be OpenAI API compatible

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will automatically connect to `http://localhost:8000`.

## What Changed

### Frontend Updates
- **API Service**: Updated to use ADK API endpoints (`/run`, `/list-apps`, etc.)
- **Port Configuration**: Set to connect to port 8000 (ADK server)
- **Response Handling**: Updated to parse ADK API responses
- **Session Management**: Automatic session creation and management

### Backend Integration
- **ADK Framework**: Uses Google's ADK for AI agents
- **Custom API**: Server exposes ADK-specific endpoints for chat and session management
- **Port 8000**: Server runs on the configured port

## API Endpoints

The ADK server provides these endpoints:

- `POST /run` - Main chat endpoint for running agents
- `GET /list-apps` - List available applications
- `POST /apps/{app_name}/users/{user_id}/sessions` - Create sessions
- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}` - Get session

## Troubleshooting

### Backend Issues
- Ensure you have Python 3.12+ installed
- Check that `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Verify ADK is available: `adk --version`

### Frontend Issues
- Check browser console for API errors
- Verify backend is running on port 8000
- Check network tab for failed requests

### Connection Issues
- Ensure both frontend and backend are running
- Check firewall settings
- Verify port 8000 is not blocked

## Development



### Environment Variables
Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEV_MODE=true
```

## Architecture

```
Frontend (React) ←→ ADK API Server (Port 8000) ←→ AI Agents
     ↓                    ↓                        ↓
  Chat UI           ADK API Endpoints        BigQuery Tools
  Visualizations    Session Management       Data Analysis
  Code Display      Agent Execution          Plot Generation
```

The system now provides a seamless integration between your React frontend and the powerful Google ADK AI agent framework.
