"""
web commands: web (status, dev, build, start)
"""

import os
import sys
import subprocess
from pathlib import Path

from . import ROOT, print_header

OK = "[OK]"
OFF = "[--]"


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
        "start": cmd_start,
        "status": cmd_status,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown web command: {cmd}")
        print("Usage: custo web [dev|build|start|status]")


def cmd_status(args):
    """Show web interface status."""
    backend = ROOT / "interfaces" / "web" / "backend" / "app.py"
    frontend = ROOT / "interfaces" / "web" / "frontend" / "custo-ui" / "dist" / "index.html"

    print_header("Web Interface")
    print(f"  Backend:  {OK if backend.exists() else OFF}")
    print(f"  Frontend: {OK if frontend.exists() else OFF}")

    # Check if running
    import socket
    port = int(os.environ.get("CUSTO_WEB_PORT", 18790))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    running = s.connect_ex(("127.0.0.1", port)) == 0
    s.close()
    print(f"  Server:   {f'{OK} Running on port {port}' if running else OFF + ' Stopped'}")
    print()
    print("  Start server:     custo web start")
    print("  Dev mode:         custo web dev")
    print("  Build frontend:   custo web build")
    print("  Check status:     custo web status")


def cmd_dev(args):
    """Start web dev server (backend + frontend hot reload)."""
    backend = ROOT / "interfaces" / "web" / "backend" / "app.py"
    frontend_dir = ROOT / "interfaces" / "web" / "frontend" / "custo-ui"

    if not backend.exists():
        print("  Backend not found.")
        return

    port = int(os.environ.get("CUSTO_WEB_PORT", 18790))
    print_header("Web Dev Server")
    print(f"  Backend:  {backend}")
    print(f"  Frontend: {frontend_dir}")
    print(f"  Port:     {port}")
    print()
    print("  Press Ctrl+C to stop")
    print()

    # Start backend
    backend_proc = subprocess.Popen(
        [sys.executable, str(backend)],
        env={**os.environ, "CUSTO_WEB_PORT": str(port)},
    )

    # Start frontend dev server if it exists
    frontend_proc = None
    if (frontend_dir / "package.json").exists():
        print("  Starting frontend dev server...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            shell=True,
        )

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n  Stopping...")
        backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()


def cmd_build(args):
    """Build static web assets."""
    frontend_dir = ROOT / "interfaces" / "web" / "frontend" / "custo-ui"

    print_header("Building Web Assets")

    if not (frontend_dir / "package.json").exists():
        print("  Frontend not found at:", frontend_dir)
        return

    print(f"  Building frontend...")
    result = subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), shell=True)
    if result.returncode == 0:
        print(f"  {OK} Build complete")
        print(f"  Output: {frontend_dir / 'dist'}")
    else:
        print(f"  {OFF} Build failed")


def cmd_start(args):
    """Start web server (production)."""
    backend = ROOT / "interfaces" / "web" / "backend" / "app.py"

    if not backend.exists():
        print("  Backend not found.")
        return

    port = int(os.environ.get("CUSTO_WEB_PORT", 18790))
    print_header("Web Server")
    print(f"  URL:      http://127.0.0.1:{port}")
    print(f"  Backend:  {backend}")
    print()
    print("  Press Ctrl+C to stop")
    print()

    proc = subprocess.Popen(
        [sys.executable, str(backend)],
        env={**os.environ, "CUSTO_WEB_PORT": str(port)},
    )

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Stopping...")
        proc.terminate()
