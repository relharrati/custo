"""LLM Provider Base - abstract interface for text generation backends."""

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion for a prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is ready to use."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier being used."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass


def get_provider(llm_config: dict = None, root_path=None):
    """Return the configured LLM provider instance."""
    from system.config import load_config
    cfg = llm_config or load_config(root_path).get("llm", {})
    provider_name = cfg.get("provider", "auto").lower()

    # Handle none/null → hardcoded
    if provider_name in ("none", "null", ""):
        from .hardcoded import HardcodedProvider
        return HardcodedProvider()

    # Auto-detect
    if provider_name == "auto":
        provider_name = _detect_provider() or "hardcoded"

    # Route to provider class
    if provider_name in ("ollama",):
        from .ollama import OllamaProvider
        return OllamaProvider(cfg)
    elif provider_name in ("lmstudio", "localai", "openai_compat"):
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(cfg)
    elif provider_name in ("vllm",):
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(dict(cfg, provider="vllm"))
    elif provider_name in ("hardcoded", "bootstrap"):
        from .hardcoded import HardcodedProvider
        return HardcodedProvider()
    else:
        # Unknown provider → fall back to hardcoded
        from .hardcoded import HardcodedProvider
        return HardcodedProvider()


def _detect_provider() -> Optional[str]:
    """Detect available LLM server by common ports/CLI tools."""
    import subprocess
    import socket

    # Check Ollama CLI
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            return "ollama"
    except FileNotFoundError:
        pass

    # Check common local LLM ports
    for host, port in [("127.0.0.1", 11434), ("127.0.0.1", 1234), ("127.0.0.1", 8000)]:
        try:
            s = socket.create_connection((host, port), timeout=0.5)
            s.close()
            if port == 11434:
                return "ollama"
            elif port == 1234:
                return "lmstudio"
            elif port == 8000:
                return "vllm"
        except OSError:
            continue

    return None


__all__ = ["LLMProvider", "get_provider"]
