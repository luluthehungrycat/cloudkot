"""
Agent Registry for Cloudkot
Central registry for managing all available agents
"""

from typing import Any

from exceptions import CloudkotValidationError

from .loader import MarkdownAgent, agent_loader


class AgentRegistry:
    """Central registry for all agents (builtin + custom)"""

    def __init__(self):
        self._agents: dict[str, MarkdownAgent] = {}
        self._builtin_agents: dict[str, MarkdownAgent] = {}
        self._custom_agents: dict[str, MarkdownAgent] = {}
        self._load_builtin_agents()
        self._load_custom_agents()

    def _load_builtin_agents(self):
        """Load built-in agents (from .agents/ in package)"""
        # Built-in agents are in the package's .agents/ directory
        # For now, we'll load from the current directory's .agents/
        # In the future, this will be from the package
        pass

    def _load_custom_agents(self):
        """Load custom agents from search paths"""
        try:
            agents = agent_loader.load_all_agents()
            self._custom_agents = agents
            self._agents = {**self._builtin_agents, **self._custom_agents}
        except Exception:
            pass

    def register_agent(self, agent: MarkdownAgent):
        """Register a new agent"""
        self._agents[agent.name] = agent
        if agent.source_file:
            self._custom_agents[agent.name] = agent
        else:
            self._builtin_agents[agent.name] = agent

    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self._agents:
            del self._agents[agent_name]
            if agent_name in self._custom_agents:
                del self._custom_agents[agent_name]
            elif agent_name in self._builtin_agents:
                del self._builtin_agents[agent_name]

    def get_agent(self, agent_name: str) -> MarkdownAgent:
        """Get an agent by name"""
        if agent_name not in self._agents:
            available = list(self._agents.keys())
            raise CloudkotValidationError(
                f"Unknown agent: {agent_name}. Available: {available}",
                field="agent"
            )
        return self._agents[agent_name]

    def list_agents(self) -> list[str]:
        """List all available agent names"""
        return list(self._agents.keys())

    def list_builtin_agents(self) -> list[str]:
        """List built-in agent names"""
        return list(self._builtin_agents.keys())

    def list_custom_agents(self) -> list[str]:
        """List custom agent names"""
        return list(self._custom_agents.keys())

    def get_agent_config(self, agent_name: str) -> dict[str, Any]:
        """Get full configuration for an agent"""
        agent = self.get_agent(agent_name)
        return agent.to_dict()

    def reload(self):
        """Reload all agents"""
        self._load_builtin_agents()
        self._load_custom_agents()

    def get_agent_permissions(self, agent_name: str) -> dict[str, str]:
        """Get permissions for a specific agent"""
        agent = self.get_agent(agent_name)
        return agent.permissions

    def get_agent_system_prompt(self, agent_name: str) -> str:
        """Get system prompt for a specific agent"""
        agent = self.get_agent(agent_name)
        return agent.system_prompt


# Singleton instance
agent_registry = AgentRegistry()
