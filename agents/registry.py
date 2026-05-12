"""Agent Registry - discovers and routes to available agents."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for a registered agent."""
    name: str
    description: str
    identity: str
    capabilities: list
    module: str
    class_name: str
    enabled: bool = True
    process: Optional[asyncio.subprocess.Process] = None


class AgentRegistry:
    """
    Discovers agents from agents/registry.json and manages agent lifecycle.
    
    Responsibilities:
    - Load agent configurations from JSON registry
    - Route task types to agent types
    - Launch/stop agent subprocesses
    - Track agent health
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.registry_path = root_path / "agents" / "registry.json"
        self.agents: Dict[str, AgentConfig] = {}
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.log_path = root_path / "logs" / "agents.log"
    
    async def load(self):
        """Load agent registry from disk."""
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            for agent_type, config in data.get("agents", {}).items():
                self.agents[agent_type] = AgentConfig(
                    name=config.get("name", agent_type),
                    description=config.get("description", ""),
                    identity=config.get("identity", "unknown"),
                    capabilities=config.get("capabilities", []),
                    module=config.get("module", f"agents.{agent_type}.agent"),
                    class_name=config.get("class", "Agent"),
                    enabled=config.get("enabled", True)
                )
        else:
            # Fallback: discover agents from directories
            await self._discover_agents()
    
    async def _discover_agents(self):
        """Discover agents by scanning agent directories."""
        agents_dir = self.root / "agents"
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name not in ("__pycache__",):
                agent_type = agent_dir.name
                self.agents[agent_type] = AgentConfig(
                    name=agent_type.capitalize(),
                    description=f"Agent: {agent_type}",
                    identity="unknown",
                    capabilities=[],
                    module=f"agents.{agent_type}.agent",
                    class_name="Agent"
                )
    
    def route_task(self, task_type: str) -> str:
        """
        Route a task type to the appropriate agent.
        
        Reads routing rules in order:
        1. registry.json's routing.task_type_mapping
        2. agent capabilities matching
        3. default agent
        """
        # First check explicit routing from registry
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            routing = data.get("routing", {})
            mapping = routing.get("task_type_mapping", {})
            if task_type in mapping:
                return mapping[task_type]
        
        # Then check agent capabilities
        for agent_type, config in self.agents.items():
            if task_type in config.capabilities:
                return agent_type
        
        # Fall back to default
        default = "main"
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            default = data.get("routing", {}).get("default_agent", "main")
        
        return default
    
    async def start_agent(self, agent_type: str) -> bool:
        """Start an agent as a subprocess."""
        if agent_type not in self.agents:
            print(f"[REGISTRY] Agent '{agent_type}' not found")
            return False
        
        config = self.agents[agent_type]
        
        if agent_type in self.processes and self.processes[agent_type].returncode is None:
            print(f"[REGISTRY] Agent '{agent_type}' already running")
            return True
        
        agent_script = self.root / "agents" / agent_type / "agent.py"
        if not agent_script.exists():
            print(f"[REGISTRY] Agent script not found: {agent_script}")
            return False
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(agent_script),
                cwd=str(self.root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.processes[agent_type] = proc
            print(f"[REGISTRY] Started agent '{agent_type}' (PID: {proc.pid})")
            return True
        except Exception as e:
            print(f"[REGISTRY] Failed to start agent '{agent_type}': {e}")
            return False
    
    async def stop_agent(self, agent_type: str):
        """Stop a running agent."""
        if agent_type in self.processes:
            proc = self.processes[agent_type]
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.kill()
            print(f"[REGISTRY] Stopped agent '{agent_type}'")
    
    async def start_all(self):
        """Start all enabled agents."""
        for agent_type, config in self.agents.items():
            if config.enabled:
                await self.start_agent(agent_type)
    
    async def stop_all(self):
        """Stop all running agents."""
        for agent_type in list(self.processes.keys()):
            await self.stop_agent(agent_type)
    
    def get_status(self) -> Dict[str, dict]:
        """Get status of all agents."""
        status = {}
        for agent_type, config in self.agents.items():
            proc = self.processes.get(agent_type)
            running = proc is not None and proc.returncode is None
            status[agent_type] = {
                "name": config.name,
                "enabled": config.enabled,
                "running": running,
                "pid": proc.pid if running else None
            }
        return status
    
    def send_message(self, agent_type: str, message: dict) -> Optional[asyncio.Future]:
        """
        Send a message to an agent via its subprocess stdin.
        
        Returns a Future that resolves when the agent responds.
        """
        if agent_type not in self.processes:
            return None
        
        proc = self.processes[agent_type]
        if proc.stdin and not proc.stdin.is_closing():
            # Serialize message with newline delimiter
            proc.stdin.write(json.dumps(message) + "\n")
            return asyncio.create_task(self._read_response(proc))
        return None
    
    async def _read_response(self, proc: asyncio.subprocess.Process) -> Optional[dict]:
        """Read a response from an agent subprocess."""
        if proc.stdout:
            line = await proc.stdout.readline()
            if line:
                try:
                    return json.loads(line.decode().strip())
                except json.JSONDecodeError:
                    pass
        return None


# Global registry singleton
_registry: Optional[AgentRegistry] = None


def get_registry(root_path: Path = None) -> AgentRegistry:
    """Get or create the global agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry(root_path or Path.cwd())
    return _registry


# Convenience alias
registry = get_registry
