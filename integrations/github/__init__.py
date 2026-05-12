"""
GitHub Integration

Integrates with GitHub for issue tracking, PR management, and repo operations.
"""

import aiohttp
import json
from pathlib import Path
from typing import Optional, List, Dict


class GitHubIntegration:
    """GitHub API integration."""

    BASE_URL = "https://api.github.com"

    def __init__(self, root_path: Path, token: str = None):
        self.root_path = root_path
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Custo-Agent"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> List[dict]:
        """List issues for a repository."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
            params = {"state": state}
            async with session.get(url, headers=self.headers, params=params) as resp:
                return await resp.json()

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> dict:
        """Create a new issue."""
        async with aiohttp.ClientSession() as session:
            payload = {"title": title, "body": body}
            if labels:
                payload["labels"] = labels
            async with session.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()

    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> dict:
        """Create a pull request."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
            async with session.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                json=payload
            ) as resp:
                return await resp.json()

    async def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get repository information."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self.headers
            ) as resp:
                return await resp.json()
