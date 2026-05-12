"""Memory layer - short-term, long-term, and reflections."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json


class MemoryManager:
    """
    Unified memory manager for Custo.
    
    Manages:
    - Inbox: incoming unprocessed items
    - Short-term: active working memory (with TTL)
    - Daily memory: end-of-day summaries
    - Long-term: permanent semantic/episodic storage
    - Reflections: agent-generated insights
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.inbox_dir = root_path / "memory" / "inbox"
        self.short_term_dir = root_path / "memory" / "short_term"
        self.daily_dir = root_path / "memory" / "daily_memory"
        self.long_term_dir = root_path / "memory" / "long_term"
        self.reflections_dir = root_path / "memory" / "reflections"
        
        # Ensure all dirs exist
        for d in [self.inbox_dir, self.short_term_dir, 
                  self.daily_dir, self.long_term_dir, self.reflections_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    # Inbox operations
    def inbox_add(self, item: Dict) -> str:
        """Add an item to inbox."""
        item_id = f"inbox_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        item_file = self.inbox_dir / f"{item_id}.json"
        
        payload = {
            "id": item_id,
            "created": datetime.now().isoformat(),
            "processed": False,
            "data": item
        }
        
        item_file.write_text(json.dumps(payload, indent=2))
        return item_id
    
    def inbox_get_pending(self, limit: int = 10) -> List[Dict]:
        """Get pending inbox items."""
        items = []
        for f in sorted(self.inbox_dir.glob("*.json")):
            data = json.loads(f.read_text())
            if not data.get("processed"):
                items.append(data)
            if len(items) >= limit:
                break
        return items
    
    def inbox_mark_processed(self, item_id: str):
        """Mark an inbox item as processed."""
        for f in self.inbox_dir.glob(f"{item_id}.json"):
            data = json.loads(f.read_text())
            data["processed"] = True
            data["processed_at"] = datetime.now().isoformat()
            f.write_text(json.dumps(data, indent=2))
    
    # Short-term memory
    def short_term_set(self, key: str, value: any, ttl: int = None):
        """Set a short-term memory entry."""
        entry = {
            "key": key,
            "value": value,
            "created": datetime.now().isoformat(),
            "ttl": ttl or 86400  # 24h default
        }
        
        filepath = self.short_term_dir / f"{key}.json"
        filepath.write_text(json.dumps(entry, indent=2))
    
    def short_term_get(self, key: str) -> Optional[any]:
        """Get a short-term memory entry (None if expired/missing)."""
        filepath = self.short_term_dir / f"{key}.json"
        if not filepath.exists():
            return None
        
        entry = json.loads(filepath.read_text())
        created = datetime.fromisoformat(entry["created"])
        ttl = entry.get("ttl", 86400)
        
        if datetime.now() - created > timedelta(seconds=ttl):
            filepath.unlink()
            return None
        
        return entry["value"]
    
    def short_term_clear_expired(self):
        """Clear all expired short-term entries."""
        for f in self.short_term_dir.glob("*.json"):
            entry = json.loads(f.read_text())
            created = datetime.fromisoformat(entry["created"])
            ttl = entry.get("ttl", 86400)
            if datetime.now() - created > timedelta(seconds=ttl):
                f.unlink()
    
    # Daily memory
    def daily_create(self, summary: str, tags: List[str] = None) -> str:
        """Create a daily memory entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_dir = self.daily_dir / today
        daily_dir.mkdir(parents=True, exist_ok=True)
        
        entry_id = f"daily_{datetime.now().strftime('%H%M%S')}"
        entry = {
            "id": entry_id,
            "date": today,
            "summary": summary,
            "tags": tags or [],
            "created": datetime.now().isoformat()
        }
        
        filepath = daily_dir / f"{entry_id}.json"
        filepath.write_text(json.dumps(entry, indent=2))
        return entry_id
    
    def daily_get(self, date: str = None) -> List[Dict]:
        """Get daily memory entries for a date."""
        target = date or datetime.now().strftime("%Y-%m-%d")
        daily_dir = self.daily_dir / target
        
        if not daily_dir.exists():
            return []
        
        entries = []
        for f in sorted(daily_dir.glob("*.json")):
            entries.append(json.loads(f.read_text()))
        return entries
    
    # Long-term memory (append-only)
    def long_term_append(self, section: str, content: str, source: str = None):
        """Append to long-term memory markdown."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Read or initialize long-term file
        lt_path = self.long_term_dir / "semantic.md"
        if lt_path.exists():
            existing = lt_path.read_text()
        else:
            existing = "# Long-Term Semantic Memory\n\n"
        
        # Append new entry
        new_block = f"\n## {section} - {today}\n\n"
        if source:
            new_block += f"_Source: {source}_\n\n"
        new_block += f"{content}\n"
        
        lt_path.write_text(existing + new_block)
    
    def long_term_search(self, keyword: str) -> List[str]:
        """Search long-term memory for keyword."""
        results = []
        for md_file in self.long_term_dir.glob("*.md"):
            content = md_file.read_text()
            if keyword.lower() in content.lower():
                # Return matching section headers
                for line in content.split('\n'):
                    if line.startswith('## ') and keyword.lower() in line.lower():
                        results.append(line)
        return results
    
    # Reflections
    def reflection_write(self, content: str, tags: List[str] = None) -> str:
        """Write a reflection entry."""
        refl_id = f"refl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        entry = {
            "id": refl_id,
            "content": content,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "agent": "unknown"  # would be filled in by calling agent
        }
        
        filepath = self.reflections_dir / f"{refl_id}.json"
        filepath.write_text(json.dumps(entry, indent=2))
        return refl_id


# Singleton instance for the running system
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(root_path: Path = None) -> MemoryManager:
    """Get or create the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(root_path or Path.cwd())
    return _memory_manager
