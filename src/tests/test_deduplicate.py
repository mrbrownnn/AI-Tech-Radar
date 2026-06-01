from src.pipeline.deduplicate import deduplicate_items


def test_deduplicate_keeps_highest_metric_for_same_url():
    items = [
        {
            "type": "repository",
            "title": "example/repo",
            "url": "https://github.com/example/repo",
            "metadata": {"stars": 10},
        },
        {
            "type": "repository",
            "title": "example/repo",
            "url": "https://github.com/example/repo",
            "metadata": {"stars": 100},
        },
    ]

    result = deduplicate_items(items)

    assert len(result) == 1
    assert result[0]["metadata"]["stars"] == 100


def test_deduplicate_similar_titles():
    items = [
        {"type": "model", "title": "Open LLM Benchmark", "metadata": {"downloads": 1}},
        {"type": "model", "title": "Open LLM Benchmarks", "metadata": {"downloads": 20}},
    ]

    result = deduplicate_items(items)

    assert len(result) == 1
    assert result[0]["metadata"]["downloads"] == 20

