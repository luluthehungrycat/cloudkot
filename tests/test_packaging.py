"""Regression tests for the distributable package layout."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).parent.parent


def test_pyproject_declares_only_existing_packages_and_cli_modules():
    """The wheel metadata must describe the modules used by the CLI."""
    with (ROOT / "pyproject.toml").open("rb") as config_file:
        poetry = tomllib.load(config_file)["tool"]["poetry"]

    for package in poetry["packages"]:
        assert (ROOT / package["include"]).is_dir(), package["include"]

    declared_files = {item["path"] if isinstance(item, dict) else item for item in poetry.get("include", [])}
    required_modules = {
        "api_client.py",
        "context_manager.py",
        "harness.py",
        "lsp_server.py",
        "main.py",
        "mcp_server.py",
        "permissions.py",
        "personality_manager.py",
        "provider_manager.py",
        "tui.py",
    }
    required_assets = {"config.toml.example", "personalities.toml", "providers.toml"}
    assert required_modules | required_assets <= declared_files


def test_default_config_lookup_is_independent_of_current_directory(tmp_path, monkeypatch):
    """Installed commands must find bundled configs when launched elsewhere."""
    from personality_manager import PersonalityManager
    from provider_manager import ProviderManager

    monkeypatch.chdir(tmp_path)

    assert ProviderManager().list_providers()
    assert PersonalityManager().list_personalities()
