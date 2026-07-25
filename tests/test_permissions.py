"""
Unit tests for PermissionManager
"""

import pytest

from permissions import PermissionLevel, PermissionManager


@pytest.fixture
def permission_manager():
    """Create a PermissionManager instance for testing"""
    return PermissionManager()


class TestPermissionManager:
    """Tests for PermissionManager class"""

    def test_default_permissions(self, permission_manager):
        """Test that default permissions are set"""
        # Should have default permissions
        assert "tool_calls" in permission_manager.permissions
        assert "file_access" in permission_manager.permissions
        assert "network_access" in permission_manager.permissions
        assert "execute_code" in permission_manager.permissions

    def test_check_permission_allow(self, permission_manager):
        """Test checking a permission that is allowed"""
        # Set a permission to ALLOW
        permission_manager.set_permission("test_perm", PermissionLevel.ALLOW)

        assert permission_manager.check_permission("test_perm") is True

    def test_check_permission_deny(self, permission_manager):
        """Test checking a permission that is denied"""
        # Set a permission to DENY
        permission_manager.set_permission("test_perm", PermissionLevel.DENY)

        assert permission_manager.check_permission("test_perm") is False

    def test_check_permission_ask(self, permission_manager):
        """Test checking a permission that requires asking"""
        # Set a permission to ASK
        permission_manager.set_permission("test_perm", PermissionLevel.ASK)

        # In non-interactive mode, ASK should return False
        assert permission_manager.check_permission("test_perm") is False

    def test_get_permission(self, permission_manager):
        """Test getting a permission level"""
        permission_manager.set_permission("test_perm", PermissionLevel.ALLOW)

        level = permission_manager.get_permission("test_perm")
        assert level == PermissionLevel.ALLOW

    def test_unknown_permission_defaults_to_deny(self, permission_manager):
        """Test that unknown permissions default to DENY"""
        level = permission_manager.get_permission("unknown_perm")
        assert level == PermissionLevel.DENY

    def test_set_permission(self, permission_manager):
        """Test setting a permission"""
        permission_manager.set_permission("new_perm", PermissionLevel.ALLOW)

        assert permission_manager.get_permission("new_perm") == PermissionLevel.ALLOW

    def test_permission_levels(self):
        """Test PermissionLevel enum"""
        assert PermissionLevel.ALLOW.value == "allow"
        assert PermissionLevel.DENY.value == "deny"
        assert PermissionLevel.ASK.value == "ask"

    def test_load_from_config(self):
        """Test loading permissions from config file"""
        # Create a temporary config file
        import os
        import tempfile

        config_content = """
[permissions]
tool_calls = "allow"
file_access = "ask"
network_access = "deny"
execute_code = "allow"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            pm = PermissionManager(config_path)

            assert pm.get_permission("tool_calls") == PermissionLevel.ALLOW
            assert pm.get_permission("file_access") == PermissionLevel.ASK
            assert pm.get_permission("network_access") == PermissionLevel.DENY
            assert pm.get_permission("execute_code") == PermissionLevel.ALLOW

        finally:
            os.unlink(config_path)
