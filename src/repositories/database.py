from collections.abc import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.models.base import Base


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _sqlalchemy_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _database_host(database_url: str) -> str | None:
    parsed = urlparse(database_url)
    return parsed.hostname


def _validate_database_url(database_url: str) -> None:
    host = _database_host(database_url)
    if host == "postgres":
        raise RuntimeError(
            "DATABASE_URL points to host 'postgres', which only works inside Docker Compose. "
            "On Render, set DATABASE_URL from the Render Postgres internal connection string "
            "or deploy via the Blueprint so fromDatabase injects it."
        )


def _log_database_target(database_url: str) -> None:
    parsed = urlparse(database_url)
    safe_target = f"{parsed.scheme}://{parsed.hostname or 'unknown'}"
    if parsed.port:
        safe_target = f"{safe_target}:{parsed.port}"
    print(f"Using database target: {safe_target}", flush=True)


settings = get_settings()
database_url = _sqlalchemy_database_url(settings.database_url)
_validate_database_url(database_url)
_log_database_target(database_url)
engine = create_engine(
    database_url,
    connect_args=_connect_args(database_url),
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_db() -> None:
    import src.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
