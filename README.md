# Aigis Governance

## Setup and run

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

4. **Create and activate a virtual environment, install dependencies, and run the app**  
   ```
   uv venv
   uv sync
   source .venv/bin/activate
   adk web
   ```

### Hint

After running the project for the first time, it is recommended to run `uv run list_extensions.py` once and copy the extension value into the .env `CODE_INTERPRETER_EXTENSION_NAME` variable for increased performance of future executions. This will be streamlined on 