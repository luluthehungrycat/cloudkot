"""Regression tests for the first-run configuration example."""

from pathlib import Path

import tomllib

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
