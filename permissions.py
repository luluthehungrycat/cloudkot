"""
Permission System for Cloudkot
Handles tool call permissions and access control
"""

import asyncio
import tomllib
from enum import Enum
from pathlib import Path


class PermissionLevel(Enum):
    DENY = "deny"
    ASK = "ask"
    ALLOW = "allow"


class PermissionManager:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.permissions: dict[str, PermissionLevel] = {}
        self._load_permissions()

    def _load_permissions(self):
        """Load permissions from config file"""
        # Default permissions
        self.permissions = {
            "tool_calls": PermissionLevel.ALLOW,
            "file_access": PermissionLevel.ASK,
            "network_access": PermissionLevel.DENY,
            "execute_code": PermissionLevel.ASK,
        }

        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)

            if "permissions" in config:
                for permission_name, permission_value in config["permissions"].items():
                    try:
                        self.permissions[permission_name] = PermissionLevel(permission_value)
                    except ValueError:
                        # Default to DENY if invalid permission level
                        self.permissions[permission_name] = PermissionLevel.DENY
        except Exception as e:
            print(f"Warning: Could not load permissions from config: {e}")

    def check_permission(self, permission_name: str) -> bool:
        """Check if a permission is granted"""
        permission = self.permissions.get(permission_name, PermissionLevel.DENY)

        if permission == PermissionLevel.ALLOW:
            return True
        elif permission == PermissionLevel.DENY:
            return False
        else:  # ASK
            # For now, we'll return False for ASK in non-interactive mode
            # In a real TUI, this would prompt the user
            return False

    def check_permission_async(self, permission_name: str) -> bool:
        """Async version of check_permission for TUI integration"""
        return self.check_permission(permission_name)

    def set_permission(self, permission_name: str, level: PermissionLevel):
        """Set a permission level"""
        self.permissions[permission_name] = level

    def get_permission(self, permission_name: str) -> PermissionLevel:
        """Get the current permission level"""
        return self.permissions.get(permission_name, PermissionLevel.DENY)

    async def request_permission(self, permission_name: str, action_description: str) -> bool:
        """
        Request permission from user (for ASK level permissions)
        In non-interactive mode, returns False
        """
        permission = self.get_permission(permission_name)

        if permission == PermissionLevel.ALLOW:
            return True
        elif permission == PermissionLevel.DENY:
            return False
        else:  # ASK
            # In a real implementation, this would show a prompt in the TUI
            # For now, we'll simulate a delay and return False
            await asyncio.sleep(0.1)
            return False


# Singleton instance
permission_manager = PermissionManager()
