"""
Skill Manager for Cloudkot
Manages all available skills and their execution
"""

import os
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_skill import BaseSkill, SkillResult
from permissions import permission_manager


class SkillManager:
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_dir = Path("skills")
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """Load built-in skills"""
        # Code Generation Skill
        self.register_skill(CodeGenerationSkill())
        
        # Code Explanation Skill
        self.register_skill(CodeExplanationSkill())
        
        # Code Refactoring Skill
        self.register_skill(CodeRefactoringSkill())
        
        # Code Review Skill
        self.register_skill(CodeReviewSkill())
        
        # Documentation Skill
        self.register_skill(DocumentationSkill())

    def register_skill(self, skill: BaseSkill):
        """Register a new skill"""
        self.skills[skill.name] = skill

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name"""
        return self.skills.get(skill_name)

    def list_skills(self) -> List[str]:
        """List all available skill names"""
        return list(self.skills.keys())

    def list_enabled_skills(self) -> List[str]:
        """List all enabled skill names"""
        return [name for name, skill in self.skills.items() if skill.enabled]

    def enable_skill(self, skill_name: str):
        """Enable a skill"""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = True

    def disable_skill(self, skill_name: str):
        """Disable a skill"""
        if skill_name in self.skills:
            self.skills[skill_name].enabled = False

    def can_execute_skill(self, skill_name: str) -> bool:
        """Check if a skill can be executed"""
        skill = self.get_skill(skill_name)
        if not skill:
            return False
        if not skill.enabled:
            return False
        return skill.can_execute(permission_manager)

    async def execute_skill(self, skill_name: str, **kwargs) -> SkillResult:
        """Execute a skill by name"""
        skill = self.get_skill(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Unknown skill: {skill_name}",
                skill_name=skill_name
            )
        
        if not skill.enabled:
            return SkillResult(
                success=False,
                error=f"Skill {skill_name} is disabled",
                skill_name=skill_name
            )
        
        if not skill.can_execute(permission_manager):
            return SkillResult(
                success=False,
                error=f"Insufficient permissions for skill {skill_name}",
                skill_name=skill_name
            )
        
        return await skill.execute(**kwargs)

    def load_custom_skills(self, skills_dir: str = "skills"):
        """Load custom skills from a directory"""
        skills_path = Path(skills_dir)
        if not skills_path.exists():
            return
        
        for skill_file in skills_path.glob("*_skill.py"):
            if skill_file.name == "base_skill.py" or skill_file.name == "skill_manager.py":
                continue
            
            module_name = skill_file.stem
            try:
                module = importlib.import_module(f"{skills_dir}.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr != BaseSkill:
                        skill_instance = attr()
                        self.register_skill(skill_instance)
            except Exception as e:
                print(f"Failed to load skill from {skill_file}: {e}")


# Create skill implementations
class CodeGenerationSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="code_generation",
            description="Generate code from natural language descriptions",
            required_permissions=["tool_calls"]
        )

    async def execute(self, prompt: str, language: str = "python", **kwargs) -> SkillResult:
        # This would integrate with the main API client
        return SkillResult(
            success=True,
            output=f"Generated {language} code for: {prompt}",
            skill_name=self.name
        )


class CodeExplanationSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="code_explanation",
            description="Explain how code works",
            required_permissions=["tool_calls"]
        )

    async def execute(self, code: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Explanation of code: {code[:50]}...",
            skill_name=self.name
        )


class CodeRefactoringSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="code_refactoring",
            description="Refactor code to improve quality",
            required_permissions=["tool_calls"]
        )

    async def execute(self, code: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Refactored code: {code[:50]}...",
            skill_name=self.name
        )


class CodeReviewSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="code_review",
            description="Review code for quality and issues",
            required_permissions=["tool_calls"]
        )

    async def execute(self, code: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Code review for: {code[:50]}...",
            skill_name=self.name
        )


class DocumentationSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="documentation",
            description="Generate documentation for code",
            required_permissions=["tool_calls"]
        )

    async def execute(self, code: str, **kwargs) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"Documentation for: {code[:50]}...",
            skill_name=self.name
        )


# Singleton instance
skill_manager = SkillManager()
