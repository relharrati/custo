"""Task routing - determines which agent handles which task type."""

from typing import Dict

# Mapping from task type to agent type
TASK_ROUTING = {
    "research": "researcher",
    "explore": "researcher",
    "search": "researcher",
    "deep_dive": "researcher",
    "synthesize": "researcher",
    "code": "coder",
    "code_implementation": "coder",
    "write_file": "coder",
    "debug": "coder",
    "run": "coder",
    "lint": "coder",
    "visual": "coder",
    "architecture": "strategist",
    "plan": "strategist",
    "design": "strategist",
    "review": "strategist",
    "analyze": "strategist",
    "roadmap": "strategist",
    "create_session": "main",
    "chat": "main",
    "reflect": "main",
    "user_input": "main",
    "default": "main"
}


def route_task(task_type: str) -> str:
    """
    Route a task type to the appropriate agent.
    
    Args:
        task_type: The type of task to route
        
    Returns:
        The agent type that should handle the task
    """
    return TASK_ROUTING.get(task_type, TASK_ROUTING["default"])


class Router:
    """Router instance for runtime registration."""
    
    def __init__(self):
        self._routes = TASK_ROUTING.copy()
    
    def register(self, task_type: str, agent_type: str):
        """Register a new task type routing."""
        self._routes[task_type] = agent_type
    
    def get(self, task_type: str) -> str:
        """Get agent type for task type."""
        return self._routes.get(task_type, self._routes["default"])


router = Router()
