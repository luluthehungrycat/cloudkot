"""Regression tests for the first-run configuration example."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).parent.parent


def test_config_example_is_safe_and_loadable(tmp_path, monkeypatch):
    """A fresh checkout must provide a credential-free local configuration."""
    example_path = ROOT / "config.toml.example"
    assert example_path.is_file()

    config_text = example_path.read_text()
    config = tomllib.loads(config_text)
    api = config["api"]

    assert api["base_url"].startswith("http://localhost:")
    assert api["api_key"] == ""
    assert "sk-" not in config_text.lower()

    config_path = tmp_path / "config.toml"
    config_path.write_text(config_text)
    monkeypatch.chdir(tmp_path)

    from main import load_config

    assert load_config() == config


def test_load_config_uses_packaged_example_when_local_config_is_missing(tmp_path, monkeypatch):
    """An installed CLI must have a safe config path outside the checkout."""
    monkeypatch.chdir(tmp_path)

    from main import load_config

    config = load_config()

    assert config["api"]["provider"] == "local"
    assert config["api"]["api_key"] == ""


def test_unknown_provider_fallback_discards_remote_credentials():
    """An invalid provider must not reuse arbitrary URLs or API keys."""
    import asyncio

    from main import create_api_client

    client = create_api_client(
        {
            "api": {
                "provider": "unknown",
                "base_url": "https://remote.example.invalid",
                "api_key": "secret-that-must-not-be-used",
                "model": "remote-model",
            }
        }
    )

    try:
        assert client.base_url == "http://localhost:8080"
        assert client.api_key == ""
        assert client.model == "mistral-tiny"
    finally:
        asyncio.run(client.close())
