# Google ADK API Server - Key Endpoints & Usage

This file summarizes the most important endpoints and payloads for the Google ADK API server (adk api_server), based on the provided documentation.

## Key Endpoints

### Session & App Management
- `GET /list-apps`
  - Lists all available apps

- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}`
  - Get a specific session

- `POST /apps/{app_name}/users/{user_id}/sessions/{session_id}`
  - Create a session with a specific ID

- `GET /apps/{app_name}/users/{user_id}/sessions`
  - List all sessions for a user

- `POST /apps/{app_name}/users/{user_id}/sessions`
  - Create a new session (ID auto-generated)

### Artifact Management
- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}`
  - Load a specific artifact

- `DELETE /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}`
  - Delete a specific artifact

- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts`
  - List all artifact names for a session

### Agent Interaction
- `POST /run`
  - Run an agent (main chat/interaction endpoint) - **NOT USED IN CURRENT IMPLEMENTATION**
  - **Payload Example:**
    ```json
    {
      "app_name": "data_science",
      "user_id": "u_123",
      "session_id": "s_abc",
      "new_message": {
        "role": "user",
        "parts": [
          { "text": "What is the capital of France?" }
        ]
      }
    }
    ```

- `POST /run_sse` ⭐ **CURRENTLY USED ENDPOINT**
  - Run agent with Server-Sent Events (for streaming responses)
  - **Payload Example:**
    ```json
    {
      "app_name": "data_science",
      "user_id": "u_123",
      "session_id": "s_abc",
      "new_message": {
        "role": "user",
        "parts": [
          { "text": "What is the capital of France?" }
        ]
      },
      "streaming": true
    }
    ```
  - **Response Format:** Server-Sent Events (SSE) with JSON data chunks
  - **Sample Response Structure:**
    ```
    data: {"content":{"parts":[{"text":"I have access to the following tables..."}],"role":"model"},"partial":true}
    data: {"content":{"parts":[{"text":" and views:"}],"role":"model"},"partial":true}
    data: {"content":{"parts":[{"text":" Complete response content"}],"role":"model"},"partial":false}
    ```

## Current Implementation Details

### Frontend (React + TypeScript)
- **Location:** `frontend/src/`
- **Key Files:**
  - `App.tsx` - Main chat interface with SSE streaming support
  - `services/api.ts` - API service with `sendMessageStreaming()` method
  - `index.css` - Styling with streaming animations and indicators

### Backend (Google ADK Framework)
- **Location:** `backend/`
- **Server:** Started via `start_server.sh` using `adk api_server`
- **Port:** http://localhost:8000
- **Framework:** Google ADK (Agent Development Kit)

### SSE Implementation Features
- **Real-time Streaming:** Messages appear as they're generated
- **Visual Indicators:** Typing, streaming, and completion states
- **Error Handling:** Retry functionality and graceful error display
- **Audio Feedback:** Subtle notification sounds
- **Progress Tracking:** Character count and response timing
- **Timeout Protection:** 30-second request timeout

## Project Structure Overview

```
aigis-governance/
├── frontend/                          # React frontend application
│   ├── src/
│   │   ├── App.tsx                   # Main chat interface
│   │   ├── services/
│   │   │   └── api.ts                # API service with SSE support
│   │   ├── lib/
│   │   │   └── utils.ts              # Utility functions
│   │   ├── assets/                   # Static assets
│   │   ├── index.css                 # Global styles and animations
│   │   └── main.tsx                  # App entry point
│   ├── package.json                  # Frontend dependencies
│   ├── vite.config.ts                # Vite build configuration
│   └── tailwind.config.js            # Tailwind CSS configuration
├── backend/                           # Google ADK backend
│   ├── data_science/                 # Data science agent implementation
│   │   ├── agent.py                  # Main agent logic
│   │   ├── prompts.py                # Prompt templates
│   │   ├── tools.py                  # Agent tools
│   │   └── sub_agents/               # Specialized sub-agents
│   ├── start_server.sh               # Server startup script
│   ├── pyproject.toml                # Python dependencies
│   └── .venv/                        # Python virtual environment
├── docs/                             # Documentation
│   └── sample-sse-response           # Sample SSE response for reference
├── AGENTS.md                         # This file - API documentation
├── README.md                         # Project overview
└── SETUP.md                          # Setup instructions
```

## Development Workflow

### Starting the Application
1. **Backend:** Run `cd backend && ./start_server.sh`
2. **Frontend:** Run `cd frontend && npm run dev`

### Making Changes
- **Frontend Changes:** Edit files in `frontend/src/`, changes auto-reload
- **Backend Changes:** Restart the ADK server after changes
- **API Changes:** Update both frontend service and this documentation

### Testing SSE Functionality
- Send a message in the chat interface
- Watch for real-time streaming response
- Check browser console for SSE data parsing
- Verify timeout handling with long requests

## Key Implementation Notes

### SSE Data Parsing
- Frontend parses `data:` lines from SSE response
- Extracts `content.parts[].text` for display
- Handles `partial: true/false` for streaming state
- Processes `actions.artifactDelta` for additional data

### State Management
- Messages have `isStreaming` state for UI updates
- Streaming messages show typing → streaming → complete states
- Error handling includes retry functionality
- Connection status is monitored in real-time

### Performance Considerations
- SSE connection is properly closed after completion
- Timeout prevents hanging connections
- Smooth scrolling and animations for good UX
- Efficient message state updates

## Future Enhancements

### Potential Improvements
- **Connection Recovery:** Auto-reconnect on connection loss
- **Message Persistence:** Save chat history locally
- **Streaming Controls:** Pause/resume streaming
- **Advanced Analytics:** Response time tracking and optimization
- **Multi-language Support:** Internationalization for UI

### Monitoring & Debugging
- **SSE Connection Logs:** Detailed connection status logging
- **Performance Metrics:** Response time and throughput tracking
- **Error Analytics:** Error categorization and frequency analysis
- **User Experience Metrics:** Streaming success rates and user satisfaction

---

**Keep this file updated as the ADK API server and project structure evolve!**
