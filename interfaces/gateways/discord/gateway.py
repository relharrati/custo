"""
Discord Gateway - Discord Integration

Handles connection to Discord and message routing.
"""

import asyncio
import discord
from pathlib import Path
from typing import Optional

from .base_gateway import BaseGateway, GatewayMessage


class DiscordGateway(BaseGateway):
    """Discord gateway implementation."""

    def __init__(self, root_path: Path, token: str, channel_id: str):
        super().__init__(root_path, "discord")
        self.token = token
        self.channel_id = int(channel_id)
        self.client: Optional[discord.Client] = None

    async def connect(self):
        """Connect to Discord."""
        intents = discord.Intents.default()
        intents.message_content = True

        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_ready():
            self._log("INFO", f"Connected as {self.client.user}")

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return

            gateway_msg = GatewayMessage(
                source="discord",
                user_id=str(message.author.id),
                content=message.content,
                timestamp=message.created_at,
                metadata={
                    "channel_id": str(message.channel.id),
                    "username": message.author.name
                }
            )
            await self._process_message(gateway_msg)

        print(f"[DISCORD] Connecting to Discord...")
        await self.client.start(self.token)

    async def disconnect(self):
        """Disconnect from Discord."""
        if self.client:
            await self.client.close()

    async def send_message(self, user_id: str, content: str):
        """Send a message to a Discord user."""
        if not self.client:
            return

        user = self.client.get_user(int(user_id))
        if user:
            await user.send(content)
        else:
            self._log("WARNING", f"User {user_id} not found")

    async def listen(self):
        """Listen for messages - handled by on_message event."""
        while self.running:
            await asyncio.sleep(1)

    async def _process_message(self, message: GatewayMessage):
        """Process incoming Discord message."""
        # Route to supervisor/agent
        print(f"[DISCORD] Received from {message.metadata.get('username')}: {message.content}")


async def main():
    """Discord gateway entry point."""
    root = Path(__file__).parent.parent.parent.parent
    config_path = root / "system" / "config.yaml"

    import yaml
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text())
        discord_config = config.get("gateways", {}).get("discord", {})
        token = discord_config.get("token")
        channel_id = discord_config.get("channel_id")

        if token:
            gateway = DiscordGateway(root, token, channel_id or "")
            try:
                await gateway.start()
            except KeyboardInterrupt:
                await gateway.stop()
        else:
            print("[DISCORD] No token configured in system/config.yaml")
    else:
        print("Configuration not found.")


if __name__ == "__main__":
    asyncio.run(main())
