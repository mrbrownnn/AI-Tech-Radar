from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from src.collectors.base import CollectedItem
from src.config import Settings


class GitHubCollector:
    source = "github"

    def __init__(self, settings: Settings, source_config: dict[str, Any]):
        self.settings = settings
        self.source_config = source_config

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            headers=headers,
            follow_redirects=True,
        ) as client:
            if self.source_config.get("api_enabled", True):
                items.extend(await self._collect_from_api(client))
            if self.source_config.get("trending_enabled", True):
                items.extend(await self._collect_from_trending(client))

        return items

    async def _collect_from_api(self, client: httpx.AsyncClient) -> list[CollectedItem]:
        pushed_after = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "q": f"stars:>100 pushed:>={pushed_after} ai OR llm",
            "sort": "stars",
            "order": "desc",
            "per_page": 50,
        }
        response = await client.get("https://api.github.com/search/repositories", params=params)
        response.raise_for_status()
        data = response.json()
        return [
            CollectedItem(
                source=self.source,
                source_id=str(item.get("id")),
                payload={**item, "_collector": "github_api"},
            )
            for item in data.get("items", [])
        ]

    async def _collect_from_trending(self, client: httpx.AsyncClient) -> list[CollectedItem]:
        from bs4 import BeautifulSoup

        since = self.source_config.get("trending_since", "daily")
        response = await client.get("https://github.com/trending", params={"since": since})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        collected: list[CollectedItem] = []
        for article in soup.select("article.Box-row"):
            title_anchor = article.select_one("h2 a")
            if title_anchor is None:
                continue
            repo_path = " ".join(title_anchor.get_text(" ", strip=True).split())
            repo_path = repo_path.replace(" / ", "/")
            url = "https://github.com" + title_anchor.get("href", "")
            description_node = article.select_one("p")
            stars_node = article.select_one('a[href$="/stargazers"]')
            forks_node = article.select_one('a[href$="/forks"]')
            language_node = article.select_one("[itemprop='programmingLanguage']")

            payload = {
                "_collector": "github_trending",
                "full_name": repo_path,
                "html_url": url,
                "description": description_node.get_text(" ", strip=True)
                if description_node
                else None,
                "stargazers_count": self._parse_int(stars_node.get_text(strip=True))
                if stars_node
                else 0,
                "forks_count": self._parse_int(forks_node.get_text(strip=True))
                if forks_node
                else 0,
                "language": language_node.get_text(strip=True) if language_node else None,
                "topics": [],
            }
            collected.append(
                CollectedItem(source=self.source, source_id=repo_path, payload=payload)
            )
        return collected

    @staticmethod
    def _parse_int(value: str) -> int:
        cleaned = value.replace(",", "").strip()
        try:
            return int(cleaned)
        except ValueError:
            return 0
