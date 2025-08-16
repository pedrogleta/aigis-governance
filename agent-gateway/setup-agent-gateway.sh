#!/bin/bash


echo "🚀 Setting up Agent Gateway..."
echo ""


if ! command -v uv &> /dev/null
then
  echo "uv not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
else
  echo "uv is already installed."
fi
