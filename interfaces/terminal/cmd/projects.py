"""
project commands: projects, project (create, open, archive, delete, summary, sessions)
"""

import sys
import json
from datetime import datetime
from pathlib import Path

from . import ROOT, print_header, print_table


def run(args: list[str], top_args: dict = None):
    """Dispatch projects|project subcommands."""
    if not args:
        cmd_projects_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "create": cmd_create,
        "open": cmd_open,
        "archive": cmd_archive,
        "delete": cmd_delete,
        "summary": cmd_summary,
        "sessions": cmd_sessions,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown project command: {cmd}")
        print("Usage: custo project [create <name>|open <name>|archive <name>|delete <name>|summary <name>|sessions <name>]")


def cmd_projects_list(args):
    """List all projects (active + archived)."""
    active_dir = ROOT / "projects" / "active"
    archived_dir = ROOT / "projects" / "archived"

    active = sorted([d.name for d in active_dir.iterdir() if d.is_dir()]) if active_dir.exists() else []
    archived = sorted([d.name for d in archived_dir.iterdir() if d.is_dir()]) if archived_dir.exists() else []

    print_header(f"Projects ({len(active)} active, {len(archived)} archived)")

    if active:
        print("\nActive:")
        for p in active:
            print(f"  • {p}")
    if archived:
        print("\nArchived:")
        for p in archived:
            print(f"  • {p}")

    if not active and not archived:
        print("\n  No projects yet. Create one: custo project create <name>")

    print()
    print("Commands:  custo project create|open|archive|delete|summary|sessions")


def cmd_create(args):
    """Create a new project."""
    if not args:
        print("Usage: custo project create <name>")
        return

    name = " ".join(args).strip().replace(" ", "-").lower()
    project_dir = ROOT / "projects" / "active" / name
    if project_dir.exists():
        print(f"  Project '{name}' already exists.")
        return

    project_dir.mkdir(parents=True)
    project_md = project_dir / "project.md"
    project_md.write_text(
        f"# {name}\n\n"
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"## Overview\n\n\n"
        f"## Goals\n\n\n"
        f"## Notes\n"
    )
    print(f"  Created project '{name}'")
    print(f"  Location: {project_dir}")


def cmd_open(args):
    """Open a project directory."""
    if not args:
        print("Usage: custo project open <name>")
        return

    name = " ".join(args)
    project_dir = ROOT / "projects" / "active" / name
    if not project_dir.exists():
        project_dir = ROOT / "projects" / "archived" / name

    if not project_dir.exists():
        print(f"  Project '{name}' not found.")
        return

    # Display project.md
    project_md = project_dir / "project.md"
    if project_md.exists():
        print(project_md.read_text().strip())
    else:
        print(f"  Opened project: {name} ({project_dir})")


def cmd_archive(args):
    """Archive a project."""
    if not args:
        print("Usage: custo project archive <name>")
        return

    name = " ".join(args)
    src = ROOT / "projects" / "active" / name
    if not src.exists():
        print(f"  Active project '{name}' not found.")
        return

    dst = ROOT / "projects" / "archived" / name
    src.rename(dst)
    print(f"  Archived '{name}' → projects/archived/")


def cmd_delete(args):
    """Delete a project."""
    if not args:
        print("Usage: custo project delete <name>")
        return

    name = " ".join(args)
    for base in [ROOT / "projects" / "active", ROOT / "projects" / "archived"]:
        target = base / name
        if target.exists():
            import shutil
            shutil.rmtree(target)
            print(f"  Deleted project '{name}'")
            return
    print(f"  Project '{name}' not found.")


def cmd_summary(args):
    """Show a project summary."""
    if not args:
        print("Usage: custo project summary <name>")
        return

    name = " ".join(args)
    project_dir = ROOT / "projects" / "active" / name
    if not project_dir.exists():
        project_dir = ROOT / "projects" / "archived" / name
    if not project_dir.exists():
        print(f"  Project '{name}' not found.")
        return

    project_md = project_dir / "project.md"
    if project_md.exists():
        content = project_md.read_text()
        lines = content.strip().split("\n")
        print(f"  Project: {name}")
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                print(f"    {line}")

    # Count sessions mentioning this project
    sessions_dir = ROOT / "sessions" / "daily"
    mentions = 0
    if sessions_dir.exists():
        for date_dir in sessions_dir.iterdir():
            if date_dir.is_dir():
                for md_file in date_dir.glob("*.md"):
                    if name.lower() in md_file.read_text().lower():
                        mentions += 1
    print(f"  Session mentions: {mentions}")


def cmd_sessions(args):
    """List sessions that mention a project."""
    if not args:
        print("Usage: custo project sessions <name>")
        return

    name = " ".join(args).lower()
    sessions_dir = ROOT / "sessions" / "daily"
    if not sessions_dir.exists():
        print("  No sessions found.")
        return

    found = []
    for date_dir in sorted(sessions_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for md_file in sorted(date_dir.glob("*.md"), reverse=True):
            content = md_file.read_text(encoding="utf-8")
            if name in content.lower():
                found.append((date_dir.name, md_file.stem))
                if len(found) >= 20:
                    break
        if len(found) >= 20:
            break

    if found:
        print(f"  Sessions mentioning '{name}':")
        for date, sid in found:
            print(f"    {date}  {sid}")
    else:
        print(f"  No sessions mention '{name}'.")
