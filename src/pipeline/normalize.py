from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


def normalize_collected_item(source: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if source == "github":
        return _normalize_github(payload)
    if source == "huggingface":
        return _normalize_huggingface(payload)
    if source == "arxiv":
        return _normalize_arxiv(payload)
    if source == "rss":
        return _normalize_rss(payload)
    return None


def _normalize_github(payload: dict[str, Any]) -> dict[str, Any]:
    title = payload.get("full_name") or payload.get("name") or "unknown/repository"
    topics = payload.get("topics") or []
    language = payload.get("language")
    tags = [*topics]
    if language:
        tags.append(language)

    return {
        "source": "github",
        "type": "repository",
        "title": title,
        "description": payload.get("description"),
        "url": payload.get("html_url"),
        "tags": tags,
        "published_at": _parse_datetime(payload.get("created_at") or payload.get("pushed_at")),
        "metadata": {
            "stars": payload.get("stargazers_count", 0),
            "forks": payload.get("forks_count", 0),
            "contributors": payload.get("contributors_count"),
            "last_commit_at": payload.get("pushed_at"),
            "collector": payload.get("_collector"),
        },
    }


def _normalize_huggingface(payload: dict[str, Any]) -> dict[str, Any]:
    hf_type = payload.get("_hf_type", "model")
    item_id = payload.get("id") or payload.get("modelId") or payload.get("name") or "unknown"
    tags = payload.get("tags") or []
    url_prefix = {
        "model": "https://huggingface.co",
        "dataset": "https://huggingface.co/datasets",
        "space": "https://huggingface.co/spaces",
    }.get(hf_type, "https://huggingface.co")

    return {
        "source": "huggingface",
        "type": hf_type,
        "title": item_id,
        "description": payload.get("description") or payload.get("pipeline_tag"),
        "url": f"{url_prefix}/{item_id}",
        "tags": tags,
        "published_at": _parse_datetime(payload.get("createdAt") or payload.get("lastModified")),
        "metadata": {
            "downloads": payload.get("downloads", 0),
            "likes": payload.get("likes", 0),
            "task": payload.get("pipeline_tag") or payload.get("sdk"),
            "last_modified": payload.get("lastModified"),
        },
    }


def _normalize_arxiv(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "arxiv",
        "type": "paper",
        "title": payload.get("title") or "Untitled paper",
        "description": payload.get("summary"),
        "url": payload.get("url") or payload.get("id"),
        "tags": ["research", "paper"],
        "published_at": _parse_datetime(payload.get("published")),
        "metadata": {
            "authors": payload.get("authors", []),
        },
    }


def _normalize_rss(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "rss",
        "type": "news",
        "title": payload.get("title") or "Untitled article",
        "description": payload.get("description"),
        "url": payload.get("url"),
        "tags": ["news"],
        "published_at": _parse_datetime(payload.get("published")),
        "metadata": {
            "feed_url": payload.get("feed_url"),
        },
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        try:
            return parsedate_to_datetime(value).replace(tzinfo=None)
        except (TypeError, ValueError):
            return None
