"""
Initialize Configuration - First-run Configuration Generator

Extended with interactive LLM provider and model selection wizard
(arrow-key TUI via InquirerPy).
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml


DEFAULT_CONFIG = {
    "version": "1.0.0",
    "system": {
        "name": "Custo",
        "description": "Autonomous Digital Operator",
        "timezone": "Africa/Casablanca",
        "locale": "en-US"
    },
    "daemon": {
        "pid_dir": "daemon/pid",
        "log_dir": "logs",
        "heartbeat_interval": 5,
        "session_timeout": 3600
    },
    "memory": {
        "short_term_ttl": 86400,
        "daily_retention_days": 30,
        "compression_enabled": True
    },
    "agents": {
        "default": "main",
        "timeout_seconds": 300,
        "max_retries": 3
    },
    "interfaces": {
        "terminal": {"enabled": True},
        "web": {"enabled": False, "port": 8080},
        "gateways": {"discord": False, "whatsapp": False}
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    "llm": {
        "provider": "auto",
        "model": "",
        "auto_download": True,
        "context_window": 4096,
        "temperature": 0.7,
        "max_tokens": 512
    }
}


def load_config(root_path: Path = None) -> dict:
    """Load system configuration from YAML, with defaults."""
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"

    if config_path.exists():
        try:
            user_config = yaml.safe_load(config_path.read_text())
            return _deep_merge(DEFAULT_CONFIG, user_config or {})
        except Exception as e:
            print(f"[CONFIG] Warning: Could not parse config.yaml: {e}")
            print("[CONFIG] Using defaults")

    return DEFAULT_CONFIG.copy()


def _deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge update dict into base dict."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def save_config(config: dict, root_path: Path = None):
    """Save configuration to YAML file."""
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))


# ---------------------------------------------------------------------------
# LLM wizard helpers (kept for basic fallback)
# ---------------------------------------------------------------------------

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
        elif sys.platform.startswith("linux"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kB = int(line.split()[1])
                        return max(1, int(kB / 1024 / 1024 + 0.5))
        elif sys.platform == "darwin":
            import subprocess
            r = subprocess.run(["sysctl", "-n", "hw.memsize"],
                               capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                return max(1, int(int(r.stdout.strip()) / (1024**3)))
    except Exception:
        pass
    return 4


def _provider_menu():
    """Display provider choice menu."""
    print("\nChoose an LLM provider:")
    print("  1) Ollama       — Recommended. Easy setup, runs locally")
    print("  2) OpenAI API")
    print("  3) Anthropic API")
    print("  4) LM Studio    — GUI app, loads any GGUF model")
    print("  5) Skip / use hardcoded responses (bootstrap mode)")
    print()
    choices = {"1": "ollama", "2": "openai", "3": "anthropic",
               "4": "lm-studio", "5": "hardcoded"}
    while True:
        sel = input("Select [1-5] (default: 1 - Ollama): ").strip()
        if not sel:
            sel = "1"
        if sel in choices:
            return choices[sel]
        print("  Invalid choice. Enter 1-5.")


def _ram_str(ram_gb: int) -> str:
    if ram_gb >= 1024:
        return f"{ram_gb // 1024}+ TB"
    if ram_gb >= 100:
        return f"{ram_gb} GB (high-end)"
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
        return f"{ram_gb} GB (very limited)"
    return "unknown (could not detect)"


def _display_model_menu(provider: str, ram_gb: int):
    """Show tiered model recommendations for the detected RAM."""
    from system.llm import OllamaProvider

    print(f"\n  Detected: ~{_ram_str(ram_gb)} RAM")
    print(f"  Recommended model size to leave breathing room:")
    print()

    tiers_dict = OllamaProvider.recommend_models(ram_gb)
    tier_order = ["minimal", "small", "medium", "large"]
    tier_labels = {
        "minimal": "Minimal models (< 2GB RAM)",
        "small": "Small models (2-8GB RAM)",
        "medium": "Medium models (8-24GB RAM)",
        "large": "Large models (24GB+ RAM)",
    }

    options = []
    idx = 1
    for tier_key in tier_order:
        models = tiers_dict.get(tier_key, [])
        if not models:
            continue
        print(f"  [{tier_key.upper()}] {tier_labels[tier_key]}")
        for model_id, name, size, note in models:
            print(f"      {idx}) {name:30s} {size:10s}  -- {note}")
            options.append((model_id, name))
            idx += 1
        print()

    return options


def _ask_auto_download() -> bool:
    """Ask whether to auto-download missing models."""
    print()
    print("  Auto-download: If the chosen model isn't installed, Custo can")
    print("  automatically run `ollama pull <model>` in the background.")
    print()
    while True:
        ans = input("  Enable auto-download? [Y/n]: ").strip().lower()
        if not ans or ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("    Please answer Y or N.")


def _run_ollama_wizard(ram_gb: int):
    """Interactive Ollama provider setup (basic fallback)."""
    print("\n" + "=" * 55)
    print("  Ollama Provider Setup")
    print("=" * 55)
    print()
    print("  Ollama is a local LLM runner. If not installed, visit:")
    print("  https://ollama.ai and download for your platform.")
    print()

    import subprocess
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=3)
        print("  [OK] Ollama CLI found")
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:11434", timeout=2)
            print("  [OK] Ollama daemon reachable at http://127.0.0.1:11434")
        except Exception:
            print("  [WARN] Ollama daemon not running -- start with `ollama serve`")
    except FileNotFoundError:
        print("  [WARN] Ollama not installed -- install from https://ollama.ai first")

    options = _display_model_menu("ollama", ram_gb)

    print()
    print("  Choose a model:")
    print("    Press a number, or Enter for the recommended default.")
    while True:
        sel = input(f"  Selection [1-{len(options)}] (default: 1): ").strip()
        if not sel:
            model_id, name = options[0]
            print(f"  -> Using: {name} ({model_id})")
            break
        try:
            n = int(sel)
            if 1 <= n <= len(options):
                model_id, name = options[n - 1]
                print(f"  -> Using: {name} ({model_id})")
                break
        except ValueError:
            pass
        print(f"  Invalid -- enter 1-{len(options)} or Enter for default")

    auto_dl = _ask_auto_download()

    return {
        "provider": "ollama",
        "model": model_id,
        "auto_download": auto_dl,
        "ollama_host": "http://127.0.0.1:11434"
    }


def _run_lmstudio_wizard(ram_gb: int):
    """Interactive LM Studio provider setup (basic fallback)."""
    print("\n" + "=" * 55)
    print("  LM Studio Provider Setup")
    print("=" * 55)
    print()
    print("  LM Studio is a desktop GUI for loading GGUF models.")
    print("  Download from https://lmstudio.ai and start the local server")
    print("  (Server tab -> Start Server).")
    print()

    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=2)
        print("  [OK] LM Studio server is running at http://127.0.0.1:1234")
    except Exception:
        print("  [INFO] No LM Studio server detected -- start it from the app")

    print()
    if ram_gb >= 8:
        print("  Models to try: llama3.2:3b, qwen2.5-coder:7b")
        default_model = "llama3.2"
    elif ram_gb >= 4:
        print("  Models to try: llama3.2:3b, gemma3:2b")
        default_model = "llama3.2"
    else:
        print("  Models to try: phi4-mini:3b, tinyllama:1b")
        default_model = "phi4-mini"

    model_input = input(f"\n  Model name (default: {default_model}): ").strip()
    model = model_input or default_model
    print(f"  -> Using model: {model}")

    return {
        "provider": "lm-studio",
        "model": model,
        "auto_download": False,
        "lmstudio_host": "http://127.0.0.1:1234"
    }


def _run_vllm_wizard(ram_gb: int):
    """Interactive vLLM provider setup (basic fallback, advanced)."""
    print("\n" + "=" * 55)
    print("  vLLM Provider Setup (Advanced)")
    print("=" * 55)
    print()
    print("  vLLM is a high-throughput LLM serving engine.")
    print("  Requires a model in supported format, typically GPU.")
    print("  See: https://docs.vllm.ai")
    print()

    model = input("  Model (HF ID, e.g. meta-llama/Llama-3.2-3B-Instruct): ").strip()
    if not model:
        print("  [WARN] No model specified -- falling back to hardcoded")
        return {"provider": "hardcoded"}

    host = input("  Server host (default: http://127.0.0.1:8000): ").strip()
    if not host:
        host = "http://127.0.0.1:8000"

    print(f"  -> Provider: vLLM")
    print(f"  -> Model: {model}")
    print(f"  -> Host: {host}")
    print()
    print("  [NOTE] You must start the vLLM server separately:")
    print(f"    python -m vllm.entrypoints.openai.api_server --model {model}")

    return {
        "provider": "vllm",
        "model": model,
        "auto_download": False,
        "vllm_host": host
    }


def run_wizard(root_path: str = None) -> dict:
    """
    Run the full interactive TUI setup wizard.
    Delegates to setup.tui_setup.run_tui_wizard() which uses InquirerPy.
    Falls back to basic text prompts if InquirerPy is missing.
    """
    base = Path(root_path or Path(__file__).parent.parent)

    try:
        from setup.tui_setup import run_tui_wizard
        run_tui_wizard()
        return {}
    except ImportError:
        return _basic_llm_wizard(base)


def _basic_llm_wizard(base: Path) -> dict:
    """Basic text-only LLM wizard when rich/InquirerPy unavailable."""
    print("\n" + "=" * 60)
    print("  Custo LLM Provider Setup (basic)")
    print("=" * 60)
    print("  Install InquirerPy for the full TUI: pip install rich prompt-toolkit")
    print()

    ram_gb = _detect_ram()
    print(f"  System RAM detected: ~{_ram_str(ram_gb)}")

    provider = _provider_menu()
    llm_config = {"provider": "hardcoded", "model": "", "auto_download": False}

    if provider == "ollama":
        llm_config = _run_ollama_wizard(ram_gb)
    elif provider == "lm-studio":
        llm_config = _run_lmstudio_wizard(ram_gb)
    elif provider == "vllm":
        llm_config = _run_vllm_wizard(ram_gb)
    elif provider == "openai":
        key = input("  Enter OpenAI API key: ").strip()
        llm_config = {"provider": "openai", "model": "gpt-4o-mini",
                       "auto_download": False, "api_key": key}
    elif provider == "anthropic":
        key = input("  Enter Anthropic API key: ").strip()
        llm_config = {"provider": "anthropic", "model": "claude-3-haiku-20240307",
                       "auto_download": False, "api_key": key}
    else:
        print("\n  Skipping LLM setup -- using hardcoded responses.")

    cfg = load_config(base)
    cfg["llm"] = {**cfg.get("llm", {}), **llm_config,
                   "context_window": 4096, "temperature": 0.7, "max_tokens": 512}
    save_config(cfg, base)

    print()
    print("  Saved to system/config.yaml")
    print("  Run 'py setup/init_config.py --wizard' for full TUI setup")
    print()

    return llm_config


def init_config(root_path: str = None, wizard: bool = False):
    """Initialize configuration file. Use --wizard flag for full TUI setup."""
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"

    if config_path.exists():
        if os.environ.get("CUSTO_NONINTERACTIVE") == "1":
            print(f"[CONFIG] Config exists at {config_path} (keeping existing)")
            return
        print(f"[CONFIG] Config already exists at {config_path}")
        # Try InquirerPy confirm first
        try:
            from InquirerPy import inquirer
            overwrite = inquirer.confirm(
                message="Overwrite existing config?",
                default=False,
            ).execute()
        except Exception:
            response = input("Overwrite? (y/N): ").strip().lower()
            overwrite = response == 'y'
        if not overwrite:
            print("[CONFIG] Aborted.")
            return

    if wizard:
        run_wizard(base)
        return

    # Non-interactive: write defaults
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(DEFAULT_CONFIG, default_flow_style=False, sort_keys=False))
    print(f"[CONFIG] Configuration written to {config_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--wizard", action="store_true", help="Run full interactive setup wizard")
    args = parser.parse_args()

    if args.wizard:
        run_wizard()
    else:
        init_config()