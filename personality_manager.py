"""
Personality Manager for Cloudkot
Handles different personality profiles for the coding agent
"""

from pathlib import Path

from compat import tomllib
from pydantic import BaseModel


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
        self._load_personalities()

    def _load_personalities(self):
        """Load personality configurations from TOML file"""
        if not self.config_path.exists():
            return

        with open(self.config_path, "rb") as f:
            config = tomllib.load(f)

        if "personalities" in config:
            for personality_name, personality_data in config["personalities"].items():
                self.personalities[personality_name] = PersonalityConfig(**personality_data)

    def get_personality(self, personality_name: str) -> PersonalityConfig:
        """Get personality configuration by name"""
        if personality_name not in self.personalities:
            raise ValueError(f"Unknown personality: {personality_name}. Available: {list(self.personalities.keys())}")
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
        with open(self.config_path, "rb") as f:
            config = tomllib.load(f)
        default = config.get("default", {})
        return str(default.get("personality", "neutral"))

    def create_custom_personality(
        self,
        name: str,
        description: str,
        system_prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> PersonalityConfig:
        """Create a custom personality configuration"""
        config = PersonalityConfig(
            name=name,
            description=description,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
        )
        self.personalities[name] = config
        return config


# Singleton instance
personality_manager = PersonalityManager()
