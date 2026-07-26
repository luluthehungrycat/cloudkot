"""
Agent System for Cloudkot
Handles loading and managing custom agents from Markdown files
"""

from .loader import AgentLoader, MarkdownAgent
from .registry import AgentRegistry

__all__ = [
    "AgentLoader",
    "MarkdownAgent",
    "AgentRegistry",
    "agent_registry",
]

# Initialize registry
agent_registry = AgentRegistry()
