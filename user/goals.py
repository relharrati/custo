"""User goals management."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class GoalsManager:
    """Manage user goals and progress."""
    
    def __init__(self, root_path: Path = None):
        self.root = Path(root_path or Path(__file__).parent.parent)
        self.goals_path = self.root / "user" / "goals.md"
    
    def load(self) -> List[Dict]:
        """Load all goals."""
        if not self.goals_path.exists():
            return []
        
        content = self.goals_path.read_text()
        goals = []
        # Parse markdown goals format
        return goals
    
    def add(self, title: str, description: str, deadline: Optional[str] = None) -> Dict:
        """Add a new goal."""
        goals = self.load()
        goal = {
            "id": f"goal_{len(goals) + 1}",
            "title": title,
            "description": description,
            "created": datetime.now().isoformat(),
            "deadline": deadline,
            "status": "active",
            "progress": 0.0
        }
        goals.append(goal)
        self._save(goals)
        return goal
    
    def update_progress(self, goal_id: str, progress: float):
        """Update goal progress."""
        goals = self.load()
        for goal in goals:
            if goal["id"] == goal_id:
                goal["progress"] = max(0.0, min(1.0, progress))
                goal["last_updated"] = datetime.now().isoformat()
        self._save(goals)
    
    def _save(self, goals: List[Dict]):
        """Save goals to disk."""
        lines = ["# User Goals\n\n"]
        for goal in goals:
            status_icon = "✓" if goal["status"] == "completed" else "◐"
            lines.append(f"## {status_icon} {goal['title']}\n")
            lines.append(f"- **Progress:** {int(goal['progress']*100)}%\n")
            lines.append(f"- **Description:** {goal['description']}\n")
            if goal.get("deadline"):
                lines.append(f"- **Deadline:** {goal['deadline']}\n")
            lines.append("\n")
        
        self.goals_path.write_text(''.join(lines))


def load_goals(root_path: Path = None) -> List[Dict]:
    """Load goals (convenience function)."""
    mgr = GoalsManager(root_path)
    return mgr.load()
