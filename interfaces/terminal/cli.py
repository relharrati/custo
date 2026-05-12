"""
CLI - Command Line Interface Entry Point

Routes commands to the appropriate module in interfaces/terminal/cmd/.
"""

import sys
import importlib
from pathlib import Path


def print_general_help():
    """Print full command reference."""
    from system.versions import get_version
    ver = get_version()

    print(f"Custo v{ver} — Autonomous Digital Operator")
    print("=" * 60)
    print()
    print("USAGE:  custo <command> [subcommand] [args]")
    print()
    print("CORE COMMANDS")
    print("  chat                    Start interactive chat session")
    print("  ask <question>          Ask a one-shot question")
    print("  shell                   Interactive REPL (coming soon)")
    print()
    print("INSTALLATION & SETUP")
    print("  install                 Install dependencies")
    print("  setup                   Run LLM provider setup wizard")
    print("  onboard                 First-time onboarding tour")
    print("  init                    Initialize config and first-run setup")
    print("  doctor                  System health check")
    print("  upgrade                 Upgrade Custo")
    print()
    print("SESSIONS")
    print("  sessions                List recent sessions")
    print("  sessions today          Show today's sessions")
    print("  sessions open <id>      View a session")
    print("  sessions search <q>     Search sessions")
    print("  sessions delete <id>    Remove a session")
    print("  resume [id]             Resume most recent (or specific) session")
    print()
    print("MEMORY")
    print("  memory                  Show memory overview")
    print("  memory search <q>       Search across memory layers")
    print("  memory add <text>       Add note to inbox")
    print("  memory open <type>      Open a memory layer directory")
    print("  memory compress         Clear expired short-term entries")
    print("  memory rebuild          Rebuild memory indices")
    print("  memory forget <id>      Remove a specific entry")
    print()
    print("PROJECTS")
    print("  projects                List all projects")
    print("  project create <name>   Create a new project")
    print("  project open <name>     View project details")
    print("  project archive <name>  Archive a project")
    print("  project delete <name>   Delete a project")
    print("  project summary <name>  Show project summary")
    print("  project sessions <name> List sessions mentioning project")
    print()
    print("TASKS")
    print("  tasks                   Task overview")
    print("  task add <desc>         Add a task")
    print("  task done <id>          Mark task complete")
    print("  task remove <id>        Remove a task")
    print("  task today              Show today's tasks")
    print("  task upcoming           Show upcoming tasks")
    print("  task recurring          Show recurring tasks")
    print("  task review             Task completion report")
    print()
    print("AGENTS")
    print("  agents                  List registered agents")
    print("  agent switch <name>     Switch agent context")
    print("  agent create <name>     Create a new agent stub")
    print("  agent open <name>       Open agent directory")
    print("  agent delete <name>     Delete an agent")
    print("  agent clone <src> <dst> Clone an agent")
    print("  agent train <name>      Train/prime agent")
    print()
    print("SKILLS")
    print("  skills                  List installed skills")
    print("  skill create <name>     Create a skill file")
    print("  skill install <name>    Install a skill")
    print("  skill uninstall <name>  Remove a skill")
    print("  skill open <name>       View skill contents")
    print("  skill test <name>       Test a skill")
    print("  skill generate          Generate skill from conversation")
    print("  selfskills              List user's self-installed skills")
    print()
    print("DAEMON")
    print("  daemon start            Start the Custo daemon (foreground)")
    print("  daemon stop             Stop the daemon")
    print("  daemon restart          Restart the daemon")
    print("  daemon status           Show daemon/agent status")
    print("  daemon logs             View daemon logs")
    print()
    print("GATEWAYS")
    print("  gateways                List gateway integrations")
    print("  gateway enable <name>   Enable a gateway")
    print("  gateway disable <name>  Disable a gateway")
    print("  gateway test <name>     Test gateway connection")
    print("  gateway install <name>  Install a gateway")
    print()
    print("WEB")
    print("  web                     Show web interface status")
    print("  web dev                 Start dev server")
    print("  web build               Build static assets")
    print()
    print("REFLECTION & OPTIMIZATION")
    print("  reflect                 Generate a reflection")
    print("  review today            Review today's activity")
    print("  optimize                Show optimization suggestions")
    print("  learnings               Show extracted insights")
    print()
    print("CONFIGURATION")
    print("  config                  Show current configuration")
    print("  config edit             Open config in editor")
    print("  reset                   Reset config to defaults (dangerous)")
    print()
    print("DEVELOPER")
    print("  version                 Show version info")
    print("  logs                    View recent log files")
    print("  debug                   Run diagnostics")
    print("  test                    Run test suite")
    print("  export                  Export data to zip")
    print("  backup                  Create full backup")
    print("  restore <path>          Restore from backup")


