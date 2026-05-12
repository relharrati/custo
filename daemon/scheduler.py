"""
Scheduler - Recurring Task Management

The Scheduler handles:
- Loading scheduled tasks from config
- Triggering recurring jobs at specified intervals
- Managing cron-like schedules
- Dispatching scheduled events to the supervisor
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ScheduledTask:
    """Represents a recurring scheduled task."""
    name: str
    frequency: str  # "hourly", "daily", "weekly", "monthly", "cron"
    cron_expr: Optional[str] = None
    last_run: Optional[float] = None
    handler: Optional[str] = None  # Module path to task handler
    enabled: bool = True


class Scheduler:
    """Manages recurring and scheduled tasks."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.tasks: List[ScheduledTask] = []
        self.running = False
        self.log_path = root_path / "logs" / "scheduler.log"
        self._ensure_logs()

    def _ensure_logs(self):
        """Ensure log directory exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Start the scheduler."""
        self.running = True
        await self._load_tasks()
        print("[SCHEDULER] Scheduler started")
        # Run scheduler loop in background task
        asyncio.create_task(self._run_loop())

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        print("[SCHEDULER] Scheduler stopped")

    async def _load_tasks(self):
        """Load scheduled tasks from configuration."""
        config_path = self.root_path / "system" / "config.yaml"

        # Parse YAML config for scheduled tasks
        # For now, use built-in defaults
        self.tasks = [
            ScheduledTask(
                name="memory_consolidation",
                frequency="daily",
                cron_expr="0 2 * * *",
                handler="daemon.jobs.memory_consolidation"
            ),
            ScheduledTask(
                name="session_indexing",
                frequency="daily",
                cron_expr="30 2 * * *",
                handler="daemon.jobs.session_indexing"
            ),
            ScheduledTask(
                name="agent_health_check",
                frequency="hourly",
                handler="daemon.jobs.agent_health_check"
            ),
            ScheduledTask(
                name="heartbeat",
                frequency="minute",
                handler="daemon.jobs.heartbeat"
            ),
        ]

    async def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()

            for task in self.tasks:
                if not task.enabled:
                    continue

                if self._should_run(task, now):
                    await self._execute_task(task)
                    task.last_run = datetime.now().timestamp()

            # Check every minute
            await asyncio.sleep(60)

    def _should_run(self, task: ScheduledTask, now: datetime) -> bool:
        """Check if a task should run at the current time."""
        if task.last_run is None:
            return True

        last_dt = datetime.fromtimestamp(task.last_run)

        if task.frequency == "minute":
            return now.minute != last_dt.minute
        elif task.frequency == "hourly":
            return now.hour != last_dt.hour
        elif task.frequency == "daily":
            return now.date() != last_dt.date()
        elif task.frequency == "weekly":
            return now.isocalendar()[1] != last_dt.isocalendar()[1]
        elif task.frequency == "monthly":
            return now.month != last_dt.month
        else:
            return False

    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        print(f"[SCHEDULER] Executing task: {task.name}")
        # Dispatch to appropriate job handler
        # Implementation would dynamically import and run handler
        pass

    def add_task(self, task: ScheduledTask):
        """Add a new scheduled task."""
        self.tasks.append(task)

    def remove_task(self, name: str):
        """Remove a scheduled task by name."""
        self.tasks = [t for t in self.tasks if t.name != name]

    def get_tasks(self) -> List[dict]:
        """Get all scheduled tasks as dictionaries."""
        return [asdict(t) for t in self.tasks]
