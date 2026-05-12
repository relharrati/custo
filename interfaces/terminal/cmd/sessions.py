"""
session commands: sessions (today, open <id>, search <q>, delete <id>), resume
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

from . import ROOT, print_header, print_table, get_session_manager


def run(args: list[str], top_args: dict = None):
    """Dispatch sessions subcommands."""
    if not args:
        cmd_sessions_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "today": cmd_today,
        "open": cmd_open,
        "search": cmd_search,
        "delete": cmd_delete,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown sessions command: {cmd}")
        print("Usage: custo sessions [today|open <id>|search <q>|delete <id>]")


def cmd_sessions_list(args):
    """List all sessions."""
    sm = get_session_manager()
    today = datetime.now().strftime("%Y-%m-%d")

    # Get from index
    idx_path = ROOT / "sessions" / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"sessions": []}
    sessions = index.get("sessions", [])

    if not sessions:
        print("No sessions found.")
        return

    print_header(f"Sessions ({len(sessions)} total)")
    rows = []
    for s in sessions[-15:]:  # last 15
        label = "today" if s.get("date") == today else s.get("date", "?")
        rows.append((s["id"][:8], label, s.get("title", "?"), s.get("message_count", 0)))
    print_table(rows, headers=["ID", "Date", "Title", "Msgs"])


def cmd_today(args):
    """Show today's sessions."""
    sm = get_session_manager()
    today_sessions = sm.get_today_sessions()

    if not today_sessions:
        print("No sessions today.")
        return

    print_header(f"Today's Sessions ({len(today_sessions)})")
    rows = []
    for s in today_sessions:
        rows.append((s["id"][:8], s.get("title", "?"), s.get("message_count", 0)))
    print_table(rows, headers=["ID", "Title", "Msgs"])
    print()
    print("Open a session: custo sessions open <id>")


def cmd_open(args):
    """Open a session to view its content."""
    if not args:
        print("Usage: custo sessions open <session_id>")
        return

    sid = args[0]

    sm = get_session_manager()
    entry = sm.get_session(sid)
    if not entry:
        print(f"Session '{sid}' not found.")
        return

    # Read the markdown file
    md_path = ROOT / entry.get("path", "")
    if not md_path.exists():
        # Try constructing path from date/id
        md_path = ROOT / "sessions" / "daily" / entry["date"] / f"{sid}.md"

    if md_path.exists():
        print(md_path.read_text(encoding="utf-8"))
    else:
        print(f"Session file not found on disk ({md_path})")
        print(f"  Index entry: {json.dumps(entry, indent=2)}")


def cmd_search(args):
    """Search sessions for text."""
    if not args:
        print("Usage: custo sessions search <query>")
        return

    query = " ".join(args).lower()
    print(f"Searching sessions for: '{query}'")
    print()

    daily_dir = ROOT / "sessions" / "daily"
    if not daily_dir.exists():
        print("No session data found.")
        return

    found = 0
    for date_dir in sorted(daily_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for md_file in sorted(date_dir.glob("*.md"), reverse=True):
            content = md_file.read_text(encoding="utf-8")
            if query in content.lower():
                if found < 20:
                    lines = content.strip().split("\n")
                    title = "?"
                    for line in lines:
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip()
                            break
                    print(f"  [{md_file.stem}] {date_dir.name} — {title}")
                found += 1

    print()
    if found == 0:
        print("  No matches found.")
    elif found > 20:
        print(f"  ... and {found - 20} more matches.")
    else:
        print(f"  {found} match(es). Open with: custo sessions open <id>")


def cmd_delete(args):
    """Delete a session."""
    if not args:
        print("Usage: custo sessions delete <session_id>")
        return

    sid = args[0]
    sm = get_session_manager()
    entry = sm.get_session(sid)
    if not entry:
        print(f"Session '{sid}' not found.")
        return

    # Mark deleted in index
    idx_path = ROOT / "sessions" / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"sessions": []}
    initial_count = len(index.get("sessions", []))
    index["sessions"] = [s for s in index.get("sessions", []) if s["id"] != sid]
    idx_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    # Remove file
    md_path = ROOT / "sessions" / "daily" / entry.get("date", "") / f"{sid}.md"
    if md_path.exists():
        md_path.unlink()
        print(f"  Removed: {md_path}")

    print(f"  Session '{sid}' deleted ({initial_count - len(index['sessions'])} removed from index).")


# ── resume alias ─────────────────────────────────────────────────

def cmd_resume(args: list[str]):
    """Resume the most recent session or a specific one."""
    sm = get_session_manager()
    idx_path = ROOT / "sessions" / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"sessions": []}
    sessions = index.get("sessions", [])

    if args:
        # Resume specific session
        sid = args[0]
        entry = sm.get_session(sid)
        if not entry:
            print(f"Session '{sid}' not found.")
            return
    else:
        # Resume most recent session
        if not sessions:
            print("No previous sessions. Starting fresh.")
            from .core import cmd_chat
            cmd_chat([])
            return
        entry = sessions[-1]

    print(f"Resuming session {entry['id'][:8]} — {entry.get('title', '')}")
    print()

    from interfaces.terminal.tui import ChatTUI
    tui = ChatTUI()
    tui.session_id = entry["id"]
    asyncio.run(tui.run())
