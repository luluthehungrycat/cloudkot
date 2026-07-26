"""
Agent System for Cloudkot
Handles loading and managing custom agents from Markdown files
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
