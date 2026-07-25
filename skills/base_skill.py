"""
Base Skill class for Cloudkot
All skills inherit from this base class
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import asyncio


class SkillResult(BaseModel):
    """Result of a skill execution"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    tokens_used: int = 0
    skill_name: str = ""


class BaseSkill:
    """Base class for all Cloudkot skills"""
    
    def __init__(self, name: str, description: str, required_permissions: List[str] = None):
        self.name = name
        self.description = description
        self.required_permissions = required_permissions or []
        self.enabled = True

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill
        Must be implemented by subclasses
        """
        raise NotImplementedError("Skills must implement the execute method")

    def can_execute(self, permission_manager: Any) -> bool:
        """Check if this skill can be executed with current permissions"""
        for permission in self.required_permissions:
            if not permission_manager.check_permission(permission):
                return False
        return True

    def __str__(self):
        return f"Skill({self.name}: {self.description})"
