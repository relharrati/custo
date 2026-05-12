"""
config commands: config (edit), reset
"""

import sys
import json
from pathlib import Path

from . import ROOT, print_header, print_table, get_config


def run(args: list[str], top_args: dict = None):
    """Dispatch config subcommands."""
    if not args:
        cmd_show([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "edit": cmd_edit,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown config command: {cmd}")
        print("Usage: custo config [edit] | custo reset")


def cmd_show(args):
    """Show current configuration."""
    from system.config import load_config
    config = load_config()
    print_header("Configuration")
    print(json.dumps(config, indent=2, default=str))
    print()
    print("  Edit:   custo config edit")
    print("  Reset:  custo reset")


def cmd_edit(args):
    """Open config file for editing."""
    cfg_path = ROOT / "system" / "config.yaml"
    if not cfg_path.exists():
        print("  Config file not found. Run 'custo init' first.")
        return

    # Try to open in system editor
    import subprocess as sp
    try:
        sp.run(["notepad", str(cfg_path)], shell=True)
    except Exception:
        try:
            sp.run(["code", str(cfg_path)], shell=True)
        except Exception:
            print(f"  Config file: {cfg_path}")
            print("  Edit manually with your preferred editor.")


def cmd_reset(args):
    """Reset Custo configuration (dangerous)."""
    import json
    from . import write_json

    print()
    print("  ⚠️  DANGER: This will reset Custo configuration.")
    print("  Your sessions, memory, and projects will NOT be deleted,")
    print("  but config will return to defaults.")
    print()
    print("  To confirm, type:  yes, reset everything")
    try:
        confirm = input("  > ")
    except (EOFError, KeyboardInterrupt):
        confirm = ""

    if confirm.strip().lower() == "yes, reset everything":
        # Reset config
        cfg_path = ROOT / "system" / "config.yaml"
        if cfg_path.exists():
            cfg_path.write_text("")
            print("  [OK] Config reset to defaults.")
        print("  Done. Run 'custo setup' to reconfigure.")
    else:
        print("  Reset cancelled.")
