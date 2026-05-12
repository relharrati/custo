"""
TUI Setup Wizard - Phased interactive setup with futuristic emerald/blue palette.

Phases:
  1. Security & Safety Confirmation
  2. Gateway Configuration (mode + bind address)
  3. Model & API Authentication
  4. Channel & Interface Integration
  5. Workspace & Skills Initialization
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Force UTF-8 for Windows terminal compatibility
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Rich-based TUI (must be installed separately)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.text import Text
    from rich.table import Table
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.align import Align
    from rich.columns import Columns
    from rich.theme import Theme
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ── Color Palette ─────────────────────────────────────────────
# TokyoNight-inspired with emerald/blue accents

EMERALD    = "#00FF7F"
BLUE       = "#7dcfff"
TEAL       = "#73daca"
GREEN      = "#9ece6a"
GOLD       = "#e0af68"
RED        = "#f7768e"
PURPLE     = "#bb9af7"
BG_DARK    = "#1a1b26"
BG_PANEL   = "#1f2335"
TEXT       = "#c0caf5"
TEXT_DIM   = "#565f89"
BORDER     = "#3b4261"

CUSTO_THEME = Theme({
    "emerald":  f"bold {EMERALD}",
    "blue":     f"bold {BLUE}",
    "teal":     f"bold {TEAL}",
    "green":    f"bold {GREEN}",
    "gold":     f"bold {GOLD}",
    "red":      f"bold {RED}",
    "purple":   f"bold {PURPLE}",
    "dim":      f"{TEXT_DIM}",
    "text":     f"{TEXT}",
    "ok":       f"bold {GREEN}",
    "warn":     f"bold {GOLD}",
    "error":    f"bold {RED}",
})

STYLES = {
    "title":     f"bold {EMERALD}",
    "phase":     f"bold {BLUE}",
    "label":     f"bold {TEAL}",
    "value":     f"{TEXT}",
    "prompt":    f"bold {EMERALD}",
    "success":   f"bold {GREEN}",
    "warning":   f"bold {GOLD}",
    "error":     f"bold {RED}",
    "info":      f"dim {TEXT_DIM}",
}

# ── ASCII Art ─────────────────────────────────────────────────
CUSTO_ASCII = rf"""
[emerald]   ____          _        [/emerald]
[emerald]  / ___|   _ ___| |_ ___  [/emerald]
[blue] | |  | | | / __| __/ _ \ [/blue]
[teal] | |__| |_| \__ \ || (_) |[/teal]
[emerald]  \____\__,_|___/\__\___/ [/emerald]
"""

ROOT = Path(__file__).parent.parent

# ── Rich Console ──────────────────────────────────────────────
console = Console(theme=CUSTO_THEME, highlight=False)

# ═══════════════════════════════════════════════════════════════
# Helper widgets
# ═══════════════════════════════════════════════════════════════

def _banner():
    """Print the Custo ASCII art banner."""
    console.print()
    console.print(Align.center(CUSTO_ASCII))
    console.print(Align.center("[dim]Autonomous Digital Operator[/dim]"))
    console.print()


def _phase_header(num: int, title: str, subtitle: str = ""):
    """Render a phase header panel."""
    header = Text()
    header.append(f"  Phase {num}: {title}", style=STYLES["phase"])
    if subtitle:
        header.append(f"\n  ", style="dim")
        header.append(subtitle, style=STYLES["info"])
    console.print(Panel(header, border_style=BLUE, box=box.ROUNDED, padding=(1, 2)))
    console.print()


def _step(msg: str, status: str = "..."):
    """Print a step line."""
    if status == "ok":
        console.print(f"  [{GREEN}]✓[/] {msg}")
    elif status == "skip":
        console.print(f"  [{GOLD}]−[/] {msg}")
    elif status == "fail":
        console.print(f"  [{RED}]✗[/] {msg}")
    else:
        console.print(f"  [{BLUE}]▸[/] {msg}")


def _divider():
    console.print(f"  [{TEXT_DIM}]" + "─" * 56 + "[/]")


def _summary_table(data: Dict):
    """Display a summary table."""
    table = Table(box=box.SIMPLE, border_style=TEXT_DIM, padding=(0, 2))
    table.add_column("Setting", style=STYLES["label"])
    table.add_column("Value", style=STYLES["value"])
    for k, v in data.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    console.print(table)


def _confirm_dangerous(msg: str) -> bool:
    """A high-visibility confirmation prompt."""
    console.print(Panel(
        f"[{GOLD}]⚠  {msg}[/{GOLD}]",
        border_style=GOLD, box=box.HEAVY, padding=(1, 2)
    ))
    result = Prompt.ask("  Type [bold]yes[/] to confirm", default="no", console=console)
    return result.strip().lower() == "yes"


# ═══════════════════════════════════════════════════════════════
# Phase 1: Security & Safety Confirmation
# ═══════════════════════════════════════════════════════════════

def phase1_security() -> bool:
    """
    Phase 1: Security & Safety Confirmation.
    
    Warns the user that Custo has file-system and command-execution
    capabilities. User must acknowledge before proceeding.
    """
    _phase_header(1, "Security & Safety Confirmation",
                  "You are about to deploy an autonomous AI agent")

    warning = Text()
    warning.append("Custo is an autonomous agent with the following capabilities:\n\n", style=TEXT)
    warning.append("  •  ", style=TEXT)
    warning.append("File-system access", style=STYLES["warning"])
    warning.append(" — read, write, modify files\n", style=TEXT)
    warning.append("  •  ", style=TEXT)
    warning.append("Command execution", style=STYLES["warning"])
    warning.append(" — run shell commands on your system\n", style=TEXT)
    warning.append("  •  ", style=TEXT)
    warning.append("Network access", style=STYLES["warning"])
    warning.append(" — communicate with APIs and services\n", style=TEXT)
    warning.append("  •  ", style=TEXT)
    warning.append("Memory persistence", style=STYLES["warning"])
    warning.append(" — stores conversations and learned patterns\n\n", style=TEXT)
    warning.append("Default security model: ", style=TEXT)
    warning.append("PRIVATE-BY-DEFAULT", style=f"bold {EMERALD}")
    warning.append("\n  • All data stays local to your machine", style=TEXT)
    warning.append("\n  • No telemetry or external calls without consent", style=TEXT)
    warning.append("\n  • Configurable gateway binding (localhost default)", style=TEXT)

    console.print(Panel(warning, border_style=EMERALD, box=box.HEAVY, padding=(1, 2)))

    console.print()
    console.print("  By continuing, you acknowledge these capabilities and accept", style=TEXT)
    console.print("  responsibility for Custo's actions on your system.", style=TEXT)
    console.print()

    confirmed = _confirm_dangerous(
        "Custo can modify files and execute commands. Continue?"
    )

    if confirmed:
        _step("Security confirmation accepted", "ok")
    else:
        console.print(f"\n  [{RED}]Setup aborted by user.[/]")
        sys.exit(0)

    return confirmed


# ═══════════════════════════════════════════════════════════════
# Phase 2: Gateway Configuration
# ═══════════════════════════════════════════════════════════════

def phase2_gateway() -> Dict:
    """
    Phase 2: Gateway Mode & Network Configuration.
    
    Configure how Custo's gateway binds to the network:
    - QuickStart: local loopback (127.0.0.1), port 18789
    - Advanced: custom bind address, port, auth
    - Daemon: install as background service
    """
    _phase_header(2, "Gateway Configuration",
                  "How should Custo listen for connections?")

    config = {
        "bind_address": "127.0.0.1",
        "port": 18789,
        "auth_mode": "none",
        "daemon_install": False,
    }

    # Mode selection
    console.print(f"  [{BLUE}]▸[/] Choose deployment mode:")
    console.print(f"    [{GREEN}]1[/]  QuickStart  —  Local only (127.0.0.1:18789)")
    console.print(f"    [{GREEN}]2[/]  Advanced    —  Custom bind address, port, auth")
    console.print(f"    [{GREEN}]3[/]  Network     —  Expose on LAN (192.168.x.x)")
    console.print()

    mode = Prompt.ask("  Select mode", choices=["1", "2", "3"], default="1", console=console)

    if mode == "1":
        # QuickStart: localhost defaults
        config["bind_address"] = "127.0.0.1"
        config["port"] = 18789
        config["auth_mode"] = "none"
        _step("QuickStart mode: local loopback (127.0.0.1:18789)", "ok")

    elif mode == "2":
        # Advanced: custom settings
        config["bind_address"] = Prompt.ask(
            "  Bind address", default="127.0.0.1", console=console
        )
        config["port"] = IntPrompt.ask(
            "  Port", default=18789, console=console
        )
        auth = Prompt.ask(
            "  Authentication mode", choices=["none", "token"], default="none", console=console
        )
        config["auth_mode"] = auth
        if auth == "token":
            _step("Token authentication enabled", "ok")
        _step(f"Gateway will bind to {config['bind_address']}:{config['port']}", "ok")

    elif mode == "3":
        # Network: expose on LAN
        # Try to detect LAN IP
        lan_ip = _detect_lan_ip()
        config["bind_address"] = Prompt.ask(
            "  LAN address", default=lan_ip or "0.0.0.0", console=console
        )
        config["port"] = IntPrompt.ask("  Port", default=18789, console=console)
        config["auth_mode"] = "token"  # Force auth for network exposure
        _step(f"Gateway will bind to {config['bind_address']}:{config['port']}", "ok")
        _step("Token authentication enabled (required for network exposure)", "ok")
        console.print(f"\n  [{GOLD}]⚠  Network mode exposes Custo on your LAN.[/]")
        console.print(f"  [{GOLD}]   Use a firewall and enable authentication.[/]")

    # Daemon installation
    console.print()
    daemon = Confirm.ask(
        "  Install as background service (run continuously)?",
        default=False, console=console
    )
    config["daemon_install"] = daemon
    if daemon:
        _step("Daemon service will be installed", "ok")
    else:
        _step("Manual startup: run 'custo daemon start' when needed", "skip")

    return config


def _detect_lan_ip() -> Optional[str]:
    """Try to detect the LAN IP address."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# Phase 3: Model & API Authentication
