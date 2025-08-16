#!/bin/bash

# Set up MinIO

echo "🚀 Setting up MinIO..."
echo ""

# Copy .env file from parent directory if it exists
if [ -f "../../.env" ]; then
    echo "📄 Copying .env from parent directory..."
    cp ../../.env .env
else
    echo "⚠️  No .env file found in parent directory."
fi

docker compose --env-file ./.env up
