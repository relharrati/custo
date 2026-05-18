"""User preferences management."""

from pathlib import Path
from typing import Dict, Any


def load_preferences(root_path: Path = None) -> Dict[str, Any]:
    """Load user preferences."""
    base = Path(root_path or Path(__file__).parent.parent)
    prefs_path = base / "user" / "preferences.md"
    
    defaults = {
        "response_style": "concise",
        "auto_reflect": True,
        "daily_summary": True,
        "notifications": True
    }
    
    if prefs_path.exists():
        # Parse preferences (simple key=value format)
        content = prefs_path.read_text()
        for line in content.split('\n'):
            if '=' in line:
                key, _, value = line.partition('=')
                defaults[key.strip()] = value.strip()
    
    return defaults


def update_preference(key: str, value: str, root_path: Path = None):
    """Update a single preference."""
    prefs = load_preferences(root_path)
    prefs[key] = value
    
    base = Path(root_path or Path(__file__).parent.parent)
    prefs_path = base / "user" / "preferences.md"
    
    lines = [f"{k}={v}" for k, v in prefs.items()]
    prefs_path.write_text('\n'.join(lines))
