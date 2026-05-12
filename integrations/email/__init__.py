"""
Email Integration

Integrates with email services for reading and sending emails.
"""

import asyncio
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class EmailIntegration:
    """Email integration for Custo."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.imap_conn = None
        self.smtp_conn = None

    async def connect_imap(self, host: str, username: str, password: str):
        """Connect to IMAP server."""
        self.imap_conn = imaplib.IMAP4_SSL(host)
        self.imap_conn.login(username, password)
        print("[EMAIL] IMAP connected")

    async def connect_smtp(self, host: str, port: int, username: str, password: str):
        """Connect to SMTP server."""
        self.smtp_conn = smtplib.SMTP_SSL(host, port)
        self.smtp_conn.login(username, password)
        print("[EMAIL] SMTP connected")

    async def fetch_unread(self, mailbox: str = "INBOX") -> List[dict]:
        """Fetch unread emails."""
        if not self.imap_conn:
            return []

        self.imap_conn.select(mailbox)
        _, messages = self.imap_conn.search(None, "UNSEEN")

        emails = []
        for msg_num in messages[0].split():
            _, msg_data = self.imap_conn.fetch(msg_num, "(RFC822)")
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            emails.append({
                "from": email_message["From"],
                "subject": email_message["Subject"],
                "date": email_message["Date"],
                "body": self._extract_body(email_message)
            })

        return emails

    def _extract_body(self, email_message) -> str:
        """Extract body from email message."""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
        return ""

    async def send_email(self, to: str, subject: str, body: str, is_html: bool = False):
        """Send an email."""
        if not self.smtp_conn:
            raise RuntimeError("SMTP not connected")

        msg = MIMEMultipart("alternative") if is_html else MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "custo@localhost"
        msg["To"] = to

        if is_html:
            msg.attach(MIMEText(body, "html"))

        self.smtp_conn.send_message(msg)

    async def disconnect(self):
        """Close connections."""
        if self.imap_conn:
            self.imap_conn.close()
        if self.smtp_conn:
            self.smtp_conn.quit()
