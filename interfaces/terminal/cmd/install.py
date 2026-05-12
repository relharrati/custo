"""
installation / onboarding commands: install, setup, onboard, init, doctor, upgrade
"""

import sys
import subprocess
from pathlib import Path

from . import ROOT, print_header


def run(args: list[str], top_args: dict = None):
    """Dispatch installation subcommands."""
    if not args:
        print("Usage: custo <install|setup|onboard|init|doctor|upgrade>")
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "install": cmd_install,
        "setup": cmd_setup,
        "onboard": cmd_onboard,
        "init": cmd_init,
        "doctor": cmd_doctor,
        "upgrade": cmd_upgrade,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown command: custo {cmd}")


def cmd_install(args):
    """Install Custo dependencies."""
    print_header("Custo Install")
    print("Checking environment...")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")
    print()
    try:
        import yaml
        print("  [OK] PyYAML found")
    except ImportError:
        print("  [..] Installing PyYAML...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
        print("  [OK] PyYAML installed")
    print()
    print("Installation complete. Run: custo setup")


def cmd_setup(args):
    """Run interactive setup / LLM wizard."""
    print_header("Custo Setup")
    print()
    try:
        from setup.init_config import run_wizard
        run_wizard()
    except ImportError as e:
        print(f"Setup wizard not available ({e}).")
        print("Run: python setup/init_config.py --wizard")


def cmd_onboard(args):
    """First-time onboarding tour."""
    print_header("Custo Onboarding")
    print()
    print("Welcome to Custo! Let's get you started.\n")
    print("  Step 1: Setup LLM  →  custo setup")
    print("  Step 2: Start chat  →  custo chat")
    print("  Step 3: Check docs  →  cat BOOTSTRAP.md")
    print()
    print("Quick tips:")
    print("  custo doctor         —  System health check")
    print("  custo sessions today —  View today's conversations")
    print("  custo memory search  —  Search what Custo remembers")
    print("  custo help           —  Show all commands")


def cmd_init(args):
    """Initialize config and first-run setup."""
    print_header("Custo Init")
    try:
        from setup.init_config import init_config
        init_config()
        print("  [OK] Configuration initialized")
    except ImportError:
        print("Running fallback initialization...")
    try:
        from setup.first_run import first_run
        first_run()
        print("  [OK] First run setup complete")
    except ImportError:
        print("  [OK] Ready to go")
    print()
    print("Run 'custo setup' to configure your LLM provider.")


def cmd_doctor(args):
    """System health diagnostic."""
    print_header("Custo Doctor — System Health Check")
    checks = []

    # Python version
    py_ok = sys.version_info >= (3, 10)
    checks.append(("Python >= 3.10", f"{sys.version.split()[0]}", "OK" if py_ok else "UPGRADE"))

    # Project structure
    dirs = ["system", "agents", "sessions", "memory", "tasks", "projects", "interfaces", "daemon"]
    missing = [d for d in dirs if not (ROOT / d).is_dir()]
    checks.append(("Project structure", f"{len(dirs) - len(missing)}/{len(dirs)} dirs", "OK" if not missing else "MISSING"))

    # Config
    cfg = ROOT / "system" / "config.yaml"
    cfg_ok = cfg.exists()
    checks.append(("Config file", "present" if cfg_ok else "missing", "OK" if cfg_ok else "WARN"))

    # Sessions index
    idx = ROOT / "sessions" / "index.json"
    idx_ok = idx.exists() and idx.stat().st_size > 0
    checks.append(("Session index", "present" if idx_ok else "empty", "OK" if idx_ok else "WARN"))

    # LLM provider
    try:
        from system.llm import get_provider
        p = get_provider(root_path=ROOT)
        checks.append(("LLM provider", p.provider_name, "OK"))
    except Exception:
        checks.append(("LLM provider", "none (hardcoded fallback)", "INFO"))

    # PyYAML
    try:
        import yaml
        checks.append(("PyYAML", "installed", "OK"))
    except ImportError:
        checks.append(("PyYAML", "missing", "INSTALL"))

    # Print results
    print()
    for label, detail, status in checks:
        print(f"  [{status:7s}] {label:<20s} {detail}")
    print()

    all_ok = all(s == "OK" for _, _, s in checks)
    if all_ok:
        print("  System is healthy!")
    else:
        warnings = [s for _, _, s in checks if s != "OK"]
        print(f"  {len(warnings)} item(s) need attention. Run 'custo help' for guidance.")


def cmd_upgrade(args):
    """Upgrade Custo to latest version."""
    print_header("Custo Upgrade")
    print("  Upgrade mechanism not yet implemented.")
    print("  For now: pull latest from your repository or re-install.")
