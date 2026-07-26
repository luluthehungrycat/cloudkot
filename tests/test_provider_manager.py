"""
Unit tests for ProviderManager
"""

import pytest

from provider_manager import ProviderManager
from exceptions import CloudkotValidationError, ProviderError


@pytest.fixture
def provider_manager():
    """Create a ProviderManager instance for testing"""
    return ProviderManager("providers.toml")


class TestProviderManager:
    """Tests for ProviderManager class"""

    def test_load_providers(self, provider_manager):
        """Test that providers are loaded from config"""
        providers = provider_manager.list_providers()

        # Should have at least the providers we defined
        expected_providers = [
            "openai", "openai_oauth", "anthropic",
            "mistral", "openrouter", "opencode_go", "opencode_zen"
        ]

        for provider in expected_providers:
            assert provider in providers

    def test_get_provider(self, provider_manager):
        """Test getting a specific provider"""
        provider = provider_manager.get_provider("openai")

        assert provider.name == "OpenAI"
        assert provider.description == "OpenAI ChatGPT models"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.api_key_env == "OPENAI_API_KEY"
        assert "gpt-4o" in provider.models

    def test_get_unknown_provider(self, provider_manager):
        """Test getting an unknown provider raises error"""
        with pytest.raises(ProviderError) as exc_info:
            provider_manager.get_provider("unknown_provider")

        assert "Unknown provider" in str(exc_info.value)

    def test_list_models(self, provider_manager):
        """Test listing models for a provider"""
        models = provider_manager.list_models("anthropic")

        assert len(models) > 0
        assert any("claude" in model.lower() for model in models)

    def test_get_default_provider(self, provider_manager):
        """Test getting the default provider"""
        default = provider_manager.get_default_provider()
        assert default == "openai"

    def test_get_default_model(self, provider_manager):
        """Test getting the default model"""
        default = provider_manager.get_default_model()
        assert default == "gpt-4o"

    def test_get_api_key_from_env(self, provider_manager, monkeypatch):
        """Test getting API key from environment variable"""
        # Set a fake API key
        monkeypatch.setenv("OPENAI_API_KEY", "test_api_key_123")

        api_key = provider_manager.get_api_key("openai")
        assert api_key == "test_api_key_123"

    def test_get_api_key_not_set(self, provider_manager, monkeypatch):
        """Test getting API key when not set in environment"""
        # Make sure the env var is not set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        api_key = provider_manager.get_api_key("openai")
        assert api_key is None
