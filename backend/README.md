# Aigis Backend

A FastAPI-based backend server.

## Setup

1. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install fastapi uvicorn
```

## Running the Server

### Option 1: Using uvicorn directly (recommended for development)
```bash
uvicorn main:app --reload
```

### Option 2: Running the Python file directly
```bash
python main.py
```

The server will start on `http://localhost:8000`

## API Endpoints

- `GET /` - Hello World endpoint that returns a JSON message

## Development

The `--reload` flag automatically restarts the server when you make changes to your code, making it ideal for development.
