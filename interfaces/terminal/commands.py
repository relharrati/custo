"""
Commands - Terminal Command Handlers

Individual command implementations for the CLI.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List

from agents.main.agent import MainAgent
from agents.registry import get_registry
from sessions.manager import SessionManager


async def memory_search(query: str):
    """Search memory for matching entries."""
    from memory.manager import get_memory_manager
    
    if not query:
        print("Usage: custo memory <search-query>")
        return
    
    base = Path(__file__).parent.parent.parent
    memory = get_memory_manager(base)
    
    print(f"Searching memory for: '{query}'")
    print("-" * 40)
    
    results = memory.long_term_search(query)
    if results:
        print(f"Found {len(results)} matches in long-term memory:")
        for r in results:
            print(f"  - {r}")
    else:
        print("No matches found in long-term memory.")


async def project_list():
    """List all projects."""
    base = Path(__file__).parent.parent.parent
    projects_dir = base / "projects" / "active"
    
    print("Active Projects:")
    print("-" * 40)
    
    projects = [p for p in projects_dir.iterdir() if p.is_dir()]
    if not projects:
        print("No active projects.")
        return
    
    for project in projects:
        project_md = project / "project.md"
        if project_md.exists():
            print(f"  {project.name}")


async def project_open(name: str):
    """Open a specific project."""
    base = Path(__file__).parent.parent.parent
    project_dir = base / "projects" / "active" / name
    
    if not project_dir.exists():
        print(f"Project '{name}' not found.")
        return
    
    print(f"Opened project: {name}")
    print(f"Location: {project_dir}")


async def show_tasks(args):
    """Show task lists."""
    base = Path(__file__).parent.parent.parent
    tasks_dir = base / "tasks"
    
    if args.today:
        today_file = tasks_dir / "today.md"
        if today_file.exists():
            print(today_file.read_text())
    elif args.list:
        print("Available task files:")
        for task_file in tasks_dir.glob("*.md"):
            print(f"  - {task_file.name}")


async def config_show():
    """Show current configuration."""
    from system.config import load_config
    
    config = load_config()
    print(json.dumps(config, indent=2))


async def config_set(key: str, value: str):
    """Set a configuration value."""
    print(f"Setting {key} = {value}")
    # Would update config here
