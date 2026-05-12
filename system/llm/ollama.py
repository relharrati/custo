"""Ollama provider with auto-download and device-aware model recommendations."""

import json
import subprocess
import socket
import urllib.request
import urllib.error
from typing import Optional


class OllamaProvider:
    """
    Ollama-based provider.
    - Auto-detects running Ollama daemon
    - Suggests models based on available RAM
    - Can auto-download missing models (1B / 3B / 7B / 14B fallbacks)
    """

    # Tiered model recommendations by available RAM
    SMALL_MODELS = [
        ("qwen2.5-coder:1.5b", "Qwen Coder 1.5B", "~1.1 GB", "Excellent for code"),
        ("gemma3:1b", "Gemma 3 1B", "~790 MB", "Fast and light"),
        ("llama3.2:1b", "Llama 3.2 1B", "~670 MB", "Good general"),
    ]
    MEDIUM_MODELS = [
        ("qwen2.5-coder:7b", "Qwen Coder 7B", "~4.5 GB", "Strong coding"),
        ("gemma3:4b", "Gemma 3 4B", "~2.6 GB", "Balanced"),
        ("llama3.2:3b", "Llama 3.2 3B", "~2.0 GB", "Quick & capable"),
    ]
    LARGE_MODELS = [
        ("qwen2.5:14b", "Qwen 14B", "~8.8 GB", "Powerful"),
        ("llama3.1:8b", "Llama 3.1 8B", "~4.9 GB", "Strong general"),
    ]
    MINIMAL_MODELS = [
        ("phi4-mini:3b", "Phi-4 Mini 3B", "~2.1 GB", "Tiny but capable"),
    ]

    def __init__(self, llm_config: dict = None):
        self._model = "qwen2.5-coder:1.5b"
        self.host = "http://127.0.0.1:11434"
        self._available = None  # cache availability check
        self.list_url = "http://127.0.0.1:11434/api/tags"
        self.pull_url = "http://127.0.0.1:11434/api/pull"

        if llm_config:
            self._model = llm_config.get("model", self._model).strip()
            host = llm_config.get("ollama_host", self.host)
            self.host = host.rstrip("/")
            self.list_url = f"{self.host}/api/tags"
            self.pull_url = f"{self.host}/api/pull"

    async def generate(self, prompt: str, **kwargs) -> str:
        """Call Ollama generate API (non-streamed)."""
        import asyncio
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 512)
            }
        }
        data = json.dumps(payload).encode()
        url = f"{self.host}/api/generate"
        loop = asyncio.get_event_loop()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=60))
            result = json.loads(resp.read())
            return result.get("response", "").strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.read() else ""
            return f"[Ollama HTTP {e.code}] {body[:200]}"
        except Exception as e:
            return f"[Ollama connection error] {e}"

    def is_available(self) -> bool:
        """Check Ollama daemon is running and model is loaded (or downloadable)."""
        if self._available is not None:
            return self._available
        try:
            req = urllib.request.Request(self.list_url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                self._available = self._model in models
        except Exception:
            self._available = False
        return self._available

    def list_local_models(self) -> list:
        """Return list of locally cached Ollama models."""
        try:
            req = urllib.request.Request(self.list_url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                return data.get("models", [])
        except Exception:
            return []

    def pull_model(self, model: str, progress_cb=None) -> bool:
        """Download model via `ollama pull`."""
        try:
            proc = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            for line in proc.stdout:
                line = line.strip()
                if progress_cb:
                    try:
                        progress_cb(line)
                    except Exception:
                        pass
            proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @staticmethod
    def detect_ram_gb() -> int:
        """Detect total system RAM in GB (best-effort)."""
        try:
            import os
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
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
                    result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return max(1, int(int(result.stdout.strip()) / (1024**3)))
        except Exception:
            pass
        return 0

    @staticmethod
    def recommend_models(ram_gb: int) -> dict:
        """Return tiered model recommendations based on RAM, using models.dev."""
        try:
            from system.llm.models_db import get_recommended_models
            return get_recommended_models(ram_gb)
        except Exception:
            # Fallback: static tiers
            tiers = {
                "minimal": OllamaProvider.MINIMAL_MODELS,
                "small": OllamaProvider.SMALL_MODELS,
                "medium": OllamaProvider.MEDIUM_MODELS,
                "large": OllamaProvider.LARGE_MODELS,
            }
            # Filter based on RAM
            result = {}
            if ram_gb >= 24:
                result["large"] = tiers["large"]
            if ram_gb >= 8:
                result["medium"] = tiers["medium"]
            if ram_gb >= 2:
                result["small"] = tiers["small"]
            result["minimal"] = tiers["minimal"]
            return result

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "Ollama"
