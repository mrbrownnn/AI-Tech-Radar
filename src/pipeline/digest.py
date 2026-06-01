from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class DigestSection:
    title: str
    content: str


@dataclass(frozen=True)
class GeneratedDigest:
    markdown: str
    sections: list[DigestSection]


SECTION_MAP = {
    "repository": "Top GitHub Repositories",
    "model": "Top AI Models",
    "dataset": "Top Datasets and Spaces",
    "space": "Top Datasets and Spaces",
    "paper": "Top Papers",
    "news": "Industry News",
}


def generate_digest(
    ranked_items: list[dict[str, Any]],
    *,
    digest_date: date,
    top_n: int,
    language: str = "en",
) -> GeneratedDigest:
    grouped = _group_items(ranked_items, top_n=top_n)
    title = "AI TECH RADAR" if language == "en" else "AI TECH RADAR"
    overview = f"# {title}\n\nDate: {digest_date.isoformat()}\n\nGenerated Automatically"

    sections: list[DigestSection] = []
    for section_title, items in grouped.items():
        section_content = _render_section(section_title, items)
        sections.append(DigestSection(title=section_title, content=section_content))

    markdown_parts = [overview, *[section.content for section in sections]]
    return GeneratedDigest(markdown="\n\n---\n\n".join(markdown_parts), sections=sections)


def _group_items(
    ranked_items: list[dict[str, Any]],
    *,
    top_n: int,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in ranked_items:
        section = SECTION_MAP.get(item.get("type"), "Interesting Releases")
        grouped.setdefault(section, [])
        if len(grouped[section]) < top_n:
            grouped[section].append(item)
    return grouped


def _render_section(title: str, items: list[dict[str, Any]]) -> str:
    lines = [f"## {title}"]
    if not items:
        lines.append("\nNo items found.")
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        metadata = item.get("metadata") or {}
        lines.extend(
            [
                "",
                f"{index}. {item.get('title', 'Untitled')}",
                _render_metric_line(item, metadata),
                "",
                item.get("description") or "No description available.",
                "",
                str(item.get("url") or ""),
            ]
        )
    return "\n".join(line for line in lines if line is not None)


def _render_metric_line(item: dict[str, Any], metadata: dict[str, Any]) -> str:
    item_type = item.get("type")
    score = item.get("final_score")
    if item_type == "repository":
        return f"Stars: {metadata.get('stars', 0)} | Forks: {metadata.get('forks', 0)} | Score: {score}"
    if item_type == "model":
        return f"Downloads: {metadata.get('downloads', 0)} | Task: {metadata.get('task') or 'unknown'} | Score: {score}"
    if item_type in {"dataset", "space"}:
        return f"Downloads: {metadata.get('downloads', 0)} | Likes: {metadata.get('likes', 0)} | Score: {score}"
    if item_type == "paper":
        authors = ", ".join(metadata.get("authors") or [])
        return f"Authors: {authors or 'unknown'} | Published: {item.get('published_at') or 'unknown'} | Score: {score}"
    return f"Source: {item.get('source')} | Score: {score}"


def split_digest_for_telegram(generated: GeneratedDigest) -> list[str]:
    overview = generated.markdown.split("\n\n---\n\n", 1)[0]
    return [overview, *[section.content for section in generated.sections]]


def split_markdown_sections(content: str) -> list[str]:
    return [part.strip() for part in content.split("\n\n---\n\n") if part.strip()]

