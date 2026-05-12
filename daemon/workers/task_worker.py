"""Task Worker - handles task routing and agent communication."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents.registry import get_registry
from sessions.manager import SessionManager
from memory.manager import get_memory_manager


class TaskWorker:
    """
    Task worker handles:
    - Receiving tasks from scheduler/supervisor
    - Looking up appropriate agent
    - Dispatching tasks to agents
    - Tracking task state and results
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.registry = get_registry(root_path)
        self.session_mgr = SessionManager(root_path)
        self.memory = get_memory_manager(root_path)
        self.running = False
        self.logger = logging.getLogger("daemon.task_worker")
        self.pending_tasks: asyncio.Queue = asyncio.Queue()
        self.results: dict = {}
    
    async def start(self):
        """Start the task worker."""
        self.running = True
        self.logger.info("Task worker started")
        # Start processing loop in background
        asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """Stop the task worker."""
        self.running = False
        self.logger.info("Task worker stopped")
    
    async def submit_task(self, task: dict) -> str:
        """
        Submit a task for processing.
        
        Returns task_id for later result retrieval.
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        task["_task_id"] = task_id
        task["_submitted_at"] = datetime.now().isoformat()
        task["_status"] = "pending"
        
        await self.pending_tasks.put(task)
        self.logger.info(f"Task submitted: {task_id} (type={task.get('type')})")
        return task_id
    
    async def _process_loop(self):
        """Main task processing loop."""
        while self.running:
            try:
                task = await asyncio.wait_for(self.pending_tasks.get(), timeout=1)
                await self._process_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing task: {e}")
    
    async def _process_task(self, task: dict):
        """Process a single task."""
        task_id = task["_task_id"]
        task_type = task.get("type", "default")
        
        self.logger.info(f"Processing task {task_id} (type={task_type})")
        
        # Route to appropriate agent
        agent_type = self.registry.route_task(task_type)
        
        # If main agent and it's a user message, create session context
        if agent_type == "main" and task_type == "user_message":
            session_id = task.get("session_id")
            if not session_id:
                # Create a new session
                session = self.session_mgr.create_session()
                task["session_id"] = session["id"]
        
        # Send to agent
        result = await self.registry.send_message(agent_type, task)
        
        if result:
            task["_status"] = "completed"
            task["_result"] = result
            task["_completed_at"] = datetime.now().isoformat()
        else:
            task["_status"] = "failed"
            task["_error"] = "Agent did not respond"
        
        self.results[task_id] = task
        self.pending_tasks.task_done()
    
    def get_result(self, task_id: str) -> Optional[dict]:
        """Get task result by ID."""
        return self.results.get(task_id)
