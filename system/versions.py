"""Version management for Custo system."""

from datetime import datetime
from typing import Dict

VERSION = "1.0.0"
BUILD_DATE = datetime.now().isoformat()
CODENAME = "Bootstrap"

VERSION_INFO: Dict[str, str] = {
    "version": VERSION,
    "build_date": BUILD_DATE,
    "codename": CODENAME,
    "components": {
        "daemon": "1.0.0",
        "agents": "1.0.0",
        "interfaces": "1.0.0",
        "memory": "1.0.0"
    }
}


def get_version() -> str:
    """Get current version string."""
    return f"Custo {VERSION} ({CODENAME})"


def get_version_info() -> Dict:
    """Get full version info dictionary."""
    return VERSION_INFO.copy()