# ═══════════════════════════════════════════════════════════════

def _detect_ram() -> int:
    """Best-effort RAM detection in GB."""
    try:
        if os.name == "nt":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return max(1, int(stat.ullTotalPhys / (1024**3)))
        else:
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kB = int(line.split()[1])
                            return max(1, int(kB / 1024 / 1024 + 0.5))
            except FileNotFoundError:
                import subprocess
                r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=3)
                if r.returncode == 0:
                    return max(1, int(int(r.stdout.strip()) / (1024**3)))
    except Exception:
        pass
    return 0


def _ram_str(ram_gb: int) -> str:
    if ram_gb >= 1024:
        return f"{ram_gb // 1024}+ TB"
    if ram_gb >= 32:
        return f"{ram_gb} GB (plenty)"
    if ram_gb >= 16:
        return f"{ram_gb} GB (good)"
    if ram_gb >= 8:
        return f"{ram_gb} GB (modest)"
    if ram_gb >= 4:
        return f"{ram_gb} GB (light)"
    if ram_gb >= 2:
        return f"{ram_gb} GB (minimal)"
    if ram_gb >= 1:
        return f"{ram_gb} GB (limited)"
    return "unknown"


def phase3_model() -> Dict:
    """
    Phase 3: Model & API Authentication.
    
    Configure the AI provider: local (Ollama/LM Studio/vLLM)
    or cloud (OpenAI/Anthropic/Gemini).
    """
    _phase_header(3, "Model & API Authentication",
                  "Choose how Custo will think and respond")

    ram_gb = _detect_ram()
    config = {}

    _step(f"Detected RAM: ~{_ram_str(ram_gb)}", "ok")
    console.print()

    # Provider selection table
    providers = Table(box=box.SIMPLE, border_style=TEXT_DIM, padding=(0, 2))
    providers.add_column("#", style=STYLES["label"], width=3)
    providers.add_column("Provider", style=STYLES["label"], width=16)
    providers.add_column("Type", style=TEXT_DIM, width=10)
    providers.add_column("Description", style=STYLES["value"])
    providers.add_row("1", "Ollama", "Local", "Free, auto-download, best privacy")
    providers.add_row("2", "LM Studio", "Local", "GUI-based, GGUF models")
    providers.add_row("3", "vLLM", "Local", "High-throughput, GPU/CPU")
    providers.add_row("4", "OpenAI", "Cloud", "GPT-4o, GPT-4o-mini")
    providers.add_row("5", "Anthropic", "Cloud", "Claude Sonnet, Haiku")
    providers.add_row("6", "Google Gemini", "Cloud", "Gemini Flash, Pro")
    providers.add_row("7", "Skip (Hardcoded)", "None", "Bootstrap fallback only")

    console.print(providers)
    console.print()

    choice = Prompt.ask(
        "  Select provider",
        choices=["1", "2", "3", "4", "5", "6", "7"],
        default="1", console=console
    )

    provider_map = {
        "1": "ollama", "2": "lmstudio", "3": "vllm",
        "4": "openai", "5": "anthropic", "6": "gemini", "7": "hardcoded"
    }
    provider = provider_map[choice]

    if provider == "ollama":
        config = _setup_ollama(ram_gb)
    elif provider == "lmstudio":
        config = _setup_lmstudio(ram_gb)
    elif provider == "vllm":
        config = _setup_vllm()
    elif provider in ("openai", "anthropic", "gemini"):
        config = _setup_cloud_api(provider)
    else:
        config = {"provider": "hardcoded", "model": "", "auto_download": False}
        _step("Using hardcoded fallback responses", "skip")

    return config


