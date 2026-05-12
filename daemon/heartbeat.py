"""
Heartbeat - System Health Monitoring

The Heartbeat component:
- Writes periodic heartbeat files
- Monitors agent liveness
- Reports system health status
- Enables external process monitoring
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path


class Heartbeat:
    """System health and liveness monitoring."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.heartbeat_file = root_path / "daemon" / "pid" / "heartbeat.json"
        self.running = False
        self.interval = 5  # seconds
        self._last_heartbeat = None

    def _ensure_heartbeat_dir(self):
        """Ensure heartbeat directory exists."""
        self.heartbeat_file.parent.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Start the heartbeat loop."""
        self.running = True
        self._ensure_heartbeat_dir()
        print("[HEARTBEAT] Heartbeat started")
        asyncio.create_task(self._beat_loop())

    async def stop(self):
        """Stop the heartbeat."""
        self.running = False
        print("[HEARTBEAT] Heartbeat stopped")

    async def _beat_loop(self):
        """Main heartbeat loop."""
        while self.running:
            await self._write_heartbeat()
            await asyncio.sleep(self.interval)

    async def _write_heartbeat(self):
        """Write current heartbeat state to file."""
        heartbeat_data = {
            "timestamp": datetime.now().isoformat(),
            "unix_time": time.time(),
            "pid": os.getpid(),
            "status": "healthy",
            "uptime_seconds": self._get_uptime()
        }

        with open(self.heartbeat_file, 'w') as f:
            json.dump(heartbeat_data, f, indent=2)

        self._last_heartbeat = time.time()

    def _get_uptime(self) -> float:
        """Get daemon uptime in seconds."""
        if not hasattr(self, '_start_time'):
            self._start_time = time.time()
        return time.time() - self._start_time

    def is_healthy(self) -> bool:
        """Check if the system is healthy based on last heartbeat."""
        if self._last_heartbeat is None:
            return False
        return (time.time() - self._last_heartbeat) < (self.interval * 2)

    def get_status(self) -> dict:
        """Get current heartbeat status."""
        if self.heartbeat_file.exists():
            with open(self.heartbeat_file, 'r') as f:
                return json.load(f)
        return {"status": "no_heartbeat"}
