"""User relationships tracking."""

from pathlib import Path
from typing import Dict, List


def load_relationships(root_path: Path = None) -> Dict[str, str]:
    """Load user relationships."""
    base = Path(root_path or Path(__file__).parent.parent)
    rel_path = base / "user" / "relationships.md"
    
    if rel_path.exists():
        # Parse relationships
        return {}
    return {}


def add_relationship(name: str, role: str, notes: str = "", root_path: Path = None):
    """Add a new relationship."""
    base = Path(root_path or Path(__file__).parent.parent)
    rel_path = base / "user" / "relationships.md"
    
    existing = rel_path.read_text() if rel_path.exists() else "# Relationships\n\n"
    new_entry = f"- **{name}** ({role}): {notes}\n"
    
    rel_path.write_text(existing + new_entry)
