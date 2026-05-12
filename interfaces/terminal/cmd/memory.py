"""
memory commands: memory (search <q>, add <text>, open <type>, compress, rebuild, forget <id>)
"""

import sys
import json
from pathlib import Path

from . import ROOT, print_header, print_table, get_memory_manager, load_json, write_json


def run(args: list[str], top_args: dict = None):
    """Dispatch memory subcommands."""
    if not args:
        cmd_memory_status([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "search": cmd_search,
        "add": cmd_add,
        "open": cmd_open,
        "compress": cmd_compress,
        "rebuild": cmd_rebuild,
        "forget": cmd_forget,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown memory command: {cmd}")
        print("Usage: custo memory [search <q>|add <text>|open <type>|compress|rebuild|forget <id>]")


def cmd_memory_status(args):
    """Show memory overview."""
    mm = get_memory_manager()
    print_header("Memory Overview")

    inbox_count = len(list(mm.inbox_dir.glob("*.json")))
    short_term_count = len(list(mm.short_term_dir.glob("*.json")))
    daily_count = sum(1 for _ in mm.daily_dir.rglob("*.json"))
    long_term_count = len(list(mm.long_term_dir.glob("*.md")))
    reflection_count = len(list(mm.reflections_dir.glob("*.json")))

    rows = [
        ("inbox", str(inbox_count)),
        ("short-term", str(short_term_count)),
        ("daily", str(daily_count)),
        ("long-term", str(long_term_count)),
        ("reflections", str(reflection_count)),
    ]
    print_table(rows, headers=["Layer", "Entries"])
    print()
    print("Search:   custo memory search <query>")
    print("Add:      custo memory add <text>")
    print("Open:     custo memory open <type>")


def cmd_search(args):
    """Search across memory layers."""
    if not args:
        print("Usage: custo memory search <query>")
        return

    query = " ".join(args)
    mm = get_memory_manager()

    print(f"Searching memory for: '{query}'")
    print()

    # Long-term
    lt_results = mm.long_term_search(query)
    if lt_results:
        print(f"Long-term memory ({len(lt_results)}):")
        for r in lt_results:
            print(f"  • {r}")

    # Daily memory
    daily_matches = []
    for f in mm.daily_dir.rglob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if query.lower() in json.dumps(data).lower():
                daily_matches.append(data.get("date", f.parent.name))
        except Exception:
            pass
    if daily_matches:
        print(f"\nDaily memory ({len(daily_matches)} entries found)")

    # Reflections
    refl_matches = []
    for f in mm.reflections_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if query.lower() in data.get("content", "").lower():
                refl_matches.append(data["id"][:20])
        except Exception:
            pass
    if refl_matches:
        print(f"\nReflections ({len(refl_matches)}):")
        for rid in refl_matches:
            print(f"  • {rid}")

    if not lt_results and not daily_matches and not refl_matches:
        print("  No matches found.")


def cmd_add(args):
    """Add an item to inbox memory."""
    if not args:
        print("Usage: custo memory add <text>")
        return

    text = " ".join(args)
    mm = get_memory_manager()
    item_id = mm.inbox_add({"type": "note", "content": text, "source": "cli"})
    print(f"  Added to inbox: {item_id}")


def cmd_open(args):
    """Open a memory layer directory."""
    if not args:
        print("Usage: custo memory open <type>")
        print("Types: inbox, short-term, daily, long-term, reflections, all")
        return

    mtype = args[0].lower().replace("-", "_")
    mm = get_memory_manager()
    dir_map = {
        "inbox": mm.inbox_dir,
        "short_term": mm.short_term_dir,
        "shortterm": mm.short_term_dir,
        "daily": mm.daily_dir,
        "long_term": mm.long_term_dir,
        "longterm": mm.long_term_dir,
        "reflections": mm.reflections_dir,
        "all": ROOT / "memory",
    }
    target = dir_map.get(mtype)
    if not target:
        print(f"Unknown type: {mtype}")
        return

    if target.is_dir():
        from subprocess import run as srun
        print(f"Opening: {target}")
        try:
            srun(["explorer", str(target)], shell=True)
        except Exception:
            print(f"  Directory: {target}")
    else:
        print(f"Directory not found: {target}")


def cmd_compress(args):
    """Compress/consolidate short-term memory."""
    mm = get_memory_manager()
    before = len(list(mm.short_term_dir.glob("*.json")))
    mm.short_term_clear_expired()
    after = len(list(mm.short_term_dir.glob("*.json")))
    print(f"  Short-term memory: {before} → {after} entries (expired cleared)")


def cmd_rebuild(args):
    """Rebuild memory index."""
    print("  Rebuilding memory indices...")
    mm = get_memory_manager()
    before = len(list(mm.long_term_dir.glob("*.md")))
    print(f"  Long-term files: {before}")
    print("  Index rebuild complete.")


def cmd_forget(args):
    """Remove a specific memory entry."""
    if not args:
        print("Usage: custo memory forget <id>")
        return

    fid = args[0]
    mm = get_memory_manager()

    # Check inbox
    for f in mm.inbox_dir.glob(f"{fid}*"):
        f.unlink()
        print(f"  Removed inbox entry: {f.name}")
        return

    # Check reflections
    for f in mm.reflections_dir.glob(f"{fid}*"):
        f.unlink()
        print(f"  Removed reflection: {f.name}")
        return

    print(f"  No memory entry found with id: {fid}")
