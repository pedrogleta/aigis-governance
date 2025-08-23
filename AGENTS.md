# Aigis Backend - Key Endpoints & Usage (FastAPI)

This file documents the current backend API and important endpoints for the custom FastAPI backend (replaces the previous Google ADK api_server). It includes auth, chat (SSE streaming), and database notes.

## Key Endpoints

### Thread & Chat Endpoints
- `POST /chat/thread` - Create a new chat thread. Returns `{"thread_id": "<uuid>"}`.

- `POST /chat/{thread_id}/message` - Send a message to a thread. Accepts a JSON body `{ "text": "..." }` and returns an SSE stream (media type `text/event-stream`) with incremental agent events.

- `GET /chat/{thread_id}` - Get the message history and metadata for a thread.

- `GET /chat/{thread_id}/state` - Retrieve the current agent/graph state for a thread (e.g., DB schema info) and thread status.

### Artifact Management
- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}`
  - Load a specific artifact

- `DELETE /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}`
  - Delete a specific artifact

- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts`
  - List all artifact names for a session

### Agent Interaction
The previous ADK endpoints (`/run`, `/run_sse`, etc.) are no longer used. The FastAPI chat routes above provide thread-based interaction and SSE streaming.
  - **Sample Response Structure:**
    ```
    data: {"content":{"parts":[{"text":"I have access to the following tables..."}],"role":"model"},"partial":true}
    data: {"content":{"parts":[{"text":" and views:"}],"role":"model"},"partial":true}
    data: {"content":{"parts":[{"text":" Complete response content"}],"role":"model"},"partial":false}
    ```
  - **Message Types Supported:**
    - **Text Messages:** Streaming text content with `partial: true/false` flags
    - **Function Calls:** Agent tool invocations with function name, arguments, and ID
    - **Function Responses:** Tool execution results with function name and response data
    - **Invocation Metadata:** Session tracking with `invocationId`, `author`, and `actions`


### Frontend (React + TypeScript)
- **Location:** `frontend/src/`
- **Key Files:**
  - `App.tsx` - Main chat interface with SSE streaming support
  - `services/api.ts` - API service with `sendMessageStreaming()` method and Zod validation
  - `components/MessageComponents.tsx` - Message type-specific rendering components
  - `index.css` - Styling with streaming animations and indicators

### Backend (FastAPI)
- **Location:** `backend/` (Python FastAPI app under `backend/app`)
- **Server:** Run with `uvicorn app.main:app --reload` (development)
- **Purpose:** Authentication, chat/streaming, database connections (Postgres primary, SQLite per-user DBs)

There is no longer a separate `agent-gateway/` ADK server in the canonical runtime for this repository; agent logic is orchestrated inside the FastAPI app and associated modules.


### SSE Implementation Features
- **Real-time Streaming:** Chat responses are streamed as Server-Sent Events from `/chat/{thread_id}/message`.
- **Multi-message Support:** The stream can include function/tool calls and tool responses as separate events before the final text content.
- **Message Type Differentiation:** Frontend distinguishes between function calls, function responses, and text parts.

## Project Structure Overview

```
aigis-governance/
├── frontend/                          # React frontend application
│   └── src/
├── backend/                           # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── routes/
│   │   │   ├── auth.py               # Auth endpoints
│   │   │   └── chat.py               # Chat endpoints + SSE
│   └── core/
│       └── database.py                # Database manager (Postgres + SQLite)
├── docs/
├── AGENTS.md                          # This file - API documentation
├── README.md                          # Project overview
└── SETUP.md                           # Setup instructions
```

## Development Workflow

### Starting the Application
This project now uses PM2 for process management. To start the application:

1. **Install PM2 globally** (if not already installed):
   ```bash
   npm install -g pm2
   ```

2. **Start the setup and services**:
   ```bash
   npm run setup
   ```
   This starts the core services using PM2 configuration files.

3. **Start the main application**:
   ```bash
   npm run dev
   ```
   This starts the main application using PM2.

4. **Monitor processes**:
   ```bash
   npm run list      # List all running PM2 processes
   npm run logs      # View logs from all processes
   ```

### PM2 Process Management
The project uses several PM2 configuration files:
- `setup.config.js` - Core setup processes
- `services.config.js` - Background services
- `app.config.js` - Main application

**Useful PM2 commands:**
```bash
npm run stop      # Stop the main application
npm run cleanup   # Stop and remove all PM2 processes
pm2 restart all   # Restart all processes
pm2 reload all    # Zero-downtime reload of all processes
```

### Making Changes
- **Frontend Changes:** Edit files in `frontend/src/`, changes auto-reload
- **Agent Gateway Changes:** Restart the PM2 process after changes: `pm2 restart <process-name>` or `npm run dev`
- **Backend Changes:** Restart the PM2 process after changes: `pm2 restart <process-name>` or `npm run setup`
- **API Changes:** Update both frontend service and this documentation
- **PM2 Configuration Changes:** After modifying PM2 config files, restart the affected processes

### Testing SSE Functionality
- **Basic Streaming:** Send a message in the chat interface and watch for real-time streaming response
- **Function Call Testing:** Ask questions that trigger database queries (e.g., "How many people are over 30?")
- **Message Type Verification:** Check that all three message types appear in sequence:
  - Blue function call boxes
  - Green function response boxes  
  - Streaming text with real-time updates
