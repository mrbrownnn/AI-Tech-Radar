from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import func, select

from src.config import Settings
from src.models.digest import Digest
from src.models.item import Item
from src.pipeline.digest import split_markdown_sections
from src.repositories.database import SessionLocal
from src.repositories.digest_repository import DigestRepository
from src.repositories.item_repository import ItemRepository
from src.scheduler.jobs import run_crawl_job, run_delivery_job, run_digest_job


COMMANDS = [
    {"command": "start", "description": "Connect to AI Tech Radar"},
    {"command": "help", "description": "Show available commands"},
    {"command": "status", "description": "Show service status"},
    {"command": "items", "description": "Show top ranked items"},
    {"command": "news", "description": "Refresh and send latest AI news"},
    {"command": "latest", "description": "Send latest digest"},
    {"command": "refresh", "description": "Refresh data now"},
    {"command": "crawl", "description": "Refresh data now"},
    {"command": "digest", "description": "Generate digest"},
    {"command": "notify", "description": "Send latest digest"},
    {"command": "run", "description": "Run refresh, digest, and notify"},
]


@dataclass
class TelegramMessage:
    chat_id: str
    text: str


class TelegramCommandBot:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._offset: int | None = None

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.enable_telegram_commands
            and self.settings.telegram_bot_token
            and self.settings.telegram_chat_id
        )

    async def start(self) -> None:
        if not self.enabled:
            return
        await self._delete_webhook()
        await self.register_commands()
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def register_commands(self) -> None:
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            response = await client.post(self._api_url("setMyCommands"), json={"commands": COMMANDS})
            response.raise_for_status()

    async def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                updates = await self._get_updates()
                for update in updates:
                    self._offset = int(update["update_id"]) + 1
                    message = self._extract_message(update)
                    if message:
                        await self._handle_message(message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                print(f"Telegram command polling error: {exc}")
                await asyncio.sleep(5)

    async def _get_updates(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds + 35) as client:
            response = await client.get(
                self._api_url("getUpdates"),
                params={
                    "timeout": 30,
                    "offset": self._offset,
                    "allowed_updates": '["message"]',
                },
            )
            response.raise_for_status()
            return response.json().get("result", [])

    def _extract_message(self, update: dict[str, Any]) -> TelegramMessage | None:
        message = update.get("message") or {}
        text = message.get("text")
        chat_id = str((message.get("chat") or {}).get("id", ""))
        if not text or not chat_id:
            return None
        return TelegramMessage(chat_id=chat_id, text=text.strip())

    async def _handle_message(self, message: TelegramMessage) -> None:
        if str(message.chat_id) != str(self.settings.telegram_chat_id):
            await self._send_text(message.chat_id, "Unauthorized chat.")
            return

        command = message.text.split()[0].split("@")[0].lower()
        if command == "/start":
            await self._send_text(message.chat_id, "AI Tech Radar is connected. Use /help.")
        elif command == "/help":
            await self._send_text(message.chat_id, self._help_text())
        elif command == "/status":
            await self._send_text(message.chat_id, await asyncio.to_thread(self._status_text))
        elif command == "/items":
            await self._send_text(message.chat_id, await asyncio.to_thread(self._top_items_text))
        elif command == "/news":
            await self._send_news(message.chat_id)
        elif command == "/latest":
            await self._send_latest_digest(message.chat_id)
        elif command in {"/refresh", "/crawl"}:
            await self._run_job(message.chat_id, "refresh", run_crawl_job)
        elif command == "/digest":
            await self._run_job(message.chat_id, "digest", run_digest_job)
        elif command == "/notify":
            await self._run_job(message.chat_id, "notify", run_delivery_job)
        elif command == "/run":
            await self._run_full_pipeline(message.chat_id)
        else:
            await self._send_text(message.chat_id, "Unknown command. Use /help.")

    async def _run_job(self, chat_id: str, name: str, job) -> None:
        await self._send_text(chat_id, f"Running {name}...")
        try:
            result = await asyncio.to_thread(job, self.settings)
        except Exception as exc:  # noqa: BLE001
            await self._send_text(chat_id, f"{name} failed: {exc}")
            return
        await self._send_text(chat_id, f"{name} completed: {result}")

    async def _run_full_pipeline(self, chat_id: str) -> None:
        await self._send_text(chat_id, "Running refresh -> digest -> notify...")
        for name, job in (
            ("refresh", run_crawl_job),
            ("digest", run_digest_job),
            ("notify", run_delivery_job),
        ):
            try:
                result = await asyncio.to_thread(job, self.settings)
            except Exception as exc:  # noqa: BLE001
                await self._send_text(chat_id, f"{name} failed: {exc}")
                return
            await self._send_text(chat_id, f"{name} completed: {result}")

    async def _send_news(self, chat_id: str) -> None:
        await self._send_text(chat_id, "Updating AI tech news...")
        try:
            crawl_result = await asyncio.to_thread(run_crawl_job, self.settings)
            await asyncio.to_thread(run_digest_job, self.settings)
        except Exception as exc:  # noqa: BLE001
            await self._send_text(chat_id, f"news failed: {exc}")
            return

        digest = await asyncio.to_thread(self._latest_digest)
        if digest is None:
            await self._send_text(chat_id, "No digest was generated.")
            return

        upserted_items = crawl_result.get("upserted_items", 0)
        await self._send_text(chat_id, f"News updated: {upserted_items} items indexed.")
        for message in split_markdown_sections(digest.content):
            await self._send_text(chat_id, message)

    async def _send_latest_digest(self, chat_id: str) -> None:
        digest = await asyncio.to_thread(self._latest_digest)
        if digest is None:
            await self._send_text(chat_id, "No digest found. Use /digest first.")
            return
        for message in split_markdown_sections(digest.content):
            await self._send_text(chat_id, message)

    def _latest_digest(self) -> Digest | None:
        db = SessionLocal()
        try:
            return DigestRepository(db).latest_digest(channel="telegram")
        finally:
            db.close()

    def _status_text(self) -> str:
        db = SessionLocal()
        try:
            item_count = db.scalar(select(func.count()).select_from(Item)) or 0
            digest_count = db.scalar(select(func.count()).select_from(Digest)) or 0
        finally:
            db.close()

        return (
            "AI Tech Radar Status\n\n"
            "API: ok\n"
            f"Scheduler: {'enabled' if self.settings.enable_scheduler else 'disabled'}\n"
            f"Realtime updates: {'enabled' if self.settings.enable_realtime_updates else 'disabled'}\n"
            f"Refresh interval: {self.settings.realtime_refresh_interval_minutes} minutes\n"
            f"Items: {item_count}\n"
            f"Digests: {digest_count}\n"
            f"Top N: {self.settings.top_n_items}\n"
            f"Language: {self.settings.digest_language}"
        )

    def _top_items_text(self) -> str:
        db = SessionLocal()
        try:
            rows = ItemRepository(db).list_ranked_items(limit=self.settings.top_n_items)
        finally:
            db.close()

        if not rows:
            return "No ranked items found. Use /refresh first."

        lines = ["Top Ranked Items"]
        for index, (item, score) in enumerate(rows, start=1):
            final_score = score.final_score if score else 0
            lines.extend(
                [
                    "",
                    f"{index}. {item.title}",
                    f"Source: {item.source} | Type: {item.type} | Score: {final_score}",
                    item.url or "",
                ]
            )
        return "\n".join(lines)

    async def _send_text(self, chat_id: str, text: str) -> None:
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            for chunk in self._chunk_text(text):
                response = await client.post(
                    self._api_url("sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "disable_web_page_preview": True,
                    },
                )
                response.raise_for_status()

    async def _delete_webhook(self) -> None:
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            response = await client.post(
                self._api_url("deleteWebhook"),
                json={"drop_pending_updates": True},
            )
            response.raise_for_status()

    def _api_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/{method}"

    @staticmethod
    def _chunk_text(text: str, limit: int = 3900) -> list[str]:
        if len(text) <= limit:
            return [text]
        chunks = []
        remaining = text
        while remaining:
            chunks.append(remaining[:limit])
            remaining = remaining[limit:]
        return chunks

    @staticmethod
    def _help_text() -> str:
        return (
            "AI Tech Radar Commands\n\n"
            "/status - show service status\n"
            "/items - show top ranked items\n"
            "/news - refresh and send latest AI news\n"
            "/latest - send latest digest\n"
            "/refresh - refresh data now\n"
            "/crawl - refresh data now\n"
            "/digest - generate digest\n"
            "/notify - send latest digest\n"
            "/run - refresh, digest, and notify\n"
            "/help - show this help"
        )
