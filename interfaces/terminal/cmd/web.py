"""
web commands: web (dev, build)
"""

from . import ROOT, print_header


def run(args: list[str], top_args: dict = None):
    """Dispatch web subcommands."""
    if not args:
        cmd_status([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "dev": cmd_dev,
        "build": cmd_build,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown web command: {cmd}")
        print("Usage: custo web [dev|build]")


def cmd_status(args):
    """Show web interface status."""
    web_dir = ROOT / "interfaces" / "web"
    has_fastapi = (web_dir / "main.py").exists() if web_dir.exists() else False
    has_html = (web_dir / "templates").exists() if web_dir.exists() else False

    print_header("Web Interface")
    print(f"  Status: {'setup ready' if has_fastapi else 'not yet installed'}")
    print(f"  API:    {'✓' if has_fastapi else '○'}")
    print(f"  UI:     {'✓' if has_html else '○'}")
    print()
    print("  Start dev server:   custo web dev")
    print("  Build static:       custo web build")


def cmd_dev(args):
    """Start web dev server."""
    web_dir = ROOT / "interfaces" / "web"
    main_py = web_dir / "main.py"
    if main_py.exists():
        print("  Starting web dev server...")
        import subprocess, sys
        subprocess.run([sys.executable, str(main_py)])
    else:
        print("  Web interface not yet implemented.")
        print("  To install: FastAPI backend + HTML dashboard")
        print("  Run 'custo doctor' for setup guidance.")


def cmd_build(args):
    """Build static web assets."""
    print("  Building web assets... (not yet implemented)")
