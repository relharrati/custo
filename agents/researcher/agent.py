"""
Researcher Agent - Knowledge & Context Gatherer
"""

import asyncio
from pathlib import Path

from agents.base_agent import BaseAgent
from memory.manager import get_memory_manager


class ResearcherAgent(BaseAgent):
    """Research specialist agent."""

    def __init__(self, root_path: Path, registry=None):
        super().__init__("researcher", root_path, registry)

    async def start(self):
        await super().start()
        self.log_decision("Researcher agent started")

    async def process_task(self, task: dict) -> dict:
        task_type = task.get("type", "search")

        if task_type in ("search", "research", "find"):
            query = task.get("query") or task.get("content", "")
            return await self._search(query)
        elif task_type == "deep_dive":
            topic = task.get("topic") or task.get("content", "")
            return await self._deep_dive(topic)
        else:
            return {"status": "received", "type": task_type}

    async def _search(self, query: str) -> dict:
        memory = get_memory_manager(self.root_path)
        if not query:
            return {"results": [], "count": 0}
        
        results = memory.long_term_search(query)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }

    async def _deep_dive(self, topic: str) -> dict:
        memory = get_memory_manager(self.root_path)
        results = memory.long_term_search(topic)
        return {
            "topic": topic,
            "summary": f"Found {len(results)} references",
            "sources": results
        }


class Agent(ResearcherAgent):
    """Alias for subprocess entrypoint."""
    pass


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import main as agent_main
    asyncio.run(agent_main())
