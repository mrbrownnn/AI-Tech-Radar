from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


def deduplicate_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    winners: list[dict[str, Any]] = []
    for item in items:
        duplicate_index = _find_duplicate_index(winners, item)
        if duplicate_index is None:
            winners.append(item)
            continue

        current = winners[duplicate_index]
        if _winner_score(item) > _winner_score(current):
            winners[duplicate_index] = item
    return winners


def _find_duplicate_index(items: list[dict[str, Any]], candidate: dict[str, Any]) -> int | None:
    candidate_url = candidate.get("url")
    candidate_repo = _repo_name(candidate)
    candidate_title = _normalize_text(candidate.get("title"))

    for index, item in enumerate(items):
        if candidate_url and candidate_url == item.get("url"):
            return index
        if candidate_repo and candidate_repo == _repo_name(item):
            return index
        title = _normalize_text(item.get("title"))
        if candidate_title and title:
            if SequenceMatcher(None, candidate_title, title).ratio() > 0.90:
                return index
    return None


def _repo_name(item: dict[str, Any]) -> str | None:
    if item.get("type") != "repository":
        return None
    title = item.get("title")
    if not title:
        return None
    return title.lower().strip()


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", value.lower())).strip()


def _winner_score(item: dict[str, Any]) -> float:
    metadata = item.get("metadata") or {}
    if "final_score" in item:
        return float(item["final_score"] or 0)
    return float(
        metadata.get("stars")
        or metadata.get("downloads")
        or metadata.get("likes")
        or metadata.get("forks")
        or 0
    )

