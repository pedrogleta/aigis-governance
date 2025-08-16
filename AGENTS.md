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
  - **Response Format:** Server-Sent Events (SSE) with JSON data chunks containing various message types
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

## Current Implementation Details

### Frontend (React + TypeScript)
- **Location:** `frontend/src/`
- **Key Files:**
  - `App.tsx` - Main chat interface with SSE streaming support
  - `services/api.ts` - API service with `sendMessageStreaming()` method and Zod validation
  - `components/MessageComponents.tsx` - Message type-specific rendering components
  - `index.css` - Styling with streaming animations and indicators

### Agent Gateway (Google ADK Framework)
- **Location:** `agent-gateway/`
- **Server:** Started via `start_gateway.sh` using `adk api_server`
- **Port:** http://localhost:8000
- **Framework:** Google ADK (Agent Development Kit)
- **Purpose:** Handles all agent interactions, session management, and artifact operations

### Backend (File Management Microservice)
- **Location:** `backend/`
- **Purpose:** General backend services including file storage and retrieval
- **Key Functionality:** MinIO file management operations
- **Architecture:** Microservice architecture separate from agent functionality

### SSE Implementation Features
- **Real-time Streaming:** Messages appear as they're generated
- **Multi-message Support:** Displays function calls, function responses, and text in sequence
- **Message Type Differentiation:** Visual distinction between different message types
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
│   │   │   └── api.ts                # API service with SSE support and Zod validation
│   │   ├── components/
│   │   │   └── MessageComponents.tsx # Message type-specific rendering components
│   │   ├── lib/
│   │   │   └── utils.ts              # Utility functions
│   │   ├── assets/                   # Static assets
│   │   ├── index.css                 # Global styles and animations
│   │   └── main.tsx                  # App entry point
│   ├── package.json                  # Frontend dependencies
│   ├── vite.config.ts                # Vite build configuration
│   └── tailwind.config.js            # Tailwind CSS configuration
├── agent-gateway/                     # Google ADK agent gateway
│   ├── data_science/                 # Data science agent implementation
│   │   ├── agent.py                  # Main agent logic
│   │   ├── prompts.py                # Prompt templates
│   │   ├── tools.py                  # Agent tools
│   │   └── sub_agents/               # Specialized sub-agents
│   ├── start_gateway.sh              # Gateway startup script
│   ├── pyproject.toml                # Python dependencies
│   └── .venv/                        # Python virtual environment
├── backend/                           # File management microservice
│   ├── [file management services]    # MinIO operations and general backend functionality
│   └── [microservice configuration]  # Service configuration and setup
├── docs/                             # Documentation
│   └── sample-sse-response           # Sample SSE response for reference
├── AGENTS.md                         # This file - API documentation
├── README.md                         # Project overview
└── SETUP.md                          # Setup instructions
```

## Development Workflow

### Starting the Application
1. **Agent Gateway:** Run `cd agent-gateway && ./start_gateway.sh`
2. **Backend:** Start the file management microservice (specific startup command depends on implementation)
3. **Frontend:** Run `cd frontend && npm run dev`

### Making Changes
- **Frontend Changes:** Edit files in `frontend/src/`, changes auto-reload
- **Agent Gateway Changes:** Restart the ADK server after changes
- **Backend Changes:** Restart the microservice after changes
- **API Changes:** Update both frontend service and this documentation

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

### Potential Improvements
- **Connection Recovery:** Auto-reconnect on connection loss
- **Message Persistence:** Save chat history locally
- **Streaming Controls:** Pause/resume streaming
- **Advanced Analytics:** Response time tracking and optimization
- **Multi-language Support:** Internationalization for UI
- **Message Type Filtering:** User preferences for which message types to display
- **Custom Message Components:** User-defined styling for different message types
- **Message Search:** Search through chat history by message type or content

### Monitoring & Debugging
- **SSE Connection Logs:** Detailed connection status logging
- **Message Processing Logs:** Console logging for each message type processed
- **Performance Metrics:** Response time and throughput tracking
- **Error Analytics:** Error categorization and frequency analysis
- **User Experience Metrics:** Streaming success rates and user satisfaction
- **Message Type Analytics:** Tracking of function calls, responses, and text message frequencies

---

**Keep this file updated as the ADK API server and project structure evolve!**
