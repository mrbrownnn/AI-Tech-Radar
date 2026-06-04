from datetime import datetime

from src.pipeline.normalize import normalize_collected_item


def test_github_daily_date_uses_pushed_at_before_created_at():
    item = normalize_collected_item(
        "github",
        {
            "full_name": "example/repo",
            "html_url": "https://github.com/example/repo",
            "created_at": "2025-01-01T00:00:00Z",
            "pushed_at": "2026-06-03T10:00:00Z",
        },
    )

    assert item is not None
    assert item["published_at"] == datetime(2026, 6, 3, 10, 0)


def test_huggingface_daily_date_uses_last_modified_before_created_at():
    item = normalize_collected_item(
        "huggingface",
        {
            "id": "example/model",
            "_hf_type": "model",
            "createdAt": "2025-01-01T00:00:00Z",
            "lastModified": "2026-06-03T11:00:00Z",
        },
    )

    assert item is not None
    assert item["published_at"] == datetime(2026, 6, 3, 11, 0)
