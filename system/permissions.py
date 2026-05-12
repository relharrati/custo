"""Permission checking system."""

from pathlib import Path
from typing import Optional


class PermissionDenied(Exception):
    """Raised when an operation lacks required permission."""
    pass


# Permission levels
PERMISSIONS = {
    "read": ["all", "user", "memory", "system"],
    "write": ["main", "coder"],  # Only main and coder can write
    "admin": ["main"],  # Only main agent can admin
    "reflect": ["main", "strategist"],
    "delegate": ["main", "strategist", "researcher"]
}


def permission_checker(
    agent_type: str,
    action: str,
    resource: Optional[str] = None
) -> bool:
    """
    Check if an agent has permission to perform an action.
    
    Args:
        agent_type: The agent attempting the action
        action: The action being attempted
        resource: Optional resource path
        
    Returns:
        True if permitted, raises PermissionDenied if not
    """
    # Main agent can do anything
    if agent_type == "main":
        return True
    
    # Check action-specific permissions
    required_role = PERMISSIONS.get(action, ["admin"])
    
    if agent_type in required_role or "all" in required_role:
        return True
    
    # Resource-specific checks
    if resource:
        # Memory write requires coder or main (for now all agents can)
        if action == "write" and "memory" in resource:
            return True
    
    raise PermissionDenied(
        f"Agent '{agent_type}' lacks permission for action '{action}'"
    )


def check_permission(agent_type: str, action: str, resource: str = None):
    """Decorator for permission checking."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            permission_checker(agent_type, action, resource)
            return func(*args, **kwargs)
        return wrapper
    return decorator
