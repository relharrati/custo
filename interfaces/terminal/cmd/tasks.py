"""
task/todo commands: tasks, task (add, done, remove, today, upcoming, recurring, review)
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

from . import ROOT, print_header, print_table


TASKS_DIR = ROOT / "tasks"


def _ensure_task_files():
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ["today.md", "upcoming.md", "completed.md", "recurring.md", "priorities.md"]:
        fpath = TASKS_DIR / fname
        if not fpath.exists():
            _init_task_file(fpath, fname)


def _init_task_file(fpath, fname):
    title = fname.replace(".md", "").replace("_", " ").title()
    fpath.write_text(
        f"# {title}\n\n"
        f"_Generated: {datetime.now().strftime('%Y-%m-%d')}_\n\n"
        "| # | Priority | Task | Status |\n"
        "|---|----------|------|--------|\n"
    )


def _next_id():
    """Generate next task ID from today's tasks."""
    _ensure_task_files()
    today = TASKS_DIR / "today.md"
    if not today.exists():
        return 1
    content = today.read_text()
    ids = re.findall(r"^\| (\d+) \|", content, re.MULTILINE)
    return max([int(i) for i in ids] + [0]) + 1


def run(args: list[str], top_args: dict = None):
    """Dispatch tasks|task subcommands."""
    if not args:
        cmd_tasks_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "add": cmd_add,
        "done": cmd_done,
        "remove": cmd_remove,
        "today": cmd_today,
        "upcoming": cmd_upcoming,
        "recurring": cmd_recurring,
        "review": cmd_review,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown task command: {cmd}")
        print("Usage: custo task [add|done|remove|today|upcoming|recurring|review]")


def cmd_tasks_list(args):
    """List task file overview."""
    _ensure_task_files()
    print_header("Tasks")
    tasks_dir = ROOT / "tasks"
    for f in sorted(tasks_dir.glob("*.md")):
        content = f.read_text()
        # Count task lines
        tasks = [l for l in content.split("\n") if l.startswith("| ") and len(l) > 10]
        total = len(tasks)
        done = sum(1 for l in tasks if "✅" in l or "Completed" in l or "DONE" in l.upper())
        name = f.stem.title()
        print(f"  {name:<15} {total:>3} total, {done:>3} done")
    print()
    print("Commands:  custo task add|done|remove|today|upcoming|recurring|review")


def _add_task_line(text: str, filepath: Path):
    """Append a task line to a markdown table."""
    _ensure_task_files()
    tid = _next_id()
    content = filepath.read_text()
    line = f"| {tid} | MEDIUM | {text} | Pending |\n"
    # Insert before last line (footer/spacing)
    content = content.rstrip() + "\n" + line
    filepath.write_text(content)
    return tid


def cmd_add(args):
    """Add a new task."""
    if not args:
        print("Usage: custo task add <description>")
        return

    text = " ".join(args)
    tid = _add_task_line(text, TASKS_DIR / "today.md")
    print(f"  Added task #{tid}: {text}")


def cmd_done(args):
    """Mark a task as done."""
    if not args:
        print("Usage: custo task done <id>")
        return

    tid = args[0]
    today = TASKS_DIR / "today.md"
    if not today.exists():
        print("  No tasks found.")
        return

    content = today.read_text()
    # Find and mark the task line
    lines = content.split("\n")
    modified = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {tid} |"):
            lines[i] = line.replace("Pending", "✅ Done")
            modified = True
            break

    if modified:
        today.write_text("\n".join(lines))
        print(f"  Task #{tid} marked as done!")
    else:
        print(f"  Task #{tid} not found.")


def cmd_remove(args):
    """Remove a task."""
    if not args:
        print("Usage: custo task remove <id>")
        return

    tid = args[0]
    today = TASKS_DIR / "today.md"
    if not today.exists():
        print("  No tasks found.")
        return

    content = today.read_text()
    lines = [l for l in content.split("\n") if not l.startswith(f"| {tid} |")]
    today.write_text("\n".join(lines))
    print(f"  Task #{tid} removed.")


def cmd_today(args):
    """Show today's tasks."""
    today = TASKS_DIR / "today.md"
    if today.exists():
        print(today.read_text().strip())
    else:
        print("  No tasks for today.")
    print()
    print("  Add: custo task add <description>")


def cmd_upcoming(args):
    """Show upcoming tasks."""
    upcoming = TASKS_DIR / "upcoming.md"
    if upcoming.exists():
        print(upcoming.read_text().strip())
    else:
        print("  No upcoming tasks.")


def cmd_recurring(args):
    """Show recurring tasks."""
    recurring = TASKS_DIR / "recurring.md"
    if recurring.exists():
        print(recurring.read_text().strip())
    else:
        print("  No recurring tasks.")


def cmd_review(args):
    """Review task status."""
    _ensure_task_files()
    print_header("Task Review")
    for fname in ["today.md", "upcoming.md", "recurring.md"]:
        fpath = TASKS_DIR / fname
        if fpath.exists():
            content = fpath.read_text()
            tasks = [l for l in content.split("\n") if l.startswith("| ") and len(l) > 10]
            pending = sum(1 for l in tasks if "Pending" in l or "In Progress" in l)
            done = sum(1 for l in tasks if "✅" in l or "Done" in l)
            print(f"  {fname.replace('.md','').title():<12} {len(tasks):>3} total → {pending} pending, {done} done")
