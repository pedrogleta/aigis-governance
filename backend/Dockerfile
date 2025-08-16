FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install small deps used by some projects and curl for healthchecks
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Try to install package if pyproject exists; keep best-effort to avoid build failures
RUN python -m pip install --upgrade pip setuptools wheel || true
RUN if [ -f pyproject.toml ]; then pip install . || true; fi

EXPOSE 8000

# Start using the repository's start script (expects start_server.sh to exist and be executable)
CMD ["bash", "./start_server.sh"]
