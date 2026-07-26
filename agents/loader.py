"""
Agent Loader for Cloudkot
Loads custom agents from Markdown files with YAML frontmatter
"""

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from exceptions import CloudkotValidationError, ConfigurationError


class MarkdownAgent(BaseModel):
    """Represents an agent loaded from a Markdown file"""

    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.7
    top_p: float = 0.9
    system_prompt: str = ""
    permissions: dict[str, str] = {}
    examples: list[str] = []
    tools: list[str] = []
    metadata: dict[str, Any] = {}
    source_file: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "system_prompt": self.system_prompt,
            "permissions": self.permissions,
            "examples": self.examples,
            "tools": self.tools,
            "metadata": self.metadata,
            "source_file": str(self.source_file) if self.source_file else None
        }


class AgentLoader:
    """Loads agents from Markdown files"""

    def __init__(self, search_paths: list[str | Path] | None = None):
        """Initialize agent loader

        Args:
            search_paths: List of paths to search for agent files
                         Defaults to [".agents", "~/.cloudkot/agents"]
        """
        if search_paths is None:
            search_paths = [
                Path(".agents"),
                Path.home() / ".cloudkot" / "agents"
            ]
        self.search_paths = [Path(p) for p in search_paths]
        self._loaded_agents: dict[str, MarkdownAgent] = {}

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse YAML frontmatter from Markdown content

        Returns:
            Tuple of (frontmatter_dict, remaining_content)
        """
        # Match frontmatter between --- delimiters
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)

        if not match:
            # No frontmatter, return empty dict and full content
            return {}, content

        frontmatter_str = match.group(1)
        remaining_content = match.group(2)

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            if frontmatter is None:
                frontmatter = {}
            return frontmatter, remaining_content
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in frontmatter: {e}",
                config_file="agent markdown"
            ) from e

    def _parse_examples(self, content: str) -> list[str]:
        """Parse examples from Markdown content"""
        examples = []

        # Look for code blocks with language "example"
        pattern = r'```example\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            # Clean up the example
            example = match.strip()
            if example:
                examples.append(example)

        return examples

    def _parse_tools(self, content: str) -> list[str]:
        """Parse tools from Markdown content"""
        tools = []

        # Look for lists starting with "## Tools" or "### Tools"
        tool_section_match = re.search(
            r'(?:##|###)\s*[Tt]ools\s*\n\n(.*?)(?=\n\n(?:##|###|$))',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if tool_section_match:
            tool_section = tool_section_match.group(1)
            # Extract list items
            tool_matches = re.findall(r'\s*[-*]\s*(`[^`]+`|\w+)', tool_section)
            for match in tool_matches:
                # Remove backticks if present
                tool_name = match.replace('`', '').strip()
                if tool_name:
                    tools.append(tool_name)

        return tools

    def _extract_system_prompt(self, content: str) -> str:
        """Extract system prompt from Markdown content"""
        # Look for "## System Prompt" or "### System Prompt"
        prompt_section_match = re.search(
            r'(?:##|###)\s*[Ss]ystem [Pp]rompt\s*\n\n(.*?)(?=\n\n(?:##|###|$))',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if prompt_section_match:
            return prompt_section_match.group(1).strip()

        # If no explicit system prompt section, use the full content
        return content.strip()

    def load_agent_from_file(self, file_path: Path) -> MarkdownAgent:
        """Load a single agent from a Markdown file

        Args:
            file_path: Path to the Markdown file

        Returns:
            MarkdownAgent instance
        """
        if not file_path.exists():
            raise ConfigurationError(
                f"Agent file not found: {file_path}",
                config_file=str(file_path)
            )

        if not file_path.suffix.lower() == ".md":
            raise ConfigurationError(
                f"Agent file must be Markdown (.md): {file_path}",
                config_file=str(file_path)
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter
            frontmatter, remaining_content = self._parse_frontmatter(content)

            # Extract metadata from frontmatter
            name = frontmatter.get("name", file_path.stem.replace("-", " "))
            version = frontmatter.get("version", "1.0.0")
            author = frontmatter.get("author", "Unknown")
            description = frontmatter.get("description", "")
            model = frontmatter.get("model", "gpt-4o")
            temperature = frontmatter.get("temperature", 0.7)
            top_p = frontmatter.get("top_p", 0.9)
            permissions = frontmatter.get("permissions", {})
            metadata = frontmatter.get("metadata", {})

            # Extract system prompt
            system_prompt = self._extract_system_prompt(remaining_content)

            # Parse examples and tools
            examples = self._parse_examples(remaining_content)
            tools = self._parse_tools(remaining_content)

            # Create and validate agent
            agent = MarkdownAgent(
                name=name,
                version=version,
                author=author,
                description=description,
                model=model,
                temperature=temperature,
                top_p=top_p,
                system_prompt=system_prompt,
                permissions=permissions,
                examples=examples,
                tools=tools,
                metadata=metadata,
                source_file=file_path
            )

            # Validate required fields
            if not agent.name:
                raise CloudkotValidationError(
                    f"Agent in {file_path} must have a name",
                    field="name"
                )

            return agent

        except Exception as e:
            raise ConfigurationError(
                f"Failed to load agent from {file_path}: {e}",
                config_file=str(file_path)
            ) from e

    def load_agents_from_directory(self, directory: Path) -> dict[str, MarkdownAgent]:
        """Load all agents from a directory

        Args:
            directory: Path to the directory containing agent files

        Returns:
            Dictionary of agent_name -> MarkdownAgent
        """
        agents = {}

        if not directory.exists():
            return agents

        # Find all .md files
        md_files = list(directory.glob("*.md"))

        for md_file in md_files:
            try:
                agent = self.load_agent_from_file(md_file)
                agents[agent.name] = agent
            except Exception as e:
                # Log error but continue with other agents
                print(f"Warning: Could not load agent from {md_file}: {e}")

        return agents

    def load_all_agents(self) -> dict[str, MarkdownAgent]:
        """Load agents from all search paths

        Returns:
            Dictionary of agent_name -> MarkdownAgent
        """
        all_agents = {}

        for search_path in self.search_paths:
            if search_path.exists():
                agents = self.load_agents_from_directory(search_path)
                all_agents.update(agents)

        self._loaded_agents = all_agents
        return all_agents

    def get_agent(self, agent_name: str) -> MarkdownAgent:
        """Get an agent by name

        Args:
            agent_name: Name of the agent

        Returns:
            MarkdownAgent instance
        """
        if not self._loaded_agents:
            self.load_all_agents()

        if agent_name not in self._loaded_agents:
            available = list(self._loaded_agents.keys())
            raise CloudkotValidationError(
                f"Unknown agent: {agent_name}. Available: {available}",
                field="agent"
            )

        return self._loaded_agents[agent_name]

    def list_agents(self) -> list[str]:
        """List all loaded agent names

        Returns:
            List of agent names
        """
        if not self._loaded_agents:
            self.load_all_agents()
        return list(self._loaded_agents.keys())

    def reload_agents(self):
        """Reload all agents from search paths"""
        self._loaded_agents = {}
        self.load_all_agents()


# Default loader instance
agent_loader = AgentLoader()
