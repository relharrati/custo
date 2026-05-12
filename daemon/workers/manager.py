"""Worker Manager - coordinates all daemon workers."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .task_worker import TaskWorker
from .memory_worker import MemoryWorker
from .reflection_worker import ReflectionWorker


class WorkerManager:
    """
    Manages all daemon worker processes.
    
    Workers:
    - TaskWorker: routes user inputs to agents
    - MemoryWorker: inbox processing, consolidation
    - ReflectionWorker: insight generation
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.workers: dict = {}
        self.running = False
        self.logger = logging.getLogger("daemon.workers")
    
    async def start(self):
        """Start all workers."""
        self.running = True
        self.logger.info("Starting worker processes...")
        
        # Initialize workers
        task_worker = TaskWorker(self.root)
        memory_worker = MemoryWorker(self.root)
        reflection_worker = ReflectionWorker(self.root)
        
        # Start them
        await task_worker.start()
        await memory_worker.start()
        await reflection_worker.start()
        
        self.workers = {
            "task": task_worker,
            "memory": memory_worker,
            "reflection": reflection_worker
        }
        
        self.logger.info(f"All {len(self.workers)} workers started")
    
    async def stop(self):
        """Stop all workers."""
        self.running = False
        self.logger.info("Stopping worker processes...")
        
        for name, worker in self.workers.items():
            try:
                await worker.stop()
                self.logger.info(f"Worker '{name}' stopped")
            except Exception as e:
                self.logger.error(f"Error stopping worker '{name}': {e}")
        
        self.workers.clear()
