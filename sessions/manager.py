"""Session management - create, index, and query conversation sessions."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SessionManager:
    """Manages Custo sessions."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.sessions_dir = root_path / "sessions" / "daily"
        self.index_path = root_path / "sessions" / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure index file exists and contains valid JSON."""
        if not self.index_path.exists() or self.index_path.stat().st_size == 0:
            self.index_path.write_text(json.dumps({
                "version": "1.0",
                "sessions": []
            }, indent=2))

    def _get_index(self) -> Dict:
        """Read index, falling back to fresh index if corrupt or empty."""
        try:
            if self.index_path.exists():
                content = self.index_path.read_text()
                if content.strip():
                    return json.loads(content)
        except json.JSONDecodeError:
            pass
        fresh = {"version": "1.0", "sessions": []}
        self.index_path.write_text(json.dumps(fresh, indent=2))
        return fresh
    
    def create_session(self, title: str = None, metadata: Dict = None) -> Dict:
        """
        Create a new session.
        
        Returns session dict with id, path, etc.
        """
        session_id = str(uuid.uuid4())[:8]
        today = datetime.now().strftime("%Y-%m-%d")
        
        session = {
            "id": session_id,
            "title": title or f"Session {datetime.now().strftime('%H:%M')}",
            "date": today,
            "created": datetime.now().isoformat(),
            "metadata": metadata or {},
            "messages": []
        }
        
        # Create daily directory
        daily_dir = self.sessions_dir / today
        daily_dir.mkdir(parents=True, exist_ok=True)
        
        # Write session file
        session_file = daily_dir / f"{session_id}.md"
        session_file.write_text(self._format_session_md(session))
        
        # Update index
        self._update_index({
            "id": session_id,
            "date": today,
            "path": str(session_file.relative_to(self.root)),
            "title": session["title"],
            "message_count": 0
        })
        
        return session
    
    def _format_session_md(self, session: Dict) -> str:
        """Format session as markdown."""
        lines = [
            "---",
            f"title: {session['title']}",
            f"date: {session['date']}",
            f"session_id: {session['id']}",
            "---",
            "",
            "# Session",
            "",
            "## Conversation",
            ""
        ]
        return '\n'.join(lines)
    
    def _update_index(self, session_entry: Dict):
        """Update the session index."""
        index = self._get_index()
        index["sessions"].append(session_entry)
        self.index_path.write_text(json.dumps(index, indent=2))
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to an existing session.

        Returns True if successful, False if session not found.
        """
        index = self._get_index()
        
        session_entry = None
        for s in index["sessions"]:
            if s["id"] == session_id:
                session_entry = s
                break
        
        if not session_entry:
            return False
        
        # Read session file
        session_file = self.root / session_entry["path"]
        session_content = session_file.read_text()
        
        # Append message at the END of the Conversation section
        prefix = "You" if role == "user" else "Custo"
        message_block = f"\n### {prefix} - {datetime.now().strftime('%H:%M')}\n\n{content}\n"

        session_content = session_content.rstrip() + message_block
        
        session_file.write_text(session_content)
        
        # Update index message count
        session_entry["message_count"] += 1
        self.index_path.write_text(json.dumps(index, indent=2))
        
        return True
    
    def get_today_sessions(self) -> List[Dict]:
        """Get all sessions from today."""
        today = datetime.now().strftime("%Y-%m-%d")
        index = self._get_index()
        return [s for s in index["sessions"] if s["date"] == today]

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a specific session by ID."""
        index = self._get_index()
        for s in index["sessions"]:
            if s["id"] == session_id:
                return s
        return None
