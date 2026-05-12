"""
Base Agent - Abstract Agent Class

All Custo agents inherit from this base class.
Provides common functionality for communication, memory access, and task handling.
"""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from agents.registry import AgentRegistry


class BaseAgent(ABC):
    """Abstract base class for all Custo agents."""

    def __init__(
        self,
        agent_type: str,
        root_path: Path,
        registry: AgentRegistry = None
    ):
        self.agent_type = agent_type
        self.root_path = root_path
        self.registry = registry or AgentRegistry(root_path)
        self.identity_path = root_path / "agents" / agent_type / "identity.py"
        self.logger = logging.getLogger(f"agent.{agent_type}")
        self.running = False
        self._message_handlers: Dict[str, Callable] = {}

    async def start(self):
        """Start the agent."""
        self.running = True
        self._setup_logging()
        self._load_identity()
        self._load_skills()
        self.logger.info(f"Agent {self.agent_type} started")

    async def stop(self):
        """Stop the agent."""
        self.running = False
        self.logger.info(f"Agent {self.agent_type} stopped")

    def _setup_logging(self):
        """Configure agent-specific logging."""
        log_dir = self.root_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / f"{self.agent_type}.log")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _load_identity(self):
        """Load agent-specific identity and capabilities."""
        identity_file = self.root_path / "agents" / self.agent_type / "identity.md"
        if identity_file.exists():
            self.identity = identity_file.read_text()
            self.logger.info("Identity loaded")

    def _load_skills(self):
        """Load agent-specific skills."""
        skills_dir = self.root_path / "agents" / self.agent_type / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.py"):
                self._register_skill(skill_file.stem, skill_file)

    def _register_skill(self, name: str, path: Path):
        """Register a skill for this agent."""
        self.logger.debug(f"Registered skill: {name}")

    def register_message_handler(self, msg_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        self._message_handlers[msg_type] = handler

    async def handle_message(self, message: dict) -> Any:
        """Handle an incoming message."""
        msg_type = message.get("type", "default")
        handler = self._message_handlers.get(msg_type, self._default_handler)
        return await handler(message)

    @abstractmethod
    async def process_task(self, task: dict) -> dict:
        """Process a task - must be implemented by subclasses."""
        pass

    def _default_handler(self, message: dict) -> dict:
        """Default message handler."""
        return {"status": "received", "agent": self.agent_type}

    def log_decision(self, decision: str, context: dict = None):
        """Log an agent decision."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_type,
            "decision": decision,
            "context": context or {}
        }
        log_file = self.root_path / "logs" / "decisions.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")

    def to_dict(self) -> dict:
        """Return agent state as dictionary."""
        return {
            "type": self.agent_type,
            "running": self.running,
            "skills": list(self._message_handlers.keys())
        }

    async def _message_loop(self):
        """Main message processing loop - reads from stdin, writes to stdout."""
        self.logger.info("Message loop started - waiting for tasks")

        while self.running:
            try:
                # Use to_thread for Windows Proactor compatibility (connect_read_pipe fails on Windows)
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break

                message = json.loads(line.strip())
                self.logger.debug(f"Received: {message.get('type', 'unknown')}")

                result = await self.process_task(message)

                response = json.dumps(result) + "\n"
                await asyncio.to_thread(sys.stdout.write, response)
                await asyncio.to_thread(sys.stdout.flush)

            except asyncio.CancelledError:
                break
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON received: {e}")
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()


async def main():
    """Agent entry point - runs as subprocess with stdin/stdout messaging."""
    import sys
    agent_type = sys.argv[1] if len(sys.argv) > 1 else "main"
    root = Path(__file__).parent.parent

    # Import specific agent
    try:
        module = __import__(f"agents.{agent_type}.agent", fromlist=["Agent"])
        AgentClass = getattr(module, "Agent")

        # Instantiate using the agent's actual __init__ signature (root_path first, not agent_type)
        agent = AgentClass(root)
        await agent.start()

        # Run message loop
        await agent._message_loop()
    except KeyboardInterrupt:
        if 'agent' in locals():
            await agent.stop()
    except ImportError as e:
        print(f"Agent {agent_type} not found: {e}", file=sys.stderr)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Agent error: {e}", file=sys.stderr)
