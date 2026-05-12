"""Heartbeat Job - updates daemon heartbeat status."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from daemon.scheduler import ScheduledTask


async def heartbeat_job(task: ScheduledTask = None) -> dict:
    """Write current heartbeat status."""
    root = Path(__file__).parent.parent.parent
    logger = logging.getLogger("job.heartbeat")
    
    heartbeat_dir = root / "daemon" / "pid"
    heartbeat_file = heartbeat_dir / "heartbeat.json"
    
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "unix_time": time.time(),
        "pid": os.getpid(),
        "status": "healthy",
        "daemon_uptime": time.time() - (getattr(heartbeat_job, '_start_time', time.time()))
    }
    
    heartbeat_file.write_text(json.dumps(data, indent=2))
    
    if not hasattr(heartbeat_job, '_start_time'):
        heartbeat_job._start_time = time.time()
    
    return {"status": "beat", "timestamp": data["timestamp"]}