def _load_mod(name):
    """Dynamically import a command module."""
    return importlib.import_module(f"interfaces.terminal.cmd.{name}")


def main():
    """CLI entry point. Routes commands to modular handlers."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print_general_help()
        return

    command = args[0]
    subargs = args[1:]

    # ── DISPATCH TABLE ──────────────────────────────────────────
    # Each entry: (module_short_name, handler_fn_name)
    # handler_fn is called with subargs.
    dispatch = {

        # ── Core ──
        "chat":     ("core", "cmd_chat"),
        "ask":      ("core", "cmd_ask"),
        "shell":    ("core", "cmd_shell"),

        # ── Install / Setup ──
        "install":  ("install", "cmd_install"),
        "setup":    ("install", "cmd_setup"),
        "onboard":  ("install", "cmd_onboard"),
        "init":     ("install", "cmd_init"),
        "doctor":   ("install", "cmd_doctor"),
        "upgrade":  ("install", "cmd_upgrade"),

        # ── Sessions ──
        "sessions": ("sessions", "run"),
        "resume":   ("sessions", "cmd_resume"),

        # ── Memory ──
        "memory":   ("memory", "run"),

        # ── Projects ──
        "projects": ("projects", "run"),
        "project":  ("projects", "run"),

        # ── Tasks ──
        "tasks":    ("tasks", "run"),
        "task":     ("tasks", "run"),

        # ── Agents ──
        "agents":   ("agents", "run"),
        "agent":    ("agents", "run"),

        # ── Skills ──
        "skills":     ("skills", "run"),
        "skill":      ("skills", "run"),
        "selfskills": ("skills", "cmd_selfskills"),

        # ── Daemon ──
        "daemon":   ("daemon", "run"),

        # ── Gateways ──
        "gateways": ("gateway", "run"),
        "gateway":  ("gateway", "run"),

        # ── Web ──
        "web":      ("web", "run"),

        # ── Reflection ──
        "reflect":    ("reflection", "run"),
        "review":     ("reflection", "run"),
        "optimize":   ("reflection", "cmd_optimize"),
        "learnings":  ("reflection", "cmd_learnings"),

        # ── Config ──
        "config":   ("config", "run"),
        "reset":    ("config", "cmd_reset"),

        # ── Dev ──
        "version":  ("dev", "cmd_version"),
        "logs":     ("dev", "cmd_logs"),
        "debug":    ("dev", "cmd_debug"),
        "test":     ("dev", "cmd_test"),
        "export":   ("dev", "cmd_export"),
        "backup":   ("dev", "cmd_backup"),
        "restore":  ("dev", "cmd_restore"),
    }

    entry = dispatch.get(command)
    if entry is None:
        print(f"Unknown command: custo {command}")
        print("Run 'custo help' for available commands.")
        return

    mod_name, handler = entry

    try:
        mod = _load_mod(mod_name)
        fn = getattr(mod, handler)
        fn(subargs)
    except ImportError as e:
        print(f"  Error loading command module '{mod_name}': {e}")
    except AttributeError as e:
        print(f"  Error: module '{mod_name}' has no handler '{handler}': {e}")
    except Exception as e:
        print(f"  Error executing '{command}': {e}")


if __name__ == "__main__":
    main()
