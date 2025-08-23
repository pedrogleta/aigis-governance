"""Shared application state for chat threads."""

from typing import Dict, Any

# In-memory store for active chat threads. In production, replace with a DB or cache.
active_threads: Dict[str, Any] = {}