def _setup_ollama(ram_gb: int) -> Dict:
    """Configure Ollama local provider."""
    config = {"provider": "ollama", "auto_download": True, "ollama_host": "http://127.0.0.1:11434"}

    # Check if Ollama is installed
    try:
        import subprocess
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=3)
        _step("Ollama CLI found", "ok")
    except FileNotFoundError:
        _step("Ollama not installed — download from https://ollama.ai", "skip")
        console.print("  You can install Ollama later and Custo will auto-detect it.", style=STYLES["info"])

    # Model recommendations based on RAM
    try:
        from system.llm.ollama import OllamaProvider
        tiers = OllamaProvider.recommend_models(ram_gb)
    except Exception:
        # Fallback static tiers
        tiers = _fallback_model_tiers(ram_gb)

    # Flatten tiers into a list
    tier_order = ["minimal", "small", "medium", "large"]
    tier_labels = {
        "minimal": "Minimal (< 2GB RAM)",
        "small": "Small (2–8GB RAM)",
        "medium": "Medium (8–24GB RAM)",
        "large": "Large (24GB+ RAM)",
    }

    options = []
    table = Table(box=box.SIMPLE, border_style=TEXT_DIM, padding=(0, 2))
    table.add_column("#", style=STYLES["label"], width=3)
    table.add_column("Model", style=STYLES["label"], width=30)
    table.add_column("Size", style=TEXT_DIM, width=12)
    table.add_column("Notes", style=STYLES["value"])

    idx = 1
    for key in tier_order:
        models = tiers.get(key, [])
        if not models:
            continue
        for model_id, name, size, note in models:
            options.append(model_id)
            table.add_row(str(idx), name, size, note)
            idx += 1

    console.print(f"\n  Recommended models for {_ram_str(ram_gb)} RAM:")
    console.print(table)
    console.print()

    sel = Prompt.ask(
        f"  Select model [1-{len(options)}]",
        default="1", console=console
    )
    try:
        model_idx = int(sel) - 1
        config["model"] = options[model_idx]
    except (ValueError, IndexError):
        config["model"] = options[0]

    _step(f"Model: {config['model']}", "ok")

    # Auto-download
    config["auto_download"] = Confirm.ask(
        "  Auto-download if missing?", default=True, console=console
    )
    if config["auto_download"]:
        _step("Will auto-pull model via 'ollama pull'", "ok")

    return config


