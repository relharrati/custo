"""
Supervisor - Agent Coordination and Task Routing

The Supervisor is responsible for:
- Managing agent lifecycle (start/stop/respawn)
- Routing tasks to appropriate agents based on type
- Monitoring agent health
- Facilitating inter-agent communication
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from agents.registry import get_registry


class Supervisor:
    """Coordinates agent operations and task routing."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.agents: Dict[str, asyncio.subprocess.Process] = {}
        self.registry = get_registry(root_path)
        self.logger = logging.getLogger("supervisor")
        self.running = False

    async def start(self):
        """Start the supervisor and launch all registered agents."""
        self.running = True
        self.logger.info("Starting supervisor...")

        # Load agent registry
        await self.registry.load()

        # Launch each agent
        for agent_type, config in self.registry.agents.items():
            await self._launch_agent(agent_type, config)

        self.logger.info(f"Supervisor started with {len(self.agents)} agents")

    async def _launch_agent(self, agent_type: str, config):
        """Launch a single agent subprocess."""
        agent_script = self.root_path / "agents" / agent_type / "agent.py"

        if not agent_script.exists():
            self.logger.warning(f"Agent script not found: {agent_script}")
            return

        # Set PYTHONPATH so agent subprocess can find top-level 'agents' package
        env = dict(os.environ)
        pythonpath = str(self.root_path)
        existing_pp = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = pythonpath + ((';' if os.name == 'nt' else ':') + existing_pp) if existing_pp else pythonpath

        # Launch agent as subprocess with stdin/stdout pipes for messaging
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(agent_script),
            cwd=str(self.root_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        self.agents[agent_type] = proc
        self.logger.info(f"Launched agent: {agent_type} (PID: {proc.pid})")

    async def stop(self):
        """Stop all agents and shutdown supervisor."""
        self.running = False
        self.logger.info("Stopping supervisor...")

        for agent_type, proc in self.agents.items():
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.kill()
            self.logger.info(f"Stopped agent: {agent_type}")

    async def route_task(self, task: dict) -> str:
        """
        Route a task to the appropriate agent.

        Returns the agent type that received the task.
        """
        task_type = task.get("type", "default")
        agent_type = self.registry.route_task(task_type)

        if agent_type not in self.agents:
            raise ValueError(f"Agent {agent_type} is not running")

        # Send task to agent via message queue
        await self._send_to_agent(agent_type, task)
        return agent_type

    async def _send_to_agent(self, agent_type: str, task: dict):
        """Send a task message to the specified agent via stdin."""
        proc = self.agents.get(agent_type)
        if not proc or proc.stdin is None:
            self.logger.warning(f"Cannot send to agent {agent_type}: not running")
            return

        try:
            message = json.dumps(task) + "\n"
            proc.stdin.write(message.encode())
            await proc.stdin.drain()
            self.logger.debug(f"Sent task to {agent_type}: {task.get('type')}")
        except Exception as e:
            self.logger.error(f"Failed to send to agent {agent_type}: {e}")

    def get_agent_status(self) -> Dict[str, dict]:
        """Get status of all agents."""
        status = {}
        for agent_type, proc in self.agents.items():
            status[agent_type] = {
                "running": proc.returncode is None,
                "pid": proc.pid if proc.returncode is None else None
            }
        return status
