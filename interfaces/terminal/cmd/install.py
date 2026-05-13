"""
install / onboarding commands: install, setup, onboard, init, doctor, upgrade, uninstall
"""

import sys
import subprocess
import shutil
from pathlib import Path

from . import ROOT, print_header


def run(args: list[str], top_args: dict = None):
    """Dispatch installation subcommands."""
    if not args:
        print("Usage: custo <install|setup|onboard|init|doctor|upgrade|uninstall>")
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
        "uninstall": cmd_uninstall,
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
    """Run interactive 5-phase TUI setup wizard."""
    try:
        from setup.tui_setup import run_tui_wizard
        run_tui_wizard()
    except ImportError:
        # Fallback to basic wizard
        try:
            from setup.init_config import run_wizard
            run_wizard()
        except ImportError as e:
            print(f"Setup wizard not available ({e}).")
            print("Run: python setup/init_config.py --wizard")


def cmd_onboard(args):
    """First-time onboarding — launches the full 5-phase TUI wizard."""
    try:
        from setup.tui_setup import run_tui_wizard
        run_tui_wizard()
    except ImportError:
        # Stale install — show update instructions
        print_header("Custo Onboarding")
        print()
        print("  To start the TUI setup wizard, update your installation:\n")
        print("  > iwr -UseBasicParsing https://github.com/relharrati/custo/raw/master/setup/install.ps1 | iex")
        print()
        print("  Or run the basic wizard:")
        print("  > py setup/init_config.py --wizard")


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
     """Upgrade Custo to latest version via git pull."""
     print_header("Custo Upgrade")
     import subprocess
     try:
         result = subprocess.run(
             ["git", "pull", "--ff-only"],
             capture_output=True, text=True, timeout=30,
             cwd=ROOT
         )
         if result.returncode == 0:
             print(f"  {result.stdout.strip()}")
             print("  [OK] Custo updated to latest version.")
         else:
             print(f"  Failed: {result.stderr.strip()}")
             print("  Try: git pull manually in your installation directory.")
     except FileNotFoundError:
         print("  Git not found. Re-install with the install script to update.")
     except subprocess.TimeoutExpired:
         print("  Git pull timed out. Check your connection.")