def _fallback_model_tiers(ram_gb: int) -> Dict:
    """Static model tiers when models.dev API is unavailable."""
    # Minimal: < 2GB
    minimal = [
        ("tinyml", "TinyML (Fallback)", "<500 MB", "Fastest, lowest quality"),
    ]
    # Small: 2-8GB
    small = [
        ("qwen2.5-coder:1.5b", "Qwen Coder 1.5B", "~1.1 GB", "Excellent code"),
        ("gemma3:1b", "Gemma 3 1B", "~790 MB", "Fast and light"),
    ]
    # Medium: 8-24GB
    medium = [
        ("llama3.2:3b", "Llama 3.2 3B", "~2.0 GB", "Great all-around"),
        ("qwen2.5-coder:7b", "Qwen Coder 7B", "~4.0 GB", "Strong code"),
    ]
    # Large: 24GB+
    large = [
        ("llama3.2:8b", "Llama 3.2 8B", "~4.9 GB", "Best quality"),
    ]

    if ram_gb < 2:
        return {"minimal": minimal, "small": [], "medium": [], "large": []}
    elif ram_gb < 8:
        return {"minimal": minimal, "small": small, "medium": [], "large": []}
    elif ram_gb < 24:
        return {"minimal": minimal, "small": small, "medium": medium, "large": []}
    return {"minimal": minimal, "small": small, "medium": medium, "large": large}


def _setup_lmstudio(ram_gb: int) -> Dict:
    """Configure LM Studio provider."""
    _step("LM Studio selected — starts a local OpenAI-compatible server", "ok")
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=2)
        _step("LM Studio server running at http://127.0.0.1:1234", "ok")
    except Exception:
        _step("Start LM Studio → load a model → Server tab → Start Server", "skip")

    model = Prompt.ask("  Model name", default="llama3.2", console=console)
    return {
        "provider": "lmstudio",
        "model": model,
        "auto_download": False,
        "lmstudio_host": "http://127.0.0.1:1234"
    }


def _setup_vllm() -> Dict:
    """Configure vLLM provider."""
    _step("vLLM — high-throughput LLM serving engine", "info")
    model = Prompt.ask(
        "  HuggingFace model ID",
        default="meta-llama/Llama-3.2-3B-Instruct",
        console=console
    )
    host = Prompt.ask("  Server URL", default="http://127.0.0.1:8000", console=console)

    if not model:
        return {"provider": "hardcoded"}
    return {
        "provider": "vllm",
        "model": model,
        "auto_download": False,
        "vllm_host": host
    }


