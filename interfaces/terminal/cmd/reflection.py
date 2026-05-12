"""
reflection/optimization commands: reflect, review, optimize, learnings
"""

from datetime import datetime
from pathlib import Path

from . import ROOT, print_header, print_table, get_memory_manager


def run(args: list[str], top_args: dict = None):
    """Dispatch reflection subcommands."""
    if not args:
        cmd_reflect([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "today": cmd_review_today,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown reflection command: {cmd}")
        print("Usage: custo reflect | custo review today | custo optimize | custo learnings")


def cmd_reflect(args):
    """Generate a reflection on current state."""
    mm = get_memory_manager()

    # Gather context
    inbox_pending = len(mm.inbox_get_pending(100))
    today_sessions_dir = ROOT / "sessions" / "daily" / datetime.now().strftime("%Y-%m-%d")
    session_count = len(list(today_sessions_dir.glob("*.md"))) if today_sessions_dir.exists() else 0

    reflection = (
        f"## Reflection - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"- **State**: System operational\n"
        f"- **Sessions today**: {session_count}\n"
        f"- **Inbox pending**: {inbox_pending}\n"
        f"- **Uptime**: {datetime.now().strftime('%H:%M')}\n"
    )

    rid = mm.reflection_write(reflection, tags=["auto", "cli"])
    print(reflection)
    print(f"  Reflection saved: {rid}")


def cmd_review_today(args):
    """Review today's activity."""
    print_header(f"Today's Review — {datetime.now().strftime('%Y-%m-%d')}")
    print()

    # Sessions
    today = datetime.now().strftime("%Y-%m-%d")
    sessions_dir = ROOT / "sessions" / "daily" / today
    if sessions_dir.exists():
        session_files = list(sessions_dir.glob("*.md"))
        print(f"  Sessions: {len(session_files)}")
        for sf in session_files[-5:]:
            size = sf.stat().st_size
            print(f"    • {sf.stem}  ({size} bytes)")
    else:
        print("  Sessions: 0")

    # Tasks
    today_file = ROOT / "tasks" / "today.md"
    if today_file.exists():
        content = today_file.read_text()
        task_lines = [l for l in content.split("\n") if l.startswith("| ") and len(l) > 10]
        done = sum(1 for l in task_lines if "✅" in l)
        print(f"  Tasks: {len(task_lines)} ({done} done)")

    # Memory
    mm = get_memory_manager()
    inbox = len(list(mm.inbox_dir.glob("*.json")))
    print(f"  Memory inbox: {inbox} items")

    # Log summary
    log_dir = ROOT / "logs"
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.log"), reverse=True)
        if log_files:
            latest = log_files[0]
            lines = latest.read_text().split("\n")
            errors = sum(1 for l in lines if "ERROR" in l)
            print(f"  Log errors today: {errors}")
    print()
    print("  Run 'custo reflect' for a full reflection.")
    print("  Run 'custo optimize' for optimization suggestions.")


def cmd_optimize(args):
    """Show optimization suggestions."""
    print_header("Optimization Suggestions")
    print()
    print("  Based on today's activity:\n")

    # Check session count
    today = datetime.now().strftime("%Y-%m-%d")
    sessions_dir = ROOT / "sessions" / "daily" / today
    if sessions_dir.exists():
        n = len(list(sessions_dir.glob("*.md")))
        if n > 20:
            print(f"  ⚡ High session count ({n}). Consider:")
            print(f"     - Memory compression:  custo memory compress")
            print(f"     - Memory rebuild:      custo memory rebuild")

    # Check inbox
    mm = get_memory_manager()
    inbox_pending = len(mm.inbox_get_pending(100))
    if inbox_pending > 10:
        print(f"  ⚡ Unprocessed inbox items ({inbox_pending}). Consider:")
        print(f"     - Review inbox:   custo memory open inbox")

    # Check task completion
    today_file = ROOT / "tasks" / "today.md"
    if today_file.exists():
        content = today_file.read_text()
        task_lines = [l for l in content.split("\n") if l.startswith("| ") and len(l) > 10]
        if task_lines:
            done = sum(1 for l in task_lines if "✅" in l)
            pct = int(done / len(task_lines) * 100)
            print(f"  {'✅' if pct > 50 else '📋'} Task completion: {pct}% ({done}/{len(task_lines)})")

    print()
    print("  Learn more:   custo learnings")


def cmd_learnings(args):
    """Show extracted learnings/insights."""
    print_header("Learnings & Insights")
    print()
    print("  Extracted patterns from today's activity:\n")
    print("  • (No significant patterns yet — more data needed)")
    print()
    print("  To extract learnings from a session:")
    print("    custo reflect         — Generate reflection")
    print("    custo review today    — Review daily activity")
