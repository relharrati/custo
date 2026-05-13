#!/usr/bin/env python3
"""
Custo Setup Wizard — Interactive TUI with Arrow Keys
─────────────────────────────────────────────────────
Arrow keys navigate  •  Space selects  •  Enter confirms
Never type a number or y/n again.

Exports:
    run_tui_wizard()  — called by init_config.py, install.py, first_run.py
"""

import os
import sys
import subprocess
import shutil
import time
import re
import socket
import secrets
import platform
import json
import threading
from pathlib import Path

if os.name == "nt":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Auto-install InquirerPy if missing ──────────────────────
try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from InquirerPy.separator import Separator
    HAS_INQUIRER = True
except ImportError:
    HAS_INQUIRER = False

# ── Constants ───────────────────────────────────────────────

APP_NAME = "Custo"
OLLAMA_PORT = 11434
CUSTO_PORT_DEFAULT = 18789
PROVIDER_MODELS = {
    "ollama": [
        ("qwen2.5-coder:0.5b",   "Tiny    0.5B  ~ 500 MB RAM"),
        ("qwen2.5-coder:1.5b",   "Small   1.5B  ~ 1.1 GB RAM"),
        ("qwen2.5-coder:3b",     "Medium  3B    ~ 2.0 GB RAM"),
        ("qwen2.5-coder:7b",     "Large   7B    ~ 4.5 GB RAM"),
        ("qwen2.5-coder:14b",    "Huge   14B    ~ 9 GB RAM"),
        ("llama3.2:1b",          "Meta Llama 3.2 1B"),
        ("llama3.2:3b",          "Meta Llama 3.2 3B"),
    ],
    "openai": [
        ("gpt-4o-mini",          "GPT-4o Mini (cheapest)"),
        ("gpt-4o",               "GPT-4o (full)"),
        ("gpt-3.5-turbo",        "GPT-3.5 Turbo (legacy)"),
    ],
    "anthropic": [
        ("claude-3-haiku-20240307",   "Claude 3 Haiku"),
        ("claude-3-sonnet-20240229",  "Claude 3 Sonnet"),
        ("claude-3-opus-20240229",    "Claude 3 Opus"),
    ],
    "lm-studio": [
        ("local", "Auto-detect local model"),
    ],
}

RECOMMENDATIONS = [
    {"max_ram": 2,  "model": "qwen2.5-coder:0.5b",  "label": "Tiny 0.5B — ~500 MB RAM"},
    {"max_ram": 4,  "model": "qwen2.5-coder:1.5b",  "label": "Small 1.5B — ~1.1 GB RAM"},
    {"max_ram": 8,  "model": "qwen2.5-coder:3b",    "label": "Medium 3B — ~2 GB RAM"},
    {"max_ram": 16, "model": "qwen2.5-coder:7b",    "label": "Large 7B — ~4.5 GB RAM"},
    {"max_ram": 999,"model": "qwen2.5-coder:14b",   "label": "Huge 14B — needs 9 GB+"},
]

STATE = {
    "provider": "ollama",
    "model": "qwen2.5-coder:1.5b",
    "port": CUSTO_PORT_DEFAULT,
    "channels": ["stdio", "sse"],
    "skills": ["file-system", "web-search", "code-execution", "shell-exec"],
    "api_key": None,
    "ram_gb": None,
}

# ── InquirerPy style ───────────────────────────────────────

def custom_style():
    """Return an InquirerPy style object."""
    from InquirerPy import get_style
    return get_style([
        ("questionmark", "hidden"),
        ("question", "#2dd4bf bold"),
        ("pointer", "#818cf8"),
        ("highlighted", "#818cf8 bold"),
        ("selected", "#34d399"),
        ("answer", "#a78bfa bold"),
        ("instruction", "#64748b"),
        ("separator", "#475569"),
        ("checkbox", "#818cf8"),
        ("checkbox-checked", "#34d399"),
    ])

