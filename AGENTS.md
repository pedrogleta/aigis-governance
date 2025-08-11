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
  - Run an agent (main chat/interaction endpoint)
  - **Payload Example:**
    ```json
    {
      "app_name": "my_sample_agent",
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

- `POST /run_sse`
  - Run agent with Server-Sent Events (for streaming responses)

## Notes
- There is no OpenAI-compatible endpoint (e.g., `/v1/chat/completions`).
- The main endpoint for sending chat messages is `POST /run`.
- Sessions and artifacts are managed via the `/apps/.../sessions/...` endpoints.
- You must specify `app_name`, `user_id`, and `session_id` for most operations.
- The message payload uses a `parts` array, each with a `text` field.

---

**Keep this file updated if the ADK API server documentation changes!**