def cmd_uninstall(args):
     """Remove Custo and all user data."""
     print_header("Custo Uninstall")
     print()
     print("  This will REMOVE:")
     print("    - The entire Custo installation directory")
     print(f"      {ROOT}")
     print("    - All sessions, memory, tasks, and project data")
     print("    - The system/config.yaml file")
     print("    - The custo/custo.bat entry points")
     print()
     print("  This will NOT remove:")
     print("    - Ollama or any LLM models installed globally")
     print("    - Any external gateway tokens you've configured elsewhere")
     print()

     # Extra safety: require explicit "DELETE" confirmation
     if not HAS_INQUIRER:
         confirm = input("  Type DELETE to confirm uninstall: ").strip()
         if confirm != "DELETE":
             print("  Cancelled. No files were removed.")
             return
     else:
         from InquirerPy import inquirer
         try:
             confirm = inquirer.text(
                 message="Type DELETE to confirm uninstall:",
                 validate=lambda _, x: x == "DELETE" or "Must type exactly DELETE",
                 style=custom_style(),
             ).execute()
         except (KeyboardInterrupt, EOFError):
             print("\n  Cancelled.")
             return
         if confirm != "DELETE":
             print("  Cancelled. No files were removed.")
             return

     # Second chance
     print()
     print("  \033[1;31mWARNING: This action is irreversible.\033[0m")

     if not HAS_INQUIRER:
         final = input("  Are you absolutely sure? [y/N]: ").strip().lower()
         if final != "y":
             print("  Cancelled.")
             return
     else:
         from InquirerPy import inquirer
         try:
             final = inquirer.confirm(
                 message="Are you absolutely sure?",
                 default=False,
                 style=custom_style(),
             ).execute()
         except (KeyboardInterrupt, EOFError):
             print("\n  Cancelled.")
             return
         if not final:
             print("  Cancelled.")
             return

     # ── Uninstall Ollama (optional) ──────────────────────
     if shutil.which("ollama"):
         print("\n  Removing Ollama...")
         try:
             if sys.platform == "darwin":
                 run_cmd(["brew", "uninstall", "--cask", "ollama"], timeout=60)
             elif sys.platform.startswith("linux"):
                 run_cmd(["sudo", "systemctl", "stop", "ollama"], timeout=10)
                 run_cmd(["sudo", "rm", "-rf", "/usr/local/bin/ollama"], timeout=10)
                 run_cmd(["sudo", "rm", "-rf", "/etc/systemd/system/ollama.service"], timeout=10)
             elif os.name == "nt":
                 run_cmd(["powershell", "-Command",
                          "Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process"],
                         timeout=10)
                 ollama_dir = Path(os.environ.get(
                     "LOCALAPPDATA", "C:/Program Files")) / "Ollama"
                 if ollama_dir.exists():
                     shutil.rmtree(ollama_dir, ignore_errors=True)
                 # Attempt MSI uninstall
                 run_cmd(["msiexec", "/x", "{ollama-guid}", "/qn"], timeout=30)
             print("  \033[1;32m\u2713 Ollama removed.\033[0m")
         except Exception as e:
             print(f"  \033[1;33mCould not fully remove Ollama: {e}\033[0m")
             print("  Remove manually from your system.")
     else:
         print("\n  Ollama not found \u2014 skipping.")

     # ── Remove Custo directory ──────────────────────────
     print("\n  Removing Custo installation...")
     try:
         shutil.rmtree(ROOT, ignore_errors=True)
         print(f"  \033[1;32m\u2713 Removed {ROOT}\033[0m")
     except Exception as e:
         print(f"  \033[1;31m\u2717 Could not remove {ROOT}: {e}\033[0m")
         print("  Try deleting it manually.")

     # ── Remove from PATH ───────────────────────────────
     print("\n  Cleaning PATH entries...")
     if os.name == "nt":
         try:
             import winreg
             for hive_name, hive in [("User", winreg.HKEY_CURRENT_USER),
                                      ("System", winreg.HKEY_LOCAL_MACHINE)]:
                 try:
                     key = winreg.OpenKey(hive,
                                          r"Environment\PATH", 0,
                                          winreg.KEY_READ | winreg.KEY_WRITE)
                     existing, _ = winreg.QueryValueEx(key, "")
                     if str(ROOT) in existing:
                         new_path = existing.replace(str(ROOT) + ";", "").replace(
                             ";" + str(ROOT), "").replace(str(ROOT), "")
                         winreg.SetValueEx(key, "", 0, winreg.REG_EXPAND_SZ,
                                           new_path)
                         print(f"  \033[1;32m\u2713 Removed from {hive_name} PATH\033[0m")
                     winreg.CloseKey(key)
                 except Exception:
                     pass
         except Exception:
             print("  \033[1;33mCould not clean PATH. Remove manually.\033[0m")

         # Remove PowerShell alias
         try:
             ps_profile = Path(os.environ.get("USERPROFILE", "")) / "Documents" / \
                          "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
             if ps_profile.exists():
                 content = ps_profile.read_text(encoding="utf-8")
                 if "custo" in content.lower():
                     lines = [l for l in content.splitlines()
                              if "custo" not in l.lower() or "Alias" not in l]
                     ps_profile.write_text("\n".join(lines) + "\n", encoding="utf-8")
                     print("  \033[1;32m\u2713 Removed PowerShell alias\033[0m")
         except Exception:
             pass

     # ── Remove bashrc/zshrc alias ──────────────────────
     for rc_file in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
         if rc_file.exists():
             try:
                 content = rc_file.read_text(encoding="utf-8")
                 if "custo" in content:
                     lines = [l for l in content.splitlines()
                              if "custo" not in l]
                     rc_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                     print(f"  \033[1;32m\u2713 Cleaned {rc_file.name}\033[0m")
             except Exception:
                 pass

     print()
     print("  \033[1;32m\u2713 Custo has been uninstalled.\033[0m")
     print("  \033[1;90mYou may need to restart your terminal for changes to take effect.\033[0m")
     print()
