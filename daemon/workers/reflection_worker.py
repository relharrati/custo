"""Reflection Worker - generates insights from system activity."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from collections import Counter

from sessions.manager import SessionManager
from memory.manager import get_memory_manager
from agents.registry import get_registry


class ReflectionWorker:
    """
    Reflection worker generates insights:
    - Agent performance patterns
    - User behavior summaries
    - Goal progress updates
    - System health observations
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.memory = get_memory_manager(root_path)
        self.session_mgr = SessionManager(root_path)
        self.registry = get_registry(root_path)
        self.running = False
        self.logger = logging.getLogger("daemon.reflection_worker")
        self._reflection_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start reflection worker."""
        self.running = True
        self.logger.info("Reflection worker started")
        # Run reflections every 6 hours
        self._reflection_task = asyncio.create_task(self._reflection_loop())
    
    async def stop(self):
        """Stop reflection worker."""
        self.running = False
        if self._reflection_task:
            self._reflection_task.cancel()
            try:
                await self._reflection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Reflection worker stopped")
    
    async def reflect_on_sessions(self, days_back: int = 1) -> dict:
        """
        Analyze sessions from recent days.
        
        Returns insights about conversation patterns.
        """
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        # Load session index
        index_path = self.root / "sessions" / "index.json"
        if not index_path.exists():
            return {"insights": [], "sessions_analyzed": 0}
        
        import json
        index = json.loads(index_path.read_text())
        
        recent_sessions = [
            s for s in index.get("sessions", [])
            if s.get("date", "") >= cutoff
        ]
        
        insights = []
        
        if recent_sessions:
            total_messages = sum(s.get("message_count", 0) for s in recent_sessions)
            avg_messages = total_messages / len(recent_sessions)
            insights.append({
                "type": "usage_statistics",
                "description": f"Analyzed {len(recent_sessions)} sessions with avg {avg_messages:.1f} messages"
            })
        
        return {
            "insights": insights,
            "sessions_analyzed": len(recent_sessions)
        }
    
    async def reflect_on_agents(self) -> dict:
        """Analyze agent performance and health."""
        status = self.registry.get_status()
        
        insights = []
        running_count = sum(1 for s in status.values() if s.get("running"))
        total = len(status)
        
        insights.append({
            "type": "agent_health",
            "description": f"{running_count}/{total} agents running"
        })
        
        # Store reflection
        reflection_text = "\n".join(f"- {a}: {s['running']}" for a, s in status.items())
        self.memory.reflection_write(
            content=f"Agent health check:\n{reflection_text}",
            tags=["agent", "health"]
        )
        
        return {"insights": insights}
    
    async def _reflection_loop(self):
        """Periodic reflection loop."""
        while self.running:
            try:
                await asyncio.sleep(21600)  # 6 hours
                
                if not self.running:
                    break
                
                self.logger.info("Running reflection cycle")
                
                # Reflect on sessions
                session_insights = await self.reflect_on_sessions()
                
                # Reflect on agents
                agent_insights = await self.reflect_on_agents()
                
                self.logger.info(
                    f"Reflection complete: {len(session_insights['insights'])} session insights, "
                    f"{len(agent_insights['insights'])} agent insights"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Reflection error: {e}")
