"""OpenAI-compatible API provider (LM Studio, vLLM, LocalAI, etc.)."""

import json
import urllib.request
import urllib.error
import asyncio
from typing import Optional


class OpenAICompatProvider:
    """
    Compatible with any OpenAI-style API server.

    LM Studio:  http://127.0.0.1:1234/v1
    vLLM:       http://127.0.0.1:8000/v1
    LocalAI:    http://127.0.0.1:8080/v1
    """
    def __init__(self, llm_config: dict = None):
        self._model = "local-model"
        self.host = "http://127.0.0.1:1234"
        self.provider_type = "lmstudio"

        if llm_config:
            provider = llm_config.get("provider", "lmstudio")
            self.provider_type = provider
            host_key = f"{provider}_host"
            self.host = llm_config.get(host_key, self.host).rstrip("/")
            self._model = llm_config.get("model", self._model)

    async def generate(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512)
        }
        data = json.dumps(payload).encode()
        url = f"{self.host}/v1/completions"

        loop = asyncio.get_event_loop()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=60))
            result = json.loads(resp.read())
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("text", "").strip()
            return ""
        except urllib.error.HTTPError as e:
            body = e.read().decode() if hasattr(e, 'read') else ""
            return f"[API HTTP {e.code}] {body[:200]}"
        except Exception as e:
            return f"[API connection error] {e} (server at {self.host})"

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return {"lmstudio": "LM Studio", "vllm": "vLLM"}.get(self.provider_type, "OpenAI-compatible")
