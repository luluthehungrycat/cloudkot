"""
Provider Manager for Cloudkot
Handles different LLM providers with their specific configurations
"""

import os

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pathlib import Path

from pydantic import BaseModel

from exceptions import ConfigurationError, ProviderError


class ProviderConfig(BaseModel):
    name: str
    description: str
    base_url: str
    api_key_env: str
    models: list[str]
    auth_type: str
    requires_oauth: bool = False
    oauth_url: str | None = None


class ProviderManager:
    def __init__(self, config_path: str = "providers.toml"):
        self.config_path = Path(config_path)
        self.providers: dict[str, ProviderConfig] = {}
        self._loaded = False
        self._load_providers()

    def _load_providers(self):
        """Load provider configurations from TOML file"""
        if self._loaded:
            return

        if not self.config_path.exists():
            raise ConfigurationError(
                f"Providers configuration file not found: {self.config_path}",
                config_file=str(self.config_path)
            )

        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)

            if "providers" in config:
                for provider_name, provider_data in config["providers"].items():
                    self.providers[provider_name] = ProviderConfig(**provider_data)

            self._loaded = True
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load providers from {self.config_path}: {e}",
                config_file=str(self.config_path)
            ) from e

    def get_provider(self, provider_name: str) -> ProviderConfig:
        """Get provider configuration by name"""
        if provider_name not in self.providers:
            available = list(self.providers.keys())
            raise ProviderError(
                f"Unknown provider: {provider_name}. Available: {available}",
                provider=provider_name
            )
        return self.providers[provider_name]

    def get_api_key(self, provider_name: str) -> str | None:
        """Get API key for a provider from environment variable"""
        provider = self.get_provider(provider_name)
        return os.getenv(provider.api_key_env)

    def list_providers(self) -> list[str]:
        """List all available providers"""
        return list(self.providers.keys())

    def list_models(self, provider_name: str) -> list[str]:
        """List available models for a provider"""
        provider = self.get_provider(provider_name)
        return provider.models

    def get_default_provider(self) -> str:
        """Get the default provider from config"""
        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)
            default = config.get("default", {})
            return str(default.get("provider", "local"))
        except Exception as e:
            raise ConfigurationError(
                f"Failed to get default provider: {e}",
                config_file=str(self.config_path)
            ) from e

    def get_default_model(self) -> str:
        """Get the default model from config"""
        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)
            default = config.get("default", {})
            return str(default.get("model", "gpt-4o"))
        except Exception as e:
            raise ConfigurationError(
                f"Failed to get default model: {e}",
                config_file=str(self.config_path)
            ) from e


# Singleton instance
provider_manager = ProviderManager()
