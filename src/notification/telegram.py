from __future__ import annotations

import asyncio

import httpx

from src.config import Settings


class TelegramNotifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_messages(self, messages: list[str]) -> None:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            raise RuntimeError("Telegram bot token or chat id is not configured")

        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            for message in messages:
                await self._send_with_retry(client, message)

    async def _send_with_retry(self, client: httpx.AsyncClient, message: str) -> None:
        delays = [5, 10, 20]
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": self.settings.telegram_chat_id,
                        "text": message,
                        "disable_web_page_preview": True,
                    },
                )
                response.raise_for_status()
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < len(delays):
                    await asyncio.sleep(delays[attempt])
        raise RuntimeError(f"Telegram delivery failed: {last_error}") from last_error

