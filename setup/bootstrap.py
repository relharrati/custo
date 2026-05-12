"""
Bootstrap - Directory and Permission Setup

This script creates any missing directories and sets up
proper permissions for the Custo system.
"""

import os
import sys
from pathlib import Path


# Required directory structure
REQUIRED_DIRS = [
    "system",
    "user",
    "sessions/daily",
    "projects/active",
    "projects/archived",
    "memory/inbox",
    "memory/short_term",
    "memory/daily_memory",
    "memory/long_term",
    "memory/reflections",
    "agents/main",
    "agents/researcher",
    "agents/coder",
    "agents/strategist",
    "skill_factory/templates",
    "skill_factory/generators",
    "skill_factory/validators",
    "skill_factory/installed",
    "tasks",
    "daemon/workers",
    "daemon/jobs",
    "daemon/pid",
    "setup",
    "interfaces/terminal",
    "interfaces/web/frontend",
    "interfaces/web/backend",
    "interfaces/web/public",
    "interfaces/gateways/discord",
    "interfaces/gateways/whatsapp",
    "integrations/calendar",
    "integrations/email",
    "integrations/notion",
    "integrations/github",
    "integrations/future",
    "logs",
]


def bootstrap(root_path: str = None):
    """Create required directories and set permissions."""
    base = Path(root_path or Path(__file__).parent.parent)

    print(f"[BOOTSTRAP] Setting up Custo in: {base}")

    for dir_path in REQUIRED_DIRS:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"[BOOTSTRAP] Created directory: {dir_path}")

    print("[BOOTSTRAP] Bootstrap complete!")


if __name__ == "__main__":
    bootstrap()
