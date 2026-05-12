"""
Initialize Configuration - First-run Configuration Generator

Extended with interactive LLM provider and model selection wizard.
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

# ---------------------------------------------------------------------------
# LLM wizard helpers
# ---------------------------------------------------------------------------

def _detect_ram() -> int:
    """Best-effort RAM detection in GB."""
    try:
        import os
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
    return 0  # unknown


def _provider_menu():
    """Display provider choice menu."""
    print("\nChoose an LLM provider:")
    print("  1) Ollama       — Recommended. Easy setup, auto-download, runs locally")
    print("  2) LM Studio    — GUI app, loads any GGUF model, OpenAI-compatible")
    print("  3) vLLM         — High-throughput server (GPU/CPU), for advanced users")
    print("  4) Skip / use hardcoded responses (bootstrap mode)")
    print()
    choices = {"1": "ollama", "2": "lmstudio", "3": "vllm", "4": "hardcoded"}
    while True:
        sel = input("Select [1-4] (default: 1 - Ollama): ").strip()
        if not sel:
            sel = "1"
        if sel in choices:
            return choices[sel]
        print("  Invalid choice. Enter 1, 2, 3 or 4.")


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
    # Convert dict to ordered list
    tier_order = ["minimal", "small", "medium", "large"]
    tier_labels = {
        "minimal": "Minimal models (< 2GB RAM)",
        "small": "Small models (2–8GB RAM)",
        "medium": "Medium models (8–24GB RAM)",
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
            print(f"      {idx}) {name:30s} {size:10s}  — {note}")
            options.append(model_id)
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
    """Interactive Ollama provider setup."""
    print("\n" + "=" * 55)
    print("  Ollama Provider Setup")
    print("=" * 55)
    print()
    print("  Ollama is a local LLM runner. If not installed, visit:")
    print("  https://ollama.ai and download for your platform.")
    print()

    # Check if Ollama is installed/running
    import subprocess
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=3)
        print("  [OK] Ollama CLI found")
        try:
            urllib.request.urlopen("http://127.0.0.1:11434", timeout=2)
            print("  [OK] Ollama daemon reachable at http://127.0.0.1:11434")
        except Exception:
            print("  [WARN] Ollama daemon not running — start it with `ollama serve` in another terminal")
    except FileNotFoundError:
        print("  [WARN] Ollama not installed — install from https://ollama.ai first")

    # Show model menu
    options = _display_model_menu("ollama", ram_gb)

    print()
    print("  Choose a model to use:")
    print("    Press a number for that model, or press Enter for the recommended default.")
    while True:
        sel = input(f"  Selection [1–{len(options)}] (default: 1): ").strip()
        if not sel:
            model_id, name = options[0]
            print(f"  → Using: {name} ({model_id})")
            break
        try:
            n = int(sel)
            if 1 <= n <= len(options):
                model_id, name = options[n - 1]
                print(f"  → Using: {name} ({model_id})")
                break
        except ValueError:
            pass
        print(f"  Invalid — enter 1–{len(options)} or Enter for default")

    auto_dl = _ask_auto_download()

    return {
        "provider": "ollama",
        "model": model_id,
        "auto_download": auto_dl,
        "ollama_host": "http://127.0.0.1:11434"
    }


def _run_lmstudio_wizard(ram_gb: int):
    """Interactive LM Studio provider setup."""
    print("\n" + "=" * 55)
    print("  LM Studio Provider Setup")
    print("=" * 55)
    print()
    print("  LM Studio is a desktop GUI for loading GGUF models.")
    print("  Download from https://lmstudio.ai and start the local server")
    print("  (Server tab → Start Server).")
    print()

    # Check for reachable LM Studio server
    try:
        urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=2)
        print("  [OK] LM Studio server is running at http://127.0.0.1:1234")
    except Exception:
        print("  [INFO] No LM Studio server detected — you'll need to start it")
        print("         (open LM Studio → select a model → Server tab → Start)")

    print()
    print("  Recommended GGUF models for your RAM:")
    print("  (Enter the exact model filename you'll load in LM Studio)")
    print()
    print(f"    ~{_ram_str(ram_gb)} → try:")
    if ram_gb >= 8:
        print("       • llama3.2:3b (lightweight, good)")
        print("       • qwen2.5-coder:7b (strong for code)")
        default_model = "llama3.2"
    elif ram_gb >= 4:
        print("       • llama3.2:3b (fits in ~2GB)")
        print("       • gemma3:2b (fast)")
        default_model = "llama3.2"
    else:
        print("       • phi4-mini:3b (2.1GB)")
        print("       • tinyllama:1b (600MB)")
        default_model = "phi4-mini"

    model_input = input(f"\n  Model name (default: {default_model}): ").strip()
    model = model_input or default_model
    print(f"  → Using model: {model}")

    return {
        "provider": "lmstudio",
        "model": model,
        "auto_download": False,  # LM Studio handles downloads manually
        "lmstudio_host": "http://127.0.0.1:1234"
    }


def _run_vllm_wizard(ram_gb: int):
    """Interactive vLLM provider setup (advanced)."""
    print("\n" + "=" * 55)
    print("  vLLM Provider Setup (Advanced)")
    print("=" * 55)
    print()
    print("  vLLM is a high-throughput LLM serving engine.")
    print("  Requires a model in supported format and typically a GPU.")
    print("  See: https://docs.vllm.ai")
    print()

    model = input("  Model (HuggingFace ID, e.g. meta-llama/Llama-3.2-3B-Instruct): ").strip()
    if not model:
        print("  [WARN] No model specified — falling back to hardcoded provider")
        return {"provider": "hardcoded"}

    host = input("  Server host (default: http://127.0.0.1:8000): ").strip()
    if not host:
        host = "http://127.0.0.1:8000"

    print(f"  → Provider: vLLM")
    print(f"  → Model: {model}")
    print(f"  → Host: {host}")
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
    """Interactive setup wizard. Uses TUI (rich) if available, falls back to basic."""
    base = Path(root_path or Path(__file__).parent.parent)

    try:
        from setup.tui_setup import run_tui_wizard
        run_tui_wizard()
        return {}
    except ImportError:
        # Fallback to basic LLM-only wizard
        return _basic_llm_wizard(base)


def _basic_llm_wizard(base: Path) -> dict:
    """Basic LLM-only wizard for when rich is not available."""
    print("\n" + "=" * 60)
    print("  Custo LLM Provider Setup (basic)")
    print("=" * 60)
    print("  Install rich for the full TUI: pip install rich prompt-toolkit")
    print()

    ram_gb = _detect_ram()
    print(f"  System RAM detected: ~{_ram_str(ram_gb)}")

    provider = _provider_menu()
    llm_config = {"provider": "hardcoded", "model": "", "auto_download": False}

    if provider == "ollama":
        llm_config = _run_ollama_wizard(ram_gb)
    elif provider == "lmstudio":
        llm_config = _run_lmstudio_wizard(ram_gb)
    elif provider == "vllm":
        llm_config = _run_vllm_wizard(ram_gb)
    else:
        print("\n  Skipping LLM setup — using hardcoded responses.")

    from system.config import load_config, save_config
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
    """Initialize configuration file. Use --wizard flag for interactive LLM setup."""
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"

    if config_path.exists():
        if os.environ.get("CUSTO_NONINTERACTIVE") == "1":
            print(f"[CONFIG] Config exists at {config_path} (keeping existing)")
        else:
            print(f"[CONFIG] Config already exists at {config_path}")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("[CONFIG] Aborted.")
                return

    if wizard:
        from setup.tui_setup import run_tui_wizard
        run_tui_wizard()
        return

    import yaml
    config_path.write_text(yaml.dump(DEFAULT_CONFIG, default_flow_style=False, sort_keys=False))
    print(f"[CONFIG] Configuration written to {config_path}")


if __name__ == "__main__":
    import sys
    if "--wizard" in sys.argv:
        run_wizard()
    else:
        init_config()
