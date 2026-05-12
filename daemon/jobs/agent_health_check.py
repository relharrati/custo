"""Agent Health Check Job - runs hourly."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from daemon.scheduler import ScheduledTask
from daemon.supervisor import Supervisor
from agents.registry import get_registry


async def agent_health_check(task: ScheduledTask = None) -> dict:
    """
    Check health of all agents.
    
    Reports:
    - Which agents are running
    - Response times
    - Memory usage
    """
    logger = logging.getLogger("job.agent_health_check")
    root = Path(__file__).parent.parent.parent
    
    registry = get_registry(root)
    status = registry.get_status()
    
    unhealthy = []
    for agent_type, info in status.items():
        if not info.get("running"):
            unhealthy.append(agent_type)
        else:
            # Could add response time check here
            pass
    
    if unhealthy:
        logger.warning(f"Unhealthy agents: {unhealthy}")
    
    return {
        "status": "completed",
        "agents_checked": len(status),
        "unhealthy": unhealthy
    }