def _setup_cloud_api(provider: str) -> Dict:
    """Configure a cloud API provider (OpenAI / Anthropic / Gemini)."""
    api_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    display_names = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "gemini": "Google Gemini",
    }
    default_models = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.0-flash",
    }
    model_suggestions = {
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "anthropic": ["claude-sonnet-4-20250514", "claude-haiku-3-5-20241022"],
        "gemini": ["gemini-2.0-flash", "gemini-2.0-pro-exp-02-05"],
    }

    display = display_names[provider]
    _step(f"Configuring {display}", "info")

    # API key input
    env_var = api_keys[provider]
    current_key = os.environ.get(env_var, "")
    masked = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else "(not set)"

    console.print(f"\n  [{BLUE}]▸[/] {display} API Key")
    console.print(f"    Current: {masked}")
    console.print(f"    Env var: {env_var}")
    console.print(f"    Get key: https://platform.openai.com/api-keys (for OpenAI)")
    console.print()

    key = Prompt.ask("  Enter API key (or Enter to keep current)", default="", console=console)
    if key:
        os.environ[env_var] = key
        _step(f"{env_var} set", "ok")
    else:
        _step(f"Using existing {env_var} or env var", "skip")

    # Model selection
    console.print(f"\n  [{BLUE}]▸[/] Model selection:")
    suggestions = model_suggestions[provider]
    for i, m in enumerate(suggestions, 1):
        console.print(f"    [{GREEN}]{i}[/]  {m}")

    model_sel = Prompt.ask(
        f"  Select model", default="1", console=console
    )
    try:
        model_idx = int(model_sel) - 1
        model = suggestions[model_idx]
    except (ValueError, IndexError):
        model = default_models[provider]

    _step(f"Model: {model}", "ok")

    return {
        "provider": provider,
        "model": model,
        "auto_download": False,
        "api_key_env": env_var
    }


# ═══════════════════════════════════════════════════════════════
# Phase 4: Channel & Interface Integration
# ═══════════════════════════════════════════════════════════════

def phase4_channels() -> Dict:
    """
    Phase 4: Channel & Interface Integration.
    
    Configure messaging platforms and web dashboard.
    """
    _phase_header(4, "Channel & Interface Integration",
                  "Connect Custo to messaging platforms")

    channels = {
        "web_dashboard": True,
        "telegram": False,
        "discord": False,
        "whatsapp": False,
    }

    console.print(f"  [{BLUE}]▸[/] Available channels:\n")

    # Web dashboard
    channels["web_dashboard"] = Confirm.ask(
        "  Enable Web Dashboard?",
        default=True, console=console
    )
    if channels["web_dashboard"]:
        _step("Web UI at http://127.0.0.1:18789", "ok")

    # Telegram
    channels["telegram"] = Confirm.ask(
        "  Enable Telegram bot?", default=False, console=console
    )
    if channels["telegram"]:
        _step("Telegram bot stub — configure token in integrations/telegram/", "skip")

    # Discord
    channels["discord"] = Confirm.ask(
        "  Enable Discord bot?", default=False, console=console
    )
    if channels["discord"]:
        _step("Discord bot stub — configure token in integrations/discord/", "skip")

    # WhatsApp
    channels["whatsapp"] = Confirm.ask(
        "  Enable WhatsApp integration?", default=False, console=console
    )
    if channels["whatsapp"]:
        _step("WhatsApp integration stub — requires API setup", "skip")

    console.print()
    _divider()
    enabled = [k for k, v in channels.items() if v]
    if enabled:
        console.print(f"  [{GREEN}]Active channels:[/] {', '.join(enabled)}")
    else:
        _step("No external channels configured — CLI/TUI only", "skip")

    return channels


# ═══════════════════════════════════════════════════════════════
# Phase 5: Workspace & Skills
# ═══════════════════════════════════════════════════════════════

