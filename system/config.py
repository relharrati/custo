"""Configuration loader - reads YAML config with fallback."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(root_path: Path = None) -> Dict[str, Any]:
    """
    Load system configuration.
    
    Falls back to sensible defaults if config.yaml doesn't exist
    or if required keys are missing.
    """
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"
    
    defaults = {
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
            "provider": "auto",  # "auto", "ollama", "lmstudio", "vllm", "hardcoded", "none"
            "model": "",  # e.g. "qwen2.5-coder:1.5b", "gemma3:1b", "llama3.2:3b"
            "auto_download": True,  # If True and model not present, download it automatically
            "context_window": 4096,
            "temperature": 0.7,
            "max_tokens": 512,
            "ollama_host": "http://127.0.0.1:11434",
            "lmstudio_host": "http://127.0.0.1:1234",
            "vllm_host": "http://127.0.0.1:8000"
        }
    }
    
    if config_path.exists():
        try:
            user_config = yaml.safe_load(config_path.read_text())
            # Deep merge user config over defaults
            return _deep_merge(defaults, user_config or {})
        except Exception as e:
            print(f"[CONFIG] Warning: Could not parse config.yaml: {e}")
            print("[CONFIG] Using defaults")
    
    return defaults


def _deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge update dict into base dict."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def save_config(config: Dict[str, Any], root_path: Path = None):
    """Save configuration to YAML file."""
    base = Path(root_path or Path(__file__).parent.parent)
    config_path = base / "system" / "config.yaml"
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
