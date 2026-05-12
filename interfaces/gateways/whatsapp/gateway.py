"""
WhatsApp Gateway - WhatsApp Integration via Twilio

Handles WhatsApp message routing using Twilio API.
"""

import asyncio
import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from threading import Thread
from pathlib import Path

from .base_gateway import BaseGateway, GatewayMessage


class WhatsAppGateway(BaseGateway):
    """WhatsApp gateway implementation via Twilio."""

    def __init__(self, root_path: Path, account_sid: str, auth_token: str, from_number: str):
        super().__init__(root_path, "whatsapp")
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.client: Optional[Client] = None
        self.app: Optional[Flask] = None

    def _create_flask_app(self):
        """Create Flask app for webhook handling."""
        app = Flask(__name__)

        @app.route("/whatsapp/webhook", methods=["POST"])
        def webhook():
            from_number = request.values.get("From", "")
            body = request.values.get("Body", "")

            message = GatewayMessage(
                source="whatsapp",
                user_id=from_number,
                content=body,
                timestamp=asyncio.get_event_loop().time(),
                metadata={"platform": "whatsapp"}
            )

            # Process message in background
            asyncio.create_task(self._process_message(message))

            # Return empty response (would send reply later)
            return str(MessagingResponse()), 200

        return app

    async def connect(self):
        """Connect to WhatsApp via Twilio webhook."""
        self.client = Client(self.account_sid, self.auth_token)

        # Start Flask webhook server in background thread
        self.app = self._create_flask_app()
        thread = Thread(target=self.app.run, kwargs={
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            "use_reloader": False
        }, daemon=True)
        thread.start()

        self._log("INFO", "WhatsApp webhook server started on port 5000")

    async def disconnect(self):
        """Disconnect from WhatsApp."""
        # Flask runs in daemon thread, just stop accepting
        self.running = False

    async def send_message(self, user_id: str, content: str):
        """Send WhatsApp message via Twilio."""
        if self.client:
            self.client.messages.create(
                from_=f"whatsapp:{self.from_number}",
                body=content,
                to=user_id
            )

    async def listen(self):
        """Listen for webhook calls - handled by Flask."""
        while self.running:
            await asyncio.sleep(1)

    async def _process_message(self, message: GatewayMessage):
        """Process incoming WhatsApp message."""
        # Route to Custo
        self._log("INFO", f"Received from {message.user_id}: {message.content}")


async def main():
    """WhatsApp gateway entry point."""
    root = Path(__file__).parent.parent.parent.parent
    config_path = root / "system" / "config.yaml"

    import yaml
    if config_path.exists():
        config = yaml.safe_load(config_path.read_text())
        wa_config = config.get("gateways", {}).get("whatsapp", {})

        sid = wa_config.get("account_sid", os.getenv("TWILIO_ACCOUNT_SID"))
        token = wa_config.get("auth_token", os.getenv("TWILIO_AUTH_TOKEN"))
        from_num = wa_config.get("from_number", os.getenv("TWILIO_FROM_NUMBER"))

        if all([sid, token, from_num]):
            gateway = WhatsAppGateway(root, sid, token, from_num)
            try:
                await gateway.start()
            except KeyboardInterrupt:
                await gateway.stop()
        else:
            print("[WHATSAPP] Missing configuration")
    else:
        print("Configuration not found.")


if __name__ == "__main__":
    asyncio.run(main())
