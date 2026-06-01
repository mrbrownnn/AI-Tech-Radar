from datetime import date

from src.pipeline.digest import generate_digest, split_digest_for_telegram


def test_digest_contains_top_items_and_links():
    digest = generate_digest(
        [
            {
                "type": "repository",
                "title": "example/repo",
                "description": "AI developer tool",
                "url": "https://github.com/example/repo",
                "metadata": {"stars": 100, "forks": 5},
                "final_score": 90,
            }
        ],
        digest_date=date(2026, 6, 1),
        top_n=5,
    )

    assert "Top GitHub Repositories" in digest.markdown
    assert "https://github.com/example/repo" in digest.markdown
    assert len(split_digest_for_telegram(digest)) == 2

