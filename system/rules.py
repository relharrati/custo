"""System rules and policies."""

RULES = {
    "identity_protection": {
        "enabled": True,
        "description": "Agent identities are sacred - never impersonate another agent"
    },
    "memory_immutability": {
        "enabled": True,
        "description": "Past memories cannot be deleted, only marked as superseded"
    },
    "delegation_first": {
        "enabled": True,
        "description": "If a specialist agent exists for a task, delegate instead of DIY"
    },
    "verify_before_claim": {
        "enabled": True,
        "description": "Never claim work is done without verification step"
    },
    "minimal_change": {
        "enabled": True,
        "description": "Smallest correct change wins - avoid over-engineering"
    }
}


def load_rules() -> dict:
    """Load system rules."""
    return RULES
