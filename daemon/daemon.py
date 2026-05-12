"""
Daemon - Main Background Runtime for Custo

This is the persistent background process that:
- Listens for events from gateways/interfaces
- Creates and manages sessions
- Routes tasks to appropriate agents
- Handles memory updates
- Runs recurring jobs
"""

import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon.supervisor import Supervisor
from daemon.scheduler import Scheduler
from daemon.heartbeat import Heartbeat
from daemon.workers.manager import WorkerManager


class Daemon:
    """Main daemon process for Custo autonomous operator."""

    def __init__(self, root_path: str = None):
        self.root_path = Path(root_path or Path(__file__).parent.parent)
        self.running = False
        self.pid_file = self.root_path / "daemon" / "pid" / "custo.pid"
        self.supervisor: Optional[Supervisor] = None
        self.scheduler: Optional[Scheduler] = None
        self.heartbeat: Optional[Heartbeat] = None
        self.worker_manager: Optional[WorkerManager] = None

    def write_pid(self):
        """Write daemon PID to file."""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))

    def remove_pid(self):
        """Remove PID file on shutdown."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    async def start(self):
        """Start the daemon and all subsystems."""
        self.running = True
        self.write_pid()

        print("[DAEMON] Starting Custo Daemon...")
        print(f"[DAEMON] Root path: {self.root_path}")

        # Initialize supervisor (agent coordination)
        self.supervisor = Supervisor(root_path=self.root_path)
        await self.supervisor.start()

        # Initialize worker manager
        self.worker_manager = WorkerManager(root_path=self.root_path)
        await self.worker_manager.start()

        # Initialize scheduler (recurring tasks)
        self.scheduler = Scheduler(root_path=self.root_path)
        await self.scheduler.start()

        # Initialize heartbeat (health monitoring)
        self.heartbeat = Heartbeat(root_path=self.root_path)
        await self.heartbeat.start()

        print("[DAEMON] All subsystems started successfully")
        print("[DAEMON] Daemon is now running...")

        # Main event loop
        try:
            await self._run()
        finally:
            await self.shutdown()

    async def _run(self):
        """Main daemon event loop."""
        while self.running:
            # Process events from interfaces/gateways
            # Delegate to supervisor for routing
            await asyncio.sleep(1)

    async def shutdown(self):
        """Gracefully shutdown all subsystems."""
        print("[DAEMON] Shutting down...")

        if self.heartbeat:
            await self.heartbeat.stop()
        if self.scheduler:
            await self.scheduler.stop()
        if self.worker_manager:
            await self.worker_manager.stop()
        if self.supervisor:
            await self.supervisor.stop()

        self.remove_pid()
        print("[DAEMON] Shutdown complete")


def main():
    """Daemon entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Custo Daemon")
    parser.add_argument("--root", default=None, help="Custo root directory")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground (no daemonize)")
    args = parser.parse_args()

    daemon = Daemon(root_path=args.root)

    if args.foreground:
        asyncio.run(daemon.start())
    else:
        # Daemonize (fork to background)
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)

        # Child continues
        os.setsid()
        daemon.write_pid()
        asyncio.run(daemon.start())


if __name__ == "__main__":
    main()
