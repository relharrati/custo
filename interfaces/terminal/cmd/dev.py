"""
dev/utility commands: logs, debug, test, version, export, backup, restore
"""

import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

from . import ROOT, print_header, print_table


def run(args: list[str], top_args: dict = None):
    """Dispatch dev subcommands."""
    if args:
        cmd = args[0]
        sub = args[1:]

        handlers = {
            "logs": cmd_logs,
            "debug": cmd_debug,
            "test": cmd_test,
            "export": cmd_export,
            "backup": cmd_backup,
            "restore": cmd_restore,
        }
        handler = handlers.get(cmd)
        if handler:
            handler(sub)
            return

    # Default: show dev info
    cmd_version([])


def cmd_version(args):
    """Show version info."""
    try:
        from system.versions import get_version
        ver = get_version()
    except ImportError:
        ver = "0.2.0-dev"
    print_header(f"Custo {ver}")
    print(f"  Python:   {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")
    print(f"  Root:     {ROOT}")
    print()
    print("  Debug:     custo debug")
    print("  Logs:      custo logs")
    print("  Test:      custo test")
    print("  Backup:    custo backup")
    print("  Export:    custo export")


def cmd_logs(args):
    """Show recent log files."""
    log_dir = ROOT / "logs"
    if not log_dir.exists():
        print("  No log directory found.")
        return

    log_files = sorted(log_dir.glob("*.log"), reverse=True)
    if not log_files:
        print("  No log files found.")
        return

    print_header("Log Files")
    for lf in log_files[:10]:
        size = lf.stat().st_size
        mtime = datetime.fromtimestamp(lf.stat().st_mtime).strftime("%H:%M")
        print(f"  {mtime}  {lf.name:<35} {size:>8} bytes")

    # Show tail of latest
    latest = log_files[0]
    lines = latest.read_text().strip().split("\n")
    tail = lines[-15:] if len(lines) > 15 else lines
    print()
    print(f"  --- tail of {latest.name} (last {len(tail)} lines) ---")
    for line in tail:
        print(f"  {line}")


def cmd_debug(args):
    """Run debug diagnostic."""
    print_header("Debug Info")
    print()

    # System paths
    print("  Paths:")
    print(f"    Root:     {ROOT}")
    print(f"    Config:   {ROOT / 'system' / 'config.yaml'}")
    print(f"    Index:    {ROOT / 'sessions' / 'index.json'}")
    print()

    # Directory sizes
    print("  Data sizes:")
    for d in ["sessions", "memory", "tasks", "logs"]:
        dpath = ROOT / d
        if dpath.exists():
            file_count = sum(1 for _ in dpath.rglob("*") if _.is_file())
            total_size = sum(f.stat().st_size for f in dpath.rglob("*") if f.is_file())
            print(f"    {d:<12} {file_count:>5} files  {total_size / 1024:>8.1f} KB")

    # Check for common issues
    print()
    print("  Checks:")
    cfg_path = ROOT / "system" / "config.yaml"
    print(f"    Config exists:     {'Yes' if cfg_path.exists() else 'No'}")
    idx_path = ROOT / "sessions" / "index.json"
    idx_ok = idx_path.exists() and idx_path.stat().st_size > 0
    print(f"    Sessions indexed:  {'Yes' if idx_ok else 'No'}")

    try:
        import yaml
        print(f"    PyYAML:            Yes ({yaml.__version__})")
    except ImportError:
        print(f"    PyYAML:            No")

    print()
    print("  Run 'custo doctor' for full health check.")


def cmd_test(args):
    """Run the test suite."""
    print("  Running test suite...")
    print()

    test_dir = ROOT / "tests"
    if not test_dir.exists():
        print("  No tests/ directory found.")
        return

    test_files = sorted(test_dir.glob("test_*.py"))
    if not test_files:
        print("  No test files found.")
        return

    results = {"pass": 0, "fail": 0, "error": 0}
    for tf in test_files:
        name = tf.stem.replace("test_", "")
        try:
            proc = subprocess.run(
                [sys.executable, str(tf)],
                capture_output=True, text=True, timeout=30,
                env={**__import__('os').environ, "PYTHONPATH": str(ROOT)},
            )
            if "PASS" in proc.stdout or "OK" in proc.stdout or proc.returncode == 0:
                print(f"  ✅ {name:<35} PASS")
                results["pass"] += 1
            elif "FAIL" in proc.stdout or proc.returncode != 0:
                print(f"  ❌ {name:<35} FAIL")
                print(f"      {proc.stdout.strip()[-100:]}")
                results["fail"] += 1
            else:
                print(f"  ⚠️  {name:<35} ? ({proc.returncode})")
                results["error"] += 1
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  {name:<35} TIMEOUT")
            results["error"] += 1
        except Exception as e:
            print(f"  💥 {name:<35} ERROR: {e}")
            results["error"] += 1

    print()
    total = sum(results.values())
    print(f"  Results: {results['pass']}/{total} passed")
    if results["fail"] > 0:
        print(f"  Failures: {results['fail']}")
    if results["error"] > 0:
        print(f"  Errors: {results['error']}")


def cmd_export(args):
    """Export Custo data."""
    import zipfile
    from io import BytesIO

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_name = f"custo_export_{timestamp}.zip"
    export_path = ROOT / export_name

    print(f"  Exporting to {export_name}...")

    with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, dirs, files in ROOT.walk():
            # Skip pycache and logs
            if "__pycache__" in root_dir.name:
                continue
            for f in files:
                if f.endswith((".py", ".md", ".yaml", ".json", ".txt", ".bat")):
                    fpath = root_dir / f
                    arcname = str(fpath.relative_to(ROOT))
                    zf.write(fpath, arcname)

    size_kb = export_path.stat().st_size / 1024
    print(f"  Done: {export_name} ({size_kb:.1f} KB)")


def cmd_backup(args):
    """Create a backup archive."""
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"custo_backup_{timestamp}"
    backup_dir = ROOT.parent / backup_name

    print(f"  Creating backup at {backup_dir}...")

    # Copy key directories
    for d in ["system", "agents", "sessions", "memory", "tasks", "projects", "interfaces", "daemon", "setup"]:
        src = ROOT / d
        if src.exists():
            dst = backup_dir / d
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            print(f"    Copied {d}/")

    # Copy key files
    for f in ["custo", "custo.bat", "README.md", "BOOTSTRAP.md", "system/config.yaml"]:
        src = ROOT / f
        if src.exists():
            shutil.copy2(src, backup_dir / f)
            print(f"    Copied {f}")

    print(f"\n  Backup created: {backup_dir}")


def cmd_restore(args):
    """Restore from a backup."""
    if not args:
        print("Usage: custo restore <backup_path>")
        print("Example: custo restore ../custo_backup_20260512_091500")
        return

    backup_path = Path(args[0])
    if not backup_path.exists() or not backup_path.is_dir():
        print(f"  Backup not found: {backup_path}")
        return

    import shutil
    print(f"  Restoring from {backup_path}...")

    for item in backup_path.iterdir():
        dst = ROOT / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
        print(f"    Restored {item.name}")

    print("  Restore complete. Run 'custo doctor' to verify.")
