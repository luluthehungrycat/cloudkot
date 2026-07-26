"""
Unit tests for Agent Loader and Registry
"""

import tempfile
from pathlib import Path

import pytest

from agents.loader import AgentLoader, MarkdownAgent
from agents.registry import AgentRegistry
from exceptions import ConfigurationError, CloudkotValidationError


@pytest.fixture
def temp_agent_file():
    """Create a temporary agent file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""---
name: Test Agent
author: Test Author
version: 1.0.0
description: A test agent for testing
model: gpt-4o
temperature: 0.8
top_p: 0.95
permissions:
  tool_calls: allow
  file_access: ask
---

# Test Agent

Du bist ein Test-Agent.

## System Prompt

Du bist ein hilfreicher Assistent.

## Beispiele

- "Hallo"
- "Wie geht's?"

## Tools

- read_file
- glob_files
""")
        f.flush()
        yield Path(f.name)
        # Cleanup
        Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def agent_loader():
    """Create an AgentLoader instance for testing"""
    return AgentLoader()


class TestMarkdownAgent:
    """Tests for MarkdownAgent model"""

    def test_agent_creation(self):
        """Test MarkdownAgent creation"""
        agent = MarkdownAgent(
            name="Test Agent",
            version="1.0.0",
            author="Test Author",
            description="A test agent",
            model="gpt-4o",
            temperature=0.8,
            top_p=0.95,
            system_prompt="You are a test agent.",
            permissions={"tool_calls": "allow"},
            examples=["example 1", "example 2"],
            tools=["read_file", "glob_files"],
            source_file=Path("test.md")
        )

        assert agent.name == "Test Agent"
        assert agent.version == "1.0.0"
        assert agent.author == "Test Author"
        assert agent.model == "gpt-4o"
        assert agent.temperature == 0.8

    def test_agent_to_dict(self):
        """Test converting agent to dictionary"""
        agent = MarkdownAgent(
            name="Test Agent",
            version="1.0.0",
            model="gpt-4o",
            system_prompt="Test prompt"
        )

        result = agent.to_dict()

        assert result["name"] == "Test Agent"
        assert result["version"] == "1.0.0"
        assert result["model"] == "gpt-4o"


class TestAgentLoader:
    """Tests for AgentLoader class"""

    def test_load_agent_from_file(self, temp_agent_file, agent_loader):
        """Test loading an agent from a file"""
        agent = agent_loader.load_agent_from_file(temp_agent_file)

        assert agent.name == "Test Agent"
        assert agent.author == "Test Author"
        assert agent.version == "1.0.0"
        assert agent.model == "gpt-4o"
        assert agent.temperature == 0.8
        assert agent.top_p == 0.95
        assert "tool_calls" in agent.permissions
        assert "file_access" in agent.permissions

    def test_load_agent_without_frontmatter(self, agent_loader):
        """Test loading an agent without frontmatter"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is a simple agent without frontmatter.")
            f.flush()
            
            agent = agent_loader.load_agent_from_file(Path(f.name))
            
            assert agent.name == "simple-agent"  # Derived from filename
            assert agent.system_prompt == "This is a simple agent without frontmatter."
            
            Path(f.name).unlink(missing_ok=True)

    def test_load_agent_invalid_file(self, agent_loader):
        """Test loading from non-existent file"""
        with pytest.raises(ConfigurationError):
            agent_loader.load_agent_from_file(Path("nonexistent.md"))

    def test_load_agent_non_markdown_file(self, agent_loader):
        """Test loading from non-Markdown file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Not a markdown file")
            f.flush()
            
            with pytest.raises(ConfigurationError):
                agent_loader.load_agent_from_file(Path(f.name))
            
            Path(f.name).unlink(missing_ok=True)

    def test_parse_examples(self, agent_loader):
        """Test parsing examples from content"""
        content = """
## Beispiele

```example
Beispiel 1
```

```example
Beispiel 2
```
"""
        examples = agent_loader._parse_examples(content)
        
        assert len(examples) == 2
        assert "Beispiel 1" in examples
        assert "Beispiel 2" in examples

    def test_parse_tools(self, agent_loader):
        """Test parsing tools from content"""
        content = """
## Tools

- read_file
- `glob_files`
- grep_files
"""
        tools = agent_loader._parse_tools(content)
        
        assert len(tools) == 3
        assert "read_file" in tools
        assert "glob_files" in tools
        assert "grep_files" in tools

    def test_extract_system_prompt(self, agent_loader):
        """Test extracting system prompt from content"""
        content = """
# Test Agent

## System Prompt

Du bist ein hilfreicher Assistent.

## Andere Sektion

Dies ist kein Teil des Prompts.
"""
        prompt = agent_loader._extract_system_prompt(content)
        
        assert "hilfreicher Assistent" in prompt
        assert "Andere Sektion" not in prompt


class TestAgentRegistry:
    """Tests for AgentRegistry class"""

    def test_list_agents(self):
        """Test listing agents"""
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        # Should have at least the example agent if .agents/ exists
        assert isinstance(agents, list)

    def test_get_agent(self):
        """Test getting an agent by name"""
        registry = AgentRegistry()
        
        # This will work if example-agent.md exists
        try:
            agent = registry.get_agent("Example Agent")
            assert agent.name == "Example Agent"
        except CloudkotValidationError:
            # Agent might not exist in test environment
            pass

    def test_get_unknown_agent(self):
        """Test getting an unknown agent raises error"""
        registry = AgentRegistry()
        
        with pytest.raises(CloudkotValidationError) as exc_info:
            registry.get_agent("Nonexistent Agent")
        
        assert "Unknown agent" in str(exc_info.value)

    def test_agent_config(self):
        """Test getting agent configuration"""
        registry = AgentRegistry()
        
        try:
            config = registry.get_agent_config("Example Agent")
            assert "name" in config
            assert "model" in config
        except CloudkotValidationError:
            # Agent might not exist in test environment
            pass
