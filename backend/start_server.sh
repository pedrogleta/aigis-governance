#!/bin/bash

# Start the ADK API server
# This script activates the virtual environment and starts the server

echo "🚀 Starting AIGIS Governance Backend..."
echo "📊 Using Google ADK framework for AI agents"
echo "🔗 Server will be available at: http://localhost:8000"
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

echo "✅ Starting ADK API server..."
echo "🌐 The server will provide ADK API endpoints"
echo "📱 Frontend should connect to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the ADK API server
adk api_server --allow_origins="*"
