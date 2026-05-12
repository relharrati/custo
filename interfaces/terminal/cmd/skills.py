"""
skill commands: skills, skill (create, install, uninstall, open, test, generate), selfskills
"""

import sys
import json
from pathlib import Path

from . import ROOT, print_header, print_table


SKILLS_DIR = ROOT / ".custo" / "skills"


def _ensure_skills_dir():
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def run(args: list[str], top_args: dict = None):
    """Dispatch skills|skill|selfskills subcommands."""
    if not args:
        cmd_skills_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "create": cmd_create,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "open": cmd_open,
        "test": cmd_test,
        "generate": cmd_generate,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown skill command: {cmd}")
        print("Usage: custo skill [create|install|uninstall|open|test|generate]")


def cmd_skills_list(args):
    """List installed skills."""
    _ensure_skills_dir()
    skills = sorted(SKILLS_DIR.glob("*.md")) if SKILLS_DIR.exists() else []

    print_header(f"Skills ({len(skills)})")
    for s in skills:
        print(f"  • {s.stem}")
    print()
    print("Commands:  custo skill create|install|uninstall|open|test|generate")
    print("           custo selfskills")


def cmd_create(args):
    """Create a new skill file."""
    if not args:
        print("Usage: custo skill create <skill_name>")
        return
    name = "_".join(args).lower().replace(" ", "_")
    _ensure_skills_dir()
    skill_file = SKILLS_DIR / f"{name}.md"
    if skill_file.exists():
        print(f"  Skill '{name}' already exists.")
        return
    skill_file.write_text(
        f"# {name} Skill\n\n"
        f"## Description\n\n\n"
        f"## Instructions\n\n\n"
        f"## Examples\n\n"
    )
    print(f"  Created skill '{name}'")
    print(f"  Location: {skill_file}")


def cmd_install(args):
    """Install a skill (stub)."""
    if not args:
        print("Usage: custo skill install <skill_name>")
        return
    name = " ".join(args)
    print(f"  Installing skill '{name}'... (not yet implemented)")


def cmd_uninstall(args):
    """Uninstall a skill."""
    if not args:
        print("Usage: custo skill uninstall <skill_name>")
        return
    name = "_".join(args).lower().replace(" ", "_")
    skill_file = SKILLS_DIR / f"{name}.md"
    if skill_file.exists():
        skill_file.unlink()
        print(f"  Uninstalled skill '{name}'")
    else:
        print(f"  Skill '{name}' not found.")


def cmd_open(args):
    """Open a skill file."""
    if not args:
        print("Usage: custo skill open <skill_name>")
        return
    name = "_".join(args).lower().replace(" ", "_")
    skill_file = SKILLS_DIR / f"{name}.md"
    if skill_file.exists():
        print(skill_file.read_text().strip())
    else:
        print(f"  Skill '{name}' not found.")


def cmd_test(args):
    """Test a skill (stub)."""
    if not args:
        print("Usage: custo skill test <skill_name>")
        return
    name = " ".join(args)
    print(f"  Testing skill '{name}'... (not yet implemented)")


def cmd_generate(args):
    """Generate a skill from conversation (stub)."""
    print("  Skill generation from conversation... (not yet implemented)")


def cmd_selfskills(args):
    """List user's self-installed skills (from ~/.claude/skills)."""
    import os
    home = Path.home()
    skill_dirs = [
        home / ".claude" / "skills",
        home / ".opencode" / "skills",
    ]
    print_header("Self Skills")
    found = False
    for sd in skill_dirs:
        if sd.exists():
            for f in sd.glob("*"):
                if f.suffix in (".md", ".py", ".sh"):
                    print(f"  • {f.stem:<30} {f.suffix}")
                    found = True
    if not found:
        print("  No self-installed skills found.")
    print()
    print("  Skills are loaded from ~/.claude/skills/")
