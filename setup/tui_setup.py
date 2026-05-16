#!/usr/bin/env python3
"""
Custo Setup Wizard — Interactive TUI with Arrow Keys
─────────────────────────────────────────────────────
Arrow keys navigate  •  Space selects  •  Enter confirms
Never type a number or y/n again.

Flow:
  1. Verify installation
  2. Detect system RAM & VRAM
  3. Recommend models from models.dev
  4. Pick provider (Ollama / LM Studio / vLLM / models.dev providers / Skip)
  5. Auto-download local models (skip for API/OAuth providers)

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
import urllib.request
import urllib.error
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
LM_STUDIO_PORT = 1234
VLLM_PORT = 8000
CUSTO_PORT_DEFAULT = 18789
MODELS_DEV_URL = "https://models.dev/api.json"

# Hardcoded API/OAuth providers that never need local model download
API_ONLY_PROVIDERS = {
    "openai", "anthropic", "google", "gemini", "groq", "together",
    "deepinfra", "fireworks", "perplexity", "cohere", "mistral",
    "cerebras", "novita", "openrouter", "replicate",
}

# Known local-run providers that support auto-download
LOCAL_PROVIDERS = {
    "ollama": {"name": "Ollama", "desc": "Local runner — auto-download models", "icon": "💻"},
    "lm-studio": {"name": "LM Studio", "desc": "Desktop GUI — load GGUF models", "icon": "🎛️"},
    "vllm": {"name": "vLLM", "desc": "High-throughput server (GPU/CPU)", "icon": "⚡"},
    "llama-cpp": {"name": "llama.cpp", "desc": "Lightweight CPU inference", "icon": "🦙"},
    "mlc-llm": {"name": "MLC LLM", "desc": "Universal deployment engine", "icon": "🔧"},
}

STATE = {
    "provider": None,
    "model": None,
    "model_display": None,
    "model_size": None,
    "port": CUSTO_PORT_DEFAULT,
    "channels": ["stdio", "sse"],
    "skills": ["file-system", "web-search", "code-execution", "shell-exec"],
    "api_key": None,
    "ram_gb": None,
    "vram_gb": None,
    "auto_download": True,
    "installation_verified": False,
    "models_dev_data": None,
}

# ── InquirerPy style (Emerald/Blue) ────────────────────────

def custom_style():
    """Return an InquirerPy style object."""
    from InquirerPy import get_style
    return get_style({
        "questionmark": "hidden",
        "question": "#2dd4bf bold",
        "pointer": "#818cf8",
        "highlighted": "#818cf8 bold",
        "selected": "#34d399",
        "answer": "#a78bfa bold",
        "instruction": "#64748b",
        "separator": "#475569",
        "checkbox": "#818cf8",
        "checkbox-checked": "#34d399",
    })

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

# ── System Detection ────────────────────────────────────────

def _detect_ram():
    """Detect total RAM in GB (best-effort)."""
    try:
        if sys.platform == "darwin":
            out, _, _ = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
            )
            return max(1, int(int(out.strip()) / (1024**3)))
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

def _detect_vram():
    """Detect GPU VRAM in GB (best-effort)."""
    try:
        if sys.platform.startswith("linux"):
            # Try nvidia-smi
            out, _, code = run_cmd(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], timeout=10)
            if code == 0 and out.strip():
                # Sum all GPUs
                total_mb = sum(int(x.strip()) for x in out.strip().split("\n") if x.strip())
                return max(0, round(total_mb / 1024))
            # Try rocm-smi (AMD)
            out, _, code = run_cmd(["rocm-smi", "--showmeminfo", "vram"], timeout=10)
            if code == 0 and out.strip():
                # Parse VRAM from rocm-smi output
                for line in out.split("\n"):
                    if "VRAM" in line and "MiB" in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if "MiB" in p and i > 0:
                                try:
                                    return max(0, round(int(parts[i-1]) / 1024))
                                except ValueError:
                                    pass
        elif os.name == "nt":
            # Try nvidia-smi on Windows
            out, _, code = run_cmd(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], timeout=10)
            if code == 0 and out.strip():
                total_mb = sum(int(x.strip()) for x in out.strip().split("\n") if x.strip())
                return max(0, round(total_mb / 1024))
            # Try wmic for integrated GPU (rough estimate)
            out, _, code = run_cmd(["wmic", "path", "win32_videocontroller", "get", "AdapterRAM"], timeout=10)
            if code == 0 and out.strip():
                for line in out.split("\n")[1:]:
                    line = line.strip()
                    if line.isdigit():
                        return max(0, round(int(line) / (1024**3)))
        elif sys.platform == "darwin":
            # Apple Silicon unified memory = RAM (already detected)
            ram = STATE.get("ram_gb", _detect_ram())
            # Apple Silicon typically dedicates ~50-75% to GPU
            return max(0, round(ram * 0.6))
    except Exception:
        pass
    return 0  # no dedicated GPU detected

def _verify_installation():
    """Verify the Custo installation is intact."""
    base = Path(__file__).resolve().parent.parent
    required = [
        "system/config.py",
        "agents/registry.py",
        "daemon/daemon.py",
        "sessions/manager.py",
        "memory/manager.py",
        "interfaces/terminal/cli.py",
        "setup/tui_setup.py",
    ]
    missing = []
    for path in required:
        if not (base / path).exists():
            missing.append(path)
    return len(missing) == 0, missing

# ── models.dev Integration ──────────────────────────────────

def _fetch_models_dev(timeout=10):
    """Fetch model data from models.dev API with caching."""
    cache_dir = Path.home() / ".cache" / "custo"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "models.json"

    # Check cache (6 hour TTL)
    if cache_file.exists():
        try:
            import time
            age = time.time() - cache_file.stat().st_mtime
            if age < (6 * 3600):
                return json.loads(cache_file.read_text())
        except Exception:
            pass

    try:
        req = urllib.request.Request(
            MODELS_DEV_URL,
            headers={"User-Agent": "Custo/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            cache_file.write_text(json.dumps(data, indent=2))
            return data
    except Exception as e:
        print(f"\n  \033[90m[models.dev] API fetch failed: {e}\033[0m")
        print("  \033[90mUsing local fallback model list.\033[0m")
        return None

def _build_provider_list(models_data):
    """Build provider list from models.dev data + known local providers."""
    providers = []

    # Add known local providers first
    for pid, pinfo in LOCAL_PROVIDERS.items():
        providers.append({
            "id": pid,
            "name": pinfo["name"],
            "desc": pinfo["desc"],
            "icon": pinfo["icon"],
            "type": "local",
        })

    # Add API providers from models.dev
    if models_data:
        # Handle both dict and list formats
        all_models = {}
        if isinstance(models_data, dict):
            all_models = models_data.get("models", models_data.get("data", {}))
            # If it's a list, convert to dict
            if isinstance(all_models, list):
                all_models = {m.get("id", m.get("name", str(i))): m for i, m in enumerate(all_models)}
        elif isinstance(models_data, list):
            all_models = {m.get("id", m.get("name", str(i))): m for i, m in enumerate(models_data)}

        seen_api = set()
        for mid, mdef in all_models.items():
            if not isinstance(mdef, dict):
                continue
            # Skip local-run models (already handled by local providers)
            if mdef.get("local_run", False):
                continue
            if mdef.get("local") is False:
                continue

            # Extract provider from model metadata
            vendor = mdef.get("vendor", "").lower()
            family = mdef.get("family", "").lower()

            # Map to known API provider IDs
            api_id = None
            if any(p in vendor for p in ("openai",)):
                api_id = "openai"
            elif any(p in vendor for p in ("anthropic",)):
                api_id = "anthropic"
            elif any(p in vendor for p in ("google",)):
                api_id = "google"
            elif any(p in vendor for p in ("mistral",)):
                api_id = "mistral"
            elif any(p in vendor for p in ("cohere",)):
                api_id = "cohere"
            elif any(p in vendor for p in ("groq",)):
                api_id = "groq"
            elif any(p in vendor for p in ("deepinfra",)):
                api_id = "deepinfra"
            elif any(p in vendor for p in ("together",)):
                api_id = "together"
            elif any(p in vendor for p in ("fireworks",)):
                api_id = "fireworks"
            elif any(p in vendor for p in ("perplexity",)):
                api_id = "perplexity"
            elif any(p in vendor for p in ("cerebras",)):
                api_id = "cerebras"
            elif any(p in vendor for p in ("novita",)):
                api_id = "novita"
            elif any(p in vendor for p in ("replicate",)):
                api_id = "replicate"
            elif any(p in vendor for p in ("openrouter",)):
                api_id = "openrouter"

            if api_id and api_id not in seen_api:
                seen_api.add(api_id)
                providers.append({
                    "id": api_id,
                    "name": api_id.title(),
                    "desc": f"API provider — {mdef.get('name', api_id)}",
                    "icon": "☁️",
                    "type": "api",
                })

    # Add "Skip" option
    providers.append({
        "id": "skip",
        "name": "Skip / Hardcoded",
        "desc": "No LLM — use hardcoded responses (bootstrap mode)",
        "icon": "⏭️",
        "type": "skip",
    })

    return providers

def _get_models_for_provider(provider_id, models_data, ram_gb, vram_gb):
    """Get model recommendations for a specific provider."""
    results = []

    if provider_id == "ollama":
        results = _get_ollama_models(models_data, ram_gb, vram_gb)
    elif provider_id == "lm-studio":
        results = _get_lm_studio_models(models_data, ram_gb, vram_gb)
    elif provider_id == "vllm":
        results = _get_vllm_models(models_data, ram_gb, vram_gb)
    elif provider_id == "llama-cpp":
        results = _get_llama_cpp_models(models_data, ram_gb, vram_gb)
    elif provider_id == "mlc-llm":
        results = _get_mlc_models(models_data, ram_gb, vram_gb)
    elif provider_id in API_ONLY_PROVIDERS:
        results = _get_api_models(provider_id, models_data)
    else:
        # Generic: try to find models for this provider
        if models_data:
            results = _get_generic_models(provider_id, models_data)

    return results

def _normalize_models_data(models_data):
    """Convert models.dev response to a consistent dict format."""
    if not models_data:
        return {}
    if isinstance(models_data, dict):
        all_models = models_data.get("models", models_data.get("data", {}))
        if isinstance(all_models, list):
            return {m.get("id", m.get("name", str(i))): m for i, m in enumerate(all_models)}
        return all_models if isinstance(all_models, dict) else {}
    if isinstance(models_data, list):
        return {m.get("id", m.get("name", str(i))): m for i, m in enumerate(models_data)}
    return {}

def _get_ollama_models(models_data, ram_gb, vram_gb):
    results = []
    SIZE_MAP = {
        "0.5b": "~500 MB", "1b": "~670 MB", "1.5b": "~1.1 GB", "2b": "~1.5 GB",
        "3b": "~2.0 GB", "4b": "~2.6 GB", "5b": "~3.3 GB", "7b": "~4.5 GB",
        "8b": "~5.0 GB", "14b": "~8.8 GB", "16b": "~10 GB", "20b": "~12 GB",
        "32b": "~20 GB", "70b": "~40 GB", "72b": "~45 GB",
    }

    def est_size(model_id):
        lid = model_id.lower()
        for size_str, display in SIZE_MAP.items():
            if size_str in lid:
                return display
        return "~?"

    def fits_ram(size_str):
        try:
            if "GB" in size_str:
                gb = float(size_str.replace("~","").replace("GB","").strip())
            elif "MB" in size_str:
                gb = float(size_str.replace("~","").replace("MB","").strip()) / 1024
            else:
                return True
            return gb <= ram_gb * 0.7  # Leave 30% for OS
        except ValueError:
            return True

    if models_data:
        all_models = _normalize_models_data(models_data)
        for mid, mdef in all_models.items():
            if not mdef.get("local_run", False):
                continue
            if mdef.get("local") is False:
                continue
            vendor = mdef.get("vendor", "").lower()
            family = mdef.get("family", "").lower()
            if not any(p in vendor for p in ("meta", "google", "microsoft", "qwen", "deepseek", "mistral", "gemma", "phi", "llama")):
                continue

            model_id = mid
            name = mdef.get("name", mid)
            size = est_size(mid)
            if not fits_ram(size):
                continue

            note = "Local model"
            if "qwen" in family or "qwen" in mid.lower():
                note = "Strong code & multilingual"
            elif "llama" in family:
                note = "Meta general purpose"
            elif "gemma" in family:
                note = "Google lightweight"
            elif "phi" in family:
                note = "Microsoft tiny"
            elif "mistral" in family:
                note = "French open-weight"
            elif "deepseek" in family:
                note = "Code focused"

            results.append((model_id, name, size, note))
    else:
        # Local fallback
        results = [
            ("qwen2.5-coder:0.5b", "Qwen Coder 0.5B", "~500 MB", "Tiny — fits 2GB+"),
            ("qwen2.5-coder:1.5b", "Qwen Coder 1.5B", "~1.1 GB", "Small — fits 4GB+"),
            ("qwen2.5-coder:3b", "Qwen Coder 3B", "~2.0 GB", "Medium — fits 8GB+"),
            ("qwen2.5-coder:7b", "Qwen Coder 7B", "~4.5 GB", "Large — fits 16GB+"),
            ("qwen2.5-coder:14b", "Qwen Coder 14B", "~8.8 GB", "Huge — fits 32GB+"),
            ("llama3.2:1b", "Llama 3.2 1B", "~670 MB", "Meta lightweight"),
            ("llama3.2:3b", "Llama 3.2 3B", "~2.0 GB", "Meta general"),
            ("gemma3:1b", "Gemma 3 1B", "~790 MB", "Google tiny"),
            ("gemma3:4b", "Gemma 3 4B", "~2.6 GB", "Google balanced"),
            ("phi4-mini:3b", "Phi-4 Mini 3B", "~2.1 GB", "Microsoft capable"),
        ]

    # Sort by size
    def sort_key(item):
        size = item[2]
        try:
            if "GB" in size:
                return float(size.replace("~","").replace("GB","").strip())
            elif "MB" in size:
                return float(size.replace("~","").replace("MB","").strip()) / 1024
        except ValueError:
            pass
        return 999
    results.sort(key=sort_key)
    return results

def _get_lm_studio_models(models_data, ram_gb, vram_gb):
    """Get LM Studio compatible models (GGUF format)."""
    results = []
    if models_data:
        all_models = _normalize_models_data(models_data)
        for mid, mdef in all_models.items():
            if not mdef.get("local_run", False):
                continue
            vendor = mdef.get("vendor", "").lower()
            family = mdef.get("family", "").lower()
            if any(p in vendor for p in ("meta", "google", "microsoft", "qwen", "deepseek", "mistral", "gemma", "phi", "llama")):
                results.append((mid, mdef.get("name", mid), "~?", f"{family.title()} — GGUF compatible"))
    else:
        results = [
            ("local", "Auto-detect loaded model", "~?", "LM Studio will auto-detect"),
        ]
    return results

def _get_vllm_models(models_data, ram_gb, vram_gb):
    """Get vLLM compatible models (HuggingFace format)."""
    results = []
    if models_data:
        all_models = _normalize_models_data(models_data)
        for mid, mdef in all_models.items():
            if not mdef.get("local_run", False):
                continue
            vendor = mdef.get("vendor", "").lower()
            family = mdef.get("family", "").lower()
            if any(p in vendor for p in ("meta", "google", "microsoft", "qwen", "deepseek", "mistral", "gemma", "phi", "llama")):
                results.append((mid, mdef.get("name", mid), "~?", f"{family.title()} — HF compatible"))
    else:
        results = [
            ("meta-llama/Llama-3.2-3B-Instruct", "Llama 3.2 3B", "~?", "Meta — HF format"),
            ("Qwen/Qwen2.5-Coder-7B-Instruct", "Qwen 2.5 Coder 7B", "~?", "Qwen — HF format"),
            ("google/gemma-2-9b", "Gemma 2 9B", "~?", "Google — HF format"),
        ]
    return results

def _get_llama_cpp_models(models_data, ram_gb, vram_gb):
    results = [
        ("local", "Auto-detect GGUF model", "~?", "llama.cpp will auto-detect"),
    ]
    return results

def _get_mlc_models(models_data, ram_gb, vram_gb):
    results = [
        ("local", "Auto-detect MLC model", "~?", "MLC LLM will auto-detect"),
    ]
    return results

def _get_api_models(provider_id, models_data):
    """Get models for an API provider."""
    results = []
    if models_data:
        all_models = _normalize_models_data(models_data)
        for mid, mdef in all_models.items():
            vendor = mdef.get("vendor", "").lower()
            family = mdef.get("family", "").lower()
            # Match provider
            provider_match = False
            if provider_id == "openai" and "openai" in vendor:
                provider_match = True
            elif provider_id == "anthropic" and "anthropic" in vendor:
                provider_match = True
            elif provider_id == "google" and "google" in vendor:
                provider_match = True
            elif provider_id == "mistral" and "mistral" in vendor:
                provider_match = True
            elif provider_id == "cohere" and "cohere" in vendor:
                provider_match = True
            elif provider_id == "groq" and "groq" in vendor:
                provider_match = True
            elif provider_id == "deepinfra" and "deepinfra" in vendor:
                provider_match = True
            elif provider_id == "together" and "together" in vendor:
                provider_match = True
            elif provider_id == "fireworks" and "fireworks" in vendor:
                provider_match = True
            elif provider_id == "perplexity" and "perplexity" in vendor:
                provider_match = True
            elif provider_id == "cerebras" and "cerebras" in vendor:
                provider_match = True
            elif provider_id == "novita" and "novita" in vendor:
                provider_match = True
            elif provider_id == "replicate" and "replicate" in vendor:
                provider_match = True

            if provider_match:
                context = mdef.get("limit", {}).get("context", 0)
                results.append((mid, mdef.get("name", mid), "API", f"Context: {context}" if context else "API model"))

    # Fallback defaults
    if not results:
        defaults = {
            "openai": [("gpt-4o-mini", "GPT-4o Mini", "API", "Cheapest"), ("gpt-4o", "GPT-4o", "API", "Full"), ("gpt-3.5-turbo", "GPT-3.5 Turbo", "API", "Legacy")],
            "anthropic": [("claude-3-haiku-20240307", "Claude 3 Haiku", "API", "Fast"), ("claude-3-sonnet-20240229", "Claude 3 Sonnet", "API", "Balanced"), ("claude-3-opus-20240229", "Claude 3 Opus", "API", "Powerful")],
            "google": [("gemini-1.5-flash", "Gemini 1.5 Flash", "API", "Fast"), ("gemini-1.5-pro", "Gemini 1.5 Pro", "API", "Powerful")],
            "mistral": [("mistral-small", "Mistral Small", "API", "Fast"), ("mistral-large", "Mistral Large", "API", "Powerful")],
            "groq": [("llama-3.1-8b-instant", "Llama 3.1 8B", "API", "Fast"), ("llama-3.1-70b-versatile", "Llama 3.1 70B", "API", "Powerful")],
        }
        results = defaults.get(provider_id, [(f"{provider_id}-model", f"{provider_id.title()} Model", "API", "Default")])

    return results

def _get_generic_models(provider_id, models_data):
    """Generic model fetch for unknown providers."""
    results = []
    if models_data:
        all_models = _normalize_models_data(models_data)
        for mid, mdef in all_models.items():
            vendor = mdef.get("vendor", "").lower()
            if provider_id.lower() in vendor:
                results.append((mid, mdef.get("name", mid), "API", f"From {provider_id}"))
    if not results:
        results = [(f"{provider_id}-model", f"{provider_id.title()} Model", "API", "Default")]
    return results

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

# ── Prompt Helpers ──────────────────────────────────────────

def _checkbox_prompt(message, choices, default=None):
    if HAS_INQUIRER:
        style = custom_style()
        selected = inquirer.checkbox(
            message=message,
            choices=choices,
            default=default or [],
            style=style,
            instruction="  (↑↓ move, Space toggle, Enter confirm)",
        ).execute()
        # InquirerPy returns list of tuples — extract values
        result = []
        for item in selected:
            if isinstance(item, (list, tuple)):
                result.append(item[1] if len(item) >= 2 else item[0])
            else:
                result.append(item)
        return result
    else:
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
    """
    Interactive select. Always returns the VALUE (second element).
    Choices format: [(display_label, value), ...]
    """
    if HAS_INQUIRER:
        result = inquirer.select(
            message=message,
            choices=choices,
            default=default,
            style=custom_style(),
            instruction="  (↑↓ to move, Enter to select)",
        ).execute()
        # InquirerPy returns the full tuple — extract value
        if isinstance(result, (list, tuple)):
            return result[1] if len(result) >= 2 else result[0]
        return result
    else:
        print(f"\n  {message}")
        for i, (label, val) in enumerate(choices, 1):
            print(f"  {i}. {label}")
        while True:
            raw = input(f"  Select [1-{len(choices)}] (default: 1): ").strip()
            if not raw:
                chosen = default if default else choices[0][1]
                return chosen[1] if isinstance(chosen, (list, tuple)) else chosen
            try:
                n = int(raw)
                if 1 <= n <= len(choices):
                    return choices[n-1][1]
            except ValueError:
                pass
            print(f"  Invalid. Enter 1-{len(choices)}.")

def _input_prompt(message, default=None, validate=None):
    if HAS_INQUIRER:
        kwargs = {"message": message, "style": custom_style()}
        if default is not None:
            kwargs["default"] = default
        if validate:
            kwargs["validate"] = validate
        return inquirer.text(**kwargs).execute()
    else:
        prompt_text = f"  {message}"
        if default is not None:
            prompt_text += f" [{default}]"
        prompt_text += ": "
        while True:
            val = input(prompt_text).strip()
            if not val and default is not None:
                return default
            if validate:
                ok, err = validate(val)
                if not ok:
                    print(f"  {err}")
                    continue
            return val

# ── PHASES ─────────────────────────────────────────────────

def phase_1_verify_installation():
    """Phase 1: Verify installation integrity."""
    clear()
    print(LOGO)
    print("  \033[1;97mWelcome to the Custo Setup Wizard\033[0m")
    print("  \033[1;90mArrow keys → navigate  |  Space → toggle  |  Enter → confirm\033[0m")
    print()

    print("  \033[1;94m▸ Phase 1: Installation Verification\033[0m")
    print()

    ok, missing = _verify_installation()
    if ok:
        print("  \033[1;32m✓ All core files present\033[0m")
        STATE["installation_verified"] = True
    else:
        print(f"  \033[1;31m✗ Missing {len(missing)} file(s):\033[0m")
        for f in missing[:5]:
            print(f"    \033[90m- {f}\033[0m")
        if len(missing) > 5:
            print(f"    \033[90m... and {len(missing)-5} more\033[0m")
        STATE["installation_verified"] = False
        if not _confirm_prompt("Continue anyway?", default=True):
            print("  \033[1;33mSetup cancelled.\033[0m")
            sys.exit(0)

    print()
    print("  Press Enter to continue...")
    if HAS_INQUIRER:
        inquirer.confirm(message="", default=True, style=custom_style()).execute()
    else:
        input()

def phase_2_system_detection():
    """Phase 2: Detect RAM, VRAM, OS, Python."""
    clear()
    print(LOGO)
    print("  \033[1;34m▸ Phase 2: System Detection\033[0m")
    print()

    ram = _detect_ram()
    vram = _detect_vram()
    STATE["ram_gb"] = ram
    STATE["vram_gb"] = vram

    print("  \033[1;94mHardware Profile\033[0m")
    print(f"  OS:       \033[1m{platform.system()} {platform.release()}\033[0m")
    print(f"  Arch:     \033[1m{platform.machine()}\033[0m")
    print(f"  Python:   \033[1m{platform.python_version()}\033[0m")

    ram_color = "\033[1;32m" if ram >= 16 else "\033[1;33m" if ram >= 8 else "\033[1;31m"
    print(f"  RAM:      {ram_color}{ram} GB\033[0m")

    if vram > 0:
        vram_color = "\033[1;32m" if vram >= 8 else "\033[1;33m" if vram >= 4 else "\033[1;31m"
        print(f"  VRAM:     {vram_color}{vram} GB (GPU detected)\033[0m")
    else:
        print(f"  VRAM:     \033[90mNone detected (CPU inference)\033[0m")

    print()
    print("  \033[1;94mModel Recommendations\033[0m")

    # Show recommendations based on RAM/VRAM
    effective_mem = vram if vram > 0 else ram
    if effective_mem >= 32:
        print("  \033[1;32m✓ Your system can run large models (14B-70B)\033[0m")
    elif effective_mem >= 16:
        print("  \033[1;32m✓ Your system can run medium models (7B-14B)\033[0m")
    elif effective_mem >= 8:
        print("  \033[1;33m⚠ Your system can run small models (1.5B-7B)\033[0m")
    elif effective_mem >= 4:
        print("  \033[1;33m⚠ Your system can run tiny models (0.5B-3B)\033[0m")
    else:
        print("  \033[1;31m✗ Very limited — consider API providers\033[0m")

    print()
    print("  Press Enter to continue...")
    if HAS_INQUIRER:
        inquirer.confirm(message="", default=True, style=custom_style()).execute()
    else:
        input()

def phase_3_provider_model():
    """
    Phase 3: Pick provider → API key (if needed) → pick model → confirm.
    Flow:
      1. List all providers (from models.dev + known locals) → select one
      2. If API provider → enter API key
      3. Show models for that provider → select one
      4. Auto-download prompt (local only)
      5. Continue to next phase
    """
    clear()
    print(LOGO)
    print("  \033[1;34m▸ Phase 3: LLM Provider & Model\033[0m")
    print()

    # Fetch models.dev data
    spinner = Spinner("Fetching models from models.dev...")
    spinner.start()
    models_data = _fetch_models_dev(timeout=10)
    spinner.stop()
    STATE["models_dev_data"] = models_data

    if models_data:
        print("  \033[1;32m✓ models.dev API connected\033[0m")
    else:
        print("  \033[1;33m⚠ Using local model fallback\033[0m")
    print()

    # ── Step 1: Select Provider ─────────────────────────────
    providers = _build_provider_list(models_data)
    provider_choices = [
        (f"{p['icon']}  {p['name']} — {p['desc']}", p["id"])
        for p in providers
    ]

    provider_id = _select_prompt("Pick your LLM provider:", provider_choices, default="ollama")
    STATE["provider"] = provider_id
    print(f"\n  \033[1;32m✓ Provider: {provider_id}\033[0m")

    # ── Handle Skip ─────────────────────────────────────────
    if provider_id == "skip":
        STATE["model"] = ""
        STATE["model_display"] = "Hardcoded responses"
        STATE["model_size"] = "N/A"
        STATE["auto_download"] = False
        print("  \033[90mSkipping LLM — hardcoded responses will be used.\033[0m")
        if not HAS_INQUIRER:
            input("  Press Enter to continue...")
        return

    # ── Step 2: API Key (for API providers) ─────────────────
    if provider_id in API_ONLY_PROVIDERS:
        print()
        print(f"  \033[1;97mConfigure {str(provider_id).title()} API Key\033[0m")
        print(f"  \033[90mGet your key from https://{str(provider_id).lower()}.com/settings/api\033[0m")
        print()
        api_key = _input_prompt(
            f"Enter your {str(provider_id).title()} API key:",
            default="",
            validate=lambda _, x: (True, "") if x == "" or len(x) >= 8 else (False, "Key must be at least 8 characters")
        )
        if api_key and len(api_key) >= 8:
            STATE["api_key"] = api_key
            print(f"  \033[1;32m✓ {str(provider_id).title()} API key configured\033[0m")
        else:
            print(f"  \033[1;33m⚠ No API key set — you can add it later in system/config.yaml\033[0m")
        STATE["auto_download"] = False
    else:
        STATE["auto_download"] = True

    # ── Step 3: Select Model ────────────────────────────────
    print()
    ram = STATE["ram_gb"]
    vram = STATE["vram_gb"]
    models = _get_models_for_provider(provider_id, models_data, ram, vram)

    if not models:
        print(f"  \033[1;33m⚠ No models from API — using fallback list\033[0m")
        if provider_id == "ollama":
            models = [
                ("qwen2.5-coder:0.5b", "Qwen Coder 0.5B", "~500 MB", "Tiny"),
                ("qwen2.5-coder:1.5b", "Qwen Coder 1.5B", "~1.1 GB", "Small"),
                ("qwen2.5-coder:3b", "Qwen Coder 3B", "~2.0 GB", "Medium"),
                ("qwen2.5-coder:7b", "Qwen Coder 7B", "~4.5 GB", "Large"),
                ("llama3.2:1b", "Llama 3.2 1B", "~670 MB", "Meta"),
                ("llama3.2:3b", "Llama 3.2 3B", "~2.0 GB", "Meta"),
            ]
        elif provider_id == "lm-studio":
            models = [("local", "Auto-detect loaded model", "~?", "LM Studio")]
        elif provider_id == "vllm":
            models = [
                ("meta-llama/Llama-3.2-3B-Instruct", "Llama 3.2 3B", "~?", "HF"),
                ("Qwen/Qwen2.5-Coder-7B-Instruct", "Qwen 2.5 Coder 7B", "~?", "HF"),
            ]
        else:
            pid_str = provider_id[0] if isinstance(provider_id, (list, tuple)) else str(provider_id)
            models = [(f"{pid_str}-model", f"{pid_str.title()} Model", "API", "Default")]

    model_choices = [(f"{name} ({size}) — {note}", mid) for mid, name, size, note in models]

    # Show RAM/VRAM hint for local providers
    is_local = provider_id in LOCAL_PROVIDERS
    if is_local:
        effective = vram if vram > 0 else ram
        if effective < 4:
            print(f"  \033[1;33m⚠ Only {effective}GB memory — smaller models recommended\033[0m")
        elif effective < 8:
            print(f"  \033[1;90m{effective}GB memory — models up to ~3B will run well\033[0m")
        print()

    model_id = _select_prompt("Pick a model:", model_choices, default=models[0][0])
    STATE["model"] = model_id

    # Store display info
    for mid, name, size, note in models:
        if mid == model_id:
            STATE["model_display"] = name
            STATE["model_size"] = size
            break

    print(f"\n  \033[1;32m✓ Model: {STATE['model_display']} ({STATE['model_size']})\033[0m")

    # ── Step 4: Auto-download (local providers only) ────────
    if is_local:
        print()
        auto_dl = _confirm_prompt("Auto-download model during setup?", default=True)
        STATE["auto_download"] = auto_dl
        if auto_dl:
            print("  \033[90mModel will be downloaded in Phase 6.\033[0m")
        else:
            print("  \033[90mYou can download it later with the provider's CLI.\033[0m")

    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_4_gateway():
    """Phase 4: Gateway port configuration."""
    clear()
    print(LOGO)
    print("  \033[1;34m▸ Phase 4: Gateway\033[0m")
    print()

    custo_busy = check_port(CUSTO_PORT_DEFAULT)
    if custo_busy:
        print(f"  \033[1;33m⚠ Port {CUSTO_PORT_DEFAULT} is already in use.\033[0m")

    port_choices = [
        ("18789 (default)", 18789),
        ("8080", 8080),
        ("8000", 8000),
    ]
    port = _select_prompt("Gateway port:", port_choices, default=18789)
    STATE["port"] = port
    print(f"\n  \033[1;32m✓ Gateway will run on port {port}\033[0m")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_5_channels_skills():
    """Phase 5: Channels & Skills selection."""
    clear()
    print(LOGO)
    print("  \033[1;34m▸ Phase 5: Channels & Skills\033[0m")
    print()

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
    print(f"\n  \033[1;32m✓ Channels: {', '.join(STATE['channels'])}\033[0m")
    print()

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
    print(f"  \033[1;32m✓ Skills: {', '.join(STATE['skills'])}\033[0m")
    print()
    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_6_install_and_verify():
    """Phase 6: Install local models + verify."""
    clear()
    print(LOGO)
    print("  \033[1;34m▸ Phase 6: Install & Verify\033[0m")
    print()

    provider = STATE["provider"]
    model = STATE["model"]

    # Skip for API providers and skip
    if provider in API_ONLY_PROVIDERS or provider == "skip":
        if provider == "skip":
            print("  \033[90mNo LLM configured — hardcoded responses active.\033[0m")
        else:
            print(f"  \033[90mProvider: {provider} (API) — no local install needed.\033[0m")
            print("  \033[90mConfigure your API key in system/config.yaml if not set.\033[0m")
        print()
        if not HAS_INQUIRER:
            input("  Press Enter to continue...")
        return

    # ── Ollama ────────────────────────────────────────────
    if provider == "ollama":
        ollama_installed = bool(shutil.which("ollama"))
        if ollama_installed:
            ver_out, _, _ = run_cmd(["ollama", "--version"])
            ver = ver_out.strip().split()[0] if ver_out.strip() else "unknown"
            print(f"  \033[1;32m✓ Ollama found: {ver}\033[0m")
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
                    spinner.stop("\033[1;32m✓ Ollama installed")
                    print()
                    ollama_installed = True
                except Exception as e:
                    spinner.stop()
                    print(f"\n  \033[1;31m✗ Install failed: {e}\033[0m")
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

        # Start daemon
        if ollama_installed:
            if check_port(OLLAMA_PORT):
                print(f"  \033[1;32m✓ Ollama running on port {OLLAMA_PORT}\033[0m")
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
                    print(f"  \033[1;32m✓ Daemon ready on port {OLLAMA_PORT}\033[0m")
                else:
                    print(f"  \033[1;33m⚠ Daemon didn't respond. Start manually: ollama serve\033[0m")
                print()

        # Pull model
        if model and ollama_installed and STATE.get("auto_download", True):
            spinner = Spinner(f"Pulling model: {model}")
            spinner.start()
            try:
                out, err, code = run_cmd(["ollama", "pull", model], timeout=600)
            except Exception as e:
                spinner.stop()
                print(f"\n  \033[1;31m✗ Pull failed: {e}\033[0m")
            else:
                spinner.stop()
                if code == 0:
                    print(f"  \033[1;32m✓ Model '{model}' ready\033[0m")
                else:
                    err_snippet = err[:150] if err else "unknown error"
                    print(f"  \033[1;31m✗ Pull failed: {err_snippet}\033[0m")
            print()

        # Verify
        if model and ollama_installed:
            spinner = Spinner("Verifying setup...")
            spinner.start()
            out, _, code = run_cmd(["ollama", "list"], timeout=30)
            spinner.stop()
            if code == 0 and model in out:
                print(f"  \033[1;32m✓ Setup verified successfully\033[0m")
            else:
                print(f"  \033[1;33m⚠ Model may still be loading. Try 'ollama list'.\033[0m")
            print()

    # ── LM Studio ─────────────────────────────────────────
    elif provider == "lm-studio":
        if check_port(LM_STUDIO_PORT):
            print(f"  \033[1;32m✓ LM Studio running on port {LM_STUDIO_PORT}\033[0m")
        else:
            print(f"  \033[1;33m⚠ LM Studio not detected on port {LM_STUDIO_PORT}\033[0m")
            print("  \033[90mOpen LM Studio → select model → Server tab → Start Server\033[0m")
        print()

    # ── vLLM ──────────────────────────────────────────────
    elif provider == "vllm":
        if check_port(VLLM_PORT):
            print(f"  \033[1;32m✓ vLLM running on port {VLLM_PORT}\033[0m")
        else:
            print(f"  \033[1;33m⚠ vLLM not detected on port {VLLM_PORT}\033[0m")
            print(f"  \033[90mStart with: python -m vllm.entrypoints.openai.api_server --model {model}\033[0m")
        print()

    # ── Other local providers ─────────────────────────────
    elif provider in LOCAL_PROVIDERS:
        print(f"  \033[90mProvider: {LOCAL_PROVIDERS[provider]['name']}\033[0m")
        print("  \033[90mConfigure this provider manually in system/config.yaml\033[0m")
        print()

    if not HAS_INQUIRER:
        input("  Press Enter to continue...")

def phase_done():
    """Phase 7: Completion summary + config save."""
    clear()
    print(LOGO)
    print("  \033[1;32m╔══════════════════════════════════════════╗\033[0m")
    print("  \033[1;32m║        ✨ S E T U P   C O M P L E T E ✨    ║\033[0m")
    print("  \033[1;32m╚══════════════════════════════════════════╝\033[0m")
    print()
    print("  Summary:")
    print(f"    Provider : \033[1m{STATE['provider'] or 'none'}\033[0m")
    print(f"    Model    : \033[1m{STATE['model'] or 'none'}\033[0m")
    if STATE.get("model_display"):
        print(f"             \033[90m({STATE['model_display']}, {STATE.get('model_size', '?')})\033[0m")
    print(f"    Gateway  : \033[1mhttp://127.0.0.1:{STATE['port']}\033[0m")
    print(f"    Channels : \033[1m{', '.join(STATE['channels'])}\033[0m")
    print(f"    Skills   : \033[1m{', '.join(STATE['skills'])}\033[0m")
    print(f"    Auto-dl  : \033[1m{'Yes' if STATE.get('auto_download') else 'No'}\033[0m")
    print()

    # Save config
    try:
        cfg_path = save_config(STATE)
        print(f"  \033[1;32m✓ Config saved: {cfg_path}\033[0m")
    except Exception as e:
        print(f"  \033[1;31m✗ Failed to save config: {e}\033[0m")
    print()

    print("  \033[1;90mNext commands to try:\033[0m")
    print("    custo chat     — Start a conversation")
    print("    custo daemon   — Start background service")
    print("    custo doctor   — Health check")
    print("    custo help     — All commands")
    print()

    # Ask to launch chat
    chat = _confirm_prompt("Launch chat now?", default=True)
    if chat:
        print("\n  Starting Custo chat...\n")
        time.sleep(0.5)
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "custo"), "chat"],
            creationflags=(0 if os.name != "nt" else subprocess.CREATE_NEW_PROCESS_GROUP),
        )

# ── Config Save ─────────────────────────────────────────────

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
            "auto_download": state.get("auto_download", True),
            "context_window": 4096,
            "temperature": 0.7,
            "max_tokens": 512,
            "ollama_host": "http://127.0.0.1:11434",
            "lmstudio_host": "http://127.0.0.1:1234",
            "vllm_host": "http://127.0.0.1:8000",
        },
        "gateway": {"enabled": True, "port": state["port"], "cors": True},
        "skills": state.get("skills", []),
        "channels": state.get("channels", []),
    }
    base.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
    return config_path

# ── Main Entry Point ──────────────────────────────────────

def run_tui_wizard():
    """
    Entry point called by init_config.py, install.py, first_run.py.
    """
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
        phase_1_verify_installation()
        phase_2_system_detection()
        phase_3_provider_model()
        phase_4_gateway()
        phase_5_channels_skills()
        phase_6_install_and_verify()
        phase_done()
    except KeyboardInterrupt:
        print("\n\n  \033[1;33mSetup cancelled. Goodbye!\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n  \033[1;31mSetup failed: {e}\033[0m")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_tui_wizard()