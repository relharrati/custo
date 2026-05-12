"""Daemon scheduled jobs."""

from .memory_consolidation import memory_consolidation
from .session_indexing import session_indexing
from .agent_health_check import agent_health_check
from .heartbeat import heartbeat_job

_job_registry = {
    "memory_consolidation": memory_consolidation,
    "session_indexing": session_indexing,
    "agent_health_check": agent_health_check,
    "heartbeat": heartbeat_job
}


def get_job(name: str):
    """Get a job handler by name."""
    return _job_registry.get(name)
