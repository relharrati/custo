"""
daemon commands: daemon (start, stop, restart, status, logs)
"""

import sys
import json
import subprocess
from pathlib import Path

from . import ROOT, print_header, print_table


def run(args: list[str], top_args: dict = None):
    """Dispatch daemon subcommands."""
    if not args:
        cmd_status([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "logs": cmd_logs,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown daemon command: {cmd}")
        print("Usage: custo daemon [start|stop|restart|status|logs]")


def cmd_start(args):
    """Start the Custo daemon."""
    print_header("Starting Daemon")

    async def _start():
        from daemon.supervisor import Supervisor
        from agents.registry import get_registry
        registry = get_registry(ROOT)
        await registry.load()
        sup = Supervisor(ROOT)
        await sup.start()

        import asyncio
        await asyncio.sleep(2)
        status = sup.get_agent_status()
        for name, info in status.items():
            icon = "✅" if info.get("running") else "❌"
            print(f"  {icon} {name}: {info.get('status', '?')}")

        print()
        print("  Daemon running. Keep this terminal open.")
        print("  Press Ctrl+C to stop.")
        try:
            while True:
                import asyncio
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await sup.stop()
            print("  Daemon stopped.")

    import asyncio
    asyncio.run(_start())


def cmd_stop(args):
    """Stop the Custo daemon."""
    print("  Stopping daemon... (not yet implemented for background mode)")
    print("  If running in foreground, press Ctrl+C.")


def cmd_restart(args):
    """Restart the daemon."""
    cmd_stop(args)
    cmd_start(args)


def cmd_status(args):
    """Show daemon and agent status."""
    print_header("Daemon Status")

    async def _check():
        from daemon.supervisor import Supervisor
        from agents.registry import get_registry
        registry = get_registry(ROOT)
        await registry.load()

        # Check if daemon process is running
        daemon_scripts = list((ROOT / "daemon").glob("daemon*.py"))
        print(f"  Daemon scripts: {len(daemon_scripts)}")
        print(f"  Registry agents: {len(registry.agents)}")

        rows = []
        for agent_type, config in registry.agents.items():
            agent_dir = ROOT / "agents" / agent_type
            has_script = (agent_dir / "agent.py").exists()
            rows.append((agent_type, "present" if has_script else "missing"))
        print()
        print_table(rows, headers=["Agent", "Status"])

    import asyncio
    asyncio.run(_check())
    print()
    print("Start daemon:    custo daemon start")
    print("View logs:       custo daemon logs")


def cmd_logs(args):
    """Show daemon logs."""
    log_dir = ROOT / "logs"
    if not log_dir.exists():
        print("  No log directory found.")
        return

    log_files = sorted(log_dir.glob("*.log"), reverse=True)
    if not log_files:
        print("  No log files found.")
        return

    print_header("Daemon Logs")
    for lf in log_files[:5]:
        size = lf.stat().st_size
        print(f"  {lf.name:<30} {size:>8} bytes")
    print()
    # Show tail of latest log
    latest = log_files[0]
    lines = latest.read_text().strip().split("\n")
    tail = lines[-20:] if len(lines) > 20 else lines
    print(f"  --- tail of {latest.name} ---")
    for line in tail:
        print(f"  {line}")
