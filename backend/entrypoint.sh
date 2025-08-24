#!/bin/sh
set -e

echo "[entrypoint] Starting backend container"

# Retry parameters for migrations (override with env vars if needed)
RETRIES=${MIGRATIONS_MAX_RETRIES:-20}
SLEEP=${MIGRATIONS_RETRY_SLEEP:-3}

echo "[entrypoint] Running Alembic migrations (alembic upgrade head)"
i=0
until uv run alembic upgrade head; do
  i=$((i+1))
  if [ "$i" -ge "$RETRIES" ]; then
    echo "[entrypoint] Migrations failed after $RETRIES attempts. Exiting."
    exit 1
  fi
  echo "[entrypoint] Migration attempt $i failed. Retrying in $SLEEP seconds..."
  sleep "$SLEEP"
done

echo "[entrypoint] Migrations complete"

echo "[entrypoint] Launching application"
if [ $# -eq 0 ]; then
  # Default command
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
else
  # If a command was provided, ensure it runs inside the uv-managed venv
  if [ "$1" = "uv" ]; then
    exec "$@"
  else
    exec uv run "$@"
  fi
fi
