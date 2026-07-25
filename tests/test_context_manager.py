"""
Unit tests for ContextManager
"""

import pytest
from context_manager import ContextManager, ContextItem


@pytest.fixture
def context_manager():
    """Create a ContextManager instance for testing"""
    return ContextManager()


class TestContextManager:
    """Tests for ContextManager class"""

    def test_add_context(self, context_manager):
        """Test adding context items"""
        item = context_manager.add_context("Hello, world!", "user")

        assert isinstance(item, ContextItem)
        assert item.content == "Hello, world!"
        assert item.role == "user"
        assert item.token_count > 0

    def test_get_context(self, context_manager):
        """Test getting context as messages"""
        context_manager.add_context("Hello!", "user")
        context_manager.add_context("Hi there!", "assistant")

        context = context_manager.get_context()

        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello!"
        assert context[1]["role"] == "assistant"
        assert context[1]["content"] == "Hi there!"

    def test_get_token_count(self, context_manager):
        """Test getting token count"""
        context_manager.add_context("Hello world", "user")
        context_manager.add_context("How are you?", "assistant")

        token_count = context_manager.get_token_count()
        assert token_count > 0

    def test_get_utilization(self, context_manager):
        """Test getting context utilization"""
        # Add some context
        context_manager.add_context("Hello world", "user")

        utilization = context_manager.get_utilization()

        # Should be between 0 and 1
        assert 0 <= utilization <= 1

    def test_clear_context(self, context_manager):
        """Test clearing context"""
        context_manager.add_context("Hello", "user")
        context_manager.add_context("Hi", "assistant")

        assert context_manager.get_token_count() > 0

        context_manager.clear_context()

        assert context_manager.get_token_count() == 0

    def test_summarize_context(self, context_manager):
        """Test summarizing context"""
        context_manager.add_context("First message", "user")
        context_manager.add_context("Second message", "user")
        context_manager.add_context("Response", "assistant")

        summary = context_manager.summarize_context()

        # Should contain user messages
        assert "First message" in summary or "Second message" in summary

    def test_get_context_hash(self, context_manager):
        """Test getting context hash"""
        context_manager.add_context("Hello", "user")

        hash1 = context_manager.get_context_hash()
        hash2 = context_manager.get_context_hash()

        # Same context should produce same hash
        assert hash1 == hash2

        # Different context should produce different hash
        context_manager.add_context("World", "assistant")
        hash3 = context_manager.get_context_hash()

        assert hash1 != hash3

    def test_context_compression(self, context_manager):
        """Test context compression when threshold is exceeded"""
        # Set a small max tokens for testing
        context_manager.max_tokens = 10
        context_manager.compression_threshold = 0.5

        # Add context that exceeds threshold
        context_manager.add_context("This is a very long message that should trigger compression", "user")

        # Token count should be reduced due to compression
        assert context_manager.get_token_count() <= context_manager.max_tokens

    def test_context_with_importance(self, context_manager):
        """Test context items with different importance levels"""
        context_manager.add_context("Important message", "user", importance=1.0)
        context_manager.add_context("Less important", "assistant", importance=0.5)

        context = context_manager.get_context()
        assert len(context) == 2

    def test_max_tokens_in_context(self, context_manager):
        """Test that context respects max_tokens limit"""
        context_manager.max_tokens = 5

        context_manager.add_context("Hello world", "user")
        context_manager.add_context("This is a much longer message", "assistant")

        context = context_manager.get_context(max_tokens=5)

        # Should only include messages that fit within token limit
        total_tokens = sum(len(msg["content"].split()) for msg in context)
        assert total_tokens <= 5

    def test_load_config(self):
        """Test loading configuration from file"""
        import tempfile
        import os

        config_content = """
[context]
max_tokens = 1000
compression_enabled = true
compression_threshold = 0.75
current_tokens = 100
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            cm = ContextManager(config_path)

            assert cm.max_tokens == 1000
            assert cm.compression_enabled is True
            assert cm.compression_threshold == 0.75
            assert cm.current_tokens == 100

        finally:
            os.unlink(config_path)
