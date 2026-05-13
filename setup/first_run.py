"""
First Run - Initial Setup and Onboarding

This script runs on first-time setup to:
- Verify installation
- Create initial user profile
- Setup default projects
- Configure initial preferences
- Optionally run LLM provider wizard (arrow-key TUI)
"""

import json
import os
import sys
import subprocess
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
    missing = [p for p in required if not (base / p).exists()]
    for path in required:
        if path in missing:
            print(f"  \033[1;33mWARNING: Missing {path}\033[0m")
    if not missing:
        print("  \033[1;32m\u2713 Installation verified.\033[0m")

    # Check if LLM is configured
    from system.config import load_config
    cfg = load_config(base)
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "").lower()
    model = llm_cfg.get("model", "").strip()

    print("[2/5] Checking LLM configuration...")
    if provider in ("", "auto", "none") or not model:
        if os.environ.get("CUSTO_NONINTERACTIVE") == "1":
            print("  Skipping LLM wizard (non-interactive mode).")
            print("  Run 'custo setup' later to configure your LLM.")
        else:
            print("\n  \033[90mNo LLM model configured yet.\033[0m")
            # Arrow-key selection for the prompt
            try:
                from setup.tui_setup import HAS_INQUIRER
                if HAS_INQUIRER:
                    from InquirerPy import inquirer
                    run_wizard = inquirer.confirm(
                        message="Run the full TUI setup wizard now? (recommended)",
                        default=True,
                    ).execute()
                else:
                    ans = input("  Run LLM setup wizard now? (recommended) [Y/n]: ").strip().lower()
                    run_wizard = ans not in ("n", "no")
            except Exception:
                ans = input("  Run LLM setup wizard now? (recommended) [Y/n]: ").strip().lower()
                run_wizard = ans not in ("n", "no")

            if run_wizard:
                try:
                    from setup.tui_setup import run_tui_wizard
                    run_tui_wizard()
                except Exception as e:
                    print(f"  \033[1;31mWizard failed ({e}). Running basic setup.\033[0m")
                    _basic_fallback(base)
            else:
                print("  Skipping LLM setup. Run `custo setup` later.")
    else:
        print(f"  \033[1;32m\u2713 LLM provider: {provider}\033[0m")
        print(f"  \033[1;32m\u2713 Model: {model}\033[0m")

    # Create initial session
    print("\n[3/5] Creating first session record...")
    sessions_dir = base / "sessions" / "daily" / datetime.now().strftime("%Y-%m-%d")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_file = sessions_dir / "initial_session.md"
    if not session_file.exists():
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
        print(f"  \033[1;32m\u2713 Session created: {session_file}\033[0m")
    else:
        print(f"  \033[1;90mSession already exists.\033[0m")

    # Update index
    print("\n[4/5] Updating session index...")
    index_path = base / "sessions" / "index.json"
    if index_path.exists() and index_path.stat().st_size > 0:
        index = json.loads(index_path.read_text())
    else:
        index = {"sessions": [], "version": "1.0"}

    entry = {
        "id": session_file.stem[:8],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "path": str(session_file.relative_to(base)),
        "title": "First Session",
        "type": "initialization",
        "message_count": 1,
    }
    if entry not in index["sessions"]:
        index["sessions"].append(entry)
        index_path.write_text(json.dumps(index, indent=2))
        print(f"  \033[1;32m\u2713 Index updated.\033[0m")
    else:
        print(f"  \033[1;90mEntry already in index.\033[0m")

    # Initialize user long-term memory
    print("\n[5/5] Initializing memory...")
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
        (memory_path.parent).mkdir(parents=True, exist_ok=True)
        memory_path.write_text(memory_content)
        print(f"  \033[1;32m\u2713 Memory initialized.\033[0m")
    else:
        print(f"  \033[1;90mMemory already exists.\033[0m")

    print()
    print("=" * 50)
    print("  \033[1;32m\u2713 Setup Complete!\033[0m")
    print("=" * 50)
    print()
    print("Your Custo instance is ready.")
    print()
    print("Next steps:")
    print("  1. Edit system/config.yaml to customize settings")
    print("  2. Complete your profile in user/profile.md")
    print("  3. Start chatting:     custo chat")
    print("  4. Start daemon:       custo daemon start")
    print("  5. View all commands:  custo help")
    print()


def _basic_fallback(base):
    """Minimal fallback when the TUI wizard isn't available."""
    print("\n  Running basic LLM setup...")
    from setup.init_config import _detect_ram, _provider_menu, _basic_llm_wizard
    ram_gb = _detect_ram()
    print(f"  Detected RAM: ~{ram_gb} GB")
    provider = _provider_menu()
    llm_config = {"provider": "hardcoded", "model": "", "auto_download": False}

    if provider == "ollama":
        from setup.init_config import _run_ollama_wizard
        llm_config = _run_ollama_wizard(ram_gb)
    elif provider == "lmstudio":
        from setup.init_config import _run_lmstudio_wizard
        llm_config = _run_lmstudio_wizard(ram_gb)
    elif provider == "vllm":
        from setup.init_config import _run_vllm_wizard
        llm_config = _run_vllm_wizard(ram_gb)

    from system.config import load_config, save_config
    cfg = load_config(base)
    cfg["llm"] = {**cfg.get("llm", {}), **llm_config,
                  "context_window": 4096, "temperature": 0.7, "max_tokens": 512}
    save_config(cfg, base)
    print("\n  Saved to system/config.yaml")


if __name__ == "__main__":
    first_run()