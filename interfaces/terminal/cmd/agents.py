"""
agent commands: agents, agent (switch, create, open, delete, clone, train)
"""

from . import ROOT, print_header, print_table


def run(args: list[str], top_args: dict = None):
    """Dispatch agents|agent subcommands."""
    if not args:
        cmd_agents_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "switch": cmd_switch,
        "create": cmd_create,
        "open": cmd_open,
        "delete": cmd_delete,
        "clone": cmd_clone,
        "train": cmd_train,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown agent command: {cmd}")
        print("Usage: custo agent [switch|create|open|delete|clone|train]")


def cmd_agents_list(args):
    """List all registered agents."""
    agents_dir = ROOT / "agents"
    agents = sorted([d.name for d in agents_dir.iterdir() if d.is_dir() and d.name != "__pycache__"])

    print_header(f"Agents ({len(agents)})")
    for name in agents:
        has_agent = (agents_dir / name / "agent.py").exists()
        agent_status = "+agent.py" if has_agent else ""
        print(f"  • {name:<15} {agent_status}")

    print()
    print("Commands:  custo agent switch|create|open|delete|clone|train")


def cmd_switch(args):
    """Switch to a different agent context."""
    if not args:
        print("Usage: custo agent switch <name>")
        print("Available:", ", ".join(sorted([d.name for d in (ROOT / "agents").iterdir() if d.is_dir() and d.name != "__pycache__"])))
        return
    name = args[0]
    agent_dir = ROOT / "agents" / name
    if not agent_dir.exists():
        print(f"  Agent '{name}' not found.")
        return
    print(f"  Switched to agent: {name}")


def cmd_create(args):
    """Create a new agent stub."""
    if not args:
        print("Usage: custo agent create <name>")
        return
    name = args[0].lower().replace(" ", "_")
    agent_dir = ROOT / "agents" / name
    if agent_dir.exists():
        print(f"  Agent '{name}' already exists.")
        return
    agent_dir.mkdir(parents=True)
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text(
        f'"""\n{name.title()} Agent - Stub\n"""\n\n'
        f'from agents.base_agent import BaseAgent\n\n\n'
        f'class Agent(BaseAgent):\n'
        f'    def __init__(self, root_path, registry=None):\n'
        f'        super().__init__("{name}", root_path, registry)\n\n'
        f'    async def process_task(self, task: dict) -> dict:\n'
        f'        return {{"type": "response", "content": f"{{self.name}} agent received: {{task}}"}}\n'
    )
    print(f"  Created agent '{name}'")
    print(f"  Location: {agent_dir}")


def cmd_open(args):
    """Open an agent's directory."""
    if not args:
        print("Usage: custo agent open <name>")
        return
    name = args[0]
    agent_dir = ROOT / "agents" / name
    if not agent_dir.exists():
        print(f"  Agent '{name}' not found.")
        return
    from subprocess import run as srun
    try:
        srun(["explorer", str(agent_dir)], shell=True)
    except Exception:
        print(f"  Location: {agent_dir}")


def cmd_delete(args):
    """Delete an agent."""
    if not args:
        print("Usage: custo agent delete <name>")
        return
    name = args[0]
    agent_dir = ROOT / "agents" / name
    if not agent_dir.exists():
        print(f"  Agent '{name}' not found.")
        return
    import shutil
    shutil.rmtree(agent_dir)
    print(f"  Deleted agent '{name}'")


def cmd_clone(args):
    """Clone an existing agent."""
    if len(args) < 2:
        print("Usage: custo agent clone <source> <new_name>")
        return
    src_name, dst_name = args[0], args[1]
    src_dir = ROOT / "agents" / src_name
    if not src_dir.exists():
        print(f"  Source agent '{src_name}' not found.")
        return
    dst_dir = ROOT / "agents" / dst_name
    if dst_dir.exists():
        print(f"  Destination '{dst_name}' already exists.")
        return
    import shutil
    shutil.copytree(src_dir, dst_dir)
    print(f"  Cloned '{src_name}' → '{dst_name}'")


def cmd_train(args):
    """Train/prime an agent (stub)."""
    if not args:
        print("Usage: custo agent train <name>")
        return
    name = args[0]
    print(f"  Training agent '{name}'... (not yet implemented)")
    print("  Agent training requires LLM provider integration.")
