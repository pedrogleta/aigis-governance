FROM python:3.13-slim

# Create app directory
WORKDIR /app

# Install system dependencies needed to build packages (if necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy lockfile and pyproject for deterministic installs
COPY pyproject.toml uv.lock /app/

# Install the `uv` CLI and use it to create a venv and sync dependencies
RUN pip install --no-cache-dir uv \
    && uv venv \
    && uv sync

# Copy application code
COPY . /app

# Expose port
EXPOSE 8000

# Run the app using `uv run` so it executes inside the uv-managed venv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
