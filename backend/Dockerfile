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

# Install entrypoint script to a stable path not affected by bind mounts
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose port
EXPOSE 8000

# Use an entrypoint that runs migrations first, then starts the app
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default CMD can be overridden by docker-compose or `docker run`
CMD ["uv", "run", "-m", "app.main"]
