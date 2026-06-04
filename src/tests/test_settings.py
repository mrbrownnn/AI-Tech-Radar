from src.config.settings import Settings


def test_bearer_tokens_are_cleaned_from_env_value_shape():
    settings = Settings(
        github_token="GITHUB_TOKEN=github_pat_example\n",
        huggingface_token=" HUGGINGFACE_TOKEN=hf_example ",
    )

    assert settings.github_token == "github_pat_example"
    assert settings.huggingface_token == "hf_example"


def test_empty_tokens_are_none():
    settings = Settings(github_token=" \n", huggingface_token="")

    assert settings.github_token is None
    assert settings.huggingface_token is None
