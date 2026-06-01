from datetime import datetime

from src.pipeline.ranking import score_item


def test_score_item_returns_weighted_final_score():
    score = score_item(
        {
            "title": "AI agent framework",
            "description": "Open source LLM developer tool",
            "tags": ["ai", "llm"],
            "published_at": datetime(2026, 6, 1),
            "metadata": {"stars": 10_000, "forks": 500, "last_commit_at": "2026-06-01T00:00:00Z"},
        },
        now=datetime(2026, 6, 1),
    )

    assert 0 <= score["final_score"] <= 100
    assert score["relevance_score"] > 50

