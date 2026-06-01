from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from src.config import get_settings
from src.notification.telegram_commands import TelegramCommandBot
from src.repositories.database import get_db, init_db
from src.repositories.digest_repository import DigestRepository
from src.repositories.item_repository import ItemRepository
from src.scheduler.jobs import create_scheduler, run_crawl_job, run_delivery_job, run_digest_job

settings = get_settings()
scheduler = None
telegram_command_bot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler, telegram_command_bot
    init_db()
    if settings.enable_scheduler:
        scheduler = create_scheduler(settings)
        scheduler.start()
    telegram_command_bot = TelegramCommandBot(settings)
    await telegram_command_bot.start()
    yield
    if telegram_command_bot:
        await telegram_command_bot.stop()
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/crawl")
def crawl(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(run_crawl_job, settings)
    return {"status": "started"}


@app.post("/refresh")
def refresh(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(run_crawl_job, settings)
    return {"status": "started"}


@app.post("/digest")
def digest() -> dict[str, str]:
    result = run_digest_job(settings)
    return {"status": result.get("status", "generated")}


@app.post("/notify")
def notify() -> dict[str, str]:
    try:
        result = run_delivery_job(settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": result.get("status", "sent")}


@app.get("/items")
def list_items(
    db: Annotated[Session, Depends(get_db)],
    source: str | None = None,
    type: str | None = None,  # noqa: A002
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[dict]:
    repo = ItemRepository(db)
    rows = repo.list_ranked_items(source=source, item_type=type, limit=limit)
    return [
        {
            "id": item.id,
            "title": item.title,
            "source": item.source,
            "type": item.type,
            "url": item.url,
            "score": score.final_score if score else 0,
        }
        for item, score in rows
    ]


@app.get("/digests/latest")
def latest_digest(db: Annotated[Session, Depends(get_db)]) -> dict:
    digest = DigestRepository(db).latest_digest()
    if digest is None:
        raise HTTPException(status_code=404, detail="No digest found")
    return {
        "id": digest.id,
        "date": digest.digest_date.isoformat(),
        "channel": digest.channel,
        "content": digest.content,
    }
