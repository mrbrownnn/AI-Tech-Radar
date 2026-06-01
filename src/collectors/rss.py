from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from src.collectors.base import CollectedItem
from src.config import Settings


class RSSCollector:
    source = "rss"

    def __init__(self, settings: Settings, source_config: dict[str, Any]):
        self.settings = settings
        self.source_config = source_config

    async def collect(self) -> list[CollectedItem]:
        feeds = self.source_config.get("feeds", [])
        items: list[CollectedItem] = []
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            for feed_url in feeds:
                response = await client.get(feed_url)
                response.raise_for_status()
                items.extend(self._parse_feed(feed_url, response.text))
        return items

    def _parse_feed(self, feed_url: str, content: str) -> list[CollectedItem]:
        root = ET.fromstring(content)
        collected: list[CollectedItem] = []
        for node in root.findall(".//item"):
            link = node.findtext("link")
            payload = {
                "feed_url": feed_url,
                "title": node.findtext("title"),
                "description": node.findtext("description"),
                "url": link,
                "published": node.findtext("pubDate"),
                "_collector": "rss",
            }
            collected.append(CollectedItem(source=self.source, source_id=link, payload=payload))
        return collected

