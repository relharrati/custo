"""
cmd - Custo Command Modules

Each module exports a dispatch function `run(args: list[str]) -> None`
that handles its command tree. Shared utilities live here in __init__.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# ── Project root ─────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent.parent  # G:\Custo


def root_path() -> Path:
    """Resolve project root from any call site."""
    return ROOT


def get_session_manager() -> "SessionManager":
    from sessions.manager import SessionManager
    return SessionManager(ROOT)


def get_memory_manager() -> "MemoryManager":
    from memory.manager import get_memory_manager
    return get_memory_manager(ROOT)


def get_registry():
    from agents.registry import get_registry
    return get_registry(ROOT)


def get_config():
    from system.config import load_config
    return load_config()


def load_json(path: Path):
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def print_header(title: str):
    width = 60
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_table(rows, headers=None):
    """Simple column-aligned table printer."""
    if not rows:
        return
    col_widths = []
    for col_idx in range(len(rows[0])):
        col_widths.append(max(len(str(r[col_idx])) for r in rows))
    if headers:
        fmt = "  ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
        print(fmt)
        print("-" * len(fmt))
    for row in rows:
        print("  ".join(f"{str(c):<{w}}" for c, w in zip(row, col_widths)))


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)
