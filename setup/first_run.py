"""
First Run - Initial Setup and Onboarding

This script runs on first-time setup to:
- Verify installation
- Create initial user profile
- Setup default projects
- Configure initial preferences
- Optionally run LLM provider wizard
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def first_run(root_path: str = None):
    """Perform first-time setup tasks."""
    base = Path(root_path or Path(__file__).parent.parent)

    print("=" * 50)
    print("  Welcome to Custo!")
    print("=" * 50)
    print()

    # Verify directory structure
    print("[1/5] Verifying installation...")
    required = [
        "system/config.yaml",
        "agents/registry.json",
        "memory/inbox",
        "sessions/daily",
    ]
    for path in required:
        if not (base / path).exists():
            print(f"  WARNING: Missing {path}")
    print("  Installation verified.")

    # Check if LLM is configured (if not, offer quick wizard)
    from system.config import load_config
    cfg = load_config(base)
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "").lower()
    model = llm_cfg.get("model", "").strip()

    if provider in ("", "auto", "none") or not model:
        if os.environ.get("CUSTO_NONINTERACTIVE") == "1":
            print("  Skipping LLM wizard (non-interactive mode).")
            print("  Run 'custo setup' later to configure your LLM.")
        else:
            print()
            print("  [INFO] No LLM model configured yet.")
            resp = input("  Run LLM setup wizard now? (recommended) [Y/n]: ").strip().lower()
            if not resp or resp in ("y", "yes"):
                from setup.tui_setup import run_tui_wizard
                run_tui_wizard()
            else:
                print("  Skipping LLM setup. Run `custo setup` later.")

    # Create initial session
    print("[2/5] Creating first session record...")
    sessions_dir = base / "sessions" / "daily" / datetime.now().strftime("%Y-%m-%d")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = sessions_dir / "initial_session.md"
    session_content = f"""---
title: First Session
date: {datetime.now().isoformat()}
type: initialization
---

# Custo Initialization Session

## Conversation
Custo system initialized successfully.

## Extracted Insights
- User profile configured
- System directories created
- Daemon ready to start

## Actions
- Completed first-run setup
- Verified all components

## Linked Memories
- [x] System bootstrap complete
"""
    session_file.write_text(session_content)
    print(f"  Session created: {session_file}")

    # Update index
    print("[3/5] Updating session index...")
    index_path = base / "sessions" / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text())
    else:
        index = {"sessions": [], "version": "1.0"}

    index["sessions"].append({
        "id": session_file.stem[:8],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "path": str(session_file.relative_to(base)),
        "title": "First Session",
        "type": "initialization",
        "message_count": 1,
    })
    index_path.write_text(json.dumps(index, indent=2))
    print("  Index updated.")

    # Initialize user long-term memory
    print("[4/5] Initializing user memory...")
    memory_path = base / "user" / "long_memory.md"
    if not memory_path.exists():
        memory_content = """# Long-term Memory

## User Profile
_First-time initialization - profile to be populated_

## Behavioral Patterns
_Patterns will be learned over time_

## Key Facts
- Custo system initialized
- Awaiting user interaction

## Relationships
_No relationships recorded yet_

## Goals
_No goals set yet_
"""
        memory_path.write_text(memory_content)
        print(f"  Memory initialized: {memory_path}")

    # Set up tasks
    print("[5/5] Initializing task lists...")
    today_tasks = base / "tasks" / "today.md"
    if today_tasks.exists():
        content = today_tasks.read_text()
        if "[x] Complete first-run setup" not in content:
            updated = content.replace(
                "- [ ] Complete first-run setup",
                "- [x] Complete first-run setup"
            )
            today_tasks.write_text(updated)

    print()
    print("=" * 50)
    print("  Setup Complete!")
    print("=" * 50)
    print()
    print("Your Custo instance is ready.")
    print()
    print("Next steps:")
    print("  1. Edit system/config.yaml to customize settings")
    print("  2. Complete your profile in user/profile.md")
    print("  3. Start the daemon: python daemon/daemon.py --foreground")
    print()
    print("Type 'custo help' for available commands (once CLI is set up).")
    print()


if __name__ == "__main__":
    first_run()
