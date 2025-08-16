#!/bin/bash

# Start the backend

# Copy .env file from parent directory if it exists
if [ -f "../.env" ]; then
    echo "📄 Copying .env from parent directory..."
    cp ../.env .env
else
    echo "⚠️  No .env file found in parent directory."
fi

echo "🚀 Starting Backend..."
echo "🔗 Server will be available at: http://0.0.0.0:3001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
