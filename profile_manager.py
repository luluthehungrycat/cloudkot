"""
Profile Manager for Cloudkot
Handles different agent profiles with their specific configurations
"""

import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pydantic import BaseModel

# Import exceptions - handle both package and root import
try:
    from exceptions import CloudkotValidationError, ConfigurationError
except ModuleNotFoundError:
    # If running from root, add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from exceptions import CloudkotValidationError, ConfigurationError


class ProfileConfig(BaseModel):
    """Configuration for a single profile"""

    name: str
    description: str
    model: str
    temperature: float = 0.7
    top_p: float = 0.9
    system_prompt: str = ""
    permissions: dict[str, str] = {}


class ProfileManager:
    """Manages agent profiles for different use cases"""

    def __init__(self, config_path: str = "profiles.toml"):
        self.config_path = Path(config_path)
        self.profiles: dict[str, ProfileConfig] = {}
        self.default_profile: str = "build"
        self._loaded = False
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from TOML file"""
        if self._loaded:
            return

        # Try to load from config path
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    config = tomllib.load(f)

                # Load profiles
                if "profiles" in config:
                    for profile_name, profile_data in config["profiles"].items():
                        try:
                            self.profiles[profile_name] = ProfileConfig(**profile_data)
                        except Exception as e:
                            raise ConfigurationError(
                                f"Invalid profile configuration for '{profile_name}': {e}",
                                config_file=str(self.config_path)
                            ) from e

                # Load default profile
                if "default" in config:
                    self.default_profile = config["default"].get("profile", "build")

                self._loaded = True
                return
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load profiles from {self.config_path}: {e}",
                    config_file=str(self.config_path)
                ) from e

        # If no config file, create default profiles
        self._create_default_profiles()
        self._loaded = True

    def _create_default_profiles(self):
        """Create default profiles if config file doesn't exist"""
        self.profiles = {
            "plan": ProfileConfig(
                name="Plan",
                description="Code-Planung und Architektur-Design",
                model="gpt-4o",
                temperature=0.3,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein erfahrener Software-Architekt. "
                    "Denke langfristig und berücksichtige Trade-offs. "
                    "Nutze UML-Diagramme zur Visualisierung."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "deny",
                    "execute_code": "ask"
                }
            ),
            "build": ProfileConfig(
                name="Build",
                description="Code-Implementierung",
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein präziser Code-Generator. "
                    "Schreibe sauberen, lesbaren und gut dokumentierten Code. "
                    "Halte dich an Best Practices."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "ask",
                    "execute_code": "ask"
                }
            ),
            "review": ProfileConfig(
                name="Review",
                description="Code-Review und Qualitätssicherung",
                model="gpt-4o",
                temperature=0.1,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein strenger Code-Reviewer. "
                    "Analysiere Code auf Fehler, Sicherheitslücken und Performance-Probleme. "
                    "Sei kritisch, aber konstruktiv."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "allow",
                    "execute_code": "deny"
                }
            ),
            "debug": ProfileConfig(
                name="Debug",
                description="Fehleranalyse und Troubleshooting",
                model="gpt-4o",
                temperature=0.5,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein systematischer Debugger. "
                    "Gehe methodisch vor: Reproduzieren -> Analysieren -> Lösen -> Verifizieren. "
                    "Frage nach Fehlermeldungen und Logs."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "allow",
                    "execute_code": "ask"
                }
            ),
            "document": ProfileConfig(
                name="Document",
                description="Dokumentation",
                model="gpt-4o",
                temperature=0.4,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein technischer Redakteur. "
                    "Schreibe klare, verständliche Dokumentation. "
                    "Nutze Beispiele und Code-Snippets."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "deny",
                    "execute_code": "deny"
                }
            ),
            "test": ProfileConfig(
                name="Test",
                description="Testing",
                model="claude-3-5-sonnet-20241022",
                temperature=0.5,
                top_p=0.9,
                system_prompt=(
                    "Du bist ein Test-Experte. "
                    "Schreibe umfassende Tests (Unit, Integration, E2E). "
                    "Teste Edge Cases und Fehlerfälle."
                ),
                permissions={
                    "tool_calls": "allow",
                    "file_access": "allow",
                    "network_access": "deny",
                    "execute_code": "ask"
                }
            )
        }
        self.default_profile = "build"

    def get_profile(self, profile_name: str | None = None) -> ProfileConfig:
        """Get a profile by name, or the default profile if None"""
        if profile_name is None:
            profile_name = self.default_profile

        if profile_name not in self.profiles:
            available = list(self.profiles.keys())
            raise CloudkotValidationError(
                f"Unknown profile: {profile_name}. Available: {available}",
                field="profile"
            )

        return self.profiles[profile_name]

    def list_profiles(self) -> list[str]:
        """List all available profile names"""
        return list(self.profiles.keys())

    def get_default_profile(self) -> str:
        """Get the name of the default profile"""
        return self.default_profile

    def set_default_profile(self, profile_name: str):
        """Set the default profile"""
        if profile_name not in self.profiles:
            raise CloudkotValidationError(
                f"Unknown profile: {profile_name}",
                field="profile"
            )
        self.default_profile = profile_name

    def get_profile_permissions(self, profile_name: str | None = None) -> dict[str, str]:
        """Get permissions for a specific profile"""
        profile = self.get_profile(profile_name)
        return profile.permissions

    def get_profile_system_prompt(self, profile_name: str | None = None) -> str:
        """Get system prompt for a specific profile"""
        profile = self.get_profile(profile_name)
        return profile.system_prompt

    def get_profile_config(self, profile_name: str | None = None) -> dict[str, Any]:
        """Get full configuration for a profile"""
        profile = self.get_profile(profile_name)
        return {
            "name": profile.name,
            "description": profile.description,
            "model": profile.model,
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "system_prompt": profile.system_prompt,
            "permissions": profile.permissions
        }

    def reload_profiles(self):
        """Reload profiles from config file"""
        self._loaded = False
        self._load_profiles()


# Singleton instance
profile_manager = ProfileManager()
