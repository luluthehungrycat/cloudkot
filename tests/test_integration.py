"""
Integration tests for Cloudkot
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_config():
    """Create a temporary config file for testing"""
    config_content = """
[api]
base_url = "http://localhost:8080"
api_key = "test_api_key"
model = "test-model"
provider = "local"

[satire]
burokratie_mode = true
form_directory = "./forms"

[personality]
# Available personalities: neutral, stromberg, friendly, pedantic
active = "neutral"
# Custom personality description (overrides built-in personalities)
custom_description = ""

[permissions]
# Tool call permissions: allow, deny, ask
tool_calls = "allow"
file_access = "ask"
network_access = "deny"
execute_code = "ask"

[context]
# Context window tracking
max_tokens = 1000
compression_enabled = true
compression_threshold = 0.8

[skills]
# Enable/disable specific skills
enabled = ["code_generation", "code_explanation"]

[mcp]
# Model Context Protocol support
enabled = false

[tui]
# Text User Interface settings
enabled = false
theme = "default"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    yield config_path

    os.unlink(config_path)


class TestIntegration:
    """Integration tests for Cloudkot components"""

    def test_full_workflow(self, temp_config):
        """Test a complete workflow from config to response"""
        # Set the config path
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(temp_config))
        config_filename = os.path.basename(temp_config)

        try:
            # Import and test components
            from api_client import APIClient, Message
            from satire.engine import SatireEngine
            from harness import CodingHarness
            from context_manager import context_manager
            from permissions import permission_manager
            from skills.skill_manager import skill_manager

            # Create API client
            api = APIClient(
                base_url="http://localhost:8080",
                api_key="test_api_key",
                model="test-model"
            )

            # Create satire engine
            satire = SatireEngine(bürokratie_mode=True)

            # Create harness
            harness = CodingHarness(api, satire)

            # Test that all components are properly connected
            assert api.base_url == "http://localhost:8080"
            assert api.model == "test-model"
            assert satire.bürokratie_mode is True

            # Test context manager
            context_manager.clear_context()
            context_manager.add_context("Test message", "user")
            assert context_manager.get_token_count() > 0

            # Test permission manager
            assert "tool_calls" in permission_manager.permissions

            # Test skill manager
            skills = skill_manager.list_skills()
            assert len(skills) > 0

        finally:
            os.chdir(original_cwd)

    def test_cli_imports(self):
        """Test that CLI imports work correctly"""
        from main import cli, load_config, create_api_client
        from api_client import APIClient
        from satire.engine import SatireEngine
        from harness import CodingHarness

        # Test that we can create instances
        satire = SatireEngine()
        assert satire.bürokratie_mode is True

    def test_provider_integration(self):
        """Test provider manager integration"""
        from provider_manager import provider_manager

        # Test that we can get providers
        providers = provider_manager.list_providers()
        assert len(providers) > 0

        # Test getting a specific provider
        openai = provider_manager.get_provider("openai")
        assert openai.name == "OpenAI"

    def test_personality_integration(self):
        """Test personality manager integration"""
        from personality_manager import personality_manager

        # Test that we can get personalities
        personalities = personality_manager.list_personalities()
        assert len(personalities) > 0

        # Test getting a specific personality
        neutral = personality_manager.get_personality("neutral")
        assert neutral.name == "Neutral"

    @pytest.mark.asyncio
    async def test_async_components(self):
        """Test async components work correctly"""
        from api_client import APIClient, Message
        from satire.engine import SatireEngine
        from harness import CodingHarness

        # Create a mock API client
        class MockAPIClient:
            async def chat(self, messages):
                return "Mock response"
            async def close(self):
                pass

        mock_api = MockAPIClient()
        satire = SatireEngine(bürokratie_mode=True)
        harness = CodingHarness(mock_api, satire)

        # Test async execution
        response = await harness.generate_code("Test prompt", "function")
        assert len(response) > 0

        response = await harness.explain_code("def test(): pass")
        assert len(response) > 0

    def test_context_compression_integration(self):
        """Test context compression integration"""
        from context_manager import context_manager

        # Clear and add context
        context_manager.clear_context()

        # Add multiple messages
        for i in range(10):
            context_manager.add_context(f"Message {i}", "user")

        # Context should be managed
        assert context_manager.get_token_count() > 0

        # Clear for next test
        context_manager.clear_context()

    def test_permission_integration(self):
        """Test permission system integration"""
        from permissions import permission_manager, PermissionLevel

        # Test permission checks
        permission_manager.set_permission("test_perm", PermissionLevel.ALLOW)
        assert permission_manager.check_permission("test_perm") is True

        permission_manager.set_permission("test_perm", PermissionLevel.DENY)
        assert permission_manager.check_permission("test_perm") is False
