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

1. **Authenticate with Google Cloud CLI**  
   Make sure you have the [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed.  
   Run the following command and follow the prompts to log in:
   ```
   gcloud auth login
   ```

2. **Set your default project**  
   Replace `<YOUR_PROJECT_ID>` with your Google Cloud project ID:
   ```
   gcloud config set project <YOUR_PROJECT_ID>
   ```

3. **Set up Application Default Credentials**  
   This is required for Vertex AI access:
   ```
   gcloud auth application-default login
   ```

### Option 1: Full AI Agent System (Production)

1. **Create and activate a virtual environment, install dependencies, and run the app**  
   ```
   uv venv
   uv sync
   source .venv/bin/activate
   adk web
   ```

2. **Start the React frontend** (in a new terminal):
   ```
   cd frontend
   npm install
   npm run dev
   ```

3. **Open your browser** and navigate to `http://localhost:5173`

### Option 2: Development/Testing Mode

1. **Start the mock backend** (for testing without full AI setup):
   ```
   pip install -r requirements.txt
   python backend_example.py
   ```

2. **Start the React frontend** (in a new terminal):
   ```
   cd frontend
   npm install
   npm run dev
   ```

3. **Open your browser** and navigate to `http://localhost:5173`

## Frontend Development

The React frontend is located in the `frontend/` directory and provides:

- 🎨 **Dark & Green Theme** - Modern, professional interface
- 💬 **Real-time Chat** - Interactive chat with AI agents
- 📊 **Data Visualization** - Display generated plots and charts
- 💻 **Code Display** - Syntax-highlighted analysis scripts
- 🔄 **Session Management** - Persistent chat sessions

### Frontend Commands

```bash
cd frontend
npm install          # Install dependencies
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
# For production AI system
uv venv
uv sync
source .venv/bin/activate
adk web

# For development/testing
pip install -r requirements.txt
python backend_example.py
```

## API Endpoints

The system provides the following API endpoints:

- `GET /health` - Health check
- `GET /api/health/bigquery` - BigQuery connection status
- `POST /api/chat` - Send chat messages and receive AI responses

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