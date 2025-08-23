# Aigis Governance

An AI Agent system that allows users to connect to BigQuery datasets and ask natural language questions about data, including creating plots for data visualization.

## Features

- 🤖 **AI Agents** - Multi-agent system for data analysis and visualization
- 🔍 **Natural Language Queries** - Ask questions about your data in plain English
- 📊 **Data Visualization** - Generate plots and charts automatically
- 🗄️ **BigQuery Integration** - Direct connection to Google BigQuery datasets
- 💻 **Modern Web Interface** - React-based chat interface with dark/green theme

## Architecture

The system consists of:
- **Backend**: Python-based AI agents using Google's ADK framework
- **Frontend**: React + Vite chat interface for user interaction
- **Database**: BigQuery integration for data access and analysis

## Setup and Run

### Prerequisites

Before running the project, make sure you are authenticated with Google Cloud and have access to Vertex AI:

1. **Install PM2 globally**  
   This project uses PM2 for process management. Install it globally:
   ```bash
   npm install -g pm2
   ```

2. **Authenticate with Google Cloud CLI**  
   Make sure you have the [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed.  
   Run the following command and follow the prompts to log in:
   ```
   gcloud auth login
   ```

3. **Set your default project**  
   Replace `<YOUR_PROJECT_ID>` with your Google Cloud project ID:
   ```
   gcloud config set project <YOUR_PROJECT_ID>
   ```

4. **Use a service account for credentials (recommended)**  
    Instead of using Application Default Credentials, create a Google Cloud service account with the following roles:

    - Vertex AI Service Agent (roles/aiplatform.serviceAgent)
    - BigQuery Data Viewer (roles/bigquery.dataViewer)

    Example commands (replace <YOUR_PROJECT_ID> and `aigis-agent` as needed):

    ```bash
    # Create the service account
    gcloud iam service-accounts create aigis-agent --display-name="Aigis Service Account"

    # Grant roles to the service account
    gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
       --member="serviceAccount:aigis-agent@<YOUR_PROJECT_ID>.iam.gserviceaccount.com" \
       --role="roles/aiplatform.serviceAgent"

    gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
       --member="serviceAccount:aigis-agent@<YOUR_PROJECT_ID>.iam.gserviceaccount.com" \
       --role="roles/bigquery.dataViewer"

    # Create a JSON key and save it directly into the backend directory
    gcloud iam service-accounts keys create backend/credentials.json \
       --iam-account=aigis-agent@<YOUR_PROJECT_ID>.iam.gserviceaccount.com
    ```

    The command above will create a JSON key and save it as `backend/credentials.json`. Place the service-account JSON key in the `backend/` directory named `credentials.json` (this will replace the example file `backend/credentials.example.json` if present).

    Important: the JSON key contains sensitive credentials. Do not commit `backend/credentials.json` to source control (add it to `.gitignore` if needed).

    If you prefer to use Application Default Credentials for quick testing, you can still run:
    ```bash
    gcloud auth application-default login
    ```

### Running the Application

This project uses PM2 for process management. Follow these steps to start the system:

1. **Install dependencies** (if not already done):
   ```bash
   npm install
   ```

2. **Run the setup script** to start the core services:
   ```bash
   npm run setup
   ```
   This will start the setup and services processes using PM2.

3. **Start the development environment**:
   ```bash
   npm run dev
   ```
   This will start the main application using PM2.

4. **Open your browser** and navigate to `http://localhost:3000`

### PM2 Management Commands

The project includes several PM2 management commands:

```bash
npm run list      # List all running PM2 processes
npm run logs      # View logs from all processes
npm run stop      # Stop the main application
npm run cleanup   # Stop and remove all PM2 processes
```



## Backend Development

The project now uses a custom FastAPI backend (replacing the previous Google ADK api_server). The backend provides authentication, chat endpoints (SSE streaming), and connections to both PostgreSQL (primary) and user-created SQLite databases.

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

Note: There used to be a `start_server.sh` reference in older docs; the current recommended dev command is `uvicorn app.main:app --reload` from the `backend/` folder.
npm run dev         # Start development server
npm run build       # Build for production
npm run preview     # Preview production build
```

## Backend Development

The Python backend includes:

- **AI Agents**: Multi-agent system for data analysis
- **BigQuery Tools**: Database connection and query tools
- **Data Science Tools**: Analysis and visualization capabilities

### Backend Commands

```bash
# Start the ADK API server
cd backend
./start_server.sh
```

## API Endpoints

The system provides the following ADK API endpoints:

- `POST /run` - Send chat messages and run AI agents
- `GET /list-apps` - List available applications
- `POST /apps/{app_name}/users/{user_id}/sessions` - Create sessions
- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}` - Get session

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
   - Ensure you're authenticated with `gcloud auth application-default login`
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

After running the project for the first time, it is recommended to run `uv run list_extensions.py` once and copy the extension value into the .env `CODE_INTERPRETER_EXTENSION_NAME` variable for increased performance of future executions. This will be streamlined in future versions.

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