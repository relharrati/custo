"""
Strategist Agent - Architecture & Planning Specialist
"""

from datetime import datetime
from pathlib import Path

from agents.base_agent import BaseAgent


class StrategistAgent(BaseAgent):
    """Architecture strategist agent."""

    def __init__(self, root_path: Path, registry=None):
        super().__init__("strategist", root_path, registry)
        self.plans = {}

    async def start(self):
        await super().start()
        self.log_decision("Strategist agent started")

    async def process_task(self, task: dict) -> dict:
        task_type = task.get("type", "plan")

        if task_type in ("plan", "create_plan"):
            goal = task.get("goal") or task.get("content", "")
            return await self._create_plan(goal)
        elif task_type in ("architect", "design"):
            subject = task.get("subject") or task.get("content", "")
            return await self._design(subject)
        elif task_type == "roadmap":
            return await self._create_roadmap(task)
        else:
            return {"status": "received", "type": task_type}

    async def _create_plan(self, goal: str) -> dict:
        plan = {
            "goal": goal,
            "created": datetime.now().isoformat(),
            "phases": [],
            "status": "draft"
        }
        plan_id = f"plan_{len(self.plans) + 1}"
        self.plans[plan_id] = plan
        return {"plan_id": plan_id, "plan": plan, "status": "created"}

    async def _design(self, subject: str) -> dict:
        return {
            "subject": subject,
            "approach": "strategic_design",
            "status": "draft"
        }

    async def _create_roadmap(self, task: dict) -> dict:
        roadmap = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "phases": [],
            "milestones": []
        }
        return {"roadmap": roadmap, "status": "draft"}


class Agent(StrategistAgent):
    """Alias for subprocess entrypoint."""
    pass


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import main as agent_main
    asyncio.run(agent_main())
