"""Long-term memory reading/writing."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def read_long_memory(root_path: Path = None) -> str:
    """Read the full long-term memory markdown."""
    base = Path(root_path or Path(__file__).parent.parent)
    memory_path = base / "user" / "long_memory.md"
    
    if memory_path.exists():
        return memory_path.read_text()
    
    return "# Long-term Memory\n\nNo memory recorded yet."


def append_memory(entry: str, root_path: Path = None):
    """Append an entry to long-term memory."""
    base = Path(root_path or Path(__file__).parent.parent)
    memory_path = base / "user" / "long_memory.md"
    
    existing = memory_path.read_text() if memory_path.exists() else "# Long-term Memory\n\n"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = f"\n## {timestamp}\n\n{entry}\n"
    
    memory_path.write_text(existing + new_entry)


def query_memory(keyword: str, root_path: Path = None) -> list:
    """Search long-term memory for keyword."""
    content = read_long_memory(root_path)
    # Simple keyword search - return matching sections
    results = []
    for section in content.split('\n## '):
        if keyword.lower() in section.lower():
            results.append(section)
    return results
