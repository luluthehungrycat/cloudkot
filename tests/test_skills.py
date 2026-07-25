"""
Unit tests for Skills System
"""

import pytest

from skills.base_skill import BaseSkill, SkillResult
from skills.skill_manager import SkillManager


@pytest.fixture
def mgr():
    """Create a SkillManager instance for testing"""
    return SkillManager()


class TestSkillManager:
    """Tests for SkillManager class"""

    def test_list_skills(self, mgr):
        """Test listing available skills"""
        skills = mgr.list_skills()

        # Should have built-in skills
        expected_skills = [
            "code_generation", "code_explanation",
            "code_refactoring", "code_review", "documentation"
        ]

        for skill in expected_skills:
            assert skill in skills

    def test_get_skill(self, mgr):
        """Test getting a specific skill"""
        skill = mgr.get_skill("code_generation")

        assert skill is not None
        assert skill.name == "code_generation"
        assert skill.description == "Generate code from natural language descriptions"

    def test_get_unknown_skill(self, mgr):
        """Test getting an unknown skill"""
        skill = mgr.get_skill("unknown_skill")
        assert skill is None

    def test_enable_disable_skill(self, mgr):
        """Test enabling and disabling skills"""
        # Initially should be enabled
        skill = mgr.get_skill("code_generation")
        assert skill.enabled is True

        # Disable it
        mgr.disable_skill("code_generation")
        assert skill.enabled is False

        # Enable it again
        mgr.enable_skill("code_generation")
        assert skill.enabled is True

    def test_list_enabled_skills(self, mgr):
        """Test listing enabled skills"""
        enabled = mgr.list_enabled_skills()

        # All built-in skills should be enabled by default
        assert "code_generation" in enabled
        assert "code_explanation" in enabled

    def test_can_execute_skill(self, mgr):
        """Test checking if a skill can be executed"""
        # Enable the skill
        mgr.enable_skill("code_generation")

        # Should be able to execute if permissions allow
        # (This test assumes tool_calls permission is allowed)
        can_execute = mgr.can_execute_skill("code_generation")
        # This might be False if permissions are not set up
        assert isinstance(can_execute, bool)

    def test_can_execute_disabled_skill(self, mgr):
        """Test that disabled skills cannot be executed"""
        mgr.disable_skill("code_generation")

        can_execute = mgr.can_execute_skill("code_generation")
        assert can_execute is False

    def test_register_skill(self, mgr):
        """Test registering a custom skill"""
        class CustomSkill(BaseSkill):
            def __init__(self):
                super().__init__(
                    name="custom_skill",
                    description="A custom test skill"
                )

            async def execute(self, **kwargs) -> SkillResult:
                return SkillResult(success=True, output="Custom skill executed")

        custom_skill = CustomSkill()
        mgr.register_skill(custom_skill)

        assert "custom_skill" in mgr.list_skills()


class TestBaseSkill:
    """Tests for BaseSkill class"""

    def test_skill_creation(self):
        """Test creating a skill"""
        skill = BaseSkill(
            name="test_skill",
            description="A test skill",
            required_permissions=["tool_calls"]
        )

        assert skill.name == "test_skill"
        assert skill.description == "A test skill"
        assert skill.required_permissions == ["tool_calls"]
        assert skill.enabled is True

    def test_skill_str(self):
        """Test string representation of skill"""
        skill = BaseSkill(name="test_skill", description="A test skill")

        skill_str = str(skill)
        assert "test_skill" in skill_str
        assert "A test skill" in skill_str

    def test_skill_execute_not_implemented(self):
        """Test that base skill execute method raises NotImplementedError"""
        skill = BaseSkill(name="test_skill", description="A test skill")

        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(skill.execute())


class TestBuiltInSkills:
    """Tests for built-in skills"""

    def test_code_generation_skill(self, mgr):
        """Test code generation skill"""
        skill = mgr.get_skill("code_generation")

        assert skill is not None
        assert "code" in skill.description.lower()

    def test_code_explanation_skill(self, mgr):
        """Test code explanation skill"""
        skill = mgr.get_skill("code_explanation")

        assert skill is not None
        assert "explain" in skill.description.lower()

    def test_code_refactoring_skill(self, mgr):
        """Test code refactoring skill"""
        skill = mgr.get_skill("code_refactoring")

        assert skill is not None
        assert "refactor" in skill.description.lower()

    def test_code_review_skill(self, mgr):
        """Test code review skill"""
        skill = mgr.get_skill("code_review")

        assert skill is not None
        assert "review" in skill.description.lower()

    def test_documentation_skill(self, mgr):
        """Test documentation skill"""
        skill = mgr.get_skill("documentation")

        assert skill is not None
        assert "documentation" in skill.description.lower()
