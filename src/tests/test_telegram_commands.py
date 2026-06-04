import asyncio
import os
from types import SimpleNamespace

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.config import Settings
from src.notification import telegram_commands
from src.notification.telegram_commands import COMMANDS, TelegramCommandBot


class RecordingTelegramCommandBot(TelegramCommandBot):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.sent_messages: list[str] = []

    async def _send_text(self, chat_id: str, text: str) -> None:
        self.sent_messages.append(text)

    def _latest_digest(self):
        return SimpleNamespace(content="Overview\n\n---\n\nTop AI Models")


def test_news_command_is_registered_and_listed_in_help():
    assert any(command["command"] == "news" for command in COMMANDS)
    assert "/news - refresh and send latest AI news" in TelegramCommandBot._help_text()


def test_send_news_runs_crawl_digest_and_sends_latest_digest(monkeypatch):
    calls = []

    def fake_crawl_job(settings):
        calls.append("crawl")
        return {"report_date": "2026-06-03", "upserted_items": 3}

    def fake_digest_job(settings):
        calls.append("digest")
        return {"status": "generated", "digest_id": 1}

    monkeypatch.setattr(telegram_commands, "run_crawl_job", fake_crawl_job)
    monkeypatch.setattr(telegram_commands, "run_digest_job", fake_digest_job)

    bot = RecordingTelegramCommandBot(
        Settings(telegram_bot_token="telegram-token", telegram_chat_id="123")
    )

    asyncio.run(bot._send_news("123"))

    assert calls == ["crawl", "digest"]
    assert bot.sent_messages == [
        "Updating AI tech news...",
        "News updated for 2026-06-03: 3 items indexed.",
        "Overview",
        "Top AI Models",
    ]
