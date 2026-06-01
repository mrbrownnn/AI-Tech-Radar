from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Tech Radar"
    database_url: str = "sqlite:///./ai_tech_radar.db"

    github_token: str | None = None
    huggingface_token: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    top_n_items: int = Field(default=5, ge=1, le=50)
    digest_language: str = Field(default="en", pattern="^(en|vi)$")
    enable_realtime_updates: bool = True
    realtime_refresh_interval_minutes: int = Field(default=15, ge=1, le=1440)
    digest_time_local: str = "08:05"
    delivery_time_local: str = "08:06"
    export_markdown_reports: bool = True
    markdown_reports_dir: Path = Path("reports")
    app_timezone: str = "Asia/Bangkok"
    enable_scheduler: bool = True
    enable_telegram_commands: bool = True
    http_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
