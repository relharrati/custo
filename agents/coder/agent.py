"""
Coder Agent - Implementation Specialist
"""

import subprocess
from pathlib import Path

from agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """Coder/implementation specialist agent."""

    def __init__(self, root_path: Path, registry=None):
        super().__init__("coder", root_path, registry)
        self.workspace = root_path

    async def start(self):
        await super().start()
        self.log_decision("Coder agent started")

    async def process_task(self, task: dict) -> dict:
        task_type = task.get("type", "write_file")

        if task_type == "write_file":
            path = task.get("path")
            content = task.get("content", "")
            return await self._write_file(path, content)
        elif task_type in ("run_command", "execute"):
            cmd = task.get("command") or task.get("content", "")
            return await self._run_command(cmd)
        elif task_type == "list_dir":
            dir_path = task.get("path", ".")
            return await self._list_dir(dir_path)
        else:
            return {"status": "acknowledged", "type": task_type}

    async def _write_file(self, path: str, content: str) -> dict:
        if not path:
            return {"error": "No path specified"}
        full_path = self.workspace / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        self.logger.info(f"Wrote file: {path}")
        return {"status": "written", "path": str(full_path)}

    async def _run_command(self, cmd: str) -> dict:
        if not cmd:
            return {"error": "No command specified"}
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=str(self.workspace)
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _list_dir(self, dir_path: str) -> dict:
        target = self.workspace / dir_path
        if not target.exists():
            return {"error": f"Path not found: {dir_path}"}
        entries = [
            {"name": e.name, "is_file": e.is_file(), "is_dir": e.is_dir()}
            for e in target.iterdir()
        ]
        return {"path": dir_path, "entries": entries}


class Agent(CoderAgent):
    """Alias for subprocess entrypoint."""
    pass


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import main as agent_main
    asyncio.run(agent_main())
