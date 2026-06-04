from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

RELEVANCE_KEYWORDS = {
    "ai",
    "agent",
    "agents",
    "automation",
    "backend",
    "benchmark",
    "code",
    "coding",
    "developer",
    "engineering",
    "framework",
    "inference",
    "language model",
    "llm",
    "machine learning",
    "model",
    "open source",
    "python",
    "rag",
    "research",
    "software",
    "tool",
}


def score_item(item: dict[str, Any], *, now: datetime | None = None) -> dict[str, float]:
    now = now or datetime.utcnow()
    popularity = popularity_score(item)
    recency = recency_score(item, now=now)
    activity = activity_score(item, now=now)
    relevance = relevance_score(item)
    final = (0.4 * popularity) + (0.3 * recency) + (0.2 * activity) + (0.1 * relevance)
    return {
        "popularity_score": round(popularity, 4),
        "activity_score": round(activity, 4),
        "recency_score": round(recency, 4),
        "relevance_score": round(relevance, 4),
        "final_score": round(final, 4),
    }


def popularity_score(item: dict[str, Any]) -> float:
    metadata = item.get("metadata") or {}
    signals = [
        metadata.get("stars", 0),
        metadata.get("forks", 0) * 2,
        metadata.get("downloads", 0),
        metadata.get("likes", 0) * 20,
    ]
    value = max(float(signal or 0) for signal in signals)
    return _log_scale(value, max_value=1_000_000)


def recency_score(item: dict[str, Any], *, now: datetime) -> float:
    published_at = item.get("published_at")
    if not isinstance(published_at, datetime):
        return 50.0
    age_days = max((now - published_at).total_seconds() / 86400, 0)
    return max(0.0, 100.0 - (age_days * 3.5))


def activity_score(item: dict[str, Any], *, now: datetime) -> float:
    metadata = item.get("metadata") or {}
    last_activity = metadata.get("last_commit_at") or metadata.get("last_modified")
    parsed = _parse_datetime(last_activity)
    if parsed:
        age_days = max((now - parsed).total_seconds() / 86400, 0)
        return max(0.0, 100.0 - (age_days * 4.0))

    downloads = float(metadata.get("downloads") or 0)
    stars = float(metadata.get("stars") or 0)
    if downloads or stars:
        return min(100.0, _log_scale(downloads + stars, max_value=250_000))
    return 40.0


def relevance_score(item: dict[str, Any]) -> float:
    text_parts = [
        item.get("title") or "",
        item.get("description") or "",
        " ".join(item.get("tags") or []),
    ]
    text = " ".join(text_parts).lower()
    hits = sum(1 for keyword in RELEVANCE_KEYWORDS if keyword in text)
    if hits == 0:
        return 35.0
    return min(100.0, 45.0 + hits * 12.0)


def _log_scale(value: float, *, max_value: float) -> float:
    if value <= 0:
        return 0.0
    return min(100.0, (math.log10(value + 1) / math.log10(max_value + 1)) * 100.0)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(UTC).replace(tzinfo=None)
