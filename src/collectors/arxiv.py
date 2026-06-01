from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from src.collectors.base import CollectedItem
from src.config import Settings


class ArxivCollector:
    source = "arxiv"

    def __init__(self, settings: Settings, source_config: dict[str, Any]):
        self.settings = settings
        self.source_config = source_config

    async def collect(self) -> list[CollectedItem]:
        categories = self.source_config.get("categories", ["cs.AI", "cs.LG", "cs.CL", "cs.CV"])
        query = " OR ".join(f"cat:{category}" for category in categories)
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 50,
        }
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            response = await client.get("https://export.arxiv.org/api/query", params=params)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items: list[CollectedItem] = []
        for entry in root.findall("atom:entry", ns):
            arxiv_id = entry.findtext("atom:id", default="", namespaces=ns)
            payload = {
                "id": arxiv_id,
                "title": entry.findtext("atom:title", default="", namespaces=ns).strip(),
                "summary": entry.findtext("atom:summary", default="", namespaces=ns).strip(),
                "published": entry.findtext("atom:published", default="", namespaces=ns),
                "authors": [
                    author.findtext("atom:name", default="", namespaces=ns)
                    for author in entry.findall("atom:author", ns)
                ],
                "url": arxiv_id,
                "_collector": "arxiv",
            }
            items.append(CollectedItem(source=self.source, source_id=arxiv_id, payload=payload))
        return items

