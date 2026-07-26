"""
Unit tests for ProfileManager
"""

import pytest

from profile_manager import ProfileManager, ProfileConfig
from exceptions import ConfigurationError, CloudkotValidationError


@pytest.fixture
def profile_manager():
    """Create a ProfileManager instance for testing"""
    return ProfileManager("profiles.toml")


class TestProfileManager:
    """Tests for ProfileManager class"""

    def test_load_profiles(self, profile_manager):
        """Test that profiles are loaded from config"""
        profiles = profile_manager.list_profiles()

        # Should have at least the profiles we defined
        expected_profiles = ["plan", "build", "review", "debug", "document", "test"]

        for profile in expected_profiles:
            assert profile in profiles

    def test_get_profile(self, profile_manager):
        """Test getting a specific profile"""
        profile = profile_manager.get_profile("build")

        assert profile.name == "Build"
        assert "Implementierung" in profile.description or "Code" in profile.description
        assert profile.model == "claude-3-5-sonnet-20241022"
        assert profile.temperature == 0.7
        assert profile.top_p == 0.9

    def test_get_unknown_profile(self, profile_manager):
        """Test getting an unknown profile raises error"""
        with pytest.raises(CloudkotValidationError) as exc_info:
            profile_manager.get_profile("unknown_profile")

        assert "Unknown profile" in str(exc_info.value)

    def test_get_default_profile(self, profile_manager):
        """Test getting the default profile"""
        default = profile_manager.get_default_profile()
        assert default == "build"

    def test_get_profile_config(self, profile_manager):
        """Test getting full profile configuration"""
        config = profile_manager.get_profile_config("review")

        assert config["name"] == "Review"
        assert config["model"] == "gpt-4o"
        assert config["temperature"] == 0.1
        assert "permissions" in config

    @pytest.mark.skip(reason="Profile permissions not yet fully implemented")
    def test_get_profile_permissions(self, profile_manager):
        """Test getting permissions for a profile"""
        permissions = profile_manager.get_profile_permissions("debug")

        assert "tool_calls" in permissions
        assert "file_access" in permissions
        assert "network_access" in permissions
        assert "execute_code" in permissions

    def test_get_profile_system_prompt(self, profile_manager):
        """Test getting system prompt for a profile"""
        prompt = profile_manager.get_profile_system_prompt("plan")

        assert len(prompt) > 0

    def test_set_default_profile(self, profile_manager):
        """Test setting the default profile"""
        profile_manager.set_default_profile("review")
        assert profile_manager.get_default_profile() == "review"
        
        # Reset to default
        profile_manager.set_default_profile("build")

    def test_set_invalid_default_profile(self, profile_manager):
        """Test setting an invalid default profile raises error"""
        with pytest.raises(CloudkotValidationError):
            profile_manager.set_default_profile("invalid_profile")

    def test_reload_profiles(self, profile_manager):
        """Test reloading profiles"""
        initial_count = len(profile_manager.list_profiles())
        profile_manager.reload_profiles()
        reloaded_count = len(profile_manager.list_profiles())
        
        assert initial_count == reloaded_count


class TestProfileConfig:
    """Tests for ProfileConfig model"""

    def test_profile_config_creation(self):
        """Test ProfileConfig creation"""
        config = ProfileConfig(
            name="Test Profile",
            description="A test profile",
            model="gpt-4o",
            temperature=0.5,
            top_p=0.9,
            system_prompt="You are a test assistant.",
            permissions={"tool_calls": "allow", "file_access": "deny"}
        )

        assert config.name == "Test Profile"
        assert config.description == "A test profile"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.top_p == 0.9
        assert config.permissions["tool_calls"] == "allow"

    def test_profile_config_defaults(self):
        """Test ProfileConfig with default values"""
        config = ProfileConfig(
            name="Minimal Profile",
            description="Minimal configuration",
            model="gpt-4o"
        )

        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.system_prompt == ""
        assert config.permissions == {}
