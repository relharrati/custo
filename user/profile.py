"""User profile management."""

from pathlib import Path
from typing import Dict, Optional


def load_profile(root_path: Path = None) -> Dict[str, str]:
    """Load user profile."""
    base = Path(root_path or Path(__file__).parent.parent)
    profile_path = base / "user" / "profile.md"
    
    if profile_path.exists():
        content = profile_path.read_text()
        # Parse simple key: value format
        profile = {}
        for line in content.split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                profile[key.strip()] = value.strip()
        return profile
    
    return {"name": "User", "status": "new"}


def save_profile(profile: Dict[str, str], root_path: Path = None):
    """Save user profile."""
    base = Path(root_path or Path(__file__).parent.parent)
    profile_path = base / "user" / "profile.md"
    
    lines = []
    for key, value in profile.items():
        lines.append(f"{key}: {value}")
    
    profile_path.write_text('\n'.join(lines))