def phase5_workspace() -> Dict:
    """
    Phase 5: Workspace & Skills Setup.
    
    Initialize workspace folder structure and enable default skills.
    """
    _phase_header(5, "Workspace & Skills Setup",
                  "Prepare the environment for daily operation")

    config = {
        "workspace_initialized": False,
        "skills_enabled": [],
    }

    # Workspace initialization
    _step("Creating workspace directories...", "...")

    bootstrap_dirs = [
        "system", "sessions/daily", "memory/inbox", "memory/short_term",
        "memory/daily_memory", "memory/long_term", "memory/reflections",
        "projects/active", "projects/archived", "tasks", "logs",
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Creating directories...", total=len(bootstrap_dirs))
        for d in bootstrap_dirs:
            (ROOT / d).mkdir(parents=True, exist_ok=True)
            progress.advance(task)

    config["workspace_initialized"] = True
    _step(f"Created {len(bootstrap_dirs)} workspace directories", "ok")

    # Skills selection
    console.print()
    console.print(f"  [{BLUE}]▸[/] Enable default skills:\n")

    skill_options = {
        "web_search": "Web Search (Brave/Tavily — requires API key)",
        "file_ops": "File Manipulation (read/write/edit files)",
        "memory": "Memory Management (auto-consolidation)",
        "reflection": "Self-Reflection (daily summaries)",
    }

    enabled_skills = []
    for skill_key, skill_desc in skill_options.items():
        enable = Confirm.ask(f"  {skill_desc}?", default=True, console=console)
        if enable:
            enabled_skills.append(skill_key)
            _step(f"{skill_desc.split('(')[0].strip()} enabled", "ok")

    config["skills_enabled"] = enabled_skills
    console.print()
    _step(f"{len(enabled_skills)} skill(s) enabled", "ok")

    return config


# ═══════════════════════════════════════════════════════════════
# Config saving
# ═══════════════════════════════════════════════════════════════

def _save_config(gateway_cfg: Dict, llm_cfg: Dict, channels_cfg: Dict, workspace_cfg: Dict):
    """Merge all phase configs and write to system/config.yaml."""
    try:
        from system.config import load_config, save_config, _deep_merge
    except ImportError:
        # Fallback: direct yaml write
        import yaml

    cfg = load_config(ROOT)

    # Gateway
    cfg.setdefault("gateway", {})
    cfg["gateway"].update({
        "bind_address": gateway_cfg.get("bind_address", "127.0.0.1"),
        "port": gateway_cfg.get("port", 18789),
        "auth_mode": gateway_cfg.get("auth_mode", "none"),
        "daemon_install": gateway_cfg.get("daemon_install", False),
    })

    # LLM
    cfg.setdefault("llm", {})
    for k, v in llm_cfg.items():
        cfg["llm"][k] = v

    # Channels
    cfg.setdefault("interfaces", {})
    cfg["interfaces"]["web"] = {"enabled": channels_cfg.get("web_dashboard", True), "port": 18789}
    cfg["interfaces"]["gateways"] = {
        "telegram": channels_cfg.get("telegram", False),
        "discord": channels_cfg.get("discord", False),
        "whatsapp": channels_cfg.get("whatsapp", False),
    }

    # Skills
    cfg.setdefault("skills", {})
    cfg["skills"]["enabled"] = workspace_cfg.get("skills_enabled", [])

    save_config(cfg, ROOT)
    _step("Configuration saved to system/config.yaml", "ok")


# ═══════════════════════════════════════════════════════════════
# Post-setup: Provider actions
# ═══════════════════════════════════════════════════════════════

def _post_setup_ollama(model: str, auto_download: bool):
    """Post-setup actions for Ollama: detect, install, download model."""
    import subprocess
    import urllib.request

    # Check if Ollama CLI exists
    ollama_found = False
    try:
        r = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            ollama_found = True
            _step(f"Ollama CLI found: {r.stdout.strip()}", "ok")
    except FileNotFoundError:
        pass

    # Check if Ollama daemon is running
    daemon_running = False
    try:
        urllib.request.urlopen("http://127.0.0.1:11434", timeout=2)
        daemon_running = True
        _step("Ollama daemon running at http://127.0.0.1:11434", "ok")
    except Exception:
        pass

    if not ollama_found:
        _step("Ollama not installed — download from https://ollama.ai", "skip")
        console.print(f"    [{TEXT_DIM}]Install, then run: ollama serve[/]")
        return

    if not daemon_running:
        _step("Ollama daemon not running — starting...", "...")
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _step("Ollama daemon started", "ok")
        except Exception:
            _step("Start manually: ollama serve in another terminal", "skip")

    # Check if model is already installed
    if model:
        model_installed = False
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            model_installed = model in r.stdout
        except Exception:
            pass

        if model_installed:
            _step(f"Model '{model}' already installed", "ok")
        elif auto_download:
            _step(f"Downloading model '{model}' (this may take a while)...", "...")
            console.print(f"    [{TEXT_DIM}]Running: ollama pull {model}[/]")
            try:
                r = subprocess.run(["ollama", "pull", model], capture_output=True, text=True, timeout=300)
                if r.returncode == 0:
                    _step(f"Model '{model}' downloaded", "ok")
                else:
                    _step(f"Download failed: {r.stderr.strip()[:80]}", "fail")
                    console.print(f"    [{TEXT_DIM}]Try: ollama pull {model}[/]")
            except subprocess.TimeoutExpired:
                _step("Download timed out — try: ollama pull " + model, "skip")
        else:
            _step(f"Run 'ollama pull {model}' to download the model", "skip")


def _post_setup_lmstudio():
    """Post-setup instructions for LM Studio."""
    import urllib.request

    try:
        urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=2)
        _step("LM Studio server running at http://127.0.0.1:1234", "ok")
    except Exception:
        _step("LM Studio not detected", "skip")
        instructions = [
            f"  [{TEXT_DIM}]1. Download LM Studio from https://lmstudio.ai[/]",
            f"  [{TEXT_DIM}]2. Load a model (e.g., llama3.2-3b)[/]",
            f"  [{TEXT_DIM}]3. Go to Server tab → Start Server[/]",
            f"  [{TEXT_DIM}]4. Verify: curl http://127.0.0.1:1234/v1/models[/]",
        ]
        for line in instructions:
            console.print(line)
        console.print()


