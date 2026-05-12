"""
Base Gateway - Abstract Gateway Interface

Base class for all gateway implementations (Discord, WhatsApp, etc.)
"""

import abc
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class GatewayMessage:
    """Represents a message from a gateway."""
    source: str  # "discord", "whatsapp", etc.
    user_id: str
    content: str
    timestamp: datetime
    metadata: dict = None


class BaseGateway(abc.ABC):
    """Abstract base class for all gateway implementations."""

    def __init__(self, root_path: Path, gateway_name: str):
        self.root_path = root_path
        self.gateway_name = gateway_name
        self.running = False

    @abc.abstractmethod
    async def connect(self):
        """Connect to the external service."""
        pass

    @abc.abstractmethod
    async def disconnect(self):
        """Disconnect from the external service."""
        pass

    @abc.abstractmethod
    async def send_message(self, user_id: str, content: str):
        """Send a message to a user."""
        pass

    @abc.abstractmethod
    async def listen(self):
        """Listen for incoming messages."""
        pass

    async def start(self):
        """Start the gateway."""
        self.running = True
        await self.connect()
        await self.listen()

    async def stop(self):
        """Stop the gateway."""
        self.running = False
        await self.disconnect()

    def _log(self, level: str, message: str):
        """Log a message."""
        print(f"[{self.gateway_name.upper()}] {level}: {message}")