# ── Logo ────────────────────────────────────────────────────

LOGO = r"""
  ┌─────────────────────────────────────────┐
  │          🔮  CUSTO SETUP WIZARD  🔮     │
  │   Autonomous Operator • Self-Hosted AI  │
  └─────────────────────────────────────────┘
"""

# ── Utilities ───────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def _detect_ram():
    """Detect total RAM in GB (best-effort)."""
    try:
        if sys.platform == "darwin":
            out, _, _ = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
            ).stdout.strip(), "", 0
            return max(1, int(int(out) / (1024**3)))
        elif sys.platform.startswith("linux"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        kb = int(line.split()[1])
                        return max(1, int(kb / (1024**2)))
        elif os.name == "nt":
            import ctypes
            class MEM(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExt", ctypes.c_ulonglong),
                ]
            m = MEM()
            m.dwLength = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return max(1, int(m.ullTotalPhys / (1024**3)))
    except Exception:
        pass
    return 4  # safe default

def recommend_model(ram_gb):
    for rec in RECOMMENDATIONS:
        if ram_gb <= rec["max_ram"]:
            return rec["model"], rec["label"]
    return "qwen2.5-coder:14b", "Huge (14B) — needs 32GB+"

def run_cmd(cmd, shell=False, timeout=300):
    if isinstance(cmd, str) and not shell:
        cmd = cmd.split()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           shell=shell, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timed out", 1
    except FileNotFoundError:
        return "", "not found", 127

def check_port(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def save_config(state):
    """Save wizard state to system/config.yaml."""
    import yaml
    base = Path(__file__).resolve().parent.parent
    config_path = base / "system" / "config.yaml"
    cfg = {
        "version": "1.0.0",
        "system": {"name": "Custo", "description": "Autonomous Digital Operator"},
        "daemon": {"pid_dir": "daemon/pid", "log_dir": "logs",
                    "heartbeat_interval": 5, "session_timeout": 3600},
        "memory": {"short_term_ttl": 86400, "daily_retention_days": 30,
                    "compression_enabled": True},
        "agents": {"default": "main", "timeout_seconds": 300, "max_retries": 3},
        "interfaces": {
            "terminal": {"enabled": True},
            "web": {"enabled": False, "port": 8080},
            "gateways": {"discord": False, "whatsapp": False},
        },
        "logging": {"level": "INFO",
                     "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "llm": {
            "provider": state["provider"],
            "model": state["model"],
            "auto_download": True,
            "context_window": 4096,
            "temperature": 0.7,
            "max_tokens": 512,
            "ollama_host": "http://127.0.0.1:11434",
        },
        "gateway": {"enabled": True, "port": state["port"], "cors": True},
        "skills": state.get("skills", []),
        "channels": state.get("channels", []),
    }
    base.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
    return config_path

# ── Spinner ────────────────────────────────────────────────

class Spinner:
    def __init__(self, text="Working..."):
        self.text = text
        self._stop = threading.Event()
        self._thread = None

    def _spin(self):
        frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        i = 0
        while not self._stop.is_set():
            out = f"\r  {frames[i]} {self.text}"
            sys.stdout.write(out)
            sys.stdout.flush()
            i = (i + 1) % len(frames)
            time.sleep(0.1)

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, success_text=None):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        if success_text:
            sys.stdout.write(f"\r  {success_text}")
        else:
            sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

# ── InquirerPy-compatible checkbox prompt (fallback for no InquirerPy) ──

def _checkbox_prompt(message, choices, default=None):
    """
    Interactive checkbox using InquirerPy (space=toggle, enter=confirm).
    Falls back to manual number selection if InquirerPy unavailable.
    """
    if HAS_INQUIRER:
        from InquirerPy import inquirer
        style = custom_style()
        selected = inquirer.checkbox(
            message=message,
            choices=choices,
            default=default or [],
            style=style,
            instruction="  (↑↓ move, Space toggle, Enter confirm)",
        ).execute()
        return selected
    else:
        # Fallback: print options, ask for comma-separated numbers
        print(f"\n  {message}")
        for i, (label, _) in enumerate(choices, 1):
            active = "X" if (default and choices[i-1][1] in default) else " "
            print(f"  [{active}] {i}. {label}")
        while True:
            raw = input("  Enter numbers (comma-separated, or Enter for all): ").strip()
            if not raw:
                return [c[1] for c in choices]
            try:
                nums = [int(x.strip()) for x in raw.split(",")]
                if all(1 <= n <= len(choices) for n in nums):
                    return [choices[n-1][1] for n in nums]
            except ValueError:
                pass
            print(f"  Invalid. Enter 1-{len(choices)} separated by commas.")

def _confirm_prompt(message, default=True):
    if HAS_INQUIRER:
        return inquirer.confirm(message, default=default, style=custom_style()).execute()
    ans = input(f"  {message} [{'Y' if default else 'y'}/{'N' if not default else 'n'}]: ").strip().lower()
    return ans not in ("n", "no") if default else ans in ("y", "yes")

def _select_prompt(message, choices, default=None):
    if HAS_INQUIRER:
        return inquirer.select(
            message=message,
            choices=choices,
            default=default,
            style=custom_style(),
            instruction="  (↑↓ to move, Enter to select)",
        ).execute()
    else:
        print(f"\n  {message}")
        for i, (label, val) in enumerate(choices, 1):
            print(f"  {i}. {label}")
        while True:
            raw = input(f"  Select [1-{len(choices)}] (default: 1): ").strip()
            if not raw:
                return default if default else choices[0][1]
            try:
                n = int(raw)
                if 1 <= n <= len(choices):
                    return choices[n-1][1]
            except ValueError:
                pass
            print(f"  Invalid. Enter 1-{len(choices)}.")

# ── PHASES ─────────────────────────────────────────────────

def phase_1_welcome():
    clear()
    print(LOGO)
    print("  \033[1;97mWelcome to the Custo Setup Wizard\033[0m")
    print("  \033[1;90mArrow keys \u2192 navigate  |  Space \u2192 toggle  |  Enter \u2192 confirm\033[0m")
    print()

    ram = _detect_ram()
    STATE["ram_gb"] = ram
    rec_model, rec_label = recommend_model(ram)

    print("  \033[1;94m\u25a0 System Detection\033[0m")
    print(f"  OS:       \033[1m{platform.system()} {platform.release()}\033[0m")
    print(f"  Arch:     \033[1m{platform.machine()}\033[0m")
    print(f"  Python:   \033[1m{platform.python_version()}\033[0m")
    color = "\033[1;32m" if ram >= 8 else "\033[1;33m" if ram >= 4 else "\033[1;31m"
    print(f"  RAM:      {color}{ram} GB\033[0m")
    print(f"  Recommend: \033[90m{rec_label}\033[0m")
    print()
    print("  Press Enter to continue...")
    if HAS_INQUIRER:
        inquirer.confirm(message="", default=True, style=custom_style()).execute()
    else:
        input()

def phase_2_security():
    clear()
    print(LOGO)
    print("  \033[1;34m\u25ba Phase 2: Security\033[0m")
    print()

    print("  \033[90mGenerating API key...\033[0m")
    key = secrets.token_urlsafe(32)
    STATE["api_key"] = key
    print(f"  \033[1;32m\u2713 API key: {key[:24]}...\033[0m")
    print()
    print("  \033[90mYou can change this in system/config.yaml later.\033[0m")
    print()

    use_custom = _confirm_prompt("Use a custom API key instead?", default=False)
    if use_custom:
        if HAS_INQUIRER:
            custom = inquirer.text(
                message="Enter your API key:",
                validate=lambda _, x: len(x) >= 8 or "min 8 chars",
                style=custom_style(),
            ).execute()
        else:
            custom = input("  Enter API key (min 8 chars): ").strip()
            while len(custom) < 8:
                custom = input("  Too short. Min 8 chars: ").strip()
        STATE["api_key"] = custom
        print(f"  \033[1;32m\u2713 Custom API key set\033[0m")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_3_model():
    clear()
    print(LOGO)
    print("  \033[1;34m\u25ba Phase 3: LLM Provider\033[0m")
    print()

    provider_choices = [
        ("\U0001f4bb  Ollama (local, recommended)", "ollama"),
        ("\U0001f50d  OpenAI API", "openai"),
        ("\U0001f9e0  Anthropic API", "anthropic"),
        ("\U0001f3a0  LM Studio", "lm-studio"),
    ]
    provider_label = _select_prompt("Pick your LLM provider:", provider_choices, default="ollama")
    STATE["provider"] = provider_label

    models = PROVIDER_MODELS.get(provider_label, [])
    model_choices = [(label, mid) for mid, label in models]

    if provider_label in ("ollama", "lm-studio"):
        # RAM-aware hint
        ram = STATE["ram_gb"]
        if ram and ram < 4 and provider_label == "ollama":
            print(f"\n  \033[1;33m\u26a0 Only {ram}GB RAM detected.\033[0m")
            print("  \033[90mSmaller models (0.5B-1.5B) will run smoothly.\033[0m")
            print()

        default_model = "qwen2.5-coder:1.5b"
        model_value = _select_prompt("Pick a model:", model_choices, default=default_model)
        STATE["model"] = model_value
    else:
        model_value = _select_prompt("Pick a model:", model_choices, default=models[0][1])
        STATE["model"] = model_value

        if HAS_INQUIRER:
            print("\n  \033[90mRemember to set your API key when running Custo.\033[0m")
        else:
            print("\n  Remember to set your API key when running Custo.")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_4_gateway():
    clear()
    print(LOGO)
    print("  \033[1;34m\u25ba Phase 4: Gateway\033[0m")
    print()

    custo_busy = check_port(CUSTO_PORT_DEFAULT)
    if custo_busy:
        print(f"  \033[1;33m\u26a0 Port {CUSTO_PORT_DEFAULT} is already in use.\033[0m")

    port_choices = [
        ("18789 (default)", 18789),
        ("8080", 8080),
        ("8000", 8000),
    ]
    port = _select_prompt("Gateway port:", port_choices, default=18789)
    STATE["port"] = port
    print(f"\n  \033[1;32m\u2713 Gateway will run on port {port}\033[0m")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_5_channels_skills():
    clear()
    print(LOGO)
    print("  \033[1;34m\u25ba Phase 5: Channels & Skills\033[0m")
    print()

    # Channels
    print("  \033[1;97mSelect communication channels:\033[0m")
    channel_choices = [
        ("Terminal (stdio)", "stdio"),
        ("HTTP SSE endpoint", "sse"),
        ("Telegram", "telegram"),
        ("Discord", "discord"),
    ]
    channel_defaults = ["stdio", "sse"]
    selected_channels = _checkbox_prompt("", channel_choices, default=channel_defaults)
    STATE["channels"] = selected_channels if selected_channels else channel_defaults
    print(f"\n  \033[1;32m\u2713 Channels: {', '.join(STATE['channels'])}\033[0m")
    print()

    # Skills
    print("  \033[1;97mSelect skills to enable:\033[0m")
    skill_choices = [
        ("File system (read/write files)", "file-system"),
        ("Web search (internet lookups)", "web-search"),
        ("Code execution (run code)", "code-execution"),
        ("Shell exec (shell commands)", "shell-exec"),
        ("Memory reflect (periodic review)", "memory-reflect"),
    ]
    skill_defaults = ["file-system", "web-search", "code-execution", "shell-exec"]
    selected_skills = _checkbox_prompt("", skill_choices, default=skill_defaults)
    STATE["skills"] = selected_skills if selected_skills else skill_defaults
    print(f"  \033[1;32m\u2713 Skills: {', '.join(STATE['skills'])}\033[0m")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_6_install_and_verify():
    clear()
    print(LOGO)
    print("  \033[1;34m\u25ba Phase 6: Install & Verify\033[0m")
    print()

    if STATE["provider"] != "ollama":
        print("  \033[90mProvider is not Ollama \u2014 skipping local install.\033[0m")
        print("  \033[90mRemember to configure your API key when running Custo.\033[0m")
        print()
        if not HAS_INQUIRER:
            input("  Press Enter to continue...")
        return

    # ── Install Ollama ──────────────────────────────────
    ollama_installed = bool(shutil.which("ollama"))
    if ollama_installed:
        ver_out, _, _ = run_cmd(["ollama", "--version"])
        ver = ver_out.strip().split()[0] if ver_out.strip() else "unknown"
        print(f"  \033[1;32m\u2713 Ollama found: {ver}\033[0m")
    else:
        print("  \033[1;33mOllama not installed.\033[0m")
        install_it = _confirm_prompt("Install Ollama now? (recommended)", default=True)
        if install_it:
            spinner = Spinner("Installing Ollama...")
            spinner.start()
            try:
                sys_name = platform.system().lower()
                if sys_name == "darwin":
                    run_cmd(["curl", "-fsSL", "https://ollama.com/install.sh"],
                            shell=True, timeout=120)
                elif sys_name == "linux":
                    run_cmd("curl -fsSL https://ollama.com/install.sh | sh",
                            shell=True, timeout=120)
                elif os.name == "nt":
                    exe = Path.home() / "AppData" / "Local" / "Temp" / "OllamaSetup.exe"
                    run_cmd([
                        "powershell", "-Command",
                        "Invoke-WebRequest",
                        "-Uri", "https://ollama.com/download/OllamaSetup.exe",
                        "-OutFile", str(exe)
                    ], timeout=120)
                    run_cmd([str(exe), "/S"], timeout=120)
                    ollama_dir = Path(os.environ.get("LOCALAPPDATA", "C:/Program Files")) / "Ollama"
                    if ollama_dir.exists():
                        os.environ["PATH"] = str(ollama_dir) + ";" + os.environ.get("PATH", "")
                else:
                    raise RuntimeError("Unsupported platform")
                spinner.stop("\033[1;32m\u2713 Ollama installed")
                print()
                ollama_installed = True
            except Exception as e:
                spinner.stop()
                print(f"\n  \033[1;31m\u2717 Install failed: {e}\033[0m")
                print("  Install manually: https://ollama.com/download")
                if not HAS_INQUIRER:
                    input("  Press Enter to continue anyway...")
                ollama_installed = False
        else:
            print("  \033[1;31mOllama is required for local LLM.\033[0m")
            print("  Install from https://ollama.com/download")
            if not HAS_INQUIRER:
                input("  Press Enter to continue anyway...")
            ollama_installed = False

    # ── Start daemon ────────────────────────────────────
    if ollama_installed:
        if check_port(OLLAMA_PORT):
            print(f"  \033[1;32m\u2713 Ollama running on port {OLLAMA_PORT}\033[0m")
        else:
            print("  Starting Ollama daemon...")
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
                )
            except FileNotFoundError:
                pass

            spinner = Spinner("Waiting for Ollama daemon...")
            spinner.start()
            daemon_ok = False
            for _ in range(30):
                if check_port(OLLAMA_PORT):
                    daemon_ok = True
                    break
                time.sleep(0.5)
            spinner.stop()
            if daemon_ok:
                print(f"  \033[1;32m\u2713 Daemon ready on port {OLLAMA_PORT}\033[0m")
            else:
                print(f"  \033[1;33m\u26a0 Daemon didn't respond. Start it manually: ollama serve\033[0m")
            print()

    # ── Pull model ──────────────────────────────────────
    model = STATE["model"]
    if model and ollama_installed:
        spinner = Spinner(f"Pulling model: {model}")
        spinner.start()
        try:
            out, err, code = run_cmd(["ollama", "pull", model], timeout=600)
        except Exception as e:
            spinner.stop()
            print(f"\n  \033[1;31m\u2717 Pull failed: {e}\033[0m")
        else:
            spinner.stop()
            if code == 0:
                print(f"  \033[1;32m\u2713 Model '{model}' ready\033[0m")
            else:
                err_snippet = err[:150] if err else "unknown error"
                print(f"  \033[1;31m\u2717 Pull failed: {err_snippet}\033[0m")
        print()

    # ── Verify ──────────────────────────────────────────
    if model and ollama_installed:
        spinner = Spinner("Verifying setup...")
        spinner.start()
        out, _, code = run_cmd(["ollama", "list"], timeout=30)
        spinner.stop()
        if code == 0 and model in out:
            print(f"  \033[1;32m\u2713 Setup verified successfully\033[0m")
        else:
            print(f"  \033[1;33m\u26a0 Model may still be loading. Try 'ollama list' to check.\033[0m")
        print()

    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_done():
    clear()
    print(LOGO)
    print("  \033[1;32m╔══════════════════════════════════════════╗\033[0m")
    print("  \033[1;32m║        \u2728 S E T U P   C O M P L E T E \u2728    ║\033[0m")
    print("  \033[1;32m╚══════════════════════════════════════════╝\033[0m")
    print()
    print("  Summary:")
    print(f"    Provider : \033[1m{STATE['provider']}\033[0m")
    print(f"    Model    : \033[1m{STATE['model']}\033[0m")
    print(f"    Gateway  : \033[1mhttp://127.0.0.1:{STATE['port']}\033[0m")
    print(f"    Channels : \033[1m{', '.join(STATE['channels'])}\033[0m")
    print(f"    Skills   : \033[1m{', '.join(STATE['skills'])}\033[0m")
    print()

    # Save config
    try:
        cfg_path = save_config(STATE)
        print(f"  \033[1;32m\u2713 Config saved: {cfg_path}\033[0m")
    except Exception as e:
        print(f"  \033[1;31m\u2717 Failed to save config: {e}\033[0m")
    print()

    print("  \033[1;90mNext commands to try:\033[0m")
    print("    custo chat     \u2014 Start a conversation")
    print("    custo daemon   \u2014 Start background service")
    print("    custo doctor   \u2014 Health check")
    print("    custo help     \u2014 All commands")
    print()

    # Ask to launch chat
    chat = _confirm_prompt("Launch chat now?", default=True)
    if chat:
        print("\n  Starting Custo chat...\n")
        time.sleep(0.5)
        subprocess.Popen(
            [sys.executable, "-m", "custo", "chat"],
            creationflags=(0 if os.name != "nt" else subprocess.CREATE_NEW_PROCESS_GROUP),
        )

# ── Main Entry Point ──────────────────────────────────────

def run_tui_wizard():
    """
    Entry point called by init_config.py, install.py, first_run.py.
    """
    # Auto-install InquirerPy if missing
    global HAS_INQUIRER
    if not HAS_INQUIRER:
        print("\n  \033[1;33mInstalling InquirerPy for the interactive wizard...\033[0m")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "InquirerPy", "-q"]
            )
            from InquirerPy import inquirer
            HAS_INQUIRER = True
        except Exception:
            print("  \033[1;33mCouldn't install InquirerPy. Falling back to basic prompts.\033[0m")
            HAS_INQUIRER = False

    try:
        phase_1_welcome()
        phase_2_security()
        phase_3_model()
        phase_4_gateway()
        phase_5_channels_skills()
        phase_6_install_and_verify()
        phase_done()
    except KeyboardInterrupt:
        print("\n\n  \033[1;33mSetup cancelled. Goodbye!\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n  \033[1;31mSetup failed: {e}\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    run_tui_wizard()