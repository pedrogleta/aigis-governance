#!/bin/bash

# Start the ADK API server
# This script activates the virtual environment and starts the server

echo "🚀 Starting AIGIS Governance Agent Gateway..."
echo "📊 Using Google ADK framework for AI agents"
echo "🔗 Server will be available at: http://0.0.0.0:8000 (accessible from host at http://localhost:8000)"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    uv venv
    uv sync
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if adk is available
if ! command -v adk &> /dev/null; then
    echo "❌ ADK command not found. Installing dependencies..."
    uv sync
fi

# Copy .env file from parent directory if it exists
if [ -f "../.env" ]; then
    echo "📄 Copying .env from parent directory..."
    cp ../.env .env
else
    echo "⚠️  No .env file found in parent directory."
fi


echo "✅ Starting ADK API server..."
echo "🌐 The server will provide ADK API endpoints"
echo "📱 Frontend should connect to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the ADK API server
adk api_server --host 0.0.0.0 --allow_origins="*"