def _post_setup_vllm(model: str, host: str):
    """Post-setup instructions for vLLM."""
    import urllib.request

    try:
        urllib.request.urlopen(host, timeout=2)
        _step(f"vLLM server running at {host}", "ok")
    except Exception:
        _step("vLLM server not detected", "skip")
        console.print(f"    [{TEXT_DIM}]Start vLLM:[/]")
        console.print(f"    [{TEXT_DIM}]  python -m vllm.entrypoints.openai.api_server --model {model}[/]")
        console.print()


def _post_setup_cloud(provider: str, env_var: str):
    """Verify cloud API key is set."""
    import os
    key = os.environ.get(env_var, "")
    if key:
        masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(set)"
        _step(f"{env_var}: {masked}", "ok")
    else:
        _step(f"{env_var} not set", "skip")
        console.print(f"    [{TEXT_DIM}]Set the {env_var} environment variable or[/]")
        console.print(f"    [{TEXT_DIM}]add it to your shell profile.[/]")
        console.print()


# ═══════════════════════════════════════════════════════════════
# Main wizard entry point
# ═══════════════════════════════════════════════════════════════

def run_tui_wizard():
    """Run the full 5-phase TUI setup wizard."""
    console.clear()

    # ── Welcome ─────────────────────────────────────────────
    _banner()

    welcome = Panel(
        f"[{TEXT}]Welcome to Custo Setup.[/]\n\n"
        f"[{TEXT_DIM}]This wizard will guide you through configuring[/]\n"
        f"[{TEXT_DIM}]your autonomous digital operator in 5 phases.[/]\n\n"
        f"[{EMERALD}]  Phase 1[/]  [{TEXT_DIM}]→[/]  Security & Safety Confirmation\n"
        f"[{BLUE}]  Phase 2[/]    [{TEXT_DIM}]→[/]  Gateway Configuration\n"
        f"[{TEAL}]  Phase 3[/]    [{TEXT_DIM}]→[/]  Model & API Authentication\n"
        f"[{GREEN}]  Phase 4[/]   [{TEXT_DIM}]→[/]  Channel & Interface Integration\n"
        f"[{PURPLE}]  Phase 5[/]  [{TEXT_DIM}]→[/]  Workspace & Skills Setup",
        border_style=EMERALD, box=box.ROUNDED, padding=(1, 2)
    )
    console.print(Align.center(welcome))
    console.print()

    if not Confirm.ask("  Begin setup?", default=True, console=console):
        console.print(f"\n  [{RED}]Setup cancelled.[/]")
        return

    # ── Phase 1: Security ──────────────────────────────────
    console.clear()
    _banner()
    phase1_security()

    console.print("\n")
    if not Confirm.ask("  Proceed to Phase 2 (Gateway Configuration)?", default=True, console=console):
        console.print(f"\n  [{RED}]Setup cancelled.[/]")
        return

    # ── Phase 2: Gateway ───────────────────────────────────
    console.clear()
    _banner()
    gateway_cfg = phase2_gateway()

    console.print("\n")
    _summary_table(gateway_cfg)
    console.print("\n")
    if not Confirm.ask("  Proceed to Phase 3 (Model Setup)?", default=True, console=console):
        console.print(f"\n  [{RED}]Setup cancelled.[/]")
        return

    # ── Phase 3: Model ─────────────────────────────────────
    console.clear()
    _banner()
    llm_cfg = phase3_model()

    console.print("\n")
    _summary_table(llm_cfg)
    console.print("\n")
    if not Confirm.ask("  Proceed to Phase 4 (Channels)?", default=True, console=console):
        console.print(f"\n  [{RED}]Setup cancelled.[/]")
        return

    # ── Phase 4: Channels ──────────────────────────────────
    console.clear()
    _banner()
    channels_cfg = phase4_channels()

    console.print("\n")
    if not Confirm.ask("  Proceed to Phase 5 (Workspace & Skills)?", default=True, console=console):
        console.print(f"\n  [{RED}]Setup cancelled.[/]")
        return

    # ── Phase 5: Workspace ─────────────────────────────────
    console.clear()
    _banner()
    workspace_cfg = phase5_workspace()

    # ── Save ───────────────────────────────────────────────
    console.print("\n")
    _divider()
    console.print(f"\n  [{BLUE}]▸[/] Saving configuration...\n")
    _save_config(gateway_cfg, llm_cfg, channels_cfg, workspace_cfg)

    # ── Post-setup: Provider actions ───────────────────────
    console.print(f"\n  [{BLUE}]▸[/] Checking provider setup...\n")
    provider = llm_cfg.get("provider", "")
    model = llm_cfg.get("model", "")

    if provider == "ollama":
        _post_setup_ollama(model, llm_cfg.get("auto_download", False))
    elif provider == "lmstudio":
        _post_setup_lmstudio()
    elif provider == "vllm":
        _post_setup_vllm(model, llm_cfg.get("vllm_host", "http://127.0.0.1:8000"))
    elif provider in ("openai", "anthropic", "gemini"):
        _post_setup_cloud(provider, llm_cfg.get("api_key_env", ""))
    else:
        _step("No LLM provider configured — using hardcoded responses", "skip")

    # ── Completion screen ──────────────────────────────────
    console.print("\n")
    _divider()
    console.print()

    provider_name = {
        "ollama": "Ollama", "lmstudio": "LM Studio", "vllm": "vLLM",
        "openai": "OpenAI", "anthropic": "Anthropic", "gemini": "Gemini",
        "hardcoded": "Hardcoded (no LLM)"
    }.get(provider, provider.capitalize())

    gateway_addr = f"{gateway_cfg.get('bind_address', '127.0.0.1')}:{gateway_cfg.get('port', 18789)}"

    completed = Panel(
        f"[{EMERALD}]  Setup complete![/]\n\n"
        f"[{TEXT_DIM}]  Summary:[/]\n"
        f"    [{EMERALD}]✓[/]  Security confirmed\n"
        f"    [{BLUE}]✓[/]  Gateway: {gateway_addr}\n"
        f"    [{TEAL}]✓[/]  Provider: {provider_name} ({model or 'N/A'})\n"
        f"    [{GREEN}]✓[/]  Channels: {sum(1 for v in channels_cfg.values() if v)} enabled\n"
        f"    [{PURPLE}]✓[/]  Skills: {len(workspace_cfg.get('skills_enabled', []))} enabled\n"
        f"\n"
        f"[{EMERALD}]  ─── Commands ───────────────────────[/]\n"
        f"\n"
        f"  [{EMERALD}]custo chat[/]     Start a conversation with Custo\n"
        f"  [{BLUE}]custo doctor[/]    Run a system health check\n"
        f"  [{TEAL}]custo daemon[/]    Start/stop the background service\n"
        f"  [{GREEN}]custo help[/]      Show all available commands\n"
        f"  [{PURPLE}]custo setup[/]    Re-run this setup wizard\n"
        f"\n"
        f"[{EMERALD}]  ────────────────────────────────────[/]",
        border_style=EMERALD, box=box.DOUBLE, padding=(2, 4)
    )
    console.print(Align.center(completed))

    # ── Offer to start chatting ────────────────────────────
    console.print()
    if Confirm.ask("  Start chatting now?", default=True, console=console):
        _step("Launching chat...", "ok")
        from interfaces.terminal.tui import ChatTUI
        import asyncio
        tui = ChatTUI()
        asyncio.run(tui.run())
    else:
        console.print(f"\n  [{TEXT_DIM}]Run 'custo chat' whenever you're ready.[/]")
        console.print()


def run_wizard(root_path: str = None):
    """Entry point called from init_config.py / first_run.py."""
    if not RICH_AVAILABLE:
        console.print(f"[{RED}]rich library required.[/] Install: pip install rich prompt-toolkit")
        console.print("Falling back to basic wizard...")
        from setup.init_config import run_wizard as basic_wizard
        return basic_wizard(root_path)

    run_tui_wizard()


if __name__ == "__main__":
    run_tui_wizard()
