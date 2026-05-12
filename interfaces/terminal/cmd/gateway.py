"""
gateway commands: gateways, gateway (enable, disable, test, install)
"""

from . import ROOT, print_header, print_table


GATEWAY_DIR = ROOT / "integrations"


def run(args: list[str], top_args: dict = None):
    """Dispatch gateways|gateway subcommands."""
    if not args:
        cmd_gateways_list([])
        return

    cmd = args[0]
    sub = args[1:]

    handlers = {
        "enable": cmd_enable,
        "disable": cmd_disable,
        "test": cmd_test,
        "install": cmd_install,
    }
    handler = handlers.get(cmd)
    if handler:
        handler(sub)
    else:
        print(f"Unknown gateway command: {cmd}")
        print("Usage: custo gateway [enable|disable|test|install]")


def _get_gateways():
    """Discover available gateway stubs."""
    gateways = {
        "discord": {
            "dir": GATEWAY_DIR / "discord",
            "status": "stub",
            "description": "Discord bot integration",
        },
        "telegram": {
            "dir": GATEWAY_DIR / "telegram",
            "status": "stub",
            "description": "Telegram bot integration",
        },
        "slack": {
            "dir": GATEWAY_DIR / "slack",
            "status": "stub",
            "description": "Slack app integration",
        },
        "email": {
            "dir": GATEWAY_DIR / "email",
            "status": "stub",
            "description": "Email gateway",
        },
        "github": {
            "dir": GATEWAY_DIR / "github",
            "status": "stub",
            "description": "GitHub integration",
        },
        "notion": {
            "dir": GATEWAY_DIR / "notion",
            "status": "stub",
            "description": "Notion workspace integration",
        },
        "calendar": {
            "dir": GATEWAY_DIR / "calendar",
            "status": "stub",
            "description": "Calendar integration",
        },
    }
    # Check which have actual implementations
    for name, gw in gateways.items():
        gw_dir = gw["dir"]
        if gw_dir.exists() and list(gw_dir.glob("*.py")):
            gw["status"] = "available"
    return gateways


def cmd_gateways_list(args):
    """List all gateways."""
    gateways = _get_gateways()

    print_header(f"Gateways ({len(gateways)})")
    rows = []
    for name, gw in sorted(gateways.items()):
        icon = "🔌" if gw["status"] == "available" else "○"
        rows.append((icon, name, gw["status"], gw["description"]))
    print_table(rows, headers=["", "Name", "Status", "Description"])
    print()
    print("Commands:  custo gateway enable|disable|test|install")


def cmd_enable(args):
    """Enable a gateway."""
    if not args:
        print("Usage: custo gateway enable <name>")
        print("Available:", ", ".join(_get_gateways().keys()))
        return
    name = args[0].lower()
    gateways = _get_gateways()
    if name not in gateways:
        print(f"  Unknown gateway: {name}")
        return
    print(f"  Enabling {name} gateway... (not yet implemented)")
    print("  Gateways require provider-specific setup.")


def cmd_disable(args):
    """Disable a gateway."""
    if not args:
        print("Usage: custo gateway disable <name>")
        return
    name = args[0].lower()
    print(f"  Disabling {name} gateway... (not yet implemented)")


def cmd_test(args):
    """Test a gateway connection."""
    if not args:
        print("Usage: custo gateway test <name>")
        return
    name = args[0].lower()
    print(f"  Testing {name} gateway... (not yet implemented)")


def cmd_install(args):
    """Install a gateway integration."""
    if not args:
        print("Usage: custo gateway install <name>")
        return
    name = args[0].lower()
    gateways = _get_gateways()
    if name not in gateways:
        print(f"  Unknown gateway: {name}")
        return
    print(f"  Installing {name} gateway... (not yet implemented)")