- **Console Monitoring:** Check browser console for SSE data parsing and message processing logs
- **Timeout Testing:** Verify timeout handling with long requests
- **Multi-message Streams:** Ensure all events in a single stream are displayed correctly

## Message Types & Data Structures

### Backend SSE Event Types
The backend sends various types of events through the SSE stream, each with different structures:

#### 1. **Text Messages** (Streaming Content)
```json
{
  "content": {
    "parts": [{"text": "Streaming text content..."}],
    "role": "model"
  },
  "partial": true,
  "invocationId": "e-12345678-1234-1234-1234-123456789abc",
  "author": "db_ds_multiagent",
  "actions": {"stateDelta": {}, "artifactDelta": {}, "requestedAuthConfigs": {}},
  "id": "unique-message-id",
  "timestamp": 1755224903.126858
}
```

#### 2. **Function Call Messages** (Tool Invocations)
```json
{
  "content": {
    "parts": [{
      "functionCall": {
        "id": "call_123",
        "name": "call_db_agent",
        "args": {"question": "How many people are over 30?"}
      }
    }],
    "role": "model"
  },
  "partial": false,
  "invocationId": "e-12345678-1234-1234-1234-123456789abc",
  "author": "db_ds_multiagent"
}
```

#### 3. **Function Response Messages** (Tool Results)
```json
{
  "content": {
    "parts": [{
      "functionResponse": {
        "id": "call_123",
        "name": "call_db_agent",
        "response": {
          "result": "There are 2 people over 30 years old."
        }
      }
    }],
    "role": "user"
  },
  "invocationId": "e-12345678-1234-1234-1234-123456789abc",
  "author": "db_ds_multiagent"
}
```

#### 4. **Final Complete Messages** (End of Stream)
```json
{
  "content": {
    "parts": [{"text": "Complete final message with all content..."}],
    "role": "model"
  },
  "partial": false,
  "invocationId": "e-12345678-1234-1234-1234-123456789abc",
  "author": "db_ds_multiagent"
}
```

### Frontend Message Components
The frontend renders different message types using specialized React components:

#### **FunctionCallComponent**
- **Visual Style:** Blue-themed box with function icon
- **Content Display:** Function name, arguments, and ID
- **Use Case:** Shows when the agent is calling a tool/function

#### **FunctionResponseComponent**  
- **Visual Style:** Green-themed box with checkmark icon
- **Content Display:** Function name and execution results
- **Use Case:** Shows the output/results of tool execution

#### **TextComponent**
- **Visual Style:** Standard text with markdown support
- **Content Display:** Streaming text with real-time updates
- **Use Case:** Displays the agent's natural language responses

### Message Flow Example
A typical conversation flow might include:
1. **User Message:** "How many people are over 30?"
2. **Function Call:** Blue box showing `call_db_agent` being invoked
3. **Function Response:** Green box showing database query results
4. **Text Response:** Streaming explanation of the results
5. **Stream Complete:** Final complete message (not displayed to avoid duplication)

## Key Implementation Notes

### SSE Data Parsing & Message Types
- **Zod Schema Validation:** Runtime validation of all incoming SSE messages using TypeScript-first schemas
- **Schema Structure:** 
  - `FunctionCallSchema`: Validates function call structure with `id`, `args`, and `name`
  - `FunctionResponseSchema`: Validates function response with `id`, `name`, and `response.result`
  - `PartSchema`: Union type for text, functionCall, or functionResponse parts
  - `ContentSchema`: Validates content structure with parts array and role
  - `SSEMessageSchema`: Main schema for all SSE messages
- **Message Type Detection:** Automatically identifies and routes different message types
- **Text Messages:** Extracts and displays `content.parts[].text` with streaming support
- **Function Calls:** Processes `content.parts[].functionCall` with name, args, and ID
- **Function Responses:** Handles `content.parts[].functionResponse` with results
- **Streaming Control:** Manages `partial: true/false` flags for real-time updates
- **Metadata Processing:** Handles `invocationId`, `author`, and `actions` for session tracking
- **Duplicate Prevention:** Avoids displaying final complete messages that duplicate streaming content

### State Management & Message Rendering
- **Message States:** Messages have `isStreaming` state for UI updates
- **Streaming Flow:** Shows typing → streaming → complete states
- **Message Components:** Different visual representations for each message type:
  - **FunctionCallComponent:** Blue-themed boxes showing function name and arguments
  - **FunctionResponseComponent:** Green-themed boxes displaying function results
  - **TextComponent:** Standard text with markdown support and streaming indicators
- **Multi-message Support:** Displays all message types in sequence within a single stream
- **Error Handling:** Includes retry functionality and graceful error display
- **Connection Monitoring:** Real-time connection status tracking

### Performance Considerations
- SSE connection is properly closed after completion
- Timeout prevents hanging connections
- Smooth scrolling and animations for good UX
- Efficient message state updates

## Future Enhancements

- Connection recovery and auto-reconnect on the frontend
- Message persistence and server-side history storage (currently in-memory threads)
- Per-thread persistence backed by PostgreSQL
- Better instrumentation and observability for SSE streams

---

Keep this file updated as the backend and project structure evolve.
