"""
Unit tests for PersonalityManager
"""

import pytest
from personality_manager import PersonalityManager, PersonalityConfig


@pytest.fixture
def personality_manager():
    """Create a PersonalityManager instance for testing"""
    return PersonalityManager("personalities.toml")


class TestPersonalityManager:
    """Tests for PersonalityManager class"""

    def test_load_personalities(self, personality_manager):
        """Test that personalities are loaded from config"""
        personalities = personality_manager.list_personalities()
        
        # Should have at least the personalities we defined
        expected_personalities = ["neutral", "stromberg", "friendly", "pedantic"]
        
        for personality in expected_personalities:
            assert personality in personalities

    def test_get_personality(self, personality_manager):
        """Test getting a specific personality"""
        personality = personality_manager.get_personality("neutral")
        
        assert personality.name == "Neutral"
        assert personality.description == "A professional, straightforward coding assistant"
        assert personality.temperature == 0.7
        assert personality.top_p == 0.9

    def test_get_unknown_personality(self, personality_manager):
        """Test getting an unknown personality raises error"""
        with pytest.raises(ValueError) as exc_info:
            personality_manager.get_personality("unknown_personality")
        
        assert "Unknown personality" in str(exc_info.value)

    def test_get_system_prompt(self, personality_manager):
        """Test getting system prompt for a personality"""
        prompt = personality_manager.get_system_prompt("stromberg")
        
        assert len(prompt) > 0
        assert "coding assistant" in prompt.lower()

    def test_get_temperature(self, personality_manager):
        """Test getting temperature for a personality"""
        temp = personality_manager.get_temperature("friendly")
        assert temp == 0.7

    def test_get_top_p(self, personality_manager):
        """Test getting top_p for a personality"""
        top_p = personality_manager.get_top_p("pedantic")
        assert top_p == 0.9

    def test_get_default_personality(self, personality_manager):
        """Test getting the default personality"""
        default = personality_manager.get_default_personality()
        assert default == "neutral"

    def test_create_custom_personality(self, personality_manager):
        """Test creating a custom personality"""
        custom = personality_manager.create_custom_personality(
            name="test_personality",
            description="A test personality",
            system_prompt="You are a test assistant.",
            temperature=0.5,
            top_p=0.8
        )
        
        assert custom.name == "test_personality"
        assert custom.description == "A test personality"
        assert custom.temperature == 0.5
        assert custom.top_p == 0.8
        
        # Check that it was added to the list
        assert "test_personality" in personality_manager.list_personalities()

    def test_stromberg_personality(self, personality_manager):
        """Test that Stromberg personality has expected traits"""
        stromberg = personality_manager.get_personality("stromberg")
        
        # Should have specific traits in the system prompt
        prompt = stromberg.system_prompt
        assert "efficient" in prompt.lower()
        assert "corporate" in prompt.lower()
        assert "direct" in prompt.lower()
        
        # Should have higher temperature for more varied responses
        assert stromberg.temperature >= 0.7
