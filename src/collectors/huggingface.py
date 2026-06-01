from __future__ import annotations

from typing import Any

import httpx

from src.collectors.base import CollectedItem
from src.config import Settings


class HuggingFaceCollector:
    source = "huggingface"

    def __init__(self, settings: Settings, source_config: dict[str, Any]):
        self.settings = settings
        self.source_config = source_config

    async def collect(self) -> list[CollectedItem]:
        headers: dict[str, str] = {}
        if self.settings.huggingface_token:
            headers["Authorization"] = f"Bearer {self.settings.huggingface_token}"

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            headers=headers,
            follow_redirects=True,
        ) as client:
            items: list[CollectedItem] = []
            if self.source_config.get("models_enabled", True):
                items.extend(await self._collect_endpoint(client, "models", "model"))
            if self.source_config.get("datasets_enabled", True):
                items.extend(await self._collect_endpoint(client, "datasets", "dataset"))
            if self.source_config.get("spaces_enabled", True):
                items.extend(await self._collect_endpoint(client, "spaces", "space"))
            return items

    async def _collect_endpoint(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        item_type: str,
    ) -> list[CollectedItem]:
        response = await client.get(
            f"https://huggingface.co/api/{endpoint}",
            params={"sort": "downloads", "direction": "-1", "limit": 50},
        )
        response.raise_for_status()
        payloads = response.json()
        collected: list[CollectedItem] = []
        for payload in payloads:
            item_id = payload.get("id") or payload.get("modelId") or payload.get("name")
            collected.append(
                CollectedItem(
                    source=self.source,
                    source_id=item_id,
                    payload={**payload, "_hf_type": item_type},
                )
            )
        return collected

