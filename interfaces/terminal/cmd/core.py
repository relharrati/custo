"""
core commands: chat, ask, shell
"""

import sys
import asyncio
from pathlib import Path

from . import ROOT, print_header


def run(args: list[str], top_args: dict = None):
    """Dispatch core subcommands."""
    if not args:
        print("Usage: custo chat | custo ask <question> | custo shell")
        return

    cmd = args[0]
    sub = args[1:]

    if cmd == "chat":
        cmd_chat(sub)
    elif cmd == "ask":
        cmd_ask(sub)
    elif cmd == "shell":
        cmd_shell(sub)
    else:
        print(f"Unknown core command: {cmd}")
        print("Available: chat, ask <question>, shell")


def cmd_chat(args: list[str]):
    """Launch interactive TUI chat."""
    from interfaces.terminal.tui import ChatTUI
    tui = ChatTUI()
    asyncio.run(tui.run())


def cmd_ask(args: list[str]):
    """Ask a one-shot question and get a response."""
    if not args:
        print("Usage: custo ask <question>")
        print("Example: custo ask 'summarize my project'")
        return

    question = " ".join(args)

    async def _ask():
        from agents.main.agent import MainAgent
        agent = MainAgent(ROOT)
        await agent.start()

        from sessions.manager import SessionManager
        sm = SessionManager(ROOT)
        sess = sm.create_session(title=f"Ask: {question[:40]}")

        result = await agent.process_task({
            "type": "user_message",
            "content": question,
            "session_id": sess["id"]
        })
        print()
        print(result.get("content", ""))
        print()
        await agent.stop()

    asyncio.run(_ask())


def cmd_shell(args: list[str]):
    """Interactive REPL-like shell. Not yet implemented."""
    print("Interactive shell mode — not yet implemented.")
    print("Use 'custo chat' for interactive conversation.")
