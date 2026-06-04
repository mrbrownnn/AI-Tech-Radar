from __future__ import annotations

import asyncio
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from sqlalchemy.orm import Session

from src.collectors import ArxivCollector, GitHubCollector, HuggingFaceCollector, RSSCollector
from src.collectors.base import CollectedItem
from src.config import Settings, get_settings
from src.notification.telegram import TelegramNotifier
from src.pipeline.daily_window import (
    is_in_report_window,
    report_date_for_timezone,
    report_window_utc,
)
from src.pipeline.deduplicate import deduplicate_items
from src.pipeline.digest import generate_digest, split_markdown_sections
from src.pipeline.normalize import normalize_collected_item
from src.pipeline.ranking import score_item
from src.repositories.database import SessionLocal
from src.repositories.digest_repository import DigestRepository
from src.repositories.item_repository import ItemRepository


def run_crawl_job(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    target_date = report_date_for_timezone(settings.app_timezone)
    source_config = load_source_config()
    collected = asyncio.run(_collect_enabled_sources(settings, source_config))

    db = SessionLocal()
    try:
        stats = _persist_collected_items(db, collected, settings, target_date)
        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_digest_job(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    target_date = report_date_for_timezone(settings.app_timezone)
    window_start, window_end = report_window_utc(target_date, settings.app_timezone)
    db = SessionLocal()
    try:
        item_repo = ItemRepository(db)
        digest_repo = DigestRepository(db)
        ranked = [
            _item_to_digest_dict(item, score)
            for item, score in item_repo.list_items_for_digest(
                published_from=window_start,
                published_to=window_end,
            )
        ]
        ranked = [item for item in ranked if item.get("final_score") is not None]
        ranked.sort(key=lambda item: item["final_score"], reverse=True)

        generated = generate_digest(
            ranked,
            digest_date=target_date,
            top_n=settings.top_n_items,
            language=settings.digest_language,
        )
        digest = digest_repo.create_digest(
            digest_date=target_date,
            content=generated.markdown,
            channel="telegram",
        )
        if settings.export_markdown_reports:
            _export_markdown(settings.markdown_reports_dir, digest.digest_date, generated.markdown)
        db.commit()
        return {"status": "generated", "digest_id": digest.id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_delivery_job(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    db = SessionLocal()
    try:
        digest_repo = DigestRepository(db)
        digest = digest_repo.latest_digest(channel="telegram")
        if digest is None:
            return {"status": "skipped", "reason": "no_digest"}

        messages = split_markdown_sections(digest.content)
        try:
            asyncio.run(TelegramNotifier(settings).send_messages(messages))
        except Exception as exc:  # noqa: BLE001
            digest_repo.create_delivery_log(
                digest_id=digest.id,
                channel="telegram",
                status="failed",
                error_message=str(exc),
            )
            db.commit()
            raise

        digest_repo.create_delivery_log(
            digest_id=digest.id,
            channel="telegram",
            status="sent",
            sent_at=datetime.utcnow(),
        )
        db.commit()
        return {"status": "sent", "digest_id": digest.id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_scheduler(settings: Settings | None = None):
    from apscheduler.schedulers.background import BackgroundScheduler

    settings = settings or get_settings()
    scheduler_timezone = ZoneInfo(settings.app_timezone)
    scheduler = BackgroundScheduler(timezone=scheduler_timezone)
    if settings.enable_realtime_updates:
        scheduler.add_job(
            run_crawl_job,
            "interval",
            minutes=settings.realtime_refresh_interval_minutes,
            id="realtime_refresh",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            next_run_time=datetime.now(scheduler_timezone),
            kwargs={"settings": settings},
        )
    digest_hour, digest_minute = _parse_hhmm(settings.digest_time_local)
    scheduler.add_job(
        run_digest_job,
        "cron",
        hour=digest_hour,
        minute=digest_minute,
        id="daily_digest",
        replace_existing=True,
        kwargs={"settings": settings},
    )
    delivery_hour, delivery_minute = _parse_hhmm(settings.delivery_time_local)
    scheduler.add_job(
        run_delivery_job,
        "cron",
        hour=delivery_hour,
        minute=delivery_minute,
        id="daily_delivery",
        replace_existing=True,
        kwargs={"settings": settings},
    )
    return scheduler


def load_source_config(path: str | Path = "src/config/sources.yaml") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


async def _collect_enabled_sources(
    settings: Settings,
    source_config: dict[str, Any],
) -> list[CollectedItem]:
    collectors = []
    if source_config.get("github", {}).get("enabled", False):
        collectors.append(GitHubCollector(settings, source_config["github"]))
    if source_config.get("huggingface", {}).get("enabled", False):
        collectors.append(HuggingFaceCollector(settings, source_config["huggingface"]))
    if source_config.get("arxiv", {}).get("enabled", False):
        collectors.append(ArxivCollector(settings, source_config["arxiv"]))
    if source_config.get("rss", {}).get("enabled", False):
        collectors.append(RSSCollector(settings, source_config["rss"]))

    collected: list[CollectedItem] = []
    for collector in collectors:
        collected.extend(await _collect_with_retries(collector))
    return collected


async def _collect_with_retries(collector: Any) -> list[CollectedItem]:
    delays = [5, 10, 20]
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            return await collector.collect()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < len(delays):
                await asyncio.sleep(delays[attempt])
    raise RuntimeError(f"{collector.__class__.__name__} failed: {last_error}") from last_error


def _persist_collected_items(
    db: Session,
    collected: list[CollectedItem],
    settings: Settings,
    target_date: date,
) -> dict[str, Any]:
    item_repo = ItemRepository(db)
    normalized_items: list[dict[str, Any]] = []
    window_start, window_end = report_window_utc(target_date, settings.app_timezone)

    for item in collected:
        normalized = normalize_collected_item(item.source, item.payload)
        if normalized and is_in_report_window(
            normalized.get("published_at"),
            target_date=target_date,
            app_timezone=settings.app_timezone,
        ):
            normalized_items.append(normalized)

    deduped = deduplicate_items(normalized_items)
    for item_data in deduped:
        item = item_repo.upsert_item(item_data)
        score_data = score_item(item_data, now=window_end)
        item_repo.save_score(item.id, score_data)

    return {
        "status": "success",
        "report_date": target_date.isoformat(),
        "window_start_utc": window_start.isoformat(),
        "window_end_utc": window_end.isoformat(),
        "collected_items": len(collected),
        "normalized_items": len(normalized_items),
        "filtered_out_items": len(collected) - len(normalized_items),
        "upserted_items": len(deduped),
    }


def _item_to_digest_dict(item: Any, score: Any | None) -> dict[str, Any]:
    return {
        "id": item.id,
        "source": item.source,
        "type": item.type,
        "title": item.title,
        "description": item.description,
        "url": item.url,
        "tags": item.tags or [],
        "metadata": item.metadata_json or {},
        "published_at": item.published_at,
        "final_score": score.final_score if score else None,
    }


def _export_markdown(directory: Path, digest_date: date, content: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest_date.isoformat()}-ai-tech-radar.md"
    path.write_text(content, encoding="utf-8")


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)
