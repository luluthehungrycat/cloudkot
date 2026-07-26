"""
Personality Manager for Cloudkot
Handles different personality profiles for the coding agent
"""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pathlib import Path

from pydantic import BaseModel

from exceptions import CloudkotValidationError, ConfigurationError


class PersonalityConfig(BaseModel):
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    top_p: float = 0.9


class PersonalityManager:
    def __init__(self, config_path: str = "personalities.toml"):
        self.config_path = Path(config_path)
        self.personalities: dict[str, PersonalityConfig] = {}
        self._loaded = False
        self._load_personalities()

    def _load_personalities(self):
        """Load personality configurations from TOML file"""
        if self._loaded:
            return

        if not self.config_path.exists():
            raise ConfigurationError(
                f"Personalities configuration file not found: {self.config_path}",
                config_file=str(self.config_path)
            )

        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)

            if "personalities" in config:
                for personality_name, personality_data in config["personalities"].items():
                    try:
                        self.personalities[personality_name] = PersonalityConfig(**personality_data)
                    except Exception as e:
                        raise CloudkotValidationError(
                            f"Invalid personality configuration for '{personality_name}': {e}",
                            field=personality_name
                        ) from e

            self._loaded = True
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load personalities from {self.config_path}: {e}",
                config_file=str(self.config_path)
            ) from e

    def get_personality(self, personality_name: str) -> PersonalityConfig:
        """Get personality configuration by name"""
        if personality_name not in self.personalities:
            available = list(self.personalities.keys())
            raise CloudkotValidationError(
                f"Unknown personality: {personality_name}. Available: {available}",
                field="personality"
            )
        return self.personalities[personality_name]

    def get_system_prompt(self, personality_name: str) -> str:
        """Get the system prompt for a personality"""
        personality = self.get_personality(personality_name)
        return personality.system_prompt

    def get_temperature(self, personality_name: str) -> float:
        """Get the temperature setting for a personality"""
        personality = self.get_personality(personality_name)
        return personality.temperature

    def get_top_p(self, personality_name: str) -> float:
        """Get the top_p setting for a personality"""
        personality = self.get_personality(personality_name)
        return personality.top_p

    def list_personalities(self) -> list[str]:
        """List all available personalities"""
        return list(self.personalities.keys())

    def get_default_personality(self) -> str:
        """Get the default personality from config"""
        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)
            default = config.get("default", {})
            return str(default.get("personality", "neutral"))
        except Exception as e:
            raise ConfigurationError(
                f"Failed to get default personality: {e}",
                config_file=str(self.config_path)
            ) from e

    def create_custom_personality(
        self,
        name: str,
        description: str,
        system_prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> PersonalityConfig:
        """Create a custom personality configuration"""
        if name in self.personalities:
            raise CloudkotValidationError(
                f"Personality '{name}' already exists",
                field="name"
            )

        try:
            config = PersonalityConfig(
                name=name,
                description=description,
                system_prompt=system_prompt,
                temperature=temperature,
                top_p=top_p,
            )
            self.personalities[name] = config
            return config
        except Exception as e:
            raise CloudkotValidationError(
                f"Failed to create personality '{name}': {e}",
                field="personality"
            ) from e


# Singleton instance
personality_manager = PersonalityManager()
