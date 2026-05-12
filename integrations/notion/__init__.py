"""
Notion Integration

Integrates with Notion for reading/writing pages and database entries.
"""

import aiohttp
import json
from pathlib import Path
from typing import Optional, Dict, List


class NotionIntegration:
    """Notion API integration."""

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, root_path: Path, api_key: str):
        self.root_path = root_path
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    async def create_page(self, database_id: str, properties: dict) -> dict:
        """Create a new page in a database."""
        async with aiohttp.ClientSession() as session:
            payload = {"parent": {"database_id": database_id}, "properties": properties}
            async with session.post(
                f"{self.BASE_URL}/pages",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()

    async def query_database(self, database_id: str, filter: Optional[dict] = None) -> List[dict]:
        """Query pages from a database."""
        async with aiohttp.ClientSession() as session:
            payload = {"filter": filter} if filter else {}
            async with session.post(
                f"{self.BASE_URL}/databases/{database_id}/query",
                headers=self.headers,
                json=payload
            ) as resp:
                result = await resp.json()
                return result.get("results", [])

    async def update_page(self, page_id: str, properties: dict):
        """Update page properties."""
        async with aiohttp.ClientSession() as session:
            payload = {"properties": properties}
            async with session.patch(
                f"{self.BASE_URL}/pages/{page_id}",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()

    async def append_block(self, page_id: str, content: str, block_type: str = "paragraph"):
        """Append content block to a page."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "children": [{
                    "object": "block",
                    "type": block_type,
                    block_type: {"rich_text": [{"type": "text", "text": {"content": content}}]}
                }]
            }
            async with session.patch(
                f"{self.BASE_URL}/blocks/{page_id}/children",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()
